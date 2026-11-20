# 09 — Méthodologie des Benchmarks, Charges et Graphiques Logarithmiques

**Série :** Architectures PostgreSQL Multi-Maîtres & Active-Active  
**Auteur :** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr)  
**Licence :** MIT License

---

## 1. Harnais d'exécution et isolation expérimentale

Les **187 lignes de mesures empiriques** couvrant **10 topologies PostgreSQL** (`results/benchmark_summary.csv`, `results/benchmark_extended_workloads.csv`, `results/benchmark_wan_sweep.csv`, `results/benchmark_concurrency_sweep.csv`) sont exécutées séquentiellement via `scripts/bench_pg_multimaster.sh` et `env/multi-db-docker-env` (`scripts/bench_pg_v2_runner.sh`) sur un hôte Docker WSL2 (20 vCPU, 16,4 Gio RAM) :

- **Isolation stricte :** Une seule pile tourne à la fois (`up -> setup -> chauffe -> suites -> down -v`) pour exclure toute contention RAM/NVMe entre RocksDB, Pebble et `shared_buffers`.
- **Zéro biais NAT :** `pgbench` et `sysbench` tournent dans un conteneur éphémère `bench_client` (`multi-db-pgbench-sysbench:latest`) relié au pont Docker interne de chaque cluster (`--cap-add NET_ADMIN`).
- **Parité de jeu et réconciliation :** Chaque suite tourne à `PG_SCALE = 2` (`200 000` comptes, `20` guichets, `2` agences). Entre chaque suite d'écriture, `reset_ds()` réinitialise les soldes ; `conv_chk()` contrôle `SUM(abalance) - SUM(delta)` sur chaque nœud (`balance_drift`).
- **Latence exacte (`p95`) :** Les journaux par transaction (`pgbench -l`) fournissent moyenne, écart-type et 95e centile (`lat_p95_ms`).

---

## 2. Adaptations de schéma par moteur

Par défaut, `pgbench -i` crée `pgbench_history` **sans clé primaire**, ce qui bloque `UPDATE`/`DELETE` en logique (`SQLSTATE 55000`) et Bucardo. Pour comparer les 10 piles équitablement tout en testant `L2` à part, l'initialiseur ajoute une clé primaire artificielle `hid` idiomatique :

| Groupe de topologies | Clé primaire artificielle `pgbench_history` et distribution | Adaptation `sysbench` |
| :--- | :--- | :--- |
| **`pg17-*` et `yugabyte`** | `hid BIGSERIAL PRIMARY KEY` | Standard `sbtest1..4` (répliqué sur `pg17-logical`) |
| **`pg-birep` et `bucardo`** | Séquence décalée `INCREMENT BY 2 START WITH {1, 2}` (`BIGINT PK`) | Standard `sbtest1..4` (synchronisé entre nœuds) |
| **`pgedge` (Spock 5)** | `hid BIGINT PRIMARY KEY DEFAULT snowflake.nextval('snowflake.id_seq')` | Standard ; `delta_apply` validé sur `abalance` |
| **`citus`** | Clé composite `PRIMARY KEY(aid, hid)` + `create_distributed_table` (`bid`/`tid`/`aid`) | `create_distributed_table('sbtest1..4','id')` |
| **`cockroach`** | `hid INT8 DEFAULT unique_rowid() PRIMARY KEY` | Repli auto `--db-ps-mode=disable` si requis |

---

## 3. Spécification complète des outils et charges

### 3.1 Suites `pgbench` (`A`, `B1`, `B2`, `C`, `D`, `G`, `H`)

Chaque suite `pgbench` utilise `-n -r --max-tries=100 --failures-detailed -l` pour mesurer les retries `SQLSTATE 40001` :

| Suite | Profil de charge | Clients / Flux | Durée | Plage empirique sur 10 topologies |
| :--- | :--- | :---: | :---: | :--- |
| **`A_single_rw`** | TPC-B standard (`1` nœud cible) | `8` (`1x8`, `-j 4`) | `20 s` | `42,08` (`cockroach`) à `875,91 TPS` (`pg-birep`) |
| **`B1_disjoint_rw`** | Clés partitionnées (`1..100k` vs `100k+1..200k`) | `8` (`2x4`, `-j 2`) | `20 s` | `60,35` (`cockroach`) à `1 078,90 TPS` (`bucardo`) |
| **`B2_overlap_rw`** | Chevauchement complet sur `2` écrivains | `8` (`2x4`, `-j 2`) | `20 s` | `74,17` (`cockroach`) à `1 267,77 TPS` (`bucardo`, `+123 679`) |
| **`C_multinode_ro`** | `pgbench -S` lecture seule | `16` (`2x8`/`1x16`) | `20 s` | `13 185,54` (`cockroach`) à `55 614,16 TPS` (`standalone`) |
| **`D_hot_conflict`** | `50` comptes chauds (`aid 1..50`, `delta 1..100`) | `8` (`2x4`/`1x8`) | `15 s` | `471,61` (`cockroach`) à `3 128,63 TPS` ; CRDT `1 837,64` (`0`) |
| **`G_conc_c1..c32`** | Balayage concurrence ($c \in \{1, 4, 8, 16, 32\}$) | `1..32` | `8 s` | `36,07` (`crdb c=1`) à `801,27 TPS` (`standalone c=32`) |
| **`H_append_only_insert`** | Pur `INSERT INTO bench_append_events` | `8` (`2x4`/`1x8`) | `12 s` | `627,13` (`pg-birep`) à `3 108,22 TPS` (`standalone`) ; `yb=2 987,24` |

### 3.2 Suites `sysbench` OLTP (`E1–E4`, `--db-driver=pgsql`)

La validation croisée exécute `sysbench --db-driver=pgsql --tables=4 --table-size=10000` sur quatre profils Lua : **`E1_sysbench_oltp_rw`** (`oltp_read_write`, `8` threads, `20 s`), **`E2_sysbench_oltp_ro`** (`oltp_read_only`, `8` threads, `12 s`), **`E3_sysbench_oltp_wo`** (`oltp_write_only`, `8` threads, `12 s`) et **`E4_sysbench_point_select`** (`oltp_point_select`, `16` threads, `12 s`).

- **Contraste critique `40001` :** Contrairement à MySQL (`--mysql-ignore-errors=all`), `sysbench --db-driver=pgsql` ne ré-essaie pas `SQLSTATE 40001`. Sous `SERIALIZABLE` de CockroachDB, E1 subit **`685` erreurs ignorées pour `902` commits** (`43,2 %` d'échecs, `p95 = 502,20 ms`), alors que YugabyteDB (`READ COMMITTED` Wait-on-Conflict) enregistre **`0` erreur** (`128,24 TPS`). En `E4`, `pg17-async-streaming` atteint **`148 022,41 TPS`** (`0,11 ms` moy.) contre `11 557–19 831 TPS` en moteurs distribués.

### 3.3 Injection de latence WAN (`F_wan_netem_10ms / 25ms / 50ms`)

La physique WAN (`~20`, `~50` et `~100 ms` RTT) est émulée via `tc qdisc netem` sur les conteneurs pairs/standby/workers/votants, puis retirée via `tc qdisc del dev eth0 root` :

```bash
docker run --rm --network container:<peer> --cap-add NET_ADMIN \
  multi-db-pgbench-sysbench:latest tc qdisc replace dev eth0 root netem delay 25ms
```

À `50 ms` unidirectionnels (`~100 ms` RTT), les moteurs `PC/EC` chutent à **`25,79 TPS`** (`pg17-sync-streaming`, `p95 = 779,85 ms`), **`8,84 TPS`** (`citus`, `p95 = 1 486,04 ms`), **`4,53 TPS`** (`cockroach`, `p95 = 4 453,74 ms`) et **`3,06 TPS`** (`yugabyte`, `p95 = 5 474,71 ms`), tandis que les piles `PA/EL` maintiennent `612,56–687,00 TPS` (`pg17-async-streaming`, `pgedge`, `bucardo`).

---

## 4. Pourquoi les échelles logarithmiques (`log10`) sont indispensables

Sur les 187 mesures empiriques, les écarts couvrent **près de cinq ordres de grandeur** :
- **Débit (`TPS`) :** de `3,06 TPS` (`yugabyte`, `F_wan_netem_50ms`) à `148 022,41 TPS` (`pg17-async-streaming`, `E4_sysbench_point_select`) — rapport $R_{\text{TPS}} = 148{,}022.41 / 3.06 \approx 48{,}373\times$ ($4,68$ décades ; `pgbench` V1 `5,78` à `55 614,16 TPS` couvre $3,98$ décades).
- **Latence (`ms`) :** de `0,110 ms` (`E4` moy. ; `0,257 ms` `pgbench -S`) à `5 474,705 ms` (`yugabyte`, `F_wan_netem_50ms` `p95` ; `3 401,333 ms` à `25 ms`) — rapport $R_{\text{lat}} = 5{,}474.705 / 0.110 \approx 49{,}770\times$ ($4,70$ décades).

L'étendue $D_{\text{décades}}$ et la distance visuelle $\Delta y_{\log}$ entre deux mesures $(v_1, v_2)$ obéissent à :

$$
D_{\text{décades}} = \log_{10}\!\left(\frac{v_{\max}}{v_{\min}}\right), \qquad \Delta y_{\log} = \log_{10}(v_2) - \log_{10}(v_1) = \log_{10}\!\left(\frac{v_2}{v_1}\right)
$$

Sur un axe linéaire à `55 614` ou `148 022 TPS`, une barre à `57,00 TPS` représente `< 0,1 %` de hauteur et `3,06 TPS` disparaît (`0,002 %`). L'axe `log10` associe à tout gain `2x` un pas constant ($\log_{10}(2) \approx 0,301$), préservant tous les rapports relatifs.

---

## 5. Tableau de bord interactif et 7 graphiques logarithmiques

Explorez les 10 topologies et 187 lignes — avec **bascule `log10` (défaut) / linéaire**, sélection multi-solutions, interface EN/FR, badges de dérive, matrice 18 tests (`L1–L8` + `T11–T18`) et export CSV — via l'[**Explorateur interactif hors-ligne (`dashboard/index.html`)**](../../dashboard/index.html).

### Graphique 01 — Débit multi-suites (`log10` TPS)
![Débit Log10 sur les suites principales](../../assets/charts/chart_01_tps_log_all_suites.png)
*Compare `A_single_rw`, `B1_disjoint_rw`, `C_multinode_ro`, `E_sysbench_oltp_rw` et `H_append_only_insert` sur 10 topologies (`42,08` à `55 614,16 TPS`).*

### Graphique 02 — Latence moyenne et `p95` (`log10` ms)
![Latence moyenne et p95 en Log10](../../assets/charts/chart_02_latency_log_all_suites.png)
*Expose plus de `4` décades de latence, de `0,257 ms` en lecture native à `625,04 ms` (`cockroach` Suite A `p95`) et `5 474,71 ms` (`yugabyte` WAN `50 ms`).*

### Graphique 03 — Balayage de concurrence (`G_conc_c1..c32`, `log10`)
![Courbes de concurrence en Log10](../../assets/charts/chart_03_concurrency_sweep_log.png)
*Courbes réelles à 5 points (`c = 1, 4, 8, 16, 32`) : `standalone` monte à `801,27 TPS` ; `pg17-sync` plafonne à `425 TPS` ; `cockroach` culmine à `c = 4` (`74,11 TPS`) puis retombe à `40,25 TPS` (`88` retries, `p95 = 3 400 ms`) à `c = 32`.*

### Graphique 04 — Sensibilité RTT WAN (`tc netem 0/10/25/50 ms`, `log10`)
![Sensibilité WAN en Log10](../../assets/charts/chart_04_wan_netem_sweep_log.png)
*Bifurcation PACELC sur `0/10/25/50 ms` : `pg17-async` (`587->600->619 TPS`) et `pgedge` (`645->647->687`) restent stables alors que `pg17-sync` (`122->57->26`), `citus` (`44->22->9`), `cockroach` (`19->10->4,5`) et `yugabyte` (`15->5,8->3,1`) chutent.*

### Graphique 05 — Profil `sysbench` (`E1–E4`, `log10`)
![Profil Sysbench en Log10](../../assets/charts/chart_05_sysbench_profile_log.png)
*Compare les quatre suites Lua (`E1–E4`) : piles PG natives à `1 659–1 806 TPS` (`E2` RO) et `124k–148k TPS` (`E4` point-select) contre `180–522 TPS` (`E2`) et `11,6k–19,8k TPS` (`E4`) en SQL distribué.*

### Graphique 06 — Streaming vs Logique Natif vs Multi-Maîtres (`log10`)
![Comparatif Streaming vs Logique vs Multi-Maîtres](../../assets/charts/chart_06_streaming_vs_logical_vs_mm.png)
*Compare directement les 10 topologies selon les cinq niveaux du Chapitre 10 (`pg17-async-streaming` `610,15` vs `pg17-logical` `532,38` vs `pg17-sync` `409,48` vs maillages actifs-actifs et Raft).*

### Graphique 07 — Intégrité des données vs Débit (Suite D Lignes Chaudes)
![Intégrité vs Débit Suite D](../../assets/charts/chart_07_integrity_vs_throughput.png)
*Met en regard débit Suite D et `balance_drift` absolu : pertes `-531 620` (`bucardo`), `-278 698` (`pgedge` LWW) et `-71 063` (`pg-birep`) face à **`0` dérive** sur `pgedge-delta-apply` (`1 837,64 TPS`), `pg17-async`/`logical` (`2 081`/`2 387`), `citus`, `yugabyte` et `cockroach`.*

---

## 6. Extensions V3 : Télémétrie Écosystème (`chart_08`, `chart_09`) et PostgreSQL 18.6 (`chart_10`)

L'extension V3 ajoute deux jeux de données modulaires sous le même standard logarithmique `log10` :
- **Popularité et vitalité ([Ch. 11](11_popularite_et_vitalite_ecosysteme.md)) :** Télémétrie GitHub REST/GraphQL (`21` lignes dans [`results/project_popularity.csv`](../../results/project_popularity.csv), couvrant `3+` décades) illustrée par [`chart_08_popularity_stars_forks_log.png`](../../assets/charts/chart_08_popularity_stars_forks_log.png) et [`chart_09_popularity_commits_activity_log.png`](../../assets/charts/chart_09_popularity_commits_activity_log.png).
- **Benchmarks générationnels PostgreSQL 18.6 ([Ch. 12](12_clustering_postgresql_18_et_benchmarks.md)) :** **87 mesures séquentielles** sur les 5 piles natives PG 18.6 ([`results/benchmark_pg18.csv`](../../results/benchmark_pg18.csv)) et **5 x 26 sondes** ([`results/functional_limits_pg18.csv`](../../results/functional_limits_pg18.csv)) à `PG_SCALE=2` avec clés `uuidv7()` sur `pg18-birep`, comparées à PG 17.11 dans [`chart_10_pg18_vs_pg17_log.png`](../../assets/charts/chart_10_pg18_vs_pg17_log.png) et [`dashboard/index.html`](../../dashboard/index.html).

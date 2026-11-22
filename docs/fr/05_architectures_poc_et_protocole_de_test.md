# Architectures PoC et protocole de test reproductible

> **Auteur** : Jean-Marie Renouard (`jmrenouard`) - [LightPath](https://www.lightpath.fr) | **Licence** : MIT

Ce chapitre documente la méthodologie expérimentale adoptée pour tester les architectures distribuées PostgreSQL de façon reproductible. Il précise aussi les limites de validité inhérentes à un laboratoire local conteneurisé. Voir [`stacks/README.md`](../../stacks/README.md) pour la liste des piles Compose.

---

## 1. Environnement matériel et contraintes de l'hôte WSL2

Les PoCs reproductibles s'exécutent sous **Docker Engine dans WSL2 (Ubuntu 24.04)** sur une station hôte dotée de **20 vCPU** et **16,4 Go de RAM** alloués. Cette contrainte mémoire dicte deux règles d'hygiène expérimentale strictes :

1. **Exécution strictement séquentielle** : Une seule grappe est démarrée à la fois (`up` $\rightarrow$ configuration $\rightarrow$ tests fonctionnels et limites $\rightarrow$ benchmarks $\rightarrow$ `down -v`). Aucune grappe lourde (YugabyteDB, CockroachDB, Spock 3 nœuds) ne cohabite en RAM avec une autre afin d'éviter tout phénomène de *swap* ou d'OOM-kill faussant les latences.
2. **Plafonnement mémoire explicite** : Les moteurs C++/Go à forte consommation mémoire (`YugabyteDB`, `CockroachDB`, `Citus`) reçoivent des limites de conteneur explicites (`mem_limit`, flags `--memory_limit_hard_bytes`, `--max-sql-memory`, `--cache`) pour garantir la reproductibilité sur 16,4 Go.

---

## 2. Topologies PoC et neutralisation du biais réseau NAT

Le harnais exécute **13 piles Docker Compose** couvrant **18 topologies actives** (plus la variante V1/V2 `pgedge-delta-apply`) :

| Pile Compose | Topologies actives (18 au total) | Image / Base technique | Nœuds & Routage |
| :--- | :--- | :--- | :--- |
| `pg17-baseline`, `pg-streaming` (plus `patroni` HA) | `pg17-standalone`, `pg17-async-streaming`, `pg17-sync-streaming`, Patroni HA (`#15`) | `postgres:17`, Patroni + `etcd` | 1 PG / 2 PG / 3 PG + 3 etcd |
| `pg-logical` | `pg17-logical` (`#16`) | `postgres:17` | 2 PG, réplication logique uni |
| `pg-birep` | `pg-birep` (`#1`) | `postgres:17` + HAProxy | 2 PG + 1 HAProxy (`15440`) |
| `pgedge` | `pgedge` (`#2`, plus V1/V2 `pgedge-delta-apply`) | PG 17 + Spock `5.0.14` + Snowflake | 3 PG + 1 HAProxy (`15450`) |
| `bucardo` | `bucardo` (`#9`) | PG 17 (`plperl`) + Bucardo `5.6.0` | 2 PG + daemon Perl (`15461`–`15462`) |
| `citus` | `citus` (`#7`) | `citusdata/citus` (`14.2.0` sur PG 17) | 1 coord (`15490`) + 2 workers |
| `yugabyte` | `yugabyte` (`#5`) | `yugabytedb/yugabyte:2026.1.3.0` (RF=3) | 3 YSQL (`5433`) + HAProxy `:15470` |
| `cockroach` | `cockroach`, `cockroach-rc` (`#6`) | `cockroachdb/cockroach:latest-v25.4` (V1/V2 : `v24.3.0`) | 3 CRDB + HAProxy `:15480` |
| `pg18-streaming`, `pg18-logical`, `pg18-birep` | `pg18-standalone`, `pg18-async-streaming`, `pg18-sync-streaming`, `pg18-logical`, `pg18-birep` (`#17`) | `postgres:18.6` (`io_method=worker`, `uuidv7()`) | 1 à 3 PG 18.6 + HAProxy |
| `yt-cluster` | `yt-cluster` (`cc=half`), `yt-cluster-async` (`nodes>=0`, `#18`) | `dbinvent/yt:1.21.3` (PG 18.7) | 3 nœuds `yt_cluster` / `ytserv` |

> [!IMPORTANT]
> **Élimination du biais de port-forwarding WSL2** : Les ports publiés sur `127.0.0.1:154xx` servent uniquement aux scripts de contrôle et d'administration. Tous les tirs de charge (`pgbench` et `sysbench`) sont injectés depuis le **réseau Docker interne (`bridge`)** directement sur les noms DNS de conteneurs afin d'éviter la surcharge du proxy TCP Windows/WSL2 sur les paquets courts.

---

## 3. Standardisation de schéma : clé primaire sur `pgbench_history`

L'initialisation standard `pgbench -i -s 10` crée quatre tables : `pgbench_branches`, `pgbench_tellers`, `pgbench_accounts` (dotées de clés primaires) et **`pgbench_history` (dépourvue de clé primaire)**. En réplication logique PostgreSQL (`REPLICA IDENTITY DEFAULT`), les insertions sur `pgbench_history` passent. Toute opération `UPDATE` ou `DELETE` échoue en revanche avec `SQLSTATE 55000`, et Bucardo rejette les tables sans clé unique.

Pour garantir l'équité des benchmarks TPC-B et la comparabilité entre moteurs, le protocole applique systématiquement deux étapes :
1. **Capture de la limite brute** : Vérification du rejet ou du comportement exact sur une table `pgbench_history_nokey` sans clé primaire.
2. **Standardisation pour la charge** : Ajout d'une colonne artificielle (*surrogate PK*, `hid BIGSERIAL PRIMARY KEY` en PG/Spock/Bucardo, ou clé composite `(aid, sk)` avec `sk BIGSERIAL` en Citus) avant l'exécution des suites de performance.

---

## 4. Protocole fonctionnel en 10 points

Chaque PoC doit valider ou documenter de façon automatisée dix vérifications structurelles :

1. **Santé et paramètres système** : Vérification de `wal_level`, `track_commit_timestamp`, extensions chargées (`spock`, `snowflake`, `citus`), ou membres Raft actifs (`RF = 3`).
2. **Routage d'entrée et isolation** : Preuve de distribution round-robin HAProxy (vérification via `inet_server_addr()`) et liaison stricte sur `127.0.0.1`.
3. **Écritures multi-nœuds convergentes** : Insertion/mise à jour simultanée sur des nœuds distincts avec vérification d'état identique post-synchronisation.
4. **Séquences et identifiants** : Validation du mécanisme anti-collision (`INCREMENT BY 2`, `snowflake.nextval()`, `unique_rowid()`, `bigserial` coordinateur).
5. **Contraintes secondaires `UNIQUE`** : Création et test de détection sur index unique non primaire.
6. **Intégrité référentielle (FK)** : Test parent-enfant simple et comportement multi-nœuds.
7. **Propagation DDL et `TRUNCATE`** : `ALTER TABLE ADD COLUMN` et `TRUNCATE TABLE` vérifiés sur chaque nœud cible.
8. **Primitives de session PostgreSQL** : Sondes `pg_advisory_lock()`, `LISTEN/NOTIFY`, `CREATE TEMP TABLE`, `SAVEPOINT` et disponibilité des extensions (`pg_trgm`, `uuid-ossp`, `pgvector`).
9. **Résilience sur perte de nœud** : Arrêt brutal d'un nœud (`docker stop`), poursuite des écritures sur les survivants, inspection des slots (`pg_replication_slots` / lag WAL) ou du quorum, redémarrage et contrôle de rattrapage complet.
10. **Nettoyage déterministe** : Destruction complète `docker compose down -v` laissant zéro conteneur ni volume orphelin.

---

## 5. Protocole de sondage des limites empiriques en 8 points

Au-delà des cas nominaux, chaque PoC est poussé jusqu'à ses **points de rupture architecturaux** afin de capturer les codes `SQLSTATE` réels :

| # | Scénario de rupture provoqué | Comportement attendu selon la famille |
| :-: | :--- | :--- |
| **L1** | Collision PK `SERIAL` non coordonnée | PG natif : `23505` + arrêt worker ; Spock : LWW + `exception_log` ; Raft : pas de collision |
| **L2** | `UPDATE`/`DELETE` sur table sans PK (`pgbench_history`) | PG natif/Spock : `SQLSTATE 55000` ; Bucardo : refus ; Raft/DocDB/Pebble : RowID interne OK |
| **L3** | *Lost Update* : `balance = balance + 100` vs `-30` simultanés | PG natif/LWW/Bucardo : solde erroné (`1100` ou `970`) ; Spock Delta : `1070` ; Raft : `40001` retry $\rightarrow$ `1070` |
| **L4** | Insertion simultanée de même `UNIQUE(email)` | PG natif : `23505` + blocage ; Spock : LWW ; Citus : OK si clé shard incluse ; Raft : un seul gagne / `40001` |
| **L5** | `CREATE UNIQUE INDEX` sans clé de shard (Citus) | Citus : rejet explicite `SQLSTATE 0A000` |
| **L6** | DDL transactionnel (`BEGIN; ALTER/CREATE; SAVEPOINT;`) | PG/Citus : rollback partiel atomique ; PG natif : DDL non répliqué ; CRDB : contraintes de retry |
| **L7** | Portée inter-nœuds de `pg_advisory_lock` & `LISTEN/NOTIFY` | Logique / Citus : strictement local au nœud ; CRDB : non supporté (`LISTEN`) |
| **L8** | Panne de quorum (1/3 puis 2/3 nœuds arrêtés) | Raft (`RF=3`) : survit à 1/3 (`RPO=0`), **gèle totalement à 2/3** (`PC/EC`) ; Citus : perte des shards du worker |

---

## 6. Suites de charge (`Suites A-H`, `V1-V5`)

Les vagues baseline (`V1-V2`) utilisent `PG_SCALE = 2` (ou `PG_BENCH_SCALE = 10`, soit $1\,000\,000$ de lignes). Les vagues `V5` optimisées utilisent `PG_SCALE = 20` avec chauffe préalable :

- **Suite A (`pgbench` TPC-B standard multi-écrivain)** : Charge mixte lecture/écriture (`accounts`, `tellers`, `branches`, `history` avec surrogate PK) répartie entre nœuds actifs par le proxy.
- **Suite B (`pgbench -S` et `B2` Overlap RW)** : Mesure du passage à l'échelle des lectures et des conflits d'écritures concurrentes.
- **Suite C (écritures disjointes partitionnées)** : Chaque nœud écrit sur une partition dédiée d'identifiants (`aid` modulaires ou plages par nœud) afin de mesurer le débit maximal sans conflit logique ni contention de verrou inter-nœuds.
- **Suite D (contention forte sur ligne chaude)** : Multiples clients ciblant un unique compte (`aid = 1`) pour exposer le coût des verrous distribués, le taux d'erreurs `SQLSTATE 40001` et la divergence en mode asynchrone.
- **Suite E (`sysbench oltp_read_write`)** : Charge analytique/OLTP alternative indépendante de `pgbench` validant le comportement sur transactions multi-requêtes préparées.
- **Suites `H`, `F_wan` et `G_conc` (`V2-V5`)** : Mesurent les insertions séquentielles (`H`), la latence WAN `tc netem 10/25/50 ms` (`F_wan`) et la montée en charge `V5` (`G_conc`).

Consultez les résultats complets aux chapitres [06](06_resultats_tests_et_benchmarks.md), [12](12_clustering_postgresql_18_et_benchmarks.md) et [13](13_optimisation_production_et_benchmarks_realistes.md).

---

## 7. Menaces à la validité (*Threats to Validity*)

Toute extrapolation des mesures de ce laboratoire vers une production industrielle doit intégrer cinq biais structurels :

1. **Latence réseau quasi nulle en local** : Entre conteneurs sur un même pont Docker, le RTT reste sous la milliseconde ($< 1\text{ ms}$). En production multi-régions ($\text{RTT} = 12\text{--}150\text{ ms}$), les solutions Raft/2PC (`#4` Eager, `#5`, `#6`, `#13`) subissent un effondrement de débit par session proportionnel à $1 / \text{RTT}$ (chapitre 02).
2. **Stockage VHDX partagé** : Sous WSL2, tous les nœuds d'une grappe écrivent sur le même contrôleur NVMe virtuel. Cette contention `fsync` cumulée pénalise artificiellement les grappes à 3 nœuds face à trois serveurs isolés.
3. **Absence de dérive NTP réelle** : Tous les conteneurs partagent le noyau Linux WSL2 et donc exactement la même horloge système ($\epsilon_{\text{clock}} \approx 0$). Les anomalies LWW liées à la dérive horloge réelle ($\Delta t_{\text{skew}} = 5\text{--}100\text{ ms}$) n'apparaissent qu'en multi-machines physique/VM.
4. **Échelle de données en mémoire** : À `scale = 10` (quelques centaines de mégaoctets), le jeu actif tient en RAM (`shared_buffers` / cache OS). Les coûts de compaction LSM (DocDB/Pebble) et de *VACUUM* (table `bucardo_delta` / heap PG) s'amplifient fortement sur des bases multi-téraoctets.
5. **Boucle de ré-essai applicative** : Les tests Raft mesurent le taux brut de `40001` et la convergence après ré-essai client. Un logiciel métier sans boucle de retry échoue directement là où le harnais de test converge.

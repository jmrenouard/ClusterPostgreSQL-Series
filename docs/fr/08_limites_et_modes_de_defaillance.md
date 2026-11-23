# Limites empiriques et modes de défaillance observés

> **Auteur** : Jean-Marie Renouard (`jmrenouard`) - [LightPath](https://www.lightpath.fr) | **Licence** : MIT

Ce chapitre recense les **huit limites architecturales (`L1` à `L8`)** effectivement reproduites et vérifiées sur les grappes Docker en fonctionnement (`results/functional_limits_matrix.csv` et journaux de test associés). Tous les codes `SQLSTATE` et messages d'erreur cités ont été capturés directement lors des exécutions réelles.

---

## 1. Synthèse des codes `SQLSTATE` et anomalies capturés (`L1`–`L8`)

| Limite | `pg-birep` (`#1`) | `pgedge` (`#2`) | `bucardo` (`#9`) | `citus` (`#7`) | `yugabyte` (`#5`) | `cockroach` (`#6`) |
|:---|:---|:---|:---|:---|:---|:---|
| **`L1` Sans PK** | `SQLSTATE 55000` (`UPD`/`DEL`) | Silencieux (`default_insert_only`) | Rejet `validate_sync` | `0A000` post-dist. | OK (RowID) | OK (`rowid` caché) |
| **`L2` `SERIAL` collision** | `23505` + **arrêt flux** | Écrasement LWW silencieux | Écrasement `bucardo_latest` | OK (coord. seq) | OK (cache seq) | OK (`unique_rowid`) |
| **`L3` Lost Update** | Diverge (`970`/`1100`) | LWW perd (`970`) / **Delta OK (`1070`)** | Perd (`970` sur `+100/-30`) | `0` perte (`40001` RR) | `0` perte (33 retries `40001`) | `0` perte (27 retries `40001`) |
| **`L4` `UNIQUE(email)`** | `23505` + **arrêt flux** | `23505` + `transdiscard` (diverge) | `23505` (`sync_mm` Bad) | **`0A000`** hors clé shard | Global **`23505`** | Global **`23505`** |
| **`L5` DDL / `SAVEPOINT`** | `ALTER` non propagé | Auto-DDL OK | `ALTER` non propagé | DDL + `SAVEPOINT` OK | DDL + `SAVEPOINT` OK | DDL + `SAVEPOINT` OK |
| **`L6` Primitives / Ext.** | Lock/Notify locaux | Lock/Notify locaux | Lock/Notify locaux | `vector` `0A000` absent | `LISTEN` **`0A000`** | `TEMP` **`XCEXF`**, `LISTEN` **`42601`** |
| **`L7` Panne 1 nœud** | Slot WAL 54 432 o | Slot WAL 309 560 o | 8 lignes `delta` | Shards worker coupés | Survit (`RPO = 0`) | Survit (`RPO = 0`) |
| **`L8` Panne quorum 2/3** | N/A (AP continue) | N/A (AP continue) | N/A (AP continue) | Coord. SPOF | **Gel** (timeout) | **Gel (`57014` timeout)** |

---

## 2. Analyse détaillée des 8 modes de défaillance

### `L1` — Tables sans clé primaire (`pgbench_history`)
- **Constat empirique** :
  - **`pg-birep` (`#1`)** : Les `INSERT` sur `pgbench_history_nokey` répliquent, mais tout `UPDATE` ou `DELETE` échoue immédiatement côté émetteur : `ERROR: 55000: cannot update table "pgbench_history_nokey" because it does not have a replica identity and publishes updates`.
  - **`pgedge` (`#2`)** : Spock place automatiquement la table sans PK dans le *repset* `default_insert_only`. L'`INSERT` réplique, mais `UPDATE 1` et `DELETE 1` exécutés sur `node1` **réussissent localement sans erreur et ne sont jamais propagés** (`node2` conserve l'ancienne valeur `delta=50`) — une divergence silencieuse dangereuse.
  - **`bucardo` (`#9`)** : `validate_sync` bloque l'ajout de la table : `ERROR: Table "public.pgbench_history_nokey" must specify a primary key!`.
  - **`citus` (`#7`)** : L'ajout post-distribution d'une PK hors clé de shard ou d'un `ADD COLUMN ... SERIAL` échoue en `SQLSTATE 0A000` (`cannot execute ADD COLUMN commands involving serial pseudotypes when metadata is synchronized to workers`).
  - **`cockroach` (`#6`)** : Injecte automatiquement une colonne cachée `rowid INT8 DEFAULT unique_rowid()`.
- **Remédiation** : Définir explicitement une clé primaire dès la création (`hid BIGSERIAL PRIMARY KEY`, `snowflake.nextval()`, ou composite `(aid, hid)` sous Citus).

### `L2` — Collision sur `SERIAL` non coordonné
- **Constat empirique** : Lors d'insertions simultanées `id = 1` sur deux nœuds :
  - **`pg-birep` (`#1`)** : Bloque l'*apply worker* (`apply_error_count = 1`) avec `ERROR: 23505: duplicate key value violates unique constraint "uncoord_serial_pkey"`.
  - **`pgedge` (`#2`) et `bucardo` (`#9`)** : Écrasent silencieusement la ligne du premier nœud (`spock.resolutions = 1`, `KID (sync_serial) Conflicts: 1`), effaçant la transaction de `node1` sans aucun signalement au client.
- **Remédiation** : Utiliser `snowflake` (`#2`), `unique_rowid()` (`#6`), `UUIDv7` ou des séquences à pas décalés (`INCREMENT BY N START WITH k`).

### `L3` — Anomalie *Lost Update* sur `balance = balance + delta`
- **Constat empirique** : Sur un solde initial `1000.00` (`+100` sur `node1`, `-30` sur `node2`, attendu `1070.00`), `pg-birep` diverge (`n1=970.00`, `n2=1100.00`). En face, `pgedge` LWW et `bucardo_latest` retiennent `970.00`. En charge réelle (Suite D), la dérive atteint `-531 620` sur Bucardo et `-278 698` sur Spock LWW.
- **Remédiation** : Activer `spock.delta_apply` (`1070.00` exact, dérive `0` en Suite D) ou choisir un moteur sérialisable avec boucle de retry client (`40001`). `yugabyte` a enregistré `33` retries et `cockroach` (`WriteTooOldError`) `27` retries.

### `L4` — Contraintes `UNIQUE(email)` secondaires
- **Constat empirique** : Deux insertions d'identifiants PK distincts portant le même `email` sur deux nœuds provoquent :
  - **`pg-birep` (`#1`)** : Blocage complet de la souscription (`23505` sur `accounts_email_key`).
  - **`pgedge` (`#2`)** : Sous `spock.exception_behaviour = transdiscard`, l'apply worker journalise `SPOCK: caught initial exception - [SQLSTATE 23505] duplicate key value violates unique constraint "accounts_email_key"`, incrémente `spock.exception_log` et jette la transaction distante — laissant **`n1=u1` et `n2=u2` définitivement désynchronisés**.
  - **`bucardo` (`#9`)** : `sync_mm` passe à l'état `Bad` (`DB db2 state: 23505 Error: 7`) pendant le `COPY`.
  - **`citus` (`#7`)** : Interdit structurellement tout index unique global sans la clé de distribution : `0A000: creating unique indexes on non-partition columns is currently unsupported`.
- **Remédiation** : Partitionner les écritures par locataire (*geo/tenant routing*) en asynchrone, ou inclure la colonne de sharding dans l'index unique sous Citus, ou exiger Raft (`#5`, `#6`).

### `L5` — DDL, `TRUNCATE` et `SAVEPOINT`
- **Constat empirique** : `ALTER TABLE ADD COLUMN` ne se propage pas automatiquement sous `pg-birep` (`#1`) et `bucardo` (`#9`), imposant une orchestration externe stricte sous peine de casser la réplication. En revanche, `TRUNCATE` se propage sur les deux par publication ou trigger. `pgedge` (`Auto-DDL`), `citus`, `yugabyte` et `cockroach` propagent les DDL automatiquement et valident le rollback partiel `SAVEPOINT`.

### `L6` — Primitives de session et compatibilité d'extensions
- **Constat empirique** :
  - **`pg_advisory_lock` et `LISTEN/NOTIFY`** : Strictement locaux au nœud sur `pg-birep`, `pgedge` et `bucardo` (un verrou pris sur `node1` est immédiatement ré-acquis sur `node2`, et aucun événement `NOTIFY` ne traverse les nœuds).
  - **`yugabyte` (`#5`)** : `pg_trgm`, `uuid-ossp`, `vector` et `pg_advisory_lock` fonctionnent, mais `LISTEN/NOTIFY` est désactivé : `0A000: LISTEN/NOTIFY is disabled`.
  - **`cockroach` (`#6`)** : `CREATE TEMP TABLE` échoue par défaut avec `XCEXF: temporary tables are only supported experimentally` (requiert `SET experimental_enable_temp_tables = on`), et `LISTEN` lève une erreur de syntaxe `42601: at or near "listen": syntax error`.
  - **`citus` (`#7`)** : L'image standard `citus:14.2.0-pg17` n'embarque pas l'extension `vector` (`0A000: extension "vector" is not available`).

### `L7` — Rétention WAL et engorgement sur coupure de nœud
- **Constat empirique** : Après l'arrêt d'un pair (`docker stop`) et 5 insertions, les slots inactifs retiennent **54 432 o** de WAL sur `pg-birep` et **309 560 o** sur `pgedge`. `bucardo` empile 8 lignes dans `bucardo.delta_public_accounts`. À haut débit OLTP, une panne prolongée sature le disque primaire.
- **Remédiation** : Toujours borner `max_slot_wal_keep_size` en logique et monitorer `pg_replication_slots` + `VACUUM` des tables delta. En `pg17-sync-streaming` (`synchronous_commit = on`), l'absence du standby synchrone gèle au contraire les validations primaires (`RPO = 0`).

### `L8` — Perte de quorum 2/3 sous Raft et fragilité des pools/coordinateurs
- **Constat empirique** : Sur `yugabyte` et `cockroach` (`RF = 3`), perdre 1 nœud sur 3 garde le cluster actif (`RPO = 0`, solde `500`). Perdre un 2e nœud (majorité 2/3 perdue) **gèle toute lecture et écriture** (`connection timeout expired` sur YugabyteDB, `SQLSTATE 57014` sur CockroachDB), prouvant le mode **PC/EC**. Sous `citus`, perdre `worker2` garde `worker1` et les tables de référence accessibles, mais bloque ses shards.

---

## 3. Incidents techniques identifiés durant le développement des PoCs

Trois problèmes d'intégration reproductibles ont également été documentés lors du montage des piles :
1. **pgEdge / Spock (`SQLSTATE 42501`)** : L'image minimale `17-spock5-minimal` restreint par défaut `output_plugin_libraries = 'pgoutput, test_decoding'`, bloquant `spock_output` (`42501`) jusqu'à surcharge explicite par `-c output_plugin_libraries=pgoutput,spock_output`.
2. **Bucardo (`PL/PerlU`)** : Le schéma de contrôle Bucardo (`db_getconn`) exige `PL/PerlU` et `libdbd-pg-perl` dans le conteneur PostgreSQL lui-même (et non uniquement dans le conteneur daemon), imposant une image PostgreSQL 17 personnalisée (`Dockerfile.pg`).
3. **YugabyteDB `yugabyted` RF=3** : Le facteur `RF = 3` devient effectif après jonction des 3 TServers et mise à jour du placement. Attendre explicitement `yb_servers()` avant tout test de panne.

---

## 4. Matrice étendue `T11–T18` (10 topologies, Streaming & Logique inclus)

Les huit tests avancés (`results/extended_functional_matrix.csv`, `functional_limits_matrix.csv`) intègrent **`pg17-async-streaming`** et **`pg17-logical`** :

- **`T11` Bulk 10k & rattrapage :** Le débit va de `22 079` (`cockroach`) à `67 406 lignes/s` (`pgedge`). Le rattrapage dure `105–115 ms` (streaming), `139 ms` (`bucardo`), `265 ms` (`cockroach`), `333–350 ms` (logique/Spock) et `417 ms` (`yugabyte`).
- **`T12` `UPDATE` vs `DELETE` :** **`pg17-logical` diverge** (`pub=upd_n1` vs `sub=DELETED`). Les maillages async retiennent `DELETED`, streaming rejette (`25006`) et Citus/YB/CRDB convergent.
- **`T13` Course FK inter-nœuds :** Streaming bloque (`25006x10`), et **`bucardo` échoue `0/10` (`23503x10`)**. Raft/Citus et logique LAN passent `10/10`.
- **`T14` Fidélité (64 Kio `BYTEA`, `JSONB`, UTF-8) :** `9/10` concordent (`md5=00493e3a`). L'image `pgedge` reste en **`SQL_ASCII`** (`chr(20013)` -> `54000`, UTF-8 échappé `3/3` `md5=f798eb5a`).
- **`T15` Lag RAW (`n=30`, `p50/p95` ms) :** `standalone` mesure `1,15/1,55`, `pgedge` `1,16/1,63`, `pg-birep` `1,47/2,28`, `pg17-logical` `1,68/2,14` et `pg17-sync` `1,88/2,74`. `yugabyte` atteint `2,01/2,83`, `citus` `1,71/13,89`, `cockroach` `4,09/4,98`, `pg17-async` `9,65/25,13` et `bucardo` `548,74/1 275,25`.
- **`T16` Crash `SIGKILL` & `RPO` :** Huit piles valident `20/20` (`RPO=0`) et `21/21`. `citus` `worker2` lève **`08006`** puis reprend `21/21`, tandis que `bucardo` `node1` finit à `20/21`.
- **`T17` TX ouverte 3 s :** Les 10/10 confirment `NO_DIRTY_READ`. `cockroach` bloque le lecteur par attente d'intention (`serializable_intent_wait=2,1 s`).
- **`T18` Séquences (50 inserts) :** Streaming (`66|true`), `yugabyte` (`101`) et `cockroach`/`citus` (`51`) restent sûrs. Les 4 piles logiques ou triggers restent à `1|false` -> **`23505`** (`pg17-logical` retient `27 320 o` WAL vs `3 088 o` en streaming).

---

## 5. Vérification des limites sur PostgreSQL 18.6 et pérennité

La re-vérification sous PG 18.6 ([`results/functional_limits_pg18.csv`](../../results/functional_limits_pg18.csv), [`results/benchmark_pg18.csv`](../../results/benchmark_pg18.csv), détail au [Ch. 12](12_clustering_postgresql_18_et_benchmarks.md)) actualise ces limites :
- **Résolu en PG 18.6 :** `uuidv7()` natif converge **50/50 insertions actif-actif** (`0` `23505`, `0` inversion B-tree), `data_checksums=on` protège contre les corruptions silencieuses, et `pg_stat_subscription_stats` expose **7 compteurs `confl_*`** dont **`confl_multiple_unique_conflicts=1`**.
- **Toujours ouvert en PG 18.6 :** `FOR ALL SEQUENCES` et `REFRESH SEQUENCES` lèvent **`SQLSTATE 42601`** (reporté PG 19, laissant les pairs à `1|false` -> `23505`). `io_method=io_uring` échoue (`EPERM`) sous seccomp Docker. `pg18-birep` subit encore `T13` (`2/10 ok`, `23503x8`) et des *Lost Updates* (`-83 252` en Suite D), sans Auto-DDL.
- **Vitalité et graphiques :** Évaluez le risque de maintenance (`pgEdge/spock` `621`/12m vs `bucardo`/`slony`/`rubyrep` `0`/12m) au [Ch. 11](11_popularite_et_vitalite_ecosysteme.md) et dans [`chart_08`](../../assets/charts/chart_08_popularity_stars_forks_log.png) / [`chart_09`](../../assets/charts/chart_09_popularity_commits_activity_log.png) / [`chart_10`](../../assets/charts/chart_10_pg18_vs_pg17_log.png).

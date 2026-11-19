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
- **Constat empirique** : Sur un solde initial `1000.00` subissant `+100` sur `node1` et `-30` sur `node2` (attendu `1070.00`), `pg-birep` diverge (`n1=970.00`, `n2=1100.00`), tandis que `pgedge` LWW et `bucardo_latest` convergent vers la valeur erronée `970.00`. En charge réelle (Suite D), la dérive atteint `-531 620` sur Bucardo et `-278 698` sur Spock LWW.
- **Remédiation** : Activer `spock.delta_apply` (`1070.00` exact et dérive `0` en Suite D), ou basculer vers un moteur à sérialisation avec boucle de retry client sur `SQLSTATE 40001` (`yugabyte` : 33 retries observés ; `cockroach` : `TransactionRetryWithProtoRefreshError: WriteTooOldError`, 27 retries observés).

### `L4` — Contraintes `UNIQUE(email)` secondaires
- **Constat empirique** : Deux insertions d'identifiants PK distincts portant le même `email` sur deux nœuds provoquent :
  - **`pg-birep` (`#1`)** : Blocage complet de la souscription (`23505` sur `accounts_email_key`).
  - **`pgedge` (`#2`)** : Sous `spock.exception_behaviour = transdiscard`, l'apply worker journalise `SPOCK: caught initial exception - [SQLSTATE 23505] duplicate key value violates unique constraint "accounts_email_key"`, incrémente `spock.exception_log` et jette la transaction distante — laissant **`n1=u1` et `n2=u2` définitivement désynchronisés**.
  - **`bucardo` (`#9`)** : `sync_mm` passe à l'état `Bad` (`DB db2 state: 23505 Error: 7`) pendant le `COPY`.
  - **`citus` (`#7`)** : Interdit structurellement tout index unique global sans la clé de distribution : `0A000: creating unique indexes on non-partition columns is currently unsupported`.
- **Remédiation** : Partitionner les écritures par locataire (*geo/tenant routing*) en asynchrone, ou inclure la colonne de sharding dans l'index unique sous Citus, ou exiger Raft (`#5`, `#6`).

### `L5` — DDL, `TRUNCATE` et `SAVEPOINT`
- **Constat empirique** : `ALTER TABLE ADD COLUMN` ne se propage pas automatiquement sous `pg-birep` (`#1`) et `bucardo` (`#9`), imposant une orchestration externe stricte sous peine de casser la réplication. En revanche, `TRUNCATE` se propage sur les deux via publication/trigger. `pgedge` (`Auto-DDL`), `citus`, `yugabyte` et `cockroach` propagent les DDL automatiquement et valident le rollback partiel `SAVEPOINT`.

### `L6` — Primitives de session et compatibilité d'extensions
- **Constat empirique** :
  - **`pg_advisory_lock` et `LISTEN/NOTIFY`** : Strictement locaux au nœud sur `pg-birep`, `pgedge` et `bucardo` (un verrou pris sur `node1` est immédiatement ré-acquis sur `node2`, et aucun événement `NOTIFY` ne traverse les nœuds).
  - **`yugabyte` (`#5`)** : `pg_trgm`, `uuid-ossp`, `vector` et `pg_advisory_lock` fonctionnent, mais `LISTEN/NOTIFY` est désactivé : `0A000: LISTEN/NOTIFY is disabled`.
  - **`cockroach` (`#6`)** : `CREATE TEMP TABLE` échoue par défaut avec `XCEXF: temporary tables are only supported experimentally` (requiert `SET experimental_enable_temp_tables = on`), et `LISTEN` lève une erreur de syntaxe `42601: at or near "listen": syntax error`.
  - **`citus` (`#7`)** : L'image standard `citus:14.2.0-pg17` n'embarque pas l'extension `vector` (`0A000: extension "vector" is not available`).

### `L7` — Rétention WAL et engorgement sur coupure de nœud
- **Constat empirique** : Lors d'un arrêt brutal (`docker stop`) d'un nœud pair suivi de seulement 5 insertions, les slots de réplication inactifs retiennent **54 432 octets** de WAL sur `pg-birep` et **309 560 octets** sur `pgedge`, tandis que `bucardo` empile 8 lignes dans `bucardo.delta_public_accounts`. À haut débit OLTP, une panne prolongée sature le disque primaire.
- **Remédiation** : Toujours borner `max_slot_wal_keep_size` en logique et monitorer `pg_replication_slots` + `VACUUM` des tables delta. En `pg17-sync-streaming` (`synchronous_commit = on`), l'absence du standby synchrone gèle au contraire les validations primaires (`RPO = 0`).

### `L8` — Perte de quorum 2/3 sous Raft et fragilité des pools/coordinateurs
- **Constat empirique** : Sur `yugabyte` et `cockroach` (`RF = 3`), la perte de 1 nœud sur 3 laisse le cluster totalement opérationnel (`RPO = 0`, solde `500` vérifié). L'arrêt d'un 2e nœud (perte de majorité 2/3) **gèle immédiatement toute lecture/écriture** (`connection timeout expired` sur YugabyteDB ; `SQLSTATE 57014: query execution canceled due to statement timeout` sur CockroachDB), illustrant strictement le modèle **PC/EC**. Sous `citus`, la perte de `worker2` maintient les tables de référence et `worker1` accessibles tout en bloquant uniquement les shards du worker coupé.

---

## 3. Incidents techniques identifiés durant le développement des PoCs

Trois problèmes d'intégration reproductibles ont également été documentés lors du montage des piles :
1. **pgEdge / Spock (`SQLSTATE 42501`)** : L'image minimale `17-spock5-minimal` restreint par défaut `output_plugin_libraries = 'pgoutput, test_decoding'`, bloquant `spock_output` (`42501`) jusqu'à surcharge explicite par `-c output_plugin_libraries=pgoutput,spock_output`.
2. **Bucardo (`PL/PerlU`)** : Le schéma de contrôle Bucardo (`db_getconn`) exige `PL/PerlU` et `libdbd-pg-perl` dans le conteneur PostgreSQL lui-même (et non uniquement dans le conteneur daemon), imposant une image PostgreSQL 17 personnalisée (`Dockerfile.pg`).
3. **YugabyteDB `yugabyted` RF=3** : Le facteur de réplication n'atteint `RF = 3` qu'après jonction effective des 3 nœuds TServer et mise à jour de placement, nécessitant une attente explicite sur la vue `yb_servers()` avant tout test de tolérance aux pannes.

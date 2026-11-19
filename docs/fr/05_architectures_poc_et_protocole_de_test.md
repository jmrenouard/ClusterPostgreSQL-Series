# Architectures PoC et protocole de test reproductible

> **Auteur** : Jean-Marie Renouard (`jmrenouard`) - [LightPath](https://www.lightpath.fr) | **Licence** : MIT

Ce chapitre documente la méthodologie expérimentale adoptée pour tester de manière équitable, transparente et reproductible les architectures multi-maîtres et distribuées PostgreSQL, ainsi que les limites de validité inhérentes à un laboratoire local conteneurisé.

---

## 1. Environnement matériel et contraintes de l'hôte WSL2

Les PoCs reproductibles s'exécutent sous **Docker Engine dans WSL2 (Ubuntu 24.04)** sur une station hôte dotée de **20 vCPU** et **16,4 Go de RAM** alloués. Cette contrainte mémoire dicte deux règles d'hygiène expérimentale strictes :

1. **Exécution strictement séquentielle** : Une seule grappe est démarrée à la fois (`up` $\rightarrow$ configuration $\rightarrow$ tests fonctionnels et limites $\rightarrow$ benchmarks $\rightarrow$ `down -v`). Aucune grappe lourde (YugabyteDB, CockroachDB, Spock 3 nœuds) ne cohabite en RAM avec une autre afin d'éviter tout phénomène de *swap* ou d'OOM-kill faussant les latences.
2. **Plafonnement mémoire explicite** : Les moteurs C++/Go à forte consommation mémoire (`YugabyteDB`, `CockroachDB`, `Citus`) reçoivent des limites de conteneur explicites (`mem_limit`, flags `--memory_limit_hard_bytes`, `--max-sql-memory`, `--cache`) pour garantir la reproductibilité sur 16,4 Go.

---

## 2. Topologies PoC et neutralisation du biais réseau NAT

| Topologie PoC | Image / Base technique | Nœuds | Ports localhost (Admin/Sonde) | Routage client benchmark |
| :--- | :--- | :---: | :--- | :--- |
| **`pg-birep`** | `postgres:17` + `haproxy:2.9-alpine` | 2 PG + 1 HAProxy | `15441`, `15442`, `15440` (proxy) | Réseau Docker interne (`haproxy_pg_birep:5432`) |
| **`pgedge`** | PG 17 + Spock 5 + Snowflake + `lolor` | 3 PG + 1 HAProxy | `15451`–`15453`, `15450` (proxy) | Réseau Docker interne (`haproxy_pgedge:5432`) |
| **`bucardo`** | PG 17 (`plperl`) + daemon Bucardo 5 | 2 PG + 1 Bucardo | `15461`, `15462` | Réseau Docker interne |
| **`yugabyte`** | `yugabytedb/yugabyte` (RF=3) | 3 nœuds YSQL | `15471`–`15473`, `17001` (UI) | Réseau Docker interne (`5433`) |
| **`cockroach`** | `cockroachdb/cockroach` (`--insecure` lab) | 3 nœuds CRDB | `15481`–`15483`, `18081` (UI) | Réseau Docker interne (`26257`) |
| **`citus`** | `citusdata/citus` (PG 17) | 1 coord + 2 workers | `15490` (coord), `15491`–`15492` | Réseau Docker interne (`citus_coord:5432`) |
| **Baselines (`#15`)** | `postgres:17` Standalone / Patroni + etcd | 1 PG / 3 PG + 3 etcd | Ports dédiés localhost | Réseau Docker interne |

> [!IMPORTANT]
> **Élimination du biais de port-forwarding WSL2** : Les ports publiés sur `127.0.0.1:154xx` servent uniquement aux scripts de contrôle et d'administration. Tous les tirs de charge (`pgbench` et `sysbench`) sont injectés depuis le **réseau Docker interne (`bridge`)** directement sur les noms DNS de conteneurs afin d'éviter la surcharge du proxy TCP Windows/WSL2 sur les paquets courts.

---

## 3. Standardisation de schéma : clé primaire sur `pgbench_history`

L'initialisation standard `pgbench -i -s 10` crée quatre tables : `pgbench_branches`, `pgbench_tellers`, `pgbench_accounts` (dotées de clés primaires) et **`pgbench_history` (dépourvue de clé primaire)**. En réplication logique PostgreSQL (`REPLICA IDENTITY DEFAULT`), les insertions sur `pgbench_history` passent, mais toute opération `UPDATE` ou `DELETE` ultérieure échoue avec `SQLSTATE 55000`, et Bucardo refuse purement les tables sans identifiant unique.

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

## 6. Suites de charge (`pgbench` Suites A-D et `sysbench` Suite E)

Les performances comparatives sont mesurées à facteur d'échelle fixe (`PG_BENCH_SCALE = 10` par défaut, soit $1\,000\,000$ de lignes dans `pgbench_accounts`) avec phase de chauffe (*warm-up*) préalable :

- **Suite A (`pgbench` TPC-B standard multi-écrivain)** : Charge mixte lecture/écriture (`accounts`, `tellers`, `branches`, `history` avec surrogate PK) répartie entre nœuds actifs via le point d'entrée proxy/routeur.
- **Suite B (`pgbench -S` lecture seule)** : Mesure du passage à l'échelle horizontal des lectures sur l'ensemble des nœuds.
- **Suite C (écritures disjointes partitionnées)** : Chaque nœud écrit sur une partition dédiée d'identifiants (`aid` modulaires ou plages par nœud) afin de mesurer le débit maximal sans conflit logique ni contention de verrou inter-nœuds.
- **Suite D (contention forte sur ligne chaude)** : Multiples clients ciblant un unique compte (`aid = 1`) pour exposer le coût des verrous distribués, le taux d'erreurs `SQLSTATE 40001` et la divergence en mode asynchrone.
- **Suite E (`sysbench oltp_read_write`)** : Charge analytique/OLTP alternative indépendante de `pgbench` validant le comportement sur transactions multi-requêtes préparées.

---

## 7. Menaces à la validité (*Threats to Validity*)

Toute extrapolation des mesures de ce laboratoire vers une production industrielle doit intégrer cinq biais structurels :

1. **Latence réseau quasi nulle en local** : Entre conteneurs sur un même pont Docker, le RTT reste sous la milliseconde ($< 1\text{ ms}$). En production multi-régions ($\text{RTT} = 12\text{--}150\text{ ms}$), les solutions Raft/2PC (`#4` Eager, `#5`, `#6`, `#13`) subissent un effondrement de débit par session proportionnel à $1 / \text{RTT}$ (chapitre 02).
2. **Stockage VHDX partagé** : Sous WSL2, tous les nœuds d'une grappe écrivent sur le même contrôleur NVMe virtuel ; la contention `fsync` cumulée pénalise artificiellement les grappes à 3 nœuds par rapport à trois serveurs physiques isolés.
3. **Absence de dérive NTP réelle** : Tous les conteneurs partagent le noyau Linux WSL2 et donc exactement la même horloge système ($\epsilon_{\text{clock}} \approx 0$). Les anomalies LWW liées à la dérive horloge réelle ($\Delta t_{\text{skew}} = 5\text{--}100\text{ ms}$) n'apparaissent qu'en multi-machines physique/VM.
4. **Échelle de données en mémoire** : À `scale = 10` (quelques centaines de mégaoctets), le jeu actif tient en RAM (`shared_buffers` / cache OS). Les coûts de compaction LSM (DocDB/Pebble) et de *VACUUM* (table `bucardo_delta` / heap PG) s'amplifient fortement sur des bases multi-téraoctets.
5. **Boucle de ré-essai applicative** : Les tests Raft mesurent à la fois le taux brut de `40001` et la convergence après ré-essai client ; un logiciel métier non préparé aux retries échouera directement là où le harnais de test converge.

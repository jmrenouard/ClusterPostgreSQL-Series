# Étude comparative fonctionnelle (40 critères sur 18 solutions)

> **Auteur** : Jean-Marie Renouard (`jmrenouard`) - [LightPath](https://www.lightpath.fr) | **Licence** : MIT

Les six matrices ci-dessous évaluent les **16+ solutions** — incluant **[#17 PG 18.6 Natif](solutions/pg18_native_clustering.md)** ([Ch. 12](12_clustering_postgresql_18_et_benchmarks.md)) et **[#18 YT Cluster](solutions/yt_cluster_lite.md)** — sur **40 critères techniques** regroupés en six axes (détails TDE au [Ch. 14](14_chiffrement_transparent_tde.md)). Les identifiants `#1` à `#18` renvoient aux chapitres 03a, 03b et 14.

---

## 1. Matrice A : Moteur, réplication, CAP/PACELC et latence (7 critères)

| # | Solution | Stockage | Réplication / Consensus | CAP/PACELC | Topologie écriture | Latence commit | Horloge | RPO / RTO (1 nœud) |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **#1** | PG 16-18 natif | PG Heap | WAL logique `origin=none` | PA/EL | Multi-maître async | Local (0 RTT) | NTP local | RPO>0 / RTO~0 |
| **#2** | pgEdge / Spock 5 | PG Heap | WAL logique `spock` | PA/EL | Multi-maître async | Local (0 RTT) | NTP `commit_ts` | RPO>0 / RTO~0 |
| **#3** | pglogical 2 | PG Heap | WAL logique binaire | PA/EL | Multi-maître async | Local (0 RTT) | NTP `commit_ts` | RPO>0 / RTO~0 |
| **#4** | EDB PGD (Com.) | PG Heap | WAL logique + Raft | PA/EL / PC/EC | Multi / Write-Lead | Local ou 1-2 RTT | NTP / Raft | RPO=0 (Eager) / >0 |
| **#5** | YugabyteDB | DocDB LSM | Raft par tablet + 2PC | PC/EC | Multi-écrivain dist. | 1-2 RTT quorum | HLC | RPO=0 / RTO~3-10s |
| **#6** | CockroachDB | Pebble LSM | Raft par range + 2PC | PC/EC | Multi-écrivain dist. | 1-2 RTT quorum | HLC | RPO=0 / RTO~3-10s |
| **#7** | Citus | PG Heap | Shard + 2PC ref | PC/EC | Shardé (coord/MX) | Local (1 shard)/2PC | Locale | Dépend HA Patroni |
| **#8** | OpenTenBase/PG-XL | PG Heap | 2PC + GTM central | PC/EC | MPP multi-coord | 1-2 RTT + GTM | GTM GXID | Dépend HA GTM/DN |
| **#9** | Bucardo 5 | PG Heap | Triggers + daemon Perl | PA/EL | Multi-source async | Local + trigger | NTP | RPO>0 / RTO~0 |
| **#10** | SymmetricDS | PG Heap | Triggers + HTTP Java | PA/EL | Multi-nœud / Edge | Local + trigger | NTP | RPO>0 / RTO~0 |
| **#11** | PgPool-II (Rep/SI) | PG Heap | Diffusion SQL sync | Fragile | Proxy multi-nœud | RTT tous nœuds | Aucune | Risque désync |
| **#12** | Aurora Limitless | Aurora dist. | Shards + routeurs AWS | PC/EC | Shardé managé | Intra-région RTT | Horloge AWS | RPO=0 (Multi-AZ) |
| **#13** | GCP Spanner PG | Spanner dist. | Paxos multi-régions | PC/EC | Multi-région dist. | 1-2 RTT Paxos | **TrueTime** | RPO=0 / RTO~0 |
| **#14** | RubyRep/Slony/Lond. | PG Heap | Triggers SQL/C/Ruby | PA/EL | Multi (RR) / Mono | Local + trigger | NTP | RPO>0 / manuel |
| **#15** | PG 17 / Patroni HA | PG Heap | WAL physique streaming | PC/EC (sync) | **Mono-primaire** | Local / 1 AZ RTT | Unique | RPO=0 / RTO 10-30s |
| **#17** | PG 18.6 Native (AIO/uuidv7) | PG Heap (AIO+chk) | WAL stream / `substream=p` | PA/EL / PC/EC | Mono ou Mesh async | Local ou 1 AZ RTT | Locale / NTP | RPO=0 (sync) / >0 |
| **#18** | YT Cluster 1.21 | PG Heap (ext.) | Triggers + Leader XA 2PC | CP(W)/EL(R) | Multi-maître 2PC | 4 RTT (`cc=half`) | Term/Subterm | RPO=0 / ~8s (`57P03`) |

---

## 2. Matrice B : Conflits, séquences, DDL et commit distribué (8 critères)

| # | Solution | Détection | Résolution | Lost Update (`+delta`) | Séquences / IDs | Auto-DDL | `TRUNCATE` | Commit dist. | Isolation |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **#1** | PG natif | Worker (`23505`) | **Stoppe flux** | **Exposé** | Pas décalé / UUID | Non | Oui | Aucun | RC/RR/SSI |
| **#2** | pgEdge/Spock 5 | `commit_ts` + log | LWW + `exception_log` | **Protégé** (Delta) | `snowflake` 64b | **Oui** | Oui | Aucun | RC/RR |
| **#3** | pglogical 2 | `commit_ts` | LWW / keep / error | **Exposé** | Sync manuelle | Manuel | Par repset | Aucun | RC/RR |
| **#4** | EDB PGD (Com.) | Raft / `commit_ts` | CRDT / LWW / Eager | **Protégé** (CRDT) | `bdr.global_seq` | **Oui** (Raft) | Oui | Raft / CAMO | RC/RR/Ser |
| **#5** | YugabyteDB | Verrous / HLC | Retry `40001` / Wait | **Protégé** (`40001`) | Seq PG / UUID | **Oui** | Oui | 2PC + Raft | RC/Snap/Ser |
| **#6** | CockroachDB | Intentions HLC | Retry `40001` strict | **Protégé** (`40001`) | `unique_rowid`/seq | **Oui** | Oui | Parallel 2PC | **Ser** (+RC) |
| **#7** | Citus | Verrous PG shard | Sérialisation shard | **Protégé** (1 shard) | `bigserial` coord | **Oui** | Oui | 2PC ref | RC/RR |
| **#8** | OpenTenBase | Verrous 2PC/GTM | Rollback 2PC | **Protégé** | GTM global | Oui (coord) | Oui | 2PC + GTM | RC/RR |
| **#9** | Bucardo 5 | Delta par lot | `bucardo_latest` | **Exposé** | Pas décalé / UUID | Non | Non | Aucun | RC local |
| **#10** | SymmetricDS | Batch `sym_data` | LWW / Newer / Custom | **Exposé** | Pas décalé / UUID | Optionnel | Optionnel | Aucun | RC local |
| **#11** | PgPool-II (Rep) | Aucune fiable | Aucune (divergent) | **Exposé** | Risque concurrence | Diffusé | Diffusé | Pseudo-sync | RC / SI |
| **#12** | Aurora Limitless | Verrous shards | Rollback distribué | **Protégé** | Distribuées / UUID | **Oui** | Oui | 2PC horloge | RC/RR |
| **#13** | GCP Spanner PG | 2PL + TrueTime | Retry / Aborted | **Protégé** | Bit-reversed / UUID | **Oui** | Oui | Paxos + 2PC | **Ext. Cons.** |
| **#14** | Legacy triggers | Batch/diff | LWW / Source | **Exposé** | Pas décalé | Manuel | Manuel | Aucun | RC local |
| **#15** | PG 17 / Patroni | Aucun conflit | Verrous PG natifs | **Protégé** (ACID) | `SERIAL` 100% natif | **Oui** (Tx) | **Oui** | Non requis | RC/RR/SSI |
| **#17** | PG 18.6 Native (AIO/uuidv7) | 7 `confl_*` (`23505`) | Manuel (arrêt Birep) | **Sync:Oui / Birep:Non** | **`uuidv7()`** (`42601` seq) | Stream / Non (Log) | Oui | Aucun / SyncRep | RC/RR/SSI |
| **#18** | YT Cluster 1.21 | Checkin Leader | Rejet `55409`/`40001` | **Protégé** (dérive `0`) | `uuidv7()` / Pas | Non (`sge`) | Oui | XA 2PC (`half`) | RC/RR/Ser* |

---

## 3. Matrice C : Contraintes, triggers, LOB et extensions PG (8 critères)

| # | Solution | Sans PK (`UPD`/`DEL`) | Index `UNIQUE` | Clés étrangères (FK) | `EXCLUDE` | Triggers | LOB | `PostGIS` / `pg_trgm` | `pgvector` |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **#1** | PG natif | **Refusé (`55000`)** | Arrêt `23505` | Risque $\ge 3$ nœuds | Local | `REPLICA` ok | Non | **100 % oui** | **Oui** |
| **#2** | pgEdge/Spock 5 | PK requise (ou FULL) | Résolu LWW | Risque $\ge 3$ nœuds | Local | Config. | **Oui (`lolor`)** | **100 % oui** | **Oui** |
| **#3** | pglogical 2 | PK requise | LWW / erreur | Risque $\ge 3$ nœuds | Local | Config. | Non | **100 % oui** | **Oui** |
| **#4** | EDB PGD (Com.) | PK requise | Global (Eager)/LWW | Fiable Write-Lead | Local/WL | Config. | Partiel | **100 % oui** | **Oui** |
| **#5** | YugabyteDB | RowID interne | **Global garanti** | **Globale garantie** | Non | PL/pgSQL | Non | `pg_trgm` / PGIS part. | **Oui** |
| **#6** | CockroachDB | RowID interne | **Global garanti** | **Globale garantie** | Non | Limités | Non | **Non** (spatial Go) | Vecteur Go |
| **#7** | Citus | PK requiert shard | **Erreur `0A000`** | Colocatée / Ref ok | Avec shard | Par shard | Non | **100 % oui** | **Oui** |
| **#8** | OpenTenBase | Toléré | Limité hors shard | Limitée | Non | Limités | Non | Limité | Limité |
| **#9** | Bucardo 5 | **PK obligatoire** | Risque collision | Risque async | Local | Oui | Non | **100 % oui** | **Oui** |
| **#10** | SymmetricDS | PK requise | Risque collision | Ordonnancement | Local | Oui | Binaire | **100 % oui** | **Oui** |
| **#11** | PgPool-II (Rep) | Toléré (risque) | Désync possible | Locale | Local | Risqué | Limité | Risque non-déterm. | Oui |
| **#12** | Aurora Limitless | Clé shard conseillée | Avec clé shard | Colocalisée | Limité | Limités | Non | Sous-ens. RDS | Oui (RDS) |
| **#13** | GCP Spanner PG | **PK obligatoire** | **Global garanti** | **Globale garantie** | Non | Limités | Non | **Non** (AlloyDB oui) | Spanner/ADB |
| **#14** | Legacy triggers | **PK obligatoire** | Risque collision | Fragile async | Local | Oui | Non | **100 % oui** | N/A |
| **#15** | PG 17 / Patroni | **100 % supporté** | **100 % natif** | **100 % natif** | **Natif** | **Natifs** | **Oui** | **100 % oui** | **100 % oui** |
| **#17** | PG 18.6 Native (AIO/uuidv7) | Stream OK / `55000` | Sync OK / `23505` | Stream OK / `23503` | Local | Natifs (`REPLICA`) | Stream / Non | **100 % oui** | **100 % oui** |
| **#18** | YT Cluster 1.21 | DML OK (copie PK) | Global (`40001`) | Global (`half` 10/10) | Local | Natifs+`yt_sync` | Non | **Oui** (cast) | **Oui** (cast) |

---

## 4. Matrice D : Protocole filaire, primitives de session et résilience (7 critères)

| # | Solution | Pilotes PG | `pg_advisory_lock` | `LISTEN / NOTIFY` | `SAVEPOINT` | `TEMP TABLE` | Quorum / Split-Brain | Perte d'un nœud |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **#1** | PG natif | 100 % PG | **Local au nœud** | **Local au nœud** | Local | Local | Aucun (divergence) | Slot WAL retient |
| **#2** | pgEdge/Spock 5 | 100 % PG | **Local au nœud** | **Local au nœud** | Local | Local | Aucun | Slot WAL retient |
| **#3** | pglogical 2 | 100 % PG | **Local au nœud** | **Local au nœud** | Local | Local | Aucun | Slot WAL retient |
| **#4** | EDB PGD (Com.) | 100 %+Proxy | Local (sauf WL) | Local | Oui | Local | **Quorum Raft** (3+) | Rattrapage Raft |
| **#5** | YugabyteDB | 100 %+Smart | Limité/mono-nœud | Non distribué | Oui | Oui | **Quorum Raft** (3+) | Tolère 1/3; stop 2/3 |
| **#6** | CockroachDB | Wire PG v3 | Non supporté | Non (`CHANGEFEED`) | Limité | Oui | **Quorum Raft** (3+) | Tolère 1/3; stop 2/3 |
| **#7** | Citus | 100 % PG | Sur coordinateur | Sur coordinateur | Oui | Sur coord | Aucun inter-worker | **Shards worker coupés** |
| **#8** | OpenTenBase | PG modifié | Limité | Non distribué | Limité | Sur coord | Dépend GTM | Shards datanode coupés |
| **#9** | Bucardo 5 | 100 % PG | Local | Local | Local | Local | Aucun | Delta croît |
| **#10** | SymmetricDS | 100 % PG | Local | Local | Local | Local | Aucun | Tampon `sym_data` |
| **#11** | PgPool-II (Rep) | Proxy PG | Sur primaire | Instable | Fragile | Risqué | Watchdog requis | Bascule/désync |
| **#12** | Aurora Limitless | Endpoint PG | Limité | Limité | Oui | Routeur | Quorum 6/3 AZ | Reprise auto AZ |
| **#13** | GCP Spanner PG | Dialecte PG | Non | Non | Non | Limité | **Quorum Paxos** | Tolère panne zone |
| **#14** | Legacy triggers | 100 % PG | Local | Local | Local | Local | Aucun | Queue locale croît |
| **#15** | PG 17 / Patroni | 100 % PG | **Global (unique)** | **100 % natif** | **Natif** | **Natif** | **Quorum etcd** (3+) | Bascule Patroni auto |
| **#17** | PG 18.6 Native (AIO/uuidv7) | 100 % PG | Local (Global 1-Pri) | Local (1-Pri natif) | Natif | Natif (`25006` RO) | Patroni / Aucun (Birep) | Slot WAL / SyncRep |
| **#18** | YT Cluster 1.21 | 100 % PG | **Local au nœud** | **Local au nœud** | **`0A000` rollback** | Natif | Leader (`min=2`) | Tolère 1/3 (`57P03` 2/3) |

---

## 5. Matrice E : Exploitation, sauvegarde, maturité et TCO (6 critères)

| # | Solution | Backup / PITR | Surcharge | Complexité ops | Maturité (2026) | Licence / Coût | Lock-in |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **#1** | PG natif | `pgBackRest` par nœud (non coord.) | Faible | Moyenne (conflits) | Stable (PG 16-18) | PG License (Gratuit) | Nul |
| **#2** | pgEdge/Spock 5 | `pgBackRest` par nœud | Faible-mod. | Modérée | Active | PG License (OS) | Faible |
| **#3** | pglogical 2 | `pgBackRest` par nœud | Faible | Modérée | Legacy | PG License (OS) | Faible |
| **#4** | EDB PGD (Com.) | `Barman` / `pgBackRest` | Modérée-élevée | Élevée | Entreprise | **Commercial** (vCPU) | Fort |
| **#5** | YugabyteDB | `yb_backup` distribué | Élevée (RAM) | Élevée (SRE) | Active | Apache 2.0 / EE | Modéré |
| **#6** | CockroachDB | `BACKUP` distribué | Élevée (RAM) | Élevée (SRE) | Active | BSL / Entreprise | Mod.-fort |
| **#7** | Citus | `pgBackRest` coordonné | Faible-mod. | Modérée (shard) | Active | AGPLv3 / Cloud | Modéré |
| **#8** | OpenTenBase/XL | Outils MPP dédiés | Élevée (GTM) | Élevée | XL gelé / OTB actif | Open-Source | Fort |
| **#9** | Bucardo 5 | `pgBackRest` par nœud | **Élevée (delta)** | Modérée (`plperl`) | Maint. réduite | BSD (Gratuit) | Faible |
| **#10** | SymmetricDS | `pgBackRest` par nœud | **Élevée (JVM)** | Modérée-élevée | Active (Edge) | GPLv3 / Pro | Faible |
| **#11** | PgPool-II (Rep) | `pgBackRest` par nœud | Élevée (SI) | Élevée (fragile) | Déconseillé MM | MIT/BSD (Gratuit) | Faible |
| **#12** | Aurora Limitless | Snapshots AWS managés | Managée | Faible (managée) | Active (Limitless) | Cloud AWS (Élevé) | **Très fort** |
| **#13** | GCP Spanner PG | Backup managé GCP | Managée | Faible (managée) | Active | Cloud GCP (Élevé) | **Très fort** |
| **#14** | Legacy triggers | `pgBackRest` par nœud | **Élevée (trig.)** | Élevée | **Obsolète** | Open-Source | Nul |
| **#15** | PG 17 / Patroni | `pgBackRest` + PITR natif | Minimale | Standard | Référence | Open-Source | Nul |
| **#17** | PG 18.6 Native (AIO/uuidv7) | `pgBackRest` (1-Pri/nœud) | Faible (AIO+chk) | Standard / Moy. (Birep) | **Cible PG 18.6** | PG License (Gratuit) | Nul |
| **#18** | YT Cluster 1.21 | `pgBackRest` (réversible) | Élevée (2PC+trig) | Moy.-élevée (`ytserv`) | Jeune (`v1.21`, bus=1) | MIT + PolyForm/Com. | Modéré (`DROP EXT`) |

---

## 6. Matrice F : TDE et chiffrement au repos (4 critères : 37–40)

Analyse complète des couches KMS et TDE au [Chapitre 14 — Chiffrement Transparent (TDE)](14_chiffrement_transparent_tde.md).

| # | Solution | 37. TDE moteur | 38. KMS et portée des clés | 39. Réplication et WAL chiffré | 40. Sauvegarde chiffrée et socle |
|:---|:---|:---|:---|:---|:---|
| **#1** | PG 16-18 natif | Absent cœur (`pg_tde` opt.) | OS/LUKS ou Percona `pg_tde` | Tuples logiques en clair sous TLS | LUKS + `hostssl` + `pgBackRest` AES |
| **#2** | pgEdge / Spock 5 | Absent de `spock` std | OS/LUKS ou KMS disque cloud | `spock_output` sous TLS (`hostssl`) | LUKS/KMS + `verify-full` + dépôt AES |
| **#3** | pglogical 2 | Absent du cœur PG | OS/LUKS ou KMS disque cloud | Flux `pglogical` sous TLS | LUKS/KMS + dépôt `pgBackRest` AES |
| **#4** | EDB PGD (Com.) | **Intégré (`EPAS`/`PGE`)** | `key_wrap_command` (`KMIP`/KMS) | Heap/WAL chiffrés + TLS | `Barman` hérite du TDE + KMS |
| **#5** | YugabyteDB | **Intégré OSS (`DocDB`)** | Clé universelle + DEK tablet | SSTables + WAL Raft + TLS | `yb_backup` chiffré bout en bout |
| **#6** | CockroachDB | **Enterprise / Cloud seul** | Store Keys + KMS cloud / KMIP | Pebble + WAL Raft (hors BSL gratuit) | `BACKUP` chiffré (Enterprise/Cloud) |
| **#7** | Citus | Absent OSS (`pg_tde` opt.) | OS/LUKS ou Azure CMK | Liens 2PC coord-workers sous TLS | LUKS/KMS + TLS + `pgBackRest` AES |
| **#8** | OpenTenBase/PG-XL | Absent fork PG 10-11 | OS/LUKS sur CN, DN et GTM | Trafic GTM/DN sous TLS | OS LUKS sur CN, DN et GTM |
| **#9** | Bucardo 5 | Absent du cœur PG | OS/LUKS sur PG + base `bucardo` | `bucardo.delta_*` en clair sur disque | LUKS sur données + contrôle + TLS |
| **#10** | SymmetricDS | Absent PG (`Pro` lots) | OS/LUKS sur PG + tampon JVM | Files `sym_data` + HTTPS mTLS | LUKS BD + disque Edge + mTLS |
| **#11** | PgPool-II (Rep) | **N/A (Proxy seul)** | `pool_passwd` AES + TLS | Rechiffre TLS ; exige TDE backend | TLS deux sauts + LUKS/TDE backend |
| **#12** | Aurora Limitless | **Managé (`AWS KMS`)** | CMK client (fixée à création) | Stockage 6x AZ chiffré | Snapshots/backups managés chiffrés |
| **#13** | GCP Spanner PG | **Managé (`CMEK`)** | `GCP Cloud KMS` / `EKM` | Colossus/LPS chiffrés (`Omni` : OS) | PITR managé chiffré (`Omni` : CSI) |
| **#14** | Legacy triggers | Absent du cœur PG | OS/LUKS sur hôtes historiques | Files `_slony`/`pgq` en clair disque | Migrer hors EOL ; LUKS + TLS |
| **#15** | PG 17 / Patroni | Absent cœur (`pg_tde`/PGEE) | `KMIP`/`OpenBao` ou OS/LUKS | KEK partagée en WAL physique | `pg_tde_basebackup` / `pgBackRest` AES |
| **#16** | PG 17 Logique Uni | Absent cœur (`pg_tde` opt.) | KEK indépendantes Pub / Sub | Lignes logiques sous TLS (`hostssl`) | Cible `pg_tde`/LUKS + `pgBackRest` AES |
| **#17** | PG 18.6 Native | Absent cœur (`pg_tde` 2.1) | `pg_tde` 2.1 (AIO) ou OS/LUKS | `pg_tde.wal_encrypt` WAL GA | `pg_tde_basebackup` / `pgBackRest` AES |
| **#18** | YT Cluster 1.21 | Absent cœur PG 18.7 | OS/LUKS sur PG + `ytserv` | gRPC Unix + mTLS pairs `ytserv` | LUKS PG + `ytserv` + backups AES |

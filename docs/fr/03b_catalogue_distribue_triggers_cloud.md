# Catalogue des solutions : SQL distribué, MPP, triggers et Cloud

> **Auteur** : Jean-Marie Renouard (`jmrenouard`) - [LightPath](https://www.lightpath.fr) | **Licence** : MIT

Ce chapitre présente les moteurs SQL distribués (`#5`–`#6`), le sharding MPP (`#7`–`#8`), les triggers et proxys (`#9`–`#11`, `#14`). Il couvre aussi les offres cloud managées (`#12`–`#13`).

## Fiches d'architecture détaillées (périmètre `03b`)

| ID | Solution / Topologie | Fiche FR dédiée | Périmètre |
| :---: | :--- | :--- | :--- |
| **#5** | YugabyteDB (`yugabyte`, YSQL + DocDB Raft) | [#5 — YugabyteDB](solutions/yugabytedb.md) | Benchmarké (`N5`) |
| **#6** | CockroachDB (`cockroach`, PG-wire + Pebble Multi-Raft) | [#6 — CockroachDB](solutions/cockroachdb.md) | Benchmarké (`N5`) |
| **#7** | Citus (`citus`, Coordinateur + Workers + 2PC) | [#7 — Citus](solutions/citus.md) | Benchmarké (`N5`) |
| **#8** | OpenTenBase / Postgres-XL / Postgres-XC | [#8 — OpenTenBase / PG-XL](solutions/opentenbase_pgxl.md) | Référence architecturale |
| **#9** | Bucardo 5 (`bucardo`, Daemon PL/PerlU) | [#9 — Bucardo 5](solutions/bucardo.md) | Benchmarké (`N4`) |
| **#10** | SymmetricDS (`sym_data` lots HTTP Java) | [#10 — SymmetricDS](solutions/symmetricds.md) | Référence architecturale |
| **#11** | PgPool-II (Streaming LB/HA vs Native Replication/SI) | [#11 — PgPool-II](solutions/pgpool_ii.md) | Référence architecturale |
| **#12** | AWS Aurora PostgreSQL Limitless (& MM v1) | [#12 — AWS Aurora Limitless](solutions/aws_aurora_limitless.md) | Référence architecturale |
| **#13** | Google Cloud Spanner (PG Interface) & AlloyDB | [#13 — GCP Spanner & AlloyDB](solutions/gcp_spanner_alloydb.md) | Référence architecturale |
| **#14** | Systèmes historiques à triggers (Slony-I, Londiste, RubyRep) | [#14 — Triggers historiques (EOL)](solutions/legacy_triggers.md) | Référence architecturale |

---

## #5 YugabyteDB (YSQL + DocDB Raft)

**Fiche dédiée :** [#5 — YugabyteDB (`yugabyte`)](solutions/yugabytedb.md)

**Architecture** : YugabyteDB réutilise directement les couches supérieures de PostgreSQL en C (parseur, optimiseur et exécuteur SQL) au sein du moteur **YSQL**, adossé au système de stockage distribué **DocDB** (C++, basé sur RocksDB/LSM). Chaque table est fragmentée en *tablets* répliqués de façon synchrone par **Raft** (facteur de réplication `RF = 3` standard) avec horloges hybrides **HLC** (*Hybrid Logical Clocks*).

**Concurrence et limites** : Le consensus Raft élimine les conflits asynchrones et assure `RPO = 0` si un nœud sur trois tombe. Le quorum gèle si deux nœuds sur trois tombent (`PC/EC`). Supporte `Serializable`, `Snapshot` et `Read Committed` (mode wait-on-conflict).

Sous forte contention, les transactions concurrentes reçoivent `SQLSTATE 40001` et demandent des reprises client. La base SQL PostgreSQL autorise `pg_trgm`, `uuid-ossp` et `pgvector`, tout en restant soumise au RTT inter-nœuds et à la RAM.

---

## #6 CockroachDB (PG-wire + Pebble Raft)

**Fiche dédiée :** [#6 — CockroachDB (`cockroach`)](solutions/cockroachdb.md)

**Architecture** : Écrit en Go, CockroachDB implémente le protocole filaire PostgreSQL v3 par-dessus un moteur clé-valeur ordonné **Pebble**. Les données sont découpées en *ranges* contigus (64 à 512 Mio) répliqués par **Raft**, avec un *leaseholder* chargé des lectures locales cohérentes et de la coordination des écritures.

**Concurrence et limites** : Par défaut en isolation stricte `SERIALIZABLE` (avec option `READ COMMITTED` en v24.x), CockroachDB assure une linéarisabilité multi-régions avec HLC et écritures d'intentions 2PC. Toute contention concurrente ou ambiguïté d'horloge déclenche `SQLSTATE 40001`, imposant des ré-essais applicatifs explicites. Des clauses natives (`SURVIVAL GOAL = ZONE | REGION`, `REGIONAL BY ROW`) optimisent le placement des *leaseholders*. En contrepartie, **aucune extension C PostgreSQL ne fonctionne** (`PostGIS` absent, seul un module Go partiel existe). `CHANGEFEED` Kafka/webhook remplace `LISTEN/NOTIFY`, et l'absence de WAL rompt la compatibilité `pgBackRest`.

---

## #7 Citus (Sharding MPP sur PostgreSQL)

**Fiche dédiée :** [#7 — Citus (`citus`)](solutions/citus.md)

**Architecture** : Extension C open-source (AGPLv3) pour PostgreSQL 17 distribuant les requêtes entre un **coordinateur** et des nœuds **workers**. Les tables se classent en trois catégories :
1. **Tables distribuées** : partitionnées par hachage sur une colonne clé (`create_distributed_table`). Les requêtes filtrant cette clé ciblent un shard unique sans 2PC.
2. **Tables de référence** : répliquées sur tous les workers et synchronisées par **2PC** (`create_reference_table`).
3. **Tables locales** : résidentes sur le coordinateur seul. Le mode **Citus MX** permet d'exposer aussi les workers comme points d'entrée SQL.

**Limites vérifiables** : Toute clé primaire ou index `UNIQUE` sur une table distribuée doit contenir la colonne de distribution, faute de quoi Citus rejette la création avec `SQLSTATE 0A000`. Une table sans clé primaire est tolérée en insertion mais reste impossible à indexer en contrainte partielle sans clé de sharding. Enfin, Citus n'assure pas la réplication inter-workers par défaut : la perte d'un worker bloque l'accès à ses shards jusqu'à son redémarrage (d'où la nécessité d'associer chaque worker à une HA Patroni en production).

---

## #8 OpenTenBase / Postgres-XL / Postgres-XC

**Fiche dédiée :** [#8 — OpenTenBase / Postgres-XL / XC (Référence architecturale)](solutions/opentenbase_pgxl.md)

**Architecture** : Famille MPP *shared-nothing* combinant coordinateurs sans état et *datanodes* PostgreSQL. Un **GTM (*Global Transaction Manager*)** centralise les `GXID` et instantanés MVCC pour assurer l'ACID distribué par 2PC.

**Statut et limites** : Le GTM introduit un point de contention critique sous fort taux de transactions courtes (chaque `BEGIN`/`COMMIT` sollicitant le GTM par réseau). **Postgres-XC** et **Postgres-XL** sont aujourd'hui considérés comme abandonnés/gelés sur d'anciens noyaux PG 9.x/10. **OpenTenBase** (maintenu par la communauté, fork PG 10–11 avec rétroportages) demeure pertinent pour l'entreposage analytique HTAP/MPP massif, mais peu adapté à l'OLTP géo-distribué léger.

---

## #9 Bucardo 5 (Daemon Perl asynchrone)

**Fiche dédiée :** [#9 — Bucardo 5 (`bucardo`)](solutions/bucardo.md)

**Architecture** : Daemon Perl externe pilotant une réplication par lots avec des déclencheurs `PL/pgSQL` générés sur chaque table. Chaque modification alimente une table tampon `bucardo_delta` sur la base source, tandis qu'une base de contrôle requiert `PL/Perl`.

**Conflits et limites** : Supporte les topologies multi-maîtres (`dbgroup` à plusieurs sources) avec résolution configurable (`bucardo_latest`, `bucardo_source`, `bucardo_target`, `bucardo_skip`). Limites majeures : chaque table exige une PK ou clé unique, et chaque écriture alimente `bucardo_delta` (nécessitant des `VACUUM` fréquents). La scrutation ajoute une latence visible et le DDL ne se propage pas.

---

## #10 SymmetricDS (Agent Java hétérogène)

**Fiche dédiée :** [#10 — SymmetricDS (Référence architecturale)](solutions/symmetricds.md)

**Architecture** : Plateforme Java asynchrone capturant les changements par triggers SQL vers `sym_data`, puis poussant les lots par HTTP/HTTPS.

**Cas d'usage et limites** : Référence incontournable lorsque l'architecture exige une synchronisation **hétérogène** (PostgreSQL vers MySQL, Oracle, SQL Server ou SQLite) ou une connectivité intermittente de type *Edge / Retail* avec résilience hors-ligne prolongée. En revanche, la double écriture par triggers et HTTP ajoutent latence et charge CPU. Ce coût pénalise un cœur OLTP homogène PostgreSQL.

---

## #11 PgPool-II (Mode Native Replication / Snapshot Isolation)

**Fiche dédiée :** [#11 — PgPool-II (Référence architecturale / PoC Streaming)](solutions/pgpool_ii.md)

**Architecture** : Proxy middleware placé devant les instances PostgreSQL. Historiquement doté d'un mode *Native Replication* (diffusion de chaque requête SQL d'écriture à tous les nœuds) complété par le mode *Snapshot Isolation* (SI) pour ordonner la visibilité transactionnelle.

**Limites critiques** : La réplication par diffusion d'instructions SQL est structurellement fragile : toute fonction non déterministe (`NOW()`, `CURRENT_TIMESTAMP`, `RANDOM()`, génération d'UUID aléatoire ou invocation dans un trigger/valeur par défaut) risque de produire des valeurs divergentes entre nœuds malgré les réécritures syntaxiques du parseur PgPool-II. De plus, deux `UPDATE` concurrents sans verrouillage global risquent d'être exécutés dans des ordres opposés. En production moderne, PgPool-II s'emploie en mode **Streaming Replication** (mono-primaire + répartition des lectures), jamais en multi-maîtres actif-actif.

---

## #12 AWS Aurora PostgreSQL Limitless (& historique Multi-Master)

**Fiche dédiée :** [#12 — AWS Aurora PostgreSQL Limitless (& MM v1)](solutions/aws_aurora_limitless.md)

**Distinction architecturale** : L'ancien service **Aurora Multi-Master** (historiquement limité à MySQL 5.6 et désormais retiré par AWS) n'a jamais proposé de multi-écrivains symétrique sur PostgreSQL. Pour la mise à l'échelle horizontale des écritures PostgreSQL, AWS propose **Aurora PostgreSQL Limitless Database** : des routeurs sans état distribuent les transactions vers des *shards* PostgreSQL synchronisés par une horloge distribuée AWS et stockés sur le stockage distribué multi-AZ Aurora. En scénario multi-régions, **Aurora Global Database** repose sur un unique écrivain primaire complété par le *Write Forwarding* (acheminant les écritures depuis une région secondaire vers le primaire sur réseau privé AWS). Architecture propriétaire strictement liée au cloud AWS.

---

## #13 Google Cloud Spanner (PG Interface) & AlloyDB

**Fiche dédiée :** [#13 — GCP Spanner (PG Interface) & AlloyDB](solutions/gcp_spanner_alloydb.md)

**Google Cloud Spanner** associe **Paxos** synchrone et horloges **TrueTime** ($\epsilon_{\text{clock}} < 7\text{ ms}$) pour une **cohérence externe** globale sans conflit. Son interface **PostgreSQL dialect** expose le protocole filaire et un SQL proche de PostgreSQL. Elle exclut toutefois les extensions C (`PostGIS`, `pg_trgm`), les triggers avancés et PL/pgSQL complet, à coût élevé. **AlloyDB for PostgreSQL** accélère le mono-primaire avec un stockage désagrégé (*log-processing storage*) et des pools de lecture élastiques, sans écriture multi-maîtres.

---

## #14 Systèmes historiques à triggers : RubyRep, Slony-I, Londiste

**Fiche dédiée :** [#14 — Systèmes historiques à triggers (EOL)](solutions/legacy_triggers.md)

Ces trois outils illustrent la génération antérieure à PostgreSQL 9.4 (avant l'arrivée des *logical decoding plugins*) :
- **RubyRep** : outil Ruby open-source de comparaison et réplication bidirectionnelle par triggers. Abandonné, limité par l'interpréteur et les verrous au rattrapage.
- **Slony-I** : réplication asynchrone mono-maître vers cascades de réplicas par triggers C/SQL. Fiable pour les migrations PG historiques, mais inapte au multi-maîtres.
- **Londiste (Skytools)** : file asynchrone **PgQ** par triggers SQL, conçue pour le mono-maître asynchrone et certaines topologies en étoile, aujourd'hui supplantée par la réplication logique native et Spock.

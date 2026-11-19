# Catalogue des solutions : SQL distribué, MPP, triggers et Cloud

> **Auteur** : Jean-Marie Renouard (`jmrenouard`) - [LightPath](https://www.lightpath.fr) | **Licence** : MIT

Ce chapitre présente les moteurs SQL distribués à consensus (`#5`–`#6`), le sharding MPP (`#7`–`#8`), la capture par triggers et proxys (`#9`–`#11`, `#14`) et les services cloud managés (`#12`–`#13`).

---

## #5 YugabyteDB (YSQL + DocDB Raft)

**Architecture** : YugabyteDB réutilise directement les couches supérieures de PostgreSQL en C (parseur, optimiseur et exécuteur SQL) au sein du moteur **YSQL**, adossé au système de stockage distribué **DocDB** (C++, basé sur RocksDB/LSM). Chaque table est fragmentée en *tablets* répliqués de façon synchrone par **Raft** (facteur de réplication `RF = 3` standard) avec horloges hybrides **HLC** (*Hybrid Logical Clocks*).

**Concurrence et limites** : Le consensus Raft élimine les conflits asynchrones et garantit `RPO = 0` lors de la perte d'un nœud sur trois, au prix d'un arrêt total de quorum si deux nœuds sur trois tombent (`PC/EC`). Supporte `Serializable`, `Snapshot` et `Read Committed` (mode wait-on-conflict). Sous forte contention sur une même ligne, les transactions concurrentes reçoivent `SQLSTATE 40001` (*serialization/conflict error*) et requièrent une boucle de ré-essai côté client. La réutilisation du code PostgreSQL autorise de nombreuses extensions (`pg_trgm`, `uuid-ossp`, `pgvector`), bien que les sémantiques distribuées restent soumises au coût RTT inter-nœuds et à une empreinte RAM élevée par processus.

---

## #6 CockroachDB (PG-wire + Pebble Raft)

**Architecture** : Écrit en Go, CockroachDB implémente le protocole filaire PostgreSQL v3 par-dessus un moteur clé-valeur ordonné **Pebble**. Les données sont découpées en *ranges* contigus (64 à 512 Mio) répliqués par **Raft**, avec un *leaseholder* chargé des lectures locales cohérentes et de la coordination des écritures.

**Concurrence et limites** : Par défaut en isolation stricte `SERIALIZABLE` (avec option `READ COMMITTED` en v24.x), CockroachDB assure une linéarisabilité multi-régions via HLC et écritures d'intentions 2PC. Toute contention concurrente ou ambiguïté d'horloge déclenche `SQLSTATE 40001`, imposant des ré-essais applicatifs explicites. Des clauses natives (`SURVIVAL GOAL = ZONE | REGION`, `REGIONAL BY ROW`) optimisent le placement des *leaseholders*. En contrepartie, **aucune extension C PostgreSQL n'est compatible** (`PostGIS` absent, seul un module spatial Go partiel est fourni), `LISTEN/NOTIFY` est remplacé par des `CHANGEFEED` Kafka/webhook, et l'absence de stockage WAL classique rompt la compatibilité avec les outils de sauvegarde PG (`pgBackRest`).

---

## #7 Citus (Sharding MPP sur PostgreSQL)

**Architecture** : Extension C open-source (AGPLv3) pour PostgreSQL 17 distribuant les requêtes entre un **coordinateur** et des nœuds **workers**. Les tables se classent en trois catégories :
1. **Tables distribuées** : partitionnées par hachage sur une colonne clé (`create_distributed_table`) ; les requêtes filtrant sur cette clé ciblent un shard unique sans 2PC.
2. **Tables de référence** : répliquées intégralement sur tous les workers et maintenues synchrones via **2PC** (`create_reference_table`).
3. **Tables locales** : résidentes sur le coordinateur seul. Le mode **Citus MX** permet d'exposer aussi les workers comme points d'entrée SQL.

**Limites vérifiables** : Toute clé primaire ou index `UNIQUE` sur une table distribuée doit contenir la colonne de distribution, faute de quoi Citus rejette la création avec `SQLSTATE 0A000`. Une table sans clé primaire est tolérée en insertion mais reste impossible à indexer en contrainte partielle sans clé de sharding. Enfin, Citus n'assure pas la réplication inter-workers par défaut : la perte d'un worker bloque l'accès à ses shards jusqu'à son redémarrage (d'où la nécessité d'associer chaque worker à une HA Patroni en production).

---

## #8 OpenTenBase / Postgres-XL / Postgres-XC

**Architecture** : Famille MPP *shared-nothing* composée de coordinateurs sans état, de *datanodes* PostgreSQL et d'un **GTM (*Global Transaction Manager*)** centralisant l'attribution des `GXID` et des instantanés MVCC globaux pour maintenir une cohérence ACID distribuée par 2PC.

**Statut et limites** : Le GTM introduit un point de contention critique sous fort taux de transactions courtes (chaque `BEGIN`/`COMMIT` sollicitant le GTM par réseau). **Postgres-XC** et **Postgres-XL** sont aujourd'hui considérés comme abandonnés/gelés sur d'anciens noyaux PG 9.x/10. **OpenTenBase** (maintenu par la communauté sur PG 10/14) demeure pertinent pour l'entreposage analytique HTAP/MPP massif, mais peu adapté à l'OLTP géo-distribué léger.

---

## #9 Bucardo 5 (Daemon Perl asynchrone)

**Architecture** : Daemon Perl externe pilotant une réplication asynchrone par lots via des déclencheurs `PL/pgSQL` générés automatiquement sur chaque table surveillée. Chaque modification alimente une table tampon `bucardo_delta` sur la base source, tandis qu'une base de contrôle requiert `PL/Perl`.

**Conflits et limites** : Supporte les topologies multi-maîtres (`dbgroup` à plusieurs sources) avec résolution configurable (`bucardo_latest`, `bucardo_source`, `bucardo_target`, `bucardo_skip`). Limites majeures : obligation stricte d'une clé primaire ou unique sur chaque table (les tables sans PK sont ignorées ou refusées), amplification I/O d'écriture (chaque `INSERT`/`UPDATE`/`DELETE` déclenche une écriture supplémentaire dans `bucardo_delta` nécessitant des purges `VACUUM` fréquentes), latence de réplication liée au cycle d'interrogation et absence totale de propagation DDL.

---

## #10 SymmetricDS (Agent Java hétérogène)

**Architecture** : Plateforme Java asynchrone capturant les changements via triggers SQL vers une table `sym_data`, encapsulés en lots compressés transmis par HTTP/HTTPS.

**Cas d'usage et limites** : Référence incontournable lorsque l'architecture exige une synchronisation **hétérogène** (PostgreSQL vers MySQL, Oracle, SQL Server ou SQLite) ou une connectivité intermittente de type *Edge / Retail* avec résilience hors-ligne prolongée. En revanche, la double écriture par triggers et la sérialisation HTTP créent une latence et un surcoût CPU prohibitifs pour un cœur OLTP homogène PostgreSQL à fort débit.

---

## #11 PgPool-II (Mode Native Replication / Snapshot Isolation)

**Architecture** : Proxy middleware placé devant les instances PostgreSQL. Historiquement doté d'un mode *Native Replication* (diffusion de chaque requête SQL d'écriture à tous les nœuds) complété par le mode *Snapshot Isolation* (SI) pour ordonner la visibilité transactionnelle.

**Limites critiques** : La réplication par diffusion d'instructions SQL est structurellement fragile : toute fonction non déterministe (`NOW()`, `CURRENT_TIMESTAMP`, `RANDOM()`, génération d'UUID aléatoire ou invocation dans un trigger/valeur par défaut) risque de produire des valeurs divergentes entre nœuds malgré les réécritures syntaxiques du parseur PgPool-II. De plus, deux `UPDATE` concurrents sans verrouillage global risquent d'être exécutés dans des ordres opposés. En production moderne, PgPool-II s'emploie en mode **Streaming Replication** (mono-primaire + répartition des lectures), jamais en multi-maîtres actif-actif.

---

## #12 AWS Aurora PostgreSQL Limitless (& historique Multi-Master)

**Distinction architecturale** : L'ancien service **Aurora Multi-Master** (historiquement limité à MySQL 5.6 et désormais retiré par AWS) n'a jamais proposé de multi-écrivains symétrique sur PostgreSQL. Pour la mise à l'échelle horizontale des écritures PostgreSQL, AWS propose **Aurora PostgreSQL Limitless Database** : des routeurs sans état distribuent les transactions vers des *shards* PostgreSQL synchronisés par une horloge distribuée AWS et stockés sur le stockage distribué multi-AZ Aurora. En scénario multi-régions, **Aurora Global Database** repose sur un unique écrivain primaire complété par le *Write Forwarding* (acheminant les écritures depuis une région secondaire vers le primaire via réseau privé AWS). Architecture propriétaire strictement liée au cloud AWS.

---

## #13 Google Cloud Spanner (PG Interface) & AlloyDB

**Google Cloud Spanner** associe consensus **Paxos** synchrone et horloges atomiques/GPS **TrueTime** ($\epsilon_{\text{clock}} < 7\text{ ms}$) pour garantir une **cohérence externe** globale sans anomalie de lecture périmée ni conflit silencieux. Son interface **PostgreSQL dialect** expose le protocole filaire et une syntaxe SQL proche de PostgreSQL, mais sans compatibilité avec les extensions C PostgreSQL (`PostGIS`, `pg_trgm` natif), les triggers avancés ou PL/pgSQL complet, et à un coût managé élevé. **AlloyDB for PostgreSQL** accélère quant à lui l'architecture mono-primaire grâce à un stockage désagrégé optimisé (*log-processing storage*) et des pools de lecture élastiques (plus *AlloyDB Omni* en conteneur), sans offrir d'écriture multi-maîtres symétrique.

---

## #14 Systèmes historiques à triggers : RubyRep, Slony-I, Londiste

Ces trois outils illustrent la génération antérieure à PostgreSQL 9.4 (avant l'arrivée des *logical decoding plugins*) :
- **RubyRep** : outil Ruby open-source de comparaison et réplication bidirectionnelle asynchrone par triggers ; projet abandonné, limité par le coût de l'interpréteur et les verrous de table lors du rattrapage.
- **Slony-I** : réplication asynchrone mono-maître vers cascades de réplicas par triggers C/SQL ; fiable historiquement pour des montées de version PG sans arrêt, mais incapable d'écriture multi-maîtres.
- **Londiste (Skytools)** : file asynchrone **PgQ** par triggers SQL, conçue pour le mono-maître asynchrone et certaines topologies en étoile, aujourd'hui supplantée par la réplication logique native et Spock.

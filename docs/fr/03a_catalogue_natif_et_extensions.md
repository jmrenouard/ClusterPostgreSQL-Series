# Catalogue des solutions : natif PostgreSQL, extensions et baselines

> **Auteur** : Jean-Marie Renouard (`jmrenouard`) - [LightPath](https://www.lightpath.fr) | **Licence** : MIT

Ce chapitre analyse les solutions directement ancrées dans le noyau ou l'API C d'extension PostgreSQL (`#1` à `#4`, `#16` logique unidirectionnelle) ainsi que les références de contrôle mono-primaire (`#15a` et `#15b`).

## Fiches d'architecture détaillées (périmètre `03a`)

| ID | Solution / Topologie | Fiche FR dédiée | Périmètre |
| :---: | :--- | :--- | :--- |
| **#1** | PG 17 Logique bidirectionnelle native (`pg-birep`) | [#1 — PG 17 Logique bidirectionnelle](solutions/pg17_bidirectional_logical.md) | Benchmarké (`N4`) |
| **#2** | pgEdge Platform / Spock v5 (`pgedge`, `pgedge-delta-apply`) | [#2 — pgEdge / Spock v5](solutions/pgedge_spock.md) | Benchmarké (`N4`, CRDT) |
| **#3** | pglogical 2 | [#3 — pglogical 2](solutions/pglogical2.md) | Référence architecturale |
| **#4** | EDB Postgres Distributed (PGD / BDR) | [#4 — EDB PGD](solutions/edb_pgd.md) | Référence architecturale |
| **#15a** | PG 17 Standalone (`pg17-standalone`) | [#15a — PG 17 Standalone](solutions/pg17_standalone.md) | Benchmarké (`N1` contrôle) |
| **#15b** | PG 17 Streaming physique & Patroni HA (`pg17-async/sync-streaming`) | [#15b — PG 17 Streaming & Patroni](solutions/pg17_physical_streaming_patroni.md) | Benchmarké (`N1`/`N2`) |
| **#16** | PG 17 Logique unidirectionnelle native (`pg17-logical`) | [#16 — PG 17 Logique unidirectionnelle](solutions/pg17_logical_unidirectional.md) | Benchmarké (`N3`) |

---

## #1 PostgreSQL 16/17/18 Réplication logique bidirectionnelle native

**Fiche dédiée :** [#1 — PG 17 Réplication logique bidirectionnelle native (`pg-birep`)](solutions/pg17_bidirectional_logical.md)

### Architecture et mécanismes internes
Depuis PostgreSQL 16, le cœur natif permet de créer une réplication logique bidirectionnelle sans boucle infinie grâce au paramètre de souscription `origin = none`. Lorsqu'un éditeur décode son WAL (`wal_level = logical` via le plugin `pgoutput`), chaque transaction reçue d'un pair porte un identifiant d'origine dans `pg_replication_origin`. En configurant `CREATE SUBSCRIPTION ... WITH (origin = none)`, l'*apply worker* du destinataire n'émet vers ses propres abonnés que les transactions générées localement (`origin IS NULL`). L'activation de `track_commit_timestamp = on` permet de tracer l'horodatage de validation des tuples.

### Conflits, DDL et séquences
- **Conflits** : PostgreSQL 17 ne propose pas de résolution automatique des conflits Write-Write ou Insert-Insert. Dès qu'une insertion distante viole une clé primaire ou un index `UNIQUE`, le worker lève `SQLSTATE 23505` (`duplicate key value`) et **interrompt la souscription** (`apply_error_count` incrémenté dans `pg_stat_subscription_stats`). L'administrateur doit supprimer la ligne conflictuelle ou sauter le LSN fautif via `ALTER SUBSCRIPTION ... SKIP (lsn = '...')`.
- **Tables sans clé primaire** : Avec `REPLICA IDENTITY DEFAULT`, un `INSERT` est répliqué, mais tout `UPDATE` ou `DELETE` est bloqué côté éditeur avec `SQLSTATE 55000`. Une clé primaire (ou `REPLICA IDENTITY FULL`, très coûteux en WAL) est obligatoire.
- **DDL et séquences** : Aucun DDL (`CREATE TABLE`, `ALTER TABLE`) n'est propagé automatiquement, hormis `TRUNCATE` si inclus dans la publication. Les valeurs de séquences `SERIAL`/`IDENTITY` ne sont pas répliquées en mode multi-maîtres sous PG 17 ; il faut recourir à des séquences à pas décalés (`INCREMENT BY N START WITH k`) ou à des UUID.

### Bilan (#1)
- **Avantages** : 100 % open-source, aucune extension tierce, compatibilité native complète avec PostgreSQL 17, surcharge nulle en écriture locale.
- **Limites** : Aucune tolérance automatique aux conflits (blocage complet du flux sur `23505`), aucune propagation DDL, zéro gestion native du *Lost Update* sur `balance = balance + delta`.

---

## #2 pgEdge Platform / Spock v5 (Open-Source)

**Fiche dédiée :** [#2 — pgEdge Platform / Spock v5 (`pgedge`, `pgedge-delta-apply`)](solutions/pgedge_spock.md)

### Architecture et mécanismes internes
**pgEdge** assemble un écosystème open-source (licence PostgreSQL) conçu pour le multi-maîtres géo-distribué sur PG 16/17 autour de trois extensions C :
1. **`spock`** : moteur de réplication logique multi-nœuds (successeur open-source de `pglogical`).
2. **`snowflake`** : générateur d'identifiants 64 bits sans coordination globale combinant horodatage, compteur séquentiel et `snowflake.node` (1 à 1023).
3. **`lolor`** : réplication des *Large Objects* PostgreSQL (`pg_largeobject`) via une table dédiée contournant l'absence de décodage logique natif des LOB.

### Conflits, DDL et Delta-Apply CRDT
- **Résolution LWW** : `spock.conflict_resolution = 'last_update_wins'` compare le `commit_timestamp` local et distant ; le perdant est consigné dans `spock.exception_log` selon `spock.exception_behaviour` (`transdiscard`, `discard`, `sub_disable`) sans figer le pipeline logique.
- **Delta-Apply CRDT** : Sur des colonnes numériques déclarées en résolution delta, Spock capture l'image *avant* et *après* dans le WAL afin de rejouer uniquement l'écart $\Delta = v_{\text{new}} - v_{\text{old}}$ sur le pair. Deux écritures concurrentes `+100` et `-30` sur un solde initial de `1000` convergent ainsi exactement vers `1070`, éliminant le *Lost Update* classique du LWW.
- **Auto-DDL** : Avec `spock.enable_ddl_replication = on`, les commandes DDL sont capturées par déclencheur d'événement et propagées automatiquement aux pairs du *repset*.

### Bilan (#2)
- **Avantages** : Pile purement open-source, Delta-Apply natif pour les compteurs, séquences Snowflake intégrées, Auto-DDL fonctionnel et gestion non bloquante des exceptions.
- **Limites** : Modèle **PA/EL** asynchrone : les écritures simultanées sur colonnes non-CRDT restent exposées à la dérive d'horloge NTP ($\Delta t_{\text{skew}}$) et aux inversions de FK sur maillage à $\ge 3$ nœuds.

---

## #3 pglogical 2 (Open-Source)

**Fiche dédiée :** [#3 — pglogical 2 (Référence architecturale)](solutions/pglogical2.md)

### Architecture et mécanismes internes
Développé historiquement par 2ndQuadrant, **pglogical 2** a préfiguré la réplication logique intégrée à PostgreSQL 10. L'extension s'appuie sur des *replication sets* (`default`, `default_insert_only`, `ddl_sql`) et un protocole binaire personnalisé transitant par `wal_level = logical` et des *output plugins* C dédiés.

### Conflits, DDL et séquences
- **Conflits** : Le paramètre `pglogical.conflict_resolution` offre cinq modes (`error`, `apply_remote`, `keep_local`, `last_update_wins`, `first_update_wins`), s'appuyant sur `track_commit_timestamp = on`. Aucun mécanisme *Delta-Apply* CRDT n'existe nativement : les opérations `balance = balance + delta` concurrentes subissent le *Lost Update* en mode LWW.
- **DDL et séquences** : La propagation DDL n'est pas transparente ; elle exige d'encapsuler explicitement les ordres dans `pglogical.replicate_ddl_command('...')`. Les séquences peuvent être synchronisées périodiquement mais restent exposées aux collisions sans décalage par pas.

### Bilan (#3)
- **Avantages** : Historique éprouvé, filtrage fin par lignes/colonnes et compatibilité sur d'anciennes versions PostgreSQL (migrations majeures sans interruption).
- **Limites** : Maintien ralenti face aux versions PG 17+, absence de CRDT/Delta-Apply, propagation DDL manuelle. Pour de nouveaux déploiements, Spock (`#2`) ou PGD (`#4`) lui succèdent directement.

---

## #4 EDB Postgres Distributed / PGD v5-v6 (Commercial / Propriétaire)

**Fiche dédiée :** [#4 — EDB Postgres Distributed / BDR (Référence architecturale)](solutions/edb_pgd.md)

> [!NOTE]
> **Statut commercial** : EDB Postgres Distributed (PGD, anciennement **BDR** - *Bi-Directional Replication*) est une solution **propriétaire et commerciale** soumise à licence EnterpriseDB.

### Architecture et mécanismes internes
PGD étend le noyau PostgreSQL (ou *EDB Postgres Extended*) par une couche de consensus **Raft** embarquée entre nœuds, orchestrée par *PGD Proxy* (routage *Always-On* vers un *Write Leader* élu par région ou globalement). L'architecture permet d'associer au sein d'une même grappe des liaisons asynchrones inter-régions et des sous-groupes synchrones intra-région.

### Conflits, modes de commit et DDL
- **Modèles configurables** :
  - *Asynchrone optimiste* avec types **CRDT** intégrés (`bdr.crdt_gcounter`, `bdr.crdt_pncounter`, `bdr.crdt_delta_counter`, `bdr.crdt_delta_sum`) et résolution LWW auditée dans `bdr.conflict_history`.
  - **Write-Lead** : toutes les écritures d'une table ou d'un groupe convergent vers un leader Raft élu, éliminant les conflits Write-Write tout en assurant une reprise automatisée.
  - **Eager All-Node** : validation synchrone globale garantissant l'absence totale de conflit au prix de la latence RTT multi-nœuds.
  - **CAMO (*Commit At Most Once*)** : protège les transactions contre le double envoi client lors d'une coupure en cours de commit.
- **DDL et séquences** : Propagation DDL automatique coordonnée par verrous distribués Raft (nécessitant l'atteinte du quorum pour valider un `ALTER TABLE`), et `bdr.global_sequences` (`snowflakeid` recommandé, `galloc` par lots alloués via Raft et `timeshard` hérité).

### Bilan (#4)
- **Avantages** : Plateforme multi-maîtres PostgreSQL la plus complète du marché sur le plan fonctionnel (Raft + CRDT + CAMO + Auto-DDL + proxy intégré).
- **Limites** : Coût de licence entreprise élevé par vCPU, verrouillage fournisseur sur l'outillage propriétaire et sensibilité du verrouillage DDL global si un nœud du quorum est déconnecté.

---

## #15 Baselines de contrôle : PG 17 Standalone & Patroni HA Mono-Primaire

**Fiches dédiées :** [#15a — PG 17 Standalone](solutions/pg17_standalone.md) · [#15b — PG 17 Streaming physique & Patroni HA](solutions/pg17_physical_streaming_patroni.md)

### Architecture de référence
Pour juger objectivement l'apport ou le coût d'une architecture multi-maîtres, deux références mono-écrivains servent d'étalon :
1. **PostgreSQL 17 Standalone** : nœud unique local, mesure le plafond brut matériel sans aucune latence réseau de réplication.
2. **Patroni + etcd + HAProxy (HA Mono-Primaire)** : grappe de 3 nœuds PostgreSQL en réplication physique WAL (`streaming replication`), arbitrée par un quorum **etcd** à 3 nœuds et exposée via un routeur **HAProxy** interrogeant les endpoints REST Patroni (`/primary`, `/replica`).

### Cohérence et limites du mono-primaire
Dans une grappe Patroni avec `synchronous_commit = on` (ou `remote_apply`), un seul nœud traite l'ensemble des écritures. Les invariants PostgreSQL (`SERIAL`, index `UNIQUE`, clés étrangères, `pg_advisory_lock`, `LISTEN/NOTIFY`, triggers, tables sans PK, `SAVEPOINT`, extensions `PostGIS`/`pgvector`) fonctionnent **à 100 % sans aucune restriction ni conflit Write-Write**. En revanche :
- La perte du primaire impose un temps de bascule ($\text{RTO} \approx 10\text{--}30\text{ s}$) le temps d'expirer le bail TTL `etcd`, promouvoir un standby et basculer les connexions HAProxy.
- Toutes les écritures géo-distribuées doivent traverser le WAN jusqu'à l'unique région primaire, pénalisant la latence des utilisateurs distants.

### Bilan (#15)
- **Avantages** : Simplicité opérationnelle, zéro anomalie de convergence, `RPO = 0` en mode synchrone intra-région, compatibilité totale avec l'écosystème PostgreSQL.
- **Limites** : Plafond de montée en charge vertical sur un unique écrivain et latence d'écriture intercontinentale incompressible vers le nœud primaire.

---

## #16 PostgreSQL 17 Réplication logique native unidirectionnelle (Pub/Sub)

**Fiche dédiée :** [#16 — PG 17 Réplication logique native unidirectionnelle (`pg17-logical`)](solutions/pg17_logical_unidirectional.md)

### Architecture et limites (`N3`)
Intégrée au noyau via `wal_level = logical` et le plugin `pgoutput`, la réplication unidirectionnelle `PUBLICATION` / `SUBSCRIPTION` diffuse les mutations de lignes (`INSERT`/`UPDATE`/`DELETE`) d'un éditeur unique vers un ou plusieurs abonnés accessibles en écriture (`PA/EL`, niveau `N3`) :
- **Filtrage et montées de version sans coupure** : prend en charge les sous-ensembles de tables, filtres `WHERE`, listes de colonnes et la réplication entre versions majeures distinctes (`PG 15 -> 17 -> 18`), contrairement au streaming physique par blocs.
- **Absence de DDL automatique et tables sans PK** : les commandes DDL ne se propagent pas automatiquement ; les opérations `UPDATE` et `DELETE` sur une table sans clé primaire échouent côté éditeur (`SQLSTATE 55000`) sans `REPLICA IDENTITY FULL`.
- **Piège des séquences (`SQLSTATE 23505`)** : l'état des séquences (`nextval()`) n'est pas répliqué nativement (`last_value` reste à `1|false` sur l'abonné en `T18`), provoquant une collision `23505` lors d'une bascule en écriture sans `setval()` ou clés UUID/Snowflake.

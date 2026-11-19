# 03b — Solution Monographs: Distributed SQL, Triggers & Cloud

**Series:** PostgreSQL Multi-Master & Active-Active Architectures  
**Author:** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr)  
**License:** MIT License

---

## Solution #5: YugabyteDB

**Family:** 3 — Distributed Consensus (PG-Wire) | **License:** Open Source (Apache 2.0)

### Architecture & Internals

YugabyteDB pairs a **forked PostgreSQL C query layer (`YSQL`)** with a C++ distributed transactional storage engine (**`DocDB`**) modeled on Google Spanner. Tables are automatically hash- or range-sharded into **tablets**; each tablet forms an independent **Raft consensus group** (typically Replication Factor `RF = 3`) persisted on **RocksDB** LSM-trees rather than PostgreSQL heap files. Every node accepts reads and writes simultaneously (active-active entry), routing operations transparently to the owning tablet Raft leader.

### Concurrency, HLC, DDL & Limits

- **Hybrid Logical Clocks (HLC) & Isolation:** HLC combines physical time (bounded by `--max_clock_skew_usec`, default `500 ms`) with logical counters to order transactions cluster-wide. Under `READ COMMITTED`, YugabyteDB supports **Wait-on-Conflict (Pessimistic)** locking; under `REPEATABLE READ` and `SERIALIZABLE`, conflicting transactions abort with **`SQLSTATE 40001`**, requiring application retry logic.
- **PG Compatibility:** Because YSQL reuses PostgreSQL's C parser, planner, and PL/pgSQL executor, triggers, views, stored procedures, `pg_trgm`, `uuid-ossp`, and `pgvector` work cleanly; only storage-coupled internals (`VACUUM`, `CTID` assumptions, raw heap extensions) differ.
- **Quorum Limits (`PC/EC`):** Survives 1-of-3 node loss with `RPO = 0`; losing 2-of-3 nodes halts tablet writes/linearizable reads immediately.

---

## Solution #6: CockroachDB

**Family:** 3 — Distributed Consensus (PG-Wire) | **License:** Open Source / BSL (Enterprise features licensed)

### Architecture & Internals

CockroachDB implements a **clean-room Go SQL engine** speaking the PostgreSQL wire protocol (`pgwire`), layered over a monotonic KV store backed by **Pebble** (a Go LSM engine) and **Multi-Raft** per 64 MiB **Range**. Each range elects a **Leaseholder** that coordinates strongly consistent reads locally without Raft disk rounds while writes replicate synchronously across the range's Raft quorum.

### Concurrency, Multi-Region & Limits

- **Strict `SERIALIZABLE` & `40001` Retries:** CockroachDB defaults globally to **`SERIALIZABLE`** isolation. Concurrent updates to the same row or overlapping predicate ranges raise **`SQLSTATE 40001`** (`RETRY_WRITE_TOO_OLD`), making client-side retry loops mandatory.
- **Geo-Distributed Primitives:** Native SQL syntax (`ALTER DATABASE ... SURVIVE REGION FAILURE`, `REGIONAL BY ROW`, `GLOBAL` tables) places leaseholders close to users or replicates read-mostly lookup tables broadly.
- **PG Ecosystem Divergence:** Not a PostgreSQL engine fork — zero support for PostgreSQL C extensions (`PostGIS` partial parity only, no `pg_stat_statements` PG parity), non-trivial PL/pgSQL/stored-procedure gaps, and `SERIAL` defaults to `unique_rowid()` (unordered 64-bit IDs) to prevent monotonic range hotspots.

---

## Solution #7: Citus

**Family:** 4 — Sharded MPP / 2PC | **License:** Open Source (AGPLv3)

### Architecture & Internals

Citus is a pure PostgreSQL extension transforming standard PostgreSQL 17 instances into a **Coordinator + Worker** horizontally sharded cluster (`citus_add_node`). Tables are classified as **Hash-Distributed** (partitioned across worker shards by a distribution column such as `account_id`), **Reference Tables** (replicated across all workers via 2PC), or Coordinator-local tables. **Citus MX** propagates shard metadata to workers so applications can issue queries against any node.

### Concurrency, `0A000` Constraint & Limits

- **Distributed 2PC:** Single-shard DML executes directly on one worker with native PG latency. Multi-shard updates and Reference Table writes enforce atomicity via **Two-Phase Commit (`PREPARE TRANSACTION` / `COMMIT PREPARED`)**, requiring `max_prepared_transactions > 0`.
- **Hard Schema Limit (`SQLSTATE 0A000`):** Every `PRIMARY KEY` or `UNIQUE` constraint on a distributed table **must include the distribution column**, or creation fails with `SQLSTATE 0A000`. Cross-shard foreign keys are restricted to colocated tables or reference tables.
- **Availability:** Without streaming HA replicas behind every worker, losing a single worker renders its shards unavailable even though healthy workers and reference reads keep running.

---

## Solution #8: OpenTenBase / Postgres-XL / Postgres-XC

**Family:** 4 — Sharded MPP / 2PC | **License:** Open Source (PostgreSQL / Tencent Apache-style)

### Architecture & Internals

Derived from NTT's **Postgres-XC**, this lineage splits PostgreSQL into stateless **Coordinators**, sharded **Datanodes**, and a centralized **Global Transaction Manager (GTM)** issuing cluster-wide transaction IDs (`GXID`) and global MVCC snapshots for consistent distributed 2PC reads and writes.

### Status & Structural Bottlenecks

- **Maintenance Status:** **Postgres-XC** is retired; **Postgres-XL** has been dormant/unmaintained since ~2018 (frozen on PG 10); **OpenTenBase** (Tencent's active fork of TBase) remains the sole actively maintained open-source descendant.
- **GTM Bottleneck:** Every distributed query and transaction contacts the **GTM** (partially buffered via GTM-Proxy). Across WAN links, GTM network trips amplify latency sharply, making this family better suited to intra-DC OLAP/HTAP MPP than geo-distributed active-active OLTP.

---

## Solution #9: Bucardo 5

**Family:** 5 — Trigger-Based Async Daemons | **License:** Open Source (BSD)

### Architecture & Internals

**Bucardo 5** is an external Perl daemon (`bucardo`) using **PL/Perl** triggers and shadow delta tables (`bucardo_delta`, `bucardo_track`) installed inside each participating PostgreSQL database. Multi-master `sync` tasks group databases as bidirectional sources (`dbgroup` with `db1:source, db2:source`) and wake via PostgreSQL `LISTEN/NOTIFY` or polling intervals.

### Conflicts, PK Constraint & Limits

- **Strict Primary Key Requirement:** Tables without a `PRIMARY KEY` or unique index cannot enter a multi-master sync (raw `pgbench_history` fails setup immediately).
- **Conflict Resolution:** Configurable strategies (`bucardo_latest`, `bucardo_source`, `bucardo_target`, custom Perl hooks) inspect delta timestamps asynchronously.
- **Limits:** High write amplification (every row mutation triggers delta inserts and index writes), no DDL auto-replication, single Perl daemon SPOF, and noticeable batch sync lag compared to WAL logical decoding.

---

## Solution #10: SymmetricDS

**Family:** 5 — Trigger-Based Async Daemons | **License:** Open Source (LGPL) / Pro (Commercial)

### Architecture & Internals

Written in Java, **SymmetricDS** captures row mutations via database triggers into internal staging tables (`sym_data`), groups them into `sym_outgoing_batch` payloads, and pushes batches over HTTP/HTTPS across multi-tier hub-and-spoke or mesh topologies.

### Conflicts & Limits

- **Strengths:** Unrivaled **heterogeneous** multi-master sync (PostgreSQL <-> MySQL <-> SQLite/Oracle) and **intermittent edge connectivity** (retail POS, offline field nodes) with built-in conflict policies (`NEWER_WINS`, `USE_PK_DATA`, `FALLBACK`).
- **Limits:** Trigger write amplification reduces peak OLTP throughput, JVM heap memory footprint adds infrastructure cost, and schema evolution requires explicit `symadmin send-schema` coordination.

---

## Solution #11: PgPool-II (Replication & Snapshot Isolation Modes)

**Family:** 6 — Statement-Broadcast Middleware | **License:** Open Source (BSD)

### Architecture & Internals

**PgPool-II** is a C proxy positioned between clients and PostgreSQL backends. Crucially, its common **Streaming Replication Mode** is single-primary + read standbys (not multi-master). True multi-node writes occur only in two specialized modes:
1. **Native Replication Mode (Statement Broadcast):** Replays every write SQL statement simultaneously onto all backend PostgreSQL nodes.
2. **Snapshot Isolation (SI) Mode:** Adds centralized transaction commit/visibility orchestration inside PgPool-II to ensure backends read consistent cross-node snapshots.

### Critical Non-Determinism Hazard

Statement broadcast breaks silently whenever SQL produces different values across nodes: `NOW()`, `CURRENT_TIMESTAMP`, `RANDOM()`, `gen_random_uuid()`, trigger side-effects, or concurrent `nextval()` interleaving. Although PgPool-II attempts regex timestamp rewriting and table locking (`insert_lock`), stored functions and concurrent workloads frequently trigger silent data divergence or proxy-serialized lock stalls.

---

## Solution #12: AWS Aurora PostgreSQL Limitless Database (& Multi-Master v1)

**Family:** 7 — Cloud-Managed Distributed Engines | **License:** Proprietary (AWS Managed)

### History & Architecture

AWS previously launched **Aurora Multi-Master (v1)** on MySQL (never GA on Aurora PostgreSQL, retired completely in 2024) because cross-writer shared-page invalidation caused severe abort storms under contention. AWS replaced that concept with **Aurora PostgreSQL Limitless Database** (GA 2024): a two-tier sharded engine decoupling **Transaction Routers** from **Data Access Shards** over Aurora's multi-AZ distributed storage, using **AWS Time Sync Service** hardware clocks and 2PC for globally consistent reads and distributed commits. Vendor lock-in and cross-shard 2PC latency remain the primary constraints.

---

## Solution #13: Google Cloud Spanner (PG Interface) & AlloyDB

**Family:** 7 — Cloud-Managed Distributed Engines | **License:** Proprietary (GCP Managed)

### Spanner vs AlloyDB Disambiguation

- **Cloud Spanner (PostgreSQL Interface):** Achieves **External Consistency** across continents via **Multi-Paxos** splits and **TrueTime** (GPS + atomic clocks bounding global uncertainty $\varepsilon < 7\text{ ms}$). Writes wait out $2\varepsilon$ before releasing locks (`commit-wait`), guaranteeing linearizable timestamps without cross-region read locks. However, Spanner's PG Interface supports only a subset of PostgreSQL SQL/types (zero C extensions, limited PL/pgSQL).
- **Google Cloud AlloyDB:** **Not active-active multi-master.** AlloyDB uses a **single primary compute writer** paired with disaggregated Log-Processing Storage and elastic read pools. It belongs in architectural matrices purely to prevent misclassifying shared-storage HA as multi-writer active-active.

---

## Solution #14: Legacy Trigger Systems (RubyRep, Slony-I, Londiste)

**Family:** 5 — Trigger-Based Async Daemons | **License:** Open Source (Historical / EOL)

### Technical Heritage & Retirement Status

- **RubyRep:** Ruby-based bidirectional table-diff and trigger sync; unmaintained, CPU-bound, unsafe for high-concurrency OLTP.
- **Slony-I:** C/SQL trigger replication designed in the 2000s before PG 9.0 streaming replication; **strictly single-origin per replication set** (not multi-master).
- **Londiste (Skytools):** Python daemon consuming `PgQ` trigger queues; scalable batch shipping in its era, now superseded by core PG 10+ `pgoutput` logical replication. None of these three should be selected for new production deployments.

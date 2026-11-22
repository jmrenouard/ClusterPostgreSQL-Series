# 03b — Solution Monographs: Distributed SQL, Triggers & Cloud

**Series:** PostgreSQL Multi-Master & Active-Active Architectures  
**Author:** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr)  
**License:** MIT License

---

## Dedicated Architecture Sheets (`03b` Scope)

| Catalog ID | Solution / Topology | Dedicated EN Sheet | Scope |
| :---: | :--- | :--- | :--- |
| **#5** | YugabyteDB (`yugabyte`, YSQL + DocDB Raft) | [Solution #5 — YugabyteDB](solutions/yugabytedb.md) | Live-benchmarked (`T5`) |
| **#6** | CockroachDB (`cockroach`, PG-Wire + Pebble Multi-Raft) | [Solution #6 — CockroachDB](solutions/cockroachdb.md) | Live-benchmarked (`T5`) |
| **#7** | Citus (`citus`, Coordinator + Workers + 2PC) | [Solution #7 — Citus](solutions/citus.md) | Live-benchmarked (`T5`) |
| **#8** | OpenTenBase / Postgres-XL / Postgres-XC | [Solution #8 — OpenTenBase / PG-XL](solutions/opentenbase_pgxl.md) | Architectural Reference |
| **#9** | Bucardo 5 (`bucardo`, PL/PerlU Trigger Daemon) | [Solution #9 — Bucardo 5](solutions/bucardo.md) | Live-benchmarked (`T4`) |
| **#10** | SymmetricDS (`sym_data` Java HTTP Batch Sync) | [Solution #10 — SymmetricDS](solutions/symmetricds.md) | Architectural Reference |
| **#11** | PgPool-II (Streaming LB/HA vs Native Replication/SI) | [Solution #11 — PgPool-II](solutions/pgpool_ii.md) | Architectural Reference |
| **#12** | AWS Aurora PostgreSQL Limitless (& MM v1) | [Solution #12 — AWS Aurora Limitless](solutions/aws_aurora_limitless.md) | Architectural Reference |
| **#13** | Google Cloud Spanner (PG Interface) & AlloyDB | [Solution #13 — GCP Spanner & AlloyDB](solutions/gcp_spanner_alloydb.md) | Architectural Reference |
| **#14** | Legacy Trigger Systems (Slony-I, Londiste, RubyRep) | [Solution #14 — Legacy Triggers (EOL)](solutions/legacy_triggers.md) | Architectural Reference |

---

## Solution #5: YugabyteDB

**Dedicated Sheet:** [Solution #5 — YugabyteDB (`yugabyte`)](solutions/yugabytedb.md)

**Family:** 3 — Distributed Consensus (PG-Wire) | **License:** Open Source (Apache 2.0)

### Architecture & Internals

YugabyteDB pairs a **forked PostgreSQL C query layer (`YSQL`)** with a C++ distributed transactional storage engine (**`DocDB`**) modeled on Google Spanner. Tables shard automatically by hash or range into **tablets**. Each tablet forms a **Raft consensus group** (typical Replication Factor `RF = 3`) backed by **RocksDB** LSM-trees. Every node accepts reads and writes simultaneously (active-active entry), routing operations transparently to the owning tablet Raft leader.

### Concurrency, HLC, DDL & Limits

- **Hybrid Logical Clocks (HLC) & Isolation:** HLC combines physical time (bounded by `--max_clock_skew_usec`, default `500 ms`) with logical counters to order transactions cluster-wide. Under `READ COMMITTED`, YugabyteDB uses **Wait-on-Conflict (Pessimistic)** locking. Under `REPEATABLE READ` and `SERIALIZABLE`, conflicting transactions abort with **`SQLSTATE 40001`** and require client retries.
- **PG Compatibility:** YSQL reuses PostgreSQL's C parser, planner, and PL/pgSQL executor, so triggers, views, `pg_trgm`, `uuid-ossp`, and `pgvector` work cleanly. Only storage-coupled internals (`VACUUM`, `CTID`, heap extensions) differ.
- **Quorum Limits (`PC/EC`):** Survives 1-of-3 node loss with `RPO = 0`. Losing 2-of-3 nodes halts tablet writes and linearizable reads immediately.

---

## Solution #6: CockroachDB

**Dedicated Sheet:** [Solution #6 — CockroachDB (`cockroach`)](solutions/cockroachdb.md)

**Family:** 3 — Distributed Consensus (PG-Wire) | **License:** Open Source / BSL (Enterprise features licensed)

### Architecture & Internals

CockroachDB implements a **clean-room Go SQL engine** speaking PostgreSQL wire protocol (`pgwire`). It stores ranges per 64 MiB **Range** over **Pebble** (Go LSM) and **Multi-Raft**. Each range elects a **Leaseholder** that coordinates strongly consistent reads locally without Raft disk rounds while writes replicate synchronously across the range's Raft quorum.

### Concurrency, Multi-Region & Limits

- **Strict `SERIALIZABLE` & `40001` Retries:** CockroachDB defaults globally to **`SERIALIZABLE`** isolation. Concurrent updates to the same row or overlapping predicate ranges raise **`SQLSTATE 40001`** (`RETRY_WRITE_TOO_OLD`), making client-side retry loops mandatory.
- **Geo-Distributed Primitives:** Native SQL syntax (`ALTER DATABASE ... SURVIVE REGION FAILURE`, `REGIONAL BY ROW`, `GLOBAL` tables) places leaseholders close to users or replicates read-mostly lookup tables broadly.
- **PG Ecosystem Divergence:** Not a PG kernel fork, so it lacks C extensions (`PostGIS` is partial, no `pg_stat_statements` parity) and has PL/pgSQL gaps. `SERIAL` defaults to `unique_rowid()` (unordered 64-bit IDs) to avoid range hotspots.

---

## Solution #7: Citus

**Dedicated Sheet:** [Solution #7 — Citus (`citus`)](solutions/citus.md)

**Family:** 4 — Sharded MPP / 2PC | **License:** Open Source (AGPLv3)

### Architecture & Internals

Citus is a pure PostgreSQL extension transforming standard PostgreSQL 17 instances into a **Coordinator + Worker** horizontally sharded cluster (`citus_add_node`). Tables are classified as **Hash-Distributed** (partitioned across worker shards by a distribution column such as `account_id`), **Reference Tables** (replicated across all workers with 2PC), or Coordinator-local tables. **Citus MX** propagates shard metadata to workers so applications can issue queries against any node.

### Concurrency, `0A000` Constraint & Limits

- **Distributed 2PC:** Single-shard DML executes directly on one worker with native PG latency. Multi-shard updates and Reference Table writes enforce atomicity with **Two-Phase Commit (`PREPARE TRANSACTION` / `COMMIT PREPARED`)**, requiring `max_prepared_transactions > 0`.
- **Hard Schema Limit (`SQLSTATE 0A000`):** Every `PRIMARY KEY` or `UNIQUE` constraint on a distributed table **must include the distribution column**, or creation fails with `SQLSTATE 0A000`. Cross-shard foreign keys are restricted to colocated tables or reference tables.
- **Availability:** Without streaming HA replicas behind every worker, losing a single worker renders its shards unavailable even though healthy workers and reference reads keep running.

---

## Solution #8: OpenTenBase / Postgres-XL / Postgres-XC

**Dedicated Sheet:** [Solution #8 — OpenTenBase / Postgres-XL / XC (Architectural Reference)](solutions/opentenbase_pgxl.md)

**Family:** 4 — Sharded MPP / 2PC | **License:** Open Source (PostgreSQL / Tencent Apache-style)

### Architecture & Internals

Derived from NTT's **Postgres-XC**, this lineage splits PostgreSQL into stateless **Coordinators** and sharded **Datanodes**. A central **Global Transaction Manager (GTM)** issues cluster `GXID` identifiers and MVCC snapshots for distributed 2PC.

### Status & Structural Bottlenecks

- **Maintenance Status:** **Postgres-XC** is retired, and **Postgres-XL** stayed dormant since ~2018 (frozen on PG 10). **OpenTenBase** (Tencent's fork of TBase) remains the sole active open-source descendant.
- **GTM Bottleneck:** Every distributed query and transaction contacts the **GTM** (partially buffered through GTM-Proxy). Across WAN links, GTM network trips amplify latency sharply, making this family better suited to intra-DC OLAP/HTAP MPP than geo-distributed active-active OLTP.

---

## Solution #9: Bucardo 5

**Dedicated Sheet:** [Solution #9 — Bucardo 5 (`bucardo`)](solutions/bucardo.md)

**Family:** 5 — Trigger-Based Async Daemons | **License:** Open Source (BSD)

### Architecture & Internals

**Bucardo 5** is an external Perl daemon (`bucardo`) using **PL/Perl** triggers and shadow delta tables (`bucardo_delta`, `bucardo_track`) installed inside each participating PostgreSQL database. Multi-master `sync` tasks group databases as bidirectional sources (`dbgroup` with `db1:source, db2:source`) and wake on PostgreSQL `LISTEN/NOTIFY` or polling intervals.

### Conflicts, PK Constraint & Limits

- **Strict Primary Key Requirement:** Tables without a `PRIMARY KEY` or unique index cannot enter a multi-master sync (raw `pgbench_history` fails setup immediately).
- **Conflict Resolution:** Configurable strategies (`bucardo_latest`, `bucardo_source`, `bucardo_target`, custom Perl hooks) inspect delta timestamps asynchronously.
- **Limits:** High write amplification (every row mutation triggers delta inserts and index writes), no DDL auto-replication, single Perl daemon SPOF, and noticeable batch sync lag compared to WAL logical decoding.

---

## Solution #10: SymmetricDS

**Dedicated Sheet:** [Solution #10 — SymmetricDS (Architectural Reference)](solutions/symmetricds.md)

**Family:** 5 — Trigger-Based Async Daemons | **License:** Open Source (LGPL) / Pro (Commercial)

### Architecture & Internals

Written in Java, **SymmetricDS** captures row changes with triggers into staging tables (`sym_data`). It packs rows into `sym_outgoing_batch` payloads and pushes batches over HTTP/HTTPS across hub-and-spoke or mesh links.

### Conflicts & Limits

- **Strengths:** Unrivaled **heterogeneous** multi-master sync (PostgreSQL <-> MySQL <-> SQLite/Oracle) and **intermittent edge connectivity** (retail POS, offline field nodes) with built-in conflict policies (`NEWER_WINS`, `USE_PK_DATA`, `FALLBACK`).
- **Limits:** Trigger write amplification reduces peak OLTP throughput, JVM heap memory footprint adds infrastructure cost, and schema evolution requires explicit `symadmin send-schema` coordination.

---

## Solution #11: PgPool-II (Replication & Snapshot Isolation Modes)

**Dedicated Sheet:** [Solution #11 — PgPool-II (Architectural Reference / Streaming PoC)](solutions/pgpool_ii.md)

**Family:** 6 — Statement-Broadcast Middleware | **License:** Open Source (BSD)

### Architecture & Internals

**PgPool-II** is a C proxy positioned between clients and PostgreSQL backends. Crucially, its common **Streaming Replication Mode** is single-primary + read standbys (not multi-master). True multi-node writes occur only in two specialized modes:
1. **Native Replication Mode (Statement Broadcast):** Replays every write SQL statement simultaneously onto all backend PostgreSQL nodes.
2. **Snapshot Isolation (SI) Mode:** Adds centralized transaction commit/visibility orchestration inside PgPool-II to ensure backends read consistent cross-node snapshots.

### Critical Non-Determinism Hazard

Statement broadcast breaks silently whenever SQL produces different values across nodes: `NOW()`, `CURRENT_TIMESTAMP`, `RANDOM()`, `gen_random_uuid()`, trigger side-effects, or concurrent `nextval()` interleaving. Although PgPool-II attempts regex timestamp rewriting and table locking (`insert_lock`), stored functions and concurrent workloads frequently trigger silent data divergence or proxy-serialized lock stalls.

---

## Solution #12: AWS Aurora PostgreSQL Limitless Database (& Multi-Master v1)

**Dedicated Sheet:** [Solution #12 — AWS Aurora PostgreSQL Limitless (& MM v1)](solutions/aws_aurora_limitless.md)

**Family:** 7 — Cloud-Managed Distributed Engines | **License:** Proprietary (AWS Managed)

### History & Architecture

AWS previously launched **Aurora Multi-Master (v1)** on MySQL (never GA on Aurora PostgreSQL, retired completely in 2024) because cross-writer shared-page invalidation caused severe abort storms under contention. AWS replaced that concept with **Aurora PostgreSQL Limitless Database** (GA 2024): a two-tier sharded engine decoupling **Transaction Routers** from **Data Access Shards** over Aurora's multi-AZ distributed storage, using **AWS Time Sync Service** hardware clocks and 2PC for globally consistent reads and distributed commits. Vendor lock-in and cross-shard 2PC latency remain the primary constraints.

---

## Solution #13: Google Cloud Spanner (PG Interface) & AlloyDB

**Dedicated Sheet:** [Solution #13 — GCP Spanner (PG Interface) & AlloyDB](solutions/gcp_spanner_alloydb.md)

**Family:** 7 — Cloud-Managed Distributed Engines | **License:** Proprietary (GCP Managed)

### Spanner vs AlloyDB Disambiguation

- **Cloud Spanner (PostgreSQL Interface):** Achieves **External Consistency** across continents via **Multi-Paxos** splits and **TrueTime** (GPS + atomic clocks bounding global uncertainty $\varepsilon < 7\text{ ms}$). Writes wait out $2\varepsilon$ before releasing locks (`commit-wait`), guaranteeing linearizable timestamps without cross-region read locks. However, Spanner's PG Interface supports only a subset of PostgreSQL SQL/types (zero C extensions, limited PL/pgSQL).
- **Google Cloud AlloyDB:** **Not active-active multi-master.** AlloyDB uses a **single primary compute writer** paired with disaggregated Log-Processing Storage and elastic read pools. It belongs in architectural matrices purely to prevent misclassifying shared-storage HA as multi-writer active-active.

---

## Solution #14: Legacy Trigger Systems (RubyRep, Slony-I, Londiste)

**Dedicated Sheet:** [Solution #14 — Legacy Trigger Systems (EOL)](solutions/legacy_triggers.md)

**Family:** 5 — Trigger-Based Async Daemons | **License:** Open Source (Historical / EOL)

### Technical Heritage & Retirement Status

- **RubyRep:** Ruby-based bidirectional table-diff and trigger sync; unmaintained, CPU-bound, unsafe for high-concurrency OLTP.
- **Slony-I:** C/SQL trigger replication designed in the 2000s before PG 9.0 streaming replication; **strictly single-origin per replication set** (not multi-master).
- **Londiste (Skytools):** Python daemon consuming `PgQ` trigger queues; scalable batch shipping in its era, now superseded by core PG 10+ `pgoutput` logical replication. None of these three should be selected for new production deployments.

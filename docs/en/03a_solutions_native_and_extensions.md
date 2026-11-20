# 03a — Solution Monographs: Native Logical, Extensions & Baselines

**Series:** PostgreSQL Multi-Master & Active-Active Architectures  
**Author:** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr)  
**License:** MIT License

---

## Dedicated Architecture Sheets (`03a` Scope)

| Catalog ID | Solution / Topology | Dedicated EN Sheet | Scope |
| :---: | :--- | :--- | :--- |
| **#1** | PG 17 Native Bidirectional Logical (`pg-birep`) | [Solution #1 — PG 17 Bidirectional Logical](solutions/pg17_bidirectional_logical.md) | Live-benchmarked (`T4`) |
| **#2** | pgEdge Platform / Spock v5 (`pgedge`, `pgedge-delta-apply`) | [Solution #2 — pgEdge / Spock v5](solutions/pgedge_spock.md) | Live-benchmarked (`T4`, CRDT) |
| **#3** | pglogical 2 | [Solution #3 — pglogical 2](solutions/pglogical2.md) | Architectural Reference |
| **#4** | EDB Postgres Distributed (PGD / BDR) | [Solution #4 — EDB PGD](solutions/edb_pgd.md) | Architectural Reference |
| **#15a** | PG 17 Standalone (`pg17-standalone`) | [Solution #15a — PG 17 Standalone](solutions/pg17_standalone.md) | Live-benchmarked (`T1` Control) |
| **#15b** | PG 17 Physical Streaming & Patroni HA (`pg17-async/sync-streaming`) | [Solution #15b — PG 17 Streaming & Patroni](solutions/pg17_physical_streaming_patroni.md) | Live-benchmarked (`T1`/`T2`) |
| **#16** | PG 17 Native Uni-Directional Logical (`pg17-logical`) | [Solution #16 — PG 17 Uni-Directional Logical](solutions/pg17_logical_unidirectional.md) | Live-benchmarked (`T3`) |

---

## Solution #1: PostgreSQL 16/17/18 Native Bidirectional Logical Replication

**Dedicated Sheet:** [Solution #1 — PG 17 Native Bidirectional Logical (`pg-birep`)](solutions/pg17_bidirectional_logical.md)

**Family:** 1 — Native Core PostgreSQL | **License:** Open Source (PostgreSQL License)

### Architecture & Internals

Introduced in PostgreSQL 16 via the `origin = none` subscription parameter, native bidirectional logical replication connects two or more standard PostgreSQL servers into an asynchronous active-active mesh using built-in `pgoutput` logical decoding. Each node creates a `PUBLICATION` for shared tables and subscribes to peer publications using:

```sql
CREATE SUBSCRIPTION sub_from_peer
  CONNECTION 'host=peer dbname=labdb user=postgres'
  PUBLICATION pub_all
  WITH (origin = none, copy_data = true);
```

Setting `origin = none` instructs the logical decoding `walsender` to emit **only locally generated changes** (records lacking a `pg_replication_origin` tag) and ignore changes previously applied by a remote subscription worker. This breaks infinite `A -> B -> A` replication loops natively inside the core engine without triggers or extensions. PostgreSQL 17 added `pg_createsubscriber` and `sync_replication_slots` for HA slot preservation, while PostgreSQL 18 expanded conflict telemetry (`pg_stat_subscription_stats` counters and detailed conflict logging with `track_commit_timestamp = on`).

### Conflict Resolution, DDL & Sequences

- **Conflicts:** Core PostgreSQL 16/17 provides **no autonomous conflict resolution** (no LWW, no CRDTs). A primary-key or `UNIQUE` collision (`SQLSTATE 23505`) **immediately halts the apply worker**, accumulating WAL inside the publisher's replication slot until an operator resolves the row or skips the transaction via `ALTER SUBSCRIPTION ... SKIP (lsn = '...')`. Missing-row updates/deletes are logged/skipped depending on version/configuration, silently creating data drift.
- **DDL & Sequences:** Neither DDL statements nor sequence increments (`nextval()`) replicate natively. Applications must deploy stepped sequences (`INCREMENT BY N START WITH node_id`) or UUIDv7/Snowflake IDs, and coordinate DDL manually in strict topological order.
- **Keyless Tables:** `UPDATE` and `DELETE` fail on tables without a `PRIMARY KEY` or `REPLICA IDENTITY FULL` (`SQLSTATE 55000`).

### Strengths & Limits

- **Pros:** Zero external dependencies, zero licensing cost, full PG 17/18 extension ecosystem, native performance.
- **Cons:** Halts on `23505` collisions; unsafe for competing multi-node writes without strict sharded/partitioned write routing; no DDL or large-object (`pg_largeobject`) replication; offline peer slots can exhaust disk WAL if `max_slot_wal_keep_size` is uncapped.

---

## Solution #2: pgEdge Platform / Spock v5

**Dedicated Sheet:** [Solution #2 — pgEdge / Spock v5 (`pgedge`, `pgedge-delta-apply`)](solutions/pgedge_spock.md)

**Family:** 2 — Logical Replication Extensions | **License:** Open Source (PostgreSQL License)

### Architecture & Internals

Developed by pgEdge for PostgreSQL 15–17, **Spock v5** modernizes the open-source `pglogical` lineage into a cohesive active-active multi-master extension suite loaded via `shared_preload_libraries = 'spock,snowflake'` (plus `lolor` for Large Objects). Each node joins a peer-to-peer logical mesh (`spock.node_create`, `spock.sub_create`) reading WAL via a custom logical output plugin that tags origins cleanly across 3+ node topologies.

### Conflict Resolution, DDL & Sequences

- **LWW & Delta-Apply CRDTs:** With `track_commit_timestamp = on` and `spock.conflict_resolution = 'last_update_wins'`, Spock compares commit timestamps (breaking ties deterministically by node ID) instead of halting on conflicts. Critically, Spock implements **Delta-Apply** for numeric columns: when `balance = balance + 50` executes, Spock transmits the old and new column values so the remote node applies `target_val + (remote_new - remote_old)`, eliminating non-commutative **Lost Updates**.
- **Snowflake Sequences (`snowflake`):** Generates 64-bit K-sortable global IDs encoding timestamp, `snowflake.node` (`1..1024`), and per-millisecond counter, eliminating `23505` PK collisions without cross-node locking.
- **Auto-DDL & Large Objects:** Setting `spock.enable_ddl_replication = on` captures schema changes via event triggers and propagates them over replication sets automatically; `lolor` intercepts `pg_largeobject` operations that standard logical replication ignores.

### Strengths & Limits

- **Pros:** 100% open-source PG 17 native storage/extensions; solves native PG's three biggest gaps (LWW + Delta-Apply CRDTs, Snowflake IDs, Auto-DDL).
- **Cons:** Still asynchronous (`PA/EL`) — non-delta columns remain vulnerable to LWW overwrites and cross-region clock skew (`chrony`/NTP drift); secondary `UNIQUE` collisions still drop one winning row under LWW; simultaneous DDL on multiple nodes lacks Raft global serialization.

---

## Solution #3: pglogical 2

**Dedicated Sheet:** [Solution #3 — pglogical 2 (Architectural Reference)](solutions/pglogical2.md)

**Family:** 2 — Logical Replication Extensions | **License:** Open Source (PostgreSQL License)

### Architecture & Internals

Created by 2ndQuadrant prior to PostgreSQL 10's built-in logical replication, **pglogical 2** exposes `pglogical.create_node`, replication sets (`default`, `default_insert_only`, `ddl_sql`), and `pglogical.create_subscription` via background worker processes. It remains widely deployed for zero-downtime major version upgrades and legacy active-active topologies.

### Conflict Resolution, DDL & Sequences

- **Conflicts:** Supports `pglogical.conflict_resolution` policies (`error`, `apply_remote`, `keep_local`, `last_update_wins`, `first_update_wins`), requiring `track_commit_timestamp = on` for timestamp-ordered resolution. Lacks Delta-Apply CRDTs.
- **DDL & Sequences:** DDL does **not** replicate transparently on raw SQL execution; operators must wrap DDL inside `SELECT pglogical.replicate_ddl_command('...')`. Sequences can sync periodically in batches (`synchronize_structure` / `add_all_sequences`), which does not protect against simultaneous uncoordinated `INSERT` collisions.

### Strengths & Limits

- **Pros:** Battle-tested selective table/column/row filtering; supports older PostgreSQL releases (PG 9.4–16/17 bridges).
- **Cons:** Superseded in modern active-active design by Spock v5 (for open-source CRDTs/auto-DDL) and native PG 17+ (for simple subscriptions); lacks CRDTs and Snowflake IDs out of the box.

---

## Solution #4: EDB Postgres Distributed (PGD v5/v6, formerly BDR)

**Dedicated Sheet:** [Solution #4 — EDB Postgres Distributed / BDR (Architectural Reference)](solutions/edb_pgd.md)

**Family:** 2 — Logical Replication Extensions | **License:** **Commercial / Proprietary** (EnterpriseDB)

### Architecture & Internals

**EDB Postgres Distributed (PGD)** — evolved from BDR (Bi-Directional Replication) — couples high-speed asynchronous logical replication with an embedded **Raft consensus layer** across data nodes and witness nodes, fronted by **PGD Proxy** for smart routing. Unlike pure async meshes, PGD lets architects mix asynchronous geo-replication with Raft-coordinated synchronous guarantees per node group or transaction.

### Conflict Resolution, DDL & Sequences

- **Multi-Mode Consistency:** Supports:
  - **Async Logical + CRDTs:** Built-in CRDT column types (`bdr.crdt_gcounter`, `bdr.crdt_pncounter`, `bdr.crdt_delta_counter`, `bdr.crdt_delta_sum`) and `bdr.conflict_history` LWW conflict resolution.
  - **CAMO (Commit At Most Once):** Pairs nodes so a client verifies commit status against a partner node if a primary dies mid-commit, preventing duplicate payment/order retries.
  - **Eager All-Node Replication:** Raft-backed global transaction synchronization across participating nodes (zero conflicts, high WAN RTT cost).
  - **Write-Lead:** PGD Proxy directs all writes to one Raft-elected Lead Master while keeping peer masters hot for sub-second failover.
- **DDL & Global Sequences:** Global DDL locks acquired via Raft consensus prevent divergent concurrent schema mutations; `bdr.global_sequences` (`snowflakeid`, Raft-backed `galloc`, and legacy `timeshard`) issue conflict-free global IDs.

### Strengths & Limits

- **Pros:** Most mature feature set on top of standard PostgreSQL (Raft DDL locks, CAMO, Write-Lead, CRDTs, enterprise PITR/proxy orchestration).
- **Cons:** **Commercial/Proprietary licensing** (`EDB` subscription required; non-trivial per-core TCO); Raft global DDL locks block writes across WAN links during schema migrations; operational complexity requires dedicated witness nodes and PGD Proxy tuning.

---

## Solution #15: Control Baselines — Standalone PG 17 & Patroni HA

**Dedicated Sheets:** [Solution #15a — PG 17 Standalone](solutions/pg17_standalone.md) · [Solution #15b — PG 17 Physical Streaming & Patroni HA](solutions/pg17_physical_streaming_patroni.md)

**Family:** 7 — Single-Primary Reference Baselines | **License:** Open Source (PostgreSQL / MIT)

### Architecture & Internals

Any credible multi-master evaluation requires two single-primary baselines to quantify the exact **coordination tax** paid for multi-writer capability:

1. **Standalone PostgreSQL 17:** Single server, local NVMe/filesystem WAL `fsync` (`synchronous_commit = on`). Delivers the theoretical maximum single-node TPS and minimum commit latency (`L_disk`) without network serialization.
2. **Patroni + etcd (Raft DCS) + HAProxy Streaming HA:** One active Primary streams physical WAL to $N-1$ read-only Standby nodes. **Patroni** stores cluster state and a time-bounded **Leader Lease** in **etcd** (Raft quorum, minimum 3 nodes), enforcing strict single-writer exclusivity via OS watchdog fencing against split-brain. **HAProxy** polls Patroni's REST API (`/primary`, `/replica`) to route writes solely to the current leader.

### Consistency, DDL & Limits

- **Zero Write Conflicts:** All DML, `SERIAL` sequences, `pg_largeobject`, `pg_advisory_lock`, `LISTEN/NOTIFY`, keyless tables, and arbitrary DDL execute with 100% PostgreSQL fidelity on one primary.
- **Configurable `RPO`/`RTO`:** Setting `synchronous_standby_names = 'FIRST 1 (*)'` with `synchronous_commit = remote_apply` guarantees `RPO = 0` (`PC/EC`), while async streaming (`PA/EL`) keeps write latency local with millisecond `RPO` and `RTO ~ 10-30 s`.
- **Limit:** Does not scale write throughput beyond one primary node's CPU/IOPS ceiling and incurs WAN latency for distant writers. Nevertheless, for **over 80% of enterprise OLTP workloads**, Patroni HA beats multi-master complexity decisively.

---

## Solution #16: PostgreSQL 17 Native Uni-Directional Logical Replication (Pub/Sub)

**Dedicated Sheet:** [Solution #16 — PG 17 Native Uni-Directional Logical (`pg17-logical`)](solutions/pg17_logical_unidirectional.md)

**Family:** 1 — Native Core PostgreSQL | **License:** Open Source (PostgreSQL License)

### Architecture & Limits (`T3`)

Built into core PostgreSQL via `wal_level = logical` and the `pgoutput` plugin, uni-directional `PUBLICATION` / `SUBSCRIPTION` streams decoded row changes (`INSERT`/`UPDATE`/`DELETE`) from one active publisher to one or more writable subscribers (`PA/EL`, `T3` tier):

- **Selective Replication & Zero-Downtime Upgrades:** Supports table subsets, `WHERE` row filters, column lists, and replication across different PostgreSQL major versions (`PG 15 -> 17 -> 18`), unlike block-level physical streaming.
- **No Automatic DDL & Keyless Rejection:** DDL statements are not replicated automatically; `UPDATE` and `DELETE` on keyless tables fail on the publisher with `SQLSTATE 55000` unless `REPLICA IDENTITY FULL` is configured.
- **Sequence Trap (`SQLSTATE 23505`):** Sequence state (`nextval()`) does not replicate automatically (`last_value` remains `1|false` on subscribers during `T18`), causing immediate `23505` primary-key collisions after subscriber promotion unless synchronized via `setval()` or UUID/Snowflake keys.

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
| **#15a** | PG 17 Standalone (`pg17-standalone`) | [Solution #15a — PG 17 Standalone](solutions/pg17_standalone.md) | Live-benchmarked (`T0` Baseline) |
| **#15b** | PG 17 Physical Streaming & Patroni HA (`pg17-async/sync-streaming`) | [Solution #15b — PG 17 Streaming & Patroni](solutions/pg17_physical_streaming_patroni.md) | Live-benchmarked (`T1`/`T2`) |
| **#16** | PG 17 Native Uni-Directional Logical (`pg17-logical`) | [Solution #16 — PG 17 Uni-Directional Logical](solutions/pg17_logical_unidirectional.md) | Live-benchmarked (`T3`) |
| **#17** | PG 18.6 Native Clustering (`pg18-standalone/streaming/logical/birep`) | [Solution #17 - PG 18.6 Native Clustering](solutions/pg18_native_clustering.md) | Live-benchmarked (5 tiers, 87 rows) |
| **#18** | YT Cluster & YT Cluster Lite (`yt-cluster`, `yt-cluster-async`) | [Solution #18 - YT Cluster & YT Cluster Lite](solutions/yt_cluster_lite.md) | Live-benchmarked (3-node 1.21.3, 22 rows) |

---

## Solution #1: PostgreSQL 16/17/18 Native Bidirectional Logical Replication

**Dedicated Sheet:** [Solution #1 — PG 17 Native Bidirectional Logical (`pg-birep`)](solutions/pg17_bidirectional_logical.md)

**Family:** 1 — Native Core PostgreSQL | **License:** Open Source (PostgreSQL License)

### Architecture & Internals

Introduced in PostgreSQL 16 with `origin = none`, native bidirectional logical replication connects PostgreSQL servers into an async active-active mesh. Each node uses built-in `pgoutput` logical decoding. Each node creates a `PUBLICATION` for shared tables and subscribes to peer publications using:

```sql
CREATE SUBSCRIPTION sub_from_peer
  CONNECTION 'host=peer dbname=labdb user=postgres'
  PUBLICATION pub_all
  WITH (origin = none, copy_data = true);
```

Setting `origin = none` instructs the logical decoding `walsender` to emit **only locally generated changes** (records lacking a `pg_replication_origin` tag) and ignore changes previously applied by a remote subscription worker. This breaks infinite `A -> B -> A` replication loops natively inside the core engine without triggers or extensions. PostgreSQL 17 added `pg_createsubscriber` and `sync_replication_slots` for HA slot preservation, while PostgreSQL 18 expanded conflict telemetry (`pg_stat_subscription_stats` counters and detailed conflict logging with `track_commit_timestamp = on`).

### Conflict Resolution, DDL & Sequences

- **Conflicts:** Core PostgreSQL 16/17 provides **no autonomous conflict resolution** (no LWW, no CRDTs). Any `PRIMARY KEY` or `UNIQUE` collision (`SQLSTATE 23505`) **halts the apply worker** and retains WAL in the slot. An operator must delete the row or skip it with `ALTER SUBSCRIPTION ... SKIP (lsn = '...')`. Missing-row writes drift silently.
- **DDL & Sequences:** Neither DDL statements nor sequence increments (`nextval()`) replicate natively. Applications must deploy stepped sequences (`INCREMENT BY N START WITH node_id`) or UUIDv7/Snowflake IDs, and coordinate DDL manually in strict topological order.
- **Keyless Tables:** `UPDATE` and `DELETE` fail on tables without a `PRIMARY KEY` or `REPLICA IDENTITY FULL` (`SQLSTATE 55000`).

### Strengths & Limits

- **Pros:** Zero external dependencies, zero licensing cost, full PG 17/18 extension ecosystem, native performance.
- **Cons:** Halts on `23505` collisions and breaks competing multi-node writes without partitioned routing. Lacks DDL and `pg_largeobject` sync, and offline peer slots can fill disk WAL if `max_slot_wal_keep_size` is uncapped.

---

## Solution #2: pgEdge Platform / Spock v5

**Dedicated Sheet:** [Solution #2 — pgEdge / Spock v5 (`pgedge`, `pgedge-delta-apply`)](solutions/pgedge_spock.md)

**Family:** 2 — Logical Replication Extensions | **License:** Open Source (PostgreSQL License)

### Architecture & Internals

Built by pgEdge for PostgreSQL 15–17, **Spock v5** updates `pglogical` into a multi-master extension suite (`shared_preload_libraries = 'spock,snowflake'`, plus `lolor`). Each node joins a peer-to-peer mesh (`spock.node_create`, `spock.sub_create`) reading WAL with a custom origin-tagging plugin.

### Conflict Resolution, DDL & Sequences

- **LWW & Delta-Apply CRDTs:** With `track_commit_timestamp = on` and `spock.conflict_resolution = 'last_update_wins'`, Spock compares commit timestamps (breaking ties deterministically by node ID) instead of halting on conflicts. Critically, Spock implements **Delta-Apply** for numeric columns: when `balance = balance + 50` executes, Spock transmits the old and new column values so the remote node applies `target_val + (remote_new - remote_old)`, eliminating non-commutative **Lost Updates**.
- **Snowflake Sequences (`snowflake`):** Generates 64-bit K-sortable global IDs encoding timestamp, `snowflake.node` (`1..1023`), and per-millisecond counter, eliminating `23505` PK collisions without cross-node locking.
- **Auto-DDL & Large Objects:** Setting `spock.enable_ddl_replication = on` captures schema changes with event triggers and pushes them over replication sets. `lolor` replicates `pg_largeobject` operations that native logical decoding ignores.

### Strengths & Limits

- **Pros:** 100% open-source PG 17 storage and extensions. Solves native PG's three biggest gaps (LWW + Delta-Apply CRDTs, Snowflake IDs, Auto-DDL).
- **Cons:** Async (`PA/EL`) design leaves non-delta columns exposed to LWW overwrites and `chrony`/NTP drift. Secondary `UNIQUE` collisions drop one winning row, and concurrent DDL lacks Raft serialization.

---

## Solution #3: pglogical 2

**Dedicated Sheet:** [Solution #3 — pglogical 2 (Architectural Reference)](solutions/pglogical2.md)

**Family:** 2 — Logical Replication Extensions | **License:** Open Source (PostgreSQL License)

### Architecture & Internals

Created by 2ndQuadrant prior to PostgreSQL 10's built-in logical replication, **pglogical 2** exposes `pglogical.create_node`, replication sets (`default`, `default_insert_only`, `ddl_sql`), and `pglogical.create_subscription` with background worker processes. It remains widely deployed for zero-downtime major version upgrades and legacy active-active topologies.

### Conflict Resolution, DDL & Sequences

- **Conflicts:** Supports `pglogical.conflict_resolution` policies (`error`, `apply_remote`, `keep_local`, `last_update_wins`, `first_update_wins`), requiring `track_commit_timestamp = on` for timestamp-ordered resolution. Lacks Delta-Apply CRDTs.
- **DDL & Sequences:** DDL does **not** replicate transparently on raw SQL execution. Operators must wrap DDL inside `SELECT pglogical.replicate_ddl_command('...')`. Sequences can sync periodically in batches (`synchronize_structure` / `add_all_sequences`), which does not protect against simultaneous uncoordinated `INSERT` collisions.

### Strengths & Limits

- **Pros:** Battle-tested table, column, and row filtering. Supports older PostgreSQL releases (`PG 9.4–16/17` bridges).
- **Cons:** Superseded by Spock v5 (for OSS CRDTs/auto-DDL) and native PG 17+ (for simple subscriptions). Lacks CRDTs and Snowflake IDs out of the box.

---

## Solution #4: EDB Postgres Distributed (PGD v5/v6, formerly BDR)

**Dedicated Sheet:** [Solution #4 — EDB Postgres Distributed / BDR (Architectural Reference)](solutions/edb_pgd.md)

**Family:** 2 — Logical Replication Extensions | **License:** **Commercial / Proprietary** (EnterpriseDB)

### Architecture & Internals

**EDB Postgres Distributed (PGD)** — evolved from BDR — pairs async logical replication with an embedded **Raft consensus layer** across data and witness nodes. **PGD Proxy** handles smart client routing. Unlike pure async meshes, PGD lets architects mix asynchronous geo-replication with Raft-coordinated synchronous guarantees per node group or transaction.

### Conflict Resolution, DDL & Sequences

- **Multi-Mode Consistency:** Supports:
  - **Async Logical + CRDTs:** Built-in CRDT column types (`bdr.crdt_gcounter`, `bdr.crdt_pncounter`, `bdr.crdt_delta_counter`, `bdr.crdt_delta_sum`) and `bdr.conflict_history` LWW conflict resolution.
  - **CAMO (Commit At Most Once):** Pairs nodes so a client verifies commit status against a partner node if a primary dies mid-commit, preventing duplicate payment/order retries.
  - **Eager All-Node Replication:** Raft-backed global transaction synchronization across participating nodes (zero conflicts, high WAN RTT cost).
  - **Write-Lead:** PGD Proxy directs all writes to one Raft-elected Lead Master while keeping peer masters hot for sub-second failover.
- **DDL & Global Sequences:** Global DDL locks acquired with Raft consensus prevent conflicting schema changes. `bdr.global_sequences` (`snowflakeid`, Raft `galloc`, and legacy `timeshard`) issue conflict-free IDs.

### Strengths & Limits

- **Pros:** Most mature feature set on top of standard PostgreSQL (Raft DDL locks, CAMO, Write-Lead, CRDTs, enterprise PITR/proxy orchestration).
- **Cons:** **Commercial/Proprietary licensing** requires an `EDB` subscription with per-core TCO. Raft DDL locks block WAN writes during migrations, and clusters require witness nodes plus PGD Proxy tuning.

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

---

## Solution #17: PostgreSQL 18.6 Native Clustering (AIO, uuidv7, Streaming & Logical)

**Dedicated Sheet:** [Solution #17 - PostgreSQL 18.6 Native Clustering](solutions/pg18_native_clustering.md) | **Empirical Benchmark Chapter:** [Ch. 12 - PG 18.6 Clustering & Benchmarks](12_postgresql_18_clustering_and_benchmarks.md)

**Family:** 1 - Native Core PostgreSQL (All 5 Tiers) | **License:** Open Source (PostgreSQL License)

### PG 16 -> PG 17 -> PG 18.6 Evolution & Capabilities

Evaluated live on `PostgreSQL 18.6 (Debian 18.6-1.pgdg13+2)` across all five native tiers (`pg18-standalone`, `pg18-async-streaming`, `pg18-sync-streaming`, `pg18-logical`, `pg18-birep`; `87` rows in `results/benchmark_pg18.csv`), PG 18.6 upgrades the core engine over PG 16 (`origin=none`, sync I/O, `checksums=off`) and PG 17 (`pg_createsubscriber`, `sync_replication_slots`, 6 `confl_*` counters):

- **AIO & Data Integrity Defaults:** Enables `data_checksums=on` at `initdb` and `io_method=worker` (`io_workers=3`, `-18.5%` cold scan `829.4 ms` vs `1,018.3 ms` `sync`; `io_uring` fails with `EPERM` under default Docker seccomp). Docker storage changes to `PGDATA=/var/lib/postgresql/18/docker` (`VOLUME /var/lib/postgresql`).
- **Native `uuidv7()` Active-Active PKs:** Built-in RFC 9562 time-ordered UUIDs converged `50/50` concurrent dual-node `pg18-birep` inserts (`0` `23505`, `0` B-tree inversions) and drove `H_append_only_insert` to **`2,066.70 TPS`** (`3.30x` PG 17 `627.13 TPS`).
- **7 `confl_*` Counters & Parallel Apply:** Expands `pg_stat_subscription_stats` to 7 counters (`+confl_multiple_unique_conflicts`), defaults subscriptions to `substream=p` (parallel streaming apply), and supports `publish_generated_columns=stored` (`s`), lifting `pg18-logical` `E_sysbench_oltp_rw` (`1,027.84 TPS`, `+72.5%`) and `H_append_only_insert` (`3,518.49 TPS`, `+85.1%`).

### Verified Native Limits (PG 18.6)

- **Logical Sequence Sync Deferred (`SQLSTATE 42601`):** `CREATE PUBLICATION ... FOR ALL SEQUENCES` and `ALTER SUBSCRIPTION ... REFRESH SEQUENCES` still fail with `SQLSTATE 42601` in PG 18.6 (deferred to PG 19); `T18` subscriber sequences stay at `1|false` (`23505` trap unless `setval()` or `uuidv7()` is used).
- **No Auto-DDL, LWW, or CRDT:** `ALTER TABLE` does not propagate (`TRUNCATE` only); keyless `UPDATE`/`DELETE` still raises `SQLSTATE 55000`; concurrent overlapping writes on `pg18-birep` still diverge (`B2` `-338`, `D` `-83,252`); `T13` async cross-node FK race fails `23503x8` (`2/10 ok`).

---

## Solution #18: YT Cluster & YT Cluster Lite (MIT Core + ytserv)

**Dedicated Sheet:** [Solution #18 - YT Cluster & YT Cluster Lite](solutions/yt_cluster_lite.md)

**Family:** 2 - Logical/Trigger Extensions & XA 2PC | **License:** MIT Core (`DBinvent/yt-cluster-lite`) + Dual-Licensed PolyForm Noncommercial 1.0.0 / Commercial (`ytserv` / `ytctl`)

### Architecture, License Split & Self-Run Jepsen Nuance

- **MIT Core vs Closed `ytserv`:** `DBinvent/yt-cluster-lite` (MIT, 7 days old, `bus factor = 1`) publishes `yt-core-proto`, the `ytpgc` C extension, and the `yt-lite` single-DB leaf node, while the full multi-master coordinator **`ytserv`/`ytctl`** (`dbinvent/yt:1.21.3`, PG 18.7) is closed/source-available under PolyForm Noncommercial / Commercial.
- **Trigger + XA 2PC + Leader Checkin:** Runs on unmodified PostgreSQL (`max_prepared_transactions >= 100`) using per-table `yt_synchronize()` row triggers and `XACT_EVENT_PRE_COMMIT` XA 2PC (`PREPARE TRANSACTION` / `COMMIT PREPARED`). Every node accepts writes, but a term/subterm elected Leader arbitrates global write order and write-time conflict checkin (`40001` / `55409`). Default `cluster_commit=half` enforces majority sync 2PC (`RPO=0`, `0` drift), while reads on non-party peers remain eventually consistent (`NO_SC`).
- **Self-Run Jepsen Elle Scope:** DBinvent self-ran Jepsen 0.3.14 + Elle (not Jepsen LLC) verifying **`cursor-stability` only** (strong writes with eventually consistent reads, not strict serializability/linearizable reads), finding and fixing 51 issues across 397 retest runs.

### Live Reversibility & Benchmark Reality (`dbinvent/yt:1.21.3`, `PG_SCALE = 2`)

- **Reversibility (`T_REVERT`) & Zero Drift:** `DROP EXTENSION yt_cluster CASCADE` on `yt3` left `ext=0`, `triggers=0`, and `5/5` committed rows intact with plain PG `INSERT` working (`6/6`). `L3` (`+100/-30`) blocked lost updates via `55409` (`0` drift -> `1070.00`), `L4` enforced global `UNIQUE` via `40001`, and `T13` passed `10/10` cross-node FKs.
- **2PC Write Ceiling vs Local Reads:** Default `yt-cluster` (`cc=half`) reached **`20.63 TPS`** (`A`), `10.69` (`B2`), `67.76` (`D`), `28.48` (`E`), `110.53` (`H`), `2.25` (`F_wan25`), and `86 rows/s` (`T11` bulk), while local reads hit `48,787.74 TPS` (`C`) and `165,472.75 TPS` (`E4`). Async `yt-cluster-async` (`cc=nodes>=0`) lifted writes `2.0x-5.1x` (`41.45` `A`, `55.03` `B2`, `163.01` `D`, `4.78` `F_wan25`, `0` drift). Verified traps: `SAVEPOINT` rollback over writes raises `SQLSTATE 0A000`, `ALTER TABLE` is not propagated (`sge` rolling migrations), `2/3` loss blocks writes (`57P03`), `advisory_lock`/`LISTEN` stay local, and stale `.s.YT.5432.pid` can trigger `YT-E1104` on PID reuse.

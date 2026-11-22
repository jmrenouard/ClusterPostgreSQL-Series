# 05 — PoC Architectures and Empirical Test Protocol

**Series:** PostgreSQL Multi-Master & Active-Active Architectures  
**Author:** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr)  
**License:** MIT License

---

## 1. Test Environment, Isolation & Resource Guardrails

To remove hidden vendor assumptions, all probes, failure drills, and benchmarks execute on one dedicated Docker host. Deterministic `Makefile` targets orchestrate every run. See the [Stacks Matrix](../../stacks/README.md) for live stack definitions and `./mdb` targets.

### 1.1 Host Profile & Execution Constraints

- **Compute & Memory Envelope:** 20 vCPU cores and **16.4 GiB RAM** running inside an isolated WSL2 Linux kernel Docker daemon.
- **Strict Sequential Topology Execution:** Distributed SQL engines (YugabyteDB `yb-tserver`/`yb-master`, CockroachDB `cockroach`, Citus workers) allocate multi-gigabyte RocksDB/Pebble block caches and JVM/C++ memory arenas. Running two clusters simultaneously exhausts 16.4 GiB RAM, triggers Linux OOM kills, or injects noisy-neighbor I/O jitter. Every topology therefore executes strictly **one stack at a time** (`up -> setup -> tests -> benchmarks -> down -v`).
- **Intra-Network Client Execution (Zero NAT Skew):** Host-to-container TCP forwarding across virtualization bridges introduces variable NAT overhead and socket exhaustion under high `pgbench` concurrency. All benchmark drivers (`pgbench`, `sysbench`) execute inside an ephemeral client container attached directly to each stack's internal Docker bridge network.
- **Explicit Memory Caps:** Container flags explicitly bound memory-hungry engines (such as `--memory_limit_hard_bytes`, `--cache`, and `--max-sql-memory`) so container OOM interference never skews comparative runs.
- **Zero Static Secrets:** All lab instances use ephemeral environment variables (`${PG_LAB_PASSWORD:-pg_poc_ephemeral}`) injected only at container runtime.

---

## 2. Reproducible PoC Topologies Matrix

The harness instantiates **13 Docker Compose stacks** covering **18 active benchmark topologies** (plus the V1/V2 `pgedge-delta-apply` mode) in `env/multi-db-docker-env`:

| Compose Stack | Architecture (#) | Active Topologies (18 Total) | Core Image Basis | Key Lab Configuration |
| :--- | :--- | :--- | :--- | :--- |
| `pg17-baseline`, `pg-streaming` (plus `patroni` HA) | #15 Control Baselines | `pg17-standalone`, `pg17-async-streaming`, `pg17-sync-streaming` (plus Patroni HA) | `postgres:17`, Patroni + `etcd` | Single-writer WAL baseline (`synchronous_commit=on` / `remote_apply`) |
| `pg-logical` | #16 Native Uni-Logical | `pg17-logical` | `postgres:17` | Native `CREATE PUBLICATION` / `SUBSCRIPTION` uni-directional stream |
| `pg-birep` | #1 Native Bidirectional | `pg-birep` | `postgres:17` + HAProxy | `wal_level=logical`, `origin=none`, stepped seq (`+2`), `track_commit_timestamp=on` |
| `pgedge` | #2 pgEdge / Spock v5 | `pgedge` (plus V1/V2 `pgedge-delta-apply`) | PG 17 + `spock 5.0.14` + `snowflake` | 3-node mesh, `last_update_wins`, `enable_ddl_replication=on`, `delta_apply` probe |
| `bucardo` | #9 Bucardo 5 | `bucardo` | PG 17 (`plperl`) + Perl `5.6.0` | `dbgroup` (`db1:source,db2:source`), `conflict_strategy=bucardo_latest` |
| `citus` | #7 Citus | `citus` | `citusdata/citus` (`14.2.0` on PG 17) | 1 Coordinator + 2 Workers, hash-distributed + 2PC reference tables |
| `yugabyte` | #5 YugabyteDB | `yugabyte` | `yugabytedb/yugabyte:2026.1.3.0` | YSQL (`5433`), DocDB Raft RF=3, HAProxy `:15470`, bounded memory |
| `cockroach` | #6 CockroachDB | `cockroach`, `cockroach-rc` | `cockroachdb/cockroach:latest-v25.4` (V1/V2 baseline: `v24.3.0`) | SQL (`26257`), `--insecure`, HAProxy `:15480`, `bench` role (`cockroach-rc`) |
| `pg18-streaming`, `pg18-logical`, `pg18-birep` | #17 PostgreSQL 18.6 | `pg18-standalone`, `pg18-async-streaming`, `pg18-sync-streaming`, `pg18-logical`, `pg18-birep` | `postgres:18.6` (Debian `pgdg13+2`) | `io_method=worker` (`io_workers=3`), `data_checksums=on`, `uuidv7()` |
| `yt-cluster` | #18 YT Cluster | `yt-cluster` (`cc=half`), `yt-cluster-async` (`nodes>=0`) | `dbinvent/yt:1.21.3` (PG 18.7) | 3-node Paxos/Raft (`yt_cluster 1.21` / `ytserv`), `YT_MAX_PREPARED=300` |

---

## 3. Schema Standardization: The `pgbench_history` Keyless Problem

Standard `pgbench -i -s 10` initializes four tables: `pgbench_branches`, `pgbench_tellers`, `pgbench_accounts` (all with `PRIMARY KEY`), and **`pgbench_history`** — which ships **without a Primary Key or `REPLICA IDENTITY`**.

That schema quirk is analytically critical:
1. During **empirical limits testing (`L2`)**, `pgbench_history` stays keyless. This setup proves exact failures (`SQLSTATE 55000` on logical `UPDATE`/`DELETE`, or Bucardo sync rejection).
2. During **throughput benchmarking (`Suites A–D`)**, we add a standardized surrogate Primary Key (`hid BIGSERIAL` stepped per node, `snowflake.nextval()`, or `unique_rowid()`). Every multi-master engine then replicates TPC-B history appends cleanly without schema disqualification.

---

## 4. 10-Point Functional Validation Protocol (`F1–F10`)

Every PoC script (`tests/test_<topo>.sh`) validates ten baseline operational capabilities before any benchmark numbers are accepted:

| ID | Check | Acceptance Verification |
| :---: | :--- | :--- |
| **F1** | Cluster Health & Topology | All nodes healthy; replication slots / Raft peers / `pg_dist_node` active |
| **F2** | Bidirectional Active-Active Writes | Concurrent writes on `Node 1` and `Node 2` converge across all peers |
| **F3** | Disjoint Keyspace Convergence | Non-overlapping row inserts/updates converge with zero missing or duplicate rows |
| **F4** | Distributed Identity Generation | Stepped sequences / Snowflake / `unique_rowid()` generate collision-free PKs |
| **F5** | Reference / Lookup Join Queries | Multi-table joins and secondary indexes return consistent results across nodes |
| **F6** | Online Schema Evolution (Basic DDL) | `ALTER TABLE ADD COLUMN` propagates or applies cleanly without breaking streams |
| **F7** | Transactional Rollback Isolation | Aborted multi-statement transactions leave zero partial side effects on peers |
| **F8** | Connection Routing & Pooling | LB/Router endpoints (`HAProxy` or native multi-node endpoints) distribute sessions |
| **F9** | Graceful Node Restart & Catch-Up | Controlled container restart restores replication without manual re-seeding |
| **F10** | Deterministic Cleanup | `down -v` destroys all containers, networks, and named volumes cleanly |

---

## 5. 8-Point Empirical Limits Protocol (`L1–L8`)

Rather than hiding edge cases behind green happy-path tests, each PoC executes eight adversarial probes and records exact observed outcomes (`PASS`, `EXPECTED_LIMITATION`, or `FAIL` with verbatim `SQLSTATE` codes):

| ID | Adversarial Probe | Expected Architectural Behavior |
| :---: | :--- | :--- |
| **L1** | Uncoordinated `SERIAL` Collision | Async logical hits `SQLSTATE 23505` (worker halt or LWW overwrite); Raft/Snowflake avoids |
| **L2** | Keyless Table `UPDATE`/`DELETE` | Native PG/Spock raises `SQLSTATE 55000`; Bucardo rejects sync; LSM engines use hidden `rowid` |
| **L3** | Non-Commutative Lost Update (`bal = bal + delta`) | LWW silently drops concurrent update; Spock `delta_apply` converges; Yugabyte/CRDB raise `40001` |
| **L4** | Simultaneous Secondary `UNIQUE(email)` | Native PG halts apply (`23505`); LWW drops losing row; Citus rejects non-shard `UNIQUE` (`0A000`) |
| **L5** | Concurrent DDL & `SAVEPOINT` Limits | Tests auto-DDL race conditions and transactional DDL / `SAVEPOINT` boundaries |
| **L6** | PG Feature Probes | Evaluates `pg_advisory_lock`, `LISTEN/NOTIFY`, `TEMP TABLE`, `pg_trgm`, `uuid-ossp`, `pgvector` |
| **L7** | Offline Node WAL Slot Bloat & Recovery | Stops `Node 2`, writes to `Node 1`, measures `pg_replication_slots` retained bytes & catch-up |
| **L8** | Majority Quorum Loss (`2/3` Down) | Stops 2 of 3 Raft/Paxos nodes to verify strict `PC/EC` stall vs `AP` continued local writes |

---

## 6. Performance Benchmark Suites (`Suites A–H`, `V1–V5`)

After `F1–F10` and `L1–L8` complete cleanly, each cluster runs standardized workload suites. Baseline waves (`V1–V2`) use `PG_SCALE=2`, whereas V5 production-tuned waves use `PG_SCALE=20` with warmed cache:

- **Suite A — `pgbench` TPC-B-like Read-Write:** Measures mixed `SELECT`/`UPDATE`/`INSERT` throughput (`TPS`) and `p50`/`p95`/`p99` latency across concurrency tiers (`1, 4, 16, 32` clients) routed across active nodes.
- **Suite B — `pgbench -S` Select-Only & `B2` Overlap RW:** Isolates horizontal read scaling across multi-node endpoints and tests concurrent overlapping write contention.
- **Suite C — `pgbench -N` Simple-Update:** Removes `pgbench_branches`/`pgbench_tellers` global lock contention to measure pure multi-node indexed row update scaling.
- **Suite D — Custom Hot-Row Conflict & Contention Script:** Directs competing writers at overlapping or partitioned key ranges. This probe measures `SQLSTATE 40001` retry tax, lock amplification, and Lost Update drift.
- **Suite E — `sysbench` OLTP (`--db-driver=pgsql`):** Cross-validates `oltp_read_write`, `oltp_read_only`, and `oltp_write_only` multi-table range scans and point lookups outside `pgbench` biases.
- **Suites H, F_wan & G_conc (`V2–V5`):** Measure append-only `INSERT` scaling (`H`), `tc netem 10/25/50 ms` WAN delay (`F_wan`), and tuned concurrency scaling (`G_conc`, `PG_SCALE=20`).

*[Chapter 06](06_empirical_test_and_benchmark_results.md), [Chapter 12](12_postgresql_18_clustering_and_benchmarks.md), and [Chapter 13](13_production_tuning_and_realistic_benchmarks.md) report all empirical measurements from Suites A–H and Protocols F/L verbatim.*

---

## 7. Threats to Validity: Local Docker Lab vs Production

Honest interpretation of Chapter 06 requires acknowledging five structural gaps between a single-host Docker lab and multi-AZ/WAN production clusters:

1. **Sub-Millisecond Loopback RTT:** Docker bridge round-trips measure `< 0.5 ms` compared to `1–3 ms` cross-AZ or `40–150 ms` transoceanic WAN links. Consensus penalties (`2 * RTT`) that look modest locally dominate WAN deployments.
2. **Shared CPU & NVMe Contention:** Three database containers share host CPU threads, Linux page cache, and one physical storage stack. Contention therefore amplifies throughput collapse at high concurrency.
3. **Virtualization Storage Stack:** WSL2 virtual disk/overlayfs layers alter `fsync()` durability timing compared to dedicated bare-metal NVMe RAID or cloud EBS volumes.
4. **Correlated Failure Domain:** Stopping containers simulates process/network loss cleanly, not independent host kernel panics or asymmetric split-brain partitions with asymmetric routing.
5. **Memory Capping:** Tight container memory caps protect host stability (`16.4 GiB`) but constrain large RocksDB/Pebble compactions and PostgreSQL `shared_buffers` below production sizing.

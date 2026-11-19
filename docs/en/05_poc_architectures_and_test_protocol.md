# 05 — PoC Architectures and Empirical Test Protocol

**Series:** PostgreSQL Multi-Master & Active-Active Architectures  
**Author:** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr)  
**License:** MIT License

---

## 1. Test Environment, Isolation & Resource Guardrails

To eliminate hidden vendor assumptions, all functional probes, failure drills, and performance benchmarks are designed for reproducible execution on a single dedicated Docker host using deterministic scripts orchestrated via `Makefile`.

### 1.1 Host Profile & Execution Constraints

- **Compute & Memory Envelope:** 20 vCPU cores and **16.4 GiB RAM** running inside an isolated WSL2 Linux kernel Docker daemon.
- **Strict Sequential Topology Execution:** Distributed SQL engines (YugabyteDB `yb-tserver`/`yb-master`, CockroachDB `cockroach`, Citus workers) allocate multi-gigabyte RocksDB/Pebble block caches and JVM/C++ memory arenas. Running two clusters simultaneously would exhaust 16.4 GiB RAM, trigger Linux OOM kills, or inject noisy-neighbor I/O jitter. Therefore, every topology executes strictly **one stack at a time** (`up -> setup -> functional & limits tests -> benchmarks -> down -v`).
- **Intra-Network Client Execution (Zero NAT Skew):** Host-to-container TCP forwarding across virtualization bridges introduces variable NAT overhead and socket exhaustion under high `pgbench` concurrency. All benchmark drivers (`pgbench`, `sysbench`) execute inside an ephemeral client container attached directly to each stack's internal Docker bridge network.
- **Explicit Memory Caps:** Memory-hungry engines are explicitly bounded via flags (e.g., `--memory_limit_hard_bytes`, `--cache`, `--max-sql-memory`) so container OOM interference never skews comparative runs.
- **Zero Static Secrets:** All lab instances use ephemeral environment variables (`${PG_LAB_PASSWORD:-pg_poc_ephemeral}`) injected only at container runtime.

---

## 2. Reproducible PoC Topologies Matrix

Six representative multi-master / distributed architectures are instantiated alongside control baselines (`#15`):

| Stack ID | Architecture (#) | Nodes & Topology | Core Engine / Image Basis | Key Lab Configuration |
| :--- | :--- | :--- | :--- | :--- |
| **`pg-birep`** | #1 Native Bidirectional | 2 PG 17 writers + HAProxy | `postgres:17` + `haproxy` | `wal_level=logical`, `origin=none`, stepped seq (`+2`), `track_commit_timestamp=on` |
| **`pgedge`** | #2 pgEdge / Spock v5 | 3 PG 17 writers + HAProxy | PG 17 + `spock` + `snowflake` | Full 3-node mesh, `last_update_wins`, `enable_ddl_replication=on`, `snowflake.node=1..3` |
| **`bucardo`** | #9 Bucardo 5 | 2 PG 17 nodes + `bucardo_daemon` | PG 17 (`plperl`) + Perl daemon | `dbgroup` (`db1:source,db2:source`), `conflict_strategy=bucardo_latest` |
| **`yugabyte`** | #5 YugabyteDB | 3-node RF=3 cluster | YugabyteDB (`yb-master`/`yb-tserver`) | YSQL (`5433`), DocDB Raft RF=3, bounded memory limits |
| **`cockroach`** | #6 CockroachDB | 3-node RF=3 cluster | CockroachDB (`v24.x`) | SQL (`26257`), `--insecure` lab mode, capped `--cache` & `--max-sql-memory` |
| **`citus`** | #7 Citus | 1 Coordinator + 2 Workers | `citus` on PG 17 | `citus_add_node`, hash-distributed + 2PC reference tables |
| **`baseline`** | #15 Control Baselines | 1 Standalone PG 17; 3-node Patroni | `postgres:17`; Patroni + `etcd` | Single-writer WAL baseline (`synchronous_commit=on` / `remote_apply`) |

---

## 3. Schema Standardization: The `pgbench_history` Keyless Problem

Standard `pgbench -i -s 10` initializes four tables: `pgbench_branches`, `pgbench_tellers`, `pgbench_accounts` (all with `PRIMARY KEY`), and **`pgbench_history`** — which ships **without a Primary Key or `REPLICA IDENTITY`**.

That schema quirk is analytically critical:
1. During **empirical limits testing (`L2`)**, `pgbench_history` deliberately remains keyless to prove and capture exact failures (`SQLSTATE 55000` on logical `UPDATE`/`DELETE`, or Bucardo sync rejection).
2. During **throughput benchmarking (`Suites A–D`)**, a standardized surrogate Primary Key (`hid BIGSERIAL` stepped per node, `snowflake.nextval()`, or `unique_rowid()`) is added consistently across topologies so every multi-master engine can replicate TPC-B history appends and cleanups without asymmetric schema disqualification.

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

## 6. Performance Benchmark Suites (`Suites A–E`)

After `F1–F10` and `L1–L8` complete cleanly, each cluster runs five standardized workload suites (`PG_BENCH_SCALE=10`, warmed cache, fixed timed windows):

- **Suite A — `pgbench` TPC-B-like Read-Write:** Measures mixed `SELECT`/`UPDATE`/`INSERT` throughput (`TPS`) and `p50`/`p95`/`p99` latency across concurrency tiers (`1, 4, 16, 32` clients) routed across active nodes.
- **Suite B — `pgbench -S` Select-Only:** Isolates horizontal read scaling across multi-node endpoints vs single-primary HAProxy pools.
- **Suite C — `pgbench -N` Simple-Update:** Removes `pgbench_branches`/`pgbench_tellers` global lock contention to measure pure multi-node indexed row update scaling.
- **Suite D — Custom Hot-Row Conflict & Contention Script:** Directs competing writers simultaneously at overlapping vs partitioned key ranges to measure `SQLSTATE 40001` retry tax, lock wait amplification, and async Lost Update rates.
- **Suite E — `sysbench` OLTP (`--db-driver=pgsql`):** Cross-validates `oltp_read_write`, `oltp_read_only`, and `oltp_write_only` multi-table range scans and point lookups outside `pgbench` biases.

*All empirical measurements from Suites A–E and Protocols F/L will be reported verbatim in Chapter 06 upon execution.*

---

## 7. Threats to Validity: Local Docker Lab vs Production

Honest interpretation of Chapter 06 requires acknowledging five structural gaps between a single-host Docker lab and multi-AZ/WAN production clusters:

1. **Sub-Millisecond Loopback RTT:** Docker bridge round-trips measure `< 0.5 ms` compared to `1–3 ms` cross-AZ or `40–150 ms` transoceanic WAN links. Consensus penalties (`2 * RTT`) that look modest locally dominate WAN deployments.
2. **Shared CPU & NVMe Contention:** Three database containers share host CPU threads, Linux page cache, and one physical storage stack, exaggerating throughput collapse at high client concurrency.
3. **Virtualization Storage Stack:** WSL2 virtual disk/overlayfs layers alter `fsync()` durability timing compared to dedicated bare-metal NVMe RAID or cloud EBS volumes.
4. **Correlated Failure Domain:** Stopping containers simulates process/network loss cleanly, not independent host kernel panics or asymmetric split-brain partitions with asymmetric routing.
5. **Memory Capping:** Tight container memory caps protect host stability (`16.4 GiB`) but constrain large RocksDB/Pebble compactions and PostgreSQL `shared_buffers` below production sizing.

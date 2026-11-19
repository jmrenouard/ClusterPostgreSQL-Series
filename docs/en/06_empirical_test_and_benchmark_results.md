# 06 — Empirical Test and Benchmark Results

**Series:** PostgreSQL Multi-Master & Active-Active Architectures  
**Author:** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr)  
**License:** MIT License

---

## 1. Executed Test Configuration & Dataset Parity

All benchmarks were executed sequentially on a 20-vCPU, 16.4 GiB WSL2 Docker host using an isolated `bench_client` container (`multi-db-pgbench-sysbench:latest`) attached directly to each cluster's Docker bridge network. Every topology ran at uniform scale **`PG_SCALE = 2`** (`200,000` `pgbench_accounts`, `20` `pgbench_tellers`, `2` `pgbench_branches`) after warm-up, with a standardized surrogate Primary Key on `pgbench_history` (stepped `BIGINT` on `pg-birep`/`bucardo`, `snowflake.nextval()` on `pgedge`, composite `PRIMARY KEY(aid, hid)` on `citus`, `unique_rowid()` on `cockroach`, `BIGSERIAL` on `yugabyte` and baselines).

*Methodological note:* While Chapter 05 defines `PG_BENCH_SCALE=10` as an initial target, the live cross-engine matrix standardized on `PG_SCALE=2` so all eight topologies—including CockroachDB and trigger-based Bucardo—initialized cleanly within bounded startup windows without host RAM throttling.

---

## 2. Core Throughput & Latency Results (Suites A, B1, B2, C)

The table below consolidates verbatim metrics from `results/benchmark_summary.csv` across `pgbench` Single-Node RW (`Suite A`, `8` clients, `20 s`), Disjoint Multi-Node RW (`Suite B1`, `2x4` clients, `20 s`), Overlapping Multi-Node RW (`Suite B2`, `2x4` clients, `20 s`), and Select-Only Read Scaling (`Suite C`, `16` clients, `20 s`).

| Topology | Suite A TPS (`avg ms`) | Suite B1 Disjoint TPS (`avg ms`) | Suite B2 Overlap TPS (`avg ms`) | B2 Retries (`40001`) | B2 Balance Drift | Suite C RO TPS (`avg ms`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **#15 `pg17-standalone`** | `866.82` (`9.22`) | `920.07` (`8.68`) | `879.01` (`9.09`) | `0` | `0` | **`55,614.16`** (`0.257`) |
| **#15 `pg17-sync-streaming`** | `409.48` (`19.52`) | `407.41` (`19.61`) | `465.22` (`17.17`) | `0` | `0` | `54,483.07` (`0.271`) |
| **#1 `pg-birep`** | `875.91` (`9.12`) | `820.09` (`9.74`) | `1,228.60` (`6.50`) | `0` | **`-4,567` (Diverged)** | `53,072.52` (`0.279`) |
| **#2 `pgedge` (Spock 5)** | `556.06` (`14.37`) | `346.95` (`23.03`) | `818.65` (`9.76`) | `0` | **`-66,328` (Lost)** | `54,124.99` (`0.273`) |
| **#9 `bucardo`** | `735.38` (`10.86`) | `1,078.90` (`7.40`) | **`1,267.77`** (`6.30`) | `0` | **`+123,679` (Lost)** | `53,731.92` (`0.274`) |
| **#7 `citus`** | `309.04` (`25.85`) | `265.29` (`30.12`) | `312.98` (`25.53`) | `0` | `0` | `21,324.70` (`0.724`) |
| **#5 `yugabyte`** | `173.64` (`45.88`) | `194.75` (`41.04`) | `170.19` (`46.96`) | `0` | `0` | `17,150.58` (`0.922`) |
| **#6 `cockroach`** | `42.08` (`187.60`) | `60.35` (`132.32`) | `74.17` (`106.44`) | `96` | `0` | `13,185.54` (`1.199`) |

### Key Insights from Suites A–C

1. **Synchronous WAL Penalty (`#15`):** Enabling `synchronous_commit=on` against one local standby cuts `pg17-standalone` single-node RW throughput by **`52.8%`** (`866.82 -> 409.48 TPS`) and doubles `p95` latency (`23.96 -> 50.31 ms`), quantifying the physical `fsync` + network round-trip floor.
2. **Disjoint Partitioning vs Overlap (`B1` vs `B2`):** Under strict disjoint key ranges (`B1`), `pg-birep` (`820.09 TPS`), `pgedge` (`346.95 TPS`), and `bucardo` (`1,078.90 TPS`) achieved **zero balance drift** (`0`). The instant multi-node workloads touched overlapping accounts (`B2`), raw TPS increased (`1,228.60` / `818.65` / `1,267.77 TPS`) solely because asynchronous writers skipped distributed locks—corrupting balances via `-4,567`, `-66,328`, and `+123,679` unit drifts! Notably, `pg-birep` did not even converge (`node1: -193,944` vs `node2: -208,996` vs expected `-189,377`).
3. **Read-Only Scaling (`Suite C`):** Native PostgreSQL heap engines sustained `53,072–55,614 TPS` at `< 0.3 ms` average latency (`16` clients). Coordinator/LSM engines traded raw point-lookup speed for distributed routing: Citus (`21,324.70 TPS`), YugabyteDB (`17,150.58 TPS`), and CockroachDB (`13,185.54 TPS`).
4. **Wait-on-Conflict vs Optimistic `SERIALIZABLE`:** YugabyteDB (`READ COMMITTED` default) ran Suites A–C with **`0` `40001` retries**, outperforming CockroachDB (`SERIALIZABLE` default) by **`4.1x`** on Suite A (`173.64` vs `42.08 TPS`), where CockroachDB logged `44` (`A`), `87` (`B1`), and `96` (`B2`) serialization retries across hot `pgbench_branches` updates (`p95 = 625.04 ms` in Suite A).

---

## 3. Suite D — Hot-Row Contention & `spock.delta_apply` Validation

Suite D (`15 s`, `8` total clients targeting `50` hot accounts `aid = 1..50` with `abalance = abalance + delta`) empirically isolates **non-commutative Lost Updates** versus CRDTs and consensus serialization:

| Topology | TPS | `lat_avg_ms` (`p95`) | Expected `SUM(delta)` | Observed `SUM(abalance)` | `balance_drift` | Convergence Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`pg17-standalone`** | `3,128.63` | `2.54` (`3.95`) | `2,362,664` | `2,362,664` | `0` | `PASS_SINGLE_PRIMARY` |
| **`pg17-sync-streaming`** | `1,370.10` | `5.83` (`8.73`) | `1,035,721` | `1,035,721` | `0` | `PASS_SINGLE_PRIMARY` |
| **`pg-birep`** | `1,231.15` | `6.48` (`13.01`) | `922,873` | `n1: 851,810 / n2: 851,747` | **`-71,063`** | **`EXPECTED_LIMITATION_DIVERGED`** |
| **`pgedge` (Default LWW)** | `2,280.11` | `3.49` (`5.31`) | `1,737,102` | `1,458,404` (all 3) | **`-278,698`** | **`EXPECTED_LIMITATION_LOST_UPDATE`** |
| **`pgedge-delta-apply`** | **`1,837.64`** | `4.34` (`9.35`) | `1,391,780` | `1,391,780` (all 3) | **`0`** | **`PASS_CONVERGED` (CRDT)** |
| **`bucardo`** | `1,378.79` | `5.79` (`8.03`) | `1,046,798` | `515,178` (both) | **`-531,620`** | **`EXPECTED_LIMITATION_LOST_UPDATE`** |
| **`citus`** | `1,691.45` | `4.72` (`6.72`) | `1,283,370` | `1,283,370` | `0` | `PASS_CONVERGED` |
| **`yugabyte`** | `832.65` | `9.59` (`15.14`) | `624,295` | `624,295` | `0` | `PASS_CONVERGED` |
| **`cockroach`** | `471.61` | `16.91` (`34.17`) | `359,402` | `359,402` | `0` | `PASS_CONVERGED` |

This experiment yields a definitive architectural result:
- **Silent Corruption Under Async LWW:** `pgedge` LWW looked fastest (`2,280.11 TPS`), yet silently discarded **`16.0%`** (`-278,698`) of committed credits. `bucardo` lost **`50.8%`** (`-531,620`) of committed money! `pg-birep` diverged even between its two nodes (`-71,063` on `node1`, `-71,126` on `node2`).
- **CRDT Delta-Apply Proof:** Enabling `ALTER TABLE pgbench_accounts ALTER COLUMN abalance SET (log_old_value=true, delta_apply_function=spock.delta_apply)` on `pgedge` preserved **`1,837.64 TPS`** across 3 active writers with **`0` balance drift**—delivering `2.2x` higher hot-key throughput than YugabyteDB and `3.9x` higher than CockroachDB while remaining `PA/EL`.

---

## 4. Suite E (`sysbench` OLTP) & Suite F (WAN `tc netem 25ms`)

To avoid single-benchmark bias (`pgbench`) and sub-millisecond Docker loopback illusions, Suites E (`sysbench oltp_read_write`, `4` tables x `10,000` rows, `8` threads, `20 s`) and F (`tc qdisc replace dev eth0 root netem delay 25ms` on peer/standby/worker/voter containers, `~50 ms` effective RTT) stress multi-statement queries and real WAN physics:

| Topology | Suite E `sysbench` TPS | Suite E QPS (`p95 ms`) | Suite E `tx_failed` | Suite A Local TPS | Suite F `netem 25ms` TPS (`p95 ms`) | WAN Drop |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`pg17-standalone`** | `1,129.51` | `22,687.48` (`7.56`) | `112` | `866.82` | N/A | N/A |
| **`pg17-sync-streaming`** | `819.36` | `16,493.23` (`11.65`) | `118` | `409.48` | **`57.00`** (`353.49`) | **`-86.1%`** |
| **`pg-birep`** | `1,105.32` | `22,192.83` (`10.84`) | `96` | `875.91` | **`824.04`** (`24.95`) | `-5.9%` |
| **`pgedge` (Spock 5)** | `888.56` | `17,873.46` (`15.27`) | `114` | `556.06` | **`646.77`** (`32.40`) | `0%` (+16% var) |
| **`bucardo`** | **`1,232.84`** | `24,757.64` (`7.70`) | `112` | `735.38` | **`763.23`** (`27.26`) | `0%` (+4% var) |
| **`citus`** | `189.44` | `3,796.81` (`50.11`) | `9` (of `3,797`) | `309.04` | **`21.67`** (`633.96`) | **`-93.0%`** |
| **`yugabyte`** | `128.24` | `2,564.80` (`81.48`) | **`0`** (of `2,574`) | `173.64` | **`5.78`** (`3,401.33`) | **`-96.7%`** |
| **`cockroach`** | `44.84` | `1,531.47` (`502.20`) | **`685`** (of `902`) | `42.08` | **`10.06`** (`2,930.54`) | **`-76.1%`** |

### Two Critical Production Realities Exposed by Suites E & F

1. **Client Drivers Without Retry Loops Collapse Under `SERIALIZABLE` (`Suite E`):** While `pgbench --max-tries=100` masked CockroachDB's `40001` aborts in Suites A–B2, stock `sysbench` lacks PostgreSQL `40001` retry handling and suffered **`685` ignored errors alongside `902` successful commits (`43.2%` abort exposure)** at `502.20 ms` `p95` latency. Meanwhile, YugabyteDB's `READ COMMITTED` Wait-on-Conflict sustained **`0` errors** (`128.24 TPS`).
2. **PACELC `EC` Tax Over WAN (`Suite F`):** Introducing a `25 ms` one-way delay (`~50 ms` RTT) onto peer nodes crushed synchronous consensus and cross-shard engines cleanly in line with Chapter 02's latency equation:
   - `pg17-sync-streaming` collapsed by `-86.1%` (`57.00 TPS`, `avg = 139.56 ms`).
   - `citus` collapsed by `-93.0%` (`21.67 TPS`, `avg = 364.81 ms`) as multi-shard TPC-B statements paid cross-worker RTTs and 2PC overhead.
   - `yugabyte` (`5.78 TPS`, `avg = 1,327.30 ms`, `p95 = 3,401.33 ms`) and `cockroach` (`10.06 TPS`, `avg = 715.77 ms`, `14` retries) dropped `-96.7%` and `-76.1%` because each TPC-B transaction touched multiple non-colocated tablets/ranges (`accounts`, `tellers`, `branches`, `history`), paying repeated `2 * RTT` distributed commit trips.
   - Asynchronous `PA/EL` systems (`pg-birep` `824.04 TPS`, `pgedge` `646.77 TPS`, `bucardo` `763.23 TPS`) committed locally without waiting for WAN round-trips.

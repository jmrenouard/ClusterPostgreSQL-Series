# 09 — Benchmark Methodology, Workloads & Logarithmic Charts

**Series:** PostgreSQL Multi-Master & Active-Active Architectures  
**Author:** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr)  
**License:** MIT License

---

## 1. Execution Harness & Controlled Isolation

All **310 raw benchmark rows** (**301 deduplicated dashboard rows**) across **17 live topologies** (`18` variants on Suite D incl. `pgedge-delta-apply`) are generated sequentially on a 20-vCPU, 16.4 GiB WSL2 Docker host via three runners under `env/multi-db-docker-env` (`v2.4.1`):
- `scripts/bench_pg_v2_runner.sh`: **187 rows** across 10 PG 17 & Distributed SQL topologies (`results/benchmark_summary.csv` `70`, `results/benchmark_extended_workloads.csv` `40`, `results/benchmark_wan_sweep.csv` `27`, `results/benchmark_concurrency_sweep.csv` `50`).
- `scripts/bench_pg18_runner.sh`: **87 rows** across 5 PG 18.6 native topologies (`results/benchmark_pg18.csv`).
- `scripts/bench_yt_runner.sh`: **36 rows** (`18` `yt-cluster` `cc=half` + `18` `yt-cluster-async` `cc=nodes>=0`) on 3-node PG 18.7 (`results/benchmark_yt_cluster.csv`).

- **One-Stack Isolation:** Exactly one cluster runs at a time (`up -> setup -> warm-up -> suites -> down -v`) to eliminate RAM/NVMe noise across RocksDB, Pebble, `ytserv`, and PostgreSQL `shared_buffers`.
- **Zero NAT Skew:** `pgbench` and `sysbench` execute inside an ephemeral `bench_client` container (`multi-db-pgbench-sysbench:latest`) attached directly to each cluster's internal Docker bridge (`--cap-add NET_ADMIN`).
- **Dataset Parity & Reconciliation:** Every suite uses `PG_SCALE = 2` (`200,000` `pgbench_accounts`, `20` `pgbench_tellers`, `2` `pgbench_branches`). Between write suites, `reset_ds()` zeroes balances and truncates `pgbench_history`; `conv_chk()` then verifies `SUM(abalance) - SUM(delta)` on every node (`balance_drift`).
- **Exact Tail Latency (`p95`):** Per-transaction logs (`pgbench -l`) yield exact mean, stddev, and 95th percentile (`lat_p95_ms`).

---

## 2. Schema Standardization Across Engines

Standard `pgbench -i` leaves `pgbench_history` **keyless**, breaking logical replication `UPDATE`/`DELETE` (`SQLSTATE 55000`) and Bucardo sync validation. To evaluate all 17 stacks fairly while testing keyless limits separately in `L2`, the harness injects an engine-idiomatic surrogate Primary Key `hid`:

| Topology Group | `pgbench_history` Surrogate PK & Distribution Adaptation | `sysbench` Adaptation |
| :--- | :--- | :--- |
| **`pg17-*`, `pg18-streaming/logical`, `yugabyte`** | `hid BIGSERIAL PRIMARY KEY` | Standard `sbtest1..4` (replicated on streaming/logical) |
| **`pg-birep` & `bucardo`** | Stepped sequence `INCREMENT BY 2 START WITH {1, 2}` (`BIGINT PK`) | Standard `sbtest1..4` (synced across nodes) |
| **`pg18-birep` & `yt-cluster*`** | Native PG 18 `hid UUID PRIMARY KEY DEFAULT uuidv7()` (`yt_setup()` on `yt*`) | `yt_setup('public.sbtest%')`; isolated `prep_sb()` before `E3` async (avoids `55000` `recon` lock) |
| **`pgedge` (Spock 5)** | `hid BIGINT PRIMARY KEY DEFAULT snowflake.nextval('snowflake.id_seq')` | Standard; `delta_apply` tested on `abalance` |
| **`citus`** | Composite `PRIMARY KEY(aid, hid)` + `create_distributed_table` (`bid`/`tid`/`aid`) | `create_distributed_table('sbtest1..4','id')` |
| **`cockroach`** | `hid INT8 DEFAULT unique_rowid() PRIMARY KEY` | Auto-fallback `--db-ps-mode=disable` if needed |

---

## 3. Complete Workload & Tool Specification

### 3.1 `pgbench` Suites (`A`, `B1`, `B2`, `C`, `D`, `G`, `H`)

All `pgbench` runs use `-n -r --max-tries=100 --failures-detailed -l` to count client-side `SQLSTATE 40001` retries explicitly (`55409`+`40001` in YT Cluster):

| Suite ID | Workload Profile | Clients / Streams | Window | Empirical Span Across 17 Topologies |
| :--- | :--- | :---: | :---: | :--- |
| **`A_single_rw`** | Standard TPC-B RW (`1` endpoint) | `8` (`1x8`, `-j 4`) | `15–20 s` | `20.63` (`yt-cluster`) to `875.91 TPS` (`pg-birep`) |
| **`B1_disjoint_rw`** | Partitioned keys (`1..100k` vs `100k+1..200k`) | `8` (`2x4`, `-j 2`) | `15–20 s` | `36.14` (`yt-cluster`) to `1,078.90 TPS` (`bucardo`) |
| **`B2_overlap_rw`** | Full overlapping keyspace on `2` writers | `8` (`2x4`, `-j 2`) | `15–20 s` | `10.69` (`yt-cluster`, `0` drift) to `1,267.77 TPS` (`bucardo`, `+123,679`) |
| **`C_multinode_ro`** | `pgbench -S` Select-Only lookups | `16` (`2x8`/`1x16`) | `15–20 s` | `13,185.54` (`cockroach`) to `55,614.16 TPS` (`pg17-standalone`) |
| **`D_hot_conflict`** | `50` hot rows (`aid 1..50`, `delta 1..100`) | `8` (`2x4`/`1x8`) | `12–15 s` | `67.76` (`yt-cluster`, `0` drift) to `3,128.63 TPS`; CRDT `1,837.64` (`0` drift) |
| **`G_conc_c1..c32`** | Concurrency sweep ($c \in \{1, 4, 8, 16, 32\}$) | `1..32` | `8 s` | `4.60` (`yt c=32`) to `814.33 TPS` (`pg17-standalone` `801`, `pg18-standalone c=32`) |
| **`H_append_only_insert`** | Pure `INSERT INTO bench_append_events` | `8` (`2x4`/`1x8`) | `12 s` | `110.53` (`yt-cluster`) to `3,518.49 TPS` (`pg18-logical`); `yb=2,987.24` |

### 3.2 `sysbench` OLTP Suites (`E1–E4`, `--db-driver=pgsql`)

Cross-validation runs `sysbench --db-driver=pgsql --tables=4 --table-size=10000` across four Lua workloads: **`E_sysbench_oltp_rw`** (`oltp_read_write`, `8` threads, `15–20 s`), **`E2_sysbench_oltp_ro`** (`oltp_read_only`, `8` threads, `12 s`), **`E3_sysbench_oltp_wo`** (`oltp_write_only`, `8` threads, `12 s`), and **`E4_sysbench_point_select`** (`oltp_point_select`, `16` threads, `12 s`).

- **Critical `40001` & Async `55000` Handling:** Unlike MySQL runs using `--mysql-ignore-errors=all`, stock `sysbench --db-driver=pgsql` lacks `SQLSTATE 40001` retry loops (`685` ignored errors alongside `902` commits on CockroachDB `E`, vs `0` errors on YugabyteDB `READ COMMITTED` `128.24 TPS`). On `yt-cluster-async`, reusing post-`E` `sbtest` tables triggered `SQLSTATE 55000` (`recon` row blocked); fresh per-suite `prep_sb()` yielded **`133.55 TPS` (`E3`)**. Point-select (`E4`) peaked at **`177,442.88 TPS`** (`0.09 ms` avg) on `yt-cluster-async` and **`148,022.41 TPS`** on `pg17-async-streaming` vs `11,557–19,831 TPS` on distributed engines.

### 3.3 WAN Latency Injection (`F_wan_netem_10ms / 25ms / 50ms`)

WAN RTT physics are emulated via Linux `tc qdisc netem` inside peer/standby/worker/voter network namespaces (`~20`, `~50`, and `~100 ms` effective RTT), cleaned up deterministically via `tc qdisc del dev eth0 root` (in YT Cluster `r_wan`, targeting a deterministic non-Leader node `wn` prevents Leader-affinity bypass):

```bash
docker run --rm --network container:<peer> --cap-add NET_ADMIN \
  multi-db-pgbench-sysbench:latest tc qdisc replace dev eth0 root netem delay 25ms
```

Under `50 ms` egress delay (`~100 ms` RTT), `PC/EC` and `ytserv` engines dropped to **`25.79 TPS`** (`pg17-sync-streaming`), **`8.84 TPS`** (`citus`), **`4.53 TPS`** (`cockroach`), **`3.06 TPS`** (`yugabyte`), **`2.90 TPS`** (`yt-cluster-async`), and **`1.41 TPS`** (`yt-cluster`), whereas `PA/EL` async topologies sustained `612.56–782.57 TPS` (`pg18-birep` `782.57`, `pgedge` `687.00`).

---

## 4. Why Logarithmic (`log10`) Scales Are Mathematically Mandatory

Across all **310 raw benchmark rows**, measurements span **over five orders of magnitude**:
- **Throughput (`TPS`):** `1.41 TPS` (`yt-cluster`, `F_wan_netem_50ms`) to `177,442.88 TPS` (`yt-cluster-async`, `E4_sysbench_point_select`) — dynamic ratio $R_{\text{TPS}} = 177{,}442.88 / 1.41 \approx 125{,}846\times$ ($5.10$ decades; core `pgbench` `2.25` to `55,614.16 TPS` spans $4.39$ decades).
- **Latency (`ms`):** `0.090 ms` (`yt-cluster-async` `E4` avg; `0.110 ms` PG 17 `E4`) to `12,893.483 ms` (`yt-cluster-async`, `F_wan_netem_50ms` `p95`; `5,474.705 ms` on `yugabyte`) — dynamic ratio $R_{\text{lat}} = 12{,}893.483 / 0.090 \approx 143{,}261\times$ ($5.16$ decades).

The decade span $D_{\text{decades}}$ and visual distance $\Delta y_{\log}$ between any two engines $(v_1, v_2)$ obey:

$$
D_{\text{decades}} = \log_{10}\!\left(\frac{v_{\max}}{v_{\min}}\right), \qquad \Delta y_{\log} = \log_{10}(v_2) - \log_{10}(v_1) = \log_{10}\!\left(\frac{v_2}{v_1}\right)
$$

On a linear axis scaled to `55,614` or `177,443 TPS`, a `57.00 TPS` sync WAN bar occupies `< 0.04%` pixel height and `1.41 TPS` disappears completely (`0.0008%`). A `log10` axis maps every `2x` speedup to an identical step ($\log_{10}(2) \approx 0.301$), preserving multiplicative ratios across all decades.

---

## 5. Interactive Dashboard & Seven Logarithmic Charts

Explore all 10 topologies and 187 rows interactively—with **default `log10` / linear toggle**, multi-solution selector pills, EN/FR UI, drift badges, 18-test Functional/Limits Matrix (`L1–L8` + `T11–T18`), and filtered CSV export—in the offline-capable [**Interactive Benchmark Explorer (`dashboard/index.html`)**](../../dashboard/index.html).

### Chart 01 — Multi-Suite Throughput (`log10` TPS)
![Log10 Throughput Across Core Suites](../../assets/charts/chart_01_tps_log_all_suites.png)
*Compares `A_single_rw`, `B1_disjoint_rw`, `C_multinode_ro`, `E_sysbench_oltp_rw`, and `H_append_only_insert` across all 10 topologies (`42.08` to `55,614.16 TPS`).*

### Chart 02 — Average & Tail `p95` Latency (`log10` ms)
![Log10 Average and p95 Latency](../../assets/charts/chart_02_latency_log_all_suites.png)
*Reveals the `4+`-decade latency spread from `0.257 ms` native reads up to `625.04 ms` (`cockroach` Suite A `p95`) and `5,474.71 ms` (`yugabyte` `50 ms` WAN `p95`).*

### Chart 03 — Concurrency Scalability Sweep (`G_conc_c1..c32`, `log10`)
![Log10 Concurrency Scalability Sweep](../../assets/charts/chart_03_concurrency_sweep_log.png)
*Real 5-point curves (`c = 1, 4, 8, 16, 32`): `pg17-standalone` scales to `801.27 TPS`; `pg17-sync` plateaus at `425 TPS`; `cockroach` peaks at `c = 4` (`74.11 TPS`) then drops to `40.25 TPS` (`88` retries, `p95 = 3,400 ms`) at `c = 32`.*

### Chart 04 — WAN RTT Sensitivity Sweep (`tc netem 0/10/25/50 ms`, `log10`)
![Log10 WAN Latency Sensitivity Sweep](../../assets/charts/chart_04_wan_netem_sweep_log.png)
*Captures the PACELC split across `0/10/25/50 ms`: `pg17-async` (`587->600->619 TPS`) and `pgedge` (`645->647->687`) stay flat while `pg17-sync` (`122->57->26`), `citus` (`44->22->9`), `cockroach` (`19->10->4.5`), and `yugabyte` (`15->5.8->3.1`) drop exponentially.*

### Chart 05 — `sysbench` Workload Profile (`E1–E4`, `log10`)
![Log10 Sysbench Workload Profile](../../assets/charts/chart_05_sysbench_profile_log.png)
*Contrasts all four Lua profiles (`E1–E4`): native PG stacks hit `1,659–1,806 TPS` (`E2` RO) and `124k–148k TPS` (`E4` point-select) vs distributed `180–522 TPS` (`E2`) and `11.6k–19.8k TPS` (`E4`).*

### Chart 06 — Streaming vs Native Logical vs Multi-Master (`log10`)
![Log10 Streaming vs Logical vs Multi-Master](../../assets/charts/chart_06_streaming_vs_logical_vs_mm.png)
*Directly contrasts all 10 topologies across Chapter 10's five replication tiers (`pg17-async-streaming` `610.15` vs `pg17-logical` `532.38` vs `pg17-sync` `409.48` vs active-active meshes and Raft).*

### Chart 07 — Data Integrity vs Throughput (Suite D Hot-Row Contention)
![Suite D Integrity vs Throughput](../../assets/charts/chart_07_integrity_vs_throughput.png)
*Exposes silent Lost Update drift (`-531,620` `bucardo`, `-278,698` `pgedge` LWW, `-71,063` `pg-birep`) versus **`0` drift** on `pgedge-delta-apply` (`1,837.64 TPS`), `pg17-async`/`logical` (`2,081`/`2,387`), `citus`, `yugabyte`, and `cockroach`.*

---

## 6. V3 Extensions: Ecosystem Telemetry (`chart_08`, `chart_09`) & PostgreSQL 18.6 (`chart_10`)

The V3 benchmark and telemetry expansion adds two modular datasets under the same `log10` visualization standard:
- **Ecosystem Popularity & Vitality ([Ch. 11](11_ecosystem_popularity_and_vitality.md)):** Live GitHub REST/GraphQL telemetry (`21` rows in [`results/project_popularity.csv`](../../results/project_popularity.csv), spanning `3+` decades) rendered in [`chart_08_popularity_stars_forks_log.png`](../../assets/charts/chart_08_popularity_stars_forks_log.png) and [`chart_09_popularity_commits_activity_log.png`](../../assets/charts/chart_09_popularity_commits_activity_log.png).
- **PostgreSQL 18.6 Generational Benchmarks ([Ch. 12](12_postgresql_18_clustering_and_benchmarks.md)):** **87 sequential rows** across all 5 native PG 18.6 topologies ([`results/benchmark_pg18.csv`](../../results/benchmark_pg18.csv)) plus **5 x 26 functional probes** ([`results/functional_limits_pg18.csv`](../../results/functional_limits_pg18.csv)) using identical `PG_SCALE=2` isolation and `uuidv7()` PKs on `pg18-birep`, compared directly against PG 17.11 in [`chart_10_pg18_vs_pg17_log.png`](../../assets/charts/chart_10_pg18_vs_pg17_log.png) and the interactive [`dashboard/index.html`](../../dashboard/index.html).

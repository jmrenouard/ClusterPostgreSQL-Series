<p align="center">
  <img alt="ClusterPostgreSQL-Series — Multi-Master & Active-Active Lab" src="assets/clusterpostgresql-series-logo.png" width="640">
</p>

# ClusterPostgreSQL-Series — PostgreSQL Multi-Master & Active-Active Architectures

**Author:** Jean-Marie Renouard (`jmrenouard`) | **Supported by:** [LightPath](https://www.lightpath.fr) | **License:** [MIT](LICENSE) | **Version française :** [README.fr.md](README.fr.md)

This repository provides a comparative PostgreSQL study, a 36-criterion matrix, and 13 Docker Compose labs ([`jmrenouard/multi-db-docker-env`](https://github.com/jmrenouard/multi-db-docker-env) `v2.6.2`). The harness runs 18 functional/limit probes (`L1-L8`, `T11-T18`) plus PG 18.6 AIO, `uuidv7()`, conflict, and YT `T_REVERT` checks. We collected **628 raw benchmark rows** (**310 baseline `PG_SCALE=2`** / **301 deduplicated** + **318 V5 tuned `PG_SCALE=20`** `pgbench`/`sysbench`/`tc netem`) across **18 live PostgreSQL topologies** (`cockroach-rc` included, `16` solutions / `19` architecture sheets). The repo also stores **22 GitHub popularity rows** (`19` repos + `3` closed/managed), **13 `log10` charts**, and [**`dashboard/index.html`**](dashboard/index.html).

---

## Executive Summary

PostgreSQL is built on a **single-writer WAL engine** (`LSN`, `XID`, `ProcArray`, local heap pages). Turning PostgreSQL into an "active-active multi-master" system forces an unavoidable trade-off along the **PACELC** spectrum:

- **Asynchronous Logical & Trigger Meshes (`PA/EL`):** Nodes commit locally under `15 ms` even with `50 ms` WAN RTT (`647–824 TPS`). Contended workloads lose updates (`-71K` to `-531K` drift) or stall on `23505`. **CRDT Delta-Apply** avoids this (`spock.delta_apply` reached `1,837.64 TPS` with **`0` drift**).
- **Distributed Consensus Raft/Paxos (`PC/EC`):** Raft guarantees `RPO = 0` and `0` drift. Cross-node RTT cuts throughput (`-76%` to `-97%` under `25 ms` WAN delay). Clients need `SQLSTATE 40001` retries (`sysbench` failed `685` of `1,587` attempts on CockroachDB).
- **Single-Primary HA Control (`#15 Patroni + etcd`):** Remains the lowest-TCO, zero-conflict optimal choice for 80%+ of OLTP workloads.

---

## Empirical Benchmark & Limits Headline Matrix (`PG_SCALE = 2`)

Executed sequentially inside isolated Docker bridge networks on a 20-vCPU / 16.4 GiB host (`results/benchmark_summary.csv`, `results/functional_limits_matrix.csv`):

| Topology (Solution #) | Suite A Single RW (TPS) | Suite B2 Overlap RW (TPS) | Suite D Hot Conflict TPS (`Drift`) | Suite E `sysbench` TPS (`Failed`) | Suite F WAN `25ms` TPS | Verified SQLSTATE Limits |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`pg17-standalone` (#15)** | `866.82` | `879.01` | `3,128.63` (`0`) | `1,129.51` (`112`) | N/A | `23505` (Single writer) |
| **`pg17-async-streaming` (#15)** | `610.15` | `584.80` | `2,081.26` (`0`) | `962.84` (`107`) | **`599.61`** (`-2%`) | `25006` RO; WAL seq `66\|true` |
| **`pg17-sync-streaming` (#15)** | `409.48` | `465.22` | `1,370.10` (`0`) | `819.36` (`118`) | **`57.00`** (`-86%`) | `23505; 25006`; `25.8` @ `50ms` |
| **`pg17-logical` (#16 Uni)** | `532.38` | `355.57` | `2,386.93` (`0`) | `595.81` (`65`) | **`654.11`** (`0%`) | `55000`; seq trap `23505`; `T12` diverge |
| **`pg-birep` (#1 Native)** | `875.91` | `1,228.60` | `1,231.15` (**`-71,063`**) | `1,105.32` (`96`) | **`824.04`** (`-6%`) | `23505` halt; `55000` keyless |
| **`pgedge` (#2 Spock LWW)** | `556.06` | `818.65` | `2,280.11` (**`-278,698`**) | `888.56` (`114`) | **`646.77`** (`0%`) | `23505` transdiscard; LWW loss |
| **`pgedge-delta-apply` (#2 CRDT)** | — | — | **`1,837.64` (`0` drift)** | — | — | Zero drift on delta columns |
| **`bucardo` (#9 Trigger)** | `735.38` | `1,267.77` | `1,378.79` (**`-531,620`**) | `1,232.84` (`112`) | **`763.23`** (`0%`) | PK req; `23505` sync stall |
| **`citus` (#7 Sharded 2PC)** | `309.04` | `312.98` | `1,691.45` (`0`) | `189.44` (`9`) | **`21.67`** (`-93%`) | `0A000` non-dist `UNIQUE`; `40001` |
| **`yugabyte` (#5 DocDB Raft)** | `173.64` | `170.19` | `832.65` (`0`) | `128.24` (`0`) | **`5.78`** (`-97%`) | `40001` (`RR`); `0A000` `LISTEN`; `2/3` halt |
| **`cockroach` (#6 Pebble Raft)** | `42.08` | `74.17` | `471.61` (`0`) | `44.84` (**`685`**) | **`10.06`** (`-76%`) | `40001`; `XCEXF`; `42601`; `57014` (`2/3`) |

### PostgreSQL 18.6 Target Topologies (`results/benchmark_pg18.csv`, `PG_SCALE = 2`)

Measured sequentially in the same isolated Docker harness on `PostgreSQL 18.6 (Debian 18.6-1.pgdg13+2)` with default `io_method=worker` (`io_workers=3`) and `data_checksums=on` (see [Solution #17](docs/en/solutions/pg18_native_clustering.md) and [Chapter 12](docs/en/12_postgresql_18_clustering_and_benchmarks.md)):

| Topology (`#17` PG 18.6) | `A_single_rw` TPS | `B2_overlap_rw` TPS (`Drift`) | `D_hot_conflict` TPS (`Drift`) | `E_sysbench_oltp_rw` TPS (`Failed`) | `H_append_only_insert` TPS | `F_wan_netem_25ms` TPS | Verified `SQLSTATE` Limits |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`pg18-standalone`** | `784.43` | `506.21` (`0`) | `2,117.66` (`0`) | `1,046.67` (`74`) | `1,956.76` | N/A | `23505`; `42601` (`FOR ALL SEQUENCES`) |
| **`pg18-async-streaming`** | `558.34` | `353.30` (`0`) | `2,277.43` (`0`) | `980.72` (`75`) | `1,423.07` | **`554.93`** | `25006` RO standby; WAL seq `66\|true` |
| **`pg18-sync-streaming`** | `497.94` | `472.20` (`0`) | `1,223.75` (`0`) | `767.63` (`76`) | `1,760.26` | **`41.56`** | `25006`; `SyncRep` stall; `25.60` @ `50ms` |
| **`pg18-logical`** | `314.26` | `475.08` (`0`) | `2,998.37` (`0`) | `1,027.84` (`79`) | **`3,518.49`** | **`844.10`** | `23505`; `42601`; `55000` (`substream=p`) |
| **`pg18-birep`** (`uuidv7()`) | `514.28` | `792.45` (**`-338`**) | `1,774.11` (**`-83,252`**) | `1,055.55` (`76`) | **`2,066.70`** (`3.30x`) | **`747.42`** | `23503`; `23505`; `42601`; `55000`; 7 `confl_*` |
| **`yt-cluster`** (`#18` `cc=half`) | `20.63` | `10.69` (`0`) | `67.76` (`0`) | `28.48` (`12`) | `110.53` | `2.25` | `0A000`; `40001`; `55409`; `57P03` (`T_REVERT` OK) |
| **`yt-cluster-async`** (`#18` `nodes>=0`) | `41.45` | `55.03` (`0`) | `163.01` (`0`) | `124.05` (`34`) | `224.93` | `4.78` | `40001`; `55000`; `55409` (`2.0x-5.1x` vs `half`, `0` drift) |

*Note: `yt-cluster` / `yt-cluster-async` ran on 3-node `dbinvent/yt:1.21.3` (PG 18.7 + `yt_cluster 1.21` / `ytserv`, `results/benchmark_yt_cluster.csv`, `36` rows across 18 suites). See [Solution #18](docs/en/solutions/yt_cluster_lite.md) and [Chapter 06 §7](docs/en/06_empirical_test_and_benchmark_results.md).*

---

## Interactive Benchmark Explorer & Logarithmic Charts (`log10`)

Open [**`dashboard/index.html`**](dashboard/index.html) offline in any browser with zero CDN dependencies and an EN/FR switcher. Toggle **Baseline `PG_SCALE=2` (`301` rows)** vs **Tuned `PG_SCALE=20` (`318` rows)**, or open `compare`. Use 18-topology presets (`YT vs Multi-Master`), `log10`/linear axes, `L1-L8`/`T11-T18`/`PG 18.6`/`YT` tabs, Popularity (`22` rows), and CSV export. Browse the **13 charts** in [Chapter 09](docs/en/09_benchmarks_methodology_and_charts.md) (`chart_01`-`07`), [Chapter 11](docs/en/11_ecosystem_popularity_and_vitality.md) (`chart_08`-`09`), and [Chapter 12](docs/en/12_postgresql_18_clustering_and_benchmarks.md) (`chart_10`). See [Chapter 06 §7–§8](docs/en/06_empirical_test_and_benchmark_results.md) (`chart_11`) and [**Chapter 13 (`PG_SCALE=20`)**](docs/en/13_production_tuning_and_realistic_benchmarks.md) (`chart_12`-`13`).

> **Live GitHub Pages & PACELC Architecture Selector:** Browse the hosted [**GitHub Pages Benchmark Explorer**](https://jmrenouard.github.io/ClusterPostgreSQL-Series/) (Pages workflow tracked in `#506`) or open the **PACELC Selector** tab locally to score all 17 topologies + V5/CRDT variants across `RPO`, `WAN RTT`, write conflicts, and `TCO` with copyable `Makefile` / `./mdb` commands and EN/FR sheet links.

![Log10 Throughput All Suites](assets/charts/chart_01_tps_log_all_suites.png)

![Log10 Latency All Suites](assets/charts/chart_02_latency_log_all_suites.png)

![Streaming vs Logical vs Multi-Master Log10](assets/charts/chart_06_streaming_vs_logical_vs_mm.png)

![Ecosystem Popularity Stars and Forks Log10](assets/charts/chart_08_popularity_stars_forks_log.png)

![Ecosystem Commits and Maintenance Vitality Log10](assets/charts/chart_09_popularity_commits_activity_log.png)

![PostgreSQL 18.6 vs PostgreSQL 17.11 Head-to-Head Log10](assets/charts/chart_10_pg18_vs_pg17_log.png)

![YT Cluster vs Active-Active Multi-Master and Raft Log10](assets/charts/chart_11_yt_cluster_vs_multimaster_log.png)

![Log10 Baseline vs Production-Tuned Throughput](assets/charts/chart_12_baseline_vs_optimized_log.png)

![Log10 Production-Tuned Panorama Across All 18 Topologies](assets/charts/chart_13_optimized_all_topologies_log.png)

> **V5 Production-Tuned Highlight (`PG_SCALE=20`, `318` rows, `fsync=on`, `v2.6.1`):** Applying durable tunings (`fillfactor=90`, `wal_compression=lz4`, PG 18/YT `io_method=worker`/`4`, `-M prepared`, `5s` warm-up, Spock `delta_apply`, Citus 1-shard colocation, Yugabyte `RC + CACHE 1000` + HAProxy `:15470`, CockroachDB `v25.4` HAProxy `:15480` + non-root `bench` `cockroach-rc`, YT `YT_MAX_PREPARED=300` + parallel `ytctl` + Leader affinity + Lua `55409` hook) drives `pg18-birep` `G_c32` to `4,163.31 TPS`, keeps `pgedge` at **`0` drift** (`2,125.19 TPS` `D`), lifts CockroachDB `v25.4` **`7.32x`** on `A` (`307.95 TPS`) and `cockroach-rc` to `0` `40001` retries in `sysbench` (`153.70 TPS`), and accelerates `yt-cluster-async` `E4` to **`189,286.48 TPS`** (`0` drift) — see [Chapter 13](docs/en/13_production_tuning_and_realistic_benchmarks.md).

---

## Complete Study Navigation (English & French)

| Chapter | English (`docs/en/`) | Français (`docs/fr/`) |
| :--- | :--- | :--- |
| **01 — Taxonomy** | [01 — Executive Summary & Taxonomy](docs/en/01_executive_summary_and_taxonomy.md) | [01 — Synthèse et taxonomie](docs/fr/01_synthese_et_taxonomie.md) |
| **02 — Theory** | [02 — CAP, PACELC & Conflict Calculus](docs/en/02_theoretical_foundations_cap_pacelc_conflicts.md) | [02 — Fondements théoriques & conflits](docs/fr/02_fondements_theoriques_cap_pacelc_conflits.md) |
| **03a — Native/Ext** | [03a — Native Logical, Extensions & Baselines](docs/en/03a_solutions_native_and_extensions.md) | [03a — Solutions natives & extensions](docs/fr/03a_catalogue_natif_et_extensions.md) |
| **03b — Dist/Cloud** | [03b — Distributed SQL, Triggers & Cloud](docs/en/03b_solutions_distributed_triggers_cloud.md) | [03b — SQL distribué, triggers & cloud](docs/fr/03b_catalogue_distribue_triggers_cloud.md) |
| **04 — Matrices** | [04 — 36-Criterion Feature Comparison](docs/en/04_comprehensive_feature_comparison.md) | [04 — Étude comparative (36 critères)](docs/fr/04_etude_comparative_fonctionnalites.md) |
| **05 — Protocol** | [05 — PoC Architectures & Test Protocol](docs/en/05_poc_architectures_and_test_protocol.md) | [05 — Architectures PoC & protocole](docs/fr/05_architectures_poc_et_protocole_de_test.md) |
| **06 — Benchmarks** | [06 — Empirical Test & Benchmark Results](docs/en/06_empirical_test_and_benchmark_results.md) | [06 — Résultats de tests & benchmarks](docs/fr/06_resultats_tests_et_benchmarks.md) |
| **07 — Guide** | [07 — Decision Framework & Production Guide](docs/en/07_decision_framework_and_production_guide.md) | [07 — Guide de choix & architecture cible](docs/fr/07_guide_de_choix_et_architecture_cible.md) |
| **08 — Limits** | [08 — Limits & Failure Modes Catalog](docs/en/08_limits_and_failure_modes.md) | [08 — Limites & modes de défaillance](docs/fr/08_limites_et_modes_de_defaillance.md) |
| **09 — Charts** | [09 — Benchmarks Methodology & Log10 Charts](docs/en/09_benchmarks_methodology_and_charts.md) | [09 — Méthodologie benchmarks & graphiques](docs/fr/09_methodologie_benchmarks_et_graphiques.md) |
| **10 — 5-Tier** | [10 — Streaming vs Logical vs Multi-Master](docs/en/10_streaming_vs_logical_vs_multimaster.md) | [10 — Streaming vs Logique vs Multi-Maîtres](docs/fr/10_comparatif_streaming_logique_multimaster.md) |
| **11 — Popularity** | [11 — Ecosystem Popularity & Engineering Vitality](docs/en/11_ecosystem_popularity_and_vitality.md) | [11 — Popularité et vitalité de l'écosystème](docs/fr/11_popularite_et_vitalite_ecosysteme.md) |
| **12 — PG 18.6** | [12 — PostgreSQL 18.6 Clustering & Benchmarks](docs/en/12_postgresql_18_clustering_and_benchmarks.md) | [12 — Clustering PostgreSQL 18.6 et benchmarks](docs/fr/12_clustering_postgresql_18_et_benchmarks.md) |
| **13 — V5 Tuning** | [13 — Production Tuning & Realistic Scale Benchmarks](docs/en/13_production_tuning_and_realistic_benchmarks.md) | [13 — Optimisation de Production et Benchmarks Réalistes](docs/fr/13_optimisation_production_et_benchmarks_realistes.md) |

---

## Solutions Catalog & Architecture Sheets (`19` EN + FR Deep Dives)

Every evaluated solution has an EN (`docs/en/solutions/`) and FR (`docs/fr/solutions/`) sheet. Each sheet provides Mermaid diagrams, modes, strengths, weaknesses, and verified metrics or exclusion baselines.

> **Catalog ID Disambiguation (`#16` vs `#14`):** `pg17-logical` uses **`#16`** (`T3`, native uni-directional logical replication), whereas **`#14`** is reserved for Legacy Trigger Systems (`Slony-I / Londiste / RubyRep`); legacy CSV tables tag `pg17-logical` as `#14 Baseline`.

| Solution & Dedicated Sheet | Product / Docs Link | GitHub Repository | Brief Description |
| :--- | :--- | :--- | :--- |
| **[#1 — PostgreSQL 17 Bidirectional Logical](docs/en/solutions/pg17_bidirectional_logical.md)** | [PG 17 Docs](https://www.postgresql.org/docs/17/logical-replication-subscription.html) | [`postgres/postgres`](https://github.com/postgres/postgres) | Core PG 16/17+ active-active logical mesh using `origin = none` (`PA/EL`) with zero extensions, halting on `23505` PK collisions without autonomous conflict resolution. |
| **[#2 — pgEdge Platform / Spock v5](docs/en/solutions/pgedge_spock.md)** | [pgEdge Docs](https://docs.pgedge.com/) | [`pgEdge/spock`](https://github.com/pgEdge/spock) · [`snowflake`](https://github.com/pgEdge/snowflake) | Open-source logical multi-master extension (`PA/EL`) adding `LWW` resolution, `CRDT` `delta_apply` conflict-free numeric columns, Snowflake IDs, and auto-DDL propagation. |
| **[#3 — pglogical 2](docs/en/solutions/pglogical2.md)** | [pglogical Docs](https://www.enterprisedb.com/docs/pglogical/latest/) | [`2ndQuadrant/pglogical`](https://github.com/2ndQuadrant/pglogical) | Extension-based asynchronous logical replication (`PA/EL`) offering selective replication sets, configurable conflict policies, and `replicate_ddl_command` without CRDTs. |
| **[#4 — EDB Postgres Distributed (PGD/BDR)](docs/en/solutions/edb_pgd.md)** | [EDB PGD Docs](https://www.enterprisedb.com/docs/pgd/latest/) | Proprietary / N/A | Commercial `bdr` multi-master platform pairing async logical replication and CRDTs (`PA/EL`) with embedded Raft consensus (`CAMO`, Eager, Write-Lead `PC/EC`) and `pgd-proxy`. |
| **[#5 — YugabyteDB (YSQL + DocDB)](docs/en/solutions/yugabytedb.md)** | [YugabyteDB Docs](https://docs.yugabyte.com/) | [`yugabyte/yugabyte-db`](https://github.com/yugabyte/yugabyte-db) | Distributed SQL engine (`PC/EC`) pairing a forked PG C `YSQL` query layer with `DocDB` per-tablet Raft consensus (`RF=3`), HLC ordering, and Wait-on-Conflict `READ COMMITTED`. |
| **[#6 — CockroachDB](docs/en/solutions/cockroachdb.md)** | [CockroachDB Docs](https://www.cockroachlabs.com/docs/stable/) | [`cockroachdb/cockroach`](https://github.com/cockroachdb/cockroach) | Clean-room Go distributed SQL engine speaking `pgwire` over `Pebble` Multi-Raft ranges (`RF=3`, `PC/EC`), enforcing strict `SERIALIZABLE` isolation (`40001` retries) by default. |
| **[#7 — Citus](docs/en/solutions/citus.md)** | [Citus Docs](https://docs.citusdata.com/en/stable/) | [`citusdata/citus`](https://github.com/citusdata/citus) | Pure PostgreSQL horizontal sharding extension (`PC/EC`) orchestrating Coordinator + Worker hash shards, 2PC distributed transactions/reference tables, and optional `Citus MX`. |
| **[#8 — OpenTenBase / Postgres-XL / XC](docs/en/solutions/opentenbase_pgxl.md)** | [OpenTenBase Docs](https://docs.opentenbase.org/) | [`OpenTenBase/OpenTenBase`](https://github.com/OpenTenBase/OpenTenBase) | Shared-nothing MPP PostgreSQL fork (`PC/EC`) with stateless Coordinators, sharded Datanodes, and a centralized Global Transaction Manager (`GTM`) for 2PC (XC retired, XL dormant). |
| **[#9 — Bucardo 5](docs/en/solutions/bucardo.md)** | [Bucardo Site](https://bucardo.org/) | [`bucardo/bucardo`](https://github.com/bucardo/bucardo) | External Perl daemon (`PA/EL`) capturing row changes via `PL/Perl` triggers into `bucardo_delta` tables for asynchronous PK-mandatory multi-master batch sync. |
| **[#10 — SymmetricDS](docs/en/solutions/symmetricds.md)** | [SymmetricDS Docs](https://symmetricds.org/docs/overview/) | [`jumpmindinc/symmetric-ds`](https://github.com/jumpmindinc/symmetric-ds) | Java JVM trigger-based asynchronous engine (`PA/EL`) staging changes in `sym_data` for heterogeneous (PG/MySQL/Oracle/SQLite) HTTP/HTTPS edge and mesh batch sync. |
| **[#11 — PgPool-II](docs/en/solutions/pgpool_ii.md)** | [PgPool-II Docs](https://www.pgpool.net/docs/latest/en/html/) | [`pgpool/pgpool2`](https://github.com/pgpool/pgpool2) | C SQL proxy supporting single-primary `streaming_replication` load balancing/Watchdog HA alongside fragile statement-broadcast `replication` and `snapshot_isolation` (`PC/EC`) modes. |
| **[#12 — AWS Aurora Limitless (& MM v1)](docs/en/solutions/aws_aurora_limitless.md)** | [AWS Aurora Limitless Docs](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/limitless.html) | Proprietary / N/A | Managed AWS sharded engine (`PC/EC`) pairing Transaction Routers, Data Access Shards, 4/6 AZ storage quorum, and Time Sync MVCC 2PC (superseding retired Aurora MM v1). |
| **[#13 — GCP Spanner PG & AlloyDB](docs/en/solutions/gcp_spanner_alloydb.md)** | [Spanner PG](https://cloud.google.com/spanner/docs/postgresql-interface) · [AlloyDB](https://cloud.google.com/alloydb/docs) | Proprietary / N/A | Contrasts Spanner PG Interface (`PGAdapter`, Multi-Paxos + TrueTime external consistency `PC/EC`) with AlloyDB's single-primary disaggregated storage and read pools. |
| **[#14 — Legacy Trigger Systems (EOL)](docs/en/solutions/legacy_triggers.md)** | [Slony-I](https://slony.info/) · [Londiste](https://wiki.postgresql.org/wiki/Londiste_Tutorial_%28Skytools_2%29) | [`slony1-engine`](https://github.com/ssinger/slony1-engine) · [`londiste`](https://github.com/pgq/londiste) · [`rubyrep`](https://github.com/rubyrep/rubyrep) | Retired/EOL pre-`pgoutput` trigger/queue replicators (`PA/EL`) — single-origin cascading Slony-I/Londiste+PGQ and abandoned JRuby RubyRep — retained as historical baselines. |
| **[#15a — PostgreSQL 17 Standalone](docs/en/solutions/pg17_standalone.md)** | [PG 17 Docs](https://www.postgresql.org/docs/17/index.html) | [`postgres/postgres`](https://github.com/postgres/postgres) | Single-writer PostgreSQL 17 control baseline using local WAL `fsync` (`CA`) with zero replication overhead to quantify multi-master coordination cost. |
| **[#15b — PG 17 Physical Streaming & Patroni](docs/en/solutions/pg17_physical_streaming_patroni.md)** | [PG 17 HA](https://www.postgresql.org/docs/17/high-availability.html) · [Patroni](https://patroni.readthedocs.io/en/latest/) | [`postgres/postgres`](https://github.com/postgres/postgres) · [`patroni/patroni`](https://github.com/patroni/patroni) | Single-primary physical block-level WAL streaming (`async` `PA/EL` or `sync` `PC/EC` `RPO=0`) orchestrated by Patroni, `etcd` Raft DCS, and HAProxy failover. |
| **[#16 — PG 17 Uni-Directional Logical](docs/en/solutions/pg17_logical_unidirectional.md)** | [PG 17 Logical Docs](https://www.postgresql.org/docs/17/logical-replication.html) | [`postgres/postgres`](https://github.com/postgres/postgres) | Built-in PG 17 `pgoutput` publish/subscribe row replication (`PA/EL`) decoupling storage and major versions (`T3`, zero-downtime upgrades, selective filtering). |
| **[#17 - PostgreSQL 18.6 Native Clustering (AIO, uuidv7, Streaming & Logical)](docs/en/solutions/pg18_native_clustering.md)** | [PG 18 Docs](https://www.postgresql.org/docs/18/index.html) | [`postgres/postgres`](https://github.com/postgres/postgres) | Core PG 18.6 target stack across all 5 native tiers adding AIO `worker`, default `data_checksums=on`, native `uuidv7()` active-active PKs, 7 `confl_*` counters, `substream=p`, and `42601` sequence sync deferral. |
| **[#18 - YT Cluster & YT Cluster Lite](docs/en/solutions/yt_cluster_lite.md)** | [YT Overview](https://dbinvent.com/30p) / [Docker Hub](https://hub.docker.com/r/dbinvent/yt) / [agent.md](https://dbinvent.com/agent.md) / [Jepsen](https://dbinvent.com/cluster/articles/jepsen) | [`DBinvent/yt-cluster-lite`](https://github.com/DBinvent/yt-cluster-lite) | Unmodified PG 18 + row triggers + Rust `ytserv` XA 2PC (`cc=half`), zero drift (`55409`/`40001`), `DROP EXTENSION` reversibility; MIT embedded leaf/ext vs `dbinvent/yt` PolyForm/Commercial. |

---

## Reproducible Lab Stacks, `multi-db-docker-env` Submodule & `Makefile`

PoC topologies, `T11–T18` suites, and V2 benchmarks use [`jmrenouard/multi-db-docker-env`](https://github.com/jmrenouard/multi-db-docker-env) (`env/multi-db-docker-env`). See [`stacks/README.md`](stacks/README.md) and `results/` for mappings and raw CSV/JSON data:

| Submodule Compose (`env/multi-db-docker-env/`) | Topology | Primary Images |
| :--- | :--- | :--- |
| `docker-compose-pg17-baseline.yml` | PG 17 Standalone & Sync Streaming | `postgres:17` |
| `docker-compose-pg-streaming.yml` / `pg-logical.yml` | PG 17 Async Streaming & Uni-Logical | `postgres:17` |
| `docker-compose-pg-birep.yml` | PG 17 Bidirectional (`origin=none`) + HAProxy | `postgres:17`, `haproxy:2.9-alpine` |
| `docker-compose-pgedge.yml` | 3-Node pgEdge Spock `5.0.14` + Snowflake + HAProxy | `ghcr.io/pgedge/pgedge-postgres:17-spock5-minimal` |
| `docker-compose-bucardo.yml` | 2-Node PG 17 (`plperl`) + Bucardo `5.6.0` Daemon | Custom `postgres:17` + `debian:trixie-slim` |
| `docker-compose-citus.yml` | Citus `14.2.0` (1 Coordinator + 2 Workers) | `citusdata/citus:14.2.0-pg17` |
| `docker-compose-yugabyte.yml` | 3-Node YugabyteDB RF=3 YSQL + DocDB + HAProxy `:15470` | `yugabytedb/yugabyte:2026.1.3.0-b100`, `haproxy:lts-alpine` |
| `docker-compose-cockroach.yml` | 3-Node CockroachDB RF=3 Multi-Raft + HAProxy `:15480` | `cockroachdb/cockroach:latest-v25.4`, `haproxy:lts-alpine` |
| `docker-compose-pg18-streaming.yml` | PG 18.6 Standalone, Async & Sync Streaming (`AIO worker`) | `postgres:18` (`18.6`) |
| `docker-compose-pg18-logical.yml` | PG 18.6 Uni-Directional Logical (`substream=p`, `pubgencols=s`) | `postgres:18` (`18.6`) |
| `docker-compose-pg18-birep.yml` | PG 18.6 Bidirectional Logical (`origin=none`, `uuidv7()`) + HAProxy | `postgres:18` (`18.6`), `haproxy:2.9-alpine` |
| `docker-compose-yt-cluster.yml` | 3-Node YT Cluster 1.21.3 (`yt_cluster` + `ytserv` XA 2PC) | `dbinvent/yt:1.21.3` (`PG 18.7`) |

### Common Commands

```bash
# Initialize the multi-db-docker-env Git submodule (13 Compose stacks; v2.6.2 benchmark harness)
make init-env
make help

# Run unit tests (security, math, 13 charts, dual-dataset 18-topology dashboard) and Compose/Bash lint
make test && make lint

# Run topology lifecycle, benchmarks (V1/V2 + PG 18.6 + YT + V5 Scale=20), charts, and dashboard
cp .env.example .env
make build-bench-image  # Build multi-db-pgbench-sysbench:latest from scripts/Dockerfile.bench
make up-pgedge && make test-pgedge && make down-pgedge
make bench-all && make bench-pg18 && make bench-yt-cluster && make bench-optimized && make popularity && make charts && make dashboard
make pages-build && make pages-check  # Stage & verify offline GitHub Pages bundle in _site/
```

---

## Governance, Security & Honest Scope

- **Living Registers:** Every engineering decision, bug RCA, dead-end, and simplification is tracked in [`docs/ACTION_LOGBOOK.md`](docs/ACTION_LOGBOOK.md) and [`docs/RCA_REGISTER.md`](docs/RCA_REGISTER.md).
- **Credential Hygiene:** Repository files hold zero real passwords or host paths. Containers read defaults from [`.env.example`](.env.example).
- **Threats to Validity:** Local benchmarks share one 20-vCPU / 16.4 GiB NVMe host. We modeled WAN delay via `tc netem` (`25 ms`), not separate regions (see [Chapter 05](docs/en/05_poc_architectures_and_test_protocol.md)).

---

## Support & Attribution

**Jean-Marie Renouard** (`jmrenouard`) authors this series under the [MIT License](LICENSE). **LightPath** provides engineering and infrastructure support:

<p align="center"><sub>Supported by</sub></p>

<p align="center"><a href="https://www.lightpath.fr"><img alt="Supported by LightPath" src="assets/lightpath-logo-light.svg#gh-light-mode-only" width="145"></a></p>

<p align="center"><a href="https://www.lightpath.fr"><img alt="Supported by LightPath" src="assets/lightpath-logo-dark.svg#gh-dark-mode-only" width="145"></a></p>

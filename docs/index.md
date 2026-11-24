# Documentation Portal — Diataxis Architecture

This portal maps all English documents across the four Diataxis quadrants. Use the top `Francais` switcher for `/fr/`.

- **Overviews:** [English README](../README.md) | [13 Compose Stacks](../stacks/README.md) | [Interactive Explorer](../dashboard/index.html)

## 1. Tutorials

| Lab | Document | Scope |
| :--- | :--- | :--- |
| **01 Docker PoC** | [First Docker PoC Lab](en/01-tutorials/01-first-docker-poc-lab.md) | `make init-env`, `up-pgedge`, `test-pgedge`, cleanup |
| **02 Benchmark Lab** | [pgbench & sysbench Lab](en/01-tutorials/02-pgbench-sysbench-lab.md) | Runner build, Compose check, charts, dashboard |
| **Quickstart** | [README Quickstart](../README.md#common-commands) | Repository setup and [Tutorials Index](en/01-tutorials/index.md) |

## 2. How-To Guides

| Guide | Document | Goal |
| :--- | :--- | :--- |
| **01 Benchmarks** | [Run Topology Benchmarks](en/02-how-to-guides/01-run-topology-benchmarks.md) | Execute benchmark runners and rebuild assets |
| **02 Hygiene Gates** | [Verify Limits & Hygiene](en/02-how-to-guides/02-verify-limits-and-hygiene.md) | Lint Compose, verify math, build EN/FR sites |
| **Overview** | [How-To Guides Index](en/02-how-to-guides/index.md) | [Catalog](../README.md#solutions-catalog--architecture-sheets-19-en--fr-deep-dives) |

## 3. Reference

Browse [Reference Index](en/03-reference/index.md), [Action Logbook](ACTION_LOGBOOK.md), and [RCA Register](RCA_REGISTER.md).

- **Chapters:** [04 Matrix](en/04_comprehensive_feature_comparison.md) | [05 PoC Protocol](en/05_poc_architectures_and_test_protocol.md) | [06 Benchmarks](en/06_empirical_test_and_benchmark_results.md) | [07 Decision Guide](en/07_decision_framework_and_production_guide.md) | [08 Limits](en/08_limits_and_failure_modes.md) | [09 Methodology](en/09_benchmarks_methodology_and_charts.md) | [11 Vitality](en/11_ecosystem_popularity_and_vitality.md) | [13 Tuning](en/13_production_tuning_and_realistic_benchmarks.md) | [14 TDE](en/14_transparent_data_encryption_tde.md)
### 19 Architecture Sheets (`docs/en/solutions/`)

| Group | Sheets |
| :--- | :--- |
| **Logical & Extensions** | [#1 pg-birep](en/solutions/pg17_bidirectional_logical.md) · [#2 pgEdge](en/solutions/pgedge_spock.md) · [#3 pglogical2](en/solutions/pglogical2.md) · [#4 EDB PGD](en/solutions/edb_pgd.md) |
| **Distributed SQL** | [#5 YugabyteDB](en/solutions/yugabytedb.md) · [#6 CockroachDB](en/solutions/cockroachdb.md) · [#7 Citus](en/solutions/citus.md) · [#8 OpenTenBase](en/solutions/opentenbase_pgxl.md) |
| **Triggers & Proxy** | [#9 Bucardo](en/solutions/bucardo.md) · [#10 SymmetricDS](en/solutions/symmetricds.md) · [#11 PgPool-II](en/solutions/pgpool_ii.md) · [#14 Triggers](en/solutions/legacy_triggers.md) |
| **Cloud & Baselines** | [#12 Aurora](en/solutions/aws_aurora_limitless.md) · [#13 Spanner](en/solutions/gcp_spanner_alloydb.md) · [#15a Standalone](en/solutions/pg17_standalone.md) · [#15b Patroni](en/solutions/pg17_physical_streaming_patroni.md) |
| **PG 17/18 & YT Cluster** | [#16 Logical](en/solutions/pg17_logical_unidirectional.md) · [#17 PG 18.6](en/solutions/pg18_native_clustering.md) · [#18 YT Cluster](en/solutions/yt_cluster_lite.md) |

## 4. Explanation

Browse [Explanation Index](en/04-explanation/index.md) for distributed systems theory and engine internals.

- **Chapters:** [01 Taxonomy](en/01_executive_summary_and_taxonomy.md) | [02 CAP & PACELC](en/02_theoretical_foundations_cap_pacelc_conflicts.md) | [03a Extensions](en/03a_solutions_native_and_extensions.md) | [03b Distributed & Cloud](en/03b_solutions_distributed_triggers_cloud.md) | [10 Trade-Offs](en/10_streaming_vs_logical_vs_multimaster.md) | [12 PG 18.6](en/12_postgresql_18_clustering_and_benchmarks.md)

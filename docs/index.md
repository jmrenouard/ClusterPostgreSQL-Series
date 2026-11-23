# Documentation Portal — Diataxis Architecture

This portal maps all English (`docs/en/`) and French (`docs/fr/`) documents into the four Diataxis quadrants. Every tracked file path remains unchanged, preserving existing benchmarks, pages, and tests.

- **Root Overviews:** [English README](../README.md) | [README francais](../README.fr.md) | [13 Compose Stacks](../stacks/README.md) | [PACELC Selector](../dashboard/index.html)

---

## 1. Tutorials (Learning & Onboarding)

Start here to understand the Docker lab architecture and reproduce your first multi-node PostgreSQL stack step by step.

| Topic | English | Francais | Focus |
| :--- | :--- | :--- | :--- |
| **Lab Quickstart & Stack Setup** | [README Quickstart](../README.md#common-commands) | [Demarrage rapide](../README.fr.md#commandes-makefile-essentielles) | Clone, init submodule, boot first stack |
| **Stack Catalog & Ports** | [Compose Stacks Guide](../stacks/README.md) | [Catalogue des stacks](../stacks/README.md) | Endpoints and credentials across 13 stacks |
| **PoC Topologies & Protocol** | [Ch. 05 — PoC Architectures](en/05_poc_architectures_and_test_protocol.md) | [Ch. 05 — Architectures PoC](fr/05_architectures_poc_et_protocole_de_test.md) | Reproducible test harness and network fault injection |

---

## 2. How-To Guides (Decisions & Operations)

Use these goal-oriented guides to select an architecture, tune production workloads, or avoid known anti-patterns.

| Guide | English | Francais | Operational Goal |
| :--- | :--- | :--- | :--- |
| **Architecture Selection & Anti-Patterns** | [Ch. 07 — Decision Framework](en/07_decision_framework_and_production_guide.md) | [Ch. 07 — Guide de choix](fr/07_guide_de_choix_et_architecture_cible.md) | Match workload patterns and avoid write traps |
| **Production Tuning (`PG_SCALE=20`)** | [Ch. 13 — Production Tuning](en/13_production_tuning_and_realistic_benchmarks.md) | [Ch. 13 — Optimisation production](fr/13_optimisation_production_et_benchmarks_realistes.md) | Size RAM, WAL, and commit sync settings |
| **Standalone vs Clustered Baselines** | [README Catalog](../README.md#solutions-catalog--architecture-sheets-19-en--fr-deep-dives) | [Catalogue des 19 solutions](../README.fr.md#2b-catalogue-des-solutions-et-fiches-techniques-19-fiches-fr--en) | Inspect topology roles before running `make up-*` |

---

## 3. Reference (Empirical Metrics, Limits & Solution Sheets)

Consult exact specifications, empirical throughput/latency numbers, failure modes, and repository governance registers.

### Chapters & Matrices

| Reference Document | English | Francais | Scope |
| :--- | :--- | :--- | :--- |
| **Feature & Limit Matrix** | [Ch. 04 — Feature Comparison](en/04_comprehensive_feature_comparison.md) | [Ch. 04 — Etude comparative](fr/04_etude_comparative_fonctionnalites.md) | 40 criteria across 6 matrices (incl. TDE) |
| **Empirical Benchmarks (`A`–`H`)** | [Ch. 06 — Benchmark Results](en/06_empirical_test_and_benchmark_results.md) | [Ch. 06 — Resultats benchmarks](fr/06_resultats_tests_et_benchmarks.md) | 301 default rows + 318 tuned rows |
| **Limits & SQLSTATE Probes** | [Ch. 08 — Limits & Failures](en/08_limits_and_failure_modes.md) | [Ch. 08 — Limites et defaillances](fr/08_limites_et_modes_de_defaillance.md) | `L1`–`L8` and `T11`–`T18` results |
| **Methodology & 13 Charts** | [Ch. 09 — Methodology & Charts](en/09_benchmarks_methodology_and_charts.md) | [Ch. 09 — Methodologie et graphiques](fr/09_methodologie_benchmarks_et_graphiques.md) | Schemas, `log10` axes, chart traceability |
| **Ecosystem Vitality (`22` Repos)** | [Ch. 11 — Ecosystem Vitality](en/11_ecosystem_popularity_and_vitality.md) | [Ch. 11 — Popularite et vitalite](fr/11_popularite_et_vitalite_ecosysteme.md) | Stars, 12-month commits, bus factor |
| **TDE & Encryption at Rest** | [Ch. 14 — Transparent Data Encryption](en/14_transparent_data_encryption_tde.md) | [Ch. 14 — Chiffrement Transparent (TDE)](fr/14_chiffrement_transparent_tde.md) | Key hierarchy, `pg_tde` 2.1, KMS, 18-arch matrix |
| **Governance & Registers** | [Action Logbook](ACTION_LOGBOOK.md) | [RCA & Assumptions Register](RCA_REGISTER.md) | Chronological changes, RCAs, `APP-001`..`APP-016` |

### 19 Bilingual Architecture Sheets (`docs/{en,fr}/solutions/`)

| ID | Technology | English Sheet | French Sheet |
| :---: | :--- | :--- | :--- |
| `#1` | PG 17 Bidirectional Logical (`pg-birep`) | [EN](en/solutions/pg17_bidirectional_logical.md) | [FR](fr/solutions/pg17_bidirectional_logical.md) |
| `#2` | pgEdge / Spock 5 (`LWW` & CRDT) | [EN](en/solutions/pgedge_spock.md) | [FR](fr/solutions/pgedge_spock.md) |
| `#3` | pglogical 2 *(Ref.)* | [EN](en/solutions/pglogical2.md) | [FR](fr/solutions/pglogical2.md) |
| `#4` | EDB Postgres Distributed *(Ref.)* | [EN](en/solutions/edb_pgd.md) | [FR](fr/solutions/edb_pgd.md) |
| `#5` | YugabyteDB (`YSQL`) | [EN](en/solutions/yugabytedb.md) | [FR](fr/solutions/yugabytedb.md) |
| `#6` | CockroachDB (`v25.4` / `v24.3.0`) | [EN](en/solutions/cockroachdb.md) | [FR](fr/solutions/cockroachdb.md) |
| `#7` | Citus (`Coord + Workers`) | [EN](en/solutions/citus.md) | [FR](fr/solutions/citus.md) |
| `#8` | OpenTenBase / PG-XL *(Ref.)* | [EN](en/solutions/opentenbase_pgxl.md) | [FR](fr/solutions/opentenbase_pgxl.md) |
| `#9` | Bucardo 5 *(Triggers)* | [EN](en/solutions/bucardo.md) | [FR](fr/solutions/bucardo.md) |
| `#10` | SymmetricDS *(Ref.)* | [EN](en/solutions/symmetricds.md) | [FR](fr/solutions/symmetricds.md) |
| `#11` | PgPool-II *(Proxy PoC)* | [EN](en/solutions/pgpool_ii.md) | [FR](fr/solutions/pgpool_ii.md) |
| `#12` | AWS Aurora Limitless *(Ref.)* | [EN](en/solutions/aws_aurora_limitless.md) | [FR](fr/solutions/aws_aurora_limitless.md) |
| `#13` | GCP Spanner PG & AlloyDB *(Ref.)* | [EN](en/solutions/gcp_spanner_alloydb.md) | [FR](fr/solutions/gcp_spanner_alloydb.md) |
| `#14` | Legacy Triggers (`Slony/Londiste/RubyRep`) | [EN](en/solutions/legacy_triggers.md) | [FR](fr/solutions/legacy_triggers.md) |
| `#15a` | PG 17 Standalone Baseline | [EN](en/solutions/pg17_standalone.md) | [FR](fr/solutions/pg17_standalone.md) |
| `#15b` | PG 17 Physical Streaming + Patroni | [EN](en/solutions/pg17_physical_streaming_patroni.md) | [FR](fr/solutions/pg17_physical_streaming_patroni.md) |
| `#16` | PG 17 Uni-Directional Logical | [EN](en/solutions/pg17_logical_unidirectional.md) | [FR](fr/solutions/pg17_logical_unidirectional.md) |
| `#17` | PostgreSQL 18.6 Native Clustering | [EN](en/solutions/pg18_native_clustering.md) | [FR](fr/solutions/pg18_native_clustering.md) |
| `#18` | YT Cluster `1.21.3` / `yt-cluster-lite` | [EN](en/solutions/yt_cluster_lite.md) | [FR](fr/solutions/yt_cluster_lite.md) |

---

## 4. Explanation (Architecture, Theory & Trade-Offs)

Read these analytical chapters to understand distributed consensus bounds, replication trade-offs, and version-specific mechanics.

| Analysis | English | Francais | Theme |
| :--- | :--- | :--- | :--- |
| **Executive Summary & Taxonomy** | [Ch. 01 — Summary & Taxonomy](en/01_executive_summary_and_taxonomy.md) | [Ch. 01 — Synthese et taxonomie](fr/01_synthese_et_taxonomie.md) | Five architectural families (`T1`–`T5`) |
| **Distributed Systems Theory** | [Ch. 02 — CAP, PACELC & Conflicts](en/02_theoretical_foundations_cap_pacelc_conflicts.md) | [Ch. 02 — Fondements CAP/PACELC](fr/02_fondements_theoriques_cap_pacelc_conflits.md) | Latency floors, clock skew, CRDT guarantees |
| **Native & Extension Catalog** | [Ch. 03a — Native & Extensions](en/03a_solutions_native_and_extensions.md) | [Ch. 03a — Catalogue natif](fr/03a_catalogue_natif_et_extensions.md) | `#1`–`#4`, `#15`–`#18` deep internals |
| **Distributed, Triggers & Cloud** | [Ch. 03b — Distributed & Cloud](en/03b_solutions_distributed_triggers_cloud.md) | [Ch. 03b — Distribue et cloud](fr/03b_catalogue_distribue_triggers_cloud.md) | `#5`–`#14` distributed SQL and cloud limits |
| **Replication Trade-Off Synthesis** | [Ch. 10 — Streaming vs Logical vs Multi-Master](en/10_streaming_vs_logical_vs_multimaster.md) | [Ch. 10 — Comparatif streaming/logique](fr/10_comparatif_streaming_logique_multimaster.md) | Why 80%+ workloads stay single-primary |
| **PostgreSQL 18.6 AIO & Replication** | [Ch. 12 — PG 18 Clustering](en/12_postgresql_18_clustering_and_benchmarks.md) | [Ch. 12 — Clustering PG 18](fr/12_clustering_postgresql_18_et_benchmarks.md) | `io_method=worker`, `uuidv7()`, sequence gap |

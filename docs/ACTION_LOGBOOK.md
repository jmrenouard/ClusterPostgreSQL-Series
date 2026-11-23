# Action Logbook & Strategic Roadmap - ClusterPostgreSQL-Series

> **Governance Rule ([`AGENTS.md`](../AGENTS.md) & [`.agents/rules/project-governance.md`](../.agents/rules/project-governance.md))**:
> Update this register in English on **every request, every change, and every result**.

## Strategic Roadmap & Milestones

| Phase | Milestone | Scope | Status | Verification |
| :--- | :--- | :--- | :---: | :--- |
| **Phase 1** | Repository Governance & Harness | License, governance, `.env.example`, CI, Makefile, tests | Complete | `make test` |
| **Phase 2** | Comparative Study (`en` / `fr`) | Architectural taxonomy, matrices, consensus limits | Complete | `make check-math` |
| **Phase 3** | Reproducible Docker PoCs | Native logical, Spock/pgEdge, Bucardo, Citus, YugabyteDB, CockroachDB | Complete | `make test-*` |
| **Phase 4** | Benchmarks & Synthesis | Empirical limits, pgbench/sysbench throughput & latency | Complete | `make bench-all` |
| **Phase 5** | V2 10-Topology Study, Charts, Dashboard & Submodule | Streaming/logical PoCs, T11-T18, Log10 PNGs, offline dashboard, `env/multi-db-docker-env` | Complete | `make test && make lint` |
| **Phase 6** | Bilingual Per-Technology Architecture Sheets | Dedicated EN+FR ~1-2 A4 sheets (`docs/{en,fr}/solutions/`) + Mermaid + navigation links + Tiers 1-5 E2E | Complete | `make test && make lint` |
| **Phase 7** | Wave 3: Ecosystem Popularity, PG 18.6, Charts 08-10 & Dashboard V3 | GitHub API popularity study, PG 18.6 PoC & 87 benchmarks, Ch. 11-12 EN/FR, Charts 08-10, 15-topology Dashboard V3, submodule `v2.3.0` | Complete | `make test && make lint` |
| **Phase 8** | Wave 4: PG 18.6 Sheet #17, YT Cluster 1.21.3 / YT Cluster Lite PoC & Sheet #18, 17-Topology Dashboard & Submodule `v2.4.0` | PG 18.6 18th sheet & core chapters, YT Cluster 22-row live PoC & 19th sheet, 22-entry popularity & Charts 08-09, 17-topology offline dashboard, 19-slug E2E tests, 13-stack `Makefile` & submodule `v2.4.0` | Complete | `make test && make lint` |
| **Phase 9** | Wave 5: 18-Suite `yt-cluster-async`, 17-Topology Charts 01-07 + `chart_11`, Benchmark Traceability & `v2.4.1` | 36-row YT Cluster empirical matrix, 17-topology `chart_01-07` + `chart_11`, 301-row offline dashboard (`yt_vs_mm`), Ch. 06 Section 7 & Ch. 09 Traceability Matrix, submodule `v2.4.1` | Complete | `make test && make lint` |
| **Phase 10** | V5 Production Tuning & Realistic Scale Benchmarks (`PG_SCALE=20`, `18` Topologies, `318` Rows, `v2.6.1`) | `results/benchmark_optimized.csv` (`318` rows), `chart_12` & `chart_13`, dual-dataset offline dashboard (`301` + `318`), Chapter 13 EN/FR, Ch. 06 Section 8, Ch. 09 Matrix, `README*` & governance updates | Complete | `make charts && make dashboard && make test && make lint` |
| **Phase 11** | Interactive PACELC Selector & GitHub Pages Explorer (`#496-#507`) | PACELC catalog/engine/UI, Node+parity tests, `make pages-build`/`pages-check`, EN/FR docs; `.github/workflows/pages.yml` tracked in `#506` (`RCA-003`) | Complete (`#506` pending `workflow` scope) | `make dashboard && make pages-build && make pages-check && make test && make lint` |
| **Phase 12** | Ponytail Quality Audit, Chart/Dashboard Refactoring, Unit Hardening & Submodule `v2.6.2` (`#509-#563`) | Audited Makefile targets, pruned 14 shadowed scripts, fixed collector/builder/chart bugs, extracted `LPUtil`, regenerated charts/shards, reconciled PACELC hooks, added Python/Node unit tests, bumped submodule `v2.6.2` | Complete | `make test && make lint && make pages-check` |

## 1. Ongoing Actions (`IN PROGRESS`)

| Action ID | Date (ISO) | Issue / Branch | Status | Summary |
| :--- | :--- | :--- | :--- | :--- |
| *None* | - | - | - | All tracked actions archived below once verified. |

## 2. Completed Actions (`COMPLETED`)

### ACT-246 - Refactor aws_aurora_limitless FR Sheet for 0 STE Errors (`#665`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#665` (`docs/issue-665-aurora-limitless-fr`)
- **Request / Changes / Result**: Refactored `docs/fr/solutions/aws_aurora_limitless.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while preserving CSV metrics and Mermaid diagrams; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-245 - Refactor aws_aurora_limitless EN Sheet for 0 STE Errors (`#663`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#663` (`docs/issue-663-aurora-limitless-en`)
- **Request / Changes / Result**: Refactored `docs/en/solutions/aws_aurora_limitless.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while preserving CSV metrics and Mermaid diagrams; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-244 - Refactor legacy_triggers FR Sheet for 0 STE Errors (`#661`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#661` (`docs/issue-661-legacy-triggers-fr`)
- **Request / Changes / Result**: Refactored `docs/fr/solutions/legacy_triggers.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while preserving CSV metrics and Mermaid diagrams; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-243 - Refactor legacy_triggers EN Sheet for 0 STE Errors (`#659`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#659` (`docs/issue-659-legacy-triggers-en`)
- **Request / Changes / Result**: Refactored `docs/en/solutions/legacy_triggers.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while preserving CSV metrics and Mermaid diagrams (FR split cleanly under diff cap); Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-242 - Refactor opentenbase_pgxl EN/FR Sheets (`#657`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#657` (`docs/issue-657-opentenbase-pgxl`)
- **Request / Changes / Result**: Refactored `docs/{en,fr}/solutions/opentenbase_pgxl.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while preserving CSV metrics and Mermaid diagrams; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-241 - Refactor pgpool_ii EN/FR Sheets (`#655`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#655` (`docs/issue-655-pgpool-ii`)
- **Request / Changes / Result**: Refactored `docs/{en,fr}/solutions/pgpool_ii.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while preserving CSV metrics and Mermaid diagrams; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-240 - Refactor yugabytedb EN/FR Sheets (`#653`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#653` (`docs/issue-653-yugabytedb`)
- **Request / Changes / Result**: Refactored `docs/{en,fr}/solutions/yugabytedb.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while preserving CSV metrics and Mermaid diagrams; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-239 - Refactor pglogical2 EN/FR Sheets (`#651`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#651` (`docs/issue-651-pglogical2`)
- **Request / Changes / Result**: Refactored `docs/{en,fr}/solutions/pglogical2.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while preserving CSV metrics and Mermaid diagrams; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-238 - Refactor symmetricds EN/FR Sheets (`#649`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#649` (`docs/issue-649-symmetricds`)
- **Request / Changes / Result**: Refactored `docs/{en,fr}/solutions/symmetricds.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while preserving CSV metrics and Mermaid diagrams; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-237 - Refactor edb_pgd EN/FR Sheets (`#647`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#647` (`docs/issue-647-edb-pgd`)
- **Request / Changes / Result**: Refactored `docs/{en,fr}/solutions/edb_pgd.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while preserving CSV metrics and Mermaid diagrams; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-236 - Refactor pgedge_spock EN/FR Sheets (`#645`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#645` (`docs/issue-645-pgedge-spock`)
- **Request / Changes / Result**: Refactored `docs/{en,fr}/solutions/pgedge_spock.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while preserving CSV metrics and Mermaid diagrams; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-235 - Refactor pg18_native_clustering EN/FR Sheets (`#643`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#643` (`docs/issue-643-pg18-native-clustering`)
- **Request / Changes / Result**: Refactored `docs/{en,fr}/solutions/pg18_native_clustering.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while keeping PG 18.6 CSV metrics and Mermaid diagrams intact; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-234 - Refactor pg17_logical_unidirectional EN/FR Sheets (`#641`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#641` (`docs/issue-641-pg17-logical-unidir`)
- **Request / Changes / Result**: Refactored `docs/{en,fr}/solutions/pg17_logical_unidirectional.md` for full-file 0 STE mixed-mode errors, 0 weak modals, and 0 prose `via` while preserving CSV metrics and Mermaid diagrams; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-233 - Refactor pg17_bidirectional_logical and pg17_standalone EN/FR Sheets (`#639`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#639` (`docs/issue-639-pg17-bidir-standalone`)
- **Request / Changes / Result**: Refactored `docs/{en,fr}/solutions/pg17_bidirectional_logical.md` for 0 STE mixed-mode errors and removed non-CSV `via` in `docs/{en,fr}/solutions/pg17_standalone.md` while keeping verbatim CSV findings intact; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-232 - Refactor Citus EN/FR Sheets and Ch 04-05 FR via Cleanup (`#637`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#637` (`docs/issue-637-citus-ch04-05-via`)
- **Request / Changes / Result**: Refactored `docs/en/solutions/citus.md` and `docs/fr/solutions/citus.md` for 0 STE mixed-mode errors and removed non-CSV `via` in `docs/fr/04_etude_comparative_fonctionnalites.md` and `docs/fr/05_architectures_poc_et_protocole_de_test.md`; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-231 - Refactor Chapter 13 EN/FR for 0 STE Errors (`#635`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#635` (`docs/issue-635-ch13-en-fr`)
- **Request / Changes / Result**: Refactored `docs/en/13_production_tuning_and_realistic_benchmarks.md` and `docs/fr/13_optimisation_production_et_benchmarks_realistes.md` for full-file 0 STE mixed-mode errors, 0 `via`, and 0 weak modals; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-230 - Refactor Chapter 12 FR for 0 STE Errors (`#633`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#633` (`docs/issue-633-ch12-fr`)
- **Request / Changes / Result**: Refactored `docs/fr/12_clustering_postgresql_18_et_benchmarks.md` for full-file 0 STE mixed-mode errors, 0 `via`, and 0 weak modals while keeping PG 18.6 benchmark figures, charts, and anchors intact; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-229 - Refactor Chapter 12 EN for 0 STE Errors (`#631`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#631` (`docs/issue-631-ch12-en`)
- **Request / Changes / Result**: Refactored `docs/en/12_postgresql_18_clustering_and_benchmarks.md` for full-file 0 STE mixed-mode errors, 0 `via`, and 0 weak modals (split FR into a separate atomic PR to stay under 14,800 B); Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-228 - Refactor Chapter 11 FR for 0 STE Errors (`#629`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#629` (`docs/issue-629-ch11-fr`)
- **Request / Changes / Result**: Refactored `docs/fr/11_popularite_et_vitalite_ecosysteme.md` for full-file 0 STE mixed-mode errors, 0 `via`, and 0 weak modals while keeping GitHub popularity figures, charts, and anchors intact; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-227 - Refactor Chapter 10 FR for 0 STE Errors (`#627`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#627` (`docs/issue-627-ch10-fr`)
- **Request / Changes / Result**: Refactored `docs/fr/10_comparatif_streaming_logique_multimaster.md` for full-file 0 STE mixed-mode errors, 0 `via`, and 0 weak modals while keeping comparisons, Mermaid diagrams, and anchors intact; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-226 - Refactor Chapter 10 EN for 0 STE Errors (`#625`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#625` (`docs/issue-625-ch10-en`)
- **Request / Changes / Result**: Refactored `docs/en/10_streaming_vs_logical_vs_multimaster.md` for full-file 0 STE mixed-mode errors, 0 `via`, and 0 weak modals while keeping comparisons, Mermaid diagrams, and anchors intact; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-225 - Refactor Chapter 09 FR for 0 STE Errors (`#623`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#623` (`docs/issue-623-ch09-fr`)
- **Request / Changes / Result**: Refactored `docs/fr/09_methodologie_benchmarks_et_graphiques.md` for full-file 0 STE mixed-mode errors, 0 `via`, and 0 weak modals while keeping benchmark formulas, charts, and anchors intact; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-224 - Refactor Chapter 08 FR for 0 STE Errors (`#621`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#621` (`docs/issue-621-ch08-fr`)
- **Request / Changes / Result**: Refactored `docs/fr/08_limites_et_modes_de_defaillance.md` for full-file 0 STE mixed-mode errors, 0 `via`, and 0 weak modals while preserving all failure-mode facts and anchors; Windows unittest and WSL `make test lint check-math check-security` pass.

### ACT-223 - Complete Chapter 06 FR Part 2 (Sections 6-8) for 0 STE Errors (`#619`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#619` (`docs/issue-619-ch06-fr-p2`)
- **Request / Changes / Result**: Completed Sections 6-8 of `docs/fr/06_resultats_tests_et_benchmarks.md` reaching full-file 0 STE mixed-mode errors, 0 `via`, and 0 weak modals; Windows unittest (`31/31`) and WSL `make test lint check-math check-security` pass.

### ACT-222 - Refactor Chapter 06 FR Part 1 (Sections 1-5) for STE Compliance (`#617`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#617` (`docs/issue-617-ch06-fr-p1`)
- **Request / Changes / Result**: Refactored Sections 1-5 (before `## 6. Extension V3`) of `docs/fr/06_resultats_tests_et_benchmarks.md` to 0 STE errors, 0 `via`, and 0 weak modals in Part 1 while preserving all CSV metrics; Windows unittest (`31/31`) and WSL `make test lint check-math check-security` pass.

### ACT-221 - Complete Chapter 06 EN Part 2 (Sections 6-8) for 0 STE Errors (`#615`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#615` (`docs/issue-615-ch06-en-p2`)
- **Request / Changes / Result**: Completed Sections 6-8 of `docs/en/06_empirical_test_and_benchmark_results.md` reaching full-file 0 STE mixed-mode errors, 0 `via`, and 0 forbidden modals; Windows unittest (`31/31`) and WSL `make test lint check-math check-security` pass.

### ACT-220 - Refactor Chapter 06 EN Part 1 (Sections 1-5) for STE Compliance (`#613`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#613` (`docs/issue-613-ch06-en-p1`)
- **Request / Changes / Result**: Refactored Sections 1-5 (before `## 6. V3 Extension`) of `docs/en/06_empirical_test_and_benchmark_results.md` to 0 STE errors, 0 `via`, and 0 forbidden modals in Part 1 while preserving all metrics; Windows unittest (`31/31`) and WSL `make test lint check-math check-security` pass.

### ACT-219 - Complete Chapter 08 EN Section 3 and Refactor Chapter 11 EN (`#611`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#611` (`docs/issue-611-ch08-en-sec3-ch11-en`)
- **Request / Changes / Result**: Completed `docs/en/08_limits_and_failure_modes.md` Section 3 (`0` STE errors full-file) and refactored `docs/en/11_ecosystem_popularity_and_vitality.md` (`0` STE errors, `0` `via`, `0` forbidden modals); Windows unittest (`31/31`) and WSL `make test lint check-math check-security` pass.

### ACT-218 - Refactor Chapter 08 EN Sections 1-2 for STE Compliance (`#609`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#609` (`docs/issue-609-ch08-en-complete`)
- **Request / Changes / Result**: Refactored Sections 1-2 (before `## 3. Extended Empirical Matrix`) of `docs/en/08_limits_and_failure_modes.md` to 0 STE errors, 0 `via`, and 0 forbidden modals in Sections 1-2 (Section 3 deferred to keep diff < 14,800 B); Windows unittest (`31/31`) and WSL `make test lint check-math check-security` pass.

### ACT-217 - Complete Chapter 09 EN Part 2 and Refactor Chapter 08 EN Part 2 (`#607`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#607` (`docs/issue-607-ch09-en-p2-ch08-en-p2`)
- **Request / Changes / Result**: Completed `docs/en/09_benchmarks_methodology_and_charts.md` Sections 5-6 (full-file 0 STE errors) and refactored `docs/en/08_limits_and_failure_modes.md` Section 4 (0 STE errors/modals/`via` in Sec 4); Windows unittest (`31/31`) and WSL `make test lint check-math check-security` pass.

### ACT-216 - Complete Chapter 03b FR Part 2 and Refactor Chapter 09 EN Part 1 (`#605`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#605` (`docs/issue-605-ch03b-fr-p2-ch09-en-p1`)
- **Request / Changes / Result**: Completed `docs/fr/03b_catalogue_distribue_triggers_cloud.md` Part 2 (`#11-#14`, full-file 0 STE errors) and refactored `docs/en/09_benchmarks_methodology_and_charts.md` Sections 1-4 (0 STE errors/modals/`via` in Part 1); Windows unittest (`31/31`) and WSL `make test lint check-math check-security` pass.

### ACT-215 - Refactor Chapter 03b FR Part 1 (#5-#10) for STE Compliance (`#603`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#603` (`docs/issue-603-ch03b-fr-p1`)
- **Request / Changes / Result**: Refactored Part 1 (`#5-#10`, before `## #11 PgPool-II`) of `docs/fr/03b_catalogue_distribue_triggers_cloud.md` to 0 STE errors, 0 `via`, and 0 weak modals in Part 1; Windows unittest (`31/31`) and WSL `make test lint check-math check-security` pass.

### ACT-214 - Refactor Chapter 03b EN Part 2 (#11-#14) and Bucardo Sheets for 0 STE Errors (`#601`)
- **Date**: `2026-11-23` | **Status**: `COMPLETED` | **Issue / Branch**: `#601` (`docs/issue-601-ch03b-en-p2-bucardo`)
- **Request / Changes / Result**: Refactored Part 2 (`#11-#14`) of `docs/en/03b_solutions_distributed_triggers_cloud.md` and `docs/{en,fr}/solutions/bucardo.md` to 0 STE mixed-mode errors, 0 `via`, and 0 forbidden modals; Windows unittest (`31/31`) and WSL `make test lint check-math check-security` pass.

### ACT-213 - Refactor Chapter 03b EN Part 1 (#5-#10) for STE Compliance (`#599`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#599` (`docs/issue-599-ch03b-en-p1`)
- **Request / Changes / Result**: Refactored Part 1 (`#5-#10`, L1-131) of `docs/en/03b_solutions_distributed_triggers_cloud.md` to 0 STE errors / 0 `via` / 0 forbidden modals in Part 1; `make test` (`31/31`) and `make lint` pass.

### ACT-212 - Refactor Chapter 03a FR Part 2 (#15-#18) for 0 STE Errors (`#597`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#597` (`docs/issue-597-ch03a-fr-p2`)
- **Request / Changes / Result**: Refactored Part 2 (`#15-#18`, L103-162) of `docs/fr/03a_catalogue_natif_et_extensions.md` to full-file `0` STE errors (`18 warnings`, 0 `via`/weak modals); `make test` (`31/31`) and `make lint` pass.

### ACT-211 - Refactor Chapter 03a FR Part 1 (#1-#4) for STE Compliance (`#595`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#595` (`docs/issue-595-ch03ab-fr-p1`)
- **Request / Changes / Result**: Refactored Part 1 (`#1-#4`, L1-102) of `docs/fr/03a_catalogue_natif_et_extensions.md` to 0 STE errors / 0 `via` / 0 weak modals in Part 1 while keeping PR diff under 14,800 B; `make test` (`31/31`) and `make lint` pass.

### ACT-210 - Refactor Chapter 03a EN Part 2 (#15-#18) for 0 STE Errors (`#593`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#593` (`docs/issue-593-ch03a-en-p2`)
- **Request / Changes / Result**: Refactored Part 2 (`#15-#18`) of `docs/en/03a_solutions_native_and_extensions.md` to 0 STE mixed-mode errors (`0 errors, 59 warnings`, 0 `via`/modals) while keeping all metrics intact; `make test` (`31/31`) and `make lint` pass.

### ACT-209 - Refactor Chapter 03a EN Part 1 (#1-#4) for ASD-STE100 (`#591`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#591` (`docs/issue-591-ch03a-en-p1`)
- **Request / Changes / Result**: Refactored Part 1 (`#1-#4`) of `docs/en/03a_solutions_native_and_extensions.md` to eliminate semicolons, `via`, and >25-word sentences while keeping links and metrics intact; `make test` (`31/31`) and `make lint` pass.

### ACT-208 - Fix ASD-STE100 Compliance in Chapter 02 FR (`#589`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#589` (`docs/issue-589-ch02-fr-ste`)
- **Request / Changes / Result**: Refactored `docs/fr/02_fondements_theoriques_cap_pacelc_conflits.md` to 0 STE mixed-mode errors (0 semicolons, 0 weak modals, `<= 25` words/sentence) while keeping LaTeX math syntax intact; `make test` (`31/31`) and `make lint` pass.

### ACT-207 - Fix ASD-STE100 Compliance in Chapter 02 EN (`#587`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#587` (`docs/issue-587-ch02-en-bucardo-ste`)
- **Request / Changes / Result**: Refactored `docs/en/02_theoretical_foundations_cap_pacelc_conflicts.md` to 0 STE mixed-mode errors (0 `may`/`via`/semicolons, `<= 25` words/sentence) while keeping LaTeX math compliant; `make test` (`31/31`) and `make lint` pass.

### ACT-206 - Fix ASD-STE100 Compliance in Chapter 01 FR & `pg17_standalone` Sheets (`#585`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#585` (`docs/issue-585-ch01-fr-standalone-ste`)
- **Request / Changes / Result**: Refactored `docs/fr/01_synthese_et_taxonomie.md` and `docs/{en,fr}/solutions/pg17_standalone.md` to 0 STE mixed-mode errors while preserving Tier 1-5 parity; `make test` (`31/31`) and `make lint` pass.

### ACT-205 - Fix ASD-STE100 Compliance in Chapter 01 EN & Patroni Sheets (`#583`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#583` (`docs/issue-583-ch01-en-patroni-ste`)
- **Request / Changes / Result**: Refactored `docs/en/01_executive_summary_and_taxonomy.md` and `docs/{en,fr}/solutions/pg17_physical_streaming_patroni.md` to 0 STE mixed-mode errors while preserving Tier 1-5 parity; `make test` (`31/31`) and `make lint` pass.

### ACT-204 - Align CockroachDB FR V5 Spec & Fix STE Compliance (`#581`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#581` (`docs/issue-581-cockroach-fr-ch01-en`)
- **Request / Changes / Result**: Added CockroachDB V5 `v25.4.21`/`3072m` upgrade block and fixed all 6 STE mixed-mode errors (`0 errors`) in `docs/fr/solutions/cockroachdb.md` (`13,940` B < `14,000` B) while preserving historical `v24.3.0` Tier 1-5 parity; `make test` (`31/31`) and `make lint` pass.

### ACT-203 - Add CockroachDB V5 Spec in EN, Remove `eventuellement` in FR & Fix STE (`#579`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#579` (`docs/issue-579-cockroach-v5-modals`)
- **Request / Changes / Result**: Added CockroachDB V5 `v25.4.21`/`3072m` upgrade note and fixed all 6 STE errors in `docs/en/solutions/cockroachdb.md` (`13,960` B), and removed all 3 `eventuellement` occurrences in `docs/fr/03a_catalogue_natif_et_extensions.md` and `docs/fr/solutions/yt_cluster_lite.md`; `make test` (`31/31`) and `make lint` pass.

### ACT-202 - Fix ASD-STE100 Compliance & Add Diataxis Links in Chapter 07 FR (`#577`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#577` (`docs/issue-577-ch07-fr-ste`)
- **Request / Changes / Result**: Refactored `docs/fr/07_guide_de_choix_et_architecture_cible.md` to 0 STE mixed-mode errors (removed `potentiellement`/`via`, semicolons, and >25-word sentences) and added Diataxis cross-links while preserving Mermaid IDs and metrics; `make test` (`31/31`) and `make lint` pass.

### ACT-201 - Fix ASD-STE100 Compliance & Add Diataxis Links in Chapter 07 EN (`#575`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#575` (`docs/issue-575-ch07-en-ste`)
- **Request / Changes / Result**: Refactored `docs/en/07_decision_framework_and_production_guide.md` to 0 STE mixed-mode errors (removed `should`/`may`/`via`, semicolons, and >25-word sentences) and added Diataxis cross-links while preserving Mermaid IDs and metrics; `make test` (`31/31`) and `make lint` pass.

### ACT-200 - Align Chapter 05 FR With 13 Stacks / 18 Topologies & STE Compliance (`#573`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#573` (`docs/issue-573-ch05-fr-stacks-ste`)
- **Request / Changes / Result**: Expanded `docs/fr/05_architectures_poc_et_protocole_de_test.md` Section 2 and Section 6 to all 13 Compose stacks (`pg17-baseline`..) / 18 topologies (`v25.4` + V1/V2 `v24.3.0`, PG 18.6, YT Cluster 1.21.3, `H`/`F_wan`/`G_conc`), added Diataxis cross-links, and fixed all STE mixed-mode errors to 0; `make test` (`31/31`) and `make lint` pass.

### ACT-199 - Align Chapter 05 EN With 13 Stacks / 18 Topologies & STE Compliance (`#571`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#571` (`docs/issue-571-ch05-stacks-ste`)
- **Request / Changes / Result**: Expanded `docs/en/05_poc_architectures_and_test_protocol.md` Section 2 and Section 6 to all 13 Compose stacks / 18 topologies (`v25.4` + V1/V2 `v24.3.0`, PG 18.6, YT Cluster 1.21.3, `H`/`F_wan`/`G_conc`), added Diataxis cross-links, and fixed all STE mixed-mode errors to 0; `make test` (`31/31`) and `make lint` pass.

### ACT-198 - Update `stacks/README.md` to 18 Topologies & Fix STE Compliance (`#569`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#569` (`docs/issue-569-stacks-18-topologies`)
- **Request / Changes / Result**: Updated `stacks/README.md` to document all 13 Compose stacks and 18 topologies (CockroachDB `v25.4` active stack + `v24.3.0` V1/V2 note) with 0 STE procedural errors; logged `RCA-028` and `IMP-015`; `make test` (`31/31`) and `make lint` pass.

### ACT-197 - Fix ASD-STE100 Compliance in `README.fr.md` (`#567`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#567` (`docs/issue-567-ste-readme-fr`)
- **Request / Changes / Result**: Refactored `README.fr.md` prose, lists, chart spacing, and LightPath logo markup to 0 STE errors (`ste_check.py --mode procedural --lang fr --no-vocab`) while keeping catalog and CSV parity; `make test` (`31/31`) and `make lint` pass.

### ACT-196 - Fix ASD-STE100 Compliance in `README.md` (`#565`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#565` (`docs/issue-565-ste-readmes-stacks`)
- **Request / Changes / Result**: Refactored `README.md` prose, lists, chart spacing, and LightPath logo markup to 0 STE errors (`ste_check.py --mode procedural --lang en --no-vocab`) while keeping catalog and CSV parity; `make test` (`31/31`) and `make lint` pass.

### ACT-195 - Bump Submodule to `v2.6.2` & Update Living Governance Registers (`#561-#563`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#561-#563` (`docs/issue-563-audit-governance-registers`)
- **Request / Changes / Result**: Bumped `env/multi-db-docker-env` to `1dc6fa80` (`v2.6.2`, PR `#562`), aligned `README.md`/`README.fr.md` harness version references, and logged `Phase 12`, `ACT-192..195`, `RCA-026..027`, `IMP-013..014`, `APP-015` (Issue `#563`); `make test` (`31/31`) and `make lint` pass.

### ACT-194 - Refactor Dashboard UI, Reconcile PACELC Hooks & Harden Unit/Node Tests (`#549-#560`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#549-#560` (`test/issue-559-dashboard-js-unit-harness`)
- **Request / Changes / Result**: Extracted shared `window.LPUtil` (`matrix.js` loaded before `popularity.js`/`opt.js`/`app.js`), fixed XSS escaping, linear tick dedup, >8 sweep labels, `SWEEP_CONC` compare rendering, CSV formula escaping, and standalone `LPUtil` guard in `opt.js` (`RCA-027`); merged `#501` PACELC UI hooks in `index.html`/`app.js` (< `14,000` B per file) and added Python + Node VM unit tests (`31/31` non-skipped) in `tests/test_benchmark_artifacts.py` (PRs `#550`-`#560`).

### ACT-193 - Harden Popularity Collector, Dashboard Builder & Chart Generators (`#529-#548`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#529-#548` (`chore/issue-547-refresh-opt-meta-timestamp`)
- **Request / Changes / Result**: Extracted `scripts/chart_meta.py` (`resolve_e1`, `inum`, `fnum`, `OUT_DIR`/`RES_DIR`), fixed 301 redirect bodies, `Link` pagination, and 30s `gh` timeout in `collect_popularity.py`, guarded `math.isfinite` and balanced 3-shard `shard_rows` (`55+56+67=178` rows) in `build_dashboard.py`, fixed empty/sweep guards and dynamic snapshot dates in `generate_charts*.py`, and regenerated `chart_08..13` + balanced shards (PRs `#530`-`#548`).

### ACT-192 - Audit Makefile Entry Points & Prune 14 Shadowed Legacy Scripts (`#509-#528`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#509-#528` (`chore/issue-527-drop-shadowed-test-yugabyte`)
- **Request / Changes / Result**: Reconciled `Makefile` (`build-bench-image`, `bench-optimized`, `bench-yt-cluster` overrides, `bench-all` fallback, `reports/*.md` clean) with `#505` Pages targets and removed 14 shadowed `scripts/*.sh/.py` files while preserving `setup_pg17_baseline.sh` (PRs `#510`-`#528`).

### ACT-191 - Document GitHub Pages Explorer & PACELC Selector in EN/FR Docs (`#507`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#507` (`docs/issue-507-pages-pacelc-docs`)
- **Request / Changes / Result**: Added GitHub Pages URL, PACELC Selector overview, and `make pages-build && make pages-check` to `README*.md` and EN/FR Ch. 07; logged `Phase 11` and updated `IDEA-005`; `make check-math && make check-security && make test` (`27/27`) and `make lint` pass.

### ACT-190 - Prepare & Document GitHub Pages Workflow Block (`#506`)
- **Date**: `2026-11-22` | **Status**: `BLOCKED` | **Issue / Branch**: `#506` (open, `RCA-003` missing OAuth `workflow` scope)
- **Request / Changes / Result**: Verified `.github/workflows/pages.yml` locally (`28/28` tests OK); push rejected without `workflow` scope; documented verified YAML and `gh auth refresh -s workflow` unblock steps on open Issue `#506`.

### ACT-189 - Add Makefile GitHub Pages Static Bundle Builder & Verifier (`#504`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#504` (`feat/issue-504-pages-bundle-builder`)
- **Request / Changes / Result**: Added `scripts/build_pages.py` (stdlib-only `_site/` builder + `--check` offline/CDN/link/hygiene verifier), wired `make pages-build`, `make pages-check`, and `make clean` in `Makefile`, ignored `_site/` in `.gitignore`, and added `tests/test_pages_bundle.py`; logged `APP-014`; `make pages-build && make pages-check && make clean`, `make test` (`27/27` OK), and `make lint` pass.

### ACT-188 - Add Automated PACELC Selector Unit & Parity Tests (`#502`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#502` (`test/issue-502-pacelc-selector-tests`)
- **Request / Changes / Result**: Extended `tests/test_benchmark_artifacts.py` (`EXPECTED_DASH_FILES` + HTML tokens) and added `tests/test_pacelc_selector.py` validating 17+2 catalog parity, Makefile/`./mdb` targets, EN/FR sheet paths, canonical S1-S4 Node.js scoring, drift rejection, score transparency across all 32 input matrices, and mock-DOM UI flows; logged `APP-013`; `make test` (`24/24` OK) and `make lint` pass.

### ACT-187 - Add PACELC Selector Tab & Styles (`#500`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#500` (`feat/issue-500-pacelc-dashboard-ui`)
- **Request / Changes / Result**: Added `dashboard/pacelc_ui.js`, `dashboard/pacelc.css`, and minimal wiring in `dashboard/{index.html,app.js}` for bilingual `data-tab="pacelc"` selector, copyable lab commands, tab jump, and CSV export; logged `IMP-012`; all files `< 14,000` B, `node --check`, `make test` (`21/21`), `make lint` pass.

### ACT-186 - Implement Pure-JS PACELC Scoring Engine (`#498`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#498` (`feat/issue-498-pacelc-scoring-engine`)
- **Request / Changes / Result**: Added `dashboard/pacelc_engine.js` (`window.LPPacelcEngine`, browser + Node.js, zero CDN, `< 8,000` B) ranking all 17 topologies + V5/CRDT variants across 4 PACELC inputs (`rpo`, `wanRttMs`, `conflictRate`, `tco`) and both `baseline`/`optimized` datasets from live `LP_BENCH_*` and `LP_MATRIX_*`; logged `APP-012`; `node --check`, `make test` (`21/21` OK), and `make lint` pass.

### ACT-185 - Generate PACELC Catalog Metadata Bundle (`#496`)
- **Date**: `2026-11-22` | **Status**: `COMPLETED` | **Issue / Branch**: `#496` (`feat/issue-496-pacelc-catalog-bundle`)
- **Request / Changes / Result**: Added `scripts/pacelc_catalog.py` (`4,929` B), wired `scripts/build_dashboard.py` to emit `dashboard/data_pacelc.js` (`5,342` B, `window.LP_PACELC_CATALOG`, 17 topologies + 2 variants), logged `APP-011`; `make dashboard && make test && make lint` + `node --check` pass.

### ACT-184 - Land V5 PG_SCALE=20 Benchmarks, Charts 12-13, Dual Dashboard, Ch. 13 & Submodule v2.6.1 (#449-#494)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#449-#494` (`chore/issue-494-phase10-gov-v261`)
- **Request / Changes / Result**: Landed `results/benchmark_optimized.csv` (318 rows, #449 / PRs #450-#452), `results/logs/benchmark-optimized.log` (3,718 lines, #453 / PRs #454-#466), `generate_charts_v5.py` & `chart_12`-`chart_13` (#467 / PRs #468-#469), dual-dataset dashboard shards/UI (#470 / PRs #471-#474, #475 / PRs #476-#478), `tests/test_benchmark_artifacts.py` (#479 / PR #480), bilingual Ch. 13 (#481 / PRs #482-#483), Ch. 06 Sec. 8 (#484 / PR #485), Ch. 09 EN/FR (#486 / PR #487, #488 / PR #489), `README*` (#490 / PR #491, #492 / PR #493), `RCA-025`/`APP-010`, `Phase 10` completion, and `env/multi-db-docker-env` bump to `v2.6.1` (`3515629`, #494); every PR < 14,800 B with `make test` (21/21 OK) and `make lint` green.

### ACT-183 - Update `README.fr.md` & Add `Phase 9` Milestone (`#447`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#447` (`docs/issue-447-readme-fr-yt`)
- **Request / Changes / Result**: Updated `README.fr.md` with 310/301 row totals, `yt-cluster-async` E/H metrics, `chart_11` embed, `v2.4.1`, and Ch. 06/09 links, and added `Phase 9` milestone row; `make test` (`21/21` OK) and `make lint` pass.

### ACT-182 - Update `README.md` with YT Cluster 36-Row Matrix, `chart_11`, & `v2.4.1` (`#445`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#445` (`docs/issue-445-readme-en-yt`)
- **Request / Changes / Result**: Updated `README.md` with 310/301 row totals, `yt-cluster-async` E/H metrics, `chart_11` embed, `v2.4.1`, and Ch. 06/09 links; `make test` (`21/21` OK) and `make lint` pass.

### ACT-181 - Add Ch. 09 FR Traceability Matrix & Charts 08-11 (`#443`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#443` (`docs/issue-443-ch09-fr-matrix`)
- **Request / Changes / Result**: Added Master Traceability Matrix Tables A/B and `chart_08..11` embeds to `docs/fr/09_methodologie_benchmarks_et_graphiques.md`; `make test` (`21/21` OK) and `make lint` pass.

### ACT-180 - Update Ch. 09 FR Sections 1-4 Harness (`#441`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#441` (`docs/issue-441-ch09-fr-harness`)
- **Request / Changes / Result**: Updated Sections 1-4 (`17` topologies, `310/301` rows, `11` PNG charts); `make test` (`21/21` OK) and `make lint` pass.

### ACT-179 - Add Ch. 09 EN Traceability Matrix & Charts 08-11 (`#439`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#439` (`docs/issue-439-ch09-en-matrix`)
- **Request / Changes / Result**: Added Master Traceability Matrix Tables A/B and `chart_08..11` embeds to `docs/en/09_benchmarks_methodology_and_charts.md`; `make test` (`21/21` OK) and `make lint` pass.

### ACT-178 - Update Ch. 09 EN Sections 1-4 Harness (`#437`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#437` (`docs/issue-437-ch09-en-harness`)
- **Request / Changes / Result**: Updated Sections 1-4 (`17` topologies, `310/301` rows, `11` PNG charts); `make test` (`21/21` OK) and `make lint` pass.

### ACT-177 - Add Section 7 YT Cluster Comparison to Chapter 06 EN/FR (`#435`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#435` (`docs/issue-435-ch06-yt-comparison`)
- **Request / Changes / Result**: Added Section 7 comparative matrix, 4 architectural takeaways, and `chart_11` embed across `docs/en/06_empirical_test_and_benchmark_results.md` and `docs/fr/06_resultats_tests_et_benchmarks.md`; verified diff `< 14,800` chars, `make test` (`21/21` OK), and `make lint`.

### ACT-176 - Add Chart 11 YT Cluster vs Multi-Master Log Comparison (`#433`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#433` (`feat/issue-433-chart-11-yt-comparison`)
- **Request / Changes / Result**: Added `scripts/generate_charts_v4.py` and `assets/charts/chart_11_yt_cluster_vs_multimaster_log.png`, wired into `Makefile` (`charts`), enforced in `tests/test_benchmark_artifacts.py` (`EXPECTED_CHARTS`), and linked in EN/FR `docs/{en,fr}/solutions/yt_cluster_lite.md`; `make test` (`21/21` OK) and `make lint` pass.

### ACT-175 - Expand Charts 01-07 to All 17 PostgreSQL & YT Cluster Topologies (`#431`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#431` (`feat/issue-431-expand-charts-01-07`)
- **Request / Changes / Result**: Updated `chart_07` (`xlim(10, ...)`, 18 bars) and 17-topology `specs` in `scripts/generate_charts.py`, regenerated `assets/charts/chart_01..07_*.png` at 180 DPI with zero overlap; `make test` (`21/21` OK) and `make lint` pass.

### ACT-174 - Extract 18-Topology Chart Metadata & Update Chart Helpers (`#428`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#428` (`refactor/issue-428-chart-meta-helpers`)
- **Request / Changes / Result**: Extracted 18-topology palette, 6 CSVs, and suite labels into `scripts/chart_meta.py` (`2,087` B), updated `save_fig`/`draw_bars`/`draw_sweep` in `scripts/generate_charts.py`; verified `py_compile`, `make test` (`21/21` OK), and `make lint`.

### ACT-173 - Update YT Cluster Log, `yt_vs_mm` Preset, `RCA-024`, & Submodule `v2.4.1` (`#427`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#427` (`chore/issue-427-log-preset-submodule`)
- **Request / Changes / Result**: Updated `results/logs/yt-cluster-benchmark.log` (36 rows), added `data-preset="yt_vs_mm"` in `dashboard/{index.html,app.js}` and `tests/test_benchmark_artifacts.py`, bumped submodule `env/multi-db-docker-env` to `v2.4.1` (`0ec32dd`), logged `RCA-024`; `make test` (`21/21` OK) and `make lint` pass.

### ACT-172 - Complete 36-Row `yt-cluster-async` Benchmarks & Rebuild Dashboard (`#425`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#425` (`feat/issue-425-yt-async-36rows`)
- **Request / Changes / Result**: Expanded `results/benchmark_yt_cluster.csv` to 36 rows (`18` sync + `18` async, monotonic WAN `8.47->4.78->2.90`, `E3=133.55 TPS`, `0` drift), rebuilt `data_bench*.js` (`301` rows), updated `tests/test_benchmark_artifacts.py` (`36`/`301`, `18+18` suites) & `tests/test_solution_sheets.py` (`36`); `make test` (`21/21` OK), `make lint` pass.

### ACT-171 - Separate `LP_MATRIX_YT` in `dashboard/data_bench_yt.js` (Issue `#423`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#423` (`chore/issue-423-yt-matrix-sep`)
- **Request / Changes / Result**: Added blank-line separator between `LP_BENCH_ROWS_YT` and `LP_MATRIX_YT` in `scripts/build_dashboard.py` and rebuilt `dashboard/data_bench_yt.js` on current CSVs; verified `make test` (`21/21` OK), `make lint`, and PR diff `< 14,800` chars.

### ACT-170 - Populate Complete 18-Suite `yt-cluster-async` Metrics in EN/FR Sheets (Issue `#421`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#421` (`docs/issue-421-yt-async-solution-sheets`)
- **Request / Changes / Result**: Updated `docs/{en,fr}/solutions/yt_cluster_lite.md` (`13.4 KB` / `13.6 KB`, `116` lines) with full 18-suite empirical `yt-cluster-async` values (`0` drift) and `SQLSTATE 55000` async `recon` notes; passed `make test` (`21/21` OK), `make lint`, and PR diff `< 11,000` chars.

### ACT-169 - Separate `LP_BENCH_META` Header in `dashboard/data_bench.js` (Issue `#419`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#419` (`chore/issue-419-meta-line-sep`)
- **Request / Changes / Result**: Added blank-line separator between `LP_BENCH_META` and `LP_BENCH_ROWS_1` in `scripts/build_dashboard.py` and rebuilt `dashboard/data_bench.js` so later metadata updates avoid 11 KB context diffs; verified `make test` (`21/21` OK), `make lint`, and PR diff `< 14,800` chars.

### ACT-168 - Link Official dbinvent/yt Docker Hub and agent.md in README Solutions Catalog (Issue `#417`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#417` (`docs/issue-417-readme-yt-docker-agent-links`)
- **Request / Changes / Result**: Added official `https://hub.docker.com/r/dbinvent/yt` and `https://dbinvent.com/agent.md` references to row `#18` of the Solutions Catalog in `README.md` and `README.fr.md` (split from `#415` to keep every PR diff strictly `< 15,000` bytes); verified `make test` (`21/21` OK) and `make lint`.

### ACT-167 - Link Official dbinvent/yt Docker Hub Image and agent.md Reference in YT Cluster Sheets and READMEs (Issue `#415`)
- **Date**: `2026-11-21` | **Status**: `COMPLETED` | **Issue / Branch**: `#415` (`docs/issue-415-yt-cluster-docker-agent-refs`)
- **Request / Changes / Result**: Added direct links to `https://hub.docker.com/r/dbinvent/yt` and `https://dbinvent.com/agent.md` across `docs/en/solutions/yt_cluster_lite.md`, `docs/fr/solutions/yt_cluster_lite.md`, `README.md`, and `README.fr.md`, explicitly clarifying that `DBinvent/yt-cluster-lite` (MIT) is designed to be embedded and connected to a real `dbinvent/yt` cluster node (matching our live 3-node `dbinvent/yt:1.21.3` PoC); verified `make test` (`21/21` OK), `make lint`, and diff `< 15,000` chars.

### ACT-166 - Extend Tier 5 Popularity, Vitality and Freshness Parity Tests Across All 38 Sheets and 22 CSV Rows (Issue `#413`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#413` (`test/issue-413-tier5-popularity-parity`)
- **Request / Changes / Result**: Replaced the partial 4-column popularity loop in `tests/test_solution_sheets_tier5.py` with `test_tier5_popularity_vitality_and_freshness_parity(self)` enforcing Section 6 headings, 8-column headers, `2026-11-20T17:26:02Z` / `archived = false` intro, 3 synthesis bullets, positional sub-cell splitting (`\s+/\s+` on `rw[3..7]`), `N/A` zero-digit proprietary opacity (`edb-pgd`, `aurora-limitless`, `gcp-spanner-alloydb` + `pgadapter`), and dormant grounding across all 19 slugs (38 sheets) and 22 rows of `results/project_popularity.csv`; verified 7-bit ASCII, `make test` (`21/21` OK, `3/3` tier5), `make lint`, `make check-math`, `make check-security`, and diff `< 15,000` chars.

### ACT-165 - Align YT Cluster Lite (#18) EN/FR Section 6 With R1 Popularity Telemetry Schema and M4 Split Record (Issue `#411`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#411` (`docs/issue-411-yt-cluster-lite-popularity-align`)
- **Request / Changes / Result**: Replaced Section 6 in `docs/{en,fr}/solutions/yt_cluster_lite.md` with the canonical 8-column / 3-bullet R1 schema (`yt-cluster-lite` verbatim from `results/project_popularity.csv`, `2026-11-20T17:26:02Z`, clickable GitHub URL, `open_issues=0`, full `git_role`, full ISO `pushed_at`, `Tier C (Fragile / Young)` | `Current -- Young` | `High Risk` preserving `2026-11-13`, `vkrinitsyn`, `ytserv`, `20.6-41.5 TPS`, and `0A000` context), plus `docs/ACTION_LOGBOOK.md` and `docs/RCA_REGISTER.md` (`IMP-011`); verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-164 - Align PG 18 Native Clustering (#17) EN/FR Section 6 With R1 Popularity Telemetry Schema (Issue `#409`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#409` (`docs/issue-409-pg18-popularity-align`)
- **Request / Changes / Result**: Replaced Section 6 in `docs/{en,fr}/solutions/pg18_native_clustering.md` with the canonical 8-column / 3-bullet R1 schema (`postgres-core` + `patroni` verbatim from `results/project_popularity.csv`, `2026-11-20T17:26:02Z`, clickable GitHub URLs, `watchers`, `open_issues`, SPDX, full ISO `pushed_at`, preserving `58*`/`APP-007` mirror note and `PGDATA`/seccomp/`setval()` guidance while staying `< 13,800` B), plus `docs/ACTION_LOGBOOK.md`; verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-163 - Enrich Legacy Triggers (#14) EN/FR Sheets With 4-Repo Popularity Telemetry and Scrub #16 (Issue `#407`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#407` (`docs/issue-407-legacy-triggers-popularity`)
- **Request / Changes / Result**: Split M4 PR 8 into atomic 8a/8b/8c PRs to stay strictly under `< 15,000` diff chars; removed `#16` from line 88 of `docs/{en,fr}/solutions/legacy_triggers.md`, added 4-row Section 6 (`slony1`, `pgq`, `londiste`, `rubyrep` verbatim from `results/project_popularity.csv`, `2026-11-20T17:26:02Z`) and `Tier D (EOL / Dormant)` synthesis, plus `docs/ACTION_LOGBOOK.md`; verified zero `#16`, `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-162 - Enrich AWS Aurora Limitless (#12) and GCP Spanner/AlloyDB (#13) EN/FR Sheets With Popularity Telemetry (Issue `#405`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#405` (`docs/issue-405-cloud-popularity`)
- **Request / Changes / Result**: Added standardized Section 6 Git/telemetry status, `pushed_at` freshness, and Manageability synthesis (`aurora-limitless` `N/A`, `gcp-spanner-alloydb` `N/A`, and `spanner-pgadapter` `GoogleCloudPlatform/pgadapter` verbatim from `results/project_popularity.csv`, `2026-11-20T17:26:02Z`, zero invented counts on closed engines) to `docs/{en,fr}/solutions/aws_aurora_limitless.md` and `docs/{en,fr}/solutions/gcp_spanner_alloydb.md`, plus `docs/ACTION_LOGBOOK.md`; verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-161 - Enrich EDB PGD (#4) Proprietary EN/FR Sheets With Popularity Telemetry and M3 Split Record (Issue `#403`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#403` (`docs/issue-403-edb-pgd-popularity`)
- **Request / Changes / Result**: Added standardized Section 6 proprietary Git/telemetry status and Manageability synthesis (`edb-pgd` verbatim from `results/project_popularity.csv`, `2026-11-20T17:26:02Z`, zero invented GitHub counts) to `docs/en/solutions/edb_pgd.md` and `docs/fr/solutions/edb_pgd.md`, plus `docs/ACTION_LOGBOOK.md` and `docs/RCA_REGISTER.md` (`IMP-010`); verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-160 - Enrich SymmetricDS (#10) and PgPool-II (#11) EN/FR Sheets With Popularity Telemetry (Issue `#401`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#401` (`docs/issue-401-symmetricds-pgpool-popularity`)
- **Request / Changes / Result**: Split M3 PR 6 into PR 6a (`symmetricds` + `pgpool_ii`) and PR 6b (`edb_pgd`) to stay under the `< 15,000`-char PR diff ceiling; added standardized Section 6 GitHub popularity, git presence, `pushed_at` freshness, and Manageability synthesis (`symmetricds` and `pgpool2` verbatim from `results/project_popularity.csv`, `2026-11-20T17:26:02Z`, noting `35` mirror committers per `APP-007`) to `docs/{en,fr}/solutions/symmetricds.md` and `docs/{en,fr}/solutions/pgpool_ii.md`, plus `docs/ACTION_LOGBOOK.md`; verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-159 - Enrich OpenTenBase / Postgres-XL (#8) EN/FR Sheets With Popularity Telemetry (Issue `#399`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#399` (`docs/issue-399-opentenbase-popularity`)
- **Request / Changes / Result**: Added standardized Section 6 GitHub popularity, git presence, `pushed_at` freshness, and Manageability synthesis (`opentenbase` verbatim from `results/project_popularity.csv`, `2026-11-20T17:26:02Z`) to `docs/en/solutions/opentenbase_pgxl.md` and `docs/fr/solutions/opentenbase_pgxl.md`, plus `docs/ACTION_LOGBOOK.md`; verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-158 - Enrich Bucardo (#9) and pglogical 2 (#3) EN/FR Sheets With Popularity Telemetry (Issue `#397`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#397` (`docs/issue-397-bucardo-pglogical2-popularity`)
- **Request / Changes / Result**: Split M3 PR 5 into PR 5a (`bucardo` + `pglogical2`) and PR 5b (`opentenbase_pgxl`) to stay under the `< 15,000`-char PR diff ceiling; added standardized Section 6 GitHub popularity, git presence, `pushed_at` freshness, and Manageability synthesis (`bucardo` and `pglogical2` verbatim from `results/project_popularity.csv`, `2026-11-20T17:26:02Z`) to `docs/{en,fr}/solutions/bucardo.md` and `docs/{en,fr}/solutions/pglogical2.md`, plus `docs/ACTION_LOGBOOK.md`; verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-157 - Enrich YugabyteDB (#5) and PG 17 Bi-Directional Logical (#1) EN/FR Sheets With Popularity Telemetry (Issue `#395`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#395` (`docs/issue-395-yugabyte-birep-popularity`)
- **Request / Changes / Result**: Added standardized Section 6 GitHub popularity, git presence, `pushed_at` freshness, and Manageability synthesis (`yugabytedb` and `postgres-core` verbatim from `results/project_popularity.csv`, `2026-11-20T17:26:02Z`) to `docs/{en,fr}/solutions/yugabytedb.md` and `docs/{en,fr}/solutions/pg17_bidirectional_logical.md` (no compaction needed), plus `docs/ACTION_LOGBOOK.md`; verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-156 - Compact FR and Enrich CockroachDB (#6) EN/FR Sheets With Popularity Telemetry (Issue `#393`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#393` (`docs/issue-393-cockroachdb-popularity`)
- **Request / Changes / Result**: Compacted 3 non-numeric FR prose lines (`L22`, `L24`, `L48`) in `docs/fr/solutions/cockroachdb.md` (`13,587` B / `161` L) and appended standardized Section 6 (`cockroachdb` verbatim from `results/project_popularity.csv`, `2026-11-20T17:26:02Z`) to `docs/en/solutions/cockroachdb.md` (`13,606` B / `161` L) and `docs/fr/solutions/cockroachdb.md`, plus `docs/ACTION_LOGBOOK.md`; verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-155 - Compact and Enrich Citus (#7) EN/FR Sheets With Popularity Telemetry (Issue `#391`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#391` (`docs/issue-391-citus-popularity`)
- **Request / Changes / Result**: Split M2 PR 3 into PR 3a (`citus`) and PR 3b (`cockroachdb`) to stay under the `< 15,000`-char diff limit; compacted 4 non-numeric prose lines (`L22`, `L24`, `L45`, `L52`) and added standardized Section 6 (`citus` verbatim from `results/project_popularity.csv`, `2026-11-20T17:26:02Z`) to `docs/en/solutions/citus.md` (`13,325` B / `155` L) and `docs/fr/solutions/citus.md` (`13,375` B / `155` L), plus `docs/ACTION_LOGBOOK.md` and `docs/RCA_REGISTER.md` (`IMP-009`); verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-154 - Enrich PG 17 Uni-Directional Logical (#16) EN/FR Sheets With Popularity Telemetry (Issue `#389`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#389` (`docs/issue-389-logical-uni-popularity`)
- **Request / Changes / Result**: Added standardized Section 6 GitHub popularity, git presence, `pushed_at` freshness, and Manageability synthesis (`postgres-core`, preserving `#16` with zero `#14` collisions) from `results/project_popularity.csv` (`2026-11-20T17:26:02Z`) to `docs/en/solutions/pg17_logical_unidirectional.md` (`13,516` B / `157` L) and `docs/fr/solutions/pg17_logical_unidirectional.md` (`13,321` B / `157` L), plus `docs/ACTION_LOGBOOK.md` and `docs/RCA_REGISTER.md` (`IDEA-008`); verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-153 - Enrich pgEdge Spock (#2) EN/FR Sheets With Popularity Telemetry (Issue `#387`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#387` (`docs/issue-387-pgedge-spock-popularity`)
- **Request / Changes / Result**: Added standardized 3-repo Section 6 GitHub popularity, git presence, `pushed_at` freshness, and Manageability synthesis (`pgedge-spock`, `pgedge-snowflake`, `pgedge-lolor`) from `results/project_popularity.csv` (`2026-11-20T17:26:02Z`) to `docs/en/solutions/pgedge_spock.md` (`13,714` B / `165` L) and `docs/fr/solutions/pgedge_spock.md` (`13,718` B / `165` L), plus `docs/ACTION_LOGBOOK.md`; verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-152 - Compact pgEdge Spock (#2) EN/FR Sheets for Popularity Telemetry Headroom (Issue `#385`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#385` (`docs/issue-385-pgedge-spock-compact`)
- **Request / Changes / Result**: Compacted non-numeric descriptive prose in `docs/en/solutions/pgedge_spock.md` (`12,973` B -> `12,146` B) and `docs/fr/solutions/pgedge_spock.md` (`13,158` B -> `12,118` B) while preserving all benchmark CSV metrics, functional probes, SQLSTATEs, and EN/FR table shapes for Section 6 popularity headroom, and updated `docs/ACTION_LOGBOOK.md`; verified `make test`, `make lint`, and PR diff `< 15,000` chars.

### ACT-151 - Enrich PG 17 Standalone (#15a) EN/FR Sheets With Popularity Telemetry (Issue `#383`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#383` (`docs/issue-383-standalone-popularity`)
- **Request / Changes / Result**: Added standardized Section 6 GitHub popularity, git presence, `pushed_at` freshness, and Manageability synthesis (`postgres-core`) from `results/project_popularity.csv` (`2026-11-20T17:26:02Z`) to `docs/en/solutions/pg17_standalone.md` (`11,376` B / `159` L) and `docs/fr/solutions/pg17_standalone.md` (`12,194` B / `159` L), plus `docs/ACTION_LOGBOOK.md`; verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-150 - Enrich PG 17 Streaming/Patroni (#15b) EN/FR Sheets With Popularity Telemetry (Issue `#381`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#381` (`docs/issue-381-patroni-popularity`)
- **Request / Changes / Result**: Compacted EN prose in `docs/en/solutions/pg17_physical_streaming_patroni.md` and added Section 6 GitHub popularity, git presence, `pushed_at` freshness, and Manageability synthesis (`postgres-core` + `patroni`) from `results/project_popularity.csv` (`2026-11-20T17:26:02Z`) to both `docs/{en,fr}/solutions/pg17_physical_streaming_patroni.md` (`13,749` B EN / `13,723` B FR, `162` L), plus `docs/ACTION_LOGBOOK.md`; verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-149 - Compact FR PG 17 Streaming/Patroni (#15b) Sheet & Log M1 Governance (Issue `#379`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#379` (`docs/issue-379-fr-patroni-compact`)
- **Request / Changes / Result**: Compacted prose and Table D notes in `docs/fr/solutions/pg17_physical_streaming_patroni.md` (`13,205` B -> `12,361` B, preserving all benchmark/probe numbers and table shapes) for Section 6 popularity headroom, and updated `docs/ACTION_LOGBOOK.md` + `docs/RCA_REGISTER.md` (`IMP-008`, `APP-009`); verified `make test` (`20/20` OK), `make lint`, and PR diff `< 15,000` chars.

### ACT-148 - Finalize Wave 4 Governance Registers (ACTION_LOGBOOK & RCA_REGISTER) (Issue `#375`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#375` (`docs/issue-375-wave4-governance-registers`)
- **Request / Changes / Result**: Added Phase 8 Wave 4 milestone and `ACT-143..148` in `docs/ACTION_LOGBOOK.md`, and logged `RCA-021..023`, `IMP-007`, `APP-008`, and `IDEA-007` in `docs/RCA_REGISTER.md` (100% 7-bit ASCII English, zero banned terms/paths); `make test` (`20/20` OK), `make lint` (all 13 submodule Compose files valid), and `node --check` on all `dashboard/*.js` verified in WSL2.

### ACT-147 - Update Root READMEs, Upgrade 19-Slug E2E Tests & Bump Submodule to v2.4.0 (Issues `#367`, `#369`, `#371`, `#373`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#367`/`#369`/`#371`/`#373` (`PRs #368`, `#370`, `#372`, `#374`)
- **Request / Changes / Result**: Updated `README.md` (`PR #368`, `10,892` B) and `README.fr.md` (`PR #370`, `10,844` B) with the 19-row Solutions Catalog (`#17` PG 18.6 native clustering, `#18` YT Cluster Lite), 17 benchmarked topologies / 287 rows, and 22 ecosystem entries; upgraded `tests/test_solution_sheets*.py` (`PR #372`, `13,556` B) to strict 19-slug / 38-sheet / 19-row catalog parity with PG 18.6 & YT Cluster CSV and popularity checks; bumped `env/multi-db-docker-env` submodule to `v2.4.0` (`e130508f89bf9c9c61cad3f7aa8d9299e4bcca93`) and wired `yt-cluster` (13 stacks total) + `bench-yt-cluster` in `Makefile` and `stacks/README.md` (`PR #374`, `3,902` B); verified `make lint` (13 stacks) and `make test` (`20/20` OK).

### ACT-146 - Publish Bilingual Sheets #17-#18 and Update Core Chapters 01, 03a, 04, 07, 11 EN/FR (Issues `#343`..`#365`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#343`..`#365` (`PRs #344`..`#366`)
- **Request / Changes / Result**: Added symmetric bilingual architecture sheets `docs/{en,fr}/solutions/yt_cluster_lite.md` (`#18`, 19th sheet) and `docs/{en,fr}/solutions/pg18_native_clustering.md` (`#17`, 18th sheet), and updated core Chapters `01`, `03a`, `04`, `07`, and `11` (EN and FR, splitting Ch. 11 into matrix + insights PRs to stay strictly `< 14,500` B) across 12 atomic PRs; verified `make test` (`20/20` OK) on every PR.

### ACT-145 - Upgrade Offline Dashboard to 17 Topologies (287 Rows) & Artifact Tests (Issues `#333`..`#341`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#333`..`#341` (`PRs #334`..`#342`)
- **Request / Changes / Result**: Extended `scripts/build_dashboard.py` and added `dashboard/data_bench_yt.js` (`22` rows + `1` matrix row), regenerated `dashboard/data_bench.js` (`17` topologies, `287` total rows) and `dashboard/data_popularity.js` (`22` entries), upgraded `dashboard/{index.html,styles.css,app.js,charts.js,popularity.js}` (`13,197` B, zero CDN, `node --check` PASS), and completed `tests/test_benchmark_artifacts.py` (`PR #342`); verified `make test` (`20/20` OK).

### ACT-144 - Update Charts 08-09 & generate_charts_v3.py for 19 Public Repos (Issues `#329`, `#331`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#329`/`#331` (`PRs #330`, `#332`)
- **Request / Changes / Result**: Compacted `chart_09`/`chart_10` typography kwargs in `scripts/generate_charts_v3.py` (`PR #330`, `7,301` B) to maintain the `< 14 KB` script cap, then added `DBinvent/yt-cluster-lite` (`19th` public repo) and regenerated 180-DPI Log10 PNGs `chart_08_popularity_stars_forks_log.png` and `chart_09_popularity_commits_activity_log.png` (`PR #332`, `8,909` B); verified `py_compile` and `make test` (`20/20` OK).

### ACT-143 - Land YT Cluster 1.21.3 Live PoC Artifacts & 22-Entry Popularity Dataset (Issues `#325`, `#327`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#325`/`#327` (`PRs #326`, `#328`)
- **Request / Changes / Result**: Added `results/benchmark_yt_cluster.csv` (`22` rows across sync `cc=half` `yt-cluster` and async `cc=0` `yt-cluster-async`), `results/functional_limits_yt_cluster.csv` (`1` row), and `results/logs/yt-cluster-benchmark.log` (`PR #326`, `10,398` B), and added `DBinvent/yt-cluster-lite` to `scripts/collect_popularity.py` and `results/project_popularity.csv` (`22` rows / `19` public repos, `PR #328`, `11,429` B); verified `make test` (`20/20` OK).

### ACT-142 - Finalize Wave 3 Governance Registers (ACTION_LOGBOOK & RCA_REGISTER) (Issue `#321`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#321` (`docs/issue-321-wave3-governance-registers`)
- **Request / Changes / Result**: Marked Phase 6 Complete, added Phase 7 Wave 3 milestone and `ACT-137..142` in `docs/ACTION_LOGBOOK.md`, and logged `RCA-016..020`, `IMP-006`, `APP-007`, and `IDEA-006` in `docs/RCA_REGISTER.md` (100% 7-bit ASCII English, zero banned terms/paths); `make test` (`20/20` OK) and `make lint` (all 12 submodule stacks valid) verified in WSL2.

### ACT-141 - Bump Submodule to v2.3.0, Extend Makefile & Update READMEs (Issues `#317`, `#319`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#317` (`chore/issue-317-submodule-v230-makefile-readmes`), `#319` (`docs/issue-319-readme-fr-wave3`)
- **Request / Changes / Result**: Updated Git submodule `env/multi-db-docker-env` to `v2.3.0` (`8ea028b7c932af45bad7b6d19263fb0359ac9041`), extended `Makefile` (`PG_STACKS` with `pg18-streaming`, `pg18-logical`, `pg18-birep` for 12 Compose stacks, `popularity`, `bench-pg18`, and V3 `charts` target) and `stacks/README.md`, and updated `README.md` (`PR #318`, `10,387` B) and `README.fr.md` (`PR #320`, `7,306` B) with Chapters 11-12, Charts 08-10, and 15-topology / 274-row counts while preserving the 17-row Solutions Catalog and branding; `make test` (`20/20` OK) and `make lint` (12 stacks) verified.

### ACT-140 - Publish Bilingual Chapters 11-12 and Cross-Chapter PG 18.6 Updates (Issues `#305`..`#315`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#305`/`#307`/`#309`/`#311`/`#313`/`#315` (`PRs #306..#316`)
- **Request / Changes / Result**: Landed symmetric bilingual Chapter 11 (`docs/en/11_ecosystem_popularity_and_vitality.md`, `docs/fr/11_popularite_et_vitalite_ecosysteme.md`), Chapter 12 (`docs/en/12_postgresql_18_clustering_and_benchmarks.md`, `docs/fr/12_clustering_postgresql_18_et_benchmarks.md`), and targeted PG 18.6/Wave 3 cross-chapter updates across `docs/{en,fr}/{06,08,09,10}_*.md` across 6 atomic `< 14 KB` PRs; verified `make test` (`20/20` OK, LaTeX math, security, Tiers 1-5 E2E parity) and `make lint`.

### ACT-139 - Upgrade Offline Dashboard V3 (15 Topologies + Popularity Tab) & Artifact Tests (Issues `#283`..`#303`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#283`..`#303` (`PRs #284..#304`)
- **Request / Changes / Result**: Updated `scripts/build_dashboard.py`, regenerated `dashboard/data_bench.js`, added `data_bench_pg18.js` (87 rows), `data_matrix_pg18.js` (5 rows), `data_popularity.js` (21 rows), and `dashboard/popularity.js`, upgraded `dashboard/{charts.js,styles.css,index.html,app.js}` via atomic `< 14 KB` PRs (`node --check` PASS on all 11 JS files, zero CDN), and extended `tests/test_benchmark_artifacts.py` (`PR #304`) validating 10 charts, 15 topologies, PG 18.6 CSVs, and popularity bundles (`20/20` OK).

### ACT-138 - Land PostgreSQL 18.6 Empirical Datasets, Benchmark Log & Charts 08-10 (Issues `#275`..`#281`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#275`/`#277`/`#279`/`#281` (`PRs #276..#282`)
- **Request / Changes / Result**: Added `results/functional_limits_pg18.csv` (5 topologies x 26 probes), `results/benchmark_pg18.csv` (87 standardized rows across `pg18-standalone`, `pg18-async-streaming`, `pg18-sync-streaming`, `pg18-logical`, `pg18-birep`), `results/logs/pg18-benchmark.log`, `scripts/generate_charts_v3.py`, and 180-DPI Log10 PNG charts `chart_08..10`; all PRs strictly `< 14 KB` with `make test` (`20/20` OK) and `make lint`.

### ACT-137 - Add Live GitHub Ecosystem Popularity Collector & Dataset (Issues `#273`, `#275`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#273` (`PR #274`), `#275` (`PR #276`)
- **Request / Changes / Result**: Added `scripts/collect_popularity.py` (`11,875` B diff, stdlib Python querying GitHub REST/GraphQL pagination headers, `subscribers_count`, canonical redirects, and `TAG_COMMIT_DATE` fallback) and `results/project_popularity.csv` (21 rows: 18 public repos + 3 proprietary/managed engines, snapshot `2026-11-20T13:34:55Z`); verified `make test` (`20/20` OK) and `make lint`.

### ACT-136 - Add Tier 5 Adversarial E2E Suite for README Catalog, 4-CSV Row Parity, and EN/FR Tables (Issue `#271`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#271` (`test/issue-271-tier5-e2e-suite`)
- **Request / Changes / Result**: Added `tests/test_solution_sheets_tier5.py` (`10,815` bytes LF, pure 7-bit ASCII, `CLUSTER_PG_REPO_ROOT`-aware with zero duplicate `TestCase` discovery) verifying the 17-row 4-column Solutions Catalogs in `README.md` / `README.fr.md`, headline CSV numbers across `README*` / `06*`, row-scoped metrics across all 4 benchmark CSVs (`187` rows), `L1-L8`/`T11-T18` matrix metrics (`T11` `rows/s`, `T15` `p50/p95/max`), and EN/FR table shape parity across all 17 pairs; `make test` (`20/20` OK), `make lint`, and `make test-solution-sheets-tier5` verified in WSL2.

### ACT-135 - Harden E2E Tiers 1-4 Validators and Fix Makefile test-% Resolution (Issue `#269`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#269` (`test/issue-269-harden-e2e-and-makefile`)
- **Request / Changes / Result**: Tightened `tests/test_solution_sheets.py` (`DHDR_RE` valid direction anchor, bracketed node-label inner-quote check + self-tests, strict `ma AND mb` Modes header check) and `tests/test_solution_sheets_parity.py` (unconditional `p99` pipe-table rejection, `[A-H]\d?_[a-z0-9_]+` `REF` row check with `*`/`\`` numeric wrappers, `*`/`\`` wrapper support on `pg17_standalone` `F_wan_netem`); fixed `Makefile:75` to resolve `tests/test_$${u}.py`; verified `make test` (`18/18` OK), `make lint`, `make test-solution-sheets`, and `make test-solution_sheets` in WSL2.

### ACT-134 - Log RCA-015 for Tier 5 Documentation Drift and E2E Blind Spots (Issue `#267`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#267` (`docs/issue-267-rca-015`)
- **Request / Changes / Result**: Added `RCA-015` in `docs/RCA_REGISTER.md` (100% 7-bit ASCII English) documenting the Suite E attempted-vs-committed denominator contradiction, cross-chapter precision drift, and Tier 5 E2E test/Makefile blind spots; `make test` (`18/18` OK) and `make lint` verified in WSL2.

### ACT-133 - Align Suite E Denominators and Cross-Chapter Precision (Issue `#265`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#265` (`docs/issue-265-tier5-docs-precision`)
- **Request / Changes / Result**: Fixed Suite E `tx_failed` denominators in `docs/en/06_empirical_test_and_benchmark_results.md:82-84` and `docs/fr/06_resultats_tests_et_benchmarks.md:71-73` to total attempts (`3,806` for `citus`, `2,574` for `yugabyte`, `1,587` for `cockroach`); aligned `#15a` Tier `T0`/`N0` and `snowflake.node` (`1..1023`) in `03a` EN/FR, OpenTenBase (`PG 10-11` fork + backports) in `03b` FR, and `BYTEA=65536B;` in `pgedge_spock.md:133` EN/FR; `make test` (`18/18` OK) and `make lint` verified in WSL2.

### ACT-132 - Integrate E2E Tiers 3-4 Parity and Navigation Test Suite (Issue `#263`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#263` (`test/issue-263-e2e-solution-sheets-parity`)
- **Request / Changes / Result**: Added `tests/test_solution_sheets_parity.py` (`12,265` bytes LF, pure 7-bit ASCII) covering E2E Tiers 3-4 (CSV telemetry parity across `benchmark_summary.csv`, `functional_limits_matrix.csv`, and `extended_functional_matrix.csv`, `lat_p99_ms`/`p99` anti-fabrication guard, non-benchmarked reference disclaimers, navigation back-links/relative links, EN/FR symmetry, `#14`/`#16` collision guard, and Ch01 freshness); `make test-solution_sheets_parity` (`2/2` OK), `make test` (`18/18` OK), and `make lint` verified in WSL2.

### ACT-131 - Integrate E2E Tiers 1-2 Solution Sheets Test Suite (Issue `#261`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#261` (`test/issue-261-e2e-solution-sheets`)
- **Request / Changes / Result**: Added `tests/test_solution_sheets.py` (`12,254` bytes LF, pure 7-bit ASCII) covering E2E Tiers 1-2 (17-slug parity, bilingual metadata/attribution headers, A4 density bounds, pure-stdlib Mermaid validator + self-tests, structural sections/tables, and math/governance/security compliance); `make test-solution_sheets` (`3/3` OK), `make test` (`16/16` OK), and `make lint` verified in WSL2.

### ACT-130 - Fix AWS Aurora Limitless Deep-Link and Align ACT-124 Line References (Issue `#259`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#259` (`docs/issue-259-aws-limitless-url-and-logbook`)
- **Request / Changes / Result**: Replaced stale `AuroraPostgreSQL.Limitless.html` redirect URL with canonical HTTP-200 `https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/limitless.html` in `README.md:90` and `README.fr.md:85`, and aligned `ACT-124` in `docs/ACTION_LOGBOOK.md` to post-edit lines `89 and 93` in `docs/fr/03a_catalogue_natif_et_extensions.md`; live HTTP `200` (zero redirects), `make test` (`13/13` OK), and `make lint` verified.

### ACT-129 - Align pgpool_ii EN/FR Check Counts with test_pgpool.sh Runtime Assertions (Issue `#257`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#257` (`docs/issue-257-pgpool-check-count`)
- **Request / Changes / Result**: Clarified `docs/en/solutions/pgpool_ii.md:74,89` and `docs/fr/solutions/pgpool_ii.md:74,89` to report `25` runtime `PASS` assertions across `18` functional groups (`24` documented in `env/multi-db-docker-env/documentation/pgpool_cluster.md`); `make test` (`13/13` OK) and `make lint` verified.

### ACT-128 - Disambiguate #16 pg17-logical in Ch. 06 and Log RCA-014 (Issue `#255`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#255` (`docs/issue-255-ch06-id-polish-rca014`)
- **Request / Changes / Result**: Updated `docs/en/06_empirical_test_and_benchmark_results.md:26` (`#14 pg17-logical` -> `#16 pg17-logical`) and `docs/fr/06_resultats_tests_et_benchmarks.md:18` (added `(#16)`) with explicit `#16` vs `#14` disambiguation footnotes; logged `RCA-014` in `docs/RCA_REGISTER.md` (split `pgpool_ii` check-count alignment into follow-up PR to keep diff `< 15,000` bytes); `make test` (`13/13` OK) and `make lint` verified.

### ACT-127 - Update Ch. 01 EN/FR Status and Chapter 02-10 Navigation Links (Issue `#253`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#253` (`docs/issue-253-ch01-status-links`)
- **Request / Changes / Result**: Updated `docs/en/01_executive_summary_and_taxonomy.md` and `docs/fr/01_synthese_et_taxonomie.md` to clear stale `Pending` / `phase empirique suivante` / `apres execution complete` text, fixed the Chapter 08 title (`08 - Limits & Failure Modes`), and added clickable Markdown links for Chapters `02` through `10` (including `06`, `08`, `09`, `10`); `make test` (`13/13` OK) and `make lint` verified.

### ACT-126 - Add 03b FR Solution Navigation Table and Section Links (Issue `#251`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#251` (`docs/issue-251-03b-fr-links`)
- **Request / Changes / Result**: Updated `docs/fr/03b_catalogue_distribue_triggers_cloud.md` with the 10-row `Fiches d'architecture detaillees (perimetre 03b)` index table (`#5`..`#14`) and 10 per-section `Fiche dediee` links to all 10 `docs/fr/solutions/*.md` sheets (`yugabytedb`, `cockroachdb`, `citus`, `opentenbase_pgxl`, `bucardo`, `symmetricds`, `pgpool_ii`, `aws_aurora_limitless`, `gcp_spanner_alloydb`, `legacy_triggers`), keeping `#14` solely on `legacy_triggers` and line 5 with zero `#16` mentions; `make test` (`13/13` OK) and `make lint` verified.

### ACT-125 - Add 03b EN Solution Navigation Table and Section Links (Issue `#249`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#249` (`docs/issue-249-03b-en-links`)
- **Request / Changes / Result**: Updated `docs/en/03b_solutions_distributed_triggers_cloud.md` with the 10-row `Dedicated Architecture Sheets (03b Scope)` index table (`#5`..`#14`) and per-section `Dedicated Sheet` links to all 10 `docs/en/solutions/*.md` sheets (`yugabytedb`, `cockroachdb`, `citus`, `opentenbase_pgxl`, `bucardo`, `symmetricds`, `pgpool_ii`, `aws_aurora_limitless`, `gcp_spanner_alloydb`, `legacy_triggers`), keeping `#14` solely on `legacy_triggers` with zero `#16` mentions; `make test` (`13/13` OK) and `make lint` verified.

### ACT-124 - Add 03a FR Solution Links, #16 Section, and EDB PGD Harmonization (Issue `#247`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#247` (`docs/issue-247-03a-fr-links-edb-sync`)
- **Request / Changes / Result**: Updated `docs/fr/03a_catalogue_natif_et_extensions.md` intro (`L5`), inserted the 7-row `03a` dedicated sheets table and per-section `Fiche(s) dediee(s)` links, appended `## #16` (`pg17-logical`, `N3`) with zero `#14` mentions, and harmonized EDB PGD lines 89 and 93 (`bdr.crdt_*`, `bdr.conflict_history`, `snowflakeid`, `galloc`, `timeshard`); `make test` (`13/13` OK) and `make lint` verified.

### ACT-123 - Add 03a EN Solution Links, #16 Section, and EDB PGD Harmonization (Issue `#245`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#245` (`docs/issue-245-03a-en-links-edb-sync`)
- **Request / Changes / Result**: Updated `docs/en/03a_solutions_native_and_extensions.md` with the 7-row `03a` Dedicated Architecture Sheets index table (`pg17_bidirectional_logical`, `pgedge_spock`, `pglogical2`, `edb_pgd`, `pg17_standalone`, `pg17_physical_streaming_patroni`, `pg17_logical_unidirectional`), per-section `Dedicated Sheet(s)` links, a new `Solution #16` (`pg17-logical`, `T3`) subsection, and harmonized EDB PGD CRDT (`bdr.crdt_*`, `bdr.conflict_history`) and `bdr.global_sequences` (`snowflakeid`, Raft `galloc`, legacy `timeshard`) terminology; `make test` (`13/13` OK) and `make lint` verified.

### ACT-122 - Add Solutions Catalog Table and Fix #16 pg17-logical ID in README.fr.md (Issue `#243`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#243` (`docs/issue-243-readme-fr-catalog`)
- **Request / Changes / Result**: Fixed `README.fr.md:22` (`Logique Uni (#14)` -> `Logique Uni (#16)`) and inserted section `2b. Catalogue des solutions et fiches techniques` with the 17-row French table, `#16` vs `#14` disambiguation blockquote, verified Product/Docs URLs, GitHub repositories (or `Proprietaire / N/A`), and 1-sentence descriptions linking all 17 `docs/fr/solutions/*.md` sheets; `make test` (`13/13` OK) and `make lint` verified.

### ACT-121 - Add Solutions Catalog Table and Fix #16 pg17-logical ID in README.md (Issue `#241`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#241` (`docs/issue-241-readme-en-catalog`)
- **Request / Changes / Result**: Fixed `README.md:32` (`pg17-logical` `#14` -> `#16 Uni`) and inserted the 17-row `Solutions Catalog & Architecture Sheets` table with `#16` vs `#14` disambiguation blockquote, verified official Product/Docs links, GitHub repositories (or `Proprietary / N/A`), and 1-sentence descriptions linking all 17 `docs/en/solutions/*.md` sheets; `make test` (`13/13` OK) and `make lint` verified.

### ACT-120 - Add French Architectural Reference Sheet for Legacy Triggers (#14) (Issue `#239`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#239` (`docs/issue-239-legacy-triggers-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/legacy_triggers.md` mirroring `docs/en/solutions/legacy_triggers.md` section-for-section (`#14`, Architectural Reference, Historical / EOL) with French 3-subgraph Mermaid diagram, trigger write-amplification model, explicit `#14` vs `#16` (`pg17-logical`) disambiguation, strengths/weaknesses, verified `results/*.csv` baselines (`#9 bucardo`, `pg17-logical`, `#1 pg-birep`, `#15a pg17-standalone`), and Ch. 03b/10 footer links; `make test` (`13/13` OK) and `make lint` verified.

### ACT-119 - Add English Architectural Reference Sheet for Legacy Triggers (#14) (Issue `#237`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#237` (`docs/issue-237-legacy-triggers-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/legacy_triggers.md` (`#14`, Architectural Reference, Historical / EOL) covering Slony-I (`logTrigger`, `slon`, `EXECUTE SCRIPT`), Londiste/Skytools (`pgq.logutriga`, `pgq.ticker`), and RubyRep (`rr_pending_changes`), with 3-subgraph Mermaid diagram, trigger write-amplification model, explicit `#14` vs `#16` (`pg17-logical`) disambiguation, strengths/weaknesses, verified `results/*.csv` baselines (`#9 bucardo`, `pg17-logical`, `#1 pg-birep`, `#15a pg17-standalone`), and Ch. 03b/10 footer links; `make test` (`13/13` OK) and `make lint` verified.

### ACT-118 - Add French Architectural Reference Sheet for GCP Spanner & AlloyDB (#13) (Issue `#235`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#235` (`docs/issue-235-gcp-spanner-alloydb-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/gcp_spanner_alloydb.md` mirroring `docs/en/solutions/gcp_spanner_alloydb.md` section-for-section (`#13`, Architectural Reference, `APP-005` managed cloud exclusion) with French dual-subgraph Mermaid diagram, TrueTime commit-wait latency model, implementation modes, strengths/weaknesses, verified `results/*.csv` baselines (`#6 cockroach`, `#5 yugabyte`, `#15b pg17-sync-streaming`), and Ch. 03b/10 footer links; `make test` (`13/13` OK) and `make lint` verified.

### ACT-117 - Add English Architectural Reference Sheet for GCP Spanner & AlloyDB (#13) (Issue `#233`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#233` (`docs/issue-233-gcp-spanner-alloydb-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/gcp_spanner_alloydb.md` (`#13`, Architectural Reference, `APP-005` managed cloud exclusion) disambiguating Cloud Spanner PG Interface (`PGAdapter`, Multi-Paxos, TrueTime commit-wait, zero C extensions) from single-primary AlloyDB / AlloyDB Omni (Log Processing Service, Read Pools, Columnar Engine), with dual-subgraph Mermaid diagram, implementation modes, strengths/weaknesses, verified `results/*.csv` baselines (`#6 cockroach`, `#5 yugabyte`, `#15b pg17-sync-streaming`), and Ch. 03b/10 footer links; `make test` (`13/13` OK) and `make lint` verified.

### ACT-116 - Add French Architectural Reference Sheet for AWS Aurora Limitless (#12) (Issue `#231`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#231` (`docs/issue-231-aws-aurora-limitless-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/aws_aurora_limitless.md` mirroring `docs/en/solutions/aws_aurora_limitless.md` section-for-section (`#12`, Architectural Reference, `APP-005` managed cloud exclusion) with French Mermaid diagram, AWS Time Sync MVCC latency model, implementation modes, strengths/weaknesses, verified `results/*.csv` `T5` baselines (`#7 citus`, `#5 yugabyte`, `#6 cockroach`, `#15a pg17-standalone`), and Ch. 03b/10 footer links; `make test` (`13/13` OK) and `make lint` verified.

### ACT-115 - Add English Architectural Reference Sheet for AWS Aurora Limitless (#12) (Issue `#229`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#229` (`docs/issue-229-aws-aurora-limitless-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/aws_aurora_limitless.md` (`#12`, Architectural Reference, `APP-005` managed cloud exclusion) with Mermaid DB Shard Group and 4/6 storage quorum diagram, AWS Time Sync MVCC latency model, implementation modes (Standard Aurora, Limitless Single-Shard vs Multi-Shard 2PC, Global DB Write Forwarding, retired Multi-Master v1), strengths/weaknesses, verified `results/*.csv` `T5` baselines (`#7 citus`, `#5 yugabyte`, `#6 cockroach`, `#15a pg17-standalone`), and Ch. 03b/10 footer links; `make test` (`13/13` OK) and `make lint` verified.

### ACT-114 - Add French Architectural Reference Sheet for SymmetricDS (#10) (Issue `#227`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#227` (`docs/issue-227-symmetricds-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/symmetricds.md` mirroring `docs/en/solutions/symmetricds.md` section-for-section (`#10`, Architectural Reference, explicitly not live-benchmarked) with French Mermaid diagram, trigger/channel/HTTP batch modes, `sym_conflict` detection/resolution, strengths/weaknesses, verified `results/benchmark_summary.csv` and `results/extended_functional_matrix.csv` anchors (`#9 bucardo`, `#2 pgedge`, `#1 pg-birep`), and Ch. 03b/10 footer links; `make test` (`13/13` OK) and `make lint` verified.

### ACT-113 - Add English Architectural Reference Sheet for SymmetricDS (#10) (Issue `#225`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#225` (`docs/issue-225-symmetricds-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/symmetricds.md` (`#10`, Architectural Reference, explicitly not live-benchmarked) with Mermaid trigger/Java HTTP/HTTPS batch data-flow diagram, latency model, implementation modes (hub-and-edge, bidirectional mesh, heterogeneous cross-DB, `sym_conflict` detection/resolution, `symadmin`), strengths/weaknesses, verified `results/benchmark_summary.csv` and `results/extended_functional_matrix.csv` anchors (`#9 bucardo`, `#2 pgedge`, `#1 pg-birep`), and Ch. 03b/10 footer links; `make test` (`13/13` OK) and `make lint` verified.

### ACT-112 - Add French Architectural Reference Sheet for PgPool-II (#11) (Issue `#223`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#223` (`docs/issue-223-pgpool-ii-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/pgpool_ii.md` mirroring `docs/en/solutions/pgpool_ii.md` section-for-section (`#11`, Architectural Reference, explicitly not live-benchmarked) with French Mermaid diagram, streaming vs broadcast/SI implementation modes, Watchdog quorum, strengths/weaknesses, verified `results/benchmark_summary.csv` anchors (`#15b`, `#1 pg-birep`), and Ch. 03b/10 footer links; `make test` (`13/13` OK) and `make lint` verified.

### ACT-111 - Add English Architectural Reference Sheet for PgPool-II (#11) (Issue `#221`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#221` (`docs/issue-221-pgpool-ii-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/pgpool_ii.md` (`#11`, Architectural Reference, explicitly not live-benchmarked) disambiguating `streaming_replication` (companion Docker PoC `pgpool/pgpool:4.6` with HAProxy `5100`/`5101`/`8406` and 3x `postgres:17` nodes `5611-5613`) from `replication` statement-broadcast, `snapshot_isolation`, `logical_replication`/`raw`, and `Watchdog` quorum modes, with Mermaid diagram, strengths/weaknesses, verified `results/benchmark_summary.csv` baselines (`#15b`, `#1 pg-birep`), and Ch. 03b/10 footer links; `make test` (`13/13` OK) and `make lint` verified.

### ACT-110 - Fix Sysbench E_sysbench_oltp_rw Denominator in CockroachDB EN/FR Sheets (Issue `#219`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#219` (`docs/issue-219-cockroachdb-sysbench-denominator`)
- **Request / Changes / Result**: Fixed the `E_sysbench_oltp_rw` transaction denominator on line 71 of `docs/en/solutions/cockroachdb.md` and `docs/fr/solutions/cockroachdb.md` (`685` failed with `902` committed / `1,587` attempted instead of `685` of `902`, matching `results/benchmark_summary.csv`, `results/logs/cockroach.log:184-191`, and `scripts/bench_pg_lib.py:225-226`), audited all 8 M3 sheets (`citus`, `yugabytedb`, `cockroachdb`, `opentenbase_pgxl` EN/FR) confirming zero other `tx_failed` denominator conflations, and added `RCA-013` to `docs/RCA_REGISTER.md`; `make test` (`13/13` OK) and `make lint` verified.

### ACT-109 - Add French Architectural Reference Sheet for OpenTenBase / Postgres-XL (#8) (Issue `#217`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#217` (`docs/issue-217-opentenbase-pgxl-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/opentenbase_pgxl.md` mirroring the English sheet section-for-section (`#8`, `T5` Architectural Reference, 96 lines, explicitly not live-benchmarked) with French Mermaid GTM/GTM-Proxy/CN/DN 2PC diagram, lineage and distribution modes, strengths/weaknesses, verified `results/benchmark_summary.csv` anchors (`#7 citus`, `#5 yugabyte`, `#6 cockroach`, `#15a pg17-standalone`), and Ch. 03b footer links; `make test` (`13/13` OK) and `make lint` verified.

### ACT-108 - Add English Architectural Reference Sheet for OpenTenBase / Postgres-XL (#8) (Issue `#215`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#215` (`docs/issue-215-opentenbase-pgxl-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/opentenbase_pgxl.md` (`#8`, `T5` Architectural Reference, explicitly not live-benchmarked) with Mermaid GTM/GTM-Proxy/CN/DN 2PC diagram, lineage and distribution modes (Postgres-XC retired, Postgres-XL PG 10 dormant, OpenTenBase active), strengths/weaknesses, verified `results/benchmark_summary.csv` comparison anchors (`#7 citus`, `#5 yugabyte`, `#6 cockroach`, `#15a pg17-standalone`), and Ch. 03b footer links; `make test` (`13/13` OK) and `make lint` verified.

### ACT-107 - Add French Architecture Sheet for CockroachDB (#6) (Issue `#213`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#213` (`docs/issue-213-cockroachdb-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/cockroachdb.md` mirroring the English sheet section-for-section (`#6`, `T5`, `cockroach` v24.3.0 / PG-wire 13.0.0, 149 lines) with French Mermaid diagram, implementation modes, strengths/weaknesses, all 19 CSV rows (`44/87/96/685(E fail)/14/16/5` and `G` `0/5/26/64/88` retries), `F1`/`L1-L8`/`T11-T18` probes (`40001;23505;XCEXF;42601;57014`), Ch. 03b links, and Docker PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-106 - Add English Architecture Sheet for CockroachDB (#6) (Issue `#211`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#211` (`docs/issue-211-cockroachdb-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/cockroachdb.md` (`#6`, `T5`, `cockroach` v24.3.0 / PG-wire 13.0.0) with Mermaid 3-node Multi-Raft diagram, implementation modes (`SERIALIZABLE` optimistic MVCC + `40001` retries, opt-in `READ COMMITTED`, Follower Reads, Multi-Region survival, `unique_rowid()` vs `CACHE 1`), strengths/weaknesses, all 19 CSV rows (`44/87/96/685(E fail)/14/16/5` and `G` `0/5/26/64/88` retries), `F1`/`L1-L8`/`T11-T18` probes (`40001;23505;XCEXF;42601;57014`), Ch. 03b links, and Docker PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-105 - Add French Architecture Sheet for YugabyteDB (#5) (Issue `#209`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#209` (`docs/issue-209-yugabytedb-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/yugabytedb.md` mirroring the English sheet section-for-section (`#5`, `T5`, `yugabyte` 2026.1.3.0-b100 / YSQL 15.12, 146 lines) with French Mermaid diagram, implementation modes, strengths/weaknesses, all 19 CSV rows (`E3` `tx_failed=1`), `F1`/`L1-L8`/`T11-T18` probes (`40001;23505;0A000`, `T18` `next_id=101`), Ch. 03b links, and Docker PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-104 - Add English Architecture Sheet for YugabyteDB (#5) (Issue `#207`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#207` (`docs/issue-207-yugabytedb-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/yugabytedb.md` (`#5`, `T5`, `yugabyte` 2026.1.3.0-b100 / YSQL 15.12) with Mermaid 3-node Raft diagram, implementation modes (`READ COMMITTED` Wait-on-Conflict vs `RR`/`SSI`, colocation, `CACHE 100` vs `1`, xCluster, Geo-Partitioning), strengths/weaknesses, all 19 CSV rows (`E3` `tx_failed=1`), `F1`/`L1-L8`/`T11-T18` probes (`40001;23505;0A000`, `T18` `next_id=101`), Ch. 03b links, and Docker PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-103 - Add French Architecture Sheet for Citus (#7) (Issue `#205`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#205` (`docs/issue-205-citus-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/citus.md` mirroring the English sheet section-for-section (`#7`, `T5`, `citus` 14.2.0 on PG 17.10, 143 lines) with French Mermaid diagram, implementation modes, strengths/weaknesses, all 19 CSV rows, `F1`/`L1-L8`/`T11-T18` probes (`0A000;40001;08006`), Ch. 03b footer links, and Docker PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-102 - Add English Architecture Sheet for Citus (#7) (Issue `#203`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#203` (`docs/issue-203-citus-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/citus.md` (`#7`, `T5`, `citus` 14.2.0 on PG 17.10) with Mermaid coordinator/worker architecture diagram, implementation modes (Hash 1PC/2PC, Reference, Local, Citus MX, Patroni HA), strengths/weaknesses, all 19 CSV rows, `F1`/`L1-L8`/`T11-T18` probes (`0A000;40001;08006`), Ch. 03b footer links, and Docker PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-101 - Polish pgedge_spock and bucardo Technical and EN/FR Parity (Issue `#201`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#201` (`docs/issue-201-spock-bucardo-polish`)
- **Request / Changes / Result**: Clarified `ALTER TABLE` event-trigger vs native WAL `TRUNCATE` replication (line 62) and `sysbench` standalone Lua noise (`112` `E`/`192` `E3`, line 76) in `docs/{en,fr}/solutions/pgedge_spock.md`, aligned Bucardo 4 `dbgroup` wording (line 53) and French Mermaid delta-merge labels (lines 36-37) in `docs/fr/solutions/bucardo.md`, and verified `make test` (`13/13` OK) and `make lint`.

### ACT-100 - Remediate pglogical2 Reference Anchors, Alignment and Log RCA-012 (Issue `#199`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#199` (`docs/issue-199-pglogical2-remediation`)
- **Request / Changes / Result**: Remediated `docs/{en,fr}/solutions/pglogical2.md` line 94 `#16 pg17-logical` anchor (replaced unverified TPS and `T15` lag figures with verified `532.38 TPS` (`A`) and `1.68 ms` `p50` (`T15`) per `results/benchmark_summary.csv:65` and `results/extended_functional_matrix.csv:5`), updated line 58 uni-directional `pglogical.create_subscription(forward_origins='{all}')` across EN/FR, aligned `docs/fr/solutions/pglogical2.md` (`L24`, `L85`, `L92`), and recorded `RCA-012` in `docs/RCA_REGISTER.md`; `make test` (`13/13` OK) and `make lint` verified.

### ACT-099 - Add French Architectural Reference Sheet for EDB Postgres Distributed (`#4`) (Issue `#197`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#197` (`docs/issue-197-edb-pgd-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/edb_pgd.md` mirroring the English sheet section-for-section (`#4`, Architectural Reference, `APP-005` commercial exclusion) with Mermaid embedded-Raft and `pgd-proxy` diagram, all 5 consistency/routing modes, `snowflakeid`/`galloc`/`timeshard` sequences, strengths/weaknesses, and baseline comparison against `#2`, `#1`, `#5`, and `#6`; `make test` (`13/13` OK) and `make lint` verified.

### ACT-098 - Add English Architectural Reference Sheet for EDB Postgres Distributed (`#4`) (Issue `#195`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#195` (`docs/issue-195-edb-pgd-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/edb_pgd.md` covering `#4` (Architectural Reference, `APP-005` commercial exclusion) with Mermaid embedded-Raft and `pgd-proxy` diagram, all 5 consistency/routing modes (Async, `bdr.crdt_*` columns, CAMO, Eager, Write-Lead), `snowflakeid`/`galloc`/`timeshard` sequences, strengths/weaknesses, and baseline comparison against `#2`, `#1`, `#5`, and `#6`; `make test` (`13/13` OK) and `make lint` verified.

### ACT-097 - Add French Architectural Reference Sheet for pglogical 2 (`#3`) (Issue `#193`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#193` (`docs/issue-193-pglogical2-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/pglogical2.md` mirroring the English sheet section-for-section (`#3`, Architectural Reference, not live-benchmarked) with Mermaid diagram, implementation modes, strengths/weaknesses, and apples-to-apples exclusion/baseline comparison against `#16`, `#1`, and `#2`; `make test` (`13/13` OK) and `make lint` verified.

### ACT-096 - Add English Architectural Reference Sheet for pglogical 2 (`#3`) (Issue `#191`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#191` (`docs/issue-191-pglogical2-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/pglogical2.md` covering `#3` (Architectural Reference, not live-benchmarked) with Mermaid diagram, implementation modes (async, `forward_origins` mesh, sync commit, `apply_delay`, `pglogical.conflict_resolution`, `replicate_ddl_command`, `synchronize_sequence`), strengths/weaknesses, and apples-to-apples exclusion/baseline comparison against `#16`, `#1`, and `#2`; `make test` (`13/13` OK) and `make lint` verified.

### ACT-095 - Add French Architecture Sheet for Bucardo 5 (`#9`) (Issue `#189`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#189` (`docs/issue-189-bucardo-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/bucardo.md` mirroring the English sheet section-for-section (`#9`, `T4`, `bucardo`) with Mermaid architecture diagram, implementation modes, strengths/weaknesses, all 18 CSV rows, `F1`/`L1-L8`/`T11-T18` probes (`23503;23505`), Ch. 03b link, and Docker PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-094 - Add English Architecture Sheet for Bucardo 5 (`#9`) (Issue `#187`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#187` (`docs/issue-187-bucardo-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/bucardo.md` covering `#9` (`T4`, `bucardo`) with Mermaid architecture diagram, implementation modes (`source:source` vs `source:target` and conflict handlers), strengths/weaknesses, all 18 CSV rows, `F1`/`L1-L8`/`T11-T18` probes (`23503;23505`), Ch. 03b link, and Docker PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-093 - Add French Architecture Sheet for pgEdge and Spock v5 (`#2`) (Issue `#185`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#185` (`docs/issue-185-pgedge-spock-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/pgedge_spock.md` mirroring the English sheet section-for-section (`#2`, `T4`, `pgedge` LWW and `pgedge-delta-apply` CRDT) with Mermaid 3-node mesh diagram, implementation modes, strengths/weaknesses, all 19+1 CSV rows, `F1`/`L1-L8`/`T11-T18` probes (`23505;54000`), and Docker/HAProxy PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-092 - Add English Architecture Sheet for pgEdge and Spock v5 (`#2`) (Issue `#183`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#183` (`docs/issue-183-pgedge-spock-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/pgedge_spock.md` covering `#2` (`T4`, `pgedge` LWW and `pgedge-delta-apply` CRDT) with Mermaid 3-node mesh diagram, implementation modes, strengths/weaknesses, all 19 `pgedge` + `pgedge-delta-apply` CSV rows, `F1`/`L1-L8`/`T11-T18` probes (`23505;54000`), and Docker/HAProxy PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-091 - Remediate pg17_bidirectional_logical EN/FR Sheets and Log RCA-011 (Issue `#181`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#181` (`docs/issue-181-m1-r2-birep-rca011`)
- **Request / Changes / Result**: Remediated `docs/{en,fr}/solutions/pg17_bidirectional_logical.md` (`../../../README*.md` footers, L57/L58/L139 `scripts/pg_birep/setup_birep.sh`, L79 p99 latency wording) and added `RCA-011` in `docs/RCA_REGISTER.md` covering M1 footer depth, Table D script path scope, Table B Status omission, and 7-bit ASCII governance gap; `make test` (`13/13` OK) and `make lint` verified.

### ACT-090 - Remediate pg17_logical_unidirectional EN and FR Sheets (Issue `#179`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#179` (`docs/issue-179-m1-r2-logical-uni`)
- **Request / Changes / Result**: Remediated `docs/{en,fr}/solutions/pg17_logical_unidirectional.md` (`../../../README*.md` footers, FR L15 `(logique unidirectionnel)`, L18 Ch. 10 path replacing non-repo `PROJECT.md`, L53 stray `\|` removal, p99 latency wording); `make test` (`13/13` OK) and `make lint` verified.

### ACT-089 - Remediate pg17_standalone EN and FR Sheets (Issue `#177`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#177` (`docs/issue-177-m1-r2-standalone-logical`)
- **Request / Changes / Result**: Remediated `docs/{en,fr}/solutions/pg17_standalone.md` (`../../../README*.md` footers, L24 `-52.8%`/`-93.4%`/`-86.1%` baseline clarity, FR L55 `L_{\text{N0-standalone}}`, p99 latency wording, Table D setup script path); `make test` (`13/13` OK) and `make lint` verified.

### ACT-088 - Remediate PG 17 Physical Streaming and Patroni HA FR Sheet (Issue `#175`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#175` (`docs/issue-175-m1-r2-streaming-fr`)
- **Request / Changes / Result**: Remediated `docs/fr/solutions/pg17_physical_streaming_patroni.md` (`../../../README.fr.md` footer, FR labels `(standby asynchrone)`/`(standby synchrone)`/`"secours"`, `vs standalone`/`vs sync LAN` denominators, p99 disclaimer, Tableau B `Statut (Les deux)`, Tableau C `L1`/`L8` CSV parity, Tableau D paths); `make test` (`13/13` OK) and `make lint` verified.

### ACT-087 - Remediate ACTION_LOGBOOK ASCII and PG 17 Streaming/Patroni EN Sheet (Issue `#173`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#173` (`docs/issue-173-m1-r2-streaming-en-ascii`)
- **Request / Changes / Result**: Replaced all 4 `U+2013` en-dashes on `ACT-079` with ASCII `-` (100% 7-bit ASCII verified) and remediated `docs/en/solutions/pg17_physical_streaming_patroni.md` (`../../../README.md` footer, `vs standalone`/`vs sync LAN` denominators, p99 disclaimer, Table B `Status (Both)`, Table C `L1`/`L8` CSV fidelity, Table D paths); `make test` (`13/13` OK) and `make lint` verified.

### ACT-086 - Add French Architecture Sheet for PG 17 Bidirectional Logical Replication (`#1`) (Issue `#171`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#171` (`docs/issue-171-pg17-birep-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/pg17_bidirectional_logical.md` covering `#1` (`T4`, `pg-birep`) mirroring the English sheet section-for-section with Mermaid diagram, implementation modes, strengths/weaknesses, verbatim CSV benchmarks, `F1`/`L1-L8`/`T11-T18` probes, and Docker/HAProxy PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-085 - Add English Architecture Sheet for PG 17 Bidirectional Logical Replication (`#1`) (Issue `#169`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#169` (`docs/issue-169-pg17-birep-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/pg17_bidirectional_logical.md` covering `#1` (`T4`, `pg-birep`) with Mermaid diagram, implementation modes (`origin=none`, stepped sequences vs UUIDv7, `SKIP (lsn=...)` halt semantics), strengths/weaknesses, verbatim CSV benchmarks, `F1`/`L1-L8`/`T11-T18` probes, and Docker/HAProxy PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-084 - Add French Architecture Sheet for PG 17 Uni-Directional Logical Replication (`#16`) (Issue `#167`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#167` (`docs/issue-167-pg17-logical-uni-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/pg17_logical_unidirectional.md` covering `#16` (`T3`, `pg17-logical`) mirroring the English sheet section-for-section with Mermaid diagram, implementation modes, sequence non-sync trap, `#14`/`#16` disambiguation, verbatim CSV benchmarks, `F1`/`L1-L8`/`T11-T18` probes, and PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-083 - Add English Architecture Sheet for PG 17 Uni-Directional Logical Replication (`#16`) (Issue `#165`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#165` (`docs/issue-165-pg17-logical-uni-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/pg17_logical_unidirectional.md` covering `#16` (`T3`, `pg17-logical`) with Mermaid diagram, implementation modes (`pgoutput`, `FOR ALL TABLES` vs filters, `copy_data`, PG 17 failover slots, `REPLICA IDENTITY`), sequence non-sync trap, `#14`/`#16` disambiguation, verbatim CSV benchmarks, `F1`/`L1-L8`/`T11-T18` probes, and PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-082 - Add French Architecture Sheet for PG 17 Physical Streaming and Patroni HA (`#15b`) (Issue `#163`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#163` (`docs/issue-163-pg17-streaming-patroni-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/pg17_physical_streaming_patroni.md` covering `#15b` (`pg17-async-streaming`, `pg17-sync-streaming`, Patroni/etcd/HAProxy) mirroring the English sheet section-for-section with Mermaid diagram, implementation modes, strengths/weaknesses, side-by-side CSV metrics, `F1`/`L1-L8`/`T11-T18` probes, and PoC specs; `make test` (`13/13` OK) and `make lint` verified.

### ACT-081 - Add English Architecture Sheet for PG 17 Physical Streaming and Patroni HA (`#15b`) (Issue `#161`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#161` (`docs/issue-161-pg17-streaming-patroni-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/pg17_physical_streaming_patroni.md` covering `#15b` (`pg17-async-streaming`, `pg17-sync-streaming`, Patroni/etcd/HAProxy) with Mermaid diagram, implementation modes (`async`, `sync` `on`/`remote_write`/`remote_apply`/`off`/`local`, `FIRST 1`/`ANY k`), side-by-side CSV metrics, `F1`/`L1-L8`/`T11-T18` probes, and PoC specs; `make test` (`13/13` OK) and `make lint` verified.

### ACT-080 - Add French Architecture Sheet for PostgreSQL 17 Standalone (`#15a`) (Issue `#159`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#159` (`docs/issue-159-pg17-standalone-fr`)
- **Request / Changes / Result**: Created `docs/fr/solutions/pg17_standalone.md` covering `#15a` (`pg17-standalone`) mirroring the English sheet section-for-section with Mermaid diagram, implementation modes, strengths/weaknesses, verbatim CSV metrics, `F1`/`L1-L8`/`T11-T18` probes, and Docker PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-079 - Add English Architecture Sheet for PostgreSQL 17 Standalone (`#15a`) (Issue `#157`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#157` (`docs/issue-157-pg17-standalone-en`)
- **Request / Changes / Result**: Created `docs/en/solutions/pg17_standalone.md` covering `#15a` (`pg17-standalone`) with Mermaid architecture diagram, `synchronous_commit`/`wal_sync_method` implementation modes table, strengths/weaknesses, verbatim CSV benchmark metrics (`A`-`E`, `E2`-`E4`, `H`, `G_conc_c1..c32`), `F1`/`L1-L8`/`T11-T18` probes, and Docker PoC spec; `make test` (`13/13` OK) and `make lint` verified.

### ACT-078 - Dashboard Project Emblem, LightPath Support Pill & Logo Unit Tests (Issue `#155`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#155` (`feat/issue-155-dashboard-project-logo-and-tests`)
- **Request / Changes / Result**: Updated `dashboard/index.html` and `dashboard/styles.css` to render `assets/clusterpostgresql-series-icon.png` in the primary `.brand` slot and LightPath dark SVG inside an explicit `"Supported by"` / `"Soutenu par"` `.support-badge` pill + footer; added `test_project_logo_and_supporter_positioning` in `tests/test_benchmark_artifacts.py` (`13/13` tests OK, `make lint` OK, `node --check` 7/7 OK, headless Chrome visually verified).

### ACT-077 - Add Dedicated ClusterPostgreSQL-Series Project Logo & Position LightPath as Supporter (Issue `#153`)
- **Date**: `2026-11-20` | **Status**: `COMPLETED` | **Issue / Branch**: `#153` / PR `#154` (`feat/issue-153-project-logo-and-lightpath-support`)
- **Request / Changes / Result**: Generated dedicated project banner (`assets/clusterpostgresql-series-logo.png`) and square emblem (`assets/clusterpostgresql-series-icon.png`), updated `README.md` and `README.fr.md` so the project logo owns the hero banner while LightPath SVGs appear under explicit `"Supported by"` / `"Soutenu par"` sections, and logged `IMP-005` (`12/12` tests OK, `make lint` OK, `9,338` B diff).

### ACT-076 - Finalize V2 Governance Registers (`ACTION_LOGBOOK.md` & `RCA_REGISTER.md`) (Issue `#151`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#151` (`docs/issue-151-v2-governance-registers`)
- **Request / Changes / Result**: Added Phase 5 milestone, `ACT-048..076`, and `RCA-008..010`, `IMP-004`, `APP-006`, `IDEA-005`; `make test` (`12/12` OK), `make lint`, and PR diff `< 14,900` chars verified.

### ACT-075 - Align Root READMEs to Single-Source Submodule Delegation (Issue `#149`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#149` / PR `#150` (`docs/issue-149-readme-submodule-single-source-links`)
- **Request / Changes / Result**: Updated `README.md` and `README.fr.md` stack tables to point exclusively to `env/multi-db-docker-env` and `stacks/README.md` (diff `4,574` B; `0` broken links across 32 `.md` files).

### ACT-074 - Deduplicate `stacks/` Part 3: Citus, YugabyteDB, CockroachDB (Issue `#147`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#147` / PR `#148` (`refactor/issue-147-dedup-stacks-part3-citus-yb-crdb`)
- **Request / Changes / Result**: Removed duplicate `stacks/citus`, `stacks/yugabytedb`, and `stacks/cockroachdb` directories delegated to `env/multi-db-docker-env` (diff `12,349` B; `12/12` tests + `lint` OK).

### ACT-073 - Deduplicate `stacks/` Part 2: pgEdge Spock & Bucardo (Issue `#145`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#145` / PR `#146` (`refactor/issue-145-dedup-stacks-part2-pgedge-bucardo`)
- **Request / Changes / Result**: Removed duplicate `stacks/pgedge-spock` and `stacks/bucardo` directories delegated to `env/multi-db-docker-env` (diff `13,443` B; `12/12` tests + `lint` OK).

### ACT-072 - Deduplicate `stacks/` Part 1 & Add `stacks/README.md` (Issue `#143`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#143` / PR `#144` (`refactor/issue-143-dedup-stacks-part1-baseline-birep`)
- **Request / Changes / Result**: Removed duplicate `stacks/pg17-baseline` and `stacks/pg-birep` and added `stacks/README.md` single-source mapping (diff `13,139` B; `12/12` tests + `lint` OK).

### ACT-071 - Integrate `multi-db-docker-env` `v2.2.0` Git Submodule & Wire `Makefile` (Issue `#141`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#141` / PR `#142` (`feat/issue-141-submodule-makefile-integration`)
- **Request / Changes / Result**: Registered `jmrenouard/multi-db-docker-env@84acc72` (`v2.2.0`) at `env/multi-db-docker-env`, excluded `env/` from repo-local test scans, wired `Makefile` (`MDB_DIR`, `init-env`, `charts`, `dashboard`, `up/down/setup/test-%`, `test-pg-extended`, `bench-all`, 9-stack `lint`), and added submodule assertions (diff `10,621` B; `12/12` tests + `9/9` compose lint OK).

### ACT-063 to ACT-070 - Land V2 Bilingual Documentation & READMEs (Issues `#125`..`#139`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#125`/`#126` (Ch06 EN/FR, `12,476` B), `#127`/`#128` (Ch08 EN/FR, `6,997` B), `#129`/`#130` (Ch09 EN, `10,855` B), `#131`/`#132` (Ch09 FR, `10,752` B), `#133`/`#134` (Ch10 EN, `12,856` B), `#135`/`#136` (Ch10 FR, `12,796` B), `#137`/`#138` (`README.md`, `7,255` B), `#139`/`#140` (`README.fr.md`, `10,584` B)
- **Request / Changes / Result**: Landed all 10 updated/new bilingual documentation files with 10-topology empirical tables, T11-T18 limits, Log10 charts, LightPath SVG picture banners, and zero `TBD_EMPIRICAL_V2` placeholders; `make test` (`11/11` OK) and `make lint` verified on every PR.

### ACT-054 to ACT-062 - Land Chart Generator, Offline HTML Dashboard & Artifact Unit Tests (Issues `#107`..`#123`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#107`/`#108` (`generate_charts.py`, `13,863` B), `#109`/`#110` (`index.html` + `data_bench_3.js`, `8,650` B), `#111`/`#112` (`styles.css`, `10,061` B), `#113`/`#114` (`charts.js`, `13,341` B), `#115`/`#116` (`app.js`, `13,751` B), `#117`/`#118` (`data_bench.js`, `10,732` B), `#119`/`#120` (`data_matrix.js` + `data_bench_2.js`, `13,133` B), `#121`/`#122` (`build_dashboard.py` + `data_matrix_ext.js`, `13,228` B), `#123`/`#124` (`test_benchmark_artifacts.py`, `7,615` B)
- **Request / Changes / Result**: Landed complete zero-CDN offline HTML Benchmark Explorer, Log10 matplotlib chart builder, auto-sharding dashboard builder, and automated artifact validation suite (`11/11` OK, `make lint` OK).

### ACT-048 to ACT-053 - Land LightPath SVG Logos, 7 Log10 PNG Charts & V2 10-Topology CSV/Log Datasets (Issues `#95`..`#105`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#95`/`#96` (LightPath dark/light SVGs, `13,554` B), `#97`/`#98` (7 180-DPI Log10 PNG charts, `1,700` B), `#99`/`#100` (`benchmark_summary.csv` + `functional_limits_matrix.csv`, `8,980` B), `#101`/`#102` (`extended_functional_matrix.csv` + `benchmark_wan_sweep.csv`, `10,099` B), `#103`/`#104` (`benchmark_extended_workloads.csv` + `benchmark_concurrency_sweep.csv`, `10,659` B), `#105`/`#106` (`pg17-async-streaming.log` + `pg17-logical.log`, `13,902` B)
- **Request / Changes / Result**: Landed branding assets, all 7 publication Log10 PNG charts, all 4 merged benchmark CSVs (178 unique empirical rows across 10 topologies x 18 suites), both 10-topology functional matrices (`L1-L8`, `T11-T18`), and raw streaming/logical logs (`11/11` tests + `lint` OK).

### ACT-047 - Finalize Governance Registers & Phase Milestones (Issue `#93`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#93` (`docs/issue-93-finalize-governance-registers`)
- **Request / Changes / Result**: Marked Phases 2-4 `Complete` in `docs/ACTION_LOGBOOK.md` and recorded empirical `RCA-004..007`, `IMP-002..003`, `APP-003..005`, and `IDEA-003..004` in `docs/RCA_REGISTER.md`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-046 - Wire `Makefile` Pattern Targets to `stacks/` & `scripts/` (Issue `#91`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#91` (`build/issue-91-makefile-stacks`)
- **Request / Changes / Result**: Updated `Makefile` (`up-%`, `down-%`, `setup-%`, `test-%`, `stacks`); `make help`, `make stacks`, `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-045 - Land Root French `README.fr.md` (Issue `#89`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#89` (`docs/issue-89-readme-fr`)
- **Request / Changes / Result**: Added `README.fr.md`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-044 - Land French Chapter 08 Limits & Failure Modes (Issue `#87`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#87` (`docs/issue-87-fr-08-limites-defaillance`)
- **Request / Changes / Result**: Added `docs/fr/08_limites_et_modes_de_defaillance.md`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-043 - Land French Chapter 06 Empirical Benchmark Results (Issue `#85`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#85` (`docs/issue-85-fr-06-resultats-benchmarks`)
- **Request / Changes / Result**: Added `docs/fr/06_resultats_tests_et_benchmarks.md`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-042 - Land Root English `README.md` (Issue `#83`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#83` (`docs/issue-83-readme-en`)
- **Request / Changes / Result**: Added `README.md`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-041 - Land English Chapter 08 Limits & Failure Modes (Issue `#81`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#81` (`docs/issue-81-en-08-limits-failure-modes`)
- **Request / Changes / Result**: Added `docs/en/08_limits_and_failure_modes.md`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-040 - Land English Chapter 06 Empirical Benchmark Results (Issue `#79`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#79` (`docs/issue-79-en-06-benchmark-results`)
- **Request / Changes / Result**: Added `docs/en/06_empirical_test_and_benchmark_results.md`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-039 - Land `yugabyte` Benchmark Result Log (Issue `#77`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#77` (`data/issue-77-log-yugabyte`)
- **Request / Changes / Result**: Added `results/logs/yugabyte.log`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-038 - Land `bucardo` Benchmark Result Log (Issue `#75`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#75` (`data/issue-75-log-bucardo`)
- **Request / Changes / Result**: Added `results/logs/bucardo.log`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-037 - Land `pgedge` Benchmark Result Log (Issue `#73`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#73` (`data/issue-73-log-pgedge`)
- **Request / Changes / Result**: Added `results/logs/pgedge.log`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-036 - Land `cockroach` Benchmark Result Log (Issue `#71`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#71` (`data/issue-71-log-cockroach`)
- **Request / Changes / Result**: Added `results/logs/cockroach.log`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-035 - Land `pg-birep` Benchmark Result Log (Issue `#69`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#69` (`data/issue-69-log-pg-birep`)
- **Request / Changes / Result**: Added `results/logs/pg-birep.log`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-034 - Land `pg17-sync-streaming` & `citus` Result Logs (Issue `#67`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#67` (`data/issue-67-logs-sync-citus`)
- **Request / Changes / Result**: Added `results/logs/pg17-sync-streaming.log` and `results/logs/citus.log`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-033 - Land Empirical Benchmark Summary JSON Part 2 (Issue `#65`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#65` (`data/issue-65-benchmark-summary-part2`)
- **Request / Changes / Result**: Added `results/benchmark_summary_part2.json`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-032 - Land Empirical Benchmark Summary JSON Part 1 (Issue `#63`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#63` (`data/issue-63-benchmark-summary-part1`)
- **Request / Changes / Result**: Added `results/benchmark_summary_part1.json`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-031 - Land Functional Limits Matrix & `pg17-standalone` Log (Issue `#61`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#61` (`data/issue-61-limits-matrix-standalone-log`)
- **Request / Changes / Result**: Added `results/functional_limits_matrix.csv` and `results/logs/pg17-standalone.log`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-030 - Land Empirical Benchmark Summary CSV & Log Allowlist (Issue `#59`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#59` (`data/issue-59-benchmark-summary-csv`)
- **Request / Changes / Result**: Added `results/benchmark_summary.csv` and `!results/logs/*.log` in `.gitignore`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-029 - Land `yugabyte` Functional & Limits Test Script (Issue `#57`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#57` (`test/issue-57-yugabyte`)
- **Request / Changes / Result**: Added `scripts/test_yugabyte.sh`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-028 - Land `cockroach` Functional & Limits Test Script (Issue `#55`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#55` (`test/issue-55-cockroach`)
- **Request / Changes / Result**: Added `scripts/test_cockroach.sh`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-027 - Land `citus` Functional & Limits Test Script (Issue `#53`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#53` (`test/issue-53-citus`)
- **Request / Changes / Result**: Added `scripts/test_citus.sh`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-026 - Land `bucardo` Functional & Limits Test Script (Issue `#51`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#51` (`test/issue-51-bucardo`)
- **Request / Changes / Result**: Added `scripts/test_bucardo.sh`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-025 - Land `pgedge` Functional & Limits Test Script (Issue `#49`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#49` (`test/issue-49-pgedge`)
- **Request / Changes / Result**: Added `scripts/test_pgedge.sh`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-024 - Land `pg-birep` Functional & Limits Test Script (Issue `#47`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#47` (`test/issue-47-pg-birep`)
- **Request / Changes / Result**: Added `scripts/test_pg_birep.sh`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-023 - Land Remaining Cluster Setup Scripts (Issue `#45`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#45` (`feat/issue-45-scripts-cluster-setups`)
- **Request / Changes / Result**: Added `scripts/setup_{pgedge,bucardo,citus,cockroach,yugabyte}.sh`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-022 - Land Benchmark Orchestrator & Baseline/Birep Setup Scripts (Issue `#43`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#43` (`feat/issue-43-scripts-bench-runner`)
- **Request / Changes / Result**: Added `scripts/bench_pg_multimaster.sh`, `scripts/setup_pg17_baseline.sh`, and `scripts/setup_birep.sh`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-021 - Land Benchmark Runner Dockerfile & Python Helper Library (Issue `#41`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#41` (`feat/issue-41-scripts-bench-lib`)
- **Request / Changes / Result**: Added `scripts/Dockerfile.bench` and `scripts/bench_pg_lib.py`; marked Phase 4 `In Progress`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-020 - Land `citus`, `yugabytedb` & `cockroachdb` Docker Stacks (Issue `#39`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#39` (`feat/issue-39-stacks-distributed-sql`)
- **Request / Changes / Result**: Added `stacks/citus/*`, `stacks/yugabytedb/*`, and `stacks/cockroachdb/*`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-019 - Land `pgedge-spock` & `bucardo` Docker Stacks (Issue `#37`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#37` (`feat/issue-37-stacks-pgedge-bucardo`)
- **Request / Changes / Result**: Added `stacks/pgedge-spock/*` and `stacks/bucardo/*`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-018 - Land `pg17-baseline` & `pg-birep` Docker Stacks (Issue `#35`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#35` (`feat/issue-35-stacks-baseline-birep`)
- **Request / Changes / Result**: Added `stacks/pg17-baseline/*` and `stacks/pg-birep/*`; `make test` (`6/6` OK), `make lint`, and PR diff `< 15,000` chars verified.

### ACT-017 - Land French Chapter 07 Decision Framework & Production Guide (Issue `#33`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#33` (`docs/issue-33-fr-07-guide-de-choix`)
- **Request / Changes / Result**: Added `docs/fr/07_guide_de_choix_et_architecture_cible.md` (completing all 14 core `en`/`fr` chapters `01-05,07`); `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-016 - Land French Chapter 05 PoC Architectures & Test Protocol (Issue `#31`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#31` (`docs/issue-31-fr-05-architectures-poc`)
- **Request / Changes / Result**: Added `docs/fr/05_architectures_poc_et_protocole_de_test.md`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-015 - Land French Chapter 04 Feature Comparison (Issue `#29`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#29` (`docs/issue-29-fr-04-etude-comparative`)
- **Request / Changes / Result**: Added `docs/fr/04_etude_comparative_fonctionnalites.md`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-014 - Land French Chapter 03b Distributed, Trigger & Cloud Solutions (Issue `#27`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#27` (`docs/issue-27-fr-03b-catalogue-distribue`)
- **Request / Changes / Result**: Added `docs/fr/03b_catalogue_distribue_triggers_cloud.md`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-013 - Land French Chapter 03a Native & Extension Solutions (Issue `#25`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#25` (`docs/issue-25-fr-03a-catalogue-natif`)
- **Request / Changes / Result**: Added `docs/fr/03a_catalogue_natif_et_extensions.md`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-012 - Land French Chapter 02 Theoretical Foundations (Issue `#23`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#23` (`docs/issue-23-fr-02-fondements-theoriques`)
- **Request / Changes / Result**: Added `docs/fr/02_fondements_theoriques_cap_pacelc_conflits.md`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-011 - Land French Chapter 01 Executive Summary & Taxonomy (Issue `#21`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#21` (`docs/issue-21-fr-01-synthese-taxonomie`)
- **Request / Changes / Result**: Added `docs/fr/01_synthese_et_taxonomie.md`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-010 - Land English Chapter 07 Decision Framework & Production Guide (Issue `#19`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#19` (`docs/issue-19-en-07-decision-framework`)
- **Request / Changes / Result**: Added `docs/en/07_decision_framework_and_production_guide.md`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-009 - Land English Chapter 05 PoC Architectures & Test Protocol (Issue `#17`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#17` (`docs/issue-17-en-05-poc-test-protocol`)
- **Request / Changes / Result**: Added `docs/en/05_poc_architectures_and_test_protocol.md`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-008 - Land English Chapter 04 Feature Comparison (Issue `#15`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#15` (`docs/issue-15-en-04-feature-comparison`)
- **Request / Changes / Result**: Added `docs/en/04_comprehensive_feature_comparison.md`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-007 - Land English Chapter 03b Distributed, Trigger & Cloud Solutions (Issue `#13`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#13` (`docs/issue-13-en-03b-distributed-cloud`)
- **Request / Changes / Result**: Added `docs/en/03b_solutions_distributed_triggers_cloud.md`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-006 - Land English Chapter 03a Native & Extension Solutions (Issue `#11`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#11` (`docs/issue-11-en-03a-native-extensions`)
- **Request / Changes / Result**: Added `docs/en/03a_solutions_native_and_extensions.md`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-005 - Land English Chapter 02 Theoretical Foundations (Issue `#9`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#9` (`docs/issue-9-en-02-theoretical-foundations`)
- **Request / Changes / Result**: Added `docs/en/02_theoretical_foundations_cap_pacelc_conflicts.md`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-004 - Land English Chapter 01 Executive Summary & Taxonomy (Issue `#7`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#7` (`docs/issue-7-en-01-executive-summary`)
- **Request / Changes / Result**: Added `docs/en/01_executive_summary_and_taxonomy.md` and marked Phase 2 `In Progress`; `make test` (`6/6` OK) and PR diff `< 15,000` chars verified.

### ACT-003 - Add Markdown LaTeX Math Validation Suite & `make check-math` (Issue `#5`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#5` (`feat/issue-5-docs-math-syntax-tests`)
- **Request**: Add `tests/test_docs_math_syntax.py`, wire `make check-math`, and mark Phase 1 complete.
- **Changes**: Created `tests/test_docs_math_syntax.py`, added `check-math` target to `Makefile`, updated Phase 1 status to `Complete` and logged `IDEA-002`.
- **Result**: `python3 -m unittest discover -s tests -v` (`6/6` OK) and `make check-math`/`make test` passed in WSL2 Ubuntu-24.04; PR diff under 15,000 chars.

### ACT-002 - Add Makefile Orchestrator & Governance/Security Tests (Issue `#3`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#3` (`feat/issue-3-makefile-ci-and-tests`)
- **Request**: Deliver `Makefile` lifecycle/check targets and governance/secret-hygiene/shell-safety unit tests under `< 15,000` diff characters.
- **Changes**: Added `Makefile` and `tests/test_governance_and_security.py`; logged `RCA-002`, `RCA-003` (GitHub OAuth token lacks `workflow` scope for `.github/workflows/ci.yml`), and `APP-002`.
- **Result**: `python3 -m unittest discover -s tests -v` (`4/4` OK) and `make help`/`test`/`check-security`/`lint`/`bench-all`/`clean` passed in WSL2 Ubuntu-24.04; PR diff under 15,000 chars.

### ACT-001 - Bootstrap Repository Governance, Registers & Environment Template (Issue `#1`)
- **Date**: `2026-11-19` | **Status**: `COMPLETED` | **Issue / Branch**: `#1` (`feat/issue-1-governance-and-test-harness`)
- **Request**: Initialize `jmrenouard/ClusterPostgreSQL-Series` governance framework, `.env.example`, and living registers under the `< 15,000`-char PR limit.
- **Changes**: Committed baseline (`LICENSE`, `.gitignore`, `.gitattributes`) on `main`; added `.env.example`, `AGENTS.md`, `.agents/AGENTS.md`, `.agents/rules/*.md`, `docs/ACTION_LOGBOOK.md`, and `docs/RCA_REGISTER.md` (splitting Makefile/CI/tests into follow-up Issue `#2` to honor `< 15,000` diff limit).
- **Result**: Verified locally against governance and math validation checks (`6/6` tests pass); PR diff strictly under 15,000 characters.

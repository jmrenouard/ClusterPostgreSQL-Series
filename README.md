# ClusterPostgreSQL-Series — PostgreSQL Multi-Master & Active-Active Architectures

**Author:** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr) | **License:** [MIT](LICENSE) | **Version française :** [README.fr.md](README.fr.md)

A rigorous engineering study, 36-criterion comparative matrix, reproducible Docker Compose labs, empirical failure-mode catalog, and standardized `pgbench` / `sysbench` benchmarks across **15 PostgreSQL multi-master, sharded, and high-availability architectures** spanning **7 architectural families**.

---

## Executive Summary

PostgreSQL is built on a **single-writer WAL engine** (`LSN`, `XID`, `ProcArray`, local heap pages). Turning PostgreSQL into an "active-active multi-master" system forces an unavoidable trade-off along the **PACELC** spectrum:

- **Asynchronous Logical & Trigger Meshes (`PA/EL`):** Commit locally at sub-15 ms latency even under `50 ms` WAN RTT (`647–824 TPS`), yet lose updates (`-71K` to `-531K` drift in 50-key contention tests) or stall on `SQLSTATE 23505` unless configured with **CRDT Delta-Apply** (`spock.delta_apply` achieved `1,837.64 TPS` with **`0` drift**).
- **Distributed Consensus Raft/Paxos (`PC/EC`):** Guarantee `RPO = 0` and zero lost updates (`0` drift), while paying cross-node RTT penalties (`-76%` to `-97%` TPS drop under simulated `25 ms` one-way WAN delay) and requiring application-level `SQLSTATE 40001` retry loops (`sysbench` failed `685` of `1,587` total attempts on CockroachDB without retries).
- **Single-Primary HA Control (`#15 Patroni + etcd`):** Remains the lowest-TCO, zero-conflict optimal choice for 80%+ of OLTP workloads.

---

## Empirical Benchmark & Limits Headline Matrix (`PG_SCALE = 2`)

Executed sequentially inside isolated Docker bridge networks on a 20-vCPU / 16.4 GiB host (`results/benchmark_summary.csv`, `results/functional_limits_matrix.csv`):

| Topology (Solution #) | Suite A Single RW (TPS) | Suite B2 Overlap RW (TPS) | Suite D Hot Conflict TPS (`Drift`) | Suite E `sysbench` TPS (`Failed`) | Suite F WAN `25ms` TPS | Verified SQLSTATE Limits |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`pg17-standalone` (#15)** | `866.82` | `879.01` | `3,128.63` (`0`) | `1,129.51` (`112`) | N/A | `23505` (Single writer) |
| **`pg17-sync-streaming` (#15)** | `409.48` | `465.22` | `1,370.10` (`0`) | `819.36` (`118`) | **`57.00`** (`-86%`) | `23505; 25006` |
| **`pg-birep` (#1 Native)** | `875.91` | `1,228.60` | `1,231.15` (**`-71,063`**) | `1,105.32` (`96`) | **`824.04`** (`-6%`) | `23505` halt; `55000` keyless |
| **`pgedge` (#2 Spock LWW)** | `556.06` | `818.65` | `2,280.11` (**`-278,698`**) | `888.56` (`114`) | **`646.77`** (`0%`) | `23505` transdiscard; LWW loss |
| **`pgedge-delta-apply` (#2 CRDT)** | — | — | **`1,837.64` (`0` drift)** | — | — | Zero drift on delta columns |
| **`bucardo` (#9 Trigger)** | `735.38` | `1,267.77` | `1,378.79` (**`-531,620`**) | `1,232.84` (`112`) | **`763.23`** (`0%`) | PK req; `23505` sync stall |
| **`citus` (#7 Sharded 2PC)** | `309.04` | `312.98` | `1,691.45` (`0`) | `189.44` (`9`) | **`21.67`** (`-93%`) | `0A000` non-dist `UNIQUE`; `40001` |
| **`yugabyte` (#5 DocDB Raft)** | `173.64` | `170.19` | `832.65` (`0`) | `128.24` (`0`) | **`5.78`** (`-97%`) | `40001` (`RR`); `0A000` `LISTEN`; `2/3` halt |
| **`cockroach` (#6 Pebble Raft)** | `42.08` | `74.17` | `471.61` (`0`) | `44.84` (**`685`**) | **`10.06`** (`-76%`) | `40001`; `XCEXF`; `42601`; `57014` (`2/3`) |

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

---

## Reproducible Lab Stacks & `Makefile` Quickstart

Self-contained PoC stacks live in `stacks/` alongside automated verification scripts in `scripts/` and raw datasets in `results/`:

| Stack Directory | Topology | Primary Images |
| :--- | :--- | :--- |
| `stacks/pg17-baseline/` | PG 17 Standalone & Sync Streaming HA | `postgres:17` |
| `stacks/pg-birep/` | PG 17 Bidirectional (`origin=none`) + HAProxy | `postgres:17`, `haproxy:2.9-alpine` |
| `stacks/pgedge-spock/` | 3-Node pgEdge Spock `5.0.14` + Snowflake + HAProxy | `ghcr.io/pgedge/pgedge-postgres:17-spock5-minimal` |
| `stacks/bucardo/` | 2-Node PG 17 (`plperl`) + Bucardo `5.6.0` Daemon | Custom `postgres:17` + `debian:trixie-slim` |
| `stacks/citus/` | Citus `14.2.0` (1 Coordinator + 2 Workers) | `citusdata/citus:14.2.0-pg17` |
| `stacks/yugabytedb/` | 3-Node YugabyteDB RF=3 YSQL + DocDB | `yugabytedb/yugabyte:2026.1.3.0-b100` |
| `stacks/cockroachdb/` | 3-Node CockroachDB RF=3 Multi-Raft | `cockroachdb/cockroach:v24.3.0` |

### Common Commands

```bash
# Inspect all Makefile targets
make help

# Run governance, secret-hygiene, LaTeX math, shell syntax, and Compose lint checks
make test
make lint

# Run the sequential benchmark harness across topologies (requires Docker + env)
cp .env.example .env
make bench-all
```

---

## Governance, Security & Honest Scope

- **Living Registers:** Every engineering decision, bug RCA, dead-end, and simplification is tracked in [`docs/ACTION_LOGBOOK.md`](docs/ACTION_LOGBOOK.md) and [`docs/RCA_REGISTER.md`](docs/RCA_REGISTER.md).
- **Credential Hygiene:** Repository files contain zero real passwords or host paths; lab containers read ephemeral defaults from [`.env.example`](.env.example).
- **Threats to Validity:** Local Docker benchmarks share one 20-vCPU / 16.4 GiB NVMe host; WAN effects were modeled via `tc netem` egress delay (`25 ms`), not independent intercontinental failure domains (see [Chapter 05](docs/en/05_poc_architectures_and_test_protocol.md)).

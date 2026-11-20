# Docker PoC Stacks — Delegated to `env/multi-db-docker-env`

All operational Docker Compose topologies, cluster initialization scripts, functional/limits suites (`L1`–`L8` and `T11`–`T18`), and V1/V2 benchmark harnesses are maintained in a **single source of truth**: the [`jmrenouard/multi-db-docker-env`](https://github.com/jmrenouard/multi-db-docker-env) Git submodule mounted at [`../env/multi-db-docker-env`](../env/multi-db-docker-env).

Duplicate compose and setup copies previously kept under `stacks/<topology>/` have been removed to eliminate drift (`IMP-004`).

## Quick Start

```bash
# 1. Initialize the multi-db-docker-env Git submodule
make init-env

# 2. List all 12 PostgreSQL compose stacks (covering all 15 benchmarked topologies)
make stacks

# 3. Start, initialize, test, and tear down any topology via Makefile
make up-pgedge && make setup-pgedge && make test-pgedge && make down-pgedge
```

## Topology Mapping (`env/multi-db-docker-env`)

| `Makefile` Target | Compose File (`env/multi-db-docker-env/`) | Topologies Covered |
| :--- | :--- | :--- |
| `pg17-baseline` | `docker-compose-pg17-baseline.yml` | `pg17-standalone`, `pg17-sync-streaming` |
| `pg-streaming` | `docker-compose-pg-streaming.yml` | `pg17-async-streaming` |
| `pg-logical` | `docker-compose-pg-logical.yml` | `pg17-logical` |
| `pg-birep` | `docker-compose-pg-birep.yml` | `pg-birep` |
| `pgedge` | `docker-compose-pgedge.yml` | `pgedge` (Spock 5.0.14) |
| `bucardo` | `docker-compose-bucardo.yml` | `bucardo` (5.6.0) |
| `citus` | `docker-compose-citus.yml` | `citus` (14.2.0) |
| `yugabyte` | `docker-compose-yugabyte.yml` | `yugabyte` (2026.1.3.0 RF=3) |
| `cockroach` | `docker-compose-cockroach.yml` | `cockroach` (v24.3.0 RF=3) |
| `pg18-streaming` | `docker-compose-pg18-streaming.yml` | `pg18-standalone`, `pg18-async-streaming`, `pg18-sync-streaming` (PG 18.6) |
| `pg18-logical` | `docker-compose-pg18-logical.yml` | `pg18-logical` (PG 18.6) |
| `pg18-birep` | `docker-compose-pg18-birep.yml` | `pg18-birep` (PG 18.6 `origin=none` + `uuidv7()`) |

# Docker PoC Stacks — Delegated to `env/multi-db-docker-env`

The [`jmrenouard/multi-db-docker-env`](https://github.com/jmrenouard/multi-db-docker-env) Git submodule at [`../env/multi-db-docker-env`](../env/multi-db-docker-env) maintains all Compose topologies, initialization scripts, and test suites. It covers 18 active topologies across 13 Compose stacks (plus V1/V2 `pgedge-delta-apply`).

We removed duplicate compose and setup copies from `stacks/<topology>/` to eliminate drift (`IMP-004`).

## Quick Start

```bash
# 1. Initialize the multi-db-docker-env Git submodule
make init-env

# 2. List all 13 PostgreSQL Compose stacks (covering 18 active topologies)
make stacks

# 3. Start, initialize, test, and tear down any topology via Makefile
make up-pgedge && make setup-pgedge && make test-pgedge && make down-pgedge

# 4. Build the shared benchmark client image and run benchmarks (V1/V2, PG 18.6, YT, V5 Scale=20)
make build-bench-image
make bench-all && make bench-pg18 && make bench-yt-cluster && make bench-optimized
```

## Topology Mapping (`env/multi-db-docker-env`)

| `Makefile` Target | Compose File (`env/multi-db-docker-env/`) | Topologies Covered |
| :--- | :--- | :--- |
| `pg17-baseline` | `docker-compose-pg17-baseline.yml` | `pg17-standalone`, `pg17-sync-streaming` |
| `pg-streaming` | `docker-compose-pg-streaming.yml` | `pg17-async-streaming` |
| `pg-logical` | `docker-compose-pg-logical.yml` | `pg17-logical` |
| `pg-birep` | `docker-compose-pg-birep.yml` | `pg-birep` |
| `pgedge` | `docker-compose-pgedge.yml` | `pgedge` (Spock 5.0.14; V1/V2 `pgedge-delta-apply`) |
| `bucardo` | `docker-compose-bucardo.yml` | `bucardo` (5.6.0) |
| `citus` | `docker-compose-citus.yml` | `citus` (14.2.0) |
| `yugabyte` | `docker-compose-yugabyte.yml` | `yugabyte` (2026.1.3.0 RF=3 + HAProxy `:15470`) |
| `cockroach` | `docker-compose-cockroach.yml` | `cockroach` (`v25.4` RF=3 + HAProxy `:15480`), `cockroach-rc` (V1/V2 baseline: `v24.3.0`) |
| `pg18-streaming` | `docker-compose-pg18-streaming.yml` | `pg18-standalone`, `pg18-async-streaming`, `pg18-sync-streaming` (PG 18.6) |
| `pg18-logical` | `docker-compose-pg18-logical.yml` | `pg18-logical` (PG 18.6) |
| `pg18-birep` | `docker-compose-pg18-birep.yml` | `pg18-birep` (PG 18.6 `origin=none` + `uuidv7()`) |
| `yt-cluster` | `docker-compose-yt-cluster.yml` | `yt-cluster` (`cc=half`), `yt-cluster-async` (`cc=0`, YT Cluster `1.21.3`) |

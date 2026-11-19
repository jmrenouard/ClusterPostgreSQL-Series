# RCA Register - Errors, Dead-Ends, Approximations & Roadmap Ideas

> **Governance Rule ([`AGENTS.md`](../AGENTS.md) & [`.agents/rules/project-governance.md`](../.agents/rules/project-governance.md))**:
> Update all four sections in English on **every request, every change, and every result**.

## 1. Errors & Bugs Encountered (`RCA-XXX`)

### RCA-001 - Empty Repository Rejects Initial Pull Request Targeting `main`
- **Date / Action**: `2026-11-19` (`ACT-001`)
- **Observed Symptom**: Opening a PR from a feature branch against `main` fails on GitHub when `main` has zero commits.
- **Root Cause Analysis**: GitHub requires at least one existing commit on the base branch (`main`) before a Pull Request diff can be computed.
- **Applied Change / Fix**: Committed the minimal baseline (`LICENSE`, `.gitignore`, `.gitattributes`) on `main` prior to opening Issue `#1` and branching `feat/issue-1-governance-and-test-harness`.
- **Result & Non-Regression Test**: Branching, PR creation, and merge workflow succeed cleanly.

### RCA-002 - Transient `Permission denied` on `make clean` over WSL2 9p Mount
- **Date / Action**: `2026-11-19` (`ACT-002`)
- **Symptom**: `rm -rf tests/__pycache__` failed immediately after `python3 -m unittest`.
- **Root Cause**: Host file indexer briefly locks `.pyc` directories on WSL2 9p mounts.
- **Fix**: Exported `PYTHONDONTWRITEBYTECODE := 1` and used `shutil.rmtree(..., ignore_errors=True)` in `Makefile` `clean`.
- **Result**: `make test` + `make clean` succeed cleanly without residue.

### RCA-003 - GitHub Push Rejected for `.github/workflows/ci.yml` Without `workflow` Scope
- **Date / Action**: `2026-11-19` (`ACT-002`)
- **Symptom**: `git push` failed with `refusing to allow an OAuth App to create or update workflow .github/workflows/ci.yml without workflow scope`.
- **Root Cause**: The active `gh` OAuth token holds `gist, read:org, repo, user` scopes only and lacks the `workflow` scope required by GitHub to push workflow YAML files.
- **Fix / Mitigation**: Excluded `.github/workflows/ci.yml` from PR so `Makefile` and test harness land cleanly on `main`; documented CI workflow addition as pending maintainer `workflow` scope authorization.
- **Result**: Remaining files push and merge cleanly; local `make lint` and `make test` run identically to CI.

### RCA-004 - `pgedge` Spock Output Plugin `SQLSTATE 42501` & Localhost Binding
- **Date / Action**: `2026-11-19` (`ACT-019` / `ACT-025`)
- **Symptom**: Initial pgEdge 3-node mesh failed subscription startup with `SQLSTATE 42501` on `spock_output` while containers bound only `localhost` and failed cross-node replication auth.
- **Root Cause**: `ghcr.io/pgedge/pgedge-postgres:17-spock5-minimal` defaults to `output_plugin_libraries='pgoutput, test_decoding'`, `listen_addresses=localhost`, and `logging_collector=on`.
- **Fix**: Overrode container command flags (`-c listen_addresses=* -c logging_collector=off -c output_plugin_libraries=pgoutput,spock_output`) and added `host replication all all scram-sha-256` to `pg_hba.conf`.
- **Result**: 3-node Spock `5.0.14` mesh converged (`2/2` replicating per node, `0` drift under `spock.delta_apply`).

### RCA-005 - Stock `postgres:17` Missing `plperl` & `DBI` for Bucardo `db_getconn`
- **Date / Action**: `2026-11-19` (`ACT-019` / `ACT-026`)
- **Symptom**: `bucardo install` and multi-master sync setup failed when targeting stock `postgres:17`.
- **Root Cause**: `bucardo.schema` defines `db_getconn()` in `plperlu` using Perl `DBI`/`DBD::Pg`, which are omitted from the standard `postgres:17` image.
- **Fix**: Built `stacks/bucardo/Dockerfile.pg` (`postgres:17` + `postgresql-plperl-17`, `libdbi-perl`, `libdbd-pg-perl`) paired with `stacks/bucardo/Dockerfile` (`debian:trixie-slim` + `bucardo` `5.6.0-4`).
- **Result**: `sync_mm` (`db1:source db2:source`) initialized cleanly (`plperlu=1`, `delta_triggers=5/5`).

### RCA-006 - Keyless `pgbench_history` Triggers `55000` / Rejection / `0A000` Across Engines
- **Date / Action**: `2026-11-19` (`ACT-021` / `ACT-031`)
- **Symptom**: Standard `pgbench -i` creates `pgbench_history` without a primary key, causing `SQLSTATE 55000` on `pg-birep` updates, silent skipping (`default_insert_only`) on `pgedge`, `validate_sync` failure on `bucardo`, and `SQLSTATE 0A000` on Citus post-distribution `ADD PRIMARY KEY`.
- **Root Cause**: Logical decoding, trigger-delta queues, and distributed hash-sharding require replica identity or upfront primary/distribution keys.
- **Fix**: Standardized `pgbench_history` with an explicit upfront surrogate PK (`hid BIGSERIAL PRIMARY KEY` or `DEFAULT unique_rowid()` on CockroachDB) before workload execution and documented the `55000`/`0A000` limits in `results/functional_limits_matrix.csv`.
- **Result**: All 8 benchmarked topologies executed Suites A-F without keyless-table breakage.

### RCA-007 - Distributed Consensus `40001` Retries, `XCEXF`, and `2/3` Raft Quorum Halt
- **Date / Action**: `2026-11-19` (`ACT-028` / `ACT-029`)
- **Symptom**: Concurrent same-row updates triggered `SQLSTATE 40001` (`WriteTooOldError` on CockroachDB, `RR` conflict on YugabyteDB) and `sysbench` logged `685` ignored errors on CockroachDB (`XCEXF` on default `TEMP TABLE` and `42601` on `LISTEN`); killing 2/3 nodes halted both clusters (`57014`/timeout) while `yugabyted` initially reported `rf=0` before full 3-node join.
- **Root Cause**: Serializable/Snapshot Raft consensus aborts conflicting writes optimistically (`40001`), forbids writes without majority (`< 2/3`), and omits async session features (`LISTEN/NOTIFY` disabled `0A000` on YugabyteDB).
- **Fix**: Added RF=3 readiness wait + memory caps in `stacks/yugabytedb/`, verified `40001` application retry convergence (`bal=1100`), and recorded all raw SQLSTATEs honestly.
- **Result**: `10/10` functional/limit probes passed across `citus`, `cockroach`, and `yugabyte`.

## 2. Technical Dead-Ends & Abandoned Leads (`IMP-XXX`)

### IMP-001 - Monolithic Bootstrap Pull Request Exceeding 15,000 Characters
- **Date / Action**: `2026-11-19` (`ACT-001`)
- **Rejected Approach**: Bundling governance rules, living registers, `Makefile`, GitHub CI, and Python test suites in a single PR (~27.5K diff chars).
- **Reason**: Exceeded the 15,000-character PR diff limit. Split cleanly into PR `#1` (governance + `.env.example` + registers) and PR `#2` (`Makefile` + CI + test suites).

### IMP-002 - Monolithic Benchmark JSON & Uncompacted 19 MB Retry Logs
- **Date / Action**: `2026-11-19` (`ACT-032` / `ACT-036`)
- **Rejected Approach**: Committing a single 28 KB `benchmark_summary.json` and raw `cockroach.log` (19 MB / 142,831 repeated `40001` retry lines).
- **Reason**: Violated the `< 15,000`-char PR diff cap and bloated repository history. Split JSON into `benchmark_summary_part1.json` + `benchmark_summary_part2.json` and summarized `cockroach.log` (`8,015` bytes) preserving exact metrics and representative retry lines.

### IMP-003 - Host-NAT Benchmark Execution & Uncapped Multi-Node Consensus Containers
- **Date / Action**: `2026-11-19` (`ACT-021`)
- **Rejected Approach**: Running `pgbench`/`sysbench` over WSL2/Windows localhost port-forwarding or running multiple multi-node clusters simultaneously without memory caps inside 16.4 GiB RAM.
- **Reason**: Host NAT skews RTT and concurrent clusters risk OOM kills. Replaced with sequential one-stack-at-a-time execution using `multi-db-pgbench-sysbench:latest` inside each stack's isolated Docker bridge network.

## 3. Current Approximations & Simplifying Assumptions (`APP-XXX`)

### APP-001 - Ephemeral Local Laboratory Credentials
- **Date / Action**: `2026-11-19` (`ACT-001`)
- **Assumption**: `.env.example` provides `PG_LAB_PASSWORD=pg_poc_ephemeral` for isolated local Docker Compose labs.
- **Impact & Removal Condition**: Strictly prohibited outside ephemeral containers; production deployments must inject externally managed credentials at runtime.

### APP-002 - Conditional Compose & Shell Linting Prior to PoC Modules
- **Date / Action**: `2026-11-19` (`ACT-002`)
- **Assumption**: `Makefile` `lint` and `.github/workflows/ci.yml` pass safely when zero `*.sh` or `docker-compose-*.yml` files exist during Phase 1 bootstrap.
- **Impact & Removal Condition**: Every future PoC PR adding `.sh` or `docker-compose-*.yml` files is automatically validated on addition.

### APP-003 - Single-Host WSL2 Docker & `tc netem 25ms` WAN Approximation
- **Date / Action**: `2026-11-19` (`ACT-021`)
- **Assumption**: All benchmarks share one 20-vCPU / 16.4 GiB NVMe WSL2 host (`Suite F` injects `25 ms` egress delay via `tc netem` on bridge containers).
- **Impact & Removal Condition**: Captures Raft/sync RTT amplification accurately in relative terms but omits independent physical AZ disk contention, NIC jitter, and cross-datacenter packet loss; removable via multi-host cloud VM benchmarks.

### APP-004 - Uniform `PG_SCALE = 2` Dataset With Surrogate History PK
- **Date / Action**: `2026-11-19` (`ACT-021`)
- **Assumption**: All 8 topologies run `PG_SCALE = 2` (`200,000` `pgbench_accounts` rows) with an added surrogate PK on `pgbench_history`.
- **Impact & Removal Condition**: Keeps dataset working set within container RAM limits for apples-to-apples comparisons; larger disk-bound I/O profiles require higher `PG_SCALE`.

### APP-005 - Commercial & Cloud-Managed Engines Assessed by Architecture Only
- **Date / Action**: `2026-11-19` (`ACT-006` / `ACT-007`)
- **Assumption**: EDB Postgres Distributed (PGD/BDR), AWS Aurora Limitless, and Google Cloud Spanner/AlloyDB are covered in theoretical/feature chapters without live Docker PoCs.
- **Impact & Removal Condition**: Reflects licensing and managed-cloud boundaries rather than omission; benchmark comparison tables explicitly mark non-tested commercial/cloud offerings.

## 4. Unimplemented Ideas & Future Roadmap (`IDEA-XXX`)

### IDEA-001 - Automated Cross-Topology `pgbench` & `sysbench` Matrix
- **Date / Action**: `2026-11-19` (`ACT-001`)
- **Proposal**: Implemented via `scripts/bench_pg_multimaster.sh` and `make bench-all`; extend in future iterations with `PG_SCALE=50+` I/O-bound sweeps.

### IDEA-002 - GitHub Actions CI Workflow Enablement Pending `workflow` OAuth Scope
- **Date / Action**: `2026-11-19` (`ACT-003`)
- **Proposal**: Add `.github/workflows/ci.yml` executing `python3 -m unittest discover -s tests -v`, `bash -n`, and `docker compose config` once the maintainer grants the GitHub `workflow` OAuth scope (`RCA-003`).

### IDEA-003 - Multi-Host Cloud Multi-Region Benchmark & PITR Soak Suite
- **Date / Action**: `2026-11-19` (`ACT-047`)
- **Proposal**: Re-run Suites A-F across 3 real cloud regions (`eu-west`, `us-east`, `ap-south`) alongside automated `pgBackRest` PITR and sustained failback soak tests to validate `APP-003` and `APP-004`.

### IDEA-004 - Retry-Aware Distributed SQL `sysbench` Driver & Delta-Apply Torture Suite
- **Date / Action**: `2026-11-19` (`ACT-047`)
- **Proposal**: Add an exponential-backoff `SQLSTATE 40001` retry wrapper for `sysbench` on CockroachDB/YugabyteDB and expand `spock.delta_apply` testing to multi-column composite counters.

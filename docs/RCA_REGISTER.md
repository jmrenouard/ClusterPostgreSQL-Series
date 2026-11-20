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

### RCA-008 - `pgedge` `SQL_ASCII` Encoding Rejects Non-ASCII `chr()` With `SQLSTATE 54000`
- **Date / Action**: `2026-11-19` (`ACT-051` / `ACT-064`)
- **Symptom**: During the `T14` rich-data fidelity probe, `chr()` calls for multi-byte UTF-8 codepoints failed on `pgedge` with `SQLSTATE 54000` (`requested character too large for encoding`).
- **Root Cause**: `ghcr.io/pgedge/pgedge-postgres:17-spock5-minimal` initializes default databases with `SQL_ASCII` encoding rather than `UTF8`.
- **Fix / Mitigation**: Verified raw UTF-8 byte-stream preservation across all 3 Spock nodes (`md5=f798eb5a` identical on 3/3 nodes) while explicitly preserving `SQLSTATE 54000` in `results/extended_functional_matrix.csv` and Chapter 08; production deployments must enforce `initdb -E UTF8`.
- **Result**: Documented transparently across `results/extended_functional_matrix.csv`, dashboard matrix tab, and EN/FR Chapter 08.

### RCA-009 - Native Logical Replication Sequence Non-Sync Causes Post-Failover `SQLSTATE 23505`
- **Date / Action**: `2026-11-19` (`ACT-051` / `ACT-067`)
- **Symptom**: In `T18` (`sequence_sync_after_50`), promoting or writing to the peer node after 50 `SERIAL` inserts on node 1 immediately failed with `SQLSTATE 23505` (`duplicate key value violates unique constraint`) across `pg17-logical`, `pg-birep`, `pgedge` (without Snowflake), and `bucardo`.
- **Root Cause**: PostgreSQL 17 logical decoding does not replicate sequence state changes (`last_value` stayed stuck at `1|false` on subscribers/peers), whereas physical WAL streaming (`pg17-async-streaming`, `pg17-sync-streaming`) replicated exact WAL sequence state (`66|true`) and Raft engines (`yugabyte`, `cockroach`) advanced global sequences cleanly.
- **Fix / Mitigation**: Documented the mandatory operational workarounds (Snowflake/UUIDv7 keys, disjoint `INCREMENT`/`START` strides, or `setval()` failover runbook) in Chapters 08 and 10 and recorded `23505` verbatim in `results/extended_functional_matrix.csv`.
- **Result**: Verified deterministically across all 10 topologies (`T18` matrix and Chapter 10).

### RCA-010 - `pg-birep` `FOR ALL TABLES` Sysbench Schema Propagation Catch-Up
- **Date / Action**: `2026-11-19` (`ACT-052` / `ACT-071`)
- **Symptom**: Running V2 Sysbench suites (`E2`-`E4`) dynamically created `sbtest1` on `pg_birep_node1` without automatic replication to `pg_birep_node2` under `FOR ALL TABLES`.
- **Root Cause**: PostgreSQL 17 logical replication does not propagate DDL (`CREATE TABLE`), and existing subscriptions only discover newly created `FOR ALL TABLES` relations after `ALTER SUBSCRIPTION ... REFRESH PUBLICATION` once matching DDL exists on the peer.
- **Fix**: Updated the V2 benchmark harness in `env/multi-db-docker-env` (`scripts/bench_pg_v2_lib.py`) to create symmetric Sysbench DDL on both nodes and refresh subscriptions with `copy_data = false` before workload execution.
- **Result**: All V2 Sysbench suites (`E2_sysbench_oltp_ro`, `E3_sysbench_oltp_wo`, `E4_sysbench_point_select`) converged cleanly across both `pg-birep` nodes.

### RCA-011 - M1 Solution Sheet Depth Links, PoC Script Paths, Table B Status & ASCII Governance Gap
- **Date / Action**: `2026-11-20` (`ACT-087`..`ACT-091`)
- **Symptom**: Forensic audit and Iteration 2 checks on the initial 8 `docs/{en,fr}/solutions/pg17_*.md` sheets found: (1) all 8 `[Index](../../README*.md)` links resolved to missing `docs/README*.md`; (2) `docs/ACTION_LOGBOOK.md` line 55 (`ACT-079`) held 4 non-ASCII `U+2013` en-dashes undetected by `ACCENTS` regex; (3) Table D cited bare/parent-repo script paths under `env/multi-db-docker-env/` headings; (4) `pg17_physical_streaming_patroni` omitted Table B `Status (Both)` and abbreviated `L1`/`L8`, while `pg17_standalone` L24 mixed standalone (`-93.4%`) and sync LAN (`-86.1%`) denominators.
- **Root Cause**: Solution sheets live 3 levels below repo root (`docs/{en,fr}/solutions/`), `test_governance_and_security.py` checked only French accented characters rather than `ord(c) > 127`, and Table D paths mixed submodule (`scripts/pg_*/`) and parent-repo (`scripts/`) locations.
- **Fix**: Remediated all 8 M1 sheets across atomic `< 15,000` B PRs (`#174`, `#176`, `#178`, `#180`, `#182`), fixing `../../../README*.md` footers, exact submodule script paths, Table B `Status` and Table C `L1`/`L8` CSV parity, denominator/p99 wording, and 100% 7-bit ASCII governance registers.
- **Result**: `0` broken relative links across all 8 sheets, `0` missing PoC paths, `0` non-ASCII lines in `ACTION_LOGBOOK.md` and `RCA_REGISTER.md`, and `make test` (`13/13` OK) + `make lint` passing on `main`.

### RCA-012 - Unverified `#16 pg17-logical` Reference Anchor in `pglogical2` EN/FR Sheets
- **Date / Action**: `2026-11-20` (`ACT-096`, `ACT-097`, `ACT-100`)
- **Symptom**: M2 Verification Wave (`auditor_m2_1`, `reviewer_m2_1`, `reviewer_m2_2`, `challenger_m2_1`) detected unverified inflated `A_single_rw` TPS and underestimated `T15` lag figures for `#16 pg17-logical` on line 94 of `docs/{en,fr}/solutions/pglogical2.md`, conflicting with `results/benchmark_summary.csv:65` (`532.38` TPS), `results/extended_functional_matrix.csv:5` (`p50=1.68ms`), and `docs/{en,fr}/solutions/pg17_logical_unidirectional.md`.
- **Root Cause**: The comparison-table anchor for `#16 pg17-logical` was written without programmatic verification against `results/benchmark_summary.csv` and `results/extended_functional_matrix.csv`, and the erroneous values were propagated from EN (`PR #192`) into FR (`PR #194`).
- **Fix**: Replaced the erroneous `#16 pg17-logical` anchor values on line 94 of `docs/{en,fr}/solutions/pglogical2.md` with verified `532.38 TPS` (`A`) and `1.68 ms` (`T15`) under `Issue #199` alongside `forward_origins='{all}'` (`L58`) and FR prose alignment (`L24`, `L85`, `L92`). Non-regression rule: cross-check every comparison-table baseline number programmatically against `results/*.csv` before opening any documentation PR.
- **Result**: `0` unverified anchor metrics across `pglogical2` EN/FR sheets, 100% `results/*.csv` parity, 7-bit ASCII compliance (`ord(c) <= 127`) in governance registers, and `make test` (`13/13` OK) + `make lint` passing on `main`.

### RCA-013 - Sysbench `tx_committed` vs. `tx_failed` Denominator Conflation in `cockroachdb.md`
- **Date / Action**: `2026-11-20` (`ACT-110`, Issue `#219`)
- **Symptom**: M3 adversarial verification (`teamwork_challenger_m3_1`) reproduced an arithmetic misstatement on line 71 of `docs/en/solutions/cockroachdb.md` (`685 of 902`) and `docs/fr/solutions/cockroachdb.md` (equivalent `685 / 902`), which implied a `75.9%` abort rate instead of the true `43.2%` (`685 / 1,587`).
- **Root Cause**: In `scripts/bench_pg_lib.py:225-226` and `results/logs/cockroach.log:184-191`, `sysbench` `transactions` (`902`) records committed transactions (`tx_committed`) separately from `ignored errors` (`685`, captured as `tx_failed`), so total attempted transactions equal `tx_committed + tx_failed = 902 + 685 = 1,587`.
- **Fix**: Updated line 71 in both `docs/en/solutions/cockroachdb.md` (`685` failed with `902` committed / `1,587` attempted) and `docs/fr/solutions/cockroachdb.md` (matching French wording for `685` failed, `902` committed / `1 587` attempted), and audited all 8 M3 sheets (`citus`, `yugabytedb`, `cockroachdb`, `opentenbase_pgxl` EN/FR) confirming no other sheet conflates `tx_committed` with total attempted transactions.
- **Result**: Exact parity restored with `results/benchmark_summary.csv` and `results/logs/cockroach.log:184-191`, 149-line EN/FR parity preserved, 7-bit ASCII compliance (`ord(c) <= 127`) verified in governance registers, and `make test` (`13/13` OK) + `make lint` passing.

### RCA-014 - M5 Catalog ID #14/#16 Collision, 03a EDB PGD Drift, and Stale Ch. 01 Status Remediation
- **Date / Action**: `2026-11-20` (`ACT-121`..`ACT-128`, Issues `#241`, `#245`, `#247`, `#253`, `#255`)
- **Symptom**: Pre-M5 repository audit detected: (1) `#14` vs `#16` Catalog ID collision tagging `pg17-logical` as `#14` in `README.md:32`, `README.fr.md:22`, and `docs/en/06_empirical_test_and_benchmark_results.md:26` while `#14` was assigned to Legacy Trigger Systems (`Slony-I / Londiste / RubyRep`); (2) `docs/en/03a_solutions_native_and_extensions.md:91,95` omitting `#16` and referencing non-existent `lww_element` / reversed `bdr.global_sequences` order; and (3) stale `Pending` / `phase empirique suivante` markers and unlinked `02`-`10` references in `01` EN/FR.
- **Root Cause**: Chapter 10 introduced `pg17-logical` (`#16`) after early `results/functional_limits_matrix.csv` (`#14 Baseline`) and Chapter 01/03a/06 texts were authored, and `03a` pre-dated the `edb_pgd.md` sheet audit.
- **Fix**: Reassigned all `pg17-logical` documentation references to `#16` with explicit disambiguation footnotes preserving read-only `results/functional_limits_matrix.csv`, added `#16` subsections and harmonized `bdr.crdt_*` / `bdr.conflict_history` / `bdr.global_sequences` in `03a` EN/FR, updated `01` EN/FR status and links, and added 17-row Solutions Catalog tables to `README.md` / `README.fr.md` (verified `pg17_standalone.md:147` already uses `Logique`).
- **Result**: Zero broken relative links across all 59 Markdown files, zero `#14`/`#16` adjacency collisions, 100% 7-bit ASCII governance registers, and `make test` (`13/13` OK) + `make lint` passing.

### RCA-015 - Ch. 06 Suite E Denominator Contradiction, Cross-Chapter Precision Drift, and Tier 5 E2E Blind Spots
- **Date / Action**: `2026-11-20` (`ACT-133`..`ACT-136`, Issues `#265`, `#267`+)
- **Observed Symptom**: M6 Tier 5 adversarial review (`teamwork_challenger_m6_t5_1`, `teamwork_challenger_m6_t5_2`) found: (1) `docs/en/06_empirical_test_and_benchmark_results.md:82-84` reported Suite E `tx_failed` against `tx_committed` (`9 (of 3,797)`, `685 (of 902)`) instead of total attempted transactions (`committed + failed` = `3,806` and `1,587`), contradicting `results/logs/cockroach.log:184-186`, `README.md:18`, `cockroachdb.md:71`, and `06` line 88 (`43.2%` abort exposure); (2) minor cross-chapter drift (`#15a` `T1`/`N1` vs `T0`/`N0`, `snowflake.node` `1..1024` vs `1..1023`, FR `03b` OpenTenBase `PG 10/14` vs `PG 10-11`, and `pgedge_spock.md:133` omitting `BYTEA=65536B;`); and (3) E2E test blind spots (`test_solution_sheets.py` accepting `flowchart XX`, space-separated quotes, and `ma OR mb`, `test_solution_sheets_parity.py` covering only 1 of 4 benchmark CSVs without row-scoping or README 4-column catalog/headline checks, and `Makefile:75` failing on hyphenated `make test-solution-sheets`).
- **Root Cause Analysis**: Chapter 06 Suite E table copied `tx_committed` denominators before `RCA-013` fixed `cockroachdb.md`, early chapter drafts predated sheet verification, and Tiers 1-4 E2E tests targeted core summary parity within `< 14 KB` per file without an adversarial Tier 5 module.
- **Applied Change / Fix**: Aligned Suite E denominators (`3,806` / `2,574` / `1,587`) in EN/FR Chapter 06, harmonized `03a`/`03b`/`pgedge_spock.md` EN/FR details (`ACT-133`), logged `RCA-015` (`ACT-134`), hardened `test_solution_sheets.py`, `test_solution_sheets_parity.py`, and `Makefile:75` (`ACT-135`), and added `tests/test_solution_sheets_tier5.py` covering README 4-column catalogs, headline parity, all 4 benchmark CSVs row-by-row, matrix metrics, and EN/FR table parity (`ACT-136`).
- **Result & Non-Regression Test**: `0` denominator contradictions, `0` cross-chapter/sheet precision drifts, `100%` of injected Tier 5 failure probes caught with `0` false positives, and `make test && make lint` passing on `main`.

### RCA-016 - PostgreSQL 18 Official Docker Image `PGDATA` Path & `VOLUME` Layout Change
- **Date / Action**: `2026-11-20` (`ACT-138`, `ACT-141`)
- **Observed Symptom**: Existing PostgreSQL 17 Docker Compose volume mounts targeting `/var/lib/postgresql/data` fail to persist or initialize cleanly under `postgres:18` (`18.6`).
- **Root Cause Analysis**: Upstream `docker-library/postgres` changed `postgres:18` defaults to `PGDATA=/var/lib/postgresql/18/docker` with parent `VOLUME /var/lib/postgresql` to support major-version `pg_upgrade` side-by-side directories.
- **Applied Change / Fix**: Mounted named volumes at `/var/lib/postgresql` and aligned `PGDATA` expectations across the 3 new PG 18.6 Compose stacks (`pg18-streaming`, `pg18-logical`, `pg18-birep`) in `env/multi-db-docker-env` `v2.3.0` (`8ea028b7`) and documented the breaking change in Chapter 12.
- **Result & Non-Regression Test**: All 5 PostgreSQL 18.6 topologies initialize, crash-recover (`T16` `RPO=0`), and pass `make lint` across all 12 Compose stacks.

### RCA-017 - PostgreSQL 18 `io_method=io_uring` Fails With `EPERM` Under Default Docker Seccomp
- **Date / Action**: `2026-11-20` (`ACT-138`, `ACT-140`)
- **Observed Symptom**: Starting `postgres:18` with `-c io_method=io_uring` aborts immediately with `EPERM` inside standard unprivileged Docker containers.
- **Root Cause Analysis**: Docker's default seccomp profile blocks `io_uring_setup` syscalls for container security isolation, whereas PostgreSQL 18's default `io_method=worker` (`io_workers=3`) uses standard POSIX workers.
- **Applied Change / Fix**: Standardized the PG 18.6 PoC stacks on default `io_method=worker`, executed controlled A/B probes (`worker` cut cold sequential scan latency `-18.5%` from `1,018.3 ms` to `829.4 ms`, while small `fsync` RW ran `290.75` vs `323.98 TPS` with `data_checksums=on`), and recorded `io_uring=EPERM` verbatim in `results/functional_limits_pg18.csv` and Chapter 12.
- **Result & Non-Regression Test**: Deterministic AIO behavior verified across all 5 PG 18.6 topologies without requiring privileged containers.

### RCA-018 - PostgreSQL 18.6 `FOR ALL SEQUENCES` / `REFRESH SEQUENCES` Rejected (`SQLSTATE 42601`)
- **Date / Action**: `2026-11-20` (`ACT-138`, `ACT-140`)
- **Observed Symptom**: Executing `CREATE PUBLICATION ... FOR ALL SEQUENCES` or `ALTER SUBSCRIPTION ... REFRESH SEQUENCES` on PostgreSQL 18.6 fails with `SQLSTATE 42601` (`syntax error`), and `T18` subscriber sequences stay at `1|false` causing post-failover `SQLSTATE 23505`.
- **Root Cause Analysis**: Native logical sequence synchronization was deferred from PostgreSQL 18 to PostgreSQL 19, leaving `SERIAL` non-sync unchanged from PG 17 (`RCA-009`), while PostgreSQL 18 added native RFC 9562 `uuidv7()` and the 7th conflict counter `confl_multiple_unique_conflicts`.
- **Applied Change / Fix**: Recorded `SQLSTATE 42601` verbatim in `results/functional_limits_pg18.csv` and Chapter 12, and verified native `uuidv7()` active-active convergence on `pg18-birep` (`50/50` dual-node inserts, `0x 23505`, `H_append_only_insert = 2,066.70 TPS`, `3.30x` vs PG 17).
- **Result & Non-Regression Test**: Honest PG 18.6 capability boundary verified across `pg18-logical` and `pg18-birep` and asserted by `tests/test_benchmark_artifacts.py`.

### RCA-019 - Canonical GitHub Repository Redirects, True Watchers & Tag-Only Release Fallback
- **Date / Action**: `2026-11-20` (`ACT-137`, `ACT-140`)
- **Observed Symptom**: Naive GitHub REST queries misreported SymmetricDS via redirected slug `JumpMind/symmetric-ds`, omitted `GoogleCloudPlatform/pgadapter`, duplicated star counts via `watchers_count`, and returned HTTP 404 on `/releases/latest` for tag-only projects (`postgres/postgres`, `pgEdge/spock`, `cockroachdb/cockroach`, `pgpool/pgpool2`).
- **Root Cause Analysis**: GitHub's REST `watchers_count` aliases `stargazers_count` (true watchers live in `subscribers_count`), organization renames redirect canonical slugs, and mature C/Go repositories publish Git tags without GitHub Release objects.
- **Applied Change / Fix**: Implemented `scripts/collect_popularity.py` to target canonical `jumpmindinc/symmetric-ds` and `GoogleCloudPlatform/pgadapter` (marked client-proxy only), read `subscribers_count`, compute exact commit/contributor counts via `per_page=1` `Link: rel="last"` pagination without cloning, and fall back to GraphQL `TAG_COMMIT_DATE DESC`.
- **Result & Non-Regression Test**: Verified 21 catalog rows (`18` public repos + `3` proprietary/managed engines) in `results/project_popularity.csv` and `tests/test_benchmark_artifacts.py`.

### RCA-020 - WSL2 `/tmp` `tmpfs` Auto-Shutdown Wipe During Multi-PR Staging
- **Date / Action**: `2026-11-20` (`ACT-139`, `ACT-140`)
- **Observed Symptom**: Staging modified tracked files into WSL2 `/tmp/cps_v3_stage/` before `git checkout -- .` lost the staged copies when the WSL2 VM briefly idled and restarted between host commands.
- **Root Cause Analysis**: WSL2 mounts `/tmp` as volatile RAM-backed `tmpfs`, which is purged automatically whenever the WSL2 distribution shuts down on idle timeout.
- **Applied Change / Fix**: Relocated staging buffers strictly to persistent host scratch storage outside the repository, verified 100% byte-for-byte parity on all recovered Wave 3 dashboard and documentation files, and normalized LF line endings prior to every atomic commit.
- **Result & Non-Regression Test**: All 24 atomic Wave 3 PRs landed cleanly with exact verified file sizes, `node --check` passing on all 11 JS bundles, and `make test` (`20/20` OK).

### RCA-021 - YT Cluster `1.21.3` Default `cc=half` Synchronous 2PC vs Async `cc=0` Behavior
- **Date / Action**: `2026-11-20` (`ACT-143`, `ACT-146`)
- **Observed Symptom**: Default YT Cluster `1.21.3` (PostgreSQL `18.7` + `yt_cluster 1.21` / `ytserv`) write transactions exhibited quorum synchronous 2PC latency and cross-node commit coordination overhead (`A_single_rw = 20.63 TPS`, `p95 = 1,330.433 ms`, `B2_overlap_rw = 10.69 TPS`, `F_wan_netem_25ms = 2.25 TPS`, `p95 = 5,557.313 ms`), contrasting with async mode (`cc=nodes>=0`, `yt-cluster-async`, `A_single_rw = 41.45 TPS`, `B2_overlap_rw = 55.03 TPS`, `D_hot_conflict = 163.01 TPS`, `F_wan_netem_25ms = 4.78 TPS`) while read-only local queries reached `C_multinode_ro = 48,787.74 TPS` and `E4_sysbench_point_select = 165,472.75 TPS`.
- **Root Cause Analysis**: YT Cluster defaults `def_cluster_commit` to `{"at_least":0,"mode":1}` (`half` synchronous 2PC across `ytserv` nodes with `sequential_consistency=0`), enforcing zero-drift multi-master consistency (`0` drift across all suites, emitting `55409` / `40001` conflict retries) at the cost of write-path 2PC RTT amplification, whereas explicit `cc=nodes>=0` switches to asynchronous commit dispatch.
- **Applied Change / Fix**: Benchmarked and documented both modes side-by-side (`yt-cluster` sync `cc=half` and `yt-cluster-async` `cc=0`, `22` rows total) in `results/benchmark_yt_cluster.csv`, `dashboard/data_bench_yt.js`, and `docs/{en,fr}/solutions/yt_cluster_lite.md`.
- **Result & Non-Regression Test**: Both modes verified end-to-end with `0` balance drift in `results/benchmark_yt_cluster.csv` and enforced by `tests/test_benchmark_artifacts.py` and `tests/test_solution_sheets_parity.py`.

### RCA-022 - YT Cluster `SAVEPOINT` Rollback Rejection (`SQLSTATE 0A000`) & `min_cluster_size=2` Halt (`SQLSTATE 57P03`)
- **Date / Action**: `2026-11-20` (`ACT-143`, `ACT-146`)
- **Observed Symptom**: Executing `SAVEPOINT` rollback failed with `SQLSTATE 0A000` (`rows=0`), and stopping 2 of 3 cluster nodes blocked client writes with `SQLSTATE 57P03` (`yt_synchronize: Network: YT-E1852`) under `min_cluster_size=2` (while single-node SIGKILL also briefly returned `57P03` during the 8 s party failover window before recovering `20/20` with `RPO=0`).
- **Root Cause Analysis**: YT Cluster's distributed 2PC coordinator does not support subtransaction savepoint rollback across coordinated PostgreSQL nodes, and quorum safety blocks writes once active nodes drop below `min_cluster_size=2` to prevent split-brain divergence.
- **Applied Change / Fix**: Recorded `0A000`, `40001`, `55409`, and `57P03` verbatim in `results/functional_limits_yt_cluster.csv`, `results/logs/yt-cluster-benchmark.log`, and `docs/{en,fr}/solutions/yt_cluster_lite.md`, and asserted all four SQLSTATEs in `tests/test_solution_sheets_parity.py`.
- **Result & Non-Regression Test**: All four SQLSTATE boundaries are reproducibly tested and verified in `make test` (`20/20` OK).

### RCA-023 - Stale `.s.YT.5432.pid` Lock File Triggers `YT-E1104` on Unclean Container Restart
- **Date / Action**: `2026-11-20` (`ACT-143`, `ACT-147`)
- **Observed Symptom**: Restarting a SIGKILL-terminated `ytserv` container failed startup with `YT-E1104` on PID reuse due to a lingering `.s.YT.5432.pid` lock file.
- **Root Cause Analysis**: Unclean container termination skips graceful `ytserv` shutdown hooks, leaving `.s.YT.5432.pid` on the persisted socket/data path and preventing `ytserv` from binding cleanly on container restart.
- **Applied Change / Fix**: Added deterministic stale PID cleanup during container startup in `env/multi-db-docker-env` `v2.4.0` (`e130508f89bf9c9c61cad3f7aa8d9299e4bcca93`, `docker-compose-yt-cluster.yml`) and documented the `YT-E1104` risk in `results/functional_limits_yt_cluster.csv` and `docs/{en,fr}/solutions/yt_cluster_lite.md`.
- **Result & Non-Regression Test**: Verified clean crash-recovery (`T16`, `20/20`, `RPO=0`) and deterministic `make lint` validation across all 13 submodule Compose stacks.

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

### IMP-004 - Duplicated Standalone `stacks/` Compose & Script Copies
- **Date / Action**: `2026-11-19` (`ACT-071`..`ACT-075`)
- **Rejected Approach**: Maintaining mirrored Docker Compose stacks and setup scripts inside `ClusterPostgreSQL-Series/stacks/<topology>/` alongside `jmrenouard/multi-db-docker-env`.
- **Reason**: Dual maintenance caused configuration drift and omitted newer V2 topologies (`pg-streaming`, `pg-logical`, `T11-T18`, `bench_pg_v2_runner.sh`). Replaced with a real Git submodule (`env/multi-db-docker-env` pinned to `v2.2.0` commit `84acc72`), delegated `Makefile` targets (`MDB_DIR`, `init-env`, `up/down/setup/test-%`, `bench-all`, 9-stack `lint`), and a single-source-of-truth `stacks/README.md`.

### IMP-005 - Using Corporate Supporter Logo in the Series Primary Hero Slot
- **Date / Action**: `2026-11-20` (`ACT-077`, Issue `#153`)
- **Rejected Approach**: Placing the LightPath corporate SVG logo alone in the top hero banner of `README.md`, `README.fr.md`, and the `.brand` slot of `dashboard/index.html`.
- **Reason**: Conflated project identity with corporate sponsorship. Generated dedicated `ClusterPostgreSQL-Series` project branding (`assets/clusterpostgresql-series-logo.png` and `assets/clusterpostgresql-series-icon.png`) for primary headers, and repositioned LightPath SVG logos explicitly as `"Supported by"` / `"Soutenu par"` support branding.

### IMP-006 - Monolithic Wave 3 Chart, Dashboard & Cross-Chapter PRs Exceeding `< 14 KB` / `< 15 KB` Caps
- **Date / Action**: `2026-11-20` (`ACT-138`..`ACT-141`)
- **Rejected Approach**: Appending Charts 08-10 into `scripts/generate_charts.py`, embedding Popularity UI into `dashboard/app.js`, or committing full `dashboard/index.html` (`21.6 KB` unified diff), `dashboard/app.js` (`17.6 KB` diff), EN+FR cross-chapters (`17.2 KB` diff), and both root READMEs (`17.7 KB` diff) in single PRs.
- **Reason**: Violated both the `< 14,000`-byte per-file test cap and the `< 15,000`-byte PR diff cap. Split into modular `scripts/generate_charts_v3.py`, `dashboard/popularity.js`, dedicated `< 13.5 KB` JS data bundles (`data_bench_pg18.js`, `data_matrix_pg18.js`, `data_popularity.js`), and 24 sequential atomic PRs all strictly `< 14,000` bytes.

### IMP-007 - Monolithic Wave 4 `generate_charts_v3.py` (`15.3 KB`) & Chapter 11 (`14.9 KB`) Diffs
- **Date / Action**: `2026-11-20` (`ACT-144`, `ACT-146`)
- **Rejected Approach**: Landing all Wave 4 `scripts/generate_charts_v3.py` edits (`15,328` B unified diff) or full Chapter 11 EN/FR rewrites (`14,746` B / `14,904` B) in single PRs, or staging new solution sheets without intermediate test synchronization.
- **Reason**: Exceeded or breached the strict `< 14,800`-byte PR diff cap and would break strict `len(SLUGS)` assertions mid-wave. Split `generate_charts_v3.py` into typography compaction (`7,301` B) + 19-repo Charts 08-09 (`8,909` B), split EN/FR Chapter 11 into matrix (`~9.9 KB`) + insights (`~5.2 KB`), and maintained `20/20` OK on every single Wave 4 PR.

### IMP-008 - Copying Partial Wave-4 Section 6 Layout or Uncompacted M1 Sheets Exceeding `14,000` B / `15,000`-Char Caps
- **Date / Action**: `2026-11-20` (`ACT-149`)
- **Rejected Approach**: Reusing the abbreviated 2-bullet Section 6 table from Wave 4 (`pg18_native_clustering.md`, `yt_cluster_lite.md` omitting `open_issues`/full `pushed_at` ISO) or appending full Section 6 onto `pg17_physical_streaming_patroni.md` (`12,955`/`13,205` B) and `pgedge_spock.md` (`12,973`/`13,158` B) without prose compaction.
- **Reason**: Omitting `open_issues`/`watchers`/`SPDX`/full `pushed_at` violates R1 verbatim telemetry coverage, and uncompacted sheets exceed the `14,000`-byte per-file test ceiling (`14.3-14.9` KB). Standardized on the full 8-column / 3-bullet Section 6 schema with surgical prose compaction preserving every CSV/probe number.

### IMP-009 - Combined `citus` + `cockroachdb` M2 PR 3 Exceeding `14,000` B / `15,000`-Char Caps
- **Date / Action**: `2026-11-20` (`ACT-155`)
- **Rejected Approach**: Appending Section 6 onto uncompacted `citus.md` (`12,848`/`12,859` B) and `fr/cockroachdb.md` (`12,684` B) or bundling all 4 `citus` + `cockroachdb` sheets in one PR (`~16.2K-18.0K` unified diff chars).
- **Reason**: Uncompacted `citus.md` approaches `14,000` B (`13,957` B FR) and the 4-sheet diff breaches the `< 15,000`-char cap. Split into PR 3a (`citus` EN+FR with 4-line non-numeric prose compaction) and PR 3b (`cockroachdb` EN+FR with 3-line FR compaction).

### IMP-010 - Combined 3-Slug M3 Batches Approaching the `15,000`-Char PR Diff Ceiling
- **Date / Action**: `2026-11-20` (`ACT-158`..`ACT-161`)
- **Rejected Approach**: Bundling all 6 sheets of M3 PR 5 (`bucardo`, `pglogical2`, `opentenbase_pgxl`) or M3 PR 6 (`symmetricds`, `pgpool_ii`, `edb_pgd`) plus governance register updates into single 3-slug PRs (`~13,952-15,100` unified diff chars).
- **Reason**: Exceeded the advisory `~13,500`-char split threshold and risked breaching the hard `< 15,000`-char PR diff cap (`AGENTS.md`). Split M3 into sequential 2+1 slug atomic PRs (PR 5a, PR 5b, PR 6a, PR 6b), keeping every PR diff well under `11,000` chars while preserving `en_shape == fr_shape`.

### IMP-011 - Bundling 4-Repo `legacy_triggers` and Both Wave-4 R1 Alignments in One M4 PR 8
- **Date / Action**: `2026-11-20` (`ACT-163`..`ACT-165`)
- **Rejected Approach**: Combining `legacy_triggers` (4-row Section 6 + `#16` scrub), `pg18_native_clustering`, and `yt_cluster_lite` EN/FR updates into a single PR 8 (`~22,000` unified diff chars) or a 2-PR split putting both Wave-4 alignments in one PR (`~13,800-14,200` chars).
- **Reason**: Breached the `< 15,000`-char PR diff cap (`AGENTS.md`) or exceeded the `~13,500`-char split threshold. Split M4 PR 8 into three sequential 1-slug atomic PRs (PR 8a, PR 8b, PR 8c), keeping each diff under `10,500` chars while preserving `en_shape == fr_shape`.

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

### APP-006 - Single-Host V2 Concurrency (`c=1..32`) & Multi-Point `tc netem` (`10/25/50ms`) Sweeps
- **Date / Action**: `2026-11-19` (`ACT-051`..`ACT-052`)
- **Assumption**: V2 concurrency sweeps (`c=1, 4, 8, 16, 32`) and 3-point WAN sweeps (`10ms`, `25ms`, `50ms` egress `tc netem`) run sequentially on one Docker host (`20` vCPU / `16.4` GiB NVMe).
- **Impact & Removal Condition**: Accurately exposes relative scaling knees, Raft/sync RTT amplification, and async decoupling across 10 topologies, while remaining bounded by shared host I/O; removable via multi-region bare-metal/cloud clusters.

### APP-007 - Point-in-Time GitHub Popularity Snapshot & Shared-Host PG 18.6 AIO Benchmarks
- **Date / Action**: `2026-11-20` (`ACT-137`, `ACT-138`)
- **Assumption**: `results/project_popularity.csv` captures live GitHub REST/GraphQL telemetry at `2026-11-20T13:34:55Z` (mirror repos `postgres/postgres` and `pgpool/pgpool2` report trusted committer counts rather than total mailing-list authors), and PG 18.6 benchmarks (`results/benchmark_pg18.csv`) run sequentially on one local WSL2 Docker host under `io_method=worker`.
- **Impact & Removal Condition**: Enables reproducible apples-to-apples PG 18.6 vs PG 17.11 comparisons and transparent maintenance vitality tracking; refreshable anytime via `make popularity` and `make bench-pg18`.

### APP-008 - YT Cluster Licensing Split (MIT Leaf Core vs Closed `ytserv`) & Vendor Self-Run Jepsen Scope
- **Date / Action**: `2026-11-20` (`ACT-143`, `ACT-146`)
- **Assumption**: `results/project_popularity.csv` tracks the public MIT-licensed `DBinvent/yt-cluster-lite` Rust leaf repository (`15` stars, `21` commits, `2` contributors), while the benchmarked `ytserv` cluster server binary (`1.21.3`) is closed/dual-licensed; additionally, published Jepsen consistency claims come from DBinvent's own self-run test suite targeting `cursor-stability` rather than an independent third-party serializability audit.
- **Impact & Removal Condition**: Documented explicitly across `docs/{en,fr}/solutions/yt_cluster_lite.md` and Chapters `03a`/`04`/`07`/`11` so production evaluators distinguish MIT leaf telemetry from closed server licensing and verify isolation guarantees independently; removable if `ytserv` is open-sourced and independently Jepsen-audited.

### APP-009 - GitHub Mirror Issue/Tag Artifacts (`2026-11-20T17:26:02Z`) & `< 14 KB` Sheet Compaction Ceiling
- **Date / Action**: `2026-11-20` (`ACT-149`)
- **Assumption**: `results/project_popularity.csv` (`2026-11-20T17:26:02Z`, `22` rows) reports `open_issues=0`, `contributors=58` (trusted committers), and next-major tag `REL_19_0` on the `postgres/postgres` GitHub mirror (canonical issue tracking lives on `pgsql-bugs`), while `pgEdge/spock` reports `v6.0.0-beta.2` alongside stable `5.0.14` tested in the PoC; additionally, tight sheets (`pg17_physical_streaming_patroni`, `pgedge_spock`) near `13 KB` require prose compaction in Sections 1-5/Table D to fit Section 6 under the `14,000`-byte cap (`tests/test_solution_sheets.py:200`).
- **Impact & Removal Condition**: Preserves 100% verbatim CSV-to-Markdown telemetry parity and zero benchmark metric loss without loosening test density bounds; mirror caveats and `v5.0.14` PoC alignment are stated inline, and telemetry refreshes via `make popularity`.

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

### IDEA-005 - Automated GitHub Pages Publishing & PostgreSQL 18+ Native Sequence Sync Study
- **Date / Action**: `2026-11-19` (`ACT-076`)
- **Proposal**: Publish `dashboard/index.html` and `assets/charts/` automatically via GitHub Pages once `workflow` OAuth scope is granted (`RCA-003`), and benchmark PostgreSQL 18/19 native logical sequence synchronization against `RCA-009`.

### IDEA-006 - PostgreSQL 19 Native Sequence Sync & Bare-Metal `io_uring` AIO Benchmark Follow-Up
- **Date / Action**: `2026-11-20` (`ACT-142`)
- **Proposal**: Re-evaluate `FOR ALL SEQUENCES` / `REFRESH SEQUENCES` (`RCA-018`) on PostgreSQL 19 once released and benchmark `io_method=io_uring` vs `worker` vs `sync` (`RCA-017`) on bare-metal Linux NVMe outside Docker's default seccomp sandbox.

### IDEA-007 - Independent Jepsen Fault-Injection & Multi-Region WAN Audit for YT Cluster 1.21+
- **Date / Action**: `2026-11-20` (`ACT-148`)
- **Proposal**: Run an independent multi-host Jepsen-style nemesis suite (network partitions, clock skew, asymmetric packet loss) against YT Cluster `1.21+` under `cc=half` and `cc=0` beyond vendor self-run `cursor-stability` tests (`APP-008`), and re-test `SAVEPOINT` (`RCA-022`) if supported in future releases.

### IDEA-008 - Automated `make popularity` Markdown Sync & Drift Guard Across All 38 Solution Sheets
- **Date / Action**: `2026-11-20` (`ACT-154`)
- **Proposal**: Add a deterministic `scripts/sync_popularity_sheets.py` helper (wired to `make popularity`) to refresh Section 6 telemetry rows across all 38 `docs/{en,fr}/solutions/*.md` sheets directly from `results/project_popularity.csv` whenever the live GitHub snapshot is regenerated.

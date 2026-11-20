# 08 — Empirical Limits and Failure Modes Catalog

**Series:** PostgreSQL Multi-Master & Active-Active Architectures  
**Author:** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr)  
**License:** MIT License

---

This chapter documents every **hard failure mode, `SQLSTATE` exception, and silent data corruption vector** reproduced empirically in our Docker test harness (`results/functional_limits_matrix.csv` and `results/logs/`). Every code cited below was directly observed against running clusters.

## 1. Summary of Observed `SQLSTATE` & Runtime Failures

| Code / Signal | Triggering Topologies | Observed Context | Operational Severity |
| :--- | :--- | :--- | :--- |
| **`23505`** | `pg-birep`, `pgedge`, `bucardo`, `yugabyte`, `cockroach` | Uncoordinated `SERIAL` PK or concurrent `UNIQUE(email)` insert | **Fatal Apply Stall** (`pg-birep`, `bucardo`) or Silent Drop (`pgedge`) |
| **`55000`** | `pg-birep` (and native `pgoutput`) | `UPDATE`/`DELETE` on keyless table (`pgbench_history`) without `RI FULL` | **Blocking DDL/DML Error** |
| **`0A000`** | `citus`, `yugabyte` | Citus `UNIQUE`/PK omitting dist key or `vector`; Yugabyte `LISTEN/NOTIFY` | **Unsupported Feature Reject** |
| **`40001`** | `cockroach`, `yugabyte` (`RR`), `citus` (`RR`) | Concurrent row update / serialization conflict | **Requires App Retry Loop** |
| **`XCEXF`** | `cockroach` | `CREATE TEMP TABLE` with default settings (`experimental_enable_temp_tables=off`) | **Session Error** |
| **`42601`** | `cockroach` | `LISTEN` / `NOTIFY` syntax unsupported in Go PG-wire parser | **Unsupported Feature** |
| **`57014`** | `cockroach` (`2/3` down) | Statement timeout during Raft majority loss (`PC/EC` cluster halt) | **Total Write/Read Outage** |
| **`42501`** | `pgedge` (container quirk) | Default `output_plugin_libraries` lacked `spock_output` permission | **Setup Blocker Fixed via Conf** |
| **`25006`** | `pg17-async/sync-streaming` | Write, `DELETE`, or `TEMP TABLE` attempted on hot standby | **Read-Only Standby Guard** |
| **`23503`** | `bucardo` (`T13` FK race) | Immediate child `INSERT` on Node 2 before async parent sync (`0/10`) | **Cross-Node FK Violation** |
| **`54000` / `08006`** | `pgedge` (`T14`), `citus` (`T16`) | `pgedge` image `SQL_ASCII` `chr(20013)` (`54000`); `citus` worker2 `SIGKILL` (`08006`) | **Encoding / Worker Drop** |

---

## 2. Detailed Anatomy of the 8 Empirical Limits (`L1–L8`)

### L1 — Keyless Tables (`pgbench_history` Without Primary Key)

- **`pg-birep` (`#1`):** `INSERT` replicated, but `UPDATE` and `DELETE` failed immediately on the publisher with **`SQLSTATE 55000`**: `cannot update table "pgbench_history_nokey" because it does not have a replica identity and publishes updates`.
- **`pgedge` (`#2`):** Spock silently mapped the keyless table into the **`default_insert_only`** replication set. Local `UPDATE` (`delta=50`) and `DELETE` succeeded on `node1` (`UPDATE 1`), while peers silently kept stale values!
- **`bucardo` (`#9`):** `validate_sync` refused initialization outright: `ERROR: Table "public.pgbench_history_nokey" must specify a primary key!`.
- **`citus` (`#7`):** Allowed table creation, yet blocked `ALTER TABLE ... ADD PRIMARY KEY` / `SERIAL` after `create_distributed_table()` with **`SQLSTATE 0A000`**. Creating `PRIMARY KEY(aid, hid)` upfront unlocked full operations.
- **`yugabyte` (`#5`) & `cockroach` (`#6`):** Both succeeded transparently via internal hidden keys (`rowid` auto-injected in CockroachDB `SHOW COLUMNS`).
- **Mitigation:** Enforce explicit Primary Keys (or composite `(shard_key, id)` for Citus) across 100% of tables via CI migration checks.

### L2 — Uncoordinated `SERIAL` Primary Key Collisions

- **`pg-birep` (`#1`):** Independent `SERIAL` sequences generated `id = 1` on both nodes. Replication crashed on **`SQLSTATE 23505`** (`duplicate key value violates unique constraint "uncoord_serial_pkey"`, `apply_error_count = 1`), blocking all subsequent transactions in that subscription queue.
- **`pgedge` (`#2`) & `bucardo` (`#9`):** Neither halted—instead, both **silently overwrote** `node1`'s legitimate row (`from_n1` destroyed, `from_n2` retained; `spock.resolutions = 1`, `bucardo Conflicts = 1`).
- **`citus` (`#7`), `yugabyte` (`#5`), `cockroach` (`#6`):** Zero collisions (`Citus` `1.62 ms` single coord seq; `Yugabyte` `1.89 ms` cache=1 / `1.98 ms` cache=100; `Cockroach` `unique_rowid()` `17.72 ms` vs Raft-serialized `SERIAL cache=1` `46.07 ms`).
- **Mitigation:** Mandate `snowflake` IDs, stepped `INCREMENT BY N` offsets, `unique_rowid()`, or UUIDv7 globally.

### L3 — Non-Commutative Lost Updates (`balance = balance + delta`)

- **Async LWW Failure:** Under competing updates (`+100` and `-30` from `1000.00`, expected `1070.00`), `pg-birep` diverged (`node1 = 970.00`, `node2 = 1100.00`), while `pgedge` LWW and `bucardo_latest` converged to **`970.00`** (silently destroying `+100`). In Suite D (`50` hot accounts), drift exploded to **`-71,063`** (`pg-birep`), **`-278,698`** (`pgedge`), and **`-531,620`** (`bucardo`).
- **`spock.delta_apply` Fix (`#2`):** Configuring `log_old_value=true, delta_apply_function=spock.delta_apply` converged all 3 nodes to exact `1070.00` (functional test) and **`0` drift** across `27,545` hot-row commits in Suite D (`1,837.64 TPS`).
- **Consensus Retry (`#5`, `#6`, `#7`):** CockroachDB (`SERIALIZABLE`) triggered `9x` raw `40001` (`WriteTooOldError`), converging to `1100` after `27` automated retries; YugabyteDB (`REPEATABLE READ`) hit `8x` raw `40001` (`33` retries -> `1100`); Citus (`READ COMMITTED`) serialized cleanly (`1100`), raising `40001` only under `REPEATABLE READ`.
- **Mitigation:** Never rely on LWW for financial balances or counters; use `spock.delta_apply` CRDTs or `40001`-retried consensus engines.

### L4 — Secondary `UNIQUE(email)` Constraint Collisions

- **The hardest async multi-master trap:** Two rows with *distinct* PKs (`id=1` on `n1`, `id=2` on `n2`) inserted concurrently with identical `email = 'dup@t.io'` both commit locally.
- **`pg-birep` (`#1`) & `bucardo` (`#9`):** Apply workers crashed hard on **`SQLSTATE 23505`** (`accounts_email_key`), freezing `sync_mm` (`Current state: Bad, Error: 7`) and halts in `pg_stat_subscription_stats` until manual row deletion.
- **`pgedge` (`#2`):** Under default `spock.exception_behaviour = transdiscard` (`check_all_uc_indexes = off`), Spock logged `23505` (`exception_log = 1`), discarded the remote transaction, and left **`node1 = u1` vs `node2 = u2` permanently diverged**!
- **`citus` (`#7`):** Rejected `UNIQUE(email)` outright on distributed tables unless the distribution column was included (`UNIQUE(dist_key, email)`), returning **`SQLSTATE 0A000`**.
- **`yugabyte` (`#5`) & `cockroach` (`#6`):** Enforced global `UNIQUE` cleanly (`23505` rejected on the second writer at commit time).
- **Mitigation:** Include shard/tenant keys in `UNIQUE` indexes on Citus; treat secondary `UNIQUE` keys in async meshes via central reservation or accept Raft consensus latency.

### L5 — DDL Propagation, `TRUNCATE` & `SAVEPOINT` Limits

- **`pg-birep` (`#1`) & `bucardo` (`#9`):** `ALTER TABLE ADD COLUMN` **did not propagate** (risking tuple schema mismatch on subsequent inserts), though `TRUNCATE TABLE` propagated via logical/trigger handlers.
- **`pgedge` (`#2`):** `enable_ddl_replication=on` automatically replicated `ALTER TABLE` and `TRUNCATE` to `node2`/`node3`.
- **`citus`, `yugabyte`, `cockroach`:** DDL propagated cluster-wide AND transactional DDL with `SAVEPOINT` / `ROLLBACK TO SAVEPOINT` succeeded across all three tested engines.

### L6 — PostgreSQL Features, Extensions & Runtime Quirks

| Feature / Extension | `pg-birep` / `pgedge` / `bucardo` | `citus` (`PG 17`) | `yugabyte` (`2026.1.3`) | `cockroach` (`v24.3.0`) |
| :--- | :--- | :--- | :--- | :--- |
| **`pg_advisory_lock`** | **Node-local only** (no cluster sync) | Worker-scoped | Global (`OK`) | Global (`OK`) |
| **`LISTEN` / `NOTIFY`** | **Node-local only** | Coord-local (`OK`) | **`ERR (0A000 disabled)`** | **`ERR (42601 syntax)`** |
| **`TEMP TABLE`** | Session-local (`OK`) | Session-local (`OK`) | Session-local (`OK`) | **`ERR (XCEXF)`** unless `experimental_enable_temp_tables=on` |
| **`pg_trgm` / `uuid-ossp`** | `OK` | `OK` | `OK` | `OK` (built-in emulation) |
| **`pgvector` (`vector`)** | Native PG extension | **`ERR (0A000)`** (on dist probe) | `OK` (native YSQL) | `CREATE EXTENSION vector` OK; native `VECTOR(3)` column OK |

*Container Image Quirk (`pgedge`):** Rocky UBI image `17-spock5-minimal` defaulted to `output_plugin_libraries='pgoutput, test_decoding'`, throwing `SQLSTATE 42501` until explicitly overridden with `output_plugin_libraries=pgoutput,spock_output` and `host replication` `scram-sha-256` entries.

### L7 — Offline Node WAL Slot Bloat & Delta Queue Retention

- Stopping one peer node left surviving nodes writable in all `AP` systems (`pg-birep` retained **`54,432 B`** WAL in `pg_replication_slots`; `pgedge` retained **`309,560 B`**; `bucardo` queued **`8` delta rows** in `bucardo.delta_public_accounts`), converging `5/5` rows cleanly upon restart. Unbounded outages risk exhausting primary disk unless `max_slot_wal_keep_size` is configured!
- On `citus`, stopping `worker2` kept reference-table reads and `worker1` shards online while failing queries hitting `worker2` shards until recovery. On `pg17-sync-streaming`, stopping the synchronous standby blocked primary commits (`RPO=0` guarantee).

### L8 — Majority Quorum Loss (`2/3` Down) & WAN RTT Collapse

- **1-of-3 Down:** Both `yugabyte` (`RF=3`) and `cockroach` (`RF=3`) survived `node2` termination cleanly with **`RPO = 0`** (`balance = 500` readable across survivors).
- **2-of-3 Down:** Terminating `node3` stripped Raft majority (`1/3 < 2/3`). Both clusters **halted completely** (`yugabyte` connection timeout; `cockroach` **`SQLSTATE 57014`** query timeout) until quorum returned—proving strict `PC/EC` behavior.
- **WAN RTT Amplification (Suite F):** Adding `25 ms` egress delay (`~50 ms` RTT) dropped `pg17-sync-streaming` to `57.00 TPS` (`-86.1%`), `citus` to `21.67 TPS` (`-93.0%`), `cockroach` to `10.06 TPS` (`-76.1%`), and `yugabyte` to `5.78 TPS` (`-96.7%`).

---

## 3. Extended Empirical Matrix (`T11–T18`) Across All 10 Topologies

Eight edge-case probes (`results/extended_functional_matrix.csv`, `functional_limits_matrix.csv`) add **`pg17-async-streaming`** and **`pg17-logical`** across all 10 topologies:

- **`T11` Bulk 10k & Catch-Up:** `22,079` (`cockroach`) to `67,406 rows/s` (`pgedge`); catch-up `105–115 ms` (streaming), `139 ms` (`bucardo`), `265 ms` (`cockroach`), `333–350 ms` (logical/Spock), `417 ms` (`yugabyte`).
- **`T12` `UPDATE` vs `DELETE` Tombstone:** **`pg17-logical` DIVERGED** (`pub=upd_n1` vs `sub=DELETED`); async meshes dropped `UPDATE` (`DELETED`); streaming rejected standby `DELETE` (`25006`); Citus/YB/CRDB converged.
- **`T13` Cross-Node FK Race:** Streaming blocked standby (`25006x10`); **`bucardo` failed `0/10` (`23503x10`)**; Raft/Citus and LAN logical/Spock passed `10/10`.
- **`T14` Rich Fidelity (64 KiB `BYTEA`, `JSONB`, UTF-8):** `9/10` bit-identical (`md5=00493e3a`); `pgedge` image defaults to **`SQL_ASCII`** (`chr(20013)` hit **`54000`**; escaped UTF-8 matched `3/3`, `md5=f798eb5a`).
- **`T15` RAW Lag (`n=30`, `p50/p95` ms):** `standalone` `1.15/1.55`, `pgedge` `1.16/1.63`, `pg-birep` `1.47/2.28`, `pg17-logical` `1.68/2.14`, `pg17-sync` `1.88/2.74`, `yugabyte` `2.01/2.83`, `citus` `1.71/13.89`, `cockroach` `4.09/4.98`, `pg17-async` `9.65/25.13`, **`bucardo` `548.74/1,275.25`**.
- **`T16` `SIGKILL` & RPO:** `20/20` (`RPO=0` LAN) + `21/21` recovery on 8 stacks; `citus` `worker2` raised **`08006`** then recovered `21/21`; `bucardo` `node1` metadata crash ended `20/21`.
- **`T17` 3s Open TX:** `NO_DIRTY_READ` on `10/10`; `cockroach` blocked reader via intent wait (`serializable_intent_wait=2.1s`).
- **`T18` Sequence Sync (50 inserts):** Streaming (`66|true`, `next=67`), `yugabyte` (`101`), `cockroach`/`citus` (`51`) failover-safe; all 4 logical/trigger stacks stuck at `1|false` -> **`23505`** (`pg17-logical` retained `27,320 B` offline WAL vs `3,088 B` streaming).

---

## 4. PostgreSQL 18.6 Limits Verification & Ecosystem Sustainability

Live PG 18.6 re-verification ([`results/functional_limits_pg18.csv`](../../results/functional_limits_pg18.csv), [`results/benchmark_pg18.csv`](../../results/benchmark_pg18.csv); full analysis in [Ch. 12](12_postgresql_18_clustering_and_benchmarks.md)) refines these limits:
- **Resolved in PG 18.6:** Native `uuidv7()` converged **50/50 dual-node active-active inserts** (`0` `23505`, `0` B-tree inversions), `data_checksums=on` guards against silent corruption, and `pg_stat_subscription_stats` now exposes **7 `confl_*` counters** including **`confl_multiple_unique_conflicts=1`**.
- **Still Open in PG 18.6:** `FOR ALL SEQUENCES` / `REFRESH SEQUENCES` raise **`SQLSTATE 42601`** (deferred to PG 19; logical peers stay at `1|false` -> `23505`), `io_method=io_uring` fails with `EPERM` under default Docker seccomp, `pg18-birep` still suffers `T13` async FK races (`2/10 ok; 23503x8`) and overlapping Lost Updates (`-83,252` in Suite D), and Auto-DDL remains absent.
- **Vitality & Charts:** Cross-check long-term maintenance risk (`pgEdge/spock` `621`/12m vs dormant `bucardo`/`slony`/`rubyrep` `0`/12m) in [Ch. 11](11_ecosystem_popularity_and_vitality.md) and [`chart_08`](../../assets/charts/chart_08_popularity_stars_forks_log.png) / [`chart_09`](../../assets/charts/chart_09_popularity_commits_activity_log.png) / [`chart_10`](../../assets/charts/chart_10_pg18_vs_pg17_log.png).

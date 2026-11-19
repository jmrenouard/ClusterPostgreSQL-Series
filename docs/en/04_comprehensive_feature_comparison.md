# 04 — Comprehensive 36-Criterion Feature Comparison

**Series:** PostgreSQL Multi-Master & Active-Active Architectures  
**Author:** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr)  
**License:** MIT License

---

All **15 architectures** from Chapter 01 are evaluated across **36 technical and operational criteria** grouped into five matrices. Abbreviations: **Ext** (Extension), **RI** (`REPLICA IDENTITY`), **LWW** (Last-Write-Wins), **CRDT** (Conflict-Free Replicated Data Type), **2PC** (Two-Phase Commit), **HLC** (Hybrid Logical Clock), **OSS** (Open Source), **Std PG** (Standard PostgreSQL heap/B-tree).

## Matrix A — Core Engine, Replication & CAP/PACELC (Criteria 1–8)

| # | Solution | 1. Engine Base | 2. Storage | 3. Sync / Consensus | 4. CAP | 5. PACELC | 6. Write Topology | 7. Min HA | 8. Quorum |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :--- | :---: | :--- |
| #1 | PG Native Birep | Core PG 16-18 | Std PG | Async `pgoutput` | AP | PA/EL | Full Mesh | 2 | None |
| #2 | pgEdge Spock v5 | PG 15-17 Ext | Std PG | Async Spock WAL | AP | PA/EL | Full Mesh | 2-3 | None |
| #3 | pglogical 2 | PG 9.4-17 Ext | Std PG | Async `pglogical` | AP | PA/EL | Mesh / Hub | 2 | None |
| #4 | EDB PGD (BDR) | PG Ext + Proxy | Std PG | Logical + Raft | Hybrid | PA/EL or PC/EC | Mesh / Lead | 3 | Raft (CAMO/Eager) |
| #5 | YugabyteDB | Fork PG C (YSQL) | DocDB LSM | Per-Tablet Raft | CP | PC/EC | Active-Active | 3 | Raft Majority |
| #6 | CockroachDB | Go SQL Engine | Pebble LSM | Per-Range Raft | CP | PC/EC | Active-Active | 3 | Raft Majority |
| #7 | Citus | PG 17 Ext | Std PG | Shards + 2PC Ref | CP | PC/EC | Coord / MX | 3 (+HA) | Worker Health |
| #8 | OpenTenBase/XL | Fork PG MPP | Std PG | GTM + 2PC | CP | PC/EC | Coord + DN | 3+ | GTM + DN |
| #9 | Bucardo 5 | PG + Perl | Std PG | Async PL/Perl Trig | AP | PA/EL | `dbgroup` | 2+ | None |
| #10 | SymmetricDS | PG + Java | Std PG | Async Trig Batch | AP | PA/EL | Mesh / Tier | 2+ | None |
| #11 | PgPool-II | Proxy + PG | Std PG | Broadcast / SI | CP/AP | PC/EC (SI) | Proxy Bcast | 2+ | Watchdog (3+) |
| #12 | Aurora Limitless | AWS PG Sharded | Aurora Log | Shards + Time 2PC | CP | PC/EC | Routers+Shards | Managed | Storage Quorum |
| #13 | GCP Spanner PG | Spanner PG Int | Colossus LSM | Paxos + TrueTime | CP | PC/EC | Multi-Region | Managed | Paxos Majority |
| #14 | Legacy Triggers | PG + Ruby/C/Py | Std PG | Trigger / PgQ | AP | PA/EL | Single/Mesh | 2+ | None |
| #15 | Patroni + etcd | Core PG 17 | Std PG | WAL + etcd Raft | CP/AP | PC/EC or PA/EL | Single Primary | 3 (etcd) | etcd Raft |

## Matrix B — Conflict Management, Identity & Commit Semantics (Criteria 9–16)

| # | Solution | 9. Conflict Detect | 10. Conflict Resolution | 11. CRDT / Delta | 12. Dist Commit | 13. `40001` Retry | 14. Clock Risk | 15. Global IDs | 16. Lost Update Safe |
| :---: | :--- | :--- | :--- | :---: | :--- | :---: | :--- | :--- | :---: |
| #1 | PG Native Birep | Apply err `23505` | **None** (Worker halts) | No | Local only | No | None | Manual Step/UUID | **No** |
| #2 | pgEdge Spock v5 | `commit_ts`+tuple | LWW / FWW / Keep | **Yes (`delta_apply`)** | Local only | No | High (NTP/LWW) | `snowflake` Ext | **Delta cols only** |
| #3 | pglogical 2 | `commit_ts` | LWW / Apply / Err | No | Local only | No | High (NTP/LWW) | Manual / Sync | **No** |
| #4 | EDB PGD (BDR) | `commit_ts`/Raft | LWW / CRDT / Eager | **Yes (CRDTs)** | CAMO / Eager | Optional | Bounded | `timeshard`/`galloc` | **Yes (Eager/CRDT)** |
| #5 | YugabyteDB | Intents / HLC | Wait-Queue / Abort | N/A | 2PC + Raft | **Yes (RR/SSI)** | HLC Bounded | PG/Dist Seq | **Yes** |
| #6 | CockroachDB | MVCC Intents | Abort (`40001`) | N/A | Parallel + Raft | **Mandatory** | HLC Bounded | `unique_rowid()` | **Yes** |
| #7 | Citus | Worker Locks | Wait / Deadlock | N/A | 2PC (`PREPARE`) | Rare | Low | Prefixed Seq | **Yes** |
| #8 | OpenTenBase/XL | GTM Locks | Wait / Abort | N/A | GTM + 2PC | Rare | Low (GTM) | GTM Sequence | **Yes** |
| #9 | Bucardo 5 | PK Delta Check | `bucardo_latest`/Perl | No | Local only | No | High (Trig ts) | Manual Step/UUID | **No** |
| #10 | SymmetricDS | `USE_PK/CHANGED` | `NEWER_WINS`/Manual | No | Local only | No | High (Batch ts) | Node-offset/UUID | **No** |
| #11 | PgPool-II | Proxy / SI Lock | Abort divergence | No | Proxy Lock / SI | Rare | Low | Lock-serialized | **Fragile** |
| #12 | Aurora Limitless | Dist Lock Mgr | Wait / Abort | N/A | 2PC + Time Sync | Possible | Hardware Bound | Router/Shard Seq | **Yes** |
| #13 | GCP Spanner PG | Wound-Wait | Wait / Abort | N/A | 2PC+Paxos+TrueTime | Possible | TrueTime HW | Bit-rev Seq | **Yes** |
| #14 | Legacy Triggers | Diff / None | Latest / Manual | No | Local only | No | High | Manual | **No** |
| #15 | Patroni + etcd | Single-Writer | None Needed | N/A | Local / Sync WAL | No | None | Native `SERIAL` | **Yes** |

## Matrix C — PostgreSQL Wire/Driver Compatibility, DDL & Data Model (Criteria 17–25)

| # | Solution | 17. Wire/Driver | 18. Keyless Tables | 19. Sec `UNIQUE` | 20. Cross-Node FKs | 21. Auto-DDL | 22. Triggers/PLpgSQL | 23. Large Obj | 24. Locks/`LISTEN` | 25. Extensions |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: | :--- | :---: | :--- | :--- |
| #1 | PG Native Birep | 100% (`libpq`/JDBC) | `55000` (needs `RI FULL`) | Halts (`23505`) | Local (cycle risk) | **No** | Full (local fire) | **No** | Node-Local | **100%** |
| #2 | pgEdge Spock v5 | 100% (`libpq`/JDBC) | Needs PK/`RI FULL` | LWW drops loser | Local (cycle risk) | **Yes** | Full (local fire) | **Yes (`lolor`)** | Node-Local | **100%** |
| #3 | pglogical 2 | 100% (`libpq`/JDBC) | Needs PK/`RI FULL` | LWW / Error | Local check | Explicit fn | Full (local fire) | **No** | Node-Local | **~95%** |
| #4 | EDB PGD (BDR) | 100% (`libpq`/JDBC) | Needs PK/`RI FULL` | Eager safe/LWW | Local / Eager | **Yes (Raft)** | Full | Limited | Proxy sticky | **~95%** |
| #5 | YugabyteDB | ~98% (Smart Drivers) | Supported (rowid) | Global | Global | **Yes** | Full PL/pgSQL | **No** | Global/`LISTEN` part | **High** (`pgvector`) |
| #6 | CockroachDB | ~75% (`pgwire` only) | Supported (rowid) | Global | Global | **Yes** | **Limited** | **No** | No adv/Changefeed | **None** |
| #7 | Citus | 100% (`libpq`/JDBC) | Allowed (limited) | **`0A000` w/o dist key** | Colocated/Ref | **Yes** | Worker caveats | Coord Only | Worker-Scoped | **High** |
| #8 | OpenTenBase/XL | ~90% (PG10-11 wire) | Supported | Needs shard key | Restricted | **Yes** | Partial | Coord Only | GTM-Scoped | **Medium** |
| #9 | Bucardo 5 | 100% (`libpq`/JDBC) | **Rejected** (PK req) | Async collision | Cycle risk | **No** | Full (off on apply) | **No** | Node-Local | **100%** |
| #10 | SymmetricDS | 100% (`libpq`/JDBC) | `USE_PK_DATA` req | Async collision | Cycle risk | `symadmin` | Full (loop guard) | Partial | Node-Local | **100%** |
| #11 | PgPool-II | 100% (`libpq`/JDBC) | Allowed | Allowed | Allowed | Broadcast | **Breaks determinism** | Risky | Proxy-Routed | **100%** |
| #12 | Aurora Limitless | ~95% (AWS Driver) | Shard key/Hidden | Shard-key rules | Colocated/Ref | **Yes** | Supported | Restricted | Router-Scoped | **Allowlist** |
| #13 | GCP Spanner PG | ~65% (PGAdapter) | **PK Required** | Global | Interleaved | **Yes** | **Minimal** (no trig) | **No** | Change Streams | **None** |
| #14 | Legacy Triggers | 100% (`libpq`/JDBC) | Rejected | Async collision | Cycle risk | **No** | Local | **No** | Node-Local | **100%** |
| #15 | Patroni + etcd | **100%** | **100%** | **100%** | **100%** | **100%** | **100%** | **100%** | **100% (Global)** | **100%** |

## Matrix D — Resilience, Failover & Operations (Criteria 26–31)

| # | Solution | 26. `RPO` (1-Loss) | 27. Est `RTO` | 28. Split-Brain Risk | 29. WAN Sensitivity | 30. Cluster PITR | 31. Operational Complexity |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| #1 | PG Native Birep | `> 0` (async) | `< 5 s` (LB) | **High** (data drift) | Low (local writes) | Per-node only | Medium (manual conflict fix) |
| #2 | pgEdge Spock v5 | `> 0` (async) | `< 5 s` (LB) | **Medium** (LWW) | Low (local writes) | Per-node only | Medium (NTP + WAL slots) |
| #3 | pglogical 2 | `> 0` (async) | `< 5 s` (LB) | **High** | Low | Per-node only | Medium-High |
| #4 | EDB PGD (BDR) | `0` (CAMO/Eager) | `1–5 s` (Proxy) | **Low** (Raft witness) | High Eager / Low Async | Managed (`Barman`) | High (Witness + Proxy + Raft) |
| #5 | YugabyteDB | **`0`** (`RF>=3`) | `3–5 s` (Raft) | **None** (Raft) | High (write RTT) | Dist Snapshots | High (LSM + tablet tuning) |
| #6 | CockroachDB | **`0`** (`RF>=3`) | `3–9 s` (Raft) | **None** (Raft) | High (write RTT) | Cluster Backup | Medium-High (retry tuning) |
| #7 | Citus | `0` (if worker HA) | `10–30 s` | Low (with Patroni) | High for 2PC | Coord + Worker | High (shard key + worker HA) |
| #8 | OpenTenBase/XL | `0` (with DN HA) | `15–60 s` | Medium (GTM SPOF) | Very High (GTM) | `pg_rman`/barrier | Very High |
| #9 | Bucardo 5 | `> 0` (batch) | `< 10 s` | **High** | Low | Per-node only | Medium-High (Perl + deltas) |
| #10 | SymmetricDS | `> 0` (batch) | `< 10 s` | **High** | Low (offline OK) | Per-node only | Medium-High (JVM + queues) |
| #11 | PgPool-II | `0` (if all ack) | `5–15 s` | **High** (SQL drift) | Very High | Per-node | Medium-High (degenerate node) |
| #12 | Aurora Limitless | **`0`** | `< 15 s` | **None** (Managed) | Medium-High (2PC) | Continuous Cloud | Low-Medium (Cloud Managed) |
| #13 | GCP Spanner PG | **`0`** | `< 1–5 s` | **None** | Medium (commit-wait) | Managed PITR | Low (Cloud Managed) |
| #14 | Legacy Triggers | `> 0` | Manual | **High** | Low | Per-node | High (Legacy debt) |
| #15 | Patroni + etcd | `0` (Sync) / `> 0` | `10–30 s` | **Low** (Watchdog) | High if Sync WAN | `pgBackRest` | **Low-Medium (Standard)** |

## Matrix E — Licensing, TCO & Optimal Fit (Criteria 32–36)

| # | Solution | 32. License | 33. Operational TCO & Licensing | 34. PG Parity | 35. Production Status | 36. Optimal Target Use Case |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| #1 | PG Native Birep | PostgreSQL (OSS) | Low SW cost; manual ops risk | Core PG 16-18 | Prod (partitioned) | Partitioned regional writers / upgrades |
| #2 | pgEdge Spock v5 | PostgreSQL (OSS) | Low SW cost; optional support | PG 15–17 | Active Production | Geo-distributed low-latency active-active |
| #3 | pglogical 2 | PostgreSQL (OSS) | Low SW cost; legacy debt | PG 9.4–17 | Maintenance | Legacy upgrades & selective subsets |
| #4 | EDB PGD (BDR) | **Proprietary** | **High** (per-core EDB license + witness) | PG 14–17 | Mature Enterprise | Regulated multi-region enterprise SLA |
| #5 | YugabyteDB | Apache 2.0 (OSS) | Medium-High (min 3 nodes, ops) | Fork PG 11/15+ | Mature Production | Cloud-native OLTP needing `RPO=0` + PL/pgSQL |
| #6 | CockroachDB | BSL / Enterprise | Medium-High (BSL prod limits/cloud) | Wire only | Mature Production | Greenfield SaaS built with `40001` retries |
| #7 | Citus | AGPLv3 (OSS) | Medium (infra scales linearly) | Core PG 17 | Mature Production | Multi-tenant SaaS sharded on `tenant_id` |
| #8 | OpenTenBase/XL | Open Source | High engineering ops cost | PG 10–11 fork | Niche / XL Dormant | Intra-DC MPP HTAP (OpenTenBase) |
| #9 | Bucardo 5 | BSD (OSS) | Low SW; high trigger/ops cost | PG 9–17 | Legacy Maint | Low-volume tables needing Perl hooks |
| #10 | SymmetricDS | LGPL / Pro | Low-Med (Pro GUI/connectors paid) | Any JDBC/PG | Mature Niche | Heterogeneous DB & offline retail edge |
| #11 | PgPool-II | BSD (OSS) | Low SW; high divergence risk | Core PG | **Streaming mode** | Pooling + single-primary reads (no bcast) |
| #12 | Aurora Limitless | AWS Proprietary | **High** (ACU router+shard cloud bill) | Aurora PG 16+ | GA Cloud Service | AWS-native horizontal PG write scaling |
| #13 | GCP Spanner PG | GCP Proprietary | **Very High** (Spanner nodes + net) | PG Wire Subset | Mature Cloud | Global ledgers needing TrueTime ACID |
| #14 | Legacy Triggers | OSS (BSD/GPL) | High maintenance debt | Legacy PG | **Deprecated/EOL** | Migration away from legacy triggers |
| #15 | Patroni + etcd | MIT / PostgreSQL | **Lowest TCO** for `RPO=0` HA | Core PG 17 | **Industry Std** | 80%+ OLTP workloads needing single-writer HA |

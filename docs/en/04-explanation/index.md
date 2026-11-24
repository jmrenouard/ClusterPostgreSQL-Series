# Explanation (English)

Analytical discussions of consensus theory, conflict calculus, replication models, and PostgreSQL 18.6 internals.

- [01 Executive Summary & Taxonomy](../01_executive_summary_and_taxonomy.md) — Taxonomy of 18 PostgreSQL topologies.
- [02 CAP, PACELC & Conflicts](../02_theoretical_foundations_cap_pacelc_conflicts.md) — CAP/PACELC trade-offs, Raft/Paxos, conflict probability.
- [03a Native & Extensions](../03a_solutions_native_and_extensions.md) — PG 17/18 logical, Spock, pglogical, EDB PGD.
- [03b Distributed & Cloud](../03b_solutions_distributed_triggers_cloud.md) — YugabyteDB, CockroachDB, Citus, YT Cluster, Cloud.
- [10 Streaming vs Multi-Master](../10_streaming_vs_logical_vs_multimaster.md) — Latency, DDL, failover, operational cost.
- [12 PG 18.6 Clustering](../12_postgresql_18_clustering_and_benchmarks.md) — AIO `io_method`, NUMA, replication updates.

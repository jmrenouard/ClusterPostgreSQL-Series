"""Shared 18-topology palette, suite labels, and CSV sources for Log10 charts."""

from __future__ import annotations

CSVS = (
    "benchmark_summary.csv",
    "benchmark_extended_workloads.csv",
    "benchmark_wan_sweep.csv",
    "benchmark_concurrency_sweep.csv",
    "benchmark_pg18.csv",
    "benchmark_yt_cluster.csv",
)

TOPOS = [
    ("pg17-standalone", "PG17 Standalone", "#475569"),
    ("pg17-async-streaming", "PG17 Async Stream", "#0284c7"),
    ("pg17-sync-streaming", "PG17 Sync Stream", "#1d4ed8"),
    ("pg17-logical", "PG17 Logical Uni", "#0891b2"),
    ("pg-birep", "PG17 BiRep", "#0d9488"),
    ("pg18-standalone", "PG18 Standalone", "#0f172a"),
    ("pg18-async-streaming", "PG18 Async Stream", "#06b6d4"),
    ("pg18-sync-streaming", "PG18 Sync Stream", "#2563eb"),
    ("pg18-logical", "PG18 Logical Uni", "#14b8a6"),
    ("pg18-birep", "PG18 BiRep (uuidv7)", "#059669"),
    ("pgedge", "pgEdge Spock (LWW)", "#f59e0b"),
    ("pgedge-delta-apply", "pgEdge delta_apply", "#16a34a"),
    ("bucardo", "Bucardo 5.6", "#ea580c"),
    ("citus", "Citus 14.2", "#7c3aed"),
    ("yugabyte", "YugabyteDB Raft", "#db2777"),
    ("cockroach", "CockroachDB Raft", "#dc2626"),
    ("cockroach-rc", "CockroachDB (RC)", "#991b1b"),
    ("yt-cluster", "YT Cluster (cc=half)", "#4f46e5"),
    ("yt-cluster-async", "YT Cluster (async)", "#8b5cf6"),
]

LBL = {k: v for k, v, _ in TOPOS}
COL = {k: c for k, _, c in TOPOS}
ORD = [k for k, _, _ in TOPOS]

SLAB = {
    "A_single_rw": "A: Single RW",
    "B1_disjoint_rw": "B1: Disjoint RW",
    "B2_overlap_rw": "B2: Overlap RW",
    "C_multinode_ro": "C: Multi-Node RO",
    "D_hot_conflict": "D: Hot Conflict",
    "E_sysbench_oltp_rw": "E1: Sysbench RW",
    "E1_sysbench_oltp_rw": "E1: Sysbench RW",
    "E2_sysbench_oltp_ro": "E2: Sysbench RO",
    "E3_sysbench_oltp_wo": "E3: Sysbench WO",
    "E4_sysbench_point_select": "E4: Point Select",
    "F_wan_netem_10ms": "F: WAN 10ms",
    "F_wan_netem_25ms": "F: WAN 25ms",
    "F_wan_netem_50ms": "F: WAN 50ms",
    "H_append_only_insert": "H: Append Insert",
}

SCOL = ["#1e40af", "#0ea5e9", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"]

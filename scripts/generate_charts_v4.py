#!/usr/bin/env python3
"""Generate Wave-4 YT Cluster vs active-active Multi-Master/Raft Log10 chart (chart_11)."""

from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from generate_charts import fnum, fval, load_data, plt, spread
from generate_charts_v3 import BKW, NAN, glog, save

MM = [
    ("yt-cluster", "YT Cluster (cc=half)", "#4f46e5", "-"),
    ("yt-cluster-async", "YT Cluster (async)", "#8b5cf6", "-."),
    ("pg18-birep", "PG18 BiRep (uuidv7)", "#059669", "--"),
    ("pgedge", "pgEdge Spock (LWW)", "#f59e0b", ":"),
    ("yugabyte", "YugabyteDB Raft", "#db2777", "-"),
    ("cockroach", "CockroachDB Raft", "#dc2626", "-"),
]
PANELS = [
    (
        "A. Core Writes, Hot Contention & Append TPS (Log10)",
        [
            ("A_single_rw", "A: Single RW"), ("B1_disjoint_rw", "B1: Disjoint"),
            ("B2_overlap_rw", "B2: Overlap"), ("D_hot_conflict", "D: Hot Conflict"),
            ("H_append_only_insert", "H: Append uuidv7"),
        ],
    ),
    (
        "B. Read Scaling & Sysbench OLTP Profiles (Log10 TPS)",
        [
            ("C_multinode_ro", "C: Read Only"), ("E_sysbench_oltp_rw", "E1: SB RW"),
            ("E2_sysbench_oltp_ro", "E2: SB RO"), ("E3_sysbench_oltp_wo", "E3: SB WO"),
            ("E4_sysbench_point_select", "E4: Point Sel"),
        ],
    ),
]
SWEEPS = [
    ("C. WAN RTT Sensitivity (tc netem 0-50ms, Log10 TPS)", "Delay (tc netem)", [("A_single_rw", "0 ms"), ("F_wan_netem_10ms", "10 ms"), ("F_wan_netem_25ms", "25 ms"), ("F_wan_netem_50ms", "50 ms")]),
    ("D. Concurrency Scaling (c=1..32, Log10 TPS)", "Concurrent Clients", [(f"G_conc_c{c}", f"c={c}") for c in (1, 4, 8, 16, 32)]),
]
FOOT = "LightPath | ClusterPostgreSQL-Series | 18-Suite Empirical Comparison (PG_SCALE=2)"


def draw_bars(ax: plt.Axes, idx: dict, ti: str, suites: list[tuple[str, str]]) -> None:
    """Render grouped Log10 TPS bars across selected active-active topologies."""
    nt, xs, w = len(MM), list(range(len(suites))), 0.84 / len(MM)
    av: list[float] = []
    for i, (tp, lb, col, _ls) in enumerate(MM):
        off = (i - (nt - 1) / 2.0) * w
        vals = [fnum(idx[tp].get(s, {}).get("tps")) for s, _ in suites]
        bars = ax.bar([x + off for x in xs], [v if v > 0 else NAN for v in vals], w * 0.9, label=lb, color=col, **BKW)
        for b, v in zip(bars, vals):
            if v > 0:
                av.append(v)
                ax.text(b.get_x() + b.get_width() / 2.0, v * 1.13, fval(v), ha="center", va="bottom", fontsize=5.8, rotation=82, weight="semibold", color="#1e293b")
    glog(ax, "y")
    ax.set_ylabel("TPS (Log10)", fontsize=8.8)
    ax.set_title(ti, fontsize=9.8, pad=10)
    if av:
        ax.set_ylim(max(10 ** math.floor(math.log10(min(av)) - 0.15), 0.5), max(av) * 4.8)
    ax.set_xticks(xs)
    ax.set_xticklabels([lb for _, lb in suites], fontsize=8.1, weight="semibold")


def draw_curve(ax: plt.Axes, idx: dict, ti: str, xlab: str, steps: list[tuple[str, str]]) -> None:
    """Render WAN or concurrency sweep curves with de-overlapped endpoint labels."""
    pts_end, xr = [], len(steps) - 1
    for tp, lb, col, ls in MM:
        pts = [(i, v) for i, (s, _) in enumerate(steps) if (v := fnum(idx[tp].get(s, {}).get("tps"))) > 0]
        if len(pts) >= 2:
            ax.plot([x for x, _ in pts], [y for _, y in pts], marker="o", ls=ls, lw=2.0, ms=5.0, color=col, label=lb)
            pts_end.append((pts[-1][1], fval(pts[-1][1]), col))
    glog(ax, "y")
    ax.set_ylabel("TPS (Log10)", fontsize=8.8)
    ax.set_xlabel(xlab, fontsize=8.6, color="#334155")
    ax.set_title(ti, fontsize=9.8, pad=10)
    if pts_end:
        sp = spread(pts_end, 0.10)
        ax.set_ylim(max(ax.get_ylim()[0], 0.5), max(ax.get_ylim()[1], max(y for y, _, _ in sp) * 1.45))
        for y, txt, c in sp:
            ax.annotate(txt, (xr, y), (5, 0), textcoords="offset points", fontsize=7.2, color=c, weight="bold", va="center")
    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([lb for _, lb in steps], fontsize=8.2)
    ax.set_xlim(-0.15, xr + 0.52)


def main() -> None:
    """Build chart_11_yt_cluster_vs_multimaster_log.png."""
    idx, _ = load_data()
    fig, ((a1, a2), (a3, a4)) = plt.subplots(2, 2, figsize=(16.0, 10.6))
    for ax, (ti, suites) in zip((a1, a2), PANELS):
        draw_bars(ax, idx, ti, suites)
    for ax, (ti, xlab, steps) in zip((a3, a4), SWEEPS):
        draw_curve(ax, idx, ti, xlab, steps)
    fig.legend(*a1.get_legend_handles_labels(), loc="lower center", ncol=6, fontsize=8.2, bbox_to_anchor=(0.5, 0.032))
    fig.subplots_adjust(top=0.89, bottom=0.11, hspace=0.30, wspace=0.18)
    save(
        fig,
        "chart_11_yt_cluster_vs_multimaster_log.png",
        "YT Cluster 1.21.3 (Sync-2PC & Async) vs Active-Active Multi-Master & Raft (Log10)",
        "3-node PG 18.7 (cc=half sync-2PC vs nodes>=0 async, 0 drift) vs PG 18 BiRep, pgEdge LWW & Raft DistSQL",
        FOOT,
    )
    print("Rendered chart_11_yt_cluster_vs_multimaster_log.png")


if __name__ == "__main__":
    main()

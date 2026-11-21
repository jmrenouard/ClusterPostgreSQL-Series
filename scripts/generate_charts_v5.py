#!/usr/bin/env python3
"""Generate V5 Production-Tuned Log10 PNG charts (chart_12 and chart_13)."""

from __future__ import annotations

import csv
import math
import pathlib
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from chart_meta import COL, SCOL, SLAB, TOPOS
from generate_charts import RES_DIR, draw_bars as draw_base_bars, fnum, fval, load_data, plt
from generate_charts_v3 import NAN, glog, save
from matplotlib.patches import Patch

OPT_CSV = RES_DIR / "benchmark_optimized.csv"

OPT_ORD = [
    "pg17-standalone", "pg17-async-streaming", "pg17-sync-streaming", "pg17-logical", "pg-birep",
    "pg18-standalone", "pg18-async-streaming", "pg18-sync-streaming", "pg18-logical", "pg18-birep",
    "pgedge", "bucardo", "citus", "yugabyte", "cockroach", "cockroach-rc", "yt-cluster", "yt-cluster-async",
]

SHORT_LBL = {
    "pg17-standalone": "PG17 Stand.", "pg17-async-streaming": "PG17 Async",
    "pg17-sync-streaming": "PG17 Sync", "pg17-logical": "PG17 Logic.", "pg-birep": "PG17 BiRep",
    "pg18-standalone": "PG18 Stand.", "pg18-async-streaming": "PG18 Async",
    "pg18-sync-streaming": "PG18 Sync", "pg18-logical": "PG18 Logic.", "pg18-birep": "PG18 BiRep",
    "pgedge": "pgEdge CRDT", "bucardo": "Bucardo 5.6", "citus": "Citus 14.2",
    "yugabyte": "YugabyteDB", "cockroach": "CRDB (Ser)", "cockroach-rc": "CRDB (RC)",
    "yt-cluster": "YT (half)", "yt-cluster-async": "YT (async)",
}

OPT_LBL = {**{k: v for k, v, _ in TOPOS}, "pgedge": "pgEdge (delta_apply)", "cockroach": "CockroachDB (Ser)"}

C12_SUITES = [
    ("A_single_rw", "A. Single-Node RW (c=8, Log10 TPS)", {
        "pg18-logical": ("5.9x", 6.2), "cockroach": ("7.3x", 6.4), "yt-cluster-async": ("2.8x", 5.8),
    }),
    ("B2_overlap_rw", "B2. Multi-Node Overlap RW (c=8, Log10 TPS)", {
        "pg-birep": ("0 drift", 6.2), "pgedge": ("CRDT 0 drift\n(was -66k)", 7.2), "yt-cluster": ("5.7x", 6.0),
    }),
    ("D_hot_conflict", "D. 50-Key Hot Conflict (Log10 TPS & Integrity)", {
        "pgedge": ("CRDT 0 drift\n(was -279k)", 11.5), "pg-birep": ("LWW\n-94.5k", 7.0),
        "bucardo": ("LWW\n-304k", 5.8),
    }),
    ("E_sysbench_oltp_rw", "E1. Sysbench OLTP RW (4x10k vs 4x25k, Log10 TPS)", {
        "pg17-logical": ("1.7x", 5.8), "cockroach": ("1.9x (0 fail)", 4.8), "cockroach-rc": ("RC 0 retries\n(3.4x Ser base)", 10.5),
    }),
    ("H_append_only_insert", "H. Append-Only Bulk Insert (uuidv7 / CACHE 1000)", {
        "pg-birep": ("3.8x", 6.2), "pg18-async-streaming": ("1.9x", 6.0), "yt-cluster-async": ("2.0x", 6.0),
    }),
    ("F_wan_netem_25ms", "F. WAN Netem 25 ms RTT (Log10 TPS)", {
        "pg17-logical": ("3.0x", 6.2), "pg18-sync-streaming": ("4.3x", 6.2), "yugabyte": ("3.6x", 6.2),
    }),
]

FOOT_12 = "LightPath | ClusterPostgreSQL-Series | Baseline (301 rows, PG_SCALE=2) vs Production-Tuned (318 rows, PG_SCALE=20, fsync=on)"
FOOT_13 = "LightPath | ClusterPostgreSQL-Series | Production-Tuned V5 Panorama (18 topologies, 318 rows, PG_SCALE=20, 4x25k Sysbench)"


def load_optimized() -> dict[str, dict[str, dict[str, str]]]:
    """Load results/benchmark_optimized.csv keyed by (topology, suite)."""
    idx: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    with OPT_CSV.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            idx[r["topology"].strip()][r["suite"].strip()] = r
    return idx


def has_drift(row: dict[str, str]) -> bool:
    """Return True if a row exhibits balance drift or lost-update divergence."""
    if not row:
        return False
    drift = abs(fnum(row.get("balance_drift", "0")))
    status = row.get("convergence_status", "")
    return drift > 0 or "DIVERGED" in status or "LOST_UPDATE" in status


def draw_c12_panel(ax: plt.Axes, base: dict, opt: dict, suite: str, title: str, pills: dict) -> None:
    """Draw one Baseline vs Production-Tuned Log10 panel across all 18 topologies."""
    xs = list(range(len(OPT_ORD)))
    w = 0.39
    vals_all: list[float] = []
    new_slots: list[int] = []
    na_slots: list[int] = []
    for i, topo in enumerate(OPT_ORD):
        brow = base[topo].get(suite, {}) if topo != "cockroach-rc" else {}
        orow = opt[topo].get(suite, {})
        bv, ov = fnum(brow.get("tps")), fnum(orow.get("tps"))
        b_bad, o_bad = has_drift(brow), has_drift(orow)
        b_col = "#fca5a5" if b_bad else "#64748b"
        b_ec = "#dc2626" if b_bad else "#ffffff"
        o_col = "#fca5a5" if o_bad else ("#16a34a" if (b_bad and not o_bad) else "#0284c7")
        o_ec = "#dc2626" if o_bad else "#ffffff"

        if bv > 0:
            vals_all.append(bv)
            ax.bar(i - w / 2, bv, w * 0.92, color=b_col, ec=b_ec, lw=0.7 if b_bad else 0.4, hatch="///" if b_bad else None)
            ax.text(i - w / 2, bv * 1.15, fval(bv), ha="center", va="bottom", fontsize=5.6, rotation=86, color="#991b1b" if b_bad else "#334155")
        elif topo == "cockroach-rc" and ov > 0:
            new_slots.append(i)

        if ov > 0:
            vals_all.append(ov)
            ax.bar(i + w / 2, ov, w * 0.92, color=o_col, ec=o_ec, lw=0.7 if o_bad else 0.4, hatch="///" if o_bad else None)
            tcol = "#991b1b" if o_bad else ("#166534" if o_col == "#16a34a" else "#0369a1")
            ax.text(i + w / 2, ov * 1.15, fval(ov), ha="center", va="bottom", fontsize=5.7, rotation=86, color=tcol, weight="bold")
        elif bv <= 0:
            na_slots.append(i)

        if topo in pills and ov > 0:
            tag, mul = pills[topo]
            is_warn = "LWW" in tag and "was " not in tag
            fc, ec, tc = ("#fee2e2", "#dc2626", "#991b1b") if is_warn else ("#dcfce7", "#16a34a", "#065f46")
            ax.text(i, max(bv, ov) * mul, tag, ha="center", va="bottom", fontsize=5.9, weight="bold", color=tc,
                    bbox={"boxstyle": "round,pad=0.20", "fc": fc, "ec": ec, "lw": 0.75})

    glog(ax, "y")
    ax.set_title(title, fontsize=9.8, pad=8)
    ax.set_ylabel("TPS (Log10)", fontsize=8.8)
    lo = max(10 ** math.floor(math.log10(min(vals_all)) - 0.15), 0.7) if vals_all else 1.0
    hi = max(vals_all) * 32.0 if vals_all else 1000.0
    ax.set_ylim(lo, hi)
    for i in new_slots:
        ax.text(i - w / 2, lo * 1.18, "new", ha="center", va="bottom", fontsize=5.5, rotation=86, color="#64748b", style="italic")
    for i in na_slots:
        ax.text(i, lo * 1.18, "N/A\n(1n)", ha="center", va="bottom", fontsize=5.6, color="#94a3b8", weight="bold")
    ax.set_xlim(-0.7, len(OPT_ORD) - 0.3)
    ax.set_xticks(xs)
    ax.set_xticklabels([SHORT_LBL[t] for t in OPT_ORD], rotation=28, ha="right", fontsize=7.6, weight="semibold")


def chart_12(base: dict, opt: dict) -> None:
    """Render chart_12_baseline_vs_optimized_log.png across 6 key suites."""
    fig, axes = plt.subplots(3, 2, figsize=(21.0, 14.8), sharex=True)
    for ax, (su, title, pills) in zip(axes.flat, C12_SUITES):
        draw_c12_panel(ax, base, opt, su, title, pills)
    handles = [
        Patch(fc="#64748b", ec="#fff", label="Baseline Default (PG_SCALE=2, 0 drift)"),
        Patch(fc="#0284c7", ec="#fff", label="Production-Tuned (PG_SCALE=20, 0 drift)"),
        Patch(fc="#16a34a", ec="#fff", label="Tuned Integrity Fix (0 drift, was LWW/Diverged)"),
        Patch(fc="#fca5a5", ec="#dc2626", hatch="///", label="Non-Zero Balance Drift (LWW Lost Update)"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.922), ncol=4, fontsize=8.6)
    fig.subplots_adjust(top=0.875, bottom=0.085, hspace=0.24, wspace=0.14)
    save(
        fig,
        "chart_12_baseline_vs_optimized_log.png",
        "Baseline (PG_SCALE=2) vs Production-Tuned (PG_SCALE=20) Across 18 Topologies (Log10)",
        "Durable fsync=on | Tuned PG18/Logical/Raft deliver 1.7x-7.3x speedups; pgEdge delta_apply removes -279k LWW drift; CRDB RC removes 40001 retries",
        FOOT_12,
    )
    print("Rendered chart_12_baseline_vs_optimized_log.png")


def spread_bidir(items: list[tuple[float, str, str]], lo: float, hi: float, gap: float) -> list[tuple[float, float, str, str]]:
    """Bidirectionally de-overlap log10 label y-positions inside [lo, hi]."""
    arr = sorted([[math.log10(max(y, 1e-4)), math.log10(max(y, 1e-4)), t, c] for y, t, c in items], key=lambda x: x[0])
    llo, lhi = math.log10(lo), math.log10(hi)
    for _ in range(120):
        for i in range(1, len(arr)):
            diff = arr[i][1] - arr[i - 1][1]
            if diff < gap:
                push = (gap - diff) * 0.52
                arr[i - 1][1] -= push
                arr[i][1] += push
        for it in arr:
            it[1] = min(max(it[1], llo), lhi)
    for i in range(1, len(arr)):
        if arr[i][1] - arr[i - 1][1] < gap:
            arr[i][1] = arr[i - 1][1] + gap
    if arr and arr[-1][1] > lhi:
        shift = arr[-1][1] - lhi
        for it in arr:
            it[1] -= shift
    return [(10 ** orig, 10 ** adj, txt, col) for orig, adj, txt, col in arr]


def draw_c13_sweep(ax: plt.Axes, opt: dict, title: str, xlab: str, steps: list[tuple[str, str]], right_pad: float, lo_floor: float) -> None:
    """Draw a 16/18-topology Log10 sweep with zero-overlap leader-line labels."""
    xr = len(steps) - 1
    endpoints: list[tuple[float, str, str]] = []
    vals_all: list[float] = []
    for topo in OPT_ORD:
        pts = [(i, v) for i, (s, _) in enumerate(steps) if (v := fnum(opt[topo].get(s, {}).get("tps"))) > 0]
        if len(pts) < 2:
            continue
        col = "#16a34a" if topo == "pgedge" else COL.get(topo, "#334155")
        ls = "--" if topo.startswith("pg18-") else ("-." if topo.startswith("yt-") else (":" if topo in ("cockroach-rc", "pgedge") else "-"))
        ax.plot([x for x, _ in pts], [y for _, y in pts], marker="o", ls=ls, lw=1.8, ms=4.2, color=col, label=OPT_LBL[topo])
        vals_all.extend(y for _, y in pts)
        endpoints.append((pts[-1][1], f"{SHORT_LBL[topo]}: {fval(pts[-1][1])}", col))

    glog(ax, "y")
    ax.set_title(title, fontsize=9.8, pad=10)
    ax.set_ylabel("TPS (Log10)", fontsize=8.8)
    ax.set_xlabel(xlab, fontsize=8.8, color="#334155")
    lo = max(10 ** math.floor(math.log10(min(vals_all)) - 0.2), lo_floor)
    hi = max(vals_all) * 2.2
    ax.set_ylim(lo, hi)
    for y_orig, y_lbl, txt, col in spread_bidir(endpoints, lo * 1.15, hi * 0.86, 0.082):
        ax.annotate(
            txt, xy=(xr, y_orig), xytext=(xr + 0.22, y_lbl),
            fontsize=6.6, color=col, weight="bold", va="center",
            arrowprops={"arrowstyle": "-", "color": col, "lw": 0.65, "alpha": 0.65, "shrinkA": 2, "shrinkB": 2},
        )
    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([lb for _, lb in steps], fontsize=8.4, weight="semibold")
    ax.set_xlim(-0.15, xr + right_pad)


def chart_13(opt: dict) -> None:
    """Render chart_13_optimized_all_topologies_log.png across all 18 topologies."""
    fig = plt.figure(figsize=(21.5, 14.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.95, 1.12], hspace=0.40, wspace=0.18)
    ax_top = fig.add_subplot(gs[0, :])
    ax_conc = fig.add_subplot(gs[1, 0])
    ax_wan = fig.add_subplot(gs[1, 1])

    core_suites = ["A_single_rw", "B1_disjoint_rw", "C_multinode_ro", "E_sysbench_oltp_rw", "H_append_only_insert"]
    draw_base_bars(ax_top, OPT_ORD, core_suites, opt, "tps", "TPS (Log10)", "A. Core Workloads Across All 18 Production-Tuned Topologies (Log10 TPS)")
    ax_top.set_xticklabels([SHORT_LBL[t] for t in OPT_ORD], rotation=22, ha="right", fontsize=8.2, weight="semibold")

    conc_steps = [(f"G_conc_c{c}", f"c={c}") for c in (1, 4, 8, 16, 32)]
    wan_steps = [("A_single_rw", "0 ms"), ("F_wan_netem_10ms", "10 ms"), ("F_wan_netem_25ms", "25 ms"), ("F_wan_netem_50ms", "50 ms")]
    draw_c13_sweep(ax_conc, opt, "B. Concurrency Scaling Sweep (c=1..32, 18 Topologies)", "Concurrent Clients", conc_steps, 1.55, 10.0)
    draw_c13_sweep(ax_wan, opt, "C. WAN Netem Latency Sweep (0-50 ms, 16 Multi-Node Topologies)", "WAN RTT Delay (tc netem)", wan_steps, 1.25, 0.8)

    fig.legend(*ax_conc.get_legend_handles_labels(), loc="lower center", ncol=6, fontsize=8.0, bbox_to_anchor=(0.5, 0.025))
    fig.subplots_adjust(top=0.885, bottom=0.125)
    save(
        fig,
        "chart_13_optimized_all_topologies_log.png",
        "Production-Tuned 18-Topology Panorama: Core Suites, Concurrency & WAN Sweep (PG_SCALE=20, Log10)",
        "All 18 topologies tuned under durable fsync=on | PG18 + pgEdge CRDT + CRDB (Serializable & RC) + YT Cluster (cc=half & async)",
        FOOT_13,
    )
    print("Rendered chart_13_optimized_all_topologies_log.png")


def main() -> None:
    """Build V5 baseline-vs-optimized and 18-topology panorama charts."""
    base, _ = load_data()
    opt = load_optimized()
    chart_12(base, opt)
    chart_13(opt)


if __name__ == "__main__":
    main()

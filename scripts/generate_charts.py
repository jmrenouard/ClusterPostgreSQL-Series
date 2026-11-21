#!/usr/bin/env python3
"""Generate 7 publication-grade Log10 PNG benchmark charts from merged CSVs."""

from __future__ import annotations

import csv
import math
import pathlib
import re
import sys
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from chart_meta import COL, CSVS, LBL, ORD, SCOL, SLAB, TOPOS

ROOT = pathlib.Path(__file__).resolve().parents[1]
RES_DIR = ROOT / "results"
OUT_DIR = ROOT / "assets" / "charts"

plt.rcParams.update({
    "figure.facecolor": "#fff", "axes.facecolor": "#f8fafc", "axes.edgecolor": "#cbd5e1",
    "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
    "xtick.color": "#1e293b", "ytick.color": "#1e293b", "xtick.labelsize": 8.0,
    "ytick.labelsize": 8.0, "axes.titleweight": "bold", "axes.labelweight": "bold",
    "legend.facecolor": "#fff", "legend.edgecolor": "#e2e8f0",
})


def fnum(v: object) -> float:
    try:
        x = float(str(v).strip())
        return x if math.isfinite(x) else 0.0
    except (ValueError, TypeError):
        return 0.0


def fval(v: float) -> str:
    if v <= 0:
        return "0"
    if v >= 1e6:
        return f"{v / 1e6:.2f}M"
    if v >= 1e4:
        return f"{v / 1e3:.1f}k"
    return f"{v / 1e3:.2f}k" if v >= 1e3 else (f"{v:.0f}" if v >= 100 else (f"{v:.1f}" if v >= 10 else f"{v:.2f}"))


def fms(v: float) -> str:
    return f"{v / 1e3:.2f}s" if v >= 1e3 else f"{fval(v)}ms"


def ftick(x: float, _p: int) -> str:
    if x <= 0:
        return "0"
    for lim, sfx in ((1e6, "M"), (1e3, "k")):
        if x >= lim:
            v = x / lim
            return f"{int(v)}{sfx}" if abs(v - round(v)) < 1e-6 else f"{v:g}{sfx}"
    return f"{int(x)}" if x >= 1 and abs(x - round(x)) < 1e-6 else f"{x:g}"


def load_data() -> tuple[dict, set[str]]:
    idx: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    su: set[str] = set()
    for name in CSVS:
        p = RES_DIR / name
        if p.is_file():
            with p.open(encoding="utf-8", newline="") as fh:
                for r in csv.DictReader(fh):
                    t, s = r["topology"].strip(), r["suite"].strip()
                    idx[t].setdefault(s, r)
                    su.add(s)
    return idx, su


def get_topos(idx: dict, delta: bool = False) -> list[str]:
    seen = set(idx)
    out = [t for t in ORD if t in seen and (delta or t != "pgedge-delta-apply")]
    return out + [t for t in sorted(seen) if t not in out and (delta or t != "pgedge-delta-apply")]


def log_y(ax: plt.Axes, yl: str, ti: str, pad: int = 10) -> None:
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(ftick))
    ax.grid(True, "major", "y", color="#cbd5e1", lw=0.8, alpha=0.8)
    ax.grid(True, "minor", "y", color="#e2e8f0", lw=0.5, ls=":", alpha=0.7)
    ax.set_ylabel(yl, fontsize=9, color="#0f172a")
    ax.set_title(ti, fontsize=9.8, color="#0f172a", pad=pad)


def save_fig(fig: plt.Figure, fn: str, ti: str, sub: str) -> None:
    fig.suptitle(ti, fontsize=12.4, weight="bold", color="#0f172a", y=0.985)
    fig.text(0.5, 0.938, sub, ha="center", va="top", fontsize=8.4, color="#475569")
    fig.text(0.99, 0.01, "LightPath | ClusterPostgreSQL-Series | 17-Topology Benchmarks (PG 17/18 + YT)", ha="right", va="bottom", fontsize=7.2, color="#64748b", style="italic")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / fn, dpi=180, bbox_inches="tight", facecolor="#fff")
    plt.close(fig)


def draw_bars(ax: plt.Axes, topos: list[str], su: list[str], idx: dict, fld: str, yl: str, ti: str) -> None:
    ns, av, xs = max(len(su), 1), [], list(range(len(topos)))
    w = min(0.84 / ns, 0.24)
    rot = 88 if (ns >= 4 and len(topos) >= 10) else (72 if ns >= 3 else (45 if ns == 2 else 0))
    fsz = 4.7 if len(topos) >= 14 and ns >= 4 else (5.2 if len(topos) >= 14 else (5.6 if len(topos) >= 10 and ns >= 4 else 6.3))
    for si, s in enumerate(su):
        off, vals = (si - (ns - 1) / 2.0) * w, [fnum(idx[t].get(s, {}).get(fld)) for t in topos]
        bars = ax.bar([x + off for x in xs], [v or float("nan") for v in vals], w * 0.9, label=SLAB.get(s, s), color=SCOL[si % len(SCOL)], ec="#fff", lw=0.45)
        for b, v in zip(bars, vals):
            if v > 0:
                av.append(v)
                ax.text(b.get_x() + b.get_width() / 2.0, v * 1.14, fval(v), ha="center", va="bottom", fontsize=fsz, rotation=rot, color="#1e293b", weight="semibold")
    log_y(ax, yl, ti, 26)
    if av:
        ax.set_ylim(max(10 ** math.floor(math.log10(min(av)) - 0.15), 0.05), max(av) * (5.8 if rot else 2.6))
    ax.set_xticks(xs)
    ax.set_xticklabels([LBL.get(t, t) for t in topos], rotation=30, ha="right", fontsize=7.4)
    ax.legend(fontsize=7.4, ncol=min(ns, 5), loc="lower center", bbox_to_anchor=(0.5, 1.01))


def spread(items: list, gap: float = 0.085) -> list:
    s = sorted([(math.log10(max(y, 1e-6)), t, c) for y, t, c in items], key=lambda p: p[0])
    for i in range(1, len(s)):
        if s[i][0] - s[i - 1][0] < gap:
            s[i] = (s[i - 1][0] + gap, s[i][1], s[i][2])
    return [(10 ** ly, t, c) for ly, t, c in s]


def draw_sweep(idx: dict, xl: list[str], seq: list[str], xlab: str, fn: str, ti: str, sub: str, ann: bool = False) -> None:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.2, 7.0))
    et, el = [], []
    for t in get_topos(idx):
        pt = [(i, v) for i, s in enumerate(seq) if (v := fnum(idx[t].get(s, {}).get("tps"))) > 0]
        pl = [(i, v) for i, s in enumerate(seq) if (v := fnum(idx[t].get(s, {}).get("lat_avg_ms"))) > 0]
        c, ls = COL.get(t, "#334155"), "--" if t.startswith("pg18-") else ("-." if t.startswith("yt-") else "-")
        for ax, p, mk, arr, fnf in ((a1, pt, "o" + ls, et, fval), (a2, pl, "s" + ls, el, fms)):
            if len(p) >= 2:
                ax.plot([x for x, _ in p], [y for _, y in p], mk, lw=1.7, ms=4.5, color=c, label=LBL.get(t, t))
                arr.append((p[-1][1], fnf(p[-1][1]), c))
    xr = len(xl) - 1
    for ax, yl, pti, pts in ((a1, "TPS (Log10)", "Throughput (Log10 TPS)", et), (a2, "Avg ms (Log10)", "Avg Latency (Log10 ms)", el)):
        log_y(ax, yl, pti)
        if ann and pts:
            sp = spread(pts, 0.068 if len(pts) >= 13 else (0.08 if len(pts) >= 9 else 0.095))
            ax.set_ylim(ax.get_ylim()[0], max(ax.get_ylim()[1], max(y for y, _, _ in sp) * 1.35))
            for y, txt, c in sp:
                ax.annotate(txt, (xr, y), (5, 0), textcoords="offset points", fontsize=6.5, color=c, weight="bold", va="center")
        ax.set_xticks(range(len(xl)))
        ax.set_xticklabels(xl, fontsize=8.4)
        if ann:
            ax.set_xlim(-0.15, xr + 0.65)
        ax.set_xlabel(xlab, fontsize=8.8, color="#334155")
    fig.legend(*a1.get_legend_handles_labels(), loc="lower center", ncol=6, fontsize=7.4, bbox_to_anchor=(0.5, 0.02))
    fig.subplots_adjust(top=0.84, bottom=0.24, wspace=0.22)
    save_fig(fig, fn, ti, sub)


def chart_07(idx: dict) -> None:
    topos = [t for t in get_topos(idx, True) if "D_hot_conflict" in idx[t]]
    dr = [idx[t]["D_hot_conflict"] for t in topos]
    tps, rd = [fnum(r.get("tps")) for r in dr], [fnum(r.get("balance_drift")) for r in dr]
    ad = [abs(d) for d in rd]
    oks = [d == 0 and not any(k in r.get("convergence_status", "") for k in ("DIVERGED", "LOST_UPDATE")) for d, r in zip(ad, dr)]
    ys = list(range(len(topos)))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15.8, 8.6), sharey=True)
    for ax, xl, ti in ((a1, "Suite D TPS (Log10)", "Hot-Row TPS (Green=0 Drift, Red=Loss)"), (a2, "Abs Drift |delta| (Log10)", "Silent Drift (50-Key Contention)")):
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(FuncFormatter(ftick))
        ax.grid(True, "major", "x", color="#cbd5e1", lw=0.8)
        ax.set_xlabel(xl, fontsize=9)
        ax.set_title(ti, fontsize=9.6, pad=8)
    a1.barh(ys, tps, color=["#16a34a" if ok else "#dc2626" for ok in oks], ec="#fff", height=0.64)
    a1.set_xlim(10, max(tps) * 11.0)
    a1.set_yticks(ys)
    a1.set_yticklabels([LBL.get(t, t) for t in topos], fontsize=8.2, weight="semibold")
    a1.invert_yaxis()
    for y, v, ok in zip(ys, tps, oks):
        a1.text(v * 1.12, y, f"{fval(v)} TPS ({'0 drift' if ok else 'LOST'})", va="center", fontsize=7.3, color="#166534" if ok else "#991b1b", weight="bold")
    a2.barh(ys, [d or 0 for d in ad], color=["#dc2626" if d > 0 else "#16a34a" for d in ad], ec="#fff", height=0.64)
    a2.set_xlim(1, max(max(ad), 1e3) * 18.0)
    for y, r, d in zip(ys, rd, ad):
        a2.text(1.5 if d == 0 else d * 1.25, y, "0 (EXACT)" if d == 0 else f"{'-' if r < 0 else '+'}{int(d):,} drift", va="center", fontsize=7.4, color="#166534" if d == 0 else "#991b1b", weight="bold")
    fig.subplots_adjust(top=0.85, bottom=0.11, wspace=0.07)
    save_fig(fig, "chart_07_integrity_vs_throughput.png", "Suite D Integrity vs Throughput (LWW vs delta_apply, YT & Raft)", "Async LWW masks silent loss; delta_apply, YT Cluster, streaming, logical & Raft keep 0 drift")


def main() -> None:
    idx, su = load_data()
    topos = get_topos(idx)
    e1 = "E1_sysbench_oltp_rw" if "E1_sysbench_oltp_rw" in su else ("E_sysbench_oltp_rw" if "E_sysbench_oltp_rw" in su else "")
    pk = lambda q: [s for s in q if s and s in su]
    sc = pk(("A_single_rw", "B1_disjoint_rw", "C_multinode_ro", e1, "H_append_only_insert"))
    sl = pk(("A_single_rw", "B1_disjoint_rw", "C_multinode_ro", e1, "F_wan_netem_25ms"))
    sb = pk((e1, "E2_sysbench_oltp_ro", "E3_sysbench_oltp_wo", "E4_sysbench_point_select"))
    specs = [
        ("chart_01_tps_log_all_suites.png", (1, 1), (19.8, 6.8), {"top": 0.83, "bottom": 0.22}, "PostgreSQL 17-Topology Throughput (Log10)", "Core pgbench, Sysbench & Append-Only TPS (PG 17/18 + YT Cluster)", [(sc, "tps", "TPS (Log10)", "Core Workloads (All 17 Topologies)")]),
        ("chart_02_latency_log_all_suites.png", (2, 1), (19.6, 10.6), {"top": 0.84, "bottom": 0.11, "hspace": 0.56}, "Average and p95 Latency Across 17 Topologies (Log10)", "Log10 separates sub-ms reads from sync/2PC/Raft WAN consensus", [(sl, "lat_avg_ms", "Avg ms (Log10)", "Average Latency (ms)"), (sl, "lat_p95_ms", "p95 ms (Log10)", "p95 Latency (ms)")]),
        ("chart_05_sysbench_profile_log.png", (1, 2), (21.0, 6.6), {"top": 0.82, "bottom": 0.24, "wspace": 0.16}, "Sysbench OLTP Profile E1-E4 (Log10)", "OLTP RW/RO/WO & Point-Select (17 topologies)", [(sb, "tps", "Sysbench TPS (Log10)", "Sysbench TPS (E1-E4)"), (sb, "lat_p95_ms", "p95 ms (Log10)", "Sysbench p95 (E1-E4)")]),
        ("chart_06_streaming_vs_logical_vs_mm.png", (1, 2), (21.0, 6.6), {"top": 0.82, "bottom": 0.24, "wspace": 0.16}, "Streaming vs Logical vs Multi-Master & YT Cluster (Log10)", "17-topology comparison across PG 17, PG 18.6, YT Cluster 1.21.3 & Raft", [(pk(("A_single_rw", "C_multinode_ro", "F_wan_netem_25ms")), "tps", "TPS (Log10)", "TPS by Tier (LAN / RO / WAN 25ms)"), (pk(("A_single_rw", "F_wan_netem_25ms")), "lat_p95_ms", "p95 ms (Log10)", "p95 Latency (LAN vs WAN 25ms)")]),
    ]
    for fn, (nr, nc), fsz, adj, ti, sub, panels in specs:
        fig, axes = plt.subplots(nr, nc, figsize=fsz)
        for ax, (p, fld, yl, pti) in zip([axes] if nr * nc == 1 else list(axes.flat), panels):
            draw_bars(ax, topos, p, idx, fld, yl, pti)
        fig.subplots_adjust(**adj)
        save_fig(fig, fn, ti, sub)
    cm = {int(m.group(1)): s for s in su if (m := re.match(r"^G_conc_c?(\d+)$", s))}
    cs = sorted(cm)
    xl, seq = ([f"c={c}" for c in cs], [cm[c] for c in cs]) if cm else (["c=8", "c=16"], ["A_single_rw", "C_multinode_ro"])
    draw_sweep(idx, xl, seq, "Clients", "chart_03_concurrency_sweep_log.png", "Concurrency Scalability (c=1..32, Log10)", "pgbench concurrency scaling (17 topologies)", bool(cm))
    rm = {0: "A_single_rw", **{int(m.group(1)): s for s in su if (m := re.match(r"^F_wan_netem_(\d+)ms$", s))}}
    rtts = sorted(rm)
    draw_sweep(idx, [f"{r} ms" for r in rtts], [rm[r] for r in rtts], "Delay (tc netem)", "chart_04_wan_netem_sweep_log.png", "WAN Latency Sensitivity (0-50ms, Log10)", "Sync/2PC/Raft collapse; async stays flat (17 topologies)", True)
    chart_07(idx)
    print(f"Rendered 7 charts ({len(topos)} topologies x {len(su)} suites).")


if __name__ == "__main__":
    main()

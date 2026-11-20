#!/usr/bin/env python3
"""Generate 3 Wave-3 publication-grade 180-DPI Log10 PNG charts (08-10)."""

from __future__ import annotations

import csv
import pathlib
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from generate_charts import OUT_DIR as OUT, RES_DIR as RES, fnum, ftick, fval, plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

PG17 = ("benchmark_summary.csv", "benchmark_extended_workloads.csv", "benchmark_wan_sweep.csv")
OVR = {"postgres-core": "PostgreSQL Core*", "pgpool2": "PgPool-II*", "spanner-pgadapter": "Spanner PGAdapter"}
CAT = {
    "Primary (Active)": ("#1d4ed8", "o"), "Primary (Companion)": ("#059669", "s"),
    "Mirror (pg.org)": ("#7c3aed", "D"), "Dormant (0/12m)": ("#dc2626", "^"), "Proxy Only": ("#d97706", "P"),
}
VIT = {"Active": "#16a34a", "Maintenance": "#d97706", "Dormant": "#dc2626", "Archived-like": "#7f1d1d"}
HA = {"l": "left", "r": "right", "c": "center"}
OFF = {
    "cockroachdb": (-10, -14, "r"), "postgres-core": (-10, 10, "r"), "citus": (10, -10, "l"),
    "yugabytedb": (-10, 10, "r"), "patroni": (-10, -10, "r"), "pglogical2": (10, -8, "l"),
    "symmetricds": (10, 8, "l"), "opentenbase": (-10, 10, "r"), "bucardo": (12, -5, "l"),
    "pgedge-spock": (10, -10, "l"), "pgpool2": (-10, 10, "r"), "pgq": (10, -4, "l"),
    "rubyrep": (-10, 10, "r"), "pgedge-snowflake": (10, -4, "l"), "spanner-pgadapter": (-10, 10, "r"),
    "pgedge-lolor": (10, -6, "l"), "slony1": (-10, 8, "r"), "londiste": (0, -15, "c"),
    "yt-cluster-lite": (10, 0, "l"),
}
PAIRS = [
    ("Stand-\nalone", "pg17-standalone", "pg18-standalone"), ("Async\nStream", "pg17-async-streaming", "pg18-async-streaming"),
    ("Sync\nStream", "pg17-sync-streaming", "pg18-sync-streaming"), ("Logical\nUni", "pg17-logical", "pg18-logical"),
    ("BiRep\nAA", "pg-birep", "pg18-birep"),
]
SUITES = [
    ("A_single_rw", "A: Single RW"), ("C_multinode_ro", "C: Multi-Node RO"),
    ("E_sysbench_oltp_rw", "E1: Sysbench RW"), ("E3_sysbench_oltp_wo", "E3: Sysbench WO"),
    ("H_append_only_insert", "H: Append Insert"), ("F_wan_netem_25ms", "F: WAN 25ms"),
]
FOOT = "LightPath | ClusterPostgreSQL-Series | Live GitHub API Snapshot (2026-11-20 UTC)"
BKW, NAN = {"ec": "#fff", "lw": 0.4}, float("nan")


def inum(v: object) -> int | None:
    s = str(v or "").strip()
    return None if not s or s.upper() == "N/A" else int(float(s))


def glog(ax: plt.Axes, axis: str) -> None:
    if axis in ("x", "both"):
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(FuncFormatter(ftick))
    if axis in ("y", "both"):
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(FuncFormatter(ftick))
    ax.grid(True, "major", axis, color="#cbd5e1", lw=0.78)
    ax.grid(True, "minor", axis, color="#e2e8f0", lw=0.45, ls=":")


def top(ax: plt.Axes, ti: str, pad: int, hnd: list | None = None, nc: int = 2, fs: float = 7.6) -> None:
    ax.set_title(ti, size=9.8, pad=pad)
    kw = {"loc": "lower center", "bbox_to_anchor": (0.5, 1.012), "ncol": nc, "fontsize": fs}
    ax.legend(handles=hnd, **kw) if hnd else ax.legend(**kw)


def save(fig: plt.Figure, fn: str, ti: str, sub: str, foot: str = FOOT) -> None:
    fig.suptitle(ti, size=12.6, weight="bold", color="#0f172a", y=0.985)
    fig.text(0.5, 0.942, sub, ha="center", va="top", size=8.4, color="#475569")
    fig.text(0.99, 0.008, foot, ha="right", va="bottom", size=7.3, color="#64748b", style="italic")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / fn, dpi=180, bbox_inches="tight", facecolor="#fff")
    plt.close(fig)


def load_pop() -> list[dict]:
    rows: list[dict] = []
    with (RES / "project_popularity.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            s = inum(r.get("stars"))
            if s is None:
                continue
            g = lambda k: inum(r.get(k)) or 0
            m, p = g("commits_12m"), r.get("pushed_at", "").strip()
            gp, gr, sid = r.get("git_present", ""), r.get("git_role", ""), r["solution_id"].strip()
            c = ("Proxy Only" if "Partial" in gp else "Mirror (pg.org)" if "Mirror" in gp
                 else "Dormant (0/12m)" if m == 0 else "Primary (Companion)" if "Companion" in gr else "Primary (Active)")
            v = "Active" if m >= 30 else ("Maintenance" if m > 0 else ("Dormant" if p >= "2024-01-01" else "Archived-like"))
            rows.append({"id": sid, "nm": OVR.get(sid, r["project_name"].split(" (")[0].strip()),
                         "s": s, "f": g("forks"), "t": g("total_commits"),
                         "m": m, "n": g("contributors"), "p": p[:7] if len(p) >= 7 else "N/A", "c": c, "v": v})
    return rows


def h_setup(ax: plt.Axes, ys: list[int], nms: list[str], xlim: tuple[float, float], xl: str) -> None:
    glog(ax, "x")
    ax.set(xlim=xlim, yticks=ys, xlabel=xl)
    ax.set_yticklabels(nms, size=8.2, weight="semibold")
    ax.invert_yaxis()


def chart_08(rows: list[dict]) -> None:
    rr = sorted(rows, key=lambda r: r["s"], reverse=True)
    ys, h, hh = list(range(len(rr))), 0.38, 0.19
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16.8, 9.1), gridspec_kw={"width_ratios": [1.16, 1.0]})

    a1.barh([y - hh for y in ys], [r["s"] for r in rr], h, color="#1d4ed8", label="GitHub Stars", **BKW)
    a1.barh([y + hh for y in ys], [r["f"] or NAN for r in rr], h, color="#0ea5e9", label="GitHub Forks", **BKW)
    for y, r in zip(ys, rr):
        s, f = r["s"], r["f"]
        a1.text(s * 1.12, y - hh, f"{s:,}", va="center", size=6.9, c="#1e3a8a", weight="bold")
        if f > 0:
            a1.text(f * 1.12, y + hh, f"{f:,}", va="center", size=6.6, c="#0369a1")
        else:
            a1.plot(4.7, y + hh, "x", c="#0369a1", ms=4.8, mew=1.4)
            a1.text(5.7, y + hh, "0 forks", va="center", size=6.5, c="#0369a1", style="italic", weight="semibold")
    h_setup(a1, ys, [r["nm"] for r in rr], (4, 350000), "Count (Log10 Scale)")
    top(a1, f"(a) GitHub Stars & Forks Across {len(rr)} Public Repos", 40, nc=2, fs=8.0)

    fl = 2.2
    if any(r["f"] == 0 for r in rr):
        a2.axhline(fl, ls=":", lw=0.85, c="#94a3b8", zorder=1)
        a2.text(85000, fl * 1.08, "0-fork floor (exact forks = 0)", ha="right", va="bottom", size=6.6, c="#64748b", style="italic")
    for rt, lb, rx in ((0.5, "50% F/S", 2400), (0.2, "20% F/S", 54000), (0.1, "10% F/S", 54000)):
        x0 = max(10.0, 2.7 / rt)
        a2.plot([x0, 75000.0], [x0 * rt, 75000.0 * rt], ls="--", lw=0.8, c="#cbd5e1", zorder=1)
        a2.text(rx, rx * rt * 1.15, lb, size=6.9, c="#64748b", rotation=32, ha="right")
    arw = {"arrowstyle": "-", "color": "#94a3b8", "lw": 0.65, "shrinkA": 2, "shrinkB": 3}
    for r in rr:
        col, mk = CAT[r["c"]]
        s, f = r["s"], r["f"]
        yp, lbl = (f, r["nm"]) if f > 0 else (fl, f"{r['nm']} (0 forks)")
        a2.scatter(s, yp, s=62, color=col if f else "#fff", marker=mk, ec="#fff" if f else col, lw=0.9 if f else 1.6, zorder=4)
        dx, dy, hc = OFF.get(r["id"], (8, 6, "l"))
        a2.annotate(lbl, (s, yp), (dx, dy), textcoords="offset points", size=7.2, weight="semibold", ha=HA[hc], va="center", arrowprops=arw, zorder=5)
    glog(a2, "both")
    a2.set(xlim=(8, 95000), ylim=(1.5, 16000), xlabel="GitHub Stars (Log10)", ylabel="GitHub Forks (Log10)")
    top(a2, "(b) Stars vs Forks by Git Presence Category", 40, [Line2D([0], [0], marker=m, color="w", label=k, markerfacecolor=c, markersize=7.0) for k, (c, m) in CAT.items()], 3, 7.2)

    fig.subplots_adjust(top=0.81, bottom=0.10, wspace=0.20)
    save(fig, "chart_08_popularity_stars_forks_log.png", "PostgreSQL Clustering Ecosystem Popularity: Stars & Forks (Log10)",
         f"{len(rr)} public GitHub repos (* = mirror of git.postgresql.org; forks=0 on floor); 3 proprietary engines (EDB PGD, Aurora Limitless, Spanner/AlloyDB) excluded")


def chart_09(rows: list[dict]) -> None:
    rr = sorted(rows, key=lambda r: (r["m"], r["t"]), reverse=True)
    ys, h, hh = list(range(len(rr))), 0.38, 0.19
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16.8, 8.9), sharey=True, gridspec_kw={"width_ratios": [1.14, 1.0]})

    tot, c12 = [r["t"] for r in rr], [r["m"] for r in rr]
    a1.barh([y - hh for y in ys], tot, h, color="#334155", **BKW)
    a1.barh([y + hh for y in ys], [v or NAN for v in c12], h, color=["#059669" if v >= 30 else "#d97706" for v in c12], **BKW)
    for y, t, m in zip(ys, tot, c12):
        a1.text(t * 1.15, y - hh, f"{t:,}", va="center", size=6.9, color="#1e293b", weight="semibold")
        if m > 0:
            a1.text(m * 1.15, y + hh, f"{m:,}/12m", va="center", size=6.7, color="#065f46" if m >= 30 else "#92400e", weight="bold")
        else:
            a1.plot(1.25, y + hh, "rx", ms=5.5, mew=1.6)
            a1.text(1.85, y + hh, "0 commits/12m (INACTIVE)", va="center", size=6.8, color="#b91c1c", weight="bold")
    h_setup(a1, ys, [r["nm"] for r in rr], (1, 1.4e6), "Commits (Log10 Scale)")
    top(a1, "(a) All-Time vs 12-Month Commit Velocity (Sorted by 12m)", 28,
        [Patch(fc=c, label=l) for c, l in (("#334155", "All-Time Commits"), ("#059669", "12m Active (>=30)"), ("#d97706", "12m Low (1-29)"))], 3, 7.5)

    a2.barh(ys, [r["n"] for r in rr], 0.62, color=[VIT[r["v"]] for r in rr], **BKW)
    for y, r in zip(ys, rr):
        cnt, v = r["n"], r["v"]
        a2.text(max(cnt, 1) * 1.15, y, f"{cnt:,}{'*' if r['id'] == 'postgres-core' else ''} | {r['p']} [{v}]", va="center", size=7.0, color=VIT[v], weight="bold")
    glog(a2, "x")
    a2.set(xlim=(1, 75000), xlabel="Contributors (Log10 Scale)")
    top(a2, "(b) Contributors, Last Push & Maintenance Vitality", 28, [Patch(fc=c, ec="#fff", label=k) for k, c in VIT.items()], 4, 7.5)

    fig.subplots_adjust(top=0.83, bottom=0.10, wspace=0.06)
    save(fig, "chart_09_popularity_commits_activity_log.png", "PostgreSQL Ecosystem Development Velocity & Maintenance Vitality (Log10)",
         f"{len(rr)} public GitHub repos | 12m cadence: Active (>=30/yr), Maintenance (1-29/yr), Dormant/Archived-like (0/12m); * = mirror committers")


def chart_10() -> None:
    idx: dict[str, dict] = defaultdict(dict)
    for p in [*(RES / n for n in PG17), RES / "benchmark_pg18.csv"]:
        with p.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                idx[r["topology"].strip()].setdefault(r["suite"].strip(), r)

    fig, axes = plt.subplots(2, 6, figsize=(18.8, 9.8), sharey="row", sharex="col")
    xs, w = list(range(len(PAIRS))), 0.37
    ht = {(4, 4): ("uuidv7\n3.30x", 11.5), (3, 2): ("3.20x", 6.2), (3, 3): ("1.98x", 7.8), (4, 3): ("1.85x", 6.2), (2, 3): ("1.73x", 6.4), (4, 2): ("1.35x", 6.0), (5, 3): ("1.29x", 6.4)}
    hp = {(4, 4): ("-83%\nuuidv7", 6.2), (3, 2): ("-79%", 5.4), (4, 3): ("-69%", 5.4), (3, 3): ("-59%", 5.2), (2, 3): ("-56%", 5.4), (4, 2): ("-32%", 5.2)}
    pill = {"boxstyle": "round,pad=0.22", "fc": "#dcfce7", "ec": "#16a34a", "lw": 0.75}
    vkw = {"ha": "center", "va": "bottom", "rotation": 90}

    for ci, (su, slab) in enumerate(SUITES):
        for ri, (fld, hero, ylo, yhi, mul) in enumerate((("tps", ht, 18.0, 420000.0, 1.18), ("lat_p95_ms", hp, 0.14, 2600.0, 1.22))):
            ax = axes[ri, ci]
            v17 = [fnum(idx[a].get(su, {}).get(fld)) for _, a, _ in PAIRS]
            v18 = [fnum(idx[b].get(su, {}).get(fld)) for _, _, b in PAIRS]
            ax.bar([x - w / 2 for x in xs], [v or NAN for v in v17], w * 0.92, color="#64748b", label="PostgreSQL 17.11", **BKW)
            ax.bar([x + w / 2 for x in xs], [v or NAN for v in v18], w * 0.92, color="#0284c7", label="PostgreSQL 18.6", **BKW)
            for i, (a, b) in enumerate(zip(v17, v18)):
                if a <= 0 and b <= 0:
                    ax.text(i, ylo * 1.7, "N/A\n(1n)", ha="center", va="bottom", size=6.7, color="#94a3b8", weight="bold")
                    continue
                if a > 0:
                    ax.text(i - w / 2, a * mul, fval(a), size=6.1, color="#334155", **vkw)
                if b > 0:
                    ax.text(i + w / 2, b * mul, fval(b), size=6.2, color="#0369a1", weight="bold", **vkw)
                if (ci, i) in hero:
                    tag, ym = hero[(ci, i)]
                    ax.text(i, max(a, b) * ym, tag, ha="center", va="bottom", size=6.5, weight="bold", color="#065f46", bbox=pill)
            glog(ax, "y")
            ax.set(xlim=(-0.62, 4.62), ylim=(ylo, yhi), xticks=xs)
            if ri == 0:
                ax.set_title(slab, size=9.4, pad=8)
                ax.tick_params(axis="x", labelbottom=False)
            else:
                ax.set_xticklabels([p[0] for p in PAIRS], size=7.2, weight="semibold")
            if ci == 0:
                ax.set_ylabel("Throughput TPS (Log10)" if ri == 0 else "p95 Latency ms (Log10)", size=9.1)

    hnd, _ = axes[0, 0].get_legend_handles_labels()
    hnd.append(Patch(fc="#dcfce7", ec="#16a34a", label="PG 18.6 Hero Gain (TPS speedup / p95 drop)"))
    fig.legend(handles=hnd, loc="upper center", bbox_to_anchor=(0.5, 0.915), ncol=3, fontsize=8.4)
    fig.subplots_adjust(top=0.84, bottom=0.10, hspace=0.14, wspace=0.14)
    save(fig, "chart_10_pg18_vs_pg17_log.png", "PostgreSQL 18.6 vs PostgreSQL 17.11 Head-to-Head (5 Native Topologies, Log10)",
         "Top: Log10 TPS (higher is better) | Bottom: Log10 p95 Latency ms (lower is better) | Native uuidv7() & substream=p drive 1.7x-3.3x gains",
         "LightPath | ClusterPostgreSQL-Series | Empirical Docker PoC: PG 18.6 (87 rows) vs PG 17.11")


def main() -> None:
    pop = load_pop()
    chart_08(pop)
    chart_09(pop)
    chart_10()
    print(f"Rendered 3 Wave-3 charts ({len(pop)} GitHub repos + 5 PG18 vs PG17 topologies).")


if __name__ == "__main__":
    main()

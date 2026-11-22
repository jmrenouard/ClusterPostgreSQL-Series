"""Shared 18-topology palette, CSV loaders, and Log10 chart styling helpers."""

from __future__ import annotations

import csv
import math
import pathlib
from collections import defaultdict
from collections.abc import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

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
BKW, NAN = {"ec": "#fff", "lw": 0.4}, float("nan")
DEFAULT_FOOT = "LightPath | ClusterPostgreSQL-Series | 17-Topology Benchmarks (PG 17/18 + YT)"


def fnum(v: object, default: float = 0.0) -> float:
    """Parse finite float or return default."""
    try:
        x = float(str(v).strip())
        return x if math.isfinite(x) else default
    except (ValueError, TypeError):
        return default


def inum(v: object) -> int | None:
    """Parse finite integer metric, returning None for empty, N/A, or non-finite values."""
    s = str(v or "").strip()
    if not s or s.upper() == "N/A":
        return None
    x = fnum(s, math.nan)
    return int(x) if math.isfinite(x) else None


def fval(v: float) -> str:
    """Format throughput/count metric compactly for bar labels."""
    if v <= 0:
        return "0"
    if v >= 1e6:
        return f"{v / 1e6:.2f}M"
    if v >= 1e4:
        return f"{v / 1e3:.1f}k"
    return f"{v / 1e3:.2f}k" if v >= 1e3 else (f"{v:.0f}" if v >= 100 else (f"{v:.1f}" if v >= 10 else f"{v:.2f}"))


def fms(v: float) -> str:
    """Format millisecond latency compactly (switching to seconds at >= 1000 ms)."""
    return f"{v / 1e3:.2f}s" if v >= 1e3 else f"{fval(v)}ms"


def ftick(x: float, _p: int) -> str:
    """Format Log10 axis tick values without trailing zeroes."""
    if x <= 0:
        return "0"
    for lim, sfx in ((1e6, "M"), (1e3, "k")):
        if x >= lim:
            v = x / lim
            return f"{int(v)}{sfx}" if abs(v - round(v)) < 1e-6 else f"{v:g}{sfx}"
    return f"{int(x)}" if x >= 1 and abs(x - round(x)) < 1e-6 else f"{x:g}"


def load_csv_idx(
    names: Iterable[str] = CSVS,
    overwrite: bool = False,
) -> tuple[dict[str, dict[str, dict[str, str]]], set[str]]:
    """Load benchmark CSVs into idx[topology][suite] and collect suite names."""
    idx: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    su: set[str] = set()
    for name in names:
        p = RES_DIR / name
        if p.is_file():
            with p.open(encoding="utf-8", newline="") as fh:
                for r in csv.DictReader(fh):
                    t, s = r["topology"].strip(), r["suite"].strip()
                    if overwrite:
                        idx[t][s] = r
                    else:
                        idx[t].setdefault(s, r)
                    su.add(s)
    return idx, su


def resolve_e1(suites: Iterable[str], default: str = "") -> str:
    """Resolve Sysbench OLTP RW suite key across E1_ and legacy E_ naming."""
    s = set(suites)
    for key in ("E1_sysbench_oltp_rw", "E_sysbench_oltp_rw"):
        if key in s:
            return key
    return default


def log_axis(ax: plt.Axes, axis: str = "y") -> None:
    """Configure Log10 scale, tick formatter, and major/minor grid lines."""
    if axis in ("x", "both"):
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(FuncFormatter(ftick))
    if axis in ("y", "both"):
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(FuncFormatter(ftick))
    ax.grid(True, "major", axis, color="#cbd5e1", lw=0.8, alpha=0.8)
    ax.grid(True, "minor", axis, color="#e2e8f0", lw=0.5, ls=":", alpha=0.7)


def save_fig(
    fig: plt.Figure,
    fn: str,
    ti: str,
    sub: str,
    foot: str = DEFAULT_FOOT,
    sub_y: float = 0.938,
    foot_y: float = 0.01,
) -> None:
    """Render shared LightPath title, subtitle, and footer, then save 180-DPI PNG."""
    fig.suptitle(ti, fontsize=12.4, weight="bold", color="#0f172a", y=0.985)
    fig.text(0.5, sub_y, sub, ha="center", va="top", fontsize=8.4, color="#475569")
    fig.text(0.99, foot_y, foot, ha="right", va="bottom", fontsize=7.2, color="#64748b", style="italic")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / fn, dpi=180, bbox_inches="tight", facecolor="#fff")
    plt.close(fig)

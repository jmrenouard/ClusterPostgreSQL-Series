#!/usr/bin/env python3
"""Build offline-capable JS data bundles for the HTML Benchmark Explorer."""

from __future__ import annotations

import csv
import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
RES = ROOT / "results"
DASH = ROOT / "dashboard"

BENCH_CSVS = (
    "benchmark_summary.csv",
    "benchmark_extended_workloads.csv",
    "benchmark_wan_sweep.csv",
    "benchmark_concurrency_sweep.csv",
)
MATRIX_CSV = RES / "functional_limits_matrix.csv"
EXT_MATRIX_CSV = RES / "extended_functional_matrix.csv"
PG18_BENCH_CSV = RES / "benchmark_pg18.csv"
PG18_MATRIX_CSV = RES / "functional_limits_pg18.csv"
YT_BENCH_CSV = RES / "benchmark_yt_cluster.csv"
YT_MATRIX_CSV = RES / "functional_limits_yt_cluster.csv"
POPULARITY_CSV = RES / "project_popularity.csv"

MAX_SHARD_BYTES = 10500
POP_NUM_COLS = {
    "account_public_repos",
    "stars",
    "forks",
    "watchers",
    "open_issues",
    "total_commits",
    "commits_12m",
    "contributors",
}

BENCH_FIELDS = [
    "topology",
    "suite",
    "clients",
    "duration_s",
    "tps",
    "qps",
    "lat_avg_ms",
    "lat_p95_ms",
    "tx_committed",
    "retries_40001",
    "convergence_status",
    "balance_drift",
]


def parse_num(val: str) -> float | int | str:
    """Convert numeric strings cleanly while preserving N/A and labels."""
    s = (val or "").strip()
    if not s or s.upper() == "N/A":
        return ""
    try:
        f = float(s)
        if f.is_integer() and "." not in s:
            return int(f)
        return round(f, 3)
    except ValueError:
        return s


def read_csv_rows(path: pathlib.Path) -> list[dict[str, str]]:
    """Read CSV file into list of dicts if present."""
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def pack_bench_row(r: dict[str, str]) -> list[object]:
    """Pack one benchmark CSV dict into compact BENCH_FIELDS list."""
    return [
        r.get("topology", "").strip(),
        r.get("suite", "").strip(),
        parse_num(r.get("clients", "")),
        parse_num(r.get("duration_s", "")),
        parse_num(r.get("tps", "")),
        parse_num(r.get("qps", "")),
        parse_num(r.get("lat_avg_ms", "")),
        parse_num(r.get("lat_p95_ms", "")),
        parse_num(r.get("tx_committed", "")),
        parse_num(r.get("retries_40001", "")),
        r.get("convergence_status", "").strip(),
        parse_num(r.get("balance_drift", "0")),
    ]


def load_bench_rows(paths: tuple[pathlib.Path, ...]) -> list[list[object]]:
    """Merge benchmark CSV paths deduplicated by (topology, suite)."""
    seen: set[tuple[str, str]] = set()
    out: list[list[object]] = []
    for path in paths:
        for r in read_csv_rows(path):
            topo = r.get("topology", "").strip()
            suite = r.get("suite", "").strip()
            key = (topo, suite)
            if not topo or not suite or key in seen:
                continue
            seen.add(key)
            out.append(pack_bench_row(r))
    return out


def dump_js_chunk(var_name: str, payload: object, header: str) -> str:
    """Serialize compact deterministic ASCII JS assignment."""
    body = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    return f"/* {header} */\nwindow.{var_name}={body};\n"


def shard_rows(rows: list[list[object]], max_bytes: int) -> list[list[list[object]]]:
    """Split row arrays into up to 3 balanced shards under max_bytes each."""
    shards: list[list[list[object]]] = [[], [], []]
    idx = 0
    cur_bytes = 256
    for row in rows:
        r_len = len(json.dumps(row, ensure_ascii=True, separators=(",", ":"))) + 1
        if idx < 2 and shards[idx] and cur_bytes + r_len > max_bytes:
            idx += 1
            cur_bytes = 128
        shards[idx].append(row)
        cur_bytes += r_len
    return shards


def emit_bench_bundles(
    rows: list[list[object]],
    pg18_rows: list[list[object]],
    yt_rows: list[list[object]],
    yt_matrix: list[dict[str, str]],
    pop_count: int,
) -> list[pathlib.Path]:
    """Emit V2 shards (data_bench{,_2,_3}.js), PG 18.6, and YT Cluster bundles (< 13.5 KB each)."""
    topos = sorted({str(r[0]) for r in rows if r[0] != "pgedge-delta-apply"})
    pg18_topos = sorted({str(r[0]) for r in pg18_rows})
    yt_topos = sorted({str(r[0]) for r in yt_rows})
    suites = sorted({str(r[1]) for r in rows + pg18_rows + yt_rows})
    meta = {
        "cols": BENCH_FIELDS,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "row_count": len(rows),
        "topology_count": len(topos),
        "pg18_row_count": len(pg18_rows),
        "pg18_topology_count": len(pg18_topos),
        "yt_row_count": len(yt_rows),
        "yt_topology_count": len(yt_topos),
        "total_row_count": len(rows) + len(pg18_rows) + len(yt_rows),
        "total_topology_count": len(topos) + len(pg18_topos) + len(yt_topos),
        "popularity_count": pop_count,
        "suite_count": len(suites),
    }
    shards = shard_rows(rows, MAX_SHARD_BYTES)
    p1 = DASH / "data_bench.js"
    p2 = DASH / "data_bench_2.js"
    p3 = DASH / "data_bench_3.js"
    p18 = DASH / "data_bench_pg18.js"
    pyt = DASH / "data_bench_yt.js"

    p1_txt = (
        dump_js_chunk("LP_BENCH_META", meta, "Auto-generated by scripts/build_dashboard.py")
        + "\n\n\n\n"
        + f"window.LP_BENCH_ROWS_1={json.dumps(shards[0], ensure_ascii=True, separators=(',', ':'))};\n"
    )
    p2_txt = dump_js_chunk("LP_BENCH_ROWS_2", shards[1], "Benchmark shard 2 (build_dashboard.py)")
    p3_txt = dump_js_chunk("LP_BENCH_ROWS_3", shards[2], "Benchmark shard 3 (build_dashboard.py)")
    p18_txt = dump_js_chunk("LP_BENCH_ROWS_PG18", pg18_rows, "PostgreSQL 18.6 benchmark rows (87 rows)")
    yt_mat_json = json.dumps(pack_matrix(yt_matrix), ensure_ascii=True, separators=(",", ":"))
    pyt_txt = (
        dump_js_chunk("LP_BENCH_ROWS_YT", yt_rows, "YT Cluster 1.21.3 benchmark & limits bundle")
        + "\n\n\n\n"
        + f"window.LP_MATRIX_YT={yt_mat_json};\n"
    )

    for p, txt in ((p1, p1_txt), (p2, p2_txt), (p3, p3_txt), (p18, p18_txt), (pyt, pyt_txt)):
        p.write_text(txt, encoding="utf-8", newline="\n")
    return [p1, p2, p3, p18, pyt]


def pack_matrix(rows: list[dict[str, str]], num_cols: set[str] | None = None) -> dict[str, object]:
    """Pack CSV dict rows into compact {cols, rows} tabular form."""
    if not rows:
        return {"cols": [], "rows": []}
    cols = [k for k in rows[0].keys() if k and k != "report_source"]
    nums = num_cols or set()
    packed = [[parse_num(r.get(c) or "") if c in nums else (r.get(c) or "").strip() for c in cols] for r in rows]
    return {"cols": cols, "rows": packed}


def emit_matrix_and_pop_bundles(
    core_rows: list[dict[str, str]],
    ext_rows: list[dict[str, str]],
    pg18_rows: list[dict[str, str]],
    pop_rows: list[dict[str, str]],
) -> list[pathlib.Path]:
    """Emit L1-L8, T11-T18, PG 18.6 matrix, and GitHub ecosystem popularity bundles."""
    specs = (
        (DASH / "data_matrix.js", "LP_MATRIX_CORE", pack_matrix(core_rows), "Functional limits matrix (L1-L8)"),
        (DASH / "data_matrix_ext.js", "LP_MATRIX_EXT", pack_matrix(ext_rows), "Extended resilience matrix (T11-T18)"),
        (DASH / "data_matrix_pg18.js", "LP_MATRIX_PG18", pack_matrix(pg18_rows), "PostgreSQL 18.6 capabilities & limits matrix"),
        (DASH / "data_popularity.js", "LP_POPULARITY", pack_matrix(pop_rows, POP_NUM_COLS), "GitHub ecosystem popularity & vitality telemetry"),
    )
    out: list[pathlib.Path] = []
    for path, var, payload, header in specs:
        path.write_text(dump_js_chunk(var, payload, header), encoding="utf-8", newline="\n")
        out.append(path)
    return out


def main() -> None:
    """Build all offline JS data bundles for dashboard/."""
    DASH.mkdir(parents=True, exist_ok=True)
    bench_rows = load_bench_rows(tuple(RES / n for n in BENCH_CSVS))
    pg18_bench = load_bench_rows((PG18_BENCH_CSV,))
    yt_bench = load_bench_rows((YT_BENCH_CSV,))
    core_matrix = read_csv_rows(MATRIX_CSV)
    ext_matrix = read_csv_rows(EXT_MATRIX_CSV)
    pg18_matrix = read_csv_rows(PG18_MATRIX_CSV)
    yt_matrix = read_csv_rows(YT_MATRIX_CSV)
    pop_rows = read_csv_rows(POPULARITY_CSV)
    emitted = (
        emit_bench_bundles(bench_rows, pg18_bench, yt_bench, yt_matrix, len(pop_rows))
        + emit_matrix_and_pop_bundles(core_matrix, ext_matrix, pg18_matrix, pop_rows)
    )
    print(
        f"Built bundles ({len(bench_rows)} V2 + {len(pg18_bench)} PG18 + {len(yt_bench)} YT bench, "
        f"{len(core_matrix)} L1-L8, {len(ext_matrix)} T11-T18, "
        f"{len(pg18_matrix)} PG18 + {len(yt_matrix)} YT matrix, {len(pop_rows)} popularity):"
    )
    for p in emitted:
        sz = p.stat().st_size
        print(f"  {p.relative_to(ROOT)}: {sz} bytes")
        if sz >= 13500:
            raise SystemExit(f"ERROR: {p.name} exceeds 13,500 bytes ({sz})")


if __name__ == "__main__":
    main()

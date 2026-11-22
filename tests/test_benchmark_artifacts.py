"""Automated validation tests for LightPath logos, Log10 charts, CSVs, and dashboard."""

from __future__ import annotations

import csv
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from collections import defaultdict
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CHARTS = ASSETS / "charts"
DASH = ROOT / "dashboard"
SCRIPTS = ROOT / "scripts"
RESULTS = ROOT / "results"

CORE_TOPOLOGIES = {
    "pg17-standalone",
    "pg17-async-streaming",
    "pg17-sync-streaming",
    "pg17-logical",
    "pg-birep",
    "pgedge",
    "bucardo",
    "citus",
    "yugabyte",
    "cockroach",
}

PG18_TOPOLOGIES = {
    "pg18-standalone",
    "pg18-async-streaming",
    "pg18-sync-streaming",
    "pg18-logical",
    "pg18-birep",
}

YT_TOPOLOGIES = {
    "yt-cluster",
    "yt-cluster-async",
}

OPT_TOPOLOGIES = CORE_TOPOLOGIES | PG18_TOPOLOGIES | YT_TOPOLOGIES | {"cockroach-rc"}

BENCH_CSVS = (
    "benchmark_summary.csv",
    "benchmark_extended_workloads.csv",
    "benchmark_wan_sweep.csv",
    "benchmark_concurrency_sweep.csv",
)

MATRIX_CSVS = (
    "functional_limits_matrix.csv",
    "extended_functional_matrix.csv",
)

EXPECTED_CHARTS = (
    "chart_01_tps_log_all_suites.png",
    "chart_02_latency_log_all_suites.png",
    "chart_03_concurrency_sweep_log.png",
    "chart_04_wan_netem_sweep_log.png",
    "chart_05_sysbench_profile_log.png",
    "chart_06_streaming_vs_logical_vs_mm.png",
    "chart_07_integrity_vs_throughput.png",
    "chart_08_popularity_stars_forks_log.png",
    "chart_09_popularity_commits_activity_log.png",
    "chart_10_pg18_vs_pg17_log.png",
    "chart_11_yt_cluster_vs_multimaster_log.png",
    "chart_12_baseline_vs_optimized_log.png",
    "chart_13_optimized_all_topologies_log.png",
)

EXPECTED_DASH_FILES = (
    "index.html",
    "styles.css",
    "pacelc.css",
    "charts.js",
    "popularity.js",
    "matrix.js",
    "opt.js",
    "app.js",
    "data_pacelc.js",
    "pacelc_engine.js",
    "pacelc_ui.js",
    "data_bench.js",
    "data_bench_2.js",
    "data_bench_3.js",
    "data_bench_pg18.js",
    "data_bench_yt.js",
    "data_bench_opt_1.js",
    "data_bench_opt_2.js",
    "data_bench_opt_3.js",
    "data_bench_opt_4.js",
    "data_matrix.js",
    "data_matrix_ext.js",
    "data_matrix_pg18.js",
    "data_popularity.js",
)


class TestBenchmarkArtifacts(unittest.TestCase):
    """Verify LightPath SVG branding, 13 Log10 PNG charts, offline dashboard, and CSVs."""

    def test_lightpath_svg_logos(self) -> None:
        """Validate official dark and light LightPath supporter SVG logos exist and parse."""
        for fname in ("lightpath-logo-dark.svg", "lightpath-logo-light.svg"):
            path = ASSETS / fname
            self.assertTrue(path.is_file(), f"Missing logo: {path.relative_to(ROOT)}")
            size = path.stat().st_size
            self.assertGreater(size, 500, f"Logo unexpectedly small: {fname}")
            self.assertLess(size, 12000, f"Logo exceeds 12 KB cap: {fname} ({size} B)")
            root = ET.fromstring(path.read_text(encoding="utf-8"))
            self.assertTrue(root.tag.endswith("svg"), f"Invalid SVG root in {fname}")

    def test_project_logo_and_supporter_positioning(self) -> None:
        """Verify dedicated ClusterPostgreSQL-Series PNG logos and LightPath supporter labels."""
        png_magic = b"\x89PNG\r\n\x1a\n"
        for fname in ("clusterpostgresql-series-logo.png", "clusterpostgresql-series-icon.png"):
            path = ASSETS / fname
            self.assertTrue(path.is_file(), f"Missing project logo: {path.relative_to(ROOT)}")
            raw = path.read_bytes()
            self.assertTrue(raw.startswith(png_magic), f"Invalid PNG header: {fname}")
            self.assertGreater(len(raw), 10000, f"Project logo unexpectedly small: {fname}")

        readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("assets/clusterpostgresql-series-logo.png", readme_en[:400])
        self.assertIn("Supported by", readme_en)

        readme_fr = (ROOT / "README.fr.md").read_text(encoding="utf-8")
        self.assertIn("assets/clusterpostgresql-series-logo.png", readme_fr[:400])
        self.assertIn("Soutenu par", readme_fr)

    def test_ten_png_charts_valid(self) -> None:
        """Verify all 13 generated PNG charts (01-13) exist with valid PNG headers."""
        png_magic = b"\x89PNG\r\n\x1a\n"
        for fname in EXPECTED_CHARTS:
            path = CHARTS / fname
            self.assertTrue(path.is_file(), f"Missing chart: {path.relative_to(ROOT)}")
            raw = path.read_bytes()
            self.assertTrue(raw.startswith(png_magic), f"Invalid PNG header: {fname}")
            self.assertGreater(len(raw), 10000, f"Chart unexpectedly small: {fname}")

    def test_dashboard_structure_and_offline_features(self) -> None:
        """Verify offline dashboard assets, 15-topology PG17+PG18 bundles, Popularity tab, and logo."""
        for fname in EXPECTED_DASH_FILES:
            path = DASH / fname
            self.assertTrue(path.is_file(), f"Missing dashboard file: {fname}")

        html = (DASH / "index.html").read_text(encoding="utf-8")
        for token in (
            "../assets/clusterpostgresql-series-icon.png",
            "../assets/lightpath-logo-dark.svg",
            "Supported by",
            "Soutenu par",
            'data-scale="log"',
            'data-scale="linear"',
            'id="topo-pills"',
            'data-preset="stream_logical"',
            'data-preset="pg18_vs_pg17"',
            'data-preset="yt_vs_mm"',
            'data-mtab="pg18"',
            'data-mtab="yt"',
            'data-tab="popularity"',
            'data-tab="pacelc"',
            'id="panel-pacelc"',
            'data-lang="en"',
            'data-lang="fr"',
            'data-dataset="baseline"',
            'data-dataset="optimized"',
            'data-dataset="compare"',
            'id="btn-export"',
            "data_bench.js",
            "data_bench_2.js",
            "data_bench_3.js",
            "data_bench_pg18.js",
            "data_bench_yt.js",
            "data_bench_opt_1.js",
            "data_bench_opt_2.js",
            "data_bench_opt_3.js",
            "data_bench_opt_4.js",
            "data_matrix.js",
            "data_matrix_ext.js",
            "data_matrix_pg18.js",
            "data_popularity.js",
            "pacelc.css",
            "data_pacelc.js",
            "pacelc_engine.js",
            "pacelc_ui.js",
            "charts.js",
            "popularity.js",
            "matrix.js",
            "opt.js",
            "app.js",
        ):
            self.assertIn(token, html, f"Missing expected dashboard token: {token}")

        cdn_refs = re.findall(r"<(?:script|link)[^>]+(?:src|href)=[\"']https?://", html, re.I)
        self.assertEqual(cdn_refs, [], f"External CDN dependency detected: {cdn_refs}")

        bench_js = (DASH / "data_bench.js").read_text(encoding="utf-8")
        m_meta = re.search(r"window\.LP_BENCH_META=(\{.*?\});", bench_js)
        self.assertIsNotNone(m_meta, "Missing LP_BENCH_META in data_bench.js")
        meta = json.loads(m_meta.group(1))
        self.assertEqual(meta["topology_count"], 10)
        self.assertEqual(meta["pg18_topology_count"], 5)
        self.assertEqual(meta["yt_topology_count"], 2)
        self.assertEqual(meta["total_topology_count"], 17)
        self.assertEqual(meta["pg18_row_count"], 87)
        self.assertEqual(meta["yt_row_count"], 36)
        self.assertEqual(meta["total_row_count"], 301)
        self.assertEqual(meta["popularity_count"], 22)
        self.assertGreaterEqual(meta["row_count"], 170)

        bench_shards: list[list[object]] = []
        for fname, var in (("data_bench.js", "LP_BENCH_ROWS_1"), ("data_bench_2.js", "LP_BENCH_ROWS_2"), ("data_bench_3.js", "LP_BENCH_ROWS_3")):
            sh_txt = (DASH / fname).read_text(encoding="utf-8")
            m_sh = re.search(rf"window\.{var}=(\[.*\]);", sh_txt)
            self.assertIsNotNone(m_sh, f"Missing {var} in {fname}")
            rows_chunk = json.loads(m_sh.group(1))
            self.assertGreater(len(rows_chunk), 0, f"Empty shard stub in {fname}")
            bench_shards.extend(rows_chunk)
        self.assertEqual(len(bench_shards), meta["row_count"])

        pg18_js = (DASH / "data_bench_pg18.js").read_text(encoding="utf-8")
        m18 = re.search(r"window\.LP_BENCH_ROWS_PG18=(\[.*\]);", pg18_js)
        self.assertIsNotNone(m18, "Missing LP_BENCH_ROWS_PG18 in data_bench_pg18.js")
        self.assertEqual(len(json.loads(m18.group(1))), 87)

        yt_js = (DASH / "data_bench_yt.js").read_text(encoding="utf-8")
        myt_b = re.search(r"window\.LP_BENCH_ROWS_YT=(\[.*?\]);", yt_js)
        self.assertIsNotNone(myt_b, "Missing LP_BENCH_ROWS_YT in data_bench_yt.js")
        self.assertEqual(len(json.loads(myt_b.group(1))), 36)
        myt_m = re.search(r"window\.LP_MATRIX_YT=(\{.*?\});", yt_js)
        self.assertIsNotNone(myt_m, "Missing LP_MATRIX_YT in data_bench_yt.js")
        self.assertEqual(len(json.loads(myt_m.group(1))["rows"]), 1)

        opt1_js = (DASH / "data_bench_opt_1.js").read_text(encoding="utf-8")
        m_opt_meta = re.search(r"window\.LP_BENCH_OPT_META=(\{.*?\});", opt1_js)
        self.assertIsNotNone(m_opt_meta, "Missing LP_BENCH_OPT_META in data_bench_opt_1.js")
        opt_meta = json.loads(m_opt_meta.group(1))
        self.assertEqual(opt_meta["row_count"], 318)
        self.assertEqual(opt_meta["topology_count"], 18)
        self.assertEqual(opt_meta["pg_scale"], 20)
        self.assertEqual(opt_meta["suite_count"], 18)
        opt_rows: list[list[object]] = []
        for idx in range(1, 5):
            sh_txt = (DASH / f"data_bench_opt_{idx}.js").read_text(encoding="utf-8")
            m_sh = re.search(r"window\.LP_BENCH_OPT_ROWS=(?:\(window\.LP_BENCH_OPT_ROWS\|\|\[\]\)\.concat\()?(\[.*\])\)?;", sh_txt)
            self.assertIsNotNone(m_sh, f"Missing LP_BENCH_OPT_ROWS in data_bench_opt_{idx}.js")
            opt_rows.extend(json.loads(m_sh.group(1)))
        self.assertEqual(len(opt_rows), 318)
        self.assertEqual(len({r[0] for r in opt_rows}), 18)

        for fname, var, exp_len in (
            ("data_matrix.js", "LP_MATRIX_CORE", 10),
            ("data_matrix_ext.js", "LP_MATRIX_EXT", 10),
            ("data_matrix_pg18.js", "LP_MATRIX_PG18", 5),
            ("data_popularity.js", "LP_POPULARITY", 22),
        ):
            txt = (DASH / fname).read_text(encoding="utf-8")
            m = re.search(rf"window\.{var}=(\{{.*\}});", txt)
            self.assertIsNotNone(m, f"Missing {var} in {fname}")
            pack = json.loads(m.group(1))
            self.assertEqual(len(pack["rows"]), exp_len, f"Expected {exp_len} rows in {fname}")

    def test_all_benchmark_and_matrix_csvs_integrity(self) -> None:
        """Confirm V2, PG 18.6, and ecosystem popularity CSVs pass schema and row integrity."""
        required = {"topology", "suite", "tps", "lat_avg_ms", "lat_p95_ms", "convergence_status", "balance_drift"}
        seen_topos: set[str] = set()
        seen_pairs: set[tuple[str, str]] = set()
        for name in BENCH_CSVS:
            path = RESULTS / name
            self.assertTrue(path.is_file(), f"Missing benchmark CSV: {name}")
            with path.open(encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            self.assertGreater(len(rows), 20, f"Too few rows in {name}")
            self.assertTrue(required.issubset(rows[0].keys()), f"Missing cols in {name}")
            for r in rows:
                t, s = r["topology"].strip(), r["suite"].strip()
                self.assertTrue(t and s)
                self.assertGreater(float(r["tps"]), 0.0)
                seen_topos.add(t)
                seen_pairs.add((t, s))

        self.assertTrue(CORE_TOPOLOGIES.issubset(seen_topos), f"Missing topologies: {CORE_TOPOLOGIES - seen_topos}")
        self.assertGreaterEqual(len(seen_pairs), 170)

        for name in MATRIX_CSVS:
            path = RESULTS / name
            self.assertTrue(path.is_file(), f"Missing matrix CSV: {name}")
            with path.open(encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual({r["topology"].strip() for r in rows}, CORE_TOPOLOGIES)

        pg18_b = RESULTS / "benchmark_pg18.csv"
        self.assertTrue(pg18_b.is_file(), "Missing benchmark_pg18.csv")
        with pg18_b.open(encoding="utf-8", newline="") as fh:
            b18_rows = list(csv.DictReader(fh))
        self.assertEqual(len(b18_rows), 87)
        self.assertTrue(required.issubset(b18_rows[0].keys()))
        self.assertEqual({r["topology"].strip() for r in b18_rows}, PG18_TOPOLOGIES)
        for r in b18_rows:
            self.assertGreater(float(r["tps"]), 0.0)

        pg18_m = RESULTS / "functional_limits_pg18.csv"
        self.assertTrue(pg18_m.is_file(), "Missing functional_limits_pg18.csv")
        with pg18_m.open(encoding="utf-8", newline="") as fh:
            m18_rows = list(csv.DictReader(fh))
        self.assertEqual(len(m18_rows), 5)
        self.assertEqual({r["topology"].strip() for r in m18_rows}, PG18_TOPOLOGIES)

        yt_b = RESULTS / "benchmark_yt_cluster.csv"
        self.assertTrue(yt_b.is_file(), "Missing benchmark_yt_cluster.csv")
        with yt_b.open(encoding="utf-8", newline="") as fh:
            yt_rows = list(csv.DictReader(fh))
        self.assertEqual(len(yt_rows), 36)
        self.assertTrue(required.issubset(yt_rows[0].keys()))
        self.assertEqual({r["topology"].strip() for r in yt_rows}, YT_TOPOLOGIES)
        for topo in YT_TOPOLOGIES:
            self.assertEqual(len({r["suite"].strip() for r in yt_rows if r["topology"].strip() == topo}), 18)
        for r in yt_rows:
            self.assertGreater(float(r["tps"]), 0.0)

        yt_m = RESULTS / "functional_limits_yt_cluster.csv"
        self.assertTrue(yt_m.is_file(), "Missing functional_limits_yt_cluster.csv")
        with yt_m.open(encoding="utf-8", newline="") as fh:
            yt_m_rows = list(csv.DictReader(fh))
        self.assertEqual(len(yt_m_rows), 1)
        self.assertEqual(yt_m_rows[0]["topology"].strip(), "yt-cluster")

        pop_p = RESULTS / "project_popularity.csv"
        self.assertTrue(pop_p.is_file(), "Missing project_popularity.csv")
        with pop_p.open(encoding="utf-8", newline="") as fh:
            pop_rows = list(csv.DictReader(fh))
        self.assertEqual(len(pop_rows), 22)
        pop_cols = {"solution_id", "project_name", "git_present", "github_repo", "stars", "forks", "total_commits", "commits_12m", "contributors", "pushed_at"}
        self.assertTrue(pop_cols.issubset(pop_rows[0].keys()))
        public = [r for r in pop_rows if r["stars"].strip().upper() != "N/A"]
        self.assertEqual(len(public), 19)

        opt_p = RESULTS / "benchmark_optimized.csv"
        self.assertTrue(opt_p.is_file(), "Missing benchmark_optimized.csv")
        with opt_p.open(encoding="utf-8", newline="") as fh:
            opt_rows = list(csv.DictReader(fh))
        self.assertEqual(len(opt_rows), 318)
        self.assertTrue((required | {"pg_scale"}).issubset(opt_rows[0].keys()))
        self.assertEqual({r["topology"].strip() for r in opt_rows}, OPT_TOPOLOGIES)
        for r in opt_rows:
            self.assertEqual(r["pg_scale"].strip(), "20")
            self.assertGreater(float(r["tps"]), 0.0)
        for topo in OPT_TOPOLOGIES:
            exp_n = 15 if topo.endswith("-standalone") else 18
            self.assertEqual(len({r["suite"].strip() for r in opt_rows if r["topology"].strip() == topo}), exp_n)
        pgedge_map = {r["suite"].strip(): r for r in opt_rows if r["topology"].strip() == "pgedge"}
        for crdt_suite in ("B2_overlap_rw", "D_hot_conflict"):
            self.assertEqual(float(pgedge_map[crdt_suite]["balance_drift"]), 0.0)
            self.assertEqual(pgedge_map[crdt_suite]["convergence_status"].strip(), "PASS_CONVERGED")

    def test_dashboard_and_scripts_file_size_cap(self) -> None:
        """Enforce < 14,000 byte limit on every text file in dashboard/ and scripts/."""
        text_exts = {".py", ".sh", ".html", ".css", ".js", ".svg"}
        oversized = []
        for directory in (DASH, SCRIPTS):
            if not directory.is_dir():
                continue
            for path in sorted(directory.rglob("*")):
                if path.is_file() and path.suffix.lower() in text_exts:
                    size = path.stat().st_size
                    if size >= 14000:
                        oversized.append(f"{path.relative_to(ROOT)} ({size} B)")
        self.assertEqual(oversized, [], f"Files >= 14,000 bytes: {oversized}")

    def test_submodule_and_makefile_integration(self) -> None:
        """Verify multi-db-docker-env Git submodule registration and Makefile targets."""
        gitmodules = ROOT / ".gitmodules"
        self.assertTrue(gitmodules.is_file(), "Missing .gitmodules file")
        gm_txt = gitmodules.read_text(encoding="utf-8")
        self.assertIn("path = env/multi-db-docker-env", gm_txt)
        self.assertIn("jmrenouard/multi-db-docker-env", gm_txt)

        mk_txt = (ROOT / "Makefile").read_text(encoding="utf-8")
        for tok in ("MDB_DIR", "init-env:", "build-bench-image:", "charts:", "dashboard:", "bench-optimized:", "BENCH_OUT_CSV=", "BENCH_LOG_DIR=", "reports/*.md"):
            self.assertIn(tok, mk_txt, f"Missing Makefile token: {tok}")

        self.assertTrue((SCRIPTS / "setup_pg17_baseline.sh").is_file(), "setup_pg17_baseline.sh must be preserved")
        legacy = (
            "bench_pg_multimaster.sh", "bench_pg_lib.py",
            "setup_birep.sh", "setup_bucardo.sh", "setup_citus.sh", "setup_cockroach.sh", "setup_pgedge.sh", "setup_yugabyte.sh",
            "test_bucardo.sh", "test_citus.sh", "test_cockroach.sh", "test_pg_birep.sh", "test_pgedge.sh", "test_yugabyte.sh",
        )
        leftovers = [n for n in legacy if (SCRIPTS / n).exists()]
        self.assertEqual(leftovers, [], f"Shadowed legacy scripts remain in scripts/: {leftovers}")

    def test_build_dashboard_parse_num_and_shard_rows(self) -> None:
        """Verify parse_num rejects non-finite floats and shard_rows balances shards evenly."""
        sys.path.insert(0, str(SCRIPTS))
        try:
            import build_dashboard as bd
        finally:
            if str(SCRIPTS) in sys.path:
                sys.path.remove(str(SCRIPTS))

        for bad in ("NaN", "nan", "inf", "-inf", "Infinity", "-Infinity"):
            val = bd.parse_num(bad)
            self.assertIsInstance(val, str)
            self.assertEqual(json.dumps(val, allow_nan=False), json.dumps(bad))
        self.assertEqual(bd.parse_num("N/A"), "")
        self.assertEqual(bd.parse_num("42"), 42)
        self.assertEqual(bd.parse_num("-71063"), -71063)
        self.assertEqual(bd.parse_num("1.2346"), 1.235)

        self.assertEqual(bd.shard_rows([], 10500), [[], [], []])
        one = bd.shard_rows([["t0", "s0", 1]], 10500)
        self.assertEqual(sum(len(s) for s in one), 1)
        rows = [[f"topo-{i % 10}", f"suite-{i}", 8, 15, 100.5 + i, 200.0, 1.2, 2.3, 1000, 0, "PASS", 0] for i in range(90)]
        shards = bd.shard_rows(rows, 10500)
        self.assertEqual(len(shards), 3)
        self.assertTrue(all(len(s) > 0 for s in shards), f"Empty shard in {[len(s) for s in shards]}")
        self.assertEqual([r for s in shards for r in s], rows)
        lens = [len(json.dumps(s, separators=(",", ":"))) for s in shards]
        self.assertLess(max(lens) - min(lens), 600, f"Unbalanced shard byte sizes: {lens}")

    def test_collect_popularity_redirects_pagination_and_timeout(self) -> None:
        """Verify 301 redirect JSON body handling, Link pagination regex, and gh timeout guard."""
        sys.path.insert(0, str(SCRIPTS))
        try:
            import collect_popularity as cp
        finally:
            if str(SCRIPTS) in sys.path:
                sys.path.remove(str(SCRIPTS))

        raw_double = (
            "HTTP/2 301 \r\nLocation: https://api.github.com/repositories/1/commits\r\n\r\n"
            '{"message":"Moved Permanently"}\r\n\r\n'
            'HTTP/2 200 \r\nLink: <https://api.github.com/repositories/1/commits?page=42>; rel="last"\r\n\r\n'
            '[{"sha":"abc"}]'
        )
        hdr1, body1 = cp.split_http_response(raw_double)
        self.assertIn("HTTP/2 200", hdr1)
        self.assertIn("page=42", hdr1)
        self.assertEqual(body1, '[{"sha":"abc"}]')

        raw_single = (
            "HTTP/1.1 301 Moved Permanently\nLocation: /new\n\n"
            '{"message":"Moved"}\n'
            'HTTP/1.1 200 OK\nLink: <https://api.github.com/x?per_page=1&page=19>; rel="last"\n\n[]'
        )
        hdr2, body2 = cp.split_http_response(raw_single)
        self.assertIn("HTTP/1.1 200 OK", hdr2)
        self.assertEqual(cp.LAST_PAGE_RE.search(hdr2).group(1), "19")
        self.assertEqual(body2, "[]")

        with mock.patch.object(cp.subprocess, "run", side_effect=subprocess.TimeoutExpired(["gh", "api", "x"], 30)) as m_run:
            rc, out, err = cp.run_gh(["api", "repos/a/b"])
        self.assertEqual(rc, 124)
        self.assertEqual(out, "")
        self.assertIn("timed out", err)
        self.assertEqual(m_run.call_args.kwargs.get("timeout"), 30)

        with mock.patch.object(cp, "run_gh", return_value=(0, raw_double, "")):
            self.assertEqual(cp.count_paginated("repos/old/repo/commits?per_page=1"), "42")
        with mock.patch.object(cp, "run_gh", return_value=(124, "", "timeout")):
            self.assertEqual(cp.count_paginated("repos/old/repo/commits?per_page=1"), "N/A")

    def test_chart_generators_meta_guards_and_snapshot_date(self) -> None:
        """Verify shared chart helpers, E1_/E_ resolution, empty guards, and dynamic snapshot date."""
        sys.path.insert(0, str(SCRIPTS))
        try:
            import chart_meta as cm
            import generate_charts as gc
            import generate_charts_v3 as v3
            import generate_charts_v5 as v5
        finally:
            if str(SCRIPTS) in sys.path:
                sys.path.remove(str(SCRIPTS))

        self.assertEqual(cm.resolve_e1({"A_single_rw", "E1_sysbench_oltp_rw", "E_sysbench_oltp_rw"}), "E1_sysbench_oltp_rw")
        self.assertEqual(cm.resolve_e1({"A_single_rw", "E_sysbench_oltp_rw"}), "E_sysbench_oltp_rw")
        self.assertEqual(cm.resolve_e1({"A_single_rw"}), "")

        self.assertEqual(cm.inum("0"), 0)
        self.assertEqual(cm.inum("42"), 42)
        for bad in ("", "N/A", "NaN", "inf", "-Infinity", "abc"):
            self.assertIsNone(cm.inum(bad))
            self.assertEqual(cm.fnum(bad), 0.0)

        gc.chart_07({})
        v3.chart_08([], "foot")
        v3.chart_09([], "foot")
        fig, ax = cm.plt.subplots()
        try:
            v5.draw_c13_sweep(ax, defaultdict(dict), "T", "X", [("A_single_rw", "0 ms"), ("F_wan_netem_10ms", "10 ms")], 1.0, 1.0)
        finally:
            cm.plt.close(fig)

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            tmp_res = pathlib.Path(tmp)
            (tmp_res / "project_popularity.csv").write_text(
                "solution_id,project_name,git_present,git_role,stars,forks,total_commits,commits_12m,contributors,pushed_at,snapshot_utc\n"
                "demo,Demo (#1),Yes,Primary,100,20,50,12,4,2026-11-21T00:00:00Z,2027-01-15T09:30:00Z\n",
                encoding="utf-8",
            )
            with mock.patch.object(v3, "RES_DIR", tmp_res):
                rows, snap_date = v3.load_pop()
            self.assertEqual(len(rows), 1)
            self.assertEqual(snap_date, "2027-01-15")


if __name__ == "__main__":
    unittest.main()

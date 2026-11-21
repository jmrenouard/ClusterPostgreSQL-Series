"""Automated validation tests for LightPath logos, Log10 charts, CSVs, and dashboard."""

from __future__ import annotations

import csv
import json
import pathlib
import re
import unittest
import xml.etree.ElementTree as ET

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
)

EXPECTED_DASH_FILES = (
    "index.html",
    "styles.css",
    "charts.js",
    "popularity.js",
    "app.js",
    "data_bench.js",
    "data_bench_2.js",
    "data_bench_3.js",
    "data_bench_pg18.js",
    "data_bench_yt.js",
    "data_matrix.js",
    "data_matrix_ext.js",
    "data_matrix_pg18.js",
    "data_popularity.js",
)


class TestBenchmarkArtifacts(unittest.TestCase):
    """Verify LightPath SVG branding, 10 Log10 PNG charts, offline dashboard, and CSVs."""

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
        """Verify all 10 generated PNG charts (01-10) exist with valid PNG headers."""
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
            'data-lang="en"',
            'data-lang="fr"',
            'id="btn-export"',
            "data_bench.js",
            "data_bench_2.js",
            "data_bench_3.js",
            "data_bench_pg18.js",
            "data_bench_yt.js",
            "data_matrix.js",
            "data_matrix_ext.js",
            "data_matrix_pg18.js",
            "data_popularity.js",
            "charts.js",
            "popularity.js",
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
        for tok in ("MDB_DIR", "init-env:", "charts:", "dashboard:"):
            self.assertIn(tok, mk_txt, f"Missing Makefile token: {tok}")


if __name__ == "__main__":
    unittest.main()

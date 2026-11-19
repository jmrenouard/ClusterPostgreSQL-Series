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
)

EXPECTED_DASH_FILES = (
    "index.html",
    "styles.css",
    "charts.js",
    "app.js",
    "data_bench.js",
    "data_bench_2.js",
    "data_bench_3.js",
    "data_matrix.js",
    "data_matrix_ext.js",
)


class TestBenchmarkArtifacts(unittest.TestCase):
    """Verify LightPath SVG branding, 7 Log10 PNG charts, offline dashboard, and CSVs."""

    def test_lightpath_svg_logos(self) -> None:
        """Validate official dark and light LightPath SVG logos exist and parse."""
        for fname in ("lightpath-logo-dark.svg", "lightpath-logo-light.svg"):
            path = ASSETS / fname
            self.assertTrue(path.is_file(), f"Missing logo: {path.relative_to(ROOT)}")
            size = path.stat().st_size
            self.assertGreater(size, 500, f"Logo unexpectedly small: {fname}")
            self.assertLess(size, 12000, f"Logo exceeds 12 KB cap: {fname} ({size} B)")
            root = ET.fromstring(path.read_text(encoding="utf-8"))
            self.assertTrue(root.tag.endswith("svg"), f"Invalid SVG root in {fname}")

    def test_seven_png_charts_valid(self) -> None:
        """Verify all 7 generated PNG charts exist with valid PNG headers."""
        png_magic = b"\x89PNG\r\n\x1a\n"
        for fname in EXPECTED_CHARTS:
            path = CHARTS / fname
            self.assertTrue(path.is_file(), f"Missing chart: {path.relative_to(ROOT)}")
            raw = path.read_bytes()
            self.assertTrue(raw.startswith(png_magic), f"Invalid PNG header: {fname}")
            self.assertGreater(len(raw), 10000, f"Chart unexpectedly small: {fname}")

    def test_dashboard_structure_and_offline_features(self) -> None:
        """Verify offline dashboard assets, 10-topology bundles, Log10 toggle, and logo."""
        for fname in EXPECTED_DASH_FILES:
            path = DASH / fname
            self.assertTrue(path.is_file(), f"Missing dashboard file: {fname}")

        html = (DASH / "index.html").read_text(encoding="utf-8")
        for token in (
            "../assets/lightpath-logo-dark.svg",
            'data-scale="log"',
            'data-scale="linear"',
            'id="topo-pills"',
            'data-preset="stream_logical"',
            'data-lang="en"',
            'data-lang="fr"',
            'id="btn-export"',
            "data_bench.js",
            "data_bench_2.js",
            "data_bench_3.js",
            "data_matrix.js",
            "data_matrix_ext.js",
            "charts.js",
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
        self.assertGreaterEqual(meta["row_count"], 170)

        for fname, var in (("data_matrix.js", "LP_MATRIX_CORE"), ("data_matrix_ext.js", "LP_MATRIX_EXT")):
            txt = (DASH / fname).read_text(encoding="utf-8")
            m = re.search(rf"window\.{var}=(\{{.*\}});", txt)
            self.assertIsNotNone(m, f"Missing {var} in {fname}")
            pack = json.loads(m.group(1))
            self.assertEqual(len(pack["rows"]), 10, f"Expected 10 matrix rows in {fname}")

    def test_all_benchmark_and_matrix_csvs_integrity(self) -> None:
        """Confirm all 4 benchmark CSVs and 2 matrix CSVs cover all 10 topologies."""
        required = {
            "topology",
            "suite",
            "tps",
            "lat_avg_ms",
            "lat_p95_ms",
            "convergence_status",
            "balance_drift",
        }
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
            m_topos = {r["topology"].strip() for r in rows}
            self.assertEqual(m_topos, CORE_TOPOLOGIES, f"Matrix {name} topology mismatch")

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

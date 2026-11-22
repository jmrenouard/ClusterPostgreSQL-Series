"""Automated tests for the offline GitHub Pages static bundle builder and verifier."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
for _p in (ROOT / "scripts", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import build_pages  # noqa: E402
from test_benchmark_artifacts import EXPECTED_CHARTS, EXPECTED_DASH_FILES  # noqa: E402


class TestPagesBundle(unittest.TestCase):
    """Validate make pages-build / make pages-check static staging and guards."""

    def test_makefile_and_gitignore_wiring(self) -> None:
        mk = (ROOT / "Makefile").read_text(encoding="utf-8")
        for tok in ("pages-build", "pages-check", "scripts/build_pages.py", "rm -rf _site"):
            self.assertIn(tok, mk)
        self.assertIn("_site/", (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())

    def test_build_and_verify_pages_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "_site"
            st = build_pages.build_pages_bundle(out)
            self.assertGreaterEqual(st["dashboard_files"], len(EXPECTED_DASH_FILES))
            self.assertGreaterEqual(st["asset_files"], len(EXPECTED_CHARTS) + 4)
            req = (".nojekyll", "index.html", *(f"dashboard/{f}" for f in EXPECTED_DASH_FILES),
                   "assets/clusterpostgresql-series-icon.png", "assets/lightpath-logo-dark.svg",
                   *(f"assets/charts/{c}" for c in EXPECTED_CHARTS))
            for r in req:
                self.assertTrue((out / r).is_file(), f"Missing staged {r}")
            self.assertEqual(build_pages.verify_pages_bundle(out), [])
            p = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_pages.py"), "--out", str(out), "--check"],
                               capture_output=True, text=True, check=False, timeout=30)
            self.assertEqual(p.returncode, 0, p.stderr)

    def test_verifier_negative_guards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "_site"
            build_pages.build_pages_bundle(out)

            (out / ".nojekyll").unlink()
            self.assertTrue(any(".nojekyll" in e for e in build_pages.verify_pages_bundle(out)))
            (out / ".nojekyll").write_text("", encoding="utf-8")

            icon = out / "assets" / "clusterpostgresql-series-icon.png"
            raw = icon.read_bytes()
            icon.unlink()
            self.assertTrue(any("clusterpostgresql-series-icon.png" in e for e in build_pages.verify_pages_bundle(out)))
            icon.write_bytes(raw)

            idx = out / "index.html"
            orig = idx.read_text(encoding="utf-8")
            idx.write_text(orig + '<script src="https://cdn.example.invalid/x.js"></script>', encoding="utf-8")
            self.assertTrue(any("External CDN" in e for e in build_pages.verify_pages_bundle(out)))
            idx.write_text(orig, encoding="utf-8")

            leak = out / "dashboard" / "leak.js"
            leak.write_text("// " + "gh" + "p_" + ("A" * 20) + "\n", encoding="utf-8")
            self.assertTrue(any("Hygiene violation" in e for e in build_pages.verify_pages_bundle(out)))
            leak.unlink()

            with self.assertRaises(ValueError):
                build_pages.build_pages_bundle(ROOT)


if __name__ == "__main__":
    unittest.main()

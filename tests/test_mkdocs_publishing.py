"""Unit and conditional integration tests for MkDocs publishing and IONOS CI."""

from __future__ import annotations

import pathlib
import shutil
import sys
import tempfile
import unittest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import build_mkdocs  # noqa: E402
import mkdocs_hooks  # noqa: E402


class _MkDocsLoader(yaml.SafeLoader):
    """YAML SafeLoader accepting PyMdownx !!python/name: tags."""


_MkDocsLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:",
    lambda loader, suffix, node: f"python/name:{suffix}",
)


def _flat_nav(node: object) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, list):
        return [p for item in node for p in _flat_nav(item)]
    if isinstance(node, dict):
        return [p for val in node.values() for p in _flat_nav(val)]
    return []


class TestMkDocsPublishing(unittest.TestCase):
    """Validate MkDocs config, hooks, IONOS site builder, workflow, and Makefile."""

    def test_mkdocs_yml_and_assets(self) -> None:
        loader = _MkDocsLoader((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
        try:
            cfg = loader.get_single_data()
        finally:
            loader.dispose()
        self.assertEqual(cfg["site_url"], "https://postgresql-cluster.lightpath.fr/")
        self.assertEqual(cfg["repo_name"], "jmrenouard/ClusterPostgreSQL-Series")
        self.assertEqual(cfg["theme"]["name"], "material")
        self.assertIn("scripts/mkdocs_hooks.py", cfg["hooks"])
        self.assertIn("stylesheets/extra.css", cfg["extra_css"])
        self.assertIn("javascripts/katex.js", cfg["extra_javascript"])
        nav = _flat_nav(cfg["nav"])
        self.assertGreaterEqual(len(nav), 70)
        for req in ("index.md", "overview-en.md", "overview-fr.md", "stacks-overview.md", "dashboard/index.html"):
            self.assertIn(req, nav)
        for p in (ROOT / "requirements-docs.txt", ROOT / "docs/javascripts/katex.js", ROOT / "docs/stylesheets/extra.css"):
            self.assertTrue(p.is_file(), f"Missing {p}")
        self.assertIn("site/", (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())

    def test_hooks_alerts_links_and_gfm_slugify(self) -> None:
        self.assertEqual(
            mkdocs_hooks.gfm_slugify("Chart 03 — Concurrency Scalability Sweep (G_conc_c1..c32, log10)"),
            "chart-03--concurrency-scalability-sweep-g_conc_c1c32-log10",
        )
        alerts = mkdocs_hooks.convert_github_alerts("> [!WARNING]\n> Guard.\n```\n> [!NOTE]\n> Keep.\n```\n")
        self.assertIn("!!! warning", alerts)
        self.assertIn("> [!NOTE]", alerts.split("```", 1)[1])

        rew = mkdocs_hooks.rewrite_relative_links(
            "[EN](../../README.md) [Img](../../assets/a.png) `[Code](../../README.md)`",
            "en/06_empirical_test_and_benchmark_results.md",
            docs_dir=ROOT / "docs",
        )
        self.assertIn("](../overview-en.md)", rew)
        self.assertIn("](../assets/a.png)", rew)
        self.assertIn("`[Code](../../README.md)`", rew)
        ov = mkdocs_hooks.rewrite_relative_links('<img src="assets/logo.png">', "overview-en.md", docs_dir=ROOT / "docs")
        self.assertIn('src="../assets/logo.png"', ov)
        stk = mkdocs_hooks.rewrite_relative_links("[Sub](../env/multi-db-docker-env)", "stacks-overview.md", docs_dir=ROOT / "docs")
        self.assertIn("/tree/main/env/multi-db-docker-env)", stk)

    def test_build_mkdocs_htaccess_and_negative_guards(self) -> None:
        ht = build_mkdocs.render_htaccess()
        for tok in ("Options -Indexes", "DirectoryIndex index.html", "ErrorDocument 404 /404.html", "RewriteEngine On", "R=301"):
            self.assertIn(tok, ht)
        with self.assertRaises(ValueError):
            build_mkdocs.build_mkdocs_site(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "site"
            out.mkdir()
            for req in build_mkdocs.REQUIRED_SITE_FILES:
                p = out / req
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("<html></html>" if req.endswith(".html") else "", encoding="utf-8")
            (out / ".htaccess").write_text(ht, encoding="utf-8")
            self.assertEqual(build_mkdocs.verify_mkdocs_site(out), [])

            (out / ".htaccess").unlink()
            self.assertTrue(any(".htaccess" in e for e in build_mkdocs.verify_mkdocs_site(out)))
            (out / ".htaccess").write_text(ht, encoding="utf-8")

            (out / "index.html").write_text('<a href="missing.html">x</a>', encoding="utf-8")
            self.assertTrue(any("Broken local ref" in e for e in build_mkdocs.verify_mkdocs_site(out)))
            (out / "index.html").write_text("<html></html>", encoding="utf-8")

            (out / ".agents").mkdir()
            (out / ".agents/secret.txt").write_text("x", encoding="utf-8")
            self.assertTrue(any("Forbidden repository artifact" in e for e in build_mkdocs.verify_mkdocs_site(out)))
            shutil.rmtree(out / ".agents")

            (out / "leak.js").write_text("// " + "gh" + "p_" + ("A" * 20), encoding="utf-8")
            self.assertTrue(any("Hygiene violation" in e for e in build_mkdocs.verify_mkdocs_site(out)))

    def test_workflow_and_makefile_wiring(self) -> None:
        wf_path = ROOT / ".github/workflows/docs-publish.yml"
        wf = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
        tr = wf.get("on") if "on" in wf else wf.get(True)
        self.assertEqual(tr["push"]["branches"], ["main"])
        self.assertEqual(tr["pull_request"]["branches"], ["main"])
        self.assertIs(tr["workflow_dispatch"]["inputs"]["deploy"]["default"], True)
        self.assertEqual(set(wf["jobs"]), {"verify-and-build", "deploy-ionos"})
        raw_wf = wf_path.read_text(encoding="utf-8")
        for tok in (
            "build_mkdocs.py --out site --strict --check",
            "actions/upload-artifact@v4",
            "include-hidden-files: true",
            "wlixcc/SFTP-Deploy-Action@v1.2.6",
            "secrets.IONOS_FTP_SERVER",
            "secrets.IONOS_FTP_USERNAME",
            "secrets.IONOS_FTP_PASSWORD",
            "secrets.IONOS_FTP_PORT",
            "secrets.IONOS_REMOTE_PATH",
            "https://postgresql-cluster.lightpath.fr/",
        ):
            self.assertIn(tok, raw_wf)
        mk = (ROOT / "Makefile").read_text(encoding="utf-8")
        for tok in ("docs-build:", "docs-check:", "scripts/build_mkdocs.py", "rm -rf _site site"):
            self.assertIn(tok, mk)

    def test_conditional_strict_mkdocs_build(self) -> None:
        mk_bin = shutil.which("mkdocs")
        if not mk_bin:
            self.skipTest("mkdocs executable not installed on PATH")
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "site"
            st = build_mkdocs.build_mkdocs_site(out, strict=True, mkdocs_bin=mk_bin)
            self.assertGreater(st["files"], 100)
            self.assertEqual(build_mkdocs.verify_mkdocs_site(out), [])


if __name__ == "__main__":
    unittest.main()

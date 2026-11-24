"""Executable validation suite for EN/FR Diataxis tutorials, how-tos, diagrams, and MkDocs separation."""

from __future__ import annotations

import os
import pathlib
import py_compile
import re
import shutil
import subprocess
import sys
import unittest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from test_docs_hygiene import MODAL_RX, check_markdown_ste_structural  # noqa: E402
from test_docs_math_syntax import check_markdown_text  # noqa: E402
from test_mkdocs_publishing import _MkDocsLoader, _flat_nav  # noqa: E402
from test_solution_sheets import validate_mermaid_markdown  # noqa: E402

MAKE_CMD_RX = re.compile(r"\bmake\s+([a-zA-Z0-9_-]+)\b")
FENCE_HDR_RX = re.compile(r"^([ \t]*)(`{3,}|~{3,})([^\r\n]*)$")
ASCII_BOX_RX = re.compile(r"(?:\+-[-+]{2,}\+|[\u250c\u2510\u2514\u2518\u251c\u2524\u252c\u2534\u253c\u2550-\u256c])")
FR_MODAL_RX = re.compile(r"\b(?:devrait|pourrait|serait|faudrait|\u00e9ventuellement)\b", re.I)

QUADRANT_SPECS = (
    (
        "en",
        ROOT / "docs/en",
        ("01-tutorials/index.md", "01-tutorials/01-first-docker-poc-lab.md", "01-tutorials/02-pgbench-sysbench-lab.md"),
        ("02-how-to-guides/index.md", "02-how-to-guides/01-run-topology-benchmarks.md", "02-how-to-guides/02-verify-limits-and-hygiene.md"),
        ("03-reference/index.md", "04-explanation/index.md"),
        ("## Prerequisites", "Expected Output"),
        ("## Prerequisites", "## Validation", "## Rollback"),
    ),
    (
        "fr",
        ROOT / "docs/fr",
        ("01-tutoriels/index.md", "01-tutoriels/01-premier-lab-poc-docker.md", "01-tutoriels/02-lab-benchmarks-pgbench-sysbench.md"),
        ("02-guides-pratiques/index.md", "02-guides-pratiques/01-executer-benchmarks-topologies.md", "02-guides-pratiques/02-verifier-limites-et-hygiene.md"),
        ("03-reference/index.md", "04-explications/index.md"),
        ("## Pr\u00e9requis", "R\u00e9sultat attendu"),
        ("## Pr\u00e9requis", "## Validation", "## Retour arri\u00e8re"),
    ),
)


def _strip_fences(text: str) -> str:
    """Return Markdown prose outside fenced code blocks."""
    out, in_f, fc, fl = [], False, "", 0
    for ln in text.splitlines():
        m = FENCE_HDR_RX.match(ln)
        if not in_f and m:
            in_f, fc, fl = True, m.group(2)[0], len(m.group(2))
            continue
        if in_f:
            s = ln.lstrip(" \t")
            if s.startswith(fc) and len(s) - len(s.lstrip(fc)) >= fl and not s.lstrip(fc).strip():
                in_f = False
            continue
        out.append(ln)
    return "\n".join(out)


def _tracked_parent_markdown() -> list[pathlib.Path]:
    """List parent-repo Markdown files excluding submodules and generated site outputs."""
    return sorted(
        p for p in ROOT.rglob("*.md")
        if not any(part in {"env", ".git", "site", "_site"} for part in p.relative_to(ROOT).parts)
    )


class TestDocsTutorialsAndHowTos(unittest.TestCase):
    """Validate EN/FR Diataxis quadrants, safe commands, diagrams, math, and i18n."""

    def test_en_and_fr_quadrants_structure_and_controlled_language(self) -> None:
        for lang, base, tuts, howtos, extras, tut_toks, how_toks in QUADRANT_SPECS:
            self.assertTrue((base / "index.md").is_file(), f"Missing {base / 'index.md'}")
            for rel in (*tuts, *howtos, *extras):
                path = base / rel
                self.assertTrue(path.is_file(), f"Missing Diataxis doc: {path}")
                txt = path.read_text(encoding="utf-8")
                self.assertEqual(check_markdown_text(txt, str(path.relative_to(ROOT))), [])
            for rel in tuts[1:]:
                txt = (base / rel).read_text(encoding="utf-8")
                self.assertIn("```mermaid\n", txt, f"Missing column-0 Mermaid block in {rel}")
                for tok in tut_toks:
                    self.assertIn(tok, txt, f"Missing {tok!r} in {rel}")
            for rel in howtos[1:]:
                txt = (base / rel).read_text(encoding="utf-8")
                for tok in how_toks:
                    self.assertIn(tok, txt, f"Missing {tok!r} in {rel}")
                self.assertTrue("> [!WARNING]" in txt or "> [!CAUTION]" in txt, f"Missing safety alert in {rel}")
                if lang == "en":
                    self.assertEqual(check_markdown_ste_structural(txt, 20), [])
                    self.assertIsNone(MODAL_RX.search(_strip_fences(txt)), f"Modal found in {rel}")
                else:
                    prose = _strip_fences(txt)
                    self.assertIsNone(FR_MODAL_RX.search(prose), f"Weak FR modal found in {rel}")
                    self.assertNotIn(";", prose, f"Semicolon found in FR how-to prose: {rel}")

    def test_referenced_commands_scripts_and_compose_configs(self) -> None:
        mk_txt = (ROOT / "Makefile").read_text(encoding="utf-8")
        targets = set(re.findall(r"^([a-zA-Z0-9_-]+):", mk_txt, re.M))
        dyn_pfxs = tuple(re.findall(r"^([a-zA-Z0-9_-]+)%:", mk_txt, re.M))
        for _, base, tuts, howtos, _, _, _ in QUADRANT_SPECS:
            for rel in (*tuts[1:], *howtos[1:]):
                txt = (base / rel).read_text(encoding="utf-8")
                for tgt in MAKE_CMD_RX.findall(txt):
                    ok = tgt in targets or any(tgt.startswith(p) for p in dyn_pfxs)
                    self.assertTrue(ok, f"Undefined make target `{tgt}` cited in {rel}")

        for req in (".env.example", "scripts/Dockerfile.bench", "scripts/setup_pg17_baseline.sh", "stacks/README.md", "dashboard/index.html", "assets/charts/chart_01_tps_log_all_suites.png"):
            self.assertTrue((ROOT / req).exists(), f"Missing referenced artifact: {req}")

        for py_cli in ("scripts/build_mkdocs.py", "scripts/build_pages.py", "scripts/collect_popularity.py"):
            res = subprocess.run([sys.executable, py_cli, "--help"], cwd=str(ROOT), capture_output=True, text=True, timeout=15)
            self.assertEqual(res.returncode, 0, f"{py_cli} --help failed: {res.stderr}")
        py_compile.compile(str(ROOT / "scripts/build_dashboard.py"), doraise=True)

        if os.name != "nt" and (bash := shutil.which("bash")):
            res = subprocess.run([bash, "-n", "scripts/setup_pg17_baseline.sh"], cwd=str(ROOT), capture_output=True, text=True, timeout=10)
            self.assertEqual(res.returncode, 0, res.stderr)

        sub = ROOT / "env/multi-db-docker-env"
        if (sub / "docker-compose-pg17-baseline.yml").is_file():
            for rel in ("docker-compose-pg17-baseline.yml", "docker-compose-pgedge.yml", "tests/test_pgedge.sh", "scripts/pgedge"):
                self.assertTrue((sub / rel).exists(), f"Missing submodule artifact: {rel}")
            for yml in ("docker-compose-pg17-baseline.yml", "docker-compose-pgedge.yml"):
                parsed = yaml.safe_load((sub / yml).read_text(encoding="utf-8"))
                self.assertIn("services", parsed, f"Invalid compose YAML: {yml}")
            if docker := shutil.which("docker"):
                chk = subprocess.run([docker, "compose", "version"], capture_output=True, timeout=10)
                if chk.returncode == 0:
                    ef = ".env" if (sub / ".env").is_file() else ".env.example"
                    for yml in ("docker-compose-pg17-baseline.yml", "docker-compose-pgedge.yml"):
                        args = [docker, "compose", *(["--env-file", ef] if (sub / ef).is_file() else []), "-f", yml, "config", "-q"]
                        res = subprocess.run(args, cwd=str(sub), capture_output=True, text=True, timeout=20)
                        self.assertEqual(res.returncode, 0, res.stderr)

    def test_zero_ascii_diagrams_and_valid_mermaid_across_all_docs(self) -> None:
        total_blocks = 0
        for md in _tracked_parent_markdown():
            txt = md.read_text(encoding="utf-8")
            rel = md.relative_to(ROOT).as_posix()
            self.assertIsNone(re.search(r"^[ \t]+```mermaid", txt, re.M), f"Indented mermaid fence in {rel}")
            self.assertIsNone(ASCII_BOX_RX.search(txt), f"ASCII box/diagram pattern in {rel}")
            cnt, errs = validate_mermaid_markdown(txt, rel)
            self.assertEqual(errs, [], f"Mermaid errors in {rel}: {errs}")
            total_blocks += cnt
        self.assertGreaterEqual(total_blocks, 54)

    def test_mkdocs_en_fr_separation_and_superfences_configs(self) -> None:
        specs = (
            ("mkdocs.yml", "en", ("fr/", "overview-fr.md", "/01-tutoriels/", "/02-guides-pratiques/"), ("fr/", "overview-fr.md"), ("en/01-tutorials/01-first-docker-poc-lab.md", "en/02-how-to-guides/01-run-topology-benchmarks.md")),
            ("mkdocs.fr.yml", "fr", ("en/", "overview-en.md", "/01-tutorials/", "/02-how-to-guides/"), ("en/", "overview-en.md"), ("fr/01-tutoriels/01-premier-lab-poc-docker.md", "fr/02-guides-pratiques/01-executer-benchmarks-topologies.md")),
        )
        for cfg_name, exp_lang, req_excl, bad_pfx, req_nav in specs:
            cfg = _MkDocsLoader((ROOT / cfg_name).read_text(encoding="utf-8")).get_single_data()
            self.assertEqual(cfg["theme"]["language"], exp_lang)
            for pat in req_excl:
                self.assertIn(pat, cfg["exclude_docs"])
            self.assertEqual({a["lang"] for a in cfg["extra"]["alternate"]}, {"en", "fr"})
            has_mermaid = any(
                isinstance(ext, dict) and "pymdownx.superfences" in ext
                and any(cf.get("name") == "mermaid" for cf in ext["pymdownx.superfences"].get("custom_fences", []) if isinstance(cf, dict))
                for ext in cfg.get("markdown_extensions", [])
            )
            self.assertTrue(has_mermaid, f"Missing superfences mermaid in {cfg_name}")
            nav = _flat_nav(cfg["nav"])
            for req in req_nav:
                self.assertIn(req, nav)
            self.assertFalse(any(p.startswith(bad_pfx) for p in nav), f"Mixed-lang nav in {cfg_name}")


if __name__ == "__main__":
    unittest.main()

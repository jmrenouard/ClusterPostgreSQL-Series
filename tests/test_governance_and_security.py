"""Repository governance, secret hygiene, and shell safety tests."""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP = {".git", "__pycache__", ".pytest_cache", ".venv", "venv"}
BANNED = (
    ("secret-store term", re.compile(r"\b(?:k[e]epass|v[a]ult|password[_ -]?manag[e]r)\b", re.I)),
    ("secret-store ext", re.compile(r"\.(?:kdb[x]|key[x])\b", re.I)),
    ("Windows user path", re.compile(r"[A-Za-z]:\\[U]sers\\", re.I)),
    ("WSL drive path", re.compile(r"/mnt/[c]/", re.I)),
    ("sync path", re.compile(r"\b[D]ropbox\b", re.I)),
    ("GitHub token", re.compile(r"(?:gh[p]|gh[o]|github_p[a]t)_[A-Za-z0-9_]{16,}")),
    ("AWS key", re.compile(r"\bAKI[A][0-9A-Z]{16}\b")),
)
ACCENTS = re.compile(
    r"[\u00e9\u00e8\u00ea\u00eb\u00e0\u00e2\u00e7\u00ee\u00ef\u00f4\u00fb\u00f9"
    r"\u00c9\u00c8\u00ca\u00cb\u00c0\u00c2\u00c7\u00ce\u00cf\u00d4\u00db\u00d9]"
)


class TestGovernanceAndSecurity(unittest.TestCase):
    """Verify licensing, governance files, registers, secret hygiene, and scripts."""

    def test_license_and_env_example(self) -> None:
        """Check MIT license attribution, .gitignore, and ephemeral .env.example."""
        lic = (ROOT / "LICENSE").read_text(encoding="utf-8")
        for tok in ("MIT License", "2026", "Jean-Marie Renouard", "LightPath"):
            self.assertIn(tok, lic)
        self.assertIn(".env", (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
        env = (ROOT / ".env.example").read_text(encoding="utf-8")
        for line in ("PG_LAB_PASSWORD=pg_poc_ephemeral", "PG_USER=postgres", "PG_DB=labdb", "PG_BENCH_SCALE=10"):
            self.assertIn(line, env)

    def test_governance_and_registers(self) -> None:
        """Check AGENTS.md, .agents/rules/*.md, ACTION_LOGBOOK.md, and RCA_REGISTER.md."""
        rules = [ROOT / ".agents" / "rules" / f"{n}.md" for n in ("git-workflow", "github-workflow", "project-governance")]
        for path in [ROOT / "AGENTS.md", ROOT / ".agents" / "AGENTS.md", *rules]:
            self.assertTrue(path.is_file(), f"Missing {path.relative_to(ROOT)}")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for m in ("15,000", "docs/ACTION_LOGBOOK.md", "docs/RCA_REGISTER.md", "docs/en/", "docs/fr/", "gh issue create"):
            self.assertIn(m, agents)
        for rp in rules:
            self.assertIn("trigger: always_on", rp.read_text(encoding="utf-8"))
        log = (ROOT / "docs" / "ACTION_LOGBOOK.md").read_text(encoding="utf-8")
        for m in ("Ongoing Actions", "Completed Actions", "ACT-001", "Request", "Changes", "Result"):
            self.assertIn(m, log)
        rca = (ROOT / "docs" / "RCA_REGISTER.md").read_text(encoding="utf-8")
        for m in ("RCA-001", "IMP-001", "APP-001", "IDEA-001"):
            self.assertIn(m, rca)

    def test_zero_secrets_or_local_paths(self) -> None:
        """Fail if any file leaks secrets, credential stores, or local paths."""
        hits = []
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or any(p in SKIP for p in path.parts):
                continue
            txt = path.read_text(encoding="utf-8", errors="ignore")
            hits.extend(f"{path.relative_to(ROOT)}: {lbl}" for lbl, pat in BANNED if pat.search(txt))
        self.assertEqual(hits, [])

    def test_english_governance_and_shell_strict_mode(self) -> None:
        """Enforce ASCII English in governance/tests/scripts and strict mode in .sh."""
        targets = [
            ROOT / "AGENTS.md", ROOT / "Makefile", ROOT / ".agents" / "AGENTS.md",
            ROOT / "docs" / "ACTION_LOGBOOK.md", ROOT / "docs" / "RCA_REGISTER.md",
            *(ROOT / ".agents" / "rules").glob("*.md"),
            *(ROOT / ".github").rglob("*.yml"),
            *(ROOT / "tests").rglob("*.py"),
            *ROOT.rglob("*.sh"),
        ]
        accents, no_strict = [], []
        for path in sorted({p for p in targets if p.is_file()}):
            txt = path.read_text(encoding="utf-8")
            rel = str(path.relative_to(ROOT))
            if ACCENTS.search(txt):
                accents.append(rel)
            if path.suffix == ".sh" and "set -euo pipefail" not in txt:
                no_strict.append(rel)
        self.assertEqual(accents, [], f"Accents: {accents}")
        self.assertEqual(no_strict, [], f"Missing strict mode: {no_strict}")


if __name__ == "__main__":
    unittest.main()

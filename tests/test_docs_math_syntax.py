"""Markdown LaTeX math syntax validation tests."""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP = {".git", "__pycache__", ".pytest_cache", ".venv", "venv"}
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
CODE_RE = re.compile(r"(`+)(?:(?!\1).)*?\1")
CURRENCY_RE = re.compile(r"^\d+(?:[.,]\d+)?[-/]$")


def check_markdown_text(text: str, label: str) -> list[str]:
    """Validate display math alignment, inline math tightness, and currency escaping."""
    errs, lines, fence, disp = [], text.splitlines(), "", False
    for idx, line in enumerate(lines):
        if m := FENCE_RE.match(line):
            if not disp:
                fence = "" if fence == m.group(1)[0] else (fence or m.group(1)[0])
            continue
        if fence:
            continue
        if disp:
            if line.strip() == "$$":
                if line != line.lstrip():
                    errs.append(f"{label}:{idx+1}: closing $$ indented")
                if idx + 1 < len(lines) and lines[idx + 1].strip():
                    errs.append(f"{label}:{idx+1}: closing $$ needs blank line")
                disp = False
            elif r"\operatorname" in line:
                errs.append(f"{label}:{idx+1}: forbidden \\operatorname")
            continue
        masked = CODE_RE.sub("", line)
        if "$$" in masked:
            if line != "$$":
                errs.append(f"{label}:{idx+1}: $$ must be unindented on own line")
            if idx > 0 and lines[idx - 1].strip():
                errs.append(f"{label}:{idx+1}: opening $$ needs blank line")
            disp = line == "$$"
            continue
        cleaned = masked.replace(r"\$", "")
        pos = [i for i, c in enumerate(cleaned) if c == "$"]
        if len(pos) % 2:
            errs.append(f"{label}:{idx+1}: unpaired $")
            continue
        for k in range(0, len(pos), 2):
            inner = cleaned[pos[k] + 1 : pos[k + 1]]
            if not inner or inner[0].isspace() or inner[-1].isspace():
                errs.append(f"{label}:{idx+1}: untight inline math")
            if r"\operatorname" in inner:
                errs.append(f"{label}:{idx+1}: forbidden \\operatorname")
            if CURRENCY_RE.match(inner):
                errs.append(f"{label}:{idx+1}: unescaped currency '${inner}$'")
    if disp:
        errs.append(f"{label}:{len(lines)}: unclosed $$")
    return errs


class TestDocsMathSyntax(unittest.TestCase):
    """Validate LaTeX math rules on all Markdown files."""

    def test_all_markdown_files_comply(self) -> None:
        """Scan every Markdown document for math formatting compliance."""
        mds = [p for p in sorted(ROOT.rglob("*.md")) if not any(d in SKIP for d in p.parts)]
        self.assertTrue(mds)
        errs = [e for p in mds for e in check_markdown_text(p.read_text(encoding="utf-8"), str(p.relative_to(ROOT)))]
        self.assertEqual(errs, [], "\n".join(errs))

    def test_validator_catches_invalid_patterns(self) -> None:
        """Confirm validator detects bad LaTeX/currency and accepts valid LaTeX."""
        self.assertEqual(check_markdown_text("Cost \\$100 and $p_i=1$.\n\n$$\n\\arg\\max_i p_i\n$$\n\nOk.\n", "ok.md"), [])
        for bad in ("  $$\nx=1\n$$\n", "$$\n\\operatorname{f}(x)\n$$\n", "Bad $ x $.\n", "Cost $100.\n", "$$x=1$$\n"):
            self.assertTrue(check_markdown_text(bad, "bad.md"))


if __name__ == "__main__":
    unittest.main()

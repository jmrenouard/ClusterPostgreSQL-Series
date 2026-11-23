"""Documentation hygiene, link resolution, and STE structural gates."""

from __future__ import annotations

import pathlib
import re
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROCEDURAL_DOCS = ("README.md", "README.fr.md", "stacks/README.md")
LINK_RX = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)")
MAKE_RX = re.compile(r"`make\s+([a-zA-Z0-9_-]+)`")
MODAL_RX = re.compile(
    r"\b(should|would|may|might|shall|\u00e9ventuellement|"
    r"devrait|devraient|pourrait|pourraient|serait|seraient)\b",
    re.I,
)
SENT_SPLIT = re.compile(
    r"(?<!No\.)(?<!e\.g\.)(?<!i\.e\.)(?<!etc\.)(?<!a\.m\.)(?<!p\.m\.)(?<=[.!?:])\s+"
    r"|(?<=(?:a\.m\.|p\.m\.|etc\.))\s+(?=[A-Z\u00c0-\u00de0-9])"
    r"|(?<=No\.)\s+(?=[A-Z\u00c0-\u00de])"
)
WORDISH = re.compile(
    r"[A-Za-z\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u00ff\u0152\u0153\u01780-9]+"
    r"(?:[.'&/\u2019-][A-Za-z\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u00ff\u0152\u0153\u01780-9]+)*"
)
BULLET_RX = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
NUM_UNIT_RX = re.compile(
    r"(?<![A-Za-z0-9_])[+-]?\d+(?:[.,:]\d+)*(?:-[+-]?\d+(?:[.,:]\d+)*)?\s*"
    r"(?:ms|us|ns|s|sec|min|mins|hr|hrs|h|%|KiB|MiB|GiB|TiB|KB|MB|GB|TB|Mbps|Gbps)(?![A-Za-z0-9_])"
)


def _tracked_markdown() -> list[pathlib.Path]:
    res = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "*.md"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [ROOT / p for p in res.stdout.splitlines() if (ROOT / p).is_file()]


def _strip_markdown(text: str) -> str:
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\A---\n.*?\n---(?:\n|\Z)", "", t, flags=re.S)
    t = re.sub(r"```.*?```|~~~.*?~~~", " ", t, flags=re.S)
    t = re.sub(r"(?<!\\)\$\$.*?(?<!\\)\$\$", " MATH ", t, flags=re.S)
    t = re.sub(r"(?<!\\)\$(?!\s)(?:[^\n$\\]|\\.)+?(?<!\s)\$", " MATH ", t)
    t = re.sub(r"``[^`\n]+``|`[^`\n]+`", " CODE ", t)
    t = re.sub(r"!?\[([^\]]*)\]\((?:[^()]|\([^)]*\))*\)", r"\1", t)
    t = re.sub(r"https?://\S+?(?=[.,;:!?)]*(?:\s|$))", " URL ", t)
    t = re.sub(r"^[ \t]*>.*$", " ", t, flags=re.M)
    return re.sub(r'"[^"\n]*"|\u201c[^\u201d\n]*\u201d|\u00ab[^\u00bb\n]*\u00bb', " QUOTED ", t)


def _strip_code_and_math(text: str) -> str:
    out, in_fence, in_math = [], False, False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if s == "$$":
            in_math = not in_math
            continue
        if not in_math:
            out.append(line)
    return "\n".join(out)


def _gfm_anchors(text: str) -> set[str]:
    seen: dict[str, int] = {}
    anchors: set[str] = set()
    for line in _strip_code_and_math(text).splitlines():
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if not m:
            continue
        h = m.group(1).strip().rstrip("#").strip()
        h = re.sub(r"`([^`]*)`", r"\1", h)
        h = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", h)
        h = re.sub(r"\*\*([^*]+)\*\*", r"\1", h)
        h = re.sub(r"(?<!\w)[*_~]+|[*_~]+(?!\w)", "", h)
        slug = "".join(
            "-" if ch == " " else ch
            for ch in h.lower()
            if ch.isalnum() or ch in (" ", "-", "_")
        )
        cnt = seen.get(slug, 0)
        seen[slug] = cnt + 1
        anchors.add(slug if cnt == 0 else f"{slug}-{cnt}")
    return anchors


def _count_ste_words(sentence: str) -> int:
    s = sentence
    for _ in range(3):
        upd = re.sub(r"\([^()]*\)", " PAREN ", s)
        if upd == s:
            break
        s = upd
    s = NUM_UNIT_RX.sub(" NUMUNIT ", s)
    s = re.sub(r"\*\*|__|#+|\*|(?<!\w)_|_(?!\w)", " ", s)
    return len(WORDISH.findall(s))


def _check_block(block: str, max_words: int) -> list[str]:
    errs: list[str] = []
    for part in SENT_SPLIT.split(block):
        sent = part.strip()
        if not sent or not WORDISH.search(sent):
            continue
        if ";" in sent:
            errs.append(f"semicolon: {sent[:60]}")
        n = _count_ste_words(sent)
        if n > max_words:
            errs.append(f"{n}>{max_words}w: {sent[:60]}")
    return errs


def check_markdown_ste_structural(text: str, max_words: int) -> list[str]:
    """Check Markdown text against structural STE limits (semicolons and word counts)."""
    stripped = _strip_markdown(text)
    stripped = re.sub(r"(?m)^[ \t]*(?:#.*|\|.*|---+|\*\*\*+|___+|===+)[ \t]*$", "", stripped)
    errs: list[str] = []
    for par in re.split(r"\n\s*\n", stripped):
        par = par.strip()
        if not par or not WORDISH.search(par):
            continue
        items, prose = [], []
        for line in par.splitlines():
            if BULLET_RX.match(line):
                items.append(line)
            elif items and re.match(r"^(?:  |\t)\S", line):
                items[-1] = items[-1] + " " + line.strip()
            else:
                prose.append(line)
        for raw_item in items:
            errs.extend(_check_block(BULLET_RX.sub("", raw_item, count=1), max_words))
        if prose:
            sents = [p.strip() for p in SENT_SPLIT.split("\n".join(prose)) if p.strip() and WORDISH.search(p)]
            if len(sents) > 6:
                errs.append(f"paragraph {len(sents)}>6 sentences")
            errs.extend(_check_block("\n".join(prose), max_words))
    return errs


class TestDocsHygiene(unittest.TestCase):
    """Verify link integrity, Makefile references, and STE structural rules."""

    def test_no_file_uri_and_valid_links_anchors(self) -> None:
        broken: list[str] = []
        for path in _tracked_markdown():
            rel = str(path.relative_to(ROOT))
            clean = re.sub(r"`[^`]*`", "", _strip_code_and_math(path.read_text(encoding="utf-8")))
            if "file://" + "/" in clean.lower():
                broken.append(f"{rel}: forbidden file:/// URI")
            for target in LINK_RX.findall(clean):
                if re.match(r"^(?:https?://|mailto:|tel:)", target, re.I):
                    continue
                pp, _, frag = target.partition("#")
                dest = (path.parent / pp).resolve() if pp else path.resolve()
                if not dest.exists():
                    broken.append(f"{rel}: missing target {target}")
                elif frag and dest.suffix == ".md":
                    if frag not in _gfm_anchors(dest.read_text(encoding="utf-8")):
                        broken.append(f"{rel}: bad anchor {target}")
        self.assertEqual(broken, [])

    def test_cited_make_targets_exist(self) -> None:
        mk = (ROOT / "Makefile").read_text(encoding="utf-8")
        exact = set(re.findall(r"^([a-zA-Z0-9_-]+):", mk, re.M))
        prefixes = tuple(re.findall(r"^([a-zA-Z0-9_-]+)%", mk, re.M))
        unknown: list[str] = []
        for path in _tracked_markdown():
            for m in MAKE_RX.finditer(path.read_text(encoding="utf-8")):
                tgt = m.group(1)
                if tgt not in exact and not any(tgt.startswith(p) for p in prefixes):
                    unknown.append(f"{path.relative_to(ROOT)}: make {tgt}")
        self.assertEqual(unknown, [])

    def test_no_forbidden_modals_and_ste_structural_zero_errors(self) -> None:
        chapters = sorted((ROOT / "docs" / "en").glob("[01]*.md")) + sorted(
            (ROOT / "docs" / "fr").glob("[01]*.md")
        )
        sheets = sorted((ROOT / "docs" / "en" / "solutions").glob("*.md")) + sorted(
            (ROOT / "docs" / "fr" / "solutions").glob("*.md")
        )
        all_targets = [ROOT / p for p in PROCEDURAL_DOCS] + chapters + sheets
        if (ROOT / "docs" / "index.md").is_file():
            all_targets.append(ROOT / "docs" / "index.md")
        failures: list[str] = []
        for path in all_targets:
            txt = path.read_text(encoding="utf-8")
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            no_code = re.sub(r"`[^`]*`", "", _strip_code_and_math(txt))
            for m in MODAL_RX.finditer(no_code):
                failures.append(f"{rel}: forbidden '{m.group(1)}'")
            limit = 20 if rel in PROCEDURAL_DOCS else 25
            failures.extend(f"{rel}: {e}" for e in check_markdown_ste_structural(txt, limit))
        self.assertEqual(failures, [])

    def test_hygiene_negative_guards(self) -> None:
        self.assertTrue(check_markdown_ste_structural("First clause; second clause.", 25))
        long_sent = " ".join(["word"] * 21) + "."
        self.assertTrue(check_markdown_ste_structural(long_sent, 20))
        self.assertEqual(check_markdown_ste_structural(long_sent, 25), [])
        self.assertTrue(MODAL_RX.search("You should run tests."))
        self.assertTrue(MODAL_RX.search("Option \u00e9ventuellement active."))


if __name__ == "__main__":
    unittest.main()

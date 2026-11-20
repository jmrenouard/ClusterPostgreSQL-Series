"""E2E validation suite (Tiers 1-2) for bilingual PostgreSQL solution sheets."""

from __future__ import annotations

import importlib.util
import os
import pathlib
import re
import unittest

rc, rs = re.compile, re.search
ROOT = pathlib.Path(os.environ.get("CLUSTER_PG_REPO_ROOT") or pathlib.Path(__file__).resolve().parents[1]).resolve()
DOCS_EN, DOCS_FR = ROOT / "docs" / "en", ROOT / "docs" / "fr"
SOL_EN, SOL_FR = DOCS_EN / "solutions", DOCS_FR / "solutions"

SPEC = dict(x.split(":") for x in (
    "pg17_standalone:pg17-standalone pg17_physical_streaming_patroni:pg17-async-streaming,pg17-sync-streaming "
    "pg17_logical_unidirectional:pg17-logical pg17_bidirectional_logical:pg-birep "
    "pgedge_spock:pgedge,pgedge-delta-apply bucardo:bucardo citus:citus yugabytedb:yugabyte "
    "cockroachdb:cockroach pglogical2: edb_pgd: opentenbase_pgxl: pgpool_ii: symmetricds: "
    "aws_aurora_limitless: gcp_spanner_alloydb: legacy_triggers:"
).split())
SLUGS = tuple(SPEC)
BENCH = {k: tuple(v.split(",")) for k, v in SPEC.items() if v}
REF = tuple(k for k, v in SPEC.items() if not v)
NAV_03A = frozenset(SLUGS[:5] + ("pglogical2", "edb_pgd"))

FENCE_RE = rc(r"^\s*(```+|~~~+)(.*)$")
DHDR_RE = rc(r"^(?:(?:flowchart|graph)(?:\s+(?:TB|TD|BT|RL|LR))?|sequenceDiagram|stateDiagram(?:-v2)?|classDiagram|erDiagram)(?:\s*%%.*)?$")
ERE = {
    "f": rc(r"<-+>|--+>|---|-\.+->|-\.-|==+>|===|--x|--o|o--o|x--x"),
    "s": rc(r"<<-->>|<<->>|-->>|->>|-->|->|--x|-x|--\)|-\)"),
    "r": rc(r"-->|--|\.\.>|<\|--|[\|\}o]+(?:--|\.\.)[\|\{o]+"),
}
FIGN_RE = rc(r"^\s*(?:subgraph|end|direction|style|classDef|class|linkStyle|click|title|accTitle|accDescr)\b")


def _load_sibling(name: str):
    """Load sibling test module privately without polluting TestLoader globals."""
    p = pathlib.Path(__file__).resolve().with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"_ext_{name}", p if p.is_file() else ROOT / "tests" / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rel_path(path: pathlib.Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_sheets() -> list[tuple[str, str, pathlib.Path, str]]:
    return [(lg, p.stem, p, p.read_text(encoding="utf-8")) for lg, d in (("en", SOL_EN), ("fr", SOL_FR)) if d.is_dir() for p in sorted(d.glob("*.md"))]


def unfenced_lines(text: str) -> list[str]:
    out, fc, fl = [], "", 0
    for ln in text.splitlines():
        if fm := FENCE_RE.match(ln):
            tk = fm.group(1)
            fc, fl = (tk[0], len(tk)) if not fc else ("", 0) if tk[0] == fc and len(tk) >= fl else (fc, fl)
        elif not fc:
            out.append(ln)
    return out


def validate_mermaid_markdown(text: str, label: str) -> tuple[int, list[str]]:
    """Validate Mermaid fenced blocks in Markdown using pure stdlib checks."""
    blks, e, fc, fl, inm, cur = [], [], "", 0, False, []
    for ln in text.splitlines():
        if fm := FENCE_RE.match(ln):
            tk, inf = fm.group(1), fm.group(2).strip()
            if not fc:
                fc, fl, inm = tk[0], len(tk), bool(re.match(r"^mermaid(?:\s|$)", inf, re.I))
                cur = [] if inm else cur
            elif tk[0] == fc and len(tk) >= fl:
                if inm:
                    blks.append(cur)
                fc, fl, inm = "", 0, False
        elif inm:
            cur.append(ln)
    if fc and inm:
        e.append(f"{label}: unclosed fence")
    pairs = {")": "(", "]": "[", "}": "{"}
    for bi, raw in enumerate(blks, 1):
        bl = f"{label}#m{bi}"
        lns = [x.strip() for x in re.sub(r"%%\{.*?\}%%", "", "\n".join(raw), flags=re.S).splitlines() if x.strip() and not x.strip().startswith("%%")]
        if not lns or not DHDR_RE.match(lns[0]):
            e.append(f"{bl}: bad header")
            continue
        hdr, body = lns[0], lns[1:]
        k = "s" if hdr.startswith("sequence") else "f" if hdr.startswith(("flowchart", "graph")) else "r"
        st = [x for x in body if not (k == "f" and FIGN_RE.match(x))]
        if len(st) < 2 or not any(ERE[k].search(x) for x in st):
            e.append(f"{bl}: need >=2 stmts/1 edge")
        dp, stk = 0, []
        for ln in body:
            s = ln.replace(r'\"', "  ")
            idx = s.find("%%")
            while idx >= 0 and s[:idx].count('"') % 2:
                idx = s.find("%%", idx + 2)
            s = (s[:idx] if idx >= 0 else s).strip()
            if not s:
                continue
            if k in ("f", "s"):
                op = r"^subgraph\b" if k == "f" else r"^(?:loop|alt|opt|par|critical|break|rect|box)\b"
                dp += 1 if re.match(op, s) else -1 if re.match(r"^end\s*$", s) else 0
                if dp < 0:
                    e.append(f"{bl}: unmatched end")
                    dp = 0
            if s.count('"') % 2:
                e.append(f"{bl}: unclosed quote")
                continue
            s = re.sub(r'"[^"]*"', '"_"', s)
            if rs(r'"_"[A-Za-z0-9_]|[A-Za-z0-9_]"_"|"_""_"', s):
                e.append(f"{bl}: nested quotes")
                continue
            if k == "s":
                s = ERE["s"].sub(" ", re.sub(r":.*$", "", s))
            elif hdr.startswith("erDiagram"):
                s = re.sub(r"[\|\}o]+(?:--|\.\.)[\|\{o]+", " ", s)
            elif k == "f":
                if s.count("|") % 2:
                    e.append(f"{bl}: unclosed pipe")
                    continue
                s = ERE["f"].sub(" ", re.sub(r"--\s+.+?\s+-->|-\.\s+.+?\s+\.->|==\s+.+?\s+==>|\|[^|]*\|", " ", s))
                if any(m.group(1).strip(" /\\(){}[]") != '"_"' for m in re.finditer(r'(?:\[|\(|\{)([^\]\)\}\n]*"_"[^\]\)\}\n]*)(?:\]|\)|\})', s)):
                    e.append(f"{bl}: nested quotes")
                    continue
                s = re.sub(r"\[[/\\]|[/\\]\]", lambda m: m.group(0).strip("/\\"), re.sub(r"\b([A-Za-z0-9_-]+)>([^\]\n]+)\]", r"\1[\2]", s))
                if ">" in s:
                    e.append(f"{bl}: unclosed flag")
                    continue
            for ch in s:
                if ch in "([{":
                    stk.append(ch)
                elif ch in pairs:
                    if not stk or stk[-1] != pairs[ch]:
                        e.append(f"{bl}: unbalanced {ch!r}")
                        break
                    stk.pop()
        if dp or stk:
            e.append(f"{bl}: unclosed d={dp} s={stk}")
    return len(blks), e


def extract_sections_and_tables(text: str):
    pr, tb, lns, i, h = {"": []}, [], unfenced_lines(text), 0, ""
    tr, ts = rc(r"^\s*\|.+\|\s*$"), rc(r"^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
    while i < len(lns):
        ln = lns[i]
        if hm := re.match(r"^#{2,3}\s+(.+?)\s*$", ln):
            h = hm.group(1)
            pr.setdefault(h, [])
        elif i + 1 < len(lns) and tr.match(ln) and ts.match(lns[i + 1]):
            hd = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            rw = []
            while i < len(lns) and tr.match(lns[i]):
                rw.append([c.strip() for c in lns[i].strip().strip("|").split("|")])
                i += 1
            tb.append((h, hd, rw))
            continue
        else:
            pr.setdefault(h, []).append(ln)
        i += 1
    return {k: "\n".join(v) for k, v in pr.items()}, tb


class TestTier1And2SolutionSheets(unittest.TestCase):
    """Tier 1 (coverage, metadata, density) and Tier 2 (Mermaid, structure, compliance)."""

    def test_tier1_slug_parity_headers_and_density(self) -> None:
        self.assertEqual((len(SLUGS), set(BENCH) | set(REF), set(BENCH) & set(REF)), (17, set(SLUGS), set()))
        for d in (SOL_EN, SOL_FR):
            self.assertEqual({p.stem for p in d.glob("*.md")} if d.is_dir() else set(), set(SLUGS))
        sh = iter_sheets()
        self.assertEqual(len(sh), 34)
        e = []
        for lg, _, p, txt in sh:
            rel, lns, sz = rel_path(p), txt.splitlines(), p.stat().st_size
            top = "\n".join(lns[:45])
            if not re.match(r"^#\s+\S+", next((x.strip() for x in lns if x.strip()), "")):
                e.append(f"{rel}: H1")
            if any(t not in top for t in ("Jean-Marie Renouard", "jmrenouard", "LightPath", "https://www.lightpath.fr", "MIT")):
                e.append(f"{rel}: attribution/MIT")
            req, ban = (("Series:", "Author:"), ("Auteur", "S\u00e9rie")) if lg == "en" else (("S\u00e9rie", "Auteur"), ("Author:", "Series:"))
            if any(k not in top for k in req) or any(k in top for k in ban):
                e.append(f"{rel}: {lg} header")
            if not [t for t in extract_sections_and_tables("\n".join(lns[:55]))[1] if len(t[2]) >= 4 and rs(r"\b(?:CAP|PACELC)\b", str(t), re.I)]:
                e.append(f"{rel}: CAP/PACELC table")
            if not (55 <= len(lns) <= 220 and 3500 <= sz < 14000):
                e.append(f"{rel}: density {len(lns)}L/{sz}B")
        self.assertEqual(e, [], "\n".join(e))

    def test_tier2_mermaid_validator_self_test(self) -> None:
        ok = (
            '```mermaid\nflowchart LR\n  subgraph G\n  A[(DocDB)] -->|l (a)| B{{Hex}}\n'
            '  B -- "q (b)" --> C([Stad])\n  C --> D>Flag]\n  D --> E[/Trap/]\n  end %% close G\n  %% (ign\n```\n'
            '```mermaid\nsequenceDiagram\n  box Cluster\n  participant C as Client (App)\n  end\n  alt Ok\n    C-)S: msg (a)\n  end\n```\n'
            '```mermaid\nerDiagram\n  NODE ||..o{ SHARD : hosts\n  NODE ||--o{ REPLICA : owns\n```'
        )
        self.assertEqual(validate_mermaid_markdown(ok, "ok.md"), (3, []))
        for bad in (
            "flowchart TD\nA-->B", "bad\nA-->B\n```", "flowchart LR\nA[(Doc] --> B\n```",
            'flowchart LR\nA["x] --> B\n```', "flowchart LR\nA -->|open B\n```",
            "flowchart LR\nsubgraph X\nA-->B\n```", "flowchart LR\nend\nA-->B\n```",
            "flowchart LR\nA[1]\nB[2]\n```", "flowchart LR\nA>Flag --> B\n```",
            'flowchart LR\nA["Hello "World""] --> B\n```',
            "flowchart XX\nA[1]-->B[2]\n```",
            'flowchart LR\nA[bad "q" txt] --> B\n```',
        ):
            self.assertTrue(validate_mermaid_markdown("```mermaid\n" + bad, "bad.md")[1], bad)

    def test_tier2_structure_mermaid_and_compliance(self) -> None:
        sh = iter_sheets()
        self.assertEqual(len(sh), 34)
        mm, sm = _load_sibling("test_docs_math_syntax"), _load_sibling("test_governance_and_security")
        lre = {
            "en": (r"description|overview|what\s+it|architecture", r"principle|internal|mechanism|operating|how\s+it", r"implementation\s+mode|variants?|topologies", r"strengths?|pros?", r"weaknesses?|cons?|limits?|traps?"),
            "fr": (r"description|pr\u00e9sentation|ce\s+qu|architecture", r"principe|m\u00e9canisme|fonctionnement|interne", r"modes?\s+d|variantes?|topologies", r"forces?|avantages?|atouts?", r"faiblesses?|inconv\u00e9nients?|limites?|pi[\u00e8e]ges?"),
        }
        ma, mb, e = r"mode|variant|variante|configuration", r"commit|conflict|conflit|rpo|rto|cap|pacelc|trade|compromis|sync|r[\u00e9e]plicat", []
        for lg, slug, p, txt in sh:
            rel = rel_path(p)
            cnt, me = validate_mermaid_markdown(txt, rel)
            if cnt < 1:
                e.append(f"{rel}: no mermaid")
            e.extend(me)
            pr, tb = extract_sections_and_tables(txt)
            dp, pp, _, sa, sb = lre[lg]
            dh, ph = [h for h in pr if rs(dp, h, re.I)], [h for h in pr if rs(pp, h, re.I)]
            if not (dh and ph) or sum(len(pr[h].strip()) for h in dict.fromkeys(dh + ph)) < 80:
                e.append(f"{rel}: short desc/principles")
            if not any(len(r) >= 2 and rs(ma, hs, re.I) and rs(mb, hs, re.I) for _, c, r in tb for hs in (" ".join(c),)):
                e.append(f"{rel}: Modes table")
            if not any(len(r) >= 2 and rs(sa, s := f"{h} {' '.join(c)}", re.I) and rs(sb, s, re.I) for h, c, r in tb):
                e.append(f"{rel}: SW table")
            if slug in BENCH and not rs(r"results/|Suite\s+[A-F]", txt):
                e.append(f"{rel}: bench ref")
            e.extend(mm.check_markdown_text(txt, rel))
            e.extend(f"{rel}: banned {lb}" for lb, pt in sm.BANNED if pt.search(txt))
            if lg == "en" and sm.ACCENTS.search(re.sub(r"\[Version\s+fran\u00e7aise\]\([^)]+\)", "", txt, flags=re.I)):
                e.append(f"{rel}: EN accents")
        self.assertEqual(e, [], "\n".join(e))


if __name__ == "__main__":
    unittest.main()

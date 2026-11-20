"""E2E validation suite (Tiers 3-4): CSV parity, reference disclaimers, and navigation."""

from __future__ import annotations

import csv
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP
import importlib.util
import pathlib
import re
import unittest

rc, rs = re.compile, re.search


def _load_base():
    """Load Tier 1-2 helpers privately without triggering duplicate TestCase discovery."""
    spec = importlib.util.spec_from_file_location("_ext_sheets", pathlib.Path(__file__).resolve().with_name("test_solution_sheets.py"))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BASE = _load_base()
ROOT, RESULTS = BASE.ROOT, BASE.ROOT / "results"
DOCS_EN, DOCS_FR, SOL_EN, SOL_FR = BASE.DOCS_EN, BASE.DOCS_FR, BASE.SOL_EN, BASE.SOL_FR
BENCH, REF, SLUGS, NAV_03A = BASE.BENCH, BASE.REF, BASE.SLUGS, BASE.NAV_03A


def _g(d: pathlib.Path, pat: str) -> pathlib.Path:
    return next(d.glob(pat))


def extract_md_targets(path: pathlib.Path) -> list[pathlib.Path]:
    """Return resolved local targets for non-external Markdown links."""
    out: list[pathlib.Path] = []
    for ln in BASE.unfenced_lines(path.read_text(encoding="utf-8")):
        for m in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", re.sub(r"(`+)(?:(?!\1).)*?\1", "", ln)):
            raw = m.group(1).strip().split()[0].strip("<>")
            if not raw.startswith(("http://", "https://", "mailto:", "tel:", "#")) and (rel := raw.split("#", 1)[0].split("?", 1)[0]):
                out.append((path.parent / rel).resolve())
    return out


def has_csv_number(norm_text: str, raw_val: str, allow_round: bool = False) -> bool:
    """Match a CSV numeric value across EN/FR decimals, thousands, padding, and rounding."""
    raw = raw_val.strip()
    d = Decimal(raw)
    cands = [raw] + ([f"{d:.2f}"] if "." in raw and len(raw.split(".", 1)[1]) < 2 else [])
    if allow_round:
        cands.extend((f"{d:.3f}", str(d.quantize(Decimal("0.01"), ROUND_HALF_UP)), str(d.quantize(Decimal("0.01"), ROUND_HALF_EVEN))))
    plus = "." not in raw and not raw.startswith("-")
    for cand in dict.fromkeys(cands):
        sign = "-" if cand.startswith("-") else (r"\+?" if plus else "")
        ip, dot, fp = cand.lstrip("-").partition(".")
        ip_pat = r"[, ]?".join(ip[max(0, k - 3) : k] for k in range(len(ip), 0, -3)[::-1]) if len(ip) > 3 else ip
        lb = rf"(?<!\d)(?<!\d[., ]){'' if cand.startswith('-') else '(?<!-)'}" if dot else r"(?<![\d#\-.A-Za-z])(?<!\d[., ])"
        la = r"(?!(?:\d|[.,]\d))" if dot else r"(?!(?:\d|[.,]\d|[A-Za-z]))"
        if rs(rf"{lb}{sign}{ip_pat}" + (rf"[.,]{fp}" if dot else "") + la, norm_text):
            return True
    return False


class TestTier3And4ParityAndNavigation(unittest.TestCase):
    """Tier 3 (CSV parity, anti-p99, reference status) and Tier 4 (links, symmetry, #14/#16, Ch01)."""

    summary_rows: list[dict[str, str]]
    sqlstates: dict[str, set[str]]

    @classmethod
    def setUpClass(cls) -> None:
        with (RESULTS / "benchmark_summary.csv").open(encoding="utf-8", newline="") as fh:
            cls.summary_rows = list(csv.DictReader(fh))
        cls.sqlstates = {}
        for fn in ("functional_limits_matrix.csv", "extended_functional_matrix.csv"):
            with (RESULTS / fn).open(encoding="utf-8", newline="") as fh:
                for row in csv.DictReader(fh):
                    cls.sqlstates.setdefault(row["topology"].strip(), set()).update(
                        s.strip() for s in row["verified_sqlstates"].split(";") if s.strip() and s.strip() != "NONE"
                    )

    def test_tier3_csv_parity_p99_and_reference(self) -> None:
        topos = {r["topology"].strip() for r in self.summary_rows}
        self.assertEqual((len(BENCH) + len(REF), {k for ks in BENCH.values() for k in ks}, len(topos)), (17, topos, 11))
        by_t: dict[str, list[dict[str, str]]] = {}
        for r in self.summary_rows:
            by_t.setdefault(r["topology"].strip(), []).append(r)
        e, tr = [], str.maketrans({"\u00a0": " ", "\u202f": " ", "\u2212": "-"})
        na = rc(r"N/A|non\s+applicable|unbenchmarked|not\s+applicable", re.I)
        for slug, keys in BENCH.items():
            codes = sorted(set().union(*(self.sqlstates.get(k, set()) for k in keys)))
            for d in (SOL_EN, SOL_FR):
                p = d / f"{slug}.md"
                rel = BASE.rel_path(p)
                if not p.is_file():
                    e.append(f"Missing {rel}")
                    continue
                txt = p.read_text(encoding="utf-8")
                norm = txt.translate(tr).replace(r"\\,", " ").replace(r"\,", " ")
                for k in keys:
                    for r in by_t[k]:
                        su = r["suite"].strip()
                        for col, cond in (("tps", True), ("balance_drift", int(r["balance_drift"]) != 0), ("retries_40001", int(r["retries_40001"]) > 0), ("tx_failed", k == "cockroach" and su == "E_sysbench_oltp_rw")):
                            if cond and not has_csv_number(norm, r[col]):
                                e.append(f"{rel}: miss {k}/{su} {col}={r[col]}")
                        if su in ("A_single_rw", "F_wan_netem_25ms") or (k == "pgedge-delta-apply" and su == "D_hot_conflict"):
                            if not (has_csv_number(norm, r["lat_avg_ms"], True) or has_csv_number(norm, r["lat_p95_ms"], True)):
                                e.append(f"{rel}: miss {k}/{su} lat")
                e.extend(f"{rel}: miss SQLSTATE {c}" for c in codes if not rs(rf"\b{re.escape(c)}\b", txt))
                if slug == "pg17_standalone":
                    for ln in txt.splitlines():
                        if rs(r"F_wan_netem", ln, re.I):
                            tb = ln.lstrip().startswith("|")
                            if (tb and rs(r"\|\s*[*`]*\d+[.,]\d+(?:\s*TPS)?[*`]*\s*\|", ln, re.I)) or (not tb and not na.search(ln) and rs(r"\d+[.,]\d+\s*TPS", ln, re.I)):
                                e.append(f"{rel}: F_wan_netem TPS")
        neg = rc(r"not\s+measured|unmeasured|not\s+recorded|non\s+mesur|pas\s+mesur|absent|n/a|never", re.I)
        p99 = rc(r"\b(?:lat_)?p99(?:_ms)?\b", re.I)
        p99n = rc(r"(?:lat_)?p99(?:_ms)?[^.\n;|]{0,20}?\d+(?:[.,]\d+)?\s*ms|(?:lat_)?p99(?:_ms)?\s*[:=]\s*\d", re.I)
        for _, _, p, txt in BASE.iter_sheets():
            rel = BASE.rel_path(p)
            e.extend(f"{rel}:{i}: bad p99" for i, ln in enumerate(txt.splitlines(), 1) if p99.search(ln) and (ln.lstrip().startswith("|") or not neg.search(ln) or p99n.search(ln)))
        hdr = rc(r"not\s+(?:live[- ])?benchmarked|non\s+benchmark|architectural\s+reference|r\u00e9f\u00e9rence\s+architecturale|\bN/A\b", re.I)
        bdy = {"en": rc(r"not\s+(?:live[- ])?benchmarked|unbenchmarked|architectural\s+reference|excluded\s+from\s+(?:live\s+)?benchmarks?", re.I), "fr": rc(r"non\s+benchmark|pas\s+benchmark|r\u00e9f\u00e9rence\s+architecturale|hors\s+benchmark|exclusion\s+du\s+benchmark", re.I)}
        rst, rrw, oth = rc(r"\b(?:PASS_CONVERGED|PASS_SINGLE_PRIMARY|PASS_NETEM(?:_\w+)?)\b"), rc(r"^\s*\|?\s*`?(?:[A-H]\d?_[a-z0-9_]+)`?\s*\|"), rc(r"\b(?:pg17-|pg-birep|pgedge|bucardo|citus|yugabyte|cockroach|standalone|patroni)\b", re.I)
        for slug in REF:
            for lg, d in (("en", SOL_EN), ("fr", SOL_FR)):
                p = d / f"{slug}.md"
                rel = BASE.rel_path(p)
                if not p.is_file():
                    e.append(f"Missing {rel}")
                    continue
                txt = p.read_text(encoding="utf-8")
                if not hdr.search("\n".join(txt.splitlines()[:45])) or not bdy[lg].search(txt):
                    e.append(f"{rel}: no ref disclaimer")
                if any(rst.search(ln) or (rrw.search(ln) and rs(r"\|\s*[*`]*\d+[.,]\d+", ln) and not oth.search(ln)) for ln in txt.splitlines()):
                    e.append(f"{rel}: REF claims results")
        self.assertEqual(e, [], "\n".join(e))

    def test_tier4_navigation_symmetry_and_integrity(self) -> None:
        sh = BASE.iter_sheets()
        by, e = {(l, s): (p, txt) for l, s, p, txt in sh}, []
        for d, sd, rm in ((DOCS_EN, SOL_EN, ROOT / "README.md"), (DOCS_FR, SOL_FR, ROOT / "README.fr.md")):
            p3a, p3b = _g(d, "03a_*.md"), _g(d, "03b_*.md")
            for p, ss in ((rm, SLUGS), (p3a, NAV_03A), (p3b, set(SLUGS) - NAV_03A)):
                tgs = set(extract_md_targets(p))
                if miss := sorted(s for s in ss if (sd / f"{s}.md").resolve() not in tgs):
                    e.append(f"{BASE.rel_path(p)}: miss {miss}")
            bk = {rm.resolve(), p3a.resolve(), p3b.resolve()}
            e.extend(f"{BASE.rel_path(p)}: no back-link" for l, _, p, _ in sh if l == d.name and not (set(extract_md_targets(p)) & bk))
            c1 = _g(d, "01_*.md")
            pat = r"\bpending\b" if d == DOCS_EN else r"phase\s+empirique\s+suivante|apr[\u00e8e]s\s+ex[\u00e9e]cution\s+compl[\u00e8e]te|\bpending\b|en\s+attente|\u00e0\s+venir"
            if rs(pat, c1.read_text(encoding="utf-8"), re.I):
                e.append(f"{BASE.rel_path(c1)}: stale Pending")
            if not {_g(d, "06_*.md").resolve(), _g(d, "08_*.md").resolve()}.issubset(set(extract_md_targets(c1))):
                e.append(f"{BASE.rel_path(c1)}: miss 06/08")
        dis = rc(r"disambiguat|d[\u00e9e]sambigu[\u00efi]s|legacy\s+CSV|reserves?\s+#14|r[\u00e9e]serve\s+#14", re.I)
        fs = [ROOT / "README.md", ROOT / "README.fr.md", ROOT / "stacks" / "README.md", *sorted(DOCS_EN.glob("*.md")), *sorted(DOCS_FR.glob("*.md")), *[p for _, _, p, _ in sh]]
        for p in fs:
            if not p.is_file():
                continue
            e.extend(f"{BASE.rel_path(p)} -> {t}" for t in extract_md_targets(p) if not t.is_relative_to(ROOT) or not t.exists())
            if p != ROOT / "stacks" / "README.md":
                nb = [(i, ln) for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if ln.strip()]
                for pos, (i, ln) in enumerate(nb):
                    if dis.search(ln):
                        continue
                    wins = [ln] + ([f"{ln}\n{nb[pos + 1][1]}"] if pos + 1 < len(nb) and not dis.search(nb[pos + 1][1]) and not (ln.lstrip().startswith("|") and nb[pos + 1][1].lstrip().startswith("|")) else [])
                    if any(rs(r"pg17[-_]logical|Logique\s+Uni", w, re.I) and rs(r"#14\b", w) for w in wins):
                        e.append(f"{BASE.rel_path(p)}:{i}: pg17-logical #14")
                    if any(rs(r"RubyRep|Slony-I|Londiste|Legacy\s+Trigger|Syst[\u00e8e]mes?\s+historiques", w, re.I) and rs(r"#16\b", w) for w in wins):
                        e.append(f"{BASE.rel_path(p)}:{i}: legacy #16")
        for s in SLUGS:
            if ("en", s) in by and ("fr", s) in by:
                ep, et = by[("en", s)]
                fp, ft = by[("fr", s)]
                br, lr = fp.stat().st_size / ep.stat().st_size, len(ft.splitlines()) / len(et.splitlines())
                if not (0.65 <= br <= 1.50 and 0.65 <= lr <= 1.50):
                    e.append(f"{s}: sym b={br:.2f} l={lr:.2f}")
                em, fm = BASE.validate_mermaid_markdown(et, s)[0], BASE.validate_mermaid_markdown(ft, s)[0]
                if not em or em != fm:
                    e.append(f"{s}: mermaid EN={em} FR={fm}")
        for lg in ("en", "fr"):
            for sl, ok, bad in (("pg17_logical_unidirectional", "#16", "#14"), ("legacy_triggers", "#14", "#16")):
                if (lg, sl) in by:
                    lns = by[(lg, sl)][1].splitlines()
                    h1 = next((x.strip() for x in lns if x.strip()), "")
                    cat = next((x for x in lns[:45] if re.match(r"^\|\s*\*\*(?:Catalog\s+ID|ID\s+Catalogue)\*\*\s*\|", x, re.I)), "")
                    if not re.match(rf"^#\s+{ok[1:]}\b", h1) or rs(rf"{bad}\b", h1):
                        e.append(f"{lg}/{sl}: bad H1 {ok}")
                    cell = cat.split("|")[2].strip() if cat.count("|") >= 3 else ""
                    if not re.match(rf"^`?{ok}\b", cell) or (rs(rf"{bad}\b", cell) and not dis.search(cat)):
                        e.append(f"{lg}/{sl}: bad Catalog ID {ok}")
        self.assertEqual(e, [], "\n".join(e))


if __name__ == "__main__":
    unittest.main()

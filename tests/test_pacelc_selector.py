"""Automated unit, parity, and scoring tests for the PACELC Architecture Selector."""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASH, SCRIPTS, SUBMOD = ROOT / "dashboard", ROOT / "scripts", ROOT / "env" / "multi-db-docker-env"
for _p in (SCRIPTS, ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pacelc_catalog  # noqa: E402
from test_benchmark_artifacts import CORE_TOPOLOGIES, PG18_TOPOLOGIES, YT_TOPOLOGIES  # noqa: E402

ALL_19 = CORE_TOPOLOGIES | PG18_TOPOLOGIES | YT_TOPOLOGIES | {"pgedge-delta-apply", "cockroach-rc"}


def _load_pacelc_bundle() -> dict[str, object]:
    raw = (DASH / "data_pacelc.js").read_text(encoding="utf-8")
    m = re.search(r"window\.LP_PACELC_CATALOG=(\{.*\});\s*$", raw, re.S)
    if not m:
        raise AssertionError("Missing window.LP_PACELC_CATALOG in dashboard/data_pacelc.js")
    return json.loads(m.group(1))


class TestPacelcSelector(unittest.TestCase):
    """Validate PACELC catalog parity, lab commands, sheet links, and JS scoring."""

    def test_catalog_coverage_parity_and_ascii(self) -> None:
        """Verify data_pacelc.js matches generator verbatim and covers 17 base + 2 variants."""
        self.assertTrue(all(b <= 127 for b in (DASH / "data_pacelc.js").read_bytes()), "data_pacelc.js must be ASCII")
        cat = _load_pacelc_bundle()
        self.assertEqual(cat, pacelc_catalog.build_pacelc_catalog(), "data_pacelc.js drifted from pacelc_catalog.py")
        self.assertEqual(cat["base_count"], 17)
        rows = [dict(zip(cat["cols"], r)) for r in cat["rows"]]
        self.assertEqual({r["topology"] for r in rows}, ALL_19)
        self.assertEqual(len(rows), 19)
        caveats = cat["caveats"]
        for r in rows:
            self.assertIn(r["pacelc_class"], {"CA", "PA/EL", "PC/EC"})
            self.assertIn(r["tco_tier"], {"low", "medium", "high"})
            self.assertIn(r["dataset_scope"], {"both", "baseline", "optimized"})
            self.assertTrue(r["caveat_keys"])
            for ck in r["caveat_keys"]:
                self.assertIn(ck, caveats)
                self.assertEqual(len(caveats[ck]), 2)
                self.assertTrue(all(isinstance(s, str) and s for s in caveats[ck]))

    def test_lab_commands_and_bilingual_sheet_paths(self) -> None:
        """Verify every Makefile, ./mdb command, and EN/FR solution sheet path resolves."""
        m_stacks = re.search(r"PG_STACKS\s*:=\s*(.+)", (ROOT / "Makefile").read_text(encoding="utf-8"))
        self.assertIsNotNone(m_stacks, "Missing PG_STACKS in Makefile")
        pg_stacks = set(m_stacks.group(1).split())
        sub_ready = (SUBMOD / "docker-compose-pgedge.yml").is_file()
        cat = _load_pacelc_bundle()
        cols, pfx = cat["cols"], cat["sheet_prefix"]
        for raw_row in cat["rows"]:
            row = dict(zip(cols, raw_row))
            topo = row["topology"]
            for lang in ("en", "fr"):
                self.assertTrue((ROOT / f"{pfx[lang]}{row['sheet_slug']}.md").is_file(), f"Missing {lang} sheet ({topo})")
            mk_parts = row["make_cmd"].split()
            self.assertEqual(mk_parts[0], "make")
            for tok in mk_parts[1:]:
                m_t = re.match(r"^(up|setup|test)-(.+)$", tok)
                self.assertIsNotNone(m_t, f"Bad make target {tok} ({topo})")
                action, stack = m_t.group(1), m_t.group(2)
                self.assertIn(stack, pg_stacks)
                if action == "setup" and sub_ready:
                    u = stack.replace("-", "_")
                    has_s = any((SUBMOD / "scripts" / u).glob("setup_*.sh")) or (SCRIPTS / f"setup_{u}.sh").is_file()
                    self.assertTrue(has_s, f"Missing setup script for {stack} ({topo})")
                if action == "test":
                    self.assertNotEqual(stack, "pg17-baseline")
                    if sub_ready:
                        self.assertTrue((SUBMOD / "tests" / f"test_{stack.replace('-', '_')}.sh").is_file())
            mdb_stacks = re.findall(r"\./mdb\s+(?:up|setup)\s+([a-z0-9-]+)", row["mdb_cmd"])
            self.assertTrue(mdb_stacks, f"Missing ./mdb command ({topo})")
            for stack in mdb_stacks:
                self.assertIn(stack, pg_stacks | {"patroni"})
                if sub_ready:
                    self.assertTrue((SUBMOD / f"docker-compose-{stack}.yml").is_file())

    def test_js_scoring_engine_and_ui_in_node(self) -> None:
        """Execute deterministic Node.js tests for S1-S4 scenarios, invariants, and UI."""
        node = shutil.which("node")
        if not node:
            self.skipTest("node executable not available on PATH")
        js = r"""
const fs = require("fs"), path = require("path"), vm = require("vm"), a = require("assert");
const dash = process.argv[1];
const scripts = [...fs.readFileSync(path.join(dash, "index.html"), "utf8").matchAll(/<script src="([^"]+)"><\/script>/g)]
  .map((m) => m[1]).filter((f) => !["popularity.js", "matrix.js", "app.js"].includes(f));
let on = {}, dl = null, copies = 0;
const el = () => ({ dataset: {}, style: {}, textContent: "", innerHTML: "", value: "",
  classList: { s: new Set(), toggle(c, v) { v ? this.s.add(c) : this.s.delete(c); } },
  addEventListener(e, f) { on[e] = f; }, appendChild: (c) => c, select() {}, remove() {}, click() { dl = this; } });
const host = el(), btns = (k, vs) => vs.map((v) => { const b = el(); b.dataset[k] = v; return b; });
const tB = btns("tab", ["bench", "matrix", "popularity", "pacelc"]), mB = btns("mtab", ["core", "ext", "pg18", "yt"]), dB = btns("dataset", ["baseline", "optimized", "compare"]);
const ctx = { window: {}, console, setTimeout: () => 0, URL: { createObjectURL: () => "blob:t", revokeObjectURL() {} }, Blob: class { constructor(p) { this.t = p.join(""); } },
  document: { body: el(), getElementById: (i) => (i === "panel-pacelc" ? host : null),
    querySelectorAll: (s) => ({ "[data-tab]": tB, "[data-mtab]": mB, "[data-dataset]": dB }[s] || []),
    querySelector: () => null, createElement: el, execCommand: (c) => (copies++, c === "copy") }, navigator: {} };
ctx.window = ctx; vm.createContext(ctx);
for (const f of scripts) vm.runInContext(fs.readFileSync(path.join(dash, f), "utf8"), ctx, { filename: f });
const eng = ctx.LPPacelcEngine;

// S1-S4 canonical decision rankings
for (const ds of ["baseline", "optimized"]) {
  const s1 = eng.rank({ rpo: "zero", wanRttMs: 0, conflictRate: "none", tco: "low", dataset: ds }, ctx);
  a.strictEqual(s1.top.topology, "pg18-sync-streaming"); a.strictEqual(s1.results[1].topology, "pg17-sync-streaming");
  a.strictEqual(s1.top.status, "recommended"); a.strictEqual(s1.top.balance_drift, 0);
  const s3 = eng.rank({ rpo: "async", wanRttMs: 25, conflictRate: "disjoint", tco: "medium", dataset: ds }, ctx);
  a.strictEqual(s3.top.topology, "pg18-birep"); a.strictEqual(s3.top.status, "recommended");
}
const s2b = eng.rank({ rpo: "async", wanRttMs: 25, conflictRate: "counter_crdt", tco: "medium", dataset: "baseline" }, ctx);
a.strictEqual(s2b.top.topology, "pgedge-delta-apply"); a.strictEqual(s2b.top.balance_drift, 0);
const s2o = eng.rank({ rpo: "async", wanRttMs: 25, conflictRate: "counter_crdt", tco: "medium", dataset: "optimized" }, ctx);
a.strictEqual(s2o.top.topology, "pgedge"); a.strictEqual(s2o.top.balance_drift, 0);
const s4 = eng.rank({ rpo: "zero", wanRttMs: 0, conflictRate: "high_contention", tco: "high", dataset: "baseline" }, ctx);
a.strictEqual(s4.top.topology, "yugabyte"); a.strictEqual(s4.top.balance_drift, 0);
const byT = Object.fromEntries(s4.results.map((r) => [r.topology, r]));
for (const [tp, dr] of [["pg-birep", -71063], ["pgedge", -278698], ["bucardo", -531620], ["pg18-birep", -83252]]) {
  a.strictEqual(byT[tp].status, "incompatible"); a.strictEqual(byT[tp].balance_drift, dr);
}
const s4wb = eng.rank({ rpo: "zero", wanRttMs: 25, conflictRate: "high_contention", tco: "high", dataset: "baseline" }, ctx);
a.strictEqual(s4wb.top.topology, "cockroach"); a.strictEqual(s4wb.top.balance_drift, 0); a(s4wb.top.caveats.some((c) => c.includes("40001")));
const s4wo = eng.rank({ rpo: "zero", wanRttMs: 25, conflictRate: "high_contention", tco: "high", dataset: "optimized" }, ctx);
a.strictEqual(s4wo.top.topology, "cockroach-rc"); a.strictEqual(s4wo.top.balance_drift, 0);

// Score transparency across all 32 input combinations + N/A resilience
for (const rpo of ["zero", "async"]) for (const wanRttMs of [0, 10, 25, 50])
  for (const conflictRate of ["none", "disjoint", "counter_crdt", "high_contention"]) for (const dataset of ["baseline", "optimized"]) {
    const res = eng.rank({ rpo, wanRttMs, conflictRate, tco: "medium", dataset }, ctx);
    a.strictEqual(res.results.length, 18);
    for (const r of res.results) a.strictEqual(r.score, Math.max(0, Math.min(100, 54 + r.reasons.reduce((s, x) => s + x.delta, 0))));
  }
const na = eng.rank({}, { LP_PACELC_CATALOG: ctx.LP_PACELC_CATALOG, LP_BENCH_META: { cols: ["topology", "suite", "tps", "lat_p95_ms"] }, LP_BENCH_ROWS_1: [["yugabyte", "A_single_rw", "N/A", ""]] });
a(na.results.every((r) => Number.isFinite(r.score) && (r.tps === null || Number.isFinite(r.tps))));

// UI mock-DOM smoke test (FR, compare->baseline jump, fallback copy, CSV export)
const st = { lang: "fr", tab: "pacelc", mtab: "core", dataset: "compare", sel: new Set() };
let redrawn = 0; ctx.LPPacelcUI.render(st, () => redrawn++);
a(host.innerHTML.includes("RECOMMAND\u00c9") && host.innerHTML.includes("docs/fr/solutions/"));
const clk = (d) => { const b = { dataset: d, textContent: "Make", closest: () => b }; on.click({ target: b }); };
clk({ cp: "make up-pg18-streaming" }); a.strictEqual(copies, 1);
clk({ j: "bench:pgedge-delta-apply" });
a.strictEqual(st.tab, "bench"); a.strictEqual(st.dataset, "baseline"); a(st.sel.has("pgedge-delta-apply") && st.sel.has("pgedge")); a.strictEqual(redrawn, 1);
ctx.LPPacelcUI.exportCSV(); a(dl && dl.download === "pacelc_baseline.csv");
"""
        proc = subprocess.run([node, "-e", js, str(DASH)], capture_output=True, text=True, check=False, timeout=30)
        self.assertEqual(proc.returncode, 0, f"Node PACELC test failed:\n{proc.stdout}\n{proc.stderr}")


if __name__ == "__main__":
    unittest.main()

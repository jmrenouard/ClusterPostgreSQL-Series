/* Production-Tuned (PG_SCALE=20) dataset & Before-vs-After Delta module (zero CDN). */
(function () {
  "use strict";

  const W = window, $ = (id) => document.getElementById(id);
  const { TOPOS, fmtNum, renderBarChart, renderLineChart, esc, isBad } = W.LPCharts;
  const TL = Object.fromEntries(TOPOS.map(([k, v]) => [k, v])), TC = Object.fromEntries(TOPOS.map(([k, , c]) => [k, c])), TO = TOPOS.map(([k]) => k);
  const BCOLS = (W.LP_BENCH_OPT_META || W.LP_BENCH_META || {}).cols || [];
  const OPT_ROWS = (W.LP_BENCH_OPT_ROWS || []).map((a) => Object.fromEntries(BCOLS.map((c, i) => [c, a[i] ?? ""])));
  const OPT_IDX = {};
  OPT_ROWS.forEach((r) => { (OPT_IDX[r.topology] = OPT_IDX[r.topology] || {})[r.suite] = r; });
  const OPT_T = (() => { const s = new Set(OPT_ROWS.map((r) => r.topology)); return [...TO.filter((t) => s.has(t)), ...[...s].filter((t) => !TO.includes(t)).sort()]; })();
  const OPT_S = [...new Set(OPT_ROWS.map((r) => r.suite))];

  let baseTheadHtml = "";
  const cmpSort = { col: "oTps", dir: -1 };
  const lbl = (m, t) => (m !== "baseline" && t === "pgedge" ? "pgEdge (delta_apply)" : m !== "baseline" && t === "cockroach" ? "CockroachDB (Ser)" : TL[t] || t);
  const dot = (t) => `<span class="dot" style="background:${TC[t] || "#64748b"}"></span>`, bdg = (c, x) => `<span class="badge ${c}">${esc(x)}</span>`;

  function cmpTip(p, mLbl) {
    const rw = (k, v, cls) => `<div class="tt-row"><span class="tt-k">${k}</span><span class="${cls || "tt-v"}">${v}</span></div>`;
    const sp = p.ratio > 0 ? `${p.ratio.toFixed(2)}x (${p.pct >= 0 ? "+" : ""}${p.pct.toFixed(0)}%)` : "New RC";
    return `<div class="tt-title">${esc(lbl("optimized", p.topology))} (${esc(mLbl)})</div>` +
      rw("Suite", esc(p.suite)) + rw("Baseline TPS", p.bTps > 0 ? fmtNum(p.bTps) : "N/A (New)") + rw("Tuned TPS", fmtNum(p.oTps)) +
      rw("Speedup", sp, p.ratio >= 1 ? "tt-ok" : "tt-v") + rw("p95 (Base/Tuned)", `${p.bP95 > 0 ? fmtNum(p.bP95) : "-"} / ${fmtNum(p.oP95)} ms`) +
      rw("Drift (Base/Tuned)", `${p.bDrift} / ${p.oDrift}`, p.oDrift === 0 ? "tt-ok" : "tt-bad");
  }

  function buildPairs(baseIdx, st, allTopos, e1Suite) {
    const q = st.qB.trim().toLowerCase();
    const suites = st.suite === "CORE_ALL" ? ["A_single_rw", "B2_overlap_rw", "D_hot_conflict", e1Suite, "H_append_only_insert", "F_wan_netem_25ms"].filter(Boolean)
      : st.suite === "SWEEP_CONC" ? ["G_conc_c1", "G_conc_c4", "G_conc_c8", "G_conc_c16", "G_conc_c32"]
      : st.suite === "SWEEP_WAN" ? ["A_single_rw", "F_wan_netem_10ms", "F_wan_netem_25ms", "F_wan_netem_50ms"] : [st.suite];
    const out = [];
    allTopos.filter((t) => st.sel.has(t)).forEach((t) => suites.forEach((su) => {
      const orow = OPT_IDX[t] && OPT_IDX[t][su];
      if (!orow) return;
      const brow = (t !== "cockroach-rc" && baseIdx[t] && baseIdx[t][su]) || null;
      if (q && !`${t} ${lbl("optimized", t)} ${su} ${orow.convergence_status}`.toLowerCase().includes(q)) return;
      const bTps = brow ? +brow.tps : 0, oTps = +orow.tps, bP95 = brow ? +brow.lat_p95_ms : 0, oP95 = +orow.lat_p95_ms;
      const bDrift = brow ? +(brow.balance_drift || 0) : 0, oDrift = +(orow.balance_drift || 0);
      out.push({
        topology: t, suite: su, base: brow, opt: orow, bTps, oTps, bP95, oP95, bDrift, oDrift,
        ratio: bTps > 0 ? oTps / bTps : 0, pct: bTps > 0 ? ((oTps - bTps) / bTps) * 100 : 0,
        fixedDrift: Boolean(brow && isBad(brow) && !isBad(orow)), oBad: isBad(orow), bBad: brow ? isBad(brow) : false,
      });
    }));
    return out;
  }

  function renderCompare(baseIdx, st, allTopos, e1Suite) {
    const fr = st.lang === "fr", pairs = buildPairs(baseIdx, st, allTopos, e1Suite);
    const kc = (c, l, v, s) => `<div class="kpi-card ${c}"><div class="kpi-label">${esc(l)}</div><div class="kpi-val">${v}</div><div class="kpi-sub">${s}</div></div>`;
    if (!pairs.length) $("kpi-grid").innerHTML = "";
    else {
      const wr = pairs.filter((p) => p.ratio > 0), topSp = wr.length ? wr.reduce((a, b) => (b.ratio > a.ratio ? b : a)) : null;
      const pkT = pairs.reduce((a, b) => (b.oTps > a.oTps ? b : a)), fxN = pairs.filter((p) => p.fixedDrift).length, okN = pairs.filter((p) => !p.oBad).length;
      $("kpi-grid").innerHTML = [
        kc("kpi-ok", fr ? "Gain max (Optimis\u00e9/Base)" : "Top Speedup (Tuned/Base)", topSp ? `${topSp.ratio.toFixed(2)}x` : "N/A", topSp ? `${esc(lbl("optimized", topSp.topology))} &middot; ${esc(topSp.suite)}` : "-"),
        kc("", fr ? "Pic TPS Optimis\u00e9 (SCALE=20)" : "Peak Tuned TPS (SCALE=20)", `${fmtNum(pkT.oTps)} TPS`, `${esc(lbl("optimized", pkT.topology))} &middot; ${esc(pkT.suite)}`),
        kc("kpi-ok", fr ? "D\u00e9rives corrig\u00e9es" : "Integrity Fixes (0 Drift)", `${fxN} fixed`, fxN ? "pgEdge CRDT delta_apply & BiRep B2" : (fr ? "0 d\u00e9rive sur s\u00e9lection" : "All selected clean")),
        kc(okN < pairs.length ? "kpi-amber" : "kpi-ok", fr ? "Int\u00e9grit\u00e9 Optimis\u00e9e" : "Tuned Integrity Pass", `${okN}/${pairs.length} OK`, `${pairs.length - okN} LWW D_hot/B2`),
      ].join("");
    }
    const cT = $("chart-tps"), cL = $("chart-lat"), ts = allTopos.filter((t) => st.sel.has(t) && OPT_IDX[t]), lf = st.lat === "p95" ? "lat_p95_ms" : "lat_avg_ms";
    $("badge-scale-tps").textContent = $("badge-scale-lat").textContent = st.scale === "log" ? "log10" : "linear";
    if (!ts.length) cT.innerHTML = cL.innerHTML = `<div class="chart-empty">${esc(fr ? "S\u00e9lectionnez au moins une solution." : "Select at least one solution above.")}</div>`;
    else if ((st.suite === "SWEEP_CONC" || st.suite === "SWEEP_WAN") && ts.length <= 8) {
      const isC = st.suite === "SWEEP_CONC", seq = isC ? ["G_conc_c1", "G_conc_c4", "G_conc_c8", "G_conc_c16", "G_conc_c32"] : ["A_single_rw", "F_wan_netem_10ms", "F_wan_netem_25ms", "F_wan_netem_50ms"], xl = isC ? ["c=1", "c=4", "c=8", "c=16", "c=32"] : ["0 ms", "10 ms", "25 ms", "50 ms"];
      const mkL = (f) => ts.flatMap((t) => {
        const col = TC[t] || "#334155", res = [{ label: `${lbl("optimized", t)} (Tuned)`, color: col, points: seq.map((s) => { const r = OPT_IDX[t][s]; return r ? { v: +r[f], tip: `<b>${esc(lbl("optimized", t))} Tuned</b><br>${esc(s)}: ${fmtNum(r[f])}` } : null; }) }];
        if (t !== "cockroach-rc" && baseIdx[t]) res.push({ label: `${lbl("baseline", t)} (Base)`, color: col, dash: true, points: seq.map((s) => { const r = baseIdx[t][s]; return r ? { v: +r[f], tip: `<b>${esc(lbl("baseline", t))} Base</b><br>${esc(s)}: ${fmtNum(r[f])}` } : null; }) });
        return res;
      });
      $("title-tps").textContent = fr ? "D\u00e9bit (TPS) : Pointill\u00e9=Base vs Plein=Optimis\u00e9" : "Throughput (TPS): Dashed=Base vs Solid=Tuned";
      $("title-lat").textContent = fr ? "Latence (ms) : Pointill\u00e9=Base vs Plein=Optimis\u00e9" : "Latency (ms): Dashed=Base vs Solid=Tuned";
      renderLineChart(cT, { xLabels: xl, series: mkL("tps"), scale: st.scale, unit: "tps" });
      renderLineChart(cL, { xLabels: xl, series: mkL(lf), scale: st.scale, unit: "ms" });
    } else {
      const su = st.suite === "SWEEP_CONC" ? "G_conc_c32" : st.suite === "SWEEP_WAN" ? "F_wan_netem_25ms" : st.suite === "CORE_ALL" ? "A_single_rw" : st.suite;
      const cats = ts.filter((t) => OPT_IDX[t][su]).map((t) => ({ key: t, label: lbl("optimized", t) }));
      const pMap = Object.fromEntries(buildPairs(baseIdx, { ...st, suite: su, qB: "" }, allTopos, e1Suite).map((p) => [p.topology, p]));
      const mkB = (f) => [
        { label: "Baseline (SCALE=2)", color: "#64748b", values: cats.map((c) => { const p = pMap[c.key]; return p && p.base ? { v: +p.base[f], bad: p.bBad, tip: cmpTip(p, "Baseline") } : null; }) },
        { label: "Tuned (SCALE=20)", color: "#0284c7", values: cats.map((c) => { const p = pMap[c.key]; return p ? { v: +p.opt[f], color: p.fixedDrift ? "#16a34a" : (p.oBad ? "#dc2626" : "#0284c7"), bad: p.oBad, good: p.fixedDrift, tip: cmpTip(p, "Tuned") } : null; }) },
      ];
      $("title-tps").textContent = `${fr ? "D\u00e9bit (TPS) Avant/Apr\u00e8s" : "TPS Before vs After"} (${su})`;
      $("title-lat").textContent = `${fr ? "Latence (ms) Avant/Apr\u00e8s" : "Latency (ms) Before vs After"} (${su})`;
      renderBarChart(cT, { categories: cats, series: mkB("tps"), scale: st.scale, unit: "tps" });
      renderBarChart(cL, { categories: cats, series: mkB(lf), scale: st.scale, unit: "ms" });
    }
    renderCompareTable(pairs, st);
  }

  function renderCompareTable(pairs, st) {
    const thead = $("bench-thead"), fr = st.lang === "fr", loc = fr ? "fr-FR" : "en-US";
    if (!baseTheadHtml) baseTheadHtml = thead.innerHTML;
    thead.innerHTML = `<tr><th data-csort="topology">${fr ? "Topologie" : "Topology"}</th><th data-csort="suite">Suite</th><th data-csort="bTps" class="num">Base TPS</th><th data-csort="oTps" class="num">${fr ? "Optim. TPS" : "Tuned TPS"}</th><th data-csort="ratio" class="num">Delta</th><th data-csort="bP95" class="num">Base p95</th><th data-csort="oP95" class="num">Tuned p95</th><th data-csort="bDrift" class="num">Base Drift</th><th data-csort="oDrift" class="num">Tuned Drift</th><th>${fr ? "Statut" : "Status"}</th></tr>`;
    const c = cmpSort.col, d = cmpSort.dir;
    const sr = [...pairs].sort((a, b) => (typeof a[c] === "number" ? (a[c] - b[c]) * d : String(a[c]).localeCompare(String(b[c])) * d));
    thead.querySelectorAll("th[data-csort]").forEach((th) => { th.classList.toggle("sorted", th.dataset.csort === c); th.onclick = () => { cmpSort.dir = cmpSort.col === th.dataset.csort ? -cmpSort.dir : -1; cmpSort.col = th.dataset.csort; renderCompareTable(pairs, st); }; });
    const nf = (v, m) => Number(v || 0).toLocaleString(loc, m ? { maximumFractionDigits: m } : undefined);
    $("bench-tbody").innerHTML = sr.map((p) => {
      const dB = p.ratio <= 0 ? bdg("delta-new", "New RC") : bdg(p.ratio >= 1 ? "delta-up" : "delta-dn", `${p.ratio.toFixed(2)}x (${p.pct >= 0 ? "+" : ""}${p.pct.toFixed(0)}%)`);
      const sB = p.fixedDrift ? bdg("badge-ok", "FIXED (0 drift)") : bdg(p.oBad ? "badge-err" : "badge-ok", p.opt.convergence_status || "PASS");
      return `<tr><td><span class="topo-cell">${dot(p.topology)}${esc(lbl("optimized", p.topology))}</span></td><td>${esc(p.suite)}</td><td class="num">${p.bTps > 0 ? nf(p.bTps, 2) : "&mdash;"}</td><td class="num"><strong>${nf(p.oTps, 2)}</strong></td><td class="num">${dB}</td><td class="num">${p.bP95 > 0 ? fmtNum(p.bP95) : "&mdash;"}</td><td class="num">${fmtNum(p.oP95)}</td><td class="num">${p.base ? bdg(p.bDrift ? "badge-err" : "badge-ok", p.bDrift ? nf(p.bDrift) : "0") : "&mdash;"}</td><td class="num">${bdg(p.oDrift ? "badge-err" : "badge-ok", p.oDrift ? nf(p.oDrift) : "0 drift")}</td><td>${sB}</td></tr>`;
    }).join("");
  }

  function syncUI(mode, lang) {
    const thead = $("bench-thead"), isB = mode === "baseline", fr = lang === "fr";
    if (thead && !baseTheadHtml) baseTheadHtml = thead.innerHTML;
    if (mode !== "compare" && thead && baseTheadHtml && thead.querySelector("th[data-csort]")) thead.innerHTML = baseTheadHtml;
    const allBtn = document.querySelector('[data-preset="all"]'), solLbl = $("sol-count-label");
    if (allBtn) allBtn.textContent = isB ? (fr ? "Toutes (17)" : "All 17") : (fr ? "Toutes (18 topologies)" : "All 18 Topologies");
    if (solLbl) solLbl.textContent = isB ? (fr ? "Solutions (17 topologies)" : "Solutions (17 Topologies)") : (fr ? "Solutions (18 topologies)" : "Solutions (18 Topologies)");
  }

  function exportCompareCSV(baseIdx, st, allTopos, e1Suite) {
    const pairs = buildPairs(baseIdx, st, allTopos, e1Suite), q = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const cols = ["topology", "suite", "base_tps", "tuned_tps", "speedup_x", "base_p95_ms", "tuned_p95_ms", "base_drift", "tuned_drift", "tuned_status"];
    const rows = pairs.map((p) => [p.topology, p.suite, p.bTps || "", p.oTps, p.ratio ? p.ratio.toFixed(3) : "", p.bP95 || "", p.oP95, p.base ? p.bDrift : "", p.oDrift, p.opt.convergence_status].map(q).join(","));
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(new Blob([[cols.join(","), ...rows].join("\n") + "\n"], { type: "text/csv;charset=utf-8;" })), download: "cluster_pg_before_after_delta.csv" });
    a.click(); URL.revokeObjectURL(a.href);
  }

  W.LPOpt = { OPT_ROWS, OPT_IDX, OPT_T, OPT_S, lbl, syncUI, renderCompare, exportCompareCSV, meta: W.LP_BENCH_OPT_META || {} };
})();

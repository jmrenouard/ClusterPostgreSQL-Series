/* Offline Benchmark Explorer controller (Baseline PG_SCALE=2, Tuned PG_SCALE=20, Delta, Matrix, Popularity). */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id), $$ = (s) => document.querySelectorAll(s);
  const { TOPOS, SNAME, fmtNum, renderBarChart, renderLineChart, esc, isBad, makeTip } = window.LPCharts;
  const TL = Object.fromEntries(TOPOS.map(([k, v]) => [k, v])), TC = Object.fromEntries(TOPOS.map(([k, , c]) => [k, c])), TO = TOPOS.map(([k]) => k);
  const SCOL = ["#1e40af", "#0ea5e9", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"];
  const MSG = {
    kpiPeak: ["Peak Selected TPS", "Pic TPS"], kpiLat: ["Lowest Avg Latency", "Meilleure latence"],
    kpiWan: ["WAN 25ms Leader", "Leader WAN 25ms"], kpiInt: ["Integrity Check", "Int\u00e9grit\u00e9"],
    noSel: ["Select at least one solution above.", "S\u00e9lectionnez au moins une solution."],
    tTps: ["Throughput (TPS)", "D\u00e9bit (TPS)"], tLat: ["Transaction Latency (ms)", "Latence transactionnelle (ms)"],
  };

  const W = window, upk = (c, r) => (r || []).map((a) => Object.fromEntries(c.map((k, i) => [k, a[i] ?? ""])));
  const BCOLS = (W.LP_BENCH_META || {}).cols || [];
  const BASE_BENCH = upk(BCOLS, [].concat(W.LP_BENCH_ROWS_1 || [], W.LP_BENCH_ROWS_2 || [], W.LP_BENCH_ROWS_3 || [], W.LP_BENCH_ROWS_PG18 || [], W.LP_BENCH_ROWS_YT || []));
  const MAT = (W.LPMatrix && W.LPMatrix.MAT) || { core: { cols: [], rows: [] }, ext: { cols: [], rows: [] }, pg18: { cols: [], rows: [] }, yt: { cols: [], rows: [] } };
  const BASE_T = (() => { const s = new Set([...BASE_BENCH, ...MAT.core.rows, ...MAT.pg18.rows, ...MAT.yt.rows].map((r) => r.topology)); return [...TO.filter((t) => s.has(t)), ...[...s].filter((t) => !TO.includes(t)).sort()]; })();
  const BASE_S = [...new Set(BASE_BENCH.map((r) => r.suite))], BASE_IDX = {};
  BASE_BENCH.forEach((r) => { (BASE_IDX[r.topology] = BASE_IDX[r.topology] || {})[r.suite] = r; });
  const Opt = W.LPOpt || null;

  const st = { lang: "en", tab: "bench", mtab: "core", dataset: "baseline", scale: "log", lat: "both", suite: "CORE_ALL", sel: new Set(BASE_T), sort: "tps", dir: -1, qB: "", qM: "" };
  const isB = () => st.dataset === "baseline" || !Opt;
  const curT = () => (isB() ? BASE_T : Opt.OPT_T), curR = () => (isB() ? BASE_BENCH : Opt.OPT_ROWS), curI = () => (isB() ? BASE_IDX : Opt.OPT_IDX), curS = () => (isB() ? BASE_S : Opt.OPT_S);
  const tLbl = (t) => (Opt ? Opt.lbl(st.dataset, t) : TL[t] || t);
  const e1S = (ss) => ["E1_sysbench_oltp_rw", "E_sysbench_oltp_rw"].find((s) => ss.includes(s)) || "";
  const tr = (k) => (MSG[k] ? MSG[k][st.lang === "fr" ? 1 : 0] : k);
  const dot = (t) => `<span class="dot" style="background:${TC[t] || "#64748b"}"></span>`, bdg = (c, x) => `<span class="badge ${c}">${esc(x)}</span>`;
  const getR = (t, s) => { const ix = curI(); return (ix[t] && ix[t][s]) || null; };

  function buildControls() {
    const p = $("topo-pills");
    p.innerHTML = "";
    curT().forEach((t) => {
      const on = st.sel.has(t), lb = document.createElement("label");
      lb.className = "topo-pill" + (on ? " active" : "");
      lb.style.borderColor = on ? (TC[t] || "#64748b") : "";
      lb.innerHTML = `<input type="checkbox"${on ? " checked" : ""}>${dot(t)}<span>${esc(tLbl(t))}</span>`;
      lb.firstChild.onchange = (e) => { e.target.checked ? st.sel.add(t) : st.sel.delete(t); renderAll(); };
      p.appendChild(lb);
    });
    const sel = $("suite-select");
    if (!sel.options.length) { ["CORE_ALL", "SWEEP_CONC", "SWEEP_WAN", ...BASE_S].forEach((k) => sel.add(new Option(SNAME[k] || k, k))); sel.value = st.suite; }
    const bm = W.LP_BENCH_META || {};
    $("meta-stamp").textContent = isB() ? `${BASE_BENCH.length} rows | ${BASE_T.filter((t) => t !== "pgedge-delta-apply").length} topologies | PG_SCALE=2 | ${bm.generated_utc || ""}` : `${Opt.OPT_ROWS.length} rows | ${Opt.OPT_T.length} topologies | PG_SCALE=${Opt.meta.pg_scale || 20} | ${Opt.meta.generated_utc || ""}`;
  }

  function fBench() {
    const q = st.qB.trim().toLowerCase();
    return curR().filter((r) => st.sel.has(r.topology) && (["CORE_ALL", "SWEEP_CONC", "SWEEP_WAN"].includes(st.suite) || r.suite === st.suite) && (!q || `${r.topology} ${tLbl(r.topology)} ${r.suite} ${r.convergence_status}`.toLowerCase().includes(q)));
  }

  function renderKPIs(rows) {
    if (!rows.length) { $("kpi-grid").innerHTML = ""; return; }
    const pk = rows.reduce((a, b) => (+b.tps > +a.tps ? b : a));
    const vl = rows.filter((r) => +r.lat_avg_ms > 0), bl = vl.length ? vl.reduce((a, b) => (+b.lat_avg_ms < +a.lat_avg_ms ? b : a)) : null;
    const wr = curR().filter((r) => st.sel.has(r.topology) && r.suite === "F_wan_netem_25ms"), bw = wr.length ? wr.reduce((a, b) => (+b.tps > +a.tps ? b : a)) : null;
    const bc = rows.filter(isBad).length, nm = (t) => esc(tLbl(t));
    const kc = (c, l, v, s) => `<div class="kpi-card ${c}"><div class="kpi-label">${esc(l)}</div><div class="kpi-val">${v}</div><div class="kpi-sub">${s}</div></div>`;
    $("kpi-grid").innerHTML = [
      kc("", tr("kpiPeak"), `${fmtNum(pk.tps)} TPS`, `${nm(pk.topology)} &middot; ${esc(pk.suite)}`),
      kc("kpi-ok", tr("kpiLat"), bl ? `${fmtNum(bl.lat_avg_ms)} ms` : "N/A", bl ? `${nm(bl.topology)} &middot; ${esc(bl.suite)}` : "-"),
      kc("kpi-amber", tr("kpiWan"), bw ? `${fmtNum(bw.tps)} TPS` : "N/A", bw ? `${nm(bw.topology)} (${fmtNum(bw.lat_avg_ms)} ms)` : "-"),
      kc(bc ? "kpi-err" : "kpi-ok", tr("kpiInt"), `${rows.length - bc}/${rows.length} OK`, bc ? `${bc} LOST/DIVERGED` : "0 drift"),
    ].join("");
  }

  function renderCharts() {
    const cT = $("chart-tps"), cL = $("chart-lat"), ix = curI(), allS = curS();
    $("title-tps").textContent = tr("tTps"); $("title-lat").textContent = tr("tLat");
    $("badge-scale-tps").textContent = $("badge-scale-lat").textContent = st.scale === "log" ? "log10" : "linear";
    const ts = curT().filter((t) => st.sel.has(t) && ix[t] && (st.suite === "D_hot_conflict" || t !== "pgedge-delta-apply"));
    if (!ts.length) { cT.innerHTML = cL.innerHTML = `<div class="chart-empty">${esc(tr("noSel"))}</div>`; return; }
    const lf = st.lat === "p95" ? "lat_p95_ms" : "lat_avg_ms";
    if (st.suite === "SWEEP_CONC" || st.suite === "SWEEP_WAN") {
      const isC = st.suite === "SWEEP_CONC", ms = allS.map((s) => [s, s.match(isC ? /^G_conc_c?(\d+)$/ : /^F_wan_netem_(\d+)ms$/)]).filter(([, m]) => m).sort((a, b) => a[1][1] - b[1][1]);
      const xl = isC ? ms.map(([, m]) => "c=" + m[1]) : ["0 ms", ...ms.map(([, m]) => m[1] + " ms")], seq = isC ? ms.map(([s]) => s) : ["A_single_rw", ...ms.map(([s]) => s)];
      const mk = (f) => ts.map((t) => ({ label: tLbl(t), color: TC[t] || "#334155", points: seq.map((s) => { const r = getR(t, s); return r ? { v: +r[f], tip: makeTip(r) } : null; }) }));
      renderLineChart(cT, { xLabels: xl, series: mk("tps"), scale: st.scale, unit: "tps", emptyMsg: tr("noSel") });
      renderLineChart(cL, { xLabels: xl, series: mk(lf), scale: st.scale, unit: "ms", emptyMsg: tr("noSel") });
      return;
    }
    const cats = ts.map((t) => ({ key: t, label: tLbl(t) }));
    if (st.suite === "CORE_ALL") {
      const sl = ["A_single_rw", "B1_disjoint_rw", "C_multinode_ro", e1S(allS), "H_append_only_insert"].filter((s) => s && allS.includes(s));
      const mk = (f) => sl.map((s, si) => ({ label: (SNAME[s] || s).split(":")[0] + ": " + s.split("_").slice(1, 3).join(" "), color: SCOL[si % SCOL.length], values: cats.map((c) => { const r = getR(c.key, s); return r ? { v: +r[f], tip: makeTip(r), bad: isBad(r) } : null; }) }));
      renderBarChart(cT, { categories: cats, series: mk("tps"), scale: st.scale, unit: "tps" });
      renderBarChart(cL, { categories: cats, series: mk(lf), scale: st.scale, unit: "ms" });
      return;
    }
    const su = st.suite, pt = (k, f, col) => { const r = getR(k, su); return r ? { v: +r[f], color: col, tip: makeTip(r), bad: isBad(r), good: !isBad(r) && su === "D_hot_conflict" } : null; };
    renderBarChart(cT, { categories: cats, scale: st.scale, unit: "tps", series: [{ label: su, color: "#0284c7", values: cats.map((c) => pt(c.key, "tps", TC[c.key])) }] });
    const ls = [["p95", "Avg ms", "#0ea5e9", "lat_avg_ms"], ["avg", "p95 ms", "#6366f1", "lat_p95_ms"]].filter(([ex]) => st.lat !== ex).map(([, lb, col, f]) => ({ label: lb, color: col, values: cats.map((c) => pt(c.key, f)) }));
    renderBarChart(cL, { categories: cats, series: ls, scale: st.scale, unit: "ms" });
  }

  function renderTable(rows) {
    const c = st.sort, d = st.dir, loc = st.lang === "fr" ? "fr-FR" : "en-US";
    const sr = [...rows].sort((a, b) => { const an = +a[c], bn = +b[c]; return (a[c] !== "" && b[c] !== "" && !Number.isNaN(an) && !Number.isNaN(bn)) ? (an - bn) * d : String(a[c] ?? "").localeCompare(String(b[c] ?? "")) * d; });
    $$("#bench-table th[data-sort]").forEach((th) => { th.classList.toggle("sorted", th.dataset.sort === c); th.onclick = () => { st.dir = st.sort === th.dataset.sort ? -st.dir : -1; st.sort = th.dataset.sort; renderTable(fBench()); }; });
    const n = (v, m) => (+(v || 0)).toLocaleString(loc, m ? { maximumFractionDigits: m } : undefined);
    $("bench-tbody").innerHTML = sr.map((r) => { const dr = +(r.balance_drift || 0); return `<tr><td><span class="topo-cell">${dot(r.topology)}${esc(tLbl(r.topology))}</span></td><td>${esc(r.suite)}</td><td class="num">${esc(r.clients)}</td><td class="num"><strong>${n(r.tps, 2)}</strong></td><td class="num">${fmtNum(r.lat_avg_ms)}</td><td class="num">${fmtNum(r.lat_p95_ms)}</td><td class="num">${n(r.tx_committed)}</td><td class="num">${esc(r.retries_40001 || 0)}</td><td>${bdg(isBad(r) ? "badge-err" : "badge-ok", r.convergence_status || "PASS")}</td><td class="num">${bdg(dr ? "badge-err" : "badge-ok", dr ? (dr > 0 ? "+" : "") + n(dr) : "0 drift")}</td></tr>`; }).join("");
  }

  function exportCSV() {
    if (st.tab === "popularity" && W.LPPopularity) return W.LPPopularity.exportCSV();
    if (st.tab === "bench" && st.dataset === "compare" && Opt) return Opt.exportCompareCSV(BASE_IDX, st, Opt.OPT_T, e1S(Opt.OPT_S));
    const isB = st.tab === "bench", cols = isB ? BCOLS : MAT[st.mtab].cols, rows = isB ? fBench() : MAT[st.mtab].rows.filter((r) => st.sel.has(r.topology));
    const q = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const csv = [cols.map(q).join(","), ...rows.map((r) => cols.map((c) => q(r[c])).join(","))].join("\n") + "\n";
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" })), download: isB ? `cluster_pg_${st.dataset}_benchmarks.csv` : `cluster_pg_${st.mtab}_matrix.csv` });
    a.click(); URL.revokeObjectURL(a.href);
  }

  function renderAll() {
    buildControls();
    $$("[data-fr]").forEach((e) => { if (!e.dataset.en) e.dataset.en = e.textContent; e.textContent = st.lang === "fr" ? e.dataset.fr : e.dataset.en; });
    if (Opt) Opt.syncUI(st.dataset, st.lang);
    $$("[data-lang]").forEach((b) => b.classList.toggle("active", b.dataset.lang === st.lang));
    const isBench = st.tab === "bench", isMat = st.tab === "matrix", isPop = st.tab === "popularity";
    [["main-controls", isPop], ["bench-controls", !isBench], ["panel-bench", !isBench], ["panel-matrix", !isMat], ["panel-popularity", !isPop]].forEach(([id, h]) => $(id).classList.toggle("hidden", h));
    if (isBench) {
      if (st.dataset === "compare" && Opt) Opt.renderCompare(BASE_IDX, st, Opt.OPT_T, e1S(Opt.OPT_S));
      else { const r = fBench(); renderKPIs(r); renderCharts(); renderTable(r); }
    } else if (isMat && W.LPMatrix) W.LPMatrix.render(st);
    else if (W.LPPopularity) W.LPPopularity.render(st.lang);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const P = { all: "ALL", clear: [], pg18_vs_pg17: TO.slice(0, 10), stream_logical: TO.slice(0, 5), active_active: ["pg-birep", "pg18-birep", "pgedge", "pgedge-delta-apply", "bucardo", "yugabyte", "cockroach", "cockroach-rc", "yt-cluster", "yt-cluster-async"], raft_async: ["pg-birep", "pgedge", "bucardo", "yugabyte", "cockroach", "cockroach-rc"], yt_vs_mm: ["yt-cluster", "yt-cluster-async", "pg18-birep", "pgedge", "yugabyte", "cockroach", "cockroach-rc"] };
    const cmpOr = (fn) => (st.dataset === "compare" && Opt ? Opt.renderCompare(BASE_IDX, st, Opt.OPT_T, e1S(Opt.OPT_S)) : fn());
    const wire = (a, k, cb) => $$(`[${a}]`).forEach((b) => { b.onclick = () => { st[k] = b.getAttribute(a); $$(`[${a}]`).forEach((x) => x.classList.toggle("active", x.getAttribute(a) === st[k])); cb(); }; });
    [["data-lang", "lang", renderAll], ["data-tab", "tab", renderAll], ["data-mtab", "mtab", () => W.LPMatrix && W.LPMatrix.render(st)], ["data-scale", "scale", () => cmpOr(renderCharts)], ["data-lat", "lat", () => cmpOr(renderCharts)]].forEach((x) => wire(...x));
    $$("[data-dataset]").forEach((b) => { b.onclick = () => { const prev = curT(), wasAll = prev.every((t) => st.sel.has(t)); st.dataset = b.dataset.dataset; $$("[data-dataset]").forEach((x) => x.classList.toggle("active", x.dataset.dataset === st.dataset)); const next = curT(); st.sel = wasAll ? new Set(next) : new Set([...st.sel].filter((t) => next.includes(t))); if (!wasAll && st.dataset !== "baseline" && st.sel.has("cockroach")) st.sel.add("cockroach-rc"); renderAll(); }; });
    $$("[data-preset]").forEach((b) => { b.onclick = () => { const allT = curT(), ps = P[b.dataset.preset]; st.sel = new Set(ps === "ALL" ? allT : (ps || []).filter((t) => allT.includes(t))); renderAll(); }; });
    $("suite-select").onchange = (e) => { st.suite = e.target.value; renderAll(); };
    $("table-filter").oninput = (e) => { st.qB = e.target.value; cmpOr(() => renderTable(fBench())); };
    $("matrix-filter").oninput = (e) => { st.qM = e.target.value; if (W.LPMatrix) W.LPMatrix.render(st); };
    $("btn-export").onclick = exportCSV;
    renderAll();
  });
})();

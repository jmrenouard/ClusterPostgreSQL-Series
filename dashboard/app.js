/* Offline Benchmark Explorer controller (15 topologies PG17/PG18, Matrix, Popularity). */
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
    matEmpty: ["Matrix CSV absent; re-run build_dashboard.py.", "CSV absent ; relancez build_dashboard.py."],
    matAll: ["Showing all matrix rows (toggle matching pills above to filter).", "Affichage complet (activez les pilules pour filtrer)."],
  };

  const upk = (cols, raw) => (raw || []).map((a) => Object.fromEntries(cols.map((c, i) => [c, a[i] ?? ""])));
  const BCOLS = (window.LP_BENCH_META || {}).cols || [];
  const BENCH = upk(BCOLS, [].concat(window.LP_BENCH_ROWS_1 || [], window.LP_BENCH_ROWS_2 || [], window.LP_BENCH_ROWS_3 || [], window.LP_BENCH_ROWS_PG18 || []));
  const pMat = (p) => (p && p.cols ? { cols: p.cols, rows: upk(p.cols, p.rows) } : { cols: [], rows: [] });
  const MAT = { core: pMat(window.LP_MATRIX_CORE), ext: pMat(window.LP_MATRIX_EXT), pg18: pMat(window.LP_MATRIX_PG18) };
  const ALL_T = (() => {
    const s = new Set([...BENCH, ...MAT.core.rows, ...MAT.pg18.rows].map((r) => r.topology));
    return [...TO.filter((t) => s.has(t)), ...[...s].filter((t) => !TO.includes(t)).sort()];
  })();
  const ALL_S = [...new Set(BENCH.map((r) => r.suite))];
  const E1 = ["E1_sysbench_oltp_rw", "E_sysbench_oltp_rw"].find((s) => ALL_S.includes(s)) || "";
  const IDX = {};
  BENCH.forEach((r) => { (IDX[r.topology] = IDX[r.topology] || {})[r.suite] = r; });

  const st = { lang: "en", tab: "bench", mtab: "core", scale: "log", lat: "both", suite: "CORE_ALL", sel: new Set(ALL_T), sort: "tps", dir: -1, qB: "", qM: "" };
  const tr = (k) => (MSG[k] ? MSG[k][st.lang === "fr" ? 1 : 0] : k);
  const dot = (t) => `<span class="dot" style="background:${TC[t] || "#64748b"}"></span>`;
  const bdg = (c, x) => `<span class="badge ${c}">${esc(x)}</span>`;
  const getR = (t, s) => (IDX[t] && IDX[t][s]) || null;

  function buildControls() {
    const p = $("topo-pills"); p.innerHTML = "";
    ALL_T.forEach((t) => {
      const on = st.sel.has(t), lb = document.createElement("label");
      lb.className = "topo-pill" + (on ? " active" : "");
      lb.style.borderColor = on ? (TC[t] || "#64748b") : "";
      lb.innerHTML = `<input type="checkbox"${on ? " checked" : ""}>${dot(t)}<span>${esc(TL[t] || t)}</span>`;
      lb.firstChild.onchange = (e) => { e.target.checked ? st.sel.add(t) : st.sel.delete(t); renderAll(); };
      p.appendChild(lb);
    });
    const sel = $("suite-select");
    if (!sel.options.length) { ["CORE_ALL", "SWEEP_CONC", "SWEEP_WAN", ...ALL_S].forEach((k) => sel.add(new Option(SNAME[k] || k, k))); sel.value = st.suite; }
    if (window.LP_BENCH_META) $("meta-stamp").textContent = `${BENCH.length} rows | ${ALL_T.filter((t) => t !== "pgedge-delta-apply").length} topologies | ${window.LP_BENCH_META.generated_utc}`;
  }

  function fBench() {
    const q = st.qB.trim().toLowerCase();
    return BENCH.filter((r) => st.sel.has(r.topology) && (["CORE_ALL", "SWEEP_CONC", "SWEEP_WAN"].includes(st.suite) || r.suite === st.suite) && (!q || `${r.topology} ${TL[r.topology] || ""} ${r.suite} ${r.convergence_status}`.toLowerCase().includes(q)));
  }

  function renderKPIs(rows) {
    if (!rows.length) { $("kpi-grid").innerHTML = ""; return; }
    const pk = rows.reduce((a, b) => (+b.tps > +a.tps ? b : a));
    const vl = rows.filter((r) => +r.lat_avg_ms > 0), bl = vl.length ? vl.reduce((a, b) => (+b.lat_avg_ms < +a.lat_avg_ms ? b : a)) : null;
    const wr = BENCH.filter((r) => st.sel.has(r.topology) && r.suite === "F_wan_netem_25ms"), bw = wr.length ? wr.reduce((a, b) => (+b.tps > +a.tps ? b : a)) : null;
    const bc = rows.filter(isBad).length, nm = (t) => esc(TL[t] || t);
    const kc = (c, l, v, s) => `<div class="kpi-card ${c}"><div class="kpi-label">${esc(l)}</div><div class="kpi-val">${v}</div><div class="kpi-sub">${s}</div></div>`;
    $("kpi-grid").innerHTML = [
      kc("", tr("kpiPeak"), `${fmtNum(pk.tps)} TPS`, `${nm(pk.topology)} &middot; ${esc(pk.suite)}`),
      kc("kpi-ok", tr("kpiLat"), bl ? `${fmtNum(bl.lat_avg_ms)} ms` : "N/A", bl ? `${nm(bl.topology)} &middot; ${esc(bl.suite)}` : "-"),
      kc("kpi-amber", tr("kpiWan"), bw ? `${fmtNum(bw.tps)} TPS` : "N/A", bw ? `${nm(bw.topology)} (${fmtNum(bw.lat_avg_ms)} ms)` : "-"),
      kc(bc ? "kpi-err" : "kpi-ok", tr("kpiInt"), `${rows.length - bc}/${rows.length} OK`, bc ? `${bc} LOST/DIVERGED` : "0 drift"),
    ].join("");
  }

  function renderCharts() {
    const cT = $("chart-tps"), cL = $("chart-lat");
    $("badge-scale-tps").textContent = $("badge-scale-lat").textContent = st.scale === "log" ? "log10" : "linear";
    const ts = ALL_T.filter((t) => st.sel.has(t) && IDX[t] && (st.suite === "D_hot_conflict" || t !== "pgedge-delta-apply"));
    if (!ts.length) { cT.innerHTML = cL.innerHTML = `<div class="chart-empty">${esc(tr("noSel"))}</div>`; return; }
    const lf = st.lat === "p95" ? "lat_p95_ms" : "lat_avg_ms";
    if (st.suite === "SWEEP_CONC" || st.suite === "SWEEP_WAN") {
      const isC = st.suite === "SWEEP_CONC";
      const ms = ALL_S.map((s) => [s, s.match(isC ? /^G_conc_c?(\d+)$/ : /^F_wan_netem_(\d+)ms$/)]).filter(([, m]) => m).sort((a, b) => a[1][1] - b[1][1]);
      const xl = isC ? ms.map(([, m]) => "c=" + m[1]) : ["0 ms", ...ms.map(([, m]) => m[1] + " ms")];
      const seq = isC ? ms.map(([s]) => s) : ["A_single_rw", ...ms.map(([s]) => s)];
      const mk = (f) => ts.map((t) => ({ label: TL[t] || t, color: TC[t] || "#334155", points: seq.map((s) => { const r = getR(t, s); return r ? { v: +r[f], tip: makeTip(r) } : null; }) }));
      renderLineChart(cT, { xLabels: xl, series: mk("tps"), scale: st.scale, unit: "tps", emptyMsg: tr("noSel") });
      renderLineChart(cL, { xLabels: xl, series: mk(lf), scale: st.scale, unit: "ms", emptyMsg: tr("noSel") });
      return;
    }
    const cats = ts.map((t) => ({ key: t, label: TL[t] || t }));
    if (st.suite === "CORE_ALL") {
      const sl = ["A_single_rw", "B1_disjoint_rw", "C_multinode_ro", E1, "H_append_only_insert"].filter((s) => s && ALL_S.includes(s));
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
    const sr = [...rows].sort((a, b) => {
      const an = +a[c], bn = +b[c];
      return (a[c] !== "" && b[c] !== "" && !Number.isNaN(an) && !Number.isNaN(bn)) ? (an - bn) * d : String(a[c] ?? "").localeCompare(String(b[c] ?? "")) * d;
    });
    $$("#bench-table th[data-sort]").forEach((th) => th.classList.toggle("sorted", th.dataset.sort === c));
    $("bench-tbody").innerHTML = sr.map((r) => {
      const dr = +(r.balance_drift || 0), n = (v, m) => (+(v || 0)).toLocaleString(loc, m ? { maximumFractionDigits: m } : undefined);
      return `<tr><td><span class="topo-cell">${dot(r.topology)}${esc(TL[r.topology] || r.topology)}</span></td><td>${esc(r.suite)}</td>` +
        `<td class="num">${esc(r.clients)}</td><td class="num"><strong>${n(r.tps, 2)}</strong></td>` +
        `<td class="num">${fmtNum(r.lat_avg_ms)}</td><td class="num">${fmtNum(r.lat_p95_ms)}</td>` +
        `<td class="num">${n(r.tx_committed)}</td><td class="num">${esc(r.retries_40001 || 0)}</td>` +
        `<td>${bdg(isBad(r) ? "badge-err" : "badge-ok", r.convergence_status || "PASS")}</td>` +
        `<td class="num">${bdg(dr ? "badge-err" : "badge-ok", dr ? (dr > 0 ? "+" : "") + n(dr) : "0 drift")}</td></tr>`;
    }).join("");
  }

  function renderMatrix() {
    const ds = MAT[st.mtab], nt = $("matrix-notice");
    if (!ds.rows.length) { nt.textContent = tr("extPending"); nt.classList.remove("hidden"); $("matrix-thead").innerHTML = $("matrix-tbody").innerHTML = ""; return; }
    nt.classList.add("hidden");
    const q = st.qM.trim().toLowerCase();
    const rows = ds.rows.filter((r) => st.sel.has(r.topology) && (!q || Object.values(r).join(" ").toLowerCase().includes(q)));
    $("matrix-thead").innerHTML = `<tr>${ds.cols.map((c) => `<th>${esc(c.replace(/_/g, " "))}</th>`).join("")}</tr>`;
    const rxs = [[/^EXPECTED_LIMITATION:?\s*/i, "badge-warn", "LIMIT"], [/^PASS:?\s*/i, "badge-ok", "PASS"], [/^PARTIAL:?\s*/i, "badge-warn", "PARTIAL"], [/^N\/A:?\s*/i, "badge-na", "N/A"]];
    $("matrix-tbody").innerHTML = rows.map((r) => `<tr>${ds.cols.map((c) => {
      const v = r[c] || "";
      if (c === "topology") return `<td><span class="topo-cell">${dot(v)}${esc(TL[v] || v)}</span></td>`;
      if (c === "verified_sqlstates") return `<td>${v.split(/[;, ]+/).filter(Boolean).map((s) => `<span class="sql-tag">${esc(s)}</span>`).join("")}</td>`;
      for (const [rx, cls, lb] of rxs) if (rx.test(v)) return `<td>${bdg(cls, lb)} ${esc(v.replace(rx, ""))}</td>`;
      return `<td>${esc(v)}</td>`;
    }).join("")}</tr>`).join("");
  }

  function exportCSV() {
    const isB = st.tab === "bench", cols = isB ? BCOLS : MAT[st.mtab].cols;
    const rows = isB ? fBench() : MAT[st.mtab].rows.filter((r) => st.sel.has(r.topology));
    const q = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const csv = [cols.map(q).join(","), ...rows.map((r) => cols.map((c) => q(r[c])).join(","))].join("\n") + "\n";
    const a = Object.assign(document.createElement("a"), {
      href: URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" })),
      download: isB ? "cluster_pg_filtered_benchmarks.csv" : `cluster_pg_${st.mtab}_matrix.csv`,
    });
    a.click(); URL.revokeObjectURL(a.href);
  }

  function renderAll() {
    buildControls();
    $$("[data-fr]").forEach((e) => { if (!e.dataset.en) e.dataset.en = e.textContent; e.textContent = st.lang === "fr" ? e.dataset.fr : e.dataset.en; });
    $$("[data-lang]").forEach((b) => b.classList.toggle("active", b.dataset.lang === st.lang));
    const isB = st.tab === "bench";
    $("panel-bench").classList.toggle("hidden", !isB);
    $("bench-controls").classList.toggle("hidden", !isB);
    $("panel-matrix").classList.toggle("hidden", isB);
    if (isB) { const r = fBench(); renderKPIs(r); renderCharts(); renderTable(r); } else renderMatrix();
  }

  document.addEventListener("DOMContentLoaded", () => {
    const P = {
      all: ALL_T, clear: [],
      stream_logical: ["pg17-standalone", "pg17-async-streaming", "pg17-sync-streaming", "pg17-logical", "pg-birep"],
      active_active: ["pg-birep", "pgedge", "pgedge-delta-apply", "bucardo", "yugabyte", "cockroach"],
      raft_async: ["pg-birep", "pgedge", "bucardo", "yugabyte", "cockroach"],
    };
    const wire = (a, k, cb) => $$(`[${a}]`).forEach((b) => {
      b.onclick = () => { st[k] = b.getAttribute(a); $$(`[${a}]`).forEach((x) => x.classList.toggle("active", x.getAttribute(a) === st[k])); cb(); };
    });
    [["data-lang", "lang", renderAll], ["data-tab", "tab", renderAll], ["data-mtab", "mtab", renderMatrix], ["data-scale", "scale", renderCharts], ["data-lat", "lat", renderCharts]].forEach((x) => wire(...x));
    $$("[data-preset]").forEach((b) => { b.onclick = () => { st.sel = new Set((P[b.dataset.preset] || []).filter((t) => ALL_T.includes(t))); renderAll(); }; });
    $("suite-select").onchange = (e) => { st.suite = e.target.value; renderAll(); };
    $("table-filter").oninput = (e) => { st.qB = e.target.value; renderTable(fBench()); };
    $("matrix-filter").oninput = (e) => { st.qM = e.target.value; renderMatrix(); };
    $$("#bench-table th[data-sort]").forEach((th) => { th.onclick = () => { const c = th.dataset.sort; st.dir = st.sort === c ? -st.dir : -1; st.sort = c; renderTable(fBench()); }; });
    $("btn-export").onclick = exportCSV;
    renderAll();
  });
})();

/* Pure SVG interactive Log10 / Linear charting engine (zero CDN dependencies). */
(function () {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";

  function el(tag, attrs, text) {
    const node = document.createElementNS(NS, tag);
    if (attrs) for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, String(v));
    if (text !== undefined) node.textContent = String(text);
    return node;
  }

  function fmtNum(v) {
    const n = Number(v);
    if (!Number.isFinite(n) || n === 0) return "0";
    const a = Math.abs(n);
    if (a >= 1e6) return (n / 1e6).toFixed(2) + "M";
    if (a >= 1e4) return (n / 1e3).toFixed(1) + "k";
    if (a >= 1e3) return (n / 1e3).toFixed(2) + "k";
    if (a >= 100) return n.toFixed(0);
    if (a >= 10) return n.toFixed(1);
    return n.toFixed(2);
  }

  function fmtTick(v, unit) {
    if (v <= 0) return "0";
    if (unit === "ms" && v >= 1e3) return (v / 1e3).toFixed(0) + "s";
    let s;
    if (v >= 1e6) s = (v / 1e6).toFixed(0) + "M";
    else if (v >= 1e3) s = (v / 1e3).toFixed(0) + "k";
    else if (v >= 1) s = String(Math.round(v * 100) / 100);
    else s = String(v);
    return unit === "ms" ? s + "ms" : s;
  }

  function logTicks(minVal, maxVal, isMs) {
    const lo = Math.min(isMs ? -1 : 0, Math.floor(Math.log10(Math.max(minVal, isMs ? 0.1 : 1))));
    const hi = Math.max(lo + 1, Math.ceil(Math.log10(Math.max(maxVal * 1.35, isMs ? 10 : 100))));
    const ticks = [];
    for (let e = lo; e <= hi; e++) ticks.push(Math.pow(10, e));
    return { lo: Math.pow(10, lo), hi: Math.pow(10, hi), ticks };
  }

  function linTicks(maxVal) {
    const raw = Math.max(maxVal * 1.15, 1);
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const norm = raw / mag;
    const step = (norm <= 2 ? 0.5 : norm <= 5 ? 1 : 2) * mag;
    const hi = Math.ceil(raw / step) * step;
    const ticks = [];
    for (let v = 0; v <= hi + step * 0.01; v += step) ticks.push(Math.round(v * 1000) / 1000);
    return { lo: 0, hi, ticks };
  }

  function showTip(evt, html) {
    const tip = document.getElementById("lp-tooltip");
    if (!tip) return;
    tip.innerHTML = html;
    tip.classList.remove("hidden");
    const pad = 14;
    const x = Math.min(evt.clientX + pad, window.innerWidth - tip.offsetWidth - 10);
    const y = Math.min(evt.clientY + pad, window.innerHeight - tip.offsetHeight - 10);
    tip.style.left = Math.max(8, x) + "px";
    tip.style.top = Math.max(8, y) + "px";
  }

  function hideTip() {
    const tip = document.getElementById("lp-tooltip");
    if (tip) tip.classList.add("hidden");
  }

  function attachHover(target, html) {
    target.style.cursor = "pointer";
    target.addEventListener("mouseenter", (e) => showTip(e, html));
    target.addEventListener("mousemove", (e) => showTip(e, html));
    target.addEventListener("mouseleave", hideTip);
  }

  function buildAxis(svg, W, H, M, scale, minV, maxV, unit) {
    const plotW = W - M.l - M.r, plotH = H - M.t - M.b, isLog = scale === "log";
    const info = isLog ? logTicks(minV, maxV, unit === "ms") : linTicks(maxV);
    const lLo = isLog ? Math.log10(info.lo) : info.lo, lHi = isLog ? Math.log10(info.hi) : info.hi;
    const yOf = (v) => {
      const frac = isLog
        ? (Math.log10(Math.max(v, info.lo)) - lLo) / Math.max(lHi - lLo, 1e-6)
        : Math.max(0, v) / Math.max(info.hi, 1e-6);
      return M.t + plotH * (1 - frac);
    };
    svg.appendChild(el("rect", { x: M.l, y: M.t, width: plotW, height: plotH, fill: "#f8fafc", rx: 4 }));
    info.ticks.forEach((tk) => {
      const y = yOf(tk);
      svg.appendChild(el("line", { x1: M.l, y1: y, x2: M.l + plotW, y2: y, stroke: "#cbd5e1", "stroke-width": 1 }));
      svg.appendChild(el("text", { x: M.l - 8, y: y + 4, "text-anchor": "end", fill: "#475569", "font-size": 10.5, "font-family": "ui-monospace, monospace" }, fmtTick(tk, unit)));
      if (isLog && tk < info.hi) {
        [2, 5].forEach((mul) => {
          const ym = yOf(tk * mul);
          if (ym >= M.t && ym <= M.t + plotH) svg.appendChild(el("line", { x1: M.l, y1: ym, x2: M.l + plotW, y2: ym, stroke: "#e2e8f0", "stroke-width": 0.7, "stroke-dasharray": "2 3" }));
        });
      }
    });
    svg.appendChild(el("line", { x1: M.l, y1: M.t + plotH, x2: M.l + plotW, y2: M.t + plotH, stroke: "#94a3b8", "stroke-width": 1.2 }));
    svg.appendChild(el("line", { x1: M.l, y1: M.t, x2: M.l, y2: M.t + plotH, stroke: "#94a3b8", "stroke-width": 1.2 }));
    return { plotW, plotH, yOf, baseY: M.t + plotH };
  }

  function renderBarChart(container, opts) {
    container.innerHTML = "";
    const { categories, series, scale, unit, emptyMsg } = opts;
    const allVals = [];
    series.forEach((s) => s.values.forEach((pt) => { if (pt && pt.v > 0) allVals.push(pt.v); }));
    if (!categories.length || !allVals.length) {
      container.innerHTML = `<div class="chart-empty">${emptyMsg || "No data for current selection."}</div>`;
      return;
    }
    const W = 680, H = 355, M = { t: series.length > 1 ? 36 : 18, r: 16, b: 84, l: 62 };
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" });
    const ax = buildAxis(svg, W, H, M, scale, Math.min(...allVals), Math.max(...allVals), unit);
    if (series.length > 1) {
      let lx = M.l;
      series.forEach((s) => {
        svg.appendChild(el("rect", { x: lx, y: 10, width: 10, height: 10, rx: 2, fill: s.color }));
        svg.appendChild(el("text", { x: lx + 14, y: 19, fill: "#334155", "font-size": 10.2, "font-weight": 600 }, s.label));
        lx += Math.max(s.label.length * 6.2 + 24, 88);
      });
    }
    const groupW = ax.plotW / categories.length, barGap = 1.8;
    const maxBarW = Math.min(34, (groupW * 0.8) / series.length);
    const lblFs = categories.length > 11 ? 9.0 : 10.0;
    categories.forEach((cat, ci) => {
      const gx = M.l + ci * groupW + groupW / 2;
      const startX = gx - (series.length * (maxBarW + barGap) - barGap) / 2;
      series.forEach((s, si) => {
        const pt = s.values[ci];
        if (!pt || !(pt.v > 0)) return;
        const bx = startX + si * (maxBarW + barGap), by = ax.yOf(pt.v), bh = Math.max(2, ax.baseY - by);
        const rect = el("rect", { x: bx, y: by, width: maxBarW, height: bh, fill: pt.color || s.color, rx: 2.2, stroke: pt.bad ? "#991b1b" : "none", "stroke-width": pt.bad ? 1.5 : 0 });
        attachHover(rect, pt.tip);
        svg.appendChild(rect);
        if (pt.bad || pt.good) svg.appendChild(el("circle", { cx: bx + maxBarW / 2, cy: Math.max(M.t + 6, by - 5), r: 3.3, fill: pt.bad ? "#dc2626" : "#16a34a", stroke: "#fff", "stroke-width": 1 }));
        if ((series.length === 1 && categories.length <= 16) || (series.length === 2 && categories.length <= 10)) {
          svg.appendChild(el("text", { x: bx + maxBarW / 2, y: Math.max(M.t + 10, by - (pt.bad || pt.good ? 11 : 4)), "text-anchor": "middle", fill: "#1e293b", "font-size": categories.length > 10 ? 8.1 : 9.1, "font-weight": 600 }, fmtNum(pt.v)));
        }
      });
      const tx = gx, ty = ax.baseY + 12;
      svg.appendChild(el("text", { x: tx, y: ty, "text-anchor": "end", fill: "#1e293b", "font-size": lblFs, "font-weight": 600, transform: `rotate(-32 ${tx} ${ty})` }, cat.label));
    });
    container.appendChild(svg);
  }

  function renderLineChart(container, opts) {
    container.innerHTML = "";
    const { xLabels, series, scale, unit, emptyMsg } = opts;
    const allVals = [];
    series.forEach((s) => s.points.forEach((pt) => { if (pt && pt.v > 0) allVals.push(pt.v); }));
    if (!xLabels.length || !allVals.length) {
      container.innerHTML = `<div class="chart-empty">${emptyMsg || "No sweep points for selection."}</div>`;
      return;
    }
    const W = 680, H = 355, M = { t: 20, r: 58, b: 64, l: 62 };
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" });
    const ax = buildAxis(svg, W, H, M, scale, Math.min(...allVals), Math.max(...allVals), unit);
    const stepX = xLabels.length > 1 ? ax.plotW / (xLabels.length - 1) : 0;
    const xOf = (i) => (xLabels.length > 1 ? M.l + i * stepX : M.l + ax.plotW / 2);
    xLabels.forEach((lbl, i) => {
      const x = xOf(i);
      svg.appendChild(el("line", { x1: x, y1: M.t, x2: x, y2: ax.baseY, stroke: "#e2e8f0", "stroke-width": 0.9 }));
      svg.appendChild(el("text", { x, y: ax.baseY + 18, "text-anchor": "middle", fill: "#1e293b", "font-size": 10.5, "font-weight": 600 }, lbl));
    });
    const endLabels = [];
    series.forEach((s) => {
      const valid = s.points.map((pt, i) => (pt && pt.v > 0 ? { i, pt, x: xOf(i), y: ax.yOf(pt.v) } : null)).filter(Boolean);
      if (!valid.length) return;
      if (valid.length >= 2) svg.appendChild(el("path", { d: valid.map((p, idx) => `${idx ? "L" : "M"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" "), fill: "none", stroke: s.color, "stroke-width": 2.3, "stroke-linejoin": "round" }));
      valid.forEach((p) => {
        const dot = el("circle", { cx: p.x, cy: p.y, r: 4.2, fill: s.color, stroke: "#fff", "stroke-width": 1.3 });
        attachHover(dot, p.pt.tip);
        svg.appendChild(dot);
      });
      const last = valid[valid.length - 1];
      const lbl = unit === "ms" && last.pt.v >= 1000 ? (last.pt.v / 1000).toFixed(2) + "s" : fmtNum(last.pt.v) + (unit === "ms" ? "ms" : "");
      endLabels.push({ x: last.x + 7, y: last.y + 3.5, color: s.color, text: lbl });
    });
    endLabels.sort((a, b) => a.y - b.y);
    for (let i = 1; i < endLabels.length; i++) if (endLabels[i].y - endLabels[i - 1].y < 10.5) endLabels[i].y = endLabels[i - 1].y + 10.5;
    endLabels.forEach((p) => svg.appendChild(el("text", { x: p.x, y: Math.min(ax.baseY + 4, p.y), fill: p.color, "font-size": 9.1, "font-weight": 700 }, p.text)));
    container.appendChild(svg);
  }

  const TOPOS = [
    ["pg17-standalone", "PG17 Standalone", "#475569"],
    ["pg17-async-streaming", "PG17 Async Stream", "#0284c7"],
    ["pg17-sync-streaming", "PG17 Sync Stream", "#1d4ed8"],
    ["pg17-logical", "PG17 Logical Uni", "#0891b2"],
    ["pg-birep", "PG17 BiRep", "#0d9488"],
    ["pg18-standalone", "PG18 Standalone", "#0f172a"],
    ["pg18-async-streaming", "PG18 Async Stream", "#06b6d4"],
    ["pg18-sync-streaming", "PG18 Sync Stream", "#2563eb"],
    ["pg18-logical", "PG18 Logical Uni", "#14b8a6"],
    ["pg18-birep", "PG18 BiRep (uuidv7)", "#059669"],
    ["pgedge", "pgEdge Spock (LWW)", "#f59e0b"],
    ["pgedge-delta-apply", "pgEdge delta_apply", "#16a34a"],
    ["bucardo", "Bucardo 5.6", "#ea580c"],
    ["citus", "Citus 14.2", "#7c3aed"],
    ["yugabyte", "YugabyteDB Raft", "#db2777"],
    ["cockroach", "CockroachDB Raft", "#dc2626"],
  ];
  const SNAME = {
    CORE_ALL: "All Core Suites (A / B1 / C / E1)",
    SWEEP_CONC: "Concurrency Sweep Curve (c=1..32)",
    SWEEP_WAN: "WAN RTT Sensitivity Curve (tc netem 0-50ms)",
    A_single_rw: "A: Single-Node RW (c=8)", B1_disjoint_rw: "B1: Multi-Node Disjoint RW",
    B2_overlap_rw: "B2: Multi-Node Overlap RW", C_multinode_ro: "C: Multi-Node Read-Only (c=16)",
    D_hot_conflict: "D: 50-Key Hot-Row Conflict & Drift",
    E_sysbench_oltp_rw: "E1: Sysbench OLTP RW", E1_sysbench_oltp_rw: "E1: Sysbench OLTP RW",
    E2_sysbench_oltp_ro: "E2: Sysbench OLTP RO", E3_sysbench_oltp_wo: "E3: Sysbench OLTP WO",
    E4_sysbench_point_select: "E4: Sysbench Point Select",
    F_wan_netem_10ms: "F: WAN Netem 10ms RTT", F_wan_netem_25ms: "F: WAN Netem 25ms RTT",
    F_wan_netem_50ms: "F: WAN Netem 50ms RTT",
    G_conc_c1: "G: Concurrency c=1", G_conc_c4: "G: Concurrency c=4", G_conc_c8: "G: Concurrency c=8",
    G_conc_c16: "G: Concurrency c=16", G_conc_c32: "G: Concurrency c=32",
    H_append_only_insert: "H: Append-Only Bulk Insert",
  };

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
  const isBad = (r) => Number(r.balance_drift || 0) !== 0 || /DIVERGED|LOST_UPDATE/i.test(String(r.convergence_status || ""));
  const TL = Object.fromEntries(TOPOS.map(([k, v]) => [k, v]));
  function makeTip(r) {
    const b = isBad(r), d = Number(r.balance_drift || 0);
    const rw = (k, v, cls) => `<div class="tt-row"><span class="tt-k">${k}</span><span class="${cls || "tt-v"}">${v}</span></div>`;
    return `<div class="tt-title">${esc(TL[r.topology] || r.topology)}</div>` +
      rw("Suite", esc(r.suite)) + rw("TPS", fmtNum(r.tps)) +
      rw("Avg/p95", `${fmtNum(r.lat_avg_ms)} / ${fmtNum(r.lat_p95_ms)} ms`) +
      rw("TX/40001", `${Number(r.tx_committed || 0).toLocaleString()} / ${r.retries_40001 || 0}`) +
      rw("Status", `${esc(r.convergence_status || "PASS")} (${d || "0 drift"})`, b ? "tt-bad" : "tt-ok");
  }

  window.LPCharts = { el, attachHover, fmtNum, fmtTick, logTicks, linTicks, renderBarChart, renderLineChart, TOPOS, SNAME, esc, isBad, makeTip };
})();

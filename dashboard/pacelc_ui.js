/* Interactive PACELC Selector UI (zero CDN, EN/FR). */
(function () {
  "use strict";
  const W = window, D = document, $$ = (s) => D.querySelectorAll(s), ce = (t) => D.createElement(t);
  const REPO = "https://github.com/jmrenouard/ClusterPostgreSQL-Series/blob/main/";
  const ST = { recommended: "ok:RECOMMENDED/RECOMMAND\u00c9", viable: "new:VIABLE", caution: "warn:CAUTION/PRUDENCE", incompatible: "err:INCOMPATIBLE" };
  const GS = "RPO;rpo;zero:RPO=0|async:RPO>0\nWAN;wanRttMs;0:0ms|10:10ms|25:25ms|50:50ms\nConflicts/Conflits;conflictRate;none:Single/Mono|disjoint:UUIDv7|counter_crdt:CRDT|high_contention:High/Forte\nTCO;tco;low:Low/Bas|medium:Med/Moy|high:High/Haut\nData/Jeu;ds;baseline:S=2|optimized:V5 S=20".split("\n").map((s) => s.split(";"));
  const cfg = { rpo: "zero", wanRttMs: 0, conflictRate: "none", tco: "low" };
  let last, host, st, redraw, wired, C;
  const tx = (s) => { const [e, f] = s.split("/"); return st?.lang === "fr" && f ? f : e; };
  const esc = (x) => C.esc(x), fmt = (x) => (x !== null ? C.fmtNum(x) : "N/A");
  const mp = (a, f) => a.map(f).join(""), dv = (c, h) => `<div class="${c}">${h}</div>`, sp = (c, h) => `<span class="${c}">${h}</span>`;
  const bt = (c, a, h) => `<button type="button" class="${c}" ${a}>${h}</button>`, jb = (s, h) => bt("preset-btn", `data-j="${esc(s)}"`, h);
  const bg = (c, x) => sp(`badge ${c === "new" ? "delta-new" : "badge-" + c}`, esc(x)), dr = (v) => bg(v ? "err" : "ok", v ? v.toLocaleString() : "0");
  const sq = (a) => mp(a, (s) => sp("sql-tag", esc(s))) || "-", sb = (k) => { const [c, l] = (ST[k] || "na:" + k).split(":"); return bg(c, tx(l)); };
  const cp = (x, b) => {
    const ok = () => { const o = b.dataset.l || (b.dataset.l = b.textContent); b.textContent = tx("Copied/Copi\u00e9"); setTimeout(() => (b.textContent = o), 1200); };
    const fb = () => { const a = D.body.appendChild(ce("textarea")); a.value = x; a.select(); try { D.execCommand("copy") && ok(); } catch (_) {} a.remove(); };
    navigator.clipboard?.writeText?.(x).then(ok, fb) ?? fb();
  };
  const jp = (spec) => {
    if (!st || !redraw) return;
    const [tab, tp = ""] = spec.split(":"), mt = tp.replace(/-delta-apply$|-rc$/, "");
    st.tab = tab;
    if (tp) st.sel = new Set(tab === "matrix" ? [mt] : tp === "pgedge-delta-apply" ? [tp, "pgedge"] : [tp]);
    if (tab === "matrix") st.mtab = /^pg18/.test(mt) ? "pg18" : /^yt/.test(mt) ? "yt" : "core";
    ["tab", "mtab"].forEach((a) => $$(`[data-${a}]`).forEach((x) => x.classList.toggle("active", x.dataset[a] === st[a])));
    redraw();
  };
  const html = (res) => {
    const r = res.top, ds = res.inputs.dataset, fr = st?.lang === "fr", sc = (c, h) => `<section class="card ${c}">${h}</section>`;
    const nm = (k) => { const m = C.TOPOS.find((x) => x[0] === k); return `<span class="dot" style="background:${m?.[2] || "#64748b"}"></span>${esc(W.LPOpt ? W.LPOpt.lbl(ds, k) : m?.[1] || k)}`; };
    const ctrl = sc("p-c", mp(GS, ([l, k, o]) => dv("ctrl-group", sp("ctrl-label", esc(tx(l))) + dv("seg", mp(o.split("|"), (p) => { const [v, x] = p.split(":"); return bt(`seg-btn${String(k === "ds" ? ds : cfg[k]) === v ? " active" : ""}`, `data-k="${k}:${v}"`, esc(tx(x))); })))));
    let hero = "";
    if (r) {
      const tp = r.topology, kp = (c, k, v) => dv(c ? `kpi-card kpi-${c}` : "kpi-card", dv("kpi-label", esc(k)) + dv("kpi-val", v));
      hero = sc("p-h" + ({ incompatible: " p-e", caution: " p-w" }[r.status] || ""),
        dv("table-head", dv("topo-cell", `${nm(tp)} ${bg("na", r.solution_id)}${bg("new", r.pacelc_class)}${sb(r.status)}`) + dv("p-sc", `${r.score}/100`)) +
        dv("kpi-grid", kp("", `TPS/p95 (${r.suite_used})`, `${fmt(r.tps)}/${fmt(r.lat_p95_ms)}ms`) + kp(r.balance_drift ? "err" : "ok", tx("Drift/D\u00e9rive"), dr(r.balance_drift)) + kp("amber", "40001/SQL", `${r.retries_40001 || 0} &middot; ${sq(r.verified_sqlstates)}`)) +
        dv("presets", mp(r.reasons, (x) => bg(x.delta >= 0 ? "ok" : "err", `${x.delta >= 0 ? "+" : ""}${x.delta} ${x.text}`))) +
        (r.caveats.length ? `<ul class="p-cv">${mp(r.caveats, (c) => `<li>${esc(c)}</li>`)}</ul>` : "") +
        dv("p-cs", mp([[r.make_cmd, "Make"], [r.mdb_cmd, "mdb"]], ([c, l]) => dv("p-cm", `<code>${esc(c)}</code>${bt("p-cp", `data-cp="${esc(c)}"`, l)}`))) +
        dv("presets", jb("bench:" + tp, "Bench") + jb("matrix:" + tp, esc(tx("Matrix/Matrice"))) + `<a class="preset-btn" href="${REPO}${esc(fr ? r.sheet_fr : r.sheet_en)}" target="_blank" rel="noopener">${esc(tx("Sheet/Fiche"))}</a>`)
      );
    }
    const trs = mp(res.results, (x, i) => `<tr>${mp([`#${i + 1}`, jb("bench:" + x.topology, nm(x.topology)), bg("new", x.pacelc_class), `<b>${x.score}</b>`, sb(x.status), fmt(x.tps), fmt(x.lat_p95_ms), dr(x.balance_drift), sq(x.verified_sqlstates)], (v, j) => `<td${"03567".includes(j) ? ' class="num"' : ""}>${v}</td>`)}</tr>`);
    return ctrl + hero + sc("table-card", dv("table-wrap", `<table class="data-table"><thead><tr>${mp("#|Topology/Topologie|PACELC|Score|Status/Statut|TPS|p95|Drift/D\u00e9rive|SQLSTATE".split("|"), (x) => `<th>${esc(tx(x))}</th>`)}</tr></thead><tbody>${trs}</tbody></table>`));
  };
  const onClick = (e) => {
    const b = e.target.closest("button"), d = b?.dataset;
    if (!d) return;
    if (d.cp) return cp(d.cp, b);
    if (d.j) return jp(d.j);
    if (!d.k) return;
    const [k, v] = d.k.split(":");
    if (k === "ds") { const db = D.querySelector(`[data-dataset="${v}"]`); if (db) return db.click(); st && (st.dataset = v); } else cfg[k] = k === "wanRttMs" ? +v : v;
    draw();
  };
  const draw = () => {
    if (!host || !W.LPPacelcEngine || !(C = W.LPCharts)) return;
    if (!wired) { host.addEventListener("click", onClick); wired = 1; }
    last = W.LPPacelcEngine.rank({ ...cfg, dataset: st?.dataset === "optimized" ? "optimized" : "baseline", lang: st?.lang === "fr" ? "fr" : "en" }, W);
    host.innerHTML = html(last);
  };
  const exportCSV = () => {
    if (!last?.results.length) return;
    const cs = "rank topology pacelc_class score status tps lat_p95_ms balance_drift make_cmd mdb_cmd".split(" ");
    const csv = [cs, ...last.results.map((r, i) => cs.map((c) => `"${String((c === "rank" ? i + 1 : r[c]) ?? "").replace(/"/g, '""')}"`))].map((r) => r.join(",")).join("\n") + "\n";
    const u = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    Object.assign(ce("a"), { href: u, download: `pacelc_${last.inputs.dataset}.csv` }).click(); URL.revokeObjectURL(u);
  };
  W.LPPacelcUI = { render(s, cb) { host = D.getElementById("panel-pacelc"); st = s; redraw = cb || redraw; draw(); }, exportCSV };
})();

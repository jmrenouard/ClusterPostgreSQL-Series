/* Pure-JS PACELC architecture scoring engine (zero CDN, browser + Node.js). */
(function (root, factory) {
  "use strict";
  const api = factory(root);
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.LPPacelcEngine = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (G) {
  "use strict";

  const TIER = { low: 0, medium: 1, high: 2 };
  const PAR = { "pgedge-delta-apply": "pgedge", "cockroach-rc": "cockroach", "yt-cluster-async": "yt-cluster" };
  const upk = (c, r) => (r || []).map((a) => Object.fromEntries(c.map((k, i) => [k, a[i] ?? ""])));

  function loadCatalog(ctx) {
    const c = ctx.LP_PACELC_CATALOG || {}, p = c.sheet_prefix || {};
    const enP = p.en || "docs/en/solutions/", frP = p.fr || "docs/fr/solutions/";
    return { caveats: c.caveats || {}, items: upk(c.cols || [], c.rows).map((it) => ({ ...it, sheet_en: `${enP}${it.sheet_slug}.md`, sheet_fr: `${frP}${it.sheet_slug}.md` })) };
  }

  function indexBench(ctx, ds) {
    const opt = ds === "optimized" || ds === "compare", cols = ((opt ? ctx.LP_BENCH_OPT_META : ctx.LP_BENCH_META) || ctx.LP_BENCH_META || {}).cols || [];
    const raw = opt ? (ctx.LP_BENCH_OPT_ROWS || []) : ["1", "2", "3", "PG18", "YT"].flatMap((k) => ctx[`LP_BENCH_ROWS_${k}`] || []);
    const idx = {};
    for (const r of upk(cols, raw)) (idx[r.topology] = idx[r.topology] || {})[r.suite] = r;
    return idx;
  }

  function indexSqlstates(ctx) {
    const sets = {};
    for (const k of ["CORE", "EXT", "PG18", "YT"]) {
      const pk = ctx[`LP_MATRIX_${k}`];
      if (!pk || !pk.cols) continue;
      for (const r of upk(pk.cols, pk.rows)) {
        if (!r.topology) continue;
        const s = (sets[r.topology] = sets[r.topology] || new Set());
        for (const t of String(r.verified_sqlstates || "").split(/[;, ]+/)) if (t && t.toUpperCase() !== "NONE") s.add(t);
      }
    }
    return Object.fromEntries(Object.entries(sets).map(([k, v]) => [k, [...v].sort()]));
  }

  function benchStats(topo, bIdx, wan) {
    const own = bIdx[topo] || {}, par = topo === "pgedge-delta-apply" ? (bIdx.pgedge || {}) : {};
    const suite = wan > 0 ? `F_wan_netem_${wan}ms` : "A_single_rw";
    const row = own[suite] || par[suite], aRow = own.A_single_rw || par.A_single_rw;
    const dRow = own.D_hot_conflict, b2 = own.B2_overlap_rw;
    const dD = dRow ? +dRow.balance_drift || 0 : 0, dB2 = b2 ? +b2.balance_drift || 0 : 0;
    const n = (r, f) => (r && r[f] !== "" ? +r[f] : null);
    return {
      suite, tps: n(row, "tps"), latP95: n(row, "lat_p95_ms"), aTps: n(aRow, "tps"), dTps: n(dRow, "tps"),
      driftD: dD, driftB2: dB2, maxDrift: Math.abs(dD) >= Math.abs(dB2) ? dD : dB2,
      retries: Object.values(own).reduce((m, r) => Math.max(m, +r.retries_40001 || 0), 0),
    };
  }

  function scoreConflict(it, mode, dr, add) {
    const p = it.conflict_profile, hasDr = Math.abs(dr) > 0, raft = p.startsWith("raft");
    if (mode === "none") return it.multi_writer ? add(-10, "Multi-writer overhead", "Surco\u00fbt multi-ma\u00eetre") : add(14, "Single-primary: 0 conflicts", "Mono-primaire : 0 conflit");
    if (!it.multi_writer) return add(-28, "Single-primary only", "Mono-primaire uniquement", 1);
    if (mode === "disjoint") {
      if (p === "uuidv7") add(18, "PG18 uuidv7(): 0 23505");
      else if (p === "disjoint" || p === "lww_crdt" || p === "crdt") add(10, p === "disjoint" ? "PG17 origin=none OK" : "Spock+Snowflake OK");
      else if (p === "sharded_2pc") add(8, "2PC sharding OK");
      else if (raft) add(6, "Raft active-active RPO=0");
      else add(-8, "Trigger/XA limits");
    } else if (mode === "counter_crdt") {
      if (p === "crdt" || (p === "lww_crdt" && !hasDr)) add(20, "delta_apply CRDT: 0 drift", "delta_apply : 0 d\u00e9rive");
      else if (hasDr) add(-34, `Drift ${dr} loses updates`, `D\u00e9rive ${dr} : pertes`, 1);
      else if (raft) add(8, "Raft 0 drift (40001)");
      else if (p === "sharded_2pc") add(4, "2PC 0 drift co-located");
      else add(-6, "XA 0 drift, low TPS");
    } else {
      if (hasDr) add(-40, `Drift ${dr} breaks integrity`, `D\u00e9rive ${dr} critique`, 1);
      else if (p === "crdt" || p === "lww_crdt") add(-22, "CRDT: no global UNIQUE/FK", "", 1);
      else if (raft) add(20, "Raft: 0 drift & UNIQUE/FK");
      else if (p === "sharded_2pc") add(-10, "Citus 0A000 UNIQUE/FK limit");
      else if (p === "xa_sync") add(-8, "YT 0 drift, 0A000, low TPS");
      else add(-20, "YT async 55000 & RPO>0", "", 1);
    }
  }

  function scoreOne(it, cfg, bIdx, sqlMap, cavMap) {
    const fr = cfg.lang === "fr", reasons = [], p = it.conflict_profile;
    let sc = 54, fail = false;
    const add = (d, en, f, hf) => { sc += d; if (hf) fail = true; reasons.push({ delta: d, text: fr && f ? f : en }); };
    const st = benchStats(it.topology, bIdx, cfg.wanRttMs), sqls = sqlMap[it.topology] || sqlMap[PAR[it.topology]] || [];

    if (cfg.rpo === "zero") it.rpo_zero ? add(12, "RPO=0 (PC/EC)") : add(-42, "Async PA/EL: RPO>0", "", 1);
    else if (!it.rpo_zero && cfg.wanRttMs > 0) add(8, "Async absorbs WAN", "Async absorbe WAN");
    else if (it.rpo_zero && cfg.wanRttMs === 0) add(4, "Sync durable LAN");
    if (!it.ha) add(-12, "No HA failover", "Sans bascule HA");
    scoreConflict(it, cfg.conflictRate, st.maxDrift, add);
    if (cfg.wanRttMs > 0 && st.tps === null) add(-20, "No WAN replication", "Sans WAN", 1);
    else if (st.tps !== null) {
      add(st.tps >= 400 ? 8 : st.tps >= 150 ? 5 : st.tps >= 40 ? 1 : st.tps >= 15 ? -4 : -10, `${st.tps.toFixed(1)} TPS (${st.suite})`);
      if (cfg.wanRttMs > 0 && st.aTps > 0 && st.tps / st.aTps < 0.25) add(-4, `WAN ${cfg.wanRttMs}ms: -${Math.round((1 - st.tps / st.aTps) * 100)}%`);
    }
    const td = (TIER[it.tco_tier] ?? 1) - (TIER[cfg.tco] ?? 0);
    if (td <= 0) add(td === 0 && cfg.tco === "low" ? 6 : 4, `Fits ${cfg.tco} TCO`, `TCO ${cfg.tco} OK`);
    else add(td === 1 ? -9 : -18, `Exceeds ${cfg.tco} TCO (${it.nodes}n)`, `D\u00e9passe TCO (${it.nodes}n)`);
    if (it.topology.startsWith("pg18-")) sc += 2;
    if (p === "raft_rc") sc += 2;
    if (p === "xa_sync" || p === "xa_async") add(-6, "APP-008: Closed ytserv, BF=1");
    if (p === "lww_trig") add(-6, "Perl triggers, low vitality");
    sc = Math.max(0, Math.min(100, Math.round(sc)));
    const status = fail || sc < 35 ? "incompatible" : sc >= 76 ? "recommended" : sc >= 56 ? "viable" : "caution";
    const caveats = (it.caveat_keys || []).map((k) => (cavMap[k] ? cavMap[k][fr ? 1 : 0] : k));
    return { ...it, score: sc, status, hard_fail: fail, reasons, tps: st.tps, lat_p95_ms: st.latP95, suite_used: st.suite, d_tps: st.dTps, drift_d: st.driftD, drift_b2: st.driftB2, balance_drift: st.maxDrift, retries_40001: st.retries, verified_sqlstates: sqls, caveats };
  }

  function rank(inp, env) {
    const ctx = env || G, o = inp || {}, rw = +o.wanRttMs;
    const cfg = {
      rpo: o.rpo === "async" ? "async" : "zero",
      wanRttMs: [0, 10, 25, 50].includes(rw) ? rw : 0,
      conflictRate: ["none", "disjoint", "counter_crdt", "high_contention"].includes(o.conflictRate) ? o.conflictRate : "none",
      tco: ["low", "medium", "high"].includes(o.tco) ? o.tco : "low",
      dataset: o.dataset === "optimized" || o.dataset === "compare" ? "optimized" : "baseline",
      lang: o.lang === "fr" ? "fr" : "en",
    };
    const { items, caveats } = loadCatalog(ctx), bIdx = indexBench(ctx, cfg.dataset), sqlMap = indexSqlstates(ctx);
    const ranked = items.filter((it) => it.dataset_scope === "both" || it.dataset_scope === cfg.dataset).map((it) => scoreOne(it, cfg, bIdx, sqlMap, caveats));
    ranked.sort((a, b) => (+a.hard_fail - +b.hard_fail) || (b.score - a.score) || ((b.tps || 0) - (a.tps || 0)) || a.topology.localeCompare(b.topology));
    return { inputs: cfg, results: ranked, top: ranked[0] || null };
  }

  return { rank, loadCatalog, indexBench, indexSqlstates };
});

/* Functional & Limits Matrix tab controller + shared UI/CSV/sort utilities (L1-L8, T11-T18, PG 18.6, YT Cluster). */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const { TOPOS, esc } = window.LPCharts;
  const TL = Object.fromEntries(TOPOS.map(([k, v]) => [k, v]));
  const TC = Object.fromEntries(TOPOS.map(([k, , c]) => [k, c]));
  const TO = TOPOS.map(([k]) => k);
  const W = window;
  const upk = (cols, raw) => (raw || []).map((a) => Object.fromEntries(cols.map((c, i) => [c, a[i] ?? ""])));
  const dot = (t) => `<span class="dot" style="background:${TC[t] || "#64748b"}"></span>`;
  const bdg = (c, x) => `<span class="badge ${c}">${esc(x)}</span>`;
  const kc = (c, l, v, s) => `<div class="kpi-card ${c}"><div class="kpi-label">${esc(l)}</div><div class="kpi-val">${v}</div><div class="kpi-sub">${s}</div></div>`;
  const rw = (k, v, cls) => `<div class="tt-row"><span class="tt-k">${esc(k)}</span><span class="${cls || "tt-v"}">${v}</span></div>`;
  const csvCell = (v) => {
    let s = String(v ?? "");
    // Prefix non-numeric formula triggers before CSV quoting to neutralize spreadsheet injection.
    if (/^[=+\-@\t\r]/.test(s) && !/^-?\d+(\.\d+)?$/.test(s)) s = "'" + s;
    return `"${s.replace(/"/g, '""')}"`;
  };
  const buildCSV = (headers, rows) => [
    headers.map(csvCell).join(","),
    ...rows.map((r) => (Array.isArray(r) ? r : headers.map((c) => r[c])).map(csvCell).join(",")),
  ].join("\n") + "\n";
  function exportCSV(filename, headers, rows) {
    const csv = buildCSV(headers, rows);
    const a = Object.assign(document.createElement("a"), {
      href: URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" })),
      download: filename,
    });
    a.click();
    URL.revokeObjectURL(a.href);
    return csv;
  }
  const toFin = (v) => {
    if (v === "" || v === null || v === undefined) return NaN;
    const n = Number(v);
    return Number.isFinite(n) ? n : NaN;
  };
  function sortRows(rows, col, dir, numCols) {
    const isNum = numCols.has(col);
    return [...rows].sort((a, b) => {
      if (isNum) {
        const an = toFin(a[col]), bn = toFin(b[col]);
        const aOk = Number.isFinite(an), bOk = Number.isFinite(bn);
        if (!aOk && !bOk) return 0;
        if (!aOk) return 1;
        if (!bOk) return -1;
        return an === bn ? 0 : (an - bn) * dir;
      }
      const as = String(a[col] ?? ""), bs = String(b[col] ?? "");
      if (!as && !bs) return 0;
      if (!as) return 1;
      if (!bs) return -1;
      return as.localeCompare(bs) * dir;
    });
  }
  W.LPUtil = { TL, TC, TO, upk, dot, bdg, kc, rw, csvCell, buildCSV, exportCSV, toFin, sortRows };

  const pMat = (p) => (p && p.cols ? { cols: p.cols, rows: upk(p.cols, p.rows) } : { cols: [], rows: [] });
  const MAT = { core: pMat(W.LP_MATRIX_CORE), ext: pMat(W.LP_MATRIX_EXT), pg18: pMat(W.LP_MATRIX_PG18), yt: pMat(W.LP_MATRIX_YT) };
  const RXS = [
    [/^EXPECTED_LIMITATION:?\s*/i, "badge-warn", "LIMIT"],
    [/^PASS:?\s*/i, "badge-ok", "PASS"],
    [/^VERIFIED:?\s*/i, "badge-ok", "VERIFIED"],
    [/^PARTIAL:?\s*/i, "badge-warn", "PARTIAL"],
    [/^N\/A:?\s*/i, "badge-na", "N/A"],
  ];

  function filteredRows(st) {
    const ds = MAT[st.mtab];
    if (!ds || !ds.rows.length) return [];
    const sel = st.sel || new Set();
    const has = ds.rows.some((r) => sel.has(r.topology));
    const q = (st.qM || "").trim().toLowerCase();
    return ds.rows.filter((r) => (!has || sel.has(r.topology)) && (!q || Object.values(r).join(" ").toLowerCase().includes(q)));
  }

  function render(st) {
    const ds = MAT[st.mtab], nt = $("matrix-notice"), fr = st.lang === "fr";
    if (!ds || !ds.rows.length) {
      nt.textContent = fr ? "CSV absent ; relancez build_dashboard.py." : "Matrix CSV absent; re-run build_dashboard.py.";
      nt.classList.remove("hidden");
      $("matrix-thead").innerHTML = $("matrix-tbody").innerHTML = "";
      return;
    }
    const sel = st.sel || new Set(), has = ds.rows.some((r) => sel.has(r.topology));
    nt.textContent = fr ? "Affichage complet (activez les pilules pour filtrer)." : "Showing all matrix rows (toggle matching pills above to filter).";
    nt.classList.toggle("hidden", has);
    const rows = filteredRows(st);
    $("matrix-thead").innerHTML = `<tr>${ds.cols.map((c) => `<th>${esc(c.replace(/_/g, " "))}</th>`).join("")}</tr>`;
    $("matrix-tbody").innerHTML = rows.map((r) => `<tr>${ds.cols.map((c) => {
      const v = r[c] || "";
      if (c === "topology") return `<td><span class="topo-cell">${dot(v)}${esc(TL[v] || v)}</span></td>`;
      if (c === "verified_sqlstates") return `<td>${v.split(/[;, ]+/).filter(Boolean).map((s) => `<span class="sql-tag">${esc(s)}</span>`).join("")}</td>`;
      for (const [rx, cls, lb] of RXS) if (rx.test(v)) return `<td>${bdg(cls, lb)} ${esc(v.replace(rx, ""))}</td>`;
      return `<td>${esc(v)}</td>`;
    }).join("")}</tr>`).join("");
  }

  W.LPMatrix = { MAT, filteredRows, render };
})();

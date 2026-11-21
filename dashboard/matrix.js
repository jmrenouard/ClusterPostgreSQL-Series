/* Functional & Limits Matrix tab controller (L1-L8, T11-T18, PG 18.6, YT Cluster). */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const { TOPOS, esc } = window.LPCharts;
  const TL = Object.fromEntries(TOPOS.map(([k, v]) => [k, v]));
  const TC = Object.fromEntries(TOPOS.map(([k, , c]) => [k, c]));
  const W = window;
  const upk = (cols, raw) => (raw || []).map((a) => Object.fromEntries(cols.map((c, i) => [c, a[i] ?? ""])));
  const pMat = (p) => (p && p.cols ? { cols: p.cols, rows: upk(p.cols, p.rows) } : { cols: [], rows: [] });
  const MAT = { core: pMat(W.LP_MATRIX_CORE), ext: pMat(W.LP_MATRIX_EXT), pg18: pMat(W.LP_MATRIX_PG18), yt: pMat(W.LP_MATRIX_YT) };
  const dot = (t) => `<span class="dot" style="background:${TC[t] || "#64748b"}"></span>`;
  const bdg = (c, x) => `<span class="badge ${c}">${esc(x)}</span>`;
  const RXS = [
    [/^EXPECTED_LIMITATION:?\s*/i, "badge-warn", "LIMIT"],
    [/^PASS:?\s*/i, "badge-ok", "PASS"],
    [/^VERIFIED:?\s*/i, "badge-ok", "VERIFIED"],
    [/^PARTIAL:?\s*/i, "badge-warn", "PARTIAL"],
    [/^N\/A:?\s*/i, "badge-na", "N/A"],
  ];

  function render(st) {
    const ds = MAT[st.mtab], nt = $("matrix-notice"), fr = st.lang === "fr";
    if (!ds || !ds.rows.length) {
      nt.textContent = fr ? "CSV absent ; relancez build_dashboard.py." : "Matrix CSV absent; re-run build_dashboard.py.";
      nt.classList.remove("hidden");
      $("matrix-thead").innerHTML = $("matrix-tbody").innerHTML = "";
      return;
    }
    const has = ds.rows.some((r) => st.sel.has(r.topology));
    nt.textContent = fr ? "Affichage complet (activez les pilules pour filtrer)." : "Showing all matrix rows (toggle matching pills above to filter).";
    nt.classList.toggle("hidden", has);
    const q = st.qM.trim().toLowerCase();
    const rows = ds.rows.filter((r) => (!has || st.sel.has(r.topology)) && (!q || Object.values(r).join(" ").toLowerCase().includes(q)));
    $("matrix-thead").innerHTML = `<tr>${ds.cols.map((c) => `<th>${esc(c.replace(/_/g, " "))}</th>`).join("")}</tr>`;
    $("matrix-tbody").innerHTML = rows.map((r) => `<tr>${ds.cols.map((c) => {
      const v = r[c] || "";
      if (c === "topology") return `<td><span class="topo-cell">${dot(v)}${esc(TL[v] || v)}</span></td>`;
      if (c === "verified_sqlstates") return `<td>${v.split(/[;, ]+/).filter(Boolean).map((s) => `<span class="sql-tag">${esc(s)}</span>`).join("")}</td>`;
      for (const [rx, cls, lb] of RXS) if (rx.test(v)) return `<td>${bdg(cls, lb)} ${esc(v.replace(rx, ""))}</td>`;
      return `<td>${esc(v)}</td>`;
    }).join("")}</tr>`).join("");
  }

  W.LPMatrix = { MAT, render };
})();

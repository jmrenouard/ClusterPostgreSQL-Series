/* Offline Ecosystem Popularity & Maintenance Vitality view (zero CDN). */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const $$ = (s) => document.querySelectorAll(s);
  const { el, attachHover, fmtNum, fmtTick, logTicks, linTicks, esc } = window.LPCharts;

  const pack = window.LP_POPULARITY || { cols: [], rows: [] };
  const COLS = pack.cols || [];
  const ROWS = (pack.rows || []).map((arr) => {
    const o = Object.fromEntries(COLS.map((c, i) => [c, arr[i] ?? ""]));
    const isProp = o.stars === "" || o.stars === "N/A";
    const c12 = Number(o.commits_12m || 0);
    o.vitality = isProp ? "Proprietary" : (c12 >= 30 ? "Active" : (c12 > 0 ? "Low" : "Dormant"));
    o.short_name = String(o.project_name || "").split(" (")[0].replace("Cloud Spanner ", "Spanner ");
    o.pushed_date = o.pushed_at && o.pushed_at !== "N/A" ? String(o.pushed_at).slice(0, 10) : "N/A";
    return o;
  });

  const VIT_CLS = { Active: "badge-ok", Low: "badge-warn", Dormant: "badge-err", Proprietary: "badge-na" };
  const VIT_COL = { Active: "#16a34a", Low: "#d97706", Dormant: "#dc2626", Proprietary: "#64748b" };
  const MET_LBL = {
    stars: ["GitHub Stars (18 Public Repos)", "\u00c9toiles GitHub (18 d\u00e9p\u00f4ts publics)", "#1d4ed8"],
    forks: ["GitHub Forks (18 Public Repos)", "Forks GitHub (18 d\u00e9p\u00f4ts publics)", "#0ea5e9"],
    commits_12m: ["12-Month Commit Velocity", "V\u00e9locit\u00e9 Commits (12 mois)", "#059669"],
    total_commits: ["All-Time Total Commits", "Commits totaux (historique)", "#334155"],
    contributors: ["Repository Contributors", "Contributeurs du d\u00e9p\u00f4t", "#7c3aed"],
  };

  const st = { lang: "en", scale: "log", met1: "stars", met2: "commits_12m", vit: "ALL", q: "", sort: "stars", dir: -1, wired: false };

  function popTip(r) {
    const rw = (k, v, cls) => `<div class="tt-row"><span class="tt-k">${k}</span><span class="${cls || "tt-v"}">${v}</span></div>`;
    const num = (v) => (v === "" || v === "N/A" ? "N/A" : Number(v).toLocaleString());
    return `<div class="tt-title">${esc(r.project_name)}</div>` +
      rw("Repo", esc(r.github_repo || "N/A")) +
      rw("Org (Repos)", r.git_account !== "N/A" ? `${esc(r.git_account)} (${num(r.account_public_repos)})` : "Proprietary") +
      rw("Stars / Forks", `${num(r.stars)} / ${num(r.forks)}`) +
      rw("Commits (Tot/12m)", `${num(r.total_commits)} / ${num(r.commits_12m)}`) +
      rw("Contributors", num(r.contributors)) +
      rw("Release / Lic.", `${esc(r.latest_release)} / ${esc(r.license_spdx)}`) +
      rw("Last Push", `${esc(r.pushed_date)} [${esc(r.vitality)}]`, r.vitality === "Active" ? "tt-ok" : (r.vitality === "Dormant" ? "tt-bad" : "tt-v"));
  }

  function renderHBar(container, metric) {
    container.innerHTML = "";
    const pub = ROWS.filter((r) => r.vitality !== "Proprietary" && (st.vit === "ALL" || r.vitality === st.vit))
      .sort((a, b) => (Number(b[metric] || 0) - Number(a[metric] || 0)) || (Number(b.stars || 0) - Number(a.stars || 0)));
    if (!pub.length) {
      container.innerHTML = `<div class="chart-empty">${st.lang === "fr" ? "Aucun d\u00e9p\u00f4t public pour ce filtre." : "No public GitHub repos for this filter."}</div>`;
      return;
    }
    const vals = pub.map((r) => Number(r[metric] || 0)).filter((v) => v > 0);
    const maxV = vals.length ? Math.max(...vals) : 10;
    const minV = vals.length ? Math.min(...vals) : 1;
    const isLog = st.scale === "log";
    const info = isLog ? logTicks(Math.max(1, minV), maxV, false) : linTicks(maxV);
    const W = 680, rowH = 22.5, M = { t: 16, r: 74, b: 32, l: 132 };
    const H = Math.max(240, M.t + M.b + pub.length * rowH);
    const plotW = W - M.l - M.r, plotH = H - M.t - M.b;
    const lLo = isLog ? Math.log10(info.lo) : info.lo, lHi = isLog ? Math.log10(info.hi) : info.hi;
    const xOf = (v) => {
      const f = isLog
        ? (Math.log10(Math.max(v, info.lo)) - lLo) / Math.max(lHi - lLo, 1e-6)
        : Math.max(0, v) / Math.max(info.hi, 1e-6);
      return M.l + plotW * f;
    };

    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" });
    svg.appendChild(el("rect", { x: M.l, y: M.t, width: plotW, height: plotH, fill: "#f8fafc", rx: 4 }));
    info.ticks.forEach((tk) => {
      const x = xOf(tk);
      svg.appendChild(el("line", { x1: x, y1: M.t, x2: x, y2: M.t + plotH, stroke: "#cbd5e1", "stroke-width": 0.9 }));
      svg.appendChild(el("text", { x, y: M.t + plotH + 16, "text-anchor": "middle", fill: "#475569", "font-size": 10, "font-family": "ui-monospace, monospace" }, fmtTick(tk, "")));
    });
    svg.appendChild(el("line", { x1: M.l, y1: M.t, x2: M.l, y2: M.t + plotH, stroke: "#94a3b8", "stroke-width": 1.2 }));
    svg.appendChild(el("line", { x1: M.l, y1: M.t + plotH, x2: M.l + plotW, y2: M.t + plotH, stroke: "#94a3b8", "stroke-width": 1.2 }));

    const baseCol = (MET_LBL[metric] && MET_LBL[metric][2]) || "#1d4ed8";
    pub.forEach((r, i) => {
      const y = M.t + i * rowH + 3, bh = rowH - 6.5, v = Number(r[metric] || 0);
      const col = metric === "commits_12m" || metric === "contributors" ? VIT_COL[r.vitality] : baseCol;
      svg.appendChild(el("text", { x: M.l - 7, y: y + bh / 2 + 3.5, "text-anchor": "end", fill: "#1e293b", "font-size": 10.2, "font-weight": 600 }, r.short_name));
      if (v > 0) {
        const bw = Math.max(3, xOf(v) - M.l);
        const rect = el("rect", { x: M.l, y, width: bw, height: bh, fill: col, rx: 2.5 });
        attachHover(rect, popTip(r));
        svg.appendChild(rect);
        svg.appendChild(el("text", { x: M.l + bw + 5, y: y + bh / 2 + 3.5, fill: "#1e293b", "font-size": 9.8, "font-weight": 700 }, v >= 1000 ? v.toLocaleString() : String(v)));
      } else {
        const z = el("text", { x: M.l + 6, y: y + bh / 2 + 3.5, fill: "#b91c1c", "font-size": 9.6, "font-weight": 700 }, "0 (Dormant)");
        attachHover(z, popTip(r));
        svg.appendChild(z);
      }
    });
    container.appendChild(svg);
  }

  function filteredRows() {
    const q = st.q.trim().toLowerCase();
    return ROWS.filter((r) => (st.vit === "ALL" || r.vitality === st.vit) &&
      (!q || `${r.project_name} ${r.github_repo} ${r.git_account} ${r.git_present} ${r.license_spdx} ${r.vitality} ${r.pushed_date}`.toLowerCase().includes(q)));
  }

  function renderKPIs() {
    const fr = st.lang === "fr";
    const pub = ROWS.filter((r) => r.vitality !== "Proprietary");
    const topS = pub.reduce((a, b) => (+b.stars > +a.stars ? b : a), pub[0]);
    const topC = pub.reduce((a, b) => (+b.commits_12m > +a.commits_12m ? b : a), pub[0]);
    const cnt = (v) => ROWS.filter((r) => r.vitality === v).length;
    const kc = (c, l, v, s) => `<div class="kpi-card ${c}"><div class="kpi-label">${esc(l)}</div><div class="kpi-val">${v}</div><div class="kpi-sub">${s}</div></div>`;
    $("pop-kpi-grid").innerHTML = [
      kc("", fr ? "Solutions suivies" : "Tracked Solutions", `${ROWS.length}`, `${pub.length} GitHub &middot; ${cnt("Proprietary")} ${fr ? "Propri\u00e9taires" : "Proprietary"}`),
      kc("kpi-amber", fr ? "Plus \u00e9toil\u00e9" : "Most Starred", topS ? `${fmtNum(topS.stars)} \u2605` : "N/A", topS ? `${esc(topS.short_name)} (${Number(topS.forks).toLocaleString()} forks)` : "-"),
      kc("kpi-ok", fr ? "Top v\u00e9locit\u00e9 12m" : "Top 12m Velocity", topC ? `${Number(topC.commits_12m).toLocaleString()} / 12m` : "N/A", topC ? `${esc(topC.short_name)} (${Number(topC.contributors).toLocaleString()} contrib.)` : "-"),
      kc("kpi-err", fr ? "Vitalit\u00e9 maintenance" : "Maintenance Vitality", `${cnt("Active")} Active`, `${cnt("Low")} Low &middot; ${cnt("Dormant")} Dormant &middot; ${cnt("Proprietary")} Prop.`),
    ].join("");
  }

  function renderTable() {
    const c = st.sort, d = st.dir, loc = st.lang === "fr" ? "fr-FR" : "en-US";
    const numCols = new Set(["stars", "forks", "total_commits", "commits_12m", "contributors"]);
    const sr = [...filteredRows()].sort((a, b) => {
      if (numCols.has(c)) {
        const av = a[c] === "" ? -1 : Number(a[c]), bv = b[c] === "" ? -1 : Number(b[c]);
        return (av - bv) * d;
      }
      return String(a[c] ?? "").localeCompare(String(b[c] ?? "")) * d;
    });
    $$("#pop-table th[data-psort]").forEach((th) => th.classList.toggle("sorted", th.dataset.psort === c));
    const fmt = (v) => (v === "" || v === "N/A" ? '<span class="badge badge-na">N/A</span>' : Number(v).toLocaleString(loc));
    $("pop-tbody").innerHTML = sr.map((r) => {
      const repoHtml = r.github_repo && r.github_repo !== "N/A"
        ? `<a class="repo-link" href="https://github.com/${esc(r.github_repo)}" target="_blank" rel="noopener">${esc(r.github_repo)}</a>`
        : `<span class="repo-link">Closed / Managed</span>`;
      const orgHtml = r.git_account && r.git_account !== "N/A"
        ? `${esc(r.git_account)}<span class="org-pill">${esc(r.account_public_repos)} repos</span>`
        : `<span class="badge badge-na">Proprietary</span>`;
      return `<tr><td><strong>${esc(r.project_name)}</strong>${repoHtml}</td>` +
        `<td>${esc(r.git_present)}</td><td>${orgHtml}</td>` +
        `<td class="num"><strong>${fmt(r.stars)}</strong></td><td class="num">${fmt(r.forks)}</td>` +
        `<td class="num">${fmt(r.total_commits)}</td><td class="num"><strong>${fmt(r.commits_12m)}</strong></td>` +
        `<td class="num">${fmt(r.contributors)}</td><td>${esc(r.latest_release)}</td>` +
        `<td>${esc(r.license_spdx)}</td><td class="date-cell">${esc(r.pushed_date)}</td>` +
        `<td><span class="badge ${VIT_CLS[r.vitality] || "badge-na"}">${esc(r.vitality)}</span></td></tr>`;
    }).join("");
  }

  function renderCharts() {
    const idx = st.lang === "fr" ? 1 : 0;
    $("pop-title-1").textContent = (MET_LBL[st.met1] || [st.met1, st.met1])[idx];
    $("pop-title-2").textContent = (MET_LBL[st.met2] || [st.met2, st.met2])[idx];
    $("pop-scale-1").textContent = $("pop-scale-2").textContent = st.scale === "log" ? "log10" : "linear";
    renderHBar($("pop-chart-1"), st.met1);
    renderHBar($("pop-chart-2"), st.met2);
  }

  function wireOnce() {
    if (st.wired) return;
    st.wired = true;
    const bind = (attr, key) => $$(`[${attr}]`).forEach((b) => {
      b.onclick = () => {
        st[key] = b.getAttribute(attr);
        $$(`[${attr}]`).forEach((x) => x.classList.toggle("active", x.getAttribute(attr) === st[key]));
        renderCharts();
      };
    });
    bind("data-pscale", "scale");
    bind("data-pmet1", "met1");
    bind("data-pmet2", "met2");
    $("pop-vit-select").onchange = (e) => { st.vit = e.target.value; renderCharts(); renderTable(); };
    $("pop-filter").oninput = (e) => { st.q = e.target.value; renderTable(); };
    $$("#pop-table th[data-psort]").forEach((th) => {
      th.onclick = () => {
        const c = th.dataset.psort;
        st.dir = st.sort === c ? -st.dir : -1;
        st.sort = c;
        renderTable();
      };
    });
  }

  function render(lang) {
    st.lang = lang || "en";
    wireOnce();
    renderKPIs();
    renderCharts();
    renderTable();
  }

  function exportCSV() {
    const cols = [...COLS, "vitality"];
    const q = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const csv = [cols.map(q).join(","), ...filteredRows().map((r) => cols.map((c) => q(r[c])).join(","))].join("\n") + "\n";
    const a = Object.assign(document.createElement("a"), {
      href: URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" })),
      download: "cluster_pg_ecosystem_popularity.csv",
    });
    a.click();
    URL.revokeObjectURL(a.href);
  }

  window.LPPopularity = { render, exportCSV, count: ROWS.length };
})();

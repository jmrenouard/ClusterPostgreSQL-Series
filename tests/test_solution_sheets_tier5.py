"""Tier 5 adversarial E2E validation: README catalog, 4-CSV row parity, matrices, and EN/FR tables."""

from __future__ import annotations

import csv
import importlib.util
import pathlib
import re
import unittest

rc, rs = re.compile, re.search


def _load_sibling(name: str):
    """Load sibling test module privately without triggering duplicate TestCase discovery."""
    p = pathlib.Path(__file__).resolve().with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"_ext_t5_{name}", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BASE = _load_sibling("test_solution_sheets")
PARITY = _load_sibling("test_solution_sheets_parity")
ROOT, RESULTS = BASE.ROOT, PARITY.RESULTS
DOCS_EN, DOCS_FR, SOL_EN, SOL_FR = BASE.DOCS_EN, BASE.DOCS_FR, BASE.SOL_EN, BASE.SOL_FR
BENCH, EXTRA_BENCH, SLUGS = BASE.BENCH, BASE.EXTRA_BENCH, BASE.SLUGS

BENCH_CSVS = (
    "benchmark_summary.csv",
    "benchmark_extended_workloads.csv",
    "benchmark_wan_sweep.csv",
    "benchmark_concurrency_sweep.csv",
)
TR = str.maketrans({"\u00a0": " ", "\u202f": " ", "\u2212": "-"})


def _norm(txt: str) -> str:
    return txt.translate(TR).replace(r"\\,", " ").replace(r"\,", " ")


def _suite_pat(topo: str, suite: str) -> re.Pattern[str]:
    if suite.startswith(("F_wan_netem_", "G_conc_")):
        return rc(rf"^\s*`{re.escape(suite)}(?![A-Za-z0-9_])")
    pref = suite.split("_", 1)[0]
    if topo == "pgedge-delta-apply" and suite == "D_hot_conflict":
        return rc(r"^\s*`D_.*(?:delta-apply|CRDT)", re.I)
    if topo == "pgedge" and suite == "D_hot_conflict":
        return rc(r"^\s*`D_.*LWW", re.I)
    return rc(rf"^\s*`{re.escape(pref)}_")


class TestTier5AdversarialCoverage(unittest.TestCase):
    """Tier 5 checks covering README 4-column catalog, headline parity, 4-CSV row parity, and EN/FR tables."""

    def test_tier5_readme_catalog_and_headline_parity(self) -> None:
        """Verify 19-row 4-col Solutions Catalog in README*.md and headline CSV accuracy in README*/06*."""
        e: list[str] = []
        for rm, sd, prop_ok in (
            (ROOT / "README.md", SOL_EN, rc(r"^Proprietary\s*/\s*N/A$", re.I)),
            (ROOT / "README.fr.md", SOL_FR, rc(r"^Propri\u00e9taire\s*/\s*N/A$", re.I)),
        ):
            txt = rm.read_text(encoding="utf-8")
            _, tables = BASE.extract_sections_and_tables(txt)
            rel_rm = BASE.rel_path(rm)
            cat_rows = None
            for _, hd, rows in tables:
                if len(hd) == 4 and len(rows) == len(SLUGS):
                    hits = set()
                    for rw in rows:
                        for m in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", rw[0]):
                            tgt = (rm.parent / m.group(1).split("#", 1)[0]).resolve()
                            if tgt.parent == sd.resolve() and tgt.is_file():
                                hits.add(tgt.stem)
                    if hits == set(SLUGS):
                        cat_rows = rows
                        break
            if cat_rows is None:
                e.append(f"{rel_rm}: missing {len(SLUGS)}-row 4-col Solutions Catalog covering all {len(SLUGS)} slugs")
                continue
            for idx, rw in enumerate(cat_rows, 1):
                if not rs(r"https://[^\s)>\]]+", rw[1]):
                    e.append(f"{rel_rm}:row{idx}: missing https product/docs URL in col 2")
                if not (rs(r"https://github\.com/[^\s)>\]]+", rw[2]) or prop_ok.match(rw[2].strip())):
                    e.append(f"{rel_rm}:row{idx}: invalid col 3 GitHub/Proprietary cell ({rw[2]!r})")
                if len(rw[3].strip()) < 20:
                    e.append(f"{rel_rm}:row{idx}: brief description < 20 chars")

        with (RESULTS / "benchmark_summary.csv").open(encoding="utf-8", newline="") as fh:
            sum_rows = list(csv.DictReader(fh))
        anchors = [
            (r["topology"].strip(), r["tps"].strip())
            for r in sum_rows
            if r["suite"].strip() == "A_single_rw"
            or (r["topology"].strip() == "pgedge-delta-apply" and r["suite"].strip() == "D_hot_conflict")
        ]
        c06_en = PARITY._g(DOCS_EN, "06_*.md")
        c06_fr = PARITY._g(DOCS_FR, "06_*.md")
        for doc in (ROOT / "README.md", ROOT / "README.fr.md", c06_en, c06_fr):
            raw = doc.read_text(encoding="utf-8")
            norm = _norm(raw)
            rel_d = BASE.rel_path(doc)
            if rs(r"\b685\s*\(?\s*(?:of|sur)\s*902\b", norm, re.I):
                e.append(f"{rel_d}: stale 685 of 902 denominator")
            for topo, tps in anchors:
                if not PARITY.has_csv_number(norm, tps):
                    e.append(f"{rel_d}: missing headline TPS {topo}={tps}")
            if doc != ROOT / "README.fr.md":
                for num in ("685", "1587"):
                    if not PARITY.has_csv_number(norm, num):
                        e.append(f"{rel_d}: missing cockroach Suite E {num}")
            if doc in (c06_en, c06_fr):
                for num in ("902", "9", "3806", "2574"):
                    if not PARITY.has_csv_number(norm, num):
                        e.append(f"{rel_d}: missing Suite E denominator/count {num}")
        self.assertEqual(e, [], "\n".join(e))

    def test_tier5_full_4csv_matrix_and_en_fr_table_parity(self) -> None:
        """Verify row-scoped metrics across all 4 benchmark CSVs (187 rows), matrix probes, and EN/FR tables."""
        all_rows: list[dict[str, str]] = []
        for fn in BENCH_CSVS:
            with (RESULTS / fn).open(encoding="utf-8", newline="") as fh:
                all_rows.extend(csv.DictReader(fh))
        self.assertEqual(len(all_rows), 187)

        by_topo: dict[str, list[dict[str, str]]] = {}
        for r in all_rows:
            by_topo.setdefault(r["topology"].strip(), []).append(r)

        lim_rows: dict[str, dict[str, str]] = {}
        with (RESULTS / "functional_limits_matrix.csv").open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                lim_rows[r["topology"].strip()] = r
        ext_rows: dict[str, dict[str, str]] = {}
        with (RESULTS / "extended_functional_matrix.csv").open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                ext_rows[r["topology"].strip()] = r

        e: list[str] = []
        for slug, keys in BENCH.items():
            for d in (SOL_EN, SOL_FR):
                p = d / f"{slug}.md"
                rel = BASE.rel_path(p)
                txt = p.read_text(encoding="utf-8")
                norm_doc = _norm(txt)
                _, tables = BASE.extract_sections_and_tables(txt)
                for k in keys:
                    for r in by_topo[k]:
                        su = r["suite"].strip()
                        pat = _suite_pat(k, su)
                        matched = [
                            " | ".join(rw)
                            for _, _, rows in tables
                            for rw in rows
                            if rows and pat.search(rw[0])
                        ]
                        if not matched:
                            e.append(f"{rel}: missing row {k}/{su}")
                            continue
                        row_raw = "\n".join(matched)
                        row_n = _norm(row_raw)
                        for col, rnd, cond in (
                            ("tps", False, True),
                            ("lat_avg_ms", True, True),
                            ("lat_stddev_ms", True, True),
                            ("lat_p95_ms", True, True),
                            ("tx_committed", False, True),
                            ("tx_failed", False, int(r["tx_failed"]) > 0),
                            ("balance_drift", False, int(r["balance_drift"]) != 0),
                        ):
                            if cond and not PARITY.has_csv_number(row_n, r[col], rnd):
                                e.append(f"{rel}: row {k}/{su} miss {col}={r[col]}")
                        qps = r["qps"].strip()
                        if qps != "N/A":
                            q_ok = PARITY.has_csv_number(row_n, qps) or (
                                qps == r["tps"].strip() and bool(rs(r"QPS\s*=\s*TPS", row_raw, re.I))
                            )
                            if not q_ok:
                                e.append(f"{rel}: row {k}/{su} miss qps={qps}")
                        if int(r["retries_40001"]) > 0 and not PARITY.has_csv_number(norm_doc, r["retries_40001"]):
                            e.append(f"{rel}: miss {k}/{su} retries_40001={r['retries_40001']}")

                    if k in lim_rows:
                        for pid in [f"L{i}" for i in range(1, 9)] + [f"T{i}" for i in range(11, 19)]:
                            if not any(rs(rf"^\s*`{pid}\b", rw[0]) for _, _, rows in tables for rw in rows if rw):
                                e.append(f"{rel}: miss probe {pid}")
                    if k in ext_rows:
                        er = ext_rows[k]
                        t11_rows = [
                            _norm(" | ".join(rw))
                            for _, _, rows in tables
                            for rw in rows
                            if rw and rs(r"^\s*`T11\b", rw[0])
                        ]
                        if m11 := rs(r"(\d+)\s*rows/s", er["t11_bulk_10k_throughput_and_catchup"]):
                            if not any(PARITY.has_csv_number(rn, m11.group(1)) for rn in t11_rows):
                                e.append(f"{rel}: T11 miss {k} {m11.group(1)} rows/s")
                        t15_rows = [
                            _norm(" | ".join(rw))
                            for _, _, rows in tables
                            for rw in rows
                            if rw and rs(r"^\s*`T15\b", rw[0])
                        ]
                        for stat in ("p50", "p95", "max"):
                            if ms := rs(rf"{stat}=(\d+(?:\.\d+)?)ms", er["t15_raw_visibility_lag_ms"]):
                                if not any(PARITY.has_csv_number(rn, ms.group(1), True) for rn in t15_rows):
                                    e.append(f"{rel}: T15 miss {k} {stat}={ms.group(1)}")

        for slug, bf, _, _, _, _, suites in PARITY.EXTRA_SPECS:
            with (RESULTS / bf).open(encoding="utf-8", newline="") as fh:
                ex_rows = list(csv.DictReader(fh))
            for d in (SOL_EN, SOL_FR):
                p = d / f"{slug}.md"
                rel = BASE.rel_path(p)
                txt = p.read_text(encoding="utf-8")
                _, tables = BASE.extract_sections_and_tables(txt)
                tab_norm = "\n".join(_norm(" | ".join(rw)) for _, _, rows in tables for rw in rows if rw)
                for r in ex_rows:
                    if r["suite"].strip() in suites and not PARITY.has_csv_number(tab_norm, r["tps"]):
                        e.append(f"{rel}: table miss {r['topology']}/{r['suite']} tps={r['tps']}")

        for slug in SLUGS:
            en_tb = BASE.extract_sections_and_tables((SOL_EN / f"{slug}.md").read_text(encoding="utf-8"))[1]
            fr_tb = BASE.extract_sections_and_tables((SOL_FR / f"{slug}.md").read_text(encoding="utf-8"))[1]
            en_shape = [len(r) for _, _, r in en_tb]
            fr_shape = [len(r) for _, _, r in fr_tb]
            if en_shape != fr_shape:
                e.append(f"{slug}: EN/FR table shape mismatch EN={en_shape} FR={fr_shape}")
        self.assertEqual(e, [], "\n".join(e))

    def test_tier5_popularity_vitality_and_freshness_parity(self) -> None:
        """Verify row-scoped Section 6 popularity, vitality, freshness, and synthesis across 38 sheets and 22 CSV rows."""
        pop_map: dict[str, tuple[str, ...]] = {
            "pg17_standalone": ("postgres-core",), "pg17_physical_streaming_patroni": ("postgres-core", "patroni"),
            "pg17_logical_unidirectional": ("postgres-core",), "pg17_bidirectional_logical": ("postgres-core",),
            "pg18_native_clustering": ("postgres-core", "patroni"),
            "pgedge_spock": ("pgedge-spock", "pgedge-snowflake", "pgedge-lolor"),
            "pglogical2": ("pglogical2",), "edb_pgd": ("edb-pgd",), "yugabytedb": ("yugabytedb",),
            "cockroachdb": ("cockroachdb",), "citus": ("citus",), "opentenbase_pgxl": ("opentenbase",),
            "bucardo": ("bucardo",), "symmetricds": ("symmetricds",), "pgpool_ii": ("pgpool2",),
            "aws_aurora_limitless": ("aurora-limitless",),
            "gcp_spanner_alloydb": ("gcp-spanner-alloydb", "spanner-pgadapter"),
            "legacy_triggers": ("slony1", "pgq", "londiste", "rubyrep"), "yt_cluster_lite": ("yt-cluster-lite",),
        }
        prop_re = {"edb-pgd": rc(r"EDB|PGD|BDR", re.I), "aurora-limitless": rc(r"Aurora|Limitless", re.I), "gcp-spanner-alloydb": rc(r"Spanner|AlloyDB", re.I)}
        with (RESULTS / "project_popularity.csv").open(encoding="utf-8", newline="") as fh:
            pop = {r["solution_id"].strip(): r for r in csv.DictReader(fh)}
        self.assertEqual((len(pop), set(pop_map), {s for ss in pop_map.values() for s in ss}), (22, set(SLUGS), set(pop)))

        sec_re = rc(r"(?:popularit.*vitalit|vitalit.*popularit)", re.I)
        sec_hdr = {
            "en": rc(r"^6\.\s+GitHub\s+Popularity,\s+Git\s+Presence\s+&\s+Maintenance\s+Vitality\s+\(`results/project_popularity\.csv`\)$"),
            "fr": rc(r"^6\.\s+Popularit\u00e9\s+GitHub,\s+pr\u00e9sence\s+Git\s+et\s+vitalit\u00e9\s+de\s+maintenance\s+\(`results/project_popularity\.csv`\)$"),
        }
        table_hdr = {
            "en": ["Project", "Git Presence / Role", "Repo (`Account / Repos`)", "Stars / Forks / Watch", "Commits (`Tot / 12m`)", "Contrib / Issues", "Lang / SPDX", "Release / Last Push"],
            "fr": ["Projet", "Pr\u00e9sence / R\u00f4le Git", "D\u00e9p\u00f4t (`Compte / D\u00e9p\u00f4ts`)", "Stars / Forks / Watch", "Commits (`Tot / 12m`)", "Contrib / Issues", "Lang / SPDX", "Tag / Dernier Push"],
        }
        intro_re = {
            "en": rc(r"^Live\s+GitHub\s+telemetry\s+\(`2026-11-20T17:26:02Z`,\s+`archived\s+=\s+false`\s+unless\s+`N/A`\):$", re.M),
            "fr": rc(r"^T\u00e9l\u00e9m\u00e9trie\s+GitHub\s+en\s+direct\s+\(`2026-11-20T17:26:02Z`,\s+`archived\s+=\s+false`\s+sauf\s+`N/A`\)\s+:$", re.M),
        }
        synth_re = {
            "en": (
                ("maint", rc(r"^-\s+\*\*Maintenance\s+Level:\*\*\s+\*\*(?:Tier\s+[SABCD]\s+\([^)]+\)|Closed\s+/\s+(?:Proprietary|Managed\s+Cloud(?:\s+\(\+\s+OSS\s+Proxy\))?))\*\*(?:\s+\+\s+\*\*Tier\s+[SABCD]\s+\([^)]+\)\*\*)?\s+--\s+\S", re.M)),
                ("fresh", rc(r"^-\s+\*\*Currency\s+/\s+Freshness:\*\*\s+\*\*(?:Current\s+--\s+(?:Daily\s+Active|High\s+Velocity|Active|Steady|Young)|Low\s+Cadence|Stale\s+/\s+Dormant|Dormant\s+/\s+Minimal\s+Maintenance|Opaque\s+\(Vendor-Managed\)|Opaque\s+Engine\s+\+\s+Active\s+Proxy)\*\*\s+--\s+\S", re.M)),
                ("ops", rc(r"^-\s+\*\*Operational\s+Manageability:\*\*\s+\*\*(?:Low\s+Risk|Moderate|High\s+Risk|Do\s+Not\s+Deploy|Vendor\s+Lock-In)\*\*\s+--\s+\S", re.M)),
            ),
            "fr": (
                ("maint", rc(r"^-\s+\*\*Niveau\s+de\s+maintenance\s*:\*\*\s+\*\*(?:Niveau\s+[SABCD]\s+\([^)]+\)|Ferm\u00e9\s+/\s+(?:Propri\u00e9taire|Cloud\s+Manag\u00e9(?:\s+\(\+\s+Proxy\s+OSS\))?))\*\*(?:\s+\+\s+\*\*Niveau\s+[SABCD]\s+\([^)]+\)\*\*)?\s+--\s+\S", re.M)),
                ("fresh", rc(r"^-\s+\*\*Fra\u00eecheur\s+/\s+Actualit\u00e9\s*:\*\*\s+\*\*(?:(?:Actuel|\u00c0\s+jour)\s+--\s+(?:Actif\s+au\s+quotidien|V\u00e9locit\u00e9\s+\u00e9lev\u00e9e|Actif|R\u00e9gulier|Jeune)|Cadence\s+faible|Obsol\u00e8te\s+/\s+Dormant|Dormant\s+/\s+Maintenance\s+minimale|Opaque\s+\(G\u00e9r\u00e9\s+par\s+l'\u00e9diteur\)|Moteur\s+opaque\s+\+\s+Proxy\s+actif)\*\*\s+--\s+\S", re.M)),
                ("ops", rc(r"^-\s+\*\*Maintenabilit\u00e9\s+op\u00e9rationnelle\s*:\*\*\s+\*\*(?:Risque\s+faible|Mod\u00e9r\u00e9|Risque\s+\u00e9lev\u00e9|Ne\s+pas\s+d\u00e9ployer|Verrouillage\s+\u00e9diteur)\*\*\s+--\s+\S", re.M)),
            ),
        }
        tier_re = rc(r"\b(?:Tier|Niveau)\s+[SABCD]\b|Closed\s*/|Ferm\u00e9\s*/", re.I)
        dormant_re = rc(r"dormant|EOL|inactive|inactif|0\s+commit|Tier\s+D|Niveau\s+D", re.I)
        active_tier_re = rc(r"\b(?:Tier|Niveau)\s+[SA]\b", re.I)
        prop_prose_re = rc(r"closed|proprietary|managed|opaque|propri\u00e9taire|manag\u00e9|ferm\u00e9", re.I)

        e: list[str] = []
        for d, lang in ((SOL_EN, "en"), (SOL_FR, "fr")):
            for slug in SLUGS:
                p = d / f"{slug}.md"
                rel = BASE.rel_path(p)
                pr, tb = BASE.extract_sections_and_tables(p.read_text(encoding="utf-8"))
                sec_tabs = [(h, hd, rows) for h, hd, rows in tb if sec_re.search(h)]
                if len(sec_tabs) != 1:
                    e.append(f"{rel}: expected 1 Sec 6 table, got {len(sec_tabs)}")
                    continue
                sec_h, hd, pop_rows = sec_tabs[0]
                prose, sids = pr.get(sec_h, ""), pop_map[slug]
                snap = pop[sids[0]]["snapshot_utc"].strip()
                if not sec_hdr[lang].match(sec_h):
                    e.append(f"{rel}: bad Sec 6 heading {sec_h!r}")
                if hd != table_hdr[lang] or len(pop_rows) != len(sids):
                    e.append(f"{rel}: header/rows mismatch rows={len(pop_rows)} exp={len(sids)}")
                if "results/project_popularity.csv" not in sec_h and "results/project_popularity.csv" not in prose:
                    e.append(f"{rel}: missing project_popularity.csv ref")
                if snap not in prose or "archived = false" not in prose or not intro_re[lang].search(prose):
                    e.append(f"{rel}: missing intro/{snap}/archived=false")
                for lbl, pat in synth_re[lang]:
                    if not pat.search(prose):
                        e.append(f"{rel}: bad synthesis bullet {lbl}")
                if not tier_re.search(prose):
                    e.append(f"{rel}: missing tier/status label")

                for sid in sids:
                    r = pop[sid]
                    repo = r["github_repo"].strip()
                    if repo == "N/A":
                        matched = [rw for rw in pop_rows if rw and prop_re[sid].search(rw[0]) and "N/A" in " | ".join(rw[2:])]
                        if len(matched) != 1:
                            e.append(f"{rel}: expected 1 prop row {sid}, got {len(matched)}")
                            continue
                        rw = matched[0]
                        if len(rw) != 8 or rs(r"https://github\.com/", " | ".join(rw)) or rs(r"\d", " | ".join(rw[1:])):
                            e.append(f"{rel}: prop row {sid} digits/URL: {rw!r}")
                        if not all("N/A" in c for c in rw[2:]) or not rs(r"Proprietary|Propri\u00e9taire", rw[2], re.I) or "Proprietary" not in rw[6]:
                            e.append(f"{rel}: prop row {sid} missing N/A/Proprietary")
                        if r["git_present"].strip() not in rw[1] or r["git_role"].strip() not in rw[1]:
                            e.append(f"{rel}: {sid} git_present/git_role mismatch")
                        if not prop_prose_re.search(prose):
                            e.append(f"{rel}: {sid} missing opacity prose")
                        continue
                    matched = [rw for rw in pop_rows if rw and repo in " | ".join(rw)]
                    if len(matched) != 1 or len(matched[0]) != 8 or f"https://github.com/{repo}" not in matched[0][2]:
                        e.append(f"{rel}: bad row/URL for {sid} ({repo})")
                        continue
                    rw = matched[0]
                    acct = "Org" if r["account_type"].strip() == "Organization" else r["account_type"].strip()
                    if not rs(rf"\(`?{re.escape(acct)}\s*/\s*{re.escape(r['account_public_repos'].strip())}`?\)", rw[2]):
                        e.append(f"{rel}: {sid} miss account={acct}/{r['account_public_repos']}")
                    role = r["git_role"].strip()
                    role_ok = role in rw[1] or (role.startswith("Mirror") and bool(rs(r"Miroir.*git\.postgresql\.org", rw[1]))) or (role == "Primary" and "Primaire" in rw[1])
                    if r["git_present"].strip() not in rw[1] or not role_ok:
                        e.append(f"{rel}: {sid} miss git_present/role")
                    cells = [re.split(r"\s+/\s+", _norm(rw[idx]).strip()) for idx in range(3, 8)]
                    for parts, cols in zip(cells[:3], (("stars", "forks", "watchers"), ("total_commits", "commits_12m"), ("contributors", "open_issues"))):
                        if len(parts) != len(cols) or any(not PARITY.has_csv_number(v, r[c]) for v, c in zip(parts, cols)):
                            e.append(f"{rel}: {sid} sub-cell {cols} got {parts!r}")
                    p6, p7 = cells[3], cells[4]
                    if len(p6) != 2 or p6[0].strip("` ") != r["primary_language"].strip() or p6[1].strip("` ") != r["license_spdx"].strip():
                        e.append(f"{rel}: {sid} lang/spdx got {p6!r}")
                    if len(p7) != 2 or p7[0].strip("` ") != r["latest_release"].strip() or p7[1].strip("` ") != r["pushed_at"].strip():
                        e.append(f"{rel}: {sid} release/pushed got {p7!r}")
                if any(pop[s]["commits_12m"].strip() == "0" for s in sids) and (not dormant_re.search(prose) or active_tier_re.search(prose)):
                    e.append(f"{rel}: dormant slug must state dormant/EOL and not Tier S/A")
        self.assertEqual(e, [], "\n".join(e))


if __name__ == "__main__":
    unittest.main()

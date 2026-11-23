# 11 — Ecosystem Popularity, Git Presence & Engineering Vitality

**Series:** PostgreSQL Multi-Master & Active-Active Architectures  
**Author:** Jean-Marie Renouard (`jmrenouard`) — [LightPath](https://www.lightpath.fr)  
**License:** MIT License

---

## 1. Live Telemetry Methodology (`2026-11-20T13:34:55Z`)

Architecture choices fail when teams mistake legacy brand awareness or cumulative GitHub stars for active engineering cadence. On **`2026-11-20T17:26:02Z`**, [`scripts/collect_popularity.py`](../../scripts/collect_popularity.py) queried live GitHub REST and GraphQL APIs across **22 catalog rows** (**19 public GitHub repos** plus **3 proprietary/managed engines**) into [`results/project_popularity.csv`](../../results/project_popularity.csv):

- **Exact Pagination (`total_commits`, `commits_12m`, `contributors`):** Calls `per_page=1` on each repo's `default_branch` (`since=2025-11-20T13:34:55Z` for 12m commits) and parses HTTP `Link: rel="last"` without cloning repositories.
- **True Watchers & Canonical Targets:** Uses `subscribers_count` (true watchers, avoiding `watchers_count` which duplicates stars), follows canonical redirects (`JumpMind/symmetric-ds` -> `jumpmindinc/symmetric-ds`), and queries `GoogleCloudPlatform/pgadapter` directly for the Spanner proxy.
- **Chronological Tags:** Reads `/releases/latest` with GraphQL `TAG_COMMIT_DATE DESC` fallback so tag-only repos (`postgres/postgres`, `pgEdge/spock`, `cockroachdb/cockroach`, `pgpool/pgpool2`) report current releases.

To contrast cumulative reach ($S$ stars) with active cadence ($C_{12\text{m}}$ commits in 12 months out of $C_{\text{total}}$), we track **12-Month Momentum ($M_{12\text{m}}$)**, **Velocity per Star ($R_{\text{vel/star}}$)**, and **Log-Decade Span ($D_{\text{decades}}$)**:

$$
M_{12\text{m}} = \frac{C_{12\text{m}}}{C_{\text{total}}} \times 100\%, \qquad R_{\text{vel/star}} = \frac{C_{12\text{m}}}{\max(S, 1)}, \qquad D_{\text{decades}} = \log_{10}\!\left(\frac{v_{\max}}{v_{\min}^{+}}\right)
$$

Live telemetry spans **three orders of magnitude**. Stars run from `26` (`pgq/londiste`) to `32,638` (`cockroachdb/cockroach`, $1{,}255\times$, $D = 3.10$). Total Commits run from `89` to `118,999` ($1{,}337\times$, $D = 3.13$). Positive 12m Commits span `8` to `7,581` ($948\times$, $D = 2.98$), and Contributors span `2` to `1,217` ($609\times$, $D = 2.78$). Per [Chapter 09](09_benchmarks_methodology_and_charts.md), `log10` axes are mandatory.

---

## 2. Complete Ecosystem Telemetry Matrix (`22` Rows)

| Solution (`#`) | Git Present (`Yes/No`) | Git Account (`Org/User`, Repos) | Repository | Stars / Forks | Commits (`Tot`/`12m`) | Contrib | Lang / SPDX | Tag (`Push`) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **PostgreSQL Core (`#1/#15/#16/#17`)** | Yes (Mirror*) | `postgres` (Org, 6) | `postgres/postgres` | 22,893 / 6,122 | 66,089 / **3,449** | 58* | C / NOASSERTION | `REL_19_0` (2026-11-20) |
| **Patroni HA (`#15b`)** | Yes | `patroni` (Org, 1) | `patroni/patroni` | 8,845 / 1,048 | 2,712 / 141 | 246 | Py / MIT | `v4.1.5` (2026-11-20) |
| **pgEdge Spock (`#2`)** | Yes | `pgEdge` (Org, 51) | `pgEdge/spock` | 769 / 59 | 1,616 / **621** | 32 | C / NOASSERTION | `v6.0.0-beta.2` (2026-11-20) |
| **pgEdge Snowflake (`#2b`)** | Yes | `pgEdge` (Org, 51) | `pgEdge/snowflake` | 103 / 14 | 239 / 48 | 20 | PLpgSQL / PG | `v2.6.1` (2026-11-18) |
| **pgEdge LOLOR (`#2c`)** | Yes | `pgEdge` (Org, 51) | `pgEdge/lolor` | 51 / 8 | 159 / 79 | 16 | C / PG | `v1.2.3` (2026-11-20) |
| **pglogical 2 (`#3`)** | Yes | `2ndQuadrant` (Org, 46) | `2ndQuadrant/pglogical` | 1,243 / 179 | 876 / **15** | 52 | C / NOASSERTION | `REL2_4_8` (2026-07-28) |
| **YugabyteDB (`#5`)** | Yes | `yugabyte` (Org, 314) | `yugabyte/yugabyte-db` | 10,670 / 1,481 | 41,469 / **5,342** | **1,217** | C / NOASSERTION | `v2026.1.3.0` (2026-11-20) |
| **CockroachDB (`#6`)** | Yes | `cockroachdb` (Org, 227) | `cockroachdb/cockroach` | **32,638** / 4,239 | **118,999** / **7,581** | 1,123 | Go / NOASSERTION | `v25.2.29` (2026-11-18) |
| **Citus (`#7`)** | Yes | `citusdata` (Org, 67) | `citusdata/citus` | 12,865 / 810 | 7,400 / 222 | 152 | C / AGPL-3.0 | `v14.3.0` (2026-11-20) |
| **OpenTenBase (`#8`)** | Yes | `OpenTenBase` (Org, 14) | `OpenTenBase/OpenTenBase` | 797 / 633 | 817 / **14** | 64 | C / NOASSERTION | `v5.0` (2026-11-09) |
| **Bucardo 5 (`#9`)** | Yes | `bucardo` (Org, 15) | `bucardo/bucardo` | 807 / 110 | 2,535 / **0** | 30 | Perl / NOASSERTION | `5.6.0` (2025-05-31) |
| **SymmetricDS (`#10`)** | Yes | `jumpmindinc` (Org, 8) | `jumpmindinc/symmetric-ds` | 882 / 241 | 14,926 / **425** | 96 | Java / N/A | `3.18.4` (2026-11-19) |
| **PgPool-II (`#11`)** | Yes (Mirror*) | `pgpool` (Org, 8) | `pgpool/pgpool2` | 448 / 102 | 4,627 / 140 | 35* | C / NOASSERTION | `V4_7_3` (2026-11-18) |
| **Slony-I (`#14a`)** | Yes | `ssinger` (User, 36) | `ssinger/slony1-engine` | 42 / 19 | 2,569 / **0** | 23 | C / NOASSERTION | `REL_2_2_11` (2024-03-11) |
| **PGQ Queue (`#14b`)** | Yes | `pgq` (Org, 13) | `pgq/pgq` | 427 / 23 | 89 / 8 | 7 | PLpgSQL / ISC | `v3.5.2` (2026-07-09) |
| **Londiste (`#14c`)** | Yes | `pgq` (Org, 13) | `pgq/londiste` | 26 / 8 | 195 / 8 | 5 | Py / ISC | `v3.12` (2026-07-22) |
| **RubyRep (`#14d`)** | Yes | `rubyrep` (User, 2) | `rubyrep/rubyrep` | 179 / 74 | 556 / **0** | **2** | Ruby / MIT | `v2.0.0` (2023-07-10) |
| **Spanner PGAdapter (`#13a`)** | Partial (Proxy) | `GoogleCloudPlatform` (Org, 1,545) | `GoogleCloudPlatform/pgadapter` | 94 / 36 | 4,040 / **934** | 22 | Java / Apache-2.0 | `v0.56.4` (2026-11-20) |
| **YT Cluster Lite (MIT Core) (`#18`)** | Yes (MIT Core; `ytserv` dual-lic.) | `DBinvent` (Org, 10) | `DBinvent/yt-cluster-lite` | 15 / 0 | 21 / **21** | **2** | Rust / MIT | `v1.21` (2026-11-20) |
| **EDB PGD / BDR (`#4`)** | No (Proprietary) | N/A (Proprietary) | N/A | N/A | N/A | N/A | N/A / Proprietary | N/A |
| **AWS Aurora Limitless (`#12`)** | No (Managed Cloud) | N/A (Proprietary) | N/A | N/A | N/A | N/A | N/A / Proprietary | N/A |
| **GCP Spanner & AlloyDB (`#13`)** | Partial (Proxy only) | N/A (Engine closed) | N/A | N/A | N/A | N/A | N/A / Proprietary | N/A |

**PostgreSQL 18.6 Core Vitality (`#17`):** [PostgreSQL 18.6 Native Clustering](solutions/pg18_native_clustering.md) ([Ch. 12](12_postgresql_18_clustering_and_benchmarks.md)) inherits the `postgres/postgres` Tier **S** core vitality profile directly: **`66,089`** total commits, **`3,449`** commits/12m, **`22,893`** stars, **`6,122`** forks, `postgres` `Organization` (`6` public repos), official mirror of `git.postgresql.org`.

*\*Notes: `postgres/postgres` (58) and `pgpool/pgpool2` (35) are official read-only mirrors of `git.postgresql.org`. Contributor counts reflect trusted committers pushing mailing-list patches, not total authors. `NOASSERTION` marks custom or dual licenses (PostgreSQL License on Core/Spock/pglogical, BSL/CSL on CockroachDB, Apache-2.0 + Polyform on YugabyteDB, BSD-like on PgPool/Bucardo/Slony). `cockroachdb` tags `v25.2.29` (LTS backport) beside `v26.2.12`. `pgEdge/spock` pairs `v6.0.0-beta.2` with stable `v5.0.14`.*

---

## 3. Logarithmic Charts & Interactive Explorer

Filter all 22 entries (19 public GitHub repos + 3 closed), toggle `log10` vs. linear axes, and cross-reference ecosystem vitality with empirical TPS/latency in the offline [**Interactive Benchmark Explorer (`dashboard/index.html`)**](../../dashboard/index.html).

### Chart 08 — Community Reach: Stars & Forks (`log10`)
![Log10 Stars and Forks Across PostgreSQL Solutions](../../assets/charts/chart_08_popularity_stars_forks_log.png)
*Contrasts cumulative reach (`15` to `32,638` stars, `0` to `6,122` forks) across 19 GitHub repos beside proprietary/managed engines.*

### Chart 09 — Engineering Vitality: Commits, 12m Velocity & Contributors (`log10`)
![Log10 Total Commits, 12m Velocity and Contributors](../../assets/charts/chart_09_popularity_commits_activity_log.png)
*Reveals the split between star inertia and active code investment: `pgEdge/spock` (`621`/12m) and `pgadapter` (`934`/12m) leap past dormant legacy tools.*

---

## 4. Popularity vs. Engineering Vitality: Five Structural Findings

```mermaid
flowchart LR
    M["Live GitHub Telemetry (19 Repos + 3 Closed)"] --> Q1["Hyper-Velocity Engines<br/>Cockroach 7,581/yr | Yugabyte 5,342/yr | PG Core 3,449/yr"]
    M --> Q2["High-Momentum Specialists<br/>PGAdapter 934/yr | pgEdge Suite 748/yr | SymmetricDS 425/yr"]
    M --> Q3["Mature Steady Infra<br/>Citus 222/yr | Patroni 141/yr | PgPool-II 140/yr"]
    M --> Q4["Maintenance / Star Inertia<br/>pglogical 15/yr | OpenTenBase 14/yr | PGQ+Londiste 16/yr"]
    M --> Q5["Dormant / EOL & Closed<br/>Bucardo/Slony/RubyRep 0/yr | EDB PGD / Aurora / Spanner"]
```

1. **GitHub Mirror Distortion (`postgres/postgres`, `pgpool/pgpool2`):** `postgres/postgres` shows `0` GitHub issues and only `58` GitHub contributors, which falsely implies a tiny team if read literally. Both `postgres/postgres` (`66,089` commits, `3,449`/12m, `6,122` forks, `REL_19_0`) and `pgpool/pgpool2` (`4,627` commits, `140`/12m, `V4_7_3`) are **official mirrors of `git.postgresql.org`** fed by mailing lists and Commitfest.
2. **Hyperscale Consensus vs. License Risk (`CockroachDB`, `YugabyteDB`):** `cockroachdb/cockroach` leads stars (`32,638`), total commits (`118,999`), and 12m velocity (`7,581` = `20.8`/day), while `yugabyte/yugabyte-db` leads contributors (`1,217`), org breadth (`314` repos), and momentum ($M_{12\text{m}} = 12.9\%$, `5,342`/12m). Both carry `8,029-9,772` open issues and non-standard licenses (`NOASSERTION`) requiring legal audit.
3. **The Star-Inertia Trap (`pgEdge/spock` vs. `pglogical` & `Bucardo`):** `2ndQuadrant/pglogical` (`1,243` stars) and `bucardo/bucardo` (`807` stars) outrank `pgEdge/spock` (`769` stars). Yet **`pgEdge/spock` shipped `621` commits/12m** ($M_{12\text{m}} = 38.4\%$, $R_{\text{vel/star}} = 0.81$). That velocity runs **`41.4x` faster than `pglogical`** (`15`/12m, `191` issues), while `bucardo` posted **`0` commits** since `2025-05-31`. With `snowflake` (`48`/12m) and `lolor` (`79`/12m, $M_{12\text{m}} = 49.7\%$), pgEdge totals **`748` commits/12m**.
4. **Mature Stability vs. Silent Workhorses (`Patroni`, `Citus`, `SymmetricDS`, `PGAdapter`):** `patroni/patroni` (`8,845` stars, `246` contributors, `1` repo, `MIT`) proves mature HA needs only `141` focused commits/12m (`v4.1.5`). `citusdata/citus` (`12,865` stars, `AGPL-3.0`) sustains PG 17/18 cadence (`222`/12m, `v14.3.0`). `jumpmindinc/symmetric-ds` (`882` stars, `14,926` commits, `425`/12m) runs quietly at industrial scale, while `GoogleCloudPlatform/pgadapter` logs **`934` commits/12m** on `94` stars ($R_{\text{vel/star}} = 9.94$) to maintain wire compatibility for a proprietary engine.
5. **High-Fork Stagnation & Personal-Account EOL (`OpenTenBase`, `PGQ`, `Slony-I`, `RubyRep`):** `OpenTenBase` shows a `0.79` fork-to-star ratio (`633/797`) yet only `14` `master` commits/12m (`421` issues). `pgq`/`londiste` stay on minimal life-support (`8`/12m each, `5-7` contributors), while `ssinger/slony1-engine` (`User`, `0`/12m) and `rubyrep/rubyrep` (`User`, `2` contributors, `0`/12m) are strictly EOL.

---

## 5. Bus-Factor & Production Sustainability Tiers

| Tier | Projects (`#`) | 12m Velocity | Bus Factor & Governance | Production Verdict |
| :---: | :--- | :---: | :--- | :--- |
| **S — Core** | `PostgreSQL Core` (`#1/#15/#16/#17`), `Patroni` (`#15b`) | 141-3,449 | Multi-vendor community; PostgreSQL / MIT licenses | **Lowest risk.** Default for 80%+ of OLTP clusters. |
| **A — Active OSS** | `CockroachDB` (`#6`), `YugabyteDB` (`#5`), `Citus` (`#7`), `pgEdge` (`#2`) | 222-7,581 | Funded teams (32-1,217 contribs); watch BSL/AGPL | **Production-viable.** Audit license and WAN limits. |
| **B — Niche** | `SymmetricDS` (`#10`), `PgPool-II` (`#11`) | 140-425 | Dedicated maintainers (35-96 contribs) | **Targeted use.** Heterogeneous sync (`#10`) or pooling (`#11`). |
| **C — Fragile / Young** | `pglogical 2` (`#3`), `OpenTenBase` (`#8`), `PGQ`/`Londiste` (`#14b/c`), `YT Cluster Lite` (`#18`) | 8-21 | Small core (2-64 contribs); `#18` bus-factor `1` + closed `ytserv` | **Avoid greenfield core.** Migrate legacy; track `#18` maturity. |
| **D — EOL** | `Bucardo 5` (`#9`), `Slony-I` (`#14a`), `RubyRep` (`#14d`) | **0** | Zero 12m commits; `User` repos (`#14a/d`), bus factor 1-2 | **Do not deploy.** Decommission legacy estates. |
| **Closed / Cloud** | `EDB PGD` (`#4`), `Aurora Limitless` (`#12`), `Spanner`/`AlloyDB` (`#13`) | Opaque (934 proxy) | Zero engine Git telemetry; commercial SLA & lock-in | **Contract audit.** Assess exit cost, `PGAdapter`, TCO. |

**YT Cluster Lite (`#18`) Vitality Nuance:** [YT Cluster Lite](solutions/yt_cluster_lite.md) (`DBinvent/yt-cluster-lite`, `15` stars, `0` forks, `21` total/`21` 12m commits, `v1.21`) is a 7-day-old MIT repo. It has `2` contributors (`1` human + `dependabot`, **bus factor = 1**), and its full `ytserv` coordinator stays closed under PolyForm Noncommercial/Commercial licensing.

---

**Navigation:** [Index](../../README.md) · [Ch. 10 — Streaming vs Logical vs Multi-Master](10_streaming_vs_logical_vs_multimaster.md) · [Ch. 12 - PG 18.6 Benchmarks](12_postgresql_18_clustering_and_benchmarks.md) · [Version française](../fr/11_popularite_et_vitalite_ecosysteme.md)

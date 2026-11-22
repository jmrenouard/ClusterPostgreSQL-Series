#!/usr/bin/env python3
"""Collect live GitHub API popularity and activity telemetry for PostgreSQL ecosystems."""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "project_popularity.csv"

CSV_COLUMNS = [
    "solution_id",
    "project_name",
    "git_present",
    "git_role",
    "github_repo",
    "git_account",
    "account_type",
    "account_public_repos",
    "stars",
    "forks",
    "watchers",
    "open_issues",
    "total_commits",
    "commits_12m",
    "contributors",
    "primary_language",
    "license_spdx",
    "archived",
    "created_at",
    "pushed_at",
    "latest_release",
    "snapshot_utc",
]

# Catalog mapping: (solution_id, project_name, git_present, git_role, github_repo)
CATALOG: list[tuple[str, str, str, str, str | None]] = [
    (
        "postgres-core",
        "PostgreSQL Core (#1/#15/#16)",
        "Yes (Mirror)",
        "Mirror (canonical: git.postgresql.org)",
        "postgres/postgres",
    ),
    ("patroni", "Patroni HA (#15b)", "Yes", "Primary", "patroni/patroni"),
    ("pgedge-spock", "pgEdge Spock (#2)", "Yes", "Primary", "pgEdge/spock"),
    (
        "pgedge-snowflake",
        "pgEdge Snowflake (#2b)",
        "Yes",
        "Primary (Companion)",
        "pgEdge/snowflake",
    ),
    (
        "pgedge-lolor",
        "pgEdge LOLOR (#2c)",
        "Yes",
        "Primary (Companion)",
        "pgEdge/lolor",
    ),
    ("pglogical2", "pglogical 2 (#3)", "Yes", "Primary", "2ndQuadrant/pglogical"),
    ("yugabytedb", "YugabyteDB (#5)", "Yes", "Primary", "yugabyte/yugabyte-db"),
    ("cockroachdb", "CockroachDB (#6)", "Yes", "Primary", "cockroachdb/cockroach"),
    ("citus", "Citus (#7)", "Yes", "Primary", "citusdata/citus"),
    (
        "opentenbase",
        "OpenTenBase (#8)",
        "Yes",
        "Primary (PG-XL/XC Successor)",
        "OpenTenBase/OpenTenBase",
    ),
    ("bucardo", "Bucardo 5 (#9)", "Yes", "Primary", "bucardo/bucardo"),
    ("symmetricds", "SymmetricDS (#10)", "Yes", "Primary", "jumpmindinc/symmetric-ds"),
    (
        "pgpool2",
        "PgPool-II (#11)",
        "Yes (Mirror)",
        "Mirror (canonical: git.postgresql.org)",
        "pgpool/pgpool2",
    ),
    (
        "slony1",
        "Slony-I (#14a)",
        "Yes",
        "Primary (Maintainer Repo)",
        "ssinger/slony1-engine",
    ),
    ("pgq", "PGQ Queue (#14b)", "Yes", "Primary", "pgq/pgq"),
    ("londiste", "Londiste (#14c)", "Yes", "Primary", "pgq/londiste"),
    ("rubyrep", "RubyRep (#14d)", "Yes", "Primary (Dormant)", "rubyrep/rubyrep"),
    (
        "spanner-pgadapter",
        "Cloud Spanner PGAdapter (#13a)",
        "Partial (Proxy only)",
        "Primary (Client Proxy; Engine Proprietary)",
        "GoogleCloudPlatform/pgadapter",
    ),
    (
        "yt-cluster-lite",
        "YT Cluster Lite (MIT Core) (#18)",
        "Yes (MIT Core; ytserv dual-licensed)",
        "Primary (MIT leaf/ext; ytserv PolyForm Noncommercial/Commercial)",
        "DBinvent/yt-cluster-lite",
    ),
    (
        "edb-pgd",
        "EDB Postgres Distributed (PGD/BDR) (#4)",
        "No (Proprietary)",
        "Proprietary (Closed Source)",
        None,
    ),
    (
        "aurora-limitless",
        "AWS Aurora Limitless (#12)",
        "No (Managed Cloud)",
        "Proprietary (Managed Cloud)",
        None,
    ),
    (
        "gcp-spanner-alloydb",
        "Google Cloud Spanner & AlloyDB (#13)",
        "Partial (PGAdapter only; engine proprietary)",
        "Proprietary (Managed Cloud)",
        None,
    ),
]

LAST_PAGE_RE = re.compile(r"[?&]page=(\d+)>;\s*rel=\"last\"")
HTTP_STATUS_RE = re.compile(r"(?m)^[ \t]*HTTP/\S*\s+\d{3}\b")
TAG_GRAPHQL = (
    'query($o:String!,$n:String!){repository(owner:$o,name:$n){'
    'refs(refPrefix:"refs/tags/",first:1,orderBy:{field:TAG_COMMIT_DATE,direction:DESC})'
    '{nodes{name}}}}'
)


def run_gh(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run gh CLI command and return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"gh command timed out after {timeout}s: {exc}"


def gh_json(endpoint: str) -> dict | list | None:
    """Call gh api and decode JSON payload, returning None on HTTP error."""
    rc, out, _ = run_gh(["api", endpoint])
    if rc != 0 or not out.strip():
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def split_http_response(raw: str) -> tuple[str, str]:
    """Split gh api -i response into final HTTP headers and body."""
    normalized = raw.replace("\r\n", "\n")
    matches = list(HTTP_STATUS_RE.finditer(normalized))
    tail = normalized[matches[-1].start() :] if matches else normalized
    headers, _, rest = tail.partition("\n\n")
    return headers, rest.strip()


def count_paginated(endpoint: str) -> str:
    """Count total items on a per_page=1 GitHub endpoint via Link rel=last."""
    rc, out, _ = run_gh(["api", "-i", endpoint])
    if rc != 0 or not out.strip():
        return "N/A"
    headers, body = split_http_response(out)
    for line in headers.splitlines():
        if line.lower().startswith("link:"):
            match = LAST_PAGE_RE.search(line)
            if match:
                return match.group(1)
    if not body:
        return "0"
    try:
        parsed = json.loads(body)
        if isinstance(parsed, list):
            return str(len(parsed))
    except json.JSONDecodeError:
        pass
    return "N/A"


def fetch_latest_release(full_name: str) -> str:
    """Fetch latest GitHub Release tag, falling back to newest tag by commit date."""
    rel = gh_json(f"repos/{full_name}/releases/latest")
    if isinstance(rel, dict) and rel.get("tag_name"):
        return str(rel["tag_name"])

    owner, repo = full_name.split("/", 1)
    rc, out, _ = run_gh(
        ["api", "graphql", "-f", f"query={TAG_GRAPHQL}", "-f", f"o={owner}", "-f", f"n={repo}"]
    )
    if rc == 0 and out.strip():
        try:
            nodes = json.loads(out)["data"]["repository"]["refs"]["nodes"]
            if nodes and nodes[0].get("name"):
                return str(nodes[0]["name"])
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            pass

    tags = gh_json(f"repos/{full_name}/tags?per_page=1")
    if isinstance(tags, list) and tags and tags[0].get("name"):
        return str(tags[0]["name"])
    return "N/A"


def collect_repo_row(
    entry: tuple[str, str, str, str, str | None],
    since_utc: str,
    snapshot_utc: str,
    user_cache: dict[str, tuple[str, str]],
) -> dict[str, str]:
    """Collect one live CSV row for a GitHub or proprietary solution entry."""
    sol_id, proj_name, git_present, git_role, repo_slug = entry
    if not repo_slug:
        return {
            "solution_id": sol_id,
            "project_name": proj_name,
            "git_present": git_present,
            "git_role": git_role,
            "github_repo": "N/A",
            "git_account": "N/A",
            "account_type": "Proprietary",
            "account_public_repos": "N/A",
            "stars": "N/A",
            "forks": "N/A",
            "watchers": "N/A",
            "open_issues": "N/A",
            "total_commits": "N/A",
            "commits_12m": "N/A",
            "contributors": "N/A",
            "primary_language": "N/A",
            "license_spdx": "Proprietary",
            "archived": "N/A",
            "created_at": "N/A",
            "pushed_at": "N/A",
            "latest_release": "N/A",
            "snapshot_utc": snapshot_utc,
        }

    meta = gh_json(f"repos/{repo_slug}")
    if not isinstance(meta, dict):
        raise RuntimeError(f"Failed to query GitHub repo metadata for {repo_slug}")

    full_name = str(meta["full_name"])
    owner = str(meta["owner"]["login"])
    branch = str(meta["default_branch"])

    if owner not in user_cache:
        acct = gh_json(f"users/{owner}")
        if isinstance(acct, dict):
            user_cache[owner] = (
                str(acct.get("type", "N/A")),
                str(acct.get("public_repos", "N/A")),
            )
        else:
            user_cache[owner] = ("N/A", "N/A")
    acct_type, acct_repos = user_cache[owner]

    q_all = urlencode({"sha": branch, "per_page": 1})
    q_12m = urlencode({"sha": branch, "since": since_utc, "per_page": 1})
    total_commits = count_paginated(f"repos/{full_name}/commits?{q_all}")
    commits_12m = count_paginated(f"repos/{full_name}/commits?{q_12m}")
    contributors = count_paginated(f"repos/{full_name}/contributors?per_page=1&anon=1")
    latest_release = fetch_latest_release(full_name)

    lic_obj = meta.get("license") or {}
    lic_spdx = str(lic_obj.get("spdx_id") or "N/A")
    lang = str(meta.get("language") or "N/A")

    return {
        "solution_id": sol_id,
        "project_name": proj_name,
        "git_present": git_present,
        "git_role": git_role,
        "github_repo": full_name,
        "git_account": owner,
        "account_type": acct_type,
        "account_public_repos": acct_repos,
        "stars": str(meta.get("stargazers_count", "N/A")),
        "forks": str(meta.get("forks_count", "N/A")),
        "watchers": str(meta.get("subscribers_count", "N/A")),
        "open_issues": str(meta.get("open_issues_count", "N/A")),
        "total_commits": total_commits,
        "commits_12m": commits_12m,
        "contributors": contributors,
        "primary_language": lang,
        "license_spdx": lic_spdx,
        "archived": "true" if meta.get("archived") else "false",
        "created_at": str(meta.get("created_at", "N/A")),
        "pushed_at": str(meta.get("pushed_at", "N/A")),
        "latest_release": latest_release,
        "snapshot_utc": snapshot_utc,
    }


def main() -> int:
    """Collect live GitHub telemetry and write results/project_popularity.csv."""
    parser = argparse.ArgumentParser(description="Collect live GitHub popularity telemetry.")
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    snapshot_utc = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    since_utc = (now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")

    rows: list[dict[str, str]] = []
    user_cache: dict[str, tuple[str, str]] = {}

    for entry in CATALOG:
        row = collect_repo_row(entry, since_utc, snapshot_utc, user_cache)
        rows.append(row)
        print(
            f"{row['solution_id']:20s} | {row['github_repo']:32s} | "
            f"stars={row['stars']:>6s} | forks={row['forks']:>5s} | "
            f"commits={row['total_commits']:>7s} | 12m={row['commits_12m']:>5s} | "
            f"contrib={row['contributors']:>5s} | rel={row['latest_release']}",
            flush=True,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.output} ({args.output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# RCA Register - Errors, Dead-Ends, Approximations & Roadmap Ideas

> **Governance Rule ([`AGENTS.md`](../AGENTS.md) & [`.agents/rules/project-governance.md`](../.agents/rules/project-governance.md))**:
> Update all four sections in English on **every request, every change, and every result**.

## 1. Errors & Bugs Encountered (`RCA-XXX`)

### RCA-001 - Empty Repository Rejects Initial Pull Request Targeting `main`
- **Date / Action**: `2026-11-19` (`ACT-001`)
- **Observed Symptom**: Opening a PR from a feature branch against `main` fails on GitHub when `main` has zero commits.
- **Root Cause Analysis**: GitHub requires at least one existing commit on the base branch (`main`) before a Pull Request diff can be computed.
- **Applied Change / Fix**: Committed the minimal baseline (`LICENSE`, `.gitignore`, `.gitattributes`) on `main` prior to opening Issue `#1` and branching `feat/issue-1-governance-and-test-harness`.
- **Result & Non-Regression Test**: Branching, PR creation, and merge workflow succeed cleanly.

### RCA-002 - Transient `Permission denied` on `make clean` over WSL2 9p Mount
- **Date / Action**: `2026-11-19` (`ACT-002`)
- **Symptom**: `rm -rf tests/__pycache__` failed immediately after `python3 -m unittest`.
- **Root Cause**: Host file indexer briefly locks `.pyc` directories on WSL2 9p mounts.
- **Fix**: Exported `PYTHONDONTWRITEBYTECODE := 1` and used `shutil.rmtree(..., ignore_errors=True)` in `Makefile` `clean`.
- **Result**: `make test` + `make clean` succeed cleanly without residue.

### RCA-003 - GitHub Push Rejected for `.github/workflows/ci.yml` Without `workflow` Scope
- **Date / Action**: `2026-11-19` (`ACT-002`)
- **Symptom**: `git push` failed with `refusing to allow an OAuth App to create or update workflow .github/workflows/ci.yml without workflow scope`.
- **Root Cause**: The active `gh` OAuth token holds `gist, read:org, repo, user` scopes only and lacks the `workflow` scope required by GitHub to push workflow YAML files.
- **Fix / Mitigation**: Excluded `.github/workflows/ci.yml` from PR so `Makefile` and test harness land cleanly on `main`; documented CI workflow addition as pending maintainer `workflow` scope authorization.
- **Result**: Remaining files push and merge cleanly; local `make lint` and `make test` run identically to CI.

## 2. Technical Dead-Ends & Abandoned Leads (`IMP-XXX`)

### IMP-001 - Monolithic Bootstrap Pull Request Exceeding 15,000 Characters
- **Date / Action**: `2026-11-19` (`ACT-001`)
- **Rejected Approach**: Bundling governance rules, living registers, `Makefile`, GitHub CI, and Python test suites in a single PR (~27.5K diff chars).
- **Reason**: Exceeded the 15,000-character PR diff limit. Split cleanly into PR `#1` (governance + `.env.example` + registers) and PR `#2` (`Makefile` + CI + test suites).

## 3. Current Approximations & Simplifying Assumptions (`APP-XXX`)

### APP-001 - Ephemeral Local Laboratory Credentials
- **Date / Action**: `2026-11-19` (`ACT-001`)
- **Assumption**: `.env.example` provides `PG_LAB_PASSWORD=pg_poc_ephemeral` for isolated local Docker Compose labs.
- **Impact & Removal Condition**: Strictly prohibited outside ephemeral containers; production deployments must inject externally managed credentials at runtime.

### APP-002 - Conditional Compose & Shell Linting Prior to PoC Modules
- **Date / Action**: `2026-11-19` (`ACT-002`)
- **Assumption**: `Makefile` `lint` and `.github/workflows/ci.yml` pass safely when zero `*.sh` or `docker-compose-*.yml` files exist during Phase 1 bootstrap.
- **Impact & Removal Condition**: Every future PoC PR adding `.sh` or `docker-compose-*.yml` files is automatically validated on addition.

## 4. Unimplemented Ideas & Future Roadmap (`IDEA-XXX`)

### IDEA-001 - Automated Cross-Topology `pgbench` & `sysbench` Matrix
- **Date / Action**: `2026-11-19` (`ACT-001`)
- **Proposal**: Implement `scripts/bench_*.sh` hooks driven by `make bench-all` to collect reproducible TPS, p95/p99 latency, and conflict rates across all PostgreSQL multi-master PoCs.

### IDEA-002 - GitHub Actions CI Workflow Enablement Pending `workflow` OAuth Scope
- **Date / Action**: `2026-11-19` (`ACT-003`)
- **Proposal**: Add `.github/workflows/ci.yml` executing `python3 -m unittest discover -s tests -v`, `bash -n`, and `docker compose config` once the maintainer grants the GitHub `workflow` OAuth scope (`RCA-003`).

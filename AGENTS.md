# ClusterPostgreSQL-Series Repository Rules (AGENTS.md)

These rules apply without exception to every contributor and agent working on `jmrenouard/ClusterPostgreSQL-Series` (Copyright (c) 2026 Jean-Marie Renouard - LightPath, https://www.lightpath.fr, MIT License).

## 1. Architecture & PR Diff Limit

1. **Exclusive `Makefile` Entry Point**: All lifecycle, test, lint, and benchmark actions run through `Makefile` (`make test`, `make lint`, `make check-math`, `make check-security`, `make up-*`, `make down-*`, `make test-*`, `make bench-all`).
2. **Strict PR Diff Limit (`< 15,000` characters)**: Every Pull Request diff (`git diff main...HEAD | wc -c`) MUST remain under **15,000 characters**. Split larger work into atomic issues and sequential PRs.
3. **Safe Shell Scripting**: Every `.sh` script MUST declare `set -euo pipefail`, quote all `"$VAR"` expansions, and clean up containers and volumes deterministically.

## 2. Mandatory 9-Step GitHub Workflow

For every request (feature, fix, study, benchmark, CI, or docs), execute all 9 steps in English:
0. **Open Issue (`gh issue create`)**: Create a tracked GitHub issue and obtain `#<id>`.
1. **Dedicated Branch**: Branch from `main` as `<type>/issue-<id>-<slug>` (never commit directly to `main`).
2. **Implement, Update Registers & Test**: Implement minimal changes, update `docs/ACTION_LOGBOOK.md` and `docs/RCA_REGISTER.md`, and pass 100% of `python3 -m unittest discover -s tests -v`.
3. **Stage Files (`git add`)**: Stage only tracked project files; exclude `.env`, logs, caches, and data directories.
4. **Conventional Commit (`git commit`)**: Commit atomically in English referencing `#<id>` while keeping diff `< 15,000` characters.
5. **Push Branch (`git push -u origin <branch>`)**: Push branch to remote.
6. **Create PR (`gh pr create`)**: Open a PR targeting `main` referencing `Closes #<id>`.
7. **Merge PR (`gh pr merge --merge --delete-branch`)**: Merge after checks pass, then `git pull --ff-only origin main`.
8. **Close Issue (`gh issue comment` + `gh issue close`)**: Post a concise English completion summary and close `#<id>`.

## 3. Living Governance Registers (`docs/ACTION_LOGBOOK.md` & `docs/RCA_REGISTER.md`)

Update both registers on **every request, every change, and every result**:
- `docs/ACTION_LOGBOOK.md`: Track `IN PROGRESS` requests (`ACT-XXX`) and archive verified `COMPLETED` changes and test results.
- `docs/RCA_REGISTER.md`: Record Errors/RCAs (`RCA-XXX`), Dead-Ends (`IMP-XXX`), Simplifying Assumptions (`APP-XXX`), and Roadmap Ideas (`IDEA-XXX`).

## 4. Language, Security & Math Integrity Policies

1. **Language Policy**:
   - **Strictly English** in `AGENTS.md`, `.agents/`, `docs/ACTION_LOGBOOK.md`, `docs/RCA_REGISTER.md`, `tests/`, `Makefile`, `.github/`, scripts, code comments, and all GitHub issues, PRs, commits, and comments.
   - **Bilingual Study Policy**: Technical study narratives and articles are maintained symmetrically under `docs/en/` (English) and `docs/fr/` (French).
2. **Zero Credentials, Zero External Secret-Store References & Zero PII**:
   - Never commit real passwords, API tokens, or references to personal credential stores or password tools.
   - Use only ephemeral laboratory placeholders (`${PG_LAB_PASSWORD:-pg_poc_ephemeral}` in compose/scripts and `.env.example`).
   - Do not include local host paths or personal PII; only public project attribution (`Jean-Marie Renouard`, `jmrenouard`, `LightPath`, `https://www.lightpath.fr`) is allowed.
3. **Markdown LaTeX Math Integrity**:
   - Display math `$$` MUST start at column 0 on dedicated lines with surrounding blank lines (never indented or single-line).
   - Never use `\operatorname{...}` (use `\arg\max`, `\arg\min`, or `\text{...}`).
   - Preserve `_` and `*`; keep inline `$x$` tight (no inner spaces); escape prose currency (`\$100`).

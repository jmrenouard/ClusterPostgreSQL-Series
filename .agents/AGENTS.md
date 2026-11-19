# Workspace Rules (.agents/AGENTS.md)

See root [`AGENTS.md`](../AGENTS.md) and `.agents/rules/` (`git-workflow.md`, `github-workflow.md`, `project-governance.md`).

- **Orchestration**: `Makefile` is the unified entry point for testing, linting, and PostgreSQL PoC lifecycles.
- **PR Size Cap**: Keep `git diff main...HEAD | wc -c` strictly `< 15,000` characters.
- **9-Step GitHub Workflow**: Always execute Steps 0–8 (`gh issue create` -> branch -> test + update `docs/ACTION_LOGBOOK.md` and `docs/RCA_REGISTER.md` -> `git add` -> `git commit` -> `git push` -> `gh pr create` -> `gh pr merge` -> `gh issue comment` + `gh issue close`).
- **Languages**: Strictly English in governance, registers, code, tests, CI, and GitHub; bilingual technical study docs in `docs/en/` and `docs/fr/`.
- **Security & Math**: Zero real secrets, zero external secret-store references, zero local host paths/PII, and strict LaTeX math compliance verified by `tests/`.

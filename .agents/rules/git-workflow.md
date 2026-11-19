---
trigger: always_on
description: Mandatory 9-step Git and GitHub workflow with < 15,000 character PR diff limit.
---

# Git Workflow Rule

For every task, execute the 9-step GitHub workflow in English:
0. Create GitHub issue (`gh issue create`).
1. Create dedicated branch `<type>/issue-<id>-<slug>` from `main`.
2. Implement changes, update `docs/ACTION_LOGBOOK.md` and `docs/RCA_REGISTER.md`, and verify `python3 -m unittest discover -s tests -v`. Keep `git diff main...HEAD | wc -c` `< 15,000`.
3. Stage tracked files cleanly (`git add`).
4. Commit using Conventional Commits referencing `#<id>`.
5. Push branch (`git push -u origin <branch>`).
6. Open PR targeting `main` with `Closes #<id>` (`gh pr create`).
7. Merge PR (`gh pr merge --merge --delete-branch`) and sync `main` (`git pull --ff-only origin main`).
8. Comment summary and close issue (`gh issue comment` + `gh issue close`).

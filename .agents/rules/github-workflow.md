---
trigger: always_on
description: Mandatory English-only GitHub lifecycle and bilingual study documentation policy.
---

# GitHub & Language Workflow Rule

1. **English-Only Operations**: All GitHub issues, PR titles/bodies, merge commits, issue comments, git commits, code comments, `AGENTS.md`, `.agents/`, `docs/ACTION_LOGBOOK.md`, `docs/RCA_REGISTER.md`, `tests/`, `Makefile`, and CI files MUST be strictly in English.
2. **Bilingual Study Content**: Architectural studies, comparative matrices, and benchmark reports reside symmetrically under `docs/en/` and `docs/fr/`.
3. **Atomic PRs**: Never open a PR whose `git diff main...HEAD | wc -c` reaches 15,000 characters; split work across sequential issues when needed.

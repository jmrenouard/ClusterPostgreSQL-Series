# How-To: Verify Limits, Math, and Hygiene Gates

Run this checklist before every commit to confirm Compose syntax, math rules, security, and strict EN/FR MkDocs builds.

## Prerequisites

- Install Python 3 with `PyYAML`, `mkdocs`, and `mkdocs-material`.
- Ensure Node.js and `docker` are available for full checks.

> [!CAUTION]
> Clean generated `site/` and `_site/` artifacts before staging commits, or repository limits and hygiene rules reject stale output files.

## Procedure

1. Lint every shell script and Compose topology:

```bash
make lint
```

2. Verify Markdown LaTeX math, security, and governance checks:

```bash
make test
make check-math
make check-security
```

3. Build and check the offline GitHub Pages bundle:

```bash
make pages-build
make pages-check
```

4. Build and verify both English and French MkDocs Material sites:

```bash
make docs-build
make docs-check
```

5. Check that your branch diff stays below the 15,000-character limit:

```bash
git diff main...HEAD | wc -c
```

## Validation

Confirm all unit tests, Pages bundle checks, and dual MkDocs `--strict` builds exit with code `0`.

## Rollback

Remove generated build outputs and caches immediately:

```bash
make clean
```

## Related Reference

Inspect technical failure codes and governance records in [Reference Index](../03-reference/index.md).

---
trigger: always_on
description: Mandatory governance registers, zero-secret/zero-PII policy, and Markdown LaTeX math rules.
---

# Project Governance Rule

1. **Living Registers**: Update `docs/ACTION_LOGBOOK.md` and `docs/RCA_REGISTER.md` on every request, every change, and every result.
   - `docs/ACTION_LOGBOOK.md`: Track `Ongoing Actions` and `Completed Actions` (`Request`, `Changes`, `Result`).
   - `docs/RCA_REGISTER.md`: Track `Errors & Bugs Encountered (RCA-XXX)`, `Technical Dead-Ends (IMP-XXX)`, `Current Approximations (APP-XXX)`, and `Unimplemented Ideas (IDEA-XXX)`.
2. **Zero Secrets & Zero PII**: Never commit real credentials, tokens, external secret-store references, or local host paths. Use `${PG_LAB_PASSWORD:-pg_poc_ephemeral}` only for local lab PoCs.
3. **LaTeX Math Integrity**: Enforce column-0 `$$` blocks with blank lines, ban `\operatorname`, keep inline `$x$` tight, preserve `_` and `*`, and escape currency `\$100`.

# WP-ANA-01 — Verification analysis: C front-end binding and dialect support

Lane: VERIFY (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-ANA-01. The
two owned SRS-001 requirements are the standing bar. The ADR-sensitive element (ADR-001 §2 core
language / front-end binding) is **Accepted** (python-clang, confirmed by WP-SPIKE-01); this note
verifies the decision-free implementation evidence only.

## Requirement → implementation → test evidence

| Requirement (SRS-001) | Implementation | Test evidence (re-run green 2026-11-18) |
|---|---|---|
| **TOOL-PAR-010** — parse C with production front-end (libclang) using exact compilation-database flags | `src/ectt/ana/frontend.py` (sole libclang dependency per SDD-001 S4.2/SDD-005 S5.3; flag passthrough from ingested entries) | 16 tagged tests: `tests/ana/test_dialects.py::test_flags_passthrough_from_compdb`, `::test_parse_errors_surface_with_locations`, dialect-parse happy paths; full set in `tests/ana/test_frontend.py` |
| **TOOL-PAR-020** — support C89, C99, C11, C17 and GNU dialect extensions | `frontend.py` dialect mapping | `tests/ana/test_dialects.py::test_c89_dialect_parse`, `::test_c99_dialect_parse`, `::test_c11_dialect_parse`, `::test_c17_dialect_parse`, `::test_gnu_dialect_extensions_parse`, `::test_dialect_normalization`, `::test_supported_dialects_inventory` (9 tagged) |

## Test run

```
tests/ana → 128 passed, 0 skipped in 3.08s
full suite → 447 passed, 4 skipped (baseline 4)
```

## Gaps / not covered

- None new. libclang is pinned at 18.1.1 in the dev install; dialect coverage is asserted against
  real parse results, not configuration tables alone.

## Result

**DONE** — both owned requirements carry named, passing tests against the real libclang front-end.

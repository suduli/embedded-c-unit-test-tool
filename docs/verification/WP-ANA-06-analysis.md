# WP-ANA-06 — Verification analysis: static function testability and macro resolution

Lane: VERIFY (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-ANA-06. The
three owned SRS-001 requirements are the standing bar. ADR-sensitive element (static-exposure
mechanism choice, ADR-001 §2/ADR-003 territory): no option is chosen here; the decision-free
verification of what exists is recorded.

## Requirement → implementation → test evidence

| Requirement (SRS-001) | Implementation state | Test evidence (re-run green 2026-11-18) | Status |
|---|---|---|---|
| **TOOL-PAR-080** — identify `static` functions; provide a mechanism to make them testable without modifying user source | Identification: `src/ectt/ana/interface.py` records `storage_class == "static"`; gate integration: `src/ectt/ana/eligibility.py` (expose_static capability flag, `static_not_exposed` reason). **Exposure mechanism (testability without source modification): not implemented** | `tests/ana/test_interface.py` (storage-class assertions at lines 56/67), `tests/ana/test_eligibility.py::test_static_function_not_exposed_is_ineligible`, `::test_static_function_eligible_with_exposure_flag` | **PARTIAL** |
| **TOOL-PAR-090** — resolve function-like and object-like macros used in interfaces; record where a macro obscures the true interface | **Not implemented** — no macro handling exists anywhere under `src/ectt/ana/` | none | **NOT COVERED** |
| **TOOL-PAR-170** — eligibility/observability gate with per-function observable channels and machine-readable gate reasons; discovery ≠ eligibility; requested-but-inaccessible reported explicitly | `src/ectt/ana/eligibility.py` (capability flags, per-function records) | `tests/ana/test_eligibility.py` — 10 tests incl. `::test_eligible_function_with_full_channels`, `::test_no_observable_channel_is_ineligible`, `::test_globals_alone_are_an_observable_channel` | **DONE** |

## Test run

```
tests/ana → 128 passed, 0 skipped
full suite → 490 passed, 4 skipped (baseline 4)
```

## Gaps / not covered

- TOOL-PAR-080's exposure mechanism (the part that must not modify user source) — belongs with
  harness/stub generation (WP-GEN-03, ADR-sensitive).
- TOOL-PAR-090 entirely — macro resolution in interfaces is unimplemented; its model shape (per
  SDD-002 S1) would extend the analysis model as an additive minor bump. No ADR question is
  decided by this note.

## Result

**PARTIAL** — TOOL-PAR-170 verified DONE; TOOL-PAR-080 verified as identification + gate only
(exposure mechanism open, ADR-sensitive); TOOL-PAR-090 has no implementation and no tests.

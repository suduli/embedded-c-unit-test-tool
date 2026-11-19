# WP-ANA-08 — Verification analysis: analysis model decision inventory

Lane: VERIFY (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-ANA-08. The
owned requirement TOOL-PAR-150 is the standing bar, restated as three falsifiable checks:

- **AC-1:** the model carries an explicit decision inventory whose completeness is recorded as
  data with exactly the statuses `not_extracted`, `partial`, `complete`.
- **AC-2:** the inventory cannot be omitted from a schema-valid model (schema enforces presence).
- **AC-3:** an inventory status unknown to the reader fails closed with a named error.

## Requirement → implementation → test evidence

| Requirement | Implementation | Test evidence (re-run green 2026-11-18) |
|---|---|---|
| TOOL-PAR-150 | `src/ectt/ana/persist.py` (inventory assembly + read gates), `src/ectt/ana/schema/analysis-model-1.1.schema.json` (required inventory), `src/ectt/ana/errors.py` (named failure) | `tests/ana/test_persist.py::test_assemble_emits_current_version_with_not_extracted_inventory` (AC-1), `::test_read_rejects_1_1_missing_decision_inventory` (AC-2), `::test_read_rejects_unknown_decision_inventory_status` (AC-3), `::test_read_accepts_1_1_with_inventories` (AC-1 statuses) |

## Test run

```
tests/ana → 128 passed, 0 skipped
full suite → 447 passed, 4 skipped (baseline 4)
```

## Gaps / not covered

- None for the owned requirement.

## Result

**DONE** — all three derived checks have named, passing tests.

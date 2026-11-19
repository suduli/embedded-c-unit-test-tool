# WP-SPIKE-02 — Verification analysis: nested type-aware test data editor spike (PySide6)

Lane: VERIFY (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

WP-SPIKE-02 owns **no SRS requirements** (validation spike; PLAN-001 §5.5); no package-specific
acceptance criterion is recorded in PLAN-001 §5.4. The per-spike pass criterion comes from
**PLAN-001 §4.4**, transcribed verbatim:

> **Pass criterion (PLAN-001 §4.4):** The type-aware nested test data editor in PySide6 against a
> struct-heavy interface — a 4-deep nested struct containing a union, a function-pointer member and
> a fixed array is editable at every level, type-validated, with enum constants by name, at
> interactive latency.

## Evidence chain (criterion → evidence)

| Criterion element | Recorded evidence (`spikes/spike-02-nested-editor/RESULTS.md`, ADR-001 §3.6) | Status |
|---|---|---|
| 4-deep nesting reaches the union | checklist item 1: `device → channel → actuators[0] → pixel`, 4 levels of struct/union nesting | met |
| Editable at every level | `QAbstractItemModel` + per-kind `QStyledItemDelegate`s over the real Qt classes; all 5 checklist items PASS twice (automated + `python app.py`) | met |
| Type-validated | checklist item 3: `999` into `pixel.channel.r` (range 0–255) rejected without committing; enforcement lives in model `validate()`, not `QValidator` (recorded finding for WP-GUI-11) | met |
| Enum constants by name | checklist item 2: `mode` combo lists `MODE_IDLE / MODE_ACTIVE / MODE_FAULT`; item 4: function-pointer member shows candidate handler names | met |
| Fixed array editable | checklist item 5: `samples` expands to 4 independently editable rows (array-adds-a-row depth nuance recorded for WP-GUI-11) | met |
| Interactive latency | cold start measured 242 ms (ADR-001 §3.6) | met |
| Verdict recorded | `PASS` in RESULTS.md §Verdict | met |

## Test evidence

The spike artifact carries its own pytest suite (`tests/test_checklist.py`, `tests/test_model.py`)
driving the real `TestDataModel`/`FieldDelegate`/`QTreeView` classes through `pytest-qt`. Re-run on
this worktree today (PySide6 installed into the chat-2 venv for this purpose — it is not a package
dev dependency):

```
12 passed, 3 warnings in 1.04s
```

Caveats recorded, both non-blocking:

1. RESULTS.md notes the automated run "substitutes for interactive verification"; a human should
   still open `python app.py` once before fully trusting the interactive feel. The two recorded
   design findings (array row-depth; validator-vs-`validate()` split) must be carried into
   WP-GUI-11's design per ADR-001 §3.6.
2. The spike has no pytest coverage inside `tests/` and owns no TOOL-* requirement — correct for a
   P0 spike feeding ADR-001 §3 and `WP-GUI-11`.

## Constraint compliance

- No `src/` or `tests/` files edited; no board or ADR writes; ADR-001 §3 (GUI stack) not reopened.

## Result

**Verified against the PLAN-001 §4.4 pass criterion** — every element has recorded, reviewable
evidence, and the spike's own 12-test suite re-runs green on this worktree. Human single-pass visual
confirmation of `app.py` remains advisory follow-up for the owner, not an open criterion element.

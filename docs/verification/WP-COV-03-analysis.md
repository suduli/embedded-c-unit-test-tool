# WP-COV-03 — Coverage threshold enforcement

Status: in progress (overnight lane B, 2026-11-21)
Requirements: TOOL-COV-130
Design elements: DSN-COV-* per PLAN-001 §3 (CMP-COV)
Dependencies: WP-COV-02 (implemented in this lane: `ectt.cov` merge + metrics)
Decisions applied as written (not re-decided):
- **ADR-004 coverage backend (owner answer, 2026-11-21): "GCC first"** — thresholds
  evaluate over the gcov-derived metric totals from WP-COV-01/02; Clang must not
  shape this item.

## Acceptance criteria

Derived from the SRS text (SRS-001 §12 line 419: "The tool shall enforce
configurable minimum coverage thresholds per metric and fail the run when they are
not met") and the PLAN-001 §5.4 row (`WP-COV-03` — Coverage threshold enforcement;
COV-130). PLAN-001 §5.4 records **no package-specific acceptance criterion** for
this package (flagged for reconciliation) — these are the derived, reviewable
criteria:

1. **AC-1 (COV-130 — per-metric thresholds).** Thresholds are configurable per
   metric (`statements`, `branches`) as exact minimum fractions (0 to 1, no
   floats). A metric strictly below its minimum records state `fail` with the
   exact recorded value and minimum; at or above it records `pass`. The overall
   result `passed` is false when any enforced metric failed — the run-level
   caller turns that into a run failure.
2. **AC-2 (enforcement scope).** Only configured metrics are enforced; an
   unconfigured metric is not evaluated. A configured metric whose totals are not
   applicable (no statements, or no branches — `total` is `None` or `0`) records
   state `not_applicable` explicitly and does not fail the run: coverage that
   cannot exist cannot be "not met", and the state is surfaced, never hidden.
3. **AC-3 (fail-closed inputs).** An unknown metric name, a minimum outside 0..1,
   or a non-Fraction minimum is refused with a named error.
4. **AC-4 (determinism).** The evaluation result serialises to a canonical
   dictionary (metric, state, covered, total, minimum) in configured order; no
   wall-clock; no network.

## Requirement → implementation → tests

| Requirement | Implementation | Tests (tests/cov/) |
|---|---|---|
| TOOL-COV-130 | `ectt.cov.thresholds.enforce_thresholds` with `MetricThreshold` (exact `Fraction` minima) | `test_metric_below_threshold_fails`, `test_metric_at_threshold_passes`, `test_metric_above_threshold_passes`, `test_overall_passed_is_false_when_any_metric_fails` |
| AC-2 scope | unconfigured metrics skipped; `not_applicable` state for empty totals | `test_unconfigured_metric_is_not_enforced`, `test_not_applicable_metric_does_not_fail` |
| AC-3 errors | named errors for unknown metric / invalid minimum | `test_unknown_metric_is_refused`, `test_minimum_outside_unit_interval_is_refused`, `test_non_fraction_minimum_is_refused` |
| AC-4 determinism | canonical dict, configured order | `test_evaluation_dict_is_canonical_and_ordered` |

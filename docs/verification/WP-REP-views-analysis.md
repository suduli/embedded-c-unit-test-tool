# WP-REP views — report views for re-execution results and thresholds (B2)

Status: implemented (overnight lane B, 2026-11-22)
Requirements served: TOOL-CBT-030/040 (subset run), TOOL-CBT-050/060 (run
comparison with coverage delta and removed tests), TOOL-CBT-080 (minimized
suite), TOOL-TGT-130 (host profile label on results), TOOL-COV-130 (threshold
results incl. the `no_data` state shown as a failure).
Design: the views are *renderers over other lanes' data classes* — they consume
only the narrow data classes named below (module-level imports, never package
roots), compute nothing from wall-clock or environment, and return plain
deterministic dictionaries. Other lanes call these views, so the function names
are stable API.

## Stable view functions (ectt.rep.views)

| Function | Consumes (narrow import) | Returns |
|---|---|---|
| `subset_run_view(subset)` | `ectt.cbt.reexecute.SubsetReExecution` | dict stating the suite was only partly run, from `suite_view` data (`partial` flag, `not_executed`, selected/not-selected partition, counts, per-test outcomes) |
| `run_comparison_view(comparison, coverage=None)` | `ectt.cbt.compare.RunComparison`, optional `ectt.cbt.compare.CoverageComparison` | dict with the exact outcome transitions, the removed tests, and the per-metric coverage delta (unmeasured stays `None`, never zero) |
| `minimized_suite_view(minimization, coverage_by_test)` | `ectt.cbt.minimize.Minimization` + the suite's coverage mapping | dict with kept vs redundant and the preserved union (sorted); refuses a minimization whose kept union no longer equals the full union |
| `host_profile_view(labelled)` | `ectt.ext.profile.LabelledResults` | dict carrying the profile id/label beside every result's id and outcome (the label rides beside the record, never replaces it) |
| `threshold_view(result)` | `ectt.cov.thresholds.ThresholdResult` | dict rendering every evaluation with its recorded state **verbatim** plus a `displayed` field: `no_data` is displayed as a failure (an empty or broken coverage run must not read as a pass), `not_applicable` displayed as exempt; `passed` mirrors `result.passed` |

## Acceptance criteria (derived; PLAN-001 §5.4 records no package-specific
criterion for this wiring — flagged for reconciliation)

1. **AC-1 (subset run).** `subset_run_view` states partiality from `suite_view`
   data only: `partial` true with the `not_executed` list and the selected /
   not-selected partition; counts derive from the same data. A `SubsetReExecution`
   whose `suite_view.partial` disagrees with its own `not_selected` partition is
   refused (`inconsistent_subset_view`) — a report must never contradict its data.
2. **AC-2 (run comparison).** The view carries `newly_failing` / `newly_passing` /
   `newly_added` / `removed` verbatim (sorted, as produced) and, when a coverage
   comparison is supplied, each metric's baseline/current totals and exact change
   (`None` when either side is unmeasured).
3. **AC-3 (minimized suite).** The view shows kept, redundant, and the preserved
   union (sorted). A `Minimization` whose kept-union differs from the full union
   against the supplied coverage mapping is refused (`stale_minimization`) — the
   view never presents a minimization that no longer preserves coverage.
4. **AC-4 (host profile label).** Every result carries its profile id and label;
   the view never alters outcomes; a label count disagreeing with the result count
   is refused (`label_result_mismatch`).
5. **AC-5 (thresholds, no_data shown as a failure).** The recorded `state` travels
   verbatim (`pass` | `fail` | `no_data` | `not_applicable`); `displayed` maps
   `no_data` to `fail` (and `not_applicable` to `exempt`); `passed` mirrors
   `result.passed` (an unallowed `no_data` fails the run).
6. **AC-6 (determinism).** Every view is a pure function of its inputs: sorted
   lists, canonical dict shapes, no wall-clock, no network. Identical inputs give
   identical view dicts.

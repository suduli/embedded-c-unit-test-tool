# Verification Analysis Note — WP-CBT-03 (Run Comparison and Coverage Delta)

RECON: PLAN-001 §5.4 records **no package-specific acceptance criterion** for this
package (flagged for reconciliation; register edits are owner territory). The
criteria below are derived from the SRS-001 requirements owned by this work package
and were written before the code. Executor: GLM (lane A, 2026-11-21 queue). The
WP-COV-02 cross-lane dependency is satisfied: lane B's ledger records WP-COV-02 =
DONE and `glm-night/20261121-b` was merged into this branch before WP-CBT-02
(post-merge gate green), so `ectt.cov` is present and its `MetricTotals` can be the
delta's unit of account (CMP-CBT depends on CMP-COV by design, SDD design graph).

## Acceptance criteria

- **AC-1 (TOOL-CBT-050):** comparing a current run against a baseline run reports,
  as sorted deterministic tuples — *newly failing* (passed in the baseline, fails
  now), *newly passing* (failed in the baseline, passes now) and *newly added*
  (present only in the current run); outcomes outside the S3 vocabulary
  (`pass | fail | error | timeout | not_run`) are refused with a named reason before
  any comparison happens.
- **AC-2 (TOOL-CBT-050, derived from the surfaced-never-dropped discipline):** a test
  present in the baseline but absent from the current run is reported as *removed* —
  visible, never silently dropped. (The SRS names three categories; the fourth is
  this package's anti-silent-loss rule and is flagged as derived.)
- **AC-3 (TOOL-CBT-050, purity):** identical runs compare to all-empty categories;
  the comparison is a pure function of the two outcome maps.
- **AC-4 (TOOL-CBT-060):** the coverage change relative to a baseline is reported
  per metric as exact integer arithmetic — current covered minus baseline covered —
  with both runs' totals carried for the report; a metric absent from either side is
  **unmeasured** and its change is `None` (unmeasured is never reported as a
  decrease or an increase).
- **AC-5 (determinism):** identical inputs give identical comparison documents.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-CBT-050** | The tool shall compare a test run against a previous run and report newly failing, newly passing, and newly added tests. | `src/ectt/cbt/compare.py` (`RunComparison`, `compare_runs`, `run_outcomes`) | **AC-1/AC-2/AC-3:** the comparison consumes plain outcome maps (`test_id -> outcome`, produced from a `ResultSet` by `run_outcomes`), classifies by exact outcome transitions and lists additions and removals; the vocabulary is checked up front, so a typo'd outcome is a named error, not a silent misclassification. **Test evidence:** `tests/cbt/test_compare.py` — `test_newly_failing_is_a_pass_that_now_fails`, `test_newly_passing_is_a_fail_that_now_passes`, `test_newly_added_tests_are_listed`, `test_removed_tests_are_surfaced_not_dropped`, `test_identical_runs_compare_empty`, `test_an_unknown_outcome_is_refused_by_name`, `test_the_comparison_is_sorted_and_deterministic`. |
| **TOOL-CBT-060** | The tool shall report coverage change relative to a baseline run. | `src/ectt/cbt/compare.py` (`MetricDelta`, `CoverageComparison`, `compare_coverage`) | **AC-4/AC-5:** per-metric deltas over `ectt.cov.metrics.MetricTotals` (the unit the merged WP-COV-02 machinery produces), exact integers, both totals carried; a metric missing on either side is unmeasured with change `None` — never read as a delta of zero. **Test evidence:** `tests/cbt/test_compare.py` — `test_statement_delta_is_exact`, `test_branch_delta_with_not_applicable_totals`, `test_an_unmeasured_side_reports_no_change`, `test_totals_travel_with_the_delta`, `test_the_comparison_document_is_deterministic`. |

## Design notes

- **Plain data in, plain data out.** Like WP-CBT-02, the comparison core consumes
  mappings (outcomes; per-metric `MetricTotals`) so the composition wires the run
  records and the coverage engine in without coupling this package to run plumbing.
- **Vocabulary up front.** The S3 outcome set is validated before classification;
  classification itself reacts only to `pass`/`fail` — an `error` is neither newly
  failing nor newly passing (it was not a verdict change).

## Not covered (recorded, not guessed)

- **Line-level newly-covered constructs** (which *lines* became covered) are the
  coverage documents' business; the delta here is per metric, as the requirement
  words it ("coverage change relative to a baseline run").
- **Cross-run flakiness attribution** (pass/fail/pass oscillation over more than two
  runs) needs a run history model this package does not own.
- **CLI/report wiring** of the comparison (lane second-pass item).

# Lane B ledger — overnight 2026-11-22

Setup: worktree wt-night-22b branched from local main fc0631c (the queue text said
e5184df; main had moved one docs-only commit further, "Add 11-22 two-lane queues
(wiring wave) and plan" — branched from current main as instructed). Baseline gates
at the branch point: 3557+1 = 3558 passed / 6 skipped, ruff, mypy, plan_check,
trace_check clean — identical to the stated baseline.

Assumptions taken (unattended run, conservative reading):
- (none yet)

| item | state | commit | est tokens | cumulative | notes |
|---|---|---|---|---|---|
| B2 | DONE | (pending) | ~120k | ~120k | ectt.rep.views: five stable view functions (names listed in docs/verification/WP-REP-views-analysis.md) over narrow data-class imports only (cbt.compare RunComparison/CoverageComparison, cbt.minimize Minimization, cbt.reexecute SubsetReExecution, cov.thresholds ThresholdResult, ext.profile LabelledResults). subset_run_view states partiality from suite_view data (refuses self-contradicting data: inconsistent_subset_view); run_comparison_view carries transitions + removed + per-metric delta (unmeasured stays None); minimized_suite_view shows kept vs redundant + preserved union (refuses stale_minimization incl. unknown kept/redundant ids); host_profile_view labels every result (refuses label_result_mismatch); threshold_view renders recorded state verbatim + displayed field mapping no_data->fail, not_applicable->exempt (refuses unknown_threshold_state), passed mirrors result.passed. Tested through the real enforce_thresholds path (no_data fails unless allowed). 14 tests. Gate green: 3572 passed. |

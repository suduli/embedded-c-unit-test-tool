# Verification Analysis Note — WP-REP-08 (Cross-Unit Summary and Coverage Trend)

Analysis evidence for requirements verified under WP-REP-08. Status: **implemented**
(evidence-backed).

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for
this package. Derived criteria (implemented as written; register edits are owner territory):

- **AC-1 (TOOL-REP-110, T — equivalence partitioning):** a summary built from report models
  of several runs partitions and carries the three dimensions the requirement names — units
  (coverage entries), targets (execution target ids), and toolchains — plus aggregated status
  totals, with each run's own facts preserved (run id, report id, counts, figures).
- **AC-2 (TOOL-REP-120, T):** a trend orders successive runs by their recorded
  ``generated_at`` (ties broken by run id — never by observation time) and records each
  unit's figures per run; units absent from a run have no entry in that run's series.
- **AC-3 (determinism):** both aggregations are pure functions of the model contents;
  dumps are byte-identical for identical inputs, and input order does not leak into the
  output.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-REP-110** | The tool shall produce a summary report aggregating results across multiple units, targets, and toolchains. | `src/ectt/rep/summary.py` (`build_cross_run_summary`, `RunSummary`, `CrossRunSummary`, `cross_run_summary_to_dict`, `dump_cross_run_summary`) | **Guarantee (partitioning):** the summary records the three named dimensions distinctly — `units` (sorted distinct coverage units), `targets` (sorted distinct recorded target ids), `toolchains` (sorted distinct recorded toolchains) — while keeping per-run detail (`RunSummary`: run id, report id, where, toolchain, target, test count, per-status counts, per-unit figures, generation time) and aggregated `status_totals`/`tests_total`.<br><br>**Guarantee (single-source aggregation):** every status and figure comes from the models' `test_statuses()`/`coverage_figures()` accessors; the aggregator never re-derives anything, so it cannot disagree with the per-run reports (WP-REP-01 guarantee inherited). Duplicate run ids are refused (`duplicate_run`); runs are ordered by run id so input order never leaks; models predating provenance (1.0 archives) report `unknown` toolchain/target/where rather than invented values.<br><br>**Test evidence:** `tests/rep/test_summary.py` — `test_summary_partitions_units_targets_toolchains`, `test_summary_aggregates_units_across_runs`, `test_summary_counts_status_families_across_runs`, `test_summary_refuses_duplicate_run_ids`, `test_summary_of_no_runs_is_empty_and_deterministic`, `test_summary_is_deterministic_and_input_order_free`, `test_summary_round_trips_through_canonical_json`, `test_summary_handles_1_0_models_without_provenance`. |
| **TOOL-REP-120** | The tool shall report coverage trend across successive runs. | `src/ectt/rep/summary.py` (`build_coverage_trend`, `TrendPoint`, `CoverageTrend`, `coverage_trend_to_dict`, `dump_coverage_trend`) | **Guarantee (successive order):** the trend's points are ordered by the models' recorded `generated_at` with run-id tie-break — a deterministic function of the persisted content (TOOL-REP-100 discipline), so re-running the aggregation over the same archives reproduces the same trend. Each point totals the run's coverage counters; `unit_series` records per-unit `(run_id, covered, total)` in run order, skipping runs where a unit is absent (documented, not zero-filled — a zero would fabricate a measurement).<br><br>**Test evidence:** `tests/rep/test_summary.py` — `test_trend_orders_runs_by_recorded_time`, `test_trend_ties_break_by_run_id`, `test_trend_totals_covered_and_total_per_run`, `test_trend_series_skips_units_absent_from_a_run`, `test_trend_refuses_duplicate_run_ids`, `test_trend_dump_is_deterministic`. |

## Design notes

- **Why ordering uses `generated_at` (content), not wall-clock at aggregation time.** The
  trend must be reproducible from archives alone; observation-time ordering would make the
  same archives produce different trends.
- **Why absent units are skipped, not zero-filled.** A zero for a unit a run did not measure
  would read as "0% covered" — misleading output (NFR-090). Absence is a fact; zero is an
  invention.
- **Why `unknown` for 1.0 archives.** TOOL-REP-110 aggregation is total over every loadable
  model; runs archived before the provenance extension genuinely lack the facts, and the
  summary marks them `unknown` instead of guessing.
- **Ratios stay out.** The aggregations carry raw counters, matching the model design (no
  renderer owns a rounding policy); percentage display belongs to a format renderer.

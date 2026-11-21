# Verification Analysis Note — WP-ATG-05 (Generation Reporting, Bounds and Capability Limits)

Analysis evidence for requirements verified under WP-ATG-05. Status: **implemented**
(evidence-backed) against a stub validation port, with the two limits stated under
"Not covered" (memory bound is the Python heap; inline assembly is not detectable from the
analysis model). Executor: Claude (lane A, 2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory).

- **AC-1 (TOOL-ATG-060 / DSN-ATG-060, per-run report):** every run reports the number of
  cases generated, the coverage achieved, and each construct left uncovered with its kind
  (line, branch, condition) and location. Only cases that were presented contribute
  coverage; constructs already covered before the run count and are not listed.
- **AC-2 (unmeasured is not uncovered):** if the port cannot measure a presented case,
  coverage is reported `unmeasured` and no uncovered list is asserted; a port that fails
  while measuring raises instead of reading as "uncovered"; a port reporting a construct
  that is not a run target is refused.
- **AC-3 (TOOL-ATG-100, scenario):** a run is bounded by configurable time, memory and
  number of cases. When a limit is reached the run stops, returns what it has generated
  (valid, non-stale cases and their coverage), and the report names the limit
  (`terminated_by`) and how many candidates were not attempted. Discarded candidates do
  not count toward the case limit.
- **AC-4 (honest bounds):** a configured memory limit is always enforced (the default probe
  measures the Python heap; tracing is started and restored around the run); limits must be
  positive; the report carries the configured limits and the reason for stopping, never a
  measured time or byte count, so it is deterministic.
- **AC-5 (TOOL-ATG-110, boundary value analysis):** constructs the engine cannot handle —
  dynamic memory, floating point, concurrency — are reported per function with their
  evidence; floating point is found through typedefs, struct members, arrays and pointers;
  only kinds the engine declares it cannot handle are reported; inline assembly, which the
  model cannot show, is listed as not assessed and is never implied absent.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-ATG-060** | The tool shall report, per generation run: number of test cases generated, coverage achieved, and the specific code constructs left uncovered. | `src/ectt/atg/run.py` (`run_generation`, `RunReport`, `CoverageReport`, `Construct`, `dump_run_report`); `CoverageDelta.newly_covered` in `src/ectt/atg/lifecycle.py` | **AC-1:** `test_the_report_gives_cases_generated_coverage_and_the_uncovered_constructs`, `test_all_constructs_covered_leaves_nothing_uncovered`, `test_only_presented_cases_contribute_coverage`, `test_already_covered_constructs_count_and_are_not_listed_as_uncovered`, `test_no_presented_case_means_zero_coverage_listing_every_target`, `test_discards_are_counted_by_reason_in_the_report_document`, `test_constructs_need_a_token_id_and_a_known_kind` (3). **AC-2:** `test_a_case_that_cannot_be_measured_makes_coverage_unmeasured_not_uncovered`, `test_a_port_reporting_an_unknown_construct_is_refused`, `test_measurement_failures_raise_instead_of_reading_as_uncovered`, `test_bad_run_inputs_are_refused`. **AC-4:** `test_the_report_is_deterministic_and_carries_no_measured_time_or_memory`, `test_the_report_names_what_limitations_were_and_were_not_assessed`. |
| **TOOL-ATG-100** | The tool shall bound generation effort by configurable time and memory limits and shall terminate gracefully, returning whatever was generated. | `RunLimits`, `BudgetClock`, `MonotonicClock`, `python_heap_probe`, `TERMINATIONS` | **AC-3:** `test_without_limits_a_run_completes`, `test_a_time_limit_stops_the_run_and_returns_what_was_generated`, `test_a_memory_limit_stops_the_run_gracefully`, `test_a_case_limit_stops_the_run_once_enough_cases_are_presented`, `test_discarded_candidates_do_not_count_toward_the_case_limit`, `test_a_limit_hit_on_the_first_candidate_returns_an_empty_but_valid_run`. **AC-4:** `test_the_default_memory_probe_measures_the_python_heap_and_restores_tracing`, `test_an_already_tracing_process_is_left_tracing`, `test_limits_must_be_positive_when_set` (5), `test_terminations_are_a_closed_vocabulary`. |
| **TOOL-ATG-110** | The tool shall report constructs the generation engine cannot handle (e.g. dynamic memory, floating point, concurrency, inline assembly) rather than failing silently. | `src/ectt/atg/capabilities.py` (`EngineCapabilities`, `Limitation`, `assess_capabilities`, `limitations_to_dict`, `ASSESSED_KINDS`, `NOT_ASSESSED_KINDS`) | **AC-5:** `test_allocator_calls_are_dynamic_memory` (8), `test_threading_locking_and_atomic_calls_are_concurrency` (11), `test_floating_point_is_found_through_typedefs_structs_arrays_and_pointers` (9), `test_a_type_name_missing_from_the_graph_is_still_recognised_when_it_is_a_float_builtin`, `test_only_kinds_the_engine_cannot_handle_are_reported`, `test_every_limitation_names_its_function_and_evidence_and_functions_are_independent`, `test_repeated_evidence_is_reported_once_and_distinct_evidence_separately`, `test_output_is_sorted_and_independent_of_function_order`, `test_failed_units_contribute_nothing`, `test_inline_assembly_is_never_claimed_absent`, `test_the_report_form_lists_the_engine_the_limitations_and_what_was_assessed`, `test_limitation_dicts_are_stable`, `test_an_engine_cannot_declare_an_unknown_kind` (3). |

## Design notes

- **Limits are cooperative.** They are checked between candidates, so a single very slow
  validation can overrun a time limit by its own duration; interrupting a build or run in
  progress belongs to the port's implementation (which owns the processes).
- **Candidate order is id order,** matching `validate_candidates`, so a bounded run stops at
  the same point whatever order the engine produced candidates in.
- **A time bound uses a monotonic clock for enforcement only.** No duration appears in the
  report; the production clock is `time.monotonic` and tests inject one.
- **No dependency on the other lane.** The unsupported-construct inventory that the
  eligibility gate (lane B) is gaining is not read here; this module covers the four kinds
  the requirement names.

## Not covered (recorded, not guessed)

- **Memory beyond the Python heap.** The default probe sees Python allocations only; a
  symbolic-execution engine's native memory is bounded by its adapter (an injectable probe
  is accepted for that).
- **Interrupting work in progress** when a limit is reached mid-validation (see design notes).
- **Inline assembly** detection: the analysis model does not record it. It is listed as not
  assessed in every report.
- **Concurrency and allocator detection by call name only:** a wrapper that allocates
  internally, or a call through a function pointer, is not seen. Evidence is the call that
  was seen, not a proof of absence.
- **Wiring** the run, the report and the limitations into a command, the progress display or
  `ectt.rep`; and a real port (build, execute, measure through the lower layers).

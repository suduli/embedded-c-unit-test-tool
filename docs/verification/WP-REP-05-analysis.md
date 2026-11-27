# Verification Analysis Note — WP-REP-05 (Certification Verification Report and Scope Statement)

Lane: B (night run of the 2026-11-23 queue) · 2026-11-27 · Worktree `wt-night-23b`, branch `glm-night/20261123-b`, baseline local `main` (b9b1262).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for
WP-REP-05. Derived from the SRS-001 text (TOOL-REP-060 — "a verification report
suitable for submission as certification evidence, containing: tool identification and
version, configuration, test cases executed with results, coverage achieved per metric,
justified exclusions, and the traceability matrix"; TOOL-REP-140 — "Every report shall
identify the test scope it covers and shall state explicitly what was excluded from that
scope"; both method *T*):

- **AC-1 (contents):** the report carries the tool version (with build id, dependency
  and schema versions and the provenance digest), the configuration the data records
  (execution facts, toolchain, host profile when the run has one), every test case with
  its status and the digest of the definition it executed, coverage per metric as raw
  counters beside the stated criteria, the justified exclusions with author, date and
  rationale, and the traceability matrix (per requirement: linked tests and verdict).
- **AC-2 (scope):** the report identifies what it covers (units, tests, requirements) and
  states explicitly what is excluded from that: tests not executed, a partial run, tests
  traced to no requirement, requirements not verified, and metrics not measured.
- **AC-3 (not claimed):** the report states what it does **not** claim. MC/DC and target
  execution are always listed as not claimed, and every known claim is either made or
  listed under `not_claimed` with its reason.
- **AC-4 (missing data):** an absent input is named in `missing_inputs`; the section that
  needs it reads `missing`; a list that cannot be determined is `None`, never an empty
  list; no figure or verdict is defaulted. Absent criteria never read as met.
- **AC-5 (claims):** a claim is written only when the caller requested it and the supplied
  data supports it. An unsupported claim is refused with `claim_not_supported` before
  anything is written. `target_executed` and `mcdc_measured` are never supported.
- **AC-6 (fail-closed inputs):** an unknown claim (`unknown_claim`), a metric the report
  cannot carry including MC/DC (`unknown_metric`), a criteria verdict recorded against
  other figures than the coverage shown beside it (`criteria_metrics_mismatch`) and a
  requirement verdict outside the trace vocabulary (`unknown_verdict`) are refused.
- **AC-7 (determinism):** identical inputs in any input order give byte-identical output;
  no wall clock is read; the report-creation timestamp is not rendered, while the
  execution timestamp is model content (TOOL-REP-070) and is recorded.

## Implementation

- `src/ectt/rep/certification.py` — `CertificationInputs` (seven optional inputs),
  `build_certification_report(inputs, claims=())`, `CertificationReport`
  (`claims`, `not_claimed`, `missing_inputs`, `to_dict`, `to_json_bytes`),
  `CERTIFICATION_CLAIMS`, `KNOWN_COVERAGE_METRICS`, `UNMEASURED_METRICS`.
- Imports from other packages are narrow data classes only: `MetricTotals`,
  `ThresholdResult`, `Justification`, `TraceabilityMatrix`, `HostProfile` (and the
  `ABI_DIMENSIONS` / `UNKNOWN_ABI` constants). None of `cov`, `trc` or `ext` imports
  `rep`, so no cycle is introduced.
- `tests/rep/test_certification.py` — the AC checks.

Two decisions worth stating, because both are places a certification report could
overstate:

- **Target execution is never claimed.** No data the tool records evidences a run on a
  target. `ectt.ext` holds target run *plans*; the execution metadata records where the
  runner was invoked and the build target (`ExecutionMetadata` is documented as "carried
  as metadata, never branched on"); a `HostProfile` labels a host run on behalf of a
  target build and by TOOL-TGT-130 never establishes target behaviour. The report records
  the execution facts verbatim and refuses `target_executed` always.
- **A claim the data does not support is refused, not softened.** The caller names the
  claims; each is checked against the data. A vacuous criteria result (`passed` with no
  evaluation) does not support `coverage_criteria_met`.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/rep/`) |
|---|---|---|
| TOOL-REP-060 (certification-evidence report: tool, configuration, tests, coverage, justified exclusions, traceability) | `certification.py` (`build_certification_report`, `_tool_section`, `_run_section`, `_coverage_section`, `_exclusions_section`, `_traceability_section`) | `test_certification.py::test_complete_data_records_every_required_element`, `::test_unmeasured_and_not_applicable_follow_the_stated_criteria`, `::test_a_criteria_verdict_from_other_figures_is_refused` |
| TOOL-REP-060 (missing data stated as missing) | `missing_inputs`; `None` for an undeterminable list; `passed: None` without criteria | `::test_each_missing_input_is_named_and_nothing_else_is` (6 inputs), `::test_missing_results_are_stated_as_missing_never_filled`, `::test_missing_coverage_is_stated_as_missing_never_filled`, `::test_missing_criteria_never_read_as_met`, `::test_missing_traceability_leaves_the_exclusions_undeterminable`, `::test_a_justification_without_a_current_digest_is_not_an_exclusion`, `::test_nothing_supplied_names_every_missing_input_and_claims_nothing`, `::test_data_gaps_inside_the_result_model_are_named`, `::test_an_unidentified_tool_is_named` |
| TOOL-REP-140 (identify the scope and state what is excluded) | `_scope_section`; `justified_exclusions` buckets | `::test_the_scope_statement_lists_what_is_excluded`, `::test_nothing_excluded_reads_as_empty_lists_not_missing`, `::test_complete_data_records_every_required_element` |
| TOOL-REP-140 (explicit statement of what is not claimed) | `claims` / `not_claimed`; `_unsupported_reason`, `_target_execution_reason` | `::test_a_claim_not_supported_by_data_is_refused` (10 cases), `::test_target_execution_is_refused_even_for_a_host_run_on_behalf_of_a_target`, `::test_claims_not_requested_are_listed_as_not_claimed`, `::test_a_metric_the_report_cannot_carry_is_refused` |
| TOOL-REP-100 (deterministic output) | canonical JSON over the document; no clock read | `::test_output_is_byte_stable_under_input_order`, `::test_the_report_creation_timestamp_is_not_rendered`, `::test_the_dictionary_is_a_fresh_copy` |
| fail-closed inputs | `_checked_claims`, `_checked_metrics`, `_check_criteria`, `_check_verdicts` | `::test_an_unknown_claim_is_refused` (6), `::test_a_metric_the_report_cannot_carry_is_refused` (2), `::test_a_criteria_verdict_from_other_figures_is_refused`, `::test_a_requirement_verdict_outside_the_trace_vocabulary_is_refused` |

## Not covered by this increment

- **No claim about a certification standard.** The report presents data and the explicit
  claims above; it does not assert that any ISO 26262 / IEC 61508 / DO-178C objective is
  met. Which objectives map to which evidence is an owner decision (PLAN-001 lists
  WP-REP-05 under the qualification tier as only partly budgeted).
- **Scope statement only in this report.** TOOL-REP-140 says *every* report; the other
  renderers (text, JSON, HTML, PDF, JUnit, Cobertura, LCOV) do not carry one. Adding it
  changes bytes of formats other lanes pin, so it is recorded in SECOND_PASS_B.
- **Units are taken from the report model's coverage entries.** A scope declared through
  `ectt.ing.scope.TestScope` is not consumed (WP-ING-04 is not a dependency of this
  package).
- **MC/DC** (TOOL-COV-050, WP-COV-05) is not measured; **target execution** has no
  evidence record. Both are named as not claimed rather than implemented.
- **Format:** canonical JSON only — there is no reader for the certification report and
  no human-readable renderer. The report has no content digest of its own (the result
  model's `report_id` and the provenance digest are carried instead).
- An unidentified tool (version `unknown`) is named under `missing_inputs` and still
  reported; the report does not refuse to build.

## Verification status

Gates re-run after the increment, each on its own: pytest green (44 new cases), ruff,
mypy, plan_check and trace_check exit 0.

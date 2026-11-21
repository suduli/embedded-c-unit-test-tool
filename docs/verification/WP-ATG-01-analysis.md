# Verification Analysis Note — WP-ATG-01 (Validation Port and Generated-Case Lifecycle)

Analysis evidence for requirements verified under WP-ATG-01. Status: **implemented**
(evidence-backed) against a stub validation port. Executor: Claude (lane A, 2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory). Decision D-02 ("Stable ids plus content digests") is implemented as written:
generated cases get a content-derived stable id and a content digest.

- **AC-1 (TOOL-ATG-050 / DSN-ATG-050, validation gate):** every candidate is built and run
  through the validation port before it is presented. A candidate that fails to build,
  crashes the harness, times out or hits a harness error is discarded and counted with its
  reason and diagnostics; it is never presented. A candidate that did not build is never
  executed. If the port itself fails, nothing is presented (the error is raised).
- **AC-2 (DSN-ATG-110, inverted dependency):** the port is declared in the generation
  package and bound at composition time; the package imports nothing from the build,
  execution, coverage, toolchain or harness-generation packages, and generation is testable
  against a stub port.
- **AC-3 (TOOL-ATG-040 / DSN-ATG-040, canonical emission):** a validated candidate is an
  ordinary `DataDrivenTestCase`: it round-trips through the `.tests` writer and parser, is
  editable afterwards without losing its id or marks, and has a content digest.
- **AC-4 (TOOL-ATG-070 / DSN-ATG-070, marked machine-generated):** the origin records
  author `atg` and `<engine>@<version>` in the artifact; `case_marks`, `format_mark` and
  `report_marks` give reports the same facts, and machine-generated cases (engine or AI
  provider) are distinguished from authored ones.
- **AC-5 (TOOL-ATG-080 / DSN-ATG-080, unreviewed expectations):** the expected values are
  the observed return value, globals and out-parameters; the case is `unreviewed`.
  `confirm_expected` is the explicit act that makes it `reviewed`, re-binds the content
  digest, and is refused for an authored case. Unreviewed generated cases can be passed to
  the traceability matrix so they do not count toward requirement verdicts.
- **AC-6 (determinism):** results do not depend on candidate order; equal vectors share one
  id and collapse to one validation.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-ATG-040** | Every automatically generated test case shall be emitted in the same format as a manually authored test case and shall be editable thereafter. | `src/ectt/atg/lifecycle.py` (`validate_candidates`, `_emit`, `make_candidate`) | **AC-3:** `test_a_generated_case_is_an_ordinary_data_driven_case`, `test_a_generated_case_survives_the_tests_file_writer_and_parser`, `test_a_generated_case_stays_editable_and_keeps_its_id_and_marks`, `test_candidate_ids_are_stable_and_content_derived`. |
| **TOOL-ATG-050** | Every automatically generated test case shall be compiled and executed before being presented; cases that fail to compile or crash the harness shall not be presented as valid. | `TestValidationPort`, `BuildOutcome`, `ExecutionOutcome`, `Discard`, `GenerationOutcome`, `validate_candidates` | **AC-1:** `test_only_candidates_that_built_and_ran_are_presented`, `test_discards_carry_their_diagnostics`, `test_a_candidate_is_never_executed_when_it_did_not_build`, `test_equal_vectors_collapse_to_one_validation`, `test_a_failing_port_presents_nothing_and_raises`, `test_an_unknown_execution_state_from_the_port_is_refused`, `test_no_candidates_is_an_empty_outcome`. **AC-2:** `test_the_stub_satisfies_the_port_protocol_and_a_partial_object_does_not`, `test_the_generation_package_does_not_depend_on_the_layers_below_it`. **AC-6:** `test_results_do_not_depend_on_candidate_order`. |
| **TOOL-ATG-070** | Automatically generated test cases shall be clearly marked as machine-generated in both the artifact and all reports. | `EngineInfo`, `is_machine_generated`, `case_marks`, `format_mark`, `report_marks` | **AC-4:** `test_origin_records_author_engine_and_version`, `test_marks_distinguish_generated_from_authored_cases`, `test_ai_provider_cases_are_machine_generated_too`, `test_report_marks_count_generated_and_unreviewed_cases`, `test_engine_identity_must_be_clean_tokens` (5 cases). Artifact side: the round-trip test above. |
| **TOOL-ATG-080** | Generated test cases shall record the observed behavior as the expected value, and shall mark that expected value as unreviewed until a user confirms it. | `_emit`, `expected_status`, `confirm_expected`, `unreviewed_test_ids` | **AC-5:** `test_observed_behaviour_becomes_the_expected_value_marked_unreviewed`, `test_a_void_function_records_no_expected_return`, `test_confirming_marks_reviewed_rebinds_the_digest_and_keeps_the_id`, `test_an_authored_case_cannot_be_confirmed`, `test_unreviewed_cases_do_not_count_toward_requirement_verdicts`. |

## Design notes

- **Vocabulary chosen here, to be confirmed:** `origin.review_state` is `unreviewed` or
  `reviewed` (absent for an authored case) and `origin.engine` is `<name>@<version>`. The
  `.tests` format already carries both fields but no document defines their values; a
  second-pass row asks for SDD-002 §5 to record them.
- **Confirmation re-binds the digest.** The review state is part of the case content, so
  confirming changes the digest and earlier runs become stale against the confirmed case.
  This is the conservative reading of D-02: evidence about an unreviewed expectation is not
  silently carried over to a reviewed one.
- **A timeout is a discard,** not a presented case: a case that cannot finish has no
  observed behaviour to record.
- **A port failure raises** instead of discarding: discarding on an infrastructure fault
  would turn "could not validate" into "invalid candidate".

## Not covered (recorded, not guessed)

- **The real port implementation** (build through CMP-BLD, run through CMP-EXH, measure
  through CMP-COV) is bound at composition time and is not part of this package; the
  engines that produce candidates are WP-ATG-02/03 (blocked on ADR-003).
- **Coverage deltas** are part of the port (`measure`, `CoverageDelta`) but nothing here
  consumes them; generation reporting and bounds are WP-ATG-05.
- **Machine-generated marks in the report renderers** (`ectt.rep`): `report_marks` and
  `format_mark` are the data, the renderers do not call them yet (second-pass row).
- **Nondeterministic behaviour** (a case whose observed value differs between runs) is not
  detected; one observed run is recorded.

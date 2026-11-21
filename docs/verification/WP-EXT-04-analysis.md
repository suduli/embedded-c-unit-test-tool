# Verification Analysis Note — WP-EXT-04 (Host and Target Test Parity)

Analysis evidence for requirements verified under WP-EXT-04. Status: **implemented**
(evidence-backed) as checks over plans, cases and results; no target hardware, simulator or
build is involved. Executor: Claude (lane A, 2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory). The TOOL-TGT-130 clause that "host success shall never establish target
behavior" is respected here (AC-5); the host-profile record of TOOL-TGT-130 itself is a
separate package and is not implemented.

- **AC-1 (TOOL-TGT-070, unmodified):** a host plan and a target plan are parity-equal
  exactly when they run the same cases (same ids, same content digests) and the same
  generated code (same digest). Any case present on one side only, any case whose content
  differs, and any difference in generated code is a named violation, all reported
  together and deterministically.
- **AC-2 (only configuration distinguishes):** the configuration that may differ is a
  typed record (toolchain, runner, result transport, target id, settings); the fields in
  which the two actually differ are listed. A host configuration reads results from stdout
  and has no target id; a target configuration names a target and retrieves results over
  one of the documented channels (semihosting, serial/UART). Malformed configurations are
  refused.
- **AC-3 (nothing host- or target-specific in a case):** test case content is scanned for
  absolute filesystem paths (Windows drive and Unix style), platform macros, `getenv`, and
  non-zero pointer literals (a memory-map address). Division and relative text are not
  mistaken for paths; null and integer casts are not mistaken for addresses. Each issue
  names the case, the field and the text.
- **AC-4 (outcomes line up):** the per-test outcomes of a host run and a target run are
  compared: agreements, divergences (for example a host pass that is a target failure) and
  tests run on one side only are all listed, never skipped.
- **AC-5 (host success proves nothing about the target):** neither the parity report nor the
  outcome comparison ever sets `establishes_target_behavior`; an agreement is a fact about
  those two runs only.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TGT-070** | Test cases shall execute unmodified on host and target, with only configuration distinguishing the two. | `src/ectt/ext/parity.py` (`ExecutionConfig`, `ExecutionPlan`, `check_parity`, `ParityReport`, `Violation`, `find_portability_issues`, `PortabilityIssue`, `compare_outcomes`, `OutcomeComparison`, `ParityError`) | **AC-1:** `test_identical_cases_and_code_with_different_configuration_is_parity`, `test_a_case_missing_on_either_side_is_a_violation`, `test_a_case_present_only_on_the_target_is_a_violation`, `test_the_same_case_id_with_different_content_is_a_violation`, `test_different_generated_code_is_a_violation`, `test_all_violations_are_reported_together_and_deterministically`, `test_case_order_does_not_matter`, `test_check_parity_needs_a_host_plan_and_a_target_plan`, `test_duplicate_case_ids_cannot_be_planned`. **AC-2:** `test_only_configuration_may_differ_and_the_differences_are_listed`, `test_invalid_configurations_are_refused` (9), `test_a_target_may_use_either_documented_channel` (2). **AC-3:** `test_a_clean_case_has_no_issues`, `test_absolute_paths_are_host_specific` (5), `test_division_and_relative_text_are_not_paths` (6), `test_platform_macros_are_host_or_target_specific` (8), `test_getenv_is_host_specific`, `test_non_zero_pointer_literals_name_a_memory_map` (4), `test_null_and_integer_casts_are_not_pointer_literals` (6), `test_every_value_field_is_scanned_with_its_path`, `test_issues_are_sorted_by_case_and_field_and_deduplicated`. **AC-4:** `test_equal_outcomes_agree_without_establishing_target_behavior`, `test_a_host_pass_that_is_a_target_failure_is_a_divergence`, `test_tests_run_on_one_side_only_are_listed_not_skipped`, `test_empty_runs_compare_as_consistent_but_prove_nothing`. **AC-5:** `test_parity_of_inputs_never_claims_target_behavior`, and the first and last outcome tests above. |

## Design notes

- **Defect found by test.** A Windows drive path such as `D:/data/in.txt` was reported twice,
  because the Unix-path pattern also matched the tail `/data/in.txt`; the pattern now
  excludes a slash that follows a drive colon
  (`test_absolute_paths_are_host_specific[D:/data/in.txt]`).
- **Defect found in review.** A drive letter needs a left boundary: without one the C string
  `"Error:
"` matched `r:\` and was reported as a drive path
  (`test_a_label_ending_in_a_colon_is_not_a_drive_path`). Configuration tokens are matched with
  `fullmatch`, because `$` also matches before a trailing newline.
- **Digest comparison, not file comparison.** Two plans are the same test when their case
  content digests and generated-code digest match (D-02); the files may live anywhere.
- **The lint is a lint.** It finds the common leaks and says so; a clean result is not a
  proof of portability. Width, alignment, packing, endianness and signedness differences
  between host and target (TOOL-TGT-130) are outside what content scanning can know.

## Not covered (recorded, not guessed)

- **TOOL-TGT-130:** the versioned host profile (target-to-host derivation, ABI differences,
  labelling every host-executed result with its profile). Not part of this item.
- **Actually executing** the same suite on a host and a target and comparing the runs: this
  package compares plans, cases and result sets that other components produce.
- **Generated-code identity** is checked by digest of the text supplied; producing that text
  for each side (and keeping any toolchain-specific preamble out of it) is the build step's.
- **Pointer values written as symbols or macros** (`UART0_BASE`) are not recognised as
  memory-map addresses; neither are platform conditions written without the common macros.
- **Wiring** into the CLI, the report renderers or the run-preparation step.

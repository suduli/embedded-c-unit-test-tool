# Verification Analysis Note — WP-EXT-07 (User-Supplied Target Execution Methods)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-EXT-07. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-PLG-040 (S, P3, T) and TOOL-TGT-120 (C, P3, T).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-PLG-040): a target execution method is addable through
  a documented interface and a user-supplied script — a declarative, frozen descriptor
  (method id, kind, script path) registered into a public method registry through
  registration only; an unknown method lookup and duplicate registration are named
  errors; listing is deterministic.
- AC-2 (falsifiable, from TOOL-TGT-120): a user-supplied flashing-and-communication
  script supports targets without a debug probe: the execution plan composes the
  script invocation with the harness and target inputs through the descriptor's
  documented template slots; a script without the template slots is a named error.
- AC-3 (falsifiable): script content is never executed at plan time — the plan is the
  composed command line; determinism asserted.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-PLG-040** | Adding a target execution method shall be possible through a documented interface and a user-supplied script. | `src/ectt/ext/usermethod.py` (`ExecutionMethodDescriptor`, `MethodRegistry`, `plan_user_execution`, `DuplicateMethodError`, `UnknownMethodError`), re-exported by `src/ectt/ext/__init__.py` | **Guarantee:** the documented interface is the descriptor — method id, script path, command template with the documented `{script}`/`{target}`/`{harness}` slots — registered into the public `MethodRegistry`; missing template slots, blank ids or script paths are named errors; duplicate ids and unknown lookups are named errors; listing is deterministic; descriptors are frozen and serialisable.<br><br>**Test evidence:** `tests/ext/test_usermethod.py` — `test_method_added_through_documented_interface_and_script`, `test_duplicate_and_unknown_methods_are_named_errors`, `test_listing_is_deterministic`, `test_method_without_template_slots_is_named_error`, `test_descriptor_is_frozen_and_deterministic`. |
| **TOOL-TGT-120** | The tool shall support execution on targets without a debug probe via a user-supplied flashing and communication script. | `src/ectt/ext/usermethod.py` (`plan_user_execution`) | **Guarantee:** the composed plan is the script invocation with target and harness substituted through the descriptor slots — a probeless target is served by the user script alone (demonstrated with a flashing-and-talking script composed exactly); script content is never executed at plan time (a nonexistent script path still composes, asserted); blank target/harness refuse the plan with a named error.<br><br>**Test evidence:** `tests/ext/test_usermethod.py` — `test_script_composition_supports_probeless_targets`, `test_script_content_is_never_executed_at_plan_time`, `test_blank_target_or_harness_is_named_error` (9 tests total, green in the WP-EXT-07 gate run: 805 passed, 4 skipped). |

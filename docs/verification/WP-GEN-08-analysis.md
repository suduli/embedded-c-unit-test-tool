# Verification Analysis Note — WP-GEN-08 (Stub Scope Control and Indirect-Call Stubbing)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-GEN-08. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-STB-080 (M, P2, T), TOOL-STB-100 (S, P2, T), TOOL-STB-140 (S, P2, T).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-STB-080): any individual function can be excluded from
  stubbing — excluded names appear in the plan's link-real list and never in the stub
  list; excluding a name that is not an external reference is a named error; the
  default plan stubs every reference.
- AC-2 (falsifiable, from TOOL-STB-100): standard-library functions are stubbed only
  on explicit user request — a stdlib name is never in the default stub list, and a
  request for a name outside the documented stdlib vocabulary (or not among the
  references) is a named error.
- AC-3 (falsifiable, from TOOL-STB-140): functions reached through function pointers
  — including via structure members — can be stubbed: pointer targets are included in
  the stub set and recorded with an indirect-call marker naming the access path; a
  pointer target that is not a reference is a named error.
- AC-4 (falsifiable): the plan is deterministic, frozen and serialisable; the stub
  list is sorted.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-STB-080** | The user shall be able to disable stubbing for any individual function, linking the real implementation instead. | `src/ectt/gen/stubscope.py` (`build_stub_plan`, `StubPlan`, `UnknownStubReferenceError`), re-exported by `src/ectt/gen/__init__.py` | **Guarantee:** `exclude` names any individual reference to leave real: excluded names appear in `link_real` and never in `stubs` — including when also requested as pointer targets (exclusion has top precedence); excluding all references empties the stub set; excluding a non-reference raises `UnknownStubReferenceError` naming it.<br><br>**Test evidence:** `tests/gen/test_stubscope.py` — `test_default_plan_stubs_every_reference`, `test_excluded_function_links_real_implementation`, `test_excluding_every_reference_leaves_no_stubs`, `test_unknown_exclude_is_named_error`, `test_excluded_pointer_target_never_stubbed`, `test_plan_is_deterministic_and_frozen`. |
| **TOOL-STB-100** | The tool shall support stubbing of standard library functions on explicit user request. | `src/ectt/gen/stubscope.py` (`STDLIB_FUNCTIONS`, `stdlib` parameter) | **Guarantee:** standard-library names are never stubbed by default (a referenced `memcpy` links the real implementation unless the user explicitly requests it); the explicit request must name a reference inside the documented 19-function vocabulary — a name outside it or not among the references raises the named error. Requests are recorded in `stdlib_stubbed`.<br><br>**Test evidence:** `tests/gen/test_stubscope.py` — `test_stdlib_never_stubbed_by_default`, `test_stdlib_stubbed_on_explicit_request`, `test_stdlib_request_outside_vocabulary_is_named_error`, `test_stdlib_request_for_unreferenced_name_is_named_error`. |
| **TOOL-STB-140** | The tool shall support stubbing functions reached through function pointers, including function pointer members of structures. | `src/ectt/gen/stubscope.py` (`pointer_targets`, `pointer_paths`, `POINTER_TARGET_MARKER`) | **Guarantee:** pointer-reached functions are included in the stub set and recorded with their access path (e.g. `cb_table.dispatch` for a structure member) in `pointer_paths`; a pointer target that is not a reference raises the named error; exclusion still wins over pointer stubbing.<br><br>**Test evidence:** `tests/gen/test_stubscope.py` — `test_pointer_targets_stubbed_with_access_path`, `test_pointer_target_must_be_a_reference`, `test_excluded_pointer_target_never_stubbed`. |

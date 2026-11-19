# Verification Analysis Note — WP-GEN-03 (Static Exposure and Integration-Scope Harness)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-GEN-03. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-HAR-030 (S, P2, T) and TOOL-HAR-080 (M, P2, T).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-HAR-030): static exposure is optional — the generator
  defaults to not exposing UUT `static` functions; with `expose_statics=True` the
  generated harness includes the UUT source translation unit (`#include "uut.c"`)
  and emits a greppable exposure record with the static prototype for every static
  function of the UUT, giving test code access to file-static functions; statics are
  never exposed when the flag is off.
- AC-2 (falsifiable, from TOOL-HAR-080): an integration-level harness spanning two
  or more designated units includes every member header, exposes the non-static
  functions of every member, and records exactly the callees defined by no member as
  the only stub requirements (`ectt:stub-required:` markers); intra-set calls are
  never marked. Fewer than two units is a named error.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-HAR-030** | The generated harness shall optionally expose `static` functions of the UUT for testing. | `src/ectt/gen/exposure.py` (`generate_with_statics`, `STATIC_EXPOSURE_MARKER`), re-exported by `src/ectt/gen/__init__.py` | **Guarantee:** exposure is optional and off by default — the WP-GEN-01 harness never carries the static marker; `generate_with_statics` includes the UUT source translation unit (`#include "uut.c"`, which gives test code direct access to file-static functions) and emits one greppable record per static function with its prototype (`ectt:exposes-static: int hidden()`), types resolved through the model's type graph.<br><br>**Test evidence:** `tests/gen/test_exposure.py` — `test_static_exposure_is_optional_and_off_by_default`, `test_static_exposure_includes_uut_source_and_records_statics`, `test_static_exposure_lists_every_static_function`. |
| **TOOL-HAR-080** | The tool shall generate an integration-level harness spanning two or more units, stubbing only dependencies external to the selected set. | `src/ectt/gen/exposure.py` (`generate_integration_harness`, `IntegrationHarness`, `IntegrationScopeTooSmallError`), stub list via `ectt.ing.conflicts.stub_requirements` | **Guarantee:** an integration harness over two or more designated units includes every member header, exposes every member's non-static functions (sorted, deterministic), and — when callee references and member definitions are supplied — marks exactly the callees defined by no member as the only stub requirements (`ectt:stub-required:` markers); intra-set calls are never marked. Fewer than two units raises `IntegrationScopeTooSmallError`; a member not in the model raises `UnknownUnitError`.<br><br>**Test evidence:** `tests/gen/test_exposure.py` — `test_integration_harness_needs_two_units`, `test_integration_harness_spans_members`, `test_integration_harness_marks_only_external_stubs`, `test_integration_member_not_in_model_is_named_error`. |

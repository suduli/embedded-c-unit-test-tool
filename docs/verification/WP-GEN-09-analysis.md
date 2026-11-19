# Verification Analysis Note — WP-GEN-09 (Stub Regeneration and Unsupported-Construct Flagging)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-GEN-09. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-STB-110 (M, P2, T), TOOL-STB-120 (M, P2, T), TOOL-STB-130 (S, P2, T).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-STB-110): every generated stub carries a clearly
  delimited user-editable body region (`ectt:stub-body: <name>` begin/end markers)
  separated from the regenerated signature region.
- AC-2 (falsifiable, from TOOL-STB-120): re-synchronising a stub whose signature
  changed preserves the user-authored body where the change permits — identical
  parameter names and unchanged return type — and regenerates the body with a report
  entry naming the change where it does not (parameter names/count changed, or the
  return type changed); every outcome is reported explicitly.
- AC-3 (falsifiable, from TOOL-STB-130): constructs the stub generator cannot fully
  handle — variadic parameters and complex function-pointer parameters — are flagged
  in the generated output with the consistent greppable marker
  `ectt:unsupported-construct`, naming the function and the reason; handleable
  constructs are never flagged.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-STB-110** | Generated stubs shall be user-editable, with editable regions clearly delimited from regenerated regions. | `src/ectt/gen/stubregen.py` (`stub_with_user_region`, `extract_user_body`, `STUB_BODY_REGION_PREFIX`), re-exported by `src/ectt/gen/__init__.py` | **Guarantee:** every stub renders with a `ectt:stub-body: <name>` begin/end region around the body — the signature line above it is the regenerated region, explicitly marked "do not edit the signature below" — and `extract_user_body` retrieves exactly the user-authored text (empty when no region exists or the name differs).<br><br>**Test evidence:** `tests/gen/test_stubregen.py` — `test_stub_body_is_delimited_user_region`, `test_extract_missing_body_is_empty`. |
| **TOOL-STB-120** | When the source function signature changes, the tool shall re-synchronize the stub signature while preserving the user-authored body where the change permits, and shall report where it does not. | `src/ectt/gen/stubregen.py` (`resync_stub`, `StubResyncResult`) | **Guarantee:** re-synchronisation renders the new signature always; the user body is preserved exactly when the change permits — same parameter names in order and unchanged return type (types may tighten) — and is regenerated with an explicit report entry naming the cause where it does not (parameter list changed, return type changed, or no user body captured). Every outcome reports.<br><br>**Test evidence:** `tests/gen/test_stubregen.py` — `test_resync_preserves_body_when_change_permits`, `test_resync_reports_parameter_list_change`, `test_resync_reports_return_type_change`, `test_resync_without_captured_body_is_reported`, `test_resync_error_derives_from_gen_error`. |
| **TOOL-STB-130** | The tool shall flag, in generated output, every construct it could not fully handle (e.g. variadic functions, complex function pointers) using a consistent, greppable marker. | `src/ectt/gen/stubregen.py` (`flag_unsupported_constructs`, `render_stub_output`, `UnsupportedConstruct`, `UNSUPPORTED_CONSTRUCT_MARKER`) | **Guarantee:** variadic parameters and complex function-pointer parameters are flagged in the generated output with the consistent `ectt:unsupported-construct: <function> <reason>` marker — the flagged function gets no stub body, handleable functions get normal stubs, and handleable constructs (plain pointers, struct pointers) are never flagged.<br><br>**Test evidence:** `tests/gen/test_stubregen.py` — `test_variadic_parameter_is_flagged`, `test_complex_function_pointer_parameter_is_flagged`, `test_handleable_constructs_never_flagged` (10 tests total, green in the WP-GEN-09 gate run: 700 passed, 4 skipped). |

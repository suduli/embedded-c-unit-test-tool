# Verification Analysis Note — WP-GEN-11 (Call Wrapping of Intra-Unit Calls)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-GEN-11. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-STB-090 (S, P3, T) — *The tool shall support intercepting calls made by
the UUT to functions defined within the UUT itself (call wrapping), without modifying
user source.*

## Acceptance criteria

- AC-1 (falsifiable): call wrapping is planned only for callees the UUT defines
  inside itself (internal classification); a wrap request naming a callee that is
  not internal is a named error; the plan is deterministic and frozen.
- AC-2 (falsifiable): the generated wrap seam is text in the harness layer only — a
  macro redirection (`#define <callee> ectt_wrap_<callee>` before the UUT source
  include, `#undef` after) plus wrapper declarations — so intercepting works without
  modifying any user source file; the seam carries the greppable
  `ectt:call-wrap:` marker per wrapped callee and unwraps cleanly after the include.
- AC-3 (falsifiable): an empty wrap request produces an empty seam; the seam renders
  deterministically.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-STB-090** | The tool shall support intercepting calls made by the UUT to functions defined within the UUT itself (call wrapping), without modifying user source. | `src/ectt/gen/callwrap.py` (`plan_call_wraps`, `CallWrapPlan`, `render_call_wrap_seam`, `NotInternalCalleeError`, `CALL_WRAP_MARKER`), re-exported by `src/ectt/gen/__init__.py` | **Guarantee:** wrap requests are validated against the analyzer's internal-call classification — a request naming a callee the UUT does not define itself raises `NotInternalCalleeError` naming the offender; the generated seam is text in the harness layer only: `#define <callee> ectt_wrap_<callee>` before the UUT-source include (which only the WP-GEN-03 static-exposure harness performs), `#undef` after, marker-commented, order-verified — so interception requires zero user-source modification. Empty plans render an empty seam; output is deterministic; plans are frozen with sorted deduplication.<br><br>**Not covered:** executing the wrapped call path (needs the compiled harness, WP-EXH-01/BLD-01); wrapper-body authoring (user region or generated default) is a follow-up refinement on top of this seam.<br><br>**Test evidence:** `tests/gen/test_callwrap.py` — `test_wrap_plan_covers_internal_callees`, `test_wrap_request_for_external_callee_is_named_error`, `test_seam_redirects_without_user_source_modification`, `test_empty_wrap_plan_renders_empty_seam`, `test_duplicate_requests_deduplicated`, `test_plan_is_frozen_and_deterministic`, `test_error_derives_from_gen_error` (7 tests, green in the WP-GEN-11 gate run: 731 passed, 4 skipped). |

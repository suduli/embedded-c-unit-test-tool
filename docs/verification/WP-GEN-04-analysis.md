# Verification Analysis Note — WP-GEN-04 (Regeneration Contract and Conflict Reporting)

Board acceptance criterion (PLAN-001 §5.4, quoted): *Regenerating a harness whose
user region is still valid preserves it byte-for-byte; regenerating one whose UUT
signature changed incompatibly reports a conflict and writes nothing.*

Supporting SRS requirements owned by this work package: TOOL-HAR-090 (M, P2, I),
TOOL-HAR-100 (M, P2, T), TOOL-HAR-110 (S, P2, T), TOOL-CBT-070 (S, P2, T).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-HAR-090): every generated harness carries a header
  identifying it as generated, the generating tool version, the source model (UUT
  header), and an interface fingerprint (a deterministic digest of the exposed
  signatures); rendering twice from an identical model yields byte-identical text.
- AC-2 (falsifiable, from TOOL-HAR-100, first clause): user edits live in designated
  user regions (`ectt:user-region: <name>` begin/end markers, emitted empty by the
  generator); regenerating a harness whose interface is unchanged preserves the
  user-region contents byte-for-byte and, for identical inputs, the whole file.
- AC-3 (falsifiable, from TOOL-HAR-100 second clause + board AC): when the UUT
  signature changed incompatibly — the interface fingerprint differs — regeneration
  reports a conflict listing the added/removed/changed signatures and writes nothing:
  `apply_regeneration` refuses to write a conflicting result and raises the named
  error with the file untouched.
- AC-4 (falsifiable, from TOOL-HAR-110): staleness of an existing harness is detected
  by fingerprint comparison against the freshly generated interface, with the
  mismatch reported.
- AC-5 (falsifiable, from TOOL-CBT-070): a test case records the interface
  fingerprint it was authored against; the same comparison detects a test case gone
  stale because the interface it exercises has changed.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-HAR-090** *(also the board AC's fingerprint basis)* | Generated harness code shall be human-readable, deterministically formatted, and carry a header identifying it as generated, the generating tool version, and the source model. *(Method I)* | `src/ectt/gen/harness.py` (banner, `tool_version`, `interface_fingerprint`), re-exported by `src/ectt/gen/__init__.py` | **Guarantee:** every generated harness carries the three-line header — generated marker, tool version plus interface fingerprint, source-model UUT — and renders byte-identically from an identical model (asserted directly). The fingerprint is a deterministic sha-256 digest (truncated to 32 hex chars) of the canonical exposed-signature text, computed from the same model every time. Readability: the output is comment-annotated C with stable section order.<br><br>**Test evidence:** `tests/gen/test_regen.py` — `test_header_identifies_generated_version_and_model`, `test_rendering_is_byte_identical_for_identical_input`. |
| **TOOL-HAR-100** | Regenerating a harness shall preserve user modifications in designated user-editable regions, or shall detect and report conflicts rather than silently overwriting. *(also the board AC)* | `src/ectt/gen/regen.py` (`regenerate`, `apply_regeneration`, `RegenerationResult`, `HarnessRegenerationConflictError`), user-region slots in `src/ectt/gen/harness.py` | **Board AC, preserved clause:** user edits live in `ectt:user-region:` begin/end markers (emitted empty by the generator for `test-cases` and `user-helpers`); regenerating with an unchanged interface fingerprint re-inserts the old region contents and the preserved output equals the old text byte-for-byte (asserted with equality, not containment).<br><br>**Board AC, conflict clause:** a changed UUT signature changes the fingerprint; the result is `STATUS_CONFLICT` with `text=None` and a conflict list naming every added/removed/changed signature; `apply_regeneration` refuses to write and raises `HarnessRegenerationConflictError` — the target file is verified byte-for-byte untouched after the refused write.<br><br>**Test evidence:** `tests/gen/test_regen.py` — `test_regeneration_preserves_user_regions_byte_for_byte`, `test_conflicting_regeneration_reports_and_writes_nothing`, `test_conflict_reports_removed_and_added_signatures`, `test_apply_writes_preserved_result`. |
| **TOOL-HAR-110** | The tool shall detect and report when the UUT interface has changed such that an existing harness is stale. | `src/ectt/gen/regen.py` (`check_harness_staleness`, `HarnessStaleness`) | **Guarantee:** staleness is the fingerprint comparison plus named reasons — a harness without a fingerprint header is stale ("no interface fingerprint"), a fingerprint mismatch is stale with the added/removed/changed signature list as reasons; an unchanged interface is fresh with no reasons.<br><br>**Test evidence:** `tests/gen/test_regen.py` — `test_harness_staleness_detected_by_fingerprint`, `test_harness_without_fingerprint_is_stale`. |
| **TOOL-CBT-070** | The tool shall detect that a test case is stale because the interface it exercises has changed. | `src/ectt/gen/regen.py` (`TestInterfaceBinding`, `check_test_case_staleness`) | **Guarantee:** a test case records the interface fingerprint it was authored against (its `TestInterfaceBinding`); the same deterministic comparison detects staleness when the exercised interface changes, and freshness otherwise. The binding rides the same fingerprint as the harness, so one change marks both the harness and every case authored against the old interface stale.<br><br>**Test evidence:** `tests/gen/test_regen.py` — `test_test_case_staleness_detected_by_fingerprint`. |

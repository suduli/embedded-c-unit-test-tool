# WP-ANA-06 — Verification analysis: static function testability and macro resolution

Lane: VERIFY (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-ANA-06. The
three owned SRS-001 requirements are the standing bar. ADR-sensitive element (static-exposure
mechanism choice, ADR-001 §2/ADR-003 territory): no option is chosen here; the decision-free
verification of what exists is recorded.

## Requirement → implementation → test evidence

| Requirement (SRS-001) | Implementation state | Test evidence (re-run green 2026-11-18) | Status |
|---|---|---|---|
| **TOOL-PAR-080** — identify `static` functions; provide a mechanism to make them testable without modifying user source | Identification: `src/ectt/ana/interface.py` records `storage_class == "static"`; gate integration: `src/ectt/ana/eligibility.py` (expose_static capability flag, `static_not_exposed` reason). **Exposure mechanism (testability without source modification): not implemented** | `tests/ana/test_interface.py` (storage-class assertions at lines 56/67), `tests/ana/test_eligibility.py::test_static_function_not_exposed_is_ineligible`, `::test_static_function_eligible_with_exposure_flag` | **PARTIAL** |
| **TOOL-PAR-090** — resolve function-like and object-like macros used in interfaces; record where a macro obscures the true interface | `src/ectt/ana/macros.py` (`MacroResolution`, `resolve_interface_macros`, `DETAILED_PROCESSING_OPTIONS`). Resolution is **derived data, not S1**: one record per macro use inside an extracted definition's signature — `kind` (`object_like` resolved to its literal expansion / `function_like` not resolvable to a value / `unresolved` fail-closed), `obscures_interface` (True for function-like and unresolved uses), definition location, use site (function + line). Function-likeness follows token adjacency to the macro name (token extents), so `#define FLAG (1 << 3)` stays object-like. Same extraction boundary as `extract_interfaces` (definitions in the main file); requires the parse to enable the detailed preprocessing record, else empty (never guessed) | `tests/ana/test_macros.py` — 11 tests: `test_object_like_macro_in_signature_is_resolved`, `test_function_like_macro_in_signature_obscures`, `test_object_like_expansion_starting_with_paren_is_not_function_like`, `test_body_macro_use_is_not_an_interface_use`, `test_two_signature_macros_on_one_line_sort_by_name`, `test_unit_without_macro_use_resolves_empty`, `test_resolution_is_deterministic`, `test_records_are_sorted_by_function_line_name`, `test_to_dict_is_json_safe`, `test_failed_translation_unit_is_refused`, `test_resolution_requires_detailed_processing_record` | **DONE** (derived-data scope) |
| **TOOL-PAR-170** — eligibility/observability gate with per-function observable channels and machine-readable gate reasons; discovery ≠ eligibility; requested-but-inaccessible reported explicitly | `src/ectt/ana/eligibility.py` (capability flags, per-function records) | `tests/ana/test_eligibility.py` — 10 tests incl. `::test_eligible_function_with_full_channels`, `::test_no_observable_channel_is_ineligible`, `::test_globals_alone_are_an_observable_channel` | **DONE** |

## Test run

```
2026-11-18 (chat 2):  tests/ana → 128 passed, 0 skipped; full suite → 490 passed, 4 skipped
2026-11-19 (lane B):  tests/ana → 148 passed, 0 skipped; full gate block green
```

## Gaps / not covered

- TOOL-PAR-080's exposure mechanism (the part that must not modify user source) — belongs with
  harness/stub generation (WP-GEN-03, ADR-sensitive). Untouched by this pass per instruction.
- TOOL-PAR-090 body-scope boundary: a macro used only inside a function body is not an
  interface use and is not recorded; chained macros are not transitively expanded (the
  expansion recorded is the definition's own body). Both boundaries are documented in
  `src/ectt/ana/macros.py`; widening them needs a consumer (WP-GEN-03) to justify.
- TOOL-PAR-090 persistence shape: resolution records are derived in-memory data (the
  eligibility-record precedent), not embedded in the S1 analysis model. Embedding them per
  SDD-002 would be an additive schema minor bump — an owner-reconcilable option, not decided
  here.

## Result

**PARTIAL** (unchanged for TOOL-PAR-080) — TOOL-PAR-170 DONE; TOOL-PAR-090 now implemented and
tested at derived-data scope (2026-11-19, lane B); TOOL-PAR-080 remains identification + gate
only (exposure mechanism open, ADR-sensitive, belongs with WP-GEN-03).

## Lane B re-verification (2026-11-19, worktree wt-night-b)

Closed the decision-free remainder left by chat 2: PAR-090 macro resolution implemented with
libclang fixtures (deterministic; the detailed preprocessing record is an explicit parse
option the resolver documents). PAR-080 was not touched (ADR-sensitive, WP-GEN-03). Full gate
block green: pytest 1044 passed / 5 skipped, ruff, mypy, plan_check, trace_check all clean.

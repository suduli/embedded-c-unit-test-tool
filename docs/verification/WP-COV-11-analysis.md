# Verification Analysis Note — WP-COV-11 (Control Coupling and Data Coupling Analysis)

Lane: B (night run of the 2026-11-23 queue) · 2026-11-27 · Worktree `wt-night-23b`, branch `glm-night/20261123-b`, baseline local `main` (b9b1262).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for
WP-COV-11. Derived from the SRS-001 text (TOOL-COV-170 — "The tool shall support
control coupling and data coupling analysis between integrated units", method *T*)
and the queue item, which adds the three cases to test and the instruction to report
data only:

- **AC-1 (control coupling):** every call recorded in the analysis model's call graph
  (`FunctionModel.calls`) from one analysed function forms a caller-to-callee pair
  with its call sites. A pair is `exercised` when at least one of its call sites
  returned, and `not_exercised` when every site is in the coverage data and none
  returned.
- **AC-2 (data coupling):** for every global variable the model's inventory records,
  the functions recorded writing it and the functions recorded reading it form
  writer-to-reader pairs. A pair is `exercised` when both functions executed and
  `not_exercised` when both are in the coverage data and at least one did not execute.
- **AC-3 (statuses):** every pair has exactly one of `exercised`, `not_exercised`,
  `not_determinable`, and a pair that is not exercised carries its reason. A global
  with no recorded access is `not_determinable` with reason `no_recorded_access`.
- **AC-4 (nothing is guessed):** a call through a pointer is never given a target; a
  call site is matched to a gcov call record only when its line holds exactly one of
  each; a file-scope static is identified by unit and name, so two same-named statics
  are never coupled; a callee defined in two units is not assigned to either.
- **AC-5 (data only):** the report carries pairs, statuses and reasons and nothing
  that reads as a score or a verdict about a coupling objective.
- **AC-6 (refusals):** a call site outside the analysis vocabularies (`unknown_call_via`,
  `unknown_call_classification`), an indirect call that names a callee
  (`indirect_call_names_callee`) and a global access outside `r`/`w`/`rw`
  (`unknown_global_access`) are refused with the named reason.
- **AC-7 (determinism):** the same content in another input order and with another
  path spelling gives byte-identical output; no wall clock is read.
- **AC-8 (unanalysed units):** a unit that did not parse is listed as not analysed with
  its recorded reason rather than silently dropped.

## Implementation

- `src/ectt/cov/coupling.py` — `analyze_coupling(model, document)` returns a
  `CouplingReport` of `CallPair`s (with their `CallSite`s) and `CouplingVariable`s
  (writers, readers, `DataPair`s); `COUPLING_STATUSES`, `DATA_PAIR_BASIS`,
  canonical `to_dict` / `to_json_bytes`.
- `tests/cov/test_coupling.py` — the AC checks, one of them driven by the real
  analyzer's output rather than hand-built records.

The analysis model is read, never changed; the import from it is the narrow
`ectt.ana.model`. Three things a reader of the report must know are decided here:

- **What "exercised" means for a data pair.** The model records a global access by
  name, without a line, so the tool can say that the two *functions* executed, not
  that the specific access statements executed. The report says so itself in
  `data_pairs_basis`.
- **Why a call site is matched only one-to-one.** A `CallModel` carries a line and no
  column; a gcov `calls[]` record carries block ids and no callee. With several calls
  on one line there is no basis for pairing them, so such sites are
  `not_determinable` (`ambiguous_call_site`).
- **Why a static is keyed by unit.** `FunctionModel.globals` records only a name. Two
  units can each hold a file-scope `count`; keying by name alone would report a
  coupling between functions that share nothing. An access in a unit to a name that
  unit declares `static` belongs to that unit's own variable; every other access has
  external linkage and is keyed by name.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/cov/`) |
|---|---|---|
| TOOL-COV-170 (control coupling) | `_call_pairs`, `_Coverage.call_status`, `_combine` | `test_coupling.py::test_a_simple_call_chain_is_reported_as_exercised`, `::test_an_unexercised_call_is_reported_as_not_exercised`, `::test_a_call_that_never_returns_is_named_apart_from_one_never_reached`, `::test_a_call_to_a_function_defined_in_another_unit_names_that_unit` |
| TOOL-COV-170 (data coupling) | `_variables`, `_data_pair`, `_Coverage.execution_of` | `::test_a_written_and_read_global_forms_an_exercised_pair`, `::test_a_data_pair_that_did_not_execute_is_named` (4 cases), `::test_an_external_global_couples_functions_across_units`, `::test_a_global_accessed_but_defined_in_no_analysed_unit_is_stated` |
| global with no recorded access is not determinable | inventory variable with no writer and no reader | `::test_a_global_with_no_recorded_access_is_not_determinable` |
| not determinable with the reason (control) | reasons `callee_not_identified`, `file_not_in_coverage`, `call_line_not_in_coverage`, `no_call_data`, `ambiguous_call_site` | `::test_a_call_through_a_pointer_has_no_guessed_target`, `::test_a_call_site_without_call_data_is_not_determinable` (3 cases), `::test_several_calls_on_one_line_are_not_matched_by_position`, `::test_one_model_site_against_two_gcov_call_records_is_not_matched` |
| nothing is guessed about identity | unit-and-name key for a file-scope static; unique defining unit for a callee | `::test_same_named_statics_in_two_units_are_not_coupled`, `::test_a_function_name_defined_in_two_units_is_not_picked` |
| data only | report shape: pairs, statuses, reasons, `data_pairs_basis` | `::test_the_report_carries_data_only` |
| refusals | `_checked_calls`, `_check_call`, the access check in `_variables` | `::test_an_unknown_call_via_is_refused`, `::test_an_unknown_call_classification_is_refused`, `::test_an_indirect_call_that_names_a_callee_is_refused`, `::test_an_unknown_global_access_is_refused`, `::test_the_analysis_vocabularies_are_the_ones_the_module_checks_against` |
| unanalysed units and determinism | `not_analysed_units`; sorted output over normalised paths | `::test_a_failed_unit_is_listed_as_not_analysed`, `::test_output_is_byte_stable_under_input_order_and_path_spelling` |
| end to end | — | `::test_the_real_analyzer_output_drives_the_analysis` (libclang extraction, not hand-built records) |

## Not covered by this increment

- **No coupling objective is assessed.** The report does not score coupling coverage
  and does not state whether any standard's objective is met; which pairs matter for
  a given standard is an owner decision.
- **"Exercised" on a data pair is function-level.** Showing that the specific access
  statements executed needs access locations, which the analysis model does not
  record.
- **Call matching is by line, one-to-one.** How GCC attributes a call inside a macro
  or several calls on one line is unchecked (no compiler on this machine); any such
  site is `not_determinable`, never guessed. Real GCC output has not been checked.
- **Only what the analysis model records.** Globals declared only in headers are not
  in the inventory, and a variable defined outside every analysed unit appears with
  no unit (`defined_in_model` false). The analyzer classifies a call relative to one
  translation unit, so a call into another unit of the same model is `external`;
  the report resolves the defining unit by function name and leaves it unset when the
  name is defined in more than one unit.
- **Whole-document statuses.** The analysis takes one coverage document; it does not
  attribute coupling to individual tests.

## Verification status

Gates re-run after the increment, each on its own: pytest green (29 new cases), ruff,
mypy, plan_check and trace_check exit 0.

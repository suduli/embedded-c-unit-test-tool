# Mutation-style test report — qua, sec, exh (lane A item A8, 2026-11-23)

Tests only; no `src/` edits landed. The runner was **copied from
`docs/glm-night/overnight-20261122/mutation_runner.py`** (the original untouched)
and its mutant set redirected at the modules this run landed: `qua/validation.py`,
`qua/known_errors.py`, `sec/sbom.py`, `sec/pins.py`, `exh/restricted.py`,
`exh/debugger.py` (A1–A6), with `tests/qua`, `tests/sec`, `tests/exh` and
`tests/core` as the judge suites. Mutants are applied to a **temp copy** of `src/`
(never to the tree); the shadow tree wins via pytest's `pythonpath` override plus
`PYTHONPATH` (same mechanism as the 2026-11-21/22 runs).

**Kill rate: 16/17 (94%); 16/16 (100%) over the non-equivalent mutants.** The one
survivor, `SEC-PINS-3` (drop the final sort in `check_pins`), is
**behaviorally equivalent**: the checker produces exactly one difference per
package, and it already iterates the names in sorted order, so the report is
name-sorted before the final sort runs — no test can distinguish it. Removing the
redundant sort is a `src/` change, which this tests-only item must not make; it is
recorded here (and would ride with the next src-touching change to that module).

## Per-mutant results

| id | module | operator | killed by |
|---|---|---|---|
| QUA-VALID-1 | qua/validation.py | flip guard (missing-tool gate) | test_validation: test_a_missing_tool_is_not_run_never_pass |
| QUA-VALID-2 | qua/validation.py | flip state (pass -> fail) | test_validation: test_every_check_passes_on_a_clean_machine |
| QUA-VALID-3 | qua/validation.py | drop clause (id-order processing) | test_validation: test_the_record_is_byte_stable_and_order_independent |
| QUA-ERRORS-1 | qua/known_errors.py | flip comparison (fix gate <=) | test_known_errors: test_a_fixed_error_stops_applying_after_its_fix |
| QUA-ERRORS-2 | qua/known_errors.py | flip guard (duplicate id) | test_known_errors: test_duplicate_error_ids_are_refused |
| QUA-ERRORS-3 | qua/known_errors.py | flip reason (workaround refusal) | test_known_errors: test_an_open_entry_without_a_workaround_is_refused |
| SEC-SBOM-1 | sec/sbom.py | flip guard (unknown-licence detection) | test_sbom: test_a_missing_licence_is_reported_unknown |
| SEC-SBOM-2 | sec/sbom.py | drop sorting (components) | test_sbom: test_the_output_is_byte_stable_and_sorted |
| SEC-SBOM-3 | sec/sbom.py | swap marker (signing) | test_sbom: test_signing_is_reported_not_configured |
| SEC-PINS-1 | sec/pins.py | flip comparison (wrong hash) | test_pins: test_a_clean_match_reports_no_differences |
| SEC-PINS-2 | sec/pins.py | flip guard (unpinned lock entry) | test_pins: test_a_clean_match_reports_no_differences |
| SEC-PINS-3 | sec/pins.py | drop sorting (equivalent mutant) | — (behaviorally equivalent, see above) |
| EXH-RESTR-1 | exh/restricted.py | flip guard (path escape) | test_restricted: test_directory_confinement_refuses_a_path_escape |
| EXH-RESTR-2 | exh/restricted.py | flip flag (inherit_handles) | test_restricted: test_the_limits_are_recorded_in_the_result |
| EXH-RESTR-3 | exh/restricted.py | drop statement (truncation flag) | test_restricted: test_the_output_limit_truncates_and_flags |
| EXH-DEBUG-1 | exh/debugger.py | flip guard (symbols gate) | test_debugger: test_a_build_without_symbols_is_refused |
| EXH-DEBUG-2 | exh/debugger.py | drop element (entry breakpoint) | test_debugger: test_the_gdb_argv_is_golden_stable |

## Notes and limits

- The mutant set is hand-written and bounded (17), not exhaustive: it targets the
  integrity-bearing decisions of the new modules (gates that must refuse, states
  that must not lie, orders that must be stable, markers that must disclose), not
  every branch of the three packages.
- The run is deterministic; a repeat run produces identical verdicts.

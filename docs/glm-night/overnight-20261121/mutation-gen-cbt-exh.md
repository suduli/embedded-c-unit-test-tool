# Mutation-style test report — gen, cbt, exh (lane A item A6, 2026-11-21)

Tests only; no `src/` edits landed. Hand-written mutants (flip a comparison, drop a
branch or clause, swap an ordering key, weaken a pattern, change a boundary constant)
were applied to a **temp copy** of `src/` (never to the tree), and the three package
suites (`tests/gen`, `tests/cbt`, `tests/exh`) ran against the copy. The shadow tree
takes precedence via pytest's `pythonpath` ini override plus `PYTHONPATH` (the
editable install is `.pth`-based; pyproject's `pythonpath = ["src", "tools"]` had to
be overridden, which is what the first, discarded run tripped over).

A mutant is **killed** when any test fails or errors. Runner:
`docs/glm-night/overnight-20261121/mutation_runner.py` (re-runnable; baseline must be
green before mutating). Scope: the core behavioural modules of the three packages —
`gen/protocol.py`, `gen/testbody.py`, `gen/stubctl.py`, `gen/harness.py`,
`cbt/reexecute.py`, `exh/runner.py`, `exh/results.py` — 20 mutants.

**Kill rate: 20/20 (100%)** in the final run. Two mutants survived the first run
(90%) and were killed by two new tests added to `tests/cbt/test_reexecute.py`
(marked as mutation-A6 survivor tests there):

- `CBT-REEXEC-2` (drop the resolved-path confinement branch): killed by
  `test_a_resolved_path_escape_is_refused` — the string-level pre-checks alone do
  not catch a path that escapes only after symlinks/junctions are resolved; the
  test reproduces the escape with a Windows junction (skipped where junctions are
  unavailable).
- `CBT-REEXEC-3` (swap the record's binding-order key from test id to digest):
  killed by `test_recorded_bindings_are_ordered_by_test_id` — bindings whose
  digest order is the reverse of their id order must still be recorded (and
  dumped) in test-id order (D-02: stable ids order the record).

## Per-mutant results (final run)

| id | module | operator | killed by |
|---|---|---|---|
| GEN-PROTO-1 | gen/protocol.py | flip comparison (end_test outcome ternary) | test_protocol: test_only_ending_a_test_with_no_failures_reports_a_pass |
| GEN-PROTO-2 | gen/protocol.py | drop statement (end_test state reset) | test_protocol: test_ending_a_test_twice_reports_it_once |
| GEN-PROTO-3 | gen/protocol.py | boundary constant (line 0 -> 0ul) | test_protocol: test_a_failure_line_has_six_tokens_in_the_order_the_reader_expects |
| GEN-TESTBODY-1 | gen/testbody.py | invert guard (expectation check) | test_testbody: test_a_case_with_stubs_renders_the_expected_golden_shape |
| GEN-TESTBODY-2 | gen/testbody.py | drop branch (case-function collision guard) | test_testbody: test_two_cases_that_map_to_one_function_name_are_refused |
| GEN-TESTBODY-3 | gen/testbody.py | weaken pattern (count regex loses the `u`) | test_testbody: test_the_composed_per_case_c_parses_with_zero_diagnostics |
| GEN-STUBCTL-1 | gen/stubctl.py | flip comparison (fixed-mode arity) | test_stubctl: test_fixed_return_value_setup |
| GEN-STUBCTL-2 | gen/stubctl.py | drop branch (expect_calls validation) | test_stubctl: test_expectations_refuse_a_bad_count_or_a_foreign_spec |
| GEN-HARNESS-1 | gen/harness.py | flip comparison (merged global access) | test_harness: test_globals_recorded_with_merged_access |
| CBT-REEXEC-1 | cbt/reexecute.py | drop branch (binary integrity) | test_reexecute: test_a_rebuilt_executable_is_refused |
| CBT-REEXEC-2 | cbt/reexecute.py | drop branch (resolved confinement) | test_reexecute: test_a_resolved_path_escape_is_refused (new) |
| CBT-REEXEC-3 | cbt/reexecute.py | swap ordering key (record bindings) | test_reexecute: test_recorded_bindings_are_ordered_by_test_id (new) |
| CBT-REEXEC-4 | cbt/reexecute.py | drop clause (run-label whitespace rule) | test_reexecute: test_run_labels_must_be_single_tokens[has space] |
| EXH-RUNNER-1 | exh/runner.py | drop branch (NR-19 stale gate) | test_reexecute: test_a_test_edited_since_the_build_is_not_executed_and_makes_the_run_partial |
| EXH-RUNNER-2 | exh/runner.py | flip comparison (parallel aggregation) | test_parallel: test_units_run_to_completion_in_input_order |
| EXH-RUNNER-3 | exh/runner.py | swap attribution constant (timeout -> error) | test_reexecute_runners: test_reexecute_isolated_reports_a_hang_as_a_timeout |
| EXH-RUNNER-4 | exh/runner.py | flip comparison (exit-code contract) | test_supervisor: test_exit_code_contract |
| EXH-RUNNER-5 | exh/runner.py | drop branch (duplicate allocation) | test_reexecute: test_recording_validates_bindings_with_the_runners_rules |
| EXH-RESULTS-1 | exh/results.py | drop branch (NR-18 pass-with-failures guard) | test_properties_seeded: test_finalize_result_accepts_exactly_what_the_nr18_rules_allow[0] |
| EXH-RESULTS-2 | exh/results.py | drop member (timeout leaves the failure set) | test_reexecute_runners: test_reexecute_isolated_reports_a_hang_as_a_timeout |

## Notes and limits

- The GEN-PROTO mutants are killed by the protocol tests because those tests
  assert the emitted stream *shape* against expectations that do not come from
  the mutated text itself (the reader-order test pins the FAILURE line before
  the C is consulted); a mutant that stayed self-consistent with the shape
  derivation would need run-time verification, which no C compiler on this
  machine allows — that limit is recorded in the lane's second-pass file.
- The mutant set is hand-written and bounded (20), not exhaustive: it targets
  the integrity-bearing decisions (result-stream protocol, staleness, binary
  integrity, confinement, ordering, aggregation, exit contract), not every
  branch in the three packages.
- One repeat run produced byte-identical verdicts (the runner is deterministic;
  the only ordering-sensitive step is pytest's own test order, which does not
  affect kill decisions here).

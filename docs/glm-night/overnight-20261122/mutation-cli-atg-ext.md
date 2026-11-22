# Mutation-style test report — cli, atg, ext (lane A item A6, 2026-11-22)

Tests only; no `src/` edits landed. Hand-written mutants (flip a comparison, drop a
branch or statement, swap the gate/run order) were applied to a **temp copy** of
`src/` (never to the tree), and the cli/atg/ext suites (`tests/cli`, `tests/atg`,
`tests/ext`) ran against the copy. The shadow tree wins via pytest's `pythonpath`
ini override plus `PYTHONPATH` (same mechanism as the 2026-11-21 run). Runner:
`docs/glm-night/overnight-20261122/mutation_runner.py` (re-runnable, baseline-gated).

**Kill rate: 16/16 (100%)** on the first run — no survivor tests were needed this
time. The mutant set targets the wiring this lane landed over 2026-11-21/22: the
composition delegates, the CLI exit contracts and JSON-safety net, the
parity-gate-before-run order, the profile labelling and ABI-unknown disclosure, the
port's coverage bookkeeping, and the run's case limit and measured flag.

## Per-mutant results

| id | module | operator | killed by |
|---|---|---|---|
| CLI-COMPOSE-1 | cli/compose.py | flip state mapping (completed -> harness_error) | test_compose: test_the_real_binding_builds_records_and_reruns |
| CLI-COMPOSE-2 | cli/compose.py | drop branch (HarnessBuildError -> plan refusal becomes a port failure) | test_compose: test_a_refused_link_plan_stops_the_run |
| CLI-COMPOSE-3 | cli/compose.py | drop statement (record keeping) | test_compose: test_the_real_binding_builds_records_and_reruns |
| CLI-CMDS-1 | cli/commands.py | flip exit contract (subset run always exits 0) | test_commands: test_subset_run_with_a_failed_test_exits_test_failure |
| CLI-CMDS-2 | cli/commands.py | flip exit contract (host run always exits 0) | test_hostprep: test_a_failed_suite_exits_test_failure_with_labels |
| CLI-CMDS-3 | cli/commands.py | drop branch (JSON/ValueError safety net) | test_commands: test_impact_malformed_json_is_a_tool_error |
| CLI-HOSTPREP-1 | cli/hostprep.py | drop statement (profile labelling) | test_hostprep: test_every_result_of_a_gated_run_carries_its_profile_label |
| CLI-HOSTPREP-2 | cli/hostprep.py | swap order (parity gate after the run) | test_hostprep: test_every_result_of_a_gated_run_carries_its_profile_label |
| ATG-BINDING-1 | atg/binding.py | flip guard (sourceless coverage reports a delta) | test_compose: test_the_real_binding_builds_records_and_reruns |
| ATG-BINDING-2 | atg/binding.py | flip comparison (newly-covered set) | test_binding: test_the_run_populates_newly_covered_through_the_bound_port |
| ATG-RUN-1 | atg/run.py | flip comparison (case limit off-by-one) | test_binding: test_the_run_respects_the_case_limit_and_reports_what_it_has |
| ATG-RUN-2 | atg/run.py | flip assignment (coverage always unmeasured) | test_compose: test_the_real_binding_builds_records_and_reruns |
| EXT-PROFILE-1 | ext/profile.py | flip comparison (integrity check) | test_hostprep: test_every_result_of_a_gated_run_carries_its_profile_label |
| EXT-PROFILE-2 | ext/profile.py | flip comparison (unknown ABI loses its marker) | test_profile: test_unknown_abi_stays_unknown |
| EXT-PARITY-1 | ext/parity.py | flip guard (gate refuses matched pairs) | test_hostprep: test_every_result_of_a_gated_run_carries_its_profile_label |
| EXT-PARITY-2 | ext/parity.py | flip comparison (plan-kind check) | test_parity: test_check_parity_needs_a_host_plan_and_a_target_plan |

## Notes and limits

- The gate-order mutant (CLI-HOSTPREP-2) is killed by the label test because
  dropping the preparation leaves `preparation = None`, which the view assembly
  dereferences — and the parity-gate-before-run discipline is separately pinned by
  the marker-file test (`test_a_refused_preparation_never_starts_a_process`), which
  the gate-reordering mutants cannot satisfy.
- The mutant set is hand-written and bounded (16), not exhaustive: it targets the
  integrity-bearing wiring (exit contracts, gate order, labelling, unknown-ABI
  disclosure, coverage bookkeeping), not every branch of the three packages.
- The run is deterministic; a repeat run produces identical verdicts.

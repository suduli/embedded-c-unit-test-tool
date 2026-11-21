# Verification Analysis Note — WP-CBT-02 (Change Impact Analysis and Subset Execution)

RECON: PLAN-001 §5.4 records **no package-specific acceptance criterion** for this
package (flagged for reconciliation in the tracker; register edits are owner
territory). The acceptance criteria below are therefore derived from the SRS-001
requirements owned by this work package, written to be falsifiable and reviewable
before any code landed. Executor: GLM (lane A, 2026-11-21 queue), with the WP-COV-02
cross-lane dependency satisfied by merging `glm-night/20261121-b` (lane B ledger row
WP-COV-02 = DONE; post-merge gate green: 3442 passed, 6 skipped, 2 xfailed).

## Acceptance criteria

- **AC-1 (TOOL-CBT-020, affected set):** a source change names the changed source
  constructs (file paths or construct ids); a test case is affected **exactly when**
  the constructs its recorded per-test coverage covers intersect the changed set;
  unaffected cases are never listed; the affected and unaffected sets are sorted and
  deterministic.
- **AC-2 (TOOL-CBT-020, degenerate inputs):** an empty change affects nothing; a
  changed construct that no test covers affects nothing; both are ordinary results,
  not errors (surfacing untested changes is a reporting concern outside this package).
- **AC-3 (TOOL-CBT-030, subset execution):** a subset execution runs exactly the
  selected cases of a recorded compiled suite — no regeneration (the recorded binary
  is re-executed as built), the same integrity gate as a full re-execution (record
  digest, binary digest: a changed or missing binary is refused), and each selected
  test in its own harness process (isolation and timeout semantics of the runner).
  An empty selection, an unknown test id or a duplicated id is refused with a named
  reason before anything runs.
- **AC-4 (TOOL-CBT-040, partial reporting):** a subset execution's result **states
  the run was partial** and identifies every test of the suite that was not selected
  — not merely the selected ones that failed to report — and the suite-level view of
  the result set is marked partial with those tests listed as not executed, so no
  consumer can read a subset run as a full pass.
- **AC-5 (determinism):** the affected set and the subset attempt's run id are
  deterministic functions of their inputs; a subset attempt and the full run of the
  same record under the same label get distinct run ids.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-CBT-020** | The tool shall determine, from a source change, the set of test cases whose covered code was affected. | `src/ectt/cbt/impact.py` (`SourceChange`, `ImpactResult`, `affected_cases`) | **AC-1/AC-2:** the change is a set of construct identities; a case's covered set comes from the caller (composition wires `ectt.cov.merge`'s per-test attribution in — this package stays layer-clean and takes plain data). Intersection is the falsifiable core: a case whose coverage misses the change is unaffected, whatever its history; the output is sorted. **Test evidence:** `tests/cbt/test_impact.py` — `test_affected_exactly_when_the_covered_set_intersects_the_change`, `test_unaffected_cases_are_never_listed`, `test_an_empty_change_affects_nothing`, `test_a_construct_no_test_covered_affects_nothing`, `test_the_output_is_sorted_and_deterministic`, `test_overlapping_coverage_affects_every_covering_case`. |
| **TOOL-CBT-030** | The tool shall support executing only the affected subset identified under TOOL-CBT-020. | `src/ectt/cbt/reexecute.py` (`reexecute_subset`, `SubsetReExecution`), sharing the integrity gate with `reexecute_suite`/`reexecute_isolated` | **AC-3/AC-5:** the subset attempt is allocated (NR-17) from exactly the selected bindings of the record, marked built, and run per test in isolation; the binary-integrity and record-digest checks are the full re-execution's (one shared gate — runner choice cannot weaken integrity); the attempt id binds record id, label and the sorted selection, so subset and full runs never collide. **Test evidence:** `tests/cbt/test_reexecute_subset.py` — `test_a_subset_runs_exactly_the_selected_tests`, `test_the_subset_attempt_has_its_own_run_id`, `test_a_changed_binary_is_refused_for_a_subset_too`, `test_an_empty_selection_is_refused`, `test_an_unknown_test_id_is_refused`, `test_a_duplicated_selection_is_refused`, `test_the_selection_is_deterministic`. |
| **TOOL-CBT-040** | When a subset is executed, all reports shall state clearly that the run was partial and identify which tests were not executed. | `src/ectt/cbt/reexecute.py` (`SubsetReExecution.partial`, `.not_selected`, `.suite_view`) | **AC-4:** `not_selected` is the full suite minus the selection — computed from the record, independent of what the harness reported; `suite_view` re-issues the result set with `partial=True` and `not_executed` naming the unselected tests, so the partiality is in the data every report consumes, not a renderer's guess. **Test evidence:** `tests/cbt/test_reexecute_subset.py` — `test_the_subset_run_states_its_partiality_and_names_the_unselected`, `test_the_suite_view_marks_the_run_partial_with_the_unselected_listed`, `test_a_full_selection_is_not_partial`. |

## Design notes

- **The impact core is plain data.** `affected_cases` takes `coverage_by_test` as a
  mapping of case id to covered construct ids; binding it to the coverage engine's
  per-test attribution (`ectt.cov.merge.coverage_for_test`, landed by the WP-COV-02
  cross-lane dependency) is composition work, kept out of this package so the CBT
  layer does not depend on the COV layer.
- **One integrity gate.** `reexecute_subset` shares `_checked_attempt` with the
  existing re-execution forms; the subset only narrows the allocation, never the
  checks.
- **Partiality is data, not prose.** TOOL-CBT-040's "all reports" is satisfied by
  putting the partial flag and the unselected list into the result view itself.

## Not covered (recorded, not guessed)

- **Construct-level (line/branch) mapping:** the change names constructs at the
  granularity the caller's coverage data uses; mapping a diff to constructs (AST or
  coverage-line granularity) belongs to the ingestion/coverage composition.
- **Cross-suite impact:** `affected_cases` answers for the coverage data supplied;
  joining several suites' records into one impact answer is composition.
- **CLI/report wiring** of the affected set and the subset run (the renderer change
  is the lane's second-pass item).

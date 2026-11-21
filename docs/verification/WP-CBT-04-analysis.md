# Verification Analysis Note — WP-CBT-04 (Test Suite Minimization)

RECON: PLAN-001 §5.4 records **no package-specific acceptance criterion** for this
package (flagged for reconciliation; register edits are owner territory). The
criteria below are derived from the SRS-001 requirement owned by this work package
and were written before the code. Executor: GLM (lane A, 2026-11-21 queue). The
WP-COV-02 cross-lane dependency is satisfied (merged earlier this run); WP-CBT-02
is DONE in this lane's ledger.

## Acceptance criteria

- **AC-1 (TOOL-CBT-080, redundancy):** a test case is identified as redundant
  exactly when its recorded coverage adds nothing to the coverage of the minimized
  set — i.e. every construct it covers is covered by the kept tests — so dropping
  all redundant cases loses no coverage at all (the union of the kept sets equals
  the union of all sets).
- **AC-2 (determinism):** the kept and redundant sets are deterministic functions
  of the coverage data: the greedy selection prefers the test covering the most
  not-yet-covered constructs and breaks ties on the lowest test id, so a shuffled
  input mapping yields the same answer; identical coverage sets keep exactly one
  test (the lowest id) and mark the rest redundant.
- **AC-3 (degenerate inputs):** an empty suite minimizes to nothing kept and
  nothing redundant; a suite whose tests all cover nothing is entirely redundant
  (the union is empty and is preserved); blank test ids or non-construct entries
  are refused with a named error before any selection happens.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-CBT-080** | The tool shall support test suite minimization, identifying redundant test cases contributing no unique coverage. | `src/ectt/cbt/minimize.py` (`Minimization`, `minimize_suite`) | **AC-1/AC-2/AC-3:** the selection is a deterministic greedy cover of the union of all coverage sets; by construction every dropped case's coverage is contained in the kept union — the falsifiable invariant is *union preservation* plus *redundancy* (each redundant set adds nothing). Minimality of the kept set is greedy, not proven-minimal (exact minimum is NP-hard; the requirement asks for identifying redundancy, not for the smallest possible suite). Per-test coverage arrives as plain data (as in WP-CBT-02/03); composition wires the coverage engine in. **Test evidence:** `tests/cbt/test_minimize.py` — `test_a_subset_test_is_redundant`, `test_a_duplicate_test_is_redundant_and_one_is_kept`, `test_the_union_is_preserved`, `test_a_unique_contributor_is_never_dropped`, `test_identical_coverage_keeps_the_lowest_id`, `test_the_result_is_deterministic_under_input_shuffling`, `test_an_empty_suite_minimizes_to_nothing`, `test_tests_covering_nothing_are_all_redundant`, `test_blank_ids_and_non_constructs_are_refused`, `test_seeded_union_preservation` (fixed seeds, no wall clock). |

## Design notes

- **Greedy, deterministic, safe.** The kept set always covers the full union, so
  the redundant set is provably loss-free; greedy order (gain desc, id asc) makes
  the answer reproducible without a wall clock or hash order.
- **Plain data in.** `coverage_by_test` maps test ids to covered construct ids;
  binding the coverage engine's per-test attribution is composition (as in
  WP-CBT-02/03).

## Not covered (recorded, not guessed)

- **Execution-time weighted minimization** (dropping the *slowest* redundant test
  first) needs run-duration data the result model deliberately does not carry.
- **Interaction-aware minimization** (pairwise testing over parameters) is the
  derivation package's territory, not coverage-based minimization.
- **CLI/report wiring** of the minimization result (lane second-pass item).

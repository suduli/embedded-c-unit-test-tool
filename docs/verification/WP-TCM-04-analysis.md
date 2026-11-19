# WP-TCM-04 — Suites, selective execution and test independence

Status: in progress (overnight lane A, 2026-11-19)
Requirements: TOOL-TCD-080, TOOL-TCD-090
Design elements: DSN-TCM-050 (suites and selection), DSN-TCM-060 (test independence)
Dependencies: WP-TCM-02 (DONE in this ledger, commit ffacfce)
Decisions applied as written (not re-decided): none new; D-02 option (a) digest binding carries over — suite membership is case content and joins the content digest.

## Acceptance criteria

Derived from the SRS texts (SRS-001 lines 310–312) and the DSN-TCM-050/DSN-TCM-060 statements:

1. **AC-1 (TCD-080 — suite membership).** A data-driven test case can declare membership in named suites; membership survives a load→save round trip byte-identically and joins the case's content digest (D-02: editing suite membership changes the digest, never the id).
2. **AC-2 (TCD-080 — one selection expression).** One selection expression selects by suite, unit, function, or test id. Dimensions combine with OR ("by suite, unit, function, or test name" — SRS); within a dimension, multiple values are OR. An empty selection selects everything (no filter = run everything). The partition (selected, excluded) is deterministic: input order preserved.
3. **AC-3 (TCD-090 — randomized ordering).** The planner returns the declared order without a seed and a deterministic seeded shuffle with one; the same seed yields the same order across processes and the recorded `order_seed` rides the run's execution metadata (SDD-002 §6, DSN-TCM-060).
4. **AC-4 (TCD-090 — independence check, verification A).** Given two result sets for the same allocations under different orders, the check reports order-independent when every test has the same outcome in both; any outcome divergence or execution-set divergence names the divergent tests.
5. **AC-5 (determinism, no wall-clock, no network).** Ordering uses an explicitly seeded generator (no `hash()` or `PYTHONHASHSEED` involvement); the modules are pure.

## Assumptions (conservative readings)

- Suite membership is carried on the case (DSN-TCM-050: "test cases carry suite membership") as an optional `suites` list — a model extension to WP-TCM-02's record, serialized as a plain list and omitted when empty (default-omission pattern).
- An empty selection selects all cases rather than none: the CLI intuition "no filter given" must not silently run nothing; documented in the API.
- The independence check treats a test present in one run but not the other as divergent: a full-suite re-run under a different order must execute the same set (subset runs are out of its contract).

## Requirement → implementation → tests

| Requirement | Implementation | Tests |
|---|---|---|
| TOOL-TCD-080 (suites) | `DataDrivenTestCase.suites` + serialization + digest payload (src/ectt/tcm/datacases.py) | tests/tcm/test_datacases.py: `test_suites_survive_round_trip_and_join_digest` |
| TOOL-TCD-080 (selection) | `ectt.tcm.selection.Selection` / `partition_cases` | tests/tcm/test_selection.py: `test_selection_by_each_dimension`, `test_selection_or_across_dimensions`, `test_empty_selection_selects_everything`, `test_partition_is_deterministic` |
| TOOL-TCD-090 (ordering) | `ectt.tcm.independence.execution_order` | tests/tcm/test_independence.py: `test_declared_order_without_seed`, `test_seeded_order_is_deterministic_across_calls` |
| TOOL-TCD-090 (independence, A) | `ectt.tcm.independence.check_order_independence` | tests/tcm/test_independence.py: `test_identical_outcomes_are_order_independent`, `test_outcome_divergence_names_the_test`, `test_execution_set_divergence_is_reported` |
| determinism | seeded generator; pure modules | `test_seeded_order_is_deterministic_across_calls` |

Uncovered: none for the derived criteria. The runner-side reset hook is
generated-harness code (CMP-GEN); the analysis half of TCD-090's
verification is the independence check above.

## Second-pass items

- PLAN-001 §5.4 has no package-specific acceptance criterion for WP-TCM-04; reconcile the derived criteria above (owner edit).
- The generated harness must reset harness state in the setup hook (DSN-TCM-060's mechanism side) — CMP-GEN scope.

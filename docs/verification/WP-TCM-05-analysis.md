# WP-TCM-05 — Ranged and robustness input generation

Status: in progress (overnight lane A, 2026-11-19)
Requirements: TOOL-TCD-070, TOOL-TCD-130
Design elements: DSN-TCM-040 (ranged input expansion), DSN-TCM-100 (robustness test cases)
Dependencies: WP-TCM-02 (DONE in this ledger, commit ffacfce)
Decisions applied as written (not re-decided): none new; D-02 digest binding carries over — robustness marking and expanded values are case content and join the digest.

## Acceptance criteria

Derived from the SRS texts (SRS-001 lines 308, 320) and the DSN-TCM-040/DSN-TCM-100 statements:

1. **AC-1 (TCD-070 — one executed test per value).** A ranged input expands to one case per value in the range. An integer range expands inclusively with a step >= 1; a malformed range (step < 1, lo > hi) is a named error. Multiple ranged inputs on one case expand to the cartesian product, in declared spec order (deterministic).
2. **AC-2 (DSN-TCM-040 — stable derived identifiers).** Each expanded case carries a derived identifier of the form `<base id>.r.<param>=<value>[+<param2>=<value2>]` that is stable under re-expansion: expanding the same base case with the same range always yields the same identifiers (no randomness, no wall-clock), so results remain comparable across runs.
3. **AC-3 (D-02 — expanded cases are digest-bound).** Each expanded case is a full case record: the expanded value rides `inputs.parameters`, and the record carries a fresh matching content digest, so results bind to exactly the content that executed.
4. **AC-4 (TCD-130 — robustness marking).** A case may be marked robustness; the marking round-trips through the on-disk format and joins the content digest. The tool's own range check refuses out-of-range values on normal cases with a named error and accepts them on robustness-marked cases — the tool does not refuse to express exactly the case the user needs (DSN-TCM-100).
5. **AC-5 (determinism, no wall-clock, no network).** Expansion and range checking are pure functions over their inputs.

## Assumptions (conservative readings)

- The range declaration rides outside the case record tonight: expansion takes the base case plus explicit ranged-input specs (an integer `[lo, hi]` inclusive range with step, expanded before combination). Persisting range declarations inside `.tests` files needs a model/serialization extension (second-pass).
- Expanded identifiers embed the base id and the value combination (readable, diffable) rather than a hash suffix; stability under re-expansion is what DSN-TCM-040 requires.
- "Range checking disabled" (TOOL-TCM-130) is implemented at the tool's own validation gate: a `ValidRange` check that rejects out-of-range inputs unless the case is robustness-marked. Runtime robustness execution (harness-side) is CMP-GEN scope.

## Requirement → implementation → tests

| Requirement | Implementation | Tests |
|---|---|---|
| TOOL-TCD-070 | `ectt.tcm.ranged.expand_integer_range` + `expand_case` (cartesian product) | tests/tcm/test_ranged.py: `test_integer_range_expands_inclusively`, `test_ranged_input_expands_one_case_per_value`, `test_multiple_ranges_expand_cartesian`, `test_malformed_range_is_rejected` |
| DSN-TCM-040 | derived id scheme `<base>.r.<param>=<value>` | `test_derived_identifiers_stable_under_reexpansion` |
| D-02 binding | expanded cases carry fresh matching digests | `test_expanded_cases_are_digest_bound` |
| TOOL-TCD-130 | `robustness` field on the model + `mark_robustness` + `ensure_range_checking` gate | tests/tcm/test_datacases.py: `test_robustness_marking_round_trips_and_joins_digest`; tests/tcm/test_ranged.py: `test_range_check_refuses_out_of_range_on_normal_case`, `test_range_check_allows_robustness_case` |
| determinism | pure expansion | `test_derived_identifiers_stable_under_reexpansion` |

Uncovered: none for the derived criteria; build-time C-codegen expansion is
CMP-GEN scope.

## Second-pass items

- PLAN-001 §5.4 has no package-specific acceptance criterion for WP-TCM-05; reconcile the derived criteria above (owner edit).
- Persist range declarations in `.tests` files (model + serialization extension) and render the build-time expansion into harness code (CMP-GEN).

# Verification Analysis Note — WP-TRC-01 (Requirement Association and Bidirectional Matrix)

Analysis evidence for requirements verified under WP-TRC-01. Status: **implemented**
(evidence-backed).

Acceptance criterion recorded in PLAN-001 §5.4 (this package has one, unlike most):
"A requirement linked by two association rows to the same test aggregates to one counted pair
and one worst-outcome verdict — never a 2/1 numerator-over-denominator — and a requirement
linked to no executed test is reported `unverified`." The evidence below is organised against
that criterion and TOOL-TRC-110, which spells out the same rules.

## Acceptance evidence against the recorded criterion

- **One counted pair.** `AssociationSet` deduplicates by construction: `from_rows` collapses
  duplicate rows, `pair_count` is the unique-pair count, and every figure in
  `verdict_figures()` uses it (`pair_denominator` labels it: "N unique (requirement, test)
  pairs"). `tests/trc/test_matrix.py::test_duplicate_rows_collapse_to_one_pair` runs the
  criterion's exact scenario — three identical rows for (R1, t1) — and asserts one pair, one
  link, one verdict, `pair_count == 1`.
- **One worst-outcome verdict.** `_requirement_verdict` computes the worst outcome over the
  linked *executed, reviewed* tests (severity `pass` < `not_run` < `timeout` < `error` <
  `fail`); the parametrised `test_verdict_is_the_worst_executed_outcome` covers the outcome
  combinations.
- **Unverified, never inferred.** A requirement whose links are all not-run/missing is
  `unverified` (`test_requirement_linked_to_no_executed_test_is_unverified`); a universe
  member without associations is `unverified`
  (`test_universe_member_without_associations_is_unverified`); coverage is not an input to
  the module at all (`test_verdict_is_never_inferred_from_coverage`).

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TRC-010** | The tool shall support associating one or more requirement identifiers with each test case. | `src/ectt/trc/associations.py` (`Association`, `AssociationSet`), `src/ectt/trc/matrix.py` (`associations_from_datacases`) | **Guarantee (association, many per test):** associations are (requirement, test) pairs; a test may carry any number of them and a requirement any number of tests. `associations_from_datacases` collects the `requirements` field of data-driven cases (WP-TCM-02) directly; raw rows from imports or user edits enter through `from_rows` with id validation (non-empty, whitespace-free; `invalid_id` otherwise) and idempotent deduplication.<br><br>**Test evidence:** `test_from_rows_accepts_duplicates_mixed_with_distinct_pairs`, `test_ids_reject_whitespace`, `test_associations_from_datacases`. |
| **TOOL-TRC-020** | The tool shall generate a bidirectional traceability matrix linking requirements to test cases and test cases to requirements. | `src/ectt/trc/matrix.py` (`build_matrix`, `TraceabilityMatrix.forward`, `TraceabilityMatrix.reverse`, `TraceabilityMatrix.to_dict`) | **Guarantee (bidirectional):** the matrix exposes `forward()` (requirement → linked tests) and `reverse()` (test → linked requirements), both deterministically sorted, plus a canonical `to_dict()` carrying both directions, the rows, and the figures. Rows exist for every requirement in the (optional) universe — a universe member without associations still gets a row, so the matrix is complete over the requirement set the caller declares.<br><br>**Test evidence:** `test_matrix_is_bidirectional_and_sorted`, `test_universe_member_without_associations_is_unverified`. |
| **TOOL-TRC-030** | The traceability matrix shall report the pass/fail status of each linked test case. | `src/ectt/trc/matrix.py` (`TestLink`, status resolution in `build_matrix`) | **Guarantee (status per link):** every link carries the recorded status from the report model's test statuses (WP-REP-01 vocabulary); a linked test with no recorded status shows `not_run`. Unknown status strings are refused (`invalid_status`) rather than guessed.<br><br>**Test evidence:** `test_links_carry_the_recorded_status`, `test_linked_test_without_a_result_is_not_run`, `test_unknown_status_is_refused`, `test_statuses_come_from_a_report_model` (integration: statuses taken straight from a persisted `ReportModel`). |
| **TOOL-TRC-110** | Requirement-level verdict figures computed by deduplicating association rows to unique pairs; worst-outcome verdicts; unreviewed-origin tests counted as unverified per TOOL-ATG-080; every percentage labels its denominator; a requirement linked to no executed test is `unverified`, never inferred from coverage. | `src/ectt/trc/matrix.py` (`TEST_SEVERITY`, `_requirement_verdict`, `TraceabilityMatrix.verdict_figures`, `unreviewed_tests` parameter) | **Guarantee (dedup first):** all counting happens after deduplication (see the criterion evidence above).<br><br>**Guarantee (worst outcome):** severity-ordered worst outcome among linked executed tests; `not_run` links never execute into the verdict.<br><br>**Guarantee (unreviewed origin, ATG-080):** a generated-and-unreviewed test (`unreviewed_tests`) keeps its recorded status in the row, flagged `unreviewed: true`, but does not execute into the verdict — a requirement whose only passing tests are unreviewed is `unverified` until reviewed; one reviewed passing test restores `pass` (`test_one_reviewed_test_overrides_unreviewed_ones`).<br><br>**Guarantee (labelled denominators):** `verdict_figures()` returns counts plus percentages, each carrying its denominator string ("N requirement rows"; "N unique (requirement, test) pairs") — no bare percentage.<br><br>**Test evidence:** `test_duplicate_rows_collapse_to_one_pair`, `test_verdict_is_the_worst_executed_outcome[*]`, `test_requirement_linked_to_no_executed_test_is_unverified`, `test_universe_member_without_associations_is_unverified`, `test_verdict_is_never_inferred_from_coverage`, `test_unreviewed_generated_tests_count_as_unverified`, `test_one_reviewed_test_overrides_unreviewed_ones`, `test_figures_label_every_denominator`, `test_matrix_is_deterministic_and_json_safe`. |

## Design notes

- **Why deduplication lives in the association set, not the matrix.** TOOL-TRC-110's rule is
  about the data, not the rendering: once the set holds unique pairs, no consumer can
  reintroduce the 2/1 shape.
- **Why unreviewed tests keep their status in the row.** The fact is recorded (the test did
  pass); only its *weight* changes (it does not execute into the verdict until reviewed).
  Hiding the status would discard evidence; counting it would overstate verification.
- **Why the universe parameter exists.** TOOL-TRC-020's matrix is complete over the declared
  requirement set; without it, only associated requirements would appear and an unverified
  requirement could vanish from the report. (The fully unlinked-reporting view is WP-TRC-02.)
- **Statuses come from the report model, not from re-running anything.** Same single-source
  discipline as the report package: the matrix reads `test_statuses()`.

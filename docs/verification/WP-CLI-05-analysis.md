# Verification Analysis Note — WP-CLI-05 (CI Sharding and Report Merge)

Analysis evidence for requirements verified under WP-CLI-05. Status: **implemented**
(evidence-backed, with one interim format constraint recorded in SECOND_PASS).

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory):

- **AC-1 (TOOL-CIC-060, T — equivalence partitioning, sharding side):** partitioning a test
  suite across N runners is a pure, deterministic function of the suite contents: complete
  (union equals the suite), disjoint (every test exactly once), balanced (sizes within one),
  order-free on both input and output; partition classes cover {N=1}, {N=len(suite)},
  {N>len(suite)} (empty trailing shards), {empty suite}, {invalid N}.
- **AC-2 (merge side):** merging per-runner reports unions the tests, refuses a test that
  ran in two shards, requires per-unit coverage totals to agree across shards, takes the
  merged covered count as a documented lower bound on the union (never an overstatement),
  and records `partial` when any shard was partial.
- **AC-3 (end-to-end):** shard → run per shard → merge reproduces the whole suite's statuses.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-CIC-060** | The tool shall support sharding a test suite across multiple CI runners and merging the resulting reports. | `src/ectt/cli/sharding.py` (`shard_suite`, `merge_reports`), the report model it merges (`ectt.rep.model`, WP-REP-01/06/08) | **Guarantee (sharding):** round-robin over the sorted ids — order-free input, order-free output, no hash-seed or machine dependence; `shard_count` validation refuses non-positive and non-integer values (`invalid_shard_count`).<br><br>**Guarantee (merge honesty):** a test present in two shard reports is refused (`duplicate_test`) — that is a scheduling bug, not a fact to paper over; per-unit coverage totals must agree across shards (`conflicting_coverage` — they measured the same unit); the merged covered count is the **maximum** over shards, a documented lower bound on the true union: CI reports may understate coverage but never overstate it (fail-safe for threshold gates). The merged run id is the sorted shard run ids joined with `+`; the provenance records each shard's report id as an input digest. Execution facts are deliberately not merged (shards may run on different runners and toolchains).<br><br>**Test evidence:** `tests/cli/test_sharding.py` — `test_six_tests_over_three_runners_balance_exactly`, `test_partition_is_complete_and_disjoint`, `test_partition_is_input_order_free`, `test_invalid_shard_counts_are_refused[*]`, `test_single_runner_takes_everything`, `test_more_runners_than_tests_yields_empty_trailing_shards`, `test_empty_suite_partitions_into_empty_shards`, `test_merge_unions_tests_and_run_ids`, `test_merge_is_input_order_free_and_deterministic`, `test_merge_refuses_a_test_that_ran_twice`, `test_merge_refuses_conflicting_coverage_totals`, `test_merge_records_partial_when_any_shard_is_partial`, `test_merge_of_nothing_is_refused`, `test_merged_report_dumps_deterministically`, `test_end_to_end_shard_then_merge_reproduces_the_whole_suite`. |

## Design notes

- **Why round-robin, not hashing.** Balanced shards with a one-line rule; hash-based
  assignment would need seed discipline for determinism that round-robin gets for free.
- **Why the merged covered count is `max`, not `sum`.** Shards run disjoint tests, but a unit
  can be (partially) covered by several shards; summing counters would overstate union
  coverage. `max` is a true lower bound — an understatement is acceptable for gates, an
  overstatement is not (NFR-090 spirit). Line-level union requires REP-10 coverage export
  (P4, ADR-004 territory).
- **Interim format constraint (SECOND_PASS).** The 1.1 report reader requires `execution`
  facts; a merged run has no single runner. Merged reports therefore dump deterministically
  but are refused on load (`missing_field`) until the reader makes `execution` optional
  (provenance stays required). The refusal is fail-safe — never silent — and the exact
  reader change is queued; cli-side code cannot edit `src/ectt/rep` under this item's path
  rules. Relatedly, the merge currently computes the report id through the rep package's
  canonical-body helper; a public factory is queued with the same fix.
- **Why this is a library seam, not a CLI verb.** The sharding and merge calls are consumed
  by CI pipeline templates (WP-CLI-04) and CI scripts; the catalogue publishes protocol-level
  operations only, and no engine operation for sharding is recorded in the register.

# Verification Analysis Note — WP-TRC-02 (Unlinked Requirement and Unlinked Test Reporting)

Analysis evidence for requirements verified under WP-TRC-02. Status: **implemented**
(evidence-backed).

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory):

- **AC-1 (TOOL-TRC-040, T — equivalence partitioning):** given the association set and the
  two explicit universes, the report partitions every universe member into linked or
  unlinked, on both sides: requirements with no linked test are listed, tests with no linked
  requirement are listed, fully linked members are listed in neither, empty associations
  list everything, and empty universes honestly report nothing (universes are required
  arguments — a defaulted universe would silently hide gaps).
- **AC-2 (consistency with WP-TRC-01):** `find_unlinked(...).unlinked_requirements` equals
  exactly the set of requirement ids for which `build_matrix` emits rows without links (all
  of which carry the `unverified` verdict).

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TRC-040** | The tool shall report requirements with no linked test case, and test cases with no linked requirement. | `src/ectt/trc/unlinked.py` (`find_unlinked`, `UnlinkedReport`), `src/ectt/trc/__init__.py` exports | **Guarantee (both gap lists):** the report carries `unlinked_requirements` (requirement-universe members absent from every association pair) and `unlinked_tests` (test-universe members likewise), deterministically sorted; `to_dict()` also records the universe sizes so a reviewer can see the report was computed over a real inventory, not an accidental empty set.<br><br>**Guarantee (explicit universes):** both universes are required keyword arguments — the caller declares what "everything" means (requirement register, test-case inventory), so the check cannot be blinded by a defaulted empty list.<br><br>**Test evidence:** `tests/trc/test_unlinked.py` — `test_requirements_without_tests_and_tests_without_requirements_are_reported`, `test_fully_linked_universes_report_nothing`, `test_empty_associations_report_everything`, `test_empty_universes_report_nothing_without_hiding_gaps`, `test_duplicate_universe_entries_collapse`, `test_report_is_deterministic_and_json_safe`, `test_consistent_with_the_matrix_unverified_rows`, `test_universe_sizes_are_recorded_for_review`, `test_partition_table[*]`. |

## Design notes

- **Why the universes are required arguments.** TOOL-TRC-040's value depends on what
  "every requirement" and "every test case" mean; deriving them from the associations would
  make the gap lists empty by construction. Requiring them keeps the call honest and reviewable.
- **Why the matrix-consistency test exists.** WP-TRC-01's matrix already emits link-less rows
  as `unverified` when a universe is given; the test pins that both views answer the same
  question identically, so consumers cannot get two answers from one data set.

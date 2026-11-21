# Verification Analysis Note — WP-TCM-07 (Boundary, Equivalence and Classification-Tree Derivation)

Analysis evidence for requirements verified under WP-TCM-07. Status: **implemented**
(evidence-backed) for integer-range parameters, enumerated or declared classes and
classification trees. Executor: Claude (lane A, 2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory). Decision D-02 ("Stable ids plus content digests") is implemented as written:
derived cases get stable ids derived from their input values and a content digest.

- **AC-1 (TOOL-TCD-110, boundary value analysis, BOUNDARY VALUE ANALYSIS / EQUIVALENCE
  PARTITIONING):** for an inclusive integer range the tool derives the minimum, minimum+1,
  a nominal midpoint, maximum-1 and the maximum; in robust mode also the two invalid
  values just outside. Duplicates collapse (a one-value range yields one value), values are
  ascending, and each keeps the role it was derived for (where roles coincide on a narrow range
  the nominal value keeps the `nominal` role, so `one_at_a_time` works for any range). Negative, narrow, one-value and
  beyond-64-bit ranges behave.
- **AC-2 (TOOL-TCD-110, equivalence class partitioning):** a range yields a valid class
  (representative: the nominal) and an invalid class below and above (representatives
  `lo-1`, `hi+1`); callers can supply their own classes with representatives.
- **AC-3 (no invented domains):** ranges come from authored `value_range` data; a parameter
  with no range, one bound, or a non-integer bound is reported by name and left alone.
- **AC-4 (combination):** for several parameters the tool supports `one_at_a_time`,
  `each_choice` (fewest vectors covering every value) and `all_combinations`, which is
  capped: exceeding the cap raises instead of truncating. Output is sorted by id,
  duplicate-free, and independent of parameter insertion order.
- **AC-5 (TOOL-TCD-120, classification trees):** a tree is classifications whose classes
  may be refined by sub-classifications; a test case chooses one leaf class per
  classification. `each_choice` covers every class at least once with the fewest cases;
  `all_combinations` is the capped product; a class that only refines assigns no value of
  its own; conflicting assignments to one parameter are refused.
- **AC-6 (ordinary cases, no invented expectations):** vectors become `DataDrivenTestCase`s
  with stable ids and fresh digests and **no expected value**; vectors with an invalid
  value become robustness cases, which the tool's own range check accepts (TOOL-TCD-130).

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TCD-110** | The tool shall support test case derivation via boundary value analysis and equivalence class partitioning of input parameters. | `src/ectt/tcm/derivation.py` (`IntegerDomain`, `boundary_values`, `equivalence_classes`, `domains_from_parameters`, `derive_vectors`, `vectors_to_cases`, `DerivedValue`, `DerivedVector`, `EquivalenceClass`); `src/ectt/tcm/errors.py` (`DerivationError`) | **AC-1:** `test_bva_of_a_normal_range_gives_the_five_classic_values`, `test_robust_bva_adds_the_two_invalid_values_just_outside`, `test_bva_of_narrow_negative_and_degenerate_ranges` (6 cases), `test_robust_bva_of_a_one_value_range_has_both_neighbours`, `test_bva_handles_values_beyond_sixty_four_bits`, `test_every_boundary_value_keeps_the_role_it_was_derived_for`, `test_an_inverted_range_is_refused`, `test_parameter_names_are_single_tokens` (2). **AC-2:** `test_a_range_has_one_valid_and_two_invalid_classes_with_representatives`, `test_equivalence_representatives_flow_into_cases`. **AC-3:** `test_domains_come_from_authored_ranges_and_unranged_parameters_are_reported`. **AC-4:** `test_one_at_a_time_varies_each_parameter_with_the_others_nominal`, `test_each_choice_covers_every_value_with_the_fewest_vectors`, `test_all_combinations_is_the_full_product`, `test_all_combinations_beyond_the_bound_is_refused_not_truncated`, `test_vectors_are_sorted_by_id_and_free_of_duplicates`, `test_derivation_is_deterministic_and_independent_of_parameter_insertion_order`, `test_a_single_parameter_without_a_nominal_still_derives`, `test_one_at_a_time_without_a_nominal_for_a_multi_choice_parameter_is_refused`, `test_bad_derivation_settings_are_refused` (4), `test_a_parameter_with_no_choices_is_refused`, `test_strategies_are_the_documented_set`. **AC-6:** `test_vectors_become_cases_without_an_invented_expected_value`, `test_invalid_values_become_robustness_cases_that_the_range_check_accepts`, `test_fixed_parameters_may_not_repeat_derived_ones`, `test_cases_need_a_unit_and_a_function` (2). |
| **TOOL-TCD-120** | The tool shall support classification-tree-based test case design. | `ClassificationNode`, `TreeClass`, `classification_vectors` | **AC-5:** `test_each_choice_covers_every_leaf_class_with_the_fewest_cases`, `test_a_class_that_only_refines_assigns_no_value_of_its_own`, `test_all_combinations_of_a_tree_is_the_product_of_the_leaf_selections`, `test_tree_cases_are_capped_not_truncated`, `test_invalid_classes_make_invalid_vectors`, `test_conflicting_assignments_to_one_parameter_are_refused`, `test_the_same_assignment_twice_is_not_a_conflict`, `test_unusable_trees_are_refused` (3), `test_tree_derivation_is_deterministic_and_sorted`. |

## Design notes

- **Defect found by test.** The first draft of the tree conflict check compared the whole
  derived value including the name of the class it came from, so two classes assigning the
  *same* value to one parameter looked like a conflict
  (`test_the_same_assignment_twice_is_not_a_conflict`). It now compares value and validity.
- **Derivation yields inputs only.** An expected value would be invented; cases are left
  without one. The user fills it in, or the cases go through the generated-case lifecycle
  (`ectt.atg`), which records observed behaviour as an unreviewed expectation.
- **Midpoint is the nominal value.** `lo + (hi - lo) // 2`; it is a representative, not a
  claim about typical use.
- **One-at-a-time is the default** because it keeps the vector count linear in the number
  of parameters; the product is available but capped.

## Not covered (recorded, not guessed)

- **Non-integer domains:** hexadecimal or character-literal bounds, enumeration names as
  range bounds, floating-point ranges (with its precision question), and struct members.
  Such a parameter is reported as unbounded, never given an invented range.
- **Pairwise (all-pairs) combination** is not provided (not in TOOL-TCD-110).
- **Deriving ranges from C types** (`uint8_t` as 0..255): the analyser deliberately does
  not manufacture ranges from source, so a type-derived default would be a policy decision
  for the owner.
- **Classification-tree authoring and storage** (a file format or editor for trees): trees
  are built in code or by a caller.
- **Wiring into a command or the GUI:** the module is the capability only.

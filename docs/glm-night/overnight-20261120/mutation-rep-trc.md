# Mutation-style strengthening: ectt.rep and ectt.trc (TEST-MUT2)

Hand-written mutants (a flipped comparison, a dropped branch, a swapped ordering), each applied to a
temporary copy of `src/` and run against the existing tests of `tests/rep`, `tests/trc` and
`tests/cli/test_sharding.py`. No file under `src/` was edited. Runner:
`docs/glm-night/overnight-20261120/mutation_rep_trc.py`. A sanity mutant (an import-time error) proves each
run uses the copy, and the unmutated copy must pass first.

**Final kill rate: 65/66 (98.5%); 65/65 (100.0%) excluding 1 equivalent mutant(s).**
**Before the new tests: 51/66 (77.3%).**

| Mutant | File | Seeded fault | Before | After | Killed by |
|---|---|---|---|---|---|
| M01 | `ectt/trc/matrix.py` | timeout no longer fails a requirement | KILLED | KILLED | tests/trc/test_matrix.py::test_verdict_is_the_worst_executed_outcome[linked3-failed] |
| M02 | `ectt/trc/matrix.py` | unreviewed tests count toward verdicts | KILLED | KILLED | tests/trc/test_change_detection.py::test_stale_tests_stop_counting_toward_verdicts |
| M03 | `ectt/trc/matrix.py` | no executed test reads as pass | KILLED | KILLED | tests/trc/test_change_detection.py::test_stale_tests_stop_counting_toward_verdicts |
| M04 | `ectt/trc/matrix.py` | best outcome instead of worst | KILLED | KILLED | tests/trc/test_matrix.py::test_verdict_is_the_worst_executed_outcome[linked1-failed] |
| M05 | `ectt/trc/matrix.py` | timeout is not an executed outcome | KILLED | KILLED | tests/trc/test_matrix.py::test_verdict_is_the_worst_executed_outcome[linked3-failed] |
| M06 | `ectt/trc/matrix.py` | unknown test defaults to pass | KILLED | KILLED | tests/trc/test_matrix.py::test_linked_test_without_a_result_is_not_run |
| M07 | `ectt/trc/matrix.py` | percentage rounded to whole numbers | SURVIVED | KILLED | tests/trc/test_mutation_survivors.py::test_verdict_percentages_keep_one_decimal |
| M08 | `ectt/trc/matrix.py` | pair count taken from row count | KILLED | KILLED | tests/trc/test_matrix.py::test_figures_label_every_denominator |
| M09 | `ectt/trc/matrix.py` | requirement universe ignored | KILLED | KILLED | tests/trc/test_imports.py::test_imported_universe_feeds_matrix_and_unlinked_report |
| M10 | `ectt/trc/matrix.py` | reverse view lists tests, not requirements | KILLED | KILLED | tests/trc/test_matrix.py::test_matrix_is_bidirectional_and_sorted |
| M11 | `ectt/trc/matrix.py` | status vocabulary check inverted | KILLED | KILLED | tests/trc/test_change_detection.py::test_stale_tests_stop_counting_toward_verdicts |
| M12 | `ectt/trc/associations.py` | pair count off by one | KILLED | KILLED | tests/trc/test_matrix.py::test_duplicate_rows_collapse_to_one_pair |
| M13 | `ectt/trc/associations.py` | tests_for selects the wrong pairs | KILLED | KILLED | tests/trc/test_change_detection.py::test_edited_text_flags_exactly_the_linked_tests_with_the_cause |
| M14 | `ectt/trc/associations.py` | requirements_for selects the wrong pairs | KILLED | KILLED | tests/trc/test_matrix.py::test_from_rows_accepts_duplicates_mixed_with_distinct_pairs |
| M15 | `ectt/trc/unlinked.py` | unlinked requirements inverted | KILLED | KILLED | tests/trc/test_imports.py::test_imported_universe_feeds_matrix_and_unlinked_report |
| M16 | `ectt/trc/unlinked.py` | linked tests built from requirement ids | KILLED | KILLED | tests/trc/test_imports.py::test_imported_universe_feeds_matrix_and_unlinked_report |
| M17 | `ectt/trc/imports.py` | id column check inverted | KILLED | KILLED | tests/trc/test_imports.py::test_csv_import_with_free_column_order |
| M18 | `ectt/trc/imports.py` | duplicate column check inverted | KILLED | KILLED | tests/trc/test_imports.py::test_csv_import_with_free_column_order |
| M19 | `ectt/trc/imports.py` | unknown column check inverted | KILLED | KILLED | tests/trc/test_imports.py::test_csv_import_with_free_column_order |
| M20 | `ectt/trc/imports.py` | CSV row numbers off by one | SURVIVED | KILLED | tests/trc/test_mutation_survivors.py::test_csv_error_messages_name_the_spreadsheet_row |
| M21 | `ectt/trc/imports.py` | duplicate requirement check inverted | KILLED | KILLED | tests/trc/test_imports.py::test_reqif_namespaced_and_bare_documents_parse_identically[namespaced] |
| M22 | `ectt/trc/imports.py` | plain-text comments not skipped | KILLED | KILLED | tests/trc/test_imports.py::test_plain_text_import_with_comments_and_blanks |
| M23 | `ectt/trc/imports.py` | CSV title not stripped | SURVIVED | KILLED | tests/trc/test_mutation_survivors.py::test_csv_titles_and_text_are_stripped |
| M24 | `ectt/trc/imports.py` | plain-text title not stripped | SURVIVED | SURVIVED | equivalent: the caller already strips the whole line and the regex consumes the blanks after the colon, so rest.strip() is a no-op |
| M25 | `ectt/trc/change_detection.py` | lone CR not normalised | SURVIVED | KILLED | tests/trc/test_mutation_survivors.py::test_lone_carriage_returns_are_not_a_requirement_change |
| M26 | `ectt/trc/change_detection.py` | changed detection inverted | KILLED | KILLED | tests/trc/test_change_detection.py::test_unchanged_requirements_flag_nothing |
| M27 | `ectt/trc/change_detection.py` | new detection inverted | KILLED | KILLED | tests/trc/test_change_detection.py::test_unchanged_requirements_flag_nothing |
| M28 | `ectt/trc/change_detection.py` | new requirements counted as unchanged | KILLED | KILLED | tests/trc/test_change_detection.py::test_new_requirement_without_baseline_is_flagged_not_assumed_reviewed |
| M29 | `ectt/trc/change_detection.py` | removed requirements flag no tests | KILLED | KILLED | tests/trc/test_change_detection.py::test_removed_requirement_flags_its_tests |
| M30 | `ectt/trc/change_detection.py` | mark_reviewed unknown check inverted | KILLED | KILLED | tests/trc/test_change_detection.py::test_mark_reviewed_clears_only_the_named_requirements |
| M31 | `ectt/trc/source_links.py` | range ending at next function start allowed | SURVIVED | KILLED | tests/trc/test_mutation_survivors.py::test_a_range_ending_on_the_next_function_line_spans_functions |
| M32 | `ectt/trc/source_links.py` | range starting at a function line misses it | SURVIVED | KILLED | tests/trc/test_mutation_survivors.py::test_a_range_starting_on_a_function_line_belongs_to_that_function |
| M33 | `ectt/trc/source_links.py` | parsed check inverted | KILLED | KILLED | tests/trc/test_mutation_survivors.py::test_a_range_starting_on_a_function_line_belongs_to_that_function |
| M34 | `ectt/trc/source_links.py` | two same-named functions not ambiguous | KILLED | KILLED | tests/trc/test_source_links.py::test_duplicate_function_names_are_ambiguous_not_guessed |
| M35 | `ectt/trc/source_links.py` | functions of other files attributed to the unit | KILLED | KILLED | tests/trc/test_mutation_survivors.py::test_a_range_starting_on_a_function_line_belongs_to_that_function |
| M36 | `ectt/trc/source_links.py` | single-line range refused | SURVIVED | KILLED | tests/trc/test_mutation_survivors.py::test_a_single_line_range_is_valid |
| M37 | `ectt/trc/reqif_export.py` | value of exactly the maximum length refused | SURVIVED | KILLED | tests/trc/test_mutation_survivors.py::test_reqif_accepts_text_of_exactly_the_maximum_length |
| M38 | `ectt/trc/reqif_export.py` | date-only time check inverted | KILLED | KILLED | tests/trc/test_mutation_survivors.py::test_reqif_accepts_text_of_exactly_the_maximum_length |
| M39 | `ectt/trc/reqif_export.py` | unreviewed flag inverted | KILLED | KILLED | tests/trc/test_reqif_export.py::test_verdicts_statuses_and_unreviewed_flags_are_carried |
| M40 | `ectt/rep/model.py` | version check inverted | KILLED | KILLED | tests/rep/test_formats.py::test_custom_format_added_without_reexecuting_tests |
| M41 | `ectt/rep/model.py` | digest check inverted | KILLED | KILLED | tests/rep/test_formats.py::test_custom_format_added_without_reexecuting_tests |
| M42 | `ectt/rep/model.py` | duplicate test check inverted | KILLED | KILLED | tests/rep/test_formats.py::test_custom_format_added_without_reexecuting_tests |
| M43 | `ectt/rep/model.py` | duplicate coverage check inverted | KILLED | KILLED | tests/rep/test_from_archive.py::test_rebuilt_report_round_trips_and_renders_deterministically |
| M44 | `ectt/rep/model.py` | full coverage refused | KILLED | KILLED | tests/rep/test_model.py::test_coverage_entry_validation |
| M45 | `ectt/rep/model.py` | digest rule inverted | KILLED | KILLED | tests/rep/test_renderers.py |
| M46 | `ectt/rep/model.py` | missing execution time not shown as unknown | SURVIVED | KILLED | tests/rep/test_mutation_survivors.py::test_missing_execution_time_is_shown_as_unknown |
| M47 | `ectt/rep/model.py` | missing target not shown as none | KILLED | KILLED | tests/rep/test_model.py::test_model_carries_execution_and_provenance |
| M48 | `ectt/rep/model.py` | partial type check inverted | KILLED | KILLED | tests/rep/test_formats.py::test_custom_format_added_without_reexecuting_tests |
| M49 | `ectt/rep/summary.py` | duplicate run check inverted | KILLED | KILLED | tests/rep/test_mutation_survivors.py::test_trend_is_ordered_by_recorded_time_before_run_id |
| M50 | `ectt/rep/summary.py` | none target not mapped to absent | KILLED | KILLED | tests/rep/test_summary.py::test_summary_partitions_units_targets_toolchains |
| M51 | `ectt/rep/summary.py` | trend ordered by run id first | SURVIVED | KILLED | tests/rep/test_mutation_survivors.py::test_trend_is_ordered_by_recorded_time_before_run_id |
| M52 | `ectt/rep/summary.py` | summary runs in reverse order | KILLED | KILLED | tests/rep/test_mutation_survivors.py::test_summary_tests_total_counts_tests_not_runs |
| M53 | `ectt/rep/summary.py` | trend total uses covered | KILLED | KILLED | tests/rep/test_mutation_survivors.py::test_trend_total_sums_the_total_not_the_covered_figures |
| M54 | `ectt/rep/summary.py` | status counts doubled | KILLED | KILLED | tests/rep/test_summary.py::test_summary_partitions_units_targets_toolchains |
| M55 | `ectt/rep/summary.py` | tests total is the run count | SURVIVED | KILLED | tests/rep/test_mutation_survivors.py::test_summary_tests_total_counts_tests_not_runs |
| M56 | `ectt/rep/formats.py` | duplicate format check inverted | KILLED | KILLED | tests/rep/test_formats.py::test_custom_format_added_without_reexecuting_tests |
| M57 | `ectt/rep/formats.py` | format names may contain whitespace | KILLED | KILLED | tests/rep/test_formats.py::test_invalid_format_names_are_refused[ ] |
| M58 | `ectt/rep/formats.py` | format names in registration order | KILLED | KILLED | tests/rep/test_formats.py::test_registry_instances_are_isolated |
| M59 | `ectt/rep/render.py` | partial flag inverted in text | KILLED | KILLED | tests/rep/test_renderers.py::test_text_summary_counts_statuses_deterministically |
| M60 | `ectt/rep/render.py` | coverage unit count wrong in text | SURVIVED | KILLED | tests/rep/test_mutation_survivors.py::test_text_report_counts_coverage_units_not_tests |
| M61 | `ectt/rep/open_export.py` | provenance digest check inverted | KILLED | KILLED | tests/rep/test_open_export.py::test_dump_is_byte_deterministic_and_round_trips |
| M62 | `ectt/rep/open_export.py` | export id check inverted | KILLED | KILLED | tests/rep/test_open_export.py::test_dump_is_byte_deterministic_and_round_trips |
| M63 | `ectt/rep/open_export.py` | export version check inverted | KILLED | KILLED | tests/rep/test_open_export.py::test_dump_is_byte_deterministic_and_round_trips |
| M64 | `ectt/rep/from_archive.py` | missing result set check inverted | KILLED | KILLED | tests/rep/test_from_archive.py::test_report_from_archive_matches_the_original_content |
| M65 | `ectt/rep/from_archive.py` | archived partial flag dropped | SURVIVED | KILLED | tests/rep/test_mutation_survivors.py::test_archived_partial_flag_is_kept |
| M66 | `ectt/rep/from_archive.py` | empty toolchain accepted | SURVIVED | KILLED | tests/rep/test_mutation_survivors.py::test_archived_execution_facts_must_both_be_non_empty[toolchain] |

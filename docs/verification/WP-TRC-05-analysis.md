# Verification Analysis Note — WP-TRC-05 (Source-Element Linking and Requirement Change Detection)

Analysis evidence for requirements verified under WP-TRC-05. Status: **implemented**
(evidence-backed), with one recorded limitation of the analysis model (below). Executor:
Claude (lane B, 2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory):

- **AC-1 (TOOL-TRC-080, links to source):** a requirement can be linked to a function of a
  unit or to a line range of a unit; each link is resolved through the analysis model and
  gets exactly one outcome, resolved or unresolved with a named reason.
- **AC-2 (DSN-TRC-060, survive line movement):** a resolved range link is persisted as the
  function containing it; the function link keeps resolving when the code moves, and a
  renamed or removed function is reported unresolved, never relinked by guess.
- **AC-3 (no guessing):** ranges outside any function, spanning functions, in unparsed or
  unknown units, and ambiguous function names are unresolved; functions declared in other
  files (headers) are not attributed to the unit.
- **AC-4 (TOOL-TRC-090, change detection):** a baseline records a digest of each
  requirement's title and text when its links were last reviewed or executed; comparing
  reports requirements changed, removed and new, and every test linked to one of them as
  needing review, with the requirement ids and kind of change that caused it.
- **AC-5 (digest discipline):** line endings are normalised (a CRLF checkout is not a
  change); any other difference, whitespace and title included, is a change.
- **AC-6 (usable downstream):** the flagged tests, passed as `unreviewed_tests` to the
  matrix, stop counting toward requirement verdicts (TOOL-TRC-110).
- **AC-7 (fail-safe, deterministic):** persisted links and baselines have a deterministic
  JSON form and strict loaders; duplicates, unknown ids and malformed documents are
  refused with a `TrcError` reason.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TRC-080** | The tool shall link requirements to source code elements in addition to test cases. | `src/ectt/trc/source_links.py` (`SourceLink`, `resolve_source_links`, `SourceLinkResolution`, `ResolvedSourceLink`, `dump_source_links`, `load_source_links`) | **AC-1:** `test_function_link_resolves_to_its_function`, `test_line_range_inside_a_function_resolves_to_that_function_as_approximate`, `test_range_in_the_last_function_resolves`, `test_forward_and_reverse_views_use_anchored_elements`. **AC-2:** `test_anchored_links_survive_line_movement`, `test_renamed_function_is_reported_not_silently_relinked`. **AC-3:** `test_unresolvable_links_are_reported_with_a_reason` (5 cases), `test_duplicate_function_names_are_ambiguous_not_guessed`, `test_functions_declared_in_other_files_are_not_attributed_to_the_unit`, `test_windows_style_and_dot_prefixed_unit_paths_match`. **AC-7:** `test_malformed_links_are_refused` (6 cases), `test_link_identifiers_are_validated`, `test_persisted_links_roundtrip_deterministically`, `test_loader_refuses_bad_documents` (8 cases), `test_duplicate_links_collapse_and_order_is_input_free`, `test_dump_contains_no_wall_clock_or_absolute_paths`. |
| **TOOL-TRC-090** | The tool shall detect when a requirement has changed since its linked test cases were last executed or reviewed. | `src/ectt/trc/change_detection.py` (`record_baseline`, `detect_changes`, `mark_reviewed`, `requirement_digest`, `ReviewBaseline`, `ChangeReport`, `dump_baseline`, `load_baseline`) | **AC-4:** `test_unchanged_requirements_flag_nothing`, `test_edited_text_flags_exactly_the_linked_tests_with_the_cause`, `test_a_test_linked_to_two_changed_requirements_lists_both_causes`, `test_title_edits_count_as_changes`, `test_removed_requirement_flags_its_tests`, `test_new_requirement_without_baseline_is_flagged_not_assumed_reviewed`, `test_empty_baseline_flags_every_requirement_as_new`. **AC-5:** `test_crlf_checkout_is_not_a_change_but_whitespace_edits_are`, `test_title_text_boundary_is_part_of_the_digest`. **AC-6:** `test_stale_tests_stop_counting_toward_verdicts`, `test_mark_reviewed_clears_only_the_named_requirements`, `test_mark_reviewed_can_baseline_a_new_requirement`. **AC-7:** `test_mark_reviewed_refuses_an_unknown_requirement`, `test_duplicate_requirement_ids_are_refused`, `test_report_and_baseline_are_deterministic`, `test_baseline_roundtrips`, `test_loader_refuses_bad_baselines` (6 cases). |

## Design notes

- **Defect found by test.** `SourceLink` first used dataclass ordering, which cannot
  compare a missing function name with a string; it now has an explicit sort key
  (`test_forward_and_reverse_views_use_anchored_elements` caught it).
- **New requirements are flagged.** With no baseline there is no evidence that the links
  were ever reviewed against this text; flagging is the conservative reading.
  `mark_reviewed` baselines a new requirement once it has been reviewed.
- **Where the baseline lives** (file location, who writes it after a review) is not
  decided here; the package provides the data and its deterministic JSON form.

## Not covered (recorded, not guessed)

- **Function extent.** The analysis model (SDD-002 §4.1, `FunctionModel.location`) records
  where a function starts, not where it ends, so a line range is attributed to the
  function that starts at or before it and refused when it reaches the next function.
  Such links are flagged `approximate`: file-scope code between two functions is
  indistinguishable from the earlier function's tail. Exact attribution needs an end line
  in the analysis model (a schema addition, second-pass row).
- **Links to elements other than functions** (types, globals, macros).
- **Source-side change detection** (a linked function whose body changed since the
  requirement's tests were reviewed) is not part of TOOL-TRC-090 as written and is not
  implemented.
- **CLI/GUI** presentation and the persisted location of links and baselines.

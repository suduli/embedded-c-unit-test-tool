# Verification Analysis Note — WP-MIG-04 (Commercial Tool and CSV Test Data Import)

Analysis evidence for requirements verified under WP-MIG-04. Status: **partial**.
TOOL-MIG-050 is implemented; TOOL-MIG-030 is implemented for tabular exports only (see
"Not covered"). Executor: Claude (lane B, 2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory):

- **AC-1 (TOOL-MIG-050, pairwise over column groups):** a spreadsheet-style CSV plus a
  column mapping imports into `DataDrivenTestCase`s carrying inputs, global initial values,
  expected return / global / out-parameter values, requirement links, suites and stub
  configuration; results are valid `.tests` documents (dump and parse back identically).
- **AC-2 (TOOL-MIG-030, equivalence partitioning over delimiters):** comma, semicolon, tab
  and pipe delimited text — the tabular plain-text exports — import identically.
- **AC-3 (no silent loss):** every data row ends as converted or rejected, with its row
  number and a reason; every source column that is not mapped is listed.
- **AC-4 (nothing invented):** a row without an id, unit or function is rejected; stub
  values without a mode are rejected; duplicate ids reject the later row. Cell text is
  stored literally and never evaluated.
- **AC-5 (fail-safe):** empty input, duplicate headers, mapped columns missing from the
  header, unsupported delimiters and invalid mappings are refused with a `MigError` reason.
- **AC-6 (determinism):** output order and content do not depend on row order or run.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-MIG-050** | The tool shall import test cases from a documented CSV interchange format, permitting migration via spreadsheet from any source. | `src/ectt/mig/csv_import.py` (`import_mapped_csv`, `validate_mapping`, `MappedCsvImport`, `RowOutcome`, `DELIMITERS`) | **AC-1:** `test_rows_become_cases_with_inputs_expected_stubs_and_links`, `test_imported_cases_carry_a_fresh_content_digest`, `test_stub_out_parameters_and_expected_out_parameters_map`, `test_imported_cases_survive_the_tests_file_writer_and_parser`. **AC-3:** `test_unmapped_columns_are_listed_not_dropped_silently`, `test_every_row_is_accounted_for`. **AC-4:** `test_rows_missing_required_values_are_rejected_with_reason`, `test_duplicate_ids_reject_the_later_row_and_name_the_first`, `test_stub_values_without_a_mode_are_rejected_never_assumed`, `test_invalid_stub_call_count_is_rejected`, `test_formula_like_cells_are_stored_literally_never_evaluated`, `test_ragged_rows_are_rejected_not_padded`. **AC-5:** `test_unusable_input_is_refused` (4 cases), `test_unsupported_delimiter_is_refused`, `test_bad_mappings_are_refused` (5 cases). **AC-6:** `test_result_does_not_depend_on_row_order`, `test_import_is_deterministic`, `test_bom_crlf_and_blank_lines_are_tolerated`, `test_quoted_cells_with_delimiters_and_newlines_survive`. |
| **TOOL-MIG-030** | The tool shall import test case data from commercial tools where those tools provide a documented or plain-text export format, converting inputs, expected values, and stub configuration. | same module | **Partial.** Any commercial export that is tabular (CSV, TSV, pipe or semicolon delimited) imports through a column mapping. **AC-2:** `test_every_supported_delimiter_gives_the_same_cases` (4 delimiters). **Not covered:** adapters that parse a specific commercial tool's own script or XML export format — see below. |

## Design notes

- **Source-neutral by construction.** The mapping is data (`column header -> target`), so
  no commercial tool's format knowledge is baked into the importer, and nothing is copied
  from `vcast-findings/`. A tool-specific adapter would produce the same
  `MappedCsvImport` result.
- **Identifiers are never invented** (D-02, stable ids plus content digests): a case keeps
  the id the source gave it, and carries a fresh content digest bound to its imported
  content.
- **Origin** of imported cases is recorded as author `human` (a spreadsheet is authored by
  a person); no engine or model is claimed.
- **Per-artifact fidelity report (TOOL-MIG-040, WP-MIG-05)** builds on `rows`
  (`converted` / `rejected` with reasons) and `unmapped_columns` as its input.

## Not covered (recorded, not guessed)

- Parsers for a commercial tool's own non-tabular export (script-style or XML). They need
  that tool's documented export sample as input, which is not in the repository; see the
  second-pass row.
- Types, ranges, or boundary checks of imported values against the unit's signature
  (the analysis model is not consulted at import time).
- Compound or iterative structures (slots and per-slot histories): TOOL-MIG-110 requires
  these to be reported as deferred; that detection is WP-MIG-05.

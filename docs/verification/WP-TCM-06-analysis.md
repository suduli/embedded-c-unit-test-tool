# WP-TCM-06 — Test case interchange import and export

Status: in progress (overnight lane A, 2026-11-19)
Requirements: TOOL-TCD-100
Design elements: DSN-TCM-070 (interchange import and export), SDD-002 §5.1 (round-trip contract point)
Dependencies: WP-TCM-02 (DONE in this ledger, commit ffacfce)
Decisions applied as written (not re-decided): none new; D-02 digest binding carries over — the digest travels as a column and mismatches are reported on import.

## Acceptance criteria

Derived from the SRS text (SRS-001 line 314), the DSN-TCM-070 statement, and SDD-002 §5.1's round-trip contract point:

1. **AC-1 (TCD-100 — documented interchange format).** Export produces a fixed-column CSV-class document with a self-identifying `ectt_interchange_version` column; the column set is the documented schema. Output is deterministic: rows sorted by id, LF endings, stable quoting.
2. **AC-2 (TCD-100 — import).** Import reconstructs case records from the interchange. The column set is validated strictly: a missing required column, an unknown column, a malformed row, a duplicate id, or an unparseable cell is a named error.
3. **AC-3 (SDD-002 §5.1 — lossless round trip).** Export → import → export is byte-identical for cases using every modeled field (origin fields, suites, robustness, comparison overrides, stubs, requirements).
4. **AC-4 (DSN-TCM-070 — loss reporting).** Content the interchange cannot express (non-schema case keys; `;` inside list-valued fields) is reported as an explicit loss per case — never silently dropped. Import reports cases whose recorded digest no longer matches their content (edited outside the tool).
5. **AC-5 (determinism, no wall-clock, no network).** Mapping-valued cells are canonical JSON; the modules are pure.

## Format (documented schema, version 1)

Columns in order: `ectt_interchange_version, id, unit, function, origin_author,
origin_engine, origin_model, origin_review_state, requirements, suites,
robustness, input_parameters, input_globals, expected_return,
expected_globals, expected_out_parameters, expected_comparison, stubs, digest`.

- List-valued fields (`requirements`, `suites`) are `;`-joined; a `;` inside a value is unrepresentable and becomes a loss report.
- Mapping-valued fields (`input_parameters`, `input_globals`, `expected_globals`, `expected_out_parameters`, `expected_comparison`, `stubs`) are canonical JSON cells.
- `robustness` is `true`/`false`; `digest` is the case's recorded content digest (D-02).

## Assumptions (conservative readings)

- "CSV or equivalent" (SRS) with "CSV-class interchange" (DSN-TCM-070): the JSON-in-cell composite columns are the documented equivalent, chosen for unambiguity over spreadsheet prettiness; a friendlier tabular mapping is a second-pass design question.
- Import accepts hand-authored rows (digest column empty → case arrives unverified/stale, reported); it never fabricates a digest.

## Requirement → implementation → tests (tests/tcm/test_interchange.py)

| Requirement | Implementation | Tests |
|---|---|---|
| TOOL-TCD-100 (export) | `ectt.tcm.interchange.export_cases` | `test_export_is_deterministic_with_schema_column` |
| TOOL-TCD-100 (import) | `ectt.tcm.interchange.import_cases` | `test_import_reconstructs_cases`, `test_import_validates_columns_strictly`, `test_import_rejects_duplicate_ids` |
| round trip | export∘import∘export identity | `test_round_trip_is_byte_identical_for_full_model` |
| loss reporting | `InterchangeExport.losses`, `InterchangeImport.digest_mismatches` | `test_unrepresentable_content_is_reported_as_loss`, `test_import_reports_digest_mismatch` |
| determinism | canonical JSON cells, sorted rows | `test_export_is_deterministic_with_schema_column` |

Uncovered: none for the derived criteria. TOOL-MIG-040's stricter
import-loss diagnostic channel is the migration package's obligation
(DSN-MIG-040) and is only sketched here via the losses mechanism.

## Second-pass items

- PLAN-001 §5.4 has no package-specific acceptance criterion for WP-TCM-06; reconcile the derived criteria above (owner edit).
- Decide whether a friendlier spreadsheet tabular mapping (fully flat columns per parameter) should replace JSON cells for the migration path (DSN-MIG-040 alignment, owner).

# Verification Analysis Note — WP-TRC-03 (Requirement Import from ReqIF, CSV and Plain Text)

Analysis evidence for requirements verified under WP-TRC-03. Status: **implemented**
(evidence-backed).

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory):

- **AC-1 (TOOL-TRC-050, T — pairwise):** the documented ReqIF subset parses over the
  pairwise combinations of {namespaced, namespace-less document} × {ReqIF.Identifier
  attribute, machine IDENTIFIER only, neither (refused)}; malformed XML is refused with a
  named reason.
- **AC-2 (TOOL-TRC-060, T):** CSV import requires a header naming `id` (free column order,
  optional `title`/`text`, duplicates and id whitespace refused); the plain-text format is
  the documented `ID: title` line grammar with comments and blank lines, refusing a
  colon-less line by line number.
- **AC-3 (one shape):** all three importers emit the same `RequirementRecord` rows
  (demonstrated by an equal-records test across the three formats), and the imported
  universe feeds the WP-TRC-01 matrix and the WP-TRC-02 unlinked report unchanged.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TRC-050** | The tool shall import requirements from ReqIF. | `src/ectt/trc/imports.py` (`import_reqif`, `RequirementRecord`) | **Guarantee (documented subset):** ReqIF 1.x `SPEC-OBJECT` elements; requirement id from the `ReqIF.Identifier` attribute value, falling back to the machine `IDENTIFIER` (both pinned by tests); title from `LONG-NAME`; text from `ReqIF.Description`. Matching is by local element name, so namespaced and bare documents parse identically (the pairwise axis). A `SPEC-OBJECT` with neither identifier source is refused (`missing_requirement_id`), as is malformed XML (`malformed_reqif`) — never silently skipped. Duplicate ids are refused (`duplicate_requirement`): an ambiguous inventory is a caller error, not something to merge silently.<br><br>**Test evidence:** `tests/trc/test_imports.py` — `test_reqif_namespaced_and_bare_documents_parse_identically[*]`, `test_reqif_identifier_only_object_uses_the_machine_identifier`, `test_reqif_object_without_any_identifier_is_refused`, `test_reqif_malformed_xml_is_refused`. |
| **TOOL-TRC-060** | The tool shall import requirements from CSV and from a documented plain-text format. | `src/ectt/trc/imports.py` (`import_requirements_csv`, `import_requirements_text`, `CSV_COLUMNS`) | **Guarantee (CSV):** strict header contract — an `id` column is required, `title`/`text` optional, column order free, repeated header columns refused; rows feed the same validation (`invalid_id`, `duplicate_requirement`).<br><br>**Guarantee (plain text):** the documented line grammar `ID: title text` with `#` comments and blank lines; a line without a colon is refused naming its line number, so a broken inventory cannot parse half-silently.<br><br>**Guarantee (one shape):** an equality test pins that the same requirement expressed in ReqIF, CSV, and plain text imports to identical records; `requirement_universe` feeds the WP-TRC-01 matrix (unverified rows) and the WP-TRC-02 unlinked report without translation.<br><br>**Test evidence:** `tests/trc/test_imports.py` — `test_csv_import_with_free_column_order`, `test_csv_without_id_column_is_refused`, `test_csv_duplicate_ids_are_refused`, `test_csv_id_whitespace_is_refused`, `test_plain_text_import_with_comments_and_blanks`, `test_plain_text_line_without_colon_is_refused_with_the_line_number`, `test_all_three_importers_feed_the_same_record_shape`, `test_imported_universe_feeds_matrix_and_unlinked_report`. |

## Design notes

- **Why local-name matching for ReqIF.** Real ReqIF files carry the 1.0 namespace, but
  hand-made and exported variants drop or change prefixes; matching by local name accepts
  both without loosening the content rules.
- **Why `ReqIF.Identifier` wins over the machine `IDENTIFIER`.** In ReqIF the machine
  identifier is the object's storage id; the `ReqIF.Identifier` attribute is the
  requirement's human identity. The fallback keeps identifier-only exports importable while
  preferring the human id when both exist.
- **Why duplicates are refused, not merged.** Two rows with one id disagree on which content
  is authoritative; merging would pick a winner silently (NFR-090). The caller fixes the
  inventory.

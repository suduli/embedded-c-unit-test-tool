# Verification Analysis Note — WP-TRC-04 (ReqIF Export and External Tool Interop)

Analysis evidence for requirements verified under WP-TRC-04. Status: **partial**.
TOOL-TRC-070 is implemented; TOOL-TRC-100 is not (see "Not covered"). Executor: Claude
(lane B, 2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory):

- **AC-1 (TOOL-TRC-070, round trip):** the matrix and requirement records export as a
  ReqIF 1.2 document that the tool's own importer reads back as exactly the requirement
  inventory it was built from (ids, titles, text — including markup characters, newlines
  and tabs, and ids that are not legal XML ids).
- **AC-2 (traceability content):** each unique (requirement, test) pair is one directed
  `SPEC-RELATION` from requirement to test; requirement verdicts, test statuses and the
  unreviewed flag are carried as attributes.
- **AC-3 (structural validity):** element order follows the ReqIF 1.2 schema (header,
  datatypes, types, objects, relations, specifications); every `IDENTIFIER` is a unique,
  legal XML id; every reference resolves.
- **AC-4 (determinism):** the output is byte-identical for identical inputs; the only time
  value is the caller-supplied `creation_time`; input order does not matter.
- **AC-5 (fail-safe):** text XML cannot carry (control characters), over-long values and a
  malformed or date-only `creation_time` are refused with a `TrcError` reason, never
  written as a corrupt document.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TRC-070** | The tool shall export traceability data in ReqIF for exchange with external requirements management tools. | `src/ectt/trc/reqif_export.py` (`export_reqif`, `REQIF_NAMESPACE`, `TEST_TYPE_ID`); `src/ectt/trc/imports.py` (`_is_test_object`, `-REF` element form in `_attribute_values`) | **AC-1:** `test_export_roundtrips_to_exactly_the_requirement_inventory`, `test_text_with_markup_newlines_and_tabs_survives`, `test_requirements_without_a_record_are_exported_with_empty_text`, `test_requirement_ids_that_are_not_legal_xml_ids_still_roundtrip`, `test_empty_matrix_exports_a_valid_empty_document`. **AC-2:** `test_one_relation_per_unique_requirement_test_pair_with_direction`, `test_verdicts_statuses_and_unreviewed_flags_are_carried`. **AC-3:** `test_document_is_well_formed_reqif_with_the_schema_element_order`, `test_every_reference_resolves_and_identifiers_are_unique_xml_ids`. **AC-4:** `test_export_is_deterministic_and_input_order_free`, `test_creation_time_is_the_only_time_in_the_document`. **AC-5:** `test_bad_header_inputs_are_refused` (3 cases), `test_text_that_xml_cannot_carry_is_refused_not_corrupted`, `test_oversized_text_is_refused`. |
| **TOOL-TRC-100** | The tool shall interoperate with an established open-source traceability tool. | none | **Not covered.** See below. |

## Design notes

- **Importer fix found while building this.** The existing ReqIF importer read attribute
  definitions only from a `REF` *attribute* (a non-standard form); ReqIF 1.2 writes an
  `ATTRIBUTE-DEFINITION-STRING-REF` *element* whose text is the id. A standards-shaped
  document therefore lost its `ReqIF.Identifier`/description on import. The importer now
  reads both (`test_standard_ref_element_form_is_read_by_the_importer`); existing tests
  for the older form still pass.
- **Duplicate-identifier defect caught by test.** The first draft reused one attribute
  definition id for both object types, which ReqIF forbids (every `IDENTIFIER` unique);
  ids are now per type.
- **Tests are objects of their own type** so the importer returns requirements only; an
  external tool sees tests as ordinary objects related to requirements.

## Not covered (recorded, not guessed)

- **TOOL-TRC-100 (priority C):** DSN-TRC-080 names StrictDoc and OpenFastTrace as the
  candidates and the SRS names neither. Choosing the adapter target is a product decision,
  and an adapter cannot be tested without that tool installed (no network here). ReqIF is
  the exchange route this package provides; StrictDoc reads and writes ReqIF. Recorded in
  the second-pass file.
- **Schema validation against the OMG XSD:** the XSD is not in the repository and cannot
  be fetched offline; conformance is argued from the 1.2 element order and checked
  structurally by the tests above, not by a validator.
- **Interchange with a live external tool** (opening the file in one) has not been done.
- **Re-import of traceability links** (relations back into associations) is not part of
  TOOL-TRC-070 and is not implemented; only requirements round-trip.

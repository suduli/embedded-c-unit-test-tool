# Verification Analysis Note — WP-REP-12 (Reconstructable Open Result Export)

Analysis evidence for requirements verified under WP-REP-12. Status: **implemented**
(evidence-backed).

Acceptance criterion recorded in PLAN-001 §5.4: "Export passing, failing, crashed, timed-out
and partial-run cases plus result identities, expected/actual values, diagnostics and
provenance; an independent reader reconstructs the test cases from TCM-06 and complete
results without a private project database. Publish the versioned JSON interchange schema,
examples and explicit loss/error handling; coverage export remains REP-10/P4." Decision
D-02 ("stable ids plus content digests") is implemented as written.

## Acceptance evidence against the recorded criterion

- **Every outcome class plus identities, values, diagnostics, provenance** —
  `test_export_covers_all_outcome_classes_and_identities`: the `result_set` section is the
  S3 exchange dictionary with pass/fail/error(timeout/crash)/not_run outcomes, per-result
  `test_id` + `test_digest` identities, the failing case's expected/actual with file/line,
  the partial-run flag, `not_executed` list and run-level `infrastructure_faults`; the
  `provenance` section embeds the core record (tool version, input digests for both halves)
  with its own verified digest.
- **Independent reader, no private database** — `reconstruct(export)` consumes only the
  bundle: cases come back through the TCM-06 importer (`import_cases`), results through the
  S3 reader (`result_set_from_dict`). `test_independent_reader_reconstructs_cases_and_results`
  and `test_reader_reconstructs_from_the_plain_document_only` run it from the plain JSON
  document alone.
- **Versioned schema published, conformance checked** —
  `src/ectt/rep/schema/open-result-1.0.schema.json` (draft 2020-12, `additionalProperties:
  false`); `test_emitted_documents_conform_to_the_published_schema` validates the emitted
  document with jsonschema (the WP-ANA-04 conformance pattern).
- **Explicit loss/error handling** — TCM-06 exporter losses travel verbatim in
  `test_case_losses` (`test_case_losses_travel_verbatim`: a requirements value containing
  ";" is reported, never dropped); the reader reports case rows whose recorded digest no
  longer matches their content (`test_digest_mismatch_in_cases_is_reported_not_dropped`);
  tampering any section or the id is refused on load (`digest_mismatch`), unknown schema
  versions refused (`incompatible_schema_version`).
- **Coverage export remains REP-10/P4** — `test_coverage_export_is_deliberately_absent`: the
  document carries no coverage section, and the published schema's description states it.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-MIG-060** | The tool shall export test cases and results in documented open formats sufficient to reconstruct them in another tool, so that adopting this tool does not create lock-in. | `src/ectt/rep/open_export.py` (`OpenResultExport`, `build_open_export`, `dump_open_export`, `load_open_export`, `reconstruct`, `Reconstruction`), `src/ectt/rep/schema/open-result-1.0.schema.json`, the TCM-06 interchange (`src/ectt/tcm/interchange.py`, lane A) and the S3 exchange reader (`src/ectt/rep/from_archive.py`) | **Guarantee (open formats, sufficient to reconstruct):** the bundle is one canonical JSON document whose two data halves are themselves documented open formats — the S3 result-set exchange dictionary and the TCM-06 fixed-column CSV, carried verbatim with its losses. Reconstruction needs only those documents and their published readers: `reconstruct` re-imports the cases (reporting digest drift per row) and revalidates the results at the runner boundary. The export id and the embedded provenance digest make the bundle integrity-checkable by a third party without any ectt code (SHA-256 over canonical JSON, D-02).<br><br>**Guarantee (lock-in):** no private project database, no proprietary binary, no tool-only semantics: the schema file plus the two referenced format specifications (SDD-002 §5/§6, TCM-06 interchange header) are the complete contract.<br><br>**Test evidence:** `tests/rep/test_open_export.py` — `test_export_covers_all_outcome_classes_and_identities`, `test_provenance_travels_with_its_own_digest`, `test_coverage_export_is_deliberately_absent`, `test_emitted_documents_conform_to_the_published_schema`, `test_dump_is_byte_deterministic_and_round_trips`, `test_load_refuses_tampered_section`, `test_load_refuses_unknown_schema_version`, `test_independent_reader_reconstructs_cases_and_results`, `test_reader_reconstructs_from_the_plain_document_only`, `test_digest_mismatch_in_cases_is_reported_not_dropped`, `test_case_losses_travel_verbatim`, `test_export_id_is_stable_and_discriminating`. |

## Design notes

- **Why the CSV travels verbatim rather than as JSON rows.** The TCM-06 interchange is
  already a documented open format with its own loss reporting and digest discipline;
  re-encoding it would create a second format to keep in sync. The bundle references its
  version (column 1 of the CSV) in the provenance schema versions.
- **Why reconstruction revalidates at the runner boundary.** The bundle is data produced by
  whatever writer; `result_set_from_dict` re-runs `finalize_result`, so a report or tool
  consuming the reconstruction can trust the records the same way it trusts live ones.
- **Why the schema forbids extra properties.** The interchange is a published contract;
  unknown keys would make version negotiation ambiguous. Additive changes bump the schema
  version (the export id binds the whole body either way).
- **Examples.** The conformance test doubles as the worked example: the fixture documents in
  `tests/rep/test_open_export.py` are a complete pass/fail/error/timeout/partial run with
  cases, losses and drift handling.

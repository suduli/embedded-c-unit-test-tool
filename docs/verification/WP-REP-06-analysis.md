# Verification Analysis Note — WP-REP-06 (Report Provenance and Format Version Stability)

Analysis evidence for requirements verified under WP-REP-06. Status: **implemented**
(evidence-backed). Dependency note: the queue lists WP-CORE-04 as a dependency; its
provenance *facility* (`ectt.core.provenance`) already exists and is used here unchanged —
this item is the report-artifact part of CORE-04's "embed in every artifact" remainder, so
the dependency is discharged for the report package without touching `src/ectt/core/`.

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written, recorded here; register edits
are owner territory):

- **AC-1 (TOOL-REP-070, I):** every report model embeds the four facts the requirement
  names — tool version, compiler and version used, target executed on, timestamp of
  execution — through the core provenance record and the execution facts, and both shipped
  renderers surface them identically via the shared `provenance_facts()` accessor.
- **AC-2 (TOOL-REP-130, I):** the report model format is versioned (`FORMAT_CHANGELOG`
  documents 1.0 and the 1.1 change); the reader accepts every version in
  `SUPPORTED_FORMAT_VERSIONS` and refuses others, so archived reports stay interpretable.
- **AC-3 (determinism preserved):** the WP-REP-01 determinism guarantees survive the
  extension — dump and renders remain byte-identical for identical inputs, and the
  cross-renderer agreement battery extends to the provenance facts.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-REP-070** | Every report shall record the tool version, the compiler and version used, the target executed on, and the timestamp of execution. | `src/ectt/rep/model.py` (`ExecutionFacts`, `provenance_facts`, `build_report_model` embedding `ectt.core.provenance.build_provenance`, `_provenance_from_dict` digest verification), `src/ectt/rep/render.py` (both renderers surface `provenance_facts`) | **Guarantee (the four facts, recorded):** `build_report_model` embeds the core provenance record — tool version, build id, interpreter version, schema versions (`report_model`, `result_set`), input digests (the digest of the result set the report was built from), and the execution timestamp from the injected Clock — plus the execution facts carried from the run (`where`, `toolchain` = compiler and version as the runner recorded it, `target_id`). The provenance record carries its own content digest; a tampered field is refused on load (`digest_mismatch`), so the provenance cannot be silently rewritten. Wall-clock values are never hashed (core facility design).<br><br>**Guarantee (renderers agree on the facts):** `provenance_facts()` is the one derivation source (`compiler`, `executed_at`, `target`, `tool_version`); `render_text` emits them as `key: value` lines and `render_json` as a `provenance` object. The cross-renderer agreement battery (`test_renderers_cannot_disagree`) asserts text facts == JSON facts == model facts for every model in the battery.<br><br>**Test evidence:** `tests/rep/test_model.py` — `test_model_carries_execution_and_provenance`, `test_target_id_renders_when_recorded`, `test_load_refuses_tampered_provenance`; `tests/rep/test_renderers.py` — `test_renderers_cannot_disagree[*]` (provenance clause), `test_renderers_record_execution_timestamp_exclude_creation_timestamp`. |
| **TOOL-REP-130** | Report formats used as certification evidence shall be versioned, and changes to them shall be documented, so that archived reports remain interpretable. | `src/ectt/rep/model.py` (`FORMAT_CHANGELOG`, `SUPPORTED_FORMAT_VERSIONS`, `REPORT_MODEL_SCHEMA_VERSION`, version-aware `load_report_model`) | **Guarantee (versioned and documented):** the format carries `schema_version`; `FORMAT_CHANGELOG` documents 1.0 (initial model) and 1.1 (added execution facts + embedded provenance record) as the change record. The writer emits the current version; the reader accepts exactly `SUPPORTED_FORMAT_VERSIONS` and refuses others (`incompatible_schema_version`).<br><br>**Guarantee (archived reports stay interpretable):** a 1.0 document loads unchanged (execution/provenance absent, `provenance_facts()` empty, renders omit the block) and its digest binding is verified over the 1.0 body; a 1.0 document that illegally carries 1.1 fields is refused (`unexpected_field`) so the version cannot be spoofed.<br><br>**Test evidence:** `tests/rep/test_model.py` — `test_format_changes_are_documented`, `test_reader_accepts_1_0_documents`, `test_reader_refuses_1_0_document_carrying_execution`, `test_load_refuses_unknown_schema_version`; `tests/rep/test_model.py::test_dump_is_byte_deterministic` (writer emits the current version, canonical form). |

## Design notes

- **Why the provenance record is embedded, not referenced.** A report used as evidence must
  be self-describing when read back without the producing machine; embedding (with the
  record's own digest) keeps the facts and their integrity in one document.
- **Why the execution timestamp renders but the creation timestamp does not.** TOOL-REP-070
  requires the execution timestamp in the report; TOOL-REP-100's "excluding timestamps" is
  satisfied because the execution timestamp is model *content* (identical inputs include it),
  while the report-creation timestamp (`generated_at`) adds nothing to the report's meaning
  and is excluded outright. `test_renderers_record_execution_timestamp_exclude_creation_timestamp`
  pins both halves.
- **Why `toolchain` is carried verbatim.** The compiler and version are whatever the
  execution host recorded (e.g. `gcc 13.2`); the report is a record, not a re-derivation.
- **Dependency discharge:** WP-CORE-04's facility is used as-is (`build_provenance`,
  `ProvenanceRecord`); nothing in `src/ectt/core/` was modified. The remaining CORE-04
  remainder (embedding in other artifacts) stays with WP-CORE-04.

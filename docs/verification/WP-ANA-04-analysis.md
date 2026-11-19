# Verification Analysis Note — WP-ANA-04 (Analysis Model Persistence and Schema Versioning)

Analysis evidence for requirements verified by analysis (*A*) under WP-ANA-04:

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-PAR-110** | Analysis model carries a schema version field so downstream stages can reject incompatible models | `src/ectt/ana/persist.py` (`assemble_analysis_model`, `write_analysis_model`, `read_analysis_model`), `src/ectt/ana/schema/analysis-model-1.0.schema.json`, `src/ectt/ana/errors.py` | **Guarantee:** every written model carries `schema_version` (`"1.0"`) as its first key. A missing, non-first, or malformed version is rejected with a named error (`MissingSchemaVersionError`, `InvalidSchemaVersionOrderError`, `MalformedSchemaVersionError`).<br><br>**Compatibility rule (SDD-002 §3):** a reader pinned to major M accepts any M.x at or above its minimum minor and ignores unknown fields, so additive changes (for example `scope`, deferred to WP-ING-04) are minor bumps. A different major is rejected in both directions with `IncompatibleSchemaVersionError`, naming both the reader and document versions. The reader never attempts a best-effort read.<br><br>**Why rejection beats degradation:** a generator that half-understands a model emits a harness that compiles but tests the wrong interface, which is worse than one that does not run (SDD-002 §3, TOOL-NFR-090).<br><br>**Published schema:** emitted models validate against the shipped 1.0 JSON Schema, which constrains the S1 enumerations and `ref:type.*` references, so a violation is detectable by any consumer without importing this tool.<br><br>**Test evidence:** `tests/ana/test_persist.py` — `test_schema_version_gate_exact_match`, `test_schema_version_gate_newer_minor_accepted_and_unknown_fields_ignored`, `test_schema_version_gate_different_major_rejected`, `test_schema_version_gate_missing_rejected`, `test_schema_version_gate_not_first_key_rejected`, `test_schema_version_gate_malformed_rejected`, `test_malformed_document_raises_named_error`. `tests/ana/test_schema_conformance.py` — `test_emitted_model_validates_against_published_schema`, `test_schema_rejects_contract_violations`, `test_writer_emits_only_schema_declared_keys`. |

## Companion row — TOOL-PAR-100 (added by night-run re-verification)

| Requirement ID | Summary Statement | Implementation Reference | Verification Evidence |
|---|---|---|---|
| **TOOL-PAR-100** | Analyzer emits a JSON analysis model of the extracted interface, persisted as a project artifact | `src/ectt/ana/persist.py` (`assemble_analysis_model`, `write_analysis_model`, `read_analysis_model`), deterministic digest from `src/ectt/core/determinism.py` | `tests/ana/test_persist.py::test_real_extraction_assemble_write_read_roundtrip` (real libclang extraction → write → read equality), `::test_model_wide_types_deduplication`, `::test_failed_unit_emitted_in_model`, `::test_missing_model_file_raises_named_error`, `::test_content_digest_stability_under_different_clocks` (byte-stability), `tests/ana/test_schema_conformance.py::test_emitted_model_validates_against_published_schema`, `::test_writer_emits_only_schema_declared_keys` |

## PLAN-001 §5.4 exit criterion mapping (recorded criterion)

> A model emitted by the analyzer validates against its published schema, carries a schema
> version, and is rejected with a named reason by a consumer pinned to an incompatible version.

| Criterion element | Evidence | Status |
|---|---|---|
| Validates against published schema | `test_emitted_model_validates_against_published_schema`, `test_schema_rejects_contract_violations` against shipped `src/ectt/ana/schema/analysis-model-*.schema.json` | met |
| Carries a schema version | first-key `schema_version` enforced (`test_schema_version_gate_not_first_key_rejected`, `test_schema_version_gate_missing_rejected`) | met |
| Rejected with named reason by consumer pinned to incompatible version | `test_schema_version_gate_different_major_rejected` (`IncompatibleSchemaVersionError` naming both versions), minor-gate acceptance/pin tests | met |

## Night-run re-verification (2026-11-18)

Re-ran the evidence suites on this worktree: `tests/ana/test_persist.py` +
`tests/ana/test_schema_conformance.py` → 41 passed. Full suite 447 passed / 4 skipped (baseline 4).
Published schemas now span 1.0–1.4 on disk; the writer pinned in these tests emits the current
version with the same first-key and gate semantics the tests assert. Criterion **met** in full.

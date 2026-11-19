# Verification Analysis Note — WP-ING-03 (Ingestion Diagnostics, Persistence and Staleness)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-ING-03. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-ING-070 (S, P2, T), TOOL-ING-090 (S, P2, T), TOOL-ING-100 (S, P2, T) and
TOOL-ING-220 (M, P2, T).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-ING-070): a diagnostics pass over an ingested database
  detects and reports three failure classes with the offending entry and subject
  identified — a source file missing on disk, an include path that does not resolve
  on disk, and a compiler flag outside the documented recognized vocabulary — as
  structured diagnostics, deterministically ordered; a clean database produces no
  diagnostics.
- AC-2 (falsifiable, from TOOL-ING-090): an ingested database persists to a
  version-controllable text file (canonical JSON with a schema version) that is
  byte-identical across saves from identical input, and reloads to a database equal
  to the original — including build tag, response-file references, and invocation
  details — so ingestion need not be repeated.
- AC-3 (falsifiable): persistence failures are named: missing/unreadable persisted
  file, non-JSON content, a persisted document without the schema version, and an
  unsupported schema version.
- AC-4 (falsifiable, from TOOL-ING-100): staleness is judged content-based — changed
  source file, changed response file, changed configuration definition, include
  surface changes — and a stale model is never consumed with only a warning: the
  staleness check returns a report and `assert_fresh` raises rather than allowing
  downstream use. (Implemented by `ectt.ing.staleness` in earlier work; this note
  claims it with the existing test evidence.)
- AC-5 (falsifiable, from TOOL-ING-220): each entry captures the build-context
  identity derivable from the invocation — compiler executable, target triple
  (`--target`, `-target`, `-mtriple`), sysroot (`--sysroot`, `-isysroot`) — and
  carries an explicit caller-supplied build tag; entries differing in any captured
  field remain distinct configurations. (Implemented in
  `ectt.ing.compdb_adapter`; claimed with existing test evidence.)

Scope notes: the recognized-flag vocabulary is documented in
`ectt.ing.diagnostics.RECOGNIZED_FLAG_PREFIXES`; a flag outside it is *reported*, not
rejected — the database still ingests (TOOL-ING-070 asks for detection and report).
Header-existence checks (TOOL-ING-070's "missing headers") are outside the
compile-command level: header resolution happens during source analysis
(CMP-ANA) and is not claimed here.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-ING-070** | The tool shall detect and report ingestion failures — missing headers, unresolvable include paths, unknown compiler flags — with the offending file and flag identified. | `src/ectt/ing/diagnostics.py` (`collect_ingestion_diagnostics`, `IngestionDiagnostic`, `RECOGNIZED_FLAG_PREFIXES`, `RECOGNIZED_FLAG_EXACT`) | **Guarantee:** a diagnostics pass over an ingested database reports, with entry source and offending subject identified: a source file that does not exist (`missing_source`), an include path that does not resolve to an existing directory relative to the entry's working directory (`unresolvable_include`), and an invocation argument outside the documented recognized vocabulary (`unknown_flag`, e.g. a foreign `/Zi`). Diagnostics are reports, not rejections — the database still ingests — and the list is deterministically ordered; a clean database yields none.<br><br>**Honest limits:** missing-header detection (headers not found *through* the include surface) happens during source analysis (CMP-ANA); this pass checks include-path resolution and the flag vocabulary at the compile-command level, which is what the ingestion layer can falsify. Missing headers found by the analyzer are surfaced by the analyzer's diagnostics, not re-detected here.<br><br>**Test evidence:** `tests/ing/test_ing03.py` — `test_clean_database_produces_no_diagnostics`, `test_missing_source_is_reported_with_entry`, `test_unresolvable_include_is_reported_with_flag`, `test_unknown_flag_is_reported`, `test_diagnostics_are_deterministically_ordered`. |
| **TOOL-ING-090** | The tool shall persist the ingested project model to a version-controllable text format so ingestion need not be repeated on every invocation. | `src/ectt/ing/persist.py` (`save_database`, `load_database`, `PERSISTED_SCHEMA_VERSION`), `PersistedModelReadError`/`PersistedModelFormatError`/`PersistedSchemaVersionError` | **Guarantee:** the database persists as canonical JSON (`indent=2`, sorted keys, schema version 1) — a diffable, version-controllable text file, byte-identical across saves of identical input — and reloads to a database whose model is equal to the original: units, include paths, definitions, invocation details (target triple, raw arguments), response-file references and build tag all round-trip. Malformed persistence is named: missing/unreadable file, non-JSON content, missing schema version, unsupported schema version, wrong structure.<br><br>**Test evidence:** `tests/ing/test_ing03.py` — `test_persistence_round_trip_preserves_the_model`, `test_persistence_is_byte_identical_for_identical_input`, `test_persisted_file_is_json_text_with_schema_version`, `test_missing_persisted_file_is_named_error`, `test_non_json_persisted_file_is_named_error`, `test_persisted_document_without_schema_version_is_named_error`, `test_unsupported_schema_version_is_named_error`, `test_ingestion_error_hierarchy_intact`. |
| **TOOL-ING-100** | The tool shall detect staleness content-based and shall force re-ingestion before any downstream use; a stale ingested model shall never be consumed with only a warning. | `src/ectt/ing/staleness.py` (`capture_staleness_inputs`, `check_staleness`, `assert_fresh`) — **pre-existing implementation, claimed here** | **Guarantee:** staleness is content-based (source fingerprints, response-file fingerprints, compdb digest, include-surface digest with header shadowing captured) and fail-closed: any difference — or an unresolvable/missing input — marks the model stale, and `assert_fresh` raises `StalenessError` ("no warn path exists") so downstream use is blocked rather than warned. This increment claims the existing implementation with a fresh end-to-end demonstration run through this run's gates.<br><br>**Test evidence:** `tests/ing/test_ing03.py` — `test_staleness_report_is_strict_not_warning_only` (fresh pass → source change → stale report → fail-closed raise), plus the pre-existing `tests/ing/test_staleness.py` suite (9 tests, green in this run). |
| **TOOL-ING-220** | The tool shall capture per-entry build-context identity — compiler executable, target triple, sysroot — and attach an explicit caller-supplied build tag; entries differing in any captured field remain distinct. | `src/ectt/ing/compdb_adapter.py` (triple/sysroot capture, `build_tag` on `CompilationDatabase`) — **pre-existing implementation, claimed here** | **Guarantee:** per entry the adapter captures the compiler executable, target triple from `--target`/`-target`/`-mtriple` (both separate and `=` forms) and sysroot from `--sysroot`/`-isysroot` (both forms, path-normalised), and `CompilationDatabase.build_tag` carries the caller-supplied tag; entries differing in any captured identity field remain distinct configurations. Claimed with the existing evidence.<br><br>**Test evidence:** `tests/ing/test_compdb_adapter.py` — `test_target_and_sysroot_capture`, `test_target_and_sysroot_separate_flag_forms`, `test_build_tag_attached_and_distinct`, `test_build_tag_default_none_and_stripped` (pre-existing, green in this run), plus `tests/ing/test_ing03.py::test_build_context_identity_captured_per_entry` asserting the captured fields on a reloaded (persisted) entry. |

## Standing summary

WP-ING-03 is recorded as **DONE** in the ledger: TOOL-ING-070 and TOOL-ING-090
implemented with tests; TOOL-ING-100 and TOOL-ING-220 claimed with their pre-existing
green implementations and evidence, plus a fresh end-to-end demonstration in this
run's gate.

# Verification Analysis Note — WP-ING-04 (Test Scope Model and Resolution)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-ING-04. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-ING-120 (M, P2, T), TOOL-ING-130 (M, P2, T), TOOL-ING-140 (M, P2, T),
TOOL-ING-150 (M, P2, T) and TOOL-ING-190 (S, P2, I).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-ING-120): a set of two or more C source files is
  accepted as a single ingestion scope without a build system; a one-file or empty
  set is a named error (`ScopeTooSmallError`).
- AC-2 (falsifiable, from TOOL-ING-130): a test scope is a named first-class record:
  it carries its name, its member translation units, and treats every function
  referenced by members but not defined by any member as external — the
  `external_dependencies` surface lists exactly those.
- AC-3 (falsifiable, from TOOL-ING-140): for a multi-TU scope, each function call is
  classified `intra-scope` when the callee is defined by a scope member and
  `external` otherwise, with the classification deterministic over the caller list.
- AC-4 (falsifiable, from TOOL-ING-150): scope membership can be defined four ways —
  explicit file list, directory expansion (`.c` files, recursive), glob pattern, and
  a named build-system target resolved against a declared target→files mapping — all
  producing the same deduplicated, deterministically ordered member set; an unknown
  target is a named error.
- AC-5 (falsifiable, from TOOL-ING-190): a scope definition persists to and reloads
  from a plain-text, version-controllable JSON file (sorted keys, schema version),
  byte-identical across saves; a duplicate scope name in one scope set is a named
  error.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-ING-120** | The tool shall accept a set of two or more C source files as a single ingestion scope, for the purpose of integration testing, without requiring a build system. | `src/ectt/ing/scope.py` (`TestScope`, `ScopeTooSmallError`) | **Guarantee:** two-or-more source files form a named scope record with no build system involved anywhere; one file or an empty set raises `ScopeTooSmallError` naming the count.<br><br>**Test evidence:** `tests/ing/test_scope.py` — `test_two_or_more_sources_form_a_scope`, `test_fewer_than_two_sources_is_named_error`. |
| **TOOL-ING-130** | The tool shall support a named **test scope** as a first-class concept: a user-defined set of translation units treated as the code under test, with all dependencies outside the set treated as external. | `src/ectt/ing/scope.py` (`TestScope`, `external_dependencies`, `ScopeSet`) | **Guarantee:** the scope is a named frozen record (`name`, `members`) with serialisation; dependencies outside the set are external by construction — `external_dependencies` lists exactly the referenced-but-undefined callees, sorted deterministically; a `ScopeSet` keeps named scopes with unique names and deterministic listing.<br><br>**Test evidence:** `tests/ing/test_scope.py` — `test_scope_is_named_first_class_record`, `test_external_dependencies_listed_exactly`, `test_scope_set_rejects_duplicate_names`. |
| **TOOL-ING-140** | For a test scope containing multiple translation units, the tool shall resolve inter-file dependencies internally to the scope and classify each function call as intra-scope or external. | `src/ectt/ing/scope.py` (`classify_calls`, `KIND_INTRA`, `KIND_EXTERNAL`) | **Guarantee:** with the per-unit callee references and per-unit defined functions supplied by the analysis layer, every call is classified `intra-scope` (callee defined by a member) or `external` (defined by none), deterministically per caller unit.<br><br>**Not covered:** extracting the callee/definition lists is the analyzer's role (CMP-ANA call models feed this classification); the classification rule itself is what this increment owns.<br><br>**Test evidence:** `tests/ing/test_scope.py` — `test_calls_classified_intra_vs_external`. |
| **TOOL-ING-150** | The tool shall support a test scope defined by explicit file list, by directory, by glob pattern, and by build-system target. | `src/ectt/ing/scope.py` (`expand_files`, `expand_directory`, `expand_glob`, `expand_target`, `UnknownScopeTargetError`) | **Guarantee:** all four definition modes produce the same deduplicated, deterministically ordered member shape: explicit lists deduplicate and sort; directory expansion collects `.c` files recursively; glob expansion matches file patterns; a named build-system target resolves against a declared target→files mapping (an unknown target raises `UnknownScopeTargetError` naming it).<br><br>**Test evidence:** `tests/ing/test_scope.py` — `test_explicit_file_list_deduplicated_and_sorted`, `test_directory_expansion_finds_c_files_recursively`, `test_glob_expansion`, `test_named_build_target_resolved_from_mapping`, `test_unknown_build_target_is_named_error`. |
| **TOOL-ING-190** | Test scope definitions shall be stored in a plain-text, version-controllable file. *(Method I)* | `src/ectt/ing/scope.py` (`save_scope`, `load_scope`, `SCOPE_SCHEMA_VERSION`, `ScopeRecordError`) | **Guarantee:** a scope persists as sorted, indented JSON with `schema_version: 1` — diffable, version-controllable text — byte-identical across saves, reloading to an equal scope; malformed files (missing, non-JSON, wrong/missing schema version) are named `ScopeRecordError`s.<br><br>**Test evidence:** `tests/ing/test_scope.py` — `test_scope_persists_and_reloads_byte_identical`, `test_malformed_scope_files_are_named_errors`. |

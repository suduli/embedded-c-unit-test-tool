# Verification Analysis Note — WP-ING-05 (Scope Conflict Detection and External Dependency Reporting)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-ING-05. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-ING-160 (S, P2, T), TOOL-ING-170 (S, P2, T), TOOL-ING-180 (S, P2, T).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-ING-160): symbol conflicts within a scope are detected
  and reported with the offending name and member units: the same name defined
  non-static by two or more members (`duplicate_definition`), the same file-static
  name defined by two or more members (`static_collision`), and a name defined
  non-static in one member and static in another (`mixed_linkage`). A conflict-free
  scope yields no reports; the report list is deterministic.
- AC-2 (falsifiable, from TOOL-ING-170): a single translation unit belongs to more
  than one test scope — a shared member produces no duplicate-name error and the
  containing-scope lookup lists every scope holding it, so a file can be tested in
  one scope and again as part of an integration scope.
- AC-3 (falsifiable, from TOOL-ING-180): the complete list of external dependencies
  requiring stubs is reported for a scope before harness generation: every referenced
  callee defined by no member appears exactly once, sorted, marked as requiring a
  stub; nothing intra-scope appears.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-ING-160** | The tool shall detect and report symbol conflicts within a test scope, including duplicate non-static definitions and colliding file-static identifiers. | `src/ectt/ing/conflicts.py` (`SymbolDeclaration`, `detect_symbol_conflicts`, `SymbolConflict`, `KIND_*` constants) | **Guarantee:** with per-member symbol declarations (name + linkage), the detector reports, with the symbol and member units named: the same non-static name defined by ≥2 members (`duplicate_definition`), the same file-static name in ≥2 members (`static_collision`), and a name non-static in one member and static in another (`mixed_linkage`). A conflict-free scope yields an empty tuple; the list is deterministically ordered by symbol.<br><br>**Not covered:** conflicts with symbols outside the scope (they are externals, ING-180's list) and library-level collisions at link time (WP-GEN-05 link closure).<br><br>**Test evidence:** `tests/ing/test_conflicts.py` — `test_clean_scope_has_no_conflicts`, `test_duplicate_non_static_definition_detected`, `test_colliding_file_static_identifiers_detected`, `test_mixed_linkage_detected`, `test_conflict_listing_is_deterministic`. |
| **TOOL-ING-170** | The tool shall support a single translation unit belonging to more than one test scope, such that a file may be tested in isolation and again as part of an integration scope. | `ectt.ing.scope.ScopeSet` + `src/ectt/ing/conflicts.py` (`scopes_containing`) | **Guarantee:** a `ScopeSet` accepts multiple scopes sharing members without any duplicate-name error — a file is a member of a two-file scope and again of a three-file integration scope — and `scopes_containing` lists every scope holding a unit, deterministically; an unregistered unit yields an empty tuple, an unknown scope name still raises the named error.<br><br>**Test evidence:** `tests/ing/test_conflicts.py` — `test_translation_unit_belongs_to_multiple_scopes`, `test_multi_scope_membership_is_not_a_duplicate_error`. |
| **TOOL-ING-180** | The tool shall report, for a given test scope, the complete list of external dependencies requiring stubs, before harness generation is performed. | `src/ectt/ing/conflicts.py` (`stub_requirements`, `StubRequirement`), building on `ectt.ing.scope.classify_calls` | **Guarantee:** with per-unit callee references and defined functions, the report lists every referenced-but-undefined symbol exactly once, sorted, each with its referencing units — nothing intra-scope appears. This is the pre-generation stub list WP-GEN-06 consumes.<br><br>**Test evidence:** `tests/ing/test_conflicts.py` — `test_stub_requirements_list_complete_and_sorted`, `test_intra_scope_calls_never_require_stubs`. |

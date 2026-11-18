# Verification Analysis Note — WP-GEN-05 (Link Closure and Unresolved Reference Reporting)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-GEN-05. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-HAR-120 (M, P2, T) — *The tool shall resolve all undefined external
references in the harness link step, either by stub generation or by explicit
user-supplied linkage, and shall report any that remain unresolved* — fed by the
WP-ING-05 stub-requirement list and producing stubs via WP-GEN-06.

## Acceptance criteria

- AC-1 (falsifiable): every external reference resolves by exactly one mechanism —
  a generated stub or explicit user-supplied linkage — and the report names which
  mechanism covers each reference; references covered by neither are `unresolved`.
- AC-2 (falsifiable): the closure is enforced, not implied: `assert_closed` raises a
  named error listing every unresolved reference; a closed report raises nothing.
- AC-3 (falsifiable): resolution is deterministic — identical inputs produce
  identical reports (sorted, serialisable) — and an empty reference list closes with
  nothing to resolve.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-HAR-120** | The tool shall resolve all undefined external references in the harness link step, either by stub generation or by explicit user-supplied linkage, and shall report any that remain unresolved. | `src/ectt/gen/linkclosure.py` (`resolve_link_closure`, `LinkClosureReport`, `LinkResolution`, `assert_closed`, `UnresolvedReferenceError`), re-exported by `src/ectt/gen/__init__.py` | **Guarantee:** every external reference resolves by exactly one mechanism — generated stub (WP-GEN-06 output) or explicit user-supplied linkage (generated artifacts win when both cover a name) — and the report names the mechanism per reference; anything covered by neither is `unresolved`. The closure is enforced: `assert_closed` raises `UnresolvedReferenceError` listing every unresolved reference; a closed report raises nothing. Reports are deterministic (sorted, deduplicated references, canonical serialisation); an empty reference list closes trivially.<br><br>**Not covered:** the actual linker invocation and archive/library resolution (WP-BLD-01 executor consumes this report); the stub-requirement feed comes from WP-ING-05 and stubs from WP-GEN-06.<br><br>**Test evidence:** `tests/gen/test_linkclosure.py` — `test_every_reference_resolves_by_one_mechanism`, `test_unresolved_references_reported`, `test_closure_is_enforced_not_implied`, `test_empty_reference_list_closes`, `test_duplicate_references_deduplicated`, `test_stub_wins_over_user_linkage`, `test_report_is_deterministic_and_serialisable` (7 tests, green in the WP-GEN-05 gate run: 678 passed, 4 skipped). |

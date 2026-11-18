# Verification Analysis Note — WP-SEC-04 (Log and Diagnostic Content Control)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-SEC-04. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-SEC-120 (M, P2, T) — *Diagnostic output and logs shall not contain user
source code content beyond what is necessary to identify a location, and the tool
shall document exactly what a diagnostic bundle contains* — built on the WP-CORE-01
determinism/output-confined core.

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-SEC-120 first clause): the diagnostic formatting
  surface emits locations as `path[:line[:column]]` references only — the emitted
  string contains the path, line and column and no source text.
- AC-2 (falsifiable): the content guard rejects diagnostic text that embeds a
  verbatim user source line — appearing as a whole diagnostic line or as a substring
  of one (whitespace-trimmed on both sides), for lines of at least 8 characters so
  braces and short statements cannot produce false positives — with a named error;
  diagnostic text carrying only location references and messages passes; the error
  names the offending source line.
- AC-3 (falsifiable, from TOOL-SEC-120 second clause): the diagnostic bundle contents
  are documented exactly — an explicit entries list (what a bundle contains) and an
  explicit exclusions list (what a bundle must never contain, led by user source
  code content) — both frozen, timestamp-free and deterministic.
- AC-4 (falsifiable): guard behaviour is exercised on both violation and clean
  inputs, including a multi-line diagnostic that mixes locations and messages, and a
  violation attempt with a trailing-whitespace variant of a source line.

Scope notes: this increment ships the diagnostic-content policy surface (formatting,
guard, bundle manifest). The logging plumbing that writes every operational log
through this policy is the WP-CORE-06 logging increment, which consumes it. The
guard is deliberately text-based: it inspects the produced diagnostic string, so it
works regardless of how the message was composed. It is a mitigation, not a parser:
arbitrary transformations of source text are not detected, only verbatim (trimmed)
embedding.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-SEC-120** | Diagnostic output and logs shall not contain user source code content beyond what is necessary to identify a location, and the tool shall document exactly what a diagnostic bundle contains. | `src/ectt/sec/diagnostics.py` (`location_reference`, `assert_no_source_content`, `bundle_manifest`, `DiagnosticBundleManifest`, `BUNDLE_ENTRIES`, `BUNDLE_EXCLUSIONS`), `src/ectt/sec/errors.py` (`SecError`, `SourceContentInDiagnosticError`), re-exported by `src/ectt/sec/__init__.py` | **Guarantee (locations, not content):** the diagnostic formatting surface emits `path[:line[:column]]` references only; the guard `assert_no_source_content` refuses any diagnostic in which a user source line (trimmed, ≥ `MIN_SOURCE_LINE_LENGTH` = 8 chars so braces and short fragments cannot false-positive) appears verbatim — as a whole line or as a substring — raising `SourceContentInDiagnosticError` that names the offending line and the diagnostic's origin. Clean diagnostics carrying only locations and messages pass; short-line exemption is tested; a whitespace variant is caught by the trim-then-substring comparison.<br><br>**Guarantee (documented bundle):** `bundle_manifest()` documents exactly what a diagnostic bundle contains (five entry kinds: version/build id, operating configuration, failing command and exit status, diagnostics reduced to location references, log excerpts under the same discipline) and what it must never contain (three exclusions, led by "user source code content (verbatim, transformed, or excerpted)"). The manifest is frozen, timestamp-free and byte-identical across calls.<br><br>**Honest limits:** the guard is text-based and catches verbatim (trimmed) embedding; transformed source text is not detected — stated in the note, not hidden. Wiring every operational log write through this policy is the WP-CORE-06 logging increment's role.<br><br>**Test evidence:** `tests/sec/test_diagnostics.py` — `test_location_reference_formats_path_line_column`, `test_location_reference_carries_no_source_text`, `test_guard_rejects_verbatim_source_line`, `test_guard_rejects_whitespace_variant`, `test_guard_allows_location_and_messages`, `test_guard_exempts_short_source_lines`, `test_guard_threshold_is_documented`, `test_guard_with_no_forbidden_lines_passes`, `test_bundle_manifest_documents_contents_exactly`, `test_bundle_manifest_excludes_source_content`, `test_bundle_manifest_is_frozen_and_deterministic` (11 tests, green in the WP-SEC-04 gate run: 520 passed, 4 skipped). |

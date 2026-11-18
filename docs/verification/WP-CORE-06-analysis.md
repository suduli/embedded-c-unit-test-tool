# Verification Analysis Note — WP-CORE-06 (Logging and Diagnostic Bundle)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-CORE-06. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-NFR-130 (S, P2, T) — *The tool shall log its operations at configurable
verbosity to support diagnosis of failures* — and TOOL-NFR-160 (M, P2, T) — *The tool
shall produce, on request, a diagnostic bundle containing version information,
configuration, and logs sufficient to reproduce a reported defect, with its contents
documented per TOOL-SEC-120*.

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-NFR-130): logging verbosity is configurable through a
  `Verbosity` scale (quiet, normal, verbose, debug); a message logged at a level above
  the configured verbosity is not recorded; records are kept in deterministic order
  and render with location references (`path[:line[:column]]`) rather than source
  content.
- AC-2 (falsifiable, from TOOL-NFR-160): `build_diagnostic_bundle` produces, on
  request, a frozen bundle containing exactly: the ectt version, the operating
  configuration as sorted key/value pairs, the log excerpt at the requested verbosity,
  the failing tool command and its exit status, and the bundle manifest entries that
  document the contents (the TOOL-SEC-120 linkage). Serialisation is deterministic.
- AC-3 (falsifiable): when the logger is configured with a source-line provider,
  every message is checked against the WP-SEC-04 content guard at record time — a
  message embedding a verbatim user source line raises the named security error and
  is never recorded, so logs follow the diagnostic-content discipline by
  construction, not by convention, and every bundle built from that logger inherits
  the guarantee.
- AC-4 (falsifiable): edge behaviour is tested: empty configuration, empty logs,
  verbosity boundary cases (a message at exactly the configured level is recorded,
  one above is not), and a source-embedding message refused by a logger configured
  with a source-line provider.

Scope notes: the logger is an in-process record keeper for tool operations; CLI
flag plumbing and stream output are later command-layer work. The location-reference
formatting is implemented locally in core to respect the layer direction (core must
not depend on the security package); the bundle build applies the WP-SEC-04 guard via
a lazy import, consistent with the repository's lazy-import idiom. Per-component log
adoption (which subsystems log what) is incremental work; this increment ships the
logging and bundle machinery itself.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-NFR-130** | The tool shall log its operations at configurable verbosity to support diagnosis of failures. | `src/ectt/core/logging.py` (`Verbosity`, `EcttLogger`, `LogRecord`), re-exported by `src/ectt/core/__init__.py` | **Guarantee:** verbosity is configurable on the `QUIET < NORMAL < VERBOSE < DEBUG` scale, changeable mid-run; a message at a level above the configured verbosity is not recorded, one at exactly the level is (boundary tested); records keep deterministic insertion order and render as message plus `path[:line[:column]]` location reference — never source text, by construction and (when a source-line provider is configured) by the WP-SEC-04 guard at record time.<br><br>**Not covered:** CLI flags selecting the verbosity and stream output are command-layer work; per-subsystem adoption of the logger is incremental.<br><br>**Test evidence:** `tests/core/test_logging.py` — `test_verbosity_admits_and_refers_levels`, `test_boundary_level_is_recorded_exactly`, `test_quiet_verbosity_records_only_quiet`, `test_set_verbosity_changes_admission`, `test_records_carry_location_references_not_source`, `test_records_are_in_deterministic_order`. |
| **TOOL-NFR-160** | The tool shall produce, on request, a diagnostic bundle containing version information, configuration, and logs sufficient to reproduce a reported defect, with its contents documented per TOOL-SEC-120. | `src/ectt/core/logging.py` (`build_diagnostic_bundle`, `DiagnosticBundle`), manifest linkage via lazy import of `ectt.sec.diagnostics.bundle_manifest` | **Guarantee:** `build_diagnostic_bundle(...)` assembles a frozen bundle with exactly: ectt version, configuration as sorted key/value pairs, the log excerpt (NORMAL and above), the failing command and its exit status, and the WP-SEC-04 manifest entries that document the bundle's contents — the "documented per TOOL-SEC-120" clause is satisfied by carrying the authoritative manifest in the bundle itself, so a recipient can see the documentation alongside the data. Serialisation is deterministic; the same inputs rebuild byte-identical bundles. When the logger has a source-line provider, record-time guarding makes every excerpt clean by construction.<br><br>**Not covered:** attachment/transport of the bundle (packaging and upload are release/CLI work); the guard relies on a configured source-line provider — a caller that supplies none gets no textual check (stated, not hidden).<br><br>**Test evidence:** `tests/core/test_logging.py` — `test_bundle_contains_documented_contents`, `test_bundle_configuration_is_sorted`, `test_bundle_is_frozen_and_deterministic`, `test_bundle_from_guarded_logger_has_clean_excerpt`, `test_bundle_with_no_logs_and_empty_config`, plus the guard pair `test_guard_refuses_source_embedding_at_record_time` and `test_guard_allows_location_and_config_messages` (13 tests total, green in the WP-CORE-06 gate run: 533 passed, 4 skipped). |

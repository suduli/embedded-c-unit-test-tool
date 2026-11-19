# Verification Analysis Note — WP-ING-06 (Multi-Toolchain Ingestion)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-ING-06. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-ING-110 (C, P3, T) — *The tool shall support ingestion of projects that
build with more than one toolchain, retaining per-toolchain flags* — building on the
WP-TCH-01 compiler configurations and the WP-ING-03 build-context identity (ING-220).

## Acceptance criteria

- AC-1 (falsifiable): a project building with more than one toolchain ingests as one
  multi-toolchain ingestion carrying a separate per-toolchain database; the same
  source path under two toolchains is retained as two distinct configurations (per
  the TOOL-ING-220 identity rule), each with its own flags.
- AC-2 (falsifiable): per-toolchain flags are retained verbatim and retrievable per
  toolchain; an unknown toolchain lookup is a named error; the ingestion is
  deterministic and serialisable.
- AC-3 (falsifiable): each toolchain's database carries a build tag identifying the
  toolchain (an explicit caller tag wins over the default).

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-ING-110** | The tool shall support ingestion of projects that build with more than one toolchain, retaining per-toolchain flags. | `src/ectt/ing/multitool.py` (`ToolchainEntry`, `ingest_multi_toolchain`, `MultiToolchainIngestion`, `UnknownToolchainError`), re-exported by `src/ectt/ing/__init__.py` (added by the morning merge if the export list was not extended — see ledger) | **Guarantee:** entries grouped per toolchain produce one ingestion with a separate `CompilationDatabase` per toolchain; the same source under two toolchains is retained as two distinct configurations with each toolchain's flags verbatim (`flags_for` returns exactly the ingested argument tuple); each toolchain's database carries a build tag (explicit caller tag wins, default is the toolchain name); unknown toolchain or source-not-under-toolchain lookups are named errors; output is deterministic (units sorted per toolchain) and serialisable; blank toolchain names are rejected.<br><br>**Not covered:** automatic toolchain discovery from ING-110's per-toolchain flag retention in the *primary* compile-database path — the WP-ING-03 build-context capture (TOOL-ING-220) already keeps per-entry identity there; this module is the multi-toolchain grouping surface.<br><br>**Test evidence:** `tests/ing/test_multitool.py` — `test_multi_toolchain_ingestion_groups_per_toolchain`, `test_same_source_stays_distinct_per_toolchain`, `test_per_toolchain_flags_retained_verbatim`, `test_unknown_toolchain_is_named_error`, `test_source_not_under_toolchain_is_named_error`, `test_build_tags_per_toolchain`, `test_ingestion_is_deterministic_and_serialisable`, `test_blank_toolchain_name_rejected` (8 tests, green in the WP-ING-06 gate run: 708 passed, 4 skipped). |

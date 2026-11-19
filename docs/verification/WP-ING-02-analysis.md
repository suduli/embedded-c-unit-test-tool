# Verification Analysis Note — WP-ING-02 (Alternative Ingestion Paths)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-ING-02. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-ING-050 (S, P2, D), TOOL-ING-060 (S, P2, T), TOOL-ING-080 (C, P2, T) and
TOOL-ING-210 (M, P2, T).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-ING-060): a single `.c` file with user-supplied include
  paths and preprocessor definitions — no build system — is ingested into the same
  `CompilationDatabase`/`TranslationUnit` model the primary path produces, with the
  include paths and definitions attached to the unit and a compiler invocation
  recorded; a missing source file and a non-`.c` source are named errors.
- AC-2 (falsifiable, from TOOL-ING-210): response-file references (`@file`) in
  ingested compile commands are expanded — resolved relative to the entry's working
  directory, parsed under documented quoting rules with quoted sections kept whole,
  recursion depth-bounded — with the raw invocation preserved on the entry and named
  diagnostics for missing, unreadable, or over-limit response files. (Implemented by
  `ectt.ing.compdb_adapter.expand_response_files` in earlier work; the evidence is the
  existing test set, cited below — this note claims it, it does not reimplement it.)
- AC-3 (falsifiable, from TOOL-ING-050, method D): the build-interception path is
  documented as a concrete command sequence (`bear -- <build>` producing
  `compile_commands.json` ingested by the primary path) in this note, and the
  ingestion half of the demonstration is the existing compile-database test evidence.
- AC-4 (falsifiable): the single-file path feeds the same model invariants as the
  primary path — the produced database round-trips through the model, and the unit's
  include paths and definitions are exactly the user-supplied ones, in order.

Scope note (why this lands as PARTIAL): TOOL-ING-080 (import from Keil uVision
`.uvprojx`, IAR EW `.ewp`, Eclipse/STM32CubeIDE project files) requires three XML
project parsers with format-specific semantics; it is not claimed by this increment
and is recorded as remaining work. No criterion for ING-080 is invented.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-ING-060** | The tool shall operate on a single `.c` file with user-supplied include paths and defines when no build system is available. | `src/ectt/ing/single_file.py` (`ingest_single_source`, `SingleSourceReadError`, `NotCSourceError`) | **Guarantee:** a single `.c` source with user-supplied include paths and preprocessor definitions is ingested into the same `CompilationDatabase`/`TranslationUnit` model the primary path produces: exactly one unit, include paths and definitions attached in the exact user order, working directory recorded, and the compiler invocation recorded as the equivalent direct compile command (`-I...`, `-D...`, source). A missing or unreadable source raises `SingleSourceReadError`; a non-`.c` source raises `NotCSourceError` naming the file; the produced unit round-trips through the model's `to_dict()` invariants.<br><br>**Not covered:** TOOL-ING-080 IDE project imports (see the standing summary).<br><br>**Test evidence:** `tests/ing/test_single_file.py` — `test_single_c_file_ingests_into_database`, `test_single_file_invocation_is_the_equivalent_compile_command`, `test_include_and_define_order_is_preserved`, `test_missing_source_is_named_error`, `test_directory_as_source_is_named_error`, `test_non_c_source_is_named_error`, `test_database_round_trips_through_model_invariants`. |
| **TOOL-ING-210** | The tool shall expand response-file references (`@file`) in ingested compile commands, with documented quoting rules, depth-bounded recursion, preserved raw invocation, and named diagnostics for missing, unreadable, or over-limit response files. | `src/ectt/ing/compdb_adapter.py` (`expand_response_files`, bounds constants), `ResponseFileError` in `src/ectt/ing/errors.py` — **pre-existing implementation, claimed here** | **Guarantee:** `expand_response_files` resolves `@file` references relative to the entry's working directory, parses with quoted sections kept whole, recurses with a documented depth limit, preserves the raw invocation on the entry, and raises named `ResponseFileError` subclasses for missing, unreadable, and over-size response files. This increment claims the existing implementation and its evidence rather than reimplementing it.<br><br>**Test evidence (pre-existing, still green in this run):** `tests/ing/test_compdb_adapter.py` — `test_response_file_expansion_arguments_form`, `test_response_file_command_form_quotes`, `test_response_file_resolved_relative_to_entry_directory`, `test_response_file_missing_fails_named`, `test_response_file_depth_limit`, `test_response_file_no_expansion_keeps_raw_empty`. |
| **TOOL-ING-050** | The tool shall support generating a compilation database via build interception (e.g. Bear) for projects without native export. *(Method D)* | Documentation in this note; ingestion half via `ectt.ing.compdb_adapter` | **Demonstration argument:** the interception path is the documented command sequence: run `bear -- make` (or `bear -- <any build command>`) in the project root; Bear intercepts the compiler executions and writes `compile_commands.json`; the tool ingests that database through the primary path (`ectt.ing.compdb_adapter`, TOOL-ING-010/020), which also applies TOOL-ING-210 expansion to any intercepted `@file` references. The ingestion half of the demonstration is exercised by the existing compile-database test set (`tests/ing/test_compdb_adapter.py`, green in this run). This note documents the path; executing `bear` on a live build is an environment demonstration recorded for a runtime-evidence run. |
| **TOOL-ING-080** | The tool shall import project configuration from Keil uVision (`.uvprojx`), IAR EW (`.ewp`), and Eclipse/STM32CubeIDE project files. | — | **Not covered by this increment** (this is why WP-ING-02 lands as PARTIAL): the three IDE formats require format-specific XML parsers and semantics that exceed the smallest increment derivable tonight. No criterion is invented and no partial importer is stubbed. Remaining work: three importers producing `TranslationUnit` records with per-toolchain flags (pairs naturally with TOOL-ING-110's multi-toolchain ingestion, WP-ING-06). |

## Standing summary

WP-ING-02 is recorded as **PARTIAL** in the ledger: TOOL-ING-060 implemented with
tests; TOOL-ING-210 claimed with its pre-existing green test evidence; TOOL-ING-050
documented as a demonstration path; TOOL-ING-080 (Keil/IAR/Eclipse importers) remains
open.

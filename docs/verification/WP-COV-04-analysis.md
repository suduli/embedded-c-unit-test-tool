# WP-COV-04 — Function and function-call coverage

Status: in progress (overnight lane B, 2026-11-21)
Requirements: TOOL-COV-030, TOOL-COV-040
Design elements: DSN-COV-* per PLAN-001 §3 (CMP-COV)
Dependencies: WP-COV-01 (implemented in this lane: `ectt.cov` gcov reader)
Decisions applied as written (not re-decided):
- **ADR-004 coverage backend (owner answer, 2026-11-21): "GCC first"** — the
  function and call records come from the same documented gcov JSON format;
  Clang must not shape this item.
- **No C compiler on this machine:** validated against hand-written fixtures from
  the documented GCC format. **Real GCC output has not been checked.**

## Format reference additions (GCC 14.4 documentation, verified 2026-11-21)

`functions[]` per file: `blocks` (number of blocks in the function),
`blocks_executed` (executed blocks), `demangled_name`, `end_column`, `end_line`,
`execution_count` (number of executions), `name`, `start_column`, `start_line`.
Line and column numbers count from 1.

`calls[]` per line (present with the documented format since version 2):
`destination_block_id` (block the call continues after return), `returned`
(number of times the call returned; the call count equals the line's `count`),
`source_block_id` (block where the call happens).

## Acceptance criteria

Derived from the SRS texts (SRS-001 §12 lines 409–410) and the PLAN-001 §5.4 row
(`WP-COV-04` — Function and function-call coverage; COV-030 COV-040). PLAN-001 §5.4
records **no package-specific acceptance criterion** for this package (flagged for
reconciliation) — these are the derived, reviewable criteria:

1. **AC-1 (COV-030 — function coverage).** Every `functions[]` record is a
   function; a function is covered iff `execution_count > 0`. Function coverage is
   an exact fraction per file and aggregate; a file/document with no function
   records reports not applicable (no fabricated 100%).
2. **AC-2 (COV-040 — function call coverage).** Every `calls[]` record is a call
   site; a call is covered iff `returned > 0` (the call returned, so the call was
   made). Call coverage is an exact fraction per file and aggregate; no call
   records → not applicable.
3. **AC-3 (merge discipline).** Functions merge by name across runs:
   `execution_count` sums; the static `blocks` count must agree across runs (a
   static instrumentation count is never summed) with `blocks_executed` taking the
   maximum (executed in any run); `demangled_name` must agree when present. Calls
   merge positionally per line like branches (`returned` sums, block ids must
   agree). Duplicated function names within one file are refused on read.
4. **AC-4 (fail-closed).** Wrong-typed or negative fields, a missing function
   name, an unknown optional key carrying a wrong type, or a duplicate function
   name is a named error.
5. **AC-5 (determinism).** Extended documents dump canonically with
   `schema_version` first; no wall-clock; no network.

## Requirement → implementation → tests

| Requirement | Implementation | Tests (tests/cov/) |
|---|---|---|
| TOOL-COV-030 | `GcovFunction` model + `ectt.cov.metrics.function_coverage` | `test_function_coverage_counts_executed_functions`, `test_function_coverage_not_applicable_without_functions`, `test_function_coverage_aggregates_across_files` |
| TOOL-COV-040 | `GcovCall` model + `ectt.cov.metrics.call_coverage` | `test_call_coverage_counts_returned_calls`, `test_call_coverage_not_applicable_without_calls` |
| AC-3 merge | `merge_run_coverage` extension for functions and calls | `test_merge_sums_function_execution_counts`, `test_merge_blocks_mismatch_is_refused`, `test_merge_call_returned_counts_sum`, `test_merge_call_block_id_disagreement_is_refused` |
| AC-4 | reader validation | `test_duplicate_function_name_is_refused`, `test_negative_execution_count_is_refused` |
| AC-5 | canonical dump | `test_function_records_dump_canonically` |

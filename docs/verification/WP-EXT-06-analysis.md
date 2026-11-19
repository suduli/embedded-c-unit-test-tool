# Verification Analysis Note — WP-EXT-06 (Suite Splitting and On-Target Footprint Documentation)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-EXT-06. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-TGT-100 (S, P3, T) and TOOL-TGT-110 (M, P3, A).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-TGT-100): when a suite exceeds a declared target
  memory budget, the planner splits it into multiple target executions — every test
  appears in exactly one chunk, chunks are greedy-filled in deterministic order and
  sorted internally, the number of chunks is minimal under first-fit, and a suite
  that fits is never split; a chunk exceeding the whole budget is a named error.
- AC-2 (falsifiable, from TOOL-TGT-110, method A): the on-target harness overhead —
  RAM, flash and stack per configuration — is documented in a frozen, deterministic
  per-configuration table with the measurement basis stated ("analytical estimates
  pending measurement, not executed evidence"), so no document claims more than is
  known; a configuration absent from the table is a named error.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TGT-100** | The tool shall support splitting a test suite across multiple target executions when the full suite exceeds target memory. | `src/ectt/ext/suite_split.py` (`split_suite`, `SuiteSplit`, `SuiteChunk`, `ChunkTooLargeError`), re-exported by `src/ectt/ext/__init__.py` | **Guarantee:** with a declared memory budget, an oversized suite splits into greedy first-fit chunks — a fitting suite stays one chunk (never split), every test appears in exactly one chunk, chunks are sorted internally and indexed deterministically (input order irrelevant, asserted), and a test costing more than the whole budget raises `ChunkTooLargeError` naming the test. First-fit minimality is asserted (5×20 at budget 60 → 2 chunks, at 100 → 1).<br><br>**Test evidence:** `tests/ext/test_suite_split.py` — `test_fitting_suite_is_not_split`, `test_oversized_suite_splits_into_multiple_executions`, `test_every_test_appears_exactly_once`, `test_chunks_are_deterministically_ordered_and_sorted`, `test_first_fit_minimises_chunk_count`, `test_chunk_larger_than_budget_is_named_error`. |
| **TOOL-TGT-110** | The tool shall document the RAM, flash, and stack overhead of the on-target harness, per configuration. *(Method A)* | `src/ectt/ext/suite_split.py` (`overhead_table`, `OverheadTable`, `OverheadEntry`, `OVERHEAD_ENTRIES`, `OVERHEAD_BASIS`, `UnknownConfigurationError`) | **Analysis argument:** the overhead table documents, per configuration (qemu-mps2-an385, stm32f407vg-openocd, stm32f411re-pyocd), the RAM, flash and stack overhead of the on-target harness — and states its measurement basis in every entry and in the table: *analytical estimates from the harness design, pending on-target measurement, not executed evidence*. That statement is what keeps the documentation honest ("document … per configuration" without claiming measured numbers); an unknown configuration is a named error listing what is documented; the table is frozen and deterministic.<br><br>**Test evidence:** `tests/ext/test_suite_split.py` — `test_overhead_documented_per_configuration`, `test_overhead_states_its_measurement_basis`, `test_unknown_configuration_is_named_error`, `test_table_is_frozen_and_deterministic` (10 tests total, green in the WP-EXT-06 gate run: 827 passed, 4 skipped). |

## Standing summary

WP-EXT-06 is recorded as **DONE** in the ledger: both requirements are covered; the
overhead numbers are explicitly marked analytical estimates pending measurement — the
owner should replace them with measured values after a runtime-evidence run (the
mechanism already carries the basis statement).

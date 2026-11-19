# WP-EXH-03 — Parallel test execution

Status: in progress (overnight lane A, 2026-11-19)
Requirements: TOOL-EXE-050
Design elements: DSN-EXH-040 (parallel execution)
Dependencies: WP-EXH-02 (DONE in this ledger, commit 0963a0d)
Decisions applied as written (not re-decided): none new; run-integrity (T-14) carries over per unit.

## Acceptance criteria

Derived from the SRS text (SRS-001 line 362) and the DSN-EXH-040 statement:

1. **AC-1 (EXE-050 — parallel, configurable).** Independent test executables run concurrently at a configurable degree (`concurrency >= 1`). Every unit completes; the per-unit results are returned in input order regardless of completion order (deterministic).
2. **AC-2 (DSN-EXH-040 — per-worker output directories).** When a worker root is given, each concurrent unit's process runs with its worker-slot directory as its working directory, so coverage data files written to the process working directory cannot collide across workers. Two units writing the same file name produce two distinct files.
3. **AC-3 (aggregation and exit contract).** The parallel outcome is `pass` only when every unit aggregated to `pass`; any `failed` unit makes the parallel outcome `failed`; otherwise (`incomplete`, `build_failed` units) it is `incomplete`. The exit-code contract applies to the parallel outcome.
4. **AC-4 (run integrity per unit).** Each unit keeps the WP-EXH-01/02 discipline: its attempt must be `built`, the NR-19 binding check runs against the unit's own digests, and the NR-18 aggregation is per unit. A stale unit is not executed and does not block the others.
5. **AC-5 (validation and determinism).** `concurrency` must be >= 1; results ordering is deterministic; no wall-clock in any record; no network.

## Assumptions (conservative readings)

- "Independent test executables" (plural, SRS) means the parallel unit is a
  whole built executable (one harness per unit), not the tests inside one
  harness — per-test isolation is WP-EXH-02's supervisor.
- Per-worker output directories are implemented as the subprocess working
  directory (coverage tools write to the process cwd by default); the worker
  root is optional — without it, units run in their inherited working
  directory (no coverage isolation is then claimed).
- Threads (not processes) drive the parallelism: the worker body is a
  blocking subprocess call, which releases the GIL; no shared mutable state
  is touched by the workers.

## Requirement → implementation → tests (tests/exh/test_parallel.py)

| Requirement | Implementation | Tests |
|---|---|---|
| TOOL-EXE-050 | `ectt.exh.runner.run_parallel` — thread-pool over per-unit `run_isolated` calls | `test_units_run_to_completion_in_input_order`, `test_low_degree_serializes_overlap` |
| DSN-EXH-040 | worker-slot working directories | `test_per_worker_directories_prevent_collisions` |
| exit contract | `aggregate_parallel_outcome` + `exit_code_for_outcome` | `test_parallel_aggregation_and_exit_code` |
| T-14 per unit | binding check per unit attempt | `test_stale_unit_is_skipped_others_execute` |
| validation/determinism | concurrency >= 1; input-order results | `test_concurrency_must_be_positive`, `test_units_run_to_completion_in_input_order` |

Uncovered: none for the derived criteria. True-concurrency evidence is the
overlap probe (`test_units_overlap_at_degree_two`): a marker written by one
unit before another starts proves both were in flight.

## Second-pass items

- PLAN-001 §5.4 has no package-specific acceptance criterion for WP-EXH-03; reconcile the derived criteria above (owner edit).
- Coverage collection per worker directory (merging per-worker coverage files into one artifact) belongs to CMP-COV and is out of lane scope tonight.

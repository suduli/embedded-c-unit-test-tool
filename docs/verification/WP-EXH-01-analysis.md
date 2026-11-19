# WP-EXH-01 — Host execution and per-test result reporting

Status: in progress (overnight lane A, 2026-11-19)
Requirements: TOOL-EXE-010, TOOL-EXE-020
Design elements: DSN-EXH-010 (execute half of EXE-010 + normalisation; the build half is DSN-BLD-010/CMP-BLD)
Dependencies: WP-BLD-01 (implemented: `ectt.bld`), WP-TCM-01 (implemented: `ectt.tcm`)
Decisions applied as written (not re-decided):
- **D-02, option (a)** (owner answer 2026-11-19): stable ids plus content digests; result records bind to the digest of the test definition they executed (SDD-003 §7 amendment, commit 15719e4).
- **T-14 run-integrity acceptance** (EXEC-PLAN-001 §7.4 card T-14; NR-17/18/19 semantics from docs/reviews/2026-11-07-subsystem-requirements-and-tasks.md): NR-17 RunAttempt allocated before build, build failure is a first-class attempt record; NR-18 pass requires finalized per-attempt result records, exit(0) alone is abnormal; NR-19 exact artifact↔test binding checked before every run — implemented under D-02(a) as content-digest binding.

## Acceptance criteria

Derived from the SRS texts (SRS-001 lines 354–356), DSN-EXH-010, SDD-002 §6 (S3 Result Set model and §6.1 contract points), and the T-14 run-integrity acceptance. PLAN-001 §5.4 records no package-specific criterion for CMP-EXH (flagged for reconciliation) — these are the derived, reviewable criteria:

1. **AC-1 (EXE-010 — execute half).** The runner invokes a built harness executable on the development host — directly, no shell, no network — captures its output stream, and normalises it at the runner boundary into one result record per test case. Downstream sees only normalised records, never framework output.
2. **AC-2 (EXE-020 — per-test reporting).** A `fail` record identifies the assertion, expected value, actual value, and source location (file and line). A `pass` record carries no failure records. Outcomes are restricted to the S3 set (pass | fail | error | timeout | not_run). A RESULT line for a test that was not allocated, a duplicate result, or an unparseable line is rejected with a named error — no results may be invented.
3. **AC-3 (NR-17 — attempt before build).** A run attempt is allocated (with execution metadata and test allocations) before the build is invoked. A build failure is recorded as a first-class attempt record carrying structured diagnostics, and yields a run outcome of `build_failed` — never `pass` — without fabricating result records.
4. **AC-4 (NR-18 — finalized records decide).** A run aggregates to `pass` only when every allocated test has a finalized result record with outcome `pass`. Any allocated test without a finalized record makes the outcome `incomplete`. Records violating their invariants (a pass with failures, a fail without failures, an executed record without a test digest) are unconstructible. The process exit status is never consulted to decide pass.
5. **AC-5 (NR-19 + D-02 — binding checked before every run).** Before execution, every allocated test's artifact-recorded content digest is checked against the test's current content digest. A mismatched (stale) test's results are not accepted as current evidence — the test lands in `not_executed` — and the run outcome is `incomplete`, never `pass`.
6. **AC-6 (partial and not_executed are fields).** Allocated tests absent from the harness stream land in `not_executed` with `partial=true` — a subset run cannot be presented as a full one because the flag travels with the data (SDD-002 §6.1).
7. **AC-7 (determinism, no wall-clock, no network).** The harness result-stream protocol carries no timing values; the normaliser leaves `duration_ms` unset. Result-set dumps are byte-deterministic canonical JSON with `schema_version` first (SDD-002 §6 sketch, ADR-002 JSON-for-exchange rule). The package performs no network I/O.

## Harness result-stream protocol (normalisation target)

Defined by this package as the normalisation target for generated harnesses
(DSN-EXH-010: framework output is normalised at the runner boundary). Line
protocol on the harness's stdout; blank lines and non-protocol lines are
ignored:

```
RESULT <test_id> <outcome>
FAILURE <test_id> <assertion> <expected> <actual> <file> <line>
```

- `<outcome>` is `pass`, `fail`, or `error` (the harness never emits `timeout`/`not_run`; those are supervisor/selection outcomes).
- Every field is a single non-empty token without whitespace; `<line>` is a positive integer.
- A `FAIL` result must be followed by at least one matching `FAILURE` line; a `FAILURE` for a test that never reports `RESULT` is a malformed stream.
- The generated harness (WP-GEN) must emit this protocol — recorded as a second-pass item.

## Requirement → implementation → tests

| Requirement | Implementation | Tests (tests/exh/test_runner.py) |
|---|---|---|
| TOOL-EXE-010 (execute half) | `ectt.exh.runner.run_harness` — direct subprocess invocation of the built executable, output captured and normalised | `test_happy_path_reports_one_record_per_result_line`, `test_missing_executable_raises_named_error` |
| TOOL-EXE-020 | `ectt.exh.results` — `ResultRecord`/`AssertionFailure`/`SourceLocation` with construction-time invariants; strict stream parser | `test_fail_record_carries_assertion_expected_actual_location`, `test_pass_record_carries_no_failures`, `test_unknown_test_result_is_rejected`, `test_duplicate_result_is_rejected`, `test_malformed_stream_is_rejected` |
| T-14 NR-17 | `ectt.exh.runner.allocate_attempt` / `record_build_failure` / `build_failed_run` | `test_attempt_is_allocated_before_build_with_allocations`, `test_build_failure_is_first_class_attempt_record` |
| T-14 NR-18 | `finalize_result` invariants + `aggregate_outcome` over finalized records | `test_pass_aggregation_requires_finalized_records_for_every_allocation`, `test_record_invariants_are_enforced`, `test_exit_status_is_never_consulted_for_outcome` |
| T-14 NR-19 / D-02 | `check_test_bindings` digest check before execution; stale tests not executed | `test_stale_binding_prevents_execution_and_reports_not_executed` |
| SDD-002 §6.1 | `partial` / `not_executed` travel with the data | `test_missing_results_mark_run_partial`, `test_stale_binding_prevents_execution_and_reports_not_executed` |
| determinism | canonical JSON dump, protocol carries no timing | `test_result_set_dump_is_deterministic_canonical_json` |

Uncovered: none — AC-1..AC-7 each have at least one named test. Timeout
enforcement, crash isolation, and the exit-code contract are WP-EXH-02 scope
(TOOL-EXE-030/040/060) and intentionally absent here.

## Second-pass items

- PLAN-001 §5.4 has no package-specific acceptance criterion for WP-EXH-01; the derived criteria above should be reviewed and reconciled into the plan (owner edit).
- T-14's document side: run-integrity acceptance wording into PLAN-001 §5.4 (WP-EXH-01/02, WP-CBT-01 exit criteria) and NR-17..19 wording into SRS-001 — owner edits, out of lane scope.
- The generated harness (WP-GEN) must emit the RESULT/FAILURE protocol defined above; coordinate when WP-GEN harness emission lands.

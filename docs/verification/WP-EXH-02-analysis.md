# WP-EXH-02 — Crash isolation, timeout and process exit status

Status: in progress (overnight lane A, 2026-11-19)
Requirements: TOOL-EXE-030, TOOL-EXE-040, TOOL-EXE-060
Design elements: DSN-EXH-020 (fault isolation supervisor), DSN-EXH-030 (timeout enforcement), DSN-EXH-050 (run status aggregation / exit-code contract)
Dependencies: WP-CORE-02 (implemented: `ectt.core`), WP-EXH-01 (DONE in this ledger, commit 98fe972)
Decisions applied as written (not re-decided):
- **T-14 run-integrity acceptance** (EXEC-PLAN-001 §7.4 card T-14): same semantics as WP-EXH-01 — NR-17 attempt lifecycle, NR-18 finalized records decide (exit(0) alone is abnormal), NR-19 binding check before every run under D-02 option (a).

## Board acceptance criterion (recorded in PLAN-001 §5.4)

> A test case that segfaults, one that hangs past the timeout, and one that calls `abort()` are each reported as a failure with the remaining cases still executed.

Interpretation applied tonight (recorded as an assumption): "reported as a failure" reads as the failure class — the case is not a pass. The S3 outcome vocabulary (SDD-002 §6) distinguishes the modes the criterion names: a crash or abnormal termination (segfault, `abort()`) is outcome `error`; a hang past the timeout is outcome `timeout`, which TOOL-EXE-040 (as reworded by the 2026-11-07 correction note, RV-02 F-11) mandates as a distinct outcome — never a pass and never an assertion failure. Remaining cases still execute. Acceptance evidence below is mechanical (tests); the "reviewed acceptance evidence" step is an owner/reviewer action (second-pass).

## Acceptance criteria

Derived from the SRS texts (SRS-001 lines 358–364), DSN-EXH-020/030/050, SDD-002 §6.1, and the board criterion:

1. **AC-1 (EXE-030 — process-granularity isolation).** Each bound test runs in its own harness process (selected via `--ectt-select <test_id>`). A test that crashes (segfault, `abort()`, or any abnormal/silent termination with no RESULT record) is attributed an `error` record; the supervisor continues with the remaining tests. A crash costs one result, not the run.
2. **AC-2 (EXE-040 — timeout is distinct).** The per-test timeout is configurable. On expiry the child is killed and the case is attributed a `timeout` record — neither pass nor fail (RV-02 F-11), carrying no assertion failures.
3. **AC-3 (EXE-060 — exit-code contract).** `exit_code(run)` maps the aggregated outcome to the documented contract: `pass` → 0; every other outcome (`failed`, `incomplete`, `build_failed`) → non-zero. Any test failure or timeout yields non-zero (EXE-040 clause).
4. **AC-4 (run integrity preserved under isolation).** The attempt lifecycle, NR-19 binding check (stale tests not executed, not accepted), NR-18 aggregation over finalized records, and `partial`/`not_executed` fields behave exactly as in WP-EXH-01.
5. **AC-5 (protocol violations still surface).** A harness stream that violates the RESULT/FAILURE protocol (malformed line, unknown test, duplicate result, orphaned FAILURE) raises its named error even under isolation — isolation contains crashes of the test in flight, not harness protocol bugs.
6. **AC-6 (determinism, no wall-clock, no network).** Records carry no timing values (`duration_ms` unset); allocation order drives execution order; no network I/O.

## Evidence

Mechanical evidence: `tests/exh/test_supervisor.py` drives interpreter-hosted
harness stubs in which one test really calls `os.abort()` (a genuine C
`abort()`), one really hangs past a 0.5 s timeout and is killed, and the
remaining tests execute and pass — the board criterion, executed end to end.
The recorded segfault case is exercised through the same no-RESULT
attribution path (a segfault produces no protocol output).

## Requirement → implementation → tests (tests/exh/test_supervisor.py)

| Requirement | Implementation | Tests |
|---|---|---|
| TOOL-EXE-030 | `ectt.exh.runner.run_isolated` — per-test process invocation, no-RESULT attribution, continue-on-crash | `test_crash_attributed_and_remaining_cases_still_execute` |
| TOOL-EXE-040 | per-test `timeout_seconds`; `TimeoutExpired` → distinct `timeout` record | `test_timeout_is_distinct_outcome_and_run_continues` |
| TOOL-EXE-060 | `ectt.exh.runner.exit_code` — documented pass→0 / everything-else→1 contract | `test_exit_code_contract` |
| T-14 NR-19/18 | binding check + aggregation reused from WP-EXH-01 | `test_isolated_run_respects_stale_binding` |
| protocol discipline | parser reused per test with single-test allocation set | `test_protocol_violation_still_surfaces_under_isolation` |
| determinism | no timing recorded; allocation order execution | `test_exit_code_contract`, crash/timeout tests assert record structure |

Uncovered: none for the derived criteria. Crash *diagnostics* (exit code,
stderr text) are observable at the supervisor but the S3 record defines no
diagnostics channel — recorded as a second-pass design question.

## Second-pass items

- PLAN-001 §5.4 WP-EXH-02's board criterion needs reviewed acceptance evidence recorded against it (owner/reviewer action; the mechanical evidence is above).
- Whether crash diagnostics (exit code, signal, stderr) belong in the S3 record — SDD-002 §6 defines no per-record diagnostics channel; an amendment would be a design change (owner).

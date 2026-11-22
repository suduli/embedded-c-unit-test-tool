# Verification Analysis Note — WP-MIG-01 (Execution of Existing Unity and cmocka Suites)

Analysis evidence for requirements verified under WP-MIG-01. Status: **implemented**
(evidence-backed).

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory):

- **AC-1 (TOOL-MIG-010, T — equivalence partitioning):** an existing suite's own binary runs
  through its own `main` — unrewritten — and its native framework stdout is normalised into
  the same finalized S3 records the generated-harness path produces. Partitions: Unity
  PASS / FAIL-with-detail / FAIL-without-detail / IGNORE; cmocka [ OK ] / [  FAILED  ] (+ RUN/LINE/
  summary context lines); unrecognised lines; empty stream; failing exit status.
- **AC-2 (stream-only contract):** no suite source is read or modified — stdout is the only
  input; the process exit status is never consulted (EXH-02 discipline, pinned by a test
  that exits non-zero with all-passing output).

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-MIG-010** | The tool shall execute existing test suites written against supported frameworks (Unity, cmocka) without requiring them to be rewritten. | `src/ectt/mig/existing_suites.py` (`run_existing_suite`, `parse_unity_output`, `parse_cmocka_output`, `ExistingSuiteRun`, `SUPPORTED_FRAMEWORKS`), `src/ectt/mig/errors.py` (`MigError`, category `migration`) | **Guarantee (no rewrite):** the executable is invoked directly (no shell, no network) exactly as its author builds it; the adapter only reads stdout. `SUPPORTED_FRAMEWORKS` equals the generator's backend ids (pinned against `ectt.gen.backends`), so a suite authored for the tool's own generated harnesses and a suite authored by hand are the same two grammars.<br><br>**Guarantee (same record discipline):** normalisation emits finalized `ResultRecord`s via `finalize_result`, so the NR-18 invariants hold at this boundary too. Unity `FAIL` with an `Expected X Was Y` message becomes a `fail` record carrying expected/actual and the framework's file/line; a `FAIL` without detail becomes `error` (an under-detailed failure is never upgraded into a claim it cannot support — and aggregation still treats it as a failure, so requirement verdicts are unaffected); `IGNORE` becomes `not_run`. cmocka `[ OK ]`/`[  FAILED  ]` become `pass`/`error` (`[  OKAY    ]` is accepted as an alias; cmocka's own spelling is `OK`) (the stream contract carries no expected/actual); richer failure-detail extraction is a documented follow-up (SECOND_PASS).<br><br>**Guarantee (never a silent pass):** unrecognised lines are reported; a run producing no records answers `aggregate=None` — never inferred from an empty stream. The process exit status is never consulted.<br><br>**Test evidence:** `tests/mig/test_existing_suites.py` — `test_unity_pass_ignore_and_detailed_fail`, `test_unity_fail_without_detail_becomes_error_not_an_upgraded_claim`, `test_unity_unrecognised_lines_are_reported`, `test_cmocka_okay_and_failed_become_pass_and_error`, `test_both_parsers_are_deterministic`, `test_records_satisfy_the_s3_vocabulary_and_nr18`, `test_run_existing_suite_aggregates_the_framework_result`, `test_all_pass_aggregate_is_pass`, `test_silent_suite_is_never_a_silent_pass`, `test_exit_status_is_never_consulted`, `test_unsupported_framework_and_missing_executable_are_refused`, `test_supported_frameworks_match_the_generator_backends`, `test_run_is_deterministic`, `test_record_type_is_the_shared_finalized_record`. |

## Design notes

- **Why an adapter instead of the exh attempt machinery.** `run_harness` executes
  *ECTT-generated* harnesses whose allocations and digests the tool already knows (NR-19
  binding check). An existing suite's test inventory is unknown until its output arrives;
  fabricating allocations would fake the staleness discipline. The adapter keeps the parts
  that transfer — finalized records, S3 vocabulary, aggregation, exit-status independence —
  and leaves the attempt machinery to generated harnesses.
- **Why FAIL-without-detail maps to `error`, not `fail`.** The S3 model requires a `fail`
  record to carry expected/actual; inventing placeholders would be misleading output
  (NFR-090). `error` is honest ("failure detected, details unavailable") and aggregates the
  same way.
- **Under-detailed cmocka failures.** cmocka's default stream carries no expected/actual
  values; extracting them from message formats is framework-version-specific work recorded
  in SECOND_PASS rather than guessed here.

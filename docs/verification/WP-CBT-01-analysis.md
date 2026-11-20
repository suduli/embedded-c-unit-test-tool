# Verification Analysis Note — WP-CBT-01 (Suite Re-Execution Without Regeneration)

Analysis evidence for requirements verified under WP-CBT-01. Status: **implemented**
(evidence-backed). Executor: Claude (lane A, 2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory). Decision D-02 ("Stable ids plus content digests") is implemented as written,
and the run-integrity acceptance of T-14 (NR-17/18/19), which was waiting on D-02, is
included as AC-3 to AC-5; the register wording of T-14 itself is owner territory.

- **AC-1 (TOOL-CBT-010, re-execute as built):** a suite built earlier runs again from a
  persisted record plus the project root plus the current test-content digests, with no
  other input: toolchain, location, target, order seed and test allocations come from the
  record.
- **AC-2 (without regeneration):** re-execution starts exactly one process, the recorded
  executable; it never calls or imports the generator, the build driver or the toolchain
  package; a missing executable asks for a rebuild instead of producing one.
- **AC-3 (T-14 NR-17/NR-18):** each re-execution is a distinct attempt with its own run id;
  the verdict is aggregated from finalized per-test records and never from the process
  exit status.
- **AC-4 (T-14 NR-19 / D-02):** a test whose content digest differs from the one the
  executable was built from is not executed and is reported stale; a removed test likewise;
  the run is partial and cannot pass as a full one.
- **AC-5 (binary integrity):** an executable whose digest differs from the recorded one is
  refused, so results are never attributed to a build the record does not describe.
- **AC-6 (record discipline):** the record is deterministic JSON, bound by its own digest
  (any edit is refused on load or on use), versioned, and confined to the project root.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-CBT-010** | The tool shall re-execute an existing test suite without regeneration or manual reconfiguration. | `src/ectt/cbt/reexecute.py` (`record_compiled_suite`, `reexecute_suite`, `CompiledSuiteRecord`, `ReExecution`, `bindings_from_cases`, `current_digests`, `dump_suite_record`, `load_suite_record`); `src/ectt/cbt/errors.py` (`CbtError`, category `execution`) | **AC-1:** `test_recorded_suite_reexecutes_with_real_results`, `test_reexecution_needs_only_the_record_root_and_current_digests`, `test_target_and_order_seed_are_part_of_the_record`. **AC-2:** `test_only_the_recorded_executable_is_launched_and_nothing_is_built`, `test_the_cbt_package_never_imports_the_generator_or_the_build_driver`, `test_a_missing_executable_asks_for_a_rebuild_instead_of_regenerating`. **AC-3:** `test_each_reexecution_is_a_distinct_run_and_leaves_the_record_unchanged`, `test_the_process_exit_status_is_never_the_verdict`, `test_run_labels_must_be_single_tokens` (3 cases). **AC-4:** `test_a_test_edited_since_the_build_is_not_executed_and_makes_the_run_partial`, `test_a_test_removed_since_the_build_is_stale_not_silently_passing`, `test_bindings_follow_case_content`. **AC-5:** `test_a_rebuilt_executable_is_refused`. **AC-6:** `test_record_roundtrips_and_is_deterministic`, `test_record_binds_the_binary_the_bindings_and_the_toolchain`, `test_loader_refuses_tampered_or_malformed_records` (7 cases), `test_loader_refuses_non_json_and_non_objects`, `test_reexecuting_a_tampered_in_memory_record_is_refused`, `test_executable_paths_may_not_leave_the_project` (4 cases), `test_recording_refuses_a_missing_executable_and_empty_bindings`, `test_recording_validates_bindings_with_the_runners_rules`. |

## Design notes

- **The execution engine is reused, not duplicated.** `ectt.exh` already owns the attempt
  lifecycle, the binding check and stream normalisation. `ectt.cbt` adds only what
  re-execution needs on top: a durable record of the build, the binary-integrity check and
  a distinct run id per re-execution.
- **Digests, not timestamps.** Staleness is decided by content digest (D-02), so a
  re-saved but unchanged test file does not invalidate a build and an edited test always
  does, whatever the file times say.
- **Refusal over repair.** A changed or missing binary is an error that tells the user to
  rebuild; the package never rebuilds, since that would be regeneration.

## Not covered (recorded, not guessed)

- **Remote targets:** the executable runs on the host through `ectt.exh`; deploying and
  re-running on a hardware target belongs to CMP-EXT.
- **Selective re-execution** of a subset of the recorded tests (TOOL-CBT-020 and later
  CBT packages); this package runs every recorded test that is not stale.
- **Where the record is stored** inside a project (the SDD-003 layout) and who writes it
  at build time: `record_compiled_suite` is called by the build step, whose wiring is not
  part of this package. A second-pass row records the integration point.
- **Parallel and isolated re-execution** (`run_parallel`, `run_isolated`) are not wrapped;
  a re-execution through them needs the same record check, which can be added when the
  caller exists.

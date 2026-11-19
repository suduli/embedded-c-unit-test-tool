# Verification Analysis Note — WP-EXT-01 (Simulator Execution: QEMU and Renode)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-EXT-01. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-TGT-020 (M, P3, T) — *The tool shall execute the test harness on an
instruction-set simulator, verified against QEMU and Renode* — built on the WP-BLD-03
cross-build planning and the WP-SEC-07 untrusted boundary.

## Acceptance criteria

- AC-1 (falsifiable): simulator execution plans are composed per harness binary for
  both documented simulator families — QEMU (`qemu-system-<machine>`) and Renode
  (`renode`/`renode-test`) — from declarative, frozen simulator descriptors (family,
  machine, command template); the composed command line includes the harness path and
  machine selection, deterministically; unknown families and blank machines are named
  errors.
- AC-2 (falsifiable): simulator output is consumed strictly through the WP-SEC-07
  untrusted boundary (`mark_untrusted` → `parse_target_output`); nothing from a
  simulator is executed or interpreted beyond that data parse.
- AC-3 (falsifiable): both descriptors are frozen and serialisable.

**Honest limits (why this lands as PARTIAL):** executing real QEMU/Renode binaries is
outside this environment; the plan composition and the data boundary are verified
here, with execution verification pending a runtime-evidence run.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TGT-020** | The tool shall execute the test harness on an instruction-set simulator, verified against QEMU and Renode. | `src/ectt/ext/simulator.py` (`SimulatorDescriptor`, `qemu_descriptor`, `renode_descriptor`, `plan_simulator_run`, `consume_simulator_output`, `UnknownSimulatorError`), `src/ectt/ext/errors.py` (`ExtError`), re-exported by `src/ectt/ext/__init__.py` | **Guarantee:** both documented simulator families carry declarative frozen descriptors — QEMU (`qemu-system-arm -M <machine> -nographic -kernel <harness>`) and Renode (`renode --disable-xwt` with platform script and `LoadELF`) — with exact command composition per harness binary and custom machine selection; unknown families, blank machines, templates without the `{harness}`/`{machine}` slots and empty harness paths are named errors; simulator output is consumed strictly through the WP-SEC-07 untrusted boundary (`mark_untrusted` → `parse_target_output`), so nothing a simulator prints is executed or interpreted beyond the data parse.<br><br>**This is why WP-EXT-01 lands as PARTIAL:** executing real QEMU/Renode binaries is outside this environment; plan composition and the data boundary are verified here, execution verification pending a runtime-evidence run.<br><br>**Test evidence:** `tests/ext/test_simulator.py` — `test_both_documented_simulator_families_have_descriptors`, `test_qemu_command_composed_with_machine_and_harness`, `test_renode_command_composed_with_script_and_harness`, `test_custom_machine_selection`, `test_unknown_family_is_named_error`, `test_blank_machine_is_named_error`, `test_template_without_slots_is_named_error`, `test_empty_harness_is_named_error`, `test_simulator_output_consumed_as_untrusted_data`, `test_descriptors_are_frozen_and_serialisable` (10 tests, green in the WP-EXT-01 gate run: 783 passed, 4 skipped). |

## Standing summary

WP-EXT-01 is recorded as **PARTIAL** in the ledger: the plan composition and the
untrusted-data boundary are covered with test evidence; against-real-simulator
execution is pending a runtime-evidence run.

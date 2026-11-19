# Verification Analysis Note — WP-EXT-02 (Hardware Execution and Flashing via Debug Probe)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-EXT-02. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-TGT-030 (M, P3, T) and TOOL-TGT-040 (M, P3, T).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-TGT-030): debug-probe execution is planned from a
  declarative frozen probe descriptor (documented probe families: OpenOCD, pyOCD,
  J-Link) — the composed plan carries the probe command, the target and the harness
  path, deterministically; an unknown probe family or blank target is a named error.
- AC-2 (falsifiable, from TOOL-TGT-040): flashing is planned through the same
  descriptors with the documented flashing-tool support — OpenOCD, pyOCD and J-Link
  each get a concrete flash command composition; a harness path is required.

**Honest limits (why this lands as PARTIAL):** composing the plans and validating
them against the documented tools is the verified core; executing real probes against
physical hardware is outside this environment and is recorded as pending a
runtime-evidence run.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TGT-030** | The tool shall execute the test harness on physical target hardware via a debug probe. | `src/ectt/ext/probe.py` (`ProbeDescriptor`, `plan_probe_run`, `ProbePlan`, `UnknownProbeError`), re-exported by `src/ectt/ext/__init__.py` | **Guarantee:** probe execution is planned from declarative frozen descriptors for the documented probe families (OpenOCD, pyOCD, J-Link) — the plan carries the composed run command, target and harness path, deterministically serialisable; unknown families, templates without `{target}`/`{harness}` slots and blank targets/harnesses are named errors.<br><br>**This is why WP-EXT-02 lands as PARTIAL:** plan composition is verified here; executing against physical hardware with real probes is outside this environment and is recorded as pending a runtime-evidence run.<br><br>**Test evidence:** `tests/ext/test_probe.py` — `test_probe_run_plan_composed`, `test_unknown_probe_family_is_named_error`, `test_blank_target_or_harness_are_named_errors`, `test_template_without_slots_is_named_error`, `test_descriptors_are_frozen_and_deterministic`. |
| **TOOL-TGT-040** | The tool shall support flashing target hardware via OpenOCD, pyOCD, and J-Link. | `src/ectt/ext/probe.py` (`plan_flash`, `openocd_descriptor`, `pyocd_descriptor`, `jlink_descriptor`, `PROBE_FAMILIES`) | **Guarantee:** all three documented flashing tools have concrete flash command compositions — OpenOCD (`program <harness> verify reset exit`), pyOCD (`pyocd flash --target <target> <harness>`), J-Link (`-device <device> -if swd` with command file) — each carrying target and harness from the plan inputs; blank target or harness refuses the plan with a named error.<br><br>**Test evidence:** `tests/ext/test_probe.py` — `test_documented_flashing_tools_have_descriptors`, `test_flash_plan_composed_for_each_tool` (7 tests total, green in the WP-EXT-02 gate run: 797 passed, 4 skipped). |

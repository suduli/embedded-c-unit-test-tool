# Verification Analysis Note — WP-BLD-03 (Cross-Compiled Target Build)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-BLD-03. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-TGT-010 (M, P3, T) — *The tool shall build the test harness for a
cross-compiled embedded target* — composed from the WP-BLD-01 planner, the WP-TCH-03
cross configurations and the WP-TCH-04 metric gate.

## Acceptance criteria

- AC-1 (falsifiable): a cross build plan composes, per harness artifact, the exact
  cross-compile command line from the cross compiler configuration — the cross
  executable name, the configuration's debug flags, the coverage flags of only the
  requested kinds (gated by TOOL-TCH-060), the compile-only and output conventions —
  deterministically ordered, with the output path per artifact.
- AC-2 (falsifiable): requesting a coverage kind the cross configuration does not
  declare is refused with the named metric error (no silent flag injection); the
  plan is deterministic and serialisable.
- AC-3 (falsifiable): artifact staleness carries over from WP-BLD-01: artifacts that
  are up to date under their recorded inputs are not re-planned for compilation.

**Honest limits (why this lands as PARTIAL):** the command *composition* is the
falsifiable core verified here; executing a real cross toolchain (compiling a real
harness with `arm-none-eabi-gcc`) is outside this environment and is recorded as
pending a runtime-evidence run, consistent with WP-TCH-03.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TGT-010** | The tool shall build the test harness for a cross-compiled embedded target. | `src/ectt/bld/crossbuild.py` (`plan_cross_build`, `CrossBuildPlan`, `CrossBuildCommand`), fed by the WP-TCH-03 cross configurations, gated by the WP-TCH-04 metric gate, filtered by the WP-BLD-01 planner; re-exported by `src/ectt/bld/__init__.py` | **Guarantee:** per harness artifact the plan composes the exact cross-compile command line from the cross configuration — cross executable name (`arm-none-eabi-gcc`), debug flags, coverage flags of only the requested declared kinds, compile-only flag, optimization flags, output convention and path under the toolchain's build root — deterministically ordered and serialisable. Undeclared metrics are refused with the named metric error (no silent flag injection); WP-BLD-01 staleness carries over (up-to-date artifacts are not re-planned); host configurations plan identically through the same path.<br><br>**This is why WP-BLD-03 lands as PARTIAL:** executing the composed commands against a real cross toolchain is outside this environment (consistent with WP-TCH-03) and is recorded as pending a runtime-evidence run.<br><br>**Test evidence:** `tests/bld/test_crossbuild.py` — `test_cross_commands_use_the_cross_executable`, `test_command_composition_is_exact_and_deterministic`, `test_coverage_flags_included_for_declared_kinds`, `test_undeclared_metric_refused`, `test_up_to_date_artifacts_not_replanned`, `test_plan_is_frozen_and_serialisable`, `test_host_config_also_plans` (7 tests, green in the WP-BLD-03 gate run: 759 passed, 4 skipped). |

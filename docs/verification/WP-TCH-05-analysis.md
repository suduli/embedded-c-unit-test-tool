# Verification Analysis Note — WP-TCH-05 (Multi-Toolchain Builds and Reproducible Containers)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-TCH-05. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-TCH-080 (S, P3, T) and TOOL-TCH-090 (S, P3, D).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-TCH-080): one multi-toolchain build plan builds the
  same suite for every named toolchain, each in its own isolated build directory
  (`<root>/<toolchain>/`), with the per-toolchain command lines composed from each
  toolchain's configuration; the plan is deterministic; a duplicate toolchain name is
  a named error.
- AC-2 (falsifiable, from TOOL-TCH-090): a reproducible container specification is
  generated deterministically from supplied data — pinned base image with digest and
  the validated toolchain roster — as version-controllable text; no digest is ever
  invented (missing digest data is a named error).

**Honest limits (why this lands as PARTIAL):** TOOL-TCH-090's demonstration evidence
is the generated container specification; building and validating the actual images
happens in CI and is recorded as pending a runtime-evidence run.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TCH-080** | The tool shall support building the same test suite for multiple toolchains in isolated build directories within one invocation. | `src/ectt/tch/multibuild.py` (`plan_multi_toolchain_builds`, `MultiBuildPlan`, `DuplicateToolchainError`), composing WP-BLD-03's per-toolchain command planner; re-exported by `src/ectt/tch/__init__.py` | **Guarantee:** one plan covers every named toolchain — the same suite specs planned per toolchain with commands composed from each toolchain's own configuration, each isolated in `<root>/<toolchain>/`; duplicate toolchain names raise `DuplicateToolchainError`, unknown names surface the registry's named error; the plan is deterministic regardless of toolchain ordering (verified by reversing the input).<br><br>**Test evidence:** `tests/tch/test_multibuild.py` — `test_same_suite_planned_per_toolchain_in_isolated_dirs`, `test_per_toolchain_commands_use_per_toolchain_executables`, `test_duplicate_toolchain_is_named_error`, `test_unknown_toolchain_is_named_error`, `test_multi_plan_is_deterministic`. |
| **TOOL-TCH-090** | The tool shall provide reproducible container images containing validated host and cross toolchains. *(Method D)* | `src/ectt/tch/multibuild.py` (`container_spec`, `ContainerSpecError`) | **Guarantee:** the container specification is generated deterministically from supplied data — base image pinned as `FROM image@sha256:<digest>` (a missing digest is a named error: reproducibility is never claimed without one) plus the sorted validated toolchain roster — as version-controllable text with the independent-rebuild statement (TOOL-SEC-030 linkage). Identical inputs, any toolchain order → byte-identical spec.<br><br>**This is why WP-TCH-05 lands as PARTIAL:** the demonstration evidence here is the generated specification; building and validating the actual images happens in CI and is recorded as pending a runtime-evidence run.<br><br>**Test evidence:** `tests/tch/test_multibuild.py` — `test_container_spec_pins_base_image_by_digest`, `test_container_spec_is_deterministic`, `test_container_spec_without_digest_is_named_error`. |

## Standing summary

WP-TCH-05 is recorded as **PARTIAL** in the ledger: TOOL-TCH-080 is covered with test
evidence; TOOL-TCH-090's container *specification* generation is covered and its image
build/validation is pending the CI runtime-evidence run.

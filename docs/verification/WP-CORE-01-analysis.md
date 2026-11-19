# WP-CORE-01 — Verification analysis: determinism, source immutability and output confinement

Lane: VERIFY (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

Recorded in PLAN-001 §5.4 (verbatim):

> Two runs from identical inputs on different machines produce byte-identical generated artifacts; a
> write attempted outside the configured output root fails and is reported; no user source file's
> mtime or content changes across a full run.

## Requirements owned → implementation → test evidence

| Requirement (SRS-001) | Implementation | Test evidence (all run green on this worktree, 2026-11-18) |
|---|---|---|
| **TOOL-NFR-060** — all tool outputs deterministic and reproducible given identical inputs | `src/ectt/core/determinism.py` (canonical JSON, stable IDs, clock protocol); `src/ectt/core/fs.py` (sorted writes) | `tests/core/test_determinism.py` (35 tests incl. `test_clock_protocol_conformance`, `test_system_clock_returns_utc`, `test_fixed_clock_frozen_and_advance`, `test_stable_id_*`), `tests/core/test_determinism_coverage.py` (18 tests), plus the shared integration test below — 35+ test names tagged `verifies: TOOL-NFR-060` |
| **TOOL-NFR-070** — tool shall not modify user source files | `src/ectt/core/fs.py` read-only source tree access | `tests/core/test_fs.py::test_source_tree_read_only_access`, `::test_source_tree_mutating_operations_raise_error`, `::test_source_tree_confinement`, `::test_source_tree_invalid_root` (+9 more) — 13 test names tagged |
| **TOOL-NFR-080** — generated files written to designated output directory separable from user source | `src/ectt/core/fs.py` output-root confinement | `tests/core/test_fs.py::test_output_root_default_path`, `::test_overlap_refusal_equal`, `::test_overlap_refusal_output_contained_in_source`, `::test_overlap_refusal_source_contained_in_output` (+24 more) — 28 test names tagged |
| **TOOL-PRJ-050** — project data stable under version control; meaning-preserving ops don't change content; deterministic file ordering | `src/ectt/prj/project.py`, `src/ectt/prj/yaml_adapter.py` (+ core determinism primitives) | `tests/core/test_determinism.py::test_canonical_json_sorted_keys` + 25 more tagged tests across `tests/core/` and `tests/prj/` (`test_project.py`, `test_yaml_adapter.py`, `test_migration.py`) |
| **TOOL-PRJ-080** — generated artifacts distinguishable from user-authored artifacts | `src/ectt/core/fs.py` (`.gitignore` in output root, separation enforcement) | `tests/core/test_fs.py::test_first_use_initialization`, `::test_output_root_recreates_missing_gitignore`, `tests/core/test_pipeline_reproducibility.py::test_byte_identical_across_differing_subprocesses` — 3 test names tagged |

## Exit-criterion element mapping

| §5.4 element | Evidence | Status |
|---|---|---|
| Two runs from identical inputs on different machines produce byte-identical generated artifacts | `tests/core/test_pipeline_reproducibility.py::test_byte_identical_across_differing_subprocesses` runs the fixture pipeline twice in separate subprocesses varying PYTHONHASHSEED (0 vs 47291), cwd, absolute output-root path, TZ (UTC vs America/New_York) and locale, then asserts SHA-256 manifests of all generated artifacts are identical. This is the automatable subset of "different machines" (environment deltas a machine difference would carry); a true cross-machine run remains an owner acceptance step, not covered by automation. | met (with stated scope) |
| A write attempted outside the configured output root fails and is reported | `tests/core/test_fs.py` confinement tests: `test_source_tree_confinement`, `test_overlap_refusal_*` (equal, output⊆source, source⊆output), `test_write_outside_output_root_rejected` class; `test_confinement_symlink_escape` **skipped on this machine** (WinError 1314 — symlink creation privilege; pre-existing at baseline, environment-dependent, not a failure) | met (1 privilege-gated test skipped, recorded) |
| No user source file's mtime or content changes across a full run | `test_byte_identical_across_differing_subprocesses` asserts mtime_ns + sha256 unchanged for every fixture source file; `test_source_tree_read_only_access`, `test_source_tree_mutating_operations_raise_error` | met |

## Test run

```
tests/core/test_determinism.py tests/core/test_determinism_coverage.py tests/core/test_fs.py
tests/core/test_fs_coverage.py tests/core/test_pipeline_reproducibility.py tests/prj/test_project.py
tests/prj/test_yaml_adapter.py tests/prj/test_migration.py tests/ana/test_frontend.py
tests/ana/test_types.py
→ 130 passed, 1 skipped (test_confinement_symlink_escape, WinError 1314) — stable across 3 runs
```

Full suite at gates: 399 passed, 4 skipped — same as baseline.

## Gaps / not covered

- True cross-machine (distinct hardware) byte-identity: not automatable here; the subprocess
  environment-delta test is the standing evidence. Owner acceptance may add a two-machine run.
- Symlink-escape confinement: test exists and is skipped only for lack of Windows symlink privilege;
  on a privilege-holding machine it runs.

## Result

**DONE** — recorded §5.4 exit criterion verified against named, passing tests for every owned
requirement; the two caveats above are recorded, neither blocks the criterion.

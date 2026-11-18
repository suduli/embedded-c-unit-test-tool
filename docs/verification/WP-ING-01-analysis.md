# WP-ING-01 — Verification analysis: compilation database ingestion

Lane: VERIFY (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).
Companion note: `docs/verification/WP-ING-01-inspection.md` (inspection evidence for the
documentation-verified requirement TOOL-ING-040).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-ING-01. The
four owned SRS-001 requirements (texts below) are the standing bar; all four are test-verifiable
(*T*) except TOOL-ING-040 (*D*, documentation) which has both documentation-presence and
scratch-configure execution tests.

## Requirement → implementation → test evidence

| Requirement (SRS-001) | Implementation | Test evidence (re-run green 2026-11-18) |
|---|---|---|
| **TOOL-ING-010** — accept `compile_commands.json` as primary project description | `src/ectt/ing/compdb_adapter.py` | 14 tagged tests in `tests/ing/test_compdb_adapter.py`: happy paths, missing-file/malformed-JSON named errors, empty-database, non-list root |
| **TOOL-ING-020** — parse both `command` (string) and `arguments` (array) forms, normalize internally | `compdb_adapter.py` normalizer | `test_compdb_adapter.py::test_command_and_arguments_normalize_to_identical_shape`, `::test_missing_command_and_arguments_raises_named_error` + 9 more |
| **TOOL-ING-030** — extract per-TU source path, working dir, include paths, definitions, standard, compiler invocation | `compdb_adapter.py` → `src/ectt/ing/model.py` | `::test_project_root_path_confinement_and_normalization`, `::test_reject_escaping_source_path_when_confined` + extraction-field assertions in the happy-path tests; 11 tagged total |
| **TOOL-ING-040** — document and support CMake `CMAKE_EXPORT_COMPILE_COMMANDS` as recommended path | `src/ectt/ing/cmake.py` (`generate_compdb_via_cmake`, `CMAKE_EXPORT_DOCUMENTATION`) | `tests/ing/test_cmake.py::test_cmake_documentation_presence`, `::test_cmake_scratch_configure_happy_path` (real cmake scratch-configure), in-source-build refusal + 7 more; 10 tagged |

## Test run

```
tests/ing → 83 passed, 0 skipped in 0.54s
full suite → 447 passed, 4 skipped (baseline 4)
```

## Gaps / not covered

- None. TOOL-ING-040's scratch-configure test exercises a real CMake when available on PATH; the
  documentation-presence test keeps the recommended-path text in the source regardless.

## Result

**DONE** — all four owned requirements carry named, passing tests; the ingestion adapter,
normalisation and CMake path are directly evidenced.

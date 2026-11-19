# WP-PRJ-01 — Verification analysis: plain-text schema-versioned project store

Lane: VERIFY (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).
Companion note: `docs/verification/WP-PRJ-01-inspection.md` (inspection evidence per requirement).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-PRJ-01. The
five owned SRS-001 requirements are the standing bar (texts quoted in the table); the ADR-sensitive
part of this package (ADR-002 project data format) is **Accepted**, so the decision-free
verification below does not reopen any decision.

## Requirement → implementation → test evidence

| Requirement (SRS-001) | Implementation | Test evidence (re-run green 2026-11-18) |
|---|---|---|
| **TOOL-PRJ-010** — project data in documented, plain-text, human-readable formats | `src/ectt/prj/yaml_adapter.py` (`RestrictedYamlAdapter`) | `tests/prj/test_yaml_adapter.py::test_yaml_typing_hazards_roundtrip` + 6 more; comment-preservation and canonical-key-ordering tests |
| **TOOL-PRJ-020** — every project data file carries an explicit schema version | `src/ectt/prj/model.py::dispatch_schema_version`, `yaml_adapter.py` | `tests/prj/test_schema_dispatch.py::test_schema_version_supported`, `::test_schema_version_absent`, + 3 more; first-key ordering via `test_yaml_adapter.py::test_canonical_key_ordering` |
| **TOOL-PRJ-070** — user source referenced by relative path; relocation/clone safe | `src/ectt/prj/paths.py::validate_project_path` | `tests/prj/test_paths.py` (9 tests incl. absolute/drive/escape rejection), `tests/prj/test_project.py::test_project_relocation`; 2 symlink-privilege skips in `test_references.py` (WinError 1314 class, pre-existing at baseline, environment-dependent) |
| **TOOL-UIX-320** — all state in plain-text version-controllable files; GUI never the sole source | `src/ectt/prj/project.py::Project.save_file` | `tests/prj/test_project.py::test_project_create_and_no_metadata_leak` |
| **TOOL-CIC-080** — all configuration expressible in version-controlled files; none GUI-only | `src/ectt/prj/project.py::Project.create/open` | `tests/prj/test_project.py::test_project_relocation` (headless reload of full configuration) |

## Test run

```
tests/prj → 79 passed, 2 skipped (symlink privilege, pre-existing) in 0.67s
full suite → 447 passed, 4 skipped (baseline 4)
```

## Gaps / not covered

- None new. The two symlink-privilege skips are the standing Windows-environment limitation also
  recorded under WP-CORE-01 (same WinError 1314 class); on a privilege-holding machine they run.

## Result

**DONE** — every owned requirement has named, passing tests; the plain-text / schema-version /
relative-path / no-GUI-state guarantees are all directly evidenced. No ADR reopened.

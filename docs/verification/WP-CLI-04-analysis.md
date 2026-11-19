# WP-CLI-04 — Analysis: reference CI pipelines and artifact caching

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-CLI-04.
Derived from the SRS-001 texts (TOOL-CIC-050 *D*, TOOL-CIC-070 *T*):

- **AC-1 (TOOL-CIC-050):** reference pipeline configurations exist for **both** GitHub Actions and
  GitLab CI, as code artifacts with tests, each invoking the tool through its documented
  non-interactive entry (`python -m ectt.cli`) and reacting to the stable exit codes
  (TOOL-CIC-030 table).
- **AC-2 (TOOL-CIC-070):** the tool defines its **cacheable artifact set** — the ingestion and
  analysis outputs carried across runs — as machine-readable data (`cacheable_artifacts()`), and
  both reference templates cache exactly that set with a key derived from the compilation database.
- **AC-3:** both templates are syntactically valid YAML (parsed in tests), so a released reference
  cannot be broken silently.
- **AC-4 (scope boundary):** executing the pipelines on real CI infrastructure is the
  demonstration the *D* verification method asks for at release time (owner/CI work, out of scope
  for an unattended run); the container image the pipelines would use is WP-PKG-05 (INS-090).

## Implementation

- `src/ectt/cli/ci_reference.py` — `GITHUB_ACTIONS_PIPELINE`, `GITLAB_CI_PIPELINE` (valid YAML
  documents), `cacheable_artifacts()` (ingestion/analysis artifact path patterns inside the
  project output area), and `cache_key_source` documenting the key derivation
  (`compile_commands.json` digest).
- `tests/cli/test_ci_reference.py` — AC checks (YAML parse, both platforms present, cache paths
  equal the artifact set, exit-code fidelity, documented commands).

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/cli/`) |
|---|---|---|
| TOOL-CIC-050 | `ci_reference.py` templates | `test_ci_reference.py::test_both_reference_pipelines_exist_and_parse`, `::test_pipelines_invoke_documented_cli_entry`, `::test_pipelines_react_to_stable_exit_codes` |
| TOOL-CIC-070 | `cacheable_artifacts()` + template cache blocks | `::test_cacheable_artifacts_cover_ingestion_and_analysis`, `::test_templates_cache_exactly_the_artifact_set`, `::test_cache_key_is_derived_from_compilation_database` |

## Not covered by this increment

- Live CI demonstration (TOOL-CIC-050 method *D*) — needs real infrastructure; recorded as owner
  follow-up.
- Versioned container image for CI — WP-PKG-05.
- CI sharding and report merge — WP-CLI-05 (TOOL-CIC-060).

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.
**PARTIAL**: templates + cache contract implemented and tested; live-pipeline demonstration and
real container image remain (owner / WP-PKG-05).

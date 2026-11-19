# WP-QUA-05 — Analysis: development process and change control documentation

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-QUA-05.
Derived from the SRS-001 text (TOOL-QUA-070, method *I*):

- **AC-1:** a development-process statement artifact exists with the three required sections —
  development process, change control, defect management — as a deterministic, rendered document.
- **AC-2:** every claim cites a repository artifact that exists (plan and gate scripts, CI
  workflows, PLAN-001 §9 change control, review evidence, ADRs), so a user can assess the process
  from the artifacts themselves.
- **AC-3:** unsourced claims are refused (fail-closed `ProcessDocumentationError`), and no
  process-compliance claim is made that the repository does not evidence.

## Implementation

- `src/ectt/qua/process_documentation.py` — `ProcessClaim` (statement + citation), the three
  sections populated strictly from recorded repository facts, `render()` deterministic output.
- `tests/qua/test_process_documentation.py` — the AC checks.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/qua/`) |
|---|---|---|
| TOOL-QUA-070 (document process, change control, defect management) | `process_documentation.py` + `default_documentation()` | `test_process_documentation.py::test_document_has_the_three_required_sections`, `::test_every_claim_cites_an_existing_repository_artifact`, `::test_render_is_deterministic`, `::test_unsourced_claims_are_refused`, `::test_no_compliance_claim_is_made` |

## Not covered by this increment

- Formal process-certification statements (part of the classification package, WP-QUA-01) — none
  claimed here. The known-error list per release is WP-QUA-04.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.

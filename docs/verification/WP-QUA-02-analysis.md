# WP-QUA-02 — Analysis: tool operational requirements specification

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-QUA-02.
Derived from the SRS-001 text (TOOL-QUA-020, method *I*):

- **AC-1:** a documented **Tool Operational Requirements specification** exists as a code artifact
  with a deterministic renderer — the accompanying document TOOL-QUA-020 asks for.
- **AC-2:** it defines **intended use** — recorded as `OPEN` pending the tool-classification
  decision (WP-QUA-01, ADR-sensitive); the section structure and the non-claim sentence exist, the
  classification is never chosen here.
- **AC-3:** it defines the **operating environment** with every fact traceable to a recorded SRS
  requirement id (platform, offline, no-admin).
- **AC-4:** it lists **known limitations** with each entry citing repository-recorded evidence
  (verification notes), and the list includes the limitations recorded by this run.
- **AC-5:** the renderer refuses environment/limitation entries without traceable sources
  (fail-closed, same discipline as WP-QUA-07's overclaim guard).

## Implementation

- `src/ectt/qua/operational_requirements.py` — `OperatingEnvironmentFact` (statement + SRS id),
  `KnownLimitation` (statement + evidence citation), `OperationalRequirements` (intended-use OPEN
  marker, environment, limitations), `default_specification()` from recorded facts,
  `render()` deterministic output, `SpecificationError` on unsourced entries.
- `tests/qua/test_operational_requirements.py` — the AC checks.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/qua/`) |
|---|---|---|
| TOOL-QUA-020 (documented TOR spec: intended use, operating environment, known limitations) | `operational_requirements.py` + `default_specification()` | `test_operational_requirements.py::test_specification_has_the_three_required_sections`, `::test_intended_use_is_open_not_decided`, `::test_environment_facts_cite_srs_ids`, `::test_limitations_cite_repository_evidence`, `::test_render_is_deterministic`, `::test_unsourced_entries_are_refused` |

## Not covered by this increment

- The classification-dependent intended-use wording (WP-QUA-01 decision) and the certification
  package (WP-QUA-03/05/06/08). The limitation list reflects this run's state; owning merges
  update it.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.

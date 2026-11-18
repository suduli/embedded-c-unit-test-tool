# WP-MIG-06 — Analysis: coexistence with another tool on one project

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-MIG-06.
Derived from the SRS-001 text (TOOL-MIG-070) and the recorded design (SDD-003 §2 write-authority
section: "Coexistence (TOOL-MIG-070) protects existing artifacts in both roots"):

- **AC-1:** the tool can **detect** pre-existing foreign artifacts in the authored-state side of
  the project root (files ectt does not own) and report them (path) without modifying them.
- **AC-2:** ectt's own writes on a shared project (project-store creation, output-root
  initialization) leave every foreign artifact **byte-identical** — proven by before/after tree
  snapshots over both roots: no interference.
- **AC-3:** ectt's owned authored-state set is explicit data (the `ectt.project` marker);
  everything else in the project root is treated as foreign and protected by default. The output
  root is protected byte-level via snapshots rather than an output-name registry.
- **AC-4 (scope boundary):** import/adapters for specific third-party tools are the other CMP-MIG
  packages (WP-MIG-01..05, WP-MIG-07); coexistence here is the non-interference contract only.

## Implementation

- `src/ectt/mig/coexistence.py` — `ForeignArtifact`, `OWNED_PROJECT_PATHS`,
  `scan_foreign_artifacts(project_root, output_root)` (deterministic sorted report),
  `snapshot_tree`/`assert_no_interference` (byte-level before/after comparison helper).
- `src/ectt/mig/__init__.py` — package exports.
- `tests/mig/test_coexistence.py` — AC checks against real `Project.create` +
  `OutputRoot` initialization with foreign artifacts planted in both roots.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/mig/`) |
|---|---|---|
| TOOL-MIG-070 (operate without interfering with another tool's artifacts) | `coexistence.py` scan + no-interference assert | `test_coexistence.py::test_ectt_writes_leave_foreign_artifacts_byte_identical`, `::test_foreign_artifacts_are_reported_not_modified`, `::test_output_root_initialization_preserves_foreign_files`, `::test_scan_reports_deterministically_sorted`, `::test_owned_paths_are_explicit`, `::test_no_interference_detects_a_modified_foreign_file` |

## Not covered by this increment

- Specific third-party adapters (Ceedling, CMock, commercial tools) — WP-MIG-02/04/05.
- Coexistence inside the *output root* of a foreign tool writing there concurrently at runtime —
  the design assigns write authorities per operation (DSN-CORE-060); cross-tool runtime
  arbitration is not a named requirement.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.

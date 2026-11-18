# WP-QUA-06 — Analysis: standards objective mapping

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-QUA-06.
Derived from the SRS-001 text (TOOL-QUA-080, method *I*):

- **AC-1:** a standards-objective mapping artifact exists for the five named standards
  (ISO 26262, IEC 61508, IEC 62304, EN 50128, DO-178C), with a deterministic renderer carrying a
  section per standard.
- **AC-2:** every mapping row cites **both** the tool capability's evidence (a repository
  artifact) and the standard clause id it relates to; rows missing either are refused.
- **AC-3:** rows never claim satisfaction or compliance — only "addressed by capability …
  (evidence …)"; a satisfaction-claim token in a row is refused (fail-closed, DSN-QUA-070
  discipline).
- **AC-4:** the default mapping is **empty** and the document says so explicitly: populating it is
  the classification-dependent work (ADR-sensitive, WP-QUA-01/WP-QUA-02), not inventable by an
  unattended run.

## Implementation

- `src/ectt/qua/standards_mapping.py` — `ObjectiveMapping` (standard, clause, capability claim,
  evidence), `ObjectiveMappingError`, `STANDARDS` (the five names), `default_mapping()` (empty,
  explicitly stated), `render()`.
- `tests/qua/test_standards_mapping.py` — the AC checks.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/qua/`) |
|---|---|---|
| TOOL-QUA-080 (mapping between capabilities and the five standards' verification objectives) | `standards_mapping.py` | `test_standards_mapping.py::test_document_has_a_section_per_named_standard`, `::test_every_row_cites_clause_and_evidence`, `::test_rows_cannot_claim_satisfaction`, `::test_default_mapping_is_empty_and_stated`, `::test_unsourced_rows_are_refused`, `::test_render_is_deterministic` |

## Not covered by this increment

- The populated mapping itself (ADR-sensitive: which objectives the tool's capabilities address
  depends on the qualification context and classification). The structure accepts rows from the
  owning merge once the classification decision exists.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.

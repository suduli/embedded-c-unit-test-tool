# WP-QUA-08 — Analysis: templates for user tool qualification artifacts

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-QUA-08.
Derived from the SRS-001 text (TOOL-QUA-100, method *I*):

- **AC-1:** fill-in templates exist for the qualification artifact kinds the package names:
  qualification plan, tool classification record, known-error list, qualification test report —
  each with a named section structure and a deterministic renderer.
- **AC-2:** templates contain **placeholders only** (`<<...>>` markers) — no fabricated factual
  content; each section carries at least one placeholder so the user fills their own context.
- **AC-3:** no template claims compliance/satisfaction/certification on the user's behalf
  (overclaim tokens refused).
- **AC-4 (ADR-sensitive boundary):** the classification-dependent prefill is left empty; the
  templates carry the placeholders the classification decision (WP-QUA-01) will fill.

## Implementation

- `src/ectt/qua/templates.py` — `QUALIFICATION_TEMPLATES` (the four named skeletons),
  `render_template(name)`, `TemplateError` (unknown name, placeholder-free section, claim token).
- `tests/qua/test_templates.py` — the AC checks.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/qua/`) |
|---|---|---|
| TOOL-QUA-100 (templates for the user's own qualification artifacts) | `templates.py` | `test_templates.py::test_all_four_templates_exist_and_render`, `::test_every_template_section_has_placeholders`, `::test_templates_contain_no_fabricated_facts`, `::test_templates_claim_no_compliance`, `::test_render_is_deterministic`, `::test_unknown_template_is_refused` |

## Not covered by this increment

- Pre-filled classification content (ADR-sensitive, WP-QUA-01) and standard-specific objective
  rows (WP-QUA-06's mapping). The templates carry placeholders for both.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.

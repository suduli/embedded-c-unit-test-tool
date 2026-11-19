# WP-QUA-07 — Analysis: explicit statement of what is and is not qualified

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

Recorded in PLAN-001 §5.4 (verbatim):

> Documentation states, in one place, what qualification evidence is provided and what remains the
> user's responsibility, and no other document claims more.

Restated with the SRS-001 text (TOOL-QUA-090: no certification/qualification claims the tool does
not hold):

- **AC-1:** one canonical, deterministically renderable qualification-scope statement exists as a
  code artifact — the single place this content lives.
- **AC-2:** its *provided* section names only evidence that exists in this repository, each item
  carrying a citation to the verification note that holds it.
- **AC-3:** its *user responsibility* section is explicit and non-empty.
- **AC-4:** the statement asserts no certification and no qualification class it does not hold;
  the renderer refuses any provided item that claims certification/qualification without an
  explicit non-claim marker (fail-closed overclaim guard, SDD-001 DSN-QUA-070 row).
- **AC-5 (ADR-sensitive boundary):** the formal tool-classification decision (TOOL-QUA-010,
  WP-QUA-01) is **not** made here; the statement's classification line is a recorded open question,
  not a choice. Only the decision-free mechanism and evidence-backed content are implemented.

## Implementation

- `src/ectt/qua/qualification_scope.py` — `ProvidedItem` (claim + evidence citation),
  `QualificationScope` (provided items, user responsibilities, classification placeholder marked
  `OPEN`), `default_scope()` built strictly from this repository's `docs/verification/*.md` notes,
  `render()` deterministic text output, overclaim guard raising `OverclaimError`.
- `tests/qua/test_qualification_scope.py` — the AC checks.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/qua/`) |
|---|---|---|
| TOOL-QUA-090 / §5.4 criterion | `qualification_scope.py` + `default_scope()` | `test_qualification_scope.py::test_statement_is_single_deterministic_render` (AC-1), `::test_every_provided_item_cites_existing_verification_note` (AC-2), `::test_user_responsibility_section_is_explicit` (AC-3), `::test_no_certification_claim_is_present` + `::test_renderer_refuses_uncited_certification_claim` (AC-4), `::test_classification_is_recorded_as_open_not_decided` (AC-5) |

## Not covered by this increment

- The classification decision itself (WP-QUA-01, ADR-sensitive) and the full qualification package
  (WP-QUA-02/03/05/06/08). The statement's evidence list is current as of this run; new evidence
  updates `default_scope()` in the owning merge.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.

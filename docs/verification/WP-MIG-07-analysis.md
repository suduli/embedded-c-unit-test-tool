# Verification Analysis Note — WP-MIG-07 (Migration Assessment Mode)

Analysis evidence for requirements verified under WP-MIG-07. Status: **implemented**
(evidence-backed) for the two import adapters that exist (Ceedling project, mapped
tabular export). Executor: Claude (lane B, 2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory):

- **AC-1 (expected fidelity before migrating):** assessing a legacy source reports, per
  artifact, converted / converted-with-loss / not-converted counts and percentages, each
  with its denominator; the WP-MIG-05 fidelity report is embedded unchanged.
- **AC-2 (manual effort):** every loss finding becomes one manual item naming the artifact,
  the kind of finding and the action a person takes; effort is reported as item counts by
  kind and never as a duration.
- **AC-3 (TOOL-MIG-110):** deferred compound structures are listed with location and appear
  as manual items by decision (author as a C-source test after migration).
- **AC-4 (states, STATE TRANSITION):** exactly three outcomes — `ready`, `needs_manual_work`,
  `not_assessable` — reached from the findings: no loss and no deferred structure gives
  `ready`; any manual item or deferred structure gives `needs_manual_work`; legacy input
  that cannot be read gives `not_assessable` with the reason.
- **AC-5 (fail-safe, read-only):** an unreadable legacy source is a finding, not an
  exception; the assessment never modifies the legacy project.
- **AC-6 (determinism):** the assessment document is byte-identical across runs.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-MIG-090** | The tool shall provide a migration assessment mode that analyses an existing project and reports the expected fidelity and manual effort of migration before migration is attempted. | `src/ectt/mig/assessment.py` (`assess_ceedling_project`, `assess_mapped_csv`, `Assessment`, `ManualItem`, `OUTCOMES`, `dump_assessment`) | **AC-1:** `test_a_clean_export_is_ready_with_full_fidelity`, `test_a_messy_export_reports_expected_fidelity_with_denominators`, `test_ceedling_assessment_reports_losses_per_artifact`, `test_assessment_document_is_deterministic_and_embeds_the_fidelity_report`. **AC-2:** `test_manual_effort_is_one_item_per_finding_with_an_action`, `test_effort_is_counted_never_timed`, `test_findings_without_a_known_action_fall_back_to_review`. **AC-3:** `test_deferred_compound_structures_are_listed_with_location`. **AC-4:** `test_a_clean_export_is_ready_with_full_fidelity`, `test_a_ceedling_project_without_losses_is_ready`, `test_a_messy_export_reports_expected_fidelity_with_denominators`, `test_outcomes_are_a_closed_vocabulary`, `test_unreadable_exports_are_findings_not_exceptions` (3 cases), `test_unreadable_ceedling_projects_are_findings_not_exceptions` (3 cases). **AC-5:** `test_assessment_never_modifies_the_legacy_project`, the two unreadable-source tests above. **AC-6:** `test_assessment_document_is_deterministic_and_embeds_the_fidelity_report`. |

## Design notes

- **Assessment is a dry run of the import adapters**, so the fidelity it predicts is the
  fidelity the import will deliver; there is no second model of "what would happen" to
  drift from the real one.
- **No time estimates.** Person-hours for a migration depend on facts the tool cannot see
  (who edits, how fast). Counting items by kind is supportable; an hour figure would be
  made up, so it is not produced.
- **`not_assessable` instead of raising.** A migration assessment's job is to inform a
  decision about legacy material, so unreadable material is the answer, not a crash.
  Mapping errors supplied by the caller are reported the same way, with their reason.

## Not covered

- Assessment of adapters that do not exist yet (commercial tool formats, coverage data).
  They plug in by providing a fidelity report; `_assessed` turns any report into an
  assessment.
- The assessment is not yet a registered interchange format in `ectt.mig.formats`
  (its JSON form is deterministic and carries the embedded fidelity report version).
- CLI and GUI presentation of an assessment; sampling very large legacy projects.
- Assessing coexistence risk (WP-MIG-06) is separate.

# Verification Analysis Note — WP-MIG-05 (Import Fidelity Reporting)

Analysis evidence for requirements verified under WP-MIG-05. Status: **implemented**
(evidence-backed) for the two import adapters that exist (mapped CSV, Ceedling). Executor:
Claude (lane B, 2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory):

- **AC-1 (TOOL-MIG-040, decision table):** every imported artifact (a CSV row, a Ceedling
  test file, `project.yml`) carries exactly one status — `converted` (no loss),
  `converted_lossy` (kept with a recorded loss) or `not_converted` (with a reason) —
  derived from its notes; informational notes never downgrade a status.
- **AC-2 (no silent discard):** source cells that the import did not keep (unmapped
  columns with content) and constructs the Ceedling importer did not expand are recorded
  as losses; rejected rows record their reason.
- **AC-3 (TOOL-MIG-110):** a row carrying a slot, slot iteration or slot history (declared
  by the caller as a deferred column) is not imported as an ordinary case; it is listed as
  a deferred structure with artifact and location, in a set that a tool can compare.
- **AC-4 (machine-checkable):** the report has a deterministic JSON form, a strict loader
  (version, status, effect, kind, counts) and a consistency check that flags a deferred
  structure whose artifact was converted (flattened), status/note mismatches and
  duplicates.
- **AC-5 (determinism):** report content and its text form are identical across runs.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-MIG-040** | Import shall report, per imported artifact, what was converted, what was converted with loss of fidelity, and what could not be converted. | `src/ectt/mig/fidelity.py` (`build_csv_fidelity_report`, `build_ceedling_fidelity_report`, `FidelityReport`, `ArtifactFidelity`, `FidelityNote`, `STATUSES`); `RowOutcome.dropped_columns` in `src/ectt/mig/csv_import.py` | **AC-1:** `test_csv_rows_are_converted_lossy_or_not_converted`, `test_ceedling_import_is_reported_per_artifact`, `test_ceedling_informational_notes_do_not_downgrade_the_status`, `test_ceedling_unfollowed_import_downgrades_the_config`. **AC-2:** `test_lossy_row_names_the_dropped_column`, `test_rejected_rows_carry_their_reason`. **AC-5:** `test_dump_is_deterministic_and_roundtrips`. |
| **TOOL-MIG-110** | Compound or iterative test structures shall be reported explicitly as deferred, with location, in a machine-checkable set, never flattened, dropped or emulated. | `DeferredStructure`, `FidelityReport.deferred_set`, `check_fidelity_report`, `load_fidelity_report`, `dump_fidelity_report` in `src/ectt/mig/fidelity.py`; `deferred_columns` and `DEFERRED_KINDS` in `src/ectt/mig/csv_import.py` | **AC-3:** `test_deferred_structure_is_reported_with_location_and_not_imported`, `test_each_deferred_kind_is_reported`, `test_a_report_without_deferred_structures_has_an_empty_set`, `test_unknown_deferred_kind_and_mapped_deferred_column_are_refused`. **AC-4:** `test_sound_reports_pass_the_consistency_check`, `test_check_flags_a_flattened_deferred_structure`, `test_check_flags_status_note_mismatches_and_duplicates`, `test_loader_refuses_tampered_reports` (6 cases), `test_loader_refuses_non_json_text`. |

## Design notes

- **Deferred rows are not converted.** Importing a slot row as an ordinary case would be
  flattening, which TOOL-MIG-110 forbids; the row is rejected with reason
  `deferred_structure` and the deferred set records it. The consistency check enforces
  this pairing.
- **Deferred structures are declared, not guessed.** The importer cannot know which column
  of an arbitrary export is a slot; the caller names it (`deferred_columns`). A
  tool-specific adapter would supply that declaration from the tool's documented format.
- **Unmapped columns count as loss only when the cell had content**
  (`RowOutcome.dropped_columns`), so a comment column that is empty for a row does not
  downgrade it.
- **Ceedling mapping.** Parameterised `TEST_CASE` rows, duplicate test names and
  un-followed `:import:` / `:mixins:` are losses; a path that matches nothing and absent
  `:paths: :test:` are informational (nothing was lost).

## Not covered

- Fidelity reporting for adapters that do not exist yet (commercial tool formats,
  coverage import). They plug in by producing `ArtifactFidelity` entries.
- Detecting slot structures inside Ceedling sources: Ceedling has no such construct, so
  its deferred set is always empty.
- Presenting the report in the CLI or GUI (separate work packages).

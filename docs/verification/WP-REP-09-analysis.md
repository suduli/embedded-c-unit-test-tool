# Verification Analysis Note — WP-REP-09 (Report Generation From Archived Result Data)

Analysis evidence for requirements verified under WP-REP-09. Status: **implemented**
(evidence-backed).

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criterion (implemented as written; register edits are owner
territory):

- **AC (TOOL-REP-150, T — state transition):** the state chain archived record → integrity
  check → result revalidation → report model → rendered bytes runs end-to-end from the
  archived document alone; no test is re-executed at any step, and the rebuilt report agrees
  with the original on every content fact (statuses, coverage, run id, hashed provenance)
  while differing only in timestamps.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-REP-150** | The tool shall support generating a report from previously archived result data without re-executing tests. | `src/ectt/rep/from_archive.py` (`report_from_archive`, `result_set_from_dict`), `src/ectt/prj/archive.py` (`load_archive_record` integrity gate, WP-PRJ-05), `src/ectt/rep/model.py` (`build_report_model`) | **Guarantee (no re-execution):** `report_from_archive` consumes only the archived document — the fixture test builds the report with no `ResultSet` in scope at call time. The archive document is integrity-verified first (its own digest binding, WP-PRJ-05), so a report is never generated from tampered data; an archive without a `result_set` section is refused (`missing_result_set`).<br><br>**Guarantee (revalidation at the boundary):** the archived results are rebuilt through `finalize_result`, which re-enforces the NR-18 invariants — an outcome the runner boundary never produced (`flaky`) cannot be smuggled into a report. The hashed provenance of the rebuilt report matches the original's (the archived result set digests identically to the run's; timestamps are excluded from the hash), so the report says exactly what the run said, stamped as a regeneration.<br><br>**Test evidence:** `tests/rep/test_from_archive.py` — `test_report_from_archive_matches_the_original_content` (statuses, coverage, run id, provenance digest, result-set input digest; timestamps differ), `test_rebuilt_report_round_trips_and_renders_deterministically`, `test_only_the_archive_document_is_consumed`, `test_archive_without_result_set_is_refused`, `test_corrupt_archive_is_refused_before_reporting`, `test_invalid_archived_outcome_is_refused_at_revalidation`, `test_bare_result_set_dictionary_rebuilds_identically`. |

## Design notes

- **Why the archive is verified before reporting.** A report built from tampered archive data
  is misleading output (NFR-090); the WP-PRJ-05 digest binding already exists, so using it as
  the entry gate is free and makes the chain sound.
- **Why results are revalidated.** The archived result-set dictionary is data; rebuilding
  through `finalize_result` means the report can only contain records the runner boundary
  would have accepted, even if the archive was produced by a buggy writer.
- **Why the hashed provenance matching matters.** It proves the regenerated report is about
  the same run: identical result-set digest and provenance digest, with only the timestamps
  (excluded from the hash) differing — the state transition changed exactly what it should.
- **Bare result-set documents.** An archive wrapper is not required to report: the public
  `result_set_from_dict` + `build_report_model` path serves a bare archived result-set
  dictionary (integrity discipline then rests with the caller).

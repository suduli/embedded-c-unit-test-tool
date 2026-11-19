# Verification Analysis Note — WP-PRJ-05 (Archival Export and Reproduction Verification)

Analysis evidence for requirements verified under WP-PRJ-05. Status: **implemented**
(evidence-backed).

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory):

- **AC-1 (TOOL-PRJ-100, T — equivalence partitioning):** an archive record is one
  self-contained, byte-deterministic canonical JSON document bundling the sections the
  requirement names — configuration, test cases, results, coverage, and tool version — with
  every section combination (full, configuration-only, empty coverage) round-tripping and
  digest-verified.
- **AC-2 (TOOL-PRJ-110, T):** verification reports, deterministically and without raising,
  whether the record can be reproduced: `reproducible` (integrity + provenance verified, and
  tool version matches when compared), `tool_version_mismatch` (produces the version that
  made the record so the caller can reproduce with it), or `corrupt_record` (integrity
  failure, with the producing version read best-effort).

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-PRJ-100** | The tool shall support exporting a complete, self-contained record of a verification run — configuration, test cases, results, coverage, and tool version — suitable for long-term archival. | `src/ectt/prj/archive.py` (`ArchiveRecord`, `build_archive_record`, `dump_archive_record`, `load_archive_record`, `ArchiveError`), `src/ectt/prj/__init__.py` exports | **Guarantee (self-contained):** the record embeds the configuration document, the test-case document, the result set (`ectt.exh.results.result_set_to_dict`), the coverage entries, and the core provenance record (tool version, build id, interpreter, schema versions, and a content digest per embedded document) — nothing is referenced by path, so the archive is interpretable without the producing machine. The configuration and test-case sections are opaque canonical documents: the archive binds them byte-exactly without interpreting them, so it cannot drift from the producing packages' on-disk formats.<br><br>**Guarantee (long-term stability):** serialisation is byte-deterministic canonical JSON (`schema_version` first key); the archive id is a stable content digest (D-02) recomputed and verified on load; tampering with any section, the provenance, or the id is refused (`digest_mismatch`); unknown schema versions are refused (`incompatible_schema_version`). Timestamps enter only through the injected Clock.<br><br>**Test evidence:** `tests/prj/test_archive.py` — `test_export_partitions[*]` (configuration-only, with test cases, with results, with empty coverage — each round-trips and honours section presence), `test_export_requires_configuration`, `test_export_is_byte_deterministic`, `test_export_records_input_digests_and_tool_version`, `test_load_refuses_tampered_configuration`, `test_load_refuses_tampered_provenance`, `test_load_refuses_unknown_schema_version`. |
| **TOOL-PRJ-110** | The tool shall support verifying an archived record against the tool version that produced it, reporting whether the record can be reproduced. | `src/ectt/prj/archive.py` (`verify_archive_record`, `ReproductionVerdict` — verdicts `reproducible`, `tool_version_mismatch`, `corrupt_record`) | **Guarantee (reporting, not raising):** verification takes the raw archived document, load-verifies it internally, and always answers with a verdict. Integrity failures answer `corrupt_record` with the producing tool version read best-effort from the document, so even a damaged archive tells the caller who made it. A verified record compares the producing tool version with the asking tool: equality answers `reproducible`; difference answers `tool_version_mismatch` naming the producing version — reproduce with it or re-record. Skipping the comparison answers integrity-only.<br><br>**Guarantee (deterministic):** the verdict is a pure function of the record and the asking version; `to_dict()` is JSON-safe for CI consumption.<br><br>**Test evidence:** `tests/prj/test_archive.py` — `test_matching_tool_version_reports_reproducible`, `test_mismatched_tool_version_is_reported_with_the_producing_version`, `test_absent_comparison_reports_integrity_only`, `test_corrupted_record_reports_not_raises`, `test_verdict_is_deterministic_and_json_safe`. |

## Design notes

- **Why configuration and test cases are opaque documents.** TOOL-PRJ-100 asks for a complete
  record, not an interpretation. Binding the producing packages' documents byte-exactly (and
  digesting each) keeps the archive format decoupled from their schema evolution; the
  archive's own version (1.0) governs only its wrapper.
- **Why the provenance is embedded, not referenced.** Same argument as WP-CORE-04/WP-REP-06:
  an archive used as evidence must be self-describing when read back without the producing
  machine.
- **Why `tool_version_mismatch` is a distinct verdict, not an error.** TOOL-PRJ-110 asks the
  tool to *report* whether the record can be reproduced; a mismatch is a true, useful answer
  (with the producing version), not a failure of the checker.
- **Dependency discharge:** WP-CORE-04 (provenance facility) and WP-REP-06 (report-side
  embedding precedent) are both landed on this branch; no core changes were needed.

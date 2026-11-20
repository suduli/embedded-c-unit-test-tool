# Verification Analysis Note — WP-MIG-03 (Interchange Format Documentation)

Analysis evidence for requirements verified under WP-MIG-03. Status: **implemented**
(evidence-backed); verification method is inspection (SRS: INSPECTION CHECKLIST), here
turned into an executable checklist. Executor: Claude (lane B, 2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory):

- **AC-1 (complete inventory):** every format the tool reads or writes today appears in one
  registry with its direction, media type, version, grammar, versioning rule, error
  handling and loss policy. The inventory is checked against an explicit expected list, so a
  new reader or writer cannot be added without a documentation decision.
- **AC-2 (independent implementation):** each format has a worked example, a published
  schema, or both; the example is accepted by the format's own reader, so an
  implementer can start from a sample that is known to be valid.
- **AC-3 (no drift):** the documented version equals the version the code reads or writes;
  published schema files exist, parse and declare `$schema`; the published schemas accept
  the worked examples (open result export, analysis model).
- **AC-4 (the checklist is itself checked):** each failure class of the checklist is
  demonstrated by a defective spec that the check flags.
- **AC-5 (publishable):** the registry renders to one deterministic Markdown reference
  covering every format with its example verbatim.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-MIG-100** | All interchange formats the tool consumes or produces shall be documented to a level permitting independent implementation. | `src/ectt/mig/formats.py` (`INTERCHANGE_FORMATS`, `FormatSpec`, `check_format_documentation`, `render_format_reference`, `format_by_id`) | **AC-1:** `test_registry_covers_every_known_reader_and_writer`, `test_every_consumed_format_has_a_reader_and_every_format_has_evidence`. **AC-2:** `test_every_worked_example_is_accepted_by_its_reader`, `test_the_shipped_documentation_passes_its_own_checklist`. **AC-3:** `test_documented_versions_equal_the_versions_in_code`, `test_published_schema_accepts_the_worked_example` (2 schemas). **AC-4:** `test_checklist_flags_a_version_that_no_longer_matches_the_code`, `test_checklist_flags_an_example_the_reader_rejects`, `test_checklist_flags_empty_documentation_fields`, `test_checklist_flags_a_bare_name_without_example_or_schema`, `test_checklist_flags_a_consumed_format_without_a_reader`, `test_checklist_flags_a_missing_schema_and_a_bad_vocabulary`, `test_checklist_flags_duplicates_and_unprobed_versions`, `test_checklist_flags_an_empty_example_and_a_failing_probe`. **AC-5:** `test_reference_is_deterministic_and_covers_every_format`, `test_reference_contains_each_example_verbatim`, `test_reference_order_does_not_depend_on_registry_order`, `test_format_by_id_refuses_an_unknown_format`. |

## Formats documented (15)

`tests-file`, `test-case-csv`, `open-result-export`, `report-model`, `analysis-model`,
`reqif`, `requirements-csv`, `requirements-text`, `mapped-csv`, `ceedling-project`,
`unity-output`, `cmocka-output`, `fidelity-report`, `source-links`, `review-baseline`.

## Defects found while writing the examples

Making the examples executable found two real defects that prose review would have missed:

- **Analysis-model example:** the first draft referenced `ref:type.int` without defining
  it; the reader's type-closure rule (SDD-002 §4.2) refused it. The example now carries the
  type it references.
- **cmocka parser (WP-MIG-01):** the parser recognised only `[  OKAY    ]`, but cmocka itself
  prints `[       OK ]`, so every passing test of a real cmocka run was reported as an
  unrecognised line and produced no record. `OK` is now accepted as well; `OKAY` stays as
  an alias. Regression test: `test_real_cmocka_ok_spelling_is_a_pass`
  (`tests/mig/test_existing_suites.py`). The WP-MIG-01 analysis note still describes the
  grammar as `OKAY / FAILED` (second-pass row).

## Not covered (recorded, not guessed)

- **Publishing the rendered reference** as a file under `docs/` (outside this item's allowed
  paths). `render_format_reference()` produces it; a second-pass row asks for the file and
  for the register to cite it.
- **The project file (`ectt.project`)** and the SDD-level formats governed by ADR-002 are
  not in the registry; they are specified by ADR-002 and its conformance tests, and are
  not an exchange format with external tools.
- **Coverage import/export formats** (TOOL-MIG-080, WP-REP-10) do not exist yet.
- **Independent implementation by a second party** is not demonstrated; the examples and
  schemas are the level of evidence available inside the repository.

# WP-COV-01 — Statement and branch coverage from compiler backend

Status: in progress (overnight lane B, 2026-11-21)
Requirements: TOOL-COV-010, TOOL-COV-020
Design elements: DSN-COV-* per PLAN-001 §3 (CMP-COV)
Dependencies: WP-EXH-01 (implemented: `ectt.exh`), WP-TCH-02 (implemented: `ectt.tch`)
Decisions applied as written (not re-decided):
- **ADR-004 coverage backend (owner answer, 2026-11-21): "GCC first".** GCC is the
  primary coverage path (`gcov --json-format`, condition coverage via
  `-fcondition-coverage`); Clang support is added later and must not shape this item.
- **No C compiler on this machine:** parsers and readers are built against hand-written
  gcov JSON fixtures taken from the *documented* GCC format. Key names were checked
  against the GCC gcov documentation (GCC 14.4, "Invoking Gcov → GCOV JSON Format"),
  not from memory. **Real GCC output has not been checked** (recorded in the lane
  ledger); the fixtures follow the documented shape exactly.

## Format reference (GCC 14.4 documentation, verified 2026-11-21)

Top-level object: `format_version` (semantic version of the format, `"1"` in GCC
9–10, `"2"` from GCC 11 — version 2 added `calls`), `gcc_version`,
`current_working_directory`, `data_file` (the `.gcda`), `files`. GCC ≥ 14 gzips the
output (`.gcov.json.gz`).

`files[]`: `file` (source name), `functions[]` (WP-COV-04 scope), `lines[]`.

`lines[]`: `line_number` (1-based), `count` (executions of the line),
`unexecuted_block` (the line contains a block that did not run), `function_name`
(may be unset for inlined statements), `branches[]` (present with `-b`),
`conditions[]` (present with `-fcondition-coverage`, GCC ≥ 14), `calls[]`,
`block_ids[]`.

`branches[]`: `count` (executions of the branch), `fallthrough` (fall-through
branch), `throw` (exceptional branch), `source_block_id`, `destination_block_id`.

`conditions[]`: `count` (number of condition outcomes in the expression),
`covered` (number of covered condition outcomes), `not_covered_true` (terms, by
index, not seen as true), `not_covered_false` (terms, by index, not seen as false).

## Acceptance criteria

Derived from the SRS texts (SRS-001 §12 lines 406–408) and the PLAN-001 §5.4 row
(`WP-COV-01` — Statement and branch coverage from compiler backend; COV-010 COV-020).
PLAN-001 §5.4 records **no package-specific acceptance criterion** for CMP-COV
(flagged for reconciliation) — these are the derived, reviewable criteria:

1. **AC-1 (COV-010 — statement coverage).** Every `lines[]` entry is a statement
   line. A line with `count > 0` is covered, `count == 0` uncovered; a line with
   `count > 0` and `unexecuted_block == true` is reported partial (not all
   statements on the line ran). Statement coverage is an exact fraction
   (covered/total line entries), computed per file and across a document; no
   floating-point ratios.
2. **AC-2 (COV-020 — branch/decision coverage).** With `-b` data, every `branches[]`
   entry is a decision branch: a branch is covered iff `count > 0`. Branch coverage
   is an exact fraction per file and aggregate. A file with no branch entries
   reports branch coverage as not applicable (no fabricated 100%).
3. **AC-3 (condition outcomes carried).** `conditions[]` entries are parsed and
   carried with `count`, `covered`, `not_covered_true`, `not_covered_false`
   validated (`0 <= covered <= count`, term indices non-negative). The MC/DC
   interpretation of these outcomes (TOOL-COV-050/060/070) is out of WP-COV-01
   scope and is not computed here.
4. **AC-4 (GCC-first format discipline).** The reader accepts the documented gcov
   JSON: format versions `"1"` and `"2"` (version-1 documents without `calls` /
   `conditions` are accepted; unknown extra keys are ignored, never interpreted);
   an unknown `format_version` is refused with a named error. Input may be raw JSON
   text, raw JSON bytes, or gzip-compressed bytes (GCC ≥ 14 emits gzip).
5. **AC-5 (fail-closed errors).** Invalid JSON, a missing required key
   (`format_version`, `gcc_version`, `data_file`, `files`, `file`, `lines`),
   a wrong-typed or negative field, a duplicate line number within one file, or a
   `covered > count` condition is rejected with a named error (code + reason);
   nothing is silently defaulted into a coverage figure.
6. **AC-6 (determinism).** The parsed document dumps to canonical JSON bytes with
   `schema_version` first; two parses of the same input are byte-identical; no
   wall-clock and no network anywhere in the package.

## Requirement → implementation → tests

| Requirement | Implementation | Tests (tests/cov/) |
|---|---|---|
| TOOL-COV-010 (statement) | `ectt.cov.metrics.statement_coverage` over `ectt.cov.model.GcovLine` (count, unexecuted_block) | `test_statement_coverage_counts_covered_uncovered_partial`, `test_statement_coverage_aggregates_across_files`, `test_statement_coverage_empty_file_is_zero_total` |
| TOOL-COV-020 (branch) | `ectt.cov.metrics.branch_coverage` over `ectt.cov.model.GcovBranch` (count) | `test_branch_coverage_counts_taken_branches`, `test_branch_coverage_not_applicable_without_branches`, `test_branch_coverage_aggregates_across_files` |
| AC-3 conditions | `ectt.cov.model.GcovCondition` validated on read | `test_conditions_are_parsed_and_carried`, `test_condition_covered_above_count_is_refused` |
| AC-4 format | `ectt.cov.gcov.read_gcov_document` (versions 1/2, unknown keys ignored, gzip, unknown version refused) | `test_version_1_document_without_conditions_loads`, `test_unknown_top_level_keys_are_ignored`, `test_gzipped_document_loads`, `test_unknown_format_version_is_refused` |
| AC-5 errors | `ectt.cov.errors.CoverageError` + subclasses, one reason per case | `test_invalid_json_is_refused`, `test_missing_required_key_is_refused`, `test_negative_count_is_refused`, `test_duplicate_line_number_is_refused`, `test_non_object_root_is_refused` |
| AC-6 determinism | canonical JSON dump with `schema_version` first | `test_dump_is_canonical_and_byte_identical` |

## Uncovered (out of WP-COV-01 scope)

- Function and function-call coverage (`functions[]` parsing) — WP-COV-04
  (TOOL-COV-030/040).
- Merge across runs and per-test attribution, artifact completeness
  (`complete`/`truncated`/`missing`, TOOL-COV-180), quarantine (TOOL-COV-220) —
  WP-COV-02.
- Threshold enforcement — WP-COV-03 (TOOL-COV-130).
- MC/DC semantics over condition outcomes, condition-count probing
  (TOOL-COV-050/060/070/080/090/190/210) — later CMP-COV work packages.
- Real GCC output verification (no C compiler on this machine; ADR-004 fixtures
  approach) — needs a human/GCC run; recorded in the lane ledger and second-pass file.

## Second-pass items

- PLAN-001 §5.4 has no package-specific acceptance criterion for WP-COV-01; the
  derived criteria above should be reviewed and reconciled into the plan (owner edit).
- Real GCC gcov output (all supported format versions) should be captured once a GCC
  toolchain is available and the fixtures re-validated against it (owner / environment).

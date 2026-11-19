# Verification Analysis Note — WP-TCM-01 (Test Cases Authored in C)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-TCM-01. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-TCD-010 (M, P1, T) — *The tool shall support test cases authored
directly in C source against the generated harness*.

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-TCD-010): a test case authored directly in C source —
  a file that includes the generated harness header — can be registered into a test
  case set through the public API under a user-chosen identifier and is retrievable
  by that identifier afterwards; the registered record captures the source path, the
  identifier and the harness header it targets.
- AC-2 (falsifiable): a C source that does not include the generated harness header
  it claims to target is rejected with a named error — it is not a test case against
  that harness — and a missing or unreadable source file is a distinct named error.
- AC-3 (falsifiable): the test case set rejects duplicate identifiers, rejects
  lookup of unknown identifiers, and lists its cases in a deterministic order;
  registering the same source under two different identifiers is allowed (the same C
  file may back two named cases) while the same identifier is never reused.
- AC-4 (falsifiable): a caller that has already validated the C source can register
  a case by explicit model without file access, through the same registry discipline
  as file-backed registration.

Scope notes: data-driven test cases, their interchange format and expected-value
vocabularies are TOOL-TCD-020/030/040/050/060 (other work packages, P2); stable
identifier preservation across regeneration is TOOL-TCD-140 (other work package);
suite grouping and selective execution is TOOL-TCD-080. This increment ships the
C-authored-case ingestion surface only. The include check is text-level; a full C
parse of user test cases is not claimed.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TCD-010** | The tool shall support test cases authored directly in C source against the generated harness. | `src/ectt/tcm/ctest.py` (`register_c_source`, `CSourceTestCase`, `TestCaseSet`), `src/ectt/tcm/errors.py` (`InvalidTestCaseError`, `TestCaseReadError`, `NotAgainstHarnessError`, `DuplicateTestCaseError`, `UnknownTestCaseError`), re-exported by `src/ectt/tcm/__init__.py` | **Guarantee:** a C source that includes the generated harness header (`#include "<harness_header>"`) is consumed as a named test case: `TestCaseSet.register_source(case_id, path, harness_header)` verifies the include relationship, registers the case under the user-chosen identifier, and the case is retrievable via `lookup`; `register_c_source` performs the same load-and-verify without registration. A source that does not include the header it targets is refused with `NotAgainstHarnessError` (it is not a test case against that harness); missing or unreadable files raise `TestCaseReadError`; blank identifiers or harness names raise `InvalidTestCaseError`; duplicate identifiers and unknown lookups raise `DuplicateTestCaseError` and `UnknownTestCaseError`. Listing is sorted and deterministic; the same C file may back two named cases, an identifier is never reused.<br><br>**Analysis argument:** TOOL-TCD-010's support obligation is the tool consuming C-authored cases against the generated harness. The include check is text-level by design — the harness header name is generated and stable (WP-GEN-01 emits it in the harness banner and include line), so a source targeting that header is a case against the harness. No C parse is claimed; compilation and execution of the cases belong to WP-BLD-01/WP-EXH-01.<br><br>**Not covered:** data-driven cases and their formats (TOOL-TCD-020/030/040+), stable-identifier preservation across regeneration (TOOL-TCD-140), suite grouping and selective execution (TOOL-TCD-080), execution of the cases.<br><br>**Test evidence:** `tests/tcm/test_ctest.py` — `test_c_source_case_registers_and_is_retrievable`, `test_source_without_harness_include_is_rejected`, `test_source_including_a_different_header_is_rejected`, `test_missing_source_file_is_named_error`, `test_directory_as_source_is_named_error`, `test_blank_identifier_is_named_error`, `test_duplicate_identifier_rejected`, `test_same_source_under_two_identifiers_is_allowed`, `test_unknown_identifier_is_named_error`, `test_listing_is_deterministic`, `test_register_model_without_file_access`, `test_register_model_rejects_blank_identifier`, `test_error_hierarchy_derives_from_core_error` (13 tests, green in the WP-TCM-01 gate run: 479 passed, 4 skipped). |

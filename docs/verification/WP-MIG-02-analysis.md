# Verification Analysis Note — WP-MIG-02 (Ceedling Project Import)

Analysis evidence for requirements verified under WP-MIG-02. Status: **implemented**
(evidence-backed). Executor: Claude (lane B, 2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory):

- **AC-1 (configuration preserved):** every section of `project.yml`, including sections
  the importer does not know, is present in the imported `config`; a content digest of the
  configuration changes when any value changes.
- **AC-2 (test cases preserved):** every test source selected by `:paths: :test:` (with
  `+:`/`-:` markers and globs) whose name matches the configured prefix and extension
  yields its test functions in source order with their source line and a stable id
  (`stable_id(project-relative path, test name)`, D-02); commented-out and string-literal
  "tests" are not counted; each file carries a content digest.
- **AC-3 (no silent loss, TOOL-MIG-040 discipline):** parameterised `TEST_CASE` /
  `TEST_RANGE` / `TEST_MATRIX` attributes, duplicate test names, un-followed `:import:` /
  `:mixins:`, path entries matching nothing, absent test paths and non-UTF-8 sources are
  each reported in `unconverted` with a location.
- **AC-4 (read-only, TOOL-MIG-070):** the import leaves the Ceedling tree byte-identical.
- **AC-5 (fail-safe):** a missing, unreadable, non-UTF-8, non-mapping, aliased or
  syntactically broken `project.yml`, and any test path that leaves the project root, is
  refused with a `MigError` carrying a reason; nothing is guessed.
- **AC-6 (determinism):** the result is identical across runs and across checkout roots
  and line-ending styles.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-MIG-020** | The tool shall import an existing Ceedling project, preserving test cases and configuration. | `src/ectt/mig/ceedling.py` (`import_ceedling_project`, `ImportedCeedlingProject`, `CeedlingTestFile`, `CeedlingTest`, `ImportNote`, `strip_c_comments_and_strings`); `MigError` reasons `no_project_file`, `invalid_project_file`, `invalid_encoding`, `unreadable_project`, `path_escape` | **AC-1:** `test_configuration_is_preserved_including_unknown_sections`, `test_config_digest_tracks_content`. **AC-2:** `test_test_cases_are_preserved_in_source_order_with_lines`, `test_commented_and_string_tests_are_not_found`, `test_custom_prefix_and_extension_are_honoured`, `test_crlf_sources_report_the_same_lines`. **AC-3:** `test_unconverted_constructs_are_reported_with_locations`, `test_external_config_and_missing_paths_are_reported`, `test_project_without_test_paths_is_reported_not_silent`, `test_non_utf8_test_source_is_decoded_and_reported`. **AC-4:** `test_import_never_modifies_the_ceedling_tree`. **AC-5:** `test_missing_project_file_is_refused`, `test_unimportable_project_files_are_refused` (4 cases), `test_test_paths_escaping_the_project_are_refused`, `test_non_utf8_project_file_is_refused`. **AC-6:** `test_import_is_deterministic`, `test_test_ids_and_digests_are_stable_across_roots`. |

## Design notes

- **Tests are preserved, not rewritten.** A Ceedling test is imperative Unity C code with
  no declarative inputs/expected values, so mapping it onto a data-driven
  `DataDrivenTestCase` would invent data. The import registers each test (file, name,
  line, id, file digest); execution of the unrewritten suite is WP-MIG-01's path.
- **Not covered here (recorded, not guessed):** expanding `TEST_CASE` / `TEST_RANGE` rows
  into individual cases; following `:import:` / `:mixins:` files; Ceedling `:tools:` /
  `:flags:` translation into ectt toolchain settings; `:cmock:` mock configuration; the
  per-artifact converted / lossy / failed report (TOOL-MIG-040, WP-MIG-04). These are
  listed as `unconverted` notes or left to the named work packages.
- **Scalars are strings** (`RestrictedYamlAdapter` convention), so `FALSE`/`true` are
  preserved as written rather than coerced.
- **Test-function recognition** is lexical (comments and string literals blanked, line
  structure kept): `[static] void test*(...)`. Preprocessor-conditional tests are found
  regardless of the condition; a Ceedling run with `:use_test_preprocessor:` could differ.

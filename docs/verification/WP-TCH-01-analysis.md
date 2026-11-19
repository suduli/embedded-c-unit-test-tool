# Verification Analysis Note — WP-TCH-01 (Declarative Compiler Configuration Format)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-TCH-01. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-PLG-020 (M, P2, T) and TOOL-TCH-020 (M, P1, T).

## Acceptance criteria

Derived from **TOOL-TCH-020** (*The tool shall define a declarative compiler
configuration format specifying: compiler invocation, flag syntax for
coverage/debug/optimization, output conventions, and supported coverage kinds*) and
**TOOL-PLG-020** (*Adding a compiler configuration shall require only a declarative
configuration file, with no modification of tool source*):

- AC-1 (falsifiable): the configuration format specifies, per compiler: the invocation
  (executable, compile-only flag, output flag, default output), flag syntax for debug
  and for named optimization levels, output conventions (object and executable
  suffixes), and the supported coverage kinds with per-kind flags. A config
  exercising every field loads successfully.
- AC-2 (falsifiable): a compiler configuration authored purely as a YAML file — with
  no modification of any tool source file — loads, validates, registers in the
  compiler-config registry and is then retrievable by name.
- AC-3 (falsifiable): the registry rejects duplicate registration of the same
  configuration name and lookup of an unregistered name with distinct named errors;
  listing is deterministic.
- AC-4 (falsifiable): malformed configurations are rejected with named errors that
  identify the offending field: not-a-mapping document, missing or unsupported
  `schema_version`, missing/blank `name` or `family`, missing or blank invocation
  executable, missing `flags.debug`/`flags.optimization`, missing
  `output.object_suffix`/`output.executable_suffix`, missing or empty `coverage.kinds`,
  a declared kind absent from `coverage.flags`, or a flag entry that is not a list of
  strings. A missing or unreadable configuration file is a named error too.
- AC-5 (falsifiable): every declared coverage kind belongs to the documented kind
  vocabulary (line, branch, condition, decision, mcdc); declaring an unknown kind is
  rejected with a named error naming the kind.

Scope note: TOOL-TCH-010 (GCC/Clang host support) belongs to WP-TCH-02 and is not
claimed here; this increment ships the format, loader, validation and registry
mechanics, and no built-in compiler configurations. TOOL-TCH-060/070 (metric gating
and version gating) belong to WP-TCH-04 and are not claimed here.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TCH-020** | The tool shall define a declarative compiler configuration format specifying: compiler invocation, flag syntax for coverage/debug/optimization, output conventions, and supported coverage kinds. | `src/ectt/tch/config.py` (schema-version-1 document contract, `InvocationSpec`, `OutputSpec`, `CompilerConfig`, `validate_compiler_config_document`, `load_compiler_config`), `src/ectt/tch/errors.py`, re-exported by `src/ectt/tch/__init__.py` | **Guarantee:** the format is a YAML mapping with `schema_version: 1` and required sections `invocation` (executable plus optional compile-only/output/default-output overrides), `flags` (`debug` list, `optimization` level→flags mapping), `output` (object/executable suffixes), and `coverage` (`kinds` from the documented vocabulary `{line, branch, condition, decision, mcdc}` plus a `flags` entry per declared kind). Loading produces an immutable `CompilerConfig` whose `to_dict()` is deterministic.<br><br>**Guarantee (named rejection):** every malformed shape is rejected by a named `TchError` subclass: non-mapping root, missing/unsupported/boolean `schema_version` (`ConfigSchemaVersionError`), missing/blank or wrong-typed fields, missing kinds, a kind without a flags entry, a flags entry for an undeclared kind, an empty kind flag list, non-string or non-list flag values (`InvalidCompilerConfigError`), and a kind outside the vocabulary (`UnknownCoverageKindError` naming the kind). Invalid YAML text and empty files are `InvalidCompilerConfigError`; missing/unreadable files are `CompilerConfigReadError`.<br><br>**Not covered:** built-in GCC/Clang configurations (WP-TCH-02), cross-compilers and shipped configurations (WP-TCH-03), metric/version gating against the declared kinds (WP-TCH-04), multi-toolchain builds (WP-TCH-05), proprietary compilers (WP-TCH-06).<br><br>**Test evidence:** `tests/tch/test_config.py` — `test_full_config_loads_with_every_field`, `test_defaults_apply_when_optional_invocation_fields_absent`, `test_missing_file_is_named_error`, `test_directory_as_config_file_is_named_error`, `test_invalid_yaml_is_named_error`, `test_empty_file_is_named_error`, `test_non_mapping_document_rejected`, `test_missing_schema_version_rejected`, `test_unsupported_schema_version_rejected`, `test_boolean_schema_version_rejected`, `test_missing_required_field_rejected` (parametrised over six sections), `test_blank_name_rejected`, `test_blank_executable_rejected`, `test_empty_kinds_list_rejected`, `test_unknown_coverage_kind_rejected`, `test_kind_vocabulary_is_the_documented_set`, `test_kind_without_flags_entry_rejected`, `test_flag_entry_for_undeclared_kind_rejected`, `test_empty_kind_flag_list_rejected`, `test_non_string_flag_rejected`, `test_non_list_flag_field_rejected`, `test_error_hierarchy_derives_from_core_error`, `test_to_dict_is_deterministic`. |
| **TOOL-PLG-020** | Adding a compiler configuration shall require only a declarative configuration file, with no modification of tool source. | `src/ectt/tch/config.py` (`load_compiler_config`, `CompilerConfigRegistry.register`/`lookup`/`list_names`), `src/ectt/tch/__init__.py` public surface | **Guarantee:** the full add path is: author a YAML file → `load_compiler_config(path)` → `registry.register(config)` → retrievable via `registry.lookup(name)`. Nothing in that path touches tool source; the test suite performs it end-to-end against a file written into a temporary directory at test time. Duplicate names are refused (`DuplicateCompilerConfigError`) so a user config cannot silently shadow a registered name; unknown lookups are refused (`UnknownCompilerConfigError`); listing is sorted and deterministic.<br><br>**Not covered:** automatic discovery of configuration files from a user directory (WP-PLG-02 owns extension discovery); built-in configurations registered by default (WP-TCH-02).<br><br>**Test evidence:** `tests/tch/test_config.py` — `test_add_compiler_requires_only_a_yaml_file`, `test_duplicate_name_rejected`, `test_unknown_name_rejected`, `test_missing_file_is_named_error`, `test_directory_as_config_file_is_named_error`, `test_listing_is_deterministic`. |

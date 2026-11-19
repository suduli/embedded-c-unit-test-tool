# Verification Analysis Note — WP-ING-07 (Authored Link Plan)

Analysis evidence for requirements verified under WP-ING-07. No schema change: the link plan is an authored project file, not part of the analysis model (S1).

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-ING-200** | Before any test-harness build, require an explicit authored link plan for the scope that enumerates the ordered link inputs with resolved identities, the linker and runtime identities, and the effective link command. An input that cannot be resolved blocks the build with a diagnostic naming it. A compilation database alone is not sufficient. | `src/ectt/ing/linkplan.py` (`load_link_plan`, `validate_link_plan`, `LinkPlan`, `LinkPlanError`), `tests/ing/test_linkplan.py` | **Guarantee (explicit plan required):** the plan is read from `link-plans/<scope>.yaml`. A missing plan is refused with `missing_plan`. A plan with no inputs is refused with `no_link_inputs`, so the compilation database alone never defines a link.<br><br>**Guarantee (resolved identities):** each input carries a sha256 identity, which must be 64 lowercase hex digits (`invalid_identity`) and must equal the digest of the file on disk (`identity_mismatch`).<br><br>**Guarantee (unresolved input blocks, names the entry):** a missing file is refused with `missing_object`. Each violation names its entry, for example `inputs[0]`, and the detail names the path as authored.<br><br>**Guarantee (named reasons, fail closed):** every violation is collected in document order and reported in one error. A plan with any violation returns no `LinkPlan`, so an invalid plan never partially loads. Unknown keys (`unknown_field`), unknown input kinds (`unknown_input_kind`) and unknown toolchain keys (`unknown_toolchain_key`) are refused, not guessed.<br><br>**Guarantee (confinement):** absolute paths (POSIX or Windows) are refused (`absolute_path`). A path containing `..` is refused (`path_outside_project`). A path that resolves outside the project root is refused by the confinement check. Duplicates are refused (`duplicate_input`).<br><br>**Guarantee (safe scope name):** a scope name that could steer the path (for example `../adc`) is refused (`invalid_scope_name`) before any file is opened.<br><br>**Guarantee (determinism):** diagnostics carry the relative plan path and the authored entry text, never an absolute path.<br><br>**Test evidence:** `tests/ing/test_linkplan.py` — `test_valid_plan_loads_with_ordered_inputs_and_identities`, `test_plan_is_read_from_the_project_store`, `test_missing_plan_is_refused_with_named_reason`, `test_compilation_database_alone_is_not_a_link_plan`, `test_missing_object_blocks_and_names_the_entry`, `test_duplicate_input_is_refused`, `test_unknown_toolchain_key_is_refused`, `test_absolute_path_is_refused` (three forms), `test_path_escaping_the_project_is_refused`, `test_identity_mismatch_is_refused`, `test_malformed_identity_is_refused` (three forms), `test_unknown_input_kind_and_unknown_key_are_refused`, `test_unknown_top_level_key_is_refused`, `test_unsupported_schema_version_and_scope_mismatch_are_refused`, `test_missing_linker_runtime_entry_and_command_are_each_named`, `test_every_violation_is_reported_in_one_run_in_document_order`, `test_invalid_plan_never_partially_loads`, `test_error_carries_the_relative_plan_path_not_an_absolute_one`, `test_unsafe_scope_name_is_refused`, `test_plan_with_yaml_anchor_is_refused_by_the_restricted_adapter`. |

## Not yet covered

- **Not wired into the build.** Nothing calls `load_link_plan` before a harness build yet. Requiring the plan before a build is the build step's job, and that step does not exist in this package yet. The guarantee holds for any caller that uses the loader.
- **Plan format is a proposal.** SDD-003 names the `link-plans/` directory but gives no field schema. The fields here (`schema_version`, `scope`, `toolchain`, `linker.identity`, `runtime`, `entry_point`, `link_command`, `inputs`) follow the PRODUCT_ARCHITECTURE list (RV-02 F-05). They need an SDD-003 amendment before anyone authors plans against them.
- **Toolchain set is an initial list.** `gcc`, `clang` and `msvc` are the keys this build accepts. A toolchain adapter must add a key before a plan may use it.
- **No symlink test.** Symlink escape is covered only by the confinement check in `resolve_project_path`, which the prj layer tests, not by a link-plan test.
- **Linker and runtime identities are recorded, not verified.** The loader requires `linker.identity` and `runtime` but cannot check them against the installed toolchain. Verifying them belongs to the toolchain adapter.
- **Effective link command is recorded, not executed or compared.** The loader does not check it against the link closure computed by DSN-GEN-090.

## Design notes

- **Why the plan is refused whole.** A build that links a partial input set could pass with a missing object, so partial loading is the unsafe outcome. The loader returns nothing unless every check passes.
- **Why identities are digests.** A digest is checked against the file on disk, so a changed object is caught before the build. A name alone would not catch that.
- **Why the version is the string `"1"`.** The restricted YAML adapter (ADR-002) reads every scalar as a string, so the version is compared as a string.

## Night-run re-verification (2026-11-18, chat 2)

Re-ran the evidence suite on this worktree: `tests/ing/test_linkplan.py` → 24 passed, 0 skipped;
full suite 466 passed / 4 skipped (baseline 4). Assessment stands unchanged. **PARTIAL** — the
loader and its fail-closed guarantees are complete and tested; remaining: (1) wire
`load_link_plan` into the harness-build step (the build step itself does not exist yet —
CMP-BLD/CMP-GEN), (2) SDD-003 amendment for the proposed plan field schema, (3) toolchain-adapter
verification of linker/runtime identities.

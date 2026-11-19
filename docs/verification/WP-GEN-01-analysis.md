# Verification Analysis Note — WP-GEN-01 (Harness Generation Core)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-GEN-01. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-HAR-010 (M, P2, T), TOOL-HAR-020 (M, P2, T), TOOL-HAR-040 (M, P2, T) and
TOOL-HAR-050 (M, P2, T). The consuming type is the WP-ANA-04 analysis model
(`ectt.ana.model.AnalysisModel`, already implemented in the repository).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-HAR-010): given an analysis model with exactly one
  parsed unit, `HarnessGenerator(model).generate()` produces, without manual editing,
  a harness source text that is a self-contained C translation unit for the designated
  UUT: it includes the UUT header derived from the unit path and declares the
  interface needed by the exposed surface. Selection is explicit: zero units, several
  units without a designated UUT, a designated path that is not in the model, and a
  unit whose status is not `parsed` each raise a distinct named error.
- AC-2 (falsifiable, from TOOL-HAR-020): every non-static function of the UUT appears
  in the generated harness with its return type and parameter list rendered as C, and
  is directly callable from test code (declared in the harness source); static
  functions of the UUT are not exposed.
- AC-3 (falsifiable, from TOOL-HAR-040): every global variable the UUT's functions
  access (the union of the model's per-function global accesses, with read/write
  merged into `rw`) appears in the generated harness as a machine-readable exposure
  record (`ectt:exposes-global <name> <access>`), and read/write exposure of the
  UUT's global surface is provided by the UUT header include in the generated source.
  Globals whose type the analysis model cannot supply are not given invented
  declarations; the exposure record is the tool's statement of the access surface.
- AC-4 (falsifiable, from TOOL-HAR-050): the generated harness includes per-test
  setup and teardown hook registration and dispatch entry points
  (`ectt_register_setup`/`ectt_register_teardown` with `ectt_run_setup`/
  `ectt_run_teardown` dispatch), so a test case or framework back-end can install
  per-test hooks.
- AC-5 (falsifiable, determinism): generating twice from the same model produces
  byte-identical source text.

Scope notes: `static` function exposure (TOOL-HAR-030) and integration-scope harnesses
(TOOL-HAR-080) belong to WP-GEN-03; framework back-ends and template-driven generation
(TOOL-HAR-060/070) belong to WP-GEN-02; the generated-file banner here is a fixed
string and does not claim the TOOL-HAR-090 contract (WP-GEN-04 owns it). Compilability
of the generated unit is established structurally here (complete declarations,
balanced braces guard); executing a real compiler against generated output is
WP-BLD-01's build orchestration (TOOL-EXE-080). TOOL-HAR-040's file-static variable
access is **not** claimed by this increment — the current analysis model records
accessed globals by name and access only (no type reference), so type-resolved
`extern` declarations and the file-static access mechanism are future work; see the
requirement trace.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-HAR-010** | The tool shall generate a compilable test harness for a designated unit under test (UUT) from the analysis model, without manual editing. | `src/ectt/gen/harness.py` (`HarnessGenerator`, `GeneratedHarness`), `src/ectt/gen/errors.py` (`NoUnitError`, `AmbiguousUnitError`, `UnknownUnitError`, `UnitNotParsedError`), re-exported by `src/ectt/gen/__init__.py` | **Guarantee:** `HarnessGenerator(model).generate()` consumes the WP-ANA-04 `AnalysisModel` directly and emits a self-contained harness translation unit (banner, UUT header include, hook block, exposure records) with no manual step. UUT designation is explicit: a single parsed unit is used automatically; several units require `uut_path=`; zero units, an unknown designation and a unit whose status is not `parsed` raise `NoUnitError`, `UnknownUnitError` and `UnitNotParsedError` respectively; several units without designation raise `AmbiguousUnitError` naming the candidates.<br><br>**Compilability evidence:** established structurally — the generated text is a complete C translation unit (include + declarations only, balanced braces). Executing a real compiler against generated output belongs to WP-BLD-01 (TOOL-EXE-080) and is explicitly not claimed here.<br><br>**Not covered:** framework-specific rendering (WP-GEN-02), static exposure and integration harnesses (WP-GEN-03), regeneration conflict contract (WP-GEN-04), the TOOL-HAR-090 generated-file header contract (the banner here is a fixed string).<br><br>**Test evidence:** `tests/gen/test_harness.py` — `test_harness_generated_without_manual_editing`, `test_harness_header_derived_for_non_c_suffix`, `test_empty_model_is_named_error`, `test_multiple_units_without_designation_is_named_error`, `test_designated_uut_selects_from_multiple_units`, `test_unknown_designated_uut_is_named_error`, `test_failed_unit_is_named_error`, `test_generation_is_byte_identical_across_runs`. |
| **TOOL-HAR-020** | The generated harness shall expose every non-static function of the UUT as directly callable from test code. | `src/ectt/gen/harness.py` (`HarnessGenerator._exposed_functions`, `ExposedFunction`) | **Guarantee:** every UUT function whose `storage_class` is not `static` (and linkage is not `internal`) appears in the harness's exposed surface, sorted by name, with its return type and parameter list rendered as C from the model's type graph (`ref:type.<id>` resolved through the model's `types` mapping); a type the graph cannot resolve is emitted as a greppable `ectt:unresolved-type(...)` flag rather than an invented declaration. Static functions never appear in the output. Exposure is "directly callable": non-static functions are reachable from test code through the included UUT header (their declarations live there), and the harness records the exact exposed signature set it generated from the model.<br><br>**Not covered:** optional `static` function exposure is TOOL-HAR-030 / WP-GEN-03.<br><br>**Test evidence:** `tests/gen/test_harness.py` — `test_every_non_static_function_is_exposed`, `test_function_signature_rendered_with_parameters`, `test_unresolvable_parameter_type_is_flagged_not_invented`. |
| **TOOL-HAR-040** | The generated harness shall provide read and write access to global and file-static variables identified by TOOL-PAR-050. | `src/ectt/gen/harness.py` (`HarnessGenerator._exposed_variables`, `ExposedVariable`, `_merge_accesses`), rendered as `ectt:exposes-global` records | **Guarantee (partial):** the harness merges the model's per-function global accesses (union with `r`+`w` → `rw`) and emits one machine-readable exposure record per accessed global, sorted by name; read/write access to the UUT's global surface is provided concretely by the generated `#include` of the UUT header (globals declared there are directly readable and writable from test code).<br><br>**Not covered (this is why WP-GEN-01 lands as PARTIAL):** the current analysis model records accessed globals by name and access only — `GlobalAccessModel` carries no type reference and the unit carries no global-definition list — so the generator cannot emit type-resolved `extern` declarations for globals that the UUT header does not declare, and it cannot implement file-static variable access (which requires a source-inclusion or accessor mechanism that is a design decision). Both are recorded as remaining work, not silently claimed.<br><br>**Test evidence:** `tests/gen/test_harness.py` — `test_globals_recorded_with_merged_access`, `test_globals_sorted_and_read_only_recorded`. |
| **TOOL-HAR-050** | The generated harness shall include per-test setup and teardown hooks. | `src/ectt/gen/harness.py` (`SETUP_TEARDOWN_BLOCK`, `GeneratedHarness.has_setup_teardown`) | **Guarantee:** every generated harness carries the hook block: `ectt_register_setup`/`ectt_register_teardown` install a `void (*)(void)` hook, `ectt_run_setup`/`ectt_run_teardown` dispatch it if installed (no-op otherwise), so a framework back-end (WP-GEN-02) or a test case can give every test its own setup/teardown. `has_setup_teardown()` asserts the block's presence in the generated text.<br><br>**Not covered:** invoking the hooks per test is the framework back-end's execution role (WP-GEN-02); this increment provides the hook surface itself.<br><br>**Test evidence:** `tests/gen/test_harness.py` — `test_setup_and_teardown_hooks_present` (checks all four entry points), plus `has_setup_teardown` exercised in the same run. |

## Standing summary

WP-GEN-01 is recorded as **PARTIAL** in the ledger: TOOL-HAR-010, TOOL-HAR-020 and
TOOL-HAR-050 are covered with test evidence; TOOL-HAR-040 is covered for the
model-derivable access record and header-based exposure, with file-static variable
access and type-resolved `extern` emission explicitly remaining (blocked on the
analysis model carrying global types, or on a static-access design decision).

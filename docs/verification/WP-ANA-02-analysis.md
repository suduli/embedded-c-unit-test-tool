# WP-ANA-02 — Verification analysis: interface and type extraction

Lane: VERIFY (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-ANA-02. The
three owned SRS-001 requirements are the standing bar. ADR-sensitive element (ADR-001 §2/§4
binding and model boundary) is Accepted; decision-free verification only.

## Requirement → implementation → test evidence

| Requirement (SRS-001) | Implementation | Test evidence (re-run green 2026-11-18) |
|---|---|---|
| **TOOL-PAR-030** — per-function extraction: name, return type, parameter names/types, storage class, linkage, source location | `src/ectt/ana/interface.py`, `src/ectt/ana/types.py`, `src/ectt/ana/model.py` | 9 tagged tests: `tests/ana/test_interface.py::test_function_storage_class_and_linkage`, `::test_parameter_types_and_directions`, `::test_function_declaration_without_definition_not_extracted`, `::test_functions_defined_in_headers_not_extracted`; error paths in `tests/ana/test_errors.py::test_extraction_errors` |
| **TOOL-PAR-040** — transitive closure of user-defined types (struct, union, enum, typedef, function pointer) from a function's interface | `interface.py` type closure, `types.py` models | 11 tagged tests: `tests/ana/test_types.py::test_anonymous_typedef_struct_extraction`, `::test_self_referential_struct_closure_terminates`, `::test_nested_struct_union_enum_function_pointer`; SDD-002 shape conformance via `test_interface.py::test_to_dict_matches_sdd002_exact_shape` |
| **TOOL-PAR-050** — identify global and file-static variables read/written by each function | `interface.py` access analysis | `tests/ana/test_interface.py::test_globals_access_modes`, `::test_globals_compound_assignment_and_increment`, model-shape in `tests/ana/test_model.py::test_function_and_type_models_properties_and_immutability` |

## Test run

```
tests/ana → 128 passed, 0 skipped in 3.08s
full suite → 447 passed, 4 skipped (baseline 4)
```

## Gaps / not covered

- None new for the owned requirements. (Function-pointer *callee resolution* is deliberately not
  here — it is WP-ANA-03/TOOL-PAR-060 scope per ADR-001 R-01 mitigation.)

## Result

**DONE** — all three owned requirements carry named, passing tests including closure-termination
and SDD-002 exact-shape conformance.

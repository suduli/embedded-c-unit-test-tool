# WP-TCM-03 — Expected-value comparison engine

Status: in progress (overnight lane A, 2026-11-19)
Requirements: TOOL-TCD-050, TOOL-TCD-060
Design elements: DSN-TCM-030 (comparison semantics), SDD-002 §5.1 (type-directed comparison)
Dependencies: WP-TCM-02 (DONE in this ledger, commit ffacfce)
Decisions applied as written (not re-decided):
- **D-02, option (a)** (owner answer 2026-11-19): stable ids plus content digests — not directly exercised here, but comparison diagnostics feed EXE-020 failure records that bind to test digests.

## Acceptance criteria

Derived from the SRS texts (SRS-001 lines 304–306), the DSN-TCM-030 statement, and SDD-002 §5.1. PLAN-001 §5.4 records no package-specific criterion for this package (flagged for reconciliation):

1. **AC-1 (TCD-050 — scalars and enums by value).** Every scalar C type (integrals, `_Bool`, chars) and enums compare by value. Integer text is decimal or `0x` hex; C octal text (`010`) is rejected with a named error rather than silently misread. Enums accept declared enumerator names (resolved through the declared table) or their numeric value; an undeclared name is a named error, not a mismatch.
2. **AC-2 (TCD-050 — pointers by policy).** Pointer comparison follows the per-field policy: `null` compares only nullness (`NULL`/`0` vs anything else), `address` compares the recorded address text exactly, `pointee` compares the pointee values recursively with the pointee's declared type.
3. **AC-3 (TCD-050 — arrays and structs member-wise, padding excluded).** Arrays compare element-wise with the declared element type and reject an element-count difference with a diagnostic. Structs compare declared members in declared member order; a missing or unexpected member is a diagnostic. Only declared members participate — there is no padding in the value domain (structurally excludes padding, DSN-TCM-030).
4. **AC-4 (TCD-050 — unions by the active member).** A union compares only the member the test names active; other members are ignored. A comparison without an active member, or naming an undeclared one, is a named error.
5. **AC-5 (TCD-060 — float tolerance).** Floating-point comparison takes an explicit absolute or relative tolerance; the default is exact (DSN-TCM-030: "defaulting to exact only where the user asks for it"). Both tolerance modes given at once is a named error. Relative tolerance with a zero expected value degenerates to exact equality. `nan` matches only `nan`; `inf`/`-inf` compare by identity. Specifying a tolerance on a non-float type is a named error.
6. **AC-6 (deterministic diagnostics).** Every mismatch names its path (member/index chain), the expected value, the actual value, and a reason from a fixed vocabulary. Nested diagnostics are emitted in declared member order. Values are rendered deterministically (canonical JSON for composites, `canonical_float_repr`-compatible text for floats).
7. **AC-7 (no wall-clock, no network).** The engine is pure: no time, no randomness, no I/O.

## Assumptions (conservative readings, recorded per the lane contract)

- The engine evaluates comparisons in memory (declared type + expected/actual values) and is the semantics oracle the harness generator renders from; actual C-level comparison codegen belongs to CMP-GEN (WP-GEN) — second-pass note.
- Struct/array/union values are carried as nested Python values by the engine; the WP-TCM-02 `.tests` serialization currently covers flat scalar expectations, so nested composite expectations need a model extension before they can be authored on disk (second-pass note).
- Tolerance overrides are keyed by comparison path; callers pass paths matching their target names (e.g. `g_adc_gain`).
- Octal integer text is rejected (C's leading-zero octal is a silent-misread trap); this is stricter than C and recorded here.

## Requirement → implementation → tests (tests/tcm/test_compare.py)

| Requirement | Implementation | Tests |
|---|---|---|
| TOOL-TCD-050 (scalars/enums) | `compare` over `ScalarType`/`EnumType` — value equality, decimal/hex parsing, char and `_Bool` handling | `test_scalars_compare_by_value`, `test_enum_by_name_and_value`, `test_octal_text_is_rejected_not_misread` |
| TOOL-TCD-050 (pointers) | `PointerType` with `null`/`address`/`pointee` policies | `test_pointer_null_policy`, `test_pointer_address_policy`, `test_pointer_pointee_policy` |
| TOOL-TCD-050 (arrays/structs) | `ArrayType`/`StructType` member-wise comparison in declared order | `test_array_elementwise_with_count_diagnostic`, `test_struct_memberwise_in_declared_order`, `test_struct_missing_and_unexpected_members` |
| TOOL-TCM-050 (unions) | `UnionType` + required active member | `test_union_compares_only_active_member`, `test_union_requires_declared_active_member` |
| TOOL-TCD-060 | `Tolerance` (absolute/relative), exact default, NaN/inf rules | `test_float_exact_by_default`, `test_float_absolute_tolerance`, `test_float_relative_tolerance`, `test_nan_matches_only_nan`, `test_tolerance_on_non_float_is_error`, `test_both_tolerance_modes_is_error` |
| determinism | declared-order diagnostics, canonical rendering | `test_diagnostics_are_in_declared_order`, `test_float_rendering_is_canonical` |

Uncovered: none for the derived criteria; C codegen of the comparison is
CMP-GEN scope (second-pass).

## Second-pass items

- PLAN-001 §5.4 has no package-specific acceptance criterion for WP-TCM-03; reconcile the derived criteria above (owner edit).
- Extend the WP-TCM-02 model/serialization so struct/array/union expectations can be authored in `.tests` files (nested values), and render the comparison semantics into harness C (CMP-GEN).

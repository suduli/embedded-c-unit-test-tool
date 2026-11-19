# Verification Analysis Note — WP-GEN-06 (Stub Generation Core)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-GEN-06. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-STB-010 (M, P2, T), TOOL-STB-020 (M, P2, T), TOOL-STB-030 (M, P2, T).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-STB-010): a stub is generated for every external
  function supplied (the WP-ING-05 stub-requirement list feeds this generator); a
  call list with no externals produces an empty stub unit; a duplicate function name
  is a named error.
- AC-2 (falsifiable, from TOOL-STB-020): every generated stub's signature is
  identical to the signature it replaces — same return type, same parameter types and
  names, in order — verifiable by direct text comparison against the input signature.
- AC-3 (falsifiable, from TOOL-STB-030): each stub unit emits the declarations its
  stubs need to compile independently: a forward declaration per stub, and for every
  struct/typedef type referenced by a signature, a type declaration collected in the
  unit's declaration block (builtins and pointers need none); output is
  deterministic and sorted.
- AC-4 (falsifiable): every stub body carries the greppable stub marker and default
  zero-return behaviour, so a stub is recognisable in generated output.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-STB-010** | The tool shall automatically generate a stub for every external function called by the UUT. | `src/ectt/gen/stubs.py` (`generate_stubs`, `FunctionSignature`, `Stub`, `StubUnit`, `DuplicateStubError`), re-exported by `src/ectt/gen/__init__.py` | **Guarantee:** one stub per external signature supplied — the WP-ING-05 `stub_requirements` list is the intended feed — sorted deterministically; an empty external list yields a valid empty unit; a duplicate name raises `DuplicateStubError`; every stub body carries the `ectt:stub` marker with a default return (zero/false/null per return type, cast for unlisted types).<br><br>**Test evidence:** `tests/gen/test_stubs.py` — `test_stub_for_every_external_function`, `test_empty_external_list_yields_empty_unit`, `test_duplicate_stub_name_is_named_error`, `test_stub_bodies_carry_marker_and_default_return`, `test_output_is_deterministic`. |
| **TOOL-STB-020** | Each generated stub shall have a signature identical to the function it replaces. | `src/ectt/gen/stubs.py` (`FunctionSignature.signature_text`, stub definition emission) | **Guarantee:** the stub definition is rendered directly from the input signature — same return type, same parameter types and names in order, empty parameter lists rendered as `void` — verified by exact text comparison of `signature_texts()` against the input and by negative assertion (a changed signature never matches). Malformed signatures (blank name/type/parameter) are named errors.<br><br>**Test evidence:** `tests/gen/test_stubs.py` — `test_stub_signature_identical_to_replaced_function`, `test_void_stub_renders_void_parameter_list`, `test_malformed_signature_is_named_error`. |
| **TOOL-STB-030** | The tool shall generate, per stub, the type and structure declarations required for the stub to compile independently. | `src/ectt/gen/stubs.py` (`_required_type_declarations`, `_candidate_keys`, `StubUnit.type_declarations`) | **Guarantee:** the stub unit collects, into one declaration block, a forward declaration for every struct/union/enum type and a typedef for every named typedef referenced by any stub signature — resolving both model refs (`ref:type.struct.Frame`) and C spellings (`struct Frame`) through the type graph; builtin and pointer types need no declarations (asserted). Output is deterministic and sorted.<br><br>**Test evidence:** `tests/gen/test_stubs.py` — `test_struct_type_declarations_collected`, `test_builtin_and_pointer_types_need_no_declarations`, `test_pointer_and_float_returns_get_cast_defaults`. |

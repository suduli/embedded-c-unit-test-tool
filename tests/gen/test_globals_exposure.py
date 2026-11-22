# implements: TOOL-HAR-040
"""Type-resolved global and file-static exposure in the generated harness (A2).

The schema 1.5 inventory (``GlobalVariableModel``) drives what the harness can
reach: visible variables get type-resolved ``extern`` declarations; file-static
variables are reached through the source-inclusion harness; a variable whose
type the model cannot resolve is reported not reachable with the named reason
``type_not_recorded``, never guessed. No C compiler is available: the generated
C is verified by parsing (libclang) and by golden text — say so wherever these
results are quoted.
"""

from __future__ import annotations

from ectt.ana.frontend import parse
from ectt.ana.model import (
    AnalysisModel,
    AnalysisUnit,
    DimensionModel,
    FunctionModel,
    GlobalVariableModel,
    ProvenanceModel,
    SourceLocation,
    TypeModel,
)
from ectt.gen import (
    MECHANISM_EXTERN_DECLARATION,
    MECHANISM_NOT_REACHABLE,
    MECHANISM_SOURCE_INCLUSION,
    REASON_TYPE_NOT_RECORDED,
    HarnessGenerator,
    render_global_exposure_block,
    resolve_global_exposures,
    spell_type,
)

TYPES = {
    "type.int": TypeModel(kind="builtin", name="int"),
    "type.uchar": TypeModel(kind="builtin", name="unsigned char"),
    "type.Frame": TypeModel(kind="struct", name="Frame"),
    "type.buf8": TypeModel(kind="array", element_type="ref:type.uchar", size=8),
}

SCALAR = GlobalVariableModel(name="g_count", type="ref:type.int", has_initializer=True, storage_class="none")
STRUCT = GlobalVariableModel(name="g_frame", type="ref:type.Frame", has_initializer=False, storage_class="none")
ARRAY = GlobalVariableModel(
    name="g_buf", type="ref:type.buf8", has_initializer=False, storage_class="none"
)
STATIC = GlobalVariableModel(name="g_state", type="ref:type.int", has_initializer=True, storage_class="static")
GHOST = GlobalVariableModel(name="g_ghost", type="ref:type.ghost", has_initializer=False, storage_class="extern")


def _model(*variables: GlobalVariableModel) -> AnalysisModel:
    function = FunctionModel("adc_scale", "external", "none", SourceLocation("uut.c", 3), "ref:type.int")
    unit = AnalysisUnit(path="uut.c", status="parsed", functions=(function,), global_variables=variables)
    return AnalysisModel(
        provenance=ProvenanceModel("0.1.0", "fixture", "fixture"),
        units=(unit,),
        types=dict(TYPES),
    )


def _harness(*variables: GlobalVariableModel) -> object:
    return HarnessGenerator(_model(*variables)).generate()


def test_spell_type_resolves_builtins_structs_and_arrays() -> None:
    """verifies: TOOL-HAR-040 — the type graph spells scalars, structs and
    arrays; a missing reference is None, never a guess."""
    assert spell_type("ref:type.int", TYPES) == "int"
    assert spell_type("ref:type.Frame", TYPES) == "struct Frame"
    assert spell_type("ref:type.buf8", TYPES) == "unsigned char[8]"
    assert spell_type("ref:type.ghost", TYPES) is None
    assert spell_type("not-a-ref", TYPES) is None


def test_a_multi_dimension_array_spells_every_dimension() -> None:
    """verifies: TOOL-HAR-040 — nested dimensions spell in order."""
    matrix = TypeModel(
        kind="array",
        element_type="ref:type.int",
        dimensions=(DimensionModel(size=2), DimensionModel(size=3)),
    )
    graph = {"type.matrix": matrix, "type.int": TypeModel(kind="builtin", name="int")}
    assert spell_type("ref:type.matrix", graph) == "int[2][3]"


def test_scalar_global_gets_an_extern_declaration() -> None:
    """verifies: TOOL-HAR-040 — golden: visible scalar resolved and declared."""
    exposures = resolve_global_exposures(_model(SCALAR).units[0], _model(SCALAR).types)
    assert len(exposures) == 1
    exposure = exposures[0]
    assert exposure.mechanism == MECHANISM_EXTERN_DECLARATION
    assert exposure.c_type == "int"
    assert exposure.declaration == "extern int g_count;"
    assert render_global_exposure_block(exposures) == (
        "/* ectt:global-exposure begin - resolved from the analysis model (TOOL-HAR-040). */\n"
        "extern int g_count;\n"
        "/* ectt:exposes-global-var: g_count extern-declaration int storage=none has-initializer=true */\n"
        "/* ectt:global-exposure end */"
    )


def test_struct_and_array_globals_get_resolved_declarations() -> None:
    """verifies: TOOL-HAR-040 — golden: struct and array spellings in order."""
    exposures = resolve_global_exposures(_model(ARRAY, STRUCT).units[0], _model(ARRAY, STRUCT).types)
    block = render_global_exposure_block(exposures)
    assert "extern unsigned char g_buf[8];" in block
    assert "extern struct Frame g_frame;" in block
    # Declarations in sorted name order, records after them.
    assert block.index("extern unsigned char g_buf[8];") < block.index("extern struct Frame g_frame;")
    assert block.index("extern struct Frame g_frame;") < block.index("/* ectt:exposes-global-var: g_frame")


def test_the_generator_embeds_the_block_after_the_access_records() -> None:
    """verifies: TOOL-HAR-040 — the harness source carries the resolved block
    where test code can see the declarations, before the user regions."""
    harness = _harness(SCALAR, STRUCT)
    source = harness.source
    assert "extern int g_count;" in source and "extern struct Frame g_frame;" in source
    assert source.index("/* ectt:global-exposure begin") < source.index("/* ectt:user-region: test-cases begin */")
    assert harness.global_exposures == resolve_global_exposures(_model(SCALAR, STRUCT).units[0], _model(SCALAR, STRUCT).types)


def test_a_file_static_variable_is_reached_by_source_inclusion_not_extern() -> None:
    """verifies: TOOL-HAR-040 — internal linkage is never extern-declared; the
    record names the source-inclusion mechanism, and the static-exposure
    harness (which includes the UUT source) records the variable as reached."""
    exposures = resolve_global_exposures(_model(STATIC).units[0], _model(STATIC).types)
    (exposure,) = exposures
    assert exposure.mechanism == MECHANISM_SOURCE_INCLUSION
    assert exposure.declaration is None
    assert exposure.c_type == "int"
    assert "ectt:exposes-global-var: g_state source-inclusion int storage=static has-initializer=true" in render_global_exposure_block(exposures)

    static_harness = HarnessGenerator(_model(STATIC)).generate()
    plain = static_harness.source
    assert "extern int g_state;" not in plain  # the plain harness does not include the source

    from ectt.gen import generate_with_statics

    statics_harness = generate_with_statics(_model(STATIC))
    assert '#include "uut.c"' in statics_harness.source
    assert "/* ectt:exposes-global-var: g_state source-inclusion int storage=static has-initializer=true */" in statics_harness.source


def test_an_unrecorded_type_is_not_reachable_with_a_named_reason() -> None:
    """verifies: TOOL-HAR-040 — a type the model cannot resolve is reported,
    never guessed: no declaration, named reason on the record."""
    exposures = resolve_global_exposures(_model(GHOST).units[0], _model(GHOST).types)
    (exposure,) = exposures
    assert exposure.mechanism == MECHANISM_NOT_REACHABLE
    assert exposure.reason == REASON_TYPE_NOT_RECORDED
    assert exposure.declaration is None and exposure.c_type == ""
    assert "reason=type_not_recorded" in render_global_exposure_block(exposures)

    harness = _harness(GHOST)
    assert all(e.declaration is None for e in harness.global_exposures)  # nothing invented
    assert not [line for line in harness.source.splitlines() if line.startswith("extern ")]


def test_a_recursive_type_chain_is_refused_not_looped() -> None:
    """verifies: TOOL-HAR-040 — a self-referencing type chain spells None."""
    looped = {"type.a": TypeModel(kind="typedef", name=None, underlying_type="ref:type.b"),
              "type.b": TypeModel(kind="typedef", name=None, underlying_type="ref:type.a")}
    assert spell_type("ref:type.a", looped) is None


def test_the_inventory_order_does_not_change_the_block() -> None:
    """verifies: TOOL-NFR-060 — exposures are name-sorted; byte-stable."""
    forward = render_global_exposure_block(resolve_global_exposures(_model(SCALAR, STRUCT).units[0], _model(SCALAR, STRUCT).types))
    reverse = render_global_exposure_block(resolve_global_exposures(_model(STRUCT, SCALAR).units[0], _model(STRUCT, SCALAR).types))
    assert forward == reverse


def test_a_model_without_recorded_globals_is_byte_identical_to_the_old_shape() -> None:
    """verifies: TOOL-NFR-060 — no inventory, no block: pre-1.5 models render
    exactly as before."""
    harness = _harness()
    assert harness.global_exposures == ()
    assert "ectt:global-exposure" not in harness.source
    again = _harness()
    assert harness.source == again.source


def test_the_generated_harness_with_globals_parses_cleanly(tmp_path) -> None:
    """verifies: TOOL-HAR-040 — the whole harness (extern declarations
    included) parses with zero diagnostics as C99 (no C compiler: parse-only)."""
    from pathlib import Path

    harness = _harness(SCALAR, STRUCT, ARRAY, STATIC, GHOST)
    root = Path(tmp_path)
    (root / "harness.c").write_text(harness.source, encoding="utf-8")
    (root / "uut.h").write_text("struct Frame { int a; };\nint adc_scale(int raw);\n", encoding="utf-8")
    parsed = parse(
        root / "harness.c",
        args=["-std=c99", "-pedantic", "-DECTT_STREAM_WRITE(t)=((void)(t))", "-I", str(root)],
    )
    assert parsed.status == "parsed"
    assert [f"{d.severity}: {d.message}" for d in parsed.diagnostics if d.severity in ("error", "fatal")] == []

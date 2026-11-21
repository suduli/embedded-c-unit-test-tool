# implements: TOOL-ATG-110
"""Constructs a generation engine cannot handle (WP-ATG-05).

Verifies: TOOL-ATG-110 (boundary value analysis): dynamic memory, floating point,
concurrency and inline assembly are reported per function as explicit limitations
rather than failing silently; inline assembly, which the model cannot show, is listed
as not assessed.
"""

from __future__ import annotations

import json

import pytest

from ectt.ana.model import (
    AnalysisUnit,
    CallModel,
    FunctionModel,
    ParameterModel,
    SourceLocation,
    StructMemberModel,
    TypeModel,
)
from ectt.atg import AtgError
from ectt.atg.capabilities import (
    ASSESSED_KINDS,
    NOT_ASSESSED_KINDS,
    EngineCapabilities,
    Limitation,
    assess_capabilities,
    limitations_to_dict,
)

TYPES = {
    "type.int": TypeModel(kind="builtin", name="int"),
    "type.double": TypeModel(kind="builtin", name="double"),
    "type.float": TypeModel(kind="builtin", name="float"),
    "type.real": TypeModel(kind="typedef", name="real", underlying_type="ref:type.double"),
    "type.Sample": TypeModel(kind="struct", name="Sample", members=(StructMemberModel("v", "ref:type.real"),)),
    "type.Pair": TypeModel(kind="struct", name="Pair", members=(StructMemberModel("a", "ref:type.int"),)),
    "type.Loop": TypeModel(kind="struct", name="Loop", members=(StructMemberModel("next", "ref:type.Loop"),)),
    "type.Doubles": TypeModel(kind="array", element_type="ref:type.double", size=4),
    "type.DoublePtr": TypeModel(kind="pointer", target="ref:type.double"),
}
ALL = frozenset({"dynamic_memory", "floating_point", "concurrency"})


def _fn(name: str, *, ret: str = "ref:type.int", params: tuple[tuple[str, str], ...] = (), calls: tuple[str, ...] = ()) -> FunctionModel:
    return FunctionModel(
        name=name,
        linkage="external",
        storage_class="none",
        location=SourceLocation("src/a.c", 1),
        return_type=ret,
        parameters=tuple(ParameterModel(n, t) for n, t in params),
        calls=tuple(CallModel(c, "external", "direct", 1) for c in calls),
    )


def _unit(*functions: FunctionModel, status: str = "parsed") -> AnalysisUnit:
    return AnalysisUnit(path="src/a.c", status=status, functions=functions)


def _found(*functions: FunctionModel, cannot: frozenset[str] = ALL) -> list[tuple[str, str, str]]:
    result = assess_capabilities([_unit(*functions)], TYPES, EngineCapabilities("klee", cannot))
    return [(item.function, item.kind, item.evidence) for item in result]


@pytest.mark.parametrize("allocator", ["malloc", "calloc", "realloc", "free", "aligned_alloc", "posix_memalign", "strdup", "strndup"])
def test_allocator_calls_are_dynamic_memory(allocator: str) -> None:
    assert _found(_fn("f", calls=(allocator,))) == [("f", "dynamic_memory", f"calls {allocator}")]


@pytest.mark.parametrize("call", ["pthread_create", "pthread_mutex_lock", "thrd_create", "mtx_lock", "cnd_wait", "sem_wait", "atomic_load", "__atomic_add_fetch", "fork", "vfork", "clone"])
def test_threading_locking_and_atomic_calls_are_concurrency(call: str) -> None:
    assert _found(_fn("f", calls=(call,))) == [("f", "concurrency", f"calls {call}")]


@pytest.mark.parametrize(
    ("ref", "expected"),
    [
        ("ref:type.double", True),
        ("ref:type.float", True),
        ("ref:type.real", True),  # typedef of double
        ("ref:type.Sample", True),  # struct holding a typedef'd double
        ("ref:type.Doubles", True),  # array of double
        ("ref:type.DoublePtr", True),  # pointer to double
        ("ref:type.int", False),
        ("ref:type.Pair", False),
        ("ref:type.Loop", False),  # self-referential, no float
    ],
)
def test_floating_point_is_found_through_typedefs_structs_arrays_and_pointers(ref: str, expected: bool) -> None:
    by_param = _found(_fn("f", params=(("x", ref),)))
    by_return = _found(_fn("g", ret=ref))

    assert bool(by_param) is expected and bool(by_return) is expected
    if expected:
        assert by_param == [("f", "floating_point", "parameter 'x' involves floating point")]
        assert by_return == [("g", "floating_point", "return type involves floating point")]


def test_a_type_name_missing_from_the_graph_is_still_recognised_when_it_is_a_float_builtin() -> None:
    assert _found(_fn("f", params=(("x", "ref:type.long double"),))) == [("f", "floating_point", "parameter 'x' involves floating point")]
    assert _found(_fn("f", params=(("x", "ref:type.mystery"),))) == []


def test_only_kinds_the_engine_cannot_handle_are_reported() -> None:
    function = _fn("f", params=(("x", "ref:type.double"),), calls=("malloc", "pthread_create"))

    assert {kind for _f, kind, _e in _found(function, cannot=frozenset({"floating_point"}))} == {"floating_point"}
    assert {kind for _f, kind, _e in _found(function, cannot=frozenset({"dynamic_memory", "concurrency"}))} == {"dynamic_memory", "concurrency"}
    assert _found(function, cannot=frozenset()) == []


def test_every_limitation_names_its_function_and_evidence_and_functions_are_independent() -> None:
    found = _found(_fn("clean"), _fn("alloc", calls=("malloc",)), _fn("both", params=(("x", "ref:type.float"),), calls=("free",)))

    assert found == [
        ("alloc", "dynamic_memory", "calls malloc"),
        ("both", "dynamic_memory", "calls free"),
        ("both", "floating_point", "parameter 'x' involves floating point"),
    ]


def test_repeated_evidence_is_reported_once_and_distinct_evidence_separately() -> None:
    found = _found(_fn("f", calls=("malloc", "malloc", "calloc")))
    assert found == [("f", "dynamic_memory", "calls calloc"), ("f", "dynamic_memory", "calls malloc")]


def test_output_is_sorted_and_independent_of_function_order() -> None:
    a, b = _fn("a", calls=("malloc",)), _fn("b", calls=("malloc",))
    assert _found(a, b) == _found(b, a)


def test_failed_units_contribute_nothing() -> None:
    failed = AnalysisUnit(path="src/bad.c", status="failed", functions=(_fn("f", calls=("malloc",)),))
    assert assess_capabilities([failed], TYPES, EngineCapabilities("klee", ALL)) == ()


def test_inline_assembly_is_never_claimed_absent() -> None:
    """The model cannot show it, so it is declared not assessed, whatever the engine says."""
    capabilities = EngineCapabilities("klee", frozenset({"inline_assembly"}))
    assert assess_capabilities([_unit(_fn("f"))], TYPES, capabilities) == ()
    document = limitations_to_dict((), capabilities)
    assert document["not_assessed_kinds"] == ["inline_assembly"]
    assert NOT_ASSESSED_KINDS == ("inline_assembly",) and "inline_assembly" not in ASSESSED_KINDS


def test_the_report_form_lists_the_engine_the_limitations_and_what_was_assessed() -> None:
    capabilities = EngineCapabilities("klee", ALL)
    limitations = assess_capabilities([_unit(_fn("f", calls=("malloc",)))], TYPES, capabilities)

    document = limitations_to_dict(limitations, capabilities)

    assert json.dumps(document, sort_keys=True)
    assert document["engine"] == "klee"
    assert document["assessed_kinds"] == ["concurrency", "dynamic_memory", "floating_point"]
    assert document["limitations"] == [{"evidence": "calls malloc", "function": "f", "kind": "dynamic_memory", "unit": "src/a.c"}]


def test_limitation_dicts_are_stable() -> None:
    assert Limitation("u", "f", "concurrency", "calls fork").to_dict() == {"evidence": "calls fork", "function": "f", "kind": "concurrency", "unit": "u"}


@pytest.mark.parametrize("kind", ["recursion", "", "Floating_Point"])
def test_an_engine_cannot_declare_an_unknown_kind(kind: str) -> None:
    with pytest.raises(AtgError) as excinfo:
        EngineCapabilities("klee", frozenset({kind}))
    assert excinfo.value.reason == "unknown_limitation_kind"


@pytest.mark.parametrize("name", ["_Float16", "__fp16", "__bf16", "__float128", "_Float128", "__ibm128", "double _Complex", "float _Complex"])
def test_extended_and_complex_floating_builtins_are_floating_point(name: str) -> None:
    types = {**TYPES, "type.ext": TypeModel(kind="builtin", name=name)}
    result = assess_capabilities([_unit(_fn("f", params=(("x", "ref:type.ext"),)))], types, EngineCapabilities("klee", ALL))
    assert [(i.function, i.kind) for i in result] == [("f", "floating_point")]


def test_sanitised_graph_keys_for_a_missing_long_double_are_recognised() -> None:
    assert _found(_fn("f", params=(("x", "ref:type.long_double"),))) == [("f", "floating_point", "parameter 'x' involves floating point")]

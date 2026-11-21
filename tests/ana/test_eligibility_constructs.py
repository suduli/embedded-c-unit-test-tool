# implements: DSN-ANA-130
"""Eligibility gate reasons from the unsupported-construct inventory (FIX-ANAGATE).

Verifies: TOOL-PAR-140 (the inventory fails closed downstream), TOOL-PAR-170.
"""

from __future__ import annotations

from typing import Any

import pytest

from ectt.ana.eligibility import (
    CONSTRUCT_REASON_PREFIX,
    UnattributedConstruct,
    assess_eligibility,
    find_unattributed_constructs,
)
from ectt.ana.frontend import parse
from ectt.ana.interface import extract_interfaces
from ectt.ana.model import (
    AnalysisUnit,
    FunctionModel,
    ParameterModel,
    SourceLocation,
    UnsupportedConstructModel,
)

FILE = "src/adc.c"


def _fn(name: str, line: int, *, with_param: bool = True) -> FunctionModel:
    return FunctionModel(
        name=name,
        linkage="external",
        storage_class="none",
        location=SourceLocation(file=FILE, line=line),
        return_type="ref:type.int",
        parameters=(ParameterModel(name="n", type="ref:type.int"),) if with_param else (),
    )


def _unit(*constructs: UnsupportedConstructModel, functions: tuple[FunctionModel, ...] | None = None) -> AnalysisUnit:
    return AnalysisUnit(
        path=FILE,
        status="parsed",
        functions=functions if functions is not None else (_fn("plain", 1), _fn("vf", 10)),
        unsupported_constructs=tuple(constructs),
    )


def _construct(kind: str, detail: str | None, line: int | None, count: int = 1) -> UnsupportedConstructModel:
    location = SourceLocation(file=FILE, line=line) if line is not None else None
    return UnsupportedConstructModel(kind=kind, count=count, detail=detail, location=location)


def _reasons(unit: AnalysisUnit) -> dict[str, tuple[str, ...]]:
    return {r.function: r.reasons for r in assess_eligibility([unit])}


@pytest.mark.parametrize(
    ("kind", "detail"),
    [("variadic_function", "vf"), ("variable_length_array_parameter", "vf.n"), ("some_future_kind", "vf")],
)
def test_each_construct_kind_becomes_a_named_reason_on_its_owner(kind: str, detail: str) -> None:
    reasons = _reasons(_unit(_construct(kind, detail, 10)))

    assert reasons["vf"] == (f"unsupported_construct:{kind}",)
    assert reasons["plain"] == ()


def test_the_owner_is_ineligible_and_others_are_untouched() -> None:
    records = {r.function: r for r in assess_eligibility([_unit(_construct("variadic_function", "vf", 10))])}

    assert records["vf"].eligible is False
    assert records["plain"].eligible is True
    assert records["vf"].observable_channels == ("parameters", "return_value")


def test_reasons_are_sorted_by_kind_and_follow_the_existing_reasons() -> None:
    static_fn = FunctionModel(
        name="hid",
        linkage="internal",
        storage_class="static",
        location=SourceLocation(file=FILE, line=20),
        return_type="ref:type.builtin.void",
    )
    unit = _unit(
        _construct("variadic_function", "hid", 20),
        _construct("variable_length_array_parameter", "hid.a", 20),
        functions=(static_fn,),
    )

    (record,) = assess_eligibility([unit])

    assert record.reasons == (
        "static_not_exposed",
        "no_observable_channel",
        "unsupported_construct:variable_length_array_parameter",
        "unsupported_construct:variadic_function",
    )


def test_ordering_does_not_depend_on_inventory_order() -> None:
    a = _construct("variadic_function", "vf", 10)
    b = _construct("variable_length_array_parameter", "vf.n", 10)
    assert _reasons(_unit(a, b)) == _reasons(_unit(b, a))


def test_empty_inventory_leaves_the_gate_unchanged() -> None:
    reasons = _reasons(_unit())
    assert reasons == {"plain": (), "vf": ()}


def test_a_detail_naming_another_function_never_matches() -> None:
    reasons = _reasons(_unit(_construct("variadic_function", "other", 10)))
    assert reasons == {"plain": (), "vf": ()}


def test_missing_location_falls_back_to_the_named_function() -> None:
    reasons = _reasons(_unit(_construct("variadic_function", "vf", None)))
    assert reasons["vf"] == ("unsupported_construct:variadic_function",)


def test_a_construct_with_neither_location_nor_detail_is_unattributable() -> None:
    unit = _unit(_construct("variadic_function", None, None))

    assert _reasons(unit) == {"plain": (), "vf": ()}
    assert find_unattributed_constructs([unit]) == (UnattributedConstruct(FILE, "variadic_function", 1),)


def test_extra_occurrences_are_reported_not_spread_over_other_functions() -> None:
    unit = _unit(_construct("variadic_function", "vf", 10, count=3))

    assert _reasons(unit) == {"plain": (), "vf": ("unsupported_construct:variadic_function",)}
    assert find_unattributed_constructs([unit]) == (UnattributedConstruct(FILE, "variadic_function", 2),)


def test_fully_attributed_inventory_has_no_unattributed_remainder() -> None:
    assert find_unattributed_constructs([_unit(_construct("variadic_function", "vf", 10))]) == ()
    assert find_unattributed_constructs([_unit()]) == ()


def test_unattributed_report_is_sorted_and_skips_failed_units() -> None:
    other = AnalysisUnit(
        path="src/a.c",
        status="parsed",
        functions=(),
        unsupported_constructs=(_construct("zeta", None, None, count=2), _construct("alpha", None, None)),
    )
    failed = AnalysisUnit(path="src/bad.c", status="failed", unsupported_constructs=(_construct("alpha", None, None),))

    found = find_unattributed_constructs([_unit(), failed, other])

    assert [(f.unit, f.kind, f.count) for f in found] == [("src/a.c", "alpha", 1), ("src/a.c", "zeta", 2)]


def test_failed_units_still_contribute_only_their_failure_record() -> None:
    failed = AnalysisUnit(path="src/bad.c", status="failed", unsupported_constructs=(_construct("variadic_function", "x", 1),))

    (record,) = assess_eligibility([failed])

    assert record.kind == "unit" and record.reasons == ("unit_failed",)


def test_reason_prefix_is_stable_vocabulary() -> None:
    assert CONSTRUCT_REASON_PREFIX == "unsupported_construct:"
    assert UnattributedConstruct("u", "k", 2).to_dict() == {"count": 2, "kind": "k", "unit": "u"}


# --- against real extraction -----------------------------------------------------------


def _extracted(code: bytes, std: str = "c99") -> Any:
    parsed = parse("probe.c", args=[f"-std={std}"], unsaved_files=[("probe.c", code)])
    return extract_interfaces(parsed)


def test_real_variadic_and_vla_functions_are_named_in_the_gate() -> None:
    unit = _extracted(
        b"int fine(int a) { return a; }\n"
        b"int vdef(int n, ...) { return n; }\n"
        b"int vla_sum(int n, int a[n]) { return a[0]; }\n"
    )

    reasons = {r.function: r.reasons for r in assess_eligibility([unit])}

    assert reasons["fine"] == ()
    assert reasons["vdef"] == ("unsupported_construct:variadic_function",)
    assert reasons["vla_sum"] == ("unsupported_construct:variable_length_array_parameter",)
    assert find_unattributed_constructs([unit]) == ()


def test_real_second_variadic_function_is_reported_as_unattributed() -> None:
    unit = _extracted(b"int first(int n, ...) { return n; }\nint second(int n, ...) { return n; }\n")

    reasons = {r.function: r.reasons for r in assess_eligibility([unit])}

    assert reasons["first"] == ("unsupported_construct:variadic_function",)
    assert reasons["second"] == ()
    assert find_unattributed_constructs([unit]) == (UnattributedConstruct("probe.c", "variadic_function", 1),)

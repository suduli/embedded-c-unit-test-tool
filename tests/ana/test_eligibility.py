# implements: DSN-ANA-130
"""Tests for the eligibility and observability gate.

Verifies: TOOL-PAR-170, DSN-ANA-130 — discovery does not imply eligibility.
"""

from __future__ import annotations

from pathlib import Path

from ectt.ana.eligibility import assess_eligibility
from ectt.ana.model import (
    AnalysisUnit,
    FunctionModel,
    GlobalAccessModel,
    ParameterModel,
    SourceLocation,
    UnitFailureModel,
)

_VOID = frozenset({"type.builtin.void"})


def _fn(
    name: str,
    *,
    storage_class: str = "none",
    linkage: str = "external",
    return_type: str = "ref:type.int",
    parameters: tuple[ParameterModel, ...] = (),
    globals_: tuple[GlobalAccessModel, ...] = (),
) -> FunctionModel:
    return FunctionModel(
        name=name,
        linkage=linkage,
        storage_class=storage_class,
        location=SourceLocation(file="src/adc.c", line=1),
        return_type=return_type,
        parameters=parameters,
        globals=globals_,
    )


def _unit(*functions: FunctionModel) -> AnalysisUnit:
    return AnalysisUnit(path="src/adc.c", status="parsed", functions=tuple(functions))


def test_eligible_function_with_full_channels() -> None:
    """verifies: TOOL-PAR-170, DSN-ANA-130"""
    records = assess_eligibility(
        [
            _unit(
                _fn(
                    "adc_read",
                    parameters=(ParameterModel(name="ch", type="ref:type.u16"),),
                    globals_=(GlobalAccessModel(name="g_level", access="rw"),),
                )
            )
        ],
        void_type_refs=_VOID,
    )
    assert len(records) == 1
    rec = records[0]
    assert rec.eligible
    assert rec.reasons == ()
    assert rec.observable_channels == ("parameters", "return_value", "globals")


def test_static_function_not_exposed_is_ineligible() -> None:
    """verifies: TOOL-PAR-170 — static storage without the opt-in exposure
    capability is a named gate reason."""
    records = assess_eligibility([_unit(_fn("helper", storage_class="static"))])
    assert not records[0].eligible
    assert records[0].reasons == ("static_not_exposed",)


def test_static_function_eligible_with_exposure_flag() -> None:
    """verifies: TOOL-PAR-170 — the exposure capability flips the outcome."""
    records = assess_eligibility(
        [_unit(_fn("helper", storage_class="static"))],
        expose_static=True,
    )
    assert records[0].eligible
    assert records[0].reasons == ()


def test_no_observable_channel_is_ineligible() -> None:
    """verifies: TOOL-PAR-170 — no parameters, void return, no globals:
    nothing can be observed, so the function is not eligible."""
    records = assess_eligibility(
        [_unit(_fn("nop", return_type="ref:type.builtin.void"))],
        void_type_refs=_VOID,
    )
    assert not records[0].eligible
    assert records[0].reasons == ("no_observable_channel",)
    assert records[0].observable_channels == ()


def test_globals_alone_are_an_observable_channel() -> None:
    """verifies: TOOL-PAR-170 — a void function writing globals is observable
    through the globals channel."""
    records = assess_eligibility(
        [
            _unit(
                _fn(
                    "set_level",
                    return_type="ref:type.builtin.void",
                    globals_=(GlobalAccessModel(name="g_level", access="w"),),
                )
            )
        ],
        void_type_refs=_VOID,
    )
    assert records[0].eligible
    assert records[0].observable_channels == ("globals",)


def test_custom_void_refs_honored() -> None:
    """verifies: TOOL-PAR-170 — the void set is a caller-supplied contract, so
    type-graph naming stays decoupled from the gate: a custom void ref earns no
    return_value channel."""
    records = assess_eligibility(
        [
            _unit(
                _fn(
                    "f",
                    return_type="ref:type.my_void",
                    parameters=(ParameterModel(name="a", type="ref:type.int"),),
                )
            )
        ],
        void_type_refs=frozenset({"type.my_void"}),
    )
    assert records[0].observable_channels == ("parameters",)
    assert records[0].eligible


def test_discovery_does_not_imply_eligibility(tmp_path: Path) -> None:
    """verifies: TOOL-PAR-170, DSN-ANA-130 — a unit with mixed functions yields
    one record per function with mixed outcomes, in order."""
    unit = _unit(
        _fn("public_ok", parameters=(ParameterModel(name="a", type="ref:type.int"),)),
        _fn("secret", storage_class="static"),
        _fn("opaque", return_type="ref:type.builtin.void"),
    )
    records = assess_eligibility([unit])
    assert [r.function for r in records] == ["public_ok", "secret", "opaque"]
    assert [r.eligible for r in records] == [True, False, False]
    assert records[1].reasons == ("static_not_exposed",)
    assert records[2].reasons == ("no_observable_channel",)
    assert all(r.to_dict()["unit"] == "src/adc.c" for r in records)


def test_failed_unit_contributes_one_unmeasurable_unit_record() -> None:
    """verifies: TOOL-PAR-170, TOOL-PAR-130 — a failed unit is unmeasurable with its recorded reason.

    Changed from the pre-1.4 behaviour (no records): a failed unit now yields one
    unit-kind record so the gap is visible to CMP-ATG instead of silently absent.
    """
    unit = AnalysisUnit(
        path="src/broken.c",
        status="failed",
        failure=UnitFailureModel(reason="frontend_parse_error", code="FrontendParseError", category="analysis", message="expected ';'"),
    )
    records = assess_eligibility([unit])

    assert len(records) == 1
    assert records[0].kind == "unit"
    assert records[0].function == ""
    assert records[0].eligible is False
    assert records[0].reasons == ("frontend_parse_error",)
    assert records[0].to_dict()["unit"] == "src/broken.c"


def test_failed_unit_without_failure_record_uses_generic_reason() -> None:
    """verifies: TOOL-PAR-170 — a failed unit lacking a recorded reason still reports as unmeasurable."""
    records = assess_eligibility([AnalysisUnit(path="src/broken.c", status="failed")])

    assert [r.reasons for r in records] == [("unit_failed",)]

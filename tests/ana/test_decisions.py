# implements: TOOL-PAR-150
"""Decision and condition inventory (schema 1.6), checked against real GCC 14.4.0 output."""

from __future__ import annotations

import copy
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from ectt.ana.errors import AnalysisModelError
from ectt.ana.frontend import parse
from ectt.ana.interface import extract
from ectt.ana.model import AnalysisModel, AnalysisUnit
from ectt.ana.persist import assemble_analysis_model, read_analysis_model
from ectt.core.determinism import FixedClock

FIXTURES = Path(__file__).resolve().parents[1] / "cov" / "fixtures" / "gcc14"

Record = tuple[str, int, int]


def _unit(name: str) -> AnalysisUnit:
    return extract(parse(FIXTURES / f"{name}.c", args=["-std=gnu11"]), working_directory=FIXTURES)


def _from_gcc(name: str) -> Counter[Record]:
    document = json.loads((FIXTURES / f"{name}.gcov.json").read_text(encoding="utf-8"))
    return Counter(
        (line["function_name"], line["line_number"], condition["count"] // 2)
        for file in document["files"]
        for line in file["lines"]
        for condition in line.get("conditions", [])
    )


def _from_model(unit: AnalysisUnit) -> Counter[Record]:
    found: Counter[Record] = Counter()
    assert unit.decisions is not None
    for decision in unit.decisions:
        measured = sum(not condition.constant for condition in decision.conditions)
        if measured:
            found[(decision.function, decision.line, measured)] += 1
    return found


@pytest.mark.parametrize("name", ["mcdc", "shapes"])
def test_decisions_match_every_gcc_record(name: str) -> None:
    """verifies: TOOL-PAR-150 — function, line and condition count agree with GCC."""
    unit = _unit(name)
    assert unit.decisions_complete
    assert _from_model(unit) == _from_gcc(name)


def test_an_unnamed_construct_is_reported_incomplete_never_hidden() -> None:
    """GNU ``a ?: b`` is the one record the walk cannot name."""
    unit = _unit("lines")
    assert not unit.decisions_complete
    assert _from_gcc("lines") - _from_model(unit) == Counter({("gnu", 29, 1): 1})
    assert not _from_model(unit) - _from_gcc("lines")


def test_macro_and_constant_conditions_are_marked() -> None:
    unit = _unit("mcdc")
    assert unit.decisions is not None
    by_function = {decision.function: decision for decision in unit.decisions}
    assert by_function["macro"].macro
    assert [c.expression for c in by_function["macro"].conditions] == ["a", "b"]
    assert [c.constant for c in by_function["constant"].conditions] == [True]
    assert [c.expression for c in by_function["repeated"].conditions] == ["a", "b", "a", "b"]


def _model(name: str) -> AnalysisModel:
    unit = replace(_unit(name), path=f"{name}.c")
    return assemble_analysis_model([unit], source_root=FIXTURES, clock=FixedClock())


def test_model_round_trip_and_inventory_status() -> None:
    model = _model("mcdc")
    assert model.decision_inventory.status == "complete"
    read = read_analysis_model(json.loads(model.to_json()))
    assert read.units[0].decisions == model.units[0].decisions


def test_incomplete_unit_makes_the_inventory_partial() -> None:
    model = _model("lines")
    assert model.decision_inventory.status == "partial"


def _document() -> dict[str, Any]:
    model = _model("mcdc")
    loaded: dict[str, Any] = json.loads(model.to_json())
    return loaded


@pytest.mark.parametrize(
    "damage",
    [
        {"kind": "switch"},
        {"line": 0},
        {"conditions": []},
        {"conditions": [{"line": 1, "column": 1}]},
    ],
)
def test_malformed_decision_records_are_refused(damage: dict[str, Any]) -> None:
    document = copy.deepcopy(_document())
    document["units"][0]["decisions"][0].update(damage)
    with pytest.raises(AnalysisModelError) as refused:
        read_analysis_model(document)
    assert refused.value.reason == "invalid_decision_record"


def test_a_1_5_document_still_reads_with_no_inventory() -> None:
    document = _document()
    document["schema_version"] = "1.5"
    for unit in document["units"]:
        unit.pop("decisions")
    assert read_analysis_model(document).units[0].decisions is None

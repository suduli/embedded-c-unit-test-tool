# implements: TOOL-PAR-130, TOOL-PAR-140, DSN-ANA-090
"""Partial-failure resilience for the analysis run (WP-ANA-07, TASK-009).

A failure on one translation unit must not abort the run: the unit is recorded as
failed with a named reason from the ectt error model (TASK-006), every other unit is
still produced, and the reader and the eligibility gate treat the failed unit as
unmeasurable with that reason. Run-level errors still propagate.

Verifies: TOOL-PAR-130, TOOL-PAR-140.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from ectt.ana import interface as interface_module
from ectt.ana.eligibility import assess_eligibility
from ectt.ana.errors import (
    AnalysisModelError,
    ExtractionError,
    SourceFileNotFoundError,
)
from ectt.ana.frontend import parse
from ectt.ana.model import AnalysisUnit, UnitFailureModel, UnsupportedConstructModel
from ectt.ana.persist import (
    SCHEMA_VERSION_CURRENT,
    assemble_analysis_model,
    failed_unit_from_error,
    read_analysis_model,
)
from ectt.core.determinism import FixedClock

GOOD_A = b"int add(int a, int b) { return a + b; }\n"
BAD = b"int broken( {\n"
GOOD_B = b"int sub(int a, int b) { return a - b; }\n"

FILES = [("good_a.c", GOOD_A), ("bad.c", BAD), ("good_b.c", GOOD_B)]
DIGESTS = {"good_a.c": "a" * 64, "bad.c": "b" * 64, "good_b.c": "c" * 64}


def _parse_all() -> list[Any]:
    """Parse each file on its own, as a caller of the run would."""
    return [parse(name, args=["-std=gnu89"], unsaved_files=[(name, code)]) for name, code in FILES]


def _assemble(units: list[Any], digests: dict[str, str] | None = None) -> Any:
    return assemble_analysis_model(
        units,
        clock=FixedClock("2026-11-18T00:00:00Z"),
        input_digests=DIGESTS if digests is None else digests,
        tool_version="test",
        front_end="libclang",
    )


def _by_path(model: Any) -> dict[str, Any]:
    return {u.path: u for u in model.units}


def test_syntax_error_in_one_unit_leaves_the_valid_units_extracted() -> None:
    """verifies: TOOL-PAR-130 — the failed unit is recorded and the valid units are still produced."""
    model = _assemble(_parse_all())
    units = _by_path(model)

    assert [u.path for u in model.units] == ["good_a.c", "bad.c", "good_b.c"]
    assert units["good_a.c"].status == "parsed"
    assert units["good_b.c"].status == "parsed"
    assert [f.name for f in units["good_a.c"].functions] == ["add"]
    assert [f.name for f in units["good_b.c"].functions] == ["sub"]

    bad = units["bad.c"]
    assert bad.status == "failed"
    assert bad.functions == ()
    assert any(d.is_error for d in bad.diagnostics)
    assert bad.failure is not None
    assert bad.failure.reason == "frontend_parse_error"
    assert bad.failure.code == "FrontendParseError"
    assert bad.failure.category == "analysis"


def test_failure_inventory_is_deterministic_and_path_free(tmp_path: Any) -> None:
    """verifies: TOOL-PAR-130 — repeated runs are byte-identical and carry no absolute paths."""
    first = _assemble(_parse_all()).to_json()
    second = _assemble(_parse_all()).to_json()

    assert first == second
    assert str(tmp_path) not in first
    assert '"reason": "frontend_parse_error"' in first


def test_failed_unit_round_trips_through_the_1_4_reader() -> None:
    """verifies: TOOL-PAR-130 — a model with a failed unit is written and read back intact."""
    model = _assemble(_parse_all())
    doc = model.to_dict()

    assert doc["schema_version"] == SCHEMA_VERSION_CURRENT == "1.5"
    reloaded = read_analysis_model(doc)

    assert _by_path(reloaded)["bad.c"].failure == _by_path(model)["bad.c"].failure
    assert _by_path(reloaded)["bad.c"].unsupported_constructs == ()


def test_reader_rejects_failed_unit_without_a_failure_record() -> None:
    """verifies: TOOL-PAR-130 — fail-closed: a failed unit must name its reason."""
    doc = copy.deepcopy(_assemble(_parse_all()).to_dict())
    bad = next(u for u in doc["units"] if u["path"] == "bad.c")
    del bad["failure"]

    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(doc)
    assert exc_info.value.reason == "missing_unit_failure"


def test_reader_rejects_failure_record_on_a_parsed_unit() -> None:
    """verifies: TOOL-PAR-130 — a parsed unit carrying a failure is contradictory and rejected."""
    doc = copy.deepcopy(_assemble(_parse_all()).to_dict())
    good = next(u for u in doc["units"] if u["path"] == "good_a.c")
    good["failure"] = {"reason": "x", "code": "x", "category": "x", "message": "x"}

    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(doc)
    assert exc_info.value.reason == "unexpected_unit_failure"


def test_reader_rejects_functions_on_a_failed_unit() -> None:
    """verifies: TOOL-PAR-130 — a failed unit contributes no functions, so none may be read back."""
    doc = copy.deepcopy(_assemble(_parse_all()).to_dict())
    bad = next(u for u in doc["units"] if u["path"] == "bad.c")
    bad["functions"] = [copy.deepcopy(next(u for u in doc["units"] if u["path"] == "good_a.c")["functions"][0])]

    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(doc)
    assert exc_info.value.reason == "failed_unit_has_functions"


def test_missing_source_for_a_failed_unit_is_recorded_not_fatal() -> None:
    """verifies: TOOL-PAR-130 — a failed unit with no readable source does not abort the run."""
    missing = failed_unit_from_error("missing.c", SourceFileNotFoundError("not found", path="missing.c"))
    units: list[Any] = [*_parse_all()[:1], missing]

    model = _assemble(units, digests={"good_a.c": DIGESTS["good_a.c"]})

    assert _by_path(model)["missing.c"].failure is not None
    assert _by_path(model)["missing.c"].failure.reason == "source_file_not_found"
    assert [i.path for i in model.provenance.inputs] == ["good_a.c"]


def test_missing_source_for_a_parsed_unit_still_propagates() -> None:
    """verifies: TOOL-PAR-130 — only failed units may skip their digest; a parsed unit still fails the run."""
    parsed = AnalysisUnit(path="nowhere.c", status="parsed")

    with pytest.raises(SourceFileNotFoundError):
        _assemble([parsed], digests={})


def test_extraction_error_becomes_a_failed_unit_with_its_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    """verifies: TOOL-PAR-130 — a per-unit extraction error is recorded; the other units survive."""
    real_extract = interface_module.extract_interfaces

    def failing_for_good_b(ptu: Any, *args: Any, **kwargs: Any) -> Any:
        if ptu.source_path == "good_b.c":
            raise ExtractionError("extraction could not complete", reason="extraction_error")
        return real_extract(ptu, *args, **kwargs)

    monkeypatch.setattr(interface_module, "extract_interfaces", failing_for_good_b)
    model = _assemble(_parse_all())
    units = _by_path(model)

    assert units["good_b.c"].status == "failed"
    assert units["good_b.c"].failure is not None
    assert units["good_b.c"].failure.reason == "extraction_error"
    assert units["good_b.c"].failure.code == "ExtractionError"
    assert [f.name for f in units["good_a.c"].functions] == ["add"]


def test_run_level_errors_are_not_caught_as_unit_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    """verifies: TOOL-PAR-130 — an unexpected error is a defect, never reported as a unit failure."""

    def defect(ptu: Any, *args: Any, **kwargs: Any) -> Any:
        raise KeyError("internal defect")

    monkeypatch.setattr(interface_module, "extract_interfaces", defect)

    with pytest.raises(KeyError):
        _assemble(_parse_all())


def test_failed_unit_helper_refuses_errors_that_are_not_per_unit() -> None:
    """verifies: TOOL-PAR-130 — only per-unit failures may be turned into a failed unit."""
    with pytest.raises(TypeError):
        failed_unit_from_error("x.c", AnalysisModelError("model problem", reason="analysis_model_error"))


def test_failed_analysis_unit_without_a_reason_gets_a_generic_one() -> None:
    """verifies: TOOL-PAR-130 — a caller that gives no reason still produces a named failure record."""
    model = _assemble([AnalysisUnit(path="legacy.c", status="failed")], digests={"legacy.c": "d" * 64})

    failure = _by_path(model)["legacy.c"].failure
    assert failure is not None
    assert failure.reason == "unit_analysis_failed"


def test_unsupported_constructs_are_kept_through_assembly() -> None:
    """verifies: TOOL-PAR-140 — the per-unit unsupported-construct inventory is not dropped on assembly."""
    construct = UnsupportedConstructModel(kind="variadic_definition", count=2, detail="vararg tail")
    unit = AnalysisUnit(path="u.c", status="parsed", unsupported_constructs=(construct,))

    model = _assemble([unit], digests={"u.c": "e" * 64})

    assert _by_path(model)["u.c"].unsupported_constructs == (construct,)


def test_eligibility_reports_the_failed_unit_with_its_recorded_reason() -> None:
    """verifies: TOOL-PAR-130, TOOL-PAR-170 — the gate marks the failed unit unmeasurable with its reason."""
    model = _assemble(_parse_all())

    records = assess_eligibility(model.units)
    unit_records = [r for r in records if r.kind == "unit"]

    assert [(r.unit, r.reasons, r.eligible) for r in unit_records] == [("bad.c", ("frontend_parse_error",), False)]
    measured = {r.function for r in records if r.kind == "function"}
    assert {"add", "sub"} <= measured
    assert all(r.unit != "bad.c" for r in records if r.kind == "function")


def test_unit_failure_model_round_trips_as_a_plain_mapping() -> None:
    """verifies: TOOL-PAR-130 — the failure record serialises to the four named fields only."""
    failure = UnitFailureModel(reason="r", code="C", category="analysis", message="m")

    assert failure.to_dict() == {"reason": "r", "code": "C", "category": "analysis", "message": "m"}
    assert UnitFailureModel.from_dict(failure.to_dict()) == failure

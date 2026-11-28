# implements: TOOL-COV-050, TOOL-COV-060, TOOL-COV-070, TOOL-COV-080, TOOL-COV-190
"""Masking MC/DC results, on real GCC 14.4.0 output with hand-computed expectations."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from ectt.ana.frontend import parse
from ectt.ana.interface import extract
from ectt.ana.model import DecisionModel
from ectt.cov.errors import CoverageError
from ectt.cov.gcov import read_gcov_document
from ectt.cov.mcdc import McdcResult, measure_mcdc
from ectt.cov.merge import _merge_documents
from ectt.cov.model import GcovDocument

FIXTURES = Path(__file__).parent / "fixtures" / "gcc14"


def _document(name: str) -> GcovDocument:
    return read_gcov_document((FIXTURES / f"{name}.gcov.json").read_bytes())


def _decisions(name: str) -> tuple[DecisionModel, ...]:
    unit = extract(parse(FIXTURES / f"{name}.c", args=["-std=gnu11"]), working_directory=FIXTURES)
    assert unit.decisions is not None
    return unit.decisions


def _measure(name: str = "mcdc", **kwargs: object) -> McdcResult:
    kwargs.setdefault("decisions", _decisions(name))
    return measure_mcdc(_document(name), f"{name}.c", **kwargs)  # type: ignore[arg-type]


def _status(result: McdcResult, function: str) -> list[tuple[str | None, bool | None, bool | None]]:
    (decision,) = [d for d in result.decisions if d.function == function]
    return [(c.expression, c.seen_true, c.seen_false) for c in decision.conditions]


def test_hand_computed_condition_status() -> None:
    """Expected values follow from the calls made in mcdc.c's main.

    and2 is called (1,1) and (0,1): b is never false.
    side is called (1,n) and (0,n): the call to bump() is never false.
    macro is called (1,0) only: only b-false decides the outcome.
    unused is never called.
    """
    result = _measure()
    assert _status(result, "and2") == [("a", True, True), ("b", True, False)]
    assert _status(result, "side") == [("a", True, True), ("bump(n)", True, False)]
    assert _status(result, "macro") == [("a", False, False), ("b", False, True)]
    assert _status(result, "unused") == [("a", False, False), ("b", False, False)]


def test_totals_form_and_mechanism_are_stated() -> None:
    result = _measure()
    assert (result.status, result.form, result.mechanism) == ("measured", "masking", "gcc -fcondition-coverage")
    assert result.compiler_version == "14.4.0"
    assert (result.covered, result.total) == (12, 30)
    assert json.dumps(result.to_dict()) == json.dumps(_measure().to_dict())


def test_a_constant_decision_is_named_and_does_not_block_completeness() -> None:
    result = _measure()
    assert [(u.function, u.reason) for u in result.unmeasured] == [("constant", "constant_decision")]
    assert result.complete


def test_without_decisions_nothing_is_claimed_complete() -> None:
    result = _measure(decisions=None)
    assert result.status == "measured" and not result.decisions_known and not result.complete
    assert all(d.expression is None for d in result.decisions)
    assert all(c.seen_true is None for d in result.decisions for c in d.conditions)
    assert (result.covered, result.total) == (12, 30)


@pytest.mark.parametrize(("limit", "reason"), [(64, "over_condition_limit"), (None, "no_condition_record")])
def test_a_decision_over_the_probed_limit(limit: int | None, reason: str) -> None:
    """limit65.c has one decision GCC gave up on; it is never counted as covered."""
    result = _measure("limit65", max_conditions=limit)
    # no records at all: the file has decisions, so this is not "measured zero"
    assert (result.status, result.reason, result.total) == ("unmeasured", "no_condition_data", None)
    # the real file: the 65-condition decision is named, main's folded ternary too
    named = {u.function: (u.conditions, u.reason) for u in result.unmeasured}
    assert named["f"] == (65, reason)
    assert named["main"] == (1, "no_condition_record")
    # next to a measured decision it is named individually
    decisions = _decisions("mcdc") + tuple(replace(d, function="f", line=900, start_line=900, end_line=900)
                                           for d in _decisions("limit65") if len(d.conditions) == 65)
    mixed = _measure(decisions=decisions, max_conditions=limit)
    (skipped,) = [u for u in mixed.unmeasured if u.function == "f"]
    assert (skipped.reason, skipped.conditions) == (reason, 65)
    assert not mixed.complete


def test_64_conditions_are_measured() -> None:
    result = _measure("limit64", max_conditions=64)
    assert (result.covered, result.total) == (64, 128)


def test_records_that_cannot_be_told_apart_are_not_guessed() -> None:
    decisions = _decisions("mcdc")
    twin = next(d for d in decisions if d.function == "and2")
    result = _measure(decisions=(*decisions, twin))
    assert [u.reason for u in result.unmeasured if u.function == "and2"] == ["ambiguous_record"] * 2
    assert _status(result, "and2") == [(None, None, None), (None, None, None)]


@pytest.mark.parametrize(
    ("document", "kwargs", "reason"),
    [
        (None, {}, "no_coverage_data"),
        ("mcdc", {"unavailable_reason": "mcdc_not_available"}, "mcdc_not_available"),
    ],
)
def test_unavailable_is_unmeasured_never_zero(document: str | None, kwargs: dict[str, str], reason: str) -> None:
    loaded = None if document is None else _document(document)
    result = measure_mcdc(loaded, "mcdc.c", **kwargs)  # type: ignore[arg-type]
    assert (result.status, result.reason, result.covered, result.total) == ("unmeasured", reason, None, None)


def test_an_unknown_file_is_unmeasured() -> None:
    assert measure_mcdc(_document("mcdc"), "other.c").reason == "no_data_for_file"


def test_merging_runs_never_invents_coverage() -> None:
    """Regression: a term unseen both true and false was subtracted only once."""
    document = _document("mcdc")
    merged = _merge_documents([document, document])
    once = measure_mcdc(document, "mcdc.c")
    twice = measure_mcdc(merged, "mcdc.c")
    assert (twice.covered, twice.total) == (once.covered, once.total)


def test_an_inconsistent_record_is_refused() -> None:
    raw = json.loads((FIXTURES / "mcdc.gcov.json").read_text(encoding="utf-8"))
    record = next(line for line in raw["files"][0]["lines"] if line.get("conditions"))["conditions"][0]
    record["covered"] = record["count"]
    with pytest.raises(CoverageError) as refused:
        measure_mcdc(read_gcov_document(json.dumps(raw)), "mcdc.c")
    assert refused.value.reason == "inconsistent_condition_record"

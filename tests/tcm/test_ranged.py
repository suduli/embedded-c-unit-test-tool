"""Tests for ranged input expansion and robustness cases (WP-TCM-05).

Covers TOOL-TCD-070 and TOOL-TCD-130 per docs/verification/WP-TCM-05-analysis.md.
"""

from __future__ import annotations

import pytest

from ectt.tcm.datacases import (
    TestCaseExpected as TcmCaseExpected,
)
from ectt.tcm.datacases import (
    TestCaseInputs as TcmCaseInputs,
)
from ectt.tcm.datacases import (
    parse_test_cases_document,
    refresh_digest,
)
from ectt.tcm.errors import RangeCheckingError, RangeExpansionError
from ectt.tcm.ranged import (
    RangedInput,
    ValidRange,
    ensure_range_checking,
    expand_case,
    expand_integer_range,
    mark_robustness,
)

BASE_ID = "tc.adc.scan.0001"


def base_case(**overrides):  # type: ignore[no-untyped-def]
    from ectt.tcm.datacases import DataDrivenTestCase

    fields: dict = {
        "case_id": BASE_ID,
        "unit": "src/a.c",
        "function": "adc_read",
        "inputs": TcmCaseInputs(parameters={"ch": "0"}),
        "expected": TcmCaseExpected(return_value="0"),
        "stubs": (),
    }
    fields.update(overrides)
    return refresh_digest(DataDrivenTestCase(**fields))


# --- AC-1: one executed case per value ----------------------------------------


def test_integer_range_expands_inclusively() -> None:
    assert expand_integer_range("0", "3", "1") == ("0", "1", "2", "3")
    assert expand_integer_range("0", "10", "5") == ("0", "5", "10")  # hi included
    assert expand_integer_range("7", "7", "1") == ("7",)


def test_malformed_range_is_rejected() -> None:
    with pytest.raises(RangeExpansionError, match="step"):
        expand_integer_range("0", "4", "0")
    with pytest.raises(RangeExpansionError, match="exceeds"):
        expand_integer_range("5", "1", "1")
    with pytest.raises(RangeExpansionError, match="decimal integer"):
        expand_integer_range("010", "12", "1")


def test_ranged_input_expands_one_case_per_value() -> None:
    expanded = expand_case(base_case(), [RangedInput("ch", expand_integer_range("0", "3", "1"))])
    assert len(expanded) == 4
    assert [case.inputs.parameters["ch"] for case in expanded] == ["0", "1", "2", "3"]
    assert all(case.unit == "src/a.c" and case.function == "adc_read" for case in expanded)


def test_multiple_ranges_expand_cartesian() -> None:
    expanded = expand_case(
        base_case(),
        [
            RangedInput("ch", ("0", "1")),
            RangedInput("gain", ("8", "16")),
        ],
    )
    assert len(expanded) == 4
    ids = [case.case_id for case in expanded]
    assert ids[0] == f"{BASE_ID}.r.ch=0+gain=8"
    assert ids[-1] == f"{BASE_ID}.r.ch=1+gain=16"


def test_empty_range_expansion_is_rejected() -> None:
    with pytest.raises(RangeExpansionError, match="no values"):
        expand_case(base_case(), [RangedInput("ch", ())])


# --- AC-2: stable derived identifiers ------------------------------------------


def test_derived_identifiers_stable_under_reexpansion() -> None:
    first = expand_case(base_case(), [RangedInput("ch", expand_integer_range("0", "7", "1"))])
    second = expand_case(base_case(), [RangedInput("ch", expand_integer_range("0", "7", "1"))])
    assert [case.case_id for case in first] == [case.case_id for case in second]
    assert first[2].case_id == f"{BASE_ID}.r.ch=2"


# --- AC-3: expanded cases are digest-bound --------------------------------------


def test_expanded_cases_are_digest_bound() -> None:
    expanded = expand_case(base_case(), [RangedInput("ch", ("0", "1"))])
    for case in expanded:
        assert not case.stale
        assert case.recorded_digest == case.content_digest
    assert expanded[0].content_digest != expanded[1].content_digest


# --- AC-4: robustness marking and the tool's range check ------------------------


def test_robustness_marking_round_trips_and_joins_digest(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from ectt.tcm.datacases import (
        TestCasesFile as TcmCasesFile,
    )
    from ectt.tcm.datacases import (
        load_test_cases_file,
        save_test_cases_file,
    )

    marked = mark_robustness(base_case())
    assert marked.robustness is True
    assert not marked.stale
    target = tmp_path / "a.tests"
    save_test_cases_file(TcmCasesFile(schema_version=1, cases=(marked,)), target)
    loaded = load_test_cases_file(target)
    assert loaded.cases[0].robustness is True
    assert not loaded.cases[0].stale
    # marking is content: the digest moves, the id does not
    assert marked.case_id == BASE_ID
    assert marked.content_digest != base_case().content_digest
    # marking twice is idempotent
    assert mark_robustness(marked).recorded_digest == marked.recorded_digest


def test_range_check_refuses_out_of_range_on_normal_case() -> None:
    case = base_case(inputs=TcmCaseInputs(parameters={"ch": "99"}))
    with pytest.raises(RangeCheckingError, match="robustness"):
        ensure_range_checking(case, {"ch": ValidRange("0", "10")})
    # in-range values pass
    ensure_range_checking(base_case(), {"ch": ValidRange("0", "10")})
    # parameters without a declared range are not checked
    ensure_range_checking(case, {})


def test_range_check_allows_robustness_case() -> None:
    case = mark_robustness(base_case(inputs=TcmCaseInputs(parameters={"ch": "9999"})))
    ensure_range_checking(case, {"ch": ValidRange("0", "10")})  # no raise: exempt


# --- model integration -----------------------------------------------------------


def test_robustness_key_parses_and_validates() -> None:
    entry = {
        "id": "tc.x.0001",
        "unit": "src/a.c",
        "function": "f",
        "inputs": {},
        "expected": {},
        "stubs": {},
        "robustness": "true",
    }
    parsed = parse_test_cases_document({"schema_version": "1", "test_cases": [entry]})
    assert parsed.cases[0].robustness is True
    bad = dict(entry, robustness="maybe")
    with pytest.raises(Exception, match="robustness"):
        parse_test_cases_document({"schema_version": "1", "test_cases": [bad]})

"""Tests for suites and the shared selection expression (WP-TCM-04).

Covers TOOL-TCD-080 per docs/verification/WP-TCM-04-analysis.md, plus the
suite-membership model extension to the WP-TCM-02 record.
"""

from __future__ import annotations

import pytest

from ectt.tcm.datacases import (
    TestCasesFile as TcmCasesFile,
)
from ectt.tcm.datacases import (
    dump_test_cases_document,
    load_test_cases_file,
    parse_test_cases_document,
    refresh_digest,
    save_test_cases_file,
)
from ectt.tcm.errors import InvalidSelectionError
from ectt.tcm.selection import Selection, partition_cases


def case_dict(**overrides):  # type: ignore[no-untyped-def]
    entry = {
        "id": "tc.adc.nominal.0001",
        "unit": "src/a.c",
        "function": "adc_read",
        "inputs": {"parameters": {"ch": "1"}},
        "expected": {"return": "0"},
        "stubs": {},
        "suites": ["smoke"],
    }
    entry.update(overrides)
    return entry


def file_dict(cases):  # type: ignore[no-untyped-def]
    return {"schema_version": "1", "test_cases": cases}


def fresh_cases():  # type: ignore[no-untyped-def]
    parsed = parse_test_cases_document(
        file_dict(
            [
                case_dict(),
                case_dict(id="tc.adc.edge.0002", function="adc_read", suites=["smoke", "edge"]),
                case_dict(id="tc.pwm.nominal.0003", unit="src/b.c", function="pwm_set", suites=[]),
                case_dict(id="tc.pwm.edge.0004", unit="src/b.c", function="pwm_set", suites=["edge"]),
            ]
        )
    )
    return tuple(refresh_digest(case) for case in parsed.cases)


# --- AC-1: suite membership on the model -------------------------------------


def test_suites_survive_round_trip_and_join_digest(tmp_path) -> None:  # type: ignore[no-untyped-def]
    parsed = parse_test_cases_document(file_dict([case_dict()]))
    case = refresh_digest(parsed.cases[0])
    assert case.suites == ("smoke",)
    target = tmp_path / "a.tests"
    save_test_cases_file(TcmCasesFile(schema_version=1, cases=(case,)), target)
    loaded = load_test_cases_file(target)
    assert loaded.cases[0].suites == ("smoke",)
    assert dump_test_cases_document(loaded) == dump_test_cases_file_helper(case)

    # membership is content: editing it changes the digest, never the id
    rejoined = refresh_digest(
        type(case)(
            case_id=case.case_id,
            unit=case.unit,
            function=case.function,
            inputs=case.inputs,
            expected=case.expected,
            stubs=case.stubs,
            origin=case.origin,
            requirements=case.requirements,
            suites=("smoke", "regression"),
        )
    )
    assert rejoined.case_id == case.case_id
    assert rejoined.content_digest != case.content_digest


def dump_test_cases_file_helper(case):  # type: ignore[no-untyped-def]
    return dump_test_cases_document(TcmCasesFile(schema_version=1, cases=(case,)))


# --- AC-2: one selection expression ------------------------------------------


def test_selection_by_each_dimension() -> None:
    cases = fresh_cases()
    selected, excluded = partition_cases(cases, Selection(suites=("edge",)))
    assert [c.case_id for c in selected] == ["tc.adc.edge.0002", "tc.pwm.edge.0004"]
    assert len(excluded) == 2
    selected, _ = partition_cases(cases, Selection(units=("src/b.c",)))
    assert [c.case_id for c in selected] == ["tc.pwm.nominal.0003", "tc.pwm.edge.0004"]
    selected, _ = partition_cases(cases, Selection(functions=("adc_read",)))
    assert [c.case_id for c in selected] == ["tc.adc.nominal.0001", "tc.adc.edge.0002"]
    selected, _ = partition_cases(cases, Selection(test_ids=("tc.pwm.nominal.0003",)))
    assert [c.case_id for c in selected] == ["tc.pwm.nominal.0003"]


def test_selection_or_across_dimensions() -> None:
    cases = fresh_cases()
    selected, _ = partition_cases(
        cases, Selection(suites=("smoke",), units=("src/b.c",))
    )
    assert [c.case_id for c in selected] == [
        "tc.adc.nominal.0001",
        "tc.adc.edge.0002",
        "tc.pwm.nominal.0003",
        "tc.pwm.edge.0004",
    ]
    # within a dimension, multiple values are OR
    selected, _ = partition_cases(cases, Selection(functions=("adc_read", "pwm_set")))
    assert len(selected) == 4


def test_empty_selection_selects_everything() -> None:
    cases = fresh_cases()
    selected, excluded = partition_cases(cases, Selection())
    assert len(selected) == 4
    assert excluded == ()
    assert Selection().is_empty


def test_partition_is_deterministic() -> None:
    cases = fresh_cases()
    one = partition_cases(cases, Selection(suites=("edge",)))
    two = partition_cases(cases, Selection(suites=("edge",)))
    assert one == two


def test_malformed_selection_is_rejected() -> None:
    with pytest.raises(InvalidSelectionError):
        Selection(suites=("  ",))
    with pytest.raises(InvalidSelectionError, match="suites"):
        Selection(suites=("",))

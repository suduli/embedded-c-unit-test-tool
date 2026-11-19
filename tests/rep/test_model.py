# implements: TOOL-REP-090, TOOL-REP-100
"""Report model construction, persistence, and validation (WP-REP-01)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from ectt.core.determinism import FixedClock
from ectt.exh.results import (
    AssertionFailure,
    ExecutionMetadata,
    ResultSet,
    SourceLocation,
    finalize_result,
)
from ectt.rep.errors import ReportModelError
from ectt.rep.model import (
    REPORT_MODEL_SCHEMA_VERSION,
    ReportModel,
    build_report_model,
    coverage_entry,
    dump_report_model,
    load_report_model,
)
from ectt.rep.model import (
    test_entry as make_test_entry,
)

CLOCK = FixedClock("2026-11-19T00:00:00+00:00")

_FAILURE = AssertionFailure(
    assertion="assert_equal",
    expected="0",
    actual="1",
    location=SourceLocation(file="test_alpha.c", line=42),
)


def _result_set(**overrides: Any) -> ResultSet:
    params: dict[str, Any] = {
        "run_id": "run-1",
        "execution": ExecutionMetadata(where="host", toolchain="gcc"),
        "results": (
            finalize_result("test.beta", "pass", "d2" * 32),
            finalize_result("test.alpha", "fail", "d1" * 32, failures=(_FAILURE,)),
        ),
        "not_executed": ("test.gamma",),
        "partial": False,
    }
    params.update(overrides)
    return ResultSet(**params)


def _model(**overrides: Any) -> ReportModel:
    return build_report_model(
        _result_set(**overrides),
        coverage=(coverage_entry("src/adc.c", 8, 10),),
        clock=CLOCK,
    )


# --- construction ----------------------------------------------------------------------


def test_build_aggregates_statuses_sorted() -> None:
    model = _model()

    assert [e.test_id for e in model.tests] == ["test.alpha", "test.beta", "test.gamma"]
    assert model.test_statuses() == {
        "test.alpha": "fail",
        "test.beta": "pass",
        "test.gamma": "not_run",
    }
    assert model.run_id == "run-1"
    assert model.partial is False


def test_build_refuses_duplicate_result() -> None:
    rs = _result_set(
        results=(
            finalize_result("t1", "pass", "d1" * 32),
            finalize_result("t1", "fail", "d1" * 32, failures=(_FAILURE,)),
        )
    )
    with pytest.raises(ReportModelError) as excinfo:
        build_report_model(rs, clock=CLOCK)
    assert excinfo.value.reason == "duplicate_test"


def test_build_refuses_result_and_not_executed_conflict() -> None:
    rs = _result_set(results=(finalize_result("t1", "pass", "d1" * 32),), not_executed=("t1",))
    with pytest.raises(ReportModelError) as excinfo:
        build_report_model(rs, clock=CLOCK)
    assert excinfo.value.reason == "conflicting_test_state"


def test_build_refuses_duplicate_coverage() -> None:
    with pytest.raises(ReportModelError) as excinfo:
        build_report_model(
            _result_set(),
            coverage=(coverage_entry("src/a.c", 1, 2), coverage_entry("src/a.c", 3, 4)),
            clock=CLOCK,
        )
    assert excinfo.value.reason == "duplicate_coverage"


def test_coverage_entry_validation() -> None:
    assert coverage_entry("u", 0, 0).total == 0
    with pytest.raises(ReportModelError):
        coverage_entry("u", 3, 2)  # covered > total
    with pytest.raises(ReportModelError):
        coverage_entry("u", -1, 2)
    with pytest.raises(ReportModelError):
        coverage_entry("u", 1, -1)
    with pytest.raises(ReportModelError):
        coverage_entry("u", 1.5, 2)  # type: ignore[arg-type]


def test_test_entry_validation() -> None:
    assert make_test_entry("t", "not_run", "").status == "not_run"
    with pytest.raises(ReportModelError) as excinfo:
        make_test_entry("t", "flaky", "d" * 64)
    assert excinfo.value.reason == "invalid_status"
    with pytest.raises(ReportModelError) as excinfo:
        make_test_entry("t", "pass", "")
    assert excinfo.value.reason == "missing_digest"


def test_ids_reject_whitespace() -> None:
    with pytest.raises(ReportModelError) as excinfo:
        make_test_entry("a b", "not_run")
    assert excinfo.value.reason == "invalid_id"
    with pytest.raises(ReportModelError):
        coverage_entry("a b", 1, 2)


# --- identity (D-02: stable ids plus content digests) ----------------------------------


def test_report_id_stable_and_discriminating() -> None:
    first = _model()
    second = _model()
    assert first.report_id == second.report_id  # identical inputs, identical id

    changed = build_report_model(
        _result_set(),
        coverage=(coverage_entry("src/adc.c", 9, 10),),
        clock=CLOCK,
    )
    assert changed.report_id != first.report_id

    retested = build_report_model(
        _result_set(results=(finalize_result("test.beta", "pass", "d2" * 32), finalize_result("test.alpha", "pass", "d1" * 32))),
        coverage=(coverage_entry("src/adc.c", 8, 10),),
        clock=CLOCK,
    )
    assert retested.report_id != first.report_id


# --- persistence (byte-deterministic) --------------------------------------------------


def test_dump_is_byte_deterministic() -> None:
    model = _model()

    assert dump_report_model(model) == dump_report_model(model)
    text = dump_report_model(model)
    assert text.splitlines()[0] == "{"
    assert text.splitlines()[1] == '  "schema_version": "1.0",'
    assert "\r" not in text
    doc = json.loads(text)
    assert doc["schema_version"] == REPORT_MODEL_SCHEMA_VERSION


def test_roundtrip_preserves_model() -> None:
    model = _model()

    loaded = load_report_model(dump_report_model(model))

    assert loaded == model
    assert loaded.generated_at == model.generated_at
    assert loaded.report_id == model.report_id


def test_load_accepts_bytes_and_mapping() -> None:
    model = _model()
    text = dump_report_model(model)

    assert load_report_model(text.encode("utf-8")) == model
    assert load_report_model(json.loads(text)) == model


def test_load_refuses_tampered_status() -> None:
    model = _model()
    doc = json.loads(dump_report_model(model))
    doc["tests"][0]["status"] = "pass"

    with pytest.raises(ReportModelError) as excinfo:
        load_report_model(doc)
    assert excinfo.value.reason == "digest_mismatch"


def test_load_refuses_unknown_schema_version() -> None:
    model = _model()
    doc = json.loads(dump_report_model(model))
    doc["schema_version"] = "9.9"

    with pytest.raises(ReportModelError) as excinfo:
        load_report_model(doc)
    assert excinfo.value.reason == "incompatible_schema_version"


def test_load_refuses_missing_field() -> None:
    model = _model()
    doc: dict[str, Any] = json.loads(dump_report_model(model))
    del doc["run_id"]

    with pytest.raises(ReportModelError) as excinfo:
        load_report_model(doc)
    assert excinfo.value.reason == "missing_field"


def test_load_refuses_duplicate_test_entry() -> None:
    model = _model()
    doc = json.loads(dump_report_model(model))
    doc["tests"].append(dict(doc["tests"][0]))
    # Keep the stored report id stale on purpose: the duplicate is rejected
    # before the digest check runs.
    with pytest.raises(ReportModelError) as excinfo:
        load_report_model(doc)
    assert excinfo.value.reason == "duplicate_test"

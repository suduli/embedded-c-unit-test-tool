# implements: TOOL-REP-150
"""Report generation from archived result data (WP-REP-09).

State transition under test: archived record -> integrity check -> result
revalidation -> report model -> rendered bytes. No test is re-executed at
any step; the only input is the archived document.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from ectt.core.determinism import FixedClock
from ectt.exh.errors import InvalidResultRecordError
from ectt.exh.results import (
    AssertionFailure,
    ExecutionMetadata,
    ResultSet,
    SourceLocation,
    finalize_result,
    result_set_to_dict,
)
from ectt.prj.archive import ArchiveError, build_archive_record, dump_archive_record
from ectt.rep.errors import ReportModelError
from ectt.rep.from_archive import report_from_archive, result_set_from_dict
from ectt.rep.model import (
    CoverageEntry,
    build_report_model,
    dump_report_model,
    load_report_model,
)
from ectt.rep.render import render_text

CLOCK = FixedClock("2026-11-19T00:00:00+00:00")
REGEN_CLOCK = FixedClock("2027-01-01T00:00:00+00:00")  # a later regeneration

_FAILURE = AssertionFailure(
    assertion="assert_equal",
    expected="0",
    actual="1",
    location=SourceLocation(file="t2.c", line=7),
)


def _result_set() -> ResultSet:
    return ResultSet(
        run_id="run-arch",
        execution=ExecutionMetadata(where="host", toolchain="gcc", target_id="tgt-1"),
        results=(
            finalize_result("t1", "pass", "d1" * 32),
            finalize_result("t2", "fail", "d2" * 32, failures=(_FAILURE,)),
        ),
        not_executed=("t3",),
    )


def _archive_text() -> str:
    record = build_archive_record(
        configuration={"schema_version": 1, "name": "demo"},
        clock=CLOCK,
        result_set=_result_set(),
        coverage=({"unit": "src/adc.c", "covered": 8, "total": 10},),
    )
    return dump_archive_record(record)


def test_report_from_archive_matches_the_original_content() -> None:
    """The original report and the regenerated one agree on every fact."""
    original = build_report_model(
        _result_set(),
        coverage=(CoverageEntry(unit="src/adc.c", covered=8, total=10),),
        clock=CLOCK,
    )
    rebuilt = report_from_archive(_archive_text(), clock=REGEN_CLOCK)

    assert rebuilt.test_statuses() == original.test_statuses()
    assert rebuilt.coverage_figures() == original.coverage_figures()
    assert rebuilt.run_id == original.run_id
    # The hashed provenance matches: same facts, timestamps excluded.
    assert rebuilt.provenance is not None and original.provenance is not None
    assert rebuilt.provenance.digest == original.provenance.digest
    assert rebuilt.provenance.input_digests["result_set"] == original.provenance.input_digests["result_set"]
    # Only the timestamps differ (regeneration happened later).
    assert rebuilt.generated_at != original.generated_at


def test_rebuilt_report_round_trips_and_renders_deterministically() -> None:
    report = report_from_archive(_archive_text(), clock=REGEN_CLOCK)
    text = dump_report_model(report)

    assert load_report_model(text) == report
    assert render_text(report) == render_text(report)


def test_only_the_archive_document_is_consumed() -> None:
    """TOOL-REP-150: no ResultSet object is needed to build the report."""
    report = report_from_archive(json.loads(_archive_text()), clock=REGEN_CLOCK)

    assert report.test_statuses() == {"t1": "pass", "t2": "fail", "t3": "not_run"}


def test_archive_without_result_set_is_refused() -> None:
    record = build_archive_record(configuration={"schema_version": 1, "name": "demo"}, clock=CLOCK)

    with pytest.raises(ReportModelError) as excinfo:
        report_from_archive(dump_archive_record(record), clock=CLOCK)
    assert excinfo.value.reason == "missing_result_set"


def test_corrupt_archive_is_refused_before_reporting() -> None:
    doc: dict[str, Any] = json.loads(_archive_text())
    doc["result_set"]["run_id"] = "tampered"

    with pytest.raises(ArchiveError):
        report_from_archive(doc, clock=CLOCK)


def test_invalid_archived_outcome_is_refused_at_revalidation() -> None:
    """An outcome the runner boundary never produced cannot be smuggled in."""
    doc: dict[str, Any] = result_set_to_dict(_result_set())
    doc["results"][0]["outcome"] = "flaky"

    with pytest.raises(InvalidResultRecordError):
        result_set_from_dict(doc)


def test_bare_result_set_dictionary_rebuilds_identically() -> None:
    rebuilt = result_set_from_dict(result_set_to_dict(_result_set()))

    assert rebuilt == _result_set()

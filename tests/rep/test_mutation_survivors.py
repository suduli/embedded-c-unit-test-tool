# implements: TOOL-REP-070, TOOL-REP-110, TOOL-REP-120, TOOL-REP-150
"""Tests added for mutants of ``ectt.rep`` that the first battery did not kill (TEST-MUT2).

Each test names the seeded fault it was written against (see
``docs/glm-night/overnight-20261120/mutation-rep-trc.md``).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ectt.exh.results import ExecutionMetadata, ResultSet, result_set_to_dict
from ectt.rep.errors import ReportModelError
from ectt.rep.from_archive import result_set_from_dict
from ectt.rep.model import CoverageEntry
from ectt.rep.render import render_text
from ectt.rep.summary import build_coverage_trend, build_cross_run_summary
from tests.rep.test_summary import _model, _pass


def test_trend_is_ordered_by_recorded_time_before_run_id() -> None:
    """M51: a run with the later id but the earlier time comes first."""
    earlier_but_later_id = _model("run-b", generated_at="2026-11-01T00:00:00+00:00")
    later_but_earlier_id = _model("run-a", generated_at="2026-11-02T00:00:00+00:00")

    trend = build_coverage_trend([later_but_earlier_id, earlier_but_later_id])

    assert [p.run_id for p in trend.points] == ["run-b", "run-a"]


def test_trend_ties_on_time_are_broken_by_run_id() -> None:
    same = "2026-11-01T00:00:00+00:00"
    trend = build_coverage_trend([_model("run-b", generated_at=same), _model("run-a", generated_at=same)])
    assert [p.run_id for p in trend.points] == ["run-a", "run-b"]


def test_trend_total_sums_the_total_not_the_covered_figures() -> None:
    """M53 (killed before) stays pinned with distinct covered and total."""
    model = _model("r1", coverage=(CoverageEntry("a.c", 1, 4), CoverageEntry("b.c", 2, 6)))
    (point,) = build_coverage_trend([model]).points
    assert (point.covered, point.total) == (3, 10)


def test_summary_tests_total_counts_tests_not_runs() -> None:
    """M55: two runs with two and three tests total five tests."""
    two = _model("run-1", results=(_pass("t_a"), _pass("t_b")))
    three = _model("run-2", results=(_pass("t_a"), _pass("t_b"), _pass("t_c")))

    summary = build_cross_run_summary([two, three])

    assert summary.tests_total == 5
    assert [run.tests for run in summary.runs] == [2, 3]


def test_text_report_counts_coverage_units_not_tests() -> None:
    """M60: two tests and one coverage unit read ``coverage: 1 units``."""
    model = _model("r1", results=(_pass("t_a"), _pass("t_b")), coverage=(CoverageEntry("src/a.c", 1, 2),))

    text = render_text(model)

    assert "coverage: 1 units" in text
    assert "tests: 2 pass=2" in text


def test_missing_execution_time_is_shown_as_unknown() -> None:
    """M46: a provenance record without ``generated_at`` reports ``unknown``, not blank."""
    model = _model("r1")
    assert model.provenance is not None
    undated = replace(model, provenance=replace(model.provenance, generated_at=None))

    assert undated.provenance_facts()["executed_at"] == "unknown"


def test_archived_partial_flag_is_kept() -> None:
    """M65: a partial archived run stays partial after reconstruction."""
    result_set = ResultSet(
        run_id="run-1",
        execution=ExecutionMetadata(where="host", toolchain="gcc"),
        results=(_pass("t_a"),),
        not_executed=("t_b",),
        partial=True,
    )

    rebuilt = result_set_from_dict(result_set_to_dict(result_set))

    assert rebuilt.partial is True
    assert rebuilt.not_executed == ("t_b",)
    assert result_set_from_dict(result_set_to_dict(replace(result_set, partial=False, not_executed=()))).partial is False


@pytest.mark.parametrize("field", ["where", "toolchain"])
def test_archived_execution_facts_must_both_be_non_empty(field: str) -> None:
    """M66: an empty toolchain (or where) is refused, not accepted."""
    doc = result_set_to_dict(
        ResultSet(run_id="run-1", execution=ExecutionMetadata(where="host", toolchain="gcc"), results=(_pass("t_a"),))
    )
    doc["execution"][field] = ""

    with pytest.raises(ReportModelError) as excinfo:
        result_set_from_dict(doc)
    assert excinfo.value.reason == "invalid_field"

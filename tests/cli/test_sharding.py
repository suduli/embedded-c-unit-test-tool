# implements: TOOL-CIC-060
"""CI sharding and report merge (WP-CLI-05).

Equivalence partitioning over suite/runner shapes for sharding, and over
shard-report combinations for the merge: disjoint suites, repeated tests,
agreeing and conflicting coverage totals, partial shards.
"""

from __future__ import annotations

import pytest

from ectt.cli.errors import CliError
from ectt.cli.sharding import merge_reports, shard_suite
from ectt.core.determinism import FixedClock
from ectt.exh.results import ExecutionMetadata, ResultSet, finalize_result
from ectt.rep.errors import ReportModelError
from ectt.rep.model import (
    CoverageEntry,
    ReportModel,
    build_report_model,
    dump_report_model,
    load_report_model,
)

CLOCK = FixedClock("2026-11-19T00:00:00+00:00")

SIX = [f"test.{i}" for i in range(6)]


def _shard_report(run_id: str, test_ids: tuple[str, ...], *, coverage=(), partial: bool = False) -> ReportModel:
    result_set = ResultSet(
        run_id=run_id,
        execution=ExecutionMetadata(where=f"runner-{run_id}", toolchain="gcc"),
        results=tuple(finalize_result(t, "pass", t.replace(".", "") * 12) for t in test_ids),
        partial=partial,
    )
    return build_report_model(result_set, coverage=coverage, clock=CLOCK)


# --- sharding partitions ---------------------------------------------------------------


def test_six_tests_over_three_runners_balance_exactly() -> None:
    shards = shard_suite(SIX, 3)

    assert [len(shard) for shard in shards] == [2, 2, 2]
    assert shards[0] == ("test.0", "test.3")


def test_partition_is_complete_and_disjoint() -> None:
    shards = shard_suite(SIX, 4)

    merged = [t for shard in shards for t in shard]
    assert sorted(merged) == sorted(SIX)
    assert len(merged) == len(set(merged))


def test_partition_is_input_order_free() -> None:
    assert shard_suite(list(reversed(SIX)), 3) == shard_suite(SIX, 3)
    assert shard_suite(SIX, 3) == shard_suite(SIX, 3)  # deterministic


@pytest.mark.parametrize("count", [0, -1, 1.5, True])
def test_invalid_shard_counts_are_refused(count: object) -> None:
    with pytest.raises(CliError) as excinfo:
        shard_suite(SIX, count)  # type: ignore[arg-type]
    assert excinfo.value.reason == "invalid_shard_count"


def test_single_runner_takes_everything() -> None:
    shards = shard_suite(SIX, 1)

    assert shards == (tuple(SIX),)


def test_more_runners_than_tests_yields_empty_trailing_shards() -> None:
    shards = shard_suite(["a", "b"], 4)

    assert [len(shard) for shard in shards] == [1, 1, 0, 0]
    assert shards[0] == ("a",)
    assert shards[3] == ()


def test_empty_suite_partitions_into_empty_shards() -> None:
    assert shard_suite([], 2) == ((), ())


# --- report merge ----------------------------------------------------------------------


def test_merge_unions_tests_and_run_ids() -> None:
    first = _shard_report("run-a", ("t1", "t2"), coverage=(CoverageEntry(unit="u.c", covered=3, total=5),))
    second = _shard_report("run-b", ("t3",), coverage=(CoverageEntry(unit="u.c", covered=1, total=5),))

    merged = merge_reports([first, second], clock=CLOCK)

    assert merged.run_id == "run-a+run-b"
    assert merged.test_statuses() == {"t1": "pass", "t2": "pass", "t3": "pass"}
    assert merged.coverage_figures() == {"u.c": (3, 5)}  # max: lower bound on the union


def test_merge_is_input_order_free_and_deterministic() -> None:
    first = _shard_report("run-a", ("t1",))
    second = _shard_report("run-b", ("t2",))

    forward = merge_reports([first, second], clock=CLOCK)
    backward = merge_reports([second, first], clock=CLOCK)

    assert forward.run_id == backward.run_id
    assert forward.test_statuses() == backward.test_statuses()
    assert forward.coverage == backward.coverage


def test_merge_refuses_a_test_that_ran_twice() -> None:
    first = _shard_report("run-a", ("t1",))
    second = _shard_report("run-b", ("t1",))

    with pytest.raises(ReportModelError) as excinfo:
        merge_reports([first, second], clock=CLOCK)
    assert excinfo.value.reason == "duplicate_test"


def test_merge_refuses_conflicting_coverage_totals() -> None:
    first = _shard_report("run-a", ("t1",), coverage=(CoverageEntry(unit="u.c", covered=1, total=5),))
    second = _shard_report("run-b", ("t2",), coverage=(CoverageEntry(unit="u.c", covered=1, total=9),))

    with pytest.raises(ReportModelError) as excinfo:
        merge_reports([first, second], clock=CLOCK)
    assert excinfo.value.reason == "conflicting_coverage"


def test_merge_records_partial_when_any_shard_is_partial() -> None:
    first = _shard_report("run-a", ("t1",))
    second = _shard_report("run-b", ("t2",), partial=True)

    merged = merge_reports([first, second], clock=CLOCK)

    assert merged.partial is True


def test_merge_of_nothing_is_refused() -> None:
    with pytest.raises(CliError) as excinfo:
        merge_reports([], clock=CLOCK)
    assert excinfo.value.reason == "no_reports"


def test_merged_report_dumps_deterministically() -> None:
    first = _shard_report("run-a", ("t1",), coverage=(CoverageEntry(unit="u.c", covered=2, total=4),))
    second = _shard_report("run-b", ("t2",), coverage=(CoverageEntry(unit="u.c", covered=3, total=4),))

    merged = merge_reports([first, second], clock=CLOCK)

    assert dump_report_model(merged) == dump_report_model(merged)


def test_merged_report_roundtrip_loads_without_execution() -> None:
    """A merged run has no single runner: 'execution' is optional on read."""
    merged = merge_reports([_shard_report("run-a", ("t1",)), _shard_report("run-b", ("t2",))], clock=CLOCK)

    loaded = load_report_model(dump_report_model(merged))

    assert loaded == merged
    assert loaded.execution is None
    assert loaded.provenance is not None


def test_merged_report_without_provenance_is_still_refused() -> None:
    import json

    merged = merge_reports([_shard_report("run-a", ("t1",))], clock=CLOCK)
    doc = json.loads(dump_report_model(merged))
    del doc["provenance"]

    with pytest.raises(ReportModelError) as excinfo:
        load_report_model(doc)
    assert excinfo.value.reason == "missing_field"


def test_report_with_execution_still_roundtrips_and_validates_it() -> None:
    import json

    single = _shard_report("run-a", ("t1",))
    assert load_report_model(dump_report_model(single)).execution == single.execution

    doc = json.loads(dump_report_model(single))
    doc["execution"] = {"where": "", "toolchain": "gcc"}
    with pytest.raises(ReportModelError):
        load_report_model(doc)


def test_end_to_end_shard_then_merge_reproduces_the_whole_suite() -> None:
    """verifies: TOOL-CIC-060 — shard across runners, merge the reports back."""
    whole = _shard_report("single", tuple(SIX))
    shards = shard_suite(SIX, 3)
    shard_reports = [
        _shard_report(f"shard-{i}", tuple(shard)) for i, shard in enumerate(shards)
    ]

    merged = merge_reports(shard_reports, clock=CLOCK)

    assert merged.test_statuses() == whole.test_statuses()
    assert len(merged.test_statuses()) == len(SIX)
    assert merged.run_id == "shard-0+shard-1+shard-2"


def test_merged_report_id_and_dump_are_input_order_free() -> None:
    first = _shard_report("run-a", ("t1",))
    second = _shard_report("run-b", ("t2",))

    forward = merge_reports([first, second], clock=CLOCK)
    backward = merge_reports([second, first], clock=CLOCK)

    assert forward.report_id == backward.report_id
    assert dump_report_model(forward) == dump_report_model(backward)

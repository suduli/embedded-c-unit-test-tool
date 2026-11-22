# implements: TOOL-CBT-030, TOOL-CBT-040
"""Subset execution of a recorded suite (WP-CBT-02).

The subset runs exactly the selected tests through the shared integrity gate
(no regeneration, binary integrity enforced, per-test isolation), gets its own
run id, and states its partiality as data: every unselected test of the suite
is named, and the suite-level view of the result set is marked partial.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from ectt.cbt import (
    CbtError,
    bindings_from_cases,
    record_compiled_suite,
    reexecute_subset,
)
from ectt.exh.results import ExecutionMetadata
from ectt.tcm import datacases as dd

EXECUTION = ExecutionMetadata(where="host", toolchain="gcc-14.2")

ISOLATED_HARNESS = (
    "import sys\n"
    "args = sys.argv[1:]\n"
    "tid = args[args.index('--ectt-select') + 1] if '--ectt-select' in args else None\n"
    "for name, outcome in (('tc.a', 'pass'), ('tc.b', 'pass'), ('tc.c', 'pass'), ('tc.d', 'fail')):\n"
    "    if tid == name or tid is None:\n"
    "        print(f'RESULT {name} {outcome}')\n"
    "        if outcome == 'fail':\n"
    "            print(f'FAILURE {name} expected_return 1 0 src/a.c 9')\n"
)


def _case(case_id: str, expected: str = "1") -> dd.DataDrivenTestCase:
    return dd.refresh_digest(
        dd.DataDrivenTestCase(
            case_id=case_id,
            unit="src/a.c",
            function="f",
            inputs=dd.TestCaseInputs(),
            expected=dd.TestCaseExpected(return_value=expected),
            stubs=(),
        )
    )


CASES = [_case("tc.a"), _case("tc.b"), _case("tc.c"), _case("tc.d")]
CURRENT = {c.case_id: c.content_digest for c in CASES}


def _suite(tmp_path: Path) -> tuple[Path, Any]:
    root = tmp_path / "proj"
    (root / "build").mkdir(parents=True)
    exe = root / "build" / "harness"
    exe.write_text(ISOLATED_HARNESS, encoding="utf-8")
    record = record_compiled_suite(root, "build/harness", EXECUTION, bindings_from_cases(CASES))
    return root, record


def test_a_subset_runs_exactly_the_selected_tests(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-030 — only the selected tests execute, each in its own
    process; tc.d (which fails) is not selected, so its result never appears."""
    root, record = _suite(tmp_path)
    subset = reexecute_subset(
        record,
        root,
        CURRENT,
        subset=("tc.a", "tc.b"),
        run_label="affected",
        timeout_seconds=30,
        argv_prefix=(sys.executable,),
    )
    assert [r.test_id for r in subset.reexecution.run.result_set.results] == ["tc.a", "tc.b"]
    assert subset.reexecution.run.outcome == "pass"
    assert subset.reexecution.run.result_set.results[0].outcome == "pass"


def test_the_subset_attempt_has_its_own_run_id(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-030, AC-5 — a subset run and the full run of the same
    record under the same label never share a run id, and the id is stable."""
    root, record = _suite(tmp_path)
    first = reexecute_subset(
        record, root, CURRENT, subset=("tc.a",), run_label="r1", timeout_seconds=30, argv_prefix=(sys.executable,)
    )
    second = reexecute_subset(
        record, root, CURRENT, subset=("tc.a",), run_label="r1", timeout_seconds=30, argv_prefix=(sys.executable,)
    )
    full = record.execution()
    assert first.reexecution.run.attempt.attempt_id == second.reexecution.run.attempt.attempt_id
    assert first.reexecution.run.attempt.attempt_id != record.record_id
    assert len({first.reexecution.run.attempt.attempt_id}) == 1
    # The full-suite attempt id (computed without running anything) differs.
    from ectt.exh.runner import allocate_attempt, mark_built

    full_attempt = mark_built(allocate_attempt(full, record.bindings))
    assert first.reexecution.run.attempt.attempt_id != full_attempt.attempt_id


def test_a_changed_binary_is_refused_for_a_subset_too(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-030 — the integrity gate is the full re-execution's."""
    root, record = _suite(tmp_path)
    (root / "build" / "harness").write_text("# rebuilt with different content\n", encoding="utf-8")
    with pytest.raises(CbtError) as excinfo:
        reexecute_subset(
            record, root, CURRENT, subset=("tc.a",), run_label="affected", timeout_seconds=30
        )
    assert excinfo.value.reason == "executable_changed"


def test_an_empty_selection_is_refused(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-030 — running nothing is not a run."""
    root, record = _suite(tmp_path)
    with pytest.raises(CbtError) as excinfo:
        reexecute_subset(record, root, CURRENT, subset=(), run_label="affected", timeout_seconds=30)
    assert excinfo.value.reason == "no_selection"


def test_an_unknown_test_id_is_refused(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-030 — the selection comes from the record's own ids."""
    root, record = _suite(tmp_path)
    with pytest.raises(CbtError) as excinfo:
        reexecute_subset(
            record, root, CURRENT, subset=("tc.a", "tc.ghost"), run_label="affected", timeout_seconds=30
        )
    assert excinfo.value.reason == "unknown_selection"
    assert "tc.ghost" in excinfo.value.message


def test_a_duplicated_selection_is_refused(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-030 — each test is selected at most once."""
    root, record = _suite(tmp_path)
    with pytest.raises(CbtError) as excinfo:
        reexecute_subset(
            record, root, CURRENT, subset=("tc.a", "tc.a"), run_label="affected", timeout_seconds=30
        )
    assert excinfo.value.reason == "duplicate_selection"


def test_the_selection_is_deterministic(tmp_path: Path) -> None:
    """verifies: AC-5 — same selection, same run id, whatever the order given."""
    root, record = _suite(tmp_path)
    forward = reexecute_subset(
        record, root, CURRENT, subset=("tc.a", "tc.b"), run_label="r", timeout_seconds=30, argv_prefix=(sys.executable,)
    )
    reverse = reexecute_subset(
        record, root, CURRENT, subset=("tc.b", "tc.a"), run_label="r", timeout_seconds=30, argv_prefix=(sys.executable,)
    )
    assert forward.reexecution.run.attempt.attempt_id == reverse.reexecution.run.attempt.attempt_id
    assert forward.selected == reverse.selected == ("tc.a", "tc.b")


def test_the_subset_run_states_its_partiality_and_names_the_unselected(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-040 — not_selected is the record minus the selection,
    computed from the record, not from what the harness reported."""
    root, record = _suite(tmp_path)
    subset = reexecute_subset(
        record, root, CURRENT, subset=("tc.a",), run_label="affected", timeout_seconds=30, argv_prefix=(sys.executable,)
    )
    assert subset.partial is True
    assert subset.selected == ("tc.a",)
    assert subset.not_selected == ("tc.b", "tc.c", "tc.d")


def test_the_suite_view_marks_the_run_partial_with_the_unselected_listed(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-040 — the suite-level view of a subset run is partial
    and lists every unselected test as not executed, so no report can read the
    subset run as a full pass."""
    root, record = _suite(tmp_path)
    subset = reexecute_subset(
        record, root, CURRENT, subset=("tc.a", "tc.b"), run_label="affected", timeout_seconds=30, argv_prefix=(sys.executable,)
    )
    view = subset.suite_view
    assert view.partial is True
    assert set(view.not_executed) == {"tc.c", "tc.d"}
    assert view.run_id == subset.reexecution.run.attempt.attempt_id


def test_a_full_selection_is_not_partial(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-040 — selecting the whole suite is not a subset run."""
    root, record = _suite(tmp_path)
    everything = tuple(c.case_id for c in CASES)
    subset = reexecute_subset(
        record, root, CURRENT, subset=everything, run_label="full", timeout_seconds=30, argv_prefix=(sys.executable,)
    )
    assert subset.partial is False
    assert subset.not_selected == ()
    assert subset.suite_view.partial is False

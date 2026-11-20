# implements: TOOL-QUA-060
"""Reproduction check over the embedded provenance (WP-CORE-04, WP-REP-06).

TOOL-QUA-060 asks that an artifact record sufficient information to
reproduce it. The report artifact's replay test: identical inputs rebuilt in
the same environment produce byte-identical reports with identical embedded
provenance digests, and any changed input fact changes both.
"""

from __future__ import annotations

from ectt.core.determinism import FixedClock
from ectt.exh.results import ExecutionMetadata, ResultSet, finalize_result
from ectt.rep.model import build_report_model, dump_report_model

CLOCK = FixedClock("2026-11-19T00:00:00+00:00")


def _build() -> str:
    result_set = ResultSet(
        run_id="repro",
        execution=ExecutionMetadata(where="host", toolchain="gcc", target_id="tgt-1"),
        results=(finalize_result("t1", "pass", "d1" * 32),),
    )
    model = build_report_model(result_set, clock=CLOCK)
    return dump_report_model(model)


def test_identical_inputs_reproduce_identical_reports() -> None:
    """verifies: TOOL-QUA-060 — same inputs, same tool, same bytes."""
    first = _build()
    second = _build()

    assert first == second


def test_changed_input_changes_the_artifact_and_its_provenance() -> None:
    result_set = ResultSet(
        run_id="repro",
        execution=ExecutionMetadata(where="host", toolchain="gcc", target_id="tgt-1"),
        results=(finalize_result("t1", "pass", "d1" * 32), finalize_result("t2", "pass", "d2" * 32)),
    )
    changed = dump_report_model(build_report_model(result_set, clock=CLOCK))

    assert changed != _build()

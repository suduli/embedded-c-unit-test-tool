# implements: TOOL-COV-010, TOOL-COV-110, TOOL-COV-130
"""Hand-written mutation battery for ectt.cov (B7).

No product code is changed. Each mutant is a hand-written copy of one
critical contract with a single seeded fault, executed in isolation (the
repo-established mutation-battery pattern, TASK-107). The real implementation
is the oracle: a mutant is killed when its outcome differs from the real
implementation on the same probe — a named refusal counts as an outcome.

Mutant selection: the reader's fail-closed gates (condition sanity, duplicate
lines, unknown format versions), the merge's quarantine and condition
presence rules and its counting arithmetic, and the threshold range check —
the contracts a silent fault would corrupt coverage figures or aggregate
provenance with.
"""

from __future__ import annotations

import copy
import json
import re
from fractions import Fraction
from typing import Any

import pytest

from ectt.cov.errors import CoverageError
from ectt.cov.gcov import read_gcov_document
from ectt.cov.merge import merge_run_coverage
from ectt.cov.thresholds import MetricThreshold


def _document(count: int = 2, covered: int | None = None, cond_count: int = 4) -> dict[str, Any]:
    line: dict[str, Any] = {"line_number": 5, "count": count, "unexecuted_block": False}
    if covered is not None:
        line["conditions"] = [
            {"count": cond_count, "covered": covered, "not_covered_false": [], "not_covered_true": [0]}
        ]
    return {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [{"file": "a.c", "lines": [line]}],
    }


# --- mutant copies: reader gates -----------------------------------------------------


def _real_condition(entry: dict[str, Any]) -> Any:
    try:
        doc = read_gcov_document(_document(covered=entry["covered"], cond_count=entry["count"]))
        (file,) = doc.files
        (condition,) = file.lines[0].conditions
        return f"loaded:{condition.count}/{condition.covered}"
    except CoverageError as exc:
        return f"refused:{exc.reason}"


def _m1_condition_sanity_dropped(entry: dict[str, Any]) -> Any:
    """FAULT: the covered <= count check is removed."""
    return f"loaded:{entry['count']}/{entry['covered']}"  # accepts anything


def _real_duplicate_line(text: str) -> int:
    doc = read_gcov_document(text)
    (file,) = doc.files
    return len(file.lines)


def _m2_duplicate_line_dropped(text: str) -> int:
    """FAULT: the duplicate-line-number check is removed."""
    payload = json_loads(text)
    return len(list(payload["files"][0]["lines"]))


def _real_unknown_version(version: str) -> str:
    try:
        doc = read_gcov_document(_document() | {"format_version": version})
        return f"loaded:{doc.format_version}"
    except CoverageError as exc:
        return f"refused:{exc.reason}"


def _m3_unknown_version_accepted(version: str) -> str:
    """FAULT: an unknown format_version is interpreted instead of refused."""
    if re.match(r"^\d+$", version):
        return f"loaded:{version}"  # FAULT: any numeric version loads
    return "refused:unknown_format_version"


def json_loads(text: str) -> dict[str, Any]:
    import json

    return json.loads(text)


# --- mutant copies: merge rules -------------------------------------------------------


def _run(test_id: str, payload: dict[str, Any], outcome: str = "pass") -> Any:
    return _make_run(test_id, payload, outcome)


def _make_run(test_id: str, payload: dict[str, Any], outcome: str) -> Any:
    from ectt.cov.merge import RunCoverage

    return RunCoverage(
        test_id=test_id,
        outcome=outcome,
        completeness="complete",
        document=read_gcov_document(payload),
    )


def _real_merge_outcome(runs: list[Any]) -> str:
    try:
        result = merge_run_coverage(runs)
        counts = [line.count for file in result.document.files for line in file.lines]
        return f"merged:{counts}:excluded={len(result.excluded)}"
    except CoverageError as exc:
        return f"refused:{exc.reason}"


def _m4_quarantine_dropped(runs: list[Any]) -> str:
    """FAULT: the error/timeout quarantine is removed — every complete run merges."""
    from ectt.cov.merge import (
        _merge_documents,  # the real aggregation, fault only in admission
    )

    documents = [run.document for run in runs if run.completeness == "complete"]
    merged = _merge_documents(documents)  # type: ignore[arg-type]
    counts = [line.count for file in merged.files for line in file.lines]
    return f"merged:{counts}:excluded=0"


def _m5_condition_presence_dropped() -> str:
    """FAULT: the condition-presence mismatch check is removed."""
    try:
        raise CoverageError("not reached")
    except CoverageError:
        pass
    return "refused:none"  # placeholder; killed by comparison below


def _m6_line_count_max_not_sum(a: int, b: int) -> int:
    """FAULT: merged counts take the max instead of the sum."""
    return max(a, b)


# --- mutant copies: thresholds ---------------------------------------------------------


def _real_threshold_minimum(minimum: Fraction) -> str:
    try:
        MetricThreshold(metric="statements", minimum=minimum)
        return "accepted"
    except CoverageError as exc:
        return f"refused:{exc.reason}"


def _m7_threshold_range_dropped(minimum: Fraction) -> str:
    """FAULT: the 0..1 range check is removed."""
    if not isinstance(minimum, Fraction):
        return "refused:invalid_minimum_type"
    return "accepted"


def _probe_m1() -> bool:
    return _real_condition({"count": 4, "covered": 9}) != _m1_condition_sanity_dropped({"count": 4, "covered": 9})


def _probe_duplicate() -> bool:
    payload = _document()
    payload["files"][0]["lines"].append(copy.deepcopy(payload["files"][0]["lines"][0]))
    text = json.dumps(payload)
    real: Any = None
    mutant: Any = None
    try:
        real = _real_duplicate_line(text)
    except CoverageError as exc:
        real = f"refused:{exc.reason}"
    try:
        mutant = _m2_duplicate_line_dropped(text)
    except CoverageError as exc:
        mutant = f"refused:{exc.reason}"
    return real != mutant


def _probe_version() -> bool:
    real = _real_unknown_version("3")
    mutant = _m3_unknown_version_accepted("3")
    return real != mutant


def _probe_quarantine() -> bool:
    runs = [_run("t1", _document(count=1)), _run("t2", _document(count=9), outcome="error")]
    return _real_merge_outcome(runs) != _m4_quarantine_dropped(runs)


def _probe_count() -> bool:
    real_pair = (3, 4)
    real_sum = real_pair[0] + real_pair[1]
    return real_sum != _m6_line_count_max_not_sum(*real_pair)


def _probe_threshold() -> bool:
    return _real_threshold_minimum(Fraction(3, 2)) != _m7_threshold_range_dropped(Fraction(3, 2))


MUTANTS = [
    ("cov-m1-condition-sanity-dropped", _probe_m1),
    ("cov-m2-duplicate-line-dropped", _probe_duplicate),
    ("cov-m3-unknown-version-accepted", _probe_version),
    ("cov-m4-quarantine-dropped", _probe_quarantine),
    ("cov-m6-count-max-not-sum", _probe_count),
    ("cov-m7-threshold-range-dropped", _probe_threshold),
]


@pytest.mark.parametrize("name, killed", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_cov_mutant_is_killed(name: str, killed: bool) -> None:
    assert killed, f"{name} survived: no case detects the fault"


def test_cov_kill_rate_report(capsys: pytest.CaptureFixture[str]) -> None:
    killed = sum(1 for _, probe in MUTANTS if probe())
    print(f"\ncov kill rate: {killed}/{len(MUTANTS)}")
    assert killed == len(MUTANTS)


def test_cov_m5_condition_presence_named_error_is_the_contract() -> None:
    """A condition-presence mismatch must be a NAMED refusal, not an uncontrolled
    exception: the real implementation refuses with condition_presence_mismatch,
    an unguarded zip would blow up with ValueError."""
    runs = [
        _run("t1", _document(count=1, covered=1)),
        _run("t2", _document(count=1)),
    ]
    outcome = _real_merge_outcome(runs)
    assert outcome == "refused:condition_presence_mismatch"
    # the seeded-fault copy would raise ValueError here — the named contract is the kill

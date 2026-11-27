# implements: TOOL-REP-060, TOOL-REP-140
"""Certification verification report and scope statement (WP-REP-05).

A report built from result, coverage and trace data states what it covers and
what it does NOT claim. Missing data is named, never filled; a claim the data
does not support is refused; the output is byte-stable.
"""

from __future__ import annotations

import dataclasses
from fractions import Fraction
from typing import Any

import pytest

from ectt.core.provenance import ProvenanceRecord
from ectt.cov.justification import Justification
from ectt.cov.model import MetricTotals
from ectt.cov.thresholds import MetricThreshold, ThresholdResult, enforce_thresholds
from ectt.exh.results import finalize_result
from ectt.ext.profile import record_host_profile
from ectt.rep import model as rep_model
from ectt.rep.certification import (
    CERTIFICATION_CLAIMS,
    CertificationInputs,
    build_certification_report,
)
from ectt.rep.errors import ReportModelError
from ectt.rep.model import (
    CoverageEntry,
    ReportModel,
    build_report_model,
    make_report_model,
)
from ectt.trc import AssociationSet, build_matrix
from ectt.trc.matrix import RequirementRow, TraceabilityMatrix
from tests.rep.test_renderers import _FAILURE, CLOCK, _result_set

_UNIT = "src/adc.c"
_DIGEST = "ab" * 32
_CREATION_TIME = "2099-01-01T00:00:00+00:00"

_SUPPORTABLE = ("all_tests_executed", "all_tests_passed", "coverage_criteria_met", "requirements_verified")


def _executed(test_id: str) -> Any:
    return finalize_result(test_id, "pass", test_id.encode("ascii").hex() * 24)


def _model(
    *,
    extra_executed: tuple[str, ...] = (),
    not_executed: tuple[str, ...] = (),
    partial: bool = False,
    failing: str | None = None,
) -> ReportModel:
    results = [_executed("t.a"), _executed("t.b"), *(_executed(test) for test in extra_executed)]
    if failing is not None:
        results.append(finalize_result(failing, "fail", "df" * 32, failures=(_FAILURE,)))
    return build_report_model(
        _result_set(tuple(results), not_executed=not_executed, partial=partial),
        coverage=(CoverageEntry(unit=_UNIT, covered=8, total=10),),
        clock=CLOCK,
    )


def _metrics() -> dict[str, MetricTotals]:
    return {"statements": MetricTotals(covered=8, total=10), "branches": MetricTotals(covered=0, total=None)}


def _criteria(metrics: dict[str, MetricTotals] | None = None, *, passed: bool = True) -> ThresholdResult:
    metrics = _metrics() if metrics is None else metrics
    statements_minimum = Fraction(4, 5) if passed else Fraction(1, 1)
    return enforce_thresholds(
        metrics,
        [
            MetricThreshold(metric="statements", minimum=statements_minimum),
            MetricThreshold(metric="branches", minimum=Fraction(1, 2)),
        ],
        allow_not_applicable=("branches",),
    )


def _matrix(
    pairs: tuple[tuple[str, str], ...] = (("REQ-1", "t.a"), ("REQ-2", "t.b")),
    *,
    passing: tuple[str, ...] = ("t.a", "t.b"),
) -> TraceabilityMatrix:
    """A matrix over ``pairs``; a linked test outside ``passing`` has no recorded status."""
    associations = AssociationSet()
    for requirement, test in pairs:
        associations.add(requirement, test)
    return build_matrix(associations, dict.fromkeys(passing, "pass"))


_UNVERIFIED_MATRIX = (("REQ-1", "t.a"), ("REQ-9", "t.unrun"))


def _justification(justification_id: str = "J-1") -> Justification:
    return Justification(
        id=justification_id,
        file=_UNIT,
        start_line=40,
        end_line=41,
        author="safety engineer",
        date="2026-11-20",
        rationale="unreachable without a hardware fault",
        source_digest=_DIGEST,
    )


def _host_profile() -> Any:
    return record_host_profile(
        name="linux-x86-proxy",
        target_triple="arm-none-eabi",
        host_triple="x86_64-linux-gnu",
        unavailable_hardware_behavior="the access is diagnosed and the test fails",
        abi={"width": "int: 32 both"},
    )


def _complete() -> CertificationInputs:
    return CertificationInputs(
        model=_model(),
        coverage_metrics=_metrics(),
        coverage_criteria=_criteria(),
        traceability=_matrix(),
        justifications=(_justification(),),
        source_digests={_UNIT: _DIGEST},
        host_profile=_host_profile(),
    )


# --- complete data -----------------------------------------------------------------------


def test_complete_data_records_every_required_element() -> None:
    """verifies: TOOL-REP-060 — tool identification, configuration, tests with
    results, coverage per metric, justified exclusions, traceability matrix."""
    report = build_certification_report(_complete(), claims=_SUPPORTABLE)
    document = report.to_dict()

    assert report.missing_inputs == ()
    assert document["tool"]["status"] == "identified"
    assert document["tool"]["version"] and document["tool"]["version"] != "unknown"
    assert document["tool"]["provenance_digest"]

    run = document["run"]
    assert run["execution"]["toolchain"] == "gcc"
    assert run["execution"]["executed_at"] == CLOCK.isoformat()
    assert [(t["test_id"], t["status"]) for t in run["tests"]] == [("t.a", "pass"), ("t.b", "pass")]
    assert run["status_counts"] == {"pass": 2, "fail": 0, "error": 0, "timeout": 0, "not_run": 0}
    assert run["host_profile"]["label"] == _host_profile().label
    # a dimension the profile never measured is unknown, never "same"
    assert run["host_profile"]["abi"]["width"] == "int: 32 both"
    assert run["host_profile"]["abi"]["endianness"] == "unknown"

    coverage = document["coverage"]
    assert coverage["achieved"]["statements"] == {"covered": 8, "total": 10}
    assert coverage["criteria"]["passed"] is True
    assert coverage["unmeasured"] == []
    assert coverage["not_applicable"] == ["branches"]

    exclusions = document["justified_exclusions"]
    assert exclusions["status"] == "recorded"
    assert [(e["id"], e["author"], e["date"], e["rationale"]) for e in exclusions["valid"]] == [
        ("J-1", "safety engineer", "2026-11-20", "unreachable without a hardware fault")
    ]

    trace = document["traceability"]
    assert trace["pair_count"] == 2
    assert [(row["requirement_id"], row["verdict"]) for row in trace["rows"]] == [
        ("REQ-1", "pass"),
        ("REQ-2", "pass"),
    ]

    assert report.claims == tuple(sorted(_SUPPORTABLE))
    assert set(report.not_claimed) == {"target_executed", "mcdc_measured"}


# --- each missing input named, never filled ------------------------------------------------


_MISSING_CASES = [
    ("model", {"results", "tool_identification", "unit_scope"}),
    ("coverage_metrics", {"coverage_metrics"}),
    ("coverage_criteria", {"coverage_criteria"}),
    ("traceability", {"traceability"}),
    ("justifications", {"justified_exclusions"}),
    ("source_digests", {"source_digests"}),
]


@pytest.mark.parametrize(("field", "expected"), _MISSING_CASES, ids=[case[0] for case in _MISSING_CASES])
def test_each_missing_input_is_named_and_nothing_else_is(field: str, expected: set[str]) -> None:
    """verifies: TOOL-REP-060 — a missing input is named; the rest is unaffected."""
    inputs: CertificationInputs = dataclasses.replace(_complete(), **{field: None})
    report = build_certification_report(inputs)
    assert set(report.missing_inputs) == expected


def test_missing_results_are_stated_as_missing_never_filled() -> None:
    document = build_certification_report(dataclasses.replace(_complete(), model=None)).to_dict()
    assert document["run"] == {"status": "missing"}
    assert document["tool"] == {"status": "missing"}
    assert document["scope"]["tests"] == {"status": "missing", "count": None}
    assert document["scope"]["units"] == {"status": "missing", "units": []}
    excluded = document["scope"]["excluded"]
    assert excluded["tests_not_executed"] is None  # not determinable, not "none"
    assert excluded["run_is_partial"] is None


def test_missing_coverage_is_stated_as_missing_never_filled() -> None:
    coverage = build_certification_report(
        dataclasses.replace(_complete(), coverage_metrics=None)
    ).to_dict()["coverage"]
    assert coverage["status"] == "missing"
    assert coverage["achieved"] is None
    assert coverage["unmeasured"] is None and coverage["not_applicable"] is None
    assert coverage["not_measured"] == ["statements", "branches", "functions", "calls", "mcdc"]


def test_missing_criteria_never_read_as_met() -> None:
    document = build_certification_report(
        dataclasses.replace(_complete(), coverage_criteria=None)
    ).to_dict()
    assert document["coverage"]["criteria"] == {"status": "not_stated", "passed": None, "evaluations": None}
    # with no stated criterion an empty metric is unmeasured, not "not applicable"
    assert document["coverage"]["unmeasured"] == ["branches"]
    assert document["coverage"]["not_applicable"] == []


def test_missing_traceability_leaves_the_exclusions_undeterminable() -> None:
    document = build_certification_report(
        dataclasses.replace(_complete(), traceability=None)
    ).to_dict()
    assert document["traceability"] == {"status": "missing"}
    assert document["scope"]["requirements"] == {"status": "missing", "count": None}
    excluded = document["scope"]["excluded"]
    assert excluded["tests_not_traced_to_any_requirement"] is None
    assert excluded["requirements_not_verified"] is None


def test_a_justification_without_a_current_digest_is_not_an_exclusion() -> None:
    exclusions = build_certification_report(
        dataclasses.replace(_complete(), source_digests=None)
    ).to_dict()["justified_exclusions"]
    assert exclusions["valid"] == []
    assert [entry["id"] for entry in exclusions["unverifiable"]] == ["J-1"]


def test_nothing_supplied_names_every_missing_input_and_claims_nothing() -> None:
    report = build_certification_report(CertificationInputs())
    assert set(report.missing_inputs) == {
        "results",
        "tool_identification",
        "unit_scope",
        "coverage_metrics",
        "coverage_criteria",
        "traceability",
        "justified_exclusions",
    }
    assert report.claims == ()
    assert set(report.not_claimed) == set(CERTIFICATION_CLAIMS)
    document = report.to_dict()
    assert document["coverage"]["criteria"]["passed"] is None
    assert document["scope"]["tests"]["count"] is None


def test_an_absent_host_profile_is_not_missing_data() -> None:
    """A host profile is context only a host run on behalf of a target carries."""
    report = build_certification_report(dataclasses.replace(_complete(), host_profile=None))
    assert report.missing_inputs == ()
    assert report.to_dict()["run"]["host_profile"] is None


def test_data_gaps_inside_the_result_model_are_named() -> None:
    """A result model that itself lacks provenance, execution facts or units."""
    bare = make_report_model(
        run_id="run-bare",
        tests=(rep_model.test_entry("t.a", "pass", "da" * 32),),
        coverage=(),
        partial=False,
        generated_at=_CREATION_TIME,
        execution=None,
        provenance=None,
    )
    document = build_certification_report(dataclasses.replace(_complete(), model=bare)).to_dict()
    assert set(document["missing_inputs"]) == {
        "tool_identification",
        "execution_facts",
        "execution_timestamp",
        "unit_scope",
    }
    assert document["tool"] == {"status": "missing"}
    assert document["run"]["execution"] == {"status": "missing", "executed_at": None}
    assert document["run"]["status"] == "recorded"  # the results themselves are present


def test_an_unidentified_tool_is_named() -> None:
    model = _model()
    unidentified = make_report_model(
        run_id=model.run_id,
        tests=model.tests,
        coverage=model.coverage,
        partial=False,
        generated_at=CLOCK.isoformat(),
        execution=model.execution,
        provenance=ProvenanceRecord(
            tool_version="unknown", build_id="unset", python_version="3.13", generated_at=CLOCK.isoformat()
        ),
    )
    document = build_certification_report(dataclasses.replace(_complete(), model=unidentified)).to_dict()
    assert "tool_identification" in document["missing_inputs"]
    assert document["tool"]["status"] == "unidentified"
    assert document["tool"]["version"] == "unknown"  # recorded as recorded


# --- byte-stable output --------------------------------------------------------------------


def test_output_is_byte_stable_under_input_order() -> None:
    """verifies: TOOL-REP-100 — identical inputs in any order give identical bytes."""
    two = (_justification("J-1"), _justification("J-0"))
    base = dataclasses.replace(_complete(), justifications=two)
    reversed_metrics = dict(reversed(list(_metrics().items())))
    other = dataclasses.replace(
        base,
        model=_model(),  # a freshly built, equal model
        coverage_metrics=reversed_metrics,
        coverage_criteria=_criteria(reversed_metrics),
        traceability=_matrix((("REQ-2", "t.b"), ("REQ-1", "t.a"))),
        justifications=tuple(reversed(two)),
    )
    first = build_certification_report(base, claims=_SUPPORTABLE).to_json_bytes()
    assert first == build_certification_report(base, claims=_SUPPORTABLE).to_json_bytes()
    assert first == build_certification_report(other, claims=tuple(reversed(_SUPPORTABLE))).to_json_bytes()


def test_the_report_creation_timestamp_is_not_rendered() -> None:
    """The execution timestamp is model content (TOOL-REP-070); the report-creation
    timestamp is not rendered."""
    model = _model()
    re_dated = make_report_model(
        run_id=model.run_id,
        tests=model.tests,
        coverage=model.coverage,
        partial=False,
        generated_at=_CREATION_TIME,
        execution=model.execution,
        provenance=model.provenance,
    )
    rendered = build_certification_report(dataclasses.replace(_complete(), model=re_dated)).to_json_bytes()
    assert _CREATION_TIME.encode("ascii") not in rendered
    assert CLOCK.isoformat().encode("ascii") in rendered


def test_the_dictionary_is_a_fresh_copy() -> None:
    report = build_certification_report(_complete())
    document = report.to_dict()
    document["claims"].append("target_executed")
    document["run"]["tests"].clear()
    assert report.claims == ()
    assert report.to_dict()["run"]["tests"]


# --- a claim not supported by data is refused -------------------------------------------------


_UNSUPPORTED = [
    ("target_executed", {}, "no target-execution record exists"),
    ("mcdc_measured", {}, "MC/DC is not measured"),
    ("all_tests_executed", {"model": _model(not_executed=("t.z",), partial=True)}, "1 test(s) were not executed"),
    ("all_tests_passed", {"model": _model(failing="t.f")}, "1 test(s) did not pass"),
    ("coverage_criteria_met", {"coverage_criteria": None}, "no coverage criteria are stated"),
    ("coverage_criteria_met", {"coverage_metrics": None}, "no coverage data is supplied"),
    (
        "coverage_criteria_met",
        {"coverage_criteria": ThresholdResult(evaluations=(), passed=True)},
        "no coverage criterion is evaluated",
    ),
    ("coverage_criteria_met", {"coverage_criteria": _criteria(passed=False)}, "a stated coverage criterion is not met"),
    ("requirements_verified", {"traceability": None}, "no traceability data is supplied"),
    ("requirements_verified", {"traceability": _matrix(_UNVERIFIED_MATRIX)}, "1 requirement(s) are not verified"),
]


@pytest.mark.parametrize(
    ("claim", "overrides", "why"),
    _UNSUPPORTED,
    ids=[f"{case[0]}-{index}" for index, case in enumerate(_UNSUPPORTED)],
)
def test_a_claim_not_supported_by_data_is_refused(claim: str, overrides: dict[str, Any], why: str) -> None:
    """verifies: TOOL-REP-140 — an unsupported claim is refused, never written."""
    inputs: CertificationInputs = dataclasses.replace(_complete(), **overrides)
    with pytest.raises(ReportModelError) as exc_info:
        build_certification_report(inputs, claims=(claim,))
    assert exc_info.value.reason == "claim_not_supported"
    assert exc_info.value.context["claim"] == claim
    assert why in str(exc_info.value)


def test_target_execution_is_refused_even_for_a_host_run_on_behalf_of_a_target() -> None:
    """A host profile labels a host run; it is not evidence of execution on the target."""
    inputs = _complete()  # carries a host profile for target arm-none-eabi
    with pytest.raises(ReportModelError) as exc_info:
        build_certification_report(inputs, claims=("target_executed",))
    assert exc_info.value.reason == "claim_not_supported"
    assert _host_profile().label in str(exc_info.value)
    assert "TOOL-TGT-130" in str(exc_info.value)
    # the report states the same when the claim is simply not made
    reason = build_certification_report(inputs).not_claimed["target_executed"]
    assert "no target-execution record" in reason and "TOOL-TGT-130" in reason


@pytest.mark.parametrize("claim", ["everything_is_fine", "", "mcdc", 42, None, ["all_tests_passed"]])
def test_an_unknown_claim_is_refused(claim: Any) -> None:
    with pytest.raises(ReportModelError) as exc_info:
        build_certification_report(_complete(), claims=(claim,))
    assert exc_info.value.reason == "unknown_claim"


@pytest.mark.parametrize("metric", ["mcdc", "conditions"])
def test_a_metric_the_report_cannot_carry_is_refused(metric: str) -> None:
    """MC/DC cannot be smuggled in as a figure: no data class measures it."""
    inputs = dataclasses.replace(_complete(), coverage_metrics={metric: MetricTotals(covered=1, total=2)})
    with pytest.raises(ReportModelError) as exc_info:
        build_certification_report(inputs)
    assert exc_info.value.reason == "unknown_metric"


def test_a_criteria_verdict_from_other_figures_is_refused() -> None:
    inputs = dataclasses.replace(_complete(), coverage_metrics={"statements": MetricTotals(covered=5, total=10)})
    with pytest.raises(ReportModelError) as exc_info:
        build_certification_report(inputs)
    assert exc_info.value.reason == "criteria_metrics_mismatch"


def test_a_requirement_verdict_outside_the_trace_vocabulary_is_refused() -> None:
    matrix = TraceabilityMatrix(
        rows=(RequirementRow(requirement_id="REQ-1", links=(), verdict="maybe"),), pair_count=0
    )
    with pytest.raises(ReportModelError) as exc_info:
        build_certification_report(dataclasses.replace(_complete(), traceability=matrix))
    assert exc_info.value.reason == "unknown_verdict"


def test_claims_not_requested_are_listed_as_not_claimed() -> None:
    """Every known claim is either made or explicitly not claimed."""
    report = build_certification_report(_complete())
    assert report.claims == ()
    assert set(report.not_claimed) == set(CERTIFICATION_CLAIMS)
    for claim in _SUPPORTABLE:
        assert report.not_claimed[claim] == "supported by the supplied data, but not requested for this report"


# --- scope statement (TOOL-REP-140) -----------------------------------------------------------


def test_the_scope_statement_lists_what_is_excluded() -> None:
    inputs = dataclasses.replace(
        _complete(),
        model=_model(extra_executed=("t.c",), not_executed=("t.z",), partial=True),
        # REQ-9 is verified only by t.z, which was not executed; t.c is traced to nothing
        traceability=_matrix((("REQ-1", "t.a"), ("REQ-2", "t.b"), ("REQ-9", "t.z"))),
        justifications=(
            _justification("J-valid"),
            Justification("J-stale", _UNIT, 50, 50, "eng", "2026-11-01", "stale", "cd" * 32),
            Justification("J-nodigest", "src/other.c", 5, 5, "eng", "2026-11-01", "no digest", "ef" * 32),
        ),
    )
    document = build_certification_report(inputs).to_dict()
    assert document["scope"]["units"] == {"status": "recorded", "units": [_UNIT]}
    assert document["scope"]["tests"] == {"status": "recorded", "count": 4}
    excluded = document["scope"]["excluded"]
    assert excluded["tests_not_executed"] == ["t.z"]
    assert excluded["run_is_partial"] is True
    assert excluded["tests_not_traced_to_any_requirement"] == ["t.c"]
    assert excluded["requirements_not_verified"] == ["REQ-9"]
    assert excluded["coverage_metrics_not_measured"] == ["functions", "calls", "mcdc"]

    exclusions = document["justified_exclusions"]
    assert [entry["id"] for entry in exclusions["valid"]] == ["J-valid"]
    assert [entry["id"] for entry in exclusions["invalidated"]] == ["J-stale"]
    assert [entry["id"] for entry in exclusions["unverifiable"]] == ["J-nodigest"]
    assert set(document["missing_inputs"]) == {"source_digests"}


def test_nothing_excluded_reads_as_empty_lists_not_missing() -> None:
    excluded = build_certification_report(_complete()).to_dict()["scope"]["excluded"]
    assert excluded["tests_not_executed"] == []
    assert excluded["tests_not_traced_to_any_requirement"] == []
    assert excluded["requirements_not_verified"] == []
    assert excluded["run_is_partial"] is False


def test_unmeasured_and_not_applicable_follow_the_stated_criteria() -> None:
    """A metric with nothing measured is unmeasured unless a criterion declares
    it not applicable; an unmeasured metric fails the criteria."""
    branches_unmeasured = enforce_thresholds(
        _metrics(), [MetricThreshold(metric="branches", minimum=Fraction(1, 2))]
    )
    inputs = dataclasses.replace(_complete(), coverage_criteria=branches_unmeasured)
    coverage = build_certification_report(inputs).to_dict()["coverage"]
    assert coverage["unmeasured"] == ["branches"]
    assert coverage["not_applicable"] == []
    assert coverage["criteria"]["passed"] is False
    assert build_certification_report(inputs).not_claimed["coverage_criteria_met"] == (
        "a stated coverage criterion is not met"
    )
    with pytest.raises(ReportModelError) as exc_info:
        build_certification_report(inputs, claims=("coverage_criteria_met",))
    assert exc_info.value.reason == "claim_not_supported"

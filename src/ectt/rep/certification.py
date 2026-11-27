# implements: TOOL-REP-060, TOOL-REP-140
"""Certification verification report and scope statement (WP-REP-05).

A verification report assembled from data the tool already holds — results,
coverage and traceability — for submission as certification evidence
(TOOL-REP-060). It states the tool version, the units and scope it covers,
what was run, the coverage achieved against the stated criteria, which items
are unmeasured or not applicable, and — explicitly — what it does NOT claim
(TOOL-REP-140).

Three rules shape every section:

* **Missing data is stated as missing, never filled.** Every input may be
  absent. An absent input is named in ``missing_inputs`` and the section that
  needs it reads ``missing``; a list that cannot be determined is ``None``,
  never an empty list. Nothing is defaulted into a figure or a verdict.
* **A claim is made only when the data supports it.** The caller names the
  claims the report may make; each is checked against the supplied data and an
  unsupported one is refused with a named reason. Every claim that is not made
  is listed under ``not_claimed`` with the reason, so the scope statement is a
  complete account: each known claim is either made or explicitly not claimed.
* **Execution facts are recorded, never interpreted.** The report carries the
  execution metadata exactly as recorded. It never derives a target execution
  from it: no data this tool records evidences a run on a target (``ectt.ext``
  holds target run plans, and the metadata records where the runner was
  invoked and the build target, not where the tests ran), and no data class
  carries MC/DC. Both are therefore always under ``not_claimed``.

The report is a pure function of its inputs: identical inputs give
byte-identical output (TOOL-REP-100). The report-creation timestamp is not
rendered; the execution timestamp is model content (TOOL-REP-070) and is
recorded like any other fact. Only narrow data classes are imported from
other packages.

Satisfies: TOOL-REP-060, TOOL-REP-140.
"""

from __future__ import annotations

import copy
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from ectt.core.determinism import canonical_json_bytes
from ectt.cov.justification import Justification
from ectt.cov.model import MetricTotals
from ectt.cov.thresholds import ThresholdResult
from ectt.ext.profile import ABI_DIMENSIONS, UNKNOWN_ABI, HostProfile
from ectt.rep.errors import ReportModelError
from ectt.rep.model import TEST_STATUSES, ReportModel
from ectt.trc.matrix import TraceabilityMatrix

__all__ = [
    "CERTIFICATION_REPORT_SCHEMA_VERSION",
    "CERTIFICATION_CLAIMS",
    "KNOWN_COVERAGE_METRICS",
    "UNMEASURED_METRICS",
    "CertificationInputs",
    "CertificationReport",
    "build_certification_report",
]

CERTIFICATION_REPORT_SCHEMA_VERSION = "1.0"

#: Coverage metrics the tool's data classes carry today.
KNOWN_COVERAGE_METRICS: tuple[str, ...] = ("statements", "branches", "functions", "calls")

#: Certification metrics no data class in the tool produces (MC/DC,
#: TOOL-COV-050). They are named here so the report always lists them as not
#: measured and can never list them as achieved.
UNMEASURED_METRICS: tuple[str, ...] = ("mcdc",)

_EVERY_METRIC: tuple[str, ...] = (*KNOWN_COVERAGE_METRICS, *UNMEASURED_METRICS)

#: Every claim a certification report can make.
CERTIFICATION_CLAIMS: tuple[str, ...] = (
    "all_tests_executed",
    "all_tests_passed",
    "coverage_criteria_met",
    "requirements_verified",
    "target_executed",
    "mcdc_measured",
)

_NOT_RUN = "not_run"
_VERDICTS = ("pass", "failed", "unverified")
_NO_DATA = "no_data"
_NOT_APPLICABLE = "not_applicable"
_MEASURED = "measured"

_MCDC_REASON = (
    "MC/DC is not measured by this tool (TOOL-COV-050 is not implemented), so "
    "no MC/DC data exists to report"
)


@dataclass(frozen=True)
class CertificationInputs:
    """The data a certification report is built from; every field may be absent.

    ``source_digests`` maps a justified file to the current digest of its
    source, which decides whether each justification still holds. A host
    profile is context only a host run on behalf of a target build carries;
    its absence is not missing data.
    """

    model: ReportModel | None = None
    coverage_metrics: Mapping[str, MetricTotals] | None = None
    coverage_criteria: ThresholdResult | None = None
    traceability: TraceabilityMatrix | None = None
    justifications: Sequence[Justification] | None = None
    source_digests: Mapping[str, str] | None = None
    host_profile: HostProfile | None = None


@dataclass(frozen=True)
class CertificationReport:
    """A built certification verification report."""

    document: Mapping[str, Any]

    @property
    def claims(self) -> tuple[str, ...]:
        """The claims this report makes, each supported by the supplied data."""
        return tuple(self.document["claims"])

    @property
    def not_claimed(self) -> dict[str, str]:
        """Every claim not made, with the reason it is not made."""
        return {entry["claim"]: entry["reason"] for entry in self.document["not_claimed"]}

    @property
    def missing_inputs(self) -> tuple[str, ...]:
        """The inputs that were absent, named."""
        return tuple(self.document["missing_inputs"])

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical dictionary form (a fresh copy on every call)."""
        return copy.deepcopy(dict(self.document))

    def to_json_bytes(self) -> bytes:
        """Return deterministic canonical JSON bytes with ``schema_version`` first."""
        return canonical_json_bytes(self.to_dict(), indent=2, first_keys=("schema_version",))


def build_certification_report(
    inputs: CertificationInputs,
    *,
    claims: Iterable[str] = (),
) -> CertificationReport:
    """Build the certification verification report from ``inputs`` (TOOL-REP-060).

    ``claims`` names the claims the report may make. Every requested claim is
    checked against the supplied data; one the data does not support is refused
    with ``claim_not_supported`` rather than written into the report. A claim
    that is not requested is listed under ``not_claimed`` instead.

    Refused before anything is written: an unknown claim (``unknown_claim``),
    a coverage metric the report cannot carry (``unknown_metric``), a criteria
    verdict recorded against other figures than the supplied coverage
    (``criteria_metrics_mismatch``), and a requirement verdict outside the
    trace vocabulary (``unknown_verdict``).
    """
    requested = _checked_claims(claims)
    metrics = _checked_metrics(inputs.coverage_metrics)
    _check_criteria(inputs.coverage_criteria, metrics)
    _check_verdicts(inputs.traceability)

    tool, tool_missing = _tool_section(inputs.model)
    run, run_missing = _run_section(inputs.model, inputs.host_profile)
    coverage, coverage_missing = _coverage_section(metrics, inputs.coverage_criteria)
    exclusions, exclusions_missing = _exclusions_section(
        inputs.justifications, inputs.source_digests
    )
    traceability, traceability_missing = _traceability_section(inputs.traceability)
    scope, scope_missing = _scope_section(inputs.model, inputs.traceability, coverage)

    missing: set[str] = set()
    for section_missing in (
        tool_missing,
        run_missing,
        coverage_missing,
        exclusions_missing,
        traceability_missing,
        scope_missing,
    ):
        missing.update(section_missing)

    for claim in requested:
        reason = _unsupported_reason(claim, inputs)
        if reason is not None:
            raise ReportModelError(
                f"claim '{claim}' is not supported by the supplied data: {reason}",
                reason="claim_not_supported",
                context={"claim": claim, "why": reason},
            )

    not_claimed = [
        {"claim": claim, "reason": _not_claimed_reason(claim, inputs)}
        for claim in CERTIFICATION_CLAIMS
        if claim not in requested
    ]
    document: dict[str, Any] = {
        "schema_version": CERTIFICATION_REPORT_SCHEMA_VERSION,
        "claims": sorted(requested),
        "coverage": coverage,
        "justified_exclusions": exclusions,
        "missing_inputs": sorted(missing),
        "not_claimed": not_claimed,
        "run": run,
        "scope": scope,
        "tool": tool,
        "traceability": traceability,
    }
    return CertificationReport(document=document)


# --- input checks -----------------------------------------------------------------------


def _checked_claims(claims: Iterable[str]) -> list[str]:
    requested = list(claims)
    unknown = sorted(repr(claim) for claim in requested if claim not in CERTIFICATION_CLAIMS)
    if unknown:
        raise ReportModelError(
            f"unknown certification claim(s) {', '.join(unknown)} (known: {', '.join(CERTIFICATION_CLAIMS)})",
            reason="unknown_claim",
        )
    return sorted(set(requested))


def _checked_metrics(metrics: Mapping[str, MetricTotals] | None) -> dict[str, MetricTotals] | None:
    if metrics is None:
        return None
    unknown = sorted(set(metrics) - set(KNOWN_COVERAGE_METRICS))
    if unknown:
        raise ReportModelError(
            f"a certification report cannot carry coverage metric(s) {', '.join(unknown)} "
            f"(known: {', '.join(KNOWN_COVERAGE_METRICS)}; MC/DC is not measured by this tool)",
            reason="unknown_metric",
        )
    return dict(metrics)


def _check_criteria(
    criteria: ThresholdResult | None,
    metrics: Mapping[str, MetricTotals] | None,
) -> None:
    """A criteria verdict must have been computed from the figures it is shown beside."""
    if criteria is None or metrics is None:
        return
    for evaluation in criteria.evaluations:
        totals = metrics.get(evaluation.metric)
        if totals is not None and (evaluation.covered, evaluation.total) != (totals.covered, totals.total):
            raise ReportModelError(
                f"the coverage criterion for '{evaluation.metric}' was recorded against "
                f"{evaluation.covered}/{evaluation.total}, but the supplied coverage is "
                f"{totals.covered}/{totals.total}",
                reason="criteria_metrics_mismatch",
            )


def _check_verdicts(traceability: TraceabilityMatrix | None) -> None:
    if traceability is None:
        return
    unknown = sorted({row.verdict for row in traceability.rows} - set(_VERDICTS))
    if unknown:
        raise ReportModelError(
            f"requirement verdict(s) outside the trace vocabulary: {', '.join(unknown)} "
            f"(known: {', '.join(_VERDICTS)})",
            reason="unknown_verdict",
        )


# --- sections ---------------------------------------------------------------------------


def _tool_section(model: ReportModel | None) -> tuple[dict[str, Any], set[str]]:
    provenance = model.provenance if model is not None else None
    if provenance is None:
        return {"status": "missing"}, {"tool_identification"}
    # core.provenance.tool_version() answers "unknown" for an installation that
    # cannot prove its version; a certification report cannot identify itself with that.
    identified = bool(provenance.tool_version.strip()) and provenance.tool_version != "unknown"
    section = {
        "status": "identified" if identified else "unidentified",
        "version": provenance.tool_version,
        "build_id": provenance.build_id,
        "python_version": provenance.python_version,
        "dependencies": dict(sorted(provenance.dependencies.items())),
        "schema_versions": dict(sorted(provenance.schema_versions.items())),
        "provenance_digest": provenance.digest,
    }
    return section, set() if identified else {"tool_identification"}


def _run_section(
    model: ReportModel | None,
    host_profile: HostProfile | None,
) -> tuple[dict[str, Any], set[str]]:
    if model is None:
        return {"status": "missing"}, {"results"}

    execution: dict[str, Any] = {"status": "missing"}
    missing: set[str] = set()
    if model.execution is None:
        missing.add("execution_facts")
    else:
        execution = {
            "status": "recorded",
            "where": model.execution.where,
            "toolchain": model.execution.toolchain,
            "target_id": model.execution.target_id,
        }
    executed_at = model.provenance.generated_at if model.provenance is not None else None
    if not executed_at:
        missing.add("execution_timestamp")
        executed_at = None
    execution["executed_at"] = executed_at

    tests = sorted(model.tests, key=lambda entry: entry.test_id)
    counts: dict[str, int] = dict.fromkeys(TEST_STATUSES, 0)
    for entry in tests:
        counts[entry.status] += 1
    section = {
        "status": "recorded",
        "run_id": model.run_id,
        "report_id": model.report_id,
        "partial": model.partial,
        "execution": execution,
        "host_profile": _host_profile_section(host_profile),
        "tests": [entry.to_dict() for entry in tests],
        "status_counts": counts,
    }
    return section, missing


def _host_profile_section(profile: HostProfile | None) -> dict[str, Any] | None:
    """The host profile the run executed under, or ``None`` when none was supplied."""
    if profile is None:
        return None
    return {
        "profile_id": profile.profile_id,
        "label": profile.label,
        "name": profile.name,
        "target_triple": profile.target_triple,
        "host_triple": profile.host_triple,
        # A dimension the profile never measured is unknown, never "same".
        "abi": {dimension: profile.abi.get(dimension, UNKNOWN_ABI) for dimension in ABI_DIMENSIONS},
    }


def _coverage_section(
    metrics: Mapping[str, MetricTotals] | None,
    criteria: ThresholdResult | None,
) -> tuple[dict[str, Any], set[str]]:
    missing: set[str] = set()
    achieved: dict[str, dict[str, Any]] | None
    unmeasured: list[str] | None
    not_applicable: list[str] | None
    if metrics is None:
        achieved = None
        unmeasured = None
        not_applicable = None
        missing.add("coverage_metrics")
    else:
        achieved = {
            name: {"covered": totals.covered, "total": totals.total}
            for name, totals in sorted(metrics.items())
        }
        standing = {name: _standing(name, totals, criteria) for name, totals in metrics.items()}
        unmeasured = sorted(name for name, state in standing.items() if state == _NO_DATA)
        not_applicable = sorted(name for name, state in standing.items() if state == _NOT_APPLICABLE)
    not_measured = [name for name in _EVERY_METRIC if metrics is None or name not in metrics]

    criteria_section: dict[str, Any]
    if criteria is None:
        criteria_section = {"status": "not_stated", "passed": None, "evaluations": None}
        missing.add("coverage_criteria")
    else:
        criteria_section = {
            "status": "stated",
            "passed": criteria.passed,
            "evaluations": [
                {
                    "metric": evaluation.metric,
                    "state": evaluation.state,
                    "covered": evaluation.covered,
                    "total": evaluation.total,
                    "minimum": _fraction_text(evaluation.minimum),
                }
                for evaluation in sorted(criteria.evaluations, key=lambda item: item.metric)
            ],
        }
    section = {
        "status": "recorded" if metrics is not None else "missing",
        "achieved": achieved,
        "criteria": criteria_section,
        "unmeasured": unmeasured,
        "not_applicable": not_applicable,
        "not_measured": not_measured,
    }
    return section, missing


def _standing(metric: str, totals: MetricTotals, criteria: ThresholdResult | None) -> str:
    """How a supplied metric stands: ``no_data``, ``not_applicable`` or ``measured``.

    The stated criterion's verdict decides when there is one. Without a
    stated criterion nothing can be declared not applicable, so a metric with
    nothing measured is unmeasured.
    """
    if criteria is not None:
        for evaluation in criteria.evaluations:
            if evaluation.metric == metric:
                return evaluation.state
    return _NO_DATA if totals.total is None or totals.total == 0 else _MEASURED


def _exclusions_section(
    justifications: Sequence[Justification] | None,
    source_digests: Mapping[str, str] | None,
) -> tuple[dict[str, Any], set[str]]:
    if justifications is None:
        return {"status": "missing", "valid": None, "invalidated": None, "unverifiable": None}, {
            "justified_exclusions"
        }
    digests = source_digests or {}
    valid: list[dict[str, Any]] = []
    invalidated: list[dict[str, Any]] = []
    unverifiable: list[dict[str, Any]] = []
    for justification in sorted(justifications, key=lambda item: (item.file, item.id)):
        record: dict[str, Any] = {
            "id": justification.id,
            "file": justification.file,
            "start_line": justification.start_line,
            "end_line": justification.end_line,
        }
        current = digests.get(justification.file)
        if current is None:
            # The associated source digest was not supplied: the justification
            # cannot be verified and is never counted as an exclusion (WP-COV-09).
            unverifiable.append(record)
        elif current == justification.source_digest:
            valid.append(
                {
                    **record,
                    "author": justification.author,
                    "date": justification.date,
                    "rationale": justification.rationale,
                }
            )
        else:
            # The associated source changed since acceptance (TOOL-COV-150):
            # the justification excludes nothing.
            invalidated.append(record)
    section = {
        "status": "recorded" if justifications else "none_recorded",
        "valid": valid,
        "invalidated": invalidated,
        "unverifiable": unverifiable,
    }
    return section, {"source_digests"} if unverifiable else set()


def _traceability_section(
    traceability: TraceabilityMatrix | None,
) -> tuple[dict[str, Any], set[str]]:
    if traceability is None:
        return {"status": "missing"}, {"traceability"}
    rows = sorted(traceability.rows, key=lambda row: row.requirement_id)
    verdicts: dict[str, int] = dict.fromkeys(_VERDICTS, 0)
    for row in rows:
        verdicts[row.verdict] += 1
    section = {
        "status": "recorded",
        "pair_count": traceability.pair_count,
        "requirement_count": len(rows),
        "verdict_counts": verdicts,
        "rows": [
            {
                "requirement_id": row.requirement_id,
                "verdict": row.verdict,
                "links": [
                    {"test_id": link.test_id, "status": link.status, "unreviewed": link.unreviewed}
                    for link in sorted(row.links, key=lambda item: item.test_id)
                ],
            }
            for row in rows
        ],
    }
    return section, set()


def _scope_section(
    model: ReportModel | None,
    traceability: TraceabilityMatrix | None,
    coverage: Mapping[str, Any],
) -> tuple[dict[str, Any], set[str]]:
    """What the report covers and, explicitly, what is excluded from that (TOOL-REP-140)."""
    units = sorted(entry.unit for entry in model.coverage) if model is not None else None
    statuses = model.test_statuses() if model is not None else None
    rows = traceability.rows if traceability is not None else None

    not_executed: list[str] | None = None
    untraced: list[str] | None = None
    unverified: list[str] | None = None
    if statuses is not None:
        not_executed = sorted(test for test, status in statuses.items() if status == _NOT_RUN)
    if rows is not None:
        unverified = sorted(row.requirement_id for row in rows if row.verdict != "pass")
        if statuses is not None:
            traced = {link.test_id for row in rows for link in row.links}
            untraced = sorted(set(statuses) - traced)

    scope = {
        "units": {
            "status": "recorded" if units else "missing",
            "units": units or [],
        },
        "tests": {
            "status": "recorded" if statuses is not None else "missing",
            "count": len(statuses) if statuses is not None else None,
        },
        "requirements": {
            "status": "recorded" if rows is not None else "missing",
            "count": len(rows) if rows is not None else None,
        },
        "excluded": {
            "tests_not_executed": not_executed,
            "run_is_partial": model.partial if model is not None else None,
            "tests_not_traced_to_any_requirement": untraced,
            "requirements_not_verified": unverified,
            "coverage_metrics_not_measured": list(coverage["not_measured"]),
        },
    }
    return scope, set() if units else {"unit_scope"}


# --- claims -----------------------------------------------------------------------------


def _unsupported_reason(claim: str, inputs: CertificationInputs) -> str | None:
    """Why ``claim`` cannot be made from ``inputs``, or ``None`` when the data supports it."""
    model = inputs.model
    if claim in ("all_tests_executed", "all_tests_passed"):
        if model is None:
            return "no result data is supplied"
        statuses = model.test_statuses()
        if not statuses:
            return "no tests are recorded"
        not_run = [test for test, status in statuses.items() if status == _NOT_RUN]
        if not_run:
            return f"{len(not_run)} test(s) were not executed"
        if model.partial:
            return "the run is a partial run"
        if claim == "all_tests_passed":
            not_passed = [test for test, status in statuses.items() if status != "pass"]
            if not_passed:
                return f"{len(not_passed)} test(s) did not pass"
        return None
    if claim == "coverage_criteria_met":
        if inputs.coverage_metrics is None:
            return "no coverage data is supplied"
        if inputs.coverage_criteria is None:
            return "no coverage criteria are stated"
        if not inputs.coverage_criteria.evaluations:
            return "no coverage criterion is evaluated"
        if not inputs.coverage_criteria.passed:
            return "a stated coverage criterion is not met"
        return None
    if claim == "requirements_verified":
        if inputs.traceability is None:
            return "no traceability data is supplied"
        if not inputs.traceability.rows:
            return "no requirements are recorded"
        unverified = [row.requirement_id for row in inputs.traceability.rows if row.verdict != "pass"]
        if unverified:
            return f"{len(unverified)} requirement(s) are not verified"
        return None
    if claim == "target_executed":
        return _target_execution_reason(inputs.host_profile)
    if claim == "mcdc_measured":
        return _MCDC_REASON
    raise AssertionError(f"unknown claim {claim!r}")  # unreachable: claims are checked first


def _target_execution_reason(profile: HostProfile | None) -> str:
    reason = (
        "no target-execution record exists in the supplied data: the tool records target "
        "run plans, and the execution facts record where the runner was invoked and the "
        "build target, not where the tests ran"
    )
    if profile is not None:
        reason += (
            f"; the run carries host profile '{profile.label}', and a host result never "
            "establishes target behaviour (TOOL-TGT-130)"
        )
    return reason


def _not_claimed_reason(claim: str, inputs: CertificationInputs) -> str:
    reason = _unsupported_reason(claim, inputs)
    if reason is not None:
        return reason
    return "supported by the supplied data, but not requested for this report"


def _fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"

# implements: TOOL-CBT-030, TOOL-CBT-050, TOOL-CBT-060, TOOL-CBT-080, TOOL-TGT-130, TOOL-COV-130
"""Report views over re-execution, comparison, minimization, profile and
threshold data (B2 wiring wave).

Each view is a renderer over another lane's data class, imported narrowly
(module-level import of the specific class's module, never a package root):
the view computes nothing from wall-clock or environment and returns a plain,
deterministic dictionary. Other lanes call these views, so the five function
names are stable API — see docs/verification/WP-REP-views-analysis.md for the
function table and the derived acceptance criteria.

Threshold semantics: the recorded evaluation state travels verbatim (COV-180
discipline — never relabelled); the view adds a separate ``displayed`` field
in which ``no_data`` reads as a failure, because an empty or broken coverage
run must not present as a pass.

Satisfies: TOOL-CBT-030, TOOL-CBT-050, TOOL-CBT-060, TOOL-CBT-080,
TOOL-TGT-130, TOOL-COV-130.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ectt.cbt.compare import CoverageComparison, RunComparison
from ectt.cbt.minimize import Minimization
from ectt.cbt.reexecute import SubsetReExecution
from ectt.cov.thresholds import ThresholdResult
from ectt.ext.profile import LabelledResults
from ectt.rep.errors import ReportModelError

__all__ = [
    "host_profile_view",
    "minimized_suite_view",
    "run_comparison_view",
    "subset_run_view",
    "threshold_view",
]


def _error(message: str, reason: str) -> ReportModelError:
    return ReportModelError(message, reason=reason)


def subset_run_view(subset: SubsetReExecution) -> dict[str, Any]:
    """Report view for a subset re-execution (TOOL-CBT-030/040).

    States that the suite was only partly run, from ``suite_view`` data: the
    ``partial`` flag, the not-executed list, the selected / not-selected
    partition, and per-test outcomes. A view whose data disagrees with itself
    (``suite_view.partial`` not matching the partition) is refused.
    """
    suite_view = subset.suite_view
    partial_from_data = bool(suite_view.partial)
    partitioned = bool(subset.not_selected)
    if partial_from_data != partitioned:
        raise _error(
            "subset re-execution is inconsistent: suite_view.partial is "
            f"{partial_from_data} but the record partitions "
            f"{len(subset.not_selected)} test(s) as not selected",
            reason="inconsistent_subset_view",
        )
    outcomes = {record.test_id: record.outcome for record in suite_view.results}
    return {
        "view": "subset_run",
        "partial": partial_from_data,
        "run_id": suite_view.run_id,
        "selected": list(subset.selected),
        "not_selected": list(subset.not_selected),
        "not_executed": list(suite_view.not_executed),
        "tests_total": len(subset.selected) + len(subset.not_selected),
        "tests_executed": len(outcomes),
        "outcomes": {test_id: outcomes[test_id] for test_id in sorted(outcomes)},
    }


def run_comparison_view(
    comparison: RunComparison,
    coverage: CoverageComparison | None = None,
) -> dict[str, Any]:
    """Report view for one run against a baseline (TOOL-CBT-050/060).

    Carries the exact outcome transitions and the removed tests verbatim
    (sorted, as produced), plus — when a coverage comparison is supplied —
    each metric's baseline/current totals and exact change; unmeasured stays
    ``None``, never zero.
    """
    view: dict[str, Any] = {
        "view": "run_comparison",
        "newly_failing": list(comparison.newly_failing),
        "newly_passing": list(comparison.newly_passing),
        "newly_added": list(comparison.newly_added),
        "removed": list(comparison.removed),
        "removed_count": len(comparison.removed),
    }
    if coverage is not None:
        view["coverage"] = {
            "deltas": [
                {
                    "metric": delta.metric,
                    "baseline": None if delta.baseline is None else delta.baseline.to_dict(),
                    "current": None if delta.current is None else delta.current.to_dict(),
                    "change": delta.change,
                }
                for delta in coverage.deltas
            ]
        }
    return view


def minimized_suite_view(
    minimization: Minimization,
    coverage_by_test: Mapping[str, Any],
) -> dict[str, Any]:
    """Report view for a minimized suite (TOOL-CBT-080).

    Shows kept versus redundant and the preserved union (sorted). The view
    recomputes both unions from the supplied coverage mapping and refuses a
    minimization that no longer preserves coverage (``stale_minimization``):
    a minimized suite must cover exactly what the full suite covered.
    """
    entries: dict[str, frozenset[str]] = {}
    for test_id, covered in coverage_by_test.items():
        entries[test_id] = frozenset(tuple(covered))
    full_union: set[str] = set()
    for covered in entries.values():
        full_union.update(covered)
    kept_union: set[str] = set()
    for test_id in minimization.kept:
        if test_id not in entries:
            raise _error(
                f"kept test '{test_id}' has no coverage entry; the minimization "
                f"does not match the supplied coverage mapping",
                reason="stale_minimization",
            )
        kept_union.update(entries[test_id])
    if kept_union != full_union:
        raise _error(
            "the minimization no longer preserves coverage: kept union "
            f"({len(kept_union)} constructs) != full union ({len(full_union)} constructs)",
            reason="stale_minimization",
        )
    for test_id in minimization.redundant:
        if test_id not in entries:
            raise _error(
                f"redundant test '{test_id}' has no coverage entry",
                reason="stale_minimization",
            )
    return {
        "view": "minimized_suite",
        "kept": list(minimization.kept),
        "redundant": list(minimization.redundant),
        "kept_count": len(minimization.kept),
        "redundant_count": len(minimization.redundant),
        "preserved_union": sorted(full_union),
        "preserved_construct_count": len(full_union),
    }


def host_profile_view(labelled: LabelledResults) -> dict[str, Any]:
    """Report view for host-executed results with their profile labels (TOOL-TGT-130).

    The profile id and label ride beside every result's id and outcome; the
    view never alters outcomes, and host success never reads as target
    behaviour (the label data is the disclosure).
    """
    if len(labelled.labels) != len(labelled.result_set.results):
        raise _error(
            f"profile labels ({len(labelled.labels)}) do not match results "
            f"({len(labelled.result_set.results)})",
            reason="label_result_mismatch",
        )
    return {
        "view": "host_profile",
        "profile_id": labelled.profile.profile_id,
        "profile_label": labelled.profile.label,
        "run_id": labelled.result_set.run_id,
        "results": [
            {
                "outcome": label.outcome,
                "profile_id": label.profile_id,
                "profile_label": label.profile_label,
                "test_id": label.test_id,
            }
            for label in sorted(labelled.labels, key=lambda l: l.test_id)
        ],
    }


def threshold_view(result: ThresholdResult) -> dict[str, Any]:
    """Report view for coverage threshold results (TOOL-COV-130).

    Every evaluation keeps its recorded state verbatim; ``displayed`` maps
    ``no_data`` to ``fail`` (an empty or broken coverage run must not present
    as a pass) and ``not_applicable`` to ``exempt``. ``passed`` mirrors
    ``result.passed``.
    """
    displayed_map = {"pass": "pass", "fail": "fail", "no_data": "fail", "not_applicable": "exempt"}
    evaluations: list[dict[str, Any]] = []
    no_data_metrics: list[str] = []
    for evaluation in result.evaluations:
        if evaluation.state not in displayed_map:
            raise _error(
                f"threshold evaluation for '{evaluation.metric}' carries unknown "
                f"state {evaluation.state!r}",
                reason="unknown_threshold_state",
            )
        if evaluation.state == "no_data":
            no_data_metrics.append(evaluation.metric)
        evaluations.append(
            {
                "covered": evaluation.covered,
                "displayed": displayed_map[evaluation.state],
                "metric": evaluation.metric,
                "minimum": f"{evaluation.minimum.numerator}/{evaluation.minimum.denominator}",
                "state": evaluation.state,
                "total": evaluation.total,
            }
        )
    return {
        "view": "thresholds",
        "passed": result.passed,
        "no_data_metrics": sorted(no_data_metrics),
        "evaluations": evaluations,
    }

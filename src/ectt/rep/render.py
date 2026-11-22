# implements: TOOL-REP-070, TOOL-REP-090, TOOL-REP-100
"""Report renderers over the single intermediate model (WP-REP-01, WP-REP-06).

Two formats — plain text and JSON — both consume only the model's
``test_statuses``, ``coverage_figures`` and ``provenance_facts`` accessors.
No renderer computes a status, a figure, or a provenance fact from anything
else, so renderers cannot disagree (TOOL-REP-090), and each renderer is a
pure function of the model content: identical inputs render byte-identical
output (TOOL-REP-100). The report-creation timestamp (``model.generated_at``)
is excluded; the execution timestamp is model content (TOOL-REP-070) and
renders like any other fact.

Derived ratios (percentages) are not rendered: the model carries raw
counters only, so no renderer owns a rounding policy.

Optional marks (TOOL-ATG-070): callers may pass data-driven test cases; the
renderers then show each test's machine-generated/unreviewed mark through
:func:`ectt.atg.lifecycle.format_mark` and summarise them through
:func:`ectt.atg.lifecycle.report_marks`. Only these narrow functions are
imported from ``ectt.atg`` — rep takes no other dependency on it. Without
cases the output is byte-identical to the unmarked report.

Satisfies: TOOL-REP-070, TOOL-REP-090, TOOL-REP-100, TOOL-ATG-070.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from ectt.atg.lifecycle import format_mark, report_marks
from ectt.core.determinism import canonical_json, canonical_text
from ectt.rep.model import ReportModel

if TYPE_CHECKING:
    from ectt.tcm.datacases import DataDrivenTestCase

__all__ = [
    "render_json",
    "render_text",
]


def render_text(model: ReportModel, *, cases: Sequence[DataDrivenTestCase] = ()) -> str:
    """Render the model as a deterministic plain-text summary.

    ``cases`` (optional) carries data-driven test cases whose marks are shown
    per test via :func:`format_mark` and summarised via :func:`report_marks`.
    """
    statuses = model.test_statuses()
    figures = model.coverage_figures()
    facts = model.provenance_facts()
    marks = report_marks(cases)
    cases_by_id = {case.case_id: case for case in cases}

    counts: dict[str, int] = dict.fromkeys(sorted(set(statuses.values())), 0)
    for status in statuses.values():
        counts[status] += 1
    summary = " ".join(f"{status}={counts[status]}" for status in sorted(counts))

    lines = [
        f"ectt report {model.run_id}",
        f"partial: {'yes' if model.partial else 'no'}",
        f"tests: {len(statuses)} {summary}".rstrip(),
    ]
    lines.extend(f"{key}: {facts[key]}" for key in sorted(facts))
    for test_id in sorted(statuses):
        case = cases_by_id.get(test_id)
        if case is None:
            lines.append(f"TEST {test_id} {statuses[test_id]}")
        else:
            lines.append(f"TEST {test_id} {statuses[test_id]} [{format_mark(case)}]")
    if marks["cases"]:
        lines.append(
            f"marks: machine_generated={marks['machine_generated']}"
            f" unreviewed_expectations={marks['unreviewed_expectations']}"
        )
    lines.append(f"coverage: {len(figures)} units")
    lines.extend(
        f"COVERAGE {unit} {figures[unit][0]}/{figures[unit][1]}" for unit in sorted(figures)
    )
    return canonical_text("\n".join(lines))


def render_json(model: ReportModel, *, cases: Sequence[DataDrivenTestCase] = ()) -> str:
    """Render the model as deterministic canonical JSON.

    With ``cases`` the marks summary (``report_marks`` shape) is included
    under ``marks``; without cases the document carries no ``marks`` key.
    """
    statuses = model.test_statuses()
    figures = model.coverage_figures()
    facts = model.provenance_facts()
    marks = report_marks(cases)
    cases_by_id = {case.case_id: case for case in cases}
    view: dict[str, object] = {
        "coverage": [
            {"covered": figures[unit][0], "total": figures[unit][1], "unit": unit}
            for unit in sorted(figures)
        ],
        "partial": model.partial,
        "run_id": model.run_id,
        "tests": [
            (
                {"id": test_id, "mark": format_mark(cases_by_id[test_id]), "status": statuses[test_id]}
                if test_id in cases_by_id
                else {"id": test_id, "status": statuses[test_id]}
            )
            for test_id in sorted(statuses)
        ],
    }
    if facts:
        view["provenance"] = facts
    if marks["cases"]:
        view["marks"] = marks
    return canonical_json(view)

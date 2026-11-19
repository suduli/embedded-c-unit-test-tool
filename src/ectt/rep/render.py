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

Satisfies: TOOL-REP-070, TOOL-REP-090, TOOL-REP-100.
"""

from __future__ import annotations

from ectt.core.determinism import canonical_json, canonical_text
from ectt.rep.model import ReportModel

__all__ = [
    "render_json",
    "render_text",
]


def render_text(model: ReportModel) -> str:
    """Render the model as a deterministic plain-text summary."""
    statuses = model.test_statuses()
    figures = model.coverage_figures()
    facts = model.provenance_facts()

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
    lines.extend(f"TEST {test_id} {statuses[test_id]}" for test_id in sorted(statuses))
    lines.append(f"coverage: {len(figures)} units")
    lines.extend(
        f"COVERAGE {unit} {figures[unit][0]}/{figures[unit][1]}" for unit in sorted(figures)
    )
    return canonical_text("\n".join(lines))


def render_json(model: ReportModel) -> str:
    """Render the model as deterministic canonical JSON."""
    statuses = model.test_statuses()
    figures = model.coverage_figures()
    facts = model.provenance_facts()
    view: dict[str, object] = {
        "coverage": [
            {"covered": figures[unit][0], "total": figures[unit][1], "unit": unit}
            for unit in sorted(figures)
        ],
        "partial": model.partial,
        "run_id": model.run_id,
        "tests": [
            {"id": test_id, "status": statuses[test_id]} for test_id in sorted(statuses)
        ],
    }
    if facts:
        view["provenance"] = facts
    return canonical_json(view)

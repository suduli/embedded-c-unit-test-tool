# implements: TOOL-REP-090, TOOL-REP-100
"""Report renderers over the single intermediate model (WP-REP-01).

Two formats — plain text and JSON — both consume only the model's
``test_statuses`` and ``coverage_figures`` accessors. No renderer computes a
status or a figure from anything else, so renderers cannot disagree
(TOOL-REP-090), and each renderer is a pure function of the model content:
identical inputs render byte-identical output (TOOL-REP-100). Timestamps
(``model.generated_at``) are deliberately excluded from rendered output.

Derived ratios (percentages) are not rendered: the model carries raw
counters only, so no renderer owns a rounding policy.

Satisfies: TOOL-REP-090, TOOL-REP-100.
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

    counts: dict[str, int] = dict.fromkeys(sorted(set(statuses.values())), 0)
    for status in statuses.values():
        counts[status] += 1
    summary = " ".join(f"{status}={counts[status]}" for status in sorted(counts))

    lines = [
        f"ectt report {model.run_id}",
        f"partial: {'yes' if model.partial else 'no'}",
        f"tests: {len(statuses)} {summary}".rstrip(),
    ]
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
    view = {
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
    return canonical_json(view)

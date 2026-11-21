# implements: TOOL-REP-030, TOOL-REP-040
"""Human-readable HTML report combining test results and annotated source (WP-REP-03).

The renderer consumes only the model's ``test_statuses``,
``coverage_figures`` and ``provenance_facts`` accessors — the same single
source as every other renderer (TOOL-REP-090) — plus the per-line annotation
produced by ``ectt.cov.justification.annotate_coverage`` (TOOL-REP-040: the
annotated source shows per-line coverage status, including ``justified``
lines carrying their owning justification id). It is a pure function of its
inputs: identical inputs render byte-identical output (TOOL-REP-100), the
model's ``generated_at`` is excluded, all dynamic text is HTML-escaped, and
the page is self-contained (no external assets, no wall-clock, no network).

Satisfies: TOOL-REP-030, TOOL-REP-040, TOOL-REP-090, TOOL-REP-100.
"""

from __future__ import annotations

import html
from collections.abc import Mapping

from ectt.core.determinism import canonical_text
from ectt.cov.justification import AnnotatedCoverage
from ectt.rep.model import ReportModel

__all__ = [
    "render_html",
]

#: Per-line CSS classes; the fixed vocabulary mirrors LINE_STATUSES.
_LINE_CLASSES = ("covered", "partial", "uncovered", "justified")

_STATUS_BADGE = {
    "pass": "pass",
    "fail": "fail",
    "error": "error",
    "timeout": "error",
    "not_run": "skipped",
}


def _e(text: str) -> str:
    """Escape dynamic text for HTML body/attribute context."""
    return html.escape(str(text), quote=True)


def render_html(
    model: ReportModel,
    annotated: AnnotatedCoverage,
    sources: Mapping[str, str],
) -> str:
    """Render the combined HTML report (TOOL-REP-030/TOOL-REP-040).

    ``annotated`` carries per-line statuses (from the coverage backend);
    ``sources`` maps a file path to its source text. A file annotated but
    without supplied source is listed under "source not available" — surfaced,
    never silently omitted.
    """
    statuses = model.test_statuses()
    figures = model.coverage_figures()
    facts = model.provenance_facts()

    counts: dict[str, int] = dict.fromkeys(sorted(set(statuses.values())), 0)
    for status in statuses.values():
        counts[status] += 1

    out: list[str] = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "<meta charset=\"utf-8\" />",
        f"<title>{_e(f'ectt report {model.run_id}')}</title>",
        "<style>",
        "body{font-family:monospace;margin:1rem}",
        "table{border-collapse:collapse}td,th{border:1px solid #999;padding:0.2rem 0.6rem;text-align:left}",
        ".covered{background:#cfc}.partial{background:#ffc}.uncovered{background:#fcc}.justified{background:#ccf}",
        ".justified::after{content:' [justified]';font-size:0.8em}",
        ".pass{color:#060}.fail{color:#900}.error{color:#900}.skipped{color:#990}",
        "code.ln{display:inline-block;width:4rem;color:#666}",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>ectt report {_e(model.run_id)}</h1>",
        f"<p>partial: {'yes' if model.partial else 'no'}</p>",
        "<h2>Summary</h2>",
        "<table><tr><th>status</th><th>count</th></tr>",
    ]
    out.extend(f"<tr><td>{_e(status)}</td><td>{counts[status]}</td></tr>" for status in sorted(counts))
    out.append("</table>")
    if facts:
        out.append("<table><tr><th>fact</th><th>value</th></tr>")
        out.extend(f"<tr><td>{_e(key)}</td><td>{_e(facts[key])}</td></tr>" for key in sorted(facts))
        out.append("</table>")


    out.append("<h2>Tests</h2>")
    out.append("<table><tr><th>test</th><th>status</th></tr>")
    out.extend(
        f'<tr><td>{_e(test_id)}</td><td class="{_e(_STATUS_BADGE[statuses[test_id]])}">{_e(statuses[test_id])}</td></tr>'
        for test_id in sorted(statuses)
    )
    out.append("</table>")

    out.append("<h2>Coverage</h2>")
    out.append("<table><tr><th>unit</th><th>covered</th><th>total</th></tr>")
    out.extend(
        f"<tr><td>{_e(unit)}</td><td>{figures[unit][0]}</td><td>{figures[unit][1]}</td></tr>"
        for unit in sorted(figures)
    )
    out.append("</table>")

    annotated_by_path = {file.file: file for file in annotated.files}
    missing_sources = [path for path in sorted(annotated_by_path) if path not in sources]

    out.append("<h2>Annotated source</h2>")
    for path in sorted(annotated_by_path):
        if path not in sources:
            continue
        source_lines = sources[path].replace("\r\n", "\n").replace("\r", "\n").split("\n")
        line_map = {line.line_number: line for line in annotated_by_path[path].lines}
        out.append(f"<h3>{_e(path)}</h3>")
        out.append("<pre>")
        for number, text in enumerate(source_lines, start=1):
            entry = line_map.get(number)
            if entry is None:
                out.append(f'<code class="ln">{_e(str(number))}</code>{_e(text)}')
            else:
                assert entry.status in _LINE_CLASSES
                out.append(
                    f'<code class="ln">{_e(str(number))}</code>'
                    f'<span class="{_e(entry.status)}" title="{_e(entry.justification_id or "")}">{_e(text)}</span>'
                )
        # annotation lines beyond the supplied source text remain visible
        max_source = len(source_lines)
        for number in sorted(n for n in line_map if n > max_source):
            entry = line_map[number]
            out.append(
                f'<code class="ln">{_e(str(number))}</code>'
                f'<span class="{_e(entry.status)}" title="{_e(entry.justification_id or "")}"></span>'
            )
        out.append("</pre>")

    if missing_sources:
        out.append("<h2>Source not available</h2>")
        out.append("<ul>")
        out.extend(f"<li>{_e(path)}</li>" for path in missing_sources)
        out.append("</ul>")

    out.append("</body>")
    out.append("</html>")
    return canonical_text("\n".join(out))

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

Text that escaping cannot protect is refused with a named reason before
anything is written (``ectt.rep.output_text``): NUL, and text that cannot be
written as UTF-8. A consumer is never left to find a page that does not show
what was written.

Satisfies: TOOL-REP-030, TOOL-REP-040, TOOL-REP-090, TOOL-REP-100.
"""

from __future__ import annotations

import html
import re
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from ectt.atg.lifecycle import format_mark, report_marks
from ectt.core.determinism import canonical_text
from ectt.cov.justification import AnnotatedCoverage
from ectt.rep.model import ReportModel
from ectt.rep.output_text import describe, refuse_characters

if TYPE_CHECKING:
    from ectt.tcm.datacases import DataDrivenTestCase

__all__ = [
    "render_html",
]

#: Per-line CSS classes; the fixed vocabulary mirrors LINE_STATUSES.
_LINE_CLASSES = ("covered", "partial", "uncovered", "justified")

#: NUL: an HTML parser replaces it with a replacement character, so the page
#: would not show what was written, and it makes the file binary to the tools
#: that read it.
_NUL = re.compile("\x00")

_STATUS_BADGE = {
    "pass": "pass",
    "fail": "fail",
    "error": "error",
    "timeout": "error",
    "not_run": "skipped",
}


def _e(text: str, what: str = "text") -> str:
    """Escape dynamic text for HTML body and attribute context.

    Escaping protects the page from the markup and the quotes in the text. A
    carriage return is written as a character reference: written literally it
    would be turned into a line feed when the page's line endings are
    normalised, and an HTML parser does the same.

    What escaping cannot protect is refused with a named reason rather than
    written: NUL (``html_illegal_character``) and text that cannot be written
    as UTF-8 (``unencodable_text``).
    """
    refuse_characters(
        text,
        what,
        forbidden=_NUL,
        reason="html_illegal_character",
        problem="NUL",
        carrier="an HTML report",
    )
    return html.escape(str(text), quote=True).replace("\r", "&#13;")


def render_html(
    model: ReportModel,
    annotated: AnnotatedCoverage,
    sources: Mapping[str, str],
    *,
    cases: Sequence[DataDrivenTestCase] = (),
) -> str:
    """Render the combined HTML report (TOOL-REP-030/TOOL-REP-040).

    ``annotated`` carries per-line statuses (from the coverage backend);
    ``sources`` maps a file path to its source text. A file annotated but
    without supplied source is listed under "source not available" — surfaced,
    never silently omitted. ``cases`` (optional) adds the machine-generated /
    unreviewed marks section (TOOL-ATG-070); without cases the section is
    absent and the output is byte-identical to the unmarked report.

    Text carrying NUL, or text that cannot be written as UTF-8, is refused
    with a named reason (``html_illegal_character``, ``unencodable_text``). A
    refused source line is named by its location only, never quoted.
    """
    statuses = model.test_statuses()
    figures = model.coverage_figures()
    facts = model.provenance_facts()
    run_what = f"run id {describe(model.run_id)}"

    counts: dict[str, int] = dict.fromkeys(sorted(set(statuses.values())), 0)
    for status in statuses.values():
        counts[status] += 1

    out: list[str] = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "<meta charset=\"utf-8\" />",
        f"<title>{_e(f'ectt report {model.run_id}', run_what)}</title>",
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
        f"<h1>ectt report {_e(model.run_id, run_what)}</h1>",
        f"<p>partial: {'yes' if model.partial else 'no'}</p>",
        "<h2>Summary</h2>",
        "<table><tr><th>status</th><th>count</th></tr>",
    ]
    out.extend(f"<tr><td>{_e(status)}</td><td>{counts[status]}</td></tr>" for status in sorted(counts))
    out.append("</table>")
    if facts:
        out.append("<table><tr><th>fact</th><th>value</th></tr>")
        out.extend(
            f"<tr><td>{_e(key)}</td><td>{_e(facts[key], f'provenance fact {key}')}</td></tr>"
            for key in sorted(facts)
        )
        out.append("</table>")


    out.append("<h2>Tests</h2>")
    out.append("<table><tr><th>test</th><th>status</th></tr>")
    out.extend(
        f'<tr><td>{_e(test_id, f"test id {describe(test_id)}")}</td>'
        f'<td class="{_e(_STATUS_BADGE[statuses[test_id]])}">{_e(statuses[test_id])}</td></tr>'
        for test_id in sorted(statuses)
    )
    out.append("</table>")

    marks = report_marks(cases)
    if marks["cases"]:
        out.append("<h2>Marks</h2>")
        out.append(
            f"<p>machine_generated={marks['machine_generated']}"
            f" unreviewed_expectations={marks['unreviewed_expectations']}</p>"
        )
        out.append("<table><tr><th>case</th><th>mark</th></tr>")
        out.extend(
            f'<tr><td>{_e(case.case_id, f"case id {describe(case.case_id)}")}</td>'
            f'<td>{_e(format_mark(case), f"mark of case {describe(case.case_id)}")}</td></tr>'
            for case in sorted(cases, key=lambda c: c.case_id)
        )
        out.append("</table>")

    out.append("<h2>Coverage</h2>")
    out.append("<table><tr><th>unit</th><th>covered</th><th>total</th></tr>")
    out.extend(
        f'<tr><td>{_e(unit, f"coverage unit {describe(unit)}")}</td>'
        f"<td>{figures[unit][0]}</td><td>{figures[unit][1]}</td></tr>"
        for unit in sorted(figures)
    )
    out.append("</table>")

    annotated_by_path = {file.file: file for file in annotated.files}
    missing_sources = [path for path in sorted(annotated_by_path) if path not in sources]

    out.append("<h2>Annotated source</h2>")
    for path in sorted(annotated_by_path):
        if path not in sources:
            continue
        file_what = f"annotated file {describe(path)}"
        source_lines = sources[path].replace("\r\n", "\n").replace("\r", "\n").split("\n")
        line_map = {line.line_number: line for line in annotated_by_path[path].lines}
        out.append(f"<h3>{_e(path, file_what)}</h3>")
        out.append("<pre>")
        for number, text in enumerate(source_lines, start=1):
            entry = line_map.get(number)
            # A source line is user content: if it is refused, the message
            # names where it is and never quotes it.
            line_what = f"source line {number} of {file_what}"
            id_what = f"justification id at line {number} of {file_what}"
            if entry is None:
                out.append(f'<code class="ln">{_e(str(number))}</code>{_e(text, line_what)}')
            else:
                assert entry.status in _LINE_CLASSES
                out.append(
                    f'<code class="ln">{_e(str(number))}</code>'
                    f'<span class="{_e(entry.status)}" title="{_e(entry.justification_id or "", id_what)}">{_e(text, line_what)}</span>'
                )
        # annotation lines beyond the supplied source text remain visible
        max_source = len(source_lines)
        for number in sorted(n for n in line_map if n > max_source):
            entry = line_map[number]
            id_what = f"justification id at line {number} of {file_what}"
            out.append(
                f'<code class="ln">{_e(str(number))}</code>'
                f'<span class="{_e(entry.status)}" title="{_e(entry.justification_id or "", id_what)}"></span>'
            )
        out.append("</pre>")

    if missing_sources:
        out.append("<h2>Source not available</h2>")
        out.append("<ul>")
        out.extend(f"<li>{_e(path, f'annotated file {describe(path)}')}</li>" for path in missing_sources)
        out.append("</ul>")

    out.append("</body>")
    out.append("</html>")
    return canonical_text("\n".join(out))

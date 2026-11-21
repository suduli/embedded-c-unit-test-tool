# implements: TOOL-REP-030, TOOL-REP-040
"""HTML report with annotated source (WP-REP-03)."""

from __future__ import annotations

from html.parser import HTMLParser

from ectt.cov.gcov import read_gcov_document
from ectt.cov.justification import annotate_coverage, compute_source_digest
from ectt.exh.results import finalize_result
from ectt.rep.html import render_html
from ectt.rep.model import CoverageEntry, build_report_model
from tests.rep.test_renderers import _FAILURE, CLOCK, _result_set

SOURCE = "int convert(int x)\n{\n    return x + 1;\n}\n    return never;\n"

PAYLOAD = {
    "format_version": "2",
    "gcc_version": "14.1.0",
    "data_file": "d.gcda",
    "files": [
        {
            "file": "src/adc.c",
            "lines": [
                {"line_number": 1, "count": 2, "unexecuted_block": False},
                {"line_number": 3, "count": 2, "unexecuted_block": False},
                {"line_number": 5, "count": 0, "unexecuted_block": False},
                {"line_number": 6, "count": 0, "unexecuted_block": False},
            ],
        }
    ],
}

SOURCE_DIGEST = compute_source_digest(SOURCE)


def _model():
    return build_report_model(
        _result_set(
            (
                finalize_result("t.alpha", "fail", "da" * 32, failures=(_FAILURE,)),
                finalize_result("t.beta", "pass", "db" * 32),
            ),
        ),
        coverage=(CoverageEntry(unit="src/adc.c", covered=2, total=3),),
        clock=CLOCK,
    )


def _annotated():
    doc = read_gcov_document(PAYLOAD)
    justification_record = _make_justification()
    return annotate_coverage(doc, [justification_record], {"src/adc.c": SOURCE_DIGEST})


def _make_justification():
    from ectt.cov.justification import Justification

    return Justification(
        id="J-1",
        file="src/adc.c",
        start_line=5,
        end_line=5,
        author="engineer",
        date="2026-11-20",
        rationale="unreachable without fault injection",
        source_digest=SOURCE_DIGEST,
    )


class _Collector(HTMLParser):
    """Collect tags/attrs/text without depending on external HTML libraries."""

    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def _parse(page: str) -> _Collector:
    collector = _Collector()
    collector.feed(page)
    return collector


# --- TOOL-REP-030: combined report -----------------------------------------------


def test_html_combines_tests_and_coverage() -> None:
    """verifies: TOOL-REP-030 — test table and coverage summary in one document."""
    page = render_html(_model(), _annotated(), {"src/adc.c": SOURCE})
    collector = _parse(page)
    text = "\n".join(collector.text)
    assert "t.alpha" in text and "t.beta" in text
    assert "fail" in text and "pass" in text
    assert "src/adc.c" in text
    assert "<table" in page


def test_html_statuses_and_figures_agree_with_the_model() -> None:
    """verifies: AC-3 — no disagreement between renderer and model."""
    model = _model()
    page = render_html(model, _annotated(), {"src/adc.c": SOURCE})
    collector = _parse(page)
    text = "\n".join(collector.text)
    statuses = model.test_statuses()
    for test_id, status in statuses.items():
        assert test_id in text
        assert status in text
    figures = model.coverage_figures()
    for unit, (covered, total) in figures.items():
        assert unit in text
        assert str(covered) in text and str(total) in text


def test_html_carries_provenance_facts() -> None:
    model = _model()
    page = render_html(model, _annotated(), {})
    facts = model.provenance_facts()
    if facts:
        for key, value in facts.items():
            assert key in page and value in page


# --- TOOL-REP-040: annotated source ------------------------------------------------


def test_annotated_source_shows_per_line_status() -> None:
    """verifies: TOOL-REP-040 — per-line classes covered/uncovered/justified."""
    page = render_html(_model(), _annotated(), {"src/adc.c": SOURCE})
    assert 'class="covered"' in page  # lines 1 and 3
    assert 'class="uncovered"' in page
    assert 'class="justified"' in page and "J-1" in page  # line 5 justified with its id
    # line numbers rendered for every source line
    for number in ("1", "2", "3", "4", "5", "6"):
        assert f'<code class="ln">{number}</code>' in page


def test_justified_line_carries_its_justification_id() -> None:
    page = render_html(_model(), _annotated(), {"src/adc.c": SOURCE})
    # the justification id is visible as the title of the justified span
    assert 'title="J-1"' in page


def test_source_lines_are_escaped() -> None:
    nasty = "int x; // <script>alert('&')</script>\n"
    payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [{"file": "src/nasty.c", "lines": [{"line_number": 1, "count": 1, "unexecuted_block": False}]}],
    }
    annotated = annotate_coverage(read_gcov_document(payload), [], {})
    page = render_html(_model(), annotated, {"src/nasty.c": nasty})
    assert "<script>alert" not in page
    assert "&lt;script&gt;" in page


def test_missing_source_is_surfaced_not_dropped() -> None:
    """verifies: AC-3 — an annotated file without source text is listed."""
    page = render_html(_model(), _annotated(), {})
    assert "Source not available" in page
    assert "src/adc.c" in page


# --- AC-4: determinism and escaping --------------------------------------------------


def test_html_is_byte_identical_and_excludes_report_creation_timestamp() -> None:
    """Re-rendering is byte-identical; the report-creation timestamp is never a
    rendered field (the execution timestamp is TOOL-REP-070 model content and
    legitimately renders, matching the WP-REP-01 renderer convention)."""
    model = _model()
    first = render_html(model, _annotated(), {"src/adc.c": SOURCE})
    again = render_html(model, _annotated(), {"src/adc.c": SOURCE})
    assert first == again
    assert "generated_at" not in first


def test_html_test_ids_are_escaped() -> None:
    model = build_report_model(
        _result_set((finalize_result('t<"&', "pass", "d0" * 32),)),
        coverage=(),
        clock=CLOCK,
    )
    page = render_html(model, _annotated(), {})
    assert 't&lt;&quot;&amp;' in page

# implements: TOOL-REP-080
"""Paginated PDF archival rendering (WP-REP-07)."""

from __future__ import annotations

import re

from ectt.exh.results import finalize_result
from ectt.rep.model import CoverageEntry, build_report_model
from ectt.rep.pdf import render_pdf
from tests.rep.test_renderers import CLOCK, _result_set

_HEADER = "%PDF-1.4\n"


def _model(tests: int = 3):
    results = tuple(
        finalize_result(f"t.{index:03d}", "pass", f"d{index:02d}" * 32) for index in range(tests)
    )
    return build_report_model(
        _result_set(results),
        coverage=(CoverageEntry(unit="src/adc.c", covered=8, total=10),),
        clock=CLOCK,
    )


def _pages(pdf: bytes) -> list[str]:
    """Extract uncompressed content streams (one per page) as latin-1 text."""
    chunks = re.findall(rb"stream\n(.*?)\nendstream", pdf, flags=re.DOTALL)
    return [chunk.decode("latin-1") for chunk in chunks]


def test_pdf_is_structurally_valid() -> None:
    """verifies: TOOL-REP-080 — header, catalog, page tree, xref, trailer."""
    pdf = render_pdf(_model())
    assert pdf.startswith(_HEADER.encode("ascii"))
    assert b"/Type /Catalog" in pdf
    assert b"/Type /Pages" in pdf
    assert b"/Type /Page " in pdf
    assert b"/BaseFont /Helvetica" in pdf
    assert b"xref" in pdf and b"trailer" in pdf and pdf.rstrip().endswith(b"%%EOF")
    # xref offsets point at "N 0 obj" markers
    xref_start = pdf.index(b"\nxref\n") + 1
    lines_after_xref = pdf[xref_start:].split(b"\n")
    first_offset = int(lines_after_xref[3][:10])  # entry 0 is the free sentinel
    assert pdf[first_offset:].startswith(b"1 0 obj")


def test_pdf_carries_tests_and_coverage_from_the_model() -> None:
    """verifies: AC-4 — text derived only from the model accessors."""
    model = _model()
    pdf = render_pdf(model).decode("latin-1")
    for test_id, status in model.test_statuses().items():
        assert f"TEST {test_id} {status}" in pdf
    for unit, (covered, total) in model.coverage_figures().items():
        assert f"COVERAGE {unit} {covered}/{total}" in pdf
    assert "partial: no" in pdf
    for key, value in model.provenance_facts().items():
        assert f"{key}: {value}" in pdf


def test_pdf_paginates_long_runs() -> None:
    """verifies: AC-1 — a long run spans multiple Letter pages with footers."""
    pdf = render_pdf(_model(tests=120))
    pages = _pages(pdf)
    assert len(pages) > 2
    assert "Page 1 of " in pages[0]
    assert f"Page {len(pages)} of {len(pages)}" in pages[-1]
    # every page declares the same MediaBox and carries the page count footer
    assert pdf.count(b"/MediaBox [0 0 612 792]") == len(pages)


def test_pdf_escapes_string_specials_and_substitutes_non_latin1() -> None:
    model = build_report_model(
        _result_set((finalize_result("weird(id\\x)", "pass", "d0" * 32),)),
        coverage=(),
        clock=CLOCK,
    )
    pdf = render_pdf(model)
    # PDF string specials are escaped: ( -> \(, backslash -> \\, ) -> \)
    assert b"(TEST weird\\(id\\\\x\\) pass) Tj" in pdf

    unicode_model = build_report_model(
        _result_set((finalize_result("emoji-日本", "pass", "d0" * 32),)),
        coverage=(),
        clock=CLOCK,
    )
    unicode_pdf = render_pdf(unicode_model)
    assert "emoji-日本".encode() not in unicode_pdf  # raw multibyte never emitted
    assert "emoji-?? pass" in unicode_pdf.decode("latin-1")  # deterministic substitution


def test_pdf_is_byte_identical_and_has_no_timestamp() -> None:
    """verifies: AC-2 — archival determinism: no Info dictionary, stable bytes."""
    first = render_pdf(_model())
    again = render_pdf(_model())
    assert first == again
    assert b"/Info" not in first
    assert b"/CreationDate" not in first


def test_pdf_truncates_overlong_lines() -> None:
    """verifies: AC-3 — long text truncates at the fixed budget with an ellipsis."""
    long_unit = "src/" + "x" * 120 + ".c"
    model = build_report_model(
        _result_set(()),
        coverage=(CoverageEntry(unit=long_unit, covered=0, total=1),),
        clock=CLOCK,
    )
    pdf = render_pdf(model).decode("latin-1")
    assert "..." in pdf
    assert ("x" * 120) not in pdf

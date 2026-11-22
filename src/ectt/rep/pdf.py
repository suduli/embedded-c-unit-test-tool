# implements: TOOL-REP-080
"""Paginated PDF archival rendering of the report model (WP-REP-07).

Satisfies: TOOL-REP-080 — reports in a paginated, archivable format (PDF) for
records retention. The writer is hand-written against the PDF 1.4 structure
(catalog, page tree, base-14 Helvetica with WinAnsi encoding, uncompressed
content streams, xref table, trailer) with no third-party dependency. It is a
pure function of the model content: byte-identical output for identical
inputs (TOOL-REP-100), no Info dictionary or other wall-clock record, text
derived only from the model's ``test_statuses``/``coverage_figures``/
``provenance_facts`` accessors like every other renderer (TOOL-REP-090).
"""

from __future__ import annotations

from ectt.rep.model import ReportModel

__all__ = [
    "render_pdf",
]

_PAGE_WIDTH = 612  # Letter, points
_PAGE_HEIGHT = 792
_MARGIN = 72
_LINE_HEIGHT = 12
_FONT_SIZE = 10
#: Maximum characters drawn on one text line at 10pt Helvetica within the
#: text column; longer lines are truncated with an ellipsis (never silently
#: overflowing the page).
_MAX_LINE_CHARS = 88


def _pdf_escape(text: str) -> str:
    """Escape a string for a PDF literal literal, WinAnsi/Latin-1 only."""
    out: list[str] = []
    for char in text:
        if char in "\\()":
            out.append("\\" + char)
        elif ord(char) < 256:
            out.append(char)
        else:
            out.append("?")  # deterministic substitution, never silent dropping
    return "".join(out)


def _fit(text: str) -> str:
    if len(text) <= _MAX_LINE_CHARS:
        return text
    return text[: _MAX_LINE_CHARS - 3] + "..."


def _model_lines(model: ReportModel) -> list[str]:
    """All report lines, derived only from the model accessors (REP-090)."""
    statuses = model.test_statuses()
    figures = model.coverage_figures()
    facts = model.provenance_facts()

    counts: dict[str, int] = dict.fromkeys(sorted(set(statuses.values())), 0)
    for status in statuses.values():
        counts[status] += 1

    lines: list[str] = [
        f"ectt report {model.run_id}",
        f"partial: {'yes' if model.partial else 'no'}",
        f"tests: {len(statuses)}",
    ]
    lines.extend(f"{key}: {facts[key]}" for key in sorted(facts))
    lines.append("")
    lines.append("TESTS")
    lines.extend(f"TEST {test_id} {statuses[test_id]}" for test_id in sorted(statuses))
    lines.append("")
    lines.append("COVERAGE")
    lines.extend(
        f"COVERAGE {unit} {figures[unit][0]}/{figures[unit][1]}" for unit in sorted(figures)
    )
    return lines


def render_pdf(model: ReportModel) -> bytes:
    """Render the model as a deterministic paginated PDF (TOOL-REP-080).

    Lines flow onto Letter-size pages with fixed margins; every page carries a
    ``Page N of M`` footer. Content streams are uncompressed so the text is
    inspectable and the bytes are stable.
    """
    body_lines = _model_lines(model)
    lines_per_page = (_PAGE_HEIGHT - 2 * _MARGIN) // _LINE_HEIGHT
    pages: list[list[str]] = []
    for start in range(0, max(len(body_lines), 1), lines_per_page - 1):
        chunk = body_lines[start : start + lines_per_page - 1]
        if not chunk:
            chunk = [""]
        pages.append(chunk)
    total_pages = len(pages)

    objects: list[bytes] = []
    page_object_ids = [3 + 2 * index for index in range(total_pages)]  # per page: page + content
    font_id = 3 + 2 * total_pages

    kids = " ".join(f"{page_id} 0 R" for page_id in page_object_ids)
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {total_pages} >>".encode("ascii"))

    for index, chunk in enumerate(pages):
        page_id = page_object_ids[index]
        content_id = page_id + 1
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {_PAGE_WIDTH} {_PAGE_HEIGHT}]"
                f" /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        stream_lines = [f"BT /F1 {_FONT_SIZE} Tf {_LINE_HEIGHT} TL {_MARGIN} {_PAGE_HEIGHT - _MARGIN} Td"]
        stream_lines.extend(f"({_pdf_escape(_fit(line))}) Tj T*" for line in chunk)
        footer = f"Page {index + 1} of {total_pages}"
        stream_lines.append(f"0 {_MARGIN // 2} Td ({_pdf_escape(footer)}) Tj")
        stream_lines.append("ET")
        content = ("\n".join(stream_lines) + "\n").encode("latin-1", errors="replace")
        objects.append(
            b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"endstream"
        )

    objects.append(
        (
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
        ).encode("ascii")
    )

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{number} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_offset = len(out)
    count = len(objects) + 1
    out.extend(f"xref\n0 {count}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.extend(f"trailer\n<< /Size {count} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
    return bytes(out)

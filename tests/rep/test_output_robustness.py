# implements: TOOL-REP-010, TOOL-REP-020, TOOL-REP-030, TOOL-MIG-080
"""A report output cannot be broken by the text it carries.

Every renderer is fed hostile text in each field it writes — a test id, a
digest, a coverage unit, a source file name, a function name, a justification
id, a source line — for every hostile class. Each pair is pinned to exactly one
outcome:

- ``carried``: the document still parses, its structure is the same as with a
  benign value, and the text reads back unchanged;
- a named refusal: a ``ReportModelError`` with the stated reason, raised by the
  renderer before anything is written;
- a refusal by the report model itself, which rejects the identifier first.

Any other exception fails the test.

Observed before the fix, by running the same text through the same writers: a
NUL or an ESC in a test id produced JUnit and Cobertura documents that did not
parse; a newline in a Cobertura export file name read back as a space; a
newline in an LCOV name produced a tracefile that could not be re-imported;
and a lone surrogate in a source line rendered a page that could not be
written as UTF-8.
"""

from __future__ import annotations

import html.parser
import re
import string
import xml.etree.ElementTree as ET
from collections.abc import Callable
from typing import Any
from xml.sax.saxutils import quoteattr

import pytest

from ectt.core.determinism import FixedClock
from ectt.cov.gcov import read_gcov_document
from ectt.cov.justification import AnnotatedCoverage, AnnotatedFile, AnnotatedLine
from ectt.exh.results import finalize_result
from ectt.rep.coverage_interchange import export_cobertura, export_lcov, import_lcov
from ectt.rep.errors import ReportModelError
from ectt.rep.html import render_html
from ectt.rep.machine_formats import render_cobertura, render_junit
from ectt.rep.model import CoverageEntry, ReportModel, build_report_model
from ectt.rep.output_text import xml_attribute
from tests.rep.test_renderers import _result_set

CLOCK = FixedClock("2026-11-19T00:00:00+00:00")
_UNIT = "src/adc.c"

CARRIED = "carried"
#: The report model rejects an identifier that contains whitespace (invalid_id).
MODEL_WHITESPACE = "refused by the model: invalid_id"
#: The report model cannot digest a lone surrogate (it raises UnicodeEncodeError
#: while computing the report id).
MODEL_SURROGATE = "refused by the model: UnicodeEncodeError"

#: Hostile text by class. ``lone_surrogate`` is how non-UTF-8 bytes reach a
#: renderer: a file decoded with ``surrogateescape`` carries each bad byte as one.
HOSTILE: dict[str, str] = {
    "markup": '<script>alert("x")</script><pre>&amp;',
    "quotes": "\"'`&<>",
    "nul": "a\x00b",
    "control": "a\x1bb\x01c",
    "newline": "a\nb",
    "carriage_return": "a\rb",
    "tab": "a\tb",
    "very_long": "x" * 200_000,
    "lone_surrogate": "a\udcffb",
    "bidi_override": "a\u202eb",
    "line_separator": "a\u2028b\u2029c",
}
_CLASSES = list(HOSTILE)

_XML_REFUSALS = ("xml_illegal_character", "unencodable_text")
_HTML_REFUSALS = ("html_illegal_character", "unencodable_text")
_LCOV_REFUSALS = ("lcov_illegal_character", "unencodable_text")

_EVERY_CLASS = dict.fromkeys(_CLASSES, CARRIED)

#: An identifier that goes through the report model: whitespace classes never
#: reach a renderer, and the model itself stumbles on a lone surrogate.
_XML_IDENTIFIER = {
    **_EVERY_CLASS,
    "nul": "xml_illegal_character",
    "control": "xml_illegal_character",
    "newline": MODEL_WHITESPACE,
    "carriage_return": MODEL_WHITESPACE,
    "tab": MODEL_WHITESPACE,
    "lone_surrogate": MODEL_SURROGATE,
    "line_separator": MODEL_WHITESPACE,
}

#: Free text in an XML attribute: tab, line feed and carriage return are written
#: as character references, so they are carried rather than normalised away.
_XML_FREE_TEXT = {
    **_EVERY_CLASS,
    "nul": "xml_illegal_character",
    "control": "xml_illegal_character",
    "lone_surrogate": "unencodable_text",
}

#: Free text that still passes through the report model on its way to an XML
#: attribute — a digest, or a coverage unit built as a bare ``CoverageEntry``,
#: which the model does not check for whitespace. The model refuses nothing
#: here except a lone surrogate, which it cannot digest.
_XML_MODELLED_FREE_TEXT = {**_XML_FREE_TEXT, "lone_surrogate": MODEL_SURROGATE}

#: Free text on one LCOV record line: the format has no escaping, so a line
#: break would split the record.
_LCOV_NAME = {
    **_EVERY_CLASS,
    "nul": "lcov_illegal_character",
    "newline": "lcov_illegal_character",
    "carriage_return": "lcov_illegal_character",
    "lone_surrogate": "unencodable_text",
}

_HTML_IDENTIFIER = {
    **_EVERY_CLASS,
    "nul": "html_illegal_character",
    "newline": MODEL_WHITESPACE,
    "carriage_return": MODEL_WHITESPACE,
    "tab": MODEL_WHITESPACE,
    "lone_surrogate": MODEL_SURROGATE,
    "line_separator": MODEL_WHITESPACE,
}
_HTML_FREE_TEXT = {**_EVERY_CLASS, "nul": "html_illegal_character", "lone_surrogate": "unencodable_text"}


# --- fixtures ------------------------------------------------------------------------------


def _model(*, test_id: str = "t.safe", unit: str = _UNIT, digest: str = "da" * 32) -> ReportModel:
    return build_report_model(
        _result_set((finalize_result(test_id, "pass", digest),)),
        coverage=(CoverageEntry(unit=unit, covered=1, total=2),),
        clock=CLOCK,
    )


def _coverage(file: str, function: str) -> Any:
    return read_gcov_document(
        {
            "format_version": "2",
            "gcc_version": "14.1.0",
            "data_file": "d.gcda",
            "files": [
                {
                    "file": file,
                    "functions": [
                        {"name": function, "start_line": 1, "end_line": 2, "execution_count": 1}
                    ],
                    "lines": [{"line_number": 1, "count": 1, "unexecuted_block": False}],
                }
            ],
        }
    )


def _annotated(file: str = _UNIT, justification_id: str | None = None) -> AnnotatedCoverage:
    return AnnotatedCoverage(
        files=(
            AnnotatedFile(
                file=file,
                lines=(
                    AnnotatedLine(line_number=1, count=1, status="covered"),
                    AnnotatedLine(line_number=2, count=0, status="justified", justification_id=justification_id),
                    AnnotatedLine(line_number=3, count=1, status="covered"),
                ),
                invalidated=(),
            ),
        )
    )


class _Page(html.parser.HTMLParser):
    """Start tags, text and attribute values of a parsed page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.data: list[str] = []
        self.attribute_values: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        self.attribute_values.extend(value for _name, value in attrs if value is not None)

    def handle_data(self, data: str) -> None:
        self.data.append(data)


def _parse(page: str) -> _Page:
    page.encode("utf-8")  # a page that cannot be written is not a report
    parsed = _Page()
    parsed.feed(page)
    parsed.close()
    assert "script" not in parsed.tags
    return parsed


def _render(render: Callable[[], str], allowed: tuple[str, ...]) -> tuple[str | None, str | None]:
    """Run ``render``: ``(output, None)``, or ``(None, reason)`` for a named refusal.

    Any other exception propagates and fails the test.
    """
    try:
        return render(), None
    except ReportModelError as exc:
        assert exc.reason in allowed
        assert str(exc).isprintable()  # the message carries no control character
        return None, exc.reason


def _model_refuses(build: Callable[[], Any], expected: str) -> None:
    """The model rejects the identifier before any renderer is reached."""
    if expected == MODEL_SURROGATE:
        with pytest.raises(UnicodeEncodeError):
            build()
    else:
        with pytest.raises(ReportModelError) as exc_info:
            build()
        assert exc_info.value.reason == "invalid_id"


def _check(output: str | None, reason: str | None, expected: str) -> None:
    assert (reason if reason is not None else CARRIED) == expected
    assert (output is not None) == (expected == CARRIED)


# --- JUnit ------------------------------------------------------------------------------------


@pytest.mark.parametrize("hostile", _CLASSES)
def test_junit_test_id_is_carried_or_refused(hostile: str) -> None:
    text, expected = HOSTILE[hostile], _XML_IDENTIFIER[hostile]
    if expected.startswith("refused by the model"):
        _model_refuses(lambda: _model(test_id=text), expected)
        return
    output, reason = _render(lambda: render_junit(_model(test_id=text)), _XML_REFUSALS)
    _check(output, reason, expected)
    if output is not None:
        assert [case.get("name") for case in ET.fromstring(output).iter("testcase")] == [text]


@pytest.mark.parametrize("hostile", _CLASSES)
def test_junit_digest_attribute_is_carried_or_refused(hostile: str) -> None:
    """The digest is free text: a tab or a line break in it must read back unchanged."""
    text, expected = HOSTILE[hostile], _XML_MODELLED_FREE_TEXT[hostile]
    if expected == MODEL_SURROGATE:
        _model_refuses(lambda: _model(digest=text), expected)
        return
    output, reason = _render(lambda: render_junit(_model(digest=text)), _XML_REFUSALS)
    _check(output, reason, expected)
    if output is not None:
        assert [case.get("hostname") for case in ET.fromstring(output).iter("testcase")] == [text]


# --- Cobertura ---------------------------------------------------------------------------------


@pytest.mark.parametrize("hostile", _CLASSES)
def test_cobertura_unit_name_is_carried_or_refused(hostile: str) -> None:
    """A unit built as a bare ``CoverageEntry`` is not checked for whitespace by
    the model, so whitespace reaches the renderer and is carried."""
    text, expected = HOSTILE[hostile], _XML_MODELLED_FREE_TEXT[hostile]
    if expected == MODEL_SURROGATE:
        _model_refuses(lambda: _model(unit=text), expected)
        return
    output, reason = _render(lambda: render_cobertura(_model(unit=text)), _XML_REFUSALS)
    _check(output, reason, expected)
    if output is not None:
        assert [element.get("name") for element in ET.fromstring(output).iter("class")] == [text]


@pytest.mark.parametrize("hostile", _CLASSES)
def test_cobertura_export_file_name_is_carried_or_refused(hostile: str) -> None:
    text, expected = HOSTILE[hostile], _XML_FREE_TEXT[hostile]
    output, reason = _render(lambda: export_cobertura(_coverage(text, "f")), _XML_REFUSALS)
    _check(output, reason, expected)
    if output is not None:
        assert [element.get("name") for element in ET.fromstring(output).iter("class")] == [text]


# --- LCOV --------------------------------------------------------------------------------------


@pytest.mark.parametrize("hostile", _CLASSES)
def test_lcov_file_and_function_names_are_carried_or_refused(hostile: str) -> None:
    """An LCOV tracefile escapes nothing: a name it cannot keep on one record
    line is refused, and anything carried must re-import as written."""
    text, expected = HOSTILE[hostile], _LCOV_NAME[hostile]
    output, reason = _render(lambda: export_lcov(_coverage(text, text)), _LCOV_REFUSALS)
    _check(output, reason, expected)
    if output is not None:
        (file,) = import_lcov(output).files
        assert file.file == text
        assert [function.name for function in file.functions] == [text]


# --- HTML --------------------------------------------------------------------------------------


def _html_identifiers(text: str) -> str:
    return render_html(_model(test_id=text, unit=text), _annotated(), {})


@pytest.mark.parametrize("hostile", _CLASSES)
def test_html_test_id_and_unit_are_carried_or_refused(hostile: str) -> None:
    text, expected = HOSTILE[hostile], _HTML_IDENTIFIER[hostile]
    if expected.startswith("refused by the model"):
        _model_refuses(lambda: _model(test_id=text), expected)
        return
    output, reason = _render(lambda: _html_identifiers(text), _HTML_REFUSALS)
    _check(output, reason, expected)
    if output is not None:
        parsed = _parse(output)
        assert parsed.tags == _parse(_html_identifiers("plain")).tags  # text, never markup
        assert text in "".join(parsed.data)


def _html_annotated(text: str) -> str:
    return render_html(_model(), _annotated(file=text, justification_id=text), {text: "a\nb\nc\n"})


@pytest.mark.parametrize("hostile", _CLASSES)
def test_html_file_name_and_justification_id_are_carried_or_refused(hostile: str) -> None:
    """These are free text: no model stands between them and the renderer."""
    text, expected = HOSTILE[hostile], _HTML_FREE_TEXT[hostile]
    output, reason = _render(lambda: _html_annotated(text), _HTML_REFUSALS)
    _check(output, reason, expected)
    if output is not None:
        parsed = _parse(output)
        assert parsed.tags == _parse(_html_annotated("plain")).tags
        assert text in "".join(parsed.data)  # the file heading
        assert text in "".join(parsed.attribute_values)  # the justification id


def _html_source(text: str) -> str:
    return render_html(_model(), _annotated(), {_UNIT: f"int first;\n{text}\nint last;\n"})


def _same_line_breaks(text: str) -> str:
    """Benign text with exactly the line breaks of ``text``."""
    return re.sub(r"[^\r\n]", "x", text)


@pytest.mark.parametrize("hostile", _CLASSES)
def test_html_source_line_is_carried_or_refused(hostile: str) -> None:
    """Source text is the one field with nothing upstream restricting it."""
    text, expected = HOSTILE[hostile], _HTML_FREE_TEXT[hostile]
    output, reason = _render(lambda: _html_source(text), _HTML_REFUSALS)
    _check(output, reason, expected)
    if output is not None:
        parsed = _parse(output)
        # same structure as benign text with the same line breaks: a line break
        # in source text is a line break, and each resulting line is shown
        assert parsed.tags == _parse(_html_source(_same_line_breaks(text))).tags
        shown = "".join(parsed.data)
        for fragment in text.replace("\r", "\n").split("\n"):
            assert fragment in shown
        assert "int first;" in shown and "int last;" in shown


# --- the refusals themselves --------------------------------------------------------------------


def test_a_refused_source_line_is_named_by_its_location_and_never_quoted() -> None:
    """verifies: TOOL-SEC-120 — a diagnostic points at user code and never quotes it."""
    secret = 'static const char key[] = "hunter2";'
    with pytest.raises(ReportModelError) as exc_info:
        render_html(_model(), _annotated(), {_UNIT: f"int first;\n{secret}\x00\nint last;\n"})
    message = str(exc_info.value)
    assert exc_info.value.reason == "html_illegal_character"
    assert "source line 2 of annotated file 'src/adc.c'" in message
    assert "U+0000" in message
    assert "hunter2" not in message and "key" not in message
    assert message.isprintable()


def test_a_refusal_shows_an_escape_sequence_instead_of_executing_it() -> None:
    with pytest.raises(ReportModelError) as exc_info:
        render_junit(_model(test_id="t.a\x1b[2Jb"))
    message = str(exc_info.value)
    assert exc_info.value.reason == "xml_illegal_character"
    assert "test id 't.a\\x1b[2Jb'" in message  # shown as an escape
    assert "U+001B" in message
    assert message.isprintable()


def test_a_broken_byte_in_a_source_file_is_refused_by_the_renderer() -> None:
    """A non-UTF-8 byte decoded with surrogateescape is a lone surrogate; the
    refusal comes from the renderer, not from a later attempt to write the file."""
    source = b"int a\x80b;\n".decode("utf-8", "surrogateescape")
    with pytest.raises(ReportModelError) as exc_info:
        render_html(_model(), _annotated(), {_UNIT: source})
    assert exc_info.value.reason == "unencodable_text"
    assert "U+DC80" in str(exc_info.value)


def test_an_lcov_name_with_a_line_break_is_refused_and_names_the_function() -> None:
    with pytest.raises(ReportModelError) as exc_info:
        export_lcov(_coverage("a.c", "do\nthing"))
    assert exc_info.value.reason == "lcov_illegal_character"
    assert "function 'do\\nthing' of source file 'a.c'" in str(exc_info.value)
    assert str(exc_info.value).isprintable()


def test_a_refusal_names_a_long_identifier_in_bounds() -> None:
    with pytest.raises(ReportModelError) as exc_info:
        export_lcov(_coverage("a.c", "x" * 5_000 + "\n"))
    message = str(exc_info.value)
    assert "function '" in message and "...' of source file 'a.c'" in message
    assert "contains a line break or NUL (U+000A)" in message
    assert len(message) < 300 and message.count("x") <= 60


# --- escaping, pinned on the attribute writer ----------------------------------------------------


def test_xml_keeps_tab_line_feed_and_carriage_return_as_character_references() -> None:
    """A parser replaces those three inside an attribute value; written as
    character references they read back exactly as written."""
    value = "a\tb\nc\rd"
    output = export_cobertura(_coverage(value, "f"))
    (element,) = ET.fromstring(output).iter("class")
    assert element.get("name") == value
    attribute = output.split("<class name=", 1)[1].split(" filename=", 1)[0]
    assert attribute == '"a&#9;b&#10;c&#13;d"'


def test_xml_markup_and_quotes_are_escaped_and_read_back_as_written() -> None:
    for value in ('<script>alert("x")</script>', "it's", 'say "hi"', "both \" and '", "&amp;", "<pre>"):
        attribute = xml_attribute(value, "value")
        assert "<script" not in attribute and "<pre" not in attribute
        assert ET.fromstring(f"<r v={attribute}/>").get("v") == value


def test_benign_xml_attributes_are_byte_identical_to_the_previous_escaping() -> None:
    """The JUnit writer used ``xml.sax.saxutils.quoteattr``; for every value that
    call accepts, the attribute writer produces the same bytes."""
    printable = string.printable.replace("\x0b", "").replace("\x0c", "") + "é中\U0001F600"
    for character in printable:
        assert xml_attribute(character) == quoteattr(character)
    for value in ("", "src/adc.c", "ectt run run-agreement", "8/10", "a\tb\nc\rd", 'say "hi" and it\'s'):
        assert xml_attribute(value) == quoteattr(value)

# implements: TOOL-ATG-070
"""Report renderers show machine-generated and unreviewed marks (B4)."""

from __future__ import annotations

from ectt.atg.lifecycle import format_mark, report_marks
from ectt.exh.results import finalize_result
from ectt.rep.html import render_html
from ectt.rep.model import build_report_model
from ectt.rep.pdf import render_pdf
from ectt.rep.render import render_json, render_text
from ectt.tcm.datacases import (
    DataDrivenTestCase,
)
from ectt.tcm.datacases import (
    TestCaseExpected as _Expected,
)
from ectt.tcm.datacases import (
    TestCaseInputs as _Inputs,
)
from ectt.tcm.datacases import (
    TestCaseOrigin as _Origin,
)
from tests.rep.test_renderers import _FAILURE, CLOCK, _result_set


def _case(case_id: str, *, author: str = "atg", engine: str = "ectt-gen",
          review_state: str | None = None) -> DataDrivenTestCase:
    return DataDrivenTestCase(
        case_id=case_id,
        unit="src/adc.c",
        function="adc_read",
        inputs=_Inputs(),
        expected=_Expected(),
        stubs=(),
        origin=_Origin(author=author, engine=engine, review_state=review_state),
    )


def _model():
    return build_report_model(
        _result_set(
            (
                finalize_result("t.alpha", "fail", "da" * 32, failures=(_FAILURE,)),
                finalize_result("t.gen1", "pass", "dg" * 32),
            ),
        ),
        clock=CLOCK,
    )


def test_marked_case_shows_mark_in_every_renderer() -> None:
    """verifies: TOOL-ATG-070 — machine-generated and unreviewed marks surface."""
    case = _case("t.gen1")  # machine-generated, expectation unreviewed
    text = render_text(_model(), cases=[case])
    assert f"TEST t.gen1 pass [{format_mark(case)}]" in text
    assert "machine-generated (ectt-gen); expected value unreviewed" in text
    assert "marks: machine_generated=1 unreviewed_expectations=1" in text

    document = render_json(_model(), cases=[case])
    assert '"mark"' in document and "machine-generated" in document
    assert '"unreviewed_expectations": 1' in document or '"unreviewed_expectations":1' in document

    page = render_html(_model(), _no_annotation(), {}, cases=[case])
    assert "machine-generated (ectt-gen); expected value unreviewed" in page

    pdf = render_pdf(_model(), cases=[case]).decode("latin-1")
    # PDF string specials are escaped, so the mark text carries \( \)
    assert "machine-generated \(ectt-gen\); expected value unreviewed" in pdf


def test_authored_case_shows_the_authored_mark() -> None:
    case = _case("t.alpha", author="human")
    text = render_text(_model(), cases=[case])
    assert "TEST t.alpha fail [authored]" in text
    assert "marks: machine_generated=0 unreviewed_expectations=0" in text


def test_unmarked_report_is_unchanged() -> None:
    """Without cases the output is byte-identical to the unmarked report."""
    model = _model()
    assert render_text(model, cases=()) == render_text(model)
    assert render_json(model, cases=()) == render_json(model)
    assert render_pdf(model, cases=()) == render_pdf(model)


def test_reviewed_case_shows_reviewed_expectation() -> None:
    from ectt.atg.lifecycle import REVIEWED

    case = _case("t.gen1", review_state=REVIEWED)
    text = render_text(_model(), cases=[case])
    assert "expected value reviewed" in text
    assert "unreviewed_expectations=0" in text


def test_marks_ordering_is_deterministic() -> None:
    """verifies: B4 — ordering deterministic (report_marks sorts by case id)."""
    cases = [_case("t.zeta"), _case("t.alpha2"), _case("t.mid")]
    marks = report_marks(cases)
    assert [m["case_id"] for m in marks["cases"]] == ["t.alpha2", "t.mid", "t.zeta"]
    text = render_text(_model(), cases=cases)
    assert text == render_text(_model(), cases=list(reversed(cases)))


def test_renderer_never_gains_a_deep_atg_dependency() -> None:
    """rep imports only the narrow atg lifecycle functions (B4 constraint)."""
    import inspect

    from ectt.rep import html as html_module
    from ectt.rep import pdf as pdf_module
    from ectt.rep import render as render_module

    for module in (render_module, html_module, pdf_module):
        source = inspect.getsource(module)
        assert "from ectt.atg.lifecycle import" in source
        assert "import ectt.atg" not in source.replace("from ectt.atg.lifecycle import", "")


def _no_annotation():
    from ectt.cov.justification import AnnotatedCoverage

    return AnnotatedCoverage(files=())

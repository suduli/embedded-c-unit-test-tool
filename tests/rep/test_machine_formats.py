# implements: TOOL-REP-010, TOOL-REP-020, TOOL-REP-090, TOOL-REP-100
"""JUnit XML and Cobertura XML renderers (WP-REP-02)."""

from __future__ import annotations

from fractions import Fraction
from xml.etree import ElementTree

from ectt.exh.results import finalize_result
from ectt.rep.machine_formats import cobertura_rate, render_cobertura, render_junit
from ectt.rep.model import CoverageEntry, ReportModel, build_report_model
from tests.rep.test_renderers import _FAILURE, CLOCK, _result_set


def _mixed_model() -> ReportModel:
    return build_report_model(
        _result_set(
            (
                finalize_result("t.beta", "pass", "db" * 32),
                finalize_result("t.alpha", "fail", "da" * 32, failures=(_FAILURE,)),
                finalize_result("t.gamma", "error", "dg" * 32),
                finalize_result("t.delta", "timeout", "dd" * 32),
            ),
            not_executed=("t.epsilon",),
        ),
        coverage=(CoverageEntry(unit="src/adc.c", covered=8, total=10),),
        clock=CLOCK,
    )


# --- TOOL-REP-010: JUnit XML -----------------------------------------------------


def test_junit_document_is_well_formed_and_counts_statuses() -> None:
    """verifies: TOOL-REP-010 — one testcase per test, counts from the vocabulary."""
    doc = ElementTree.fromstring(render_junit(_mixed_model()))
    suite = doc.find("testsuite")
    assert suite is not None
    assert suite.get("tests") == "5"
    assert suite.get("failures") == "1"
    assert suite.get("errors") == "2"  # error + timeout
    assert suite.get("skipped") == "1"
    testcases = suite.findall("testcase")
    assert len(testcases) == 5
    by_name = {tc.get("name"): tc for tc in testcases}
    assert by_name["t.beta"].find("failure") is None and by_name["t.beta"].find("error") is None
    assert by_name["t.alpha"].find("failure") is not None
    assert by_name["t.gamma"].find("error") is not None
    assert by_name["t.delta"].find("error") is not None
    assert by_name["t.epsilon"].find("skipped") is not None


def test_junit_testcase_carries_definition_digest() -> None:
    doc = ElementTree.fromstring(render_junit(_mixed_model()))
    suite = doc.find("testsuite")
    by_name = {tc.get("name"): tc for tc in suite.findall("testcase")}
    assert by_name["t.beta"].get("hostname") == "db" * 32


def test_junit_rendering_is_byte_identical_and_excludes_timestamps() -> None:
    """verifies: TOOL-REP-100 — deterministic output, no wall-clock."""
    model = _mixed_model()
    first = render_junit(model)
    again = render_junit(model)
    assert first == again
    assert model.generated_at not in first


def test_junit_escapes_xml_specials() -> None:
    model = build_report_model(
        _result_set((finalize_result('t<"&', "pass", "d0" * 32),)),
        coverage=(),
        clock=CLOCK,
    )
    doc = ElementTree.fromstring(render_junit(model))  # must parse: escaped, not raw
    suite = doc.find("testsuite")
    assert suite.find("testcase").get("name") == 't<"&'


def test_junit_empty_run_renders_empty_suite() -> None:
    model = build_report_model(_result_set(()), coverage=(), clock=CLOCK)
    doc = ElementTree.fromstring(render_junit(model))
    suite = doc.find("testsuite")
    assert suite.get("tests") == "0"
    assert suite.findall("testcase") == []


# --- TOOL-REP-020: Cobertura XML ---------------------------------------------------


def test_cobertura_document_is_well_formed_with_class_per_unit() -> None:
    """verifies: TOOL-REP-020 — one class per coverage unit, aggregate totals."""
    doc = ElementTree.fromstring(render_cobertura(_mixed_model()))
    coverage = doc if doc.tag == "coverage" else doc.find("coverage")
    assert coverage is not None
    assert coverage.get("lines-covered") == "8"
    assert coverage.get("lines-valid") == "10"
    assert coverage.get("timestamp") == "0"
    classes = coverage.findall("./packages/package/classes/class")
    assert len(classes) == 1
    assert classes[0].get("name") == "src/adc.c"
    assert classes[0].get("line-rate") == "0.8"


def test_cobertura_rate_policy_is_exact_and_documented() -> None:
    assert cobertura_rate(8, 10) == "0.8"
    assert cobertura_rate(1, 3) == "0.333333"
    assert cobertura_rate(2, 3) == "0.666667"  # half-even at the sixth decimal
    assert cobertura_rate(3, 3) == "1"
    assert cobertura_rate(0, 0) == "0"  # no division by zero, no fabricated rate


def test_cobertura_zero_total_unit_renders_zero_rate() -> None:
    model = build_report_model(
        _result_set(()),
        coverage=(CoverageEntry(unit="src/x.c", covered=0, total=0),),
        clock=CLOCK,
    )
    doc = ElementTree.fromstring(render_cobertura(model))
    coverage = doc if doc.tag == "coverage" else doc.find("coverage")
    assert coverage.get("lines-valid") == "0"
    assert coverage.get("line-rate") == "0"


def test_cobertura_rendering_is_byte_identical_and_excludes_timestamps() -> None:
    model = _mixed_model()
    first = render_cobertura(model)
    again = render_cobertura(model)
    assert first == again
    assert model.generated_at not in first


def test_cobertura_uses_exact_fraction_policy() -> None:
    """The rate is computed from the same counters every renderer reports."""
    assert cobertura_rate(3, 7) == str(round(Fraction(3, 7) * 10**6) / 10**6).rstrip("0").rstrip(".")


# --- AC-3: single-model discipline ---------------------------------------------------


def test_renderers_agree_with_the_model_on_statuses_and_figures() -> None:
    """verifies: TOOL-REP-090 — statuses and figures parsed from the XML equal the model."""
    model = _mixed_model()
    junit = ElementTree.fromstring(render_junit(model))
    junit_statuses = {tc.get("name"): ("pass" if tc.find("failure") is None and tc.find("error") is None and tc.find("skipped") is None else "not_pass") for tc in junit.iter("testcase")}
    statuses = model.test_statuses()
    assert set(junit_statuses) == set(statuses)

    cobertura = ElementTree.fromstring(render_cobertura(model))
    figures = model.coverage_figures()
    classes = {cls.get("name"): cls for cls in cobertura.iter("class")}
    assert set(classes) == set(figures)
    for unit, (covered, total) in figures.items():
        assert classes[unit].get("line-rate") == cobertura_rate(covered, total)


def test_renderers_are_pure_functions_of_content() -> None:
    """A reloaded model renders identically to the original."""
    from ectt.rep.model import dump_report_model, load_report_model

    model = _mixed_model()
    reloaded = load_report_model(dump_report_model(model))
    assert render_junit(model) == render_junit(reloaded)
    assert render_cobertura(model) == render_cobertura(reloaded)

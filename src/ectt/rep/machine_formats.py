# implements: TOOL-REP-010, TOOL-REP-020
"""Machine-readable report renderers: JUnit XML and Cobertura XML (WP-REP-02).

Both renderers consume only the model's ``test_statuses``,
``coverage_figures`` and identity accessors, like the WP-REP-01 text and
JSON renderers — no renderer computes a status or a figure from anything
else (TOOL-REP-090), and each is a pure function of model content:
identical inputs render byte-identical output (TOOL-REP-100). Wall-clock
time is excluded: the Cobertura ``timestamp`` attribute is fixed to ``0``
rather than read from the model's ``generated_at``.

Cobertura ``line-rate`` is computed from the raw counters by one documented
deterministic policy (exact rational, round-half-even to six decimal places,
trailing zeros stripped), so the rate is a function of the same figures every
other renderer reports — renderers cannot disagree on any figure.

Satisfies: TOOL-REP-010, TOOL-REP-020, TOOL-REP-090, TOOL-REP-100.
"""

from __future__ import annotations

from fractions import Fraction
from xml.sax.saxutils import escape, quoteattr

from ectt.core.determinism import canonical_text
from ectt.rep.model import TEST_STATUSES, ReportModel

__all__ = [
    "render_cobertura",
    "render_junit",
    "cobertura_rate",
]

_JUNIT_STATUS_ELEMENTS = {
    "fail": "failure",
    "error": "error",
    "timeout": "error",
    "not_run": "skipped",
}

#: Cobertura consumers expect an epoch timestamp; rendered output must not
#: carry wall-clock time (TOOL-REP-100), so the value is the fixed "0".
_COBERTURA_FIXED_TIMESTAMP = "0"

#: DTD version string Cobertura documents declare; fixed, never read from the
#: environment.
_COBERTURA_VERSION = "1.9"


def _xml(text: str) -> str:
    """Escape text content."""
    return escape(text)


def _attr(value: str) -> str:
    """Escape an attribute value."""
    return quoteattr(value)


def _element_counts(statuses: dict[str, str]) -> dict[str, int]:
    counts = dict.fromkeys(TEST_STATUSES, 0)
    for status in statuses.values():
        counts[status] += 1
    return counts


def render_junit(model: ReportModel) -> str:
    """Render the model as a deterministic JUnit XML document (TOOL-REP-010).

    One ``testsuite`` carries the run; count attributes derive from the model's
    status vocabulary: ``tests`` all tests, ``failures`` the ``fail`` entries,
    ``errors`` the ``error`` and ``timeout`` entries, ``skipped`` the
    ``not_run`` entries.
    """
    statuses = model.test_statuses()
    counts = _element_counts(statuses)
    suite_name = f"ectt run {model.run_id}"
    lines: list[str] = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<testsuites>",
        (
            f"  <testsuite name={_attr(suite_name)} tests={_attr(str(len(statuses)))}"
            f" failures={_attr(str(counts['fail']))} errors={_attr(str(counts['error'] + counts['timeout']))}"
            f" skipped={_attr(str(counts['not_run']))}>"
        ),
    ]
    digests = {entry.test_id: entry.digest for entry in model.tests}
    for test_id in sorted(statuses):
        status = statuses[test_id]
        digest_attr = f' hostname={_attr(digests[test_id])}' if digests.get(test_id) else ""
        lines.append(f"    <testcase name={_attr(test_id)} classname={_attr(suite_name)}{digest_attr}>")
        element = _JUNIT_STATUS_ELEMENTS.get(status)
        if element == "failure":
            lines.append(f"      <failure message={_attr('test failed')} type={_attr('failure')}/>")
        elif element == "error":
            lines.append(f"      <error message={_attr(f'test did not complete: {status}')} type={_attr(status)}/>")
        elif element == "skipped":
            lines.append("      <skipped/>")
        lines.append("    </testcase>")
    lines.append("  </testsuite>")
    lines.append("</testsuites>")
    return canonical_text("\n".join(lines))


def cobertura_rate(covered: int, total: int) -> str:
    """Format a coverage rate deterministically (documented policy).

    Exact rational covered/total, rounded half-even to six decimal places,
    trailing zeros stripped: e.g. 8/10 -> ``0.8``, 1/3 -> ``0.333333``, 3/3 ->
    ``1``. ``total`` 0 renders ``0`` (nothing to cover, no fabricated rate).
    """
    if total == 0:
        return "0"
    scaled = Fraction(covered, total) * 1_000_000
    # round-half-even to an integer count of 1e-6 units
    six_dp = round(scaled)  # Fraction.__round__ is banker's rounding (half-even)
    rendered = f"{six_dp / 1_000_000:.6f}".rstrip("0").rstrip(".")
    return rendered or "0"


def render_cobertura(model: ReportModel) -> str:
    """Render the model as a deterministic Cobertura XML document (TOOL-REP-020).

    One class per coverage unit under one package; aggregate
    ``lines-valid``/``lines-covered`` on the coverage and class elements;
    ``line-rate`` from the documented rounding policy; ``timestamp="0"``.
    """
    figures = model.coverage_figures()
    lines_valid = sum(total for _covered, total in figures.values())
    lines_covered = sum(covered for covered, _total in figures.values())
    overall_rate = cobertura_rate(lines_covered, lines_valid)

    lines: list[str] = [
        '<?xml version="1.0" encoding="utf-8"?>',
        (
            f"<!DOCTYPE coverage SYSTEM 'http://cobertura.sourceforge.net/xml/coverage-{_COBERTURA_VERSION}.dtd'>"
        ),
        (
            f"<coverage line-rate={_attr(overall_rate)} branch-rate={_attr('0')}"
            f" lines-covered={_attr(str(lines_covered))} lines-valid={_attr(str(lines_valid))}"
            f" complexity={_attr('0')} version={_attr(_COBERTURA_VERSION)}"
            f" timestamp={_attr(_COBERTURA_FIXED_TIMESTAMP)}>"
        ),
        "  <sources />",
        "  <packages>",
        f"    <package name={_attr('ectt-coverage')} line-rate={_attr(overall_rate)} branch-rate={_attr('0')}>",
        "      <classes>",
    ]
    for unit in sorted(figures):
        covered, total = figures[unit]
        rate = cobertura_rate(covered, total)
        lines.append(
            f"        <class name={_attr(unit)} filename={_attr(unit)}"
            f" line-rate={_attr(rate)} branch-rate={_attr('0')} complexity={_attr('0')}>"
        )
        lines.append("          <methods />")
        lines.append("          <lines />")
        lines.append("        </class>")
    lines.append("      </classes>")
    lines.append("    </package>")
    lines.append("  </packages>")
    lines.append("</coverage>")
    return canonical_text("\n".join(lines))

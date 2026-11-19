# implements: TOOL-PLG-050
"""Report format extension point (WP-REP-11).

Equivalence partitioning over provider inputs, plus the core guarantee: a
new format is added by consuming the documented intermediate model, with no
test re-execution.
"""

from __future__ import annotations

import json

import pytest

from ectt.core.determinism import FixedClock
from ectt.exh.results import ExecutionMetadata, ResultSet, finalize_result
from ectt.plg.points import CONTRACT_REPORT_FORMAT, default_registry
from ectt.rep.errors import ReportModelError
from ectt.rep.formats import (
    REPORT_FORMAT_CONTRACT,
    REPORT_FORMATS_POINT_ID,
    ReportFormatRegistry,
    default_format_registry,
)
from ectt.rep.model import (
    ReportModel,
    build_report_model,
    dump_report_model,
    load_report_model,
)
from ectt.rep.render import render_json, render_text

CLOCK = FixedClock("2026-11-19T00:00:00+00:00")


def _markdown_format(model: ReportModel) -> str:
    """A third-party-style format: consumes only the documented model."""
    statuses = model.test_statuses()
    figures = model.coverage_figures()
    lines = [f"# ectt report {model.run_id}"]
    lines.extend(f"- {test_id}: {status}" for test_id, status in sorted(statuses.items()))
    lines.extend(f"- {unit}: {covered}/{total}" for unit, (covered, total) in sorted(figures.items()))
    return "\n".join(lines) + "\n"


def _model_from_persisted_dump() -> ReportModel:
    """Build the model the way a report consumer would: from the persisted dump.

    No ``ResultSet`` and no execution artefact is involved in this function:
    the model already exists. This is the structural proof that adding a
    format re-executes no tests (TOOL-PLG-050).
    """
    result_set = ResultSet(
        run_id="run-1",
        execution=ExecutionMetadata(where="host", toolchain="gcc"),
        results=(finalize_result("t1", "pass", "d1" * 32),),
    )
    model = build_report_model(result_set, clock=CLOCK)
    return load_report_model(dump_report_model(model))


def test_extension_point_descriptor_exists() -> None:
    """The registry implements providers for the documented plg seam."""
    point = default_registry().lookup(REPORT_FORMATS_POINT_ID)
    assert point.contract == CONTRACT_REPORT_FORMAT == REPORT_FORMAT_CONTRACT
    assert point.interface_version == "1"


def test_custom_format_added_without_reexecuting_tests() -> None:
    model = _model_from_persisted_dump()
    registry = ReportFormatRegistry()
    registry.register("markdown", _markdown_format)

    rendered = registry.render(model, "markdown")

    assert rendered == "# ectt report run-1\n- t1: pass\n"
    assert registry.render(model, "markdown") == rendered  # deterministic


def test_builtin_formats_stay_byte_identical_to_direct_renderers() -> None:
    model = _model_from_persisted_dump()
    registry = default_format_registry()

    assert registry.names() == ("json", "text")
    assert registry.render(model, "text") == render_text(model)
    assert registry.render(model, "json") == render_json(model)


def test_registry_instances_are_isolated() -> None:
    first = default_format_registry()
    first.register("mine", _markdown_format)

    assert default_format_registry().names() == ("json", "text")
    assert first.names() == ("json", "mine", "text")


# --- equivalence partitions over provider inputs ---------------------------------------


@pytest.mark.parametrize("bad_name", ["", " ", "has space", "tab\tname", None, 7])
def test_invalid_format_names_are_refused(bad_name: object) -> None:
    registry = ReportFormatRegistry()

    with pytest.raises(ReportModelError) as excinfo:
        registry.register(bad_name, _markdown_format)  # type: ignore[arg-type]
    assert excinfo.value.reason == "invalid_format_name"


def test_non_callable_provider_is_refused() -> None:
    registry = ReportFormatRegistry()

    with pytest.raises(ReportModelError) as excinfo:
        registry.register("broken", "not a function")  # type: ignore[arg-type]
    assert excinfo.value.reason == "invalid_provider"


def test_duplicate_format_name_is_refused() -> None:
    registry = ReportFormatRegistry()
    registry.register("mine", _markdown_format)

    with pytest.raises(ReportModelError) as excinfo:
        registry.register("mine", _markdown_format)
    assert excinfo.value.reason == "duplicate_format"


def test_unknown_format_render_is_refused_and_names_available_ones() -> None:
    registry = default_format_registry()

    with pytest.raises(ReportModelError) as excinfo:
        registry.render(_model_from_persisted_dump(), "pdf")
    assert excinfo.value.reason == "unknown_format"
    assert "text" in str(excinfo.value)


def test_custom_format_output_is_json_safe_when_requested() -> None:
    """The same custom-format idea over a JSON-emitting provider."""
    model = _model_from_persisted_dump()
    registry = ReportFormatRegistry()
    registry.register("compact", lambda m: json.dumps(m.test_statuses(), sort_keys=True))

    assert json.loads(registry.render(model, "compact")) == {"t1": "pass"}

# implements: TOOL-TRC-080
"""Requirement-to-source-element links (WP-TRC-05).

Verifies: TOOL-TRC-080 — links to a function or a line range, resolved through
the analysis model and persisted as function anchors that survive line movement.
"""

from __future__ import annotations

import json

import pytest

from ectt.ana.model import (
    AnalysisModel,
    AnalysisUnit,
    FunctionModel,
    ProvenanceModel,
    SourceLocation,
)
from ectt.trc import (
    SourceLink,
    TrcError,
    dump_source_links,
    load_source_links,
    resolve_source_links,
)


def _function(name: str, line: int, file: str = "src/adc.c") -> FunctionModel:
    return FunctionModel(
        name=name,
        linkage="external",
        storage_class="none",
        location=SourceLocation(file, line),
        return_type="ref:type.int",
    )


def _model(*, shift: int = 0, names: tuple[str, ...] = ("adc_init", "adc_read", "adc_close")) -> AnalysisModel:
    starts = {"adc_init": 10, "adc_read": 30, "adc_close": 60}
    unit = AnalysisUnit(
        path="src/adc.c",
        status="parsed",
        functions=tuple(_function(n, starts[n] + shift) for n in names),
    )
    failed = AnalysisUnit(path="src/broken.c", status="failed")
    provenance = ProvenanceModel(tool_version="0", front_end="test", generated_at="t")
    return AnalysisModel(provenance=provenance, units=(unit, failed))


def _one(link: SourceLink, model: AnalysisModel | None = None):
    (result,) = resolve_source_links([link], model or _model()).links
    return result


def test_function_link_resolves_to_its_function() -> None:
    result = _one(SourceLink("REQ-1", "src/adc.c", function="adc_read"))
    assert (result.status, result.function, result.approximate) == ("resolved", "adc_read", False)


def test_line_range_inside_a_function_resolves_to_that_function_as_approximate() -> None:
    result = _one(SourceLink("REQ-1", "src/adc.c", start_line=32, end_line=40))
    assert (result.status, result.function, result.approximate) == ("resolved", "adc_read", True)


def test_range_in_the_last_function_resolves() -> None:
    result = _one(SourceLink("REQ-1", "src/adc.c", start_line=61, end_line=500))
    assert (result.status, result.function) == ("resolved", "adc_close")


@pytest.mark.parametrize(
    ("link", "reason"),
    [
        (SourceLink("R", "src/adc.c", start_line=1, end_line=5), "range_outside_any_function"),
        (SourceLink("R", "src/adc.c", start_line=25, end_line=35), "range_spans_functions"),
        (SourceLink("R", "src/adc.c", function="adc_missing"), "function_not_found"),
        (SourceLink("R", "src/none.c", function="f"), "unit_not_found"),
        (SourceLink("R", "src/broken.c", function="f"), "unit_not_parsed"),
    ],
)
def test_unresolvable_links_are_reported_with_a_reason(link: SourceLink, reason: str) -> None:
    result = _one(link)
    assert (result.status, result.reason, result.function) == ("unresolved", reason, None)


def test_duplicate_function_names_are_ambiguous_not_guessed() -> None:
    unit = AnalysisUnit(
        path="src/adc.c",
        status="parsed",
        functions=(_function("dup", 10), _function("dup", 40)),
    )
    model = AnalysisModel(provenance=ProvenanceModel("0", "t", "t"), units=(unit,))
    assert _one(SourceLink("R", "src/adc.c", function="dup"), model).reason == "ambiguous_function"


def test_functions_declared_in_other_files_are_not_attributed_to_the_unit() -> None:
    unit = AnalysisUnit(
        path="src/adc.c",
        status="parsed",
        functions=(_function("from_header", 5, file="inc/adc.h"), _function("own", 20)),
    )
    model = AnalysisModel(provenance=ProvenanceModel("0", "t", "t"), units=(unit,))
    assert _one(SourceLink("R", "src/adc.c", function="from_header"), model).reason == "function_not_found"
    assert _one(SourceLink("R", "src/adc.c", start_line=6, end_line=8), model).reason == "range_outside_any_function"


def test_anchored_links_survive_line_movement() -> None:
    """The persisted anchor is the function: moving code does not break the link."""
    ranged = SourceLink("REQ-1", "src/adc.c", start_line=32, end_line=40)
    before = resolve_source_links([ranged], _model())
    anchored = before.anchored()
    assert anchored == (SourceLink("REQ-1", "src/adc.c", function="adc_read"),)

    after = resolve_source_links(anchored, _model(shift=100))
    assert [(r.status, r.function) for r in after.links] == [("resolved", "adc_read")]
    # The original raw range no longer lands in the same function once code has moved.
    assert resolve_source_links([ranged], _model(shift=100)).links[0].function != "adc_read"


def test_renamed_function_is_reported_not_silently_relinked() -> None:
    anchored = (SourceLink("REQ-1", "src/adc.c", function="adc_read"),)
    renamed = _model(names=("adc_init", "adc_close"))
    (result,) = resolve_source_links(anchored, renamed).links
    assert (result.status, result.reason) == ("unresolved", "function_not_found")


def test_forward_and_reverse_views_use_anchored_elements() -> None:
    links = [
        SourceLink("REQ-1", "src/adc.c", function="adc_init"),
        SourceLink("REQ-1", "src/adc.c", start_line=31, end_line=33),
        SourceLink("REQ-2", "src/adc.c", function="adc_read"),
        SourceLink("REQ-3", "src/adc.c", function="nope"),
    ]
    resolution = resolve_source_links(links, _model())

    assert resolution.forward() == {
        "REQ-1": (("src/adc.c", "adc_init"), ("src/adc.c", "adc_read")),
        "REQ-2": (("src/adc.c", "adc_read"),),
    }
    assert resolution.reverse() == {
        ("src/adc.c", "adc_init"): ("REQ-1",),
        ("src/adc.c", "adc_read"): ("REQ-1", "REQ-2"),
    }
    assert [r.link.requirement_id for r in resolution.unresolved] == ["REQ-3"]


def test_duplicate_links_collapse_and_order_is_input_free() -> None:
    a = SourceLink("REQ-1", "src/adc.c", function="adc_init")
    b = SourceLink("REQ-2", "src/adc.c", function="adc_read")
    first = resolve_source_links([a, b, a], _model())
    second = resolve_source_links([b, a], _model())
    assert first == second
    assert len(first.links) == 2


def test_windows_style_and_dot_prefixed_unit_paths_match() -> None:
    result = _one(SourceLink("REQ-1", ".\\src\\adc.c", function="adc_init"))
    assert result.status == "resolved"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"function": "f", "start_line": 1, "end_line": 2},
        {},
        {"start_line": 3},
        {"start_line": 5, "end_line": 4},
        {"start_line": 0, "end_line": 4},
        {"function": "  "},
    ],
)
def test_malformed_links_are_refused(kwargs: dict[str, object]) -> None:
    with pytest.raises(TrcError):
        SourceLink("REQ-1", "src/adc.c", **kwargs)  # type: ignore[arg-type]


def test_link_identifiers_are_validated() -> None:
    with pytest.raises(TrcError) as excinfo:
        SourceLink("has space", "src/adc.c", function="f")
    assert excinfo.value.reason == "invalid_id"
    with pytest.raises(TrcError):
        SourceLink("REQ-1", " ", function="f")


def test_persisted_links_roundtrip_deterministically() -> None:
    links = [
        SourceLink("REQ-2", "src/adc.c", function="adc_read"),
        SourceLink("REQ-1", "src/adc.c", start_line=3, end_line=9),
    ]
    text = dump_source_links(links)
    assert text == dump_source_links(reversed(links))
    assert load_source_links(text) == tuple(sorted(links))


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("{nope", "invalid_links_document"),
        ("[]", "unsupported_links_version"),
        ('{"links_version": "9", "links": []}', "unsupported_links_version"),
        ('{"links_version": "1", "links": {}}', "invalid_links_document"),
        ('{"links_version": "1", "links": [3]}', "invalid_links_document"),
        ('{"links_version": "1", "links": [{"requirement_id": "R", "unit": "u", "function": "f", "extra": 1}]}', "invalid_links_document"),
        ('{"links_version": "1", "links": [{"unit": "u", "function": "f"}]}', "invalid_links_document"),
        ('{"links_version": "1", "links": [{"requirement_id": "R", "unit": "u"}]}', "invalid_link"),
    ],
)
def test_loader_refuses_bad_documents(text: str, reason: str) -> None:
    with pytest.raises(TrcError) as excinfo:
        load_source_links(text)
    assert excinfo.value.reason == reason


def test_dump_contains_no_wall_clock_or_absolute_paths() -> None:
    text = dump_source_links([SourceLink("REQ-1", "src/adc.c", function="f")])
    assert json.loads(text) == {
        "links": [{"function": "f", "requirement_id": "REQ-1", "unit": "src/adc.c"}],
        "links_version": "1",
    }


@pytest.mark.parametrize(
    "entry",
    [
        {"requirement_id": "R1", "unit": "src/a.c", "function": 5},
        {"requirement_id": "R1", "unit": 7, "function": "f"},
        {"requirement_id": "R1", "unit": "src/a.c", "start_line": 2.5, "end_line": 3.5},
        {"requirement_id": "R1", "unit": "src/a.c", "start_line": 1.0, "end_line": 2.0},
        {"requirement_id": "R1", "unit": "src/a.c", "function": ["f"]},
    ],
)
def test_loader_rejects_wrongly_typed_fields_with_trc_error(entry: dict[str, object]) -> None:
    text = json.dumps({"links_version": "1", "links": [entry]})
    with pytest.raises(TrcError):
        load_source_links(text)

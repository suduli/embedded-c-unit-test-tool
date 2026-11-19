# implements: TOOL-PAR-090
"""Macro resolution for extracted interfaces (WP-ANA-06).

Function-like and object-like macros used in the signature of an extracted
definition are resolved; function-like uses are recorded as obscuring the
true interface. Deterministic, sorted, derived-data only (not in S1).
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from ectt.ana.errors import ExtractionRefusedError
from ectt.ana.frontend import parse
from ectt.ana.macros import (
    DETAILED_PROCESSING_OPTIONS,
    MacroResolution,
    resolve_interface_macros,
)

SOURCE = (
    "#define MAX_CHANNELS 8\n"
    "#define FLAG (1 << 3)\n"
    "#define PTR(T) T*\n"
    "#define BODY_ONLY 7\n"
    "int read_channel(int a[MAX_CHANNELS]) { return a[0] + BODY_ONLY; }\n"
    "int deref(PTR(int) p, int fallback) { return fallback; }\n"
    "int mixed(int a[MAX_CHANNELS], PTR(char) q) { return 0; }\n"
)
LINE_MAX_CHANNELS_DEF = 1
LINE_FLAG_DEF = 2
LINE_PTR_DEF = 3
LINE_READ_CHANNEL = 5
LINE_DEREF = 6
LINE_MIXED = 7


def _resolve(code: str, std: str = "gnu89") -> tuple[MacroResolution, ...]:
    parsed = parse(
        "probe.c",
        args=[f"-std={std}"],
        unsaved_files=[("probe.c", code)],
        options=DETAILED_PROCESSING_OPTIONS,
    )
    return resolve_interface_macros(parsed)


def _by_name(resolutions: tuple[MacroResolution, ...], name: str) -> list[MacroResolution]:
    return [r for r in resolutions if r.name == name]


def test_object_like_macro_in_signature_is_resolved() -> None:
    records = _resolve(SOURCE)

    found = _by_name(records, "MAX_CHANNELS")
    assert len(found) == 2  # read_channel, mixed — both signature uses
    assert {r.used_in_function for r in found} == {"read_channel", "mixed"}
    first = next(r for r in found if r.used_in_function == "read_channel")
    assert first.kind == "object_like"
    assert first.obscures_interface is False
    assert first.expansion == "8"
    assert first.definition_file is not None
    assert first.definition_file.endswith("probe.c")
    assert first.definition_line == LINE_MAX_CHANNELS_DEF
    assert first.used_at_line == LINE_READ_CHANNEL


def test_function_like_macro_in_signature_obscures() -> None:
    records = _resolve(SOURCE)

    found = _by_name(records, "PTR")
    assert len(found) == 2  # deref, mixed
    first = next(r for r in found if r.used_in_function == "deref")
    assert first.kind == "function_like"
    assert first.obscures_interface is True
    assert first.expansion is None
    assert first.definition_line == LINE_PTR_DEF
    assert first.used_at_line == LINE_DEREF


def test_object_like_expansion_starting_with_paren_is_not_function_like() -> None:
    """verifies: TOOL-PAR-090 — ``#define FLAG (1 << 3)`` is object-like.

    Function-likeness follows token adjacency to the name, not the shape of
    the expansion; a naive "second token is ( " rule would misclassify it.
    """
    records = _resolve(SOURCE)

    assert _by_name(records, "FLAG") == []  # defined but never used


def test_body_macro_use_is_not_an_interface_use() -> None:
    """BODY_ONLY appears only inside a function body: not recorded."""
    records = _resolve(SOURCE)

    assert _by_name(records, "BODY_ONLY") == []


def test_two_signature_macros_on_one_line_sort_by_name() -> None:
    records = _resolve(SOURCE)

    mixed = [r for r in records if r.used_in_function == "mixed"]
    assert [r.name for r in mixed] == ["MAX_CHANNELS", "PTR"]  # same line, name order
    assert mixed[0].kind == "object_like"
    assert mixed[1].kind == "function_like"


def test_unit_without_macro_use_resolves_empty() -> None:
    records = _resolve(b"int add(int a, int b) { return a + b; }\n".decode())

    assert records == ()


def test_resolution_is_deterministic() -> None:
    first = tuple(r.to_dict() for r in _resolve(SOURCE))
    second = tuple(r.to_dict() for r in _resolve(SOURCE))

    assert first == second


def test_records_are_sorted_by_function_line_name() -> None:
    records = _resolve(SOURCE)

    keys = [(r.used_in_function, r.used_at_line, r.name) for r in records]
    assert keys == sorted(keys)
    assert len(records) == 4  # read_channel:MAX, deref:PTR, mixed:MAX, mixed:PTR


def test_to_dict_is_json_safe() -> None:
    records = _resolve(SOURCE)

    blob = json.dumps([r.to_dict() for r in records])
    restored: list[dict[str, Any]] = json.loads(blob)
    assert restored[0]["name"] == records[0].name
    assert restored[0]["obscures_interface"] is records[0].obscures_interface


def test_failed_translation_unit_is_refused() -> None:
    parsed = parse(
        "bad.c",
        args=["-std=gnu89"],
        unsaved_files=[("bad.c", b"int broken( {\n")],
        options=DETAILED_PROCESSING_OPTIONS,
    )

    with pytest.raises(ExtractionRefusedError):
        resolve_interface_macros(parsed)


def test_resolution_requires_detailed_processing_record() -> None:
    """Without the record the AST carries no macro cursors: empty, no guess."""
    parsed = parse(
        "probe.c",
        args=["-std=gnu89"],
        unsaved_files=[("probe.c", SOURCE)],
    )

    assert resolve_interface_macros(parsed) == ()

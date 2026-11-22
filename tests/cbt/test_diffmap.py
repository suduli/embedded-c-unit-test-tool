# implements: TOOL-CBT-020
"""Source diff -> construct identities via the 1.5 function extents (A3).

The identity convention is the coverage data's: ``path:line`` for line
constructs, the bare path for a file-level construct. Every non-precise case
carries its named note; nothing is silently narrowed.
"""

from __future__ import annotations

import pytest

from ectt.cbt import DiffImpact, LineRange, SourceDiff, changed_constructs, impacts_of

EXTENTS = {
    # src/adc.c: adc_read occupies lines 10..19, adc_scale 30..39
    "adc_read": (10, 19),
    "adc_scale": (30, 39),
}


def _diff(*ranges: tuple[int, int], path: str = "src/adc.c", old: str = "a" * 8, new: str = "b" * 8) -> SourceDiff:
    return SourceDiff(path=path, old_digest=old, new_digest=new, ranges=tuple(LineRange(first, last) for first, last in ranges))


def test_a_change_inside_one_function_maps_to_its_lines() -> None:
    """verifies: TOOL-CBT-020 — precise case: line constructs plus the named
    function, nothing file-level."""
    impact = changed_constructs(_diff((12, 13)), EXTENTS)
    assert impact.changed is True and impact.whole_file is False
    assert impact.functions == ("adc_read",)
    assert impact.constructs == ("src/adc.c:12", "src/adc.c:13")
    assert impact.file_construct is None and impact.note is None


def test_a_change_spanning_two_functions_names_both() -> None:
    """verifies: TOOL-CBT-020 — a range crossing extents attributes every
    changed line to its own function."""
    impact = changed_constructs(_diff((18, 31)), EXTENTS)
    assert impact.functions == ("adc_read", "adc_scale")
    assert impact.constructs == (
        "src/adc.c:18",
        "src/adc.c:19",
        "src/adc.c:30",
        "src/adc.c:31",
    )


def test_a_change_between_functions_falls_back_to_the_file_named() -> None:
    """verifies: TOOL-CBT-020 — lines no extent covers cannot be attributed:
    the file-level construct rides along with the named note."""
    impact = changed_constructs(_diff((5, 6)), EXTENTS)
    assert impact.functions == () and impact.constructs == ()
    assert impact.file_construct == "src/adc.c"
    assert impact.note == "lines_outside_extents"


def test_a_change_partly_inside_and_partly_outside_keeps_both() -> None:
    """verifies: TOOL-CBT-020 — the precise constructs stay precise and the
    unattributable lines still surface the file-level construct."""
    impact = changed_constructs(_diff((12, 25)), EXTENTS)
    assert impact.functions == ("adc_read",)
    assert impact.constructs == tuple(f"src/adc.c:{line}" for line in range(12, 20))
    assert impact.file_construct == "src/adc.c"
    assert impact.note == "lines_outside_extents"


def test_a_whole_file_change_is_the_file_construct() -> None:
    """verifies: TOOL-CBT-020 — no ranges: whole-file change, named."""
    impact = changed_constructs(_diff(), EXTENTS)
    assert impact.whole_file is True
    assert impact.file_construct == "src/adc.c"
    assert impact.note == "whole_file_change"
    assert impact.functions == () and impact.constructs == ()


def test_a_model_without_extents_falls_back_whole_file() -> None:
    """verifies: TOOL-CBT-020 — the model cannot narrow what it does not know:
    whole file, named note."""
    impact = changed_constructs(_diff((12, 13)), {})
    assert impact.whole_file is True
    assert impact.file_construct == "src/adc.c"
    assert impact.note == "no_function_extents"


def test_unchanged_content_is_not_an_impact() -> None:
    """verifies: TOOL-CBT-020 — equal digests mean no change, whatever the ranges say."""
    impact = changed_constructs(
        SourceDiff(path="src/adc.c", old_digest="same", new_digest="same"), EXTENTS
    )
    assert impact.changed is False
    assert impact.constructs == () and impact.functions == ()
    assert impact.file_construct is None and impact.note is None


def test_a_new_file_is_a_whole_file_change() -> None:
    """verifies: TOOL-CBT-020 — an empty old digest (the file did not exist)
    changes the whole file, named."""
    impact = changed_constructs(SourceDiff(path="src/new.c", old_digest="", new_digest="b" * 8), {})
    assert impact.changed is True and impact.whole_file is True
    assert impact.note == "no_function_extents"


def test_impacts_of_maps_several_files_in_order() -> None:
    """verifies: TOOL-CBT-020 — one impact per diff; a path with no recorded
    extents falls back per file."""
    impacts = impacts_of(
        [_diff((12, 12)), _diff((1, 1), path="src/hal.c")],
        {"src/adc.c": EXTENTS},
    )
    assert [i.path for i in impacts] == ["src/adc.c", "src/hal.c"]
    assert impacts[0].functions == ("adc_read",)
    assert impacts[1].note == "no_function_extents"


def test_bad_input_is_refused() -> None:
    """verifies: API — malformed ranges and blank paths are refused."""
    with pytest.raises(ValueError):
        LineRange(5, 4)
    with pytest.raises(ValueError):
        LineRange(0, 3)
    with pytest.raises(ValueError):
        SourceDiff(path=" ", old_digest="a", new_digest="b")
    with pytest.raises(ValueError):
        SourceDiff(path="x.c", old_digest="same", new_digest="same", ranges=(LineRange(1, 2),))


def test_the_answer_is_deterministic_under_input_order() -> None:
    """verifies: TOOL-NFR-060 — extents order does not change the answer."""
    first = changed_constructs(_diff((12, 12), (31, 31)), EXTENTS)
    shuffled = {"adc_scale": EXTENTS["adc_scale"], "adc_read": EXTENTS["adc_read"]}
    second = changed_constructs(_diff((12, 12), (31, 31)), shuffled)
    assert first == second
    assert isinstance(first, DiffImpact)
    assert first.functions == ("adc_read", "adc_scale")

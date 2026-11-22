# implements: TOOL-CBT-020
"""Map a source diff to the construct identities the coverage data uses (A3).

Change impact (``ectt.cbt.impact.affected_cases``) intersects a change against
the constructs each test's coverage covers. This module does the first half:
from a source change — the file, its old and new content digests, and the
changed line ranges — it produces the affected construct identities, using the
function extents recorded by the analysis model (schema 1.5,
``FunctionModel.start_line``/``end_line``, 1-indexed inclusive).

The identity convention is the one the coverage data uses: ``<path>:<line>``
for a line construct, and the bare ``<path>`` for a file-level construct.

Conservative mapping, each case named:

* **changed lines inside a function extent** map to their line constructs and
  the containing function is named — this is the precise case;
* **changed lines outside every known extent** (between functions, top-level
  data) cannot be attributed to a function, so the file-level construct is
  returned too, with the note ``lines_outside_extents`` — never silently
  narrowed;
* **a whole-file change** (no ranges given, or a new file) is the file-level
  construct with the note ``whole_file_change``;
* **a path with no recorded extents** falls back to the whole file with the
  note ``no_function_extents`` — the model cannot narrow what it does not
  know.

Extents arrive as plain data (function name -> ``(first, last)``); composition
extracts them from the 1.5 model, as with the rest of this package's inputs.
Deterministic: identical inputs give identical, sorted results.

Satisfies: TOOL-CBT-020 (the diff half of change impact).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

__all__ = [
    "NOTE_LINES_OUTSIDE_EXTENTS",
    "NOTE_NO_FUNCTION_EXTENTS",
    "NOTE_WHOLE_FILE_CHANGE",
    "DiffImpact",
    "LineRange",
    "SourceDiff",
    "changed_constructs",
]

NOTE_LINES_OUTSIDE_EXTENTS = "lines_outside_extents"
NOTE_NO_FUNCTION_EXTENTS = "no_function_extents"
NOTE_WHOLE_FILE_CHANGE = "whole_file_change"


@dataclass(frozen=True)
class LineRange:
    """A 1-based, inclusive line range of a changed file."""

    first: int
    last: int

    def __post_init__(self) -> None:
        if not isinstance(self.first, int) or not isinstance(self.last, int):
            raise ValueError("line ranges are integers")
        if self.first < 1 or self.last < self.first:
            raise ValueError(f"line range must be 1-based and non-empty, got {self.first}..{self.last}")

    def contains(self, line: int) -> bool:
        return self.first <= line <= self.last


@dataclass(frozen=True)
class SourceDiff:
    """One changed file: its paths' old and new content digests plus ranges.

    ``ranges`` empty means a whole-file change (rewrite or new file). Equal
    digests mean the file did not change.
    """

    path: str
    old_digest: str
    new_digest: str
    ranges: tuple[LineRange, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValueError("a source diff names a non-empty path")
        for what, digest in (("old_digest", self.old_digest), ("new_digest", self.new_digest)):
            if not isinstance(digest, str):
                raise ValueError(f"a source diff's {what} must be a string (empty for a new file)")
        if self.old_digest == self.new_digest and self.ranges:
            raise ValueError("a source diff with equal digests carries no ranges")

    @property
    def changed(self) -> bool:
        return self.old_digest != self.new_digest


@dataclass(frozen=True)
class DiffImpact:
    """The construct identities a change affects, at the coverage data's granularity."""

    path: str
    changed: bool
    #: True when the answer is the file-level construct (fallback or whole-file).
    whole_file: bool
    #: Names of the functions whose extents contain changed lines, sorted.
    functions: tuple[str, ...]
    #: ``path:line`` constructs for changed lines inside extents, sorted.
    constructs: tuple[str, ...]
    #: The file-level identity when the change is file-wide (or fell back to it).
    file_construct: str | None = None
    #: The named note for a fallback; ``None`` for the precise case.
    note: str | None = None


def changed_constructs(
    diff: SourceDiff,
    extents: Mapping[str, tuple[int, int]],
) -> DiffImpact:
    """The affected construct identities of one changed file, deterministic.

    ``extents`` maps function name to ``(first_line, last_line)`` inclusive,
    from the analysis model's 1.5 function extents. See the module docstring
    for the mapping rules and their named notes.
    """
    if not diff.changed:
        return DiffImpact(path=diff.path, changed=False, whole_file=False, functions=(), constructs=())

    if not extents:
        return DiffImpact(
            path=diff.path,
            changed=True,
            whole_file=True,
            functions=(),
            constructs=(),
            file_construct=diff.path,
            note=NOTE_NO_FUNCTION_EXTENTS,
        )

    if not diff.ranges:
        return DiffImpact(
            path=diff.path,
            changed=True,
            whole_file=True,
            functions=(),
            constructs=(),
            file_construct=diff.path,
            note=NOTE_WHOLE_FILE_CHANGE,
        )

    changed_lines = sorted({line for range_ in diff.ranges for line in range(range_.first, range_.last + 1)})
    functions: list[str] = []
    constructs: list[str] = []
    outside = False
    for line in changed_lines:
        inside = [name for name, (first, last) in extents.items() if first <= line <= last]
        if inside:
            constructs.append(f"{diff.path}:{line}")
            functions.extend(inside)
        else:
            outside = True
    if outside:
        # Changed lines the model cannot attribute to any function: the
        # file-level construct rides along, conservatively, with the note.
        return DiffImpact(
            path=diff.path,
            changed=True,
            whole_file=False,
            functions=tuple(sorted(set(functions))),
            constructs=tuple(sorted(constructs)),
            file_construct=diff.path,
            note=NOTE_LINES_OUTSIDE_EXTENTS,
        )
    return DiffImpact(
        path=diff.path,
        changed=True,
        whole_file=False,
        functions=tuple(sorted(set(functions))),
        constructs=tuple(sorted(constructs)),
    )


def impacts_of(
    diffs: Sequence[SourceDiff],
    extents_by_path: Mapping[str, Mapping[str, tuple[int, int]]],
) -> tuple[DiffImpact, ...]:
    """One impact per diff, in input order (files with no extents fall back)."""
    return tuple(
        changed_constructs(diff, extents_by_path.get(diff.path, {})) for diff in diffs
    )

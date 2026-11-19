"""Stub scope control and indirect-call stubbing (WP-GEN-08).

The plan decides what gets stubbed: every external reference by default, any
individual function excluded by the user (real implementation linked
instead), standard-library functions only on explicit request from the
documented vocabulary, and functions reached through function pointers —
including structure members — recorded with their access path.

Satisfies: TOOL-STB-080, TOOL-STB-100, TOOL-STB-140.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ectt.gen.errors import GenError

__all__ = [
    "STDLIB_FUNCTIONS",
    "POINTER_TARGET_MARKER",
    "StubPlan",
    "UnknownStubReferenceError",
    "build_stub_plan",
]

# The documented standard-library vocabulary that may be stubbed on explicit
# request (TOOL-STB-100). Anything outside this set is refused.
STDLIB_FUNCTIONS = frozenset(
    {
        "malloc",
        "calloc",
        "realloc",
        "free",
        "memcpy",
        "memset",
        "memmove",
        "memcmp",
        "strcpy",
        "strncpy",
        "strlen",
        "strcmp",
        "strncmp",
        "printf",
        "sprintf",
        "snprintf",
        "rand",
        "srand",
        "time",
    }
)

POINTER_TARGET_MARKER = "ectt:stub-via:function-pointer"


class UnknownStubReferenceError(GenError):
    """Raised when a plan names a function that is not an external reference."""

    def __init__(self, message: str, *, reason: str = "unknown_stub_reference") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class StubPlan:
    """What gets stubbed, what links the real implementation, and why."""

    references: tuple[str, ...]
    stubs: tuple[str, ...]
    link_real: tuple[str, ...]
    stdlib_stubbed: tuple[str, ...]
    pointer_targets: tuple[str, ...]
    pointer_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "link_real": list(self.link_real),
            "pointer_paths": {name: self.pointer_paths[name] for name in sorted(self.pointer_paths)},
            "pointer_targets": list(self.pointer_targets),
            "references": list(self.references),
            "stdlib_stubbed": list(self.stdlib_stubbed),
            "stubs": list(self.stubs),
        }


def build_stub_plan(
    references: tuple[str, ...],
    *,
    exclude: tuple[str, ...] = (),
    stdlib: tuple[str, ...] = (),
    pointer_targets: tuple[str, ...] = (),
    pointer_paths: dict[str, str] | None = None,
) -> StubPlan:
    """Build the stub plan for the external reference set.

    - ``exclude``: functions to leave real (STB-080) — must be references.
    - ``stdlib``: standard-library functions to stub on explicit request
      (STB-100) — must be references and inside the documented vocabulary.
    - ``pointer_targets``: functions reached through function pointers
      (STB-140) — must be references; ``pointer_paths`` records the access
      path (e.g. ``cb_table.dispatch``) per target.
    """
    known = set(references)
    for name in exclude:
        if name not in known:
            raise UnknownStubReferenceError(
                f"cannot exclude '{name}': it is not an external reference"
            )
    for name in stdlib:
        if name not in known:
            raise UnknownStubReferenceError(
                f"cannot stub stdlib '{name}': it is not an external reference"
            )
        if name not in STDLIB_FUNCTIONS:
            raise UnknownStubReferenceError(
                f"'{name}' is outside the documented standard-library vocabulary"
            )
    for name in pointer_targets:
        if name not in known:
            raise UnknownStubReferenceError(
                f"cannot stub pointer target '{name}': it is not an external reference"
            )
    excluded = set(exclude)
    stdlib_set = set(stdlib)
    pointers = set(pointer_targets)
    # Precedence: an excluded name is never stubbed, by any mechanism.
    # Standard-library names are stubbed only when explicitly requested
    # (TOOL-STB-100); every other reference is stubbed by default.
    stub_list = tuple(
        sorted(
            name
            for name in dict.fromkeys(references)
            if name not in excluded
            and (name not in STDLIB_FUNCTIONS or name in stdlib_set)
        )
    )
    link_real = tuple(sorted(excluded))
    return StubPlan(
        references=tuple(sorted(dict.fromkeys(references))),
        stubs=stub_list,
        link_real=link_real,
        stdlib_stubbed=tuple(sorted(stdlib_set - excluded)),
        pointer_targets=tuple(sorted(pointers - excluded)),
        pointer_paths=dict(pointer_paths or {}),
    )

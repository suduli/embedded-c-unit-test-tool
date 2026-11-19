"""Suite splitting and on-target footprint documentation (WP-EXT-06).

When a suite exceeds a declared target memory budget, the planner splits it
into greedy first-fit chunks — every test exactly once, minimal chunks under
first-fit, deterministic order — for multiple target executions. The
on-target harness overhead per configuration is documented in a frozen table
stating its measurement basis.

Satisfies: TOOL-TGT-100, TOOL-TGT-110.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from ectt.ext.errors import ExtError

__all__ = [
    "OVERHEAD_BASIS",
    "ChunkTooLargeError",
    "SuiteChunk",
    "SuiteSplit",
    "OverheadEntry",
    "OverheadTable",
    "UnknownConfigurationError",
    "split_suite",
    "overhead_table",
    "OVERHEAD_ENTRIES",
]


class ChunkTooLargeError(ExtError):
    """Raised when one test exceeds the entire target memory budget."""

    def __init__(self, message: str, *, reason: str = "chunk_too_large") -> None:
        super().__init__(message, reason=reason)


class UnknownConfigurationError(ExtError):
    """Raised when a configuration is absent from the overhead table."""

    def __init__(self, message: str, *, reason: str = "unknown_configuration") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class SuiteChunk:
    """One target execution chunk."""

    index: int
    tests: tuple[str, ...]
    total_cost: int

    def to_dict(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {"index": self.index, "tests": list(self.tests), "total_cost": self.total_cost}


@dataclass(frozen=True)
class SuiteSplit:
    """The split plan: one chunk per target execution."""

    budget: int
    chunks: tuple[SuiteChunk, ...]

    @property
    def split_needed(self) -> bool:
        """Whether more than one target execution is needed."""
        return len(self.chunks) > 1

    def to_dict(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "budget": self.budget,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }


def split_suite(
    test_costs: dict[str, int],
    budget: int,
) -> SuiteSplit:
    """Split the suite into first-fit chunks within the memory budget.

    Tests are filled greedily in sorted-name order; every test appears in
    exactly one chunk; a fitting suite is a single chunk; a test larger than
    the whole budget is a named error.
    """
    if budget <= 0:
        raise ChunkTooLargeError("the target memory budget must be positive")
    chunks: list[SuiteChunk] = []
    current: list[str] = []
    current_cost = 0
    for name in sorted(test_costs):
        cost = test_costs[name]
        if cost > budget:
            raise ChunkTooLargeError(
                f"test '{name}' costs {cost}, exceeding the entire target "
                f"memory budget {budget}"
            )
        if current_cost + cost > budget and current:
            chunks.append(SuiteChunk(index=len(chunks), tests=tuple(current), total_cost=current_cost))
            current = []
            current_cost = 0
        current.append(name)
        current_cost += cost
    if current:
        chunks.append(SuiteChunk(index=len(chunks), tests=tuple(current), total_cost=current_cost))
    return SuiteSplit(budget=budget, chunks=tuple(chunks))


# The on-target harness overhead per configuration. These are analytical
# estimates from the harness design (hook block + dispatch + chunk metadata),
# NOT measured values: the basis is stated so no document claims more.
OVERHEAD_BASIS: Final[str] = (
    "analytical estimates from the harness design (setup/teardown hooks, "
    "dispatch entry points, chunk metadata); pending on-target measurement, "
    "not executed evidence"
)

_OVERHEAD_ROWS: Final[tuple[tuple[str, int, int, int], ...]] = (
    ("qemu-mps2-an385", 256, 1024, 128),
    ("stm32f407vg-openocd", 192, 768, 96),
    ("stm32f411re-pyocd", 192, 768, 96),
)


@dataclass(frozen=True)
class OverheadEntry:
    """The documented overhead of one target configuration."""

    configuration: str
    ram_bytes: int
    flash_bytes: int
    stack_bytes: int
    basis: str = OVERHEAD_BASIS

    def to_dict(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "basis": self.basis,
            "configuration": self.configuration,
            "flash_bytes": self.flash_bytes,
            "ram_bytes": self.ram_bytes,
            "stack_bytes": self.stack_bytes,
        }


@dataclass(frozen=True)
class OverheadTable:
    """The frozen per-configuration overhead table (TOOL-TGT-110)."""

    entries: tuple[OverheadEntry, ...]
    basis: str = OVERHEAD_BASIS

    def lookup(self, configuration: str) -> OverheadEntry:
        """The overhead documented for one configuration."""
        for entry in self.entries:
            if entry.configuration == configuration:
                return entry
        raise UnknownConfigurationError(
            f"no overhead is documented for configuration '{configuration}'; "
            f"documented: {', '.join(e.configuration for e in self.entries)}"
        )

    def to_dict(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "basis": self.basis,
            "entries": [
                entry.to_dict()
                for entry in sorted(self.entries, key=lambda e: e.configuration)
            ],
        }


OVERHEAD_ENTRIES: Final[tuple[OverheadEntry, ...]] = tuple(
    OverheadEntry(configuration=name, ram_bytes=ram, flash_bytes=flash, stack_bytes=stack)
    for name, ram, flash, stack in _OVERHEAD_ROWS
)


def overhead_table() -> OverheadTable:
    """The current overhead table. Deterministic on every call."""
    return OverheadTable(entries=OVERHEAD_ENTRIES)

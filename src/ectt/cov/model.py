# implements: TOOL-COV-010, TOOL-COV-020
"""Coverage model for the GCC gcov backend (CMP-COV).

The model mirrors the documented GCC gcov JSON format (GCC 14.4, "Invoking Gcov →
GCOV JSON Format") restricted to the statement and branch/decision scope of
TOOL-COV-010/TOOL-COV-020. `functions[]` records belong to WP-COV-04 and are not
modelled here.

Satisfies: TOOL-COV-010, TOOL-COV-020.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from ectt.core.determinism import canonical_json_bytes

__all__ = [
    "SCHEMA_VERSION_CURRENT",
    "GcovBranch",
    "GcovCondition",
    "GcovLine",
    "GcovFile",
    "GcovDocument",
    "MetricTotals",
]

#: Version of the ectt coverage-model exchange document this module emits.
SCHEMA_VERSION_CURRENT: str = "1.0"


@dataclass(frozen=True)
class GcovCondition:
    """One condition outcome record on an instrumented line (GCC 14+).

    ``count`` is the number of condition outcomes in the expression, ``covered``
    the number of covered outcomes, and ``not_covered_true`` / ``not_covered_false``
    the term indices (0-based) not seen as true / false. The MC/DC interpretation
    of these outcomes is out of WP-COV-01 scope.
    """

    count: int
    covered: int
    not_covered_true: tuple[int, ...] = ()
    not_covered_false: tuple[int, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "covered": self.covered,
            "not_covered_true": list(self.not_covered_true),
            "not_covered_false": list(self.not_covered_false),
        }


@dataclass(frozen=True)
class GcovBranch:
    """One decision branch taken from an instrumented line (gcov ``-b``)."""

    count: int
    fallthrough: bool | None = None
    throw: bool | None = None
    source_block_id: int | None = None
    destination_block_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {"count": self.count}
        if self.fallthrough is not None:
            res["fallthrough"] = self.fallthrough
        if self.throw is not None:
            res["throw"] = self.throw
        if self.source_block_id is not None:
            res["source_block_id"] = self.source_block_id
        if self.destination_block_id is not None:
            res["destination_block_id"] = self.destination_block_id
        return res


@dataclass(frozen=True)
class GcovLine:
    """One instrumented statement line with its branches and condition outcomes."""

    line_number: int
    count: int
    unexecuted_block: bool = False
    function_name: str | None = None
    branches: tuple[GcovBranch, ...] = ()
    conditions: tuple[GcovCondition, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "line_number": self.line_number,
            "count": self.count,
            "unexecuted_block": self.unexecuted_block,
        }
        if self.function_name is not None:
            res["function_name"] = self.function_name
        if self.branches:
            res["branches"] = [b.to_dict() for b in self.branches]
        if self.conditions:
            res["conditions"] = [c.to_dict() for c in self.conditions]
        return res


@dataclass(frozen=True)
class GcovFile:
    """Per-source-file coverage: the instrumented statement lines in line order."""

    file: str
    lines: tuple[GcovLine, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "lines": [line.to_dict() for line in self.lines],
        }


@dataclass(frozen=True)
class GcovDocument:
    """A parsed gcov JSON document (statement and branch scope)."""

    format_version: str
    gcc_version: str
    data_file: str
    files: tuple[GcovFile, ...] = ()
    current_working_directory: str | None = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION_CURRENT,
            "format_version": self.format_version,
            "gcc_version": self.gcc_version,
            "data_file": self.data_file,
            "files": [f.to_dict() for f in self.files],
        }
        if self.current_working_directory is not None:
            res["current_working_directory"] = self.current_working_directory
        return res

    def to_json_bytes(self, *, indent: int | None = 2) -> bytes:
        """Return UTF-8 canonical JSON bytes with ``schema_version`` first."""
        return canonical_json_bytes(self.to_dict(), indent=indent, first_keys=("schema_version",))


@dataclass(frozen=True)
class MetricTotals:
    """Exact covered/total fraction for one metric; ``None`` total = not applicable."""

    covered: int
    total: int | None

    def to_dict(self) -> dict[str, Any]:
        return {"covered": self.covered, "total": self.total}

    def fraction(self) -> Fraction | None:
        """Exact covered/total fraction, or ``None`` when not applicable."""
        if self.total is None or self.total == 0:
            return None
        return Fraction(self.covered, self.total)

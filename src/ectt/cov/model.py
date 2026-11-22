# implements: TOOL-COV-010, TOOL-COV-020, TOOL-COV-030, TOOL-COV-040
"""Coverage model for the GCC gcov backend (CMP-COV).

The model mirrors the documented GCC gcov JSON format (GCC 14.4, "Invoking Gcov →
GCOV JSON Format"): statement and branch/decision scope (TOOL-COV-010/020,
WP-COV-01) plus function and function-call records (TOOL-COV-030/040, WP-COV-04).

Satisfies: TOOL-COV-010, TOOL-COV-020, TOOL-COV-030, TOOL-COV-040.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from ectt.core.determinism import canonical_json_bytes

__all__ = [
    "SCHEMA_VERSION_CURRENT",
    "GcovBranch",
    "GcovCall",
    "GcovCondition",
    "GcovFunction",
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
class GcovCall:
    """One call site on an instrumented line (gcov format version 2+).

    ``returned`` is the number of times the call returned (the call count equals
    the line's ``count``); a call is covered iff ``returned > 0`` (TOOL-COV-040).
    """

    returned: int
    source_block_id: int | None = None
    destination_block_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {"returned": self.returned}
        if self.source_block_id is not None:
            res["source_block_id"] = self.source_block_id
        if self.destination_block_id is not None:
            res["destination_block_id"] = self.destination_block_id
        return res


@dataclass(frozen=True)
class GcovFunction:
    """One function record of a file (documented gcov function form, TOOL-COV-030).

    ``blocks`` is the static number of basic blocks in the function,
    ``blocks_executed`` the number executed in this run, ``execution_count`` the
    number of executions of the function. Line and column numbers are 1-based.
    """

    name: str
    start_line: int
    end_line: int
    execution_count: int
    blocks: int | None = None
    blocks_executed: int | None = None
    demangled_name: str | None = None
    start_column: int | None = None
    end_column: int | None = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "execution_count": self.execution_count,
        }
        if self.blocks is not None:
            res["blocks"] = self.blocks
        if self.blocks_executed is not None:
            res["blocks_executed"] = self.blocks_executed
        if self.demangled_name is not None:
            res["demangled_name"] = self.demangled_name
        if self.start_column is not None:
            res["start_column"] = self.start_column
        if self.end_column is not None:
            res["end_column"] = self.end_column
        return res


@dataclass(frozen=True)
class GcovLine:
    """One instrumented statement line with its branches, conditions, and calls."""

    line_number: int
    count: int
    unexecuted_block: bool = False
    function_name: str | None = None
    branches: tuple[GcovBranch, ...] = ()
    conditions: tuple[GcovCondition, ...] = ()
    calls: tuple[GcovCall, ...] = ()

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
        if self.calls:
            res["calls"] = [c.to_dict() for c in self.calls]
        return res


@dataclass(frozen=True)
class GcovFile:
    """Per-source-file coverage: functions and instrumented statement lines."""

    file: str
    functions: tuple[GcovFunction, ...] = ()
    lines: tuple[GcovLine, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {"file": self.file}
        if self.functions:
            res["functions"] = [f.to_dict() for f in self.functions]
        res["lines"] = [line.to_dict() for line in self.lines]
        return res


@dataclass(frozen=True)
class GcovDocument:
    """A parsed gcov JSON document (statement, branch, function and call scope)."""

    format_version: str
    gcc_version: str
    #: Name of the data file (GCDA). For a MERGED document: the sorted,
    #: comma-joined data files of every contributing document, so the merged
    #: provenance is a pure function of the run set, never of the input order.
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

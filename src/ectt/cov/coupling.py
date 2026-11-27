# implements: TOOL-COV-170
"""Control coupling and data coupling between integrated units (WP-COV-11).

Control coupling: for every call from one analysed function to another, the
call graph of the analysis model (``FunctionModel.calls``) supplies the caller,
the callee and the call site's line; the gcov data says whether the call was
exercised. Data coupling: for every global variable the analysis model's
inventory records (``AnalysisUnit.global_variables``, schema 1.5), the
functions that write it and the functions that read it
(``FunctionModel.globals``) form the pairs, and the gcov data says whether
both sides executed.

This module reports data only. It computes no score and states no verdict
about any standard's coupling objective.

Every pair carries exactly one status:

- ``exercised`` — a call pair: at least one of its call sites returned; a data
  pair: the writer and the reader function both executed.
- ``not_exercised`` — a call pair: every call site is in the coverage data and
  none returned; a data pair: both functions are in the coverage data and at
  least one did not execute.
- ``not_determinable`` — the data cannot decide, with the reason named.

Two limits are deliberate and are stated in the output rather than papered
over. A call site is matched to a gcov call record only when its line holds
exactly one model call site and exactly one gcov call record, because neither
side carries a callee identity for the record; any other shape is
``not_determinable``. For a data pair, "exercised" means the two *functions*
executed at least once: the model records global accesses by name, without a
line, so this does not show that the specific access statement executed.

Satisfies: TOOL-COV-170.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from ectt.ana.model import (
    CALL_CLASSIFICATIONS,
    CALL_VIA,
    AnalysisModel,
    AnalysisUnit,
    CallModel,
    FunctionModel,
)
from ectt.core.determinism import canonical_json_bytes
from ectt.cov.errors import CoverageError
from ectt.cov.model import GcovDocument, GcovFile, GcovLine

__all__ = [
    "COUPLING_SCHEMA_VERSION",
    "COUPLING_STATUSES",
    "DATA_PAIR_BASIS",
    "CallPair",
    "CallSite",
    "CouplingReport",
    "CouplingVariable",
    "DataPair",
    "analyze_coupling",
]

COUPLING_SCHEMA_VERSION = "1.0"

#: The status of every reported pair.
COUPLING_STATUSES: tuple[str, ...] = ("exercised", "not_exercised", "not_determinable")

_EXERCISED = "exercised"
_NOT_EXERCISED = "not_exercised"
_NOT_DETERMINABLE = "not_determinable"
_PARSED = "parsed"

_INTERNAL = "internal"
_STATIC = "static"
_EXTERNAL = "external"
_EXTERN = "extern"
_POINTER = "function_pointer"

#: What ``exercised`` means for a data pair (the model has no access lines).
DATA_PAIR_BASIS = "function_executed"


@dataclass(frozen=True)
class CallSite:
    """One call site's standing."""

    line: int
    status: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"line": self.line, "reason": self.reason, "status": self.status}


@dataclass(frozen=True)
class CallPair:
    """One caller-to-callee coupling."""

    caller: str
    caller_unit: str
    #: ``None`` when the target is not identified (a call through a pointer).
    callee: str | None
    #: The unit whose inventory of functions defines the callee, when that is unique.
    callee_unit: str | None
    classification: str
    status: str
    reason: str | None
    sites: tuple[CallSite, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "callee": self.callee,
            "callee_unit": self.callee_unit,
            "caller": self.caller,
            "caller_unit": self.caller_unit,
            "classification": self.classification,
            "reason": self.reason,
            "sites": [site.to_dict() for site in self.sites],
            "status": self.status,
        }


@dataclass(frozen=True)
class DataPair:
    """One writer-to-reader coupling through one global variable."""

    variable: str
    writer: str
    writer_unit: str
    reader: str
    reader_unit: str
    status: str
    reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "reader": self.reader,
            "reader_unit": self.reader_unit,
            "reason": self.reason,
            "status": self.status,
            "variable": self.variable,
            "writer": self.writer,
            "writer_unit": self.writer_unit,
        }


@dataclass(frozen=True)
class CouplingVariable:
    """One global variable of the inventory and the functions recorded on it."""

    variable: str
    #: The unit that owns a file-scope variable or defines an external one.
    unit: str | None
    linkage: str  # "internal" (file scope) | "external"
    defined_in_model: bool
    status: str  # "recorded" | "not_determinable"
    reason: str | None
    writers: tuple[tuple[str, str], ...]
    readers: tuple[tuple[str, str], ...]
    pairs: tuple[DataPair, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "defined_in_model": self.defined_in_model,
            "linkage": self.linkage,
            "pairs": [pair.to_dict() for pair in self.pairs],
            "readers": [_function_entry(function, unit) for function, unit in self.readers],
            "reason": self.reason,
            "status": self.status,
            "unit": self.unit,
            "variable": self.variable,
            "writers": [_function_entry(function, unit) for function, unit in self.writers],
        }


@dataclass(frozen=True)
class CouplingReport:
    """Control and data coupling of one analysis model against one coverage document."""

    call_pairs: tuple[CallPair, ...]
    variables: tuple[CouplingVariable, ...]
    analysed_units: tuple[str, ...]
    not_analysed_units: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": COUPLING_SCHEMA_VERSION,
            "units": {
                "analysed": list(self.analysed_units),
                "not_analysed": [dict(entry) for entry in self.not_analysed_units],
            },
            "call_pairs": [pair.to_dict() for pair in self.call_pairs],
            "data_pairs_basis": DATA_PAIR_BASIS,
            "variables": [variable.to_dict() for variable in self.variables],
        }

    def to_json_bytes(self) -> bytes:
        """Return deterministic canonical JSON bytes with ``schema_version`` first."""
        return canonical_json_bytes(self.to_dict(), indent=2, first_keys=("schema_version",))


def analyze_coupling(model: AnalysisModel, document: GcovDocument) -> CouplingReport:
    """Report control and data coupling of ``model`` against the gcov ``document``.

    Only parsed units are analysed; a failed unit is listed as not analysed
    with its recorded reason. The model is read, never changed.

    Refused with a named reason: a call site whose ``via`` or ``classification``
    is outside the analysis vocabulary (``unknown_call_via``,
    ``unknown_call_classification``) and a global access outside ``r``/``w``/
    ``rw`` (``unknown_global_access``).
    """
    parsed = sorted(
        (unit for unit in model.units if unit.status == _PARSED), key=lambda unit: _posix(unit.path)
    )
    not_analysed = tuple(
        {
            "unit": _posix(unit.path),
            "reason": unit.failure.reason if unit.failure is not None else "unit_not_parsed",
        }
        for unit in sorted(
            (unit for unit in model.units if unit.status != _PARSED), key=lambda unit: _posix(unit.path)
        )
    )

    coverage = _Coverage(document)
    # Keyed (function, unit) like every writer and reader tuple below.
    function_files = {
        (function.name, _posix(unit.path)): _posix(function.location.file) or _posix(unit.path)
        for unit in parsed
        for function in unit.functions
    }
    call_pairs = _call_pairs(parsed, coverage)
    variables = _variables(parsed, coverage, function_files)
    return CouplingReport(
        call_pairs=call_pairs,
        variables=variables,
        analysed_units=tuple(_posix(unit.path) for unit in parsed),
        not_analysed_units=not_analysed,
    )


# --- coverage lookups -------------------------------------------------------------------


def _posix(path: str) -> str:
    posix = path.replace("\\", "/")
    while posix.startswith("./"):
        posix = posix[2:]
    return posix


class _Coverage:
    """The gcov document indexed by normalised file name and line."""

    def __init__(self, document: GcovDocument) -> None:
        self.files: dict[str, list[GcovFile]] = {}
        self.lines: dict[tuple[str, int], list[GcovLine]] = {}
        self._execution: dict[tuple[str, str], list[int]] = {}
        for file in document.files:
            name = _posix(file.file)
            self.files.setdefault(name, []).append(file)
            for line in file.lines:
                self.lines.setdefault((name, line.line_number), []).append(line)
            for function in file.functions:
                self._execution.setdefault((name, function.name), []).append(function.execution_count)

    def call_status(self, file: str, line: int, sites_on_line: int) -> tuple[str, str | None]:
        """The standing of the single call site being evaluated at ``file:line``."""
        if len(self.files.get(file, [])) != 1:
            return _NOT_DETERMINABLE, "file_not_in_coverage" if file not in self.files else "ambiguous_file"
        records = self.lines.get((file, line), [])
        if not records:
            return _NOT_DETERMINABLE, "call_line_not_in_coverage"
        calls = [call for record in records for call in record.calls]
        if not calls:
            return _NOT_DETERMINABLE, "no_call_data"
        if sites_on_line != 1 or len(records) != 1 or len(calls) != 1:
            # Neither side names the callee of a call record, so a positional
            # match between several calls is not a determination.
            return _NOT_DETERMINABLE, "ambiguous_call_site"
        returned = calls[0].returned
        if returned > 0:
            return _EXERCISED, None
        return _NOT_EXERCISED, "call_site_not_reached" if records[0].count == 0 else "call_never_returned"

    def execution_of(self, file: str, function: str) -> tuple[int | None, str | None]:
        """The function's execution count, or ``None`` with the reason it is not determinable."""
        counts = self._execution.get((file, function), [])
        if not counts:
            return None, "function_not_in_coverage"
        if len(counts) > 1:
            return None, "ambiguous_function_name"
        return counts[0], None


# --- control coupling -------------------------------------------------------------------


@dataclass(frozen=True)
class _Site:
    unit: str
    file: str
    function: str
    call: CallModel

    @property
    def sort_key(self) -> tuple[Any, ...]:
        return (self.unit, self.function, self.call.line, self.call.callee, self.call.via)


def _call_pairs(parsed: Sequence[AnalysisUnit], coverage: _Coverage) -> tuple[CallPair, ...]:
    sites: list[_Site] = []
    sites_on_line: dict[tuple[str, int], int] = {}
    for unit in parsed:
        unit_path = _posix(unit.path)
        for function in unit.functions:
            _checked_calls(function, unit_path)
            for call in function.calls:
                site = _Site(unit_path, _posix(function.location.file) or unit_path, function.name, call)
                _check_call(call, site)
                sites.append(site)
                key = (site.file, call.line)
                sites_on_line[key] = sites_on_line.get(key, 0) + 1

    defining_units: dict[str, set[str]] = {}
    for unit in parsed:
        for function in unit.functions:
            defining_units.setdefault(function.name, set()).add(_posix(unit.path))

    grouped: dict[tuple[str, str, str, str], list[_Site]] = {}
    for site in sites:
        grouped.setdefault((site.unit, site.function, site.call.callee, site.call.classification), []).append(site)

    pairs: list[CallPair] = []
    for (caller_unit, caller, callee, classification), members in grouped.items():
        members.sort(key=lambda site: site.sort_key)
        call_sites: list[CallSite] = []
        for site in members:
            status, reason = (
                (_NOT_DETERMINABLE, "callee_not_identified")
                if site.call.via == _POINTER
                else coverage.call_status(site.file, site.call.line, sites_on_line[(site.file, site.call.line)])
            )
            call_sites.append(CallSite(line=site.call.line, status=status, reason=reason))
        status, reason = _combine(call_sites)
        if classification == _INTERNAL:
            callee_unit: str | None = caller_unit
        else:
            candidates = sorted(defining_units.get(callee, ()))
            callee_unit = candidates[0] if len(candidates) == 1 else None
        pairs.append(
            CallPair(
                caller=caller,
                caller_unit=caller_unit,
                callee=callee or None,
                callee_unit=callee_unit,
                classification=classification,
                status=status,
                reason=reason,
                sites=tuple(call_sites),
            )
        )
    pairs.sort(key=lambda pair: (pair.caller_unit, pair.caller, pair.callee or "", pair.classification))
    return tuple(pairs)


def _checked_calls(function: FunctionModel, unit_path: str) -> None:
    for call in function.calls:
        if call.via not in CALL_VIA:
            raise CoverageError(
                f"call site at line {call.line} of '{function.name}' in '{unit_path}' has via {call.via!r} "
                f"outside the analysis vocabulary {CALL_VIA}",
                reason="unknown_call_via",
            )
        if call.classification not in CALL_CLASSIFICATIONS:
            raise CoverageError(
                f"call site at line {call.line} of '{function.name}' in '{unit_path}' has classification "
                f"{call.classification!r} outside the analysis vocabulary {CALL_CLASSIFICATIONS}",
                reason="unknown_call_classification",
            )


def _combine(sites: Sequence[CallSite]) -> tuple[str, str | None]:
    """Fold call sites into one pair status; a site that cannot be decided is never read as exercised."""
    if any(site.status == _EXERCISED for site in sites):
        return _EXERCISED, None
    reasons = _distinct(site.reason for site in sites)
    if all(site.status == _NOT_EXERCISED for site in sites):
        return _NOT_EXERCISED, "; ".join(reasons) or None
    return _NOT_DETERMINABLE, "; ".join(
        _distinct(site.reason for site in sites if site.status == _NOT_DETERMINABLE)
    )


# --- data coupling ----------------------------------------------------------------------


@dataclass
class _Variable:
    name: str
    linkage: str
    unit: str | None
    defined_in_model: bool
    writers: dict[tuple[str, str], None]
    readers: dict[tuple[str, str], None]

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return (self.name, self.linkage, self.unit or "")


def _variables(
    parsed: Sequence[AnalysisUnit],
    coverage: _Coverage,
    function_files: Mapping[tuple[str, str], str],
) -> tuple[CouplingVariable, ...]:
    variables: dict[tuple[str, str, str], _Variable] = {}
    for unit in parsed:
        unit_path = _posix(unit.path)
        for record in unit.global_variables:
            if record.storage_class == _STATIC:
                variables.setdefault(
                    ("static", unit_path, record.name),
                    _Variable(record.name, _INTERNAL, unit_path, True, {}, {}),
                )
            else:
                key = ("external", "", record.name)
                existing = variables.get(key)
                if existing is None:
                    variables[key] = _Variable(
                        record.name,
                        _EXTERNAL,
                        None if record.storage_class == _EXTERN else unit_path,
                        record.storage_class != _EXTERN,
                        {},
                        {},
                    )
                elif existing.unit is None and record.storage_class != _EXTERN:
                    # The defining unit, in sorted unit order; an extern-only entry names none.
                    existing.unit = unit_path
                    existing.defined_in_model = True

    for unit in parsed:
        unit_path = _posix(unit.path)
        file_static = {record.name for record in unit.global_variables if record.storage_class == _STATIC}
        for function in unit.functions:
            for access in function.globals:
                if access.access not in ("r", "w", "rw"):
                    raise CoverageError(
                        f"access of '{access.name}' in '{function.name}' in '{unit_path}' is {access.access!r}, "
                        "not one of r, w, rw",
                        reason="unknown_global_access",
                    )
                # An access in this unit to a name it declares file-static is to
                # that unit's own variable; anything else has external linkage.
                key = (
                    ("static", unit_path, access.name)
                    if access.name in file_static
                    else ("external", "", access.name)
                )
                variable = variables.get(key)
                if variable is None:
                    # Accessed, but defined in no analysed unit's inventory.
                    variable = _Variable(access.name, _EXTERNAL, None, False, {}, {})
                    variables[key] = variable
                if access.access in ("w", "rw"):
                    variable.writers[(function.name, unit_path)] = None
                if access.access in ("r", "rw"):
                    variable.readers[(function.name, unit_path)] = None

    report: list[CouplingVariable] = []
    for variable in sorted(variables.values(), key=lambda item: item.sort_key):
        writers = tuple(sorted(variable.writers))
        readers = tuple(sorted(variable.readers))
        if not writers and not readers:
            report.append(
                CouplingVariable(
                    variable=variable.name,
                    unit=variable.unit,
                    linkage=variable.linkage,
                    defined_in_model=variable.defined_in_model,
                    status=_NOT_DETERMINABLE,
                    reason="no_recorded_access",
                    writers=(),
                    readers=(),
                    pairs=(),
                )
            )
            continue
        pairs = tuple(
            _data_pair(variable.name, writer, reader, coverage, function_files)
            for writer in writers
            for reader in readers
            if writer != reader
        )
        report.append(
            CouplingVariable(
                variable=variable.name,
                unit=variable.unit,
                linkage=variable.linkage,
                defined_in_model=variable.defined_in_model,
                status="recorded",
                reason=None,
                writers=writers,
                readers=readers,
                pairs=pairs,
            )
        )
    return tuple(report)


def _data_pair(
    variable: str,
    writer: tuple[str, str],
    reader: tuple[str, str],
    coverage: _Coverage,
    function_files: Mapping[tuple[str, str], str],
) -> DataPair:
    writer_name, writer_unit = writer
    reader_name, reader_unit = reader
    writer_count, writer_reason = coverage.execution_of(function_files[writer], writer_name)
    reader_count, reader_reason = coverage.execution_of(function_files[reader], reader_name)

    undetermined = [
        f"{which}: {reason}"
        for which, reason in (("writer", writer_reason), ("reader", reader_reason))
        if reason is not None
    ]
    pair = DataPair(
        variable=variable,
        writer=writer_name,
        writer_unit=writer_unit,
        reader=reader_name,
        reader_unit=reader_unit,
        status=_NOT_DETERMINABLE,
        reason="; ".join(undetermined),
    )
    if undetermined:
        return pair
    assert writer_count is not None and reader_count is not None
    if writer_count > 0 and reader_count > 0:
        return replace(pair, status=_EXERCISED, reason=None)
    not_executed = [which for which, count in (("writer", writer_count), ("reader", reader_count)) if count == 0]
    return replace(
        pair,
        status=_NOT_EXERCISED,
        reason="_and_".join(f"{which}_not_executed" for which in not_executed),
    )


# --- helpers ----------------------------------------------------------------------------


def _check_call(call: CallModel, site: _Site) -> None:
    if call.via == _POINTER and call.callee:
        raise CoverageError(
            f"call site at line {call.line} of '{site.function}' in '{site.unit}' is a call through a "
            f"pointer but names callee {call.callee!r}; an indirect target is never guessed",
            reason="indirect_call_names_callee",
        )


def _distinct(reasons: Iterable[str | None]) -> list[str]:
    seen: list[str] = []
    for reason in reasons:
        if reason is not None and reason not in seen:
            seen.append(reason)
    return seen


def _function_entry(function: str, unit: str) -> dict[str, str]:
    return {"function": function, "unit": unit}

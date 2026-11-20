# implements: TOOL-MIG-050
"""Column-mapped CSV / delimited plain-text test data import (WP-MIG-04).

TOOL-MIG-050: import test cases from a documented CSV interchange format,
permitting migration via spreadsheet from any source. TOOL-MIG-030: import test
case data from commercial tools that offer a documented or plain-text export,
converting inputs, expected values and stub configuration.

The importer is source-neutral: the caller states, as data, which column of the
source export carries which part of the ectt case model (a *column mapping*).
Comma, semicolon, tab and pipe delimited text are supported, which covers
spreadsheet exports and plain-text tool exports that are tabular. Format
specific adapters for individual commercial tools need their documented export
samples and are recorded as follow-up work.

Mapping targets (right-hand side of the mapping):

``id``, ``unit``, ``function``, ``requirements`` (``;``-separated), ``suites``
(``;``-separated), ``expect_return``, ``input:<name>``, ``global_init:<name>``,
``expect_global:<name>``, ``expect_out:<name>``, ``stub:<fn>:mode``,
``stub:<fn>:returns`` (``;``-separated), ``stub:<fn>:expect_calls`` and
``stub:<fn>:out:<name>``.

Never silent: every source row ends as *converted* or *rejected* with a reason
and its row number, and every source column that is not mapped is listed.
Identifiers are never invented (D-02: a case keeps the id its author gave it);
a row without one is rejected. Cell text is stored as written, never evaluated.
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ectt.mig.errors import MigError
from ectt.tcm.datacases import (
    DataDrivenTestCase,
    StubSpec,
    TestCaseExpected,
    TestCaseInputs,
    TestCaseOrigin,
    refresh_digest,
)

__all__ = [
    "DELIMITERS",
    "MappedCsvImport",
    "RowOutcome",
    "import_mapped_csv",
    "validate_mapping",
]

DELIMITERS: tuple[str, ...] = (",", ";", "\t", "|")

_SIMPLE_TARGETS = frozenset({"id", "unit", "function", "requirements", "suites", "expect_return"})
_NAMED_TARGET = re.compile(r"^(input|global_init|expect_global|expect_out):(\S+)$")
_STUB_TARGET = re.compile(r"^stub:([^:\s]+):(mode|returns|expect_calls|out:\S+)$")
_EXPECT_CALLS = re.compile(r"^\d+$")


@dataclass(frozen=True)
class RowOutcome:
    """What happened to one source row (1-based data-row number)."""

    row: int
    status: str  # "converted" | "rejected"
    case_id: str | None
    reason: str | None = None
    detail: str | None = None


@dataclass(frozen=True)
class MappedCsvImport:
    """Imported cases plus a complete account of every row and column."""

    cases: tuple[DataDrivenTestCase, ...]
    rows: tuple[RowOutcome, ...]
    unmapped_columns: tuple[str, ...]

    @property
    def rejected(self) -> tuple[RowOutcome, ...]:
        return tuple(r for r in self.rows if r.status == "rejected")


def validate_mapping(mapping: Mapping[str, str]) -> None:
    """Refuse a mapping whose targets are not part of the documented set."""
    if not mapping:
        raise MigError("column mapping is empty", reason="empty_mapping")
    targets = list(mapping.values())
    for column, target in mapping.items():
        if not (
            target in _SIMPLE_TARGETS or _NAMED_TARGET.match(target) or _STUB_TARGET.match(target)
        ):
            raise MigError(
                f"column '{column}' maps to unknown target '{target}'",
                reason="unknown_target",
            )
    if len(set(targets)) != len(targets):
        raise MigError("two columns map to the same target", reason="duplicate_target")
    required = {"id", "unit", "function"}
    missing = sorted(required - set(targets))
    if missing:
        raise MigError(f"mapping lacks required target(s): {', '.join(missing)}", reason="missing_required_target")


def _split(text: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in text.split(";") if part.strip())


def _build_case(cells: Mapping[str, str]) -> DataDrivenTestCase:
    """Assemble one case from ``target -> non-empty text``; raises ``ValueError(reason, detail)``."""
    for required in ("id", "unit", "function"):
        if required not in cells:
            raise ValueError(f"missing_{required}", f"row has no value for '{required}'")

    parameters: dict[str, str] = {}
    global_inits: dict[str, str] = {}
    global_finals: dict[str, str] = {}
    out_parameters: dict[str, str] = {}
    stubs: dict[str, dict[str, Any]] = {}
    for target, value in cells.items():
        named = _NAMED_TARGET.match(target)
        if named:
            kind, name = named.groups()
            {
                "input": parameters,
                "global_init": global_inits,
                "expect_global": global_finals,
                "expect_out": out_parameters,
            }[kind][name] = value
            continue
        stub = _STUB_TARGET.match(target)
        if stub:
            fn, part = stub.groups()
            entry = stubs.setdefault(fn, {"out_parameters": {}})
            if part == "mode":
                entry["mode"] = value
            elif part == "returns":
                entry["returns"] = _split(value)
            elif part == "expect_calls":
                if not _EXPECT_CALLS.match(value):
                    raise ValueError("invalid_expect_calls", f"stub '{fn}' expect_calls '{value}' is not a non-negative integer")
                entry["expect_calls"] = value
            else:
                entry["out_parameters"][part[len("out:") :]] = value

    stub_specs: list[StubSpec] = []
    for fn in sorted(stubs):
        entry = stubs[fn]
        if "mode" not in entry:
            raise ValueError("stub_mode_missing", f"stub '{fn}' has values but no mode; a mode is never assumed")
        stub_specs.append(
            StubSpec(
                name=fn,
                mode=entry["mode"],
                returns=entry.get("returns", ()),
                expect_calls=entry.get("expect_calls"),
                out_parameters=entry["out_parameters"],
            )
        )

    case = DataDrivenTestCase(
        case_id=cells["id"],
        unit=cells["unit"],
        function=cells["function"],
        inputs=TestCaseInputs(parameters=parameters, global_inits=global_inits),
        expected=TestCaseExpected(
            return_value=cells.get("expect_return"),
            global_finals=global_finals,
            out_parameters=out_parameters,
        ),
        stubs=tuple(stub_specs),
        origin=TestCaseOrigin(author="human"),
        requirements=_split(cells.get("requirements", "")),
        suites=_split(cells.get("suites", "")),
    )
    return refresh_digest(case)


def import_mapped_csv(
    text: str,
    mapping: Mapping[str, str],
    *,
    delimiter: str = ",",
) -> MappedCsvImport:
    """Import ``text`` into data-driven cases according to ``mapping``.

    ``mapping`` is ``source column header -> target`` (see the module
    docstring). Raises :class:`MigError` for unusable input as a whole (empty
    text, unknown delimiter or mapping target, a mapped column that is absent,
    duplicate headers); individual bad rows are rejected and reported instead.
    """
    if delimiter not in DELIMITERS:
        raise MigError(f"unsupported delimiter {delimiter!r}", reason="unsupported_delimiter")
    validate_mapping(mapping)
    body = text.lstrip("﻿")
    if not body.strip():
        raise MigError("import text is empty", reason="empty_input")

    reader = csv.reader(io.StringIO(body, newline=""), delimiter=delimiter)
    try:
        header = next(reader)
        records = list(reader)
    except csv.Error as exc:
        raise MigError(f"import text is not valid delimited text: {exc}", reason="malformed_input") from exc
    header = [h.strip() for h in header]
    if len(set(header)) != len(header):
        raise MigError("header contains duplicate column names", reason="duplicate_column")
    missing = sorted(set(mapping) - set(header))
    if missing:
        raise MigError(f"mapped column(s) not in the header: {', '.join(missing)}", reason="unknown_column")

    index = {name: i for i, name in enumerate(header)}
    unmapped = tuple(sorted(name for name in header if name not in mapping))

    cases: list[DataDrivenTestCase] = []
    outcomes: list[RowOutcome] = []
    seen_ids: dict[str, int] = {}
    for number, record in enumerate((r for r in records if any(c.strip() for c in r)), start=1):
        if len(record) != len(header):
            outcomes.append(
                RowOutcome(number, "rejected", None, "ragged_row", f"expected {len(header)} cells, found {len(record)}")
            )
            continue
        cells = {
            target: record[index[column]].strip()
            for column, target in mapping.items()
            if record[index[column]].strip()
        }
        try:
            case = _build_case(cells)
        except ValueError as exc:
            reason, detail = exc.args
            outcomes.append(RowOutcome(number, "rejected", cells.get("id"), reason, detail))
            continue
        if case.case_id in seen_ids:
            outcomes.append(
                RowOutcome(
                    number,
                    "rejected",
                    case.case_id,
                    "duplicate_id",
                    f"id already used by row {seen_ids[case.case_id]}",
                )
            )
            continue
        seen_ids[case.case_id] = number
        cases.append(case)
        outcomes.append(RowOutcome(number, "converted", case.case_id))

    return MappedCsvImport(
        cases=tuple(sorted(cases, key=lambda c: c.case_id)),
        rows=tuple(outcomes),
        unmapped_columns=unmapped,
    )

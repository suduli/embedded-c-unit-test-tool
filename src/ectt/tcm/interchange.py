# implements: DSN-TCM-070
"""Test case interchange import and export (WP-TCM-06).

A documented CSV-class interchange (TOOL-TCD-100, DSN-TCM-070): the export
path against lock-in and the spreadsheet-based migration path in. The
round-trip contract (SDD-002 §5.1) is "a lossless projection of this model,
or it reports the loss": whatever the format cannot express is reported per
case, never silently dropped. The case digest travels as a column (D-02
option a); import reports rows whose recorded digest no longer matches
their content.

The schema is the fixed column set with ``ectt_interchange_version`` first;
list-valued fields are ``;``-joined and mapping-valued fields are canonical
JSON cells. Import validates the column set strictly.

Satisfies: TOOL-TCD-100; DSN-TCM-070; SDD-002 §5.1 (round trip).
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from ectt.core.determinism import canonical_json
from ectt.tcm.datacases import (
    DataDrivenTestCase,
    StubSpec,
    TestCaseExpected,
    TestCaseInputs,
    TestCaseOrigin,
    compute_case_digest,
)
from ectt.tcm.errors import InterchangeError

__all__ = [
    "INTERCHANGE_VERSION",
    "COLUMNS",
    "InterchangeExport",
    "InterchangeImport",
    "export_cases",
    "import_cases",
]

INTERCHANGE_VERSION = "1"

COLUMNS: tuple[str, ...] = (
    "ectt_interchange_version",
    "id",
    "unit",
    "function",
    "origin_author",
    "origin_engine",
    "origin_model",
    "origin_review_state",
    "requirements",
    "suites",
    "robustness",
    "input_parameters",
    "input_globals",
    "expected_return",
    "expected_globals",
    "expected_out_parameters",
    "expected_comparison",
    "stubs",
    "digest",
)

_LIST_COLUMNS = ("requirements", "suites")
_JSON_COLUMNS = (
    "input_parameters",
    "input_globals",
    "expected_globals",
    "expected_out_parameters",
    "expected_comparison",
    "stubs",
)


def _join_list(values: tuple[str, ...]) -> str:
    return ";".join(values)


def _split_list(text: str) -> tuple[str, ...]:
    return tuple(part for part in text.split(";") if part)


def _json_cell(value: Any) -> str:
    if not value:
        return "{}"
    return canonical_json(value)


def _parse_json_cell(text: str, *, column: str, row: str) -> Any:
    stripped = text.strip()
    if not stripped or stripped == "{}":
        return {}
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise InterchangeError(
            f"row for '{row}': column '{column}' is not valid JSON: {exc}"
        ) from None


@dataclass(frozen=True)
class InterchangeExport:
    """The interchange text plus everything the format could not express."""

    text: str
    losses: tuple[str, ...]


@dataclass(frozen=True)
class InterchangeImport:
    """Reconstructed cases plus integrity notes from the import."""

    cases: tuple[DataDrivenTestCase, ...]
    digest_mismatches: tuple[str, ...]


def _case_row(case: DataDrivenTestCase) -> tuple[list[str], list[str]]:
    losses: list[str] = []
    for field in _LIST_COLUMNS:
        values = case.requirements if field == "requirements" else case.suites
        losses.extend(
            f"case '{case.case_id}': {field} value '{value}' contains "
            "';' and cannot round-trip through the interchange"
            for value in values
            if ";" in value
        )
    if case.extra:
        losses.append(
            f"case '{case.case_id}': non-schema key(s) {sorted(case.extra)} "
            "are not representable in the interchange"
        )
    row = [
        INTERCHANGE_VERSION,
        case.case_id,
        case.unit,
        case.function,
        case.origin.author,
        case.origin.engine or "",
        case.origin.model or "",
        case.origin.review_state or "",
        _join_list(case.requirements),
        _join_list(case.suites),
        "true" if case.robustness else "false",
        _json_cell(dict(case.inputs.parameters)),
        _json_cell(dict(case.inputs.global_inits)),
        case.expected.return_value or "",
        _json_cell(dict(case.expected.global_finals)),
        _json_cell(dict(case.expected.out_parameters)),
        _json_cell({k: dict(v) for k, v in case.expected.comparison.items()}),
        _json_cell(
            {
                stub.name: {
                    "mode": stub.mode,
                    **({"returns": list(stub.returns)} if stub.returns else {}),
                    **({"expect_calls": stub.expect_calls} if stub.expect_calls is not None else {}),
                    **({"out_parameters": dict(stub.out_parameters)} if stub.out_parameters else {}),
                }
                for stub in case.stubs
            }
        ),
        case.recorded_digest or "",
    ]
    return row, losses


def export_cases(cases: Sequence[DataDrivenTestCase]) -> InterchangeExport:
    """Serialize cases into the documented interchange (deterministic).

    Rows are sorted by id; content the format cannot express is reported in
    ``losses`` rather than dropped (DSN-TCM-070).
    """
    losses: list[str] = []
    seen: set[str] = set()
    rows: list[list[str]] = []
    for case in cases:
        if case.case_id in seen:
            raise InterchangeError(
                f"test case '{case.case_id}' appears more than once in the export"
            )
        seen.add(case.case_id)
        row, case_losses = _case_row(case)
        rows.append(row)
        losses.extend(case_losses)
    rows.sort(key=lambda row: row[1])  # deterministic: sorted by id
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)
    writer.writerows(rows)
    return InterchangeExport(text=buffer.getvalue(), losses=tuple(losses))


def _validate_header(reader_fieldnames: list[str] | None) -> None:
    if reader_fieldnames is None:
        raise InterchangeError("interchange is empty; expected the documented header row")
    missing = [column for column in COLUMNS if column not in reader_fieldnames]
    unknown = [column for column in reader_fieldnames if column not in COLUMNS]
    if missing:
        raise InterchangeError(f"interchange is missing required column(s): {missing}")
    if unknown:
        raise InterchangeError(f"interchange carries unknown column(s): {unknown}")


def import_cases(text: str) -> InterchangeImport:
    """Reconstruct cases from the interchange (strict column validation).

    Rows lacking a digest arrive unverified; rows whose recorded digest no
    longer matches their reconstructed content are reported in
    ``digest_mismatches`` (D-02 staleness, never silently accepted).
    """
    reader = csv.DictReader(io.StringIO(text))
    _validate_header(list(reader.fieldnames or []))
    cases: list[DataDrivenTestCase] = []
    mismatches: list[str] = []
    seen: set[str] = set()
    for row in reader:
        case_id = (row["id"] or "").strip()
        if not case_id:
            raise InterchangeError("interchange row is missing a non-empty 'id'")
        if case_id in seen:
            raise InterchangeError(f"test case '{case_id}' appears more than once")
        seen.add(case_id)
        unit = (row["unit"] or "").strip()
        function = (row["function"] or "").strip()
        if not unit or not function:
            raise InterchangeError(
                f"row for '{case_id}' is missing a non-empty 'unit' or 'function'"
            )
        parameters = _parse_json_cell(row["input_parameters"], column="input_parameters", row=case_id)
        global_inits = _parse_json_cell(row["input_globals"], column="input_globals", row=case_id)
        expected_globals = _parse_json_cell(row["expected_globals"], column="expected_globals", row=case_id)
        out_parameters = _parse_json_cell(
            row["expected_out_parameters"], column="expected_out_parameters", row=case_id
        )
        comparison = _parse_json_cell(row["expected_comparison"], column="expected_comparison", row=case_id)
        stubs_raw = _parse_json_cell(row["stubs"], column="stubs", row=case_id)
        if not isinstance(parameters, dict) or not isinstance(global_inits, dict):
            raise InterchangeError(f"row for '{case_id}': input cells must be JSON objects")
        if not isinstance(expected_globals, dict) or not isinstance(out_parameters, dict):
            raise InterchangeError(f"row for '{case_id}': expected map cells must be JSON objects")
        if not isinstance(comparison, dict) or not isinstance(stubs_raw, dict):
            raise InterchangeError(f"row for '{case_id}': comparison and stubs cells must be JSON objects")
        stubs = tuple(
            sorted(
                (
                    StubSpec(
                        name=name,
                        mode=spec.get("mode", ""),
                        returns=tuple(spec.get("returns", ())),
                        expect_calls=spec.get("expect_calls"),
                        out_parameters=spec.get("out_parameters", {}),
                    )
                    for name, spec in stubs_raw.items()
                    if isinstance(spec, dict)
                ),
                key=lambda stub: stub.name,
            )
        )
        case = DataDrivenTestCase(
            case_id=case_id,
            unit=unit,
            function=function,
            inputs=TestCaseInputs(parameters=parameters, global_inits=global_inits),
            expected=TestCaseExpected(
                return_value=(row["expected_return"] or "").strip() or None,
                global_finals=expected_globals,
                out_parameters=out_parameters,
                comparison={key: dict(value) for key, value in comparison.items()},
            ),
            stubs=stubs,
            origin=TestCaseOrigin(
                author=(row["origin_author"] or "human").strip() or "human",
                engine=(row["origin_engine"] or "").strip() or None,
                model=(row["origin_model"] or "").strip() or None,
                review_state=(row["origin_review_state"] or "").strip() or None,
            ),
            requirements=_split_list(row["requirements"] or ""),
            suites=_split_list(row["suites"] or ""),
            robustness=(row["robustness"] or "").strip().lower() == "true",
        )
        digest = compute_case_digest(case.content_payload())
        recorded = (row["digest"] or "").strip() or None
        case = replace(case, content_digest=digest, recorded_digest=recorded)
        if case.recorded_digest is not None and case.recorded_digest != case.content_digest:
            mismatches.append(case_id)
        cases.append(case)
    return InterchangeImport(cases=tuple(cases), digest_mismatches=tuple(sorted(mismatches)))

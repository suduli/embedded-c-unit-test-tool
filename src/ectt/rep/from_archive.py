# implements: TOOL-REP-150
"""Report generation from archived result data (WP-REP-09).

A report is rebuilt from an archived record (WP-PRJ-05) without re-executing
tests: the archive document is integrity-verified first (its own digest
binding), the archived result set is revalidated at the runner boundary
(``finalize_result`` enforces the NR-18 invariants again), and the archived
coverage section becomes the report's coverage.

The rebuilt report's *hashed* provenance matches the original's: the
archived result set digests identically to the run's, and the regeneration
timestamp is excluded from the provenance hash. Only the timestamps differ.

A bare archived result-set dictionary (without the archive wrapper) can be
rebuilt through ``result_set_from_dict`` + ``build_report_model``.

Satisfies: TOOL-REP-150.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from ectt.core.determinism import Clock
from ectt.exh.results import (
    AssertionFailure,
    ExecutionMetadata,
    ResultSet,
    SourceLocation,
    finalize_result,
)
from ectt.prj.archive import load_archive_record
from ectt.rep.errors import ReportModelError
from ectt.rep.model import (
    ReportModel,
    build_report_model,
    coverage_entry,
)

__all__ = [
    "report_from_archive",
    "result_set_from_dict",
]


def _require(data: Mapping[str, Any], key: str, where: str) -> Any:
    if key not in data:
        raise ReportModelError(f"archived {where} is missing '{key}'", reason="missing_field")
    return data[key]


def result_set_from_dict(doc: Mapping[str, Any]) -> ResultSet:
    """Rebuild a validated ResultSet from its canonical exchange dictionary.

    Every result is revalidated at the runner boundary (``finalize_result``),
    so an archived result set cannot smuggle in an invalid record.
    """
    run_id = doc.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ReportModelError("archived result set is missing 'run_id'", reason="missing_field")
    execution_raw = doc.get("execution")
    if not isinstance(execution_raw, Mapping):
        raise ReportModelError("archived result set is missing 'execution'", reason="missing_field")
    where = _require(execution_raw, "where", "execution facts")
    toolchain = _require(execution_raw, "toolchain", "execution facts")
    if not isinstance(where, str) or not where or not isinstance(toolchain, str) or not toolchain:
        raise ReportModelError(
            "archived execution facts require non-empty where and toolchain",
            reason="invalid_field",
        )
    target_id = execution_raw.get("target_id")
    order_seed = execution_raw.get("order_seed")

    results = []
    for raw in doc.get("results", []):
        if not isinstance(raw, Mapping):
            raise ReportModelError("every archived result must be an object", reason="invalid_entry")
        failures = tuple(
            AssertionFailure(
                assertion=str(_require(failure, "assertion", "failure")),
                expected=str(_require(failure, "expected", "failure")),
                actual=str(_require(failure, "actual", "failure")),
                location=SourceLocation(
                    file=str(_require(failure["location"], "file", "failure location")),
                    line=int(_require(failure["location"], "line", "failure location")),
                    column=failure["location"].get("column"),
                ),
            )
            for failure in raw.get("failures", [])
        )
        results.append(
            finalize_result(
                str(_require(raw, "test_id", "result")),
                str(_require(raw, "outcome", "result")),
                str(_require(raw, "test_digest", "result")),
                failures=failures,
                duration_ms=raw.get("duration_ms"),
            )
        )

    return ResultSet(
        run_id=run_id,
        execution=ExecutionMetadata(
            where=where,
            toolchain=toolchain,
            target_id=str(target_id) if target_id is not None else None,
            order_seed=int(order_seed) if order_seed is not None else None,
        ),
        results=tuple(results),
        not_executed=tuple(str(test_id) for test_id in doc.get("not_executed", [])),
        partial=bool(doc.get("partial", False)),
        infrastructure_faults=tuple(str(fault) for fault in doc.get("infrastructure_faults", [])),
        schema_version=str(doc.get("schema_version", "1.0")),
    )


def report_from_archive(archive: str | bytes | Mapping[str, Any], *, clock: Clock) -> ReportModel:
    """Build a report model from an archived record (TOOL-REP-150).

    Consumes only the archived document — no test is re-executed. The archive
    is integrity-verified first (its own digest binding); the archived result
    set is revalidated at the runner boundary; the archived coverage section
    becomes the report's coverage. An archive without a result_set section is
    refused: there is nothing to report from.
    """
    if isinstance(archive, (bytes, bytearray, memoryview)):
        doc: Any = json.loads(bytes(archive).decode("utf-8"))
    elif isinstance(archive, str):
        doc = json.loads(archive)
    elif isinstance(archive, Mapping):
        doc = dict(archive)
    else:
        raise TypeError(f"Unsupported archive source: {type(archive).__name__}")
    if not isinstance(doc, Mapping):
        raise ReportModelError("archive document root must be a JSON object", reason="invalid_root_type")

    if doc.get("result_set") is None:
        raise ReportModelError(
            "archived record carries no result_set section to report from",
            reason="missing_result_set",
        )
    result_set_raw = doc["result_set"]
    if not isinstance(result_set_raw, Mapping):
        raise ReportModelError("archived 'result_set' must be an object", reason="invalid_entry")

    # Integrity first: refuse to report from a record that fails its own
    # digest binding (WP-PRJ-05).
    load_archive_record(doc)

    result_set = result_set_from_dict(result_set_raw)
    coverage = tuple(
        coverage_entry(str(entry["unit"]), int(entry["covered"]), int(entry["total"]))
        for entry in doc.get("coverage", [])
        if isinstance(entry, Mapping)
    )
    return build_report_model(result_set, coverage=coverage, clock=clock)

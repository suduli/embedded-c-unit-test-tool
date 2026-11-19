# implements: TOOL-REP-090, TOOL-REP-100
"""Single intermediate report model (WP-REP-01).

One documented intermediate data model feeds every report format: renderers
consume only the model's accessors, so two renderers cannot disagree on a
test status or a coverage figure (TOOL-REP-090), and rendering is a pure
function of the model content (TOOL-REP-100; timestamps enter the model only
through the injected Clock and are excluded from rendered output).

Identity follows decision D-02 ("stable ids plus content digests"): every
executed test entry carries the content digest of the test definition it
executed, and the model carries a report id computed over its canonical
content and verified on load.

Satisfies: TOOL-REP-090, TOOL-REP-100.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from ectt.core.determinism import Clock, canonical_json, canonical_json_bytes, stable_id
from ectt.exh.results import ResultSet
from ectt.rep.errors import ReportModelError

__all__ = [
    "REPORT_MODEL_SCHEMA_VERSION",
    "TEST_STATUSES",
    "CoverageEntry",
    "ReportModel",
    "TestEntry",
    "build_report_model",
    "coverage_entry",
    "dump_report_model",
    "load_report_model",
    "report_model_to_dict",
    "test_entry",
]

REPORT_MODEL_SCHEMA_VERSION = "1.0"

#: The report status vocabulary: the S3 outcome vocabulary of the execution
#: host (ectt.exh.results), carried unchanged.
TEST_STATUSES = ("pass", "fail", "error", "timeout", "not_run")


@dataclass(frozen=True)
class TestEntry:
    """One test's status in the report model."""

    test_id: str
    status: str
    digest: str = ""  # content digest of the executed definition; empty only for not_run

    def to_dict(self) -> dict[str, str]:
        """Return the canonical dictionary form."""
        return {"digest": self.digest, "status": self.status, "test_id": self.test_id}


@dataclass(frozen=True)
class CoverageEntry:
    """One unit's coverage figures in the report model.

    Figures are the raw counters; derived ratios are a display concern and
    are deliberately not part of the model (REP-10 export is WP-REP-06/P4).
    """

    unit: str
    covered: int
    total: int

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical dictionary form."""
        return {"covered": self.covered, "total": self.total, "unit": self.unit}


@dataclass(frozen=True)
class ReportModel:
    """The single intermediate report model every format renders from."""

    report_id: str
    run_id: str
    tests: tuple[TestEntry, ...]
    coverage: tuple[CoverageEntry, ...]
    partial: bool
    generated_at: str

    def test_statuses(self) -> dict[str, str]:
        """Return the test statuses; the one source every renderer consumes."""
        return {entry.test_id: entry.status for entry in self.tests}

    def coverage_figures(self) -> dict[str, tuple[int, int]]:
        """Return the coverage figures; the one source every renderer consumes."""
        return {entry.unit: (entry.covered, entry.total) for entry in self.coverage}


def _id(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        raise ReportModelError(f"{what} must be a non-empty string without whitespace", reason="invalid_id")
    return value


def test_entry(test_id: str, status: str, digest: str = "") -> TestEntry:
    """Construct a validated test entry."""
    _id(test_id, "test id")
    if status not in TEST_STATUSES:
        raise ReportModelError(
            f"test '{test_id}' has unknown status '{status}' (vocabulary: {', '.join(TEST_STATUSES)})",
            reason="invalid_status",
        )
    if not isinstance(digest, str):
        raise ReportModelError(f"test '{test_id}' digest must be a string", reason="invalid_digest")
    if status != "not_run" and not digest:
        raise ReportModelError(
            f"executed test '{test_id}' requires the digest of the definition it ran (D-02)",
            reason="missing_digest",
        )
    return TestEntry(test_id=test_id, status=status, digest=digest)


def coverage_entry(unit: str, covered: int, total: int) -> CoverageEntry:
    """Construct a validated coverage entry."""
    _id(unit, "coverage unit id")
    if not isinstance(covered, int) or not isinstance(total, int) or isinstance(covered, bool) or isinstance(total, bool):
        raise ReportModelError(f"coverage figures for '{unit}' must be integers", reason="invalid_coverage_figures")
    if covered < 0 or total < 0 or covered > total:
        raise ReportModelError(
            f"coverage figures for '{unit}' are inconsistent: covered={covered}, total={total}",
            reason="invalid_coverage_figures",
        )
    return CoverageEntry(unit=unit, covered=covered, total=total)


def _make_model(
    *,
    run_id: str,
    tests: tuple[TestEntry, ...],
    coverage: tuple[CoverageEntry, ...],
    partial: bool,
    generated_at: str,
) -> ReportModel:
    body: dict[str, Any] = {
        "coverage": [entry.to_dict() for entry in coverage],
        "generated_at": generated_at,
        "partial": partial,
        "run_id": run_id,
        "tests": [entry.to_dict() for entry in tests],
    }
    report_id = stable_id(canonical_json_bytes(body))
    return ReportModel(
        report_id=report_id,
        run_id=run_id,
        tests=tests,
        coverage=coverage,
        partial=partial,
        generated_at=generated_at,
    )


def build_report_model(
    result_set: ResultSet,
    *,
    coverage: Iterable[CoverageEntry] = (),
    clock: Clock,
) -> ReportModel:
    """Aggregate one run's results and optional coverage figures into the model.

    Tests not executed (listed in ``result_set.not_executed``) enter with
    status ``not_run`` and no digest. Timestamps enter only through the
    injected Clock (TOOL-REP-100).
    """
    if not isinstance(result_set, ResultSet):
        raise TypeError(f"Expected ectt.exh.results.ResultSet, got {type(result_set).__name__}")
    _id(result_set.run_id, "run id")

    entries: dict[str, TestEntry] = {}
    for record in result_set.results:
        if record.test_id in entries:
            raise ReportModelError(f"duplicate result for test '{record.test_id}'", reason="duplicate_test")
        entries[record.test_id] = test_entry(record.test_id, record.outcome, record.test_digest)
    for test_id in result_set.not_executed:
        if test_id in entries:
            raise ReportModelError(
                f"test '{test_id}' has both a result and a not-executed entry",
                reason="conflicting_test_state",
            )
        entries[test_id] = test_entry(test_id, "not_run", "")

    coverage_map: dict[str, CoverageEntry] = {}
    for entry in coverage:
        if entry.unit in coverage_map:
            raise ReportModelError(f"duplicate coverage entry for unit '{entry.unit}'", reason="duplicate_coverage")
        coverage_map[entry.unit] = entry

    return _make_model(
        run_id=result_set.run_id,
        tests=tuple(entries[key] for key in sorted(entries)),
        coverage=tuple(coverage_map[key] for key in sorted(coverage_map)),
        partial=result_set.partial,
        generated_at=clock.isoformat(),
    )


def report_model_to_dict(model: ReportModel) -> dict[str, Any]:
    """Return the canonical dictionary form (schema_version first on dump)."""
    return {
        "coverage": [entry.to_dict() for entry in model.coverage],
        "generated_at": model.generated_at,
        "partial": model.partial,
        "report_id": model.report_id,
        "run_id": model.run_id,
        "schema_version": REPORT_MODEL_SCHEMA_VERSION,
        "tests": [entry.to_dict() for entry in model.tests],
    }


def dump_report_model(model: ReportModel) -> str:
    """Serialise the model to byte-deterministic canonical JSON text."""
    return canonical_json(report_model_to_dict(model), first_keys=("schema_version",))


def _field(data: Mapping[str, Any], key: str, where: str) -> Any:
    if key not in data:
        raise ReportModelError(f"report model {where} is missing required field '{key}'", reason="missing_field")
    return data[key]


def _report_id_from_body(body: Mapping[str, Any]) -> str:
    return stable_id(
        canonical_json_bytes(
            {
                "coverage": body["coverage"],
                "generated_at": body["generated_at"],
                "partial": body["partial"],
                "run_id": body["run_id"],
                "tests": body["tests"],
            }
        )
    )


def load_report_model(source: str | bytes | Mapping[str, Any]) -> ReportModel:
    """Load and validate a persisted report model.

    Refuses unknown schema versions and models whose stored report id does
    not match the id recomputed from the content (D-02 digest binding).
    """
    if isinstance(source, (bytes, bytearray, memoryview)):
        doc: Any = json.loads(bytes(source).decode("utf-8"))
    elif isinstance(source, str):
        doc = json.loads(source)
    elif isinstance(source, Mapping):
        doc = dict(source)
    else:
        raise TypeError(f"Unsupported report model source: {type(source).__name__}")
    if not isinstance(doc, Mapping):
        raise ReportModelError("report model document root must be a JSON object", reason="invalid_root_type")

    version = _field(doc, "schema_version", "document")
    if version != REPORT_MODEL_SCHEMA_VERSION:
        raise ReportModelError(
            f"unsupported report model schema version '{version}' (reader publishes {REPORT_MODEL_SCHEMA_VERSION})",
            reason="incompatible_schema_version",
        )

    run_id = _field(doc, "run_id", "document")
    generated_at = _field(doc, "generated_at", "document")
    partial = _field(doc, "partial", "document")
    stored_report_id = _field(doc, "report_id", "document")
    if not isinstance(partial, bool):
        raise ReportModelError("'partial' must be a boolean", reason="invalid_partial")
    _id(run_id, "run id")
    if not isinstance(generated_at, str) or not generated_at:
        raise ReportModelError("'generated_at' must be a non-empty string", reason="invalid_timestamp")

    raw_tests = _field(doc, "tests", "document")
    raw_coverage = _field(doc, "coverage", "document")
    if not isinstance(raw_tests, list) or not isinstance(raw_coverage, list):
        raise ReportModelError("'tests' and 'coverage' must be arrays", reason="invalid_collection")

    tests: list[TestEntry] = []
    seen_tests: set[str] = set()
    for raw in raw_tests:
        if not isinstance(raw, Mapping):
            raise ReportModelError("every test entry must be an object", reason="invalid_entry")
        entry = test_entry(_field(raw, "test_id", "test entry"), _field(raw, "status", "test entry"), raw.get("digest", ""))
        if entry.test_id in seen_tests:
            raise ReportModelError(f"duplicate test entry '{entry.test_id}'", reason="duplicate_test")
        seen_tests.add(entry.test_id)
        tests.append(entry)

    coverage_list: list[CoverageEntry] = []
    seen_units: set[str] = set()
    for raw in raw_coverage:
        if not isinstance(raw, Mapping):
            raise ReportModelError("every coverage entry must be an object", reason="invalid_entry")
        cov_entry = coverage_entry(_field(raw, "unit", "coverage entry"), _field(raw, "covered", "coverage entry"), _field(raw, "total", "coverage entry"))
        if cov_entry.unit in seen_units:
            raise ReportModelError(f"duplicate coverage entry '{cov_entry.unit}'", reason="duplicate_coverage")
        seen_units.add(cov_entry.unit)
        coverage_list.append(cov_entry)

    recomputed = _report_id_from_body(
        {
            "coverage": [entry.to_dict() for entry in coverage_list],
            "generated_at": generated_at,
            "partial": partial,
            "run_id": run_id,
            "tests": [entry.to_dict() for entry in tests],
        }
    )
    if recomputed != stored_report_id:
        raise ReportModelError(
            "stored report id does not match the recomputed content digest",
            reason="digest_mismatch",
        )

    return ReportModel(
        report_id=stored_report_id,
        run_id=run_id,
        tests=tuple(tests),
        coverage=tuple(coverage_list),
        partial=partial,
        generated_at=generated_at,
    )

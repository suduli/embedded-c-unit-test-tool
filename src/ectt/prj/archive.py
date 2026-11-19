# implements: TOOL-PRJ-100, TOOL-PRJ-110
"""Archival export and reproduction verification (WP-PRJ-05).

An archive record is one complete, self-contained document of a verification
run — configuration, test cases, results, coverage, and the tool version —
serialised as byte-deterministic canonical JSON with a content-derived
archive id (D-02) and the embedded core provenance record, so it is suitable
for long-term archival.

Reproduction verification (TOOL-PRJ-110) checks an archived record and
reports, deterministically, whether it can be reproduced: record integrity
(archive id over content), provenance integrity (embedded record digest),
and whether the tool version that produced the record matches the tool
asking the question.

The configuration and test-case sections are opaque canonical documents:
the archive binds them byte-exactly without interpreting them, so it never
drifts from the producing packages' on-disk formats.

Satisfies: TOOL-PRJ-100, TOOL-PRJ-110.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from ectt.core.determinism import Clock, canonical_json, canonical_json_bytes, stable_id
from ectt.core.errors import EcttError
from ectt.core.provenance import ProvenanceRecord, build_provenance
from ectt.exh.results import ResultSet, result_set_to_dict

__all__ = [
    "ARCHIVE_SCHEMA_VERSION",
    "ArchiveError",
    "ArchiveRecord",
    "ReproductionVerdict",
    "build_archive_record",
    "dump_archive_record",
    "load_archive_record",
    "verify_archive_record",
]

ARCHIVE_SCHEMA_VERSION = "1.0"


class ArchiveError(EcttError):
    """Raised for invalid archive records and refused loads/verifications."""

    category: ClassVar[str] = "project"


@dataclass(frozen=True)
class ArchiveRecord:
    """One self-contained verification run, ready for long-term archival."""

    archive_id: str
    configuration: Mapping[str, Any]
    test_cases: Mapping[str, Any] | None
    result_set: Mapping[str, Any] | None
    coverage: tuple[Mapping[str, Any], ...]
    provenance: ProvenanceRecord

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical dictionary form."""
        doc: dict[str, Any] = {
            "archive_id": self.archive_id,
            "configuration": dict(self.configuration),
            "coverage": [dict(entry) for entry in self.coverage],
            "provenance": self.provenance.to_dict(),
            "schema_version": ARCHIVE_SCHEMA_VERSION,
        }
        if self.test_cases is not None:
            doc["test_cases"] = dict(self.test_cases)
        if self.result_set is not None:
            doc["result_set"] = dict(self.result_set)
        return doc


@dataclass(frozen=True)
class ReproductionVerdict:
    """Deterministic answer to 'can this archived record be reproduced?'."""

    verdict: str  # reproducible | corrupt_record | corrupt_provenance | tool_version_mismatch
    produced_with: str
    current_tool_version: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical dictionary form."""
        return {
            "current_tool_version": self.current_tool_version,
            "detail": self.detail,
            "produced_with": self.produced_with,
            "verdict": self.verdict,
        }


def _body(record: ArchiveRecord) -> dict[str, Any]:
    body = record.to_dict()
    body.pop("schema_version", None)
    return body


def build_archive_record(
    *,
    configuration: Mapping[str, Any],
    clock: Clock,
    test_cases: Mapping[str, Any] | None = None,
    result_set: ResultSet | None = None,
    coverage: Iterable[Mapping[str, Any]] = (),
) -> ArchiveRecord:
    """Bundle one verification run into a self-contained archive record.

    The embedded provenance records the tool version, build id, interpreter,
    schema versions, and the digests of the supplied documents. Timestamps
    enter only through the injected Clock.
    """
    if not isinstance(configuration, Mapping) or not configuration:
        raise ArchiveError(
            "archive record requires a non-empty configuration document",
            reason="missing_configuration",
        )
    if test_cases is not None and not isinstance(test_cases, Mapping):
        raise TypeError(f"Expected a mapping for test_cases, got {type(test_cases).__name__}")

    coverage_list = tuple(dict(entry) for entry in coverage)

    input_digests: dict[str, str] = {}
    if test_cases is not None:
        input_digests["test_cases"] = stable_id(canonical_json_bytes(dict(test_cases)))
    if result_set is not None:
        input_digests["result_set"] = stable_id(canonical_json_bytes(result_set_to_dict(result_set)))
    for index, entry in enumerate(coverage_list):
        input_digests[f"coverage[{index}]"] = stable_id(canonical_json_bytes(entry))

    schema_versions: dict[str, str] = {"archive": ARCHIVE_SCHEMA_VERSION}
    if result_set is not None:
        schema_versions["result_set"] = str(result_set.schema_version)
    provenance = build_provenance(
        clock=clock,
        schema_versions=schema_versions,
        input_digests=input_digests,
    )

    record = ArchiveRecord(
        archive_id="",
        configuration=dict(configuration),
        test_cases=dict(test_cases) if test_cases is not None else None,
        result_set=result_set_to_dict(result_set) if result_set is not None else None,
        coverage=coverage_list,
        provenance=provenance,
    )
    archive_id = stable_id(canonical_json_bytes(_body(record)))
    return ArchiveRecord(
        archive_id=archive_id,
        configuration=record.configuration,
        test_cases=record.test_cases,
        result_set=record.result_set,
        coverage=record.coverage,
        provenance=record.provenance,
    )


def dump_archive_record(record: ArchiveRecord) -> str:
    """Serialise the record to byte-deterministic canonical JSON text."""
    return canonical_json(record.to_dict(), first_keys=("schema_version",))


def load_archive_record(source: str | bytes | Mapping[str, Any]) -> ArchiveRecord:
    """Load and validate an archived record.

    Refuses unknown schema versions and records whose stored archive id does
    not match the id recomputed from the content (D-02 digest binding).
    """
    if isinstance(source, (bytes, bytearray, memoryview)):
        doc: Any = json.loads(bytes(source).decode("utf-8"))
    elif isinstance(source, str):
        doc = json.loads(source)
    elif isinstance(source, Mapping):
        doc = dict(source)
    else:
        raise TypeError(f"Unsupported archive record source: {type(source).__name__}")
    if not isinstance(doc, Mapping):
        raise ArchiveError("archive record root must be a JSON object", reason="invalid_root_type")

    if doc.get("schema_version") != ARCHIVE_SCHEMA_VERSION:
        raise ArchiveError(
            f"unsupported archive schema version {doc.get('schema_version')!r} "
            f"(reader publishes {ARCHIVE_SCHEMA_VERSION})",
            reason="incompatible_schema_version",
        )

    configuration = doc.get("configuration")
    if not isinstance(configuration, Mapping) or not configuration:
        raise ArchiveError("archived configuration is missing or empty", reason="missing_configuration")

    raw_provenance = doc.get("provenance")
    if not isinstance(raw_provenance, Mapping):
        raise ArchiveError("archive record is missing its provenance", reason="missing_provenance")
    for key in ("tool_version", "build_id", "python_version", "dependencies", "schema_versions", "input_digests", "digest"):
        if key not in raw_provenance:
            raise ArchiveError(f"embedded provenance is missing '{key}'", reason="missing_provenance")
    provenance = ProvenanceRecord(
        tool_version=str(raw_provenance["tool_version"]),
        build_id=str(raw_provenance["build_id"]),
        python_version=str(raw_provenance["python_version"]),
        dependencies=dict(raw_provenance["dependencies"]),
        schema_versions=dict(raw_provenance["schema_versions"]),
        input_digests=dict(raw_provenance["input_digests"]),
        generated_at=raw_provenance.get("generated_at"),
    )
    if provenance.digest != raw_provenance["digest"]:
        raise ArchiveError("embedded provenance digest does not match its content", reason="digest_mismatch")

    test_cases = doc.get("test_cases")
    result_set = doc.get("result_set")
    raw_coverage = doc.get("coverage", [])
    if not isinstance(raw_coverage, list):
        raise ArchiveError("'coverage' must be an array", reason="invalid_collection")

    record = ArchiveRecord(
        archive_id="",
        configuration=dict(configuration),
        test_cases=dict(test_cases) if isinstance(test_cases, Mapping) else None,
        result_set=dict(result_set) if isinstance(result_set, Mapping) else None,
        coverage=tuple(dict(entry) for entry in raw_coverage if isinstance(entry, Mapping)),
        provenance=provenance,
    )
    recomputed = stable_id(canonical_json_bytes(_body(record)))
    stored_id = doc.get("archive_id")
    if recomputed != stored_id:
        raise ArchiveError("stored archive id does not match the recomputed content digest", reason="digest_mismatch")

    return ArchiveRecord(
        archive_id=stored_id,
        configuration=record.configuration,
        test_cases=record.test_cases,
        result_set=record.result_set,
        coverage=record.coverage,
        provenance=record.provenance,
    )


def verify_archive_record(
    source: str | bytes | Mapping[str, Any],
    *,
    current_tool_version: str | None = None,
) -> ReproductionVerdict:
    """Verify an archived record; report, never raise.

    Integrity first: the record is load-verified (archive id over content,
    embedded provenance digest). A record that fails verification yields a
    ``corrupt_record`` verdict with the tool version read best-effort from
    the document. A verified record compares the producing tool version with
    the asking tool; an absent ``current_tool_version`` skips that
    comparison.
    """
    raw_tool_version = "unknown"
    if isinstance(source, Mapping):
        candidate = source.get("provenance")
    else:
        try:
            candidate = json.loads(source if isinstance(source, str) else bytes(source).decode("utf-8")).get("provenance")
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            candidate = None
    if isinstance(candidate, Mapping) and candidate.get("tool_version"):
        raw_tool_version = str(candidate["tool_version"])

    try:
        record = load_archive_record(source)
    except ArchiveError as exc:
        return ReproductionVerdict(
            verdict="corrupt_record",
            produced_with=raw_tool_version,
            current_tool_version=current_tool_version or "unknown",
            detail=f"record integrity check failed: {exc}",
        )

    produced_with = record.provenance.tool_version
    if current_tool_version is None:
        return ReproductionVerdict(
            verdict="reproducible",
            produced_with=produced_with,
            current_tool_version=produced_with,
            detail="record integrity and provenance verified; no tool version comparison requested",
        )
    if current_tool_version != produced_with:
        return ReproductionVerdict(
            verdict="tool_version_mismatch",
            produced_with=produced_with,
            current_tool_version=current_tool_version,
            detail=(
                f"record was produced by tool version '{produced_with}'; the asking tool is "
                f"'{current_tool_version}'; reproduce with the producing version or re-record"
            ),
        )
    return ReproductionVerdict(
        verdict="reproducible",
        produced_with=produced_with,
        current_tool_version=current_tool_version,
        detail="record integrity, provenance, and tool version all match",
    )

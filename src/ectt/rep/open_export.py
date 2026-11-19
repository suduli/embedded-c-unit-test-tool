# implements: TOOL-MIG-060
"""Reconstructable open result export (WP-REP-12).

One versioned JSON interchange document carrying a run's complete results
(the S3 exchange dictionary: passing, failing, crashed, timed-out and
partial-run cases; per-result identities; expected/actual values with
locations; run-level diagnostics) plus the TCM-06 test-case interchange CSV
carried verbatim with its per-row losses reported explicitly. The embedded
provenance record travels with its own digest, and the whole body is bound
by a content-derived export id (D-02) verified on load.

An independent reader reconstructs both halves without any private project
database: ``reconstruct`` re-imports the cases through the TCM-06 importer
(digest mismatches are reported, never swallowed) and the results through
the S3 reader. Coverage export deliberately remains REP-10 (P4) and is not
carried here; the published schema states that too.

Satisfies: TOOL-MIG-060.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ectt.core.determinism import Clock, canonical_json, canonical_json_bytes, stable_id
from ectt.core.provenance import ProvenanceRecord, build_provenance
from ectt.exh.results import ResultSet, result_set_to_dict
from ectt.rep.errors import ReportModelError
from ectt.rep.from_archive import result_set_from_dict
from ectt.tcm.datacases import DataDrivenTestCase
from ectt.tcm.interchange import InterchangeImport, export_cases, import_cases

__all__ = [
    "OPEN_EXPORT_SCHEMA_VERSION",
    "OpenResultExport",
    "Reconstruction",
    "build_open_export",
    "dump_open_export",
    "load_open_export",
    "reconstruct",
]

OPEN_EXPORT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class OpenResultExport:
    """The open interchange bundle: results plus cases, self-describing."""

    export_id: str
    result_set: Mapping[str, Any]
    test_cases_csv: str
    test_case_losses: tuple[str, ...]
    provenance: ProvenanceRecord

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical dictionary form."""
        return {
            "export_id": self.export_id,
            "provenance": self.provenance.to_dict(),
            "result_set": dict(self.result_set),
            "schema_version": OPEN_EXPORT_SCHEMA_VERSION,
            "test_case_losses": list(self.test_case_losses),
            "test_cases_csv": self.test_cases_csv,
        }


@dataclass(frozen=True)
class Reconstruction:
    """What an independent reader gets back from an open export."""

    result_set: ResultSet
    cases: tuple[DataDrivenTestCase, ...]
    digest_mismatches: tuple[str, ...]


def _body(export: OpenResultExport) -> dict[str, Any]:
    body = export.to_dict()
    body.pop("schema_version")
    return body


def build_open_export(
    *,
    result_set: ResultSet,
    cases: Sequence[DataDrivenTestCase] | None = None,
    clock: Clock,
) -> OpenResultExport:
    """Bundle one run's results and its TCM-06 case interchange.

    ``cases`` may be empty (a run without data-driven cases): the CSV then
    carries only the header and the loss list stays explicit.
    """
    if not isinstance(result_set, ResultSet):
        raise TypeError(f"Expected ectt.exh.results.ResultSet, got {type(result_set).__name__}")

    export_result = export_cases(list(cases)) if cases is not None else export_cases([])
    result_dict = result_set_to_dict(result_set)
    schema_versions: dict[str, str] = {
        "open_export": OPEN_EXPORT_SCHEMA_VERSION,
        "result_set": result_set.schema_version,
        "test_case_interchange": "1",
    }
    provenance = build_provenance(
        clock=clock,
        schema_versions=schema_versions,
        input_digests={
            "result_set": stable_id(canonical_json_bytes(result_dict)),
            "test_cases_csv": stable_id(export_result.text),
        },
    )
    draft = OpenResultExport(
        export_id="",
        result_set=result_dict,
        test_cases_csv=export_result.text,
        test_case_losses=tuple(export_result.losses),
        provenance=provenance,
    )
    return OpenResultExport(
        export_id=stable_id(canonical_json_bytes(_body(draft))),
        result_set=draft.result_set,
        test_cases_csv=draft.test_cases_csv,
        test_case_losses=draft.test_case_losses,
        provenance=draft.provenance,
    )


def dump_open_export(export: OpenResultExport) -> str:
    """Serialise the export to byte-deterministic canonical JSON text."""
    return canonical_json(export.to_dict(), first_keys=("schema_version",))


def load_open_export(source: str | bytes | Mapping[str, Any]) -> OpenResultExport:
    """Load and validate an open export (digest binding verified)."""
    if isinstance(source, (bytes, bytearray, memoryview)):
        doc: Any = json.loads(bytes(source).decode("utf-8"))
    elif isinstance(source, str):
        doc = json.loads(source)
    elif isinstance(source, Mapping):
        doc = dict(source)
    else:
        raise TypeError(f"Unsupported open export source: {type(source).__name__}")
    if not isinstance(doc, Mapping):
        raise ReportModelError("open export root must be a JSON object", reason="invalid_root_type")

    if doc.get("schema_version") != OPEN_EXPORT_SCHEMA_VERSION:
        raise ReportModelError(
            f"unsupported open export schema version {doc.get('schema_version')!r} "
            f"(reader publishes {OPEN_EXPORT_SCHEMA_VERSION})",
            reason="incompatible_schema_version",
        )
    for key in ("export_id", "result_set", "test_cases_csv", "test_case_losses", "provenance"):
        if key not in doc:
            raise ReportModelError(f"open export is missing '{key}'", reason="missing_field")

    raw_provenance = doc["provenance"]
    if not isinstance(raw_provenance, Mapping):
        raise ReportModelError("embedded provenance must be an object", reason="invalid_provenance")
    for key in ("tool_version", "build_id", "python_version", "dependencies", "schema_versions", "input_digests", "digest"):
        if key not in raw_provenance:
            raise ReportModelError(f"embedded provenance is missing '{key}'", reason="missing_provenance")
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
        raise ReportModelError("embedded provenance digest does not match its content", reason="digest_mismatch")

    result_set = doc["result_set"]
    test_cases_csv = doc["test_cases_csv"]
    losses = doc["test_case_losses"]
    if not isinstance(result_set, Mapping) or not isinstance(test_cases_csv, str) or not isinstance(losses, list):
        raise ReportModelError(
            "'result_set' must be an object, 'test_cases_csv' a string, 'test_case_losses' an array",
            reason="invalid_section",
        )

    draft = OpenResultExport(
        export_id="",
        result_set=dict(result_set),
        test_cases_csv=test_cases_csv,
        test_case_losses=tuple(str(loss) for loss in losses),
        provenance=provenance,
    )
    recomputed = stable_id(canonical_json_bytes(_body(draft)))
    if recomputed != doc["export_id"]:
        raise ReportModelError("stored export id does not match the recomputed content digest", reason="digest_mismatch")

    return OpenResultExport(
        export_id=str(doc["export_id"]),
        result_set=draft.result_set,
        test_cases_csv=draft.test_cases_csv,
        test_case_losses=draft.test_case_losses,
        provenance=draft.provenance,
    )


def reconstruct(export: OpenResultExport) -> Reconstruction:
    """The independent reader: rebuild cases and results from the documents.

    No private project database is consulted — the bundle is the only
    input. Case rows whose recorded digest no longer matches their content
    are reported, not dropped.
    """
    import_result: InterchangeImport = import_cases(export.test_cases_csv)
    result_set = result_set_from_dict(export.result_set)
    return Reconstruction(
        result_set=result_set,
        cases=tuple(import_result.cases),
        digest_mismatches=tuple(import_result.digest_mismatches),
    )

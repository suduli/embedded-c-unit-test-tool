# implements: TOOL-MIG-040, TOOL-MIG-110
"""Import fidelity reporting (WP-MIG-05, DSN-MIG-090).

TOOL-MIG-040: import reports, per imported artifact, what was converted, what
was converted with loss of fidelity, and what could not be converted, rather
than silently discarding content.

TOOL-MIG-110: compound or iterative test structures (slots, slot iterations,
per-slot histories) are reported explicitly as deferred, with their location,
in a machine-checkable set, never flattened, dropped or emulated.

The report is built from the results of the import adapters
(:func:`ectt.mig.csv_import.import_mapped_csv`,
:func:`ectt.mig.ceedling.import_ceedling_project`). It is a plain data record
with a deterministic JSON form, a strict loader and a consistency check, so
migration scope can be audited by a tool and not only read by a person.

Statuses: ``converted`` (nothing lost), ``converted_lossy`` (kept, with at
least one recorded loss), ``not_converted`` (kept nothing of it; the reason is
recorded). A note's ``effect`` is ``loss`` or ``info``; only losses change the
status.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ectt.core.determinism import canonical_json
from ectt.mig.ceedling import CEEDLING_PROJECT_FILE, ImportedCeedlingProject
from ectt.mig.csv_import import DEFERRED_KINDS, MappedCsvImport
from ectt.mig.errors import MigError

__all__ = [
    "FIDELITY_REPORT_VERSION",
    "STATUSES",
    "ArtifactFidelity",
    "DeferredStructure",
    "FidelityNote",
    "FidelityReport",
    "build_ceedling_fidelity_report",
    "build_csv_fidelity_report",
    "check_fidelity_report",
    "dump_fidelity_report",
    "load_fidelity_report",
]

FIDELITY_REPORT_VERSION = "1"
STATUSES: tuple[str, ...] = ("converted", "converted_lossy", "not_converted")
_EFFECTS: tuple[str, ...] = ("loss", "info")

#: Ceedling importer note kinds that are informational: nothing was lost.
_CEEDLING_INFO_KINDS = frozenset({"path_matches_nothing", "no_test_paths"})


@dataclass(frozen=True)
class FidelityNote:
    """One recorded finding about an artifact."""

    kind: str
    detail: str
    effect: str  # "loss" | "info"

    def to_dict(self) -> dict[str, str]:
        return {"detail": self.detail, "effect": self.effect, "kind": self.kind}


@dataclass(frozen=True)
class ArtifactFidelity:
    """Outcome for one imported artifact (a source row, a test file, a config file)."""

    artifact: str
    kind: str
    status: str
    notes: tuple[FidelityNote, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact,
            "kind": self.kind,
            "notes": [n.to_dict() for n in self.notes],
            "status": self.status,
        }


@dataclass(frozen=True)
class DeferredStructure:
    """A compound or iterative structure found in legacy material and deferred."""

    kind: str  # one of DEFERRED_KINDS
    artifact: str
    location: str

    def to_dict(self) -> dict[str, str]:
        return {"artifact": self.artifact, "kind": self.kind, "location": self.location}


@dataclass(frozen=True)
class FidelityReport:
    """Per-artifact import outcomes plus the deferred-structure set."""

    source: str
    artifacts: tuple[ArtifactFidelity, ...]
    deferred: tuple[DeferredStructure, ...]

    def counts(self) -> dict[str, int]:
        return {status: sum(1 for a in self.artifacts if a.status == status) for status in STATUSES}

    def deferred_set(self) -> frozenset[tuple[str, str, str]]:
        """The machine-checkable set: ``(kind, artifact, location)`` triples."""
        return frozenset((d.kind, d.artifact, d.location) for d in self.deferred)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifacts": [a.to_dict() for a in self.artifacts],
            "counts": self.counts(),
            "deferred": [d.to_dict() for d in self.deferred],
            "report_version": FIDELITY_REPORT_VERSION,
            "source": self.source,
        }


def _status(notes: tuple[FidelityNote, ...], *, rejected: bool = False) -> str:
    if rejected:
        return "not_converted"
    return "converted_lossy" if any(n.effect == "loss" for n in notes) else "converted"


def _sorted_artifacts(items: list[ArtifactFidelity]) -> tuple[ArtifactFidelity, ...]:
    return tuple(sorted(items, key=lambda a: (a.kind, a.artifact)))


def build_csv_fidelity_report(source: str, result: MappedCsvImport) -> FidelityReport:
    """Report on a mapped CSV import: one artifact per source row."""
    artifacts: list[ArtifactFidelity] = []
    deferred: list[DeferredStructure] = []
    for row in result.rows:
        artifact = f"row {row.row}"
        notes: tuple[FidelityNote, ...]
        if row.status == "rejected":
            notes = (FidelityNote(row.reason or "rejected", row.detail or "", "loss"),)
            artifacts.append(ArtifactFidelity(artifact, "csv_row", "not_converted", notes))
            deferred.extend(
                DeferredStructure(kind, artifact, f"{artifact}, column '{column}'") for kind, column in row.deferred
            )
        else:
            notes = tuple(
                FidelityNote("unmapped_column", f"cell of column '{column}' was not imported", "loss")
                for column in row.dropped_columns
            )
            artifacts.append(ArtifactFidelity(artifact, "csv_row", _status(notes), notes))
    return FidelityReport(source, _sorted_numeric(artifacts), tuple(sorted(deferred, key=lambda d: (d.artifact, d.location, d.kind))))


def _sorted_numeric(items: list[ArtifactFidelity]) -> tuple[ArtifactFidelity, ...]:
    return tuple(sorted(items, key=lambda a: (a.kind, int(a.artifact.split()[-1]))))


def build_ceedling_fidelity_report(source: str, imported: ImportedCeedlingProject) -> FidelityReport:
    """Report on a Ceedling import: one artifact for ``project.yml`` and one per test file."""
    by_artifact: dict[str, list[FidelityNote]] = {CEEDLING_PROJECT_FILE: []}
    kinds: dict[str, str] = {CEEDLING_PROJECT_FILE: "ceedling_config"}
    for test_file in imported.test_files:
        by_artifact[test_file.path] = []
        kinds[test_file.path] = "ceedling_test_file"

    for note in imported.unconverted:
        path = note.location.split(":", 1)[0]
        target = path if path in by_artifact and path != CEEDLING_PROJECT_FILE else CEEDLING_PROJECT_FILE
        effect = "info" if note.kind in _CEEDLING_INFO_KINDS else "loss"
        where = note.location if target != note.location else ""
        detail = f"{note.detail} ({where})" if where else note.detail
        by_artifact[target].append(FidelityNote(note.kind, detail, effect))

    artifacts = []
    for name, notes_list in by_artifact.items():
        notes = tuple(sorted(notes_list, key=lambda n: (n.kind, n.detail)))
        artifacts.append(ArtifactFidelity(name, kinds[name], _status(notes), notes))
    return FidelityReport(source, _sorted_artifacts(artifacts), ())


def dump_fidelity_report(report: FidelityReport) -> str:
    """Deterministic JSON text (canonical key order, no timestamps)."""
    return canonical_json(report.to_dict())


def _require(cond: bool, message: str, reason: str) -> None:
    if not cond:
        raise MigError(message, reason=reason)


def load_fidelity_report(text: str | Mapping[str, Any]) -> FidelityReport:
    """Strictly load a report; refuses unknown versions, statuses, effects and kinds."""
    try:
        doc: Any = json.loads(text) if isinstance(text, str) else dict(text)
    except json.JSONDecodeError as exc:
        raise MigError(f"fidelity report is not valid JSON: {exc}", reason="invalid_report") from exc
    _require(isinstance(doc, dict), "fidelity report root must be an object", "invalid_report")
    _require(
        doc.get("report_version") == FIDELITY_REPORT_VERSION,
        f"unsupported fidelity report version {doc.get('report_version')!r}",
        "unsupported_report_version",
    )
    source = doc.get("source")
    _require(isinstance(source, str), "fidelity report needs a 'source' string", "invalid_report")
    artifacts: list[ArtifactFidelity] = []
    for raw in doc.get("artifacts", []):
        _require(isinstance(raw, dict) and raw.get("status") in STATUSES, "artifact has an unknown status", "invalid_status")
        notes = []
        for note in raw.get("notes", []):
            _require(isinstance(note, dict) and note.get("effect") in _EFFECTS, "note has an unknown effect", "invalid_effect")
            notes.append(FidelityNote(str(note["kind"]), str(note["detail"]), note["effect"]))
        artifacts.append(ArtifactFidelity(str(raw["artifact"]), str(raw["kind"]), raw["status"], tuple(notes)))
    deferred: list[DeferredStructure] = []
    for raw in doc.get("deferred", []):
        _require(isinstance(raw, dict) and raw.get("kind") in DEFERRED_KINDS, "unknown deferred structure kind", "invalid_deferred_kind")
        deferred.append(DeferredStructure(raw["kind"], str(raw["artifact"]), str(raw["location"])))
    report = FidelityReport(source, tuple(artifacts), tuple(deferred))
    stored = doc.get("counts")
    _require(stored is None or stored == report.counts(), "stored counts do not match the artifacts", "counts_mismatch")
    return report


def check_fidelity_report(report: FidelityReport) -> list[str]:
    """Return the list of consistency violations (empty when the report is sound).

    Invariants: artifact ids unique per kind; statuses match their notes (lossy
    needs a loss note, converted has none, not_converted records a reason);
    every deferred structure names an artifact that is ``not_converted`` and
    has a location; deferred triples are unique.
    """
    problems: list[str] = []
    seen: set[tuple[str, str]] = set()
    by_name: dict[str, ArtifactFidelity] = {}
    for art in report.artifacts:
        key = (art.kind, art.artifact)
        if key in seen:
            problems.append(f"duplicate artifact {art.artifact!r} ({art.kind})")
        seen.add(key)
        by_name.setdefault(art.artifact, art)
        has_loss = any(n.effect == "loss" for n in art.notes)
        if art.status == "converted" and has_loss:
            problems.append(f"{art.artifact!r} is 'converted' but records a loss")
        if art.status == "converted_lossy" and not has_loss:
            problems.append(f"{art.artifact!r} is 'converted_lossy' without a recorded loss")
        if art.status == "not_converted" and not art.notes:
            problems.append(f"{art.artifact!r} is 'not_converted' without a reason")
    triples: set[tuple[str, str, str]] = set()
    for item in report.deferred:
        triple = (item.kind, item.artifact, item.location)
        if triple in triples:
            problems.append(f"duplicate deferred structure {triple}")
        triples.add(triple)
        if not item.location:
            problems.append(f"deferred {item.kind} in {item.artifact!r} has no location")
        owner = by_name.get(item.artifact)
        if owner is None:
            problems.append(f"deferred {item.kind} names unknown artifact {item.artifact!r}")
        elif owner.status != "not_converted":
            problems.append(f"deferred {item.kind} in {item.artifact!r} but the artifact was converted (flattened)")
    return problems

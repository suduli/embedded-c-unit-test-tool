# implements: TOOL-MIG-090
"""Migration assessment mode (WP-MIG-07, DSN-MIG-070).

TOOL-MIG-090: a mode that analyses an existing project and reports the expected
fidelity and manual effort of migration *before* migration is attempted, so the
decision is informed rather than discovered halfway through.

An assessment is a dry run of an import adapter. It never writes anything,
never raises for a legacy project it cannot read (that is a finding), and
reports:

* **outcome** - ``ready`` (nothing is lost and nothing needs hand work),
  ``needs_manual_work`` (the migration keeps what it can and lists the rest) or
  ``not_assessable`` (the legacy input cannot be read at all; the reason is given);
* **expected fidelity** - the per-artifact converted / converted-with-loss /
  not-converted counts with labelled denominators (the fidelity report of
  WP-MIG-05 is embedded unchanged);
* **manual effort** - one item per thing a person must do, with the artifact and
  an action. Effort is stated as a *count of items by kind*. No durations are
  estimated: an hour figure would be invented, and "never state what you cannot
  support" applies to estimates too;
* the **deferred structures** of TOOL-MIG-110, which are manual items by decision
  (compound authoring is deferred), listed with location.

Satisfies: TOOL-MIG-090.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ectt.core.determinism import canonical_json
from ectt.mig.ceedling import import_ceedling_project
from ectt.mig.csv_import import import_mapped_csv
from ectt.mig.errors import MigError
from ectt.mig.fidelity import (
    FidelityReport,
    build_ceedling_fidelity_report,
    build_csv_fidelity_report,
)

__all__ = [
    "OUTCOMES",
    "Assessment",
    "ManualItem",
    "assess_ceedling_project",
    "assess_mapped_csv",
    "dump_assessment",
]

OUTCOMES: tuple[str, ...] = ("ready", "needs_manual_work", "not_assessable")

#: What a person does about each finding kind. Unknown kinds fall back to a review.
_ACTIONS: dict[str, str] = {
    "parameterised_test_attribute": "Expand the TEST_CASE / TEST_RANGE / TEST_MATRIX rows into separate cases, or keep the test as a Unity test",
    "duplicate_test_name": "Rename the duplicate test function so each test has a unique name",
    "external_config_not_followed": "Merge the :import: / :mixins: configuration files into project.yml",
    "non_utf8_source": "Re-encode the source file as UTF-8",
    "unmapped_column": "Map the column to a case field, or confirm that its content may be dropped",
    "missing_id": "Give the row a case id",
    "missing_unit": "Give the row a unit",
    "missing_function": "Give the row a function",
    "duplicate_id": "Make the case ids unique",
    "ragged_row": "Correct the row so it has the same number of cells as the header",
    "stub_mode_missing": "State the stub mode; it is never assumed",
    "invalid_expect_calls": "Write the stub call count as a non-negative integer",
    "deferred_structure": "Author the compound test as a C-source test after migration (compound authoring is deferred)",
}
_FALLBACK_ACTION = "Review the finding by hand"


@dataclass(frozen=True)
class ManualItem:
    """One thing a person must do before or after migration."""

    artifact: str
    kind: str
    action: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"action": self.action, "artifact": self.artifact, "detail": self.detail, "kind": self.kind}


@dataclass(frozen=True)
class Assessment:
    """The result of assessing one legacy source, deterministic and read-only."""

    source: str
    outcome: str
    reason: str | None
    fidelity: FidelityReport | None
    manual_items: tuple[ManualItem, ...]

    def expected_fidelity(self) -> dict[str, Any]:
        """Counts and percentages of artifacts by status, each with its denominator."""
        if self.fidelity is None:
            return {"artifacts": 0, "counts": {}, "denominator": "0 artifacts", "percentages": {}}
        counts = self.fidelity.counts()
        total = sum(counts.values())
        percentages = {
            status: round(100.0 * n / total, 1) if total else 0.0 for status, n in counts.items()
        }
        return {
            "artifacts": total,
            "counts": counts,
            "denominator": f"{total} artifacts",
            "percentages": percentages,
        }

    def effort_by_kind(self) -> dict[str, int]:
        """Manual items counted by finding kind (never a duration)."""
        result: dict[str, int] = {}
        for item in self.manual_items:
            result[item.kind] = result.get(item.kind, 0) + 1
        return dict(sorted(result.items()))

    def deferred_set(self) -> frozenset[tuple[str, str, str]]:
        return self.fidelity.deferred_set() if self.fidelity is not None else frozenset()

    def to_dict(self) -> dict[str, Any]:
        return {
            "deferred": [d.to_dict() for d in self.fidelity.deferred] if self.fidelity is not None else [],
            "effort": {"by_kind": self.effort_by_kind(), "items": len(self.manual_items), "unit": "items (no durations are estimated)"},
            "expected_fidelity": self.expected_fidelity(),
            "fidelity_report": self.fidelity.to_dict() if self.fidelity is not None else None,
            "manual_items": [m.to_dict() for m in self.manual_items],
            "outcome": self.outcome,
            "reason": self.reason,
            "source": self.source,
        }


def _manual_items(report: FidelityReport) -> tuple[ManualItem, ...]:
    items = [
        ManualItem(art.artifact, note.kind, _ACTIONS.get(note.kind, _FALLBACK_ACTION), note.detail)
        for art in report.artifacts
        for note in art.notes
        if note.effect == "loss"
    ]
    return tuple(sorted(items, key=lambda m: (m.artifact, m.kind, m.detail)))


def _assessed(source: str, report: FidelityReport) -> Assessment:
    items = _manual_items(report)
    outcome = "needs_manual_work" if items or report.deferred else "ready"
    return Assessment(source, outcome, None, report, items)


def _not_assessable(source: str, error: MigError) -> Assessment:
    reason = getattr(error, "reason", None) or "unreadable"
    return Assessment(source, "not_assessable", f"{reason}: {error}", None, ())


def assess_ceedling_project(root: Path | str) -> Assessment:
    """Assess migrating the Ceedling project at ``root``; reads, never writes."""
    source = Path(root).name or str(root)
    try:
        imported = import_ceedling_project(root)
    except MigError as error:
        return _not_assessable(source, error)
    return _assessed(source, build_ceedling_fidelity_report(source, imported))


def assess_mapped_csv(
    text: str,
    mapping: Mapping[str, str],
    *,
    source: str = "export",
    delimiter: str = ",",
    deferred_columns: Mapping[str, str] | None = None,
) -> Assessment:
    """Assess migrating a tabular export through ``mapping``; nothing is imported."""
    try:
        result = import_mapped_csv(text, mapping, delimiter=delimiter, deferred_columns=deferred_columns)
    except MigError as error:
        return _not_assessable(source, error)
    return _assessed(source, build_csv_fidelity_report(source, result))


def dump_assessment(assessment: Assessment) -> str:
    """Deterministic JSON text of an assessment."""
    return canonical_json(assessment.to_dict())

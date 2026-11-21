# implements: TOOL-COV-160
"""Coverage separation: unit under test versus harness, stubs, framework (CMP-COV).

Satisfies: TOOL-COV-160 — report coverage of the unit under test separately
from coverage of harness, stub, and framework code.

Roles are assigned explicitly by the caller (UUT set from a test scope per
TOOL-ING-130, harness/stub sets from the harness generator, framework from the
tool runtime); nothing is inferred from path shapes or conventions. A file
without an assignment is surfaced as ``unclassified`` — never merged into a
role, never dropped — and the per-role totals plus the unclassified files sum
to the whole-document totals (conservation).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ectt.cov.errors import CoverageError
from ectt.cov.metrics import (
    MetricTotals,
    branch_coverage,
    function_coverage,
    statement_coverage,
)
from ectt.cov.model import GcovDocument, GcovFile

__all__ = [
    "COVERAGE_ROLES",
    "RoleCoverage",
    "SeparatedCoverage",
    "separate_coverage",
]

#: Roles coverage can be separated into (TOOL-COV-160).
COVERAGE_ROLES: tuple[str, ...] = ("uut", "harness", "stub", "framework")


@dataclass(frozen=True)
class RoleCoverage:
    """One role's coverage: its files and the metrics over them."""

    role: str
    files: tuple[str, ...]
    statements: MetricTotals
    branches: MetricTotals
    functions: MetricTotals

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "files": list(self.files),
            "statements": self.statements.to_dict(),
            "branches": self.branches.to_dict(),
            "functions": self.functions.to_dict(),
        }


@dataclass(frozen=True)
class SeparatedCoverage:
    """Per-role coverage of one document plus surfaced unclassified files."""

    roles: tuple[RoleCoverage, ...]
    unclassified: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "roles": [role.to_dict() for role in self.roles],
            "unclassified": list(self.unclassified),
        }


def separate_coverage(
    document: GcovDocument,
    assignments: Mapping[str, str],
) -> SeparatedCoverage:
    """Split a coverage document's metrics per role (TOOL-COV-160).

    ``assignments`` maps a covered source file path to its role (one of
    :data:`COVERAGE_ROLES`). Files of the document without an assignment are
    reported under ``unclassified``; an assignment for a file the document
    does not cover is ignored; an unknown role value is refused.
    """
    for path, role in assignments.items():
        if role not in COVERAGE_ROLES:
            raise CoverageError(
                f"coverage file '{path}' assigned unknown role '{role}' "
                f"(known: {', '.join(COVERAGE_ROLES)})",
                reason="unknown_role",
            )

    by_role: dict[str, list[GcovFile]] = {name: [] for name in COVERAGE_ROLES}
    unclassified: list[str] = []
    for file in document.files:
        assigned_role = assignments.get(file.file)
        if assigned_role is None:
            unclassified.append(file.file)
            continue
        by_role[assigned_role].append(file)

    roles = tuple(
        RoleCoverage(
            role=role_name,
            files=tuple(sorted(f.file for f in by_role[role_name])),
            statements=statement_coverage(by_role[role_name]),
            branches=branch_coverage(by_role[role_name]),
            functions=function_coverage(by_role[role_name]),
        )
        for role_name in COVERAGE_ROLES
    )
    return SeparatedCoverage(roles=roles, unclassified=tuple(sorted(unclassified)))

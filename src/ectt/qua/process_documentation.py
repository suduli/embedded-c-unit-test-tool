"""Development process and change control documentation (WP-QUA-05).

TOOL-QUA-070: the tool shall document its own development process, change
control, and defect management to support user assessment.

The document is assembled strictly from recorded repository facts, each
claim citing the artifact that evidences it (gate scripts, CI workflows,
PLAN-001 §9, review records, ADRs). Unsourced claims are refused; no
process-compliance claim is made that the repository does not evidence.

Satisfies: TOOL-QUA-070.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "ProcessClaim",
    "ProcessDocumentationError",
    "default_documentation",
    "render",
]


class ProcessDocumentationError(Exception):
    """Raised when a process claim lacks its required citation."""


@dataclass(frozen=True)
class ProcessClaim:
    """One process claim, traceable to a repository artifact."""

    statement: str
    citation: str


@dataclass(frozen=True)
class ProcessDocumentation:
    """The tool's own process, change-control and defect-management record."""

    development_process: tuple[ProcessClaim, ...] = ()
    change_control: tuple[ProcessClaim, ...] = ()
    defect_management: tuple[ProcessClaim, ...] = ()
    revision: str = field(default="2026-11-18")


def default_documentation() -> ProcessDocumentation:
    """Build the document strictly from repository-recorded facts."""
    return ProcessDocumentation(
        development_process=(
            ProcessClaim(
                statement=(
                    "Every change passes five gates before landing: unit test "
                    "suite, ruff lint, mypy type check, plan_check and "
                    "trace_check consistency gates."
                ),
                citation=".github/workflows/tests.yml",
            ),
            ProcessClaim(
                statement=(
                    "The requirements-to-design allocation is maintained by a "
                    "checked script, not by hand: plan_check validates the "
                    "requirement count sentinel and allocation coverage."
                ),
                citation="design/trace/plan_check.py",
            ),
            ProcessClaim(
                statement=(
                    "Requirement-to-design traceability is validated by a "
                    "graph check on every change."
                ),
                citation="design/trace/trace_check.py",
            ),
            ProcessClaim(
                statement=(
                    "Each work package lands with a verification note mapping "
                    "requirement to implementation to test evidence."
                ),
                citation="docs/verification/WP-CORE-01-analysis.md",
            ),
        ),
        change_control=(
            ProcessClaim(
                statement=(
                    "Plan changes follow a recorded change-control section: "
                    "scope-change proposals require rebaselining, and the "
                    "requirement register is the source of truth."
                ),
                citation="PLAN-001-specification-analysis-and-work-breakdown.md (§9)",
            ),
            ProcessClaim(
                statement=(
                    "Architecture decisions are recorded as ADRs; accepted "
                    "decisions and their implementation consequences are "
                    "listed in the plan."
                ),
                citation="ADR-001-architecture-decisions.md",
            ),
            ProcessClaim(
                statement=(
                    "Independent document reviews are recorded with evidence "
                    "files before findings are acted on."
                ),
                citation="docs/reviews/2026-11-06-vcast-findings-evidence-RV-01.md",
            ),
        ),
        defect_management=(
            ProcessClaim(
                statement=(
                    "Verification gaps are recorded as named gaps in the "
                    "affected work package's analysis note rather than left "
                    "unrecorded (example: symlink-privilege test skips)."
                ),
                citation="docs/verification/WP-PRJ-04-analysis.md",
            ),
            ProcessClaim(
                statement=(
                    "Work-package completion states are recorded in a ledger "
                    "with per-item evidence and open items, so unresolved "
                    "defects stay visible."
                ),
                citation="docs/glm-night/CHAT2_LEDGER.md",
            ),
        ),
    )


def _validate(documentation: ProcessDocumentation) -> None:
    for section in (
        documentation.development_process,
        documentation.change_control,
        documentation.defect_management,
    ):
        for claim in section:
            if not claim.citation:
                raise ProcessDocumentationError(
                    f"process claim without citation: {claim.statement!r}"
                )
            if "ISO 26262 certified" in claim.statement or "CMMI" in claim.statement:
                raise ProcessDocumentationError(
                    f"process claim asserts compliance the repository does not "
                    f"evidence: {claim.statement!r}"
                )


def render(documentation: ProcessDocumentation) -> str:
    """Render the deterministic process documentation; refuses unsourced claims."""
    _validate(documentation)
    lines: list[str] = [
        "Development process, change control and defect management",
        "=========================================================",
        "",
    ]
    for title, section in (
        ("Development process", documentation.development_process),
        ("Change control", documentation.change_control),
        ("Defect management", documentation.defect_management),
    ):
        lines.append(f"{title}:")
        lines.extend(f"- {claim.statement} [citation: {claim.citation}]" for claim in section)
        lines.append("")
    lines.append(
        f"Documentation revision: {documentation.revision} "
        "(single source: ectt.qua.process_documentation)"
    )
    return "\n".join(lines) + "\n"


def _citation_exists(claim: ProcessClaim) -> bool:
    """Check the cited artifact exists (best-effort, relative to repo root)."""
    candidate = Path(claim.citation.split(" (")[0])
    return candidate.exists()

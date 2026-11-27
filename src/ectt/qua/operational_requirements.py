"""Tool Operational Requirements specification (WP-QUA-02).

TOOL-QUA-020: the tool shall be accompanied by a documented Tool
Operational Requirements specification defining its intended use, operating
environment, and known limitations.

The three required sections are structural. Intended use is recorded as
OPEN — it depends on the tool-classification decision (WP-QUA-01,
ADR-sensitive), which is never made here. Environment facts must cite their
SRS requirement; limitations must cite repository evidence; unsourced
entries are refused (fail-closed, DSN-QUA-070 discipline).

Satisfies: TOOL-QUA-020.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ectt.qua.qualification_scope import NON_CLAIM_SENTENCE

__all__ = [
    "KnownLimitation",
    "OperatingEnvironmentFact",
    "OperationalRequirements",
    "SpecificationError",
    "default_specification",
    "render",
]


class SpecificationError(Exception):
    """Raised when a specification entry lacks its required source."""


@dataclass(frozen=True)
class OperatingEnvironmentFact:
    """One operating-environment fact, traceable to an SRS requirement."""

    statement: str
    srs_id: str


@dataclass(frozen=True)
class KnownLimitation:
    """One known limitation, traceable to repository evidence."""

    statement: str
    evidence: str


@dataclass(frozen=True)
class OperationalRequirements:
    """The Tool Operational Requirements specification."""

    intended_use: str = (
        "OPEN — intended use follows the tool-classification decision "
        "(WP-QUA-01), which is pending; no use class is claimed here."
    )
    environment: tuple[OperatingEnvironmentFact, ...] = ()
    limitations: tuple[KnownLimitation, ...] = ()
    revision: str = field(default="2026-11-18")


def default_specification() -> OperationalRequirements:
    """Build the specification from recorded SRS facts and repo evidence.

    Every environment fact cites its SRS requirement id; every limitation
    cites a verification note that exists in this repository.
    """
    return OperationalRequirements(
        environment=(
            OperatingEnvironmentFact(
                statement="The tool runs on Windows.",
                srs_id="TOOL-NFR-020",
            ),
            OperatingEnvironmentFact(
                statement=(
                    "The tool requires no network access for any non-AI "
                    "functionality."
                ),
                srs_id="TOOL-NFR-100",
            ),
            OperatingEnvironmentFact(
                statement="Installation does not require administrative privileges.",
                srs_id="TOOL-NFR-110",
            ),
            OperatingEnvironmentFact(
                statement=(
                    "All tool-generated files are written to a designated output "
                    "directory, separable from user source."
                ),
                srs_id="TOOL-NFR-080",
            ),
        ),
        limitations=(
            KnownLimitation(
                statement=(
                    "Symlink-based confinement tests are skipped on machines "
                    "without Windows symlink privilege (WinError 1314 class)."
                ),
                evidence="docs/verification/WP-CORE-01-analysis.md",
            ),
            KnownLimitation(
                statement=(
                    "The packaging spike's clean-machine endpoint-security check "
                    "has not been run; the recorded verdict is local-build only."
                ),
                evidence="docs/verification/WP-SPIKE-03-analysis.md",
            ),
            KnownLimitation(
                statement=(
                    "The analysis model's unsupported-construct inventory is "
                    "carried but not yet populated by extraction."
                ),
                evidence="docs/verification/WP-ANA-07-analysis.md",
            ),
            KnownLimitation(
                statement=(
                    "Macro resolution in interfaces is not implemented; macros "
                    "obscuring an interface are not yet recorded."
                ),
                evidence="docs/verification/WP-ANA-06-analysis.md",
            ),
            KnownLimitation(
                statement=(
                    "The provenance record is not yet embedded in every "
                    "generated artifact."
                ),
                evidence="docs/verification/WP-CORE-04-analysis.md",
            ),
        ),
    )


def _validate(specification: OperationalRequirements) -> None:
    for fact in specification.environment:
        if not fact.srs_id.startswith("TOOL-"):
            raise SpecificationError(
                f"environment fact without an SRS id: {fact.statement!r}"
            )
    for limitation in specification.limitations:
        if not limitation.evidence:
            raise SpecificationError(
                f"limitation without evidence: {limitation.statement!r}"
            )


def render(specification: OperationalRequirements) -> str:
    """Render the deterministic specification; refuses unsourced entries."""
    _validate(specification)
    lines: list[str] = [
        "Tool Operational Requirements specification",
        "===========================================",
        "",
        NON_CLAIM_SENTENCE,
        "",
        f"Intended use: {specification.intended_use}",
        "",
        "Operating environment:",
    ]
    lines.extend(
        f"- {fact.statement} [source: {fact.srs_id}]" for fact in specification.environment
    )
    lines.append("")
    lines.append("Known limitations:")
    lines.extend(
        f"- {limitation.statement} [evidence: {limitation.evidence}]"
        for limitation in specification.limitations
    )
    lines.append("")
    lines.append(
        f"Specification revision: {specification.revision} "
        "(single source: ectt.qua.operational_requirements)"
    )
    return "\n".join(lines) + "\n"

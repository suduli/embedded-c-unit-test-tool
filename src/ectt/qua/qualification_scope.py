"""Qualification-scope statement (WP-QUA-07).

TOOL-QUA-090: the tool shall not claim certification or qualification it
does not hold; documentation shall state clearly what qualification evidence
is provided and what remains the user's responsibility. PLAN-001 §5.4 pins
this to one place with no other document claiming more.

This module is that one place: a data-backed statement whose *provided*
items each cite a verification note in ``docs/verification/`` and whose
renderer refuses any certification claim (fail-closed overclaim guard,
DSN-QUA-070). The tool-classification decision (TOOL-QUA-010, WP-QUA-01) is
open and recorded as such — never chosen here.

Satisfies: TOOL-QUA-090.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "OverclaimError",
    "ProvidedItem",
    "QualificationScope",
    "default_scope",
    "render",
]

#: Words that would constitute a certification claim; any provided item
#: containing them is refused unless the claim is itself the non-claim
#: sentence rendered by :func:`render`.
_CERTIFICATION_TOKENS = ("certified", "certification", "iso 26262", "iec 61508", "do-178c")

#: The only certification-related sentence the statement may contain: the
#: explicit non-claim.
NON_CLAIM_SENTENCE = (
    "This tool does not claim certification or qualification it does not hold; "
    "no certificate is issued with it."
)


@dataclass(frozen=True)
class ProvidedItem:
    """One piece of qualification evidence the tool actually provides."""

    claim: str
    evidence: str


class OverclaimError(Exception):
    """Raised when a provided item would claim certification the tool does not hold."""


@dataclass(frozen=True)
class QualificationScope:
    """The single source of truth for what is and is not qualified.

    ``classification`` is a recorded open question (WP-QUA-01, ADR-sensitive);
    it is never a chosen class.
    """

    provided: tuple[ProvidedItem, ...] = ()
    user_responsibility: tuple[str, ...] = ()
    classification: str = "OPEN — tool classification decision pending (WP-QUA-01)"
    revision: str = field(default="2026-11-18")


def default_scope() -> QualificationScope:
    """Build the statement strictly from repository-recorded evidence.

    Every provided item cites a verification note under ``docs/verification/``
    that this worktree contains; nothing here exceeds those notes.
    """
    return QualificationScope(
        provided=(
            ProvidedItem(
                claim=(
                    "Determinism, source immutability and output confinement are "
                    "implemented and verified against the PLAN-001 §5.4 exit criterion "
                    "for WP-CORE-01."
                ),
                evidence="docs/verification/WP-CORE-01-analysis.md",
            ),
            ProvidedItem(
                claim=(
                    "The structured error model, fail-safe transaction and cooperative "
                    "cancellation (WP-CORE-02 mechanisms) are implemented and tested."
                ),
                evidence="docs/verification/WP-CORE-02-analysis.md",
            ),
            ProvidedItem(
                claim=(
                    "A provenance/version-identification facility exists and is tested; "
                    "embedding into every generated artifact is still open."
                ),
                evidence="docs/verification/WP-CORE-04-analysis.md",
            ),
            ProvidedItem(
                claim=(
                    "Plain-text schema-versioned project store, compilation-database "
                    "ingestion, C front-end and interface/type extraction are implemented "
                    "with test evidence."
                ),
                evidence="docs/verification/WP-PRJ-01-analysis.md, "
                "docs/verification/WP-ING-01-analysis.md, "
                "docs/verification/WP-ANA-01-analysis.md, "
                "docs/verification/WP-ANA-02-analysis.md",
            ),
            ProvidedItem(
                claim=(
                    "The engine API protocol (versioned hello negotiation, operation "
                    "catalogue with CLI equivalents, local-only stdio transport with "
                    "SDD-002 §9.2 framing) is implemented and tested."
                ),
                evidence="docs/verification/WP-API-01-analysis.md, "
                "docs/verification/WP-API-02-analysis.md",
            ),
            ProvidedItem(
                claim=(
                    "The catalogue-generated non-interactive CLI with documented exit "
                    "codes and a pinned container-execution contract is implemented."
                ),
                evidence="docs/verification/WP-CLI-01-analysis.md, "
                "docs/verification/WP-CLI-02-analysis.md, "
                "docs/verification/WP-CLI-03-analysis.md",
            ),
            ProvidedItem(
                claim=(
                    "The three validation spikes (CFG sufficiency, nested type-aware "
                    "editor, packaging) carry verified recorded evidence; the "
                    "clean-machine endpoint-security check of the packaging spike is "
                    "still open."
                ),
                evidence="docs/verification/WP-SPIKE-01-analysis.md, "
                "docs/verification/WP-SPIKE-02-analysis.md, "
                "docs/verification/WP-SPIKE-03-analysis.md",
            ),
        ),
        user_responsibility=(
            "The tool is not certified: all certification activity, safety-case "
            "argumentation and assessor interaction remain the user's responsibility.",
            "The user must qualify the tool in their own process context; the provided "
            "evidence is a starting point, not a substitute for their qualification plan.",
            "Generated harnesses are outputs to be reviewed, not trusted evidence: the "
            "user remains responsible for their correctness in the target context.",
            "Coverage interpretation (including unmeasured constructs) remains the "
            "user's responsibility; the tool reports what it measured and nothing more.",
        ),
    )


def _refuses_certification_claims(item: ProvidedItem) -> None:
    lowered = item.claim.lower()
    for token in _CERTIFICATION_TOKENS:
        if token in lowered:
            raise OverclaimError(
                f"provided item claims '{token}' without the tool holding it "
                f"(TOOL-QUA-090); only the fixed non-claim sentence is permitted"
            )


def render(scope: QualificationScope) -> str:
    """Render the deterministic qualification-scope statement.

    Refuses provided items that would claim certification (TOOL-QUA-090).
    """
    for item in scope.provided:
        _refuses_certification_claims(item)
    lines: list[str] = [
        "Qualification scope statement",
        "=============================",
        "",
        NON_CLAIM_SENTENCE,
        "",
        f"Tool classification: {scope.classification}",
        "",
        "What the tool provides (evidence in this repository):",
    ]
    lines.extend(f"- {item.claim} [evidence: {item.evidence}]" for item in scope.provided)
    lines.append("")
    lines.append("What remains the user's responsibility:")
    lines.extend(f"- {entry}" for entry in scope.user_responsibility)
    lines.append("")
    lines.append(f"Statement revision: {scope.revision} (single source: ectt.qua)")
    return "\n".join(lines) + "\n"

"""Link closure and unresolved-reference reporting (WP-GEN-05).

Every undefined external reference in the harness link step resolves by one
of two mechanisms — a generated stub (WP-GEN-06) or explicit user-supplied
linkage — and anything left over is reported, with the closure enforced
rather than implied.

Satisfies: TOOL-HAR-120.
"""

from __future__ import annotations

from dataclasses import dataclass

from ectt.gen.errors import GenError

__all__ = [
    "RESOLVED_BY_STUB",
    "RESOLVED_BY_USER_LINKAGE",
    "UnresolvedReferenceError",
    "LinkResolution",
    "LinkClosureReport",
    "resolve_link_closure",
    "assert_closed",
]

RESOLVED_BY_STUB = "stub"
RESOLVED_BY_USER_LINKAGE = "user_linkage"


class UnresolvedReferenceError(GenError):
    """Raised when the link step still has unresolved external references."""

    def __init__(self, message: str, *, reason: str = "unresolved_reference") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class LinkResolution:
    """One reference and the mechanism that covers it."""

    reference: str
    resolved_by: str  # RESOLVED_BY_STUB | RESOLVED_BY_USER_LINKAGE


@dataclass(frozen=True)
class LinkClosureReport:
    """The full link-closure verdict for one harness link step."""

    resolved: tuple[LinkResolution, ...]
    unresolved: tuple[str, ...]

    @property
    def closed(self) -> bool:
        """Whether every reference resolved."""
        return not self.unresolved

    def to_dict(self) -> dict[str, list[object]]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "resolved": [
                {"reference": item.reference, "resolved_by": item.resolved_by}
                for item in self.resolved
            ],
            "unresolved": list(self.unresolved),
        }


def resolve_link_closure(
    references: tuple[str, ...],
    *,
    stubs: tuple[str, ...] = (),
    user_linkage: tuple[str, ...] = (),
) -> LinkClosureReport:
    """Resolve every reference against the stub and user-linkage sets.

    A reference covered by both mechanisms resolves as a stub (generated
    artifacts win); one covered by neither is reported unresolved.
    """
    stub_names = set(stubs)
    user_names = set(user_linkage)
    resolved: list[LinkResolution] = []
    unresolved: list[str] = []
    for reference in sorted(dict.fromkeys(references)):
        if reference in stub_names:
            resolved.append(LinkResolution(reference=reference, resolved_by=RESOLVED_BY_STUB))
        elif reference in user_names:
            resolved.append(
                LinkResolution(reference=reference, resolved_by=RESOLVED_BY_USER_LINKAGE)
            )
        else:
            unresolved.append(reference)
    return LinkClosureReport(resolved=tuple(resolved), unresolved=tuple(unresolved))


def assert_closed(report: LinkClosureReport) -> None:
    """Raise with the full unresolved list unless every reference resolved."""
    if not report.closed:
        raise UnresolvedReferenceError(
            "link step has unresolved external references: "
            + ", ".join(report.unresolved)
        )

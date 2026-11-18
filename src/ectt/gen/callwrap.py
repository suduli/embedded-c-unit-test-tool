"""Call wrapping of intra-unit calls (WP-GEN-11).

Intercepting calls the UUT makes to functions it defines itself — call
wrapping — without modifying user source. The wrap lives entirely in the
generated harness layer: a macro redirection defined before the UUT source
include (which only the static-exposure harness performs) and undefined after
it, with a greppable marker per wrapped callee.

Satisfies: TOOL-STB-090.
"""

from __future__ import annotations

from dataclasses import dataclass

from ectt.gen.errors import GenError

__all__ = [
    "CALL_WRAP_MARKER",
    "CallWrapPlan",
    "NotInternalCalleeError",
    "plan_call_wraps",
    "render_call_wrap_seam",
]

CALL_WRAP_MARKER = "ectt:call-wrap"


class NotInternalCalleeError(GenError):
    """Raised when a wrap request names a callee the UUT does not define itself."""

    def __init__(self, message: str, *, reason: str = "not_internal_callee") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class CallWrapPlan:
    """Which intra-unit callees are wrapped and how the seam redirects them."""

    internal_callees: tuple[str, ...]
    wrapped: tuple[str, ...]

    def to_dict(self) -> dict[str, list[str]]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {"internal_callees": list(self.internal_callees), "wrapped": list(self.wrapped)}


def plan_call_wraps(
    internal_callees: tuple[str, ...],
    wrap_requests: tuple[str, ...],
) -> CallWrapPlan:
    """Plan call wraps for intra-unit callees.

    ``internal_callees`` lists the functions the UUT defines and calls within
    itself (the analyzer's internal call classification); ``wrap_requests``
    selects the subset to wrap. A request outside that set is a named error.
    """
    known = set(internal_callees)
    for request in wrap_requests:
        if request not in known:
            raise NotInternalCalleeError(
                f"'{request}' is not defined within the UUT itself; call wrapping "
                f"applies only to intra-unit callees"
            )
    return CallWrapPlan(
        internal_callees=tuple(sorted(dict.fromkeys(internal_callees))),
        wrapped=tuple(sorted(dict.fromkeys(wrap_requests))),
    )


def render_call_wrap_seam(plan: CallWrapPlan, uut_source: str = "uut.c") -> str:
    """Render the harness-layer seam that redirects intra-unit calls.

    The seam defines a wrapper alias for every wrapped callee before the UUT
    source include and undefines it after, so interception needs no user
    source modification.
    """
    if not plan.wrapped:
        return ""
    lines: list[str] = [
        f"/* {CALL_WRAP_MARKER}: intra-unit call wrapping (generated seam). */",
        "/* Intercepting happens here, in generated text only - user source is never modified. */",
    ]
    lines.extend(f"#define {callee} ectt_wrap_{callee}" for callee in plan.wrapped)
    lines.append(f'#include "{uut_source}"')
    lines.extend(f"#undef {callee}" for callee in plan.wrapped)
    return "\n".join(lines) + "\n"

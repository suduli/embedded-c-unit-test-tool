"""CFG capability contract and cyclomatic complexity (WP-ANA-05).

TOOL-PAR-070 asks for a per-function control flow graph. libclang cannot
supply one (SDD-001 §4.2, DSN-ANA-040), so the CFG sits behind a capability
record and consumers degrade rather than break. Which mechanism *builds* the
CFG is the open ADR-001 §2.4 decision (custom builder vs a future C++
analyzer); nothing here claims a CFG exists.

TOOL-PAR-120 asks for cyclomatic complexity per function in the model. The
standard MCC approximation (decision points + 1) is computable from the
parsed translation unit without the open CFG decision: statement/branch
tokens (``if``, ``for``, ``while``, ``case``) and short-circuit/ternary
operators (``&&``, ``||``, ``?``) are counted per top-level function
definition.

Satisfies: TOOL-PAR-070 (degrade contract), TOOL-PAR-120 (computation).
Design: SDD-001 §4.2 (DSN-ANA-040), ADR-001 §2.4/§2.5.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any

__all__ = [
    "CFG_UNAVAILABLE_REASON",
    "CfgCapability",
    "compute_complexities",
    "count_decision_points",
    "cyclomatic_complexity",
]

#: Why the CFG is unavailable in this build: the producer mechanism is the
#: open ADR-001 §2.4 decision. Recorded as data so consumers degrade with a
#: reason instead of breaking on a missing graph.
CFG_UNAVAILABLE_REASON = (
    "cfg producer not selected: ADR-001 section 2.4 decision is open "
    "(libclang supplies no CFG; see WP-SPIKE-01 evidence)"
)

#: Single-token decision constructs (word tokens) and operators.
_KEYWORD_DECISIONS = frozenset({"if", "for", "while", "case"})
_OPERATOR_DECISIONS = frozenset({"&&", "||", "?"})

#: clang.cindex cursor kinds that open a function definition scope.
_FUNCTION_KINDS = ("FUNCTION_DECL", "CXX_METHOD")


@dataclass(frozen=True)
class CfgCapability:
    """The declared CFG capability of this build (DSN-ANA-040)."""

    available: bool
    reason: str

    @staticmethod
    def cfg_unavailable() -> CfgCapability:
        """The current build's capability: no CFG, with the recorded reason."""
        return CfgCapability(available=False, reason=CFG_UNAVAILABLE_REASON)


def cyclomatic_complexity(decision_points: int) -> int:
    """Return the standard MCC value: decision points + 1."""
    if decision_points < 0:
        raise ValueError("decision_points must be non-negative")
    return decision_points + 1


def count_decision_points(tokens: Iterable[tuple[str, str]]) -> int:
    """Count decision points in an iterable of ``(kind, spelling)`` tokens.

    ``kind`` is the token kind name (``keyword``/``punctuation``/...);
    identifier and operator spellings carry the decisions. The plain
    ``while`` of a ``do``-``while`` loop counts once, matching the standard
    MCC treatment of the loop's single decision.
    """
    count = 0
    for kind, spelling in tokens:
        is_keyword_decision = kind == "keyword" and spelling in _KEYWORD_DECISIONS
        if is_keyword_decision or spelling in _OPERATOR_DECISIONS:
            count += 1
    return count


def _iter_function_extents(tu: object) -> Iterator[tuple[str, object, object]]:
    """Yield ``(name, extent, tokens)`` for each top-level function definition."""
    # libclang cursors are duck-typed here to avoid importing clang.cindex at
    # module import time (the frontend owns that dependency).
    root = tu.cursor  # type: ignore[attr-defined]
    children: Iterable[object] = root.get_children()  # type: ignore[attr-defined]
    for child in children:
        kind_name = child.kind.name  # type: ignore[attr-defined]
        if kind_name in _FUNCTION_KINDS and child.is_definition():  # type: ignore[attr-defined]
            yield child.spelling, child.extent, child.get_tokens()  # type: ignore[attr-defined]


def compute_complexities(tu: object) -> dict[str, int]:
    """Compute MCC complexity per top-level function definition in ``tu``.

    Returns a mapping of function name to complexity, sorted by name for
    determinism. Functions are the translation unit's top-level definitions.
    """
    result: dict[str, int] = {}
    for name, _extent, tokens in _iter_function_extents(tu):
        libclang_tokens: Iterable[Any] = tokens  # type: ignore[assignment]
        token_pairs = [(token.kind.name.lower(), token.spelling) for token in libclang_tokens]
        result[name] = cyclomatic_complexity(count_decision_points(token_pairs))
    return dict(sorted(result.items()))

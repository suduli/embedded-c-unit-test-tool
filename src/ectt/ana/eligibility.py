# implements: DSN-ANA-130
"""Eligibility and observability gate over the analysis model.

Satisfies: TOOL-PAR-170.

The gate evaluates each discovered function against declared capability flags
and records, per function, the observable channels (parameters, return value,
global accesses) and machine-readable reasons when the function is not
eligible. Discovery does not imply eligibility: a function present in the
analysis model is not automatically testable, and requested-but-inaccessible
state is reported explicitly as gate reasons rather than silently dropped.

The records are S1-adjacent derived data consumed by CMP-ATG; they are
deliberately NOT part of the S1 document, because eligibility depends on the
consuming capability flags rather than on extracted facts alone.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from ectt.ana.model import AnalysisUnit

__all__ = [
    "EligibilityRecord",
    "assess_eligibility",
]

DEFAULT_VOID_TYPE_REFS = frozenset({"type.builtin.void"})


@dataclass(frozen=True)
class EligibilityRecord:
    """Per-function eligibility and observability assessment.

    Attributes:
        function: Function name.
        unit: Unit path the function was discovered in.
        eligible: True when no gate reason fired.
        observable_channels: Declared channels — a subset of "parameters",
            "return_value", "globals".
        reasons: Machine-readable gate reasons; empty when eligible.
    """

    function: str
    unit: str
    eligible: bool
    observable_channels: tuple[str, ...] = ()
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        return {
            "function": self.function,
            "unit": self.unit,
            "eligible": self.eligible,
            "observable_channels": list(self.observable_channels),
            "reasons": list(self.reasons),
        }


def assess_eligibility(
    units: Sequence[AnalysisUnit],
    *,
    expose_static: bool = False,
    void_type_refs: frozenset[str] = DEFAULT_VOID_TYPE_REFS,
) -> tuple[EligibilityRecord, ...]:
    """Evaluate every discovered function against the capability flags.

    Gate reasons emitted by this assessment:

    - ``static_not_exposed`` — internal (static) storage with the opt-in
      static exposure capability disabled.
    - ``no_observable_channel`` — no parameters, a void return type, and no
      global accesses: nothing about the function's behaviour can be
      observed through declared channels.

    Aspects not yet represented in the analysis model (variadic tails, VLAs,
    unsupported parameter shapes) are deliberately not assessed here; they
    enter the gate when their model facts exist.

    Args:
        units: Analysis units to assess (failed units contribute nothing).
        expose_static: The static-exposure capability flag (PAR-080/090).
        void_type_refs: Type-graph refs that mean "returns nothing".

    Returns:
        Eligibility records in unit order, then function order.
    """
    records: list[EligibilityRecord] = []
    for unit in units:
        if unit.status != "parsed":
            continue
        for fn in unit.functions:
            return_ref = fn.return_type
            if return_ref.startswith("ref:"):
                return_ref = return_ref[4:]
            channels: list[str] = []
            if fn.parameters:
                channels.append("parameters")
            if return_ref not in void_type_refs:
                channels.append("return_value")
            if fn.globals:
                channels.append("globals")

            reasons: list[str] = []
            if fn.storage_class == "static" and not expose_static:
                reasons.append("static_not_exposed")
            if not channels:
                reasons.append("no_observable_channel")

            records.append(
                EligibilityRecord(
                    function=fn.name,
                    unit=unit.path,
                    eligible=not reasons,
                    observable_channels=tuple(channels),
                    reasons=tuple(reasons),
                )
            )
    return tuple(records)

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

from ectt.ana.model import AnalysisUnit, FunctionModel, UnsupportedConstructModel

__all__ = [
    "CONSTRUCT_REASON_PREFIX",
    "EligibilityRecord",
    "UnattributedConstruct",
    "assess_eligibility",
    "find_unattributed_constructs",
]

#: Gate reasons for recorded unsupported constructs are ``unsupported_construct:<kind>``.
CONSTRUCT_REASON_PREFIX = "unsupported_construct:"

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
        kind: "function" for a function record; "unit" for the single record a
            failed unit contributes (TOOL-PAR-130). A unit record has an empty
            ``function``, and its reason is the unit's recorded failure reason.
    """

    function: str
    unit: str
    eligible: bool
    observable_channels: tuple[str, ...] = ()
    reasons: tuple[str, ...] = field(default_factory=tuple)
    kind: str = "function"

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        return {
            "function": self.function,
            "unit": self.unit,
            "kind": self.kind,
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
    - ``unsupported_construct:<kind>`` — the function owns a construct recorded
      in its unit's unsupported-construct inventory (TOOL-PAR-140), for example
      ``unsupported_construct:variadic_function``. One reason per kind, sorted
      by kind, after the reasons above.

    Attribution uses the per-occurrence records (schema 1.5): every occurrence
    names its owner function, so each owner is gated by name. Models recorded
    before schema 1.5 carry no occurrences; for those the inventory keeps only
    the *first* occurrence of each kind (its location and the owning
    function's name), so only that occurrence is attributable via the first-
    occurrence heuristic. Occurrences beyond the first are not guessed onto
    other functions; they are reported by :func:`find_unattributed_constructs`
    instead.

    Args:
        units: Analysis units to assess. A failed unit contributes one unit-kind
            record that is unmeasurable, with its recorded failure reason.
        expose_static: The static-exposure capability flag (PAR-080/090).
        void_type_refs: Type-graph refs that mean "returns nothing".

    Returns:
        Eligibility records in unit order, then function order.
    """
    records: list[EligibilityRecord] = []
    for unit in units:
        if unit.status != "parsed":
            # Unmeasurable as a whole: no function of a failed unit is assessed (TOOL-PAR-130).
            unit_reason = unit.failure.reason if unit.failure is not None else "unit_failed"
            records.append(
                EligibilityRecord(
                    function="",
                    unit=unit.path,
                    eligible=False,
                    reasons=(unit_reason,),
                    kind="unit",
                )
            )
            continue
        owners = _construct_owners(unit)
        for fn in unit.functions:
            return_ref = fn.return_type
            return_ref = return_ref.removeprefix("ref:")
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
            reasons.extend(f"{CONSTRUCT_REASON_PREFIX}{kind}" for kind in sorted(owners.get(id(fn), ())))

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


def _owns(fn: FunctionModel, construct: UnsupportedConstructModel) -> bool:
    """True when ``construct``'s recorded first occurrence belongs to ``fn``.

    First-occurrence fallback for models recorded before schema 1.5 (no
    per-occurrence owner records). The inventory records the owning
    definition's location and a detail that names the construct (``fn`` or
    ``fn.param``). A recorded location must match the function's; a missing
    location falls back to the name in the detail. A detail that names a
    different function never matches.
    """
    named = construct.detail.split(".", 1)[0] if construct.detail else None
    if named is not None and named != fn.name:
        return False
    if construct.location is not None:
        return construct.location.file == fn.location.file and construct.location.line == fn.location.line
    return named is not None


def _construct_owners(unit: AnalysisUnit) -> dict[int, set[str]]:
    """Map ``id(function)`` to the recorded construct kinds it owns.

    Schema 1.5: every occurrence names its owner function, so each named owner
    is attributed. Constructs without occurrence records (pre-1.5 models) fall
    back to the first-occurrence heuristic in :func:`_owns`.
    """
    owners: dict[int, set[str]] = {}
    for construct in unit.unsupported_constructs:
        if construct.occurrences:
            for occ in construct.occurrences:
                for fn in unit.functions:
                    if fn.name == occ.function:
                        owners.setdefault(id(fn), set()).add(construct.kind)
                        break
            continue
        for fn in unit.functions:
            if _owns(fn, construct):
                owners.setdefault(id(fn), set()).add(construct.kind)
                break
    return owners


@dataclass(frozen=True)
class UnattributedConstruct:
    """Occurrences of a construct kind the inventory cannot assign to a function."""

    unit: str
    kind: str
    count: int

    def to_dict(self) -> dict[str, Any]:
        return {"count": self.count, "kind": self.kind, "unit": self.unit}


def find_unattributed_constructs(units: Sequence[AnalysisUnit]) -> tuple[UnattributedConstruct, ...]:
    """Report construct occurrences that no function's gate reason accounts for.

    For each parsed unit and kind: ``count`` minus the occurrences attributed
    to functions. Schema 1.5 attributes every occurrence whose owner function
    name matches a function in the unit; models recorded before schema 1.5
    attribute at most the first occurrence (via the first-occurrence
    heuristic, or the full count when even the first is unattributable). The
    remainders are surfaced explicitly rather than silently dropped or spread
    over functions that may not own them. Sorted by unit then kind.
    """
    found: list[UnattributedConstruct] = []
    for unit in units:
        if unit.status != "parsed":
            continue
        function_names = {fn.name for fn in unit.functions}
        for construct in sorted(unit.unsupported_constructs, key=lambda c: c.kind):
            if construct.occurrences:
                attributed = sum(1 for occ in construct.occurrences if occ.function in function_names)
            else:
                attributed = 1 if any(_owns(fn, construct) for fn in unit.functions) else 0
            remaining = construct.count - attributed
            if remaining > 0:
                found.append(UnattributedConstruct(unit.path, construct.kind, remaining))
    return tuple(sorted(found, key=lambda f: (f.unit, f.kind)))

# implements: TOOL-ATG-110
"""Constructs a generation engine cannot handle, reported per function (WP-ATG-05, DSN-ATG-100).

TOOL-ATG-110: report the constructs the engine cannot handle (dynamic memory, floating
point, concurrency, inline assembly) rather than failing silently, so an absent test is
distinguishable from an impossible one.

An engine declares the kinds it cannot handle (:class:`EngineCapabilities`). This module
finds, in the analysis model, the functions that involve those kinds and returns one
:class:`Limitation` per function and kind, each with the evidence that triggered it:

* ``dynamic_memory``: a call to an allocator (``malloc``, ``calloc``, ``realloc``, ``free``,
  ``aligned_alloc``, ``posix_memalign``, ``strdup``, ``strndup``);
* ``floating_point``: a parameter or return type that is, or points to, holds or is an array
  of, ``float``, ``double`` or ``long double`` (typedefs and struct members followed);
* ``concurrency``: a call into a threading, locking or atomics API (``pthread_*``, ``thrd_*``,
  ``mtx_*``, ``cnd_*``, ``sem_*``, ``atomic_*``, ``__atomic_*``) or ``fork``, ``vfork``, ``clone``;

**Inline assembly cannot be detected**: the analysis model does not record it. It is always
listed in ``not_assessed``, so a report never implies that none was found.

Only kinds the engine declares it cannot handle are reported; an engine that handles
floating point gets no floating-point limitation. Output is sorted and deterministic.

Satisfies: TOOL-ATG-110.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ectt.ana.model import AnalysisUnit, FunctionModel, TypeModel
from ectt.atg.errors import AtgError

__all__ = [
    "ASSESSED_KINDS",
    "NOT_ASSESSED_KINDS",
    "EngineCapabilities",
    "Limitation",
    "assess_capabilities",
]

ASSESSED_KINDS: tuple[str, ...] = ("concurrency", "dynamic_memory", "floating_point")
NOT_ASSESSED_KINDS: tuple[str, ...] = ("inline_assembly",)

_ALLOCATORS = frozenset({"malloc", "calloc", "realloc", "free", "aligned_alloc", "posix_memalign", "strdup", "strndup"})
_CONCURRENCY_PREFIXES = ("pthread_", "thrd_", "mtx_", "cnd_", "sem_", "atomic_", "__atomic_")
_CONCURRENCY_CALLS = frozenset({"fork", "vfork", "clone"})
_FLOAT_NAMES = frozenset({"float", "double", "long double"})


@dataclass(frozen=True)
class EngineCapabilities:
    """What a generation engine declares it cannot handle (any of ``ASSESSED_KINDS`` and ``inline_assembly``)."""

    engine: str
    cannot_handle: frozenset[str]

    def __post_init__(self) -> None:
        known = set(ASSESSED_KINDS) | set(NOT_ASSESSED_KINDS)
        unknown = sorted(k for k in self.cannot_handle if k not in known)
        if unknown:
            raise AtgError(
                f"engine '{self.engine}' declares unknown limitation kind(s): {', '.join(unknown)} "
                f"(known: {', '.join(sorted(known))})",
                reason="unknown_limitation_kind",
            )


@dataclass(frozen=True)
class Limitation:
    """One reason a function cannot be generated for: the function, the kind and the evidence."""

    unit: str
    function: str
    kind: str
    evidence: str

    def to_dict(self) -> dict[str, str]:
        return {"evidence": self.evidence, "function": self.function, "kind": self.kind, "unit": self.unit}


def _involves_float(ref: str, types: Mapping[str, TypeModel], seen: frozenset[str]) -> bool:
    key = ref.removeprefix("ref:")
    if key in seen:
        return False
    model = types.get(key)
    if model is None:
        return key.removeprefix("type.") in _FLOAT_NAMES
    trail = seen | {key}
    if model.kind == "builtin":
        return (model.name or "") in _FLOAT_NAMES
    if model.kind == "typedef":
        return bool(model.underlying_type) and _involves_float(str(model.underlying_type), types, trail)
    if model.kind == "pointer":
        return bool(model.target) and _involves_float(str(model.target), types, trail)
    if model.kind == "array":
        return bool(model.element_type) and _involves_float(str(model.element_type), types, trail)
    if model.kind in ("struct", "union"):
        return any(_involves_float(m.type, types, trail) for m in model.members)
    return False


def _function_findings(function: FunctionModel, types: Mapping[str, TypeModel]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    callees = sorted({call.callee for call in function.calls})
    findings.extend(("dynamic_memory", f"calls {name}") for name in callees if name in _ALLOCATORS)
    findings.extend(
        ("concurrency", f"calls {name}")
        for name in callees
        if name in _CONCURRENCY_CALLS or name.startswith(_CONCURRENCY_PREFIXES)
    )
    if _involves_float(function.return_type, types, frozenset()):
        findings.append(("floating_point", "return type involves floating point"))
    findings.extend(
        ("floating_point", f"parameter '{p.name}' involves floating point")
        for p in function.parameters
        if _involves_float(p.type, types, frozenset())
    )
    return findings


def assess_capabilities(
    units: Sequence[AnalysisUnit],
    types: Mapping[str, TypeModel],
    capabilities: EngineCapabilities,
) -> tuple[Limitation, ...]:
    """The limitations of ``capabilities.engine`` over the functions of ``units``, sorted.

    Failed units contribute nothing here (the eligibility gate reports them as unmeasurable). Duplicate findings of one kind in one function are reported once per
    distinct evidence.
    """
    cannot = capabilities.cannot_handle
    found: dict[tuple[str, str, str, str], Limitation] = {}
    for unit in units:
        if unit.status != "parsed":
            continue
        for function in unit.functions:
            for kind, evidence in _function_findings(function, types):
                if kind in cannot:
                    found[(unit.path, function.name, kind, evidence)] = Limitation(unit.path, function.name, kind, evidence)
    return tuple(found[key] for key in sorted(found))


def limitations_to_dict(limitations: Sequence[Limitation], capabilities: EngineCapabilities) -> dict[str, Any]:
    """Report form: the limitations plus what was and was not assessed."""
    return {
        "assessed_kinds": list(ASSESSED_KINDS),
        "engine": capabilities.engine,
        "limitations": [limitation.to_dict() for limitation in limitations],
        "not_assessed_kinds": list(NOT_ASSESSED_KINDS),
    }

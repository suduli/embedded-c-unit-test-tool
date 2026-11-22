# implements: TOOL-QUA-030
"""The user-executable validation suite (WP-QUA-03).

TOOL-QUA-030: the tool shall have a validation test suite demonstrating that it
satisfies its Tool Operational Requirements, executable by the end user.

A :class:`ValidationCheck` declares its id, the claim it proves, its *declared*
cost class (`instant` | `quick` | `long` — never measured: the record carries no
wall-clock value) and the external tools it needs. :func:`run_validation_suite`
executes the checks offline, with bundled inputs only — no network, no compiler,
no debugger — and produces a :class:`ValidationReport` whose every result is
exactly one of ``pass``, ``fail``, ``not-run``, with a named reason on every
non-pass. A check that needs a tool the machine does not have is ``not-run``
(``missing_tool``, naming the tool) and can never read as a pass.

The record is deterministic JSON: processed in id order, canonical serialisation,
no timestamps — byte-stable across runs and independent of the order in which the
checks were presented.

The bundled default checks (:func:`default_validation_checks`) prove engine
fundamentals that hold offline: the operation catalogue is published, the
protocol's interface version is self-consistent, the canonical JSON helper is
deterministic, and the Tool Operational Requirements specification renders.

Satisfies: TOOL-QUA-030.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Collection
from dataclasses import dataclass
from typing import Any

from ectt.core.determinism import canonical_json

__all__ = [
    "COST_CLASSES",
    "STATE_FAIL",
    "STATE_NOT_RUN",
    "STATE_PASS",
    "REASON_CHECK_ERROR",
    "REASON_CHECK_FAILED",
    "REASON_MISSING_TOOL",
    "CheckOutcome",
    "ValidationCheck",
    "ValidationReport",
    "default_validation_checks",
    "dump_validation_report",
    "run_validation_suite",
]

STATE_PASS = "pass"
STATE_FAIL = "fail"
STATE_NOT_RUN = "not-run"
STATES: tuple[str, ...] = (STATE_PASS, STATE_FAIL, STATE_NOT_RUN)

#: Declared cost classes of a check (how long it takes, as the author declares
#: it; the record never measures).
COST_CLASSES: tuple[str, ...] = ("instant", "quick", "long")

#: Named reasons: why a check did not pass.
REASON_MISSING_TOOL = "missing_tool"
REASON_CHECK_FAILED = "check_failed"
REASON_CHECK_ERROR = "check_error"

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}$")


@dataclass(frozen=True)
class ValidationCheck:
    """One self-check of the validation suite (TOOL-QUA-030).

    ``proves`` states what the check demonstrates (ideally citing the
    operational requirement it exercises); ``cost`` is the declared cost class;
    ``requires`` names the external tools the check needs — a tool missing from
    the machine makes the check ``not-run``, never ``pass``. ``check`` returns
    True when the claim is demonstrated.
    """

    check_id: str
    proves: str
    cost: str
    check: Callable[[], bool]
    requires: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _IDENTIFIER_RE.match(self.check_id or ""):
            raise ValueError(f"check id {self.check_id!r} is not a simple identifier")
        if not self.proves.strip():
            raise ValueError(f"check '{self.check_id}' must state what it proves")
        if self.cost not in COST_CLASSES:
            raise ValueError(
                f"check '{self.check_id}' declares unknown cost {self.cost!r} "
                f"(declared classes: {', '.join(COST_CLASSES)})"
            )
        for tool in self.requires:
            if not _IDENTIFIER_RE.match(tool or ""):
                raise ValueError(f"check '{self.check_id}' requires the invalid tool name {tool!r}")
        if not callable(self.check):
            raise ValueError(f"check '{self.check_id}' needs a callable")


@dataclass(frozen=True)
class CheckOutcome:
    """The result of one check: pass, fail or not-run, with a named reason."""

    check_id: str
    proves: str
    cost: str
    state: str
    reason: str | None = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "cost": self.cost,
            "detail": self.detail,
            "proves": self.proves,
            "reason": self.reason,
            "state": self.state,
        }


@dataclass(frozen=True)
class ValidationReport:
    """The result record of one suite run, in id order (TOOL-QUA-030)."""

    results: tuple[CheckOutcome, ...]

    def counts(self) -> dict[str, int]:
        counts = dict.fromkeys(STATES, 0)
        for result in self.results:
            counts[result.state] += 1
        return dict(sorted(counts.items()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "counts": self.counts(),
            "results": [result.to_dict() for result in self.results],
        }


def dump_validation_report(report: ValidationReport) -> str:
    """Deterministic JSON text of a result record (byte-stable across runs)."""
    return canonical_json(report.to_dict())


def run_validation_suite(
    checks: Collection[ValidationCheck],
    *,
    available_tools: Collection[str] = (),
) -> ValidationReport:
    """Run the checks offline and return the result record.

    Checks are processed in id order. A check whose required tools are not all
    available is ``not-run`` (reason ``missing_tool``, the absent tools named in
    the detail) and its callable is never invoked. An executed check reports
    ``pass`` when it returns True, ``fail`` (``check_failed``) when it returns
    False, and ``fail`` (``check_error``) when it raises — the exception's text
    is deliberately not recorded, so the record stays byte-stable.
    """
    available = frozenset(available_tools)
    results: list[CheckOutcome] = []
    for check in sorted(checks, key=lambda c: c.check_id):
        missing = sorted(set(check.requires) - available)
        if missing:
            results.append(
                CheckOutcome(
                    check_id=check.check_id,
                    proves=check.proves,
                    cost=check.cost,
                    state=STATE_NOT_RUN,
                    reason=REASON_MISSING_TOOL,
                    detail=", ".join(missing),
                )
            )
            continue
        try:
            demonstrated = bool(check.check())
        except Exception:  # noqa: BLE001 - the check's failure is the result
            results.append(
                CheckOutcome(
                    check_id=check.check_id,
                    proves=check.proves,
                    cost=check.cost,
                    state=STATE_FAIL,
                    reason=REASON_CHECK_ERROR,
                    detail="the check raised; see its own diagnostics",
                )
            )
            continue
        if demonstrated:
            results.append(
                CheckOutcome(
                    check_id=check.check_id,
                    proves=check.proves,
                    cost=check.cost,
                    state=STATE_PASS,
                )
            )
        else:
            results.append(
                CheckOutcome(
                    check_id=check.check_id,
                    proves=check.proves,
                    cost=check.cost,
                    state=STATE_FAIL,
                    reason=REASON_CHECK_FAILED,
                )
            )
    return ValidationReport(results=tuple(results))


def default_validation_checks() -> tuple[ValidationCheck, ...]:
    """The bundled, offline self-checks (all ``instant``, none requires a tool).

    Each check proves an engine fundamental a user can verify on their own
    machine without a compiler, a debugger or a network connection.
    """
    from ectt.api.catalogue import default_catalogue
    from ectt.qua.operational_requirements import default_specification

    def catalogue_published() -> bool:
        return len(default_catalogue().names()) >= 1

    def protocol_version_self_consistent() -> bool:
        from ectt.api.catalogue import INTERFACE_VERSION, SUPPORTED_INTERFACE_VERSIONS

        return INTERFACE_VERSION in SUPPORTED_INTERFACE_VERSIONS

    def canonical_json_deterministic() -> bool:
        probe = {"b": [1, 2], "a": "x"}
        return canonical_json(probe) == canonical_json(dict(reversed(list(probe.items()))))

    def operational_specification_renders() -> bool:
        specification = default_specification()
        return bool(specification.intended_use) and len(specification.limitations) >= 1

    return (
        ValidationCheck(
            check_id="qua.catalogue-published",
            proves="the engine operation catalogue is published (the CLI/API surface exists)",
            cost="instant",
            check=catalogue_published,
        ),
        ValidationCheck(
            check_id="qua.hello-version-self-consistent",
            proves="the protocol's interface version is the one this build negotiates",
            cost="instant",
            check=protocol_version_self_consistent,
        ),
        ValidationCheck(
            check_id="qua.json-determinism",
            proves="canonical JSON is order-independent (deterministic artifacts, TOOL-NFR-060)",
            cost="instant",
            check=canonical_json_deterministic,
        ),
        ValidationCheck(
            check_id="qua.operational-specification-present",
            proves="the Tool Operational Requirements specification exists and renders (TOOL-QUA-020)",
            cost="instant",
            check=operational_specification_renders,
        ),
    )

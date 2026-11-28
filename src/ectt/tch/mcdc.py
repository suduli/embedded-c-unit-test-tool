# implements: TOOL-COV-190
"""MC/DC capability: version gate, probed condition limit and the stated form.

Owner decisions of 2026-11-27: the form offered is masking MC/DC with the gap
to unique-cause documented; GCC only; a GCC older than 14 is "not available"
(the other coverage still runs, MC/DC is reported unmeasured with the reason).

The maximum number of conditions per decision is *probed* on the configured
compiler (TOOL-COV-190), never taken from documentation. A probe that cannot
decide yields ``None`` ("unknown"), never a guessed number.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ectt.tch.config import CompilerConfig
from ectt.tch.gating import VersionRequirementError, check_version

__all__ = [
    "MCDC_FORM",
    "MCDC_MECHANISM",
    "McdcPlan",
    "ConditionLimitProbe",
    "plan_mcdc",
    "probe_condition_limit",
    "probe_source",
]

MCDC_FORM = "masking"
MCDC_MECHANISM = "gcc -fcondition-coverage"

_LIMIT_WARNING = "-Wcoverage-too-many-conditions"
_PROBE_CEILING = 4096

#: Compile one translation unit with the given extra flags and return
#: ``(succeeded, compiler output)``.
CompileRunner = Callable[[str, tuple[str, ...]], tuple[bool, str]]


@dataclass(frozen=True)
class ConditionLimitProbe:
    """The recorded evidence of one limit probe."""

    max_conditions: int | None
    attempts: tuple[tuple[int, bool], ...]  # (condition count, instrumented)
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_conditions": self.max_conditions,
            "attempts": [{"conditions": n, "instrumented": ok} for n, ok in self.attempts],
            "detail": self.detail,
        }


@dataclass(frozen=True)
class McdcPlan:
    """Whether MC/DC can be measured with a compiler, and how."""

    available: bool
    reason: str | None  # None when available, else a stable reason name
    detail: str
    form: str = MCDC_FORM
    mechanism: str = MCDC_MECHANISM
    compiler_version: str | None = None
    max_conditions: int | None = None
    compile_flags: tuple[str, ...] = ()
    gcov_flags: tuple[str, ...] = ()


def probe_source(conditions: int) -> str:
    """A translation unit holding one decision with ``conditions`` conditions."""
    parameters = ", ".join(f"int c{i}" for i in range(conditions))
    expression = " && ".join(f"c{i}" for i in range(conditions))
    return f"int probe({parameters}) {{ if ({expression}) {{ return 1; }} return 0; }}\n"


def probe_condition_limit(run: CompileRunner) -> ConditionLimitProbe:
    """Find the largest decision the compiler still instruments."""
    attempts: list[tuple[int, bool]] = []

    def instrumented(count: int) -> bool | None:
        succeeded, output = run(probe_source(count), ("--coverage", "-fcondition-coverage", "-c"))
        if not succeeded:
            return None
        accepted = _LIMIT_WARNING not in output
        attempts.append((count, accepted))
        return accepted

    def unknown(detail: str) -> ConditionLimitProbe:
        return ConditionLimitProbe(None, tuple(attempts), detail)

    low, high = 0, 2
    while high <= _PROBE_CEILING:
        verdict = instrumented(high)
        if verdict is None:
            return unknown(f"the probe with {high} conditions did not compile")
        if not verdict:
            break
        low, high = high, high * 2
    else:
        return unknown(f"no limit found up to {low} conditions")
    while high - low > 1:
        middle = (low + high) // 2
        verdict = instrumented(middle)
        if verdict is None:
            return unknown(f"the probe with {middle} conditions did not compile")
        low, high = (middle, high) if verdict else (low, middle)
    if low < 2:
        return unknown("the compiler instrumented no multi-condition decision")
    return ConditionLimitProbe(low, tuple(attempts), f"probed: {low} instrumented, {high} refused")


def plan_mcdc(
    config: CompilerConfig, version_text: str, probe: ConditionLimitProbe | None = None
) -> McdcPlan:
    """Decide whether MC/DC is available for a configuration and compiler version.

    Never raises for an unsuitable compiler: the caller runs the other coverage
    and reports MC/DC unmeasured with ``reason``.
    """

    def unavailable(reason: str, detail: str) -> McdcPlan:
        return McdcPlan(available=False, reason=reason, detail=detail)

    if config.family != "gcc":
        return unavailable(
            "mcdc_not_available", f"MC/DC is supported with GCC only; the configuration family is '{config.family}'"
        )
    if "mcdc" not in config.coverage_kinds:
        return unavailable("mcdc_not_declared", f"configuration '{config.name}' does not declare MC/DC")
    try:
        gate = check_version("mcdc", config.family, version_text)
    except VersionRequirementError as exc:
        return unavailable("mcdc_version_unknown", str(exc))
    if not gate.supported:
        return unavailable("mcdc_not_available", gate.message)
    return McdcPlan(
        available=True,
        reason=None,
        detail=gate.message,
        compiler_version=f"{gate.version[0]}.{gate.version[1]}",
        max_conditions=None if probe is None else probe.max_conditions,
        compile_flags=config.coverage_flags["mcdc"],
        gcov_flags=("--conditions",),
    )

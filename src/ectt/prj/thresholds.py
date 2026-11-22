# implements: TOOL-COV-130, TOOL-PRJ-040
"""Coverage threshold configuration in the project data format (B3).

A project may configure coverage thresholds (statements, branches) and the
allow_not_applicable list as an OPTIONAL ``coverage_thresholds`` section of
its document data; the section is absent from every project written before
this one, and an absent section simply means no thresholds (a no-op — the
existing file format is unchanged).

Minimums are stored as exact fraction strings (``numerator/denominator`` or
a plain integer) — never floats, in the data or in the file: a decimal or
exponent value is refused, because a stored threshold that only approximates
the intended fraction would silently shift the pass/fail boundary. Loading
produces :class:`ectt.cov.MetricThreshold` values ready for
``ectt.cov.thresholds.enforce_thresholds``.

Satisfies: TOOL-COV-130 (project-side configuration), TOOL-PRJ-040 (project
data format).
"""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import Any

from ectt.cov.thresholds import THRESHOLD_METRICS, MetricThreshold
from ectt.prj.errors import ProjectError

__all__ = [
    "CoverageThresholdConfig",
    "coverage_thresholds_from_data",
    "coverage_thresholds_to_data",
]

_SECTION = "coverage_thresholds"
_FRACTION_RE = re.compile(r"^(?P<num>\d+)(?:/(?P<den>\d+))?$")


@dataclass(frozen=True)
class CoverageThresholdConfig:
    """The parsed coverage-threshold section of one project."""

    thresholds: tuple[MetricThreshold, ...]
    allow_not_applicable: tuple[str, ...]


def coverage_thresholds_from_data(data: Mapping[str, Any]) -> CoverageThresholdConfig | None:
    """Load the coverage-threshold configuration from project data.

    Returns ``None`` when the section is absent (no thresholds configured —
    the no-op case every pre-existing project takes). A present section must
    configure at least one metric with exact fraction minimums; unknown
    metrics, float minimums and unknown allow_not_applicable entries are
    refused with named reasons.
    """
    if _SECTION not in data:
        return None
    section = data[_SECTION]
    if not isinstance(section, Mapping):
        raise ProjectError(
            f"project '{_SECTION}' section must be a mapping, got {type(section).__name__}",
            reason="invalid_threshold_section",
        )
    metrics_raw = section.get("metrics")
    if not isinstance(metrics_raw, Mapping):
        raise ProjectError(
            f"project '{_SECTION}' section requires a 'metrics' mapping",
            reason="invalid_threshold_section",
        )
    if not metrics_raw:
        raise ProjectError(
            f"a present '{_SECTION}' section must configure at least one metric",
            reason="empty_threshold_section",
        )
    thresholds: list[MetricThreshold] = []
    for metric, minimum in metrics_raw.items():
        if metric not in THRESHOLD_METRICS:
            raise ProjectError(
                f"unknown coverage metric '{metric}' in '{_SECTION}' "
                f"(known: {', '.join(THRESHOLD_METRICS)})",
                reason="unknown_threshold_metric",
            )
        if isinstance(minimum, (bool, float)):
            raise ProjectError(
                f"threshold minimum for '{metric}' must be an exact fraction string "
                f"(numerator/denominator or a plain integer), got float {minimum!r}",
                reason="float_threshold_minimum",
            )
        if not isinstance(minimum, str):
            raise ProjectError(
                f"threshold minimum for '{metric}' must be a string, got {type(minimum).__name__}",
                reason="invalid_threshold_minimum",
            )
        match = _FRACTION_RE.match(minimum.strip())
        if match is None or (match.group("den") is not None and int(match.group("den")) == 0):
            raise ProjectError(
                f"threshold minimum for '{metric}' must be 'numerator/denominator' or a "
                f"plain integer, got {minimum!r} (decimal and exponent forms are floats "
                f"in disguise and are refused)",
                reason="invalid_threshold_minimum",
            )
        thresholds.append(MetricThreshold(metric=metric, minimum=_exact_fraction(match)))

    # Deterministic regardless of file key order (the canonical YAML dump
    # sorts keys): thresholds load sorted by metric name.
    thresholds.sort(key=lambda t: t.metric)

    allow_raw = section.get("allow_not_applicable", ())
    if not isinstance(allow_raw, (list, tuple)):
        raise ProjectError(
            f"'{_SECTION}'.allow_not_applicable must be a list of metric names",
            reason="invalid_threshold_section",
        )
    allow: list[str] = []
    for metric in allow_raw:
        if metric not in THRESHOLD_METRICS:
            raise ProjectError(
                f"unknown coverage metric '{metric}' in allow_not_applicable "
                f"(known: {', '.join(THRESHOLD_METRICS)})",
                reason="unknown_threshold_metric",
            )
        allow.append(metric)
    return CoverageThresholdConfig(
        thresholds=tuple(thresholds),
        allow_not_applicable=tuple(allow),
    )


def _exact_fraction(match: re.Match[str]) -> Any:
    from fractions import Fraction

    num = int(match.group("num"))
    den = match.group("den")
    return Fraction(num, int(den)) if den is not None else Fraction(num, 1)


def coverage_thresholds_to_data(
    thresholds: Collection[MetricThreshold],
    allow_not_applicable: Collection[str] = (),
) -> dict[str, Any]:
    """Build the ``coverage_thresholds`` section for project data.

    Minimums are written as exact fraction strings; the caller merges the
    returned section into the project document data (a key the project format
    did not know before this section is purely additive).
    """
    metrics: dict[str, str] = {}
    for threshold in thresholds:
        metrics[threshold.metric] = (
            f"{threshold.minimum.numerator}/{threshold.minimum.denominator}"
        )
    return {
        "metrics": metrics,
        "allow_not_applicable": sorted(allow_not_applicable),
    }

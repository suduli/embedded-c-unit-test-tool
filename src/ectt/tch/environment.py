"""First-run environment verification (WP-TCH-07).

On first run the tool verifies its environment — toolchain presence and
feature availability — and reports clearly what is missing or unsupported.
Executable resolution is injectable so verification is testable without a
real toolchain; version facts are reported when declared, never by executing
a compiler here.

Satisfies: TOOL-INS-080.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "STATUS_OK",
    "STATUS_MISSING",
    "STATUS_UNSUPPORTED",
    "EnvironmentRequirement",
    "EnvironmentReport",
    "EnvironmentCheckResult",
    "verify_environment",
    "first_run_needed",
]

STATUS_OK = "ok"
STATUS_MISSING = "missing"
STATUS_UNSUPPORTED = "unsupported"

KIND_TOOLCHAIN = "toolchain"
KIND_FEATURE = "feature"


@dataclass(frozen=True)
class EnvironmentRequirement:
    """One thing the environment must provide.

    ``kind`` is ``toolchain`` (``target`` is an executable name, ``config`` the
    compiler configuration that needs it) or ``feature`` (``target`` is a
    feature name checked against the declared availability mapping).
    """

    kind: str
    target: str
    config: str = ""
    declared_version: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in (KIND_TOOLCHAIN, KIND_FEATURE):
            raise ValueError(f"unknown environment requirement kind '{self.kind}'")
        if not self.target.strip():
            raise ValueError("environment requirement target must not be empty")


@dataclass(frozen=True)
class EnvironmentCheckResult:
    """The verdict for one requirement."""

    requirement: EnvironmentRequirement
    status: str
    detail: str

    def render(self) -> str:
        """One clear line: target, status, detail."""
        prefix = f"{self.requirement.kind} {self.requirement.target}"
        if self.requirement.config:
            prefix += f" (config {self.requirement.config})"
        return f"{prefix}: {self.status} - {self.detail}"


@dataclass(frozen=True)
class EnvironmentReport:
    """The verdict for all requirements, deterministic and sorted."""

    results: tuple[EnvironmentCheckResult, ...]

    def render(self) -> str:
        """All result lines in deterministic order."""
        return "\n".join(result.render() for result in self.results)

    def missing_or_unsupported(self) -> tuple[EnvironmentCheckResult, ...]:
        """Results that are not ok, in report order."""
        return tuple(
            result for result in self.results if result.status != STATUS_OK
        )

    def to_dict(self) -> dict[str, list[dict[str, str]]]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "results": [
                {
                    "config": result.requirement.config,
                    "detail": result.detail,
                    "kind": result.requirement.kind,
                    "status": result.status,
                    "target": result.requirement.target,
                }
                for result in self.results
            ]
        }


def verify_environment(
    requirements: tuple[EnvironmentRequirement, ...],
    *,
    feature_availability: Mapping[str, bool] | None = None,
    executable_resolver: Callable[[str], str | None] | None = None,
) -> EnvironmentReport:
    """Verify every requirement and report what is missing or unsupported.

    ``executable_resolver`` defaults to a PATH lookup (``shutil.which``);
    tests inject a resolver so no real toolchain is needed.
    """
    features = feature_availability or {}
    resolve = executable_resolver if executable_resolver is not None else shutil.which
    results: list[EnvironmentCheckResult] = []
    for requirement in requirements:
        if requirement.kind == KIND_TOOLCHAIN:
            resolved = resolve(requirement.target)
            if resolved is None:
                results.append(
                    EnvironmentCheckResult(
                        requirement=requirement,
                        status=STATUS_MISSING,
                        detail=(
                            f"executable '{requirement.target}' was not found on PATH"
                        ),
                    )
                )
            else:
                version_note = (
                    f" (declared version {requirement.declared_version})"
                    if requirement.declared_version
                    else ""
                )
                results.append(
                    EnvironmentCheckResult(
                        requirement=requirement,
                        status=STATUS_OK,
                        detail=f"resolved to '{resolved}'{version_note}",
                    )
                )
        else:
            if requirement.target not in features:
                results.append(
                    EnvironmentCheckResult(
                        requirement=requirement,
                        status=STATUS_UNSUPPORTED,
                        detail=(
                            f"feature '{requirement.target}' is not declared "
                            f"available in this environment"
                        ),
                    )
                )
            elif features[requirement.target]:
                results.append(
                    EnvironmentCheckResult(
                        requirement=requirement,
                        status=STATUS_OK,
                        detail=f"feature '{requirement.target}' is available",
                    )
                )
            else:
                results.append(
                    EnvironmentCheckResult(
                        requirement=requirement,
                        status=STATUS_UNSUPPORTED,
                        detail=f"feature '{requirement.target}' is declared unavailable",
                    )
                )
    ordered = tuple(
        sorted(results, key=lambda r: (r.requirement.kind, r.requirement.target))
    )
    return EnvironmentReport(results=ordered)


def first_run_needed(marker_path: Path | str) -> bool:
    """Whether a first run is needed: the marker file is missing or unreadable."""
    marker = Path(marker_path)
    try:
        return not marker.is_file()
    except OSError:
        return True

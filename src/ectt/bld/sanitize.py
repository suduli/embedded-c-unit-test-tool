"""Sanitizer integration: opt-in flags and run-output findings (WP-BLD-02).

Sanitizers are never mandatory: the default settings enable nothing. When a
mode is requested, the module produces the documented GNU-style compile-and-
link flags and the runtime-options environment, and classifies sanitizer
diagnostics from captured run output into structured findings that can be
reported alongside — not instead of — the test verdict.

Satisfies: TOOL-EXE-090.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ectt.bld.errors import InvalidSanitizerModeError

__all__ = [
    "SANITIZER_NONE",
    "SANITIZER_ADDRESS",
    "SANITIZER_UNDEFINED",
    "KNOWN_SANITIZER_MODES",
    "SanitizerSettings",
    "SanitizerFinding",
    "sanitizer_compile_flags",
    "sanitizer_runtime_env",
    "classify_run_output",
]

SANITIZER_NONE = "none"
SANITIZER_ADDRESS = "address"
SANITIZER_UNDEFINED = "undefined"

KNOWN_SANITIZER_MODES = frozenset({SANITIZER_ADDRESS, SANITIZER_UNDEFINED})

# Diagnostic markers per sanitizer, matched against captured run output.
# AddressSanitizer/leak/thread markers all start "ERROR: <Name>:"; UBSan prints
# "runtime error:" per diagnostic and "SUMMARY: UndefinedBehaviorSanitizer" at
# the end.
_MARKER_RE = re.compile(
    r"ERROR:\s*(?P<asan>AddressSanitizer|LeakSanitizer|ThreadSanitizer):"
    r"|runtime error:"
    r"|SUMMARY:\s*(?P<summary>AddressSanitizer|LeakSanitizer|ThreadSanitizer|UndefinedBehaviorSanitizer)",
)


@dataclass(frozen=True)
class SanitizerSettings:
    """Requested sanitizer configuration. The default enables nothing."""

    modes: frozenset[str] = frozenset()
    halt_on_error: bool = True

    def __post_init__(self) -> None:
        unknown = self.modes - KNOWN_SANITIZER_MODES
        if unknown:
            raise InvalidSanitizerModeError(
                f"unknown sanitizer mode(s): {', '.join(sorted(unknown))} "
                f"(known: {', '.join(sorted(KNOWN_SANITIZER_MODES))})"
            )

    def to_dict(self) -> dict[str, object]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "halt_on_error": self.halt_on_error,
            "modes": sorted(self.modes),
        }


@dataclass(frozen=True)
class SanitizerFinding:
    """One sanitizer diagnostic recognised in captured run output."""

    sanitizer: str  # canonical kind name, e.g. "address", "undefined"
    summary: str  # the matching diagnostic line


def sanitizer_compile_flags(settings: SanitizerSettings) -> tuple[str, ...]:
    """Compile-and-link flags for the requested modes (GNU-style compilers).

    Empty settings produce no flags; both modes requested produce one merged
    ``-fsanitize=`` flag.
    """
    if not settings.modes:
        return ()
    return (f"-fsanitize={','.join(sorted(settings.modes))}",)


def sanitizer_runtime_env(settings: SanitizerSettings) -> dict[str, str]:
    """Runtime-options environment for the requested modes."""
    if not settings.modes:
        return {}
    env: dict[str, str] = {}
    if SANITIZER_ADDRESS in settings.modes:
        env["ASAN_OPTIONS"] = f"halt_on_error={1 if settings.halt_on_error else 0}"
    return env


def classify_run_output(output_text: str) -> tuple[SanitizerFinding, ...]:
    """Return sanitizer findings found in captured run output, in order.

    Detection is textual and per-line; a line may yield at most one finding.
    Output without sanitizer markers yields no findings.
    """
    findings: list[SanitizerFinding] = []
    for line in output_text.splitlines():
        match = _MARKER_RE.search(line)
        if match is None:
            continue
        if match.group("asan"):
            sanitizer = match.group("asan").replace("AddressSanitizer", "address").replace(
                "LeakSanitizer", "address"
            ).replace("ThreadSanitizer", "thread")
        elif match.group("summary"):
            sanitizer = (
                match.group("summary")
                .replace("AddressSanitizer", "address")
                .replace("LeakSanitizer", "address")
                .replace("ThreadSanitizer", "thread")
                .replace("UndefinedBehaviorSanitizer", "undefined")
            )
        else:
            sanitizer = "undefined"
        findings.append(SanitizerFinding(sanitizer=sanitizer, summary=line.strip()))
    return tuple(findings)

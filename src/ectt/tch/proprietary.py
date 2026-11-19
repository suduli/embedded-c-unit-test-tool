"""Proprietary compiler support through the configuration mechanism (WP-TCH-06).

Proprietary compilers (Keil armcc/armclang, IAR, TASKING, Green Hills) are
supported where their invocation is externally scriptable: the support
mechanism is the public schema-version-1 configuration path, and this module
documents the proprietary family roster with per-family scriptability notes.

Satisfies: TOOL-TCH-100.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ectt.tch.errors import TchError

__all__ = [
    "PROPRIETARY_FAMILIES",
    "ProprietaryFamily",
    "proprietary_families",
    "ProprietaryConfigError",
]

_ARMCC_YAML_EXAMPLE = """\
schema_version: 1
name: keil-armclang
family: armclang
invocation:
  executable: armclang
  compile_only_flag: "-c"
  output_flag: "-o"
flags:
  debug: ["-g"]
  optimization:
    none: ["-O0"]
    size: ["-Oz"]
    speed: ["-O2"]
output:
  object_suffix: ".o"
  executable_suffix: ".axf"
coverage:
  kinds: [line]
  flags:
    line: ["--coverage"]
"""


class ProprietaryConfigError(TchError):
    """Raised when proprietary family documentation data is malformed."""

    def __init__(self, message: str, *, reason: str = "proprietary_config_error") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class ProprietaryFamily:
    """One proprietary compiler family, documented for external scriptability."""

    family: str
    compilers: tuple[str, ...]
    externally_scriptable: bool
    note: str

    def to_dict(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "compilers": list(self.compilers),
            "externally_scriptable": self.externally_scriptable,
            "family": self.family,
            "note": self.note,
        }


_FAMILIES: tuple[ProprietaryFamily, ...] = (
    ProprietaryFamily(
        family="armcc",
        compilers=("armcc",),
        externally_scriptable=True,
        note="classic Keil armcc driver is externally scriptable (command-line driven)",
    ),
    ProprietaryFamily(
        family="armclang",
        compilers=("armclang",),
        externally_scriptable=True,
        note="Keil armclang is LLVM-based and command-line driven",
    ),
    ProprietaryFamily(
        family="iar",
        compilers=("iccarm", "iarbuild"),
        externally_scriptable=True,
        note="IAR iccarm is externally scriptable; project builds go through iarbuild",
    ),
    ProprietaryFamily(
        family="tasking",
        compilers=("cctc",),
        externally_scriptable=True,
        note="TASKING compiler driver is externally scriptable",
    ),
    ProprietaryFamily(
        family="greenhills",
        compilers=("ccarm", "ghs"),
        externally_scriptable=True,
        note="Green Hills compilers are externally scriptable via their drivers",
    ),
)


def proprietary_families() -> tuple[ProprietaryFamily, ...]:
    """The documented proprietary family roster, deterministic on every call."""
    return _FAMILIES


PROPRIETARY_FAMILIES: frozenset[str] = frozenset(item.family for item in _FAMILIES)

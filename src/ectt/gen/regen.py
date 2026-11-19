"""Regeneration contract and conflict reporting (WP-GEN-04).

User edits live in designated user regions of the generated harness. The
regeneration contract: when the interface fingerprint recorded in the existing
harness matches the freshly generated one, the user-region contents are
preserved byte-for-byte; when the UUT signature changed incompatibly, the
conflict is reported with the offending signatures and nothing is written.

Satisfies: TOOL-HAR-090, TOOL-HAR-100, TOOL-HAR-110, TOOL-CBT-070.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ectt.gen.errors import GenError
from ectt.gen.harness import GeneratedHarness

__all__ = [
    "STATUS_PRESERVED",
    "STATUS_CONFLICT",
    "HarnessRegenerationConflictError",
    "RegenerationResult",
    "TestInterfaceBinding",
    "check_harness_staleness",
    "check_test_case_staleness",
    "regenerate",
    "apply_regeneration",
]

STATUS_PRESERVED: Final[str] = "preserved"
STATUS_CONFLICT: Final[str] = "conflict"

_REGION_RE: Final[re.Pattern[str]] = re.compile(
    r"/\* ectt:user-region: (?P<name>\S+) begin \*/\n"
    r"(?P<content>.*?)"
    r"/\* ectt:user-region: (?P=name) end \*/",
    re.DOTALL,
)

_FINGERPRINT_RE: Final[re.Pattern[str]] = re.compile(
    r"Interface fingerprint: ([0-9a-f]+)"
)


class HarnessRegenerationConflictError(GenError):
    """Raised when a conflicting regeneration is applied (nothing was written)."""

    def __init__(
        self, message: str, *, reason: str = "harness_regeneration_conflict"
    ) -> None:
        super().__init__(message, reason=reason)


def _fingerprint_of(harness: GeneratedHarness) -> str:
    if not harness.interface_fingerprint:
        raise GenError("harness carries no interface fingerprint; regenerate it first")
    return harness.interface_fingerprint


def _extract_fingerprint(text: str) -> str:
    match = _FINGERPRINT_RE.search(text)
    if match is None:
        raise GenError(
            "existing harness text has no interface fingerprint in its header"
        )
    return match.group(1)


def _extract_regions(text: str) -> dict[str, str]:
    return {
        match.group("name"): match.group("content")
        for match in _REGION_RE.finditer(text)
    }


def _signature_of(harness: GeneratedHarness) -> dict[str, str]:
    signatures: dict[str, str] = {}
    for function in harness.functions:
        parameters = ", ".join(
            f"{ptype} {pname}" for ptype, pname in function.parameters
        )
        signatures[f"function:{function.name}"] = (
            f"{function.return_type} {function.name}({parameters or 'void'})"
        )
    for variable in harness.variables:
        signatures[f"variable:{variable.name}"] = f"{variable.access} {variable.name}"
    return signatures


@dataclass(frozen=True)
class RegenerationResult:
    """The outcome of one regeneration attempt."""

    status: str
    text: str | None  # None when conflicting: nothing to write
    conflicts: tuple[str, ...]

    @property
    def written_anything(self) -> bool:
        """Whether applying this result would write a file."""
        return self.text is not None


def regenerate(old_text: str, harness: GeneratedHarness) -> RegenerationResult:
    """Apply the regeneration contract to an existing harness text.

    Interface unchanged: the user-region contents of the old text are
    preserved byte-for-byte inside the regenerated output. Interface changed:
    the result is a conflict report naming every added, removed and changed
    signature, with ``text=None``.
    """
    old_fingerprint = _extract_fingerprint(old_text)
    new_fingerprint = _fingerprint_of(harness)
    if old_fingerprint == new_fingerprint:
        regions = _extract_regions(old_text)
        text = harness.source
        dropped: list[str] = []
        for name, content in regions.items():
            empty_block = (
                f"/* ectt:user-region: {name} begin */\n"
                f"/* ectt:user-region: {name} end */"
            )
            filled_block = (
                f"/* ectt:user-region: {name} begin */\n"
                f"{content}"
                f"/* ectt:user-region: {name} end */"
            )
            # A region with no slot in the regenerated source would lose the
            # user's content silently, so it is a conflict, not a success.
            if empty_block not in text:
                dropped.append(f"user region dropped: {name}")
                continue
            text = text.replace(empty_block, filled_block)
        if dropped:
            return RegenerationResult(
                status=STATUS_CONFLICT, text=None, conflicts=tuple(dropped)
            )
        return RegenerationResult(status=STATUS_PRESERVED, text=text, conflicts=())
    return RegenerationResult(
        status=STATUS_CONFLICT,
        text=None,
        conflicts=_conflicts(old_text, harness),
    )


def _conflicts(old_text: str, harness: GeneratedHarness) -> tuple[str, ...]:
    """Name every added, removed and changed signature between old and new."""
    old_block: dict[str, str] = {}
    for match in re.finditer(r"/\* exposes: (.+?) \*/", old_text):
        signature = match.group(1)
        name = signature.split("(")[0].split(" ")[-1]
        old_block[f"function:{name}"] = signature
    for match in re.finditer(r"/\* ectt:exposes-global: (\S+) (\S+) \*/", old_text):
        old_block[f"variable:{match.group(1)}"] = f"{match.group(2)} {match.group(1)}"
    new_block = _signature_of(harness)
    conflicts: list[str] = []
    for key in sorted(set(old_block) | set(new_block)):
        if key not in new_block:
            conflicts.append(f"removed: {old_block[key]}")
        elif key not in old_block:
            conflicts.append(f"added: {new_block[key]}")
        elif old_block[key] != new_block[key]:
            conflicts.append(f"changed: {old_block[key]} -> {new_block[key]}")
    return tuple(conflicts)


def apply_regeneration(path: Path | str, result: RegenerationResult) -> None:
    """Write a preserved regeneration; refuse to write a conflicting one."""
    if result.status == STATUS_CONFLICT or result.text is None:
        raise HarnessRegenerationConflictError(
            "regeneration conflict reported; nothing written: "
            + "; ".join(result.conflicts)
        )
    Path(path).write_text(result.text, encoding="utf-8")


@dataclass(frozen=True)
class TestInterfaceBinding:
    """The interface fingerprint a test case was authored against (TOOL-CBT-070)."""

    case_id: str
    interface_fingerprint: str


@dataclass(frozen=True)
class HarnessStaleness:
    """Staleness verdict with reasons (TOOL-HAR-110 / TOOL-CBT-070)."""

    stale: bool
    reasons: tuple[str, ...]


def check_harness_staleness(
    old_text: str, harness: GeneratedHarness
) -> HarnessStaleness:
    """Whether the existing harness is stale relative to the current interface."""
    try:
        old_fingerprint = _extract_fingerprint(old_text)
    except GenError:
        return HarnessStaleness(
            stale=True,
            reasons=("existing harness carries no interface fingerprint",),
        )
    if old_fingerprint != _fingerprint_of(harness):
        return HarnessStaleness(
            stale=True,
            reasons=("interface fingerprint changed", *_conflicts(old_text, harness)),
        )
    return HarnessStaleness(stale=False, reasons=())


def check_test_case_staleness(
    binding: TestInterfaceBinding, harness: GeneratedHarness
) -> HarnessStaleness:
    """Whether a test case is stale because the interface it exercises changed."""
    if binding.interface_fingerprint != _fingerprint_of(harness):
        return HarnessStaleness(
            stale=True,
            reasons=("interface fingerprint changed since the test case was authored",),
        )
    return HarnessStaleness(stale=False, reasons=())

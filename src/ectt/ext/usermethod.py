"""User-supplied target execution methods (WP-EXT-07).

An execution method is addable through a documented interface and a
user-supplied script: a declarative descriptor (method id, script path, a
command template with {target} and {harness} slots) registered into a public
registry. Plans compose the script invocation — the script content itself is
never executed at plan time, which supports targets without a debug probe.

Satisfies: TOOL-PLG-040, TOOL-TGT-120.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ectt.ext.errors import ExtError

__all__ = [
    "ExecutionMethodDescriptor",
    "ExecutionMethodPlan",
    "MethodRegistry",
    "DuplicateMethodError",
    "UnknownMethodError",
    "plan_user_execution",
]


class DuplicateMethodError(ExtError):
    """Raised when an execution-method id is registered twice."""

    def __init__(self, message: str, *, reason: str = "duplicate_method") -> None:
        super().__init__(message, reason=reason)


class UnknownMethodError(ExtError):
    """Raised when an execution-method lookup or plan names an unknown method."""

    def __init__(self, message: str, *, reason: str = "unknown_method") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class ExecutionMethodDescriptor:
    """One user-supplied execution method: a documented interface plus a script."""

    method_id: str
    script_path: str
    command_template: str  # must contain {script}, {target} and {harness}

    def __post_init__(self) -> None:
        if not isinstance(self.method_id, str) or not self.method_id.strip():
            raise UnknownMethodError("execution method id must be a non-empty string")
        if not isinstance(self.script_path, str) or not self.script_path.strip():
            raise UnknownMethodError(
                f"method '{self.method_id}' requires a non-empty script path"
            )
        for slot in ("{script}", "{target}", "{harness}"):
            if slot not in self.command_template:
                raise UnknownMethodError(
                    f"method '{self.method_id}' command template must include "
                    f"{slot} (documented interface slots)"
                )

    def to_dict(self) -> dict[str, str]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "command_template": self.command_template,
            "method_id": self.method_id,
            "script_path": self.script_path,
        }


@dataclass(frozen=True)
class ExecutionMethodPlan:
    """The composed invocation of one user execution method."""

    method_id: str
    target: str
    harness: str
    command_line: str

    def to_dict(self) -> dict[str, str]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "command_line": self.command_line,
            "harness": self.harness,
            "method_id": self.method_id,
            "target": self.target,
        }


class MethodRegistry:
    """Public registry of user-supplied execution methods."""

    def __init__(self) -> None:
        self._methods: dict[str, ExecutionMethodDescriptor] = {}

    def register(self, descriptor: ExecutionMethodDescriptor) -> None:
        """Register a method descriptor; reject a reused id."""
        if descriptor.method_id in self._methods:
            raise DuplicateMethodError(
                f"execution method '{descriptor.method_id}' is already registered"
            )
        self._methods[descriptor.method_id] = descriptor

    def lookup(self, method_id: str) -> ExecutionMethodDescriptor:
        """The descriptor registered under ``method_id``."""
        try:
            return self._methods[method_id]
        except KeyError:
            raise UnknownMethodError(
                f"no execution method is registered under '{method_id}'"
            ) from None

    def list_ids(self) -> tuple[str, ...]:
        """Registered method ids, ordered deterministically."""
        return tuple(sorted(self._methods))


def plan_user_execution(
    method_id: str,
    registry: MethodRegistry,
    *,
    target: str,
    harness: str,
) -> ExecutionMethodPlan:
    """Compose the script invocation for one target/harness (TOOL-TGT-120).

    The script content is never executed here — plan time only composes the
    command line from the descriptor's documented template slots.
    """
    descriptor = registry.lookup(method_id)
    if not target.strip() or not harness.strip():
        raise UnknownMethodError(
            f"method '{method_id}' requires a non-empty target and harness"
        )
    command_line = (
        descriptor.command_template.replace(
            "{script}", Path(descriptor.script_path).as_posix()
        )
        .replace("{target}", target)
        .replace("{harness}", harness)
    )
    return ExecutionMethodPlan(
        method_id=descriptor.method_id,
        target=target,
        harness=harness,
        command_line=command_line,
    )

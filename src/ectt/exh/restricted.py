# implements: TOOL-EXE-010, TOOL-EXE-030
"""Restricted execution context for starting a generated harness (WP-SEC-06).

Hardens the host execution of TOOL-EXE-010/030: a restricted context confines
the working directory (resolved inside the project root), scrubs the
environment (only an explicit allow-list passes, values taken from the
machine's environment; an allow-listed name absent from the machine is
omitted, never invented), closes inherited handles (``inherit_handles`` is
always False — a security property, not an option), and carries a wall-clock
limit and an output size limit.

Every refusal — a working directory that escapes the project root
(``path_escape``), non-positive limits or an empty allow-list
(``invalid_limit``/``empty_allow_list``) — is raised **before** the starter is
invoked: a refused context starts nothing.

The run goes through an injected starter. The production starter wraps
``subprocess.run`` with ``cwd``, the scrubbed ``env``, ``close_fds=True`` and
the wall-clock limit as the timeout; tests inject a fake that records exactly
what it was given (there is no C compiler, debugger or simulator on this
machine — verification is by fake callables and golden text, and no test
starts a real process). The result records both limits, the captured output
truncated to the output limit (``stdout_truncated=True`` when the limit
binds), and ``timed_out=True`` when the starter reports the wall-clock limit
as exceeded.

Satisfies: TOOL-EXE-010, TOOL-EXE-030 (restricted-launch discipline).
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ectt.exh.errors import ExhError

__all__ = [
    "WallClockExceeded",
    "RestrictedContext",
    "RestrictedRunResult",
    "build_context",
    "default_starter",
    "run_restricted",
]


class WallClockExceeded(ExhError):
    """The starter reported the wall-clock limit as exceeded."""

    def __init__(self, message: str, *, reason: str = "wall_clock_exceeded") -> None:
        super().__init__(message, reason=reason)


class RestrictedContextError(ExhError):
    """A restricted context was refused; nothing is started."""

    def __init__(self, message: str, *, reason: str = "restricted_context_refused") -> None:
        super().__init__(message, reason=reason)


class Starter(Protocol):
    """The injected process starter; production wraps ``subprocess.run``."""

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: str,
        env: Mapping[str, str],
        timeout_seconds: float,
        close_fds: bool,
    ) -> Any: ...


@dataclass(frozen=True)
class RestrictedContext:
    """The confined launch parameters of one restricted run (WP-SEC-06)."""

    working_directory: str  # absolute, resolved inside the project root
    environment: Mapping[str, str]  # only the allow-listed names, scrubbed
    wall_clock_limit_s: float
    output_limit_bytes: int
    inherit_handles: bool = False  # always False: not an option

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment_keys": sorted(self.environment),
            "inherit_handles": self.inherit_handles,
            "output_limit_bytes": self.output_limit_bytes,
            "wall_clock_limit_s": self.wall_clock_limit_s,
            "working_directory": self.working_directory,
        }


@dataclass(frozen=True)
class RestrictedRunResult:
    """What one restricted run did, with its context and limits recorded."""

    context: RestrictedContext
    exit_status: int | None
    stdout: str
    stdout_truncated: bool
    timed_out: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.to_dict(),
            "exit_status": self.exit_status,
            "stdout_truncated": self.stdout_truncated,
            "timed_out": self.timed_out,
        }


def build_context(
    *,
    root: Path | str,
    working_directory: Path | str,
    environment_allow: Iterable[str],
    machine_environment: Mapping[str, str],
    wall_clock_limit_s: float,
    output_limit_bytes: int,
) -> RestrictedContext:
    """Build the restricted context, refusing before anything can run.

    ``working_directory`` must resolve inside ``root`` (``path_escape``
    otherwise). Only the allow-listed names pass from
    ``machine_environment``; an allow-listed name the machine does not have is
    omitted, never invented. Both limits must be positive and the allow-list
    must not be empty. A refusal raises before the starter is ever invoked.
    """
    root_resolved = Path(root).resolve()
    working_resolved = Path(working_directory).resolve()
    if not working_resolved.is_relative_to(root_resolved):
        raise RestrictedContextError(
            f"the restricted working directory {str(working_directory)!r} escapes "
            f"the project root {str(root)!r}",
            reason="path_escape",
        )
    if wall_clock_limit_s <= 0:
        raise RestrictedContextError(
            f"the wall-clock limit must be positive, got {wall_clock_limit_s}",
            reason="invalid_limit",
        )
    if output_limit_bytes <= 0:
        raise RestrictedContextError(
            f"the output limit must be positive, got {output_limit_bytes}",
            reason="invalid_limit",
        )
    allowed = [name for name in environment_allow if _is_name(name)]
    if not allowed:
        raise RestrictedContextError(
            "the environment allow-list is empty; a restricted run passes no environment at all",
            reason="empty_allow_list",
        )
    scrubbed = {name: machine_environment[name] for name in sorted(allowed) if name in machine_environment}
    return RestrictedContext(
        working_directory=str(working_resolved),
        environment=scrubbed,
        wall_clock_limit_s=wall_clock_limit_s,
        output_limit_bytes=output_limit_bytes,
        inherit_handles=False,
    )


def _is_name(name: str) -> bool:
    return bool(name) and "=" not in name and "\x00" not in name


def default_starter(
    argv: Sequence[str],
    *,
    cwd: str,
    env: Mapping[str, str],
    timeout_seconds: float,
    close_fds: bool,
) -> Any:
    """The production starter: a direct, confined ``subprocess.run``."""
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=dict(env),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
        close_fds=close_fds,
    )


@dataclass(frozen=True)
class _Completed:
    stdout: str
    returncode: int | None


def run_restricted(
    context: RestrictedContext,
    argv: Sequence[str],
    *,
    starter: Starter,
) -> RestrictedRunResult:
    """Start the harness under the restricted context and record everything.

    The starter receives exactly the context's confinement: the confined
    working directory, the scrubbed environment, the wall-clock limit as the
    timeout and ``close_fds=True`` (handles are never inherited). The captured
    output is truncated to the context's output limit with
    ``stdout_truncated=True`` when the limit binds; a starter that reports the
    wall-clock limit as exceeded (``WallClockExceeded``) yields
    ``timed_out=True`` with no exit status.
    """
    timed_out = False
    exit_status: int | None = None
    stdout = ""
    try:
        completed = starter(
            list(argv),
            cwd=context.working_directory,
            env=context.environment,
            timeout_seconds=context.wall_clock_limit_s,
            close_fds=True,
        )
        stdout = completed.stdout or ""
        exit_status = completed.returncode
    except WallClockExceeded:
        timed_out = True

    encoded_length = len(stdout.encode("utf-8", errors="replace"))
    truncated = encoded_length > context.output_limit_bytes
    if truncated:
        stdout = stdout.encode("utf-8", errors="replace")[: context.output_limit_bytes].decode(
            "utf-8", errors="ignore"
        )
    return RestrictedRunResult(
        context=context,
        exit_status=exit_status,
        stdout=stdout,
        stdout_truncated=truncated,
        timed_out=timed_out,
    )

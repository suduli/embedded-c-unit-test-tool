# implements: TOOL-EXE-070
"""Debugger launch with an entry breakpoint (WP-EXH-04).

TOOL-EXE-070: the tool shall support launching a test case under a debugger,
with the harness prepared and execution stopped at entry to the function
under test.

:func:`build_debugger_launch` constructs the gdb command line — gdb first,
with ``break <function>`` so execution stops at the test function's entry,
the harness as the debuggee and the arguments the normal run uses (for
example ``--ectt-select``). The working directory travels beside the argv, as
the normal run's cwd does. Every refusal names its reason, in order, before
anything can start: ``debugger_not_named``, ``no_symbols`` (a build without
recorded debug symbols cannot step), ``harness_not_built``.

Starting the debugger is behind an injected starter: the builder only
constructs; :func:`start_debugger` hands the argv and the working directory
to the starter. Tests use a recording fake — there is no C compiler, debugger
or simulator on this machine, so verification is by golden text and fake
callables, and no test starts a real process.

The argv is the execution contract (paths with spaces survive as single
elements); the display form (:meth:`DebugLaunch.command_line`) quotes them.

Satisfies: TOOL-EXE-070.
"""

from __future__ import annotations

import shlex
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ectt.exh.errors import ExhError

__all__ = ["DebugLaunch", "build_debugger_launch", "start_debugger"]

#: The first debugger the tool builds a command line for.
DEBUGGER_GDB = "gdb"


class DebuggerLaunchError(ExhError):
    """A debugger launch was refused; ``reason`` names why."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "debugger_launch_refused",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


@dataclass(frozen=True)
class DebugLaunch:
    """The prepared debugger launch: argv, working directory, breakpoint."""

    debugger: str
    argv: tuple[str, ...]
    working_directory: str
    breakpoint: str

    def command_line(self) -> str:
        """The display form: shell-quoted, safe for paths with spaces."""
        return shlex.join(self.argv)


def build_debugger_launch(
    *,
    debugger: str | None,
    harness: Path | str,
    test_function: str,
    symbols_recorded: bool,
    working_directory: Path | str,
    args: Sequence[str] = (),
) -> DebugLaunch:
    """Construct the gdb launch, refusing before anything can start.

    The refusals, in order: ``debugger_not_named`` (no debugger given),
    ``no_symbols`` (the build did not record debug symbols — stepping through
    the function under test needs them), ``harness_not_built`` (the harness
    file does not exist). On success the argv is deterministic: the debugger,
    the entry breakpoint, then ``--args`` with the harness and the normal
    run's arguments.
    """
    if debugger is None or not debugger.strip():
        raise DebuggerLaunchError(
            "no debugger was named for the launch", reason="debugger_not_named"
        )
    if not symbols_recorded:
        raise DebuggerLaunchError(
            "the build recorded no debug symbols; the debugger cannot step the "
            "function under test",
            reason="no_symbols",
        )
    harness_path = Path(harness)
    if not harness_path.is_file():
        raise DebuggerLaunchError(
            f"the harness '{harness}' is not built (no such file)",
            reason="harness_not_built",
            path=harness_path,
        )
    if not test_function.strip():
        raise DebuggerLaunchError(
            "the entry breakpoint needs the function under test",
            reason="no_breakpoint_function",
        )
    breakpoint = f"break {test_function.strip()}"
    argv = (debugger.strip(), "-ex", breakpoint, "--args", str(harness_path), *args)
    return DebugLaunch(
        debugger=debugger.strip(),
        argv=argv,
        working_directory=str(working_directory),
        breakpoint=breakpoint,
    )


def start_debugger(launch: DebugLaunch, *, starter: Any) -> Any:
    """Hand the prepared launch to the injected starter (nothing else starts).

    The starter receives the argv and the working directory exactly as built.
    The production starter would spawn the debugger interactively; tests pass
    a recording fake, because no debugger exists on this machine.
    """
    return starter(list(launch.argv), cwd=launch.working_directory)

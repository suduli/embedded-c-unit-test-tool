"""Dispatch layer for the ectt CLI (WP-CLI-01).

Maps a parsed catalogue command onto the executor registered for it. The
registry is filled by the packages that implement each engine operation;
a catalogue operation without an executor in this build fails safe — the
error is reported and the process exits non-zero, never faking success
(TOOL-NFR-090).

Satisfies: TOOL-CIC-010, TOOL-CIC-020.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from typing import TextIO

from ectt.api.catalogue import Catalogue, default_catalogue
from ectt.cli.errors import CliError, OperationNotAvailable
from ectt.cli.exit_codes import EXIT_TOOL_ERROR, EXIT_USAGE, exit_code_for_category
from ectt.cli.generator import build_parser, command_names
from ectt.core.errors import EcttError

__all__ = [
    "Dispatcher",
    "OperationNotAvailable",
    "run",
]

#: Handler signature: receives the parsed argparse namespace.
Handler = Callable[[argparse.Namespace], int]

#: Exit code for an operation the build cannot execute yet: a tool error
#: (TOOL-CIC-030 table in ``ectt.cli.exit_codes``).
EXIT_OPERATION_NOT_AVAILABLE = EXIT_TOOL_ERROR


class Dispatcher:
    """Registry of executors for catalogue operations."""

    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register(self, operation: str, handler: Handler) -> None:
        """Wire ``handler`` as the executor of catalogue operation ``operation``."""
        if operation in self._handlers:
            raise CliError(
                f"handler already registered for operation: {operation}",
                reason="duplicate_handler",
            )
        self._handlers[operation] = handler

    def has(self, operation: str) -> bool:
        """Return whether ``operation`` has an executor wired."""
        return operation in self._handlers

    def dispatch(self, namespace: argparse.Namespace) -> int:
        """Execute the parsed command, refusing unwired operations fail-safe."""
        operation = getattr(namespace, "operation", None)
        if operation is None:
            raise CliError("no operation given", reason="no_operation")
        handler = self._handlers.get(operation)
        if handler is None:
            raise OperationNotAvailable(
                f"operation is published in the catalogue but has no executor "
                f"in this build: {operation}",
                operation=operation,
            )
        return handler(namespace)


def run(
    argv: list[str] | None = None,
    *,
    catalogue: Catalogue | None = None,
    dispatcher: Dispatcher | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run one non-interactive CLI invocation and return the exit code.

    ``stdout``/``stderr`` default to the process streams so the CLI operates
    on plain stdio with no display server (TOOL-CIC-020).
    """
    catalogue = catalogue if catalogue is not None else default_catalogue()
    dispatcher = dispatcher if dispatcher is not None else Dispatcher()
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr

    parser = build_parser(catalogue)
    namespace = parser.parse_args(argv)

    if namespace.list_commands:
        for name in command_names(catalogue):
            print(name, file=stdout)
        return 0

    if getattr(namespace, "operation", None) is None:
        parser.print_help(stderr)
        return EXIT_USAGE

    try:
        return dispatcher.dispatch(namespace)
    except EcttError as exc:
        # Every ectt exception category maps onto the stable documented
        # table (TOOL-CIC-030); the error is reported and the process exits
        # non-zero, never faking success (TOOL-NFR-090, WP-CORE-02).
        print(f"ectt: error: {exc}", file=stderr)
        return exit_code_for_category(exc.category)

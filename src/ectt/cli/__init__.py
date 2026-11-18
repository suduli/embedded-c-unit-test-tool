"""Non-interactive CLI generated from the engine operation catalogue (WP-CLI-01).

The CLI has no hand-written command list: subcommands come from the same
catalogue the engine API publishes (DSN-CLI-010, SDD-002 §9.3), so a
capability cannot become GUI-only by omission (TOOL-UIX-010) and every
automated-verification capability is reachable non-interactively
(TOOL-CIC-010). No module here imports a GUI toolkit — the CLI operates
without a graphical environment or display server (TOOL-CIC-020).

Satisfies: TOOL-CIC-010, TOOL-CIC-020.
Design: SDD-002 §9.3 (one operation catalogue).
"""

from __future__ import annotations

from ectt.cli.dispatch import Dispatcher, OperationNotAvailable, run
from ectt.cli.errors import CliError
from ectt.cli.generator import build_parser, command_names

__all__ = [
    "CliError",
    "Dispatcher",
    "OperationNotAvailable",
    "build_parser",
    "command_names",
    "run",
]

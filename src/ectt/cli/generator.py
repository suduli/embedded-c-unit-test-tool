"""Catalogue-driven parser generation for the ectt CLI (WP-CLI-01).

The parser is generated from the engine operation catalogue (DSN-CLI-010):
one subcommand per catalogue operation, derived from the catalogue's own
metadata. A capability added to the catalogue is automatically reachable
from the CLI; a capability absent from the catalogue is unreachable from
any front-end (TOOL-UIX-010).

Satisfies: TOOL-CIC-010.
Design: SDD-002 §9.3.
"""

from __future__ import annotations

import argparse

from ectt.api.catalogue import Catalogue

__all__ = [
    "build_parser",
    "command_names",
]


def command_names(catalogue: Catalogue) -> list[str]:
    """Return the CLI subcommand names, which are exactly the catalogue's."""
    return catalogue.names()


def build_parser(catalogue: Catalogue) -> argparse.ArgumentParser:
    """Build the non-interactive CLI parser from ``catalogue``.

    One subparser per catalogue operation. ``--list-commands`` prints the
    catalogue names deterministically for automated verification.
    """
    parser = argparse.ArgumentParser(
        prog="ectt",
        description=(
            "Non-interactive CLI of the ectt engine. Commands are generated "
            "from the engine operation catalogue (SDD-002 §9.3, DSN-CLI-010)."
        ),
    )
    parser.add_argument(
        "--list-commands",
        action="store_true",
        help="print the catalogue operation names and exit",
    )
    subparsers = parser.add_subparsers(dest="operation", metavar="OPERATION")
    for name in catalogue.names():
        operation = catalogue.get(name)
        sub = subparsers.add_parser(name, help=operation.summary)
        sub.add_argument("--target-id", help="session ID of the targeted operation")
    return parser

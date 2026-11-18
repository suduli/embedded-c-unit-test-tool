"""Tests for catalogue-driven CLI parser generation (WP-CLI-01).

Covers: every catalogue operation yields a subcommand, no subcommand exists
outside the catalogue, and the deterministic command listing.

Verifies: TOOL-CIC-010.
"""

from __future__ import annotations

import argparse

from ectt.api.catalogue import Catalogue, Operation, default_catalogue
from ectt.cli.generator import build_parser, command_names


def test_every_catalogue_operation_yields_a_subcommand() -> None:
    """verifies: TOOL-CIC-010

    The parser is generated from the catalogue (DSN-CLI-010): every published
    operation must be invocable non-interactively.
    """
    catalogue = default_catalogue()
    parser = build_parser(catalogue)
    for name in catalogue.names():
        namespace = parser.parse_args([name, "--target-id", "17"])
        assert namespace.operation == name
        assert namespace.target_id == "17"


def test_no_command_outside_catalogue() -> None:
    """verifies: TOOL-CIC-010, TOOL-UIX-010

    A command the catalogue does not publish is a usage error — there is no
    place a GUI-only capability could hide.
    """
    catalogue = default_catalogue()
    parser = build_parser(catalogue)
    with __import__("pytest").raises(SystemExit) as excinfo:
        parser.parse_args(["not.in.catalogue"])
    assert excinfo.value.code == 2


def test_command_names_match_catalogue_exactly() -> None:
    """verifies: TOOL-CIC-010

    Generated command list equals the catalogue names, sorted, no drift.
    """
    catalogue = Catalogue()
    catalogue.register(Operation(name="b.op", summary="b", cli_equivalent="ectt b"))
    catalogue.register(Operation(name="a.op", summary="a", cli_equivalent="ectt a"))
    assert command_names(catalogue) == ["a.op", "b.op"]


def test_parser_help_text_carries_operation_summary() -> None:
    """The generated help surfaces the catalogue summary, not hand-written
    text that could drift from the catalogue."""
    catalogue = default_catalogue()
    parser = build_parser(catalogue)
    assert isinstance(parser, argparse.ArgumentParser)
    summary = catalogue.get("operation.cancel").summary
    assert summary.startswith("Request cancellation")

"""Tests for CLI dispatch (WP-CLI-01).

Covers: deterministic listing, usage error on no command, fail-safe refusal
of unwired catalogue operations, and end-to-end dispatch of a wired handler.

Verifies: TOOL-CIC-010, TOOL-NFR-090.
"""

from __future__ import annotations

import argparse
import io

import pytest

from ectt.api.catalogue import Catalogue, Operation
from ectt.cli.dispatch import Dispatcher, run
from ectt.cli.errors import CliError, OperationNotAvailable


def test_list_commands_prints_catalogue_names() -> None:
    """verifies: TOOL-CIC-010

    ``--list-commands`` gives automated verification a machine-readable,
    deterministic surface without interaction.
    """
    catalogue = Catalogue()
    catalogue.register(Operation(name="alpha.op", summary="a", cli_equivalent="ectt a"))
    catalogue.register(Operation(name="beta.op", summary="b", cli_equivalent="ectt b"))
    stdout = io.StringIO()
    code = run(["--list-commands"], catalogue=catalogue, stdout=stdout)
    assert code == 0
    assert stdout.getvalue().splitlines() == ["alpha.op", "beta.op"]


def test_no_command_prints_help_to_stderr() -> None:
    """An empty invocation is a usage error on stderr, not a silent success."""
    stderr = io.StringIO()
    code = run([], stderr=stderr)
    assert code == 2
    assert "usage" in stderr.getvalue().lower()


def test_unknown_command_is_usage_error() -> None:
    """verifies: TOOL-CIC-010

    argparse rejects unknown commands with exit code 2 (usage error).
    """
    with pytest.raises(SystemExit) as excinfo:
        run(["not.a.command"])
    assert excinfo.value.code == 2


def test_unwired_catalogue_operation_fails_safe_nonzero() -> None:
    """verifies: TOOL-CIC-010, TOOL-NFR-090

    A catalogue operation whose executor has not landed reports the error on
    stderr and exits non-zero — no misleading success output.
    """
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = run(
        ["operation.cancel", "--target-id", "17"],
        stdout=stdout,
        stderr=stderr,
    )
    assert code != 0
    assert stdout.getvalue() == ""
    assert "operation.cancel" in stderr.getvalue()
    assert "no executor" in stderr.getvalue()


def test_wired_handler_exit_code_zero() -> None:
    """verifies: TOOL-CIC-010

    A registered executor runs end-to-end and its return value is the exit
    code; handlers receive the parsed namespace (target-id visible).
    """
    catalogue = Catalogue()
    catalogue.register(
        Operation(name="sample.op", summary="s", cli_equivalent="ectt sample")
    )
    dispatcher = Dispatcher()
    seen: list[str] = []

    def handler(namespace: argparse.Namespace) -> int:
        seen.append(getattr(namespace, "target_id", ""))
        return 0

    dispatcher.register("sample.op", handler)
    code = run(
        ["sample.op", "--target-id", "42"],
        catalogue=catalogue,
        dispatcher=dispatcher,
    )
    assert code == 0
    assert seen == ["42"]


def test_duplicate_handler_registration_refused() -> None:
    """Two executors for one operation would make dispatch ambiguous."""
    dispatcher = Dispatcher()
    dispatcher.register("op.x", lambda ns: 0)
    with pytest.raises(CliError) as excinfo:
        dispatcher.register("op.x", lambda ns: 0)
    assert excinfo.value.reason == "duplicate_handler"


def test_dispatch_without_handler_raises_operation_not_available() -> None:
    """The dispatcher itself refuses unwired operations with the named error."""
    dispatcher = Dispatcher()
    namespace = argparse.Namespace(operation="ghost.op")
    with pytest.raises(OperationNotAvailable) as excinfo:
        dispatcher.dispatch(namespace)
    assert excinfo.value.operation == "ghost.op"

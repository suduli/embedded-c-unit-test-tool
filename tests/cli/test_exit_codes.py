"""Tests for the stable documented CLI exit codes (WP-CLI-02).

Verifies: TOOL-CIC-030.
"""

from __future__ import annotations

import io

import pytest

from ectt.api.catalogue import Catalogue, Operation
from ectt.cli.dispatch import Dispatcher, run
from ectt.cli.errors import CliError
from ectt.cli.exit_codes import (
    EXIT_CODE_TABLE,
    EXIT_COVERAGE_THRESHOLD,
    EXIT_SUCCESS,
    EXIT_TEST_FAILURE,
    EXIT_TOOL_ERROR,
    EXIT_USAGE,
)


def test_four_categories_have_distinct_stable_codes() -> None:
    """verifies: TOOL-CIC-030

    The four categories the requirement names each have a distinct constant;
    values are fixed here so regressions fail loudly.
    """
    assert EXIT_SUCCESS == 0
    assert EXIT_TOOL_ERROR == 1
    assert EXIT_TEST_FAILURE == 10
    assert EXIT_COVERAGE_THRESHOLD == 11
    assert len({EXIT_SUCCESS, EXIT_TOOL_ERROR, EXIT_TEST_FAILURE, EXIT_COVERAGE_THRESHOLD}) == 4


def test_exit_code_table_documents_every_code() -> None:
    """verifies: TOOL-CIC-030

    The table is the documentation source: every constant appears with a
    meaning, and usage error (2) is recorded too.
    """
    assert EXIT_CODE_TABLE[EXIT_SUCCESS] == "success"
    assert EXIT_CODE_TABLE[EXIT_TOOL_ERROR] == "tool error"
    assert EXIT_CODE_TABLE[EXIT_TEST_FAILURE] == "test failure"
    assert EXIT_CODE_TABLE[EXIT_COVERAGE_THRESHOLD] == "coverage threshold failure"
    assert EXIT_CODE_TABLE[EXIT_USAGE] == "command-line usage error"
    assert set(EXIT_CODE_TABLE) == {0, 1, 2, 10, 11}


def test_success_is_zero_and_others_nonzero() -> None:
    """verifies: TOOL-CIC-030

    Success is the only zero; every distinguished failure is non-zero.
    """
    assert EXIT_SUCCESS == 0
    for code in (EXIT_TOOL_ERROR, EXIT_USAGE, EXIT_TEST_FAILURE, EXIT_COVERAGE_THRESHOLD):
        assert code != 0


def test_tool_error_is_returned_for_cli_error() -> None:
    """verifies: TOOL-CIC-030

    A ``CliError`` raised by dispatch maps to ``EXIT_TOOL_ERROR``.
    """
    catalogue = Catalogue()
    catalogue.register(Operation(name="boom.op", summary="b", cli_equivalent="ectt boom"))
    dispatcher = Dispatcher()

    def handler(namespace: object) -> int:
        raise CliError("executor exploded", reason="boom")

    dispatcher.register("boom.op", handler)  # type: ignore[arg-type]
    stderr = io.StringIO()
    code = run(["boom.op"], catalogue=catalogue, dispatcher=dispatcher, stderr=stderr)
    assert code == EXIT_TOOL_ERROR


def test_handler_returned_codes_pass_through() -> None:
    """verifies: TOOL-CIC-030

    Handlers return table codes directly: a wired executor that reports a
    test failure or a coverage miss yields that exact code.
    """
    catalogue = Catalogue()
    catalogue.register(Operation(name="test.op", summary="t", cli_equivalent="ectt test"))
    catalogue.register(
        Operation(name="cov.op", summary="c", cli_equivalent="ectt cov")
    )
    dispatcher = Dispatcher()
    dispatcher.register("test.op", lambda ns: EXIT_TEST_FAILURE)
    dispatcher.register("cov.op", lambda ns: EXIT_COVERAGE_THRESHOLD)
    assert run(["test.op"], catalogue=catalogue, dispatcher=dispatcher) == EXIT_TEST_FAILURE
    assert run(["cov.op"], catalogue=catalogue, dispatcher=dispatcher) == EXIT_COVERAGE_THRESHOLD


def test_operation_not_available_maps_to_tool_error() -> None:
    """verifies: TOOL-CIC-030

    Unwired catalogue operations exit with the tool-error code.
    """
    stderr = io.StringIO()
    code = run(["operation.cancel", "--target-id", "17"], stderr=stderr)
    assert code == EXIT_TOOL_ERROR


def test_usage_error_keeps_conventional_two() -> None:
    """verifies: TOOL-CIC-030

    Empty invocation keeps argparse's conventional usage-error code 2,
    recorded in the table.
    """
    stderr = io.StringIO()
    assert run([], stderr=stderr) == EXIT_USAGE


@pytest.mark.parametrize(
    ("code", "name"),
    [
        (EXIT_SUCCESS, "success"),
        (EXIT_TOOL_ERROR, "tool error"),
        (EXIT_TEST_FAILURE, "test failure"),
        (EXIT_COVERAGE_THRESHOLD, "coverage threshold failure"),
    ],
)
def test_table_names_the_requirement_categories(code: int, name: str) -> None:
    """verifies: TOOL-CIC-030

    Each requirement-named category is present in the documented table under
    its own code.
    """
    assert EXIT_CODE_TABLE[code] == name

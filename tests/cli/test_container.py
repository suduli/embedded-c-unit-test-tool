"""Container-execution demonstration tests (WP-CLI-03).

TOOL-CIC-040 (method: demonstration): the CLI must be installable and
executable within a container image. The image itself is WP-PKG-05 (INS-090);
this module pins the *execution* contract at the process boundary — a
subprocess invocation of ``python -m ectt.cli`` in a stripped, container-like
environment (no display variables, no TTY stdin) with plain stdio semantics
and the WP-CLI-02 exit codes.

Verifies: TOOL-CIC-040.
"""

from __future__ import annotations

import os
import subprocess
import sys

from ectt.cli.exit_codes import EXIT_SUCCESS, EXIT_TOOL_ERROR

#: Environment of a minimal headless container: no display, no terminal,
#: PYTHONPATH pointed at the repository sources.
_CONTAINER_ENV = {
    key: value
    for key, value in os.environ.items()
    if key not in {"DISPLAY", "TERM", "WAYLAND_DISPLAY", "SESSIONTYPE"}
}


def _run_cli(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, "-I", "-m", "ectt.cli", *args],
        capture_output=True,
        stdin=subprocess.DEVNULL,
        env={**_CONTAINER_ENV, "PYTHONPATH": os.path.join(os.getcwd(), "src")},
        check=False,
        timeout=120,
    )


def test_cli_runs_headless_in_stripped_environment() -> None:
    """verifies: TOOL-CIC-040

    ``--list-commands`` inside a container-like environment exits 0 and
    prints the catalogue names — install-and-run, no display server needed.
    """
    proc = _run_cli("--list-commands")
    assert proc.returncode == EXIT_SUCCESS
    names = proc.stdout.decode("utf-8").splitlines()
    assert "operation.cancel" in names


def test_stdout_carries_only_requested_output() -> None:
    """verifies: TOOL-CIC-040

    Container logs stay machine-readable: stdout carries nothing but the
    requested output, even when the invocation fails.
    """
    proc = _run_cli("--list-commands")
    assert proc.stdout.decode("utf-8").strip() != ""
    assert "warning" not in proc.stdout.decode("utf-8").lower()

    failing = _run_cli("operation.cancel", "--target-id", "17")
    assert failing.returncode == EXIT_TOOL_ERROR
    assert failing.stdout == b""  # failure text belongs on stderr only


def test_unwired_operation_exit_code_in_container_env() -> None:
    """verifies: TOOL-CIC-040, TOOL-CIC-030

    Exit-code fidelity survives the process boundary: an unwired catalogue
    operation is the tool-error code, not a crash.
    """
    proc = _run_cli("operation.cancel", "--target-id", "17")
    assert proc.returncode == EXIT_TOOL_ERROR
    assert b"no executor" in proc.stderr


def test_help_works_without_tty() -> None:
    """verifies: TOOL-CIC-040

    ``--help`` works with stdin closed (DEVNULL) — no interactive prompt is
    ever required.
    """
    proc = _run_cli("--help")
    assert proc.returncode == EXIT_SUCCESS
    assert b"operation catalogue" in proc.stdout

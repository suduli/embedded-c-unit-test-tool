# implements: TOOL-EXE-010, TOOL-EXE-030
"""Restricted execution context for harness launches (WP-SEC-06).

There is no C compiler, debugger or simulator on this machine: verification
uses a recording FAKE starter (which captures exactly what it was given) and
golden text — no test starts a real process. Every refusal happens before the
starter is invoked: a refused context starts nothing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ectt.exh import (
    RestrictedContextError,
    WallClockExceeded,
    build_context,
    run_restricted,
)

MACHINE_ENV = {
    "PATH": r"C:\tools\bin",
    "HOME": r"C:\Users\builder",
    "ECTT_SECRET_TOKEN": "do-not-leak",
    "TEMP": r"C:\Temp",
}


class FakeStarter:
    """Records every invocation; returns canned output."""

    def __init__(self, stdout: str = "", returncode: int = 0, raise_timeout: bool = False) -> None:
        self.calls: list[dict[str, Any]] = []
        self._stdout = stdout
        self._returncode = returncode
        self._raise_timeout = raise_timeout

    def __call__(self, argv: Any, *, cwd: str, env: Any, timeout_seconds: float, close_fds: bool) -> Any:
        self.calls.append(
            {
                "argv": list(argv),
                "cwd": cwd,
                "env": dict(env),
                "timeout_seconds": timeout_seconds,
                "close_fds": close_fds,
            }
        )
        if self._raise_timeout:
            raise WallClockExceeded("the wall-clock limit was exceeded")
        return _Completed(stdout=self._stdout, returncode=self._returncode)


class _Completed:
    def __init__(self, stdout: str, returncode: int) -> None:
        self.stdout = stdout
        self.returncode = returncode


def _context(tmp_path: Path, **overrides: Any) -> Any:
    kwargs: dict[str, Any] = {
        "root": tmp_path,
        "working_directory": tmp_path / "sandbox",
        "environment_allow": ("PATH", "TEMP"),
        "machine_environment": MACHINE_ENV,
        "wall_clock_limit_s": 10.0,
        "output_limit_bytes": 4096,
    }
    kwargs.update(overrides)
    return build_context(**kwargs)


def test_the_environment_passes_only_the_allow_list(tmp_path: Path) -> None:
    """verifies: WP-SEC-06 AC-1 — only allow-listed names pass, values come from
    the machine's environment, absent names are omitted, secrets never leak."""
    context = _context(tmp_path)
    assert sorted(context.environment) == ["PATH", "TEMP"]
    assert context.environment["PATH"] == r"C:\tools\bin"
    assert "ECTT_SECRET_TOKEN" not in context.environment
    absent = _context(tmp_path, environment_allow=("PATH", "MISSING_VAR"))
    assert sorted(absent.environment) == ["PATH"]  # omitted, never invented
    # An allow-listed name that is itself not a name is dropped, not passed.
    weird = _context(tmp_path, environment_allow=("PATH", "BAD=NAME"))
    assert sorted(weird.environment) == ["PATH"]


def test_directory_confinement_refuses_a_path_escape(tmp_path: Path) -> None:
    """verifies: WP-SEC-06 AC-1 — a working directory outside the project root
    (or escaping through ..) is refused with the named reason."""
    with pytest.raises(RestrictedContextError) as outside:
        _context(tmp_path, working_directory=tmp_path.parent / "elsewhere")
    assert outside.value.reason == "path_escape"
    with pytest.raises(RestrictedContextError) as climbing:
        _context(tmp_path, working_directory=tmp_path / ".." / "elsewhere")
    assert climbing.value.reason == "path_escape"


def test_a_refused_context_starts_nothing(tmp_path: Path) -> None:
    """verifies: WP-SEC-06 AC-3 — every refusal is raised before the starter is
    invoked; the recording starter's call list stays empty."""
    starter = FakeStarter()
    for kwargs in (
        {"working_directory": tmp_path.parent / "elsewhere"},
        {"wall_clock_limit_s": 0},
        {"output_limit_bytes": -1},
        {"environment_allow": ()},
    ):
        with pytest.raises(RestrictedContextError):
            context = _context(tmp_path, **kwargs)
            run_restricted(context, ["harness"], starter=starter)
    assert starter.calls == []


def test_the_limits_are_recorded_in_the_result(tmp_path: Path) -> None:
    """verifies: WP-SEC-06 AC-2 — the result records the context with both
    limits, the closed handles and the scrubbed environment."""
    starter = FakeStarter(stdout="ok", returncode=0)
    context = _context(tmp_path)
    result = run_restricted(context, ["build/harness"], starter=starter)
    assert result.context.wall_clock_limit_s == 10.0
    assert result.context.output_limit_bytes == 4096
    assert result.context.inherit_handles is False
    assert result.exit_status == 0 and result.timed_out is False
    document = json.loads(json.dumps(result.to_dict()))
    assert document["context"]["inherit_handles"] is False
    assert document["context"]["wall_clock_limit_s"] == 10.0


def test_the_output_limit_truncates_and_flags(tmp_path: Path) -> None:
    """verifies: WP-SEC-06 AC-4 — captured output beyond the limit is truncated
    with the flag set; within the limit it passes whole."""
    starter = FakeStarter(stdout="x" * 100)
    context = _context(tmp_path, output_limit_bytes=10)
    result = run_restricted(context, ["harness"], starter=starter)
    assert result.stdout_truncated is True
    assert len(result.stdout) == 10

    whole = run_restricted(_context(tmp_path), ["harness"], starter=FakeStarter(stdout="short"))
    assert whole.stdout == "short" and whole.stdout_truncated is False


def test_the_starter_receives_the_scrubbed_invocation(tmp_path: Path) -> None:
    """verifies: WP-SEC-06 AC-4 — the starter gets exactly the confinement:
    confined cwd, scrubbed env, the wall-clock limit, close_fds=True."""
    starter = FakeStarter()
    context = _context(tmp_path)
    run_restricted(context, ["build/harness", "--flag"], starter=starter)
    (call,) = starter.calls
    assert call["argv"] == ["build/harness", "--flag"]
    assert call["cwd"] == context.working_directory
    assert call["env"] == {"PATH": r"C:\tools\bin", "TEMP": r"C:\Temp"}
    assert call["timeout_seconds"] == 10.0
    assert call["close_fds"] is True  # handles are never inherited


def test_the_recorded_invocation_is_golden_stable(tmp_path: Path) -> None:
    """verifies: WP-SEC-06 AC-4 — the recorded invocation serialises to the
    same bytes on every run (golden text; no wall clock)."""
    starter = FakeStarter()
    context = _context(tmp_path)
    run_restricted(context, ["build/harness"], starter=starter)
    golden = json.dumps(starter.calls, sort_keys=True, indent=1)
    again = FakeStarter()
    run_restricted(_context(tmp_path), ["build/harness"], starter=again)
    assert json.dumps(again.calls, sort_keys=True, indent=1) == golden


def test_a_wall_clock_exceeding_starter_reports_timed_out(tmp_path: Path) -> None:
    """verifies: WP-SEC-06 AC-4 — a starter that reports the wall-clock limit as
    exceeded yields timed_out=True with no exit status."""
    result = run_restricted(
        _context(tmp_path), ["harness"], starter=FakeStarter(raise_timeout=True)
    )
    assert result.timed_out is True
    assert result.exit_status is None


def test_confined_directory_inside_the_root_is_accepted(tmp_path: Path) -> None:
    """verifies: WP-SEC-06 AC-1 — a sandbox inside the root resolves and is
    recorded as the absolute confined path."""
    (tmp_path / "sandbox").mkdir()
    context = _context(tmp_path)
    assert Path(context.working_directory) == (tmp_path / "sandbox").resolve()

# implements: TOOL-EXE-070
"""Debugger launch with an entry breakpoint (WP-EXH-04).

There is no C compiler, debugger or simulator on this machine: the argv is
verified by golden text, the refusals by their named reasons, and the launch
hand-off by a recording fake starter — no test starts a real process.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ectt.exh import DebuggerLaunchError, build_debugger_launch, start_debugger


def _built(tmp_path: Path, name: str = "harness") -> Path:
    harness = tmp_path / name
    harness.parent.mkdir(parents=True, exist_ok=True)
    harness.write_text("/* a built harness binary stands in here */\n", encoding="utf-8")
    return harness


def test_the_gdb_argv_is_golden_stable(tmp_path: Path) -> None:
    """verifies: TOOL-EXE-070 — gdb first, the entry breakpoint, the harness as
    the debuggee and the normal run's arguments; golden text."""
    launch = build_debugger_launch(
        debugger="gdb",
        harness=_built(tmp_path),
        test_function="adc_scale",
        symbols_recorded=True,
        working_directory=tmp_path,
        args=("--ectt-select", "tc.one"),
    )
    assert launch.argv == (
        "gdb",
        "-ex",
        "break adc_scale",
        "--args",
        str(_built(tmp_path)),
        "--ectt-select",
        "tc.one",
    )
    assert launch.breakpoint == "break adc_scale"
    assert launch.working_directory == str(tmp_path)
    golden = json.dumps(launch.argv, sort_keys=False)
    again = build_debugger_launch(
        debugger="gdb",
        harness=_built(tmp_path),
        test_function="adc_scale",
        symbols_recorded=True,
        working_directory=tmp_path,
        args=("--ectt-select", "tc.one"),
    )
    assert json.dumps(again.argv, sort_keys=False) == golden


def test_an_unnamed_debugger_is_refused() -> None:
    """verifies: TOOL-EXE-070 — no debugger named, no launch."""
    with pytest.raises(DebuggerLaunchError) as excinfo:
        build_debugger_launch(
            debugger=None,
            harness="harness",
            test_function="f",
            symbols_recorded=True,
            working_directory=".",
        )
    assert excinfo.value.reason == "debugger_not_named"
    with pytest.raises(DebuggerLaunchError) as blank:
        build_debugger_launch(
            debugger="  ",
            harness="harness",
            test_function="f",
            symbols_recorded=True,
            working_directory=".",
        )
    assert blank.value.reason == "debugger_not_named"


def test_a_build_without_symbols_is_refused() -> None:
    """verifies: TOOL-EXE-070 — stepping needs recorded debug symbols."""
    with pytest.raises(DebuggerLaunchError) as excinfo:
        build_debugger_launch(
            debugger="gdb",
            harness="harness",
            test_function="f",
            symbols_recorded=False,
            working_directory=".",
        )
    assert excinfo.value.reason == "no_symbols"


def test_an_unbuilt_harness_is_refused(tmp_path: Path) -> None:
    """verifies: TOOL-EXE-070 — the harness file must exist."""
    with pytest.raises(DebuggerLaunchError) as excinfo:
        build_debugger_launch(
            debugger="gdb",
            harness=tmp_path / "missing",
            test_function="f",
            symbols_recorded=True,
            working_directory=tmp_path,
        )
    assert excinfo.value.reason == "harness_not_built"


def test_a_missing_breakpoint_function_is_refused(tmp_path: Path) -> None:
    """verifies: TOOL-EXE-070 — the entry breakpoint needs the function."""
    with pytest.raises(DebuggerLaunchError) as excinfo:
        build_debugger_launch(
            debugger="gdb",
            harness=_built(tmp_path),
            test_function=" ",
            symbols_recorded=True,
            working_directory=tmp_path,
        )
    assert excinfo.value.reason == "no_breakpoint_function"


def test_the_starter_receives_the_argv_and_the_working_directory(tmp_path: Path) -> None:
    """verifies: TOOL-EXE-070 — the launch hands the built argv and the working
    directory to the injected starter, exactly and nothing more."""
    harness = _built(tmp_path)
    launch = build_debugger_launch(
        debugger="gdb",
        harness=harness,
        test_function="adc_scale",
        symbols_recorded=True,
        working_directory=tmp_path,
    )
    calls: list[dict] = []

    def starter(argv: list[str], *, cwd: str) -> str:
        calls.append({"argv": list(argv), "cwd": cwd})
        return "debugger-session"

    assert start_debugger(launch, starter=starter) == "debugger-session"
    assert calls == [{"argv": list(launch.argv), "cwd": str(tmp_path)}]


def test_paths_with_spaces_survive_and_quote_for_display(tmp_path: Path) -> None:
    """verifies: TOOL-EXE-070 — a harness path with spaces is one argv element
    (the execution contract), and the display form quotes it."""
    spaced = _built(tmp_path, name="my harnesses/harness one")
    launch = build_debugger_launch(
        debugger="gdb",
        harness=spaced,
        test_function="adc_scale",
        symbols_recorded=True,
        working_directory=tmp_path,
    )
    (debuggee,) = [element for element in launch.argv if "harness one" in element]
    assert debuggee == str(spaced)  # one element, unescaped
    assert '"' not in debuggee
    assert f"'{spaced}'" in launch.command_line() or f'"{spaced}"' in launch.command_line()


def test_a_refused_launch_never_starts(tmp_path: Path) -> None:
    """verifies: TOOL-EXE-070 — the refusals happen in the builder, before any
    starter exists: a refused launch cannot start anything."""
    calls: list[list[str]] = []

    def starter(argv: list[str], *, cwd: str) -> None:
        calls.append(list(argv))

    with pytest.raises(DebuggerLaunchError):
        build_debugger_launch(
            debugger=None,
            harness=_built(tmp_path),
            test_function="f",
            symbols_recorded=True,
            working_directory=tmp_path,
        )
    with pytest.raises(DebuggerLaunchError):
        build_debugger_launch(
            debugger="gdb",
            harness=tmp_path / "missing",
            test_function="f",
            symbols_recorded=True,
            working_directory=tmp_path,
        )
    assert calls == []

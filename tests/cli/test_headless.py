"""Headless-operation tests for the CLI (WP-CLI-01).

Verifies: TOOL-CIC-020 — the tool operates without a graphical environment
or display server: no GUI/Qt import anywhere under ``src/ectt/cli`` and a
full dispatch cycle on plain stdio.
"""

from __future__ import annotations

import ast
import io
import pathlib

from ectt.api.catalogue import Catalogue, Operation
from ectt.cli.dispatch import Dispatcher, run

GUI_TOKENS = ("PySide6", "PyQt5", "PyQt6", "QtWidgets", "QtGui", "tkinter", "curses")


def test_cli_modules_import_no_gui_dependencies() -> None:
    """verifies: TOOL-CIC-020

    AST-scan every CLI module for GUI toolkit imports; the CLI must be
    renderable nowhere and runnable everywhere.
    """
    cli_root = pathlib.Path("src/ectt/cli")
    assert cli_root.is_dir()
    scanned = 0
    for path in sorted(cli_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for token in GUI_TOKENS:
                        assert token not in alias.name, (path, alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for token in GUI_TOKENS:
                    assert token not in module, (path, module)
        scanned += 1
    assert scanned >= 4  # __init__, errors, generator, dispatch, __main__


def test_dispatch_runs_without_display() -> None:
    """verifies: TOOL-CIC-020

    A full invoke-and-dispatch cycle works on plain stdio streams only.
    """
    catalogue = Catalogue()
    catalogue.register(
        Operation(name="headless.op", summary="h", cli_equivalent="ectt headless")
    )
    dispatcher = Dispatcher()
    dispatcher.register("headless.op", lambda ns: 0)
    stdout = io.StringIO()
    code = run(
        ["headless.op"],
        catalogue=catalogue,
        dispatcher=dispatcher,
        stdout=stdout,
    )
    assert code == 0

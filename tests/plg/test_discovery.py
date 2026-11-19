"""Tests for the WP-PLG-02 extension discovery and failure isolation.

Verifies: TOOL-PLG-070, TOOL-PLG-080.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from ectt.plg import (
    KIND_IMPORT_ERROR,
    KIND_INCOMPATIBLE,
    KIND_RUNTIME_ERROR,
    KIND_SYNTAX_ERROR,
    ExtensionPointRegistry,
    discover_extensions,
)
from ectt.plg.discovery import ExtensionsDirError, LoadFailure

GOOD_EXT = """\
def register(registry):
    from ectt.plg.points import ExtensionPoint
    registry.register(ExtensionPoint(
        point_id="user_hook",
        title="User hook",
        description="Discovered from the extensions directory.",
        contract="user_contract",
        interface_version="1",
    ))
"""

BROKEN_SYNTAX = "def register(registry):\n    return (unclosed\n"
BROKEN_IMPORT = "import module_that_does_not_exist_xyz\n\ndef register(registry):\n    pass\n"
RAISES_RUNTIME = "raise RuntimeError('boom at import')\n"
NO_REGISTER = "value = 42\n"


def _populate(tmp_path: Path) -> Path:
    (tmp_path / "good.py").write_text(GOOD_EXT, encoding="utf-8")
    (tmp_path / "broken.py").write_text(BROKEN_SYNTAX, encoding="utf-8")
    (tmp_path / "missing_import.py").write_text(BROKEN_IMPORT, encoding="utf-8")
    (tmp_path / "raises.py").write_text(RAISES_RUNTIME, encoding="utf-8")
    (tmp_path / "no_register.py").write_text(NO_REGISTER, encoding="utf-8")
    (tmp_path / "readme.txt").write_text("ignored\n", encoding="utf-8")
    return tmp_path


def test_extensions_discovered_and_loaded_without_reinstallation(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-070"""
    registry = ExtensionPointRegistry()
    report = discover_extensions(_populate(tmp_path), registry)
    assert report.loaded == ("good",)
    assert registry.lookup("user_hook").title == "User hook"


def test_failures_are_isolated_and_reported_clearly(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-080"""
    registry = ExtensionPointRegistry()
    report = discover_extensions(_populate(tmp_path), registry)
    # Loading continued: the good extension still registered.
    assert "good" in report.loaded
    kinds = {f.name: f.kind for f in report.failures}
    assert kinds == {
        "broken": KIND_SYNTAX_ERROR,
        "missing_import": KIND_IMPORT_ERROR,
        "raises": KIND_RUNTIME_ERROR,
        "no_register": KIND_INCOMPATIBLE,
    }
    lines = report.render().splitlines()
    assert any("broken.py".replace(".py", "") in line and "syntax_error" in line for line in lines)


def test_remaining_functionality_continues_after_failures(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-080"""
    (tmp_path / "second_good.py").write_text(
        GOOD_EXT.replace("user_hook", "second_hook"), encoding="utf-8"
    )
    registry = ExtensionPointRegistry()
    report = discover_extensions(_populate(tmp_path), registry)
    assert report.loaded == ("good", "second_good")
    assert len(report.failures) == 4
    # The tool keeps operating: both user extension points are usable.
    assert registry.lookup("user_hook") is not None
    assert registry.lookup("second_hook") is not None


def test_missing_directory_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-070"""
    with pytest.raises(ExtensionsDirError):
        discover_extensions(tmp_path / "absent", ExtensionPointRegistry())


def test_non_py_files_ignored(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-070"""
    registry = ExtensionPointRegistry()
    report = discover_extensions(_populate(tmp_path), registry)
    assert all(f.name != "readme" for f in report.failures)


def test_report_is_deterministic_and_frozen(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-080"""
    registry_one = ExtensionPointRegistry()
    registry_two = ExtensionPointRegistry()
    first = discover_extensions(_populate(tmp_path), registry_one)
    second = discover_extensions(_populate(tmp_path), registry_two)
    assert first.to_dict() == second.to_dict()
    assert dataclasses.is_dataclass(LoadFailure)
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.loaded = ()  # type: ignore[misc]

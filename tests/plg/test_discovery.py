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
    UntrustedExtensionsError,
    discover_extensions,
)
from ectt.plg.discovery import (
    DiscoveryReport,
    ExtensionsDirError,
    LoadFailure,
    load_extension_file,
)
from ectt.sec import UntrustedProjectTracker

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
BROKEN_IMPORT = (
    "import module_that_does_not_exist_xyz\n\ndef register(registry):\n    pass\n"
)
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


def _discover(tmp_path: Path, registry: ExtensionPointRegistry) -> DiscoveryReport:
    """Populate, mark the directory opened, then discover (trust must match content)."""
    directory = _populate(tmp_path)
    tracker = UntrustedProjectTracker(directory / "trust.json")
    tracker.mark_opened(directory)
    return discover_extensions(directory, registry, trust=tracker)


SENTINEL_EXT = """\
from pathlib import Path
Path(__file__).with_name("ran.marker").write_text("executed", encoding="utf-8")


def register(registry):
    pass
"""


def test_untrusted_directory_runs_no_extension(tmp_path: Path) -> None:
    """verifies: TOOL-SEC-050, TOOL-PLG-070"""
    (tmp_path / "sentinel.py").write_text(SENTINEL_EXT, encoding="utf-8")
    tracker = UntrustedProjectTracker(tmp_path / "trust.json")

    with pytest.raises(UntrustedExtensionsError):
        discover_extensions(tmp_path, ExtensionPointRegistry(), trust=tracker)

    assert not (tmp_path / "ran.marker").exists()


def test_single_file_loader_also_requires_trust(tmp_path: Path) -> None:
    """verifies: TOOL-SEC-050, TOOL-PLG-070"""
    (tmp_path / "sentinel.py").write_text(SENTINEL_EXT, encoding="utf-8")
    tracker = UntrustedProjectTracker(tmp_path / "trust.json")

    with pytest.raises(UntrustedExtensionsError):
        load_extension_file(
            tmp_path / "sentinel.py", ExtensionPointRegistry(), trust=tracker
        )

    assert not (tmp_path / "ran.marker").exists()


def test_editing_an_extension_after_trust_makes_directory_untrusted(
    tmp_path: Path,
) -> None:
    """verifies: TOOL-SEC-050"""
    _discover(tmp_path, ExtensionPointRegistry())
    tracker = UntrustedProjectTracker(tmp_path / "trust.json")
    assert tracker.decision(tmp_path).known is True

    (tmp_path / "good.py").write_text(
        GOOD_EXT + "\n# changed after trust\n", encoding="utf-8"
    )

    with pytest.raises(UntrustedExtensionsError):
        discover_extensions(tmp_path, ExtensionPointRegistry(), trust=tracker)


def test_trust_record_inside_the_directory_does_not_invalidate_trust(
    tmp_path: Path,
) -> None:
    """verifies: TOOL-SEC-050"""
    _discover(tmp_path, ExtensionPointRegistry())
    tracker = UntrustedProjectTracker(tmp_path / "trust.json")
    assert tracker.decision(tmp_path).known is True


def test_extensions_discovered_and_loaded_without_reinstallation(
    tmp_path: Path,
) -> None:
    """verifies: TOOL-PLG-070"""
    registry = ExtensionPointRegistry()
    report = _discover(tmp_path, registry)
    assert report.loaded == ("good",)
    assert registry.lookup("user_hook").title == "User hook"


def test_failures_are_isolated_and_reported_clearly(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-080"""
    registry = ExtensionPointRegistry()
    report = _discover(tmp_path, registry)
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
    assert any(
        "broken.py".replace(".py", "") in line and "syntax_error" in line
        for line in lines
    )


def test_remaining_functionality_continues_after_failures(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-080"""
    (tmp_path / "second_good.py").write_text(
        GOOD_EXT.replace("user_hook", "second_hook"), encoding="utf-8"
    )
    registry = ExtensionPointRegistry()
    report = _discover(tmp_path, registry)
    assert report.loaded == ("good", "second_good")
    assert len(report.failures) == 4
    # The tool keeps operating: both user extension points are usable.
    assert registry.lookup("user_hook") is not None
    assert registry.lookup("second_hook") is not None


def test_missing_directory_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-070"""
    with pytest.raises(ExtensionsDirError):
        discover_extensions(
            tmp_path / "absent",
            ExtensionPointRegistry(),
            trust=UntrustedProjectTracker(tmp_path / "trust.json"),
        )


def test_non_py_files_ignored(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-070"""
    registry = ExtensionPointRegistry()
    report = _discover(tmp_path, registry)
    assert all(f.name != "readme" for f in report.failures)


def test_report_is_deterministic_and_frozen(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-080"""
    registry_one = ExtensionPointRegistry()
    registry_two = ExtensionPointRegistry()
    first = _discover(tmp_path, registry_one)
    second = _discover(tmp_path, registry_two)
    assert first.to_dict() == second.to_dict()
    assert dataclasses.is_dataclass(LoadFailure)
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.loaded = ()  # type: ignore[misc]

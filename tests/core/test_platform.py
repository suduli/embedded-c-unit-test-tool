"""Platform baseline and offline guarantee (WP-CORE-03).

Implements: TOOL-NFR-010 (boundary value analysis over sys.platform values),
TOOL-NFR-020 (equivalence partitioning by platform family), TOOL-NFR-100
(offline inspection over the whole product source).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from ectt.core.determinism import canonical_json_bytes
from ectt.core.platform import (
    NETWORK_MODULES,
    VALIDATED_PLATFORMS,
    OfflineViolationError,
    Platform,
    PlatformError,
    assert_offline,
    current_platform,
    detect_platform,
    executable_suffix,
    find_network_imports,
    platform_report,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "ectt"


# --- TOOL-NFR-010 / TOOL-NFR-020: platform detection ----------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("win32", Platform.WINDOWS),
        ("cygwin", Platform.UNKNOWN),
        ("linux", Platform.LINUX),
        ("linux2", Platform.LINUX),
        ("darwin", Platform.MACOS),
        ("freebsd13", Platform.UNKNOWN),
        ("", Platform.UNKNOWN),
    ],
)
def test_detect_platform_boundary_values(value: str, expected: Platform) -> None:
    """verifies: TOOL-NFR-010/020 — detection partitions the platform families."""
    assert detect_platform(value) is expected


def test_current_platform_matches_running_interpreter() -> None:
    assert current_platform() is detect_platform(sys.platform)


def test_executable_suffix_partitions_by_platform_family() -> None:
    assert executable_suffix(Platform.WINDOWS) == ".exe"
    assert executable_suffix(Platform.LINUX) == ""
    assert executable_suffix(Platform.MACOS) == ""


def test_executable_suffix_unknown_platform_raises() -> None:
    with pytest.raises(PlatformError) as excinfo:
        executable_suffix(Platform.UNKNOWN)
    assert excinfo.value.reason == "unsupported_platform"


def test_platform_errors_share_the_core_category() -> None:
    """verifies: no new error category is introduced by WP-CORE-03."""
    assert PlatformError("x").category == "core"
    assert OfflineViolationError("x").category == "core"


# --- Decision D-03: "Windows first, Linux CI kept green" ------------------------------


def test_validated_platforms_follow_decision_d03() -> None:
    assert frozenset({Platform.WINDOWS, Platform.LINUX}) == VALIDATED_PLATFORMS


def test_macos_recognised_but_not_yet_validated() -> None:
    assert Platform.MACOS not in VALIDATED_PLATFORMS
    assert detect_platform("darwin") is Platform.MACOS
    assert executable_suffix(Platform.MACOS) == ""  # shared POSIX path


# TOOL-NFR-010 — Linux x86-64 baseline; the hook the Linux CI lane executes.
@pytest.mark.skipif(
    sys.platform != "linux", reason="Linux CI evidence; executes only on Linux x86-64"
)
def test_linux_x86_64_baseline() -> None:
    assert current_platform() is Platform.LINUX
    assert executable_suffix() == ""


# TOOL-NFR-020 — Windows-first baseline; executes on every Windows run.
@pytest.mark.skipif(
    sys.platform != "win32", reason="Windows-first evidence; executes on Windows"
)
def test_windows_baseline() -> None:
    assert current_platform() is Platform.WINDOWS
    assert executable_suffix() == ".exe"


def test_platform_report_is_deterministic_and_wall_clock_free() -> None:
    """verifies: AC-4 — report is stable, canonical-JSON serialisable, no clock."""
    first = platform_report()
    second = platform_report()
    assert first == second
    assert canonical_json_bytes(first) == canonical_json_bytes(first)
    assert set(first) == {"executable_suffix", "machine", "platform", "validated"}


# --- TOOL-NFR-100: offline audit -------------------------------------------------------


def _make_tree(tmp_path: Path) -> Path:
    src = tmp_path / "pkg"
    (src / "sub").mkdir(parents=True)
    return src


def test_find_network_imports_detects_banned_modules(tmp_path: Path) -> None:
    src = _make_tree(tmp_path)
    (src / "net.py").write_text(
        "import socket\nimport json\nfrom urllib.request import urlopen\n",
        encoding="utf-8",
    )
    (src / "sub" / "third.py").write_text("import requests\n", encoding="utf-8")

    assert find_network_imports(src) == (
        ("net.py", 1, "socket"),
        ("net.py", 3, "urllib"),
        ("sub/third.py", 1, "requests"),
    )


def test_find_network_imports_clean_tree_has_no_hits(tmp_path: Path) -> None:
    src = _make_tree(tmp_path)
    (src / "safe.py").write_text(
        "import json\nfrom pathlib import Path\nimport hashlib\n",
        encoding="utf-8",
    )

    assert find_network_imports(src) == ()


def test_find_network_imports_output_is_sorted_and_deterministic(tmp_path: Path) -> None:
    src = _make_tree(tmp_path)
    (src / "b.py").write_text("import socket\n", encoding="utf-8")
    (src / "a.py").write_text("import ssl\nimport socket\n", encoding="utf-8")
    expected = (("a.py", 1, "ssl"), ("a.py", 2, "socket"), ("b.py", 1, "socket"))

    assert find_network_imports(src) == expected
    assert find_network_imports(src) == find_network_imports(src)


def test_find_network_imports_flags_unparsable_file(tmp_path: Path) -> None:
    src = _make_tree(tmp_path)
    (src / "broken.py").write_text("def f(:\n", encoding="utf-8")

    assert find_network_imports(src) == (("broken.py", 0, "<syntax-error>"),)


def test_find_network_imports_skips_caches(tmp_path: Path) -> None:
    src = _make_tree(tmp_path)
    cache = src / "__pycache__"
    cache.mkdir()
    (cache / "net.py").write_text("import socket\n", encoding="utf-8")

    assert find_network_imports(src) == ()


def test_assert_offline_raises_on_violation(tmp_path: Path) -> None:
    src = _make_tree(tmp_path)
    (src / "net.py").write_text("import http.client\n", encoding="utf-8")

    with pytest.raises(OfflineViolationError) as excinfo:
        assert_offline(src)
    assert excinfo.value.reason == "network_import"


def test_assert_offline_accepts_clean_tree(tmp_path: Path) -> None:
    src = _make_tree(tmp_path)
    (src / "ok.py").write_text("import json\n", encoding="utf-8")

    assert_offline(src)  # does not raise


def test_repository_source_is_offline() -> None:
    """verifies: TOOL-NFR-100 — product source imports no network module."""
    assert find_network_imports(SRC_ROOT) == ()


@pytest.mark.parametrize(
    "mod", ["socket", "ssl", "urllib", "http", "requests", "httpx", "aiohttp"]
)
def test_banned_module_list_covers_essentials(mod: str) -> None:
    assert mod in NETWORK_MODULES

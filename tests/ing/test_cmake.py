# implements: DSN-ING-020
"""Tests for CMake compilation database export documentation and helper.

Verifies: TOOL-ING-040, DSN-ING-020.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ectt.ing.cmake import (
    CMAKE_EXPORT_DOCUMENTATION,
    generate_compdb_via_cmake,
)
from ectt.ing.errors import CMakeConfigureError


def test_cmake_documentation_presence() -> None:
    """verifies: TOOL-ING-040, DSN-ING-020"""
    assert "CMAKE_EXPORT_COMPILE_COMMANDS=ON" in CMAKE_EXPORT_DOCUMENTATION
    assert "cmake -S" in CMAKE_EXPORT_DOCUMENTATION
    assert "Ninja" in CMAKE_EXPORT_DOCUMENTATION


def test_source_dir_not_found(tmp_path: Path) -> None:
    """verifies: TOOL-ING-040, DSN-ING-020"""
    non_existent = tmp_path / "non_existent_src"
    with pytest.raises(CMakeConfigureError) as exc_info:
        generate_compdb_via_cmake(non_existent)
    assert exc_info.value.reason == "source_dir_not_found"


def test_missing_cmakelists_raises_error(tmp_path: Path) -> None:
    """verifies: TOOL-ING-040, DSN-ING-020"""
    src_dir = tmp_path / "src_no_cmake"
    src_dir.mkdir()
    with pytest.raises(CMakeConfigureError) as exc_info:
        generate_compdb_via_cmake(src_dir)
    assert exc_info.value.reason == "missing_cmakelists"


def test_in_source_build_strictly_forbidden(tmp_path: Path) -> None:
    """verifies: TOOL-ING-040, DSN-ING-020"""
    src_dir = tmp_path / "src_with_cmake"
    src_dir.mkdir()
    (src_dir / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.20)\n", encoding="utf-8")

    # In-source build (build_dir == source_dir) must be rejected
    with pytest.raises(CMakeConfigureError) as exc_info:
        generate_compdb_via_cmake(src_dir, build_dir=src_dir)
    assert exc_info.value.reason == "in_source_build_forbidden"


def test_cmake_not_found_raises_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-ING-040, DSN-ING-020"""
    src_dir = tmp_path / "src_cmake"
    src_dir.mkdir()
    (src_dir / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.20)\n", encoding="utf-8")

    with patch("subprocess.run", side_effect=FileNotFoundError("cmake not found")):
        with pytest.raises(CMakeConfigureError) as exc_info:
            generate_compdb_via_cmake(src_dir, cmake_executable="nonexistent_cmake")
        assert exc_info.value.reason == "cmake_not_found"


def test_cmake_execution_failed_raises_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-ING-040, DSN-ING-020"""
    src_dir = tmp_path / "src_cmake"
    src_dir.mkdir()
    (src_dir / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.20)\n", encoding="utf-8")

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stderr = "CMake Error at CMakeLists.txt: syntax error"

    with patch("subprocess.run", return_value=mock_proc):
        with pytest.raises(CMakeConfigureError) as exc_info:
            generate_compdb_via_cmake(src_dir)
        assert exc_info.value.reason == "cmake_execution_failed"
        assert exc_info.value.exit_code == 1


def test_compdb_not_generated_raises_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-ING-040, DSN-ING-020"""
    src_dir = tmp_path / "src_cmake"
    src_dir.mkdir()
    (src_dir / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.20)\n", encoding="utf-8")

    build_dir = tmp_path / "build_scratch"

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        with pytest.raises(CMakeConfigureError) as exc_info:
            generate_compdb_via_cmake(src_dir, build_dir=build_dir)
        assert exc_info.value.reason == "compdb_not_generated"


def test_cmake_scratch_configure_happy_path(tmp_path: Path) -> None:
    """verifies: TOOL-ING-040, DSN-ING-020"""
    src_dir = tmp_path / "src_cmake"
    src_dir.mkdir()
    cmakelists_content = "cmake_minimum_required(VERSION 3.20)\nproject(demo C)\nadd_executable(demo main.c)\n"
    cmakelists = src_dir / "CMakeLists.txt"
    cmakelists.write_text(cmakelists_content, encoding="utf-8")
    mtime_before = cmakelists.stat().st_mtime_ns

    build_dir = tmp_path / "build_scratch"

    def fake_subprocess_run(cmd: list[str], **kwargs: object) -> MagicMock:
        # Verify mandatory flags
        assert "-S" in cmd
        assert str(src_dir.resolve()) in cmd
        assert "-B" in cmd
        assert str(build_dir.resolve()) in cmd
        assert "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON" in cmd

        # Simulate cmake writing compile_commands.json into scratch build dir
        build_dir.mkdir(parents=True, exist_ok=True)
        (build_dir / "compile_commands.json").write_text("[]", encoding="utf-8")

        mock = MagicMock()
        mock.returncode = 0
        mock.stderr = ""
        return mock

    with patch("subprocess.run", side_effect=fake_subprocess_run):
        result_path = generate_compdb_via_cmake(src_dir, build_dir=build_dir)

    assert result_path == (build_dir / "compile_commands.json").resolve()
    assert result_path.is_file()

    # Verify source directory and CMakeLists.txt are completely untouched (immutability)
    assert cmakelists.read_text(encoding="utf-8") == cmakelists_content
    assert cmakelists.stat().st_mtime_ns == mtime_before


def test_cmake_execution_oserror_raises_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-ING-040, DSN-ING-020"""
    src_dir = tmp_path / "src_cmake"
    src_dir.mkdir()
    (src_dir / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.20)\n", encoding="utf-8")

    with patch("subprocess.run", side_effect=OSError("Process spawn failure")):
        with pytest.raises(CMakeConfigureError) as exc_info:
            generate_compdb_via_cmake(src_dir)
        assert exc_info.value.reason == "cmake_execution_error"


def test_cmake_scratch_configure_default_build_dir(tmp_path: Path) -> None:
    """verifies: TOOL-ING-040, DSN-ING-020"""
    src_dir = tmp_path / "src_cmake_default"
    src_dir.mkdir()
    (src_dir / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.20)\n", encoding="utf-8")

    allocated_build_dir: Path | None = None

    def fake_subprocess_run(cmd: list[str], **kwargs: object) -> MagicMock:
        nonlocal allocated_build_dir
        b_idx = cmd.index("-B")
        allocated_build_dir = Path(cmd[b_idx + 1])
        allocated_build_dir.mkdir(parents=True, exist_ok=True)
        (allocated_build_dir / "compile_commands.json").write_text("[]", encoding="utf-8")

        mock = MagicMock()
        mock.returncode = 0
        mock.stderr = ""
        return mock

    with patch("subprocess.run", side_effect=fake_subprocess_run):
        result_path = generate_compdb_via_cmake(src_dir)

    assert allocated_build_dir is not None
    assert result_path == (allocated_build_dir / "compile_commands.json").resolve()
    assert result_path.is_file()


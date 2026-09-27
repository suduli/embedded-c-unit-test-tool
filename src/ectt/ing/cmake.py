# implements: DSN-ING-020
"""CMake compilation database export documentation and scratch-configure helper.

Satisfies: TOOL-ING-040, DSN-ING-020.

RECOMMENDED WORKFLOW (CMake Ingestion):
--------------------------------------
The recommended mechanism for ingesting CMake-based projects into ectt is generating
a Clang JSON Compilation Database (`compile_commands.json`) via CMake's built-in
`CMAKE_EXPORT_COMPILE_COMMANDS` facility.

Usage with standard CMake CLI:
    cmake -S <project_source_dir> -B <build_dir> -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

Supported Generators:
    - Ninja (`-G Ninja`) [Recommended]
    - Makefile (`-G "Unix Makefiles"` or `-G "MinGW Makefiles"`)
    (Note: Visual Studio and Xcode multi-configuration generators do not support
    CMAKE_EXPORT_COMPILE_COMMANDS in older CMake versions without Ninja Multi-Config.)

Architecture Constraint:
    CMake is read-side only. ectt never modifies the user's `CMakeLists.txt` or
    in-tree source files. When extracting a compilation database automatically,
    ectt configures into an isolated temporary scratch directory via `-S <src> -B <scratch>`
    and harvests `compile_commands.json` without polluting or modifying the user's tree.
"""

from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path

from ectt.ing.errors import CMakeConfigureError

__all__ = [
    "CMAKE_EXPORT_DOCUMENTATION",
    "generate_compdb_via_cmake",
]

CMAKE_EXPORT_DOCUMENTATION = """
### Recommended Ingestion: CMake compile_commands.json Generation

To generate `compile_commands.json` for consumption by ectt:

```sh
cmake -S <source-dir> -B <build-dir> -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

Key guidelines:
1. Use the **Ninja** or **Unix/MinGW Makefiles** generator for reliable compilation database emission.
2. Ingest into ectt using `ectt.ing.load_compdb("<build-dir>/compile_commands.json")`.
3. Never edit the user's `CMakeLists.txt` to inject flags; CMake is read-side only.
"""


def generate_compdb_via_cmake(
    source_dir: Path | str,
    *,
    build_dir: Path | str | None = None,
    cmake_args: Sequence[str] = (),
    cmake_executable: str = "cmake",
) -> Path:
    """Configure a project with CMake into a scratch directory and return compile_commands.json.

    Satisfies: TOOL-ING-040.

    Ensures:
    - Never modifies user source files or `CMakeLists.txt`.
    - Never configures in-source (build_dir must differ from source_dir).
    - If build_dir is not provided, allocates a dedicated scratch directory in temp.
    - Shells out to `cmake -S <source_dir> -B <build_dir> -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`.

    Args:
        source_dir: Directory containing project root and CMakeLists.txt.
        build_dir: Optional scratch directory. If None, creates a fresh temporary directory.
        cmake_args: Additional arguments passed to CMake configure (e.g. ['-G', 'Ninja']).
        cmake_executable: Path or name of the CMake executable (default 'cmake').

    Returns:
        Path to the harvested `compile_commands.json`.

    Raises:
        CMakeConfigureError: If cmake is not found, CMakeLists.txt is missing, in-source
            build is requested, or CMake execution fails.
    """
    src_path = Path(source_dir).resolve()
    if not src_path.is_dir():
        raise CMakeConfigureError(
            f"Source directory '{source_dir}' does not exist",
            reason="source_dir_not_found",
            path=src_path,
        )

    cmakelists_path = src_path / "CMakeLists.txt"
    if not cmakelists_path.is_file():
        raise CMakeConfigureError(
            f"No CMakeLists.txt found in source directory '{src_path}'",
            reason="missing_cmakelists",
            path=cmakelists_path,
        )

    # Determine build scratch directory
    if build_dir is not None:
        bld_path = Path(build_dir).resolve()
    else:
        bld_path = Path(tempfile.mkdtemp(prefix="ectt_cmake_scratch_")).resolve()

    # Safety constraint: In-source build is strictly forbidden to preserve source immutability
    if bld_path == src_path:
        raise CMakeConfigureError(
            f"In-source CMake build is forbidden; build directory '{bld_path}' must differ from source directory",
            reason="in_source_build_forbidden",
            path=bld_path,
        )

    bld_path.mkdir(parents=True, exist_ok=True)

    cmd = [
        cmake_executable,
        "-S",
        str(src_path),
        "-B",
        str(bld_path),
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        *cmake_args,
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CMakeConfigureError(
            f"CMake executable '{cmake_executable}' not found in PATH",
            reason="cmake_not_found",
            path=bld_path,
        ) from exc
    except OSError as exc:
        raise CMakeConfigureError(
            f"Failed to execute CMake: {exc}",
            reason="cmake_execution_error",
            path=bld_path,
        ) from exc

    if proc.returncode != 0:
        raise CMakeConfigureError(
            f"CMake configure failed with exit code {proc.returncode}:\n{proc.stderr}",
            exit_code=proc.returncode,
            stderr=proc.stderr,
            reason="cmake_execution_failed",
            path=bld_path,
        )

    compdb_path = bld_path / "compile_commands.json"
    if not compdb_path.is_file():
        raise CMakeConfigureError(
            f"CMake configuration succeeded but '{compdb_path}' was not generated. "
            "Ensure the CMake generator supports CMAKE_EXPORT_COMPILE_COMMANDS (e.g. Ninja or Makefiles).",
            reason="compdb_not_generated",
            path=compdb_path,
        )

    return compdb_path

# implements: DSN-PRJ-040
"""Path validation and POSIX normalization for ectt project trees.

Enforces relative-only references to user source, requirements, and configuration:
- All paths are POSIX-style relative to the project root with '/' separators.
- Absolute paths, Windows drive letters, UNC paths, and '..' boundary escapes are rejected.
- Relocating or cloning the project directory leaves all relative paths valid.

Satisfies: TOOL-PRJ-070, DSN-PRJ-040.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath

from ectt.prj.errors import InvalidRelativePathError, ProjectConfinementError

__all__ = [
    "validate_project_path",
    "resolve_project_path",
    "normalize_posix_path",
]

_WINDOWS_DRIVE_RE = re.compile(r"^[a-zA-Z]:")
_UNC_PREFIX_RE = re.compile(r"^[\\/]{2}")


def normalize_posix_path(path_str: str) -> str:
    """Normalize a relative path string into clean POSIX format with '/' separators.

    Rejects paths that escape beyond the top-level via '..' traversal.
    """
    raw = path_str.strip()
    if not raw:
        raise InvalidRelativePathError("Path string cannot be empty", reason="empty_path", path=path_str)

    # Check for UNC prefix (e.g. \\server\share or //server/share)
    if _UNC_PREFIX_RE.match(raw):
        raise InvalidRelativePathError(
            f"UNC path '{path_str}' is forbidden; paths must be relative to project root",
            reason="unc_path",
            path=path_str,
        )

    # Check for Windows drive letter (e.g. C: or C:\foo or c:/bar)
    if _WINDOWS_DRIVE_RE.match(raw):
        raise InvalidRelativePathError(
            f"Path with drive letter '{path_str}' is forbidden; paths must be relative to project root",
            reason="drive_letter",
            path=path_str,
        )

    # Check for leading slashes indicating root/absolute paths
    if raw.startswith("/") or raw.startswith("\\"):
        raise InvalidRelativePathError(
            f"Absolute path '{path_str}' is forbidden; paths must be relative to project root",
            reason="absolute_path",
            path=path_str,
        )

    # Check PurePath properties across POSIX and Windows parsers
    posix_pure = PurePosixPath(raw)
    win_pure = PureWindowsPath(raw)
    if posix_pure.is_absolute() or win_pure.is_absolute() or bool(win_pure.drive):
        raise InvalidRelativePathError(
            f"Absolute path or drive path '{path_str}' is forbidden",
            reason="absolute_path",
            path=path_str,
        )

    # Split on both / and \ to normalize across platforms
    parts = re.split(r"[\\/]+", raw)
    normalized_parts: list[str] = []

    for part in parts:
        if not part or part == ".":
            continue
        if part == "..":
            if not normalized_parts:
                raise InvalidRelativePathError(
                    f"Path '{path_str}' escapes project root boundary via '..'",
                    reason="path_escape",
                    path=path_str,
                )
            normalized_parts.pop()
        else:
            normalized_parts.append(part)

    if not normalized_parts:
        raise InvalidRelativePathError(
            f"Path '{path_str}' resolves to root or empty path",
            reason="root_target",
            path=path_str,
        )

    return "/".join(normalized_parts)


def validate_project_path(path: Path | str) -> str:
    """Validate that a path is a valid POSIX relative path within project bounds.

    Returns the normalized POSIX path string.
    Raises InvalidRelativePathError on any violation.
    """
    path_str = str(path)
    return normalize_posix_path(path_str)


def resolve_project_path(project_root: Path, rel_path: Path | str) -> Path:
    """Resolve a project-relative path against the project root directory.

    Guarantees the resolved path does not escape the project root.
    """
    normalized = validate_project_path(rel_path)
    resolved_root = project_root.resolve()
    candidate = (resolved_root / normalized).resolve()

    if not candidate.is_relative_to(resolved_root):
        raise ProjectConfinementError(
            f"Resolved path '{candidate}' escapes project root '{resolved_root}'",
            reason="project_confinement_violation",
            path=candidate,
        )

    return candidate

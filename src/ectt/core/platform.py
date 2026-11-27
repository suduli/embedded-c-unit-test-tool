# implements: DSN-CORE-010
"""Platform baseline and offline guarantee (WP-CORE-03).

Implements: TOOL-NFR-010 (Linux x86-64), TOOL-NFR-020 (Windows), TOOL-NFR-200 (macOS),
TOOL-NFR-100 (no network access for non-AI functionality).

Platform order follows owner decision D-03 (owner answer, 2026-11-19, memo
option (a)): "Windows first, Linux CI kept green". Windows is the first-class
development platform, Linux is exercised continuously by CI, and macOS shares
the POSIX code path but has no runner evidence yet. Unvalidated platforms are
reported, not refused.

The offline guarantee is machine-checked: an AST import scan over a source
root against an explicit deny-list of network-capable modules. Unparsable
files are reported so the scan cannot be silently blinded.
"""

from __future__ import annotations

import ast
import platform as _platform
import sys
from collections.abc import Iterator
from enum import Enum
from pathlib import Path

from ectt.core.determinism import CoreError

__all__ = [
    "NETWORK_MODULES",
    "VALIDATED_PLATFORMS",
    "OfflineViolationError",
    "Platform",
    "PlatformError",
    "assert_offline",
    "current_platform",
    "detect_platform",
    "executable_suffix",
    "find_network_imports",
    "platform_report",
]

_SYNTAX_ERROR_MODULE = "<syntax-error>"

_SKIP_DIRS = frozenset(
    {"__pycache__", ".git", ".venv", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
)


class PlatformError(CoreError):
    """Raised when the host platform is outside the supported baseline."""


class OfflineViolationError(CoreError):
    """Raised when the offline audit finds a network-capable import."""


class Platform(Enum):
    """Canonical host platforms recognised by the tool."""

    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


#: Platforms with continuous validation evidence under decision D-03
#: ("Windows first, Linux CI kept green"). MACOS is recognised and shares the
#: POSIX code path but has no runner evidence yet; see WP-CORE-03-analysis.md.
VALIDATED_PLATFORMS: frozenset[Platform] = frozenset(
    {Platform.WINDOWS, Platform.LINUX}
)

#: Top-level module names whose import makes code network-capable. stdlib
#: network stacks and common third-party clients. TOOL-NFR-100 deny-list.
NETWORK_MODULES: frozenset[str] = frozenset(
    {
        "aiohttp",
        "ftplib",
        "grpc",
        "http",
        "httpx",
        "imaplib",
        "nntplib",
        "poplib",
        "pycurl",
        "requests",
        "socket",
        "smtplib",
        "ssl",
        "telnetlib",
        "urllib",
        "urllib3",
        "websocket",
        "websockets",
        "xmlrpc",
    }
)


def detect_platform(sys_platform_value: str | None = None) -> Platform:
    """Map a ``sys.platform`` value to the canonical platform.

    Pure by design: pass the value explicitly to exercise any equivalence
    class on any host; omit it to classify the running interpreter.
    """
    value = sys.platform if sys_platform_value is None else sys_platform_value
    if value.startswith("win"):
        return Platform.WINDOWS
    if value.startswith("linux"):
        return Platform.LINUX
    if value.startswith("darwin"):
        return Platform.MACOS
    return Platform.UNKNOWN


def current_platform() -> Platform:
    """Return the canonical platform of the running interpreter."""
    return detect_platform()


def executable_suffix(platform: Platform | None = None) -> str:
    """Return the native executable suffix for a platform.

    ``".exe"`` on Windows, ``""`` on the POSIX branch (Linux, macOS). Raises
    ``PlatformError`` for an unknown platform rather than guessing.
    """
    resolved = current_platform() if platform is None else platform
    if resolved is Platform.WINDOWS:
        return ".exe"
    if resolved in (Platform.LINUX, Platform.MACOS):
        return ""
    raise PlatformError(
        f"No executable suffix for platform {resolved.value}",
        reason="unsupported_platform",
    )


def platform_report() -> dict[str, str | bool]:
    """Return the deterministic host facts the tool relies on.

    No wall-clock, no network. Raises ``PlatformError`` on an unknown host
    (fail-safe: the report refuses to describe a platform it cannot name).
    """
    plat = current_platform()
    return {
        "executable_suffix": executable_suffix(plat),
        "machine": _platform.machine(),
        "platform": plat.value,
        "validated": plat in VALIDATED_PLATFORMS,
    }


def _python_files(source_root: Path) -> Iterator[Path]:
    for path in sorted(source_root.rglob("*.py")):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        yield path


def _banned_tops(node: ast.Import | ast.ImportFrom) -> Iterator[str]:
    if isinstance(node, ast.Import):
        for alias in node.names:
            yield alias.name.split(".")[0]
    elif node.module is not None:
        yield node.module.split(".")[0]


def find_network_imports(source_root: Path) -> tuple[tuple[str, int, str], ...]:
    """Scan a source tree for imports of network-capable modules.

    Returns a sorted tuple of ``(relative path, line number, top-level
    module)`` triples; empty means the tree is offline. Files that cannot be
    parsed are reported with module ``<syntax-error>`` (line 0) so the scan
    cannot be silently blinded. Relative imports carry no top-level module
    and are skipped. Dynamic string-based imports (``importlib.import_module``)
    are out of scope; see WP-CORE-03-analysis.md.
    """
    violations: list[tuple[str, int, str]] = []
    for path in _python_files(source_root):
        rel = path.relative_to(source_root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            violations.append((rel, 0, _SYNTAX_ERROR_MODULE))
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            violations.extend(
                (rel, node.lineno, top)
                for top in _banned_tops(node)
                if top in NETWORK_MODULES
            )
    return tuple(sorted(violations))


def assert_offline(source_root: Path) -> None:
    """Raise ``OfflineViolationError`` if any network-capable import exists."""
    hits = find_network_imports(source_root)
    if hits:
        listed = "\n".join(f"  {rel}:{line}: {mod}" for rel, line, mod in hits)
        raise OfflineViolationError(
            f"Network-capable imports found under {source_root}:\n{listed}",
            reason="network_import",
            path=source_root,
        )

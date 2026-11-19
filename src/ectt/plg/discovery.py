"""Extension discovery and load-failure isolation (WP-PLG-02).

User-supplied extensions load from a documented directory without
reinstallation. Each file loads in isolation: a failing extension is reported
by name, kind and detail while every other extension still loads, so the tool
continues operating with the remaining functionality.

Loading executes user code; callers must consult the WP-SEC-03 trust gate
(``ectt.sec.UntrustedProjectTracker``) before discovery.

Satisfies: TOOL-PLG-070, TOOL-PLG-080.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from ectt.plg.errors import PlgError

__all__ = [
    "KIND_SYNTAX_ERROR",
    "KIND_IMPORT_ERROR",
    "KIND_RUNTIME_ERROR",
    "KIND_INCOMPATIBLE",
    "LoadFailure",
    "DiscoveryReport",
    "ExtensionsDirError",
    "discover_extensions",
    "load_extension_file",
]

KIND_SYNTAX_ERROR = "syntax_error"
KIND_IMPORT_ERROR = "import_error"
KIND_RUNTIME_ERROR = "runtime_error"
KIND_INCOMPATIBLE = "incompatible"


class ExtensionsDirError(PlgError):
    """Raised when the extensions directory is missing or unreadable."""

    def __init__(
        self, message: str, *, reason: str = "extensions_dir_error", path: str | None = None
    ) -> None:
        super().__init__(message, reason=reason, path=path)


@dataclass(frozen=True)
class LoadFailure:
    """One extension that failed to load, with its name, kind and detail."""

    name: str
    kind: str
    detail: str

    def render(self) -> str:
        """A clear one-line report of the failure."""
        return f"extension '{self.name}' failed to load ({self.kind}): {self.detail}"


@dataclass(frozen=True)
class DiscoveryReport:
    """The outcome of one discovery pass, deterministic and inspectable."""

    loaded: tuple[str, ...]
    failures: tuple[LoadFailure, ...]

    def render(self) -> str:
        """Clear report lines for every failure, plus the loaded set."""
        lines = [f"loaded extensions: {', '.join(self.loaded) or '(none)'}"]
        lines.extend(failure.render() for failure in self.failures)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "failures": [
                {"detail": f.detail, "kind": f.kind, "name": f.name}
                for f in sorted(self.failures, key=lambda f: f.name)
            ],
            "loaded": sorted(self.loaded),
        }


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ExtensionsDirError(f"cannot build import spec for '{path.name}'", path=str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_extension_file(path: Path, registry: object) -> str:
    """Load one extension file and run its ``register(registry)``.

    Raises a named :class:`PlgError` subclass on any failure mode; use
    :func:`discover_extensions` for isolated bulk loading.
    """
    module = _load_module(path)
    register = getattr(module, "register", None)
    if not callable(register):
        raise ExtensionsDirError(
            f"extension '{path.name}' is incompatible: it exposes no register(registry)",
            path=str(path),
        )
    register(registry)
    return path.stem


def discover_extensions(directory: Path | str, registry: object) -> DiscoveryReport:
    """Discover and load every ``*.py`` extension in ``directory``.

    Each file loads in isolation: a failing extension becomes a recorded
    ``LoadFailure`` (named, kinded, detailed) and the remaining extensions
    still load.
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise ExtensionsDirError(
            f"extensions directory '{directory}' does not exist", path=str(dir_path)
        )
    loaded: list[str] = []
    failures: list[LoadFailure] = []
    for path in sorted(dir_path.glob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            module = _load_module(path)
        except SyntaxError as exc:
            failures.append(
                LoadFailure(name=path.stem, kind=KIND_SYNTAX_ERROR, detail=str(exc))
            )
            continue
        except ImportError as exc:
            failures.append(
                LoadFailure(name=path.stem, kind=KIND_IMPORT_ERROR, detail=str(exc))
            )
            continue
        except Exception as exc:  # noqa: BLE001 - isolation is the point here
            failures.append(
                LoadFailure(name=path.stem, kind=KIND_RUNTIME_ERROR, detail=repr(exc))
            )
            continue
        register = getattr(module, "register", None)
        if not callable(register):
            failures.append(
                LoadFailure(
                    name=path.stem,
                    kind=KIND_INCOMPATIBLE,
                    detail="exposes no register(registry) callable",
                )
            )
            continue
        try:
            register(registry)
        except Exception as exc:  # noqa: BLE001 - isolation is the point here
            failures.append(
                LoadFailure(name=path.stem, kind=KIND_RUNTIME_ERROR, detail=repr(exc))
            )
            continue
        loaded.append(path.stem)
    return DiscoveryReport(loaded=tuple(sorted(loaded)), failures=tuple(failures))

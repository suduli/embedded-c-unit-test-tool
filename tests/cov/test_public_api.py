# implements: TOOL-COV-140
"""The coverage package's declared public surface is importable from it.

``ectt.cov.__all__`` is a promise: ``from ectt.cov import <name>`` resolves for
every name in it. The justification names were added to that list on 2026-11-21
without the import that binds them, and nothing failed, because every test
imported them from ``ectt.cov.justification`` directly. These checks pin the
promise from both sides: nothing is declared that is not bound, and nothing a
module publishes is left undeclared.
"""

from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

import ectt.cov


def _public_modules() -> list[ModuleType]:
    modules = [
        importlib.import_module(f"ectt.cov.{info.name}")
        for info in pkgutil.iter_modules(ectt.cov.__path__)
        if not info.ispkg and not info.name.startswith("_")
    ]
    return sorted(modules, key=lambda module: module.__name__)


def test_every_declared_export_is_bound_on_the_package() -> None:
    """verifies: ``from ectt.cov import <name>`` resolves for every name in ``__all__``."""
    missing = [name for name in ectt.cov.__all__ if not hasattr(ectt.cov, name)]
    assert missing == []


def test_no_export_is_declared_twice() -> None:
    declared = list(ectt.cov.__all__)
    assert len(declared) == len(set(declared))


def test_everything_a_module_publishes_is_reachable_from_the_package() -> None:
    """verifies: a module added to the package is published, not merely present."""
    unpublished: dict[str, list[str]] = {}
    for module in _public_modules():
        for name in getattr(module, "__all__", ()):
            if not hasattr(ectt.cov, name):
                unpublished.setdefault(module.__name__, []).append(name)
    assert unpublished == {}

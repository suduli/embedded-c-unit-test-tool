# implements: TOOL-MIG-010
"""Error model for the migration package."""

from __future__ import annotations

from typing import ClassVar

from ectt.core.errors import EcttError

__all__ = [
    "MigError",
]


class MigError(EcttError):
    """Raised for existing-suite execution problems."""

    category: ClassVar[str] = "migration"

# implements: TOOL-ATG-050
"""Error model for the generation package (WP-ATG-01)."""

from __future__ import annotations

from typing import ClassVar

from ectt.core.errors import EcttError

__all__ = [
    "AtgError",
]


class AtgError(EcttError):
    """Raised for invalid generation inputs and failed validation infrastructure."""

    category: ClassVar[str] = "generation"

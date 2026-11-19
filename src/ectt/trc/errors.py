# implements: TOOL-TRC-010
"""Error model for the traceability package (WP-TRC-01)."""

from __future__ import annotations

from typing import ClassVar

from ectt.core.errors import EcttError

__all__ = [
    "TrcError",
]


class TrcError(EcttError):
    """Raised for invalid associations and matrix inputs."""

    category: ClassVar[str] = "traceability"

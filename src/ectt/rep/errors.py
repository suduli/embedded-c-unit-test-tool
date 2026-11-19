# implements: TOOL-REP-090
"""Error model for the report package (WP-REP-01)."""

from __future__ import annotations

from typing import ClassVar

from ectt.core.errors import EcttError

__all__ = [
    "ReportModelError",
]


class ReportModelError(EcttError):
    """Raised for invalid report models and refused loads."""

    category: ClassVar[str] = "report"

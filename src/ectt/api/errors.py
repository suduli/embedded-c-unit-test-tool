"""Error classes for the ectt engine API (WP-API-01).

Protocol-level failures surface as ``ApiError`` (category ``api``) and are
translated into correlated error envelopes by :mod:`ectt.api.protocol`.

Satisfies: TOOL-UIX-020, TOOL-PLG-060.
Design: SDD-002 §9.2 (error envelope), §3 (fail-closed versioning).
"""

from __future__ import annotations

from typing import ClassVar

from ectt.core.errors import EcttError

__all__ = [
    "ApiError",
]


class ApiError(EcttError):
    """Base exception for engine-API protocol errors."""

    category: ClassVar[str] = "api"

    def __init__(
        self,
        message: str,
        *,
        reason: str = "api_error",
    ) -> None:
        super().__init__(message, reason=reason)

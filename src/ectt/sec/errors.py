"""Error classes for ectt security and integrity.

Satisfies: TOOL-SEC-120.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ectt.core.fs import CoreError

__all__ = [
    "SecError",
    "SourceContentInDiagnosticError",
]


class SecError(CoreError):
    """Base exception for ectt security-policy violations."""

    category: ClassVar[str] = "security"

    def __init__(
        self,
        message: str,
        *,
        reason: str = "security_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class SourceContentInDiagnosticError(SecError):
    """Raised when a diagnostic embeds user source code content."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "source_content_in_diagnostic",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)

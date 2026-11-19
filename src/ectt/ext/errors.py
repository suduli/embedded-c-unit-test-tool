"""Error classes for ectt target execution.

Satisfies: TOOL-TGT-020, TOOL-TGT-030, TOOL-TGT-080, TOOL-TGT-090, TOOL-TGT-110.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ectt.core.fs import CoreError

__all__ = [
    "ExtError",
]


class ExtError(CoreError):
    """Base exception for ectt target execution operations."""

    category: ClassVar[str] = "target"

    def __init__(
        self,
        message: str,
        *,
        reason: str = "target_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)

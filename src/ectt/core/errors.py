# implements: DSN-CORE-010
"""Structured error model shared by every ectt package (WP-CORE-02).

Every ectt exception derives from EcttError and exposes the same fields:

- ``message``  human-readable text (unchanged public message per subclass)
- ``reason``   stable machine-readable reason code
- ``category`` coarse class of failure, fixed per package base class
- ``code``     stable identifier: the exception class name
- ``path``     optional file or directory the error concerns
- ``context``  optional mapping of extra JSON-safe details

``to_dict()`` returns a canonical, JSON-serialisable mapping so that the same
error always serialises to the same bytes.

Cancellation is cooperative: a CancellationToken is checked at write
boundaries, and raising CancelledError unwinds the operation.

Satisfies: TOOL-NFR-090, TOOL-NFR-180.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path, PurePath
from typing import Any, ClassVar

__all__ = [
    "EcttError",
    "CancelledError",
    "CancellationToken",
]


def _jsonable(value: Any) -> Any:
    """Coerce a context value into a stable JSON-safe form."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, PurePath):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {str(k): _jsonable(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [_jsonable(v) for v in value]
        if isinstance(value, (set, frozenset)):
            items.sort(key=repr)
        return items
    return str(value)


class EcttError(Exception):
    """Root of the ectt exception hierarchy."""

    category: ClassVar[str] = "internal"

    def __init__(
        self,
        message: str,
        *,
        reason: str = "core_error",
        path: Path | str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.reason = reason
        self.path = Path(path) if path is not None else None
        self.context: dict[str, Any] = dict(context) if context else {}

    @property
    def code(self) -> str:
        """Stable identifier for this error: the concrete exception class name."""
        return type(self).__name__

    def __str__(self) -> str:
        if self.path is not None:
            return f"{self.message} [reason={self.reason}, path={self.path}]"
        return f"{self.message} [reason={self.reason}]"

    def to_dict(self) -> dict[str, Any]:
        """Return a canonical, JSON-serialisable description of this error."""
        return {
            "category": self.category,
            "code": self.code,
            "context": _jsonable(self.context),
            "message": self.message,
            "path": self.path.as_posix() if self.path is not None else None,
            "reason": self.reason,
        }


class CancellationToken:
    """Cooperative cancellation flag checked at write boundaries."""

    def __init__(self) -> None:
        self._cancelled = False

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        self._cancelled = True

    def raise_if_cancelled(self) -> None:
        if self._cancelled:
            raise CancelledError("Operation was cancelled", reason="cancelled")


class CancelledError(EcttError):
    """Raised when an operation observes a cancelled CancellationToken."""

    category: ClassVar[str] = "cancelled"

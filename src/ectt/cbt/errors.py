# implements: TOOL-CBT-010
"""Error model for suite re-execution (WP-CBT-01)."""

from __future__ import annotations

from typing import ClassVar

from ectt.core.errors import EcttError

__all__ = [
    "CbtError",
]


class CbtError(EcttError):
    """Raised when an existing compiled suite cannot be re-executed as recorded.

    Shares the ``execution`` category of the host-execution package: to a user
    this is a failed run request, not a separate kind of failure.
    """

    category: ClassVar[str] = "execution"

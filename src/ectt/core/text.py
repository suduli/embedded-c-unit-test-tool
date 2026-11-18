"""Externalised user-facing text (WP-CORE-07).

All user-facing text lives in a message catalog keyed by stable identifiers;
code never embeds user-facing strings. The default catalog is English-only —
no translation ships in v1.0 (TOOL-NFR-190) — but a translation is delivered
by supplying another catalog, never by editing code.

Satisfies: TOOL-NFR-190.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ectt.core.errors import EcttError

__all__ = [
    "DEFAULT_CATALOG_NAME",
    "MessageCatalog",
    "TextFormatError",
    "UnknownMessageKeyError",
    "default_catalog",
]

DEFAULT_CATALOG_NAME = "en"


class UnknownMessageKeyError(EcttError):
    """Raised when a message key is absent from the catalog."""

    category = "text"

    def __init__(self, message: str, *, reason: str = "unknown_message_key") -> None:
        super().__init__(message, reason=reason)


class TextFormatError(EcttError):
    """Raised when a message cannot be formatted with the supplied values."""

    category = "text"

    def __init__(self, message: str, *, reason: str = "text_format_error") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class MessageCatalog:
    """A frozen catalog of user-facing messages keyed by stable identifiers."""

    name: str
    messages: dict[str, str]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise UnknownMessageKeyError("catalog name must be a non-empty string")
        for key, text in self.messages.items():
            if not isinstance(key, str) or not key.strip():
                raise UnknownMessageKeyError("message keys must be non-empty strings")
            if not isinstance(text, str) or not text.strip():
                raise UnknownMessageKeyError(
                    f"message '{key}' must carry non-empty text"
                )

    def message(self, key: str, **values: Any) -> str:
        """The catalog text for ``key``, formatted with ``values``."""
        try:
            template = self.messages[key]
        except KeyError:
            raise UnknownMessageKeyError(
                f"message key '{key}' is not in catalog '{self.name}'"
            ) from None
        try:
            return template.format(**values)
        except (KeyError, IndexError) as exc:
            raise TextFormatError(
                f"message '{key}' needs a placeholder {exc} that was not supplied"
            ) from None

    def keys(self) -> tuple[str, ...]:
        """All message keys, ordered deterministically."""
        return tuple(sorted(self.messages))

    def to_dict(self) -> dict[str, str]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {key: self.messages[key] for key in sorted(self.messages)}


_DEFAULT_MESSAGES: dict[str, str] = field(default_factory=dict)

_DEFAULT_MESSAGES = {
    "app.title": "ECTT - Embedded-C Unit-Test Tool",
    "untrusted_project.warning": (
        "Warning: project '{project}' has not been opened with this tool "
        "before. Running it will execute user-supplied code ({kinds}). "
        "Review the project, then confirm to continue."
    ),
    "ingest.single_file.ok": "Ingested single source {source}.",
    "ingest.database.loaded": "Ingested {count} translation unit(s) from {path}.",
    "ingest.stale": "The ingested project model is stale; re-ingestion is required.",
    "build.plan.up_to_date": "{count} artifact(s) up to date.",
    "build.plan.rebuild": "{count} artifact(s) scheduled for recompilation.",
    "environment.first_run": "First run: verifying environment.",
    "environment.missing": "Missing: {subject}",
    "environment.unsupported": "Unsupported: {subject}",
    "config.not_data": (
        "Configuration value at '{key_path}' is not data; configuration is "
        "data, not script."
    ),
    "harness.generated": "Harness for {uut} written to {output}.",
    "diagnostic.bundle.created": (
        "Diagnostic bundle written ({entries} documented entries)."
    ),
}


def default_catalog() -> MessageCatalog:
    """The shipped catalog (English-only; no translation in v1.0)."""
    return MessageCatalog(name=DEFAULT_CATALOG_NAME, messages=dict(_DEFAULT_MESSAGES))

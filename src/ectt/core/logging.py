"""Configurable-verbosity logging and the diagnostic bundle (WP-CORE-06).

The logger records tool operations at a configurable verbosity, each record
carrying a location reference rather than source content. The diagnostic
bundle builder collects version, configuration, logs, and the failing command
into a frozen, deterministic artifact whose contents are documented by the
WP-SEC-04 manifest; every log line is run through the WP-SEC-04 content guard
at build time.

Satisfies: TOOL-NFR-130, TOOL-NFR-160.
"""

from __future__ import annotations

import enum
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass

__all__ = [
    "Verbosity",
    "LogRecord",
    "EcttLogger",
    "DiagnosticBundle",
    "build_diagnostic_bundle",
]


class Verbosity(enum.IntEnum):
    """Configurable logging verbosity scale."""

    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


def _location_reference(
    path: str, line: int | None = None, column: int | None = None
) -> str:
    """Location reference format shared with the security package semantics."""
    if line is None:
        return path
    if column is None:
        return f"{path}:{line}"
    return f"{path}:{line}:{column}"


@dataclass(frozen=True)
class LogRecord:
    """One recorded log entry: level, message, optional location reference."""

    level: int
    message: str
    location: str | None = None

    def render(self) -> str:
        """Rendered line: message with its location reference, never source text."""
        if self.location:
            return f"{self.message} [{self.location}]"
        return self.message


class EcttLogger:
    """Records tool operations at a configurable verbosity.

    When a ``source_lines_provider`` is configured, every message is checked
    against the WP-SEC-04 content guard before it is recorded: a message
    embedding verbatim user source content raises the named security error and
    is never recorded.
    """

    def __init__(
        self,
        verbosity: Verbosity = Verbosity.NORMAL,
        *,
        source_lines_provider: Callable[[], Iterable[str]] | None = None,
    ) -> None:
        self._verbosity = Verbosity(verbosity)
        self._source_lines_provider = source_lines_provider
        self._records: list[LogRecord] = []

    @property
    def verbosity(self) -> Verbosity:
        return self._verbosity

    def set_verbosity(self, verbosity: Verbosity) -> None:
        """Change the verbosity; already-recorded entries are kept."""
        self._verbosity = Verbosity(verbosity)

    def log(
        self,
        message: str,
        *,
        level: Verbosity = Verbosity.NORMAL,
        path: str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        """Record a message at ``level`` if the configured verbosity admits it.

        The record carries a location reference built from ``path``/``line``/
        ``column``; it never carries source content by construction, and when a
        source-line provider is configured the WP-SEC-04 guard refuses verbatim
        embeddings before recording.
        """
        if level > self._verbosity:
            return
        if self._source_lines_provider is not None:
            from ectt.sec.diagnostics import assert_no_source_content

            assert_no_source_content(message, self._source_lines_provider(), origin="log")
        location = (
            _location_reference(path, line, column) if path is not None else None
        )
        self._records.append(
            LogRecord(level=int(level), message=message, location=location)
        )

    def records(self, at_or_above: Verbosity = Verbosity.QUIET) -> tuple[LogRecord, ...]:
        """All recorded entries from ``at_or_above`` upward, in record order."""
        return tuple(
            record for record in self._records if record.level >= int(at_or_above)
        )

    def render(self, at_or_above: Verbosity = Verbosity.NORMAL) -> str:
        """Rendered log excerpt, one line per record, in record order."""
        return "\n".join(
            record.render() for record in self.records(at_or_above=at_or_above)
        )


@dataclass(frozen=True)
class DiagnosticBundle:
    """The diagnostic bundle: exactly what the WP-SEC-04 manifest documents."""

    ectt_version: str
    configuration: tuple[tuple[str, str], ...]
    log_excerpt: tuple[str, ...]
    command: str
    exit_status: int
    manifest_entries: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "command": self.command,
            "configuration": [list(item) for item in self.configuration],
            "ectt_version": self.ectt_version,
            "exit_status": self.exit_status,
            "log_excerpt": list(self.log_excerpt),
            "manifest_entries": list(self.manifest_entries),
        }


def build_diagnostic_bundle(
    *,
    configuration: Mapping[str, str],
    logger: EcttLogger,
    command: str,
    exit_status: int,
    ectt_version: str,
) -> DiagnosticBundle:
    """Build the diagnostic bundle from tool state.

    The log excerpt is taken at NORMAL verbosity and above from ``logger``;
    when the logger was configured with a source-line provider, its messages
    were already checked against the WP-SEC-04 guard at record time. The
    manifest entries carried in the bundle are the WP-SEC-04 documentation of
    what a bundle contains.
    """
    from ectt.sec.diagnostics import bundle_manifest

    config_pairs = tuple(
        sorted((str(key), str(value)) for key, value in configuration.items())
    )
    excerpt_lines = tuple(
        record.render() for record in logger.records(at_or_above=Verbosity.NORMAL)
    )
    manifest = bundle_manifest()
    return DiagnosticBundle(
        ectt_version=ectt_version,
        configuration=config_pairs,
        log_excerpt=excerpt_lines,
        command=command,
        exit_status=exit_status,
        manifest_entries=manifest.entries,
    )

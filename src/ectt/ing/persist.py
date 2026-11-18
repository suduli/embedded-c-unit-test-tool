"""Persistence of the ingested project model (WP-ING-03).

The ingested database persists as canonical JSON with a schema version — a
version-controllable text format — so ingestion need not be repeated. Saving
is deterministic: identical databases produce byte-identical files.

Satisfies: TOOL-ING-090.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ectt.ing.errors import IngestionError
from ectt.ing.model import CompilationDatabase, CompilerInvocation, TranslationUnit

__all__ = [
    "PERSISTED_SCHEMA_VERSION",
    "PersistedModelReadError",
    "PersistedModelFormatError",
    "PersistedSchemaVersionError",
    "save_database",
    "load_database",
]

PERSISTED_SCHEMA_VERSION = 1


class PersistedModelReadError(IngestionError):
    """Raised when the persisted model file is missing or unreadable."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "persisted_model_read_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class PersistedModelFormatError(IngestionError):
    """Raised when the persisted model is not the expected JSON structure."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "persisted_model_format_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class PersistedSchemaVersionError(IngestionError):
    """Raised when the persisted schema version is missing or unsupported."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "persisted_schema_version_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


def save_database(database: CompilationDatabase, path: Path | str) -> None:
    """Persist the database as canonical JSON with a schema version."""
    document: dict[str, Any] = {
        "schema_version": PERSISTED_SCHEMA_VERSION,
        "database": database.to_dict(),
    }
    text = json.dumps(document, indent=2, sort_keys=True) + "\n"
    Path(path).write_text(text, encoding="utf-8")


def _invocation_from_dict(data: dict[str, Any]) -> CompilerInvocation:
    return CompilerInvocation(
        executable=str(data["executable"]),
        arguments=tuple(data.get("arguments", ())),
        residual_flags=tuple(data.get("residual_flags", ())),
        raw_arguments=tuple(data.get("raw_arguments", ())),
        target_triple=data.get("target_triple"),
        sysroot=data.get("sysroot"),
    )


def _unit_from_dict(data: dict[str, Any]) -> TranslationUnit:
    return TranslationUnit(
        source_path=str(data["source_path"]),
        working_directory=str(data["working_directory"]),
        include_paths=tuple(data.get("include_paths", ())),
        preprocessor_definitions=tuple(data.get("preprocessor_definitions", ())),
        compiler_invocation=_invocation_from_dict(data["compiler_invocation"]),
        language_standard=data.get("language_standard"),
        output_file=data.get("output_file"),
        response_files=tuple(data.get("response_files", ())),
    )


def load_database(path: Path | str) -> CompilationDatabase:
    """Reload a persisted database; named errors for every malformed shape."""
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PersistedModelReadError(
            f"cannot read persisted ingestion model: {exc}",
            path=file_path,
        ) from exc
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PersistedModelFormatError(
            f"persisted ingestion model is not valid JSON: {exc}",
            path=file_path,
        ) from exc
    if not isinstance(document, dict):
        raise PersistedModelFormatError(
            "persisted ingestion model must be a JSON object",
            path=file_path,
        )
    version = document.get("schema_version")
    if version is None:
        raise PersistedSchemaVersionError(
            "persisted ingestion model is missing 'schema_version'",
            path=file_path,
        )
    if version != PERSISTED_SCHEMA_VERSION:
        raise PersistedSchemaVersionError(
            f"persisted ingestion model schema_version {version} is unsupported "
            f"(this tool supports {PERSISTED_SCHEMA_VERSION})",
            path=file_path,
        )
    database_data = document.get("database")
    if not isinstance(database_data, dict):
        raise PersistedModelFormatError(
            "persisted ingestion model has no 'database' object",
            path=file_path,
        )
    units_raw = database_data.get("translation_units", [])
    if not isinstance(units_raw, list):
        raise PersistedModelFormatError(
            "persisted 'translation_units' must be a list",
            path=file_path,
        )
    units: list[TranslationUnit] = []
    for unit_raw in units_raw:
        if not isinstance(unit_raw, dict):
            raise PersistedModelFormatError(
                "persisted translation unit entries must be objects",
                path=file_path,
            )
        units.append(_unit_from_dict(unit_raw))
    build_tag = database_data.get("build_tag")
    return CompilationDatabase(
        translation_units=tuple(units),
        build_tag=str(build_tag) if build_tag is not None else None,
    )

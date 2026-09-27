# implements: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090
"""Error classes for ectt C front-end binding and analysis.

Satisfies: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090.
"""

from __future__ import annotations

from pathlib import Path

from ectt.core.determinism import CoreError

__all__ = [
    "AnalysisError",
    "LibclangError",
    "LibclangNotFoundError",
    "LibclangLoadError",
    "LibclangVersionError",
    "DialectError",
    "UnsupportedDialectError",
    "SourceFileNotFoundError",
    "FrontendParseError",
    "ExtractionError",
    "ExtractionRefusedError",
    "AnalysisModelError",
    "SchemaVersionError",
    "MissingSchemaVersionError",
    "InvalidSchemaVersionOrderError",
    "MalformedSchemaVersionError",
    "IncompatibleSchemaVersionError",
    "TypeMergeError",
    "TypeDefinitionConflictError",
    "TypeClosureError",
]


class AnalysisError(CoreError):
    """Base exception for ectt analysis and C front-end errors."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "analysis_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)

    def __str__(self) -> str:
        details: list[str] = [f"reason={self.reason}"]
        if self.path is not None:
            details.append(f"path={self.path}")
        return f"{self.message} [{', '.join(details)}]"


class LibclangError(AnalysisError):
    """Base exception for libclang library and binding issues."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "libclang_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class LibclangNotFoundError(LibclangError):
    """Raised when the libclang Python package/bindings cannot be imported."""

    def __init__(
        self,
        message: str = "libclang Python bindings are not installed or cannot be found",
        *,
        reason: str = "libclang_not_found",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class LibclangLoadError(LibclangError):
    """Raised when the libclang native shared library fails to load."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "libclang_load_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class LibclangVersionError(LibclangError):
    """Raised when loaded libclang version is below the required version floor."""

    def __init__(
        self,
        message: str,
        *,
        version: str | None = None,
        floor: str = "18.1",
        reason: str = "libclang_version_below_floor",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
        self.version = version
        self.floor = floor

    def __str__(self) -> str:
        details: list[str] = [f"reason={self.reason}", f"floor={self.floor}"]
        if self.version is not None:
            details.append(f"version={self.version}")
        if self.path is not None:
            details.append(f"path={self.path}")
        return f"{self.message} [{', '.join(details)}]"


class DialectError(AnalysisError):
    """Base exception for C language standard dialect errors."""

    def __init__(
        self,
        message: str,
        *,
        dialect: str | None = None,
        reason: str = "dialect_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
        self.dialect = dialect

    def __str__(self) -> str:
        details: list[str] = [f"reason={self.reason}"]
        if self.dialect is not None:
            details.append(f"dialect={self.dialect}")
        if self.path is not None:
            details.append(f"path={self.path}")
        return f"{self.message} [{', '.join(details)}]"


class UnsupportedDialectError(DialectError):
    """Raised when an unsupported or unrecognized C dialect standard is specified."""

    def __init__(
        self,
        message: str,
        *,
        dialect: str | None = None,
        reason: str = "unsupported_dialect",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, dialect=dialect, reason=reason, path=path)


class SourceFileNotFoundError(AnalysisError):
    """Raised when a translation unit source file does not exist on disk."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "source_file_not_found",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class FrontendParseError(AnalysisError):
    """Raised when libclang encounters an unrecoverable parse or translation unit loading failure."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "frontend_parse_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class ExtractionError(AnalysisError):
    """Base exception for interface, type, or global extraction errors."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "extraction_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class ExtractionRefusedError(ExtractionError):
    """Raised when extraction is refused on a failed or unparsed translation unit."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "extraction_refused_failed_unit",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class AnalysisModelError(AnalysisError):
    """Base exception for analysis model validation, persistence, and schema errors."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "analysis_model_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class SchemaVersionError(AnalysisModelError):
    """Base exception for analysis model schema version violations."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "schema_version_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class MissingSchemaVersionError(SchemaVersionError):
    """Raised when schema_version is absent from an analysis model document."""

    def __init__(
        self,
        message: str = "Missing 'schema_version' in analysis model document",
        *,
        reason: str = "missing_schema_version",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class InvalidSchemaVersionOrderError(SchemaVersionError):
    """Raised when schema_version is present but is not the first key in the document."""

    def __init__(
        self,
        message: str = "'schema_version' must be the first key in the analysis model document",
        *,
        reason: str = "schema_version_not_first",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class MalformedSchemaVersionError(SchemaVersionError):
    """Raised when schema_version does not conform to the expected 'MAJOR.MINOR' format."""

    def __init__(
        self,
        message: str,
        *,
        version: Any = None,
        reason: str = "malformed_schema_version",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
        self.version = version


class IncompatibleSchemaVersionError(SchemaVersionError):
    """Raised when an analysis model has an incompatible major version or unsupported minor version.

    Implements: SDD-002 §3.
    """

    def __init__(
        self,
        message: str,
        *,
        reader_version: str = "1.0",
        document_version: str,
        reason: str = "incompatible_schema_version",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
        self.reader_version = reader_version
        self.document_version = document_version

    def __str__(self) -> str:
        details: list[str] = [
            f"reason={self.reason}",
            f"reader_version={self.reader_version}",
            f"document_version={self.document_version}",
        ]
        if self.path is not None:
            details.append(f"path={self.path}")
        return f"{self.message} [{', '.join(details)}]"


class TypeMergeError(AnalysisModelError):
    """Base exception for model-wide type graph merging errors."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "type_merge_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class TypeDefinitionConflictError(TypeMergeError):
    """Raised when conflicting definitions for the same type ID appear in different translation units.

    Implements: SDD-002 §4.1, DSN-ANA-070.
    """

    def __init__(
        self,
        message: str,
        *,
        type_id: str,
        unit_a: str,
        unit_b: str,
        reason: str = "type_definition_conflict",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
        self.type_id = type_id
        self.unit_a = unit_a
        self.unit_b = unit_b

    def __str__(self) -> str:
        details: list[str] = [
            f"reason={self.reason}",
            f"type_id={self.type_id}",
            f"unit_a={self.unit_a}",
            f"unit_b={self.unit_b}",
        ]
        if self.path is not None:
            details.append(f"path={self.path}")
        return f"{self.message} [{', '.join(details)}]"


class TypeClosureError(TypeMergeError):
    """Raised when a type reference (ref:type.*) does not resolve in the model-wide types map.

    Implements: SDD-002 §4.2.
    """

    def __init__(
        self,
        message: str,
        *,
        ref: str,
        reason: str = "type_closure_violation",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
        self.ref = ref

    def __str__(self) -> str:
        details: list[str] = [f"reason={self.reason}", f"ref={self.ref}"]
        if self.path is not None:
            details.append(f"path={self.path}")
        return f"{self.message} [{', '.join(details)}]"

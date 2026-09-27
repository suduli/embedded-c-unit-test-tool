# implements: DSN-PRJ-010, DSN-PRJ-040, DSN-PRJ-030
"""Error classes for ectt project store and serialization.

Satisfies: TOOL-PRJ-010, TOOL-PRJ-020, TOOL-PRJ-070, TOOL-UIX-360.
"""

from __future__ import annotations

from pathlib import Path

from ectt.core.fs import CoreError

__all__ = [
    "ProjectError",
    # YAML restriction errors
    "RestrictedYamlError",
    "YamlSyntaxError",
    "AnchorForbiddenError",
    "TagForbiddenError",
    "MergeKeyForbiddenError",
    "DuplicateKeyError",
    "MultiDocumentForbiddenError",
    "NonStringKeyError",
    "EmptyDocumentError",
    "NotAMappingError",
    # Comment preservation error
    "CommentPreservationError",
    # Schema version errors
    "SchemaVersionError",
    "MissingSchemaVersionError",
    "InvalidSchemaVersionError",
    "UnsupportedSchemaVersionError",
    "MigrationRequiredError",
    # Project lifecycle and path errors
    "ProjectRootNotFoundError",
    "ProjectPathError",
    "InvalidRelativePathError",
    "ProjectConfinementError",
    "ProjectLocationError",
]


class ProjectError(CoreError):
    """Base exception for ectt project store operations."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "project_error",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
        self.line = line
        self.column = column

    def __str__(self) -> str:
        details: list[str] = [f"reason={self.reason}"]
        if self.path is not None:
            details.append(f"path={self.path}")
        if self.line is not None:
            details.append(f"line={self.line}")
        if self.column is not None:
            details.append(f"column={self.column}")
        return f"{self.message} [{', '.join(details)}]"


# --- Restricted YAML Parser Errors ---


class RestrictedYamlError(ProjectError):
    """Base exception for restricted YAML syntax and policy violations."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "restricted_yaml_error",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


class YamlSyntaxError(RestrictedYamlError):
    """Raised when YAML syntax is malformed."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "yaml_syntax_error",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


class AnchorForbiddenError(RestrictedYamlError):
    """Raised when YAML anchors (&) or aliases (*) are encountered."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "anchor_forbidden",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


class TagForbiddenError(RestrictedYamlError):
    """Raised when explicit YAML tags (! or !!) are encountered."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "tag_forbidden",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


class MergeKeyForbiddenError(RestrictedYamlError):
    """Raised when YAML merge keys (<<) are encountered."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "merge_key_forbidden",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


class DuplicateKeyError(RestrictedYamlError):
    """Raised when duplicate keys are encountered in a mapping."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "duplicate_key",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


class MultiDocumentForbiddenError(RestrictedYamlError):
    """Raised when a stream contains more than one YAML document."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "multi_document_forbidden",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


class NonStringKeyError(RestrictedYamlError):
    """Raised when a mapping key is not a string scalar."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "non_string_key",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


class EmptyDocumentError(RestrictedYamlError):
    """Raised when a project file is empty or contains no document."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "empty_document",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


class NotAMappingError(RestrictedYamlError):
    """Raised when the root of a project file is not a mapping."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "not_a_mapping",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


# --- Comment Overwrite Error ---


class CommentPreservationError(ProjectError):
    """Raised when saving over a file that contains comments without discard_comments=True."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "comment_preservation_refused",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


# --- Schema Version Errors ---


class SchemaVersionError(ProjectError):
    """Base exception for schema version dispatch errors."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "schema_version_error",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


class MissingSchemaVersionError(SchemaVersionError):
    """Raised when schema_version key is absent in a project file."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "missing_schema_version",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


class InvalidSchemaVersionError(SchemaVersionError):
    """Raised when schema_version cannot be parsed as an integer."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "invalid_schema_version",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)


class UnsupportedSchemaVersionError(SchemaVersionError):
    """Raised when schema_version exceeds the maximum version supported by the tool."""

    def __init__(
        self,
        message: str,
        *,
        version: int | None = None,
        min_version: int | None = None,
        max_version: int | None = None,
        reason: str = "unsupported_schema_version",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)
        self.version = version
        self.min_version = min_version
        self.max_version = max_version


class MigrationRequiredError(SchemaVersionError):
    """Raised when schema_version is less than the minimum supported version."""

    def __init__(
        self,
        message: str,
        *,
        version: int | None = None,
        min_version: int | None = None,
        reason: str = "migration_required",
        path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, line=line, column=column)
        self.version = version
        self.min_version = min_version


# --- Project Lifecycle and Path Errors ---


class ProjectRootNotFoundError(ProjectError):
    """Raised when walking upward fails to locate an ectt.project marker."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "project_root_not_found",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class ProjectPathError(ProjectError):
    """Base exception for invalid or escaping paths in project references."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "project_path_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class InvalidRelativePathError(ProjectPathError):
    """Raised when a path is absolute, has a drive letter/UNC prefix, or escapes root via '..'."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "invalid_relative_path",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class ProjectConfinementError(ProjectPathError):
    """Raised when a path targets a file escaping the project root boundary."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "project_confinement_violation",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class ProjectLocationError(ProjectPathError):
    """Raised when a project file is targeted inside user source roots or the output root."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "disallowed_project_location",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)

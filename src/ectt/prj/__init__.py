# implements: DSN-PRJ-010, DSN-PRJ-040, DSN-PRJ-030
"""ECTT Project Data Management and Storage.

Provides plain-text, schema-versioned, deterministic storage for ectt project trees:
- Restricted YAML loader and deterministic emitter with scalar typing hazard protections.
- Schema versioning and migration dispatch per SDD-003 §5.
- Relative-only, POSIX-normalized path confinement and relocation safety.
- Atomic project writes preserving byte-identity and preventing silent comment loss.

Satisfies: TOOL-PRJ-010, TOOL-PRJ-020, TOOL-PRJ-050, TOOL-PRJ-070, TOOL-UIX-320, TOOL-CIC-080.
"""

from ectt.prj.errors import (
    AnchorForbiddenError,
    CommentPreservationError,
    DuplicateKeyError,
    EmptyDocumentError,
    InvalidRelativePathError,
    InvalidSchemaVersionError,
    MergeKeyForbiddenError,
    MigrationRequiredError,
    MissingSchemaVersionError,
    MultiDocumentForbiddenError,
    NonStringKeyError,
    NotAMappingError,
    ProjectConfinementError,
    ProjectError,
    ProjectLocationError,
    ProjectPathError,
    ProjectRootNotFoundError,
    RestrictedYamlError,
    SchemaVersionError,
    TagForbiddenError,
    UnsupportedSchemaVersionError,
    YamlSyntaxError,
)
from ectt.prj.model import (
    DEFAULT_KIND_REGISTRY,
    PROJECT_KIND,
    FileKind,
    KindRegistry,
    ProjectDocument,
    dispatch_schema_version,
)
from ectt.prj.paths import (
    normalize_posix_path,
    resolve_project_path,
    validate_project_path,
)
from ectt.prj.project import (
    PROJECT_ROOT_MARKER,
    Project,
)
from ectt.prj.yaml_adapter import (
    RestrictedYamlAdapter,
    SerializationAdapter,
    detect_yaml_comments,
)

__all__ = [
    # Errors
    "ProjectError",
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
    "CommentPreservationError",
    "SchemaVersionError",
    "MissingSchemaVersionError",
    "InvalidSchemaVersionError",
    "UnsupportedSchemaVersionError",
    "MigrationRequiredError",
    "ProjectRootNotFoundError",
    "ProjectPathError",
    "InvalidRelativePathError",
    "ProjectConfinementError",
    "ProjectLocationError",
    # Paths
    "validate_project_path",
    "resolve_project_path",
    "normalize_posix_path",
    # YAML and Serialization
    "SerializationAdapter",
    "RestrictedYamlAdapter",
    "detect_yaml_comments",
    # Model and Registry
    "FileKind",
    "KindRegistry",
    "PROJECT_KIND",
    "DEFAULT_KIND_REGISTRY",
    "dispatch_schema_version",
    "ProjectDocument",
    # Project lifecycle
    "PROJECT_ROOT_MARKER",
    "Project",
]

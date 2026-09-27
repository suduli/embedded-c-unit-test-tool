# implements: TOOL-PAR-010, TOOL-PAR-020, TOOL-PAR-030, TOOL-PAR-040, TOOL-PAR-050, DSN-ANA-090, DSN-ANA-020, DSN-ANA-070
"""C front-end binding, analysis, and persistence subsystem (CMP-ANA).

Owns the sole libclang dependency in ectt per SDD-001 S4.2 and SDD-005 S5.3.
Front-end bindings are loaded lazily so that importing persist/reader modules
does not load libclang (SDD-002 S4).

Satisfies: TOOL-PAR-010, TOOL-PAR-020, TOOL-PAR-030, TOOL-PAR-040, TOOL-PAR-050,
           TOOL-PAR-100, TOOL-PAR-110, DSN-ANA-090, DSN-ANA-020, DSN-ANA-070.
"""

from __future__ import annotations

from typing import Any

from ectt.ana.errors import (
    AnalysisError,
    AnalysisModelError,
    DialectError,
    ExtractionError,
    ExtractionRefusedError,
    FrontendParseError,
    IncompatibleSchemaVersionError,
    InvalidSchemaVersionOrderError,
    LibclangError,
    LibclangLoadError,
    LibclangNotFoundError,
    LibclangVersionError,
    MalformedSchemaVersionError,
    MissingSchemaVersionError,
    SourceFileNotFoundError,
    TypeClosureError,
    TypeDefinitionConflictError,
    TypeMergeError,
    UnsupportedDialectError,
)
from ectt.ana.model import (
    AnalysisModel,
    AnalysisUnit,
    Diagnostic,
    EnumeratorModel,
    FunctionModel,
    GlobalAccessModel,
    InputFileModel,
    ParameterModel,
    ParsedTranslationUnit,
    ParseResult,
    ProvenanceModel,
    SourceLocation,
    StructMemberModel,
    TypeModel,
)
from ectt.ana.persist import (
    READER_MAJOR,
    READER_MIN_MINOR,
    assemble_analysis_model,
    compute_model_digest,
    load_analysis_model,
    read_analysis_model,
    write_analysis_model,
)

_FRONTEND_ATTRS = {
    "ClangFrontend",
    "parse",
    "get_libclang_version",
    "get_libclang_version_tuple",
    "is_supported_dialect",
    "normalize_dialect",
    "normalize_path",
    "extract_include_dirs",
    "resolve_source_location_path",
    "SUPPORTED_DIALECTS",
    "ISO_DIALECTS",
    "GNU_DIALECTS",
    "LIBCLANG_FLOOR_VERSION",
}

_INTERFACE_ATTRS = {
    "extract_interfaces",
    "extract",
}

_TYPES_ATTRS = {
    "TypeGraphBuilder",
}


def __getattr__(name: str) -> Any:
    """Lazily load front-end, interface extraction, and type builder symbols on access."""
    if name in _FRONTEND_ATTRS:
        import ectt.ana.frontend as fe

        return getattr(fe, name)
    if name in _INTERFACE_ATTRS:
        import ectt.ana.interface as iface

        return getattr(iface, name)
    if name in _TYPES_ATTRS:
        import ectt.ana.types as t

        return getattr(t, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Binding & frontend (lazy)
    "ClangFrontend",
    "parse",
    "get_libclang_version",
    "get_libclang_version_tuple",
    "is_supported_dialect",
    "normalize_dialect",
    "normalize_path",
    "extract_include_dirs",
    "resolve_source_location_path",
    "SUPPORTED_DIALECTS",
    "ISO_DIALECTS",
    "GNU_DIALECTS",
    "LIBCLANG_FLOOR_VERSION",
    # Interface & extraction (lazy)
    "extract_interfaces",
    "extract",
    "TypeGraphBuilder",
    # Model
    "Diagnostic",
    "ParsedTranslationUnit",
    "ParseResult",
    "SourceLocation",
    "ParameterModel",
    "GlobalAccessModel",
    "FunctionModel",
    "StructMemberModel",
    "EnumeratorModel",
    "TypeModel",
    "AnalysisUnit",
    "InputFileModel",
    "ProvenanceModel",
    "AnalysisModel",
    # Persistence
    "READER_MAJOR",
    "READER_MIN_MINOR",
    "assemble_analysis_model",
    "write_analysis_model",
    "read_analysis_model",
    "load_analysis_model",
    "compute_model_digest",
    # Errors
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

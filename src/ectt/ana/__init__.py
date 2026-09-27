# implements: TOOL-PAR-010, TOOL-PAR-020, TOOL-PAR-030, TOOL-PAR-040, TOOL-PAR-050, DSN-ANA-090, DSN-ANA-020
"""C front-end binding and analysis subsystem (CMP-ANA).

Owns the sole libclang dependency in ectt per SDD-001 S4.2 and SDD-005 S5.3.

Satisfies: TOOL-PAR-010, TOOL-PAR-020, TOOL-PAR-030, TOOL-PAR-040, TOOL-PAR-050, DSN-ANA-090, DSN-ANA-020.
"""

from __future__ import annotations

from ectt.ana.errors import (
    AnalysisError,
    DialectError,
    ExtractionError,
    ExtractionRefusedError,
    FrontendParseError,
    LibclangError,
    LibclangLoadError,
    LibclangNotFoundError,
    LibclangVersionError,
    SourceFileNotFoundError,
    UnsupportedDialectError,
)
from ectt.ana.frontend import (
    GNU_DIALECTS,
    ISO_DIALECTS,
    LIBCLANG_FLOOR_VERSION,
    SUPPORTED_DIALECTS,
    ClangFrontend,
    get_libclang_version,
    get_libclang_version_tuple,
    is_supported_dialect,
    normalize_dialect,
    normalize_path,
    extract_include_dirs,
    resolve_source_location_path,
    parse,
)
from ectt.ana.interface import (
    extract,
    extract_interfaces,
)
from ectt.ana.model import (
    AnalysisUnit,
    Diagnostic,
    EnumeratorModel,
    FunctionModel,
    GlobalAccessModel,
    ParameterModel,
    ParsedTranslationUnit,
    ParseResult,
    SourceLocation,
    StructMemberModel,
    TypeModel,
)
from ectt.ana.types import TypeGraphBuilder

__all__ = [
    # Binding & frontend
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
    # Interface & extraction
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
]

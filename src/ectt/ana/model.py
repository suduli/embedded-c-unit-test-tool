# implements: DSN-ANA-090, DSN-ANA-020
"""Data model for translation units, function interfaces, and type graphs.

Satisfies: TOOL-PAR-010, TOOL-PAR-020, TOOL-PAR-030, TOOL-PAR-040, TOOL-PAR-050, DSN-ANA-090, DSN-ANA-020.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ectt.core.determinism import canonical_json

__all__ = [
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
]


@dataclass(frozen=True)
class Diagnostic:
    """Normalized diagnostic produced during translation unit parsing.

    Attributes:
        message: Human-readable diagnostic message text.
        severity: Severity string ('ignored', 'note', 'warning', 'error', 'fatal').
        severity_code: Raw libclang diagnostic severity integer (0=Ignored, 1=Note, 2=Warning, 3=Error, 4=Fatal).
        file: Normalized source file path where diagnostic occurred (if known).
        line: 1-indexed source line number (if known).
        column: 1-indexed source column number (if known).
        category: Optional diagnostic category name.
    """

    message: str
    severity: str
    severity_code: int = 0
    file: str | None = None
    line: int | None = None
    column: int | None = None
    category: str | None = None

    @property
    def is_error(self) -> bool:
        """Return True if this diagnostic is an error or fatal error."""
        return self.severity in ("error", "fatal") or self.severity_code >= 3

    def to_dict(self) -> dict[str, Any]:
        """Return plain dictionary representation."""
        result: dict[str, Any] = {
            "message": self.message,
            "severity": self.severity,
            "severity_code": self.severity_code,
        }
        if self.file is not None:
            result["file"] = self.file
        if self.line is not None:
            result["line"] = self.line
        if self.column is not None:
            result["column"] = self.column
        if self.category is not None:
            result["category"] = self.category
        return result

    def __str__(self) -> str:
        """Formatted string representation."""
        loc = ""
        if self.file is not None:
            loc = self.file
            if self.line is not None:
                loc += f":{self.line}"
                if self.column is not None:
                    loc += f":{self.column}"
            loc += ": "
        return f"{loc}{self.severity}: {self.message}"


@dataclass(frozen=True)
class ParsedTranslationUnit:
    """In-memory result of parsing a translation unit with the C front-end.

    Implements: DSN-ANA-090.

    Attributes:
        source_path: POSIX-normalized relative or reference path of the translation unit.
        status: Parse status per DSN-ANA-090: 'parsed' on success, 'failed' on error.
        diagnostics: Sequence of normalized diagnostics in parse order.
        translation_unit: Handle to the underlying libclang TranslationUnit (if available).
    """

    source_path: str
    status: str  # "parsed" | "failed" (DSN-ANA-090)
    diagnostics: tuple[Diagnostic, ...] = field(default_factory=tuple)
    translation_unit: Any = field(default=None, repr=False)
    arguments: tuple[str, ...] = field(default_factory=tuple)
    include_dirs: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_parsed(self) -> bool:
        """Return True if status is 'parsed'."""
        return self.status == "parsed"

    @property
    def is_failed(self) -> bool:
        """Return True if status is 'failed'."""
        return self.status == "failed"

    @property
    def has_errors(self) -> bool:
        """Return True if any diagnostic is an error or fatal diagnostic."""
        return any(d.is_error for d in self.diagnostics)

    @property
    def errors(self) -> tuple[Diagnostic, ...]:
        """Return all error and fatal diagnostics."""
        return tuple(d for d in self.diagnostics if d.is_error)

    @property
    def warnings(self) -> tuple[Diagnostic, ...]:
        """Return all warning diagnostics."""
        return tuple(d for d in self.diagnostics if d.severity == "warning")

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation matching SDD-002 S4.1 unit shape."""
        return {
            "path": self.source_path,
            "status": self.status,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }

    def to_json(self, *, indent: int | None = None) -> str:
        """Return deterministic canonical JSON representation."""
        return canonical_json(self.to_dict(), indent=indent)


# ParseResult is an alias for ParsedTranslationUnit
ParseResult = ParsedTranslationUnit


@dataclass(frozen=True)
class SourceLocation:
    """Source file path, line number, and origin.

    Attributes:
        file: Normalized relative source file path.
        line: 1-indexed source line number.
        origin: 'project' | 'include' | 'external'.
    """

    file: str
    line: int
    origin: str | None = "project"

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        res: dict[str, Any] = {"file": self.file, "line": self.line}
        if self.origin is not None:
            res["origin"] = self.origin
        return res


@dataclass(frozen=True)
class ParameterModel:
    """Function or callback parameter description."""

    name: str
    type: str
    direction: str = "unknown"  # "in" | "unknown" (SDD-002 §4.1)

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        return {
            "name": self.name,
            "type": self.type,
            "direction": self.direction,
        }


@dataclass(frozen=True)
class GlobalAccessModel:
    """Global or file-static variable access by a function."""

    name: str
    access: str  # "r" | "w" | "rw" (SDD-002 §4.1)

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        return {
            "name": self.name,
            "access": self.access,
        }


@dataclass(frozen=True)
class FunctionModel:
    """Extracted function interface and variable accesses.

    Implements: TOOL-PAR-030, TOOL-PAR-050, DSN-ANA-020.
    """

    name: str
    linkage: str  # "external" | "internal"
    storage_class: str  # "none" | "static"
    location: SourceLocation
    return_type: str  # "ref:type.<id>"
    parameters: tuple[ParameterModel, ...] = field(default_factory=tuple)
    globals: tuple[GlobalAccessModel, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation matching SDD-002 §4.1."""
        return {
            "name": self.name,
            "linkage": self.linkage,
            "storage_class": self.storage_class,
            "location": self.location.to_dict(),
            "return_type": self.return_type,
            "parameters": [p.to_dict() for p in self.parameters],
            "globals": [g.to_dict() for g in self.globals],
        }


@dataclass(frozen=True)
class StructMemberModel:
    """Member field of a struct or union."""

    name: str
    type: str  # "ref:type.<id>"
    bit_width: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        res: dict[str, Any] = {"name": self.name, "type": self.type}
        if self.bit_width is not None:
            res["bit_width"] = self.bit_width
        return res


@dataclass(frozen=True)
class EnumeratorModel:
    """Constant value within an enumeration."""

    name: str
    value: int

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        return {"name": self.name, "value": self.value}


@dataclass(frozen=True)
class TypeModel:
    """Type entry in the S1 type graph.

    Implements: TOOL-PAR-040, DSN-ANA-020.
    """

    kind: str  # "struct" | "union" | "enum" | "typedef" | "function_pointer" | "builtin" | "pointer" | "array"
    name: str | None = None
    location: SourceLocation | None = None
    underlying_type: str | None = None
    target: str | None = None
    element_type: str | None = None
    size: int | None = None
    is_const: bool | None = None
    return_type: str | None = None
    parameters: tuple[ParameterModel, ...] = field(default_factory=tuple)
    members: tuple[StructMemberModel, ...] = field(default_factory=tuple)
    enumerators: tuple[EnumeratorModel, ...] = field(default_factory=tuple)
    is_anonymous: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation conforming to SDD-002 §4.1."""
        res: dict[str, Any] = {"kind": self.kind}
        if self.name is not None:
            res["name"] = self.name
        if self.location is not None:
            res["location"] = self.location.to_dict()
        if self.is_anonymous:
            res["is_anonymous"] = True

        if self.kind in ("struct", "union"):
            res["members"] = [m.to_dict() for m in self.members]
        elif self.kind == "enum":
            res["enumerators"] = [e.to_dict() for e in self.enumerators]
            if self.underlying_type is not None:
                res["underlying_type"] = self.underlying_type
        elif self.kind == "typedef":
            if self.underlying_type is not None:
                res["underlying_type"] = self.underlying_type
        elif self.kind == "function_pointer":
            if self.return_type is not None:
                res["return_type"] = self.return_type
            res["parameters"] = [p.to_dict() for p in self.parameters]
        elif self.kind == "pointer":
            if self.target is not None:
                res["target"] = self.target
            if self.is_const is not None:
                res["is_const"] = self.is_const
        elif self.kind == "array":
            if self.element_type is not None:
                res["element_type"] = self.element_type
            res["size"] = self.size
        elif self.kind == "builtin":
            if self.name is not None:
                res["name"] = self.name

        return res


@dataclass(frozen=True)
class AnalysisUnit:
    """Extracted unit containing functions, types, and diagnostics.

    Implements: TOOL-PAR-030, TOOL-PAR-040, TOOL-PAR-050, DSN-ANA-020.
    """

    path: str
    status: str
    diagnostics: tuple[Diagnostic, ...] = field(default_factory=tuple)
    functions: tuple[FunctionModel, ...] = field(default_factory=tuple)
    types: dict[str, TypeModel] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation matching SDD-002 §4.1 unit shape."""
        return {
            "path": self.path,
            "status": self.status,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "functions": [f.to_dict() for f in self.functions],
            "types": {k: self.types[k].to_dict() for k in sorted(self.types.keys())},
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        """Return deterministic canonical JSON representation."""
        return canonical_json(self.to_dict(), indent=indent)

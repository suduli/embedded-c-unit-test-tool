# implements: DSN-ANA-090, DSN-ANA-020
"""Data model for translation units, function interfaces, and type graphs.

Satisfies: TOOL-PAR-010, TOOL-PAR-020, TOOL-PAR-030, TOOL-PAR-040, TOOL-PAR-050, DSN-ANA-090, DSN-ANA-020.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from ectt.core.determinism import canonical_json, canonical_json_bytes

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
    "InputFileModel",
    "ProvenanceModel",
    "AnalysisModel",
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Diagnostic:
        """Create Diagnostic from dictionary representation."""
        return cls(
            message=data.get("message", ""),
            severity=data.get("severity", "ignored"),
            severity_code=int(data.get("severity_code", 0)),
            file=data.get("file"),
            line=data.get("line"),
            column=data.get("column"),
            category=data.get("category"),
        )

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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceLocation:
        """Create SourceLocation from dictionary representation."""
        return cls(
            file=data.get("file", ""),
            line=int(data.get("line", 0)),
            origin=data.get("origin", "project"),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParameterModel:
        """Create ParameterModel from dictionary representation."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            direction=data.get("direction", "unknown"),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GlobalAccessModel:
        """Create GlobalAccessModel from dictionary representation."""
        return cls(
            name=data.get("name", ""),
            access=data.get("access", "r"),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FunctionModel:
        """Create FunctionModel from dictionary representation."""
        loc_data = data.get("location", {})
        loc = SourceLocation.from_dict(loc_data) if isinstance(loc_data, dict) else SourceLocation("", 0)
        return cls(
            name=data.get("name", ""),
            linkage=data.get("linkage", "external"),
            storage_class=data.get("storage_class", "none"),
            location=loc,
            return_type=data.get("return_type", ""),
            parameters=tuple(ParameterModel.from_dict(p) for p in data.get("parameters", [])),
            globals=tuple(GlobalAccessModel.from_dict(g) for g in data.get("globals", [])),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StructMemberModel:
        """Create StructMemberModel from dictionary representation."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            bit_width=data.get("bit_width"),
        )


@dataclass(frozen=True)
class EnumeratorModel:
    """Constant value within an enumeration."""

    name: str
    value: int

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        return {"name": self.name, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnumeratorModel:
        """Create EnumeratorModel from dictionary representation."""
        return cls(
            name=data.get("name", ""),
            value=int(data.get("value", 0)),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TypeModel:
        """Create TypeModel from dictionary representation."""
        loc_data = data.get("location")
        loc = SourceLocation.from_dict(loc_data) if isinstance(loc_data, dict) else None
        return cls(
            kind=data.get("kind", "builtin"),
            name=data.get("name"),
            location=loc,
            underlying_type=data.get("underlying_type"),
            target=data.get("target"),
            element_type=data.get("element_type"),
            size=data.get("size"),
            is_const=data.get("is_const"),
            return_type=data.get("return_type"),
            parameters=tuple(ParameterModel.from_dict(p) for p in data.get("parameters", [])),
            members=tuple(StructMemberModel.from_dict(m) for m in data.get("members", [])),
            enumerators=tuple(EnumeratorModel.from_dict(e) for e in data.get("enumerators", [])),
            is_anonymous=bool(data.get("is_anonymous", False)),
        )


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

    def to_dict_without_types(self) -> dict[str, Any]:
        """Return dictionary representation matching SDD-002 §4.1 unit shape in model document."""
        return {
            "path": self.path,
            "status": self.status,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "functions": [f.to_dict() for f in self.functions],
            "cfg": None,
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        """Return deterministic canonical JSON representation."""
        return canonical_json(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnalysisUnit:
        """Create AnalysisUnit from dictionary representation."""
        types_raw = data.get("types", {})
        return cls(
            path=data.get("path", ""),
            status=data.get("status", "parsed"),
            diagnostics=tuple(Diagnostic.from_dict(d) for d in data.get("diagnostics", [])),
            functions=tuple(FunctionModel.from_dict(f) for f in data.get("functions", [])),
            types={k: TypeModel.from_dict(v) for k, v in types_raw.items()} if isinstance(types_raw, dict) else {},
        )


@dataclass(frozen=True)
class InputFileModel:
    """Translation unit main source file reference and content digest."""

    path: str
    digest: str

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        return {"path": self.path, "digest": self.digest}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InputFileModel:
        """Create InputFileModel from dictionary representation."""
        return cls(path=data.get("path", ""), digest=data.get("digest", ""))


@dataclass(frozen=True)
class ProvenanceModel:
    """Tool version, front-end details, timestamp, and input digests for an analysis model."""

    tool_version: str
    front_end: str
    generated_at: str
    inputs: tuple[InputFileModel, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation."""
        return {
            "tool_version": self.tool_version,
            "front_end": self.front_end,
            "generated_at": self.generated_at,
            "inputs": [i.to_dict() for i in sorted(self.inputs, key=lambda inp: inp.path)],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProvenanceModel:
        """Create ProvenanceModel from dictionary representation."""
        return cls(
            tool_version=data.get("tool_version", ""),
            front_end=data.get("front_end", ""),
            generated_at=data.get("generated_at", ""),
            inputs=tuple(InputFileModel.from_dict(i) for i in data.get("inputs", [])),
        )


@dataclass(frozen=True)
class AnalysisModel:
    """Top-level S1 Analysis Model document.

    Implements: SDD-002 §4.1, DSN-ANA-070.
    Satisfies: TOOL-PAR-100, TOOL-PAR-110.
    """

    provenance: ProvenanceModel
    units: tuple[AnalysisUnit, ...] = field(default_factory=tuple)
    types: dict[str, TypeModel] = field(default_factory=dict)
    schema_version: str = "1.0"
    capabilities: dict[str, bool] = field(default_factory=lambda: {"cfg": False})

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation conforming to SDD-002 §4.1."""
        return {
            "schema_version": self.schema_version,
            "provenance": self.provenance.to_dict(),
            "units": [u.to_dict_without_types() for u in self.units],
            "types": {k: self.types[k].to_dict() for k in sorted(self.types.keys())},
            "capabilities": dict(self.capabilities),
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        """Return deterministic canonical JSON representation with schema_version first."""
        return canonical_json(self.to_dict(), indent=indent, first_keys=("schema_version",))

    def to_json_bytes(self, *, indent: int | None = 2) -> bytes:
        """Return UTF-8 encoded canonical JSON bytes with schema_version first."""
        return canonical_json_bytes(self.to_dict(), indent=indent, first_keys=("schema_version",))

    def content_digest(self) -> str:
        """Compute stable content digest excluding provenance.generated_at."""
        doc = self.to_dict()
        if "provenance" in doc and isinstance(doc["provenance"], dict):
            doc["provenance"].pop("generated_at", None)
        return hashlib.sha256(canonical_json_bytes(doc)).hexdigest()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnalysisModel:
        """Create AnalysisModel from dictionary representation."""
        prov = data.get("provenance", {})
        types_raw = data.get("types", {})
        return cls(
            schema_version=data.get("schema_version", "1.0"),
            provenance=ProvenanceModel.from_dict(prov) if isinstance(prov, dict) else ProvenanceModel("", "", ""),
            units=tuple(AnalysisUnit.from_dict(u) for u in data.get("units", [])),
            types={k: TypeModel.from_dict(v) for k, v in types_raw.items()} if isinstance(types_raw, dict) else {},
            capabilities=dict(data.get("capabilities", {"cfg": False})),
        )

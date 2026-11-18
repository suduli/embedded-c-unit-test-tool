"""Stub generation core (WP-GEN-06).

One stub per external function (fed by the WP-ING-05 requirement list), each
with a signature identical to the function it replaces, the forward
declarations and type declarations needed to compile independently, and a
greppable stub marker.

Satisfies: TOOL-STB-010, TOOL-STB-020, TOOL-STB-030.
"""

from __future__ import annotations

from dataclasses import dataclass

from ectt.ana.model import TypeModel
from ectt.gen.errors import GenError

__all__ = [
    "STUB_MARKER",
    "FunctionSignature",
    "Stub",
    "StubUnit",
    "DuplicateStubError",
    "generate_stubs",
]

STUB_MARKER = "ectt:stub"


class DuplicateStubError(GenError):
    """Raised when two stubs would carry the same function name."""

    def __init__(self, message: str, *, reason: str = "duplicate_stub") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class FunctionSignature:
    """The signature of an external function to stub."""

    name: str
    return_type: str
    parameters: tuple[tuple[str, str], ...] = ()  # (C type, parameter name)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise GenError("stub function name must be a non-empty string", reason="invalid_signature")
        if not isinstance(self.return_type, str) or not self.return_type.strip():
            raise GenError(
                f"stub '{self.name}' return type must be a non-empty string",
                reason="invalid_signature",
            )
        for c_type, parameter_name in self.parameters:
            if not isinstance(c_type, str) or not c_type.strip():
                raise GenError(
                    f"stub '{self.name}' has an empty parameter type",
                    reason="invalid_signature",
                )
            if not isinstance(parameter_name, str) or not parameter_name.strip():
                raise GenError(
                    f"stub '{self.name}' has an empty parameter name",
                    reason="invalid_signature",
                )

    def signature_text(self) -> str:
        """The canonical signature: identical to what the stub emits (STB-020)."""
        parameters = ", ".join(f"{c_type} {name}" for c_type, name in self.parameters)
        return f"{self.return_type} {self.name}({parameters or 'void'})"


@dataclass(frozen=True)
class Stub:
    """One generated stub."""

    signature: FunctionSignature
    c_text: str


@dataclass(frozen=True)
class StubUnit:
    """The complete stub output for one link unit."""

    stubs: tuple[Stub, ...]
    type_declarations: tuple[str, ...]
    source: str

    def signature_texts(self) -> tuple[str, ...]:
        """Every stub's signature, in unit order."""
        return tuple(stub.signature.signature_text() for stub in self.stubs)


_RETURN_ZERO: dict[str, str] = {
    "int": "return 0;",
    "long": "return 0L;",
    "long long": "return 0LL;",
    "unsigned": "return 0u;",
    "unsigned long": "return 0ul;",
    "unsigned long long": "return 0ull;",
    "short": "return 0;",
    "char": "return 0;",
    "_Bool": "return 0;",
    "bool": "return false;",
    "float": "return 0.0f;",
    "double": "return 0.0;",
    "long double": "return 0.0L;",
    "void": "return;",
}


def _default_return(return_type: str) -> str:
    zero = _RETURN_ZERO.get(return_type)
    if zero is not None:
        return f"    {zero} /* {STUB_MARKER}: default value */"
    return f"    return ({return_type})0; /* {STUB_MARKER}: default value */"


def _candidate_keys(ref: str) -> tuple[str, ...]:
    """Type-graph keys a C spelling or model ref could resolve to."""
    if ref.startswith("ref:"):
        return (ref[len("ref:"):],)
    for keyword in ("struct ", "union ", "enum "):
        if ref.startswith(keyword):
            tail = ref[len(keyword):].strip()
            return (f"type.{keyword.strip()}.{tail}", f"type.{tail}")
    return (f"type.{ref.strip()}",)


def _required_type_declarations(
    signatures: tuple[FunctionSignature, ...],
    types: dict[str, TypeModel] | None,
) -> tuple[str, ...]:
    """Declarations for struct/typedef types used by the signatures (STB-030)."""
    refs: set[str] = set()
    for signature in signatures:
        for c_type, _name in signature.parameters:
            refs.add(c_type)
        refs.add(signature.return_type)
    declarations: set[str] = set()
    for ref in refs:
        if types is None:
            continue
        type_model: TypeModel | None = None
        for key in _candidate_keys(ref):
            type_model = types.get(key)
            if type_model is not None:
                break
        if type_model is None:
            continue
        if type_model.kind == "struct" and type_model.name:
            declarations.add(f"typedef struct {type_model.name} {type_model.name};")
        elif type_model.kind == "union" and type_model.name:
            declarations.add(f"typedef union {type_model.name} {type_model.name};")
        elif type_model.kind == "enum" and type_model.name:
            declarations.add(f"typedef enum {type_model.name} {type_model.name};")
        elif type_model.kind == "typedef" and type_model.underlying_type:
            declarations.add(f"typedef {type_model.underlying_type} {type_model.name};")
    return tuple(sorted(declarations))


def generate_stubs(
    signatures: tuple[FunctionSignature, ...],
    *,
    types: dict[str, TypeModel] | None = None,
) -> StubUnit:
    """Generate one stub per external signature, deterministically ordered."""
    seen: set[str] = set()
    for signature in signatures:
        if signature.name in seen:
            raise DuplicateStubError(
                f"two stubs would be generated for '{signature.name}'"
            )
        seen.add(signature.name)
    ordered = tuple(sorted(signatures, key=lambda sig: sig.name))
    type_declarations = _required_type_declarations(ordered, types)
    stubs: list[Stub] = []
    lines: list[str] = [
        "/* Generated by ectt - do not edit. Stubs for external functions. */",
        "",
    ]
    lines.extend(f"{declaration}" for declaration in type_declarations)
    if type_declarations:
        lines.append("")
    for signature in ordered:
        parameters = ", ".join(f"{c_type} {name}" for c_type, name in signature.parameters)
        definition = (
            f"{signature.return_type} {signature.name}({parameters or 'void'}) {{\n"
            f"{_default_return(signature.return_type)}\n"
            f"}}"
        )
        stubs.append(Stub(signature=signature, c_text=definition))
        lines.append(definition)
        lines.append("")
    return StubUnit(
        stubs=tuple(stubs),
        type_declarations=type_declarations,
        source="\n".join(lines),
    )

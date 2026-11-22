# implements: TOOL-HAR-040
"""Type-resolved global and file-static exposure for the generated harness (A2).

The analysis model (schema 1.5) records the unit's global and file-static
variables with their type reference, initial-value presence and storage class
(``ectt.ana.model.GlobalVariableModel``). This module turns that inventory into
what the generated harness needs to read and set the variables
(TOOL-HAR-040):

* **visible variables** (storage class ``none`` or ``extern``) get a
  type-resolved ``extern`` declaration in the harness — the declaration is
  emitted only when the model can supply the type; a type the model cannot
  resolve is reported **not reachable** with the named reason
  ``type_not_recorded``, never guessed;
* **file-static variables** (internal linkage) cannot be extern-declared; they
  are reached through the source-inclusion mechanism (the static-exposure
  harness of WP-GEN-03 includes the UUT translation unit, which makes the
  definitions visible) and carry a greppable exposure record instead of a
  declaration.

Everything here is deterministic: exposures are resolved in sorted name order
and the rendered block is byte-stable. There is no C compiler on this machine:
the generated C is verified by parsing (libclang) and by golden text.

Reads the model only; ``ectt.ana`` is not edited.

Satisfies: TOOL-HAR-040.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ectt.ana.model import AnalysisUnit, TypeModel

__all__ = [
    "MECHANISM_EXTERN_DECLARATION",
    "MECHANISM_NOT_REACHABLE",
    "MECHANISM_SOURCE_INCLUSION",
    "REASON_TYPE_NOT_RECORDED",
    "GlobalExposure",
    "render_global_exposure_block",
    "resolve_global_exposures",
    "spell_type",
    "spell_type_parts",
]

#: The variable is visible outside its translation unit: one extern declaration.
MECHANISM_EXTERN_DECLARATION = "extern-declaration"

#: Internal linkage: reached through the source-inclusion harness (WP-GEN-03).
MECHANISM_SOURCE_INCLUSION = "source-inclusion"

#: The model cannot supply the type: no declaration is emitted, never guessed.
MECHANISM_NOT_REACHABLE = "not-reachable"

#: The named reason for an unreachable variable.
REASON_TYPE_NOT_RECORDED = "type_not_recorded"

_GLOBAL_EXPOSURE_BEGIN = "/* ectt:global-exposure begin - resolved from the analysis model (TOOL-HAR-040). */"
_GLOBAL_EXPOSURE_END = "/* ectt:global-exposure end */"


@dataclass(frozen=True)
class GlobalExposure:
    """One model-recorded variable and how the harness reaches it (TOOL-HAR-040).

    ``mechanism`` is one of the three module constants; ``declaration`` is the
    emitted ``extern`` line (only for the extern-declaration mechanism);
    ``reason`` names why a variable is not reachable. ``has_initializer`` is
    the model's initial-value presence (a tentative definition has none).
    ``c_type`` is the full type spelling; ``declarator_suffix`` carries array
    dimensions separately, because in a C declaration they bind to the
    identifier (``extern unsigned char g_buf[8];``), not to the element type.
    """

    name: str
    storage_class: str
    has_initializer: bool
    mechanism: str
    c_type: str = ""
    declarator_suffix: str = ""
    declaration: str | None = None
    reason: str | None = None

    def record(self) -> str:
        """The greppable exposure record line for this variable."""
        kind = self.mechanism
        type_text = self.c_type or "-"
        reason_text = f" reason={self.reason}" if self.reason else ""
        return (
            f"/* ectt:exposes-global-var: {self.name} {kind} {type_text} "
            f"storage={self.storage_class} has-initializer={str(self.has_initializer).lower()}"
            f"{reason_text} */"
        )


def spell_type_parts(
    type_ref: str, types: Mapping[str, TypeModel], _visiting: tuple[str, ...] = ()
) -> tuple[str, str] | None:
    """The base type spelling and declarator suffix of a ``ref:type.<id>``.

    Arrays return their element spelling and the dimension suffix separately
    (``("unsigned char", "[8]")``), because in a C declaration the dimensions
    bind to the identifier, not to the element type. Returns ``None`` when the
    reference is not in the graph (or a chain step is missing) — the caller
    reports that as ``type_not_recorded`` instead of inventing a spelling. A
    recursive chain is refused rather than looped.
    """
    key = type_ref.removeprefix("ref:")
    if key in _visiting:
        return None
    model = types.get(key)
    if model is None:
        return None
    trail = (*_visiting, key)
    if model.kind in ("builtin", "typedef", "struct", "union", "enum"):
        if model.name:
            # A struct/union/enum name is a tag: C refers to it through the
            # tag keyword unless a typedef aliases it (kind typedef).
            if model.kind == "struct":
                return f"struct {model.name}", ""
            if model.kind == "union":
                return f"union {model.name}", ""
            if model.kind == "enum":
                return f"enum {model.name}", ""
            return model.name, ""
        if model.underlying_type:
            return spell_type_parts(model.underlying_type, types, trail)
        return None
    if model.kind == "pointer":
        if model.target is None:
            return None
        target = spell_type_parts(model.target, types, trail)
        return None if target is None else (f"{target[0]} *", target[1])
    if model.kind == "array":
        if model.element_type is None:
            return None
        element = spell_type_parts(model.element_type, types, trail)
        if element is None:
            return None
        dimensions = [d.size for d in model.dimensions] if model.dimensions else [model.size]
        if any(size is None for size in dimensions):
            return None
        suffix = "".join(f"[{size}]" for size in dimensions)
        return element[0], element[1] + suffix
    return None


def spell_type(type_ref: str, types: Mapping[str, TypeModel]) -> str | None:
    """The full C spelling of a ``ref:type.<id>`` (base type plus dimensions)."""
    parts = spell_type_parts(type_ref, types)
    return None if parts is None else parts[0] + parts[1]


def resolve_global_exposures(
    unit: AnalysisUnit,
    types: Mapping[str, TypeModel],
) -> tuple[GlobalExposure, ...]:
    """Resolve the unit's recorded variables into exposure records, name-sorted.

    Visible variables (storage ``none``/``extern``) resolve to extern
    declarations; file-static variables resolve to the source-inclusion
    mechanism; a variable whose type the model cannot resolve is not reachable
    with the named reason ``type_not_recorded`` — never guessed.
    """
    exposures: list[GlobalExposure] = []
    for variable in sorted(unit.global_variables, key=lambda g: g.name):
        parts = spell_type_parts(variable.type, types)
        if parts is None:
            exposures.append(
                GlobalExposure(
                    name=variable.name,
                    storage_class=variable.storage_class,
                    has_initializer=variable.has_initializer,
                    mechanism=MECHANISM_NOT_REACHABLE,
                    reason=REASON_TYPE_NOT_RECORDED,
                )
            )
            continue
        base, suffix = parts
        if variable.storage_class == "static":
            exposures.append(
                GlobalExposure(
                    name=variable.name,
                    storage_class=variable.storage_class,
                    has_initializer=variable.has_initializer,
                    mechanism=MECHANISM_SOURCE_INCLUSION,
                    c_type=base + suffix,
                    declarator_suffix=suffix,
                )
            )
            continue
        exposures.append(
            GlobalExposure(
                name=variable.name,
                storage_class=variable.storage_class,
                has_initializer=variable.has_initializer,
                mechanism=MECHANISM_EXTERN_DECLARATION,
                c_type=base + suffix,
                declarator_suffix=suffix,
                declaration=f"extern {base} {variable.name}{suffix};",
            )
        )
    return tuple(exposures)


def render_global_exposure_block(exposures: tuple[GlobalExposure, ...]) -> str:
    """The deterministic global-exposure block of a generated harness.

    Declarations first (visible variables, sorted), then one exposure record
    per variable including the static and unreachable ones. Empty when the
    model records no variables, so pre-1.5 models render byte-identically to
    before.
    """
    if not exposures:
        return ""
    lines: list[str] = [_GLOBAL_EXPOSURE_BEGIN]
    lines.extend(e.declaration for e in exposures if e.declaration is not None)
    lines.extend(e.record() for e in exposures)
    lines.append(_GLOBAL_EXPOSURE_END)
    return "\n".join(lines)

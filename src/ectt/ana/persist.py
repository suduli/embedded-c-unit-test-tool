# implements: DSN-ANA-070, DSN-ANA-040, DSN-ANA-090
"""Analysis model assembly, persistence, type graph merging, and schema versioning.

Satisfies: TOOL-PAR-100, TOOL-PAR-110, TOOL-PAR-150, DSN-ANA-070, DSN-ANA-040, DSN-ANA-090.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ectt.ana.errors import (
    AnalysisModelError,
    ExtractionError,
    FrontendParseError,
    IncompatibleSchemaVersionError,
    InvalidSchemaVersionOrderError,
    MalformedSchemaVersionError,
    MissingSchemaVersionError,
    SourceFileNotFoundError,
    TypeClosureError,
    TypeDefinitionConflictError,
)
from ectt.ana.model import (
    CALL_CLASSIFICATIONS,
    CALL_VIA,
    AnalysisModel,
    AnalysisUnit,
    DecisionInventoryModel,
    InputFileModel,
    ParsedTranslationUnit,
    ProvenanceModel,
    TypeModel,
    UnitFailureModel,
)
from ectt.core.determinism import Clock, canonical_json_bytes
from ectt.core.fs import OutputRoot

__all__ = [
    "READER_MAJOR",
    "READER_MIN_MINOR",
    "SCHEMA_VERSION_CURRENT",
    "PER_UNIT_FAILURES",
    "assemble_analysis_model",
    "failed_unit_from_error",
    "write_analysis_model",
    "read_analysis_model",
    "load_analysis_model",
    "compute_model_digest",
]

READER_MAJOR: int = 1
READER_MIN_MINOR: int = 0
# The schema version assemble() emits for newly created models. Bumping this
# is a schema-publishing event (src/ectt/ana/schema/analysis-model-<v>.schema.json)
# and moves only this line; tests must assert this constant, never a literal,
# so a bump cannot silently strand them (root cause of the 1.0 -> 1.1 -> 1.2
# test drift fixed in TASK-001).
SCHEMA_VERSION_CURRENT: str = "1.4"
_VERSION_RE = re.compile(r"^(\d+)\.(\d+)$")

# Errors that describe one translation unit only (TOOL-PAR-130). Anything else is
# run-level and must propagate: catching it here would report a real defect as a
# "unit failed" record, which is the misleading output NFR-090 forbids.
PER_UNIT_FAILURES: tuple[type[Exception], ...] = (
    SourceFileNotFoundError,
    FrontendParseError,
    ExtractionError,
)


def failed_unit_from_error(
    path: Path | str,
    exc: Exception,
    *,
    diagnostics: Sequence[Any] = (),
) -> AnalysisUnit:
    """Turn one per-unit error into a failed analysis unit with a named reason.

    The caller catches ``PER_UNIT_FAILURES`` and passes the error here, so the
    other units of the run are unaffected. The message is fixed text: the raw
    exception message can embed absolute paths and libclang internals.

    Implements: TOOL-PAR-130.
    """
    if not isinstance(exc, PER_UNIT_FAILURES):
        raise TypeError(f"Only per-unit failures may become a failed unit, got {type(exc).__name__}")
    reason = str(getattr(exc, "reason", "analysis_error"))
    return AnalysisUnit(
        path=_normalize_unit_path(str(path)),
        status="failed",
        diagnostics=tuple(diagnostics),
        functions=(),
        types={},
        failure=UnitFailureModel(
            reason=reason,
            code=type(exc).__name__,
            category=str(getattr(exc, "category", "analysis")),
            message=f"unit not analysed: {reason}",
        ),
    )


def _find_all_type_refs(obj: Any) -> set[str]:
    """Recursively discover all 'ref:type.*' reference strings within a data structure."""
    refs: set[str] = set()
    if isinstance(obj, str):
        if obj.startswith("ref:"):
            refs.add(obj)
    elif isinstance(obj, Mapping):
        for v in obj.values():
            refs.update(_find_all_type_refs(v))
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            refs.update(_find_all_type_refs(item))
    return refs


def _normalize_unit_path(path_str: str) -> str:
    """Normalize source unit path to relative POSIX format without leading slashes or drive letters."""
    p = Path(path_str)
    # Strip drive letter if present
    if p.drive:
        path_str = path_str[len(p.drive):]
    path_str = path_str.replace("\\", "/").lstrip("/")
    parts = [part for part in path_str.split("/") if part and part != "."]
    return "/".join(parts)


def assemble_analysis_model(
    units: Sequence[AnalysisUnit | ParsedTranslationUnit],
    *,
    clock: Clock,
    source_root: Path | str | None = None,
    input_digests: Mapping[str, str] | None = None,
    tool_version: str | None = None,
    front_end: str | None = None,
) -> AnalysisModel:
    """Assemble individual translation unit analysis results into a unified AnalysisModel document.

    Merges per-unit type graphs into a top-level types map, enforces type closure,
    records provenance with injected clock timestamps and source input digests,
    and sets capabilities per SDD-002 §4.1.

    Implements: SDD-002 §4.1, DSN-ANA-070.
    Satisfies: TOOL-PAR-100, TOOL-PAR-110.
    """
    if clock is None:
        raise TypeError("clock is required and must implement ectt.core.determinism.Clock")

    generated_at = clock.isoformat()

    # 1. Resolve tool version and front-end identification
    if tool_version is None:
        try:
            tool_version = importlib.metadata.version("ectt")
        except importlib.metadata.PackageNotFoundError:
            # Running from an uninstalled source tree; never claim a version we cannot prove.
            tool_version = "unknown"

    if front_end is None:
        from ectt.ana.frontend import get_libclang_version_tuple

        maj, min_, patch = get_libclang_version_tuple()
        front_end = f"libclang {maj}.{min_}.{patch}"

    # 2. Process units. A per-unit failure becomes a failed unit with a named reason
    # (TOOL-PAR-130) and never removes the other units. Run-level errors (type merge,
    # closure, digests of parsed units) still propagate.
    final_units: list[AnalysisUnit] = []
    for item in units:
        if isinstance(item, ParsedTranslationUnit):
            if item.status == "failed" or item.has_errors:
                errors = item.errors
                final_units.append(
                    AnalysisUnit(
                        path=_normalize_unit_path(item.source_path),
                        status="failed",
                        diagnostics=item.diagnostics,
                        functions=(),
                        types={},
                        failure=UnitFailureModel(
                            reason="frontend_parse_error",
                            code=FrontendParseError.__name__,
                            category=FrontendParseError.category,
                            message=errors[0].message if errors else "translation unit did not parse",
                        ),
                    )
                )
            else:
                from ectt.ana.interface import extract_interfaces

                try:
                    extracted = extract_interfaces(item)
                except ExtractionError as exc:
                    final_units.append(failed_unit_from_error(item.source_path, exc, diagnostics=item.diagnostics))
                    continue
                final_units.append(
                    AnalysisUnit(
                        path=_normalize_unit_path(extracted.path),
                        status=extracted.status,
                        diagnostics=extracted.diagnostics,
                        functions=extracted.functions,
                        types=extracted.types,
                        unsupported_constructs=extracted.unsupported_constructs,
                    )
                )
        elif isinstance(item, AnalysisUnit):
            norm_path = _normalize_unit_path(item.path)
            if item.status == "failed":
                final_units.append(
                    AnalysisUnit(
                        path=norm_path,
                        status="failed",
                        diagnostics=item.diagnostics,
                        functions=(),
                        types={},
                        unsupported_constructs=item.unsupported_constructs,
                        failure=item.failure
                        or UnitFailureModel(
                            reason="unit_analysis_failed",
                            code="AnalysisError",
                            category="analysis",
                            message="unit not analysed: no reason recorded by the caller",
                        ),
                    )
                )
            else:
                final_units.append(
                    AnalysisUnit(
                        path=norm_path,
                        status=item.status,
                        diagnostics=item.diagnostics,
                        functions=item.functions,
                        types=item.types,
                        unsupported_constructs=item.unsupported_constructs,
                    )
                )
        else:
            raise TypeError(f"Expected AnalysisUnit or ParsedTranslationUnit, got {type(item).__name__}")

    # 3. Model-wide type merge with conflict detection (SDD-002 §4.1)
    merged_types: dict[str, TypeModel] = {}
    type_origins: dict[str, str] = {}

    for unit in final_units:
        for type_id, type_model in unit.types.items():
            if type_id not in merged_types:
                merged_types[type_id] = type_model
                type_origins[type_id] = unit.path
            else:
                existing = merged_types[type_id]
                # Compare canonical representations including source location
                if existing.to_dict() != type_model.to_dict():
                    origin_unit = type_origins[type_id]
                    raise TypeDefinitionConflictError(
                        f"Conflicting definitions for type '{type_id}' between unit '{origin_unit}' and unit '{unit.path}'",
                        type_id=type_id,
                        unit_a=origin_unit,
                        unit_b=unit.path,
                    )

    # 4. Transitive type closure validation (SDD-002 §4.2)
    # Check all ref:type.* in units and types
    units_dict_repr = [u.to_dict_without_types() for u in final_units]
    types_dict_repr = {k: v.to_dict() for k, v in merged_types.items()}
    all_refs = _find_all_type_refs(units_dict_repr) | _find_all_type_refs(types_dict_repr)

    for ref in sorted(all_refs):
        if ref.startswith("ref:"):
            target_id = ref[4:]
            if target_id not in merged_types:
                raise TypeClosureError(
                    f"Dangling type reference '{ref}': target '{target_id}' not found in model-wide types",
                    ref=ref,
                )

    # 5. Input file digests
    input_records: list[InputFileModel] = []
    base_dir = Path(source_root) if source_root is not None else None

    for unit in final_units:
        unit_path_str = unit.path
        if input_digests is not None and unit_path_str in input_digests:
            digest = input_digests[unit_path_str]
        else:
            cand = base_dir / unit_path_str if base_dir is not None else Path(unit_path_str)
            if cand.is_file():
                digest = hashlib.sha256(cand.read_bytes()).hexdigest()
            elif unit.status == "failed":
                # A failed unit may have no readable source; its failure reason records that.
                continue
            else:
                raise SourceFileNotFoundError(
                    f"Translation unit source file '{unit_path_str}' not found on disk at '{cand}'",
                    path=cand,
                )
        input_records.append(InputFileModel(path=unit_path_str, digest=digest))

    sorted_inputs = tuple(sorted(input_records, key=lambda inp: inp.path))

    provenance = ProvenanceModel(
        tool_version=tool_version,
        front_end=front_end,
        generated_at=generated_at,
        inputs=sorted_inputs,
    )

    return AnalysisModel(
        schema_version=SCHEMA_VERSION_CURRENT,
        provenance=provenance,
        units=tuple(final_units),
        types=merged_types,
        capabilities={"cfg": False},
        decision_inventory=DecisionInventoryModel(
            status="not_extracted",
            detail="decision extraction is not implemented in this analyzer build (capabilities.cfg is false)",
        ),
    )


def write_analysis_model(
    output_root: OutputRoot,
    rel_path: Path | str,
    model: AnalysisModel | Mapping[str, Any],
) -> Path:
    """Atomically write an AnalysisModel to disk inside the confined OutputRoot.

    Implements: DSN-CORE-060, DSN-ANA-070.
    Satisfies: TOOL-PAR-100.
    """
    if isinstance(model, AnalysisModel):
        doc = model.to_dict()
    elif isinstance(model, Mapping):
        doc = dict(model)
    else:
        raise TypeError(f"Expected AnalysisModel or Mapping, got {type(model).__name__}")

    data = canonical_json_bytes(doc, first_keys=("schema_version",))
    return output_root.write_bytes(rel_path, data)


def read_analysis_model(
    source: Path | str | bytes | Mapping[str, Any],
    *,
    output_root: OutputRoot | None = None,
    rel_path: Path | str | None = None,
) -> AnalysisModel:
    """Read, validate, and deserialize an AnalysisModel document.

    Enforces the SDD-002 §3 version gate, top-level key requirements,
    and SDD-002 §4.2 type closure over the merged types graph.

    Does NOT depend on libclang or jsonschema at runtime.

    Implements: SDD-002 §3, SDD-002 §4.1, SDD-002 §4.2.
    Satisfies: TOOL-PAR-100, TOOL-PAR-110.
    """
    doc: Any

    if output_root is not None and rel_path is not None:
        doc = _decode_json(_read_file(output_root.resolve_path(rel_path)))
    elif isinstance(source, Path):
        doc = _decode_json(_read_file(source))
    elif isinstance(source, str):
        # A str is JSON text if it starts with '{' after whitespace, otherwise a file path.
        if source.lstrip().startswith("{"):
            doc = _decode_json(source.encode("utf-8"))
        else:
            doc = _decode_json(_read_file(Path(source)))
    elif isinstance(source, (bytes, bytearray, memoryview)):
        doc = _decode_json(bytes(source))
    elif isinstance(source, Mapping):
        doc = dict(source)
    else:
        raise TypeError(f"Unsupported source type for read_analysis_model: {type(source).__name__}")

    if not isinstance(doc, dict):
        raise AnalysisModelError("Analysis model document root must be a JSON object", reason="invalid_root_type")

    # 1. Version gate: presence check
    if "schema_version" not in doc:
        raise MissingSchemaVersionError(
            "Missing required 'schema_version' field in analysis model document",
            reason="missing_schema_version",
        )

    # 2. Version gate: first key check (SDD-002 §3)
    keys = list(doc.keys())
    if not keys or keys[0] != "schema_version":
        first_key = keys[0] if keys else "<empty>"
        raise InvalidSchemaVersionOrderError(
            f"'schema_version' must be the first key in the analysis model document, but found '{first_key}'",
            reason="schema_version_not_first",
        )

    # 3. Version gate: format check
    raw_version = doc["schema_version"]
    if not isinstance(raw_version, str):
        raise MalformedSchemaVersionError(
            f"Expected string schema_version (e.g. '1.0'), got {type(raw_version).__name__}",
            version=raw_version,
            reason="malformed_schema_version",
        )

    match = _VERSION_RE.match(raw_version.strip())
    if not match:
        raise MalformedSchemaVersionError(
            f"Malformed schema_version '{raw_version}'; expected 'MAJOR.MINOR' format e.g. '1.0'",
            version=raw_version,
            reason="malformed_schema_version",
        )

    doc_major = int(match.group(1))
    doc_minor = int(match.group(2))

    # 4. Version gate: major incompatibility check (both directions)
    if doc_major != READER_MAJOR:
        raise IncompatibleSchemaVersionError(
            f"Incompatible schema version '{raw_version}': reader is pinned to major {READER_MAJOR} but document specifies major {doc_major}",
            reader_version=f"{READER_MAJOR}.{READER_MIN_MINOR}",
            document_version=raw_version,
            reason="major_version_mismatch",
        )

    # 5. Version gate: minor version floor check
    if doc_minor < READER_MIN_MINOR:
        raise IncompatibleSchemaVersionError(
            f"Unsupported schema version '{raw_version}': reader requires at least minor {READER_MIN_MINOR}",
            reader_version=f"{READER_MAJOR}.{READER_MIN_MINOR}",
            document_version=raw_version,
            reason="minor_version_too_low",
        )

    # 6. Required top-level keys
    required_keys = ("schema_version", "provenance", "units", "types", "capabilities")
    for rk in required_keys:
        if rk not in doc:
            raise AnalysisModelError(
                f"Missing required top-level key '{rk}' in analysis model document",
                reason="missing_required_key",
            )

    # 6b. Minor-version-gated inventories (schema 1.1: TOOL-PAR-140, TOOL-PAR-150).
    # Fail-closed per SDD-002 §3: unknown semantic values are rejected, never
    # interpreted, and a 1.1 document cannot omit either inventory.
    if doc_minor >= 1:
        if "decision_inventory" not in doc:
            raise AnalysisModelError(
                "Missing required top-level key 'decision_inventory' in analysis model document (schema >= 1.1)",
                reason="missing_decision_inventory",
            )
        inventory = doc["decision_inventory"]
        allowed_status = ("not_extracted", "partial", "complete")
        status = inventory.get("status") if isinstance(inventory, dict) else None
        if status not in allowed_status:
            raise AnalysisModelError(
                f"Unknown decision inventory status {status!r}; expected one of {allowed_status}",
                reason="unknown_decision_inventory_status",
            )
        units_obj = doc.get("units")
        if isinstance(units_obj, list):
            for idx, unit_doc in enumerate(units_obj):
                if isinstance(unit_doc, dict) and "unsupported_constructs" not in unit_doc:
                    raise AnalysisModelError(
                        f"Unit at index {idx} is missing required 'unsupported_constructs' (schema >= 1.1)",
                        reason="missing_unsupported_constructs",
                    )

    # 6c. Minor-version-gated call graph (schema 1.3: TOOL-PAR-060). Fail-closed:
    # every function must carry calls[], and every call must use a known classification
    # and via value; an unknown value is rejected, never interpreted.
    if doc_minor >= 3:
        units_for_calls = doc.get("units")
        if isinstance(units_for_calls, list):
            for u_idx, unit_doc in enumerate(units_for_calls):
                if not isinstance(unit_doc, dict):
                    continue
                for fn_doc in unit_doc.get("functions", []):
                    if not isinstance(fn_doc, dict) or "calls" not in fn_doc:
                        raise AnalysisModelError(
                            f"Function in unit at index {u_idx} is missing required 'calls' (schema >= 1.3)",
                            reason="missing_calls",
                        )
                    for call_doc in fn_doc["calls"]:
                        cls_value = call_doc.get("classification") if isinstance(call_doc, dict) else None
                        via_value = call_doc.get("via") if isinstance(call_doc, dict) else None
                        if cls_value not in CALL_CLASSIFICATIONS or via_value not in CALL_VIA:
                            raise AnalysisModelError(
                                f"Unknown call classification {cls_value!r} or via {via_value!r} (schema >= 1.3)",
                                reason="unknown_call_value",
                            )

    # 6d. Minor-version-gated failure record (schema 1.4: TOOL-PAR-130). A failed unit
    # must name its reason and carry no functions; a parsed unit must not carry one.
    if doc_minor >= 4:
        units_for_failure = doc.get("units")
        if isinstance(units_for_failure, list):
            for u_idx, unit_doc in enumerate(units_for_failure):
                if not isinstance(unit_doc, dict):
                    continue
                failure_doc = unit_doc.get("failure")
                if unit_doc.get("status") == "failed":
                    if not _is_failure_doc(failure_doc):
                        raise AnalysisModelError(
                            f"Failed unit at index {u_idx} is missing a valid 'failure' record (schema >= 1.4)",
                            reason="missing_unit_failure",
                        )
                    if unit_doc.get("functions"):
                        raise AnalysisModelError(
                            f"Failed unit at index {u_idx} must not carry functions (schema >= 1.4)",
                            reason="failed_unit_has_functions",
                        )
                elif "failure" in unit_doc:
                    raise AnalysisModelError(
                        f"Unit at index {u_idx} carries a 'failure' record but is not failed (schema >= 1.4)",
                        reason="unexpected_unit_failure",
                    )

    # 7. Type closure validation over merged map on read (SDD-002 §4.2)
    types_obj = doc["types"]
    if not isinstance(types_obj, dict):
        raise AnalysisModelError("Expected 'types' to be an object mapping type IDs to definitions", reason="invalid_types")

    units_obj = doc["units"]
    if not isinstance(units_obj, list):
        raise AnalysisModelError("Expected 'units' to be an array of translation unit objects", reason="invalid_units")

    all_refs = _find_all_type_refs(units_obj) | _find_all_type_refs(types_obj)
    for ref in sorted(all_refs):
        if ref.startswith("ref:"):
            target_id = ref[4:]
            if target_id not in types_obj:
                raise TypeClosureError(
                    f"Dangling type reference '{ref}': target '{target_id}' not found in model-wide types",
                    ref=ref,
                )

    # 8. Reconstruct typed model, ignoring unknown fields per SDD-002 §3 minor bump rule
    return AnalysisModel.from_dict(doc)


# Canonical alias for reader
load_analysis_model = read_analysis_model


def _is_failure_doc(value: Any) -> bool:
    """True when a failure record carries all four string fields (schema 1.4)."""
    return isinstance(value, dict) and all(
        isinstance(value.get(key), str) for key in ("reason", "code", "category", "message")
    )


def _read_file(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise AnalysisModelError(
            f"Failed to read analysis model file '{path}': {exc}",
            reason="model_read_error",
        ) from exc


def _decode_json(data: bytes) -> Any:
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise AnalysisModelError(
            f"Analysis model is not valid UTF-8 JSON: {exc}",
            reason="invalid_json",
        ) from exc


def compute_model_digest(model: AnalysisModel | Mapping[str, Any]) -> str:
    """Compute deterministic content digest of an analysis model excluding provenance.generated_at.

    Implements: SDD-003 §9 content-addressed cache and TOOL-HAR-110 staleness checks.
    """
    if isinstance(model, AnalysisModel):
        return model.content_digest()
    doc_copy = copy.deepcopy(dict(model))
    if "provenance" in doc_copy and isinstance(doc_copy["provenance"], dict):
        doc_copy["provenance"].pop("generated_at", None)
    return hashlib.sha256(canonical_json_bytes(doc_copy)).hexdigest()

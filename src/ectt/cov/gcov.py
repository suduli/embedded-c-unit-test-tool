# implements: TOOL-COV-010, TOOL-COV-020
"""Reader for the documented GCC gcov JSON intermediate format.

Implements the WP-COV-01 backend reader (ADR-004: GCC first). The accepted
shape and key names follow the GCC gcov documentation (GCC 14.4, "Invoking
Gcov → GCOV JSON Format"): top-level ``format_version``/``gcc_version``/
``current_working_directory``/``data_file``/``files``; ``files[]`` with
``file``/``functions``/``lines``; ``lines[]`` with ``line_number``/``count``/
``unexecuted_block``/``function_name``/``branches``/``conditions``/``calls``/
``block_ids``; ``branches[]`` with ``count``/``fallthrough``/``throw``/
``source_block_id``/``destination_block_id``; ``conditions[]`` with
``count``/``covered``/``not_covered_true``/``not_covered_false``.

Format discipline (SDD-002 §3 analogue): format versions ``"1"`` and ``"2"``
are known (version 2 added ``calls``; GCC >= 14 adds ``conditions`` while
staying at version 2). Unknown versions are refused with a named error; keys
outside the documented set are ignored, never interpreted. GCC >= 14 gzips the
output; gzip-compressed input is accepted.

There is no C compiler on this machine: the reader is validated against
hand-written fixtures following the documented format, not against real GCC
output (WP-COV-01 analysis; ADR-004).

Satisfies: TOOL-COV-010, TOOL-COV-020.
"""

from __future__ import annotations

import gzip
import json
from collections.abc import Mapping
from typing import Any

from ectt.cov.errors import CoverageParseError
from ectt.cov.model import (
    GcovBranch,
    GcovCondition,
    GcovDocument,
    GcovFile,
    GcovLine,
)

__all__ = [
    "KNOWN_FORMAT_VERSIONS",
    "read_gcov_document",
]

#: Format versions this reader accepts. Version 1 (GCC 9-10) has no ``calls``
#: and no ``conditions``; version 2 (GCC 11+) adds ``calls``; GCC >= 14 adds
#: ``conditions`` while remaining at version 2. A later version is refused
#: until this reader is reviewed against its documentation.
KNOWN_FORMAT_VERSIONS: tuple[str, ...] = ("1", "2")

_GZIP_MAGIC = b"\x1f\x8b"


def read_gcov_document(source: bytes | bytearray | memoryview | str | Mapping[str, Any]) -> GcovDocument:
    """Parse and validate a gcov JSON document into the coverage model.

    ``source`` may be raw JSON text, raw JSON bytes, gzip-compressed bytes
    (GCC >= 14 emits ``.gcov.json.gz``), or an already-decoded mapping. Every
    deviation from the documented format is a named error.
    """
    doc: Any
    if isinstance(source, Mapping):
        doc = source
    else:
        raw: bytes
        if isinstance(source, str):
            raw = source.encode("utf-8")
        elif isinstance(source, (bytes, bytearray, memoryview)):
            raw = bytes(source)
        else:
            raise TypeError(f"Unsupported gcov document source: {type(source).__name__}")
        if raw[:2] == _GZIP_MAGIC:
            try:
                raw = gzip.decompress(raw)
            except OSError as exc:
                raise CoverageParseError(
                    f"gcov document is gzip-compressed but not valid gzip: {exc}",
                    reason="invalid_gzip",
                ) from exc
        doc = _decode_json(raw)
    return _build_document(doc)


def _decode_json(raw: bytes) -> Any:
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise CoverageParseError(
            f"gcov document is not valid UTF-8 JSON: {exc}",
            reason="invalid_json",
        ) from exc


def _require_object(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CoverageParseError(
            f"gcov document {where} must be a JSON object, got {type(value).__name__}",
            reason="not_an_object",
        )
    return value


def _require_str(container: Mapping[str, Any], key: str, where: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value:
        raise CoverageParseError(
            f"gcov document {where} requires a non-empty string '{key}'",
            reason="missing_or_invalid_key",
        )
    return value


def _require_int(
    container: Mapping[str, Any],
    key: str,
    where: str,
    *,
    minimum: int = 0,
) -> int:
    value = container.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise CoverageParseError(
            f"gcov document {where} requires integer '{key}' >= {minimum}, got {value!r}",
            reason="missing_or_invalid_key",
        )
    return value


def _optional_str(container: Mapping[str, Any], key: str) -> str | None:
    value = container.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise CoverageParseError(
            f"gcov document optional field '{key}' must be a non-empty string when present",
            reason="invalid_optional_key",
        )
    return value


def _optional_bool(container: Mapping[str, Any], key: str) -> bool | None:
    value = container.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise CoverageParseError(
            f"gcov document optional field '{key}' must be a boolean when present",
            reason="invalid_optional_key",
        )
    return value


def _optional_int(container: Mapping[str, Any], key: str) -> int | None:
    value = container.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise CoverageParseError(
            f"gcov document optional field '{key}' must be an integer when present",
            reason="invalid_optional_key",
        )
    return value


def _build_document(doc: Any) -> GcovDocument:
    root = _require_object(doc, "root")
    format_version = _require_str(root, "format_version", "root")
    if format_version not in KNOWN_FORMAT_VERSIONS:
        raise CoverageParseError(
            f"gcov document format_version {format_version!r} is not known to this reader "
            f"(known: {', '.join(KNOWN_FORMAT_VERSIONS)}); refusing to interpret an "
            f"undocumented format",
            reason="unknown_format_version",
        )
    gcc_version = _require_str(root, "gcc_version", "root")
    data_file = _require_str(root, "data_file", "root")
    current_working_directory = root.get("current_working_directory")
    if current_working_directory is not None and (
        not isinstance(current_working_directory, str) or not current_working_directory
    ):
        raise CoverageParseError(
            "gcov document root field 'current_working_directory' must be a "
            "non-empty string when present",
            reason="invalid_optional_key",
        )

    files_raw = root.get("files")
    if not isinstance(files_raw, list):
        raise CoverageParseError(
            "gcov document root requires 'files' to be an array",
            reason="missing_or_invalid_key",
        )
    files = tuple(_build_file(f, idx) for idx, f in enumerate(files_raw))
    return GcovDocument(
        format_version=format_version,
        gcc_version=gcc_version,
        data_file=data_file,
        files=files,
        current_working_directory=current_working_directory,
    )


def _build_file(value: Any, idx: int) -> GcovFile:
    where = f"files[{idx}]"
    entry = _require_object(value, where)
    file_name = _require_str(entry, "file", where)
    lines_raw = entry.get("lines")
    if not isinstance(lines_raw, list):
        raise CoverageParseError(
            f"gcov document {where} requires 'lines' to be an array",
            reason="missing_or_invalid_key",
        )
    lines: list[GcovLine] = []
    seen_lines: set[int] = set()
    for line_idx, line_raw in enumerate(lines_raw):
        line = _build_line(line_raw, f"{where}.lines[{line_idx}]")
        if line.line_number in seen_lines:
            raise CoverageParseError(
                f"gcov document {where} records line_number {line.line_number} more than once",
                reason="duplicate_line",
            )
        seen_lines.add(line.line_number)
        lines.append(line)
    lines.sort(key=lambda line: line.line_number)
    return GcovFile(file=file_name, lines=tuple(lines))


def _build_line(value: Any, where: str) -> GcovLine:
    entry = _require_object(value, where)
    line_number = _require_int(entry, "line_number", where, minimum=1)
    count = _require_int(entry, "count", where, minimum=0)
    unexecuted_block = entry.get("unexecuted_block", False)
    if not isinstance(unexecuted_block, bool):
        raise CoverageParseError(
            f"gcov document {where} field 'unexecuted_block' must be a boolean",
            reason="missing_or_invalid_key",
        )
    function_name = _optional_str(entry, "function_name")

    branches_raw = entry.get("branches", [])
    if not isinstance(branches_raw, list):
        raise CoverageParseError(
            f"gcov document {where} field 'branches' must be an array when present",
            reason="invalid_optional_key",
        )
    branches = tuple(_build_branch(b, f"{where}.branches[{i}]") for i, b in enumerate(branches_raw))

    conditions_raw = entry.get("conditions", [])
    if not isinstance(conditions_raw, list):
        raise CoverageParseError(
            f"gcov document {where} field 'conditions' must be an array when present",
            reason="invalid_optional_key",
        )
    conditions = tuple(
        _build_condition(c, f"{where}.conditions[{i}]") for i, c in enumerate(conditions_raw)
    )

    return GcovLine(
        line_number=line_number,
        count=count,
        unexecuted_block=unexecuted_block,
        function_name=function_name,
        branches=branches,
        conditions=conditions,
    )


def _build_branch(value: Any, where: str) -> GcovBranch:
    entry = _require_object(value, where)
    return GcovBranch(
        count=_require_int(entry, "count", where, minimum=0),
        fallthrough=_optional_bool(entry, "fallthrough"),
        throw=_optional_bool(entry, "throw"),
        source_block_id=_optional_int(entry, "source_block_id"),
        destination_block_id=_optional_int(entry, "destination_block_id"),
    )


def _build_condition(value: Any, where: str) -> GcovCondition:
    entry = _require_object(value, where)
    count = _require_int(entry, "count", where, minimum=1)
    covered = _require_int(entry, "covered", where, minimum=0)
    if covered > count:
        raise CoverageParseError(
            f"gcov document {where} condition records covered={covered} above count={count}",
            reason="covered_above_count",
        )
    return GcovCondition(
        count=count,
        covered=covered,
        not_covered_true=_build_term_list(entry, "not_covered_true", where),
        not_covered_false=_build_term_list(entry, "not_covered_false", where),
    )


def _build_term_list(container: Mapping[str, Any], key: str, where: str) -> tuple[int, ...]:
    raw = container.get(key, [])
    if not isinstance(raw, list):
        raise CoverageParseError(
            f"gcov document {where} field '{key}' must be an array when present",
            reason="invalid_optional_key",
        )
    terms: list[int] = []
    for term in raw:
        if isinstance(term, bool) or not isinstance(term, int) or term < 0:
            raise CoverageParseError(
                f"gcov document {where} field '{key}' must contain non-negative integers, got {term!r}",
                reason="invalid_optional_key",
            )
        terms.append(term)
    return tuple(terms)

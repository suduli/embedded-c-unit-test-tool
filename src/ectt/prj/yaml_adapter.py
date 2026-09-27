# implements: DSN-PRJ-010, DSN-PRJ-030
"""Restricted YAML serialization adapter and deterministic emitter for ectt.

Enforces SDD-003 §10 hazard mitigations and DSN-SEC-060 configuration-as-data rules:
- All scalars are parsed as strings (implicit typing disabled).
- Every scalar is double-quoted on write.
- Anchors, aliases, tags, merge keys, duplicate keys, multi-doc streams, and non-string
  keys are strictly rejected with file and line information.
- Comments are detected on overwrite; overwriting without discard_comments=True raises
  CommentPreservationError.
- Canonical key ordering puts schema_version first.
- Default values are omitted on write.
- Output uses LF endings, UTF-8 without BOM, no trailing whitespace, and canonical float format.

Satisfies: TOOL-PRJ-010, TOOL-PRJ-020, TOOL-PRJ-050, TOOL-SEC-070, DSN-PRJ-010, DSN-PRJ-030, DSN-SEC-060.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import yaml
import yaml.reader
import yaml.scanner

from ectt.core.determinism import canonical_float_repr
from ectt.prj.errors import (
    AnchorForbiddenError,
    CommentPreservationError,
    DuplicateKeyError,
    EmptyDocumentError,
    MergeKeyForbiddenError,
    MultiDocumentForbiddenError,
    NonStringKeyError,
    NotAMappingError,
    TagForbiddenError,
    YamlSyntaxError,
)

__all__ = [
    "SerializationAdapter",
    "RestrictedYamlAdapter",
    "detect_yaml_comments",
]


@runtime_checkable
class SerializationAdapter(Protocol):
    """Abstract protocol for project file serialization backends."""

    def load(self, text: str, *, path: Path | str | None = None) -> dict[str, Any]:
        """Deserialize plain text into a document dictionary."""
        ...

    def dump(
        self,
        data: Mapping[str, Any],
        *,
        canonical_keys: Sequence[str] = (),
        default_values: Mapping[str, Any] | None = None,
    ) -> str:
        """Serialize a document dictionary into deterministic text."""
        ...

    def dump_bytes(
        self,
        data: Mapping[str, Any],
        *,
        canonical_keys: Sequence[str] = (),
        default_values: Mapping[str, Any] | None = None,
    ) -> bytes:
        """Serialize a document dictionary into UTF-8 encoded bytes."""
        ...


class _CommentScanner(yaml.scanner.Scanner, yaml.reader.Reader):
    """Scanner subclass that captures YAML comment locations with 1-indexed lines and columns."""

    def __init__(self, stream: str) -> None:
        yaml.reader.Reader.__init__(self, stream)
        yaml.scanner.Scanner.__init__(self)
        self.comments: list[tuple[int, int]] = []

    def scan_to_next_token(self) -> None:
        if self.index == 0 and self.peek() == "\uFEFF":
            self.forward()
        found = False
        while not found:
            while self.peek() == " ":
                self.forward()
            if self.peek() == "#":
                self.comments.append((self.line + 1, self.column + 1))
                while self.peek() not in "\0\r\n\x85\u2028\u2029":
                    self.forward()
            if self.scan_line_break():
                if not self.flow_level:
                    self.allow_simple_key = True
            else:
                found = True


def detect_yaml_comments(text: str) -> list[tuple[int, int]]:
    """Scan YAML text and return a list of (line, column) tuples for all comments."""
    scanner = _CommentScanner(text)
    try:
        while scanner.check_token():
            scanner.get_token()
    except yaml.YAMLError:
        # Syntax errors during scanning are caught during parse phase
        pass
    return scanner.comments


class RestrictedYamlAdapter:
    """Restricted YAML loader and deterministic emitter."""

    def load(self, text: str, *, path: Path | str | None = None) -> dict[str, Any]:
        """Parse restricted YAML text into a dictionary.

        Enforces:
        - Every scalar is parsed as a string.
        - Exactly one document; root must be a mapping.
        - Rejection of aliases, anchors, explicit tags, merge keys (<<),
          duplicate mapping keys, and non-string mapping keys.
        """
        if not text or text.strip() == "":
            raise EmptyDocumentError(
                f"Project file '{path or '<string>'}' is empty; expected a YAML mapping",
                path=path,
            )

        # PyYAML handles \r\n, but let's normalize CRLF to LF for consistent line indexing
        normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")

        try:
            events = list(yaml.parse(normalized_text))
        except yaml.error.MarkedYAMLError as exc:
            line = exc.problem_mark.line + 1 if exc.problem_mark else None
            col = exc.problem_mark.column + 1 if exc.problem_mark else None
            raise YamlSyntaxError(
                f"YAML syntax error in '{path or '<string>'}': {exc.problem}",
                path=path,
                line=line,
                column=col,
            ) from exc
        except yaml.YAMLError as exc:
            raise YamlSyntaxError(
                f"YAML parse error in '{path or '<string>'}': {exc}",
                path=path,
            ) from exc

        return self._build_document(events, path=path)

    def _build_document(
        self,
        events: list[yaml.Event],
        *,
        path: Path | str | None = None,
    ) -> dict[str, Any]:
        """Convert YAML parse events into Python data structure while applying strict validation."""
        doc_count = 0
        root_data: dict[str, Any] | None = None

        # Context stack items are either:
        # ('map', dict_obj, seen_keys_set, current_key_or_none)
        # ('seq', list_obj)
        stack: list[tuple[str, Any, Any, Any]] = []

        for ev in events:
            # 1. Reject aliases and anchors
            if isinstance(ev, yaml.AliasEvent):
                line = ev.start_mark.line + 1 if ev.start_mark else None
                col = ev.start_mark.column + 1 if ev.start_mark else None
                raise AnchorForbiddenError(
                    f"YAML alias '*{ev.anchor}' is forbidden in project files",
                    path=path,
                    line=line,
                    column=col,
                )

            if getattr(ev, "anchor", None) is not None:
                line = ev.start_mark.line + 1 if ev.start_mark else None
                col = ev.start_mark.column + 1 if ev.start_mark else None
                raise AnchorForbiddenError(
                    f"YAML anchor '&{ev.anchor}' is forbidden in project files",
                    path=path,
                    line=line,
                    column=col,
                )

            # 2. Reject explicit tags
            if getattr(ev, "tag", None) is not None:
                line = ev.start_mark.line + 1 if ev.start_mark else None
                col = ev.start_mark.column + 1 if ev.start_mark else None
                raise TagForbiddenError(
                    f"Explicit YAML tag '{ev.tag}' is forbidden in project files",
                    path=path,
                    line=line,
                    column=col,
                )

            # 3. Track documents
            if isinstance(ev, yaml.DocumentStartEvent):
                doc_count += 1
                if doc_count > 1:
                    line = ev.start_mark.line + 1 if ev.start_mark else None
                    col = ev.start_mark.column + 1 if ev.start_mark else None
                    raise MultiDocumentForbiddenError(
                        "Multi-document YAML streams are forbidden; project files must contain exactly one document",
                        path=path,
                        line=line,
                        column=col,
                    )
                continue

            if isinstance(ev, yaml.DocumentEndEvent):
                continue

            if isinstance(ev, (yaml.StreamStartEvent, yaml.StreamEndEvent)):
                continue

            # 4. Process Collections and Scalars
            if not stack:
                # Root must be a mapping
                if not isinstance(ev, yaml.MappingStartEvent):
                    line = ev.start_mark.line + 1 if ev.start_mark else None
                    col = ev.start_mark.column + 1 if ev.start_mark else None
                    raise NotAMappingError(
                        f"Project file root must be a YAML mapping, got {type(ev).__name__}",
                        path=path,
                        line=line,
                        column=col,
                    )
                stack.append(("map", {}, set(), None))
                continue

            # Check if MappingEnd or SequenceEnd completed a container
            if isinstance(ev, yaml.MappingEndEvent):
                finished = stack.pop()
                finished_val = finished[1]
                if not stack:
                    root_data = finished_val
                else:
                    parent_type, parent_container, parent_keys, parent_key = stack[-1]
                    if parent_type == "map":
                        parent_container[parent_key] = finished_val
                        stack[-1] = (parent_type, parent_container, parent_keys, None)
                    elif parent_type == "seq":
                        parent_container.append(finished_val)
                continue

            if isinstance(ev, yaml.SequenceEndEvent):
                finished = stack.pop()
                finished_val = finished[1]
                if not stack:
                    root_data = finished_val
                else:
                    parent_type, parent_container, parent_keys, parent_key = stack[-1]
                    if parent_type == "map":
                        parent_container[parent_key] = finished_val
                        stack[-1] = (parent_type, parent_container, parent_keys, None)
                    elif parent_type == "seq":
                        parent_container.append(finished_val)
                continue

            ctx_type, container, seen_keys, current_key = stack[-1]

            if ctx_type == "map":
                if current_key is None:
                    # Expecting a mapping key
                    if not isinstance(ev, yaml.ScalarEvent):
                        line = ev.start_mark.line + 1 if ev.start_mark else None
                        col = ev.start_mark.column + 1 if ev.start_mark else None
                        raise NonStringKeyError(
                            f"Mapping key must be a string scalar, got {type(ev).__name__}",
                            path=path,
                            line=line,
                            column=col,
                        )

                    key_val = ev.value
                    line = ev.start_mark.line + 1 if ev.start_mark else None
                    col = ev.start_mark.column + 1 if ev.start_mark else None

                    if key_val == "<<":
                        raise MergeKeyForbiddenError(
                            "YAML merge keys ('<<') are forbidden in project files",
                            path=path,
                            line=line,
                            column=col,
                        )

                    if key_val in seen_keys:
                        raise DuplicateKeyError(
                            f"Duplicate mapping key '{key_val}'",
                            path=path,
                            line=line,
                            column=col,
                        )

                    seen_keys.add(key_val)
                    stack[-1] = (ctx_type, container, seen_keys, key_val)

                else:
                    # Expecting value for current_key
                    if isinstance(ev, yaml.ScalarEvent):
                        container[current_key] = ev.value
                        stack[-1] = (ctx_type, container, seen_keys, None)
                    elif isinstance(ev, yaml.MappingStartEvent):
                        stack.append(("map", {}, set(), None))
                    elif isinstance(ev, yaml.SequenceStartEvent):
                        stack.append(("seq", [], None, None))
                    else:
                        line = ev.start_mark.line + 1 if ev.start_mark else None
                        col = ev.start_mark.column + 1 if ev.start_mark else None
                        raise YamlSyntaxError(
                            f"Unexpected YAML event {type(ev).__name__}",
                            path=path,
                            line=line,
                            column=col,
                        )

            elif ctx_type == "seq":
                if isinstance(ev, yaml.ScalarEvent):
                    container.append(ev.value)
                elif isinstance(ev, yaml.MappingStartEvent):
                    stack.append(("map", {}, set(), None))
                elif isinstance(ev, yaml.SequenceStartEvent):
                    stack.append(("seq", [], None, None))
                else:
                    line = ev.start_mark.line + 1 if ev.start_mark else None
                    col = ev.start_mark.column + 1 if ev.start_mark else None
                    raise YamlSyntaxError(
                        f"Unexpected YAML event {type(ev).__name__}",
                        path=path,
                        line=line,
                        column=col,
                    )

        if root_data is None:
            raise EmptyDocumentError(
                f"Project file '{path or '<string>'}' contains no document",
                path=path,
            )

        return root_data

    # --- Deterministic Emitter ---

    def dump(
        self,
        data: Mapping[str, Any],
        *,
        canonical_keys: Sequence[str] = (),
        default_values: Mapping[str, Any] | None = None,
    ) -> str:
        """Deterministically serialize data dictionary into restricted YAML string."""
        if not isinstance(data, Mapping):
            raise TypeError(f"Expected mapping for project file root, got {type(data).__name__}")

        lines: list[str] = []
        self._emit_mapping(
            data,
            lines,
            indent=0,
            canonical_keys=canonical_keys,
            default_values=default_values or {},
        )
        return "\n".join(lines) + "\n"

    def dump_bytes(
        self,
        data: Mapping[str, Any],
        *,
        canonical_keys: Sequence[str] = (),
        default_values: Mapping[str, Any] | None = None,
    ) -> bytes:
        """Serialize data dictionary into UTF-8 encoded bytes without BOM."""
        text = self.dump(
            data,
            canonical_keys=canonical_keys,
            default_values=default_values,
        )
        return text.encode("utf-8")

    def _format_scalar(self, val: Any) -> str:
        """Format scalar value as double-quoted string with JSON escaping rules."""
        if isinstance(val, float):
            s = canonical_float_repr(val)
        elif isinstance(val, bool):
            s = "true" if val else "false"
        elif isinstance(val, int):
            s = str(val)
        elif isinstance(val, str):
            s = val
        else:
            s = str(val)
        return json.dumps(s, ensure_ascii=False)

    def _sort_keys(
        self,
        keys: Iterable[str],
        canonical_keys: Sequence[str],
    ) -> list[str]:
        """Order keys deterministically with schema_version always first."""
        keys_set = set(keys)
        ordered: list[str] = []

        # 1. schema_version is ALWAYS first
        if "schema_version" in keys_set:
            ordered.append("schema_version")
            keys_set.remove("schema_version")

        # 2. Declared canonical keys in declared order
        for k in canonical_keys:
            if k in keys_set:
                ordered.append(k)
                keys_set.remove(k)

        # 3. Remaining keys sorted alphabetically
        for k in sorted(keys_set):
            ordered.append(k)

        return ordered

    def _emit_mapping(
        self,
        data: Mapping[str, Any],
        lines: list[str],
        indent: int,
        canonical_keys: Sequence[str] = (),
        default_values: Mapping[str, Any] | None = None,
    ) -> None:
        """Recursively format mapping elements."""
        defaults = default_values or {}
        sorted_keys = self._sort_keys(data.keys(), canonical_keys)
        prefix = " " * indent

        for key in sorted_keys:
            val = data[key]

            # Omit default values and None
            if val is None:
                continue
            if key in defaults and val == defaults[key]:
                continue

            quoted_key = self._format_scalar(key)

            if isinstance(val, Mapping):
                if not val:
                    lines.append(f"{prefix}{quoted_key}: {{}}")
                else:
                    lines.append(f"{prefix}{quoted_key}:")
                    self._emit_mapping(
                        val,
                        lines,
                        indent=indent + 2,
                        canonical_keys=(),
                        default_values={},
                    )
            elif isinstance(val, (list, tuple)):
                if not val:
                    lines.append(f"{prefix}{quoted_key}: []")
                else:
                    lines.append(f"{prefix}{quoted_key}:")
                    self._emit_sequence(val, lines, indent=indent + 2)
            else:
                quoted_val = self._format_scalar(val)
                lines.append(f"{prefix}{quoted_key}: {quoted_val}")

    def _emit_sequence(
        self,
        items: Sequence[Any],
        lines: list[str],
        indent: int,
    ) -> None:
        """Recursively format sequence elements."""
        prefix = " " * indent

        for item in items:
            if isinstance(item, Mapping):
                if not item:
                    lines.append(f"{prefix}- {{}}")
                else:
                    keys = self._sort_keys(item.keys(), ())
                    first_key = keys[0]
                    first_val = item[first_key]
                    first_quoted_key = self._format_scalar(first_key)

                    if isinstance(first_val, Mapping):
                        if not first_val:
                            lines.append(f"{prefix}- {first_quoted_key}: {{}}")
                        else:
                            lines.append(f"{prefix}- {first_quoted_key}:")
                            self._emit_mapping(
                                first_val,
                                lines,
                                indent=indent + 4,
                                canonical_keys=(),
                                default_values={},
                            )
                    elif isinstance(first_val, (list, tuple)):
                        if not first_val:
                            lines.append(f"{prefix}- {first_quoted_key}: []")
                        else:
                            lines.append(f"{prefix}- {first_quoted_key}:")
                            self._emit_sequence(first_val, lines, indent=indent + 4)
                    else:
                        quoted_val = self._format_scalar(first_val)
                        lines.append(f"{prefix}- {first_quoted_key}: {quoted_val}")

                    sub_prefix = " " * (indent + 2)
                    for next_key in keys[1:]:
                        next_val = item[next_key]
                        next_quoted_key = self._format_scalar(next_key)

                        if isinstance(next_val, Mapping):
                            if not next_val:
                                lines.append(f"{sub_prefix}{next_quoted_key}: {{}}")
                            else:
                                lines.append(f"{sub_prefix}{next_quoted_key}:")
                                self._emit_mapping(
                                    next_val,
                                    lines,
                                    indent=indent + 4,
                                    canonical_keys=(),
                                    default_values={},
                                )
                        elif isinstance(next_val, (list, tuple)):
                            if not next_val:
                                lines.append(f"{sub_prefix}{next_quoted_key}: []")
                            else:
                                lines.append(f"{sub_prefix}{next_quoted_key}:")
                                self._emit_sequence(next_val, lines, indent=indent + 4)
                        else:
                            quoted_val = self._format_scalar(next_val)
                            lines.append(f"{sub_prefix}{next_quoted_key}: {quoted_val}")

            elif isinstance(item, (list, tuple)):
                if not item:
                    lines.append(f"{prefix}- []")
                else:
                    lines.append(f"{prefix}-")
                    self._emit_sequence(item, lines, indent=indent + 2)
            else:
                quoted_val = self._format_scalar(item)
                lines.append(f"{prefix}- {quoted_val}")

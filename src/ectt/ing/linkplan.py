# implements: DSN-ING-120
"""Authored link plan: load, validate and fail closed (WP-ING-07, TASK-010).

A test scope's link is defined by an explicit, version-controlled plan under
``link-plans/<scope>.yaml`` in the project store. The compilation database never
defines the link on its own. Validation collects every violation with a named
reason. A plan with any violation is refused whole, so an invalid plan never
partially loads.

Satisfies: TOOL-ING-200.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, ClassVar

from ectt.ing.errors import IngestionError
from ectt.prj.errors import InvalidRelativePathError, ProjectConfinementError
from ectt.prj.paths import resolve_project_path, validate_project_path
from ectt.prj.yaml_adapter import RestrictedYamlAdapter

__all__ = [
    "LINK_PLAN_DIR",
    "LINK_PLAN_SCHEMA_VERSION",
    "KNOWN_TOOLCHAINS",
    "LinkInput",
    "LinkPlan",
    "LinkPlanError",
    "LinkPlanViolation",
    "link_plan_relpath",
    "load_link_plan",
    "validate_link_plan",
]

# Restricted YAML (ADR-002) reads every scalar as a string, so the version is compared as "1".
LINK_PLAN_SCHEMA_VERSION: str = "1"
LINK_PLAN_DIR: str = "link-plans"

# Toolchain keys this build knows how to resolve. A key outside this set is
# refused, never guessed. Extending the set is a deliberate change, made with
# the toolchain adapter that understands the key.
KNOWN_TOOLCHAINS: frozenset[str] = frozenset({"gcc", "clang", "msvc"})

INPUT_KINDS: frozenset[str] = frozenset({"object", "archive", "library"})

_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
    {"schema_version", "scope", "toolchain", "linker", "runtime", "entry_point", "link_command", "inputs"}
)
_INPUT_KEYS: frozenset[str] = frozenset({"kind", "path", "identity"})
_SCOPE_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class LinkInput:
    """One ordered link input with its resolved identity (sha256 of the file)."""

    kind: str
    path: str
    identity: str


@dataclass(frozen=True)
class LinkPlan:
    """A validated link plan. Only ever built from a plan with zero violations."""

    scope: str
    toolchain: str
    linker_identity: str
    runtime: str
    entry_point: str
    link_command: tuple[str, ...]
    inputs: tuple[LinkInput, ...]


@dataclass(frozen=True)
class LinkPlanViolation:
    """One named reason a plan is refused. ``entry`` names the offending item."""

    reason: str
    entry: str
    detail: str


class LinkPlanError(IngestionError):
    """A link plan was refused. ``violations`` lists every problem found, in document order."""

    category: ClassVar[str] = "ingestion"

    def __init__(
        self,
        violations: Sequence[LinkPlanViolation],
        *,
        scope: str,
        path: Path | str | None = None,
    ) -> None:
        self.violations: tuple[LinkPlanViolation, ...] = tuple(violations)
        self.scope = scope
        lines = "; ".join(f"{v.reason} at {v.entry}: {v.detail}" for v in self.violations)
        super().__init__(
            f"link plan for scope '{scope}' refused ({len(self.violations)} violation(s)): {lines}",
            reason="link_plan_invalid",
            path=path,
        )


def link_plan_relpath(scope: str) -> str:
    """Project-relative path of the authored plan for ``scope``. Refuses unsafe scope names."""
    if not _SCOPE_RE.match(scope):
        raise LinkPlanError(
            [LinkPlanViolation("invalid_scope_name", "scope", f"{scope!r} is not a simple name")],
            scope=str(scope),
        )
    return f"{LINK_PLAN_DIR}/{scope}.yaml"


def _is_absolute(path_text: str) -> bool:
    return PurePosixPath(path_text).is_absolute() or PureWindowsPath(path_text).is_absolute()


def _check_input(
    index: int,
    raw: Any,
    project_root: Path,
    seen_paths: set[str],
    violations: list[LinkPlanViolation],
) -> LinkInput | None:
    entry = f"inputs[{index}]"
    if not isinstance(raw, Mapping):
        violations.append(LinkPlanViolation("invalid_input", entry, "each input must be a mapping"))
        return None

    before = len(violations)
    violations.extend(
        LinkPlanViolation("unknown_field", entry, f"unknown key '{key}'")
        for key in sorted(str(k) for k in raw)
        if key not in _INPUT_KEYS
    )

    kind = raw.get("kind")
    if not isinstance(kind, str) or not kind:
        violations.append(LinkPlanViolation("missing_field", entry, "'kind' is required"))
    elif kind not in INPUT_KINDS:
        violations.append(LinkPlanViolation("unknown_input_kind", entry, f"kind '{kind}' is not known"))

    path_text = raw.get("path")
    if not isinstance(path_text, str) or not path_text:
        violations.append(LinkPlanViolation("missing_field", entry, "'path' is required"))
        path_text = None
    elif _is_absolute(path_text):
        violations.append(LinkPlanViolation("absolute_path", entry, f"'{path_text}' must be project-relative"))
        path_text = None
    elif ".." in PurePosixPath(path_text.replace("\\", "/")).parts:
        violations.append(LinkPlanViolation("path_outside_project", entry, f"'{path_text}' escapes the project"))
        path_text = None
    else:
        try:
            path_text = validate_project_path(path_text)
        except ProjectConfinementError:
            violations.append(LinkPlanViolation("path_outside_project", entry, f"'{path_text}' escapes the project"))
            path_text = None
        except InvalidRelativePathError:
            violations.append(LinkPlanViolation("invalid_path", entry, f"'{path_text}' is not a valid path"))
            path_text = None

    identity = raw.get("identity")
    if not isinstance(identity, str) or not _SHA256_RE.match(identity):
        violations.append(
            LinkPlanViolation("invalid_identity", entry, "'identity' must be a sha256 hex digest (64 lowercase hex)")
        )
        identity = None

    if path_text is not None:
        if path_text in seen_paths:
            violations.append(LinkPlanViolation("duplicate_input", entry, f"'{path_text}' is listed more than once"))
        seen_paths.add(path_text)

        try:
            resolved = resolve_project_path(project_root, path_text)
        except ProjectConfinementError:
            violations.append(LinkPlanViolation("path_outside_project", entry, f"'{path_text}' escapes the project"))
            resolved = None

        if resolved is not None:
            if not resolved.is_file():
                violations.append(LinkPlanViolation("missing_object", entry, f"'{path_text}' does not exist"))
            elif identity is not None and hashlib.sha256(resolved.read_bytes()).hexdigest() != identity:
                violations.append(
                    LinkPlanViolation("identity_mismatch", entry, f"'{path_text}' differs from its recorded identity")
                )

    if len(violations) != before or kind is None or path_text is None or identity is None:
        return None
    return LinkInput(kind=kind, path=path_text, identity=identity)


def validate_link_plan(
    data: Mapping[str, Any],
    *,
    project_root: Path,
    scope: str,
    path: Path | str | None = None,
) -> LinkPlan:
    """Validate a parsed plan document and return it, or raise ``LinkPlanError``.

    Every problem is collected before raising, so one run reports all of them.
    Nothing is returned unless the whole plan is valid.

    Implements: DSN-ING-120. Satisfies: TOOL-ING-200.
    """
    violations: list[LinkPlanViolation] = []

    violations.extend(
        LinkPlanViolation("unknown_field", key, "unknown top-level key")
        for key in sorted(str(k) for k in data)
        if key not in _TOP_LEVEL_KEYS
    )

    if data.get("schema_version") != LINK_PLAN_SCHEMA_VERSION:
        violations.append(
            LinkPlanViolation(
                "unsupported_schema_version",
                "schema_version",
                f"expected {LINK_PLAN_SCHEMA_VERSION}, got {data.get('schema_version')!r}",
            )
        )

    declared_scope = data.get("scope")
    if declared_scope != scope:
        violations.append(
            LinkPlanViolation("scope_mismatch", "scope", f"plan declares {declared_scope!r}, expected {scope!r}")
        )

    toolchain = data.get("toolchain")
    if not isinstance(toolchain, str) or not toolchain:
        violations.append(LinkPlanViolation("missing_field", "toolchain", "'toolchain' is required"))
        toolchain = None
    elif toolchain not in KNOWN_TOOLCHAINS:
        violations.append(
            LinkPlanViolation("unknown_toolchain_key", "toolchain", f"'{toolchain}' is not a known toolchain")
        )
        toolchain = None

    linker = data.get("linker")
    linker_identity = linker.get("identity") if isinstance(linker, Mapping) else None
    if not isinstance(linker_identity, str) or not linker_identity:
        violations.append(LinkPlanViolation("missing_field", "linker", "'linker.identity' is required"))
        linker_identity = None

    runtime = data.get("runtime")
    if not isinstance(runtime, str) or not runtime:
        violations.append(LinkPlanViolation("missing_field", "runtime", "'runtime' is required"))
        runtime = None

    entry_point = data.get("entry_point")
    if not isinstance(entry_point, str) or not entry_point:
        violations.append(LinkPlanViolation("missing_field", "entry_point", "'entry_point' is required"))
        entry_point = None

    link_command = data.get("link_command")
    command: tuple[str, ...] | None = None
    if not isinstance(link_command, list) or not link_command or not all(
        isinstance(tok, str) and tok for tok in link_command
    ):
        violations.append(
            LinkPlanViolation("missing_field", "link_command", "'link_command' must be a non-empty list of strings")
        )
    else:
        command = tuple(link_command)

    inputs_raw = data.get("inputs")
    checked: list[LinkInput | None] = []
    if not isinstance(inputs_raw, list) or not inputs_raw:
        violations.append(
            LinkPlanViolation(
                "no_link_inputs",
                "inputs",
                "a non-empty ordered list of inputs is required; the compilation database alone does not define the link",
            )
        )
    else:
        seen: set[str] = set()
        for index, raw in enumerate(inputs_raw):
            checked.append(_check_input(index, raw, project_root, seen, violations))

    if violations:
        raise LinkPlanError(violations, scope=scope, path=path)

    inputs = tuple(item for item in checked if item is not None)
    assert toolchain is not None and linker_identity is not None and runtime is not None
    assert entry_point is not None and command is not None
    return LinkPlan(
        scope=scope,
        toolchain=toolchain,
        linker_identity=linker_identity,
        runtime=runtime,
        entry_point=entry_point,
        link_command=command,
        inputs=inputs,
    )


def load_link_plan(project_root: Path, scope: str, *, adapter: RestrictedYamlAdapter | None = None) -> LinkPlan:
    """Load ``link-plans/<scope>.yaml`` from the project store and validate it.

    A missing plan is refused with reason ``missing_plan``. A plan that is not
    restricted YAML raises the prj YAML error unchanged.

    Implements: DSN-ING-120. Satisfies: TOOL-ING-200.
    """
    rel = link_plan_relpath(scope)
    target = resolve_project_path(project_root, rel)
    if not target.is_file():
        raise LinkPlanError(
            [LinkPlanViolation("missing_plan", "scope", f"no authored link plan at '{rel}'")],
            scope=scope,
            path=rel,
        )
    text = target.read_text(encoding="utf-8")
    data = (adapter or RestrictedYamlAdapter()).load(text, path=rel)
    return validate_link_plan(data, project_root=project_root, scope=scope, path=rel)

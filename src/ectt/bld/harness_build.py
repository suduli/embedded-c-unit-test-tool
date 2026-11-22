# implements: TOOL-CBT-010, TOOL-ING-200
"""The harness-build step: link plan, build port, compiled-suite record.

Wires three packages into one build step:

1. **Plan before build.** The authored link plan (``ectt.ing.linkplan``) is
   loaded and validated *before* any build work happens. A refused plan stops
   the build with the plan's named reasons; the build port is never invoked
   and no record is written (DSN-ING-120: fail closed, report every reason).
2. **The build is a port.** Actually producing the harness binary is a
   caller-supplied callable: production supplies the toolchain-driving port,
   tests supply a fake (there is no C compiler on every machine). The step
   owns the layout and the record; the port owns the bytes.
3. **Record at build time.** On success ``ectt.cbt.record_compiled_suite``
   records the built suite (D-02: stable ids plus content digests) and the
   record is stored in the project layout (SDD-003):
   ``<output-root>/<environment>/build/<scope>.suite-record.json``. The
   default output root is ``build/ectt`` per SDD-003.

Re-execution (``ectt.cbt.reexecute_suite`` and its isolated and parallel
forms) consumes that record; nothing in it is needed at run time.

There is deliberately no compiler invocation here. Everything else is
deterministic: same inputs produce byte-identical records (canonical JSON,
content digests, digest-sorted bindings).

Satisfies: TOOL-CBT-010 (record at build time), TOOL-ING-200 (plan before
link), TOOL-EXE-080 (the step consumes the incremental planner's records via
the digests it binds).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ectt.bld.errors import BldError
from ectt.cbt.reexecute import (
    CompiledSuiteRecord,
    bindings_from_cases,
    dump_suite_record,
    load_suite_record,
    record_compiled_suite,
)
from ectt.exh.results import ExecutionMetadata
from ectt.ing.linkplan import LinkPlan, LinkPlanError, LinkPlanViolation, load_link_plan
from ectt.prj.errors import InvalidRelativePathError, ProjectConfinementError
from ectt.prj.paths import resolve_project_path, validate_project_path
from ectt.tcm.datacases import DataDrivenTestCase

__all__ = [
    "DEFAULT_OUTPUT_ROOT",
    "BuiltSuite",
    "HarnessBuildError",
    "HarnessBuildRefusedError",
    "HarnessBuildRequest",
    "SuiteBuildResult",
    "build_harness_suite",
    "environment_build_relpath",
    "load_stored_suite_record",
    "suite_record_relpath",
]

#: SDD-003's default output root, used when a project declares none.
DEFAULT_OUTPUT_ROOT = "build/ectt"

# Same simple-name rule the link plan uses for scopes (DSN-ING-120); one file
# per environment means the environment name must be a single path segment.
_NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}$")

RecordBuildPort = Callable[["HarnessBuildRequest"], str]


class HarnessBuildError(BldError):
    """A harness build step failed for a named, structural reason."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "harness_build_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class HarnessBuildRefusedError(HarnessBuildError):
    """The authored link plan was refused; the build stops before any build work.

    ``reasons`` lists every named violation reason, in document order — the
    refusal never hides the plan's own vocabulary (``missing_plan``,
    ``unknown_toolchain_key``, ``identity_mismatch`, ...).
    """

    def __init__(
        self,
        violations: Sequence[LinkPlanViolation],
        *,
        scope: str,
        path: Path | str | None = None,
    ) -> None:
        self.violations: tuple[LinkPlanViolation, ...] = tuple(violations)
        self.reasons: tuple[str, ...] = tuple(v.reason for v in self.violations)
        lines = "; ".join(f"{v.reason} at {v.entry}: {v.detail}" for v in self.violations)
        super().__init__(
            f"harness build for scope '{scope}' stopped: link plan refused "
            f"({len(self.violations)} violation(s)): {lines}",
            reason="link_plan_refused",
            path=path,
        )


@dataclass(frozen=True)
class HarnessBuildRequest:
    """What the build port is asked to build.

    ``executable`` is the project-relative path the step has chosen for the
    harness binary; the port writes it there and returns the path it actually
    produced (which the record then binds by content digest).
    """

    scope: str
    environment: str
    executable: str
    link_plan: LinkPlan
    cases: tuple[DataDrivenTestCase, ...]


@dataclass(frozen=True)
class BuiltSuite:
    """What a build port returns: the project-relative executable it produced."""

    executable: str


@dataclass(frozen=True)
class SuiteBuildResult:
    """The outcome of one harness build: the record, where it is stored, the plan."""

    record: CompiledSuiteRecord
    record_path: str
    link_plan: LinkPlan


def suite_record_relpath(output_root: str | None, environment: str, scope: str) -> str:
    """Project-relative path of the stored suite record (SDD-003 layout).

    ``<output-root>/<environment>/build/<scope>.suite-record.json`` with the
    SDD-003 default output root when none is declared. Refuses non-simple
    environment or scope names and any non-project-relative output root, so a
    malformed name never reaches the filesystem.
    """
    root = output_root or DEFAULT_OUTPUT_ROOT
    if not _NAME_RE.match(environment):
        raise HarnessBuildError(
            f"environment name {environment!r} is not a simple name", reason="invalid_environment_name"
        )
    if not _NAME_RE.match(scope):
        raise HarnessBuildError(f"scope name {scope!r} is not a simple name", reason="invalid_scope_name")
    try:
        root_posix = validate_project_path(root)
    except (InvalidRelativePathError, ProjectConfinementError) as exc:
        raise HarnessBuildError(
            f"output root {root!r} is not a project-relative path", reason="invalid_output_root"
        ) from exc
    return f"{root_posix}/{environment}/build/{scope}.suite-record.json"


def environment_build_relpath(output_root: str | None, environment: str) -> str:
    """Project-relative directory where one environment's build outputs live."""
    root = output_root or DEFAULT_OUTPUT_ROOT
    if not _NAME_RE.match(environment):
        raise HarnessBuildError(
            f"environment name {environment!r} is not a simple name", reason="invalid_environment_name"
        )
    try:
        root_posix = validate_project_path(root)
    except (InvalidRelativePathError, ProjectConfinementError) as exc:
        raise HarnessBuildError(
            f"output root {root!r} is not a project-relative path", reason="invalid_output_root"
        ) from exc
    return f"{root_posix}/{environment}/build"


def build_harness_suite(
    root: Path | str,
    *,
    scope: str,
    environment: str,
    execution: ExecutionMetadata,
    cases: Sequence[DataDrivenTestCase],
    build: RecordBuildPort,
    output_root: str | None = None,
) -> SuiteBuildResult:
    """Run the harness-build step for one scope: plan, build, record, store.

    Order of operations, each a stop gate for the next:

    1. load and validate the authored link plan — a refusal stops everything
       with the plan's named reasons and the port is never invoked;
    2. invoke the build port with the request (plan, chosen executable path,
       cases); it returns the project-relative executable it produced;
    3. record the built suite (``record_compiled_suite`` validates the
       executable's existence, confinement and the test bindings) and store
       the record's deterministic JSON under the SDD-003 build directory.

    The stored record is exactly what ``ectt.cbt`` re-execution loads; the
    same inputs produce byte-identical records.
    """
    record_rel = suite_record_relpath(output_root, environment, scope)
    executable_rel = record_rel.removesuffix(".suite-record.json")

    try:
        plan = load_link_plan(Path(root), scope)
    except LinkPlanError as exc:
        raise HarnessBuildRefusedError(exc.violations, scope=scope, path=exc.path) from exc

    request = HarnessBuildRequest(
        scope=scope,
        environment=environment,
        executable=executable_rel,
        link_plan=plan,
        cases=tuple(cases),
    )
    produced = build(request)
    if isinstance(produced, BuiltSuite):
        produced = produced.executable

    record = record_compiled_suite(Path(root), produced, execution, bindings_from_cases(cases))

    record_path = resolve_project_path(Path(root), record_rel)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_bytes(dump_suite_record(record).encode("utf-8"))
    return SuiteBuildResult(record=record, record_path=record_rel, link_plan=plan)


def load_stored_suite_record(
    root: Path | str,
    *,
    output_root: str | None = None,
    environment: str,
    scope: str,
) -> CompiledSuiteRecord:
    """Load a stored suite record strictly; a missing file is a named error.

    The returned record is bound by its own digest (tampering is refused) and
    is exactly what ``ectt.cbt.reexecute_suite`` and its isolated/parallel
    forms accept.
    """
    rel = suite_record_relpath(output_root, environment, scope)
    path = resolve_project_path(Path(root), rel)
    if not path.is_file():
        raise HarnessBuildError(
            f"no stored suite record at '{rel}'; the suite must be built first",
            reason="record_missing",
            path=path,
        )
    # Strict load: a tampered or malformed record is refused here, not repaired.
    return load_suite_record(path.read_text(encoding="utf-8"))

# implements: TOOL-CBT-010
"""Re-execute an existing compiled suite without regeneration (WP-CBT-01).

TOOL-CBT-010: the tool shall re-execute an existing test suite without
regeneration or manual reconfiguration.

A :class:`CompiledSuiteRecord` is written once, when a suite is built. It holds
everything needed to run that build again: the harness executable (by
project-relative path and by content digest), where and with which toolchain it
was built, and the test-content digest each allocated test was built from
(D-02: stable ids plus content digests). :func:`reexecute_suite` then needs only
the record, the project root and the *current* test-content digests:

* **No regeneration.** Nothing here imports or calls the generator or the
  build driver (a test checks the imports); the recorded executable is run as
  it is.
* **Binary integrity.** The executable's digest must equal the recorded one;
  a replaced or rebuilt binary is refused (``executable_changed``), because
  results from it would be attributed to a build the record does not describe.
* **Run integrity (T-14, enforced by ``ectt.exh``).** Every re-execution is a
  new attempt allocated before the run (NR-17); the outcome is aggregated from
  finalized per-test records, never the exit status (NR-18); a test whose
  content changed since the build is *not executed* and is reported stale
  (NR-19) so the run is partial and cannot pass as a full one.
* **Distinct runs.** The caller names each re-execution (``run_label``); two
  re-executions of one record get different run ids, so cross-run summaries do
  not see a duplicate.

Satisfies: TOOL-CBT-010; T-14 run-integrity acceptance (NR-17/18/19).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from ectt.cbt.errors import CbtError
from ectt.core.determinism import canonical_json, stable_id
from ectt.exh.results import ExecutionMetadata
from ectt.exh.runner import (
    ExecutedRun,
    ParallelUnit,
    RunAttempt,
    TestBinding,
    allocate_attempt,
    mark_built,
    run_harness,
    run_isolated,
    run_parallel,
)
from ectt.tcm.datacases import DataDrivenTestCase

__all__ = [
    "SUITE_RECORD_VERSION",
    "CompiledSuiteRecord",
    "ParallelReExecution",
    "ReExecution",
    "ReExecutionSpec",
    "bindings_from_cases",
    "current_digests",
    "dump_suite_record",
    "load_suite_record",
    "record_compiled_suite",
    "reexecute_isolated",
    "reexecute_parallel",
    "reexecute_suite",
]

SUITE_RECORD_VERSION = "1"


@dataclass(frozen=True)
class CompiledSuiteRecord:
    """Everything needed to run a built suite again, bound by a digest."""

    executable: str  # project-relative POSIX path
    executable_digest: str
    where: str
    toolchain: str
    target_id: str | None
    order_seed: int | None
    bindings: tuple[TestBinding, ...]
    record_id: str

    def execution(self) -> ExecutionMetadata:
        return ExecutionMetadata(
            where=self.where,
            toolchain=self.toolchain,
            target_id=self.target_id,
            order_seed=self.order_seed,
        )

    def body(self) -> dict[str, Any]:
        return {
            "bindings": [{"artifact_digest": b.artifact_digest, "test_id": b.test_id} for b in self.bindings],
            "executable": self.executable,
            "executable_digest": self.executable_digest,
            "order_seed": self.order_seed,
            "target_id": self.target_id,
            "toolchain": self.toolchain,
            "where": self.where,
        }


@dataclass(frozen=True)
class ReExecution:
    """Result of one re-execution of a recorded suite."""

    run: ExecutedRun
    record_id: str
    executable_digest: str
    regenerated: bool = False

    @property
    def stale_test_ids(self) -> tuple[str, ...]:
        return self.run.stale_ids


def _file_digest(path: Path) -> str:
    return stable_id(path.read_bytes())


def _confined(root: Path, relative: str) -> Path:
    posix = relative.replace("\\", "/")
    parts = posix.split("/")
    if not posix or posix.startswith("/") or ":" in parts[0] or ".." in parts:
        raise CbtError(f"executable path '{relative}' must be relative and stay inside the project", reason="path_escape")
    resolved = (root / posix).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise CbtError(f"executable path '{relative}' leaves the project root", reason="path_escape")
    return resolved


def _record_id(body: Mapping[str, Any]) -> str:
    return stable_id(canonical_json(dict(body)))


def record_compiled_suite(
    root: Path | str,
    executable: str,
    execution: ExecutionMetadata,
    bindings: Sequence[TestBinding],
) -> CompiledSuiteRecord:
    """Record a freshly built suite so it can be re-executed later.

    ``executable`` is a path relative to ``root``; its content digest is taken
    now. The bindings are the tests the build was made from and their
    test-content digests (``bindings_from_cases`` builds them from cases).
    """
    root_path = Path(root)
    exe = _confined(root_path, executable)
    if not exe.is_file():
        raise CbtError(f"compiled suite executable '{executable}' does not exist", reason="executable_missing", path=exe)
    if not bindings:
        raise CbtError("a compiled suite record needs at least one test binding", reason="no_bindings")
    ordered = tuple(sorted(bindings, key=lambda b: b.test_id))
    allocate_attempt(execution, ordered)  # validates ids and digests with the runner's own rules
    draft = CompiledSuiteRecord(
        executable=executable.replace("\\", "/"),
        executable_digest=_file_digest(exe),
        where=execution.where,
        toolchain=execution.toolchain,
        target_id=execution.target_id,
        order_seed=execution.order_seed,
        bindings=ordered,
        record_id="",
    )
    return replace(draft, record_id=_record_id(draft.body()))


def bindings_from_cases(cases: Sequence[DataDrivenTestCase]) -> tuple[TestBinding, ...]:
    """Bind each case id to its current content digest (D-02)."""
    return tuple(TestBinding(case.case_id, case.content_digest) for case in sorted(cases, key=lambda c: c.case_id))


def current_digests(cases: Sequence[DataDrivenTestCase]) -> dict[str, str]:
    """The current test-content digest of each case, for the binding check."""
    return {case.case_id: case.content_digest for case in cases}


def dump_suite_record(record: CompiledSuiteRecord) -> str:
    """Deterministic JSON text of a record."""
    return canonical_json({"record_id": record.record_id, "record_version": SUITE_RECORD_VERSION, **record.body()})


def load_suite_record(text: str) -> CompiledSuiteRecord:
    """Strictly load a record; refuses unknown versions, malformed fields and tampering."""
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CbtError(f"suite record is not valid JSON: {exc}", reason="invalid_record") from exc
    if not isinstance(doc, dict) or doc.get("record_version") != SUITE_RECORD_VERSION:
        raise CbtError(
            f"unsupported suite record (expected record_version {SUITE_RECORD_VERSION!r})",
            reason="unsupported_record_version",
        )
    required = ("bindings", "executable", "executable_digest", "record_id", "toolchain", "where")
    missing = [key for key in required if key not in doc]
    if missing:
        raise CbtError(f"suite record is missing {', '.join(missing)}", reason="invalid_record")
    raw_bindings = doc["bindings"]
    if not isinstance(raw_bindings, list) or not all(isinstance(b, dict) and {"test_id", "artifact_digest"} <= set(b) for b in raw_bindings):
        raise CbtError("suite record bindings are malformed", reason="invalid_record")
    try:
        record = CompiledSuiteRecord(
            executable=str(doc["executable"]),
            executable_digest=str(doc["executable_digest"]),
            where=str(doc["where"]),
            toolchain=str(doc["toolchain"]),
            target_id=None if doc.get("target_id") is None else str(doc["target_id"]),
            order_seed=None if doc.get("order_seed") is None else int(doc["order_seed"]),
            bindings=tuple(TestBinding(str(b["test_id"]), str(b["artifact_digest"])) for b in raw_bindings),
            record_id=str(doc["record_id"]),
        )
    except (TypeError, ValueError) as exc:
        raise CbtError(f"suite record has a malformed field: {exc}", reason="invalid_record") from exc
    if _record_id(record.body()) != record.record_id:
        raise CbtError("stored suite record id does not match its content", reason="digest_mismatch")
    return record


def _checked_attempt(record: CompiledSuiteRecord, root: Path | str, run_label: str) -> tuple[RunAttempt, Path]:
    """Shared re-execution integrity gate: record, binary, then a built attempt.

    Validates the run label and the record's own digest, confines and
    existence-checks the recorded executable, refuses a binary whose content
    no longer matches the recorded build, and returns the built attempt (with
    a run id naming this record and this re-execution) plus the executable
    path. Every re-execution form — plain, isolated, parallel — goes through
    exactly this gate, so runner choice cannot weaken integrity.
    """
    if not isinstance(run_label, str) or not run_label.strip() or any(c.isspace() for c in run_label):
        raise CbtError("run_label must be a non-empty string without whitespace", reason="invalid_run_label")
    if _record_id(record.body()) != record.record_id:
        raise CbtError("suite record id does not match its content", reason="digest_mismatch")

    exe = _confined(Path(root), record.executable)
    if not exe.is_file():
        raise CbtError(
            f"recorded executable '{record.executable}' no longer exists; the suite must be rebuilt (it is not regenerated here)",
            reason="executable_missing",
            path=exe,
        )
    if _file_digest(exe) != record.executable_digest:
        raise CbtError(
            f"executable '{record.executable}' differs from the recorded build; results would not describe that build",
            reason="executable_changed",
            path=exe,
        )

    attempt = allocate_attempt(record.execution(), record.bindings)
    attempt = mark_built(attempt)
    attempt = _distinct(attempt, record, run_label)
    return attempt, exe


def reexecute_suite(
    record: CompiledSuiteRecord,
    root: Path | str,
    current: Mapping[str, str],
    *,
    run_label: str,
    argv_prefix: Sequence[str] = (),
) -> ReExecution:
    """Run the recorded suite again exactly as built; never regenerates or rebuilds.

    ``current`` maps test ids to their current content digests; tests whose
    digest differs from the recorded one are not executed and are reported in
    ``stale_test_ids``. ``run_label`` distinguishes this re-execution from
    others of the same record (it becomes part of the run id).
    ``argv_prefix`` is for interpreter-hosted stub harnesses in tests.
    """
    attempt, exe = _checked_attempt(record, root, run_label)
    run = run_harness(attempt, exe, current_digests=current, argv_prefix=argv_prefix)
    return ReExecution(run=run, record_id=record.record_id, executable_digest=record.executable_digest)


def reexecute_isolated(
    record: CompiledSuiteRecord,
    root: Path | str,
    current: Mapping[str, str],
    *,
    run_label: str,
    timeout_seconds: float,
    argv_prefix: Sequence[str] = (),
    cwd: Path | str | None = None,
) -> ReExecution:
    """Re-execute through ``ectt.exh.run_isolated`` (process-granularity isolation).

    The same integrity gate as :func:`reexecute_suite` (record digest, binary
    digest, NR-19 binding check inside the runner); each non-stale test runs
    in its own harness process with ``--ectt-select``. A crash costs one
    ``error`` record, a hang past ``timeout_seconds`` one ``timeout`` record;
    the remaining tests still execute.
    """
    attempt, exe = _checked_attempt(record, root, run_label)
    run = run_isolated(
        attempt,
        exe,
        current_digests=current,
        timeout_seconds=timeout_seconds,
        argv_prefix=argv_prefix,
        cwd=cwd,
    )
    return ReExecution(run=run, record_id=record.record_id, executable_digest=record.executable_digest)


@dataclass(frozen=True)
class ReExecutionSpec:
    """One recorded suite to re-execute in parallel, with its run inputs.

    ``root`` is that record's project root and ``current`` its current
    test-content digests; specs may come from different projects.
    """

    record: CompiledSuiteRecord
    root: Path | str
    current: Mapping[str, str]
    run_label: str


@dataclass(frozen=True)
class ParallelReExecution:
    """Per-record re-executions in input order plus the aggregated outcome."""

    reexecutions: tuple[ReExecution, ...]
    outcome: str
    worker_dirs: tuple[str, ...] = ()


def reexecute_parallel(
    specs: Sequence[ReExecutionSpec],
    *,
    concurrency: int,
    timeout_seconds: float,
    worker_root: Path | str | None = None,
    argv_prefix: Sequence[str] = (),
) -> ParallelReExecution:
    """Re-execute recorded suites concurrently through ``ectt.exh.run_parallel``.

    Every spec passes the integrity gate *before* any process starts: one
    tampered or missing binary refuses the whole call (no partial side
    effects). Two specs with the same record and run label would collide on
    the run id and are refused. Results are returned in input order; the
    outcome aggregates per-record outcomes (pass only when every
    re-execution passed).
    """
    if not specs:
        raise CbtError("parallel re-execution requires at least one recorded suite", reason="no_specs")
    seen: set[str] = set()
    checked: list[tuple[ReExecutionSpec, RunAttempt, Path]] = []
    for spec in specs:
        run_id = stable_id(spec.record.record_id, spec.run_label)
        if run_id in seen:
            raise CbtError(
                f"two specs share record '{spec.record.record_id}' and run label '{spec.run_label}'; "
                "their run ids would collide",
                reason="duplicate_run",
            )
        seen.add(run_id)
        attempt, exe = _checked_attempt(spec.record, spec.root, spec.run_label)
        checked.append((spec, attempt, exe))

    units = tuple(
        ParallelUnit(attempt=attempt, executable=exe, current_digests=spec.current)
        for spec, attempt, exe in checked
    )
    parallel = run_parallel(
        units,
        concurrency=concurrency,
        timeout_seconds=timeout_seconds,
        worker_root=worker_root,
        argv_prefix=argv_prefix,
    )
    reexecutions = tuple(
        ReExecution(
            run=unit,
            record_id=spec.record.record_id,
            executable_digest=spec.record.executable_digest,
        )
        for (spec, _attempt, _exe), unit in zip(checked, parallel.units, strict=True)
    )
    return ParallelReExecution(
        reexecutions=reexecutions,
        outcome=parallel.outcome,
        worker_dirs=parallel.worker_dirs,
    )


def _distinct(attempt: RunAttempt, record: CompiledSuiteRecord, run_label: str) -> RunAttempt:
    """Give the attempt a run id that names this record and this re-execution."""
    return replace(attempt, attempt_id=stable_id(record.record_id, run_label))

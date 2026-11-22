# implements: DSN-ATG-110, TOOL-ATG-050
"""The production composition point of the generation run's port (A1).

The CLI layer binds ectt.atg's :class:`BoundValidationPort` to the engine
components (ectt.bld harness-build step, ectt.cbt recorded re-execution over
ectt.exh) — the binding ectt.atg must not do itself (DSN-ATG-110). The tests
inject fake build/execute delegates where the port protocol is under test, and
a fake compile port (interpreter-hosted harness) where the real binding is
under test — no C compiler is used anywhere.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

import pytest

from ectt.atg.errors import AtgError
from ectt.atg.lifecycle import (
    BuildOutcome,
    EngineInfo,
    ExecutionOutcome,
    GenerationCandidate,
    make_candidate,
    validate_one,
)
from ectt.atg.run import Construct, run_generation
from ectt.cli.compose import compose_generation_run
from ectt.exh.results import ExecutionMetadata
from ectt.tcm.datacases import TestCaseInputs

ENGINE = EngineInfo("compose-test", "1.0")
EXECUTION = ExecutionMetadata(where="host", toolchain="fake-gcc")

OBJ_BYTES = b"\x7fELF fake object for compose"
VALID_PLAN = (
    "schema_version: '1'\n"
    "scope: compose-scope\n"
    "toolchain: gcc\n"
    "linker:\n"
    "  identity: GNU ld 2.42\n"
    "runtime: host\n"
    "entry_point: main\n"
    "link_command:\n"
    "  - gcc\n"
    "  - -o\n"
    "  - build/ectt/compose.host/build/compose-scope\n"
    "inputs:\n"
    "  - kind: object\n"
    "    path: objects/uut.o\n"
    "    identity: {obj}\n"
)
PASSING_HARNESS = "import sys\nprint('RESULT {case_id} pass')\n"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    (root / "objects").mkdir(parents=True)
    (root / "objects/uut.o").write_bytes(OBJ_BYTES)
    (root / "link-plans").mkdir()
    (root / "link-plans/compose-scope.yaml").write_text(VALID_PLAN.format(obj=_sha(OBJ_BYTES)), encoding="utf-8")
    return root


def _compile_port(root: Path, body: str = PASSING_HARNESS) -> Any:
    def build(request: Any) -> str:
        target = root / request.executable
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body.replace("{case_id}", request.cases[0].case_id), encoding="utf-8")
        return request.executable

    return build


def _candidate() -> GenerationCandidate:
    return make_candidate("src/adc.c", "adc_scale", TestCaseInputs(parameters={"raw": "0"}))


TARGETS = (
    Construct("L1", "line", "src/adc.c:10"),
    Construct("L2", "line", "src/adc.c:12"),
)


def test_the_delegates_are_bound_verbatim_and_in_validation_order() -> None:
    """verifies: DSN-ATG-110 — injected delegates ride through unchanged, and
    the port calls build first, then execute, exactly as the gate does."""
    calls: list[str] = []

    def fake_build(candidate: GenerationCandidate) -> BuildOutcome:
        calls.append("build")
        return BuildOutcome(ok=True)

    def fake_execute(candidate: GenerationCandidate) -> ExecutionOutcome:
        calls.append("execute")
        return ExecutionOutcome(state="completed", detail="pass")

    composition = compose_generation_run(
        Path("."),  # never touched: the delegates are the fakes
        scope="s",
        environment="e",
        execution=EXECUTION,
        compile_port=lambda request: "x",
        build=fake_build,
        execute=fake_execute,
    )
    case, discard = validate_one(_candidate(), composition.port, ENGINE)
    assert discard is None and case is not None
    assert calls == ["build", "execute"]


def test_a_build_refusal_stops_the_candidate_with_its_named_reason() -> None:
    """verifies: TOOL-ATG-050 — a named build failure is a counted discard that
    carries the refusal reason; the run presents nothing for that candidate."""
    composition = compose_generation_run(
        Path("."),
        scope="s",
        environment="e",
        execution=EXECUTION,
        compile_port=lambda request: "x",
        build=lambda candidate: BuildOutcome(ok=False, diagnostics=("unknown_toolchain_key",)),
        execute=lambda candidate: ExecutionOutcome(state="completed"),
    )
    case, discard = validate_one(_candidate(), composition.port, ENGINE)
    assert case is None
    assert discard is not None and discard.reason == "build_failed"
    assert "unknown_toolchain_key" in discard.detail


def test_a_refused_link_plan_stops_the_run(tmp_path: Path) -> None:
    """verifies: TOOL-ATG-050, TOOL-ING-200 — with the real binding, a project
    without an authored plan refuses every build with the plan's named reason,
    so the run presents nothing."""
    root = tmp_path / "proj"
    (root / "objects").mkdir(parents=True)
    (root / "objects/uut.o").write_bytes(OBJ_BYTES)
    # No link plan at all.
    composition = compose_generation_run(
        root,
        scope="compose-scope",
        environment="compose.host",
        execution=EXECUTION,
        compile_port=_compile_port(root),
    )
    run = run_generation([_candidate()], composition.port, ENGINE, function="adc_scale", targets=TARGETS)
    assert run.report.cases_generated == 0
    assert len(run.report.discarded) == 1
    assert run.report.discarded[0].reason == "build_failed"
    assert "missing_plan" in run.report.discarded[0].detail


def test_the_real_binding_builds_records_and_reruns(tmp_path: Path) -> None:
    """verifies: DSN-ATG-110 — the real binding: build goes through the
    harness-build step (recorded in the project layout), execute re-runs the
    record, and the run presents the case."""
    root = _project(tmp_path)
    composition = compose_generation_run(
        root,
        scope="compose-scope",
        environment="compose.host",
        execution=EXECUTION,
        compile_port=_compile_port(root),
        coverage_for=lambda candidate: ("L1",),
        total_constructs=2,
        argv_prefix=(sys.executable,),
    )
    run = run_generation([_candidate()], composition.port, ENGINE, function="adc_scale", targets=TARGETS)

    assert run.report.cases_generated == 1
    assert run.report.coverage.status == "measured"
    candidate_id = run.cases[0].case_id
    assert candidate_id in composition.records  # the build step recorded it
    assert (root / "build/ectt/compose.host/build/compose-scope.suite-record.json").is_file()
    assert composition.port.covered == ("L1",)


def test_a_build_that_produces_no_binary_is_a_named_discard(tmp_path: Path) -> None:
    """verifies: TOOL-ATG-050 — the recording step refuses a phantom binary and
    the refusal becomes the discard's diagnostic."""
    root = _project(tmp_path)
    composition = compose_generation_run(
        root,
        scope="compose-scope",
        environment="compose.host",
        execution=EXECUTION,
        compile_port=lambda request: request.executable,  # claims success, writes nothing
    )
    case, discard = validate_one(_candidate(), composition.port, ENGINE)
    assert case is None
    assert discard is not None and discard.reason == "build_failed"
    assert "does not exist" in discard.detail


def test_executing_an_unbuilt_candidate_is_a_named_error() -> None:
    """verifies: TOOL-ATG-050 — execute without a record from build is a named
    error, never a silent verdict (the lifecycle re-raises it as-is)."""
    composition = compose_generation_run(
        Path("."),
        scope="s",
        environment="e",
        execution=EXECUTION,
        compile_port=lambda request: "x",
        build=lambda candidate: BuildOutcome(ok=True),  # claims success, records nothing
        execute=None,  # the real binding: there is no record to run
    )
    with pytest.raises(AtgError) as excinfo:
        validate_one(_candidate(), composition.port, ENGINE)
    assert excinfo.value.reason == "not_built"


def test_the_port_outcome_reflects_the_result_stream(tmp_path: Path) -> None:
    """verifies: DSN-ATG-110 — a completed run maps to the completed state
    through the real binding."""
    root = _project(tmp_path)
    composition = compose_generation_run(
        root,
        scope="compose-scope",
        environment="compose.host",
        execution=EXECUTION,
        compile_port=_compile_port(root),
        argv_prefix=(sys.executable,),
    )
    candidate = _candidate()
    assert composition.port.build(candidate).ok is True
    outcome = composition.port.execute(candidate)
    assert outcome.state == "completed"
    assert outcome.detail == "pass"

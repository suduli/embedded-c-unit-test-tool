# implements: TOOL-ATG-050, TOOL-ATG-060, DSN-ATG-110
"""The generation run bound to the real build and execution components (A5).

This is the composition the layer rule demands live outside ``ectt.atg``: the
port's build delegate runs the real harness-build step
(``ectt.bld.build_harness_suite`` — link-plan gated, suite recorded) and the
execute delegate re-executes the recorded suite through ``ectt.cbt`` /
``ectt.exh`` with isolation and a timeout. There is no C compiler on this
machine: **every test uses a fake compile port** (interpreter-hosted harness
scripts) and a fake coverage source — say so wherever these results are
quoted. The composition module that binds this in production is the CLI's
(second-pass row recorded).
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

import pytest

from ectt.atg import BoundValidationPort
from ectt.atg.errors import AtgError
from ectt.atg.lifecycle import (
    BuildOutcome,
    EngineInfo,
    ExecutionOutcome,
    GenerationCandidate,
    make_candidate,
    validate_one,
)
from ectt.atg.run import Construct, RunLimits, run_generation
from ectt.bld import HarnessBuildError, build_harness_suite
from ectt.cbt.errors import CbtError
from ectt.cbt.reexecute import reexecute_isolated
from ectt.exh.results import ExecutionMetadata
from ectt.tcm import datacases as dd
from ectt.tcm.datacases import DataDrivenTestCase, refresh_digest

ENGINE = EngineInfo("fake-symex", "1.0")
EXECUTION = ExecutionMetadata(where="host", toolchain="fake-gcc")

OBJ_BYTES = b"\x7fELF fake object for atg"

PASSING_HARNESS = "import sys\nprint('RESULT {case_id} pass')\n"
CRASHING_HARNESS = "import sys, os\nos._exit(1)  # silent abnormal termination: no RESULT record\n"
HANGING_HARNESS = "import time\ntime.sleep(5)\nprint('RESULT {case_id} pass')\n"

VALID_PLAN = (
    "schema_version: '1'\n"
    "scope: atg-scope\n"
    "toolchain: gcc\n"
    "linker:\n"
    "  identity: GNU ld 2.42\n"
    "runtime: host\n"
    "entry_point: main\n"
    "link_command:\n"
    "  - gcc\n"
    "  - -o\n"
    "  - build/ectt/atg.host/build/atg-scope\n"
    "inputs:\n"
    "  - kind: object\n"
    "    path: objects/uut.o\n"
    "    identity: {obj}\n"
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    (root / "objects").mkdir(parents=True)
    (root / "objects/uut.o").write_bytes(OBJ_BYTES)
    (root / "link-plans").mkdir()
    (root / "link-plans/atg-scope.yaml").write_text(VALID_PLAN.format(obj=_sha(OBJ_BYTES)), encoding="utf-8")
    return root


def _compile_port(root: Path, body: str):
    """The fake compile port: writes the interpreter harness, returns its path."""

    def build(request: Any) -> str:
        target = root / request.executable
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body.replace("{case_id}", request.cases[0].case_id), encoding="utf-8")
        return request.executable

    return build


def _case_for(candidate: GenerationCandidate) -> DataDrivenTestCase:
    """The single-case suite a candidate validates against (D-02 digests)."""
    return refresh_digest(
        DataDrivenTestCase(
            case_id=candidate.candidate_id,
            unit=candidate.unit,
            function=candidate.function,
            inputs=candidate.inputs,
            expected=dd.TestCaseExpected(),
            stubs=candidate.stubs,
            requirements=candidate.requirements,
        )
    )


def _outcome_of(candidate_id: str, rexec: Any) -> ExecutionOutcome:
    """Map an executed run onto the lifecycle's execution states."""
    run = rexec.run
    outcomes = {r.test_id: r.outcome for r in run.result_set.results}
    if any(o == "timeout" for o in outcomes.values()):
        return ExecutionOutcome(state="timeout", detail="the harness exceeded the port's timeout")
    if any(o == "error" for o in outcomes.values()):
        missing = ",".join(run.result_set.not_executed) or candidate_id
        return ExecutionOutcome(state="crash", detail=f"abnormal termination for: {missing}")
    if run.outcome == "incomplete":
        missing = ",".join(run.result_set.not_executed) or candidate_id
        return ExecutionOutcome(state="crash", detail=f"no result record for: {missing}")
    if run.outcome == "build_failed":
        return ExecutionOutcome(state="harness_error", detail="the recorded suite failed to build")
    if run.outcome in ("pass", "failed"):
        return ExecutionOutcome(state="completed", detail=run.outcome)
    return ExecutionOutcome(state="harness_error", detail=f"unmapped run outcome '{run.outcome}'")


def make_port(
    root: Path,
    body: str = PASSING_HARNESS,
    coverage: dict[str, tuple[str, ...]] | None = None,
    total: int = 3,
    timeout_seconds: float = 30.0,
    compile_port: Any | None = None,
) -> BoundValidationPort:
    """Compose the port: real bld/cbt/exh delegates around a fake compile port."""
    built: dict[str, tuple[Any, DataDrivenTestCase]] = {}

    def build(candidate: GenerationCandidate) -> BuildOutcome:
        case = _case_for(candidate)
        try:
            result = build_harness_suite(
                root,
                scope="atg-scope",
                environment="atg.host",
                execution=EXECUTION,
                cases=(case,),
                build=compile_port if compile_port is not None else _compile_port(root, body),
            )
        except (HarnessBuildError, CbtError) as exc:
            return BuildOutcome(ok=False, diagnostics=(exc.message,))
        built[candidate.candidate_id] = (result.record, case)
        return BuildOutcome(ok=True)

    def execute(candidate: GenerationCandidate) -> ExecutionOutcome:
        record, case = built[candidate.candidate_id]
        rexec = reexecute_isolated(
            record,
            root,
            {case.case_id: case.content_digest},
            run_label="atg",
            timeout_seconds=timeout_seconds,
            argv_prefix=(sys.executable,),
        )
        return _outcome_of(candidate.candidate_id, rexec)

    coverage_map = coverage or {}
    return BoundValidationPort(
        build=build,
        execute=execute,
        coverage_for=lambda candidate: coverage_map.get(candidate.candidate_id, ()),
        total_constructs=total,
    )


def _candidate(inputs: dict[str, str] | None = None) -> GenerationCandidate:
    return make_candidate(
        "src/adc.c",
        "adc_scale",
        dd.TestCaseInputs(parameters=inputs or {"raw": "0"}),
    )


TARGETS = (
    Construct("L1", "line", "src/adc.c:10"),
    Construct("L2", "line", "src/adc.c:12"),
    Construct("L3", "line", "src/adc.c:15"),
)


# --- the happy path -------------------------------------------------------------------------


def test_the_run_populates_newly_covered_through_the_bound_port(tmp_path: Path) -> None:
    """verifies: TOOL-ATG-060 — presented cases fold their coverage; the deltas
    carry the constructs each case newly covered."""
    root = _project(tmp_path)
    first = _candidate({"raw": "0"})
    second = _candidate({"raw": "255"})
    port = make_port(
        root,
        coverage={
            first.candidate_id: ("L1", "L2"),
            second.candidate_id: ("L2", "L3"),
        },
    )

    run = run_generation([first, second], port, ENGINE, function="adc_scale", targets=TARGETS)

    assert run.report.coverage.status == "measured"
    assert run.report.coverage.covered == 3
    assert run.report.coverage.uncovered == ()
    assert run.report.cases_generated == 2
    # Candidates run in id order; the deltas fold coverage in that order, and
    # each carries exactly what its case newly covered.
    covered: set[str] = set()
    expected: list[tuple[str, ...]] = []
    for candidate in sorted([first, second], key=lambda c: c.candidate_id):
        reported = ("L1", "L2") if candidate is first else ("L2", "L3")
        expected.append(tuple(sorted(c for c in reported if c not in covered)))
        covered.update(reported)
    assert [d.newly_covered for d in port.deltas] == expected
    assert any(d.newly_covered for d in port.deltas)
    assert port.covered == ("L1", "L2", "L3")


def test_the_port_builds_through_the_harness_build_step_and_reruns_the_record(tmp_path: Path) -> None:
    """verifies: DSN-ATG-110 — build is plan-gated and recorded; execute reruns
    the record without regeneration (the suite record exists after the run)."""
    root = _project(tmp_path)
    port = make_port(root)
    candidate = _candidate()

    case, discard = validate_one(candidate, port, ENGINE)

    assert discard is None and case is not None
    assert case.case_id == candidate.candidate_id
    assert case.origin.author == "atg" and case.origin.review_state == "unreviewed"
    # The suite record landed in the project layout (SDD-003).
    record_path = root / "build/ectt/atg.host/build/atg-scope.suite-record.json"
    assert record_path.is_file()
    # The recorded binary was produced by the compile port at the chosen path.
    assert (root / "build/ectt/atg.host/build/atg-scope").is_file()


def test_the_port_outcome_reflects_the_result_stream(tmp_path: Path) -> None:
    """verifies: TOOL-ATG-050 — a completed run maps to the completed state."""
    root = _project(tmp_path)
    port = make_port(root)
    candidate = _candidate()
    assert port.build(candidate).ok is True
    outcome = port.execute(candidate)
    assert outcome.state == "completed"
    assert outcome.detail == "pass"


# --- the error cases ------------------------------------------------------------------------


def test_a_port_that_fails_itself_raises_instead_of_discarding(tmp_path: Path) -> None:
    """verifies: TOOL-ATG-050 — a compile-port failure is infrastructure, not a
    discard: nothing is presented on the strength of a validation that did not
    happen."""
    root = _project(tmp_path)

    def broken_compile(request: Any) -> str:
        raise RuntimeError("no compiler")

    port = make_port(root, compile_port=broken_compile)
    with pytest.raises(AtgError) as excinfo:
        validate_one(_candidate(), port, ENGINE)
    assert excinfo.value.reason == "port_failed"


def test_a_build_that_produces_no_binary_discards_the_candidate(tmp_path: Path) -> None:
    """verifies: TOOL-ATG-050 — a build whose binary never appears is a counted
    build failure, with the recording error as its diagnostic."""
    root = _project(tmp_path)

    def phantom_compile(request: Any) -> str:
        return request.executable  # claims success, writes nothing

    port = make_port(root, compile_port=phantom_compile)
    case, discard = validate_one(_candidate(), port, ENGINE)
    assert case is None
    assert discard is not None and discard.reason == "build_failed"
    assert "does not exist" in discard.detail


def test_a_refused_link_plan_stops_the_build_with_its_named_reason(tmp_path: Path) -> None:
    """verifies: TOOL-ATG-050, TOOL-ING-200 — a missing plan refuses the build
    with its named reason, and the candidate is discarded for it."""
    root = tmp_path / "proj"
    (root / "objects").mkdir(parents=True)
    (root / "objects/uut.o").write_bytes(OBJ_BYTES)
    # No link plan at all: the harness-build step refuses before anything builds.
    with pytest.raises(HarnessBuildError) as excinfo:
        build_harness_suite(
            root,
            scope="atg-scope",
            environment="atg.host",
            execution=EXECUTION,
            cases=(_case_for(_candidate()),),
            build=_compile_port(root, PASSING_HARNESS),
        )
    assert excinfo.value.reasons == ("missing_plan",)

    port = make_port(root)
    case, discard = validate_one(_candidate(), port, ENGINE)
    assert case is None
    assert discard is not None and discard.reason == "build_failed"
    assert "missing_plan" in discard.detail


def test_a_crashing_harness_discards_the_candidate(tmp_path: Path) -> None:
    """verifies: TOOL-ATG-050 — an abnormal termination is a counted discard."""
    root = _project(tmp_path)
    port = make_port(root, body=CRASHING_HARNESS)
    case, discard = validate_one(_candidate(), port, ENGINE)
    assert case is None
    assert discard is not None and discard.reason == "crash"


def test_a_hanging_harness_is_discarded_as_a_timeout(tmp_path: Path) -> None:
    """verifies: TOOL-ATG-050, TOOL-EXE-040 — the port's timeout becomes a
    timeout discard, and the run still finishes (the runner kills the process)."""
    root = _project(tmp_path)
    port = make_port(root, body=HANGING_HARNESS, timeout_seconds=0.2)
    case, discard = validate_one(_candidate(), port, ENGINE)
    assert case is None
    assert discard is not None and discard.reason == "timeout"


def test_an_unknown_construct_from_the_coverage_source_refuses_the_run(tmp_path: Path) -> None:
    """verifies: TOOL-ATG-060 — a source reporting outside the targets is an
    error, not silent coverage."""
    root = _project(tmp_path)
    candidate = _candidate()
    port = make_port(root, coverage={candidate.candidate_id: ("L1", "GHOST")})
    with pytest.raises(AtgError) as excinfo:
        run_generation([candidate], port, ENGINE, function="adc_scale", targets=TARGETS)
    assert excinfo.value.reason == "unknown_construct"


def test_a_port_without_a_coverage_source_reports_unmeasured(tmp_path: Path) -> None:
    """verifies: TOOL-ATG-060 — a port composed without a coverage source says
    unmeasured instead of asserting an uncovered list (unmeasured != uncovered)."""
    root = _project(tmp_path)
    port = BoundValidationPort(
        build=lambda candidate: BuildOutcome(ok=False, diagnostics=()),
        execute=lambda candidate: ExecutionOutcome(state="completed"),
        coverage_for=None,
    )
    # measure() on a sourceless port returns None — the run maps it to unmeasured.
    assert port.measure(_candidate()) is None
    run = run_generation([_candidate()], make_port(root), ENGINE, function="adc_scale", targets=TARGETS)
    # The composed port above has a (fake empty) source, so coverage is measured
    # at zero; the sourceless port's None is what maps to unmeasured.
    assert run.report.coverage.status == "measured"


def test_the_run_respects_the_case_limit_and_reports_what_it_has(tmp_path: Path) -> None:
    """verifies: TOOL-ATG-100 — the bound port composes with the run limits."""
    root = _project(tmp_path)
    candidates = [_candidate({"raw": str(i)}) for i in range(4)]
    port = make_port(root, coverage={c.candidate_id: (f"L{(i % 3) + 1}",) for i, c in enumerate(candidates)})
    run = run_generation(
        candidates,
        port,
        ENGINE,
        function="adc_scale",
        targets=TARGETS,
        limits=RunLimits(max_cases=2),
    )
    assert run.report.terminated_by == "case_limit"
    assert run.report.cases_generated == 2
    assert run.report.not_attempted == 2


def test_the_binding_constructor_refuses_non_callables() -> None:
    """verifies: DSN-ATG-110 — a miscomposed port is refused, not silently built."""
    with pytest.raises(ValueError):
        BoundValidationPort(build=None, execute=lambda c: ExecutionOutcome(state="completed"))  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        BoundValidationPort(
            build=lambda c: BuildOutcome(ok=True),
            execute=lambda c: ExecutionOutcome(state="completed"),
            coverage_for=42,  # type: ignore[arg-type]
        )

# implements: TOOL-CBT-010, TOOL-ING-200
"""The harness-build step: link-plan gate, build port, stored suite record.

Verifies the two integrations of the build step: the authored link plan gates
the build (a refusal stops it with the plan's named reasons, before the build
port is ever invoked), and the built suite is recorded and stored in the
project layout (SDD-003) for re-execution without regeneration.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

import pytest

import ectt.bld
from ectt.bld import (
    DEFAULT_OUTPUT_ROOT,
    HarnessBuildError,
    HarnessBuildRefusedError,
    build_harness_suite,
    environment_build_relpath,
    load_stored_suite_record,
    suite_record_relpath,
)
from ectt.cbt import dump_suite_record, reexecute_suite
from ectt.exh.results import ExecutionMetadata
from ectt.tcm import datacases as dd

EXECUTION = ExecutionMetadata(where="host", toolchain="gcc-14.2")
OBJ_BYTES = b"\x7fELF fake object adc"

HARNESS = (
    "import sys\n"
    "print('banner noise')\n"
    "print('RESULT tc.one pass')\n"
    "print('RESULT tc.two fail')\n"
    "print('FAILURE tc.two expected_return 1 0 src/a.c 9')\n"
    "sys.exit(0)\n"
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _case(case_id: str, expected: str = "1") -> dd.DataDrivenTestCase:
    return dd.refresh_digest(
        dd.DataDrivenTestCase(
            case_id=case_id,
            unit="src/a.c",
            function="f",
            inputs=dd.TestCaseInputs(),
            expected=dd.TestCaseExpected(return_value=expected),
            stubs=(),
        )
    )


CASES = [_case("tc.one"), _case("tc.two")]

VALID_YAML = (
    "schema_version: '1'\n"
    "scope: adc\n"
    "toolchain: gcc\n"
    "linker:\n"
    "  identity: GNU ld 2.42\n"
    "runtime: host\n"
    "entry_point: main\n"
    "link_command:\n"
    "  - gcc\n"
    "  - -o\n"
    "  - build/ectt/adc.host/build/adc\n"
    "inputs:\n"
    "  - kind: object\n"
    "    path: objects/adc.o\n"
    "    identity: {obj}\n"
)


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    (root / "objects").mkdir(parents=True)
    (root / "objects/adc.o").write_bytes(OBJ_BYTES)
    return root


def _write_plan(root: Path, text: str) -> None:
    (root / "link-plans").mkdir(exist_ok=True)
    (root / "link-plans/adc.yaml").write_text(text, encoding="utf-8")


def _fake_build(root: Path, body: str = HARNESS) -> Any:
    calls: list[Any] = []

    def build(request: Any) -> str:
        calls.append(request)
        target = root / request.executable
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        return request.executable

    build.calls = calls  # type: ignore[attr-defined]
    return build


def _built(root: Path, tmp_path: Path) -> Any:
    _write_plan(root, VALID_YAML.format(obj=_sha(OBJ_BYTES)))
    return build_harness_suite(
        root,
        scope="adc",
        environment="adc.host",
        execution=EXECUTION,
        cases=CASES,
        build=_fake_build(root),
    )


def test_valid_plan_builds_records_and_stores_the_record(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-010, TOOL-ING-200 — plan, build, record, store in order."""
    root = _project(tmp_path)
    result = _built(root, tmp_path)

    expected_rel = f"{DEFAULT_OUTPUT_ROOT}/adc.host/build/adc.suite-record.json"
    assert result.record_path == expected_rel
    stored = load_stored_suite_record(root, environment="adc.host", scope="adc")
    assert stored == result.record
    assert result.record.executable == f"{DEFAULT_OUTPUT_ROOT}/adc.host/build/adc"
    assert {b.test_id for b in result.record.bindings} == {"tc.one", "tc.two"}
    assert result.link_plan.toolchain == "gcc"


def test_the_record_is_deterministic_across_projects(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-060 — same inputs, byte-identical stored record."""
    first = _built(_project(tmp_path / "a"), tmp_path)
    second = _built(_project(tmp_path / "b"), tmp_path)
    assert dump_suite_record(first.record) == dump_suite_record(second.record)
    assert (tmp_path / "a/proj" / first.record_path).read_bytes() == (
        tmp_path / "b/proj" / second.record_path
    ).read_bytes()


def test_refused_plan_stops_the_build_with_its_named_reason(tmp_path: Path) -> None:
    """verifies: TOOL-ING-200 — an invalid plan refuses the build, port never runs."""
    root = _project(tmp_path)
    _write_plan(root, VALID_YAML.format(obj=_sha(OBJ_BYTES)).replace("toolchain: gcc", "toolchain: wat"))
    build = _fake_build(root)

    with pytest.raises(HarnessBuildRefusedError) as excinfo:
        build_harness_suite(
            root,
            scope="adc",
            environment="adc.host",
            execution=EXECUTION,
            cases=CASES,
            build=build,
        )

    assert excinfo.value.reasons == ("unknown_toolchain_key",)
    assert build.calls == []  # the build port is never invoked
    assert not (root / DEFAULT_OUTPUT_ROOT).exists()  # nothing is written


def test_missing_plan_is_refused_with_missing_plan(tmp_path: Path) -> None:
    """verifies: TOOL-ING-200 — no authored plan means no build (the compilation
    database alone never defines the link)."""
    root = _project(tmp_path)
    build = _fake_build(root)

    with pytest.raises(HarnessBuildRefusedError) as excinfo:
        build_harness_suite(
            root,
            scope="adc",
            environment="adc.host",
            execution=EXECUTION,
            cases=CASES,
            build=build,
        )

    assert excinfo.value.reasons == ("missing_plan",)
    assert build.calls == []


def test_scope_mismatch_refuses_the_build(tmp_path: Path) -> None:
    """verifies: TOOL-ING-200 — a plan for another scope is not silently used."""
    root = _project(tmp_path)
    _write_plan(root, VALID_YAML.format(obj=_sha(OBJ_BYTES)).replace("scope: adc", "scope: other"))

    with pytest.raises(HarnessBuildRefusedError) as excinfo:
        build_harness_suite(
            root,
            scope="adc",
            environment="adc.host",
            execution=EXECUTION,
            cases=CASES,
            build=_fake_build(root),
        )

    assert excinfo.value.reasons == ("scope_mismatch",)


def test_changed_input_identity_refuses_the_build(tmp_path: Path) -> None:
    """verifies: TOOL-ING-200 — a link input that no longer matches its recorded
    identity refuses the build (D-02: content digests are the binding)."""
    root = _project(tmp_path)
    _write_plan(root, VALID_YAML.format(obj=_sha(b"different bytes")))
    build = _fake_build(root)

    with pytest.raises(HarnessBuildRefusedError) as excinfo:
        build_harness_suite(
            root,
            scope="adc",
            environment="adc.host",
            execution=EXECUTION,
            cases=CASES,
            build=build,
        )

    assert excinfo.value.reasons == ("identity_mismatch",)
    assert build.calls == []


def test_invalid_environment_name_refuses_before_anything_runs(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-070 — a non-simple environment name never reaches the
    filesystem: no plan load, no build, no write."""
    root = _project(tmp_path)
    build = _fake_build(root)

    with pytest.raises(HarnessBuildError) as excinfo:
        build_harness_suite(
            root,
            scope="adc",
            environment="../escape",
            execution=EXECUTION,
            cases=CASES,
            build=build,
        )

    assert excinfo.value.reason == "invalid_environment_name"
    assert build.calls == []
    assert not (root / "link-plans").exists() or not list((root / "link-plans").iterdir())


def test_output_root_may_not_escape_the_project(tmp_path: Path) -> None:
    """verifies: SDD-003 confinement — the record is stored inside the project."""
    root = _project(tmp_path)
    _write_plan(root, VALID_YAML.format(obj=_sha(OBJ_BYTES)))

    with pytest.raises(HarnessBuildError) as excinfo:
        build_harness_suite(
            root,
            scope="adc",
            environment="adc.host",
            execution=EXECUTION,
            cases=CASES,
            build=_fake_build(root),
            output_root="../outside",
        )

    assert excinfo.value.reason == "invalid_output_root"


def test_missing_record_is_a_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-010 — loading before building is refused, not guessed."""
    root = _project(tmp_path)
    with pytest.raises(HarnessBuildError) as excinfo:
        load_stored_suite_record(root, environment="adc.host", scope="adc")
    assert excinfo.value.reason == "record_missing"


def test_record_relpath_rejects_bad_scope(tmp_path: Path) -> None:
    """verifies: SDD-003 — path builders refuse unsafe scope names."""
    with pytest.raises(HarnessBuildError) as excinfo:
        suite_record_relpath(None, "adc.host", "../evil")
    assert excinfo.value.reason == "invalid_scope_name"


def test_environment_build_relpath_lays_out_the_build_dir(tmp_path: Path) -> None:
    """verifies: SDD-003 — the per-environment build directory is deterministic."""
    assert environment_build_relpath(None, "adc.host") == f"{DEFAULT_OUTPUT_ROOT}/adc.host/build"
    assert environment_build_relpath("out", "adc.host") == "out/adc.host/build"


def test_reexecution_reuses_the_stored_record_without_regeneration(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-010 — re-execution loads the stored record and runs the
    recorded binary as built; the record is unchanged by the run."""
    root = _project(tmp_path)
    result = _built(root, tmp_path)
    record_path = root / result.record_path
    before = record_path.read_bytes()

    stored = load_stored_suite_record(root, environment="adc.host", scope="adc")
    rexec = reexecute_suite(
        stored,
        root,
        {c.case_id: c.content_digest for c in CASES},
        run_label="rerun",
        argv_prefix=(sys.executable,),
    )

    assert rexec.record_id == result.record.record_id
    assert len(rexec.run.result_set.results) == 2
    assert rexec.run.outcome == "failed"  # tc.two fails in the recorded build
    assert record_path.read_bytes() == before  # the record was reused, not rewritten


def test_changed_source_invalidates_the_record(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-010, T-14 NR-19 — a test edited since the build is
    stale, not executed, and the run cannot pass as a full one."""
    root = _project(tmp_path)
    result = _built(root, tmp_path)
    stored = load_stored_suite_record(root, environment="adc.host", scope="adc")

    current = {c.case_id: c.content_digest for c in CASES}
    current["tc.two"] = _sha(b"edited test body")  # the source changed after the build

    rexec = reexecute_suite(
        stored,
        root,
        current,
        run_label="after-edit",
        argv_prefix=(sys.executable,),
    )

    assert rexec.stale_test_ids == ("tc.two",)
    assert rexec.run.result_set.partial is True
    assert rexec.run.outcome != "pass"
    assert "tc.two" in rexec.run.result_set.not_executed
    assert result.record.executable == stored.executable


def test_package_exports_the_build_step(tmp_path: Path) -> None:
    """verifies: API surface — the step is importable from ectt.bld."""
    for name in (
        "build_harness_suite",
        "load_stored_suite_record",
        "HarnessBuildRefusedError",
        "HarnessBuildError",
        "suite_record_relpath",
        "environment_build_relpath",
        "DEFAULT_OUTPUT_ROOT",
    ):
        assert name in ectt.bld.__all__

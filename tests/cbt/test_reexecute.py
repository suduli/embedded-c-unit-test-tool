# implements: TOOL-CBT-010
"""Suite re-execution without regeneration (WP-CBT-01).

Verifies: TOOL-CBT-010 (equivalence partitioning over suite states), with the
T-14 run-integrity acceptance (NR-17/18/19) reached through ``ectt.exh``.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import ectt.cbt
from ectt.cbt import (
    CbtError,
    bindings_from_cases,
    current_digests,
    dump_suite_record,
    load_suite_record,
    record_compiled_suite,
    reexecute_suite,
)
from ectt.exh import runner as exh_runner
from ectt.exh.results import ExecutionMetadata
from ectt.tcm import datacases as dd

HARNESS = """\
import sys
print("banner noise")
print("RESULT tc.one pass")
print("RESULT tc.two fail")
print("FAILURE tc.two expected_return 1 0 src/a.c 9")
sys.exit(0)
"""

EXECUTION = ExecutionMetadata(where="host", toolchain="gcc-14.2")


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


def _suite(tmp_path: Path, body: str = HARNESS) -> tuple[Path, Any]:
    root = tmp_path / "proj"
    (root / "build").mkdir(parents=True)
    (root / "build" / "harness.py").write_text(body, encoding="utf-8", newline="\n")
    record = record_compiled_suite(root, "build/harness.py", EXECUTION, bindings_from_cases(CASES))
    return root, record


def _rerun(root: Path, record: Any, *, current: dict[str, str] | None = None, label: str = "rerun-1") -> Any:
    return reexecute_suite(
        record,
        root,
        current if current is not None else current_digests(CASES),
        run_label=label,
        argv_prefix=(sys.executable,),
    )


# --- re-execution as recorded ------------------------------------------------------------


def test_recorded_suite_reexecutes_with_real_results(tmp_path: Path) -> None:
    root, record = _suite(tmp_path)

    rerun = _rerun(root, record)

    assert rerun.run.outcome == "failed"
    assert {r.test_id: r.outcome for r in rerun.run.result_set.results} == {"tc.one": "pass", "tc.two": "fail"}
    assert rerun.regenerated is False
    assert rerun.stale_test_ids == ()
    assert rerun.run.result_set.partial is False


def test_reexecution_needs_only_the_record_root_and_current_digests(tmp_path: Path) -> None:
    """No manual reconfiguration: toolchain, location and bindings come from the record."""
    root, record = _suite(tmp_path)
    reloaded = load_suite_record(dump_suite_record(record))

    rerun = _rerun(root, reloaded)

    assert rerun.run.result_set.execution == EXECUTION
    assert rerun.run.attempt.allocations == tuple(bindings_from_cases(CASES))


def test_each_reexecution_is_a_distinct_run_and_leaves_the_record_unchanged(tmp_path: Path) -> None:
    root, record = _suite(tmp_path)
    before = dump_suite_record(record)

    first = _rerun(root, record, label="rerun-1")
    second = _rerun(root, record, label="rerun-2")
    again = _rerun(root, record, label="rerun-1")

    assert first.run.result_set.run_id != second.run.result_set.run_id
    assert first.run.result_set.run_id == again.run.result_set.run_id
    assert dump_suite_record(record) == before


def test_the_process_exit_status_is_never_the_verdict(tmp_path: Path) -> None:
    """NR-18: the stub exits 0 although a test failed, and exits 1 although all passed."""
    all_pass_exit_1 = "import sys\nprint('RESULT tc.one pass')\nprint('RESULT tc.two pass')\nsys.exit(1)\n"
    root, record = _suite(tmp_path, all_pass_exit_1)
    assert _rerun(root, record).run.outcome == "pass"

    root2, record2 = _suite(tmp_path / "second")
    assert _rerun(root2, record2).run.outcome == "failed"


def test_only_the_recorded_executable_is_launched_and_nothing_is_built(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No regeneration: exactly one process starts, and it is the harness."""
    root, record = _suite(tmp_path)
    launched: list[list[str]] = []
    real_run = subprocess.run

    def spy(command: Any, *args: Any, **kwargs: Any) -> Any:
        launched.append([str(part) for part in command])
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)

    _rerun(root, record)

    assert len(launched) == 1
    assert launched[0][0] == sys.executable
    assert Path(launched[0][1]).name == "harness.py"


def test_the_cbt_package_never_imports_the_generator_or_the_build_driver() -> None:
    forbidden = {"ectt.gen", "ectt.bld", "ectt.tch"}
    package_dir = Path(ectt.cbt.__file__).parent
    imported: set[str] = set()
    for source in package_dir.glob("*.py"):
        for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
    assert not {m for m in imported if any(m == f or m.startswith(f + ".") for f in forbidden)}


# --- run integrity (T-14 NR-19) ----------------------------------------------------------


def test_a_test_edited_since_the_build_is_not_executed_and_makes_the_run_partial(tmp_path: Path) -> None:
    root, record = _suite(tmp_path)
    edited = {**current_digests(CASES), "tc.two": _case("tc.two", expected="2").content_digest}

    rerun = _rerun(root, record, current=edited)

    assert rerun.stale_test_ids == ("tc.two",)
    assert [r.test_id for r in rerun.run.result_set.results] == ["tc.one"]
    assert rerun.run.result_set.partial is True
    assert rerun.run.result_set.not_executed == ("tc.two",)
    assert rerun.run.outcome != "pass"


def test_a_test_removed_since_the_build_is_stale_not_silently_passing(tmp_path: Path) -> None:
    root, record = _suite(tmp_path)
    remaining = {"tc.one": current_digests(CASES)["tc.one"]}

    rerun = _rerun(root, record, current=remaining)

    assert rerun.stale_test_ids == ("tc.two",)
    assert rerun.run.result_set.partial is True


# --- binary integrity and refusals ---------------------------------------------------------


def test_a_rebuilt_executable_is_refused(tmp_path: Path) -> None:
    root, record = _suite(tmp_path)
    (root / "build" / "harness.py").write_text(HARNESS + "# rebuilt\n", encoding="utf-8", newline="\n")

    with pytest.raises(CbtError) as excinfo:
        _rerun(root, record)
    assert excinfo.value.reason == "executable_changed"


def test_a_missing_executable_asks_for_a_rebuild_instead_of_regenerating(tmp_path: Path) -> None:
    root, record = _suite(tmp_path)
    (root / "build" / "harness.py").unlink()

    with pytest.raises(CbtError) as excinfo:
        _rerun(root, record)
    assert excinfo.value.reason == "executable_missing"
    assert "rebuilt" in excinfo.value.message
    assert not (root / "build" / "harness.py").exists()


@pytest.mark.parametrize("path", ["../outside.py", "/abs/harness.py", "C:/harness.py", "a/../../b.py"])
def test_executable_paths_may_not_leave_the_project(tmp_path: Path, path: str) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    with pytest.raises(CbtError) as excinfo:
        record_compiled_suite(root, path, EXECUTION, bindings_from_cases(CASES))
    assert excinfo.value.reason == "path_escape"


def test_recording_refuses_a_missing_executable_and_empty_bindings(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    (root / "build").mkdir(parents=True)
    with pytest.raises(CbtError) as missing:
        record_compiled_suite(root, "build/none.py", EXECUTION, bindings_from_cases(CASES))
    assert missing.value.reason == "executable_missing"

    (root / "build" / "h.py").write_text("pass\n", encoding="utf-8")
    with pytest.raises(CbtError) as none:
        record_compiled_suite(root, "build/h.py", EXECUTION, [])
    assert none.value.reason == "no_bindings"


def test_recording_validates_bindings_with_the_runners_rules(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    (root / "build").mkdir(parents=True)
    (root / "build" / "h.py").write_text("pass\n", encoding="utf-8")
    with pytest.raises(Exception, match="allocated more than once"):
        record_compiled_suite(root, "build/h.py", EXECUTION, [exh_runner.TestBinding("t", "d" * 64), exh_runner.TestBinding("t", "e" * 64)])


@pytest.mark.parametrize("label", ["", " ", "has space"])
def test_run_labels_must_be_single_tokens(tmp_path: Path, label: str) -> None:
    root, record = _suite(tmp_path)
    with pytest.raises(CbtError) as excinfo:
        _rerun(root, record, label=label)
    assert excinfo.value.reason == "invalid_run_label"


# --- the record ----------------------------------------------------------------------------


def test_record_roundtrips_and_is_deterministic(tmp_path: Path) -> None:
    _, record = _suite(tmp_path)
    text = dump_suite_record(record)
    assert load_suite_record(text) == record
    assert text == dump_suite_record(record)
    assert "\\" not in record.executable


def test_record_binds_the_binary_the_bindings_and_the_toolchain(tmp_path: Path) -> None:
    root, record = _suite(tmp_path)
    other = record_compiled_suite(root, "build/harness.py", ExecutionMetadata(where="host", toolchain="clang-18"), bindings_from_cases(CASES))
    fewer = record_compiled_suite(root, "build/harness.py", EXECUTION, bindings_from_cases(CASES[:1]))
    assert len({record.record_id, other.record_id, fewer.record_id}) == 3


def test_target_and_order_seed_are_part_of_the_record(tmp_path: Path) -> None:
    root, _ = _suite(tmp_path)
    execution = ExecutionMetadata(where="rig", toolchain="arm-gcc", target_id="tgt-1", order_seed=7)
    record = record_compiled_suite(root, "build/harness.py", execution, bindings_from_cases(CASES))
    reloaded = load_suite_record(dump_suite_record(record))
    assert reloaded.execution() == execution


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda d: d.update(record_version="2"), "unsupported_record_version"),
        (lambda d: d.pop("executable"), "invalid_record"),
        (lambda d: d.update(bindings="no"), "invalid_record"),
        (lambda d: d["bindings"].append({"test_id": "x"}), "invalid_record"),
        (lambda d: d.update(order_seed="seven"), "invalid_record"),
        (lambda d: d.update(toolchain="tampered"), "digest_mismatch"),
        (lambda d: d["bindings"][0].update(artifact_digest="0" * 64), "digest_mismatch"),
    ],
)
def test_loader_refuses_tampered_or_malformed_records(tmp_path: Path, mutate: Any, reason: str) -> None:
    import json

    _, record = _suite(tmp_path)
    doc = json.loads(dump_suite_record(record))
    mutate(doc)
    with pytest.raises(CbtError) as excinfo:
        load_suite_record(json.dumps(doc))
    assert excinfo.value.reason == reason


def test_loader_refuses_non_json_and_non_objects() -> None:
    for text in ("{nope", "[]"):
        with pytest.raises(CbtError):
            load_suite_record(text)


def test_reexecuting_a_tampered_in_memory_record_is_refused(tmp_path: Path) -> None:
    from dataclasses import replace

    root, record = _suite(tmp_path)
    forged = replace(record, toolchain="clang-99")
    with pytest.raises(CbtError) as excinfo:
        _rerun(root, forged)
    assert excinfo.value.reason == "digest_mismatch"


def test_bindings_follow_case_content(tmp_path: Path) -> None:
    changed = [_case("tc.one"), _case("tc.two", expected="9")]
    assert bindings_from_cases(CASES) != bindings_from_cases(changed)
    assert current_digests(changed)["tc.two"] == changed[1].content_digest

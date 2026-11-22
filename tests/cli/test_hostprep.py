# implements: TOOL-TGT-130
"""The host run preparation in the CLI (A5): parity gate first, labelled results.

The parity gate runs before anything else — a refusal names its reasons and
nothing executes. Every result of a gated run carries its profile label, and
the view shows the profile's ABI differences with unmeasured dimensions as
``unknown``. Hardware is not available, so the target plan is a declaration
and the host execution uses an interpreter-hosted fake harness.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace as dc_replace
from pathlib import Path

import pytest

from ectt.cbt import bindings_from_cases, dump_suite_record, record_compiled_suite
from ectt.cli.commands import run_cbt_commands
from ectt.cli.exit_codes import EXIT_TEST_FAILURE, EXIT_TOOL_ERROR
from ectt.cli.hostprep import prepare_and_run_host_suite, profile_abi_map
from ectt.exh.results import ExecutionMetadata
from ectt.ext.errors import ExtError
from ectt.ext.parity import ExecutionConfig, ExecutionPlan
from ectt.ext.profile import UNKNOWN_ABI, dump_host_profile, record_host_profile
from ectt.tcm import datacases as dd

EXECUTION = ExecutionMetadata(where="host", toolchain="gcc-14.2")

HARNESS = (
    "import sys\n"
    "args = sys.argv[1:]\n"
    "tid = args[args.index('--ectt-select') + 1] if '--ectt-select' in args else None\n"
    "for name in ('tc.a', 'tc.b'):\n"
    "    if tid == name or tid is None:\n"
    "        print(f'RESULT {name} pass')\n"
)

PROFILE_ARGS = {
    "name": "linux-x86-proxy",
    "target_triple": "arm-none-eabi",
    "host_triple": "x86_64-linux-gnu",
    "unavailable_hardware_behavior": "the access is diagnosed and the test fails",
    "abi": {"width": "int: 32 both"},
}


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


CASES = [_case("tc.a"), _case("tc.b")]
CURRENT = {c.case_id: c.content_digest for c in CASES}


def _plans(generated: str = "GEN") -> tuple[dict, dict]:
    digests = {c.case_id: c.content_digest for c in CASES}

    def plan(kind: str, toolchain: str, transport: str, target_id: str | None) -> dict:
        config: dict = {
            "kind": kind,
            "toolchain": toolchain,
            "runner": "direct" if kind == "host" else "qemu",
            "transport": transport,
        }
        if target_id is not None:
            config["target_id"] = target_id
        return {"case_digests": digests, "generated_code_digest": generated, "config": config}

    return plan("host", "gcc-14.2", "stdout", None), plan("target", "arm-none-eabi-gcc", "semihosting", "qemu-virt")


def _profile_file(tmp_path: Path) -> Path:
    profile = record_host_profile(**PROFILE_ARGS)  # type: ignore[arg-type]
    file = tmp_path / "profile.json"
    file.write_text(dump_host_profile(profile), encoding="utf-8")
    return file


def _recorded(tmp_path: Path, body: str = HARNESS) -> tuple[Path, Path]:
    root = tmp_path / "proj"
    (root / "build").mkdir(parents=True)
    (root / "build" / "harness").write_text(body, encoding="utf-8")
    record = record_compiled_suite(root, "build/harness", EXECUTION, bindings_from_cases(CASES))
    record_file = tmp_path / "suite-record.json"
    record_file.write_text(dump_suite_record(record), encoding="utf-8")
    return root, record_file


def _run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = run_cbt_commands(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _argv(tmp_path: Path, root: Path, record_file: Path) -> list[str]:
    host_plan, target_plan = _plans()
    return [
        "host-run",
        "--profile", str(_profile_file(tmp_path)),
        "--host-plan", json.dumps(host_plan),
        "--target-plan", json.dumps(target_plan),
        "--record", str(record_file),
        "--root", str(root),
        "--current", json.dumps(CURRENT),
        "--run-label", "hostprep",
        "--argv-prefix", json.dumps([sys.executable]),
    ]


def test_every_result_of_a_gated_run_carries_its_profile_label(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """verifies: TOOL-TGT-130 — the gate passes, the suite runs, and the view
    labels every result with the profile id and label."""
    root, record_file = _recorded(tmp_path)
    code, out, _ = _run(_argv(tmp_path, root, record_file), capsys)
    assert code == 0
    document = json.loads(out)
    assert document["outcome"] == "pass"
    assert len(document["results"]) == 2
    assert all(r["profile_id"] and r["profile_label"] for r in document["results"])
    assert all(r["outcome"] == "pass" for r in document["results"])


def test_unknown_abi_differences_show_as_unknown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """verifies: TOOL-TGT-130 — an unmeasured ABI dimension is reported as the
    explicit unknown marker, never as 'same'."""
    profile = record_host_profile(**PROFILE_ARGS)  # type: ignore[arg-type]
    abi = profile_abi_map(profile)
    assert abi["width"] == "int: 32 both"
    assert abi["alignment"] == UNKNOWN_ABI
    assert abi["endianness"] == UNKNOWN_ABI
    assert abi["packing"] == UNKNOWN_ABI and abi["signedness"] == UNKNOWN_ABI

    root, record_file = _recorded(tmp_path)
    code, out, _ = _run(_argv(tmp_path, root, record_file), capsys)
    assert code == 0
    document = json.loads(out)
    assert document["abi"]["width"] == "int: 32 both"
    assert document["abi"]["alignment"] == UNKNOWN_ABI


def test_a_parity_failure_blocks_the_run_with_its_named_reason(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """verifies: TOOL-TGT-130 — a diverging case refuses the preparation with
    the named reason; nothing executes."""
    root, record_file = _recorded(tmp_path)
    _host_plan, target_plan = _plans()
    diverging = {**target_plan, "case_digests": {**target_plan["case_digests"], "tc.b": "f" * 64}}
    argv = _argv(tmp_path, root, record_file)
    argv[argv.index("--target-plan") + 1] = json.dumps(diverging)
    code, _, err = _run(argv, capsys)
    assert code == EXIT_TOOL_ERROR
    assert "case_content_differs" in err


def test_a_refused_preparation_never_starts_a_process(tmp_path: Path) -> None:
    """verifies: TOOL-TGT-130 — the gate runs before anything else: a tampered
    governing profile refuses the run and no harness process is started."""
    marker = tmp_path / "marker.txt"
    root, _record_file = _recorded(
        tmp_path, body=HARNESS + f"open(r'{marker}', 'w').write('ran')\n"
    )
    record = record_compiled_suite(root, "build/harness", EXECUTION, bindings_from_cases(CASES))
    # A profile edited after recording: its id no longer binds its content.
    profile = record_host_profile(**PROFILE_ARGS)  # type: ignore[arg-type]
    tampered = dc_replace(profile, name="edited")

    with pytest.raises(ExtError) as excinfo:
        prepare_and_run_host_suite(
            profile=tampered,
            host_plan=ExecutionPlan(
                case_digests={c.case_id: c.content_digest for c in CASES},
                generated_code_digest="GEN",
                config=ExecutionConfig("host", "gcc-14.2", "direct", "stdout"),
            ),
            target_plan=ExecutionPlan(
                case_digests={c.case_id: c.content_digest for c in CASES},
                generated_code_digest="GEN",
                config=ExecutionConfig(
                    "target", "arm-none-eabi-gcc", "qemu", "semihosting", target_id="qemu-virt"
                ),
            ),
            record=record,
            root=root,
            current=CURRENT,
            run_label="hostprep",
            argv_prefix=(sys.executable,),
        )
    assert excinfo.value.reason == "digest_mismatch"
    assert not marker.exists()  # nothing ran


def test_a_failed_suite_exits_test_failure_with_labels(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """verifies: stable exit codes — a failing suite is EXIT_TEST_FAILURE with
    the label still on every result."""
    failing = (
        "import sys\n"
        "args = sys.argv[1:]\n"
        "tid = args[args.index('--ectt-select') + 1] if '--ectt-select' in args else None\n"
        "for name in ('tc.a', 'tc.b'):\n"
        "    if tid == name or tid is None:\n"
        "        print(f'RESULT {name} ' + ('fail' if name == 'tc.b' else 'pass'))\n"
        "        if name == 'tc.b':\n"
        "            print(f'FAILURE {name} e 1 0 a.c 9')\n"
    )
    root, record_file = _recorded(tmp_path, body=failing)
    argv = _argv(tmp_path, root, record_file)
    code, out, _ = _run(argv, capsys)
    assert code == EXIT_TEST_FAILURE
    document = json.loads(out)
    assert document["outcome"] == "failed"
    assert all(r["profile_id"] for r in document["results"])

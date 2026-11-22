"""Mutation-style test runner for lane A item A6 (tests-only; no src/ edits land).

Hand-written mutants (flip a comparison, drop a branch, drop a statement, swap
an ordering) are applied to a TEMP COPY of ``src/`` (never to the tree), the
package test suites run against the copy (the editable install is ``.pth``-based,
so a ``PYTHONPATH`` shadow ``src`` takes precedence), and a mutant is KILLED when
any test fails or errors. Survivors are listed for follow-up tests.

Usage:
    python docs/glm-night/overnight-20261121/mutation_runner.py [--only id[,id...]]

Output: a JSON report on stdout and a human summary; the lane's
mutation-gen-cbt-exh.md is written from it.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PY = REPO / ".venv" / "Scripts" / "python.exe"
TEST_DIRS = ["tests/gen", "tests/cbt", "tests/exh"]

# (id, module relative to src, operator, find, replace)
MUTANTS: list[tuple[str, str, str, str, str]] = [
    # --- ectt.gen ---
    ("GEN-PROTO-1", "ectt/gen/protocol.py", "flip comparison",
     'ectt_report_result(ectt_current_test, ectt_current_failures > 0 ? "fail" : "pass");',
     'ectt_report_result(ectt_current_test, ectt_current_failures == 0 ? "fail" : "pass");'),
    ("GEN-PROTO-2", "ectt/gen/protocol.py", "drop statement (state reset)",
     """void ectt_end_test(void) {
    if (ectt_current_test != 0) {
        ectt_report_result(ectt_current_test, ectt_current_failures > 0 ? "fail" : "pass");
        ectt_current_test = 0;
        ectt_current_failures = 0;
    }
}""",
     """void ectt_end_test(void) {
    if (ectt_current_test != 0) {
        ectt_report_result(ectt_current_test, ectt_current_failures > 0 ? "fail" : "pass");
        ectt_current_failures = 0;
    }
}"""),
    ("GEN-PROTO-3", "ectt/gen/protocol.py", "boundary constant",
     "ectt_write_unsigned(line == 0 ? 1ul : (unsigned long)line);",
     "ectt_write_unsigned(line == 0 ? 0ul : (unsigned long)line);"),
    ("GEN-TESTBODY-1", "ectt/gen/testbody.py", "invert guard",
     "if (!({expression})) {{", "if ({expression}) {{"),
    ("GEN-TESTBODY-2", "ectt/gen/testbody.py", "drop branch (collision guard)",
     """        name = "ectt_case_" + re.sub(r"[^A-Za-z0-9_]", "_", render.case_id)
        if name in taken:""",
     """        name = "ectt_case_" + re.sub(r"[^A-Za-z0-9_]", "_", render.case_id)
        if False and name in taken:"""),
    ("GEN-TESTBODY-3", "ectt/gen/testbody.py", "weaken pattern",
     '_CALL_COUNT_RE = re.compile(r"^ectt_stub_(\\w+)_call_count\\(\\) == (\\d+)u$")',
     '_CALL_COUNT_RE = re.compile(r"^ectt_stub_(\\w+)_call_count\\(\\) == (\\d+)$")'),
    ("GEN-STUBCTL-1", "ectt/gen/stubctl.py", "flip comparison",
     'if len(spec.returns) != 1:', 'if len(spec.returns) != 2:'),
    ("GEN-STUBCTL-2", "ectt/gen/stubctl.py", "drop branch (validation)",
     "if not spec.expect_calls.isdigit():", "if False:"),
    ("GEN-HARNESS-1", "ectt/gen/harness.py", "flip comparison",
     'if accesses == {"r"}:', 'if accesses != {"r"}:'),
    # --- ectt.cbt ---
    ("CBT-REEXEC-1", "ectt/cbt/reexecute.py", "drop branch (binary integrity)",
     "if _file_digest(exe) != record.executable_digest:", "if False:"),
    ("CBT-REEXEC-2", "ectt/cbt/reexecute.py", "drop branch (confinement)",
     "    if not resolved.is_relative_to(root.resolve()):",
     "    if False and not resolved.is_relative_to(root.resolve()):"),
    ("CBT-REEXEC-3", "ectt/cbt/reexecute.py", "swap ordering key",
     "ordered = tuple(sorted(bindings, key=lambda b: b.test_id))",
     "ordered = tuple(sorted(bindings, key=lambda b: b.artifact_digest))"),
    ("CBT-REEXEC-4", "ectt/cbt/reexecute.py", "drop clause (label rule)",
     "if not isinstance(run_label, str) or not run_label.strip() or any(c.isspace() for c in run_label):",
     "if not isinstance(run_label, str) or not run_label.strip():"),
    # --- ectt.exh ---
    ("EXH-RUNNER-1", "ectt/exh/runner.py", "drop branch (NR-19 stale gate)",
     "    accepted = tuple(record for record in records if record.test_id not in stale_ids)",
     "    accepted = records"),
    ("EXH-RUNNER-2", "ectt/exh/runner.py", "flip comparison (parallel aggregation)",
     'if any(outcome == "failed" for outcome in outcomes):',
     'if any(outcome == "pass" for outcome in outcomes):'),
    ("EXH-RUNNER-3", "ectt/exh/runner.py", "swap attribution constant",
     'finalize_result(test_id, "timeout", digests_by_test[test_id])',
     'finalize_result(test_id, "error", digests_by_test[test_id])'),
    ("EXH-RUNNER-4", "ectt/exh/runner.py", "flip comparison (exit contract)",
     'return 0 if run.outcome == "pass" else 1',
     'return 0 if run.outcome == "failed" else 1'),
    ("EXH-RUNNER-5", "ectt/exh/runner.py", "drop branch (duplicate allocation)",
     "        if binding.test_id in seen:", "        if False:"),
    ("EXH-RESULTS-1", "ectt/exh/results.py", "drop branch (NR-18 guard)",
     'if outcome == "pass" and failure_tuple:', "if False:"),
    ("EXH-RESULTS-2", "ectt/exh/results.py", "drop member from failure set",
     'if any(record.outcome in ("fail", "error", "timeout") for record in executed):',
     'if any(record.outcome in ("fail", "error") for record in executed):'),
]


def _apply(src_copy: Path, module: str, find: str, replace: str) -> bool:
    target = src_copy / module
    text = target.read_text(encoding="utf-8")
    count = text.count(find)
    if count != 1:
        return False
    target.write_text(text.replace(find, replace, 1), encoding="utf-8", newline="")
    return True


def _run_tests(pythonpath: str) -> tuple[int, str]:
    import os

    env = dict(os.environ)
    env["PYTHONPATH"] = pythonpath
    # pyproject sets pytest's pythonpath = ["src", "tools"], which pytest
    # inserts ahead of PYTHONPATH; override it so the shadow copy wins.
    # The ini list splits on os.pathsep (";" on Windows).
    override = os.pathsep.join([pythonpath, "tools"])
    proc = subprocess.run(
        [str(PY), "-m", "pytest", "-q", "-p", "no:cacheprovider", "--no-header", "-x", "-o", f"pythonpath={override}", *TEST_DIRS],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=300,
    )
    return proc.returncode, (proc.stdout + proc.stderr)[-4000:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    only = {item.strip() for item in args.only.split(",") if item.strip()}

    # Baseline: the tests must pass on the unmutated tree.
    code, tail = _run_tests(str(REPO / "src"))
    if code != 0:
        print("BASELINE RED - aborting; the suite must be green before mutating.")
        print(tail)
        return 2

    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="ectt-mutation-") as tmp:
        base_src = Path(tmp) / "src"
        for mutant_id, module, operator, find, replace in MUTANTS:
            if only and mutant_id not in only:
                continue
            shutil.copytree(REPO / "src", base_src, dirs_exist_ok=True)
            if not _apply(base_src, module, find, replace):
                results.append({"id": mutant_id, "state": "BAD-MUTANT", "module": module, "operator": operator})
                continue
            code, tail = _run_tests(str(base_src))
            first_failure = ""
            for line in tail.splitlines():
                if line.startswith("FAILED ") or line.startswith("ERROR "):
                    first_failure = line.strip()
                    break
            results.append(
                {
                    "id": mutant_id,
                    "state": "KILLED" if code != 0 else "SURVIVED",
                    "module": module,
                    "operator": operator,
                    "evidence": first_failure or f"exit={code}",
                }
            )

    killed = sum(1 for r in results if r["state"] == "KILLED")
    survived = [r for r in results if r["state"] == "SURVIVED"]
    scored = [r for r in results if r["state"] in ("KILLED", "SURVIVED")]
    print(json.dumps(results, indent=1))
    print(f"\nKILL RATE: {killed}/{len(scored)} = {killed / len(scored) if scored else 0:.0%}")
    for survivor in survived:
        print(f"SURVIVOR: {survivor['id']} ({survivor['module']}, {survivor['operator']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Mutation-style test runner for lane A item A6 (tests-only; no src/ edits land).

Hand-written mutants (flip a comparison, drop a branch, swap an ordering) are
applied to a TEMP COPY of ``src/`` (never to the tree), the cli/atg/ext test
suites run against the copy, and a mutant is KILLED when any test fails or
errors. pyproject's pytest ``pythonpath = ["src", "tools"]`` is overridden so
the shadow copy wins.

Usage:
    python docs/glm-night/overnight-20261122/mutation_runner.py [--only id[,id...]]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PY = REPO / ".venv" / "Scripts" / "python.exe"
TEST_DIRS = ["tests/cli", "tests/atg", "tests/ext"]

# (id, module relative to src, operator, find, replace)
MUTANTS: list[tuple[str, str, str, str, str]] = [
    # --- ectt.cli ---
    ("CLI-COMPOSE-1", "ectt/cli/compose.py", "flip state mapping",
     'if run.outcome in ("pass", "failed"):\n        return ExecutionOutcome(state="completed", detail=run.outcome)',
     'if run.outcome in ("pass", "failed"):\n        return ExecutionOutcome(state="harness_error", detail=run.outcome)'),
    ("CLI-COMPOSE-2", "ectt/cli/compose.py", "drop branch (build gate)",
     "        except (HarnessBuildError, CbtError) as exc:",
     "        except CbtError as exc:"),
    ("CLI-COMPOSE-3", "ectt/cli/compose.py", "drop statement (record keeping)",
     "        records[candidate.candidate_id] = result.record",
     "        pass"),
    ("CLI-CMDS-1", "ectt/cli/commands.py", "flip exit contract",
     '    return 0 if subset.reexecution.run.outcome == "pass" else EXIT_TEST_FAILURE',
     '    return 0 if subset.reexecution.run.outcome == "pass" else 0'),
    ("CLI-CMDS-2", "ectt/cli/commands.py", "flip exit contract (host run)",
     '    return 0 if outcome.reexecution.run.outcome == "pass" else EXIT_TEST_FAILURE',
     '    return 0 if outcome.reexecution.run.outcome == "pass" else 0'),
    ("CLI-CMDS-3", "ectt/cli/commands.py", "drop branch (JSON safety)",
     "    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:",
     "    except (OSError,) as exc:"),
    ("CLI-HOSTPREP-1", "ectt/cli/hostprep.py", "drop statement (labelling)",
     "    labelled = label_host_results(profile, rexec.run.result_set)",
     "    labelled = rexec.run.result_set"),
    ("CLI-HOSTPREP-2", "ectt/cli/hostprep.py", "swap call order (gate after run)",
     "    preparation = prepare_host_proxy_run(profile, host_plan, target_plan)",
     "    preparation = prepare_host_proxy_run(profile, host_plan, target_plan) if False else None"),
    # --- ectt.atg ---
    ("ATG-BINDING-1", "ectt/atg/binding.py", "flip guard (coverage source)",
     "        if self._coverage_for is None:\n            return None",
     "        if self._coverage_for is not None:\n            return None"),
    ("ATG-BINDING-2", "ectt/atg/binding.py", "flip comparison (newly covered)",
     "        newly = tuple(sorted(c for c in reported if c not in self._covered))",
     "        newly = tuple(sorted(c for c in reported if c in self._covered))"),
    ("ATG-RUN-1", "ectt/atg/run.py", "flip comparison (case limit)",
     "            if bounds.max_cases is not None and len(cases) >= bounds.max_cases:",
     "            if bounds.max_cases is not None and len(cases) > bounds.max_cases:"),
    ("ATG-RUN-2", "ectt/atg/run.py", "flip assignment (measured flag)",
     "    measured = True",
     "    measured = False"),
    # --- ectt.ext ---
    ("EXT-PROFILE-1", "ectt/ext/profile.py", "flip comparison (integrity)",
     "    return bool(profile.profile_id) and _profile_id(profile.body()) == profile.profile_id",
     "    return bool(profile.profile_id) and _profile_id(profile.body()) != profile.profile_id"),
    ("EXT-PROFILE-2", "ectt/ext/profile.py", "flip comparison (abi measured)",
     "    return (value, True) if value is not None else (UNKNOWN_ABI, False)",
     "    return (value, True) if value is not None else (value, False)"),
    ("EXT-PARITY-1", "ectt/ext/parity.py", "flip guard (parity gate)",
     "    if not report.ok:\n        raise ParityGateError(report.violations)",
     "    if report.ok:\n        raise ParityGateError(report.violations)"),
    ("EXT-PARITY-2", "ectt/ext/parity.py", "flip comparison (plan kinds)",
     '    if host.config.kind != "host" or target.config.kind != "target":',
     '    if host.config.kind != "host" and target.config.kind != "target":'),
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
    override = os.pathsep.join([pythonpath, "tools"])
    env = dict(os.environ)
    env["PYTHONPATH"] = pythonpath
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

"""Mutation-style test runner for lane B item B6 (tests-only; no src/ edits land).

Adapted from ``docs/glm-night/overnight-20261122/mutation_runner.py`` (lane A),
as the queue instructs. Hand-written mutants (flip a comparison, drop a branch,
swap an ordering) are applied to a TEMP COPY of ``src/`` (never to the tree),
the trc/mig/prj test suites run against the copy, and a mutant is KILLED when
any test fails or errors. pyproject's pytest ``pythonpath = ["src", "tools"]``
is overridden so the shadow copy wins.

Usage:
    .venv/Scripts/python.exe docs/glm-night/overnight-20261123/mutation_runner_trc_mig_prj.py [--only id[,id...]]
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
TEST_DIRS = ["tests/trc", "tests/mig", "tests/prj"]

# (id, module relative to src, operator, find, replace)
MUTANTS: list[tuple[str, str, str, str, str]] = [
    # --- ectt.trc (B2/B3 lineage: matrix, links, reqif) ---
    ("TRC-VERDICT-1", "ectt/trc/matrix.py", "worst outcome -> best outcome",
     "worst = max(executed, key=lambda link: TEST_SEVERITY[link.status])",
     "worst = min(executed, key=lambda link: TEST_SEVERITY[link.status])"),
    ("TRC-VERDICT-2", "ectt/trc/matrix.py", "unreviewed tests execute into the verdict",
     "executed = [link for link in links if link.status in _EXECUTED and not link.unreviewed]",
     "executed = [link for link in links if link.status in _EXECUTED]"),
    ("TRC-VERDICT-3", "ectt/trc/matrix.py", "unverified -> pass",
     '        return "unverified"  # nothing executed: never inferred from coverage',
     '        return "pass"'),
    ("TRC-LINKS-1", "ectt/trc/source_links.py", "extent boundary off by one",
     "            if end <= candidate.end_line:",
     "            if end <= candidate.end_line + 1:"),
    ("TRC-LINKS-2", "ectt/trc/source_links.py", "span refusal becomes approximate resolution",
     '            return ResolvedSourceLink(link, "unresolved", reason="range_spans_functions")',
     '            return ResolvedSourceLink(link, "resolved", function=candidate.name, approximate=True)'),
    ("TRC-REQIF-1", "ectt/trc/imports.py", "dangling SPEC-OBJECT-REF accepted",
     "            if ref not in real_id_by_xml:",
     "            if False and ref not in real_id_by_xml:"),
    ("TRC-REQIF-2", "ectt/trc/reqif_export.py", "relation SOURCE and TARGET swapped",
     '            _sub(_sub(relation, "SOURCE"), "SPEC-OBJECT-REF", requirement_ids[row.requirement_id])\n            _sub(_sub(relation, "TARGET"), "SPEC-OBJECT-REF", tests[link.test_id][0])',
     '            _sub(_sub(relation, "SOURCE"), "SPEC-OBJECT-REF", tests[link.test_id][0])\n            _sub(_sub(relation, "TARGET"), "SPEC-OBJECT-REF", requirement_ids[row.requirement_id])'),
    # --- ectt.mig (existing-suite normalisation, format registry) ---
    ("MIG-UNITY-1", "ectt/mig/existing_suites.py", "unity PASS -> fail",
     '            records.append(_finalize(name, "pass"))',
     '            records.append(_finalize(name, "fail"))'),
    ("MIG-UNITY-2", "ectt/mig/existing_suites.py", "unity unrecognised lines dropped",
     "        match = _UNITY_LINE.match(line)\n        if match is None:\n            unrecognised.append(line)",
     "        match = _UNITY_LINE.match(line)\n        if match is None:\n            pass"),
    ("MIG-CMOCKA-1", "ectt/mig/existing_suites.py", "unfinished cmocka RUN is a silent pass",
     "    if started is not None:  # the process ended mid-test: never a silent pass",
     "    if False and started is not None:  # the process ended mid-test: never a silent pass"),
    ("MIG-FMT-1", "ectt/mig/formats.py", "version drift check inverted",
     "                if actual != spec.version:",
     "                if actual == spec.version:"),
    # --- ectt.prj (shards, save discipline, threshold config) ---
    ("PRJ-SHARD-1", "ectt/prj/shards.py", "shard name allows a leading dot",
     '_SHARD_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")',
     '_SHARD_NAME = re.compile(r"^[A-Za-z0-9._-]+$")'),
    ("PRJ-SHARD-2", "ectt/prj/shards.py", "diff-stable write inverted",
     "        if previous == content:",
     "        if previous != content:"),
    ("PRJ-SAVE-1", "ectt/prj/project.py", "comment preservation dropped",
     "                if comments and not discard_comments:",
     "                if False and comments and not discard_comments:"),
    ("PRJ-SAVE-2", "ectt/prj/project.py", "byte-identical no-op inverted",
     "                    if f.read() == new_bytes:",
     "                    if f.read() != new_bytes:"),
    ("PRJ-THRESH-1", "ectt/prj/thresholds.py", "float minimum accepted",
     "        if isinstance(minimum, (bool, float)):",
     "        if False and isinstance(minimum, (bool, float)):"),
    ("PRJ-THRESH-2", "ectt/prj/thresholds.py", "unknown metric in the allow list accepted",
     '        if metric not in THRESHOLD_METRICS:\n            raise ProjectError(\n                f"unknown coverage metric \'{metric}\' in allow_not_applicable "',
     '        if False and metric not in THRESHOLD_METRICS:\n            raise ProjectError(\n                f"unknown coverage metric \'{metric}\' in allow_not_applicable "'),
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
    with tempfile.TemporaryDirectory(prefix="ectt-mutation-b-") as tmp:
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
            print(f"{results[-1]['state']:8} {mutant_id}  ({results[-1]['evidence'][:90]})")

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

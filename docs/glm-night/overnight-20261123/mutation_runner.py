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
TEST_DIRS = ["tests/qua", "tests/sec", "tests/exh", "tests/core"]

# (id, module relative to src, operator, find, replace)
MUTANTS: list[tuple[str, str, str, str, str]] = [
    # --- ectt.qua (A1/A2) ---
    ("QUA-VALID-1", "ectt/qua/validation.py", "flip guard (missing tool)",
     "        missing = sorted(set(check.requires) - available)\n        if missing:",
     "        missing = sorted(set(check.requires) - available)\n        if False and missing:"),
    ("QUA-VALID-2", "ectt/qua/validation.py", "flip state (pass -> fail)",
     '                    state=STATE_PASS,',
     '                    state=STATE_FAIL,'),
    ("QUA-VALID-3", "ectt/qua/validation.py", "drop clause (order)",
     "    for check in sorted(checks, key=lambda c: c.check_id):",
     "    for check in list(checks):"),
    ("QUA-ERRORS-1", "ectt/qua/known_errors.py", "flip comparison (fix gate)",
     "        return _version_key(release) < _version_key(self.fixed_in)",
     "        return _version_key(release) <= _version_key(self.fixed_in)"),
    ("QUA-ERRORS-2", "ectt/qua/known_errors.py", "flip guard (duplicate id)",
     "    if error_id in seen:",
     "    if False and error_id in seen:"),
    ("QUA-ERRORS-3", "ectt/qua/known_errors.py", "flip reason (workaround)",
     '                reason="missing_workaround",',
     '                reason="missing_field",'),
    # --- ectt.sec (A3/A4) ---
    ("SEC-SBOM-1", "ectt/sec/sbom.py", "flip guard (unknown licence)",
     '    licences_unknown = tuple(\n        p.name for p in ordered if p.licence is None or not p.licence.strip()\n    )',
     '    licences_unknown = tuple(\n        p.name for p in ordered if p.licence is not None and p.licence.strip()\n    )'),
    ("SEC-SBOM-2", "ectt/sec/sbom.py", "drop sorting",
     "    ordered = sorted(packages, key=lambda p: p.name)",
     "    ordered = list(packages)"),
    ("SEC-SBOM-3", "ectt/sec/sbom.py", "swap marker (signing)",
     '    signing: str = SIGNING_NOT_CONFIGURED',
     '    signing: str = "signed"'),
    ("SEC-PINS-1", "ectt/sec/pins.py", "flip comparison (hash)",
     "        if installed_hash != pin.sha256:",
     "        if installed_hash == pin.sha256:"),
    ("SEC-PINS-2", "ectt/sec/pins.py", "flip guard (unpinned lock entry)",
     '        if pin.sha256 is None:',
     '        if pin.sha256 is not None:'),
    ("SEC-PINS-3", "ectt/sec/pins.py", "drop sorting",
     "    return tuple(sorted(differences, key=lambda d: (d.name, d.kind)))",
     "    return tuple(differences)"),
    # --- ectt.exh (A5/A6) ---
    ("EXH-RESTR-1", "ectt/exh/restricted.py", "flip guard (path escape)",
     "    if not working_resolved.is_relative_to(root_resolved):",
     "    if False and not working_resolved.is_relative_to(root_resolved):"),
    ("EXH-RESTR-2", "ectt/exh/restricted.py", "flip flag (handles)",
     "        inherit_handles=False,",
     "        inherit_handles=True,"),
    ("EXH-RESTR-3", "ectt/exh/restricted.py", "drop statement (truncation)",
     '    truncated = encoded_length > context.output_limit_bytes',
     '    truncated = False'),
    ("EXH-DEBUG-1", "ectt/exh/debugger.py", "flip guard (symbols)",
     "    if not symbols_recorded:",
     "    if False and not symbols_recorded:"),
    ("EXH-DEBUG-2", "ectt/exh/debugger.py", "drop element (breakpoint)",
     '    argv = (debugger.strip(), "-ex", breakpoint, "--args", str(harness_path), *args)',
     '    argv = (debugger.strip(), "--args", str(harness_path), *args)'),
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

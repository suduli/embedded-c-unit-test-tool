# implements: TOOL-MIG-010
"""Execution of existing Unity and cmocka suites (WP-MIG-01).

An existing suite runs through its own ``main``: the executable is invoked
directly (no shell, no network, exit status never consulted — EXH-02
discipline) and its native framework output is normalised into the same
finalized result records the generated-harness path produces
(``finalize_result`` enforces the NR-18 invariants at this boundary too).
No suite source is read, modified, or rewritten: the contract is stdout only.

Normalisation rules, deliberately conservative:

- Unity ``file:line:name:PASS|FAIL|IGNORE`` lines become ``pass`` records,
  ``fail`` records (when the message states ``Expected X Was Y``, those
  values travel; the assertion name is the framework's, not invented), or
  ``not_run`` for ``IGNORE``. A ``FAIL`` line whose message carries no
  detail becomes ``error`` — the NR-18 invariants forbid a ``fail`` record
  without expected/actual, and an under-detailed failure must not be
  upgraded into a claim it cannot support. Aggregation treats ``error`` as
  a failure, so the requirement-level verdict is unaffected.
- cmocka ``[  OKAY    ]``/``[  FAILED  ]`` pairs become ``pass``/``error``
  records (the stream contract carries no expected/actual values); ``RUN``
  and summary lines are context, not records.
- Lines that match neither framework grammar are reported as
  ``unrecognised_lines``; a run that produces no records at all answers
  ``aggregate=None`` with the raw lines reported — never a silent ``pass``.

Satisfies: TOOL-MIG-010.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ectt.exh.results import (
    AssertionFailure,
    ResultRecord,
    SourceLocation,
    aggregate_outcome,
    finalize_result,
)
from ectt.mig.errors import MigError

__all__ = [
    "SUPPORTED_FRAMEWORKS",
    "ExistingSuiteRun",
    "parse_cmocka_output",
    "parse_unity_output",
    "run_existing_suite",
]

SUPPORTED_FRAMEWORKS = ("cmocka", "unity")

_UNITY_LINE = re.compile(
    r"^(?P<file>[^:\s]+):(?P<line>\d+):(?P<name>[^:\s]+):"
    r"(?P<verdict>PASS|FAIL|IGNORE)(?::\s*(?P<message>.*))?$"
)
_UNITY_EXPECTED = re.compile(r"Expected (?P<expected>.*) Was (?P<actual>.*)$")
_CMOCKA_VERDICT = re.compile(r"^\[\s*(?P<verdict>OKAY|OK|FAILED)\s*\]\s*(?P<name>\S+)\s*$")
_CMOCKA_LINE = re.compile(r"^\[\s*LINE\s*\]\s*(?P<file>[^:\s]+):(?P<line>\d+):\s*(?P<message>.*)$")


@dataclass(frozen=True)
class ExistingSuiteRun:
    """One existing-suite execution, normalised into the S3 vocabulary."""

    framework: str
    records: tuple[ResultRecord, ...]
    unrecognised_lines: tuple[str, ...]
    aggregate: str | None  # exh.aggregate_outcome result; None when nothing parsed


def _finalize(
    test_id: str,
    outcome: str,
    *,
    failure: tuple[str, str, str, str, int] | None = None,
) -> ResultRecord:
    if failure is not None:
        assertion, expected, actual, file, line = failure
        return finalize_result(
            test_id,
            outcome,
            f"existing-suite:{test_id}",
            failures=(
                AssertionFailure(
                    assertion=assertion,
                    expected=expected,
                    actual=actual,
                    location=SourceLocation(file=file, line=line),
                ),
            ),
        )
    return finalize_result(test_id, outcome, f"existing-suite:{test_id}")


def parse_unity_output(text: str) -> tuple[tuple[ResultRecord, ...], tuple[str, ...]]:
    """Normalise Unity output into finalized records plus unrecognised lines."""
    records: list[ResultRecord] = []
    unrecognised: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        match = _UNITY_LINE.match(line)
        if match is None:
            unrecognised.append(line)
            continue
        name = match.group("name")
        verdict = match.group("verdict")
        if verdict == "PASS":
            records.append(_finalize(name, "pass"))
        elif verdict == "IGNORE":
            records.append(_finalize(name, "not_run"))
        else:
            message = match.group("message") or ""
            detail = _UNITY_EXPECTED.search(message)
            if detail is not None:
                records.append(
                    _finalize(
                        name,
                        "fail",
                        failure=(
                            "unity_assert",
                            detail.group("expected").strip(),
                            detail.group("actual").strip(),
                            match.group("file"),
                            int(match.group("line")),
                        ),
                    )
                )
            else:
                records.append(_finalize(name, "error"))
    return tuple(records), tuple(unrecognised)


def parse_cmocka_output(text: str) -> tuple[tuple[ResultRecord, ...], tuple[str, ...]]:
    """Normalise cmocka output into finalized records plus unrecognised lines."""
    records: list[ResultRecord] = []
    unrecognised: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        verdict_match = _CMOCKA_VERDICT.match(line)
        if verdict_match is None:
            unrecognised.append(line)
            continue
        name = verdict_match.group("name")
        outcome = "error" if verdict_match.group("verdict") == "FAILED" else "pass"
        records.append(_finalize(name, outcome))
    return tuple(records), tuple(unrecognised)


_PARSERS = {
    "unity": parse_unity_output,
    "cmocka": parse_cmocka_output,
}


def run_existing_suite(
    executable: Path | str,
    framework: str,
    *,
    argv_prefix: Sequence[str] = (),
) -> ExistingSuiteRun:
    """Execute an existing suite binary and normalise its framework output.

    The executable runs directly (no shell, no network); the process exit
    status is never consulted (EXH-02). ``argv_prefix`` lets a caller
    prepend interpreter arguments (used by the test suite for
    interpreter-hosted suite stubs); production passes nothing.
    """
    if framework not in SUPPORTED_FRAMEWORKS:
        raise MigError(
            f"unsupported existing-suite framework '{framework}' "
            f"(supported: {', '.join(SUPPORTED_FRAMEWORKS)})",
            reason="unsupported_framework",
        )
    executable_path = Path(executable)
    if not executable_path.is_file():
        raise MigError(
            f"existing suite executable '{executable_path}' does not exist",
            path=executable_path,
            reason="executable_missing",
        )
    try:
        completed = subprocess.run(
            [*argv_prefix, str(executable_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=None,
        )
        stdout = completed.stdout
    except OSError as exc:
        raise MigError(
            f"cannot launch existing suite '{executable_path}': {exc}",
            path=executable_path,
            reason="execution_launch_error",
        ) from exc

    parser = _PARSERS[framework]
    records, unrecognised = parser(stdout)
    if records:
        by_id = {record.test_id: record for record in records}
        aggregate = aggregate_outcome(by_id, sorted(by_id))
    else:
        aggregate = None  # nothing recognised: never a silent pass
    return ExistingSuiteRun(
        framework=framework,
        records=tuple(records),
        unrecognised_lines=tuple(unrecognised),
        aggregate=aggregate,
    )

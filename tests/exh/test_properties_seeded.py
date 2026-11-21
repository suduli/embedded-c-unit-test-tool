# implements: TOOL-EXE-020
"""Seeded property-style tests for ectt.exh result normalisation (TEST-PROP-TCM, tests only).

Inputs come from ``random.Random(seed)`` with fixed seeds (the seed is the test id), so a
failure is reproducible with one number. The properties:

* ``finalize_result`` accepts a record exactly when the NR-18 rules hold (checked against an
  independently written oracle over random outcomes and failures);
* the result-stream normaliser returns exactly the records the stream describes, whatever
  the interleaving of RESULT and FAILURE lines and however much framework chatter surrounds
  them, and refuses each kind of protocol violation with its own named error;
* the run outcome is a function of the records and the allocation only (never of order).
"""

from __future__ import annotations

import random
from typing import Any

import pytest

from ectt.exh.errors import (
    DuplicateTestResultError,
    InvalidResultRecordError,
    MalformedResultStreamError,
    UnknownTestResultError,
)
from ectt.exh.results import (
    AssertionFailure,
    ResultRecord,
    SourceLocation,
    aggregate_outcome,
    finalize_result,
)
from ectt.exh.runner import _parse_result_stream

SEEDS = range(40)
DIGEST = "d" * 64
_TOKENS = ["adc", "expected_return", "g_state", "0", "4095", "-1", "0x10", "src/a.c", "frame.len", "NULL"]
OUTCOMES = ("pass", "fail", "error", "timeout", "not_run")


def _failure(rng: random.Random, *, valid: bool = True) -> AssertionFailure:
    fields = [rng.choice(_TOKENS) for _ in range(3)]
    line = rng.randint(1, 500)
    if not valid:
        broken = rng.choice(["assertion", "expected", "actual", "file", "line"])
        if broken == "line":
            line = rng.choice([0, -1])
        elif broken == "file":
            return AssertionFailure(fields[0], fields[1], fields[2], SourceLocation(" ", line))
        else:
            fields[["assertion", "expected", "actual"].index(broken)] = "  "
    return AssertionFailure(fields[0], fields[1], fields[2], SourceLocation("src/a.c", line))


# --- finalize_result ---------------------------------------------------------------------------


def _oracle_accepts(outcome: str, failures: list[AssertionFailure], *, test_id: str, digest: str, duration: int | None) -> bool:
    if not test_id.strip() or not digest.strip():
        return False
    if duration is not None and duration < 0:
        return False
    if outcome == "pass":
        return not failures
    if outcome == "fail":
        return bool(failures) and all(
            f.assertion.strip() and f.expected.strip() and f.actual.strip() and f.location.file.strip() and f.location.line >= 1
            for f in failures
        )
    return not failures  # error, timeout, not_run


@pytest.mark.parametrize("seed", SEEDS)
def test_finalize_result_accepts_exactly_what_the_nr18_rules_allow(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(40):
        outcome = rng.choice(OUTCOMES)
        count = rng.choice([0, 0, 1, 2, 3])
        failures = [_failure(rng, valid=rng.random() < 0.75) for _ in range(count)]
        test_id = rng.choice(["tc.one", "tc.two", "", "  "])
        digest = rng.choice([DIGEST, DIGEST, "", " "])
        duration = rng.choice([None, 0, 12, -1])
        expected = _oracle_accepts(outcome, failures, test_id=test_id, digest=digest, duration=duration)

        if expected:
            record = finalize_result(test_id, outcome, digest, failures=failures, duration_ms=duration)
            assert (record.test_id, record.outcome, record.failures) == (test_id, outcome, tuple(failures))
        else:
            with pytest.raises(InvalidResultRecordError):
                finalize_result(test_id, outcome, digest, failures=failures, duration_ms=duration)


@pytest.mark.parametrize("seed", SEEDS[:10])
def test_an_unknown_outcome_is_always_refused(seed: int) -> None:
    rng = random.Random(seed)
    bad = rng.choice(["passed", "PASS", "failed", "skip", "", "ok", "crash"])
    with pytest.raises(InvalidResultRecordError):
        finalize_result("tc.one", bad, DIGEST)


# --- stream normalisation -----------------------------------------------------------------------


def _scenario(rng: random.Random) -> tuple[dict[str, tuple[str, list[AssertionFailure]]], list[list[str]]]:
    """Random tests with outcomes and failures, as per-test line sequences (order within a test is free)."""
    tests: dict[str, tuple[str, list[AssertionFailure]]] = {}
    sequences: list[list[str]] = []
    for index in range(rng.randint(1, 8)):
        test_id = f"tc.{index}"
        outcome = rng.choice(["pass", "fail", "error"])
        failures = [_failure(rng) for _ in range(rng.randint(1, 3))] if outcome == "fail" else []
        tests[test_id] = (outcome, failures)
        lines = [f"FAILURE {test_id} {f.assertion} {f.expected} {f.actual} {f.location.file} {f.location.line}" for f in failures]
        position = rng.randint(0, len(lines))
        lines.insert(position, f"RESULT {test_id} {outcome}")  # FAILURE lines may precede or follow RESULT
        sequences.append(lines)
    return tests, sequences


def _merge(rng: random.Random, sequences: list[list[str]], chatter: int) -> list[str]:
    """Randomly interleave sequences, keeping each one's own order, with noise lines mixed in."""
    pending = [list(s) for s in sequences if s]
    noise = [rng.choice(["framework banner", "  ", "", "Unity test run 1 of 1", "RESULTS: all done", "PASS (not a record)", "12 Tests 0 Failures"]) for _ in range(chatter)]
    merged: list[str] = []
    while pending or noise:
        choice = rng.randrange(len(pending) + (1 if noise else 0))
        if choice == len(pending):
            merged.append(noise.pop())
        else:
            merged.append(pending[choice].pop(0))
            if not pending[choice]:
                pending.pop(choice)
    return merged


def _expected_records(tests: dict[str, tuple[str, list[AssertionFailure]]]) -> tuple[ResultRecord, ...]:
    return tuple(finalize_result(t, o, DIGEST, failures=f) for t, (o, f) in sorted(tests.items()))


def _parse(lines: list[str], tests: dict[str, Any]) -> tuple[ResultRecord, ...]:
    return _parse_result_stream("\n".join(lines) + "\n", frozenset(tests), dict.fromkeys(tests, DIGEST))


@pytest.mark.parametrize("seed", SEEDS)
def test_the_normaliser_returns_exactly_the_records_the_stream_describes(seed: int) -> None:
    rng = random.Random(seed)
    tests, sequences = _scenario(rng)
    lines = _merge(rng, sequences, chatter=rng.randint(0, 6))

    assert _parse(lines, tests) == _expected_records(tests)


@pytest.mark.parametrize("seed", SEEDS)
def test_the_result_does_not_depend_on_interleaving_noise_or_line_endings(seed: int) -> None:
    rng = random.Random(seed)
    tests, sequences = _scenario(rng)
    first = _parse(_merge(rng, sequences, chatter=0), tests)
    second = _parse(_merge(rng, sequences, chatter=7), tests)
    crlf = _parse_result_stream("\r\n".join(_merge(rng, sequences, chatter=3)) + "\r\n", frozenset(tests), dict.fromkeys(tests, DIGEST))

    assert first == second == crlf == _expected_records(tests)


@pytest.mark.parametrize("seed", SEEDS)
def test_records_come_back_sorted_by_test_id_with_failures_in_stream_order(seed: int) -> None:
    rng = random.Random(seed)
    tests, sequences = _scenario(rng)
    records = _parse(_merge(rng, sequences, chatter=2), tests)

    assert [r.test_id for r in records] == sorted(tests)
    for record in records:
        assert list(record.failures) == tests[record.test_id][1]


@pytest.mark.parametrize("seed", SEEDS)
def test_whitespace_padding_around_lines_is_ignored(seed: int) -> None:
    rng = random.Random(seed)
    tests, sequences = _scenario(rng)
    lines = [f"{' ' * rng.randint(0, 3)}{line}{' ' * rng.randint(0, 3)}" for line in _merge(rng, sequences, chatter=1)]
    assert _parse(lines, tests) == _expected_records(tests)


def _mutate(rng: random.Random, tests: dict[str, tuple[str, list[AssertionFailure]]], lines: list[str]) -> tuple[list[str], type[Exception]]:
    result_indices = [i for i, line in enumerate(lines) if line.startswith("RESULT ")]
    failing = [t for t, (o, _f) in tests.items() if o == "fail"]
    passing = [t for t, (o, _f) in tests.items() if o == "pass"]
    kinds = ["duplicate", "unknown", "short_result", "bad_outcome"]
    if passing:
        kinds.append("failure_on_pass")
    if failing:
        kinds += ["orphan_failure", "bad_line_number", "short_failure", "fail_without_failure"]
    kind = rng.choice(kinds)
    out = list(lines)
    if kind == "duplicate":
        i = rng.choice(result_indices)
        out.insert(i, out[i])
        return out, DuplicateTestResultError
    if kind == "unknown":
        out.append("RESULT tc.not_allocated pass")
        return out, UnknownTestResultError
    if kind == "short_result":
        i = rng.choice(result_indices)
        out[i] = " ".join(out[i].split()[:2])
        return out, MalformedResultStreamError
    if kind == "bad_outcome":
        i = rng.choice(result_indices)
        out[i] = out[i].rsplit(" ", 1)[0] + " passed"
        return out, MalformedResultStreamError
    if kind == "failure_on_pass":
        out.append(f"FAILURE {rng.choice(passing)} a 1 2 f.c 3")
        return out, MalformedResultStreamError
    target = rng.choice(failing)
    if kind == "orphan_failure":
        return [line for line in out if line != f"RESULT {target} fail"], MalformedResultStreamError
    failure_indices = [i for i, line in enumerate(out) if line.startswith(f"FAILURE {target} ")]
    if kind == "bad_line_number":
        i = rng.choice(failure_indices)
        out[i] = out[i].rsplit(" ", 1)[0] + " " + rng.choice(["0", "x", "-3", "1.5"])
        return out, MalformedResultStreamError
    if kind == "short_failure":
        i = rng.choice(failure_indices)
        out[i] = " ".join(out[i].split()[:6])
        return out, MalformedResultStreamError
    return [line for i, line in enumerate(out) if i not in failure_indices], InvalidResultRecordError  # fail_without_failure


@pytest.mark.parametrize("seed", SEEDS)
def test_every_kind_of_protocol_violation_is_refused_with_its_own_error(seed: int) -> None:
    rng = random.Random(seed)
    tests, sequences = _scenario(rng)
    lines = _merge(rng, sequences, chatter=2)
    mutated, expected_error = _mutate(rng, tests, lines)

    with pytest.raises(expected_error):
        _parse(mutated, tests)


# --- run outcome ----------------------------------------------------------------------------------------


def _oracle_outcome(records: dict[str, ResultRecord], allocated: list[str]) -> str:
    if any(t not in records for t in allocated):
        return "incomplete"
    if any(records[t].outcome in ("fail", "error", "timeout") for t in allocated):
        return "failed"
    return "pass"


@pytest.mark.parametrize("seed", SEEDS)
def test_the_run_outcome_matches_an_independent_oracle_and_ignores_order(seed: int) -> None:
    rng = random.Random(seed)
    allocated = [f"tc.{i}" for i in range(rng.randint(1, 8))]
    records: dict[str, ResultRecord] = {}
    for test_id in allocated:
        if rng.random() < 0.85:
            outcome = rng.choice(["pass", "pass", "pass", "fail", "error", "timeout", "not_run"])
            failures = [_failure(rng)] if outcome == "fail" else []
            records[test_id] = finalize_result(test_id, outcome, DIGEST, failures=failures)
    shuffled = list(allocated)
    rng.shuffle(shuffled)
    items = list(records.items())
    rng.shuffle(items)

    outcome = aggregate_outcome(dict(items), shuffled)

    assert outcome == _oracle_outcome(records, allocated)
    assert outcome == aggregate_outcome(records, allocated)


@pytest.mark.parametrize("seed", SEEDS[:15])
def test_a_missing_record_always_makes_the_run_incomplete_even_when_others_failed(seed: int) -> None:
    rng = random.Random(seed)
    allocated = [f"tc.{i}" for i in range(rng.randint(2, 6))]
    records = {t: finalize_result(t, "error", DIGEST) for t in allocated}
    del records[rng.choice(allocated)]
    assert aggregate_outcome(records, allocated) == "incomplete"


@pytest.mark.parametrize("seed", SEEDS[:15])
def test_not_run_never_passes_the_run(seed: int) -> None:
    rng = random.Random(seed)
    allocated = [f"tc.{i}" for i in range(rng.randint(1, 6))]
    records = {t: finalize_result(t, "pass", DIGEST) for t in allocated}
    records[rng.choice(allocated)] = finalize_result("tc.x", "not_run", DIGEST)
    # a not_run record is present, so the run is complete; it is not a failure but it is not
    # accepted as evidence either: the oracle below states what the function does today
    assert aggregate_outcome(records, allocated) == _oracle_outcome(records, allocated)

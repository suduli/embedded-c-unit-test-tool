# implements: TOOL-QUA-040
"""Seeded property-style tests for ectt.qua (A9, tests only; no src/ edits).

Property: **known-error list validation order independence** — for random valid
entries, the loaded list (and every release query over it) is identical whatever
order the blocks were written in, and a violation is refused with the same named
reason wherever it sits. Inputs come from ``random.Random(seed)`` with fixed
seeds; no wall clock.
"""

from __future__ import annotations

import random

import pytest

from ectt.qua import KnownErrorListError, errors_for_release, load_known_errors

SEEDS = [0, 1, 7, 42, 1337]


def _entry(rng: random.Random, index: int) -> str:
    major = rng.randint(0, 2)
    minor = rng.randint(0, 20)
    introduced = f"{major}.{minor}.0"
    affected = ", ".join(f"{major}.{minor}.{p}" for p in sorted({0, rng.randint(1, 5)}))
    fixed = rng.random() < 0.5
    fix_version = f"{major}.{minor + 1}.{rng.randint(0, 9)}"
    if not fixed and rng.random() < 0.9:
        workaround = f"workaround {index}: use the JSON report"
    else:
        workaround = f"workaround {index}: regenerate as v2"
    status = "open" if not fixed else f"fixed in {fix_version}"
    return (
        f"error: ERR-{index:03d}\n"
        f"summary: seeded error {index}\n"
        f"introduced-in: {introduced}\n"
        f"affected-versions: {affected}\n"
        f"workaround: {workaround}\n"
        f"status: {status}\n"
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_the_loaded_list_is_order_independent(seed: int) -> None:
    """verifies: TOOL-QUA-040 — shuffled block order, identical loaded list."""
    rng = random.Random(seed)
    entries = [_entry(rng, i) for i in range(rng.randint(2, 6))]
    straight = load_known_errors("\n".join(entries))
    shuffled = entries[:]
    rng.shuffle(shuffled)
    mixed = load_known_errors("\n".join(shuffled))
    assert straight == mixed
    assert [e.error_id for e in straight] == sorted(e.error_id for e in straight)


@pytest.mark.parametrize("seed", SEEDS)
def test_a_violation_is_refused_the_same_wherever_it_sits(seed: int) -> None:
    """verifies: TOOL-QUA-040 — injecting the same duplicate id anywhere in a
    shuffled list is refused with the same named reason."""
    rng = random.Random(seed)
    count = rng.randint(2, 5)
    entries = [_entry(rng, i) for i in range(count)]
    base = load_known_errors("\n".join(entries))
    duplicate = _entry(rng, 99).replace(
        "error: ERR-099", f"error: {base[0].error_id}"
    )
    position = rng.randint(0, len(entries))
    poisoned = [*entries[:position], duplicate, *entries[position:]]
    with pytest.raises(KnownErrorListError) as excinfo:
        load_known_errors("\n".join(poisoned))
    assert excinfo.value.reason == "duplicate_error_id"
    assert base[0].error_id in str(excinfo.value)


@pytest.mark.parametrize("seed", SEEDS)
def test_release_queries_are_order_independent(seed: int) -> None:
    """verifies: TOOL-QUA-040 — every queried release returns the same entries
    from the shuffled list as from the straight one."""
    rng = random.Random(seed)
    entries = [_entry(rng, i) for i in range(rng.randint(2, 6))]
    straight = load_known_errors("\n".join(entries))
    shuffled = load_known_errors("\n".join(entries[:]))
    shuffled_entries = entries[:]
    rng.shuffle(shuffled_entries)
    shuffled = load_known_errors("\n".join(shuffled_entries))
    for release in ("0.1.0", "0.5.3", "1.19.0", "2.0.0"):
        assert errors_for_release(shuffled, release) == errors_for_release(straight, release)
        assert [e.error_id for e in errors_for_release(straight, release)] == sorted(
            e.error_id for e in errors_for_release(straight, release)
        )

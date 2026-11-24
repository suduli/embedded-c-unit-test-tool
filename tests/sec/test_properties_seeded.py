# implements: TOOL-NFR-100
"""Seeded property-style tests for ectt.sec (A9, tests only; no src/ edits).

Fixed seeds (the seed is the test id); no wall clock. Properties:

* **SBOM output stable under input order** (WP-SEC-01): a random package list
  produces the byte-identical document whatever order it is presented in, and the
  unknown-licence disclosure matches an independently computed set.
* **Lock-file checker symmetry** (WP-SEC-02): swapping the installed state with
  the pins flips exactly the missing/extra kinds and leaves wrong_version,
  wrong_hash and unpinned unchanged; the checker is deterministic under input
  reordering.
"""

from __future__ import annotations

import random

import pytest

from ectt.sec import (
    PinnedPackage,
    SbomComponent,
    check_pins,
    dump_sbom,
    generate_sbom,
    load_pin_lock,
)

SEEDS = [0, 1, 7, 42, 1337]


def _packages(rng: random.Random) -> list[SbomComponent]:
    packages = [SbomComponent(name="ectt", version="0.1.0", licence="MIT", is_tool=True)]
    for index in range(rng.randint(1, 6)):
        licence = rng.choice(("MIT", "BSD-3-Clause", None, ""))
        sha = f"{rng.getrandbits(256):064x}" if rng.random() < 0.5 else None
        packages.append(
            SbomComponent(
                name=f"dep-{index}-{rng.randint(0, 99)}",
                version=f"{rng.randint(0, 3)}.{rng.randint(0, 20)}.{rng.randint(0, 9)}",
                licence=licence,
                sha256=sha,
            )
        )
    return packages


@pytest.mark.parametrize("seed", SEEDS)
def test_the_sbom_is_stable_under_input_order(seed: int) -> None:
    """verifies: WP-SEC-01 AC-2 — shuffled package lists give the byte-identical
    document and the same unknown-licence disclosure."""
    rng = random.Random(seed)
    packages = _packages(rng)
    straight = generate_sbom(packages)
    shuffled = packages[:]
    rng.shuffle(shuffled)
    mixed = generate_sbom(shuffled)
    assert dump_sbom(straight) == dump_sbom(mixed)
    oracle_unknown = sorted(
        p.name for p in packages if p.licence is None or not p.licence.strip()
    )
    assert straight.licences_unknown == tuple(oracle_unknown)
    assert straight.licences_unknown == mixed.licences_unknown


@pytest.mark.parametrize("seed", SEEDS)
def test_duplicate_package_names_are_refused_regardless_of_order(seed: int) -> None:
    """verifies: WP-SEC-01 — the same name twice is refused wherever it sits."""
    rng = random.Random(seed)
    packages = _packages(rng)
    twin = SbomComponent(name=packages[0].name, version="9.9.9", licence="MIT")
    poisoned = [*packages, twin]
    rng.shuffle(poisoned)
    with pytest.raises(Exception) as excinfo:
        generate_sbom(poisoned)
    assert "two components" in str(excinfo.value)


def _pins(rng: random.Random) -> tuple[dict[str, tuple[str, str | None]], dict[str, PinnedPackage]]:
    installed: dict[str, tuple[str, str | None]] = {}
    pin_map: dict[str, PinnedPackage] = {}
    for index in range(rng.randint(2, 7)):
        name = f"pkg-{index}-{rng.randint(0, 99)}"
        version = f"{rng.randint(0, 2)}.{rng.randint(0, 9)}.{rng.randint(0, 9)}"
        pin_version = version if rng.random() < 0.7 else f"0.0.{index}"
        hash_hex = f"{rng.getrandbits(256):064x}" if rng.random() < 0.7 else None
        installed[name] = (version, hash_hex if rng.random() < 0.8 else None)
        pin_map[name] = PinnedPackage(name=name, version=pin_version, sha256=hash_hex)
    if rng.random() < 0.5:  # sometimes an installed-but-unpinned package
        name = f"rogue-{rng.randint(0, 99)}"
        installed[name] = ("1.0.0", None)
    if rng.random() < 0.5:  # sometimes a pinned-but-not-installed package
        name = f"absent-{rng.randint(0, 99)}"
        pin_map[name] = PinnedPackage(name=name, version="2.0.0", sha256=f"{rng.getrandbits(256):064x}")
    return installed, pin_map


@pytest.mark.parametrize("seed", SEEDS)
def test_the_checker_is_symmetric_in_missing_and_extra(seed: int) -> None:
    """verifies: WP-SEC-02 AC-2 — swapping the installed state and the pins
    flips exactly the missing/extra kinds; wrong_version, wrong_hash and
    unpinned are unchanged (the comparison is pairwise)."""
    rng = random.Random(seed)
    installed, pin_map = _pins(rng)
    forward = check_pins(installed, pin_map)

    swapped_installed = {name: (p.version, p.sha256) for name, p in pin_map.items()}
    swapped_pins = {name: PinnedPackage(name=name, version=v, sha256=h) for name, (v, h) in installed.items()}
    backward = check_pins(swapped_installed, swapped_pins)

    forward_missing = {d.name for d in forward if d.kind == "missing"}
    forward_extra = {d.name for d in backward if d.kind == "missing"}  # flipped
    backward_missing = {d.name for d in backward if d.kind == "missing"}
    assert backward_missing == forward_extra
    assert {d.name for d in forward if d.kind == "extra"} == backward_missing
    assert forward_missing == {d.name for d in backward if d.kind == "extra"}

    for kind in ("wrong_version", "wrong_hash", "unpinned"):
        assert {d.name for d in forward if d.kind == kind} == {d.name for d in backward if d.kind == kind}


@pytest.mark.parametrize("seed", SEEDS)
def test_the_lock_checker_is_deterministic_under_reordering(seed: int) -> None:
    """verifies: WP-SEC-02 AC-4 — identical inputs in any order, identical
    report; the lock loader is order-independent too."""
    rng = random.Random(seed)
    installed, pin_map = _pins(rng)
    first = check_pins(installed, pin_map)
    second = check_pins(dict(reversed(list(installed.items()))), dict(reversed(list(pin_map.items()))))
    assert first == second
    assert [(d.name, d.kind) for d in first] == sorted((d.name, d.kind) for d in first)

    lock_text = "\n".join(
        f"{p.name}=={p.version}" + (f" --hash=sha256:{p.sha256}" if p.sha256 else "")
        for p in reversed(list(pin_map.values()))
    )
    reloaded = {p.name: p for p in load_pin_lock(lock_text)}
    assert reloaded == pin_map

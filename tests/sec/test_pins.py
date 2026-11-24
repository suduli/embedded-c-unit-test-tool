# implements: TOOL-NFR-100
"""Pinned dependency integrity check (WP-SEC-02).

The installed state arrives as data (the checker is read-only by
construction); the lock loads strictly; every difference is reported by name
and the report is deterministic.
"""

from __future__ import annotations

import pytest

from ectt.sec import PinDifference, SecError, check_pins, load_pin_lock

LOCK = """
# the pinned tool and its dependencies
ectt==0.1.0 --hash=sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
attrs==26.1.0 --hash=sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
pyyaml==6.0.4
"""

PINS = {p.name: p for p in load_pin_lock(LOCK)}


def test_a_clean_match_reports_no_differences() -> None:
    """verifies: WP-SEC-02 AC-2 — the installed tree matches the lock exactly."""
    # A clean match means every pinned package is present with the pinned
    # version and hash where the lock records one; pyyaml's missing hash is the
    # unpinned case, so a truly clean report needs a hash for it too.
    fully_pinned = {p.name: p for p in load_pin_lock(LOCK.replace("pyyaml==6.0.4", "pyyaml==6.0.4 --hash=sha256:" + "c" * 64))}
    differences = check_pins(
        {
            "ectt": ("0.1.0", "a" * 64),
            "attrs": ("26.1.0", "b" * 64),
            "pyyaml": ("6.0.4", "c" * 64),
        },
        fully_pinned,
    )
    assert differences == ()


def test_a_missing_pin_is_reported_by_name() -> None:
    """verifies: WP-SEC-02 AC-2 — pinned but not installed."""
    differences = check_pins({"attrs": ("26.1.0", "b" * 64), "pyyaml": ("6.0.4", None)}, PINS)
    (missing,) = [d for d in differences if d.kind == "missing"]
    assert missing.name == "ectt"
    assert "pinned at 0.1.0" in missing.detail


def test_an_extra_package_is_reported_by_name() -> None:
    """verifies: WP-SEC-02 AC-2 — installed but not pinned."""
    differences = check_pins(
        {
            "ectt": ("0.1.0", "a" * 64),
            "attrs": ("26.1.0", "b" * 64),
            "pyyaml": ("6.0.4", None),
            "rogue": ("9.9.9", None),
        },
        PINS,
    )
    (extra,) = [d for d in differences if d.kind == "extra"]
    assert extra.name == "rogue"
    assert "not pinned" in extra.detail


def test_a_wrong_version_is_reported_by_name() -> None:
    """verifies: WP-SEC-02 AC-2 — both present, versions differ."""
    differences = check_pins(
        {"ectt": ("0.0.9", "a" * 64), "attrs": ("26.1.0", "b" * 64), "pyyaml": ("6.0.4", None)}, PINS
    )
    (wrong,) = [d for d in differences if d.kind == "wrong_version"]
    assert wrong.name == "ectt"
    assert "pinned 0.1.0, installed 0.0.9" in wrong.detail


def test_a_wrong_hash_is_reported_by_name() -> None:
    """verifies: WP-SEC-02 AC-2 — both hashes present and differ."""
    differences = check_pins(
        {"ectt": ("0.1.0", "f" * 64), "attrs": ("26.1.0", "b" * 64), "pyyaml": ("6.0.4", None)}, PINS
    )
    (wrong,) = [d for d in differences if d.kind == "wrong_hash"]
    assert wrong.name == "ectt"


def test_an_unverifiable_integrity_is_reported_as_unpinned() -> None:
    """verifies: WP-SEC-02 AC-2 — no hash on either side means integrity cannot
    be verified; the package is never silently accepted."""
    differences = check_pins(
        {"ectt": ("0.1.0", "a" * 64), "attrs": ("26.1.0", "b" * 64), "pyyaml": ("6.0.4", None)}, PINS
    )
    (unpinned,) = [d for d in differences if d.kind == "unpinned"]
    assert unpinned.name == "pyyaml"  # the lock entry records no hash
    assert "cannot be verified" in unpinned.detail

    # The reverse: the lock pins a hash but the installed evidence has none.
    differences = check_pins({"ectt": ("0.1.0", None)}, PINS)
    (unpinned,) = [d for d in differences if d.name == "ectt"]
    assert unpinned.kind == "unpinned"
    assert "installed evidence" in unpinned.detail


def test_a_malformed_lock_file_is_refused() -> None:
    """verifies: WP-SEC-02 AC-1 — structural violations name themselves."""
    with pytest.raises(SecError) as malformed:
        load_pin_lock("attrs 26.1.0\n")
    assert malformed.value.reason == "malformed_line"
    with pytest.raises(SecError) as bad_hash:
        load_pin_lock("attrs==26.1.0 --hash=sha256:XYZ\n")
    assert bad_hash.value.reason == "malformed_line"
    with pytest.raises(SecError) as duplicate:
        load_pin_lock("attrs==26.1.0\nattrs==26.1.1\n")
    assert duplicate.value.reason == "duplicate_pin"
    # A hash with uppercase hex is malformed too (the pin form is lowercase).
    with pytest.raises(SecError) as upper:
        load_pin_lock("attrs==26.1.0 --hash=sha256:" + "A" * 64 + "\n")
    assert upper.value.reason == "malformed_line"


def test_the_report_is_sorted_and_deterministic() -> None:
    """verifies: WP-SEC-02 AC-4 — differences sorted by (name, kind); identical
    inputs give identical reports."""
    installed = {
        "ectt": ("0.0.9", "a" * 64),
        "attrs": ("26.1.0", "b" * 64),
        "pyyaml": ("6.0.4", None),
        "rogue": ("9.9.9", None),
    }
    first = check_pins(installed, PINS)
    second = check_pins(dict(reversed(list(installed.items()))), PINS)
    assert first == second
    assert [(d.name, d.kind) for d in first] == sorted((d.name, d.kind) for d in first)
    assert all(isinstance(d, PinDifference) for d in first)
    assert [d.to_dict() for d in first] == [d.to_dict() for d in second]

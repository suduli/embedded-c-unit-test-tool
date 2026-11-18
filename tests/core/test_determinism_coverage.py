"""Gap-filling behaviour tests for ectt.core.determinism (TASK-004).

Covers the clock construction edge cases, mixed-type canonical ordering, stable-id
encoding branches, CoreError rendering, and the hash-seed re-exec error path.

Verifies: TOOL-NFR-060.
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

import pytest

from ectt.core import determinism
from ectt.core.determinism import (
    CoreError,
    FixedClock,
    canonicalize,
    stable_id,
)


def test_core_error_str_includes_path_when_given() -> None:
    """verifies: TOOL-NFR-060"""
    err = CoreError("disk full", reason="io_failed", path=Path("out/x.bin"))

    assert err.path == Path("out/x.bin")
    assert str(err) == f"disk full [reason=io_failed, path={Path('out/x.bin')}]"


def test_core_error_str_without_path() -> None:
    """verifies: TOOL-NFR-060"""
    err = CoreError("bad input", reason="invalid")

    assert err.path is None
    assert str(err) == "bad input [reason=invalid]"


def test_fixed_clock_normalises_naive_and_aware_datetimes_to_utc() -> None:
    """verifies: TOOL-NFR-060"""
    naive = FixedClock(datetime.datetime(2026, 3, 1, 9, 30))
    assert naive.isoformat() == "2026-03-01T09:30:00+00:00"

    offset_zone = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    aware = FixedClock(datetime.datetime(2026, 3, 1, 15, 0, tzinfo=offset_zone))
    assert aware.isoformat() == "2026-03-01T09:30:00+00:00"


def test_fixed_clock_parses_naive_and_offset_iso_strings() -> None:
    """verifies: TOOL-NFR-060"""
    naive = FixedClock("2026-05-02T08:00:00")
    assert naive.now().tzinfo is datetime.UTC
    assert naive.isoformat() == "2026-05-02T08:00:00+00:00"

    offset = FixedClock("2026-05-02T10:00:00+02:00")
    assert offset.isoformat() == "2026-05-02T08:00:00+00:00"


def test_fixed_clock_rejects_unsupported_type() -> None:
    """verifies: TOOL-NFR-060"""
    with pytest.raises(TypeError, match="Unsupported time specification"):
        FixedClock([2026, 1, 1])  # type: ignore[arg-type]


def test_fixed_clock_rejects_malformed_iso_string() -> None:
    """verifies: TOOL-NFR-060"""
    with pytest.raises(ValueError):
        FixedClock("not-a-timestamp")


def test_canonicalize_naive_datetime_is_marked_utc() -> None:
    """verifies: TOOL-NFR-060"""
    result = canonicalize({"at": datetime.datetime(2026, 7, 4, 12, 0)})

    assert result == {"at": "2026-07-04T12:00:00+00:00"}


def test_canonicalize_mixed_type_set_is_order_independent() -> None:
    """verifies: TOOL-NFR-060

    Sets carry no order; the canonical list must be identical regardless of the
    order in which the elements were inserted, across heterogeneous types.
    """
    first = frozenset({1, "one", b"raw", 2.5, Path("p/q")})
    second = frozenset([Path("p/q"), 2.5, b"raw", "one", 1])

    assert canonicalize(first) == canonicalize(second)
    assert len(canonicalize(first)) == 5


def test_stable_id_bytes_and_str_encode_identically() -> None:
    """verifies: TOOL-NFR-060"""
    assert stable_id(b"abc") == stable_id("abc")


def test_stable_id_distinguishes_bool_values() -> None:
    """verifies: TOOL-NFR-060"""
    assert stable_id(True) != stable_id(False)


def test_stable_id_distinguishes_negative_zero() -> None:
    """verifies: TOOL-NFR-060"""
    assert stable_id(-0.0) != stable_id(0.0)
    assert stable_id(float("nan")) == stable_id(float("nan"))


def test_stable_id_path_matches_posix_string() -> None:
    """verifies: TOOL-NFR-060"""
    assert stable_id(Path("a") / "b") == stable_id("a/b")


def test_stable_id_is_key_order_invariant_for_dicts() -> None:
    """verifies: TOOL-NFR-060"""
    assert stable_id({"b": 1, "a": 2}) == stable_id({"a": 2, "b": 1})
    assert stable_id({"a": 2}) != stable_id({"a": 3})


def test_stable_id_fallback_uses_str_representation() -> None:
    """verifies: TOOL-NFR-060"""
    assert stable_id(None) == stable_id("None")


def test_neutralize_hash_seed_returns_true_when_already_pinned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """verifies: TOOL-NFR-060"""
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    monkeypatch.delenv("_ECTT_HASHSEED_LOCKED", raising=False)

    assert determinism.neutralize_hash_seed() is True


def test_neutralize_hash_seed_returns_true_under_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """verifies: TOOL-NFR-060"""
    monkeypatch.setenv("PYTHONHASHSEED", "random")
    monkeypatch.setenv("_ECTT_HASHSEED_LOCKED", "1")

    assert determinism.neutralize_hash_seed() is True


def test_neutralize_hash_seed_wraps_subprocess_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """verifies: TOOL-NFR-060"""
    monkeypatch.setenv("PYTHONHASHSEED", "random")
    monkeypatch.delenv("_ECTT_HASHSEED_LOCKED", raising=False)

    def broken_run(*args: object, **kwargs: object) -> None:
        raise OSError("spawn denied")

    monkeypatch.setattr(subprocess, "run", broken_run)

    with pytest.raises(CoreError) as exc_info:
        determinism.neutralize_hash_seed()
    assert exc_info.value.reason == "reexec_failed"


@pytest.mark.skipif(sys.platform != "win32", reason="child-process exit path is the Windows branch")
def test_neutralize_hash_seed_propagates_child_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """verifies: TOOL-NFR-060"""
    monkeypatch.setenv("PYTHONHASHSEED", "random")
    monkeypatch.delenv("_ECTT_HASHSEED_LOCKED", raising=False)
    seen: dict[str, object] = {}

    class _Result:
        returncode = 3

    def fake_run(cmd: list[str], *, env: dict[str, str], check: bool) -> _Result:
        seen["env"] = env
        seen["check"] = check
        return _Result()

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(SystemExit) as exc_info:
        determinism.neutralize_hash_seed()

    assert exc_info.value.code == 3
    assert seen["check"] is False
    env = seen["env"]
    assert isinstance(env, dict)
    assert env["PYTHONHASHSEED"] == "0"
    assert env["_ECTT_HASHSEED_LOCKED"] == "1"

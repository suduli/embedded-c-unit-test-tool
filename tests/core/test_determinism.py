# implements: DSN-CORE-010
"""Tests for ectt.core.determinism.

Verifies: TOOL-NFR-060, TOOL-PRJ-050, DSN-CORE-010.
"""

from __future__ import annotations

import datetime
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from ectt.core.determinism import (
    Clock,
    CoreError,
    FixedClock,
    SystemClock,
    canonical_bytes,
    canonical_float_repr,
    canonical_json,
    canonical_json_bytes,
    canonical_text,
    canonicalize,
    neutralize_hash_seed,
    stable_id,
)


def test_clock_protocol_conformance() -> None:
    """verifies: TOOL-NFR-060, DSN-CORE-010"""
    sys_clock = SystemClock()
    fixed_clock = FixedClock("2026-09-26T12:00:00+00:00")

    assert isinstance(sys_clock, Clock)
    assert isinstance(fixed_clock, Clock)


def test_system_clock_returns_utc() -> None:
    """verifies: TOOL-NFR-060, DSN-CORE-010"""
    clock = SystemClock()
    t1 = clock.time()
    dt = clock.now()
    iso = clock.isoformat()

    assert dt.tzinfo == datetime.timezone.utc
    assert iso.endswith("+00:00")
    assert t1 > 0.0


def test_fixed_clock_frozen_and_advance() -> None:
    """verifies: TOOL-NFR-060, DSN-CORE-010"""
    # From ISO string with explicit timezone
    clock = FixedClock("2026-09-26T12:00:00+00:00")
    assert clock.isoformat() == "2026-09-26T12:00:00+00:00"
    assert clock.time() == datetime.datetime(2026, 9, 26, 12, 0, 0, tzinfo=datetime.timezone.utc).timestamp()

    # Repeated calls return identical values
    assert clock.now() == clock.now()
    assert clock.time() == clock.time()

    # Advance clock
    clock.advance(3600.0)
    assert clock.isoformat() == "2026-09-26T13:00:00+00:00"


def test_fixed_clock_initialization_variants() -> None:
    """verifies: TOOL-NFR-060, DSN-CORE-010"""
    # Default construction
    default_clock = FixedClock()
    assert default_clock.now() == datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    # From naive datetime (assumes UTC)
    naive_dt = datetime.datetime(2026, 5, 1, 8, 30, 0)
    clock_dt = FixedClock(naive_dt)
    assert clock_dt.now().tzinfo == datetime.timezone.utc
    assert clock_dt.now().hour == 8

    # From float timestamp
    ts = 1700000000.0
    clock_ts = FixedClock(ts)
    assert clock_ts.time() == ts

    # Error case: unsupported type
    with pytest.raises(TypeError, match="Unsupported time specification"):
        FixedClock([2026, 1, 1])  # type: ignore[arg-type]


def test_stable_id_deterministic_and_unique() -> None:
    """verifies: TOOL-NFR-060, TOOL-PRJ-050, DSN-CORE-010"""
    id1 = stable_id("unit_test_1", "adc_read", 42)
    id2 = stable_id("unit_test_1", "adc_read", 42)
    assert id1 == id2
    assert len(id1) == 64  # SHA-256 hex string

    id_diff = stable_id("unit_test_1", "adc_read", 43)
    assert id1 != id_diff


def test_stable_id_collision_resistance() -> None:
    """verifies: TOOL-NFR-060, TOOL-PRJ-050, DSN-CORE-010"""
    # Framing with byte length prevents delimiter ambiguity
    id_a = stable_id("a", "bc")
    id_b = stable_id("ab", "c")
    assert id_a != id_b

    id_empty_1 = stable_id("", "foo")
    id_empty_2 = stable_id("foo", "")
    assert id_empty_1 != id_empty_2


def test_stable_id_dict_insertion_order_invariance() -> None:
    """verifies: TOOL-NFR-060, TOOL-PRJ-050, DSN-CORE-010"""
    dict1 = {"z": 10, "a": 20, "m": 30}
    dict2 = {"a": 20, "m": 30, "z": 10}

    assert stable_id(dict1) == stable_id(dict2)


def test_canonical_json_sorted_keys() -> None:
    """verifies: TOOL-PRJ-050, DSN-CORE-010"""
    dict_unordered_1 = {"zebra": 1, "apple": 2, "mango": 3}
    dict_unordered_2 = {"apple": 2, "zebra": 1, "mango": 3}

    json1 = canonical_json(dict_unordered_1)
    json2 = canonical_json(dict_unordered_2)

    assert json1 == json2
    # Verify key order in output text
    lines = [line.strip() for line in json1.splitlines() if line.strip()]
    assert lines[1].startswith('"apple"')
    assert lines[2].startswith('"mango"')
    assert lines[3].startswith('"zebra"')


def test_canonical_json_set_ordering() -> None:
    """verifies: TOOL-PRJ-050, DSN-CORE-010"""
    set1 = {"cherry", "banana", "apple"}
    set2 = {"apple", "cherry", "banana"}

    data1 = {"fruits": set1}
    data2 = {"fruits": set2}

    assert canonical_json(data1) == canonical_json(data2)

    # Sets must be sorted into lists
    canonical = canonicalize(set1)
    assert canonical == ["apple", "banana", "cherry"]


def test_canonical_json_heterogeneous_set_sorting() -> None:
    """verifies: TOOL-PRJ-050, DSN-CORE-010"""
    # Heterogeneous sets must sort without raising TypeError
    mixed_set = {42, "string", True, 3.14}
    c_mixed = canonicalize(mixed_set)
    assert len(c_mixed) == 4
    # Re-canonicalizing another set with same items produces identical order
    mixed_set_2 = {"string", 3.14, True, 42}
    assert c_mixed == canonicalize(mixed_set_2)


def test_canonical_json_preserves_list_order() -> None:
    """verifies: TOOL-PRJ-050, DSN-CORE-010"""
    # Lists have semantic ordering and must not be sorted
    seq1 = [3, 1, 2]
    seq2 = [1, 2, 3]

    assert canonical_json(seq1) != canonical_json(seq2)
    assert canonicalize(seq1) == [3, 1, 2]


def test_float_shortest_round_trip() -> None:
    """verifies: TOOL-PRJ-050, DSN-CORE-010"""
    # 0.1 stays 0.1, not 0.10000000000000000555
    assert canonical_float_repr(0.1) == "0.1"

    # 1e-7 round-trips correctly
    assert canonical_float_repr(1e-7) == "1e-07"
    assert float(canonical_float_repr(1e-7)) == 1e-7

    # Negative zero preservation
    assert canonical_float_repr(-0.0) == "-0.0"
    assert canonical_float_repr(0.0) == "0.0"

    # Round trip through JSON
    raw = canonical_json({"val": 0.1, "tiny": 1e-7, "neg_zero": -0.0})
    parsed = json.loads(raw)
    assert parsed["val"] == 0.1
    assert parsed["tiny"] == 1e-7
    assert parsed["neg_zero"] == 0.0
    assert math.copysign(1.0, parsed["neg_zero"]) == -1.0


def test_canonical_text_normalization() -> None:
    """verifies: TOOL-PRJ-050, DSN-CORE-010"""
    # CRLF and CR normalization + trailing line whitespace stripping
    raw_text = "line1 \r\nline2\t  \rline3\n\n\n"
    normalized = canonical_text(raw_text)

    # Exactly LF line endings
    assert "\r" not in normalized
    # Trailing whitespace on lines removed
    assert normalized == "line1\nline2\nline3\n"

    # Empty text
    assert canonical_text("") == ""
    assert canonical_text("   \n\n  \n") == ""


def test_canonical_bytes_helper() -> None:
    """verifies: TOOL-PRJ-050, DSN-CORE-010"""
    b1 = canonical_bytes("test\r\n")
    assert b1 == b"test\n"

    raw_binary = b"\x00\x01\x02\xff"
    assert canonical_bytes(raw_binary) == raw_binary


def test_canonical_float_special_values() -> None:
    """verifies: TOOL-PRJ-050, DSN-CORE-010"""
    assert canonical_float_repr(float("nan")) == "NaN"
    assert canonical_float_repr(float("inf")) == "Infinity"
    assert canonical_float_repr(float("-inf")) == "-Infinity"


def test_neutralize_hash_seed_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    """verifies: TOOL-NFR-060, DSN-CORE-010"""
    monkeypatch.setenv("_ECTT_HASHSEED_LOCKED", "1")
    monkeypatch.setenv("PYTHONHASHSEED", "random")

    # When guard is active, neutralize_hash_seed immediately returns True without re-execing
    assert neutralize_hash_seed(target_seed="0") is True

    monkeypatch.delenv("_ECTT_HASHSEED_LOCKED")
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    # When already target seed, returns True
    assert neutralize_hash_seed(target_seed="0") is True


def test_canonicalize_paths_and_dates() -> None:
    """verifies: TOOL-PRJ-050, DSN-CORE-010"""
    p = Path("foo/bar/baz.c")
    assert canonicalize(p) == "foo/bar/baz.c"

    dt = datetime.datetime(2026, 9, 26, 15, 30, tzinfo=datetime.timezone.utc)
    assert canonicalize(dt) == "2026-09-26T15:30:00+00:00"


def test_canonicalize_colliding_keys_raises_value_error() -> None:
    """verifies: TOOL-PRJ-050, DSN-CORE-010"""
    colliding = {1: "int_value", "1": "str_value"}
    with pytest.raises(ValueError, match="Duplicate stringified dictionary key '1'"):
        canonicalize(colliding)

    with pytest.raises(ValueError, match="Duplicate stringified dictionary key '1'"):
        canonical_json(colliding)


def test_neutralize_hash_seed_subprocess_observes_zero(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-060, DSN-CORE-010"""
    script = tmp_path / "check_seed.py"
    script.write_text(
        "import os, sys\n"
        "from ectt.core.determinism import neutralize_hash_seed\n"
        "neutralize_hash_seed('0')\n"
        "print('OBSERVED_SEED=' + os.environ.get('PYTHONHASHSEED', 'NONE'))\n",
        encoding="utf-8",
    )
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "random"
    env["PYTHONPATH"] = str(repo_root / "src")
    env.pop("_ECTT_HASHSEED_LOCKED", None)

    res = subprocess.run(
        [sys.executable, str(script)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Child script failed: {res.stderr}"
    assert "OBSERVED_SEED=0" in res.stdout


def test_neutralize_hash_seed_propagates_exit_code(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-060, DSN-CORE-010"""
    script = tmp_path / "exit_nonzero.py"
    script.write_text(
        "import sys\n"
        "from ectt.core.determinism import neutralize_hash_seed\n"
        "neutralize_hash_seed('0')\n"
        "sys.exit(42)\n",
        encoding="utf-8",
    )
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "random"
    env["PYTHONPATH"] = str(repo_root / "src")
    env.pop("_ECTT_HASHSEED_LOCKED", None)

    res = subprocess.run(
        [sys.executable, str(script)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 42


def test_neutralize_hash_seed_reexec_failure_raises_core_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """verifies: TOOL-NFR-060, DSN-CORE-010"""
    monkeypatch.delenv("_ECTT_HASHSEED_LOCKED", raising=False)
    monkeypatch.setenv("PYTHONHASHSEED", "random")

    def mock_subprocess_run(*args: Any, **kwargs: Any) -> Any:
        raise OSError("Simulated execution failure")

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    with pytest.raises(CoreError) as exc_info:
        neutralize_hash_seed(target_seed="0")

    assert exc_info.value.reason == "reexec_failed"


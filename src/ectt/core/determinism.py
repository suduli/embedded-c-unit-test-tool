# implements: DSN-CORE-010
"""Deterministic execution discipline and canonical serialization.

Fixes the sources of run-to-run variance:
- All collection iteration is over explicitly sorted keys/elements where order is non-semantic.
- All generated identifiers derive from content hashes rather than object identity or insertion order.
- Timestamps enter artifacts only through an injectable Clock protocol.
- PYTHONHASHSEED-style environment variance is neutralized at entry points, while the core
  algorithms remain order-independent by construction.

Satisfies: TOOL-NFR-060, TOOL-PRJ-050.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "Clock",
    "SystemClock",
    "FixedClock",
    "stable_id",
    "canonical_float_repr",
    "canonicalize",
    "canonical_text",
    "canonical_bytes",
    "canonical_json",
    "canonical_json_bytes",
    "neutralize_hash_seed",
    "CoreError",
]


class CoreError(Exception):
    """Base exception for ectt core platform errors."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "core_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.reason = reason
        self.path = Path(path) if path is not None else None

    def __str__(self) -> str:
        if self.path is not None:
            return f"{self.message} [reason={self.reason}, path={self.path}]"
        return f"{self.message} [reason={self.reason}]"


@runtime_checkable
class Clock(Protocol):
    """Injectable time source ensuring timestamps enter artifacts deterministically."""

    def now(self) -> datetime.datetime:
        """Return the current datetime (always timezone-aware UTC)."""
        ...

    def time(self) -> float:
        """Return the current epoch timestamp in seconds."""
        ...

    def isoformat(self) -> str:
        """Return canonical ISO 8601 formatted timestamp string in UTC."""
        ...


class SystemClock:
    """System clock reading host time in UTC."""

    def now(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    def time(self) -> float:
        return time.time()

    def isoformat(self) -> str:
        return self.now().isoformat()


class FixedClock:
    """Deterministic frozen clock for reproducible artifact generation and testing."""

    def __init__(self, frozen_time: datetime.datetime | float | int | str | None = None) -> None:
        if frozen_time is None:
            self._dt = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        elif isinstance(frozen_time, datetime.datetime):
            if frozen_time.tzinfo is None:
                self._dt = frozen_time.replace(tzinfo=datetime.timezone.utc)
            else:
                self._dt = frozen_time.astimezone(datetime.timezone.utc)
        elif isinstance(frozen_time, (int, float)):
            self._dt = datetime.datetime.fromtimestamp(float(frozen_time), tz=datetime.timezone.utc)
        elif isinstance(frozen_time, str):
            parsed = datetime.datetime.fromisoformat(frozen_time)
            if parsed.tzinfo is None:
                self._dt = parsed.replace(tzinfo=datetime.timezone.utc)
            else:
                self._dt = parsed.astimezone(datetime.timezone.utc)
        else:
            raise TypeError(f"Unsupported time specification for FixedClock: {type(frozen_time)!r}")

    def now(self) -> datetime.datetime:
        return self._dt

    def time(self) -> float:
        return self._dt.timestamp()

    def isoformat(self) -> str:
        return self._dt.isoformat()

    def advance(self, seconds: float) -> None:
        """Advance the frozen clock by the given duration in seconds."""
        self._dt += datetime.timedelta(seconds=seconds)


def canonical_float_repr(val: float) -> str:
    """Format floating point numbers using shortest round-trip representation.

    Correctly preserves distinction between -0.0 and +0.0, and handles NaN/Inf.
    """
    if math.isnan(val):
        return "NaN"
    if math.isinf(val):
        return "-Infinity" if val < 0.0 else "Infinity"
    if val == 0.0:
        return "-0.0" if math.copysign(1.0, val) < 0.0 else "0.0"
    return repr(val)


def _stable_sort_key(item: Any) -> tuple[int, str, Any]:
    """Generate a total ordering key across heterogeneous types without raising TypeError."""
    if isinstance(item, bool):
        return (0, type(item).__qualname__, int(item))
    if isinstance(item, (int, float)):
        # Distinguish -0.0 from +0.0 in sort order
        neg_zero = isinstance(item, float) and item == 0.0 and math.copysign(1.0, item) < 0.0
        return (1, type(item).__qualname__, (item, neg_zero))
    if isinstance(item, str):
        return (2, type(item).__qualname__, item)
    if isinstance(item, (bytes, bytearray, memoryview)):
        return (3, type(item).__qualname__, bytes(item).hex())
    if isinstance(item, Path):
        return (4, type(item).__qualname__, item.as_posix())
    if isinstance(item, (list, tuple)):
        return (5, type(item).__qualname__, tuple(_stable_sort_key(x) for x in item))
    if isinstance(item, (dict, set, frozenset)):
        return (6, type(item).__qualname__, repr(item))
    return (7, type(item).__qualname__, repr(item))


def canonicalize(data: Any, *, first_keys: Sequence[str] = ()) -> Any:
    """Recursively transform data structures into canonical forms:

    - dict: keys sorted deterministically, with optional first_keys prioritized.
    - set / frozenset: converted to sorted list (sets carry no semantic order).
    - list / tuple: semantic order preserved, elements canonicalized recursively.
    - Path: normalized to POSIX string format.
    - datetime: normalized to UTC ISO 8601 string.
    - float: values preserved (shortest round-trip applied during serialization).
    """
    if isinstance(data, dict):
        result: dict[str, Any] = {}
        stringified_keys: set[str] = set()
        for k in data.keys():
            k_str = str(k)
            if k_str in stringified_keys:
                raise ValueError(
                    f"Duplicate stringified dictionary key '{k_str}' detected during canonicalization "
                    f"(colliding key: {k!r})"
                )
            stringified_keys.add(k_str)

        for fk in first_keys:
            if fk in data:
                result[fk] = canonicalize(data[fk])
        for k, v in sorted(data.items(), key=lambda kv: _stable_sort_key(kv[0])):
            key_str = str(k)
            if key_str in result:
                continue
            result[key_str] = canonicalize(v)
        return result
    if isinstance(data, (set, frozenset)):
        canonical_items = [canonicalize(item) for item in data]
        return sorted(canonical_items, key=_stable_sort_key)
    if isinstance(data, (list, tuple)):
        return [canonicalize(item) for item in data]
    if isinstance(data, Path):
        return data.as_posix()
    if isinstance(data, (datetime.datetime, datetime.date)):
        if isinstance(data, datetime.datetime):
            if data.tzinfo is None:
                data = data.replace(tzinfo=datetime.timezone.utc)
            else:
                data = data.astimezone(datetime.timezone.utc)
        return data.isoformat()
    return data


def canonical_text(text: str) -> str:
    """Normalize text content according to diff-stability rules:

    - Standardize all line endings to LF ('\\n').
    - Strip trailing whitespace on each line.
    - Trim trailing blank lines and guarantee exactly one trailing newline (unless empty).
    """
    if not text:
        return ""
    normalized_endings = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" \t") for line in normalized_endings.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def canonical_bytes(content: str | bytes) -> bytes:
    """Convert text or bytes into canonical UTF-8 bytes."""
    if isinstance(content, str):
        return canonical_text(content).encode("utf-8")
    return bytes(content)


def canonical_json(
    data: Any,
    *,
    indent: int | None = 2,
    first_keys: Sequence[str] = (),
) -> str:
    """Serialize data to byte-deterministic canonical JSON:

    - Keys sorted (or ordered by first_keys then sorted).
    - Sets and non-semantic collections sorted.
    - LF line endings only.
    - UTF-8 representation (no unnecessary \\u escapes).
    - No trailing whitespace.
    - Shortest round-trip float representations ('0.1' stays '0.1', '-0.0' stays '-0.0').
    """
    canonical_data = canonicalize(data, first_keys=first_keys)
    separators = (",", ": ") if indent is not None else (",", ":")
    raw_json = json.dumps(
        canonical_data,
        indent=indent,
        ensure_ascii=False,
        sort_keys=False if first_keys else True,
        separators=separators,
    )
    return canonical_text(raw_json)


def canonical_json_bytes(
    data: Any,
    *,
    indent: int | None = 2,
    first_keys: Sequence[str] = (),
) -> bytes:
    """Return UTF-8 encoded canonical JSON bytes."""
    return canonical_json(data, indent=indent, first_keys=first_keys).encode("utf-8")


def _part_to_canonical_bytes(part: Any) -> bytes:
    """Encode an individual part to canonical bytes for stable ID hashing."""
    if isinstance(part, bytes):
        return part
    if isinstance(part, str):
        return part.encode("utf-8")
    if isinstance(part, bool):
        return b"1" if part else b"0"
    if isinstance(part, int):
        return str(part).encode("ascii")
    if isinstance(part, float):
        return canonical_float_repr(part).encode("ascii")
    if isinstance(part, Path):
        return part.as_posix().encode("utf-8")
    if isinstance(part, (dict, list, tuple, set, frozenset)):
        return canonical_json_bytes(part)
    return str(part).encode("utf-8")


def stable_id(*parts: Any) -> str:
    """Generate a content-derived stable identifier (SHA-256 over canonical encoding).

    Never relies on id(), hash(), or insertion order.
    Arguments are framed with their byte lengths to mathematically prevent collision attacks.
    """
    hasher = hashlib.sha256()
    for part in parts:
        b = _part_to_canonical_bytes(part)
        hasher.update(f"{len(b)}:".encode("ascii"))
        hasher.update(b)
    return hasher.hexdigest()


def neutralize_hash_seed(
    target_seed: str = "0",
    *,
    env_var: str = "PYTHONHASHSEED",
    guard_var: str = "_ECTT_HASHSEED_LOCKED",
) -> bool:
    """Entry-point neutralization of hash-seed variance across runtimes.

    For standalone CLI entry points: if the process runs with an unpinned or different
    PYTHONHASHSEED, re-executes using sys.orig_argv with the target seed (default "0")
    behind an environment guard variable to eliminate infinite loops.

    On Windows, uses subprocess.run to preserve stdio, console attachment, and the
    child's exit status. On POSIX, replaces the process using os.execv.
    If re-execution fails, raises CoreError with reason="reexec_failed".

    Returns True if already running under the target seed or guard.
    """
    current = os.environ.get(env_var)
    if current == target_seed or os.environ.get(guard_var) == "1":
        return True

    env = os.environ.copy()
    env[env_var] = target_seed
    env[guard_var] = "1"

    # sys.orig_argv preserves python interpreter flags and -m invocations
    cmd = [sys.executable] + list(sys.orig_argv[1:])

    if sys.platform == "win32":
        try:
            res = subprocess.run(cmd, env=env)
        except Exception as exc:
            raise CoreError(
                f"Failed to re-execute process with {env_var}={target_seed}: {exc}",
                reason="reexec_failed",
            ) from exc
        sys.exit(res.returncode)
    else:
        try:
            os.execv(sys.executable, cmd)
        except Exception as exc:
            raise CoreError(
                f"Failed to execv process with {env_var}={target_seed}: {exc}",
                reason="reexec_failed",
            ) from exc
        sys.exit(1)

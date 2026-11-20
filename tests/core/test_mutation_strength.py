# implements: TASK-107
"""Hand-written mutation battery for ectt.core (TASK-107, tests only).

No product code is changed. Each mutant is a hand-written copy of one
critical core function with a single seeded fault, executed in isolation.
The battery asserts (1) the real implementation satisfies every case and
(2) every mutant is killed by at least one case — the behaviour the suite
pins down detects the fault class. A kill-rate report is printed by the
summary test.

Mutant selection: canonical text normalisation, canonical float
representation, and stable-id framing are the byte-level contracts every
persisted artifact depends on (TOOL-NFR-060 family); a silent fault in any
of them changes artifacts without changing their shape.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from ectt.core.determinism import canonical_float_repr, canonical_text, stable_id

EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


@dataclass(frozen=True)
class Case:
    case_id: str
    run: Callable[[Any], Any]
    expect: Any


def _killed(case: Case, impl: Any) -> bool:
    try:
        actual = case.run(impl)
    except Exception:
        # The real implementation does not raise on these cases; a mutant
        # that raises is detected.
        return True
    return actual != case.expect


# --- canonical_text mutants ------------------------------------------------------------
# Real contract: normalise CRLF and lone CR to LF, strip trailing whitespace
# per line, trim trailing blank lines, guarantee exactly one trailing newline.


def _m1_text_lone_cr_kept(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    lines = [line.rstrip(" \t") for line in normalized.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def _m2_text_trailing_ws_kept(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def _m3_text_blank_lines_kept(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" \t") for line in normalized.split("\n")]
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def _m4_text_no_final_newline(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" \t") for line in normalized.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return ""
    return "\n".join(lines)


CASES_TEXT = [
    Case("crlf", lambda t: t("a\r\nb"), "a\nb\n"),
    Case("lone_cr", lambda t: t("a\rb"), "a\nb\n"),
    Case("trailing_ws", lambda t: t("a \nb\t\n"), "a\nb\n"),
    Case("trailing_blank_lines", lambda t: t("a\n\n\n"), "a\n"),
    Case("no_final_newline", lambda t: t("a"), "a\n"),
    Case("empty", lambda t: t(""), ""),
    Case("whitespace_only", lambda t: t("  \n\n"), ""),
]


# --- canonical_float_repr mutants ------------------------------------------------------


def _m5_float_drops_neg_zero(val: float) -> str:
    if math.isnan(val):
        return "NaN"
    if math.isinf(val):
        return "-Infinity" if val < 0.0 else "Infinity"
    if val == 0.0:
        return "0.0"
    return repr(val)


def _m6_float_inf_sign_swapped(val: float) -> str:
    if math.isnan(val):
        return "NaN"
    if math.isinf(val):
        return "Infinity" if val < 0.0 else "-Infinity"
    if val == 0.0:
        return "-0.0" if math.copysign(1.0, val) < 0.0 else "0.0"
    return repr(val)


def _m7_float_nan_lowercase(val: float) -> str:
    if math.isnan(val):
        return "nan"
    if math.isinf(val):
        return "-Infinity" if val < 0.0 else "Infinity"
    if val == 0.0:
        return "-0.0" if math.copysign(1.0, val) < 0.0 else "0.0"
    return repr(val)


CASES_FLOAT = [
    Case("shortest_roundtrip", lambda f: f(0.1), "0.1"),
    Case("neg_zero", lambda f: f(-0.0), "-0.0"),
    Case("pos_zero", lambda f: f(0.0), "0.0"),
    Case("nan", lambda f: f(float("nan")), "NaN"),
    Case("pos_inf", lambda f: f(float("inf")), "Infinity"),
    Case("neg_inf", lambda f: f(float("-inf")), "-Infinity"),
]


# --- stable_id mutants -----------------------------------------------------------------


def _part_bytes(part: Any) -> bytes:
    if isinstance(part, bytes):
        return part
    if isinstance(part, str):
        return part.encode("utf-8")
    if isinstance(part, bool):
        return b"1" if part else b"0"
    if isinstance(part, int):
        return str(part).encode("ascii")
    if isinstance(part, float):
        return repr(part).encode("ascii")
    if isinstance(part, Path):
        return part.as_posix().encode("utf-8")
    return str(part).encode("utf-8")


def _m8_id_no_length_framing(*parts: Any) -> str:
    hasher = hashlib.sha256()
    for part in parts:
        hasher.update(_part_bytes(part))
    return hasher.hexdigest()


def _m9_id_path_name_only(*parts: Any) -> str:
    hasher = hashlib.sha256()
    for part in parts:
        b = _part_bytes(part)
        if isinstance(part, Path):
            b = part.name.encode("utf-8")
        hasher.update(f"{len(b)}:".encode("ascii"))
        hasher.update(b)
    return hasher.hexdigest()


CASES_ID = [
    Case("framing_disambiguates", lambda f: f("ab", "c") != f("a", "bc"), True),
    Case("deterministic", lambda f: f("x") == f("x"), True),
    Case("path_posix_canonical", lambda f: f(Path("x/a.txt")) == f("x/a.txt"), True),
    Case("bytes_str_equivalence", lambda f: f(b"abc") == f("abc"), True),
    Case("empty_parts_sha256", lambda f: f(), EMPTY_SHA256),
]


MUTANTS: list[tuple[str, Any, list[Case]]] = [
    ("canonical_text/M1-lone-cr-kept", _m1_text_lone_cr_kept, CASES_TEXT),
    ("canonical_text/M2-trailing-ws-kept", _m2_text_trailing_ws_kept, CASES_TEXT),
    ("canonical_text/M3-blank-lines-kept", _m3_text_blank_lines_kept, CASES_TEXT),
    ("canonical_text/M4-no-final-newline", _m4_text_no_final_newline, CASES_TEXT),
    ("canonical_float_repr/M5-neg-zero-dropped", _m5_float_drops_neg_zero, CASES_FLOAT),
    ("canonical_float_repr/M6-inf-sign-swapped", _m6_float_inf_sign_swapped, CASES_FLOAT),
    ("canonical_float_repr/M7-nan-lowercase", _m7_float_nan_lowercase, CASES_FLOAT),
    ("stable_id/M8-length-framing-removed", _m8_id_no_length_framing, CASES_ID),
    ("stable_id/M9-path-name-only", _m9_id_path_name_only, CASES_ID),
]


def test_real_implementations_pass_the_battery() -> None:
    """The battery itself must accept the real implementations unchanged."""
    real: list[tuple[Any, list[Case]]] = [
        (canonical_text, CASES_TEXT),
        (canonical_float_repr, CASES_FLOAT),
        (stable_id, CASES_ID),
    ]
    for impl, cases in real:
        for case in cases:
            assert not _killed(case, impl), f"battery case {case.case_id} rejects the real implementation"


@pytest.mark.parametrize(("mutant_id", "impl", "cases"), MUTANTS, ids=[m[0] for m in MUTANTS])
def test_mutant_is_killed(mutant_id: str, impl: Any, cases: list[Case]) -> None:
    detections = [c.case_id for c in cases if _killed(c, impl)]
    assert detections, f"mutant {mutant_id} SURVIVED the battery — add a test that kills it"


def test_kill_rate_report(capsys: pytest.CaptureFixture[str]) -> None:
    killed = 0
    lines: list[str] = []
    for mutant_id, impl, cases in MUTANTS:
        detections = [c.case_id for c in cases if _killed(c, impl)]
        if detections:
            killed += 1
            lines.append(f"{mutant_id}: KILLED by {', '.join(detections)}")
        else:
            lines.append(f"{mutant_id}: SURVIVED")
    rate = killed / len(MUTANTS) if MUTANTS else 1.0
    print("\nectt.core mutation kill-rate report\n" + "\n".join(lines))
    print(f"kill rate: {killed}/{len(MUTANTS)} ({rate:.0%})")
    captured = capsys.readouterr()
    assert "SURVIVED" not in captured.out
    assert rate == 1.0

# implements: TOOL-PAR-060, DSN-ANA-030
"""Tests for call graph extraction and callee classification (WP-ANA-03, TASK-008).

Fixtures cover: direct call, static function, recursion, function-pointer call,
call to an undeclared function, a macro-wrapped call, and a call into a system header.
The 1.2 reader rules and the 1.3 reader gate are also exercised.

Verifies: TOOL-PAR-060, DSN-ANA-030.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from ectt.ana.errors import AnalysisModelError
from ectt.ana.frontend import parse
from ectt.ana.interface import extract_interfaces
from ectt.ana.model import CallModel
from ectt.ana.persist import assemble_analysis_model, read_analysis_model
from ectt.core.determinism import FixedClock

CALL_FIXTURE = b"""#include <vendor/vendor.h>
extern int ext_fn(int);
#define CALL(x) helper(x)
static int helper(int a) { return a; }
int rec(int n) { if (n <= 0) return 0; return rec(n - 1); }
int (*fp)(int);
int driver(int v) {
  int r = helper(v);
  r += vendor_fn(v);
  r += ext_fn(v);
  r += fp(v);
  r += CALL(v);
  r += undeclared_fn(v);
  return r + rec(v);
}
"""


@pytest.fixture
def sysdir(tmp_path: Path) -> Path:
    """A directory passed with -isystem so its header is classified as a system header."""
    vendor = tmp_path / "sys" / "vendor"
    vendor.mkdir(parents=True)
    (vendor / "vendor.h").write_text("int vendor_fn(int);\n", encoding="utf-8")
    return tmp_path / "sys"


def _extract(sysdir: Path, code: bytes = CALL_FIXTURE, name: str = "cg.c") -> Any:
    ptu = parse(name, args=["-std=gnu89", "-isystem", str(sysdir)], unsaved_files=[(name, code)])
    assert ptu.status == "parsed", [str(d) for d in ptu.diagnostics]
    return extract_interfaces(ptu)


def _calls_of(unit: Any, fn_name: str) -> list[CallModel]:
    fn = {f.name: f for f in unit.functions}[fn_name]
    return list(fn.calls)


def test_direct_call_to_unit_function_is_internal(sysdir: Path) -> None:
    """verifies: TOOL-PAR-060 — a callee defined in the unit is classified internal."""
    calls = _calls_of(_extract(sysdir), "driver")

    helper_calls = [c for c in calls if c.callee == "helper"]
    assert helper_calls, calls
    assert all(c.classification == "internal" and c.via == "direct" for c in helper_calls)


def test_static_callee_is_internal(sysdir: Path) -> None:
    """verifies: TOOL-PAR-060 — a file-static callee is still an in-unit (internal) callee."""
    unit = _extract(sysdir)
    static_fn = {f.name: f for f in unit.functions}["helper"]
    assert static_fn.storage_class == "static"

    assert any(c.callee == "helper" and c.classification == "internal" for c in _calls_of(unit, "driver"))


def test_recursive_call_recorded_as_internal_direct(sysdir: Path) -> None:
    """verifies: TOOL-PAR-060 — self-recursion is a direct internal call on the function itself."""
    calls = _calls_of(_extract(sysdir), "rec")

    assert calls == [CallModel(callee="rec", classification="internal", via="direct", line=5)]


def test_function_pointer_call_is_unresolved_never_guessed(sysdir: Path) -> None:
    """verifies: TOOL-PAR-060 — an indirect call is unresolved with an empty callee, not guessed."""
    calls = _calls_of(_extract(sysdir), "driver")

    indirect = [c for c in calls if c.via == "function_pointer"]
    assert len(indirect) == 1
    assert indirect[0].callee == ""
    assert indirect[0].classification == "unresolved"
    assert indirect[0].line == 11


def test_undeclared_callee_is_unresolved_undeclared(sysdir: Path) -> None:
    """verifies: TOOL-PAR-060 — a call to an undeclared function is unresolved, not external."""
    calls = _calls_of(_extract(sysdir), "driver")

    undeclared = [c for c in calls if c.via == "undeclared"]
    assert undeclared == [CallModel(callee="undeclared_fn", classification="unresolved", via="undeclared", line=13)]


def test_macro_wrapped_call_is_recorded_at_its_line(sysdir: Path) -> None:
    """verifies: TOOL-PAR-060 — a call expanded from a macro is still recorded, at the use site."""
    calls = _calls_of(_extract(sysdir), "driver")

    assert any(c.callee == "helper" and c.line == 12 and c.classification == "internal" for c in calls)


def test_system_header_callee_is_library_and_declared_callee_is_external(sysdir: Path) -> None:
    """verifies: TOOL-PAR-060 — system-header callees are library; other declarations are external."""
    calls = _calls_of(_extract(sysdir), "driver")

    by_callee = {c.callee: c for c in calls if c.via == "direct"}
    assert by_callee["vendor_fn"].classification == "library"
    assert by_callee["ext_fn"].classification == "external"


def test_calls_are_sorted_by_line(sysdir: Path) -> None:
    """verifies: TOOL-PAR-060 — call lists are ordered by source position."""
    lines = [c.line for c in _calls_of(_extract(sysdir), "driver")]

    assert lines == sorted(lines)


def test_two_runs_are_byte_identical(sysdir: Path) -> None:
    """verifies: TOOL-PAR-060, DSN-ANA-030 — extraction is deterministic across runs."""
    first = _extract(sysdir).to_json()
    second = _extract(sysdir).to_json()

    assert first == second
    assert '"via": "function_pointer"' in first


def _assembled_doc(sysdir: Path, tmp_path: Path) -> dict[str, Any]:
    unit = _extract(sysdir)
    model = assemble_analysis_model(
        [unit],
        clock=FixedClock("2026-11-18T00:00:00Z"),
        input_digests={"cg.c": "0" * 64},
        tool_version="test",
        front_end="libclang",
    )
    return model.to_dict()


def test_schema_1_3_document_round_trips(sysdir: Path, tmp_path: Path) -> None:
    """verifies: TOOL-PAR-060 — a 1.3 document with calls reads back with the same call sites."""
    doc = _assembled_doc(sysdir, tmp_path)
    assert doc["schema_version"] == "1.3"

    reloaded = read_analysis_model(doc)

    fn = {f.name: f for f in reloaded.units[0].functions}["driver"]
    assert fn.calls == tuple(_calls_of(_extract(sysdir), "driver"))


def test_schema_1_2_document_without_calls_still_reads(sysdir: Path, tmp_path: Path) -> None:
    """verifies: TOOL-PAR-060 — 1.2 reader rules hold: a 1.2 document without calls[] loads with none."""
    doc = copy.deepcopy(_assembled_doc(sysdir, tmp_path))
    doc["schema_version"] = "1.2"
    for unit in doc["units"]:
        for fn in unit["functions"]:
            del fn["calls"]

    reloaded = read_analysis_model(doc)

    assert all(f.calls == () for u in reloaded.units for f in u.functions)


def test_schema_1_3_missing_calls_is_rejected(sysdir: Path, tmp_path: Path) -> None:
    """verifies: TOOL-PAR-060 — a 1.3 document must carry calls[] on every function (fail-closed)."""
    doc = copy.deepcopy(_assembled_doc(sysdir, tmp_path))
    del doc["units"][0]["functions"][0]["calls"]

    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(doc)
    assert exc_info.value.reason == "missing_calls"


def test_schema_1_3_unknown_call_value_is_rejected(sysdir: Path, tmp_path: Path) -> None:
    """verifies: TOOL-PAR-060 — an unknown classification value is rejected, never interpreted."""
    doc = copy.deepcopy(_assembled_doc(sysdir, tmp_path))
    driver = next(f for f in doc["units"][0]["functions"] if f["name"] == "driver")
    driver["calls"][0]["classification"] = "maybe_internal"

    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(doc)
    assert exc_info.value.reason == "unknown_call_value"

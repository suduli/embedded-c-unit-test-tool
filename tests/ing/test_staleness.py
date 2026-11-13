# implements: DSN-ING-060
"""Tests for content-based, fail-closed staleness detection.

Verifies: TOOL-ING-090, TOOL-ING-100, DSN-ING-060 — including the shadowing
and __has_include invalidation fixtures.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from ectt.ing import load_compdb
from ectt.ing.errors import StalenessError
from ectt.ing.staleness import (
    assert_fresh,
    capture_staleness_inputs,
    check_staleness,
)


def _make_project(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A minimal project: compdb, one source, one include dir with a header.

    Returns (compdb_path, include_dir, source_file).
    """
    src = tmp_path / "src"
    inc = tmp_path / "include"
    build = tmp_path / "build"
    src.mkdir(parents=True)
    inc.mkdir()
    build.mkdir()
    (src / "adc.c").write_text(
        '#include "adc.h"\nint adc(void) { return 1; }\n', encoding="utf-8"
    )
    (inc / "adc.h").write_text("#pragma once\n", encoding="utf-8")
    compdb = build / "compile_commands.json"
    compdb.write_text(
        json.dumps([
            {
                "directory": str(build),
                "file": str(src / "adc.c"),
                "arguments": [
                    "gcc",
                    "-I",
                    str(inc),
                    "-c",
                    str(src / "adc.c"),
                ],
            }
        ]),
        encoding="utf-8",
    )
    return compdb, inc, src / "adc.c"


def _capture_project(compdb: Path):
    from ectt.ing import load_compdb

    db = load_compdb(compdb)
    return capture_staleness_inputs(db, compdb_path=compdb)


def test_fresh_when_nothing_changed(tmp_path: Path) -> None:
    """verifies: TOOL-ING-100, DSN-ING-060 — identical state is not stale."""
    compdb, _inc, _src = _make_project(tmp_path)
    cap1 = _capture_project(compdb)
    cap2 = _capture_project(compdb)
    report = check_staleness(cap1, cap2)
    assert not report.stale
    assert report.reasons == ()
    assert_fresh(report)  # no raise


def test_stale_when_source_content_changed_same_mtime(tmp_path: Path) -> None:
    """verifies: TOOL-ING-100 — staleness is content-based, not mtime-based:
    the modified source keeps its original mtime and is still detected."""
    compdb, _inc, src = _make_project(tmp_path)
    cap1 = _capture_project(compdb)
    original_stat = src.stat()
    src.write_text('#include "adc.h"\nint adc(void) { return 2; }\n', encoding="utf-8")
    os.utime(src, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    cap2 = _capture_project(compdb)
    report = check_staleness(cap1, cap2)
    assert report.stale
    assert "source_changed" in report.reasons
    assert src.as_posix() in report.changed_paths
    with pytest.raises(StalenessError) as excinfo:
        assert_fresh(report)
    assert "source_changed" in excinfo.value.reasons


def test_stale_when_shadowing_header_created_then_fresh_after_revert(
    tmp_path: Path,
) -> None:
    """verifies: TOOL-ING-100 — creating a header in an earlier include dir
    shadows the same-named header in a later dir and marks the model stale;
    removing it restores freshness."""
    compdb, inc, _src = _make_project(tmp_path)
    inc_b = tmp_path / "include_b"
    inc_b.mkdir()
    (inc_b / "feature.h").write_text("#pragma once\n", encoding="utf-8")
    data = json.loads(compdb.read_text(encoding="utf-8"))
    data[0]["arguments"] = [
        "gcc",
        "-I",
        str(inc),
        "-I",
        str(inc_b),
        "-c",
        str(Path(data[0]["file"])),
    ]
    compdb.write_text(json.dumps(data), encoding="utf-8")
    base = _capture_project(compdb)
    assert not check_staleness(base, _capture_project(compdb)).stale

    shadow = inc / "feature.h"  # earlier dir: shadows include_b/feature.h
    shadow.write_text("#pragma once\n", encoding="utf-8")
    report = check_staleness(base, _capture_project(compdb))
    assert report.stale
    assert "include_surface_changed" in report.reasons

    shadow.unlink()  # revert: resolution goes back to include_b's header
    restored = _capture_project(compdb)
    assert not check_staleness(base, restored).stale


def test_stale_when_has_include_outcome_changes(tmp_path: Path) -> None:
    """verifies: TOOL-ING-100 — a header whose appearance changes __has_include
    outcomes on the include surface marks the model stale."""
    compdb, inc, _src = _make_project(tmp_path)
    base = _capture_project(compdb)
    assert not check_staleness(base, _capture_project(compdb)).stale

    (inc / "opt_feature.h").write_text("#pragma once\n", encoding="utf-8")
    report = check_staleness(base, _capture_project(compdb))
    assert report.stale
    assert "include_surface_changed" in report.reasons


def test_stale_when_response_file_changed(tmp_path: Path) -> None:
    """verifies: TOOL-ING-100, TOOL-ING-210 — a changed response file marks the
    model stale."""
    build = tmp_path / "build"
    build.mkdir()
    rsp = tmp_path / "flags.rsp"
    rsp.write_text("-DVERSION=1", encoding="utf-8")
    src = tmp_path / "x.c"
    src.write_text("int x(void) { return 0; }\n", encoding="utf-8")
    compdb = build / "compile_commands.json"
    compdb.write_text(
        json.dumps([
            {
                "directory": str(tmp_path),
                "file": str(src),
                "arguments": ["gcc", "@flags.rsp", "-c", str(src)],
            }
        ]),
        encoding="utf-8",
    )
    base = _capture_project(compdb)
    assert not check_staleness(base, _capture_project(compdb)).stale

    rsp.write_text("-DVERSION=2", encoding="utf-8")
    report = check_staleness(base, _capture_project(compdb))
    assert report.stale
    assert "response_file_changed" in report.reasons


def test_stale_when_compdb_changed(tmp_path: Path) -> None:
    """verifies: TOOL-ING-100 — a changed ingested configuration definition is
    detected via the compdb content digest."""
    compdb, _inc, _src = _make_project(tmp_path)
    base = _capture_project(compdb)
    data = json.loads(compdb.read_text(encoding="utf-8"))
    data[0]["arguments"].insert(1, "-O2")
    compdb.write_text(json.dumps(data), encoding="utf-8")
    report = check_staleness(base, _capture_project(compdb))
    assert report.stale
    assert "compdb_changed" in report.reasons


def test_stale_when_source_missing(tmp_path: Path) -> None:
    """verifies: TOOL-ING-100 — a vanished source is fail-closed stale."""
    compdb, _inc, src = _make_project(tmp_path)
    base = _capture_project(compdb)
    src.unlink()
    report = check_staleness(base, _capture_project(compdb))
    assert report.stale
    assert "source_missing" in report.reasons


def test_unknown_include_surface_forces_stale(tmp_path: Path) -> None:
    """verifies: TOOL-ING-100 — an include surface that cannot be enumerated
    within bounds is unknown, and unknown forces re-ingest (no warn path)."""
    compdb, inc, _src = _make_project(tmp_path)
    (inc / "feature.h").write_text("#pragma once\n", encoding="utf-8")
    db = load_compdb(compdb)
    bounded = capture_staleness_inputs(db, compdb_path=compdb, max_include_surface_files=1)
    assert bounded.include_surface_digest is None
    assert bounded.unknown_include_surface
    report = check_staleness(bounded, capture_staleness_inputs(
        db, compdb_path=compdb, max_include_surface_files=1
    ))
    assert report.stale
    assert "include_surface_unknown" in report.reasons


def test_assert_fresh_carries_reasons_and_paths(tmp_path: Path) -> None:
    """verifies: TOOL-ING-100 — StalenessError carries machine-readable reasons
    and changed paths."""
    compdb, _inc, src = _make_project(tmp_path)
    base = _capture_project(compdb)
    src.write_text("int other(void) { return 3; }\n", encoding="utf-8")
    report = check_staleness(base, _capture_project(compdb))
    with pytest.raises(StalenessError) as excinfo:
        assert_fresh(report)
    assert excinfo.value.reasons == report.reasons
    assert excinfo.value.changed_paths == report.changed_paths
    assert "source_changed" in excinfo.value.reasons

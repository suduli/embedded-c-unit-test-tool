"""Tests for the WP-TCM-01 C-authored test case surface.

Covers: registration of C sources that include the generated harness header,
named-error rejection of sources that do not, registry discipline, and
deterministic listing.

Verifies: TOOL-TCD-010.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.core.fs import CoreError
from ectt.tcm import (
    CSourceTestCase,
    DuplicateTestCaseError,
    InvalidTestCaseError,
    NotAgainstHarnessError,
    TcmError,
    UnknownTestCaseError,
    register_c_source,
)
from ectt.tcm import (
    TestCaseReadError as TcmReadError,
)
from ectt.tcm import (
    TestCaseSet as TcmCaseSet,
)

HARNESS_HEADER = "uut.harness.h"

CASE_SOURCE = """\
#include "uut.harness.h"

static void test_compute_adds(void) {
    ectt_run_setup();
    int result = compute(2, 3);
    ectt_run_teardown();
    (void)result;
}
"""


def _write_case(tmp_path: Path, text: str = CASE_SOURCE, name: str = "test_add.c") -> Path:
    source = tmp_path / name
    source.write_text(text, encoding="utf-8")
    return source


def test_c_source_case_registers_and_is_retrievable(tmp_path: Path) -> None:
    """verifies: TOOL-TCD-010"""
    source = _write_case(tmp_path)
    case = register_c_source("add_two_plus_three", source, HARNESS_HEADER)
    assert case.case_id == "add_two_plus_three"
    assert case.source_path == source.as_posix()
    assert case.harness_header == HARNESS_HEADER

    cases = TcmCaseSet()
    registered = cases.register_source("add_two_plus_three", source, HARNESS_HEADER)
    assert cases.lookup("add_two_plus_three") == registered


def test_source_without_harness_include_is_rejected(tmp_path: Path) -> None:
    """verifies: TOOL-TCD-010"""
    source = _write_case(tmp_path, 'int main(void) { return 0; }\n', "plain.c")
    with pytest.raises(NotAgainstHarnessError) as excinfo:
        register_c_source("plain", source, HARNESS_HEADER)
    assert "uut.harness.h" in str(excinfo.value)


def test_source_including_a_different_header_is_rejected(tmp_path: Path) -> None:
    """verifies: TOOL-TCD-010"""
    source = _write_case(
        tmp_path, '#include "other.h"\nint main(void) { return 0; }\n', "other_case.c"
    )
    with pytest.raises(NotAgainstHarnessError):
        register_c_source("other", source, HARNESS_HEADER)


def test_missing_source_file_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-TCD-010"""
    with pytest.raises(TcmReadError):
        register_c_source("ghost", tmp_path / "absent.c", HARNESS_HEADER)


def test_directory_as_source_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-TCD-010"""
    directory = tmp_path / "src-dir.c"
    directory.mkdir()
    with pytest.raises(TcmReadError):
        register_c_source("dir", directory, HARNESS_HEADER)


def test_blank_identifier_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-TCD-010"""
    source = _write_case(tmp_path)
    with pytest.raises(InvalidTestCaseError):
        register_c_source("   ", source, HARNESS_HEADER)
    with pytest.raises(InvalidTestCaseError):
        register_c_source("ok", source, "")


def test_duplicate_identifier_rejected(tmp_path: Path) -> None:
    """verifies: TOOL-TCD-010"""
    cases = TcmCaseSet()
    cases.register_source("dup", _write_case(tmp_path, name="a.c"), HARNESS_HEADER)
    with pytest.raises(DuplicateTestCaseError):
        cases.register_source("dup", _write_case(tmp_path, name="b.c"), HARNESS_HEADER)


def test_same_source_under_two_identifiers_is_allowed(tmp_path: Path) -> None:
    """verifies: TOOL-TCD-010"""
    source = _write_case(tmp_path)
    cases = TcmCaseSet()
    cases.register_source("case_one", source, HARNESS_HEADER)
    cases.register_source("case_two", source, HARNESS_HEADER)
    assert cases.list_ids() == ("case_one", "case_two")


def test_unknown_identifier_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-TCD-010"""
    cases = TcmCaseSet()
    cases.register_source("known", _write_case(tmp_path), HARNESS_HEADER)
    with pytest.raises(UnknownTestCaseError):
        cases.lookup("unknown")


def test_listing_is_deterministic(tmp_path: Path) -> None:
    """verifies: TOOL-TCD-010"""
    cases = TcmCaseSet()
    for letter in "zab":
        cases.register_source(
            f"case_{letter}", _write_case(tmp_path, name=f"{letter}.c"), HARNESS_HEADER
        )
    assert cases.list_ids() == ("case_a", "case_b", "case_z")


def test_register_model_without_file_access() -> None:
    """verifies: TOOL-TCD-010"""
    cases = TcmCaseSet()
    case = CSourceTestCase(
        case_id="prevalidated",
        source_path="src/test_x.c",
        harness_header=HARNESS_HEADER,
    )
    cases.register_model(case)
    assert cases.lookup("prevalidated") == case
    assert len(cases) == 1


def test_register_model_rejects_blank_identifier() -> None:
    """verifies: TOOL-TCD-010"""
    cases = TcmCaseSet()
    with pytest.raises(InvalidTestCaseError):
        cases.register_model(
            CSourceTestCase(case_id="", source_path="s.c", harness_header=HARNESS_HEADER)
        )


def test_error_hierarchy_derives_from_core_error() -> None:
    """verifies: TOOL-TCD-010"""
    for cls in (
        TcmError,
        InvalidTestCaseError,
        TcmReadError,
        NotAgainstHarnessError,
        DuplicateTestCaseError,
        UnknownTestCaseError,
    ):
        assert issubclass(cls, CoreError)

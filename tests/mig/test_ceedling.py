# implements: TOOL-MIG-020
"""Ceedling project import (WP-MIG-02).

Verifies: TOOL-MIG-020 (preserve test cases and configuration), with the
no-silent-loss discipline of TOOL-MIG-040 and the no-interference rule of
TOOL-MIG-070.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.mig import import_ceedling_project
from ectt.mig.ceedling import strip_c_comments_and_strings
from ectt.mig.coexistence import assert_no_interference, snapshot_tree
from ectt.mig.errors import MigError

PROJECT_YML = """\
---
:project:
  :build_root: build
  :use_exceptions: FALSE
  :test_file_prefix: test_
:paths:
  :test:
    - +:test/**
    - -:test/support
  :source:
    - src/**
  :include:
    - inc/**
:defines:
  :test:
    - TEST
    - UNIT_TEST_BUILD
:unity:
  :defines:
    - UNITY_INCLUDE_DOUBLE
:plugins:
  :enabled:
    - gcov
:custom_vendor_section:
  :answer: forty-two
"""

TEST_ADC = """\
#include "unity.h"
#include "adc.h"

/* void test_commented_out(void) { } */
// void test_line_commented(void) { }

void setUp(void) {}
void tearDown(void) {}

void test_adc_zero_reads_zero(void)
{
    TEST_ASSERT_EQUAL_INT(0, adc_scale(0));
}

static void test_adc_full_scale(void)
{
    const char *text = "void test_in_string(void)";
    TEST_ASSERT_EQUAL_INT(4095, adc_scale(4095));
}
"""

TEST_PARAM = """\
#include "unity.h"

TEST_CASE(1, 2)
TEST_CASE(3, 4)
void test_adds(int a, int b) { }

void test_plain(void) { }
void test_plain(void) { }
"""


def _make_project(root: Path) -> Path:
    (root / "test" / "support").mkdir(parents=True)
    (root / "test" / "sub").mkdir()
    (root / "src").mkdir()
    (root / "project.yml").write_text(PROJECT_YML, encoding="utf-8")
    (root / "test" / "test_adc.c").write_text(TEST_ADC, encoding="utf-8")
    (root / "test" / "sub" / "test_param.c").write_text(TEST_PARAM, encoding="utf-8")
    (root / "test" / "support" / "test_excluded.c").write_text("void test_excluded(void) {}\n", encoding="utf-8")
    (root / "test" / "helper.c").write_text("void test_not_a_test_file(void) {}\n", encoding="utf-8")
    (root / "src" / "adc.c").write_text("int adc_scale(int x) { return x; }\n", encoding="utf-8")
    return root


@pytest.fixture
def project(tmp_path: Path) -> Path:
    return _make_project(tmp_path / "ceed")


def test_test_cases_are_preserved_in_source_order_with_lines(project: Path) -> None:
    imported = import_ceedling_project(project)

    by_path = {f.path: f for f in imported.test_files}
    assert sorted(by_path) == ["test/sub/test_param.c", "test/test_adc.c"]
    adc = by_path["test/test_adc.c"]
    assert [(t.name, t.line) for t in adc.tests] == [("test_adc_zero_reads_zero", 10), ("test_adc_full_scale", 15)]
    assert imported.test_count == 4


def test_commented_and_string_tests_are_not_found(project: Path) -> None:
    names = {t.name for f in import_ceedling_project(project).test_files for t in f.tests}
    assert not names & {"test_commented_out", "test_line_commented", "test_in_string", "test_excluded"}
    assert "test_not_a_test_file" not in names


def test_configuration_is_preserved_including_unknown_sections(project: Path) -> None:
    imported = import_ceedling_project(project)

    assert imported.config[":custom_vendor_section"] == {":answer": "forty-two"}
    assert imported.config[":defines"] == {":test": ["TEST", "UNIT_TEST_BUILD"]}
    assert imported.config[":project"][":build_root"] == "build"
    assert imported.config[":plugins"] == {":enabled": ["gcov"]}


def test_config_digest_tracks_content(project: Path) -> None:
    first = import_ceedling_project(project).config_digest
    (project / "project.yml").write_text(PROJECT_YML.replace("UNIT_TEST_BUILD", "OTHER"), encoding="utf-8")
    assert import_ceedling_project(project).config_digest != first


def test_unconverted_constructs_are_reported_with_locations(project: Path) -> None:
    notes = {(n.kind, n.location) for n in import_ceedling_project(project).unconverted}

    assert ("parameterised_test_attribute", "test/sub/test_param.c:3") in notes
    assert ("parameterised_test_attribute", "test/sub/test_param.c:4") in notes
    assert ("duplicate_test_name", "test/sub/test_param.c:8") in notes


def test_external_config_and_missing_paths_are_reported(tmp_path: Path) -> None:
    root = tmp_path / "p"
    root.mkdir()
    (root / "project.yml").write_text(":import:\n  - other.yml\n:paths:\n  :test:\n    - nowhere\n", encoding="utf-8")

    kinds = {n.kind for n in import_ceedling_project(root).unconverted}

    assert {"external_config_not_followed", "path_matches_nothing"} <= kinds


def test_project_without_test_paths_is_reported_not_silent(tmp_path: Path) -> None:
    root = tmp_path / "p"
    root.mkdir()
    (root / "project.yml").write_text(":project:\n  :build_root: b\n", encoding="utf-8")

    imported = import_ceedling_project(root)

    assert imported.test_files == ()
    assert [n.kind for n in imported.unconverted] == ["no_test_paths"]


def test_import_never_modifies_the_ceedling_tree(project: Path) -> None:
    before = snapshot_tree(project)
    import_ceedling_project(project)
    assert_no_interference(before, snapshot_tree(project), context="ceedling import")


def test_import_is_deterministic(project: Path) -> None:
    assert import_ceedling_project(project).to_dict() == import_ceedling_project(project).to_dict()


def test_test_ids_and_digests_are_stable_across_roots(tmp_path: Path) -> None:
    first = import_ceedling_project(_make_project(tmp_path / "one"))
    second = import_ceedling_project(_make_project(tmp_path / "two"))
    assert first.to_dict() == second.to_dict()
    ids = [t.test_id for f in first.test_files for t in f.tests]
    assert len(ids) == len(set(ids)) == 4


def test_crlf_sources_report_the_same_lines(project: Path) -> None:
    path = project / "test" / "test_adc.c"
    path.write_bytes(TEST_ADC.replace("\n", "\r\n").encode("utf-8"))

    adc = next(f for f in import_ceedling_project(project).test_files if f.path == "test/test_adc.c")

    assert [t.line for t in adc.tests] == [10, 15]


def test_missing_project_file_is_refused(tmp_path: Path) -> None:
    with pytest.raises(MigError) as excinfo:
        import_ceedling_project(tmp_path)
    assert excinfo.value.reason == "no_project_file"


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("- just\n- a list\n", "invalid_project_file"),
        (":a: &x 1\n:b: *x\n", "invalid_project_file"),
        (":a: [unclosed\n", "invalid_project_file"),
        ("", "invalid_project_file"),
    ],
)
def test_unimportable_project_files_are_refused(tmp_path: Path, text: str, reason: str) -> None:
    (tmp_path / "project.yml").write_text(text, encoding="utf-8")
    with pytest.raises(MigError) as excinfo:
        import_ceedling_project(tmp_path)
    assert excinfo.value.reason == reason


def test_test_paths_escaping_the_project_are_refused(tmp_path: Path) -> None:
    (tmp_path / "project.yml").write_text(":paths:\n  :test:\n    - ../outside\n", encoding="utf-8")
    with pytest.raises(MigError) as excinfo:
        import_ceedling_project(tmp_path)
    assert excinfo.value.reason == "path_escape"


def test_non_utf8_project_file_is_refused(tmp_path: Path) -> None:
    (tmp_path / "project.yml").write_bytes(b":a: \xff\xfe\n")
    with pytest.raises(MigError) as excinfo:
        import_ceedling_project(tmp_path)
    assert excinfo.value.reason == "invalid_encoding"


def test_non_utf8_test_source_is_decoded_and_reported(project: Path) -> None:
    (project / "test" / "test_latin.c").write_bytes(b"/* caf\xe9 */\nvoid test_latin(void) { }\n")

    imported = import_ceedling_project(project)

    latin = next(f for f in imported.test_files if f.path == "test/test_latin.c")
    assert [t.name for t in latin.tests] == ["test_latin"]
    assert any(n.kind == "non_utf8_source" and n.location == "test/test_latin.c" for n in imported.unconverted)


def test_custom_prefix_and_extension_are_honoured(tmp_path: Path) -> None:
    (tmp_path / "t").mkdir()
    (tmp_path / "project.yml").write_text(
        ":project:\n  :test_file_prefix: check_\n:extension:\n  :source: cc\n:paths:\n  :test:\n    - t\n",
        encoding="utf-8",
    )
    (tmp_path / "t" / "check_a.cc").write_text("void test_a(void) {}\n", encoding="utf-8")
    (tmp_path / "t" / "test_b.c").write_text("void test_b(void) {}\n", encoding="utf-8")

    imported = import_ceedling_project(tmp_path)

    assert [f.path for f in imported.test_files] == ["t/check_a.cc"]


def test_strip_keeps_line_structure_and_handles_unterminated_input() -> None:
    src = 'a /* x\ny */ b\n"str\nc // tail\n/* open'
    out = strip_c_comments_and_strings(src)
    assert out.count("\n") == src.count("\n")
    assert "str" not in out
    assert "tail" not in out

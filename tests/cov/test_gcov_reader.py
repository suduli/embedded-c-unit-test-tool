# implements: TOOL-COV-010, TOOL-COV-020
"""gcov JSON reader (WP-COV-01): documented-format fixtures, fail-closed errors.

Fixtures follow the GCC gcov documentation key-for-key; there is no C compiler
on this machine, so real GCC output has not been checked (ADR-004).
"""

from __future__ import annotations

import gzip
import json
from copy import deepcopy
from typing import Any

import pytest

from ectt.cov.errors import CoverageParseError
from ectt.cov.gcov import read_gcov_document
from ectt.cov.model import GcovDocument
from tests.cov import (
    GCOV_V1_MINIMAL,
    GCOV_V2_WITH_BRANCHES_AND_CONDITIONS,
    gcov_json,
)


def test_documented_v2_fixture_parses() -> None:
    doc = read_gcov_document(gcov_json(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS))
    assert isinstance(doc, GcovDocument)
    assert doc.format_version == "2"
    assert doc.gcc_version.startswith("14.")
    assert doc.data_file.endswith("adc.gcda")
    assert doc.current_working_directory == "/build/proj"
    (file,) = doc.files
    assert file.file == "adc.c"
    assert [line.line_number for line in file.lines] == [6, 8, 10, 12]


def test_version_1_document_without_conditions_loads() -> None:
    """A version-1 document (GCC 9-10: no calls, no conditions) is accepted."""
    doc = read_gcov_document(gcov_json(GCOV_V1_MINIMAL))
    assert doc.format_version == "1"
    (file,) = doc.files
    assert all(line.branches == () and line.conditions == () for line in file.lines)


def test_unknown_top_level_and_line_keys_are_ignored() -> None:
    """Additive keys the reader does not model are ignored, never interpreted."""
    payload = deepcopy(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    payload["future_top_level_field"] = {"anything": True}
    payload["files"][0]["lines"][0]["calls"] = [
        {"destination_block_id": 9, "returned": 2, "source_block_id": 3}
    ]
    payload["files"][0]["lines"][0]["block_ids"] = [3]
    doc = read_gcov_document(payload)
    (file,) = doc.files
    assert file.lines[0].line_number == 6


def test_gzipped_document_loads() -> None:
    """GCC >= 14 emits gzip-compressed JSON; compressed input is accepted."""
    compressed = gzip.compress(gcov_json(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS).encode("utf-8"))
    doc = read_gcov_document(compressed)
    assert doc.data_file.endswith("adc.gcda")


def test_raw_text_bytes_and_mapping_inputs_agree() -> None:
    text = gcov_json(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    from_text = read_gcov_document(text)
    from_bytes = read_gcov_document(text.encode("utf-8"))
    from_mapping = read_gcov_document(deepcopy(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS))
    assert from_text.to_json_bytes() == from_bytes.to_json_bytes() == from_mapping.to_json_bytes()


def test_unknown_format_version_is_refused() -> None:
    payload = deepcopy(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    payload["format_version"] = "3"
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document(payload)
    assert exc_info.value.reason == "unknown_format_version"


def test_invalid_json_is_refused() -> None:
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document("{not json")
    assert exc_info.value.reason == "invalid_json"


def test_non_object_root_is_refused() -> None:
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document("[]")
    assert exc_info.value.reason == "not_an_object"


@pytest.mark.parametrize(
    "key",
    ["format_version", "gcc_version", "data_file", "files"],
)
def test_missing_required_root_key_is_refused(key: str) -> None:
    payload = deepcopy(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    del payload[key]
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document(payload)
    assert exc_info.value.reason == "missing_or_invalid_key"


def test_missing_lines_array_is_refused() -> None:
    payload = deepcopy(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    del payload["files"][0]["lines"]
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document(payload)
    assert exc_info.value.reason == "missing_or_invalid_key"


def test_negative_count_is_refused() -> None:
    payload = deepcopy(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    payload["files"][0]["lines"][0]["count"] = -1
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document(payload)
    assert exc_info.value.reason == "missing_or_invalid_key"


def test_duplicate_line_number_is_refused() -> None:
    payload = deepcopy(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    duplicate = deepcopy(payload["files"][0]["lines"][0])
    payload["files"][0]["lines"].append(duplicate)
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document(payload)
    assert exc_info.value.reason == "duplicate_line"


def test_condition_covered_above_count_is_refused() -> None:
    payload = deepcopy(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    payload["files"][0]["lines"][2]["conditions"][0]["covered"] = 9
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document(payload)
    assert exc_info.value.reason == "covered_above_count"


def test_condition_terms_must_be_non_negative_integers() -> None:
    payload = deepcopy(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    payload["files"][0]["lines"][2]["conditions"][0]["not_covered_true"] = [0, -2]
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document(payload)
    assert exc_info.value.reason == "invalid_optional_key"


def test_branch_and_condition_records_are_carried() -> None:
    doc = read_gcov_document(gcov_json(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS))
    (file,) = doc.files
    branch_line = file.lines[1]
    assert len(branch_line.branches) == 2
    branch = branch_line.branches[0]
    assert branch.count == 1
    assert branch.fallthrough is True
    assert branch.throw is False
    assert branch.source_block_id == 3
    assert branch.destination_block_id == 5
    condition_line = file.lines[2]
    (condition,) = condition_line.conditions
    assert condition.count == 4
    assert condition.covered == 2
    assert condition.not_covered_true == (0, 1)
    assert condition.not_covered_false == ()


def test_dump_is_canonical_and_byte_identical() -> None:
    first = read_gcov_document(gcov_json(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS))
    second = read_gcov_document(gcov_json(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS))
    assert first.to_json_bytes() == second.to_json_bytes()
    doc: dict[str, Any] = json.loads(first.to_json_bytes().decode("utf-8"))
    assert next(iter(doc.keys())) == "schema_version"

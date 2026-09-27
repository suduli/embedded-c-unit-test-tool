# implements: DSN-PRJ-010, DSN-PRJ-030
"""Tests for ectt.prj.yaml_adapter (Restricted YAML adapter and deterministic emitter).

Verifies: TOOL-PRJ-010, TOOL-PRJ-020, TOOL-PRJ-050, TOOL-SEC-070, DSN-PRJ-010, DSN-PRJ-030, DSN-SEC-060.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from ectt.prj.errors import (
    AnchorForbiddenError,
    DuplicateKeyError,
    EmptyDocumentError,
    MergeKeyForbiddenError,
    MultiDocumentForbiddenError,
    NonStringKeyError,
    NotAMappingError,
    TagForbiddenError,
    YamlSyntaxError,
)
from ectt.prj.yaml_adapter import RestrictedYamlAdapter, detect_yaml_comments


def test_yaml_typing_hazards_roundtrip() -> None:
    """verifies: TOOL-PRJ-010, TOOL-PRJ-050, DSN-PRJ-010, DSN-PRJ-030 (SDD-003 §10).

    Verifies that all YAML typing hazards ('NO', 'on', 'yes', 'null', '~', '1.10',
    '0x1F', '1e3', '010', '.inf', '1.2.3', empty string) parse strictly as strings
    and round-trip as exact strings without type coercion.
    """
    adapter = RestrictedYamlAdapter()

    hazards = {
        "no_val": "NO",
        "on_val": "on",
        "yes_val": "yes",
        "null_val": "null",
        "tilde_val": "~",
        "float_hazard": "1.10",
        "hex_hazard": "0x1F",
        "sci_hazard": "1e3",
        "octal_hazard": "010",
        "inf_hazard": ".inf",
        "version_hazard": "1.2.3",
        "empty_hazard": "",
        "bool_true": "true",
        "bool_false": "false",
    }

    doc = {
        "schema_version": "1",
        "hazards": hazards,
    }

    # 1. Dump to YAML string
    emitted = adapter.dump(doc)

    # 2. Parse emitted YAML
    loaded = adapter.load(emitted)

    # 3. Verify all values in loaded document are strings and match exact inputs
    for key, expected_val in hazards.items():
        loaded_val = loaded["hazards"][key]
        assert isinstance(loaded_val, str), f"Expected str for {key}, got {type(loaded_val)}"
        assert loaded_val == expected_val, f"Value mismatch for {key}: {loaded_val!r} != {expected_val!r}"

    # 4. Verify unquoted YAML input with hazards also loads strictly as strings
    raw_yaml_unquoted = (
        "schema_version: 1\n"
        "hazards:\n"
        "  no_val: NO\n"
        "  on_val: on\n"
        "  yes_val: yes\n"
        "  null_val: null\n"
        "  tilde_val: ~\n"
        "  float_hazard: 1.10\n"
        "  hex_hazard: 0x1F\n"
        "  sci_hazard: 1e3\n"
        "  octal_hazard: 010\n"
        "  inf_hazard: .inf\n"
        "  version_hazard: 1.2.3\n"
    )

    loaded_raw = adapter.load(raw_yaml_unquoted)
    for key, expected_val in hazards.items():
        if key in loaded_raw["hazards"]:
            val = loaded_raw["hazards"][key]
            assert isinstance(val, str)
            assert val == expected_val


def test_reject_anchors_and_aliases() -> None:
    """verifies: TOOL-SEC-070, DSN-SEC-060"""
    adapter = RestrictedYamlAdapter()

    # Anchor definition
    yaml_with_anchor = (
        'schema_version: "1"\n'
        'base: &my_anchor "value"\n'
        'ref: "other"\n'
    )
    with pytest.raises(AnchorForbiddenError) as exc_info:
        adapter.load(yaml_with_anchor)
    assert exc_info.value.line == 2
    assert "anchor" in exc_info.value.message.lower()

    # Alias usage
    yaml_with_alias = (
        'schema_version: "1"\n'
        'base: "value"\n'
        'ref: *my_anchor\n'
    )
    with pytest.raises(AnchorForbiddenError) as exc_info:
        adapter.load(yaml_with_alias)
    assert exc_info.value.line == 3
    assert "alias" in exc_info.value.message.lower()


def test_reject_explicit_tags() -> None:
    """verifies: TOOL-SEC-070, DSN-SEC-060"""
    adapter = RestrictedYamlAdapter()

    cases = [
        ('schema_version: "1"\ncmd: !!python/object/apply:os.system ["calc"]\n', 2),
        ('schema_version: "1"\nval: !!int 123\n', 2),
        ('schema_version: "1"\nval: !!str "hello"\n', 2),
        ('schema_version: "1"\nval: !custom_tag "data"\n', 2),
    ]

    for raw, expected_line in cases:
        with pytest.raises(TagForbiddenError) as exc_info:
            adapter.load(raw)
        assert exc_info.value.line == expected_line
        assert "tag" in exc_info.value.message.lower()


def test_reject_merge_keys() -> None:
    """verifies: TOOL-SEC-070, DSN-SEC-060"""
    adapter = RestrictedYamlAdapter()

    raw = (
        'schema_version: "1"\n'
        'base: {"a": "1"}\n'
        '<<: {"b": "2"}\n'
    )
    with pytest.raises(MergeKeyForbiddenError) as exc_info:
        adapter.load(raw)
    assert exc_info.value.line == 3
    assert "<<" in exc_info.value.message


def test_reject_duplicate_mapping_keys() -> None:
    """verifies: TOOL-SEC-070, DSN-PRJ-010, DSN-SEC-060"""
    adapter = RestrictedYamlAdapter()

    raw = (
        'schema_version: "1"\n'
        'name: "first"\n'
        'name: "duplicate"\n'
    )
    with pytest.raises(DuplicateKeyError) as exc_info:
        adapter.load(raw)
    assert exc_info.value.line == 3
    assert "name" in exc_info.value.message


def test_reject_multi_document_stream() -> None:
    """verifies: TOOL-SEC-070, DSN-PRJ-010"""
    adapter = RestrictedYamlAdapter()

    raw = (
        'schema_version: "1"\n'
        'name: "doc1"\n'
        "---\n"
        'schema_version: "1"\n'
        'name: "doc2"\n'
    )
    with pytest.raises(MultiDocumentForbiddenError) as exc_info:
        adapter.load(raw)
    assert exc_info.value.line == 3


def test_reject_non_string_mapping_keys() -> None:
    """verifies: TOOL-SEC-070, DSN-PRJ-010"""
    adapter = RestrictedYamlAdapter()

    raw = (
        'schema_version: "1"\n'
        '[1, 2]: "value"\n'
    )
    with pytest.raises(NonStringKeyError) as exc_info:
        adapter.load(raw)
    assert exc_info.value.line == 2


def test_reject_empty_document_and_non_mapping() -> None:
    """verifies: TOOL-PRJ-010, DSN-PRJ-010"""
    adapter = RestrictedYamlAdapter()

    with pytest.raises(EmptyDocumentError):
        adapter.load("")

    with pytest.raises(EmptyDocumentError):
        adapter.load("   \n\n  ")

    with pytest.raises(NotAMappingError):
        adapter.load("- item1\n- item2\n")

    with pytest.raises(NotAMappingError):
        adapter.load('"just a scalar string"')


def test_syntax_error_reported_with_line() -> None:
    """verifies: TOOL-UIX-360, DSN-PRJ-010"""
    adapter = RestrictedYamlAdapter()

    raw = (
        'schema_version: "1"\n'
        'unclosed: [item1, item2\n'
    )
    with pytest.raises(YamlSyntaxError) as exc_info:
        adapter.load(raw)
    assert exc_info.value.line is not None


def test_comment_detection_and_string_false_positives() -> None:
    """verifies: TOOL-PRJ-010, DSN-PRJ-030"""
    raw = (
        'schema_version: "1" # inline comment\n'
        "# whole line comment\n"
        'description: "Fix bug #123 in ADC module"\n'
        "notes: 'Another #456 issue'\n"
        'final: "val" # trailing\n'
    )

    comments = detect_yaml_comments(raw)
    assert len(comments) == 3
    assert comments[0] == (1, 21)
    assert comments[1] == (2, 1)
    assert comments[2] == (5, 14)


def test_crlf_normalized_to_lf_on_write() -> None:
    """verifies: TOOL-PRJ-050, DSN-PRJ-030"""
    adapter = RestrictedYamlAdapter()

    crlf_input = (
        'schema_version: "1"\r\n'
        'name: "crlf_test"\r\n'
        'multiline: "line1\\r\\nline2"\r\n'
    )
    loaded = adapter.load(crlf_input)
    emitted = adapter.dump(loaded)

    assert "\r" not in emitted
    assert emitted.endswith("\n")


def test_unicode_strings_roundtrip() -> None:
    """verifies: TOOL-PRJ-010, TOOL-PRJ-050, DSN-PRJ-030"""
    adapter = RestrictedYamlAdapter()

    doc = {
        "schema_version": "1",
        "description": "Unicode test: 日本語, Café, Grüß Gott, 🚀 rocket, µV microvolts",
        "japanese": "テストケース",
    }

    emitted_bytes = adapter.dump_bytes(doc)
    assert not emitted_bytes.startswith(b"\xef\xbb\xbf")  # No UTF-8 BOM

    emitted_text = emitted_bytes.decode("utf-8")
    loaded = adapter.load(emitted_text)

    assert loaded["description"] == doc["description"]
    assert loaded["japanese"] == doc["japanese"]


def test_canonical_key_ordering() -> None:
    """verifies: TOOL-PRJ-050, DSN-PRJ-030"""
    adapter = RestrictedYamlAdapter()

    # Pass keys in arbitrary insertion order
    doc = {
        "z_key": "last",
        "settings": {"opt": "2", "arch": "arm"},
        "schema_version": "1",
        "alpha": "first",
        "name": "my_project",
    }

    emitted = adapter.dump(doc, canonical_keys=("schema_version", "name", "settings"))
    lines = [line.strip() for line in emitted.splitlines() if line.strip()]

    # schema_version must be first
    assert lines[0] == '"schema_version": "1"'
    assert lines[1] == '"name": "my_project"'
    assert lines[2] == '"settings":'
    assert lines[3] == '"arch": "arm"'
    assert lines[4] == '"opt": "2"'
    assert lines[5] == '"alpha": "first"'
    assert lines[6] == '"z_key": "last"'


def test_default_values_omitted() -> None:
    """verifies: TOOL-PRJ-050, DSN-PRJ-030"""
    adapter = RestrictedYamlAdapter()

    doc = {
        "schema_version": "1",
        "name": "proj",
        "source_roots": [],
        "output_root": "",
        "active": "true",
    }

    defaults = {
        "source_roots": [],
        "output_root": "",
    }

    emitted = adapter.dump(doc, default_values=defaults)
    assert "source_roots" not in emitted
    assert "output_root" not in emitted
    assert "name" in emitted
    assert "active" in emitted


def test_floats_emitted_via_canonical_float_repr() -> None:
    """verifies: TOOL-PRJ-050, DSN-PRJ-030"""
    adapter = RestrictedYamlAdapter()

    doc = {
        "schema_version": "1",
        "point_one": 0.1,
        "neg_zero": -0.0,
        "pos_zero": 0.0,
        "nan_val": float("nan"),
        "inf_val": float("inf"),
        "neg_inf": float("-inf"),
    }

    emitted = adapter.dump(doc)
    loaded = adapter.load(emitted)

    assert loaded["point_one"] == "0.1"
    assert loaded["neg_zero"] == "-0.0"
    assert loaded["pos_zero"] == "0.0"
    assert loaded["nan_val"] == "NaN"
    assert loaded["inf_val"] == "Infinity"
    assert loaded["neg_inf"] == "-Infinity"


def test_byte_identical_re_save() -> None:
    """verifies: TOOL-PRJ-050, DSN-PRJ-030"""
    adapter = RestrictedYamlAdapter()

    doc = {
        "schema_version": "1",
        "name": "canonical_doc",
        "nested": {
            "a": "1",
            "b": ["item1", "item2"],
        },
        "tests": [
            {"id": "tc1", "score": "0.1"},
            {"id": "tc2", "score": "0.2"},
        ],
    }

    pass1 = adapter.dump(doc)
    loaded1 = adapter.load(pass1)
    pass2 = adapter.dump(loaded1)

    assert pass1 == pass2

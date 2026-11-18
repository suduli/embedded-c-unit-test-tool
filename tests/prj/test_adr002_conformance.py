# implements: DSN-PRJ-010, DSN-PRJ-030, DSN-SEC-060
"""ADR-002 Restricted YAML conformance suite (TASK-005).

Every restricted-grammar rule named in ADR-002 maps to at least one test below.
Each test's docstring cites the ADR section it checks. The mapping:

| ADR-002 clause | Test(s) |
|---|---|
| §1.1 hazard matrix (NO, 1.10, 010, 0x1F, ~) | test_hazard_literals_load_as_strings |
| §2.1 scalars parsed as strings | test_hazard_literals_load_as_strings |
| §2.1 every scalar double-quoted on write | test_every_scalar_is_double_quoted_on_write |
| §2.1 type conversion only at the model layer | test_hazard_literals_load_as_strings |
| §2.2 single adapter, format-agnostic core | test_project_uses_single_restricted_adapter |
| §2.3 schema_version always first | test_schema_version_is_first_regardless_of_input_order |
| §2.3 canonical key order | test_keys_follow_canonical_order_after_schema_version |
| §2.3 default values omitted | test_default_values_are_omitted_on_write |
| §2.3 LF, UTF-8 no BOM, single trailing newline, no trailing spaces | test_output_bytes_are_lf_utf8_no_bom_single_newline |
| §2.3 2-space indent per nesting level | test_indentation_is_two_spaces_per_level |
| §2.3 floats via canonical_float_repr, quoted | test_floats_are_quoted_canonical_strings |
| §2.3 canonical input reproduces identical bytes | test_canonical_input_round_trips_byte_identical |
| §2.3 / §8 valid noncanonical input may normalise on save | test_noncanonical_input_normalises_on_save |
| §3.1 no executable constructs | test_no_executable_constructs_are_accepted |
| §3.2 anchors and aliases (billion-laughs) | test_alias_bomb_rejected_before_expansion |
| §3.2 merge keys | test_merge_key_rejected_with_line |
| §3.2 explicit tags | test_explicit_tags_rejected_on_scalars_and_mappings |
| §3.2 duplicate mapping keys | test_duplicate_key_rejected_with_named_error |
| §3.2 multi-document streams | test_multi_document_stream_rejected |
| §3.2 non-string mapping keys | test_non_string_key_rejected |
| §5 comment-loss rule | test_comment_loss_refused_without_discard (project-level) |
| §3 named errors carry file and line | test_rejections_carry_line_numbers |
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.prj import project as project_module
from ectt.prj.errors import (
    AnchorForbiddenError,
    CommentPreservationError,
    DuplicateKeyError,
    MergeKeyForbiddenError,
    MultiDocumentForbiddenError,
    NonStringKeyError,
    TagForbiddenError,
    YamlSyntaxError,
)
from ectt.prj.project import Project
from ectt.prj.yaml_adapter import RestrictedYamlAdapter


def _adapter() -> RestrictedYamlAdapter:
    return RestrictedYamlAdapter()


def test_hazard_literals_load_as_strings() -> None:
    """verifies: ADR-002 §1.1, §2.1 — every hazard literal stays a string after load."""
    text = (
        'schema_version: "1"\n'
        'state: "NO"\n'
        'version: "1.10"\n'
        'pin: "010"\n'
        'mask: "0x1F"\n'
        'flag: "~"\n'
    )
    loaded = _adapter().load(text)

    assert loaded == {
        "schema_version": "1",
        "state": "NO",
        "version": "1.10",
        "pin": "010",
        "mask": "0x1F",
        "flag": "~",
    }
    assert all(isinstance(v, str) for v in loaded.values())


def test_every_scalar_is_double_quoted_on_write() -> None:
    """verifies: ADR-002 §2.1 — every scalar value is emitted double-quoted."""
    data = {
        "schema_version": "1",
        "name": "adc_scope",
        "limits": {"low": 1.5, "high": True},
        "tags": ["alpha", 7],
    }
    emitted = _adapter().dump(data)

    value_lines = [line for line in emitted.splitlines() if ":" in line or line.lstrip().startswith("-")]
    assert value_lines, "expected emitted scalar lines"
    for line in value_lines:
        stripped = line.strip()
        if stripped.endswith(":"):
            continue  # mapping header, no scalar on this line
        value = stripped.split(": ", 1)[1] if ": " in stripped else stripped.lstrip("- ")
        assert value.startswith('"') and value.endswith('"'), line


def test_project_uses_single_restricted_adapter() -> None:
    """verifies: ADR-002 §2.2 — surface syntax is confined to one adapter."""
    assert project_module.RestrictedYamlAdapter is RestrictedYamlAdapter


def test_schema_version_is_first_regardless_of_input_order() -> None:
    """verifies: ADR-002 §2.3 — schema_version is always the first key emitted."""
    data = {"name": "x", "zeta": "z", "schema_version": "1", "alpha": "a"}
    emitted = _adapter().dump(data)

    assert emitted.splitlines()[0] == '"schema_version": "1"'


def test_keys_follow_canonical_order_after_schema_version() -> None:
    """verifies: ADR-002 §2.3 — keys follow the declared canonical order."""
    data = {"schema_version": "1", "c": "3", "a": "1", "b": "2"}
    emitted = _adapter().dump(data, canonical_keys=["schema_version", "b", "a"])

    keys = [line.split(":", 1)[0].strip('"') for line in emitted.splitlines()]
    assert keys == ["schema_version", "b", "a", "c"]


def test_default_values_are_omitted_on_write() -> None:
    """verifies: ADR-002 §2.3 — default values are omitted on write."""
    data = {"schema_version": "1", "mode": "off", "name": "n"}
    emitted = _adapter().dump(data, default_values={"mode": "off"})

    assert "mode" not in emitted
    assert '"name": "n"' in emitted


def test_output_bytes_are_lf_utf8_no_bom_single_newline() -> None:
    """verifies: ADR-002 §2.3 — LF endings, UTF-8 without BOM, one trailing newline."""
    data = {"schema_version": "1", "label": "héllo ✓"}
    raw = _adapter().dump_bytes(data)

    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    for line in raw.decode("utf-8").split("\n"):
        assert line == line.rstrip(), f"trailing whitespace: {line!r}"
    assert "héllo ✓".encode() in raw


def test_indentation_is_two_spaces_per_level() -> None:
    """verifies: ADR-002 §2.3 — fixed two-space indentation per nesting level."""
    data = {"schema_version": "1", "outer": {"inner": {"leaf": "v"}}}
    emitted = _adapter().dump(data)

    assert '"outer":\n  "inner":\n    "leaf": "v"\n' in emitted


def test_floats_are_quoted_canonical_strings() -> None:
    """verifies: ADR-002 §2.3 — floats via canonical_float_repr, emitted quoted."""
    emitted = _adapter().dump({"schema_version": "1", "gain": 0.1, "zero": -0.0})

    assert '"gain": "0.1"' in emitted
    assert '"zero": "-0.0"' in emitted
    loaded = _adapter().load(emitted)
    assert loaded["gain"] == "0.1"


def test_canonical_input_round_trips_byte_identical() -> None:
    """verifies: ADR-002 §2.3 — canonical input reloads and re-emits identical bytes."""
    adapter = _adapter()
    first = adapter.dump_bytes({"schema_version": "1", "a": "x", "nested": {"k": "v"}})

    second = adapter.dump_bytes(adapter.load(first.decode("utf-8")))

    assert second == first


def test_noncanonical_input_normalises_on_save() -> None:
    """verifies: ADR-002 §2.3, §8 — valid noncanonical input may normalise on save."""
    adapter = _adapter()
    noncanonical = 'name: "x"\nschema_version: "1"\n'
    normalised = adapter.dump_bytes(adapter.load(noncanonical))

    assert normalised.startswith(b'"schema_version": "1"\n')
    assert normalised != noncanonical.encode("utf-8")


def test_no_executable_constructs_are_accepted() -> None:
    """verifies: ADR-002 §3.1 — configuration is data: a plain-looking expression stays a string."""
    loaded = _adapter().load('schema_version: "1"\nexpr: "${os.system(x)}"\ninclude: "other.yaml"\n')

    assert loaded["expr"] == "${os.system(x)}"
    assert loaded["include"] == "other.yaml"


def test_alias_bomb_rejected_before_expansion() -> None:
    """verifies: ADR-002 §3.2 — alias-expansion denial of service is refused at the first alias."""
    bomb = (
        'schema_version: "1"\n'
        'a: &a ["x", "x", "x", "x", "x", "x", "x", "x", "x"]\n'
        'b: &b [*a, *a, *a, *a, *a, *a, *a, *a, *a]\n'
        'c: &c [*b, *b, *b, *b, *b, *b, *b, *b, *b]\n'
    )
    with pytest.raises(AnchorForbiddenError) as exc_info:
        _adapter().load(bomb)
    assert exc_info.value.line == 2


def test_merge_key_rejected_with_line() -> None:
    """verifies: ADR-002 §3.2 — merge keys are refused."""
    text = 'schema_version: "1"\nbase: {k: "v"}\nderived:\n  <<: "base"\n'
    with pytest.raises(MergeKeyForbiddenError) as exc_info:
        _adapter().load(text)
    assert exc_info.value.line is not None


def test_explicit_tags_rejected_on_scalars_and_mappings() -> None:
    """verifies: ADR-002 §3.2 — explicit tags are refused on scalars and mappings."""
    scalar_tag = 'schema_version: "1"\nnum: !!int "5"\n'
    mapping_tag = 'schema_version: "1"\nobj: !custom {k: "v"}\n'
    for text in (scalar_tag, mapping_tag):
        with pytest.raises(TagForbiddenError):
            _adapter().load(text)


def test_duplicate_key_rejected_with_named_error() -> None:
    """verifies: ADR-002 §3.2 — duplicate mapping keys are refused, not silently overwritten."""
    text = 'schema_version: "1"\nname: "a"\nname: "b"\n'
    with pytest.raises(DuplicateKeyError) as exc_info:
        _adapter().load(text)
    assert exc_info.value.line == 3


def test_multi_document_stream_rejected() -> None:
    """verifies: ADR-002 §3.2 — exactly one document per file."""
    text = 'schema_version: "1"\n---\nschema_version: "1"\n'
    with pytest.raises(MultiDocumentForbiddenError):
        _adapter().load(text)


def test_non_string_key_rejected() -> None:
    """verifies: ADR-002 §3.2 — non-string mapping keys are refused."""
    # Scalar key `1` is a string under ADR-002 §2.1; only compound keys are forbidden.
    with pytest.raises(NonStringKeyError):
        _adapter().load('schema_version: "1"\n? [a, b]\n: "v"\n')


def test_rejections_carry_line_numbers() -> None:
    """verifies: ADR-002 §3 — named errors specify the file and line."""
    text = 'schema_version: "1"\nname: "a"\n: broken: [\n'
    with pytest.raises(YamlSyntaxError) as exc_info:
        _adapter().load(text, path="scope.yaml")
    assert exc_info.value.line is not None
    assert "scope.yaml" in str(exc_info.value)


def test_comment_loss_refused_without_discard(tmp_path: Path) -> None:
    """verifies: ADR-002 §5 — overwriting a commented file raises unless discard_comments=True."""
    project = Project.create(tmp_path / "proj")
    target = tmp_path / "proj" / "scopes" / "s.scope"
    target.parent.mkdir(parents=True)
    target.write_text('schema_version: "1"\n# rationale\nname: "a"\n', encoding="utf-8")

    with pytest.raises(CommentPreservationError):
        project.save_file("scopes/s.scope", {"schema_version": "1", "name": "b"})
    assert "rationale" in target.read_text(encoding="utf-8")

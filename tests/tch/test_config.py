"""Tests for the WP-TCH-01 declarative compiler configuration format.

Covers: full-format loading, add-a-compiler-by-file-only (no tool source
change), duplicate/unknown registry handling, deterministic listing, and the
named-error surface for every malformed shape the validator knows about.

Verifies: TOOL-PLG-020, TOOL-TCH-020.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ectt.tch import (
    CONFIG_SCHEMA_VERSION,
    KNOWN_COVERAGE_KINDS,
    CompilerConfig,
    CompilerConfigReadError,
    CompilerConfigRegistry,
    ConfigSchemaVersionError,
    DuplicateCompilerConfigError,
    InvalidCompilerConfigError,
    TchError,
    UnknownCompilerConfigError,
    UnknownCoverageKindError,
    load_compiler_config,
    validate_compiler_config_document,
)

FULL_CONFIG = """\
schema_version: 1
name: acme-gcc
family: gcc
invocation:
  executable: gcc
  compile_only_flag: "-c"
  output_flag: "-o"
  default_output: a.out
flags:
  debug: ["-g", "-O0"]
  optimization:
    none: ["-O0"]
    speed: ["-O2"]
output:
  object_suffix: ".o"
  executable_suffix: ""
coverage:
  kinds: [line, branch]
  flags:
    line: ["--coverage"]
    branch: ["--coverage"]
"""


def _write_config(tmp_path: Path, text: str, name: str = "cfg.yaml") -> Path:
    config_path = tmp_path / name
    config_path.write_text(text, encoding="utf-8")
    return config_path


def test_full_config_loads_with_every_field() -> None:
    """verifies: TOOL-TCH-020"""
    config = validate_compiler_config_document(
        yaml.safe_load(FULL_CONFIG)
    )
    assert config.name == "acme-gcc"
    assert config.family == "gcc"
    assert config.invocation.executable == "gcc"
    assert config.invocation.compile_only_flag == "-c"
    assert config.invocation.output_flag == "-o"
    assert config.invocation.default_output == "a.out"
    assert config.debug_flags == ("-g", "-O0")
    assert config.optimization_flags["speed"] == ("-O2",)
    assert config.output.object_suffix == ".o"
    assert config.output.executable_suffix == ""
    assert config.coverage_kinds == {"line", "branch"}
    assert config.coverage_flags["line"] == ("--coverage",)


def test_defaults_apply_when_optional_invocation_fields_absent() -> None:
    """verifies: TOOL-TCH-020"""
    minimal = (
        "schema_version: 1\n"
        "name: min\n"
        "family: gcc\n"
        "invocation:\n"
        "  executable: cc1\n"
        "flags:\n"
        "  debug: []\n"
        "  optimization: {}\n"
        "output:\n"
        "  object_suffix: '.o'\n"
        "  executable_suffix: ''\n"
        "coverage:\n"
        "  kinds: [line]\n"
        "  flags:\n"
        "    line: ['--coverage']\n"
    )
    config = validate_compiler_config_document(yaml.safe_load(minimal))
    assert config.invocation.compile_only_flag == "-c"
    assert config.invocation.output_flag == "-o"
    assert config.invocation.default_output == "a.out"
    assert config.debug_flags == ()
    assert config.optimization_flags == {}


def test_add_compiler_requires_only_a_yaml_file(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-020"""
    config_path = _write_config(tmp_path, FULL_CONFIG, "my-compiler.yaml")
    registry = CompilerConfigRegistry()
    registry.register(load_compiler_config(config_path))
    assert registry.lookup("acme-gcc").family == "gcc"
    assert registry.list_names() == ("acme-gcc",)


def test_duplicate_name_rejected() -> None:
    """verifies: TOOL-PLG-020"""
    registry = CompilerConfigRegistry()
    first = validate_compiler_config_document(yaml.safe_load(FULL_CONFIG))
    second = validate_compiler_config_document(yaml.safe_load(FULL_CONFIG))
    registry.register(first)
    with pytest.raises(DuplicateCompilerConfigError):
        registry.register(second)


def test_unknown_name_rejected() -> None:
    """verifies: TOOL-PLG-020"""
    registry = CompilerConfigRegistry()
    with pytest.raises(UnknownCompilerConfigError):
        registry.lookup("nope")


def test_listing_is_deterministic() -> None:
    """verifies: TOOL-TCH-020"""
    registry = CompilerConfigRegistry()
    for letter in "zab":
        config = validate_compiler_config_document(
            yaml.safe_load(FULL_CONFIG.replace("acme-gcc", f"c-{letter}"))
        )
        registry.register(config)
    assert registry.list_names() == ("c-a", "c-b", "c-z")


def test_missing_file_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-020"""
    with pytest.raises(CompilerConfigReadError):
        load_compiler_config(tmp_path / "absent.yaml")


def test_directory_as_config_file_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-PLG-020"""
    directory = tmp_path / "not-a-file.yaml"
    directory.mkdir()
    with pytest.raises(CompilerConfigReadError):
        load_compiler_config(directory)


def test_invalid_yaml_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-TCH-020"""
    config_path = _write_config(tmp_path, "schema_version: [1\n  broken")
    with pytest.raises(InvalidCompilerConfigError):
        load_compiler_config(config_path)


def test_empty_file_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-TCH-020"""
    config_path = _write_config(tmp_path, "")
    with pytest.raises(InvalidCompilerConfigError):
        load_compiler_config(config_path)


def test_non_mapping_document_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    with pytest.raises(InvalidCompilerConfigError):
        validate_compiler_config_document(["not", "a", "mapping"])


def test_missing_schema_version_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    del document["schema_version"]
    with pytest.raises(ConfigSchemaVersionError):
        validate_compiler_config_document(document)


def test_unsupported_schema_version_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    document["schema_version"] = CONFIG_SCHEMA_VERSION + 1
    with pytest.raises(ConfigSchemaVersionError):
        validate_compiler_config_document(document)


def test_boolean_schema_version_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    document["schema_version"] = True
    with pytest.raises(ConfigSchemaVersionError):
        validate_compiler_config_document(document)


@pytest.mark.parametrize(
    "field", ["name", "family", "invocation", "flags", "output", "coverage"]
)
def test_missing_required_field_rejected(field: str) -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    del document[field]
    with pytest.raises(InvalidCompilerConfigError):
        validate_compiler_config_document(document)


def test_blank_name_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    document["name"] = "   "
    with pytest.raises(InvalidCompilerConfigError):
        validate_compiler_config_document(document)


def test_blank_executable_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    document["invocation"]["executable"] = ""
    with pytest.raises(InvalidCompilerConfigError):
        validate_compiler_config_document(document)


def test_empty_kinds_list_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    document["coverage"]["kinds"] = []
    with pytest.raises(InvalidCompilerConfigError):
        validate_compiler_config_document(document)


def test_unknown_coverage_kind_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    document["coverage"]["kinds"] = ["line", "psychic"]
    with pytest.raises(UnknownCoverageKindError) as excinfo:
        validate_compiler_config_document(document)
    assert "psychic" in str(excinfo.value)


def test_kind_vocabulary_is_the_documented_set() -> None:
    """verifies: TOOL-TCH-020"""
    assert {"line", "branch", "condition", "decision", "mcdc"} == KNOWN_COVERAGE_KINDS


def test_kind_without_flags_entry_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    document["coverage"]["kinds"] = ["line", "branch"]
    del document["coverage"]["flags"]["branch"]
    with pytest.raises(InvalidCompilerConfigError):
        validate_compiler_config_document(document)


def test_flag_entry_for_undeclared_kind_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    document["coverage"]["flags"]["mcdc"] = ["--coverage"]
    with pytest.raises(InvalidCompilerConfigError):
        validate_compiler_config_document(document)


def test_empty_kind_flag_list_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    document["coverage"]["flags"]["line"] = []
    with pytest.raises(InvalidCompilerConfigError):
        validate_compiler_config_document(document)


def test_non_string_flag_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    document["flags"]["debug"] = ["-g", 3]
    with pytest.raises(InvalidCompilerConfigError):
        validate_compiler_config_document(document)


def test_non_list_flag_field_rejected() -> None:
    """verifies: TOOL-TCH-020"""
    document = yaml.safe_load(FULL_CONFIG)
    document["flags"]["debug"] = "-g"
    with pytest.raises(InvalidCompilerConfigError):
        validate_compiler_config_document(document)


def test_error_hierarchy_derives_from_core_error() -> None:
    """verifies: TOOL-TCH-020"""
    from ectt.core.fs import CoreError

    for cls in (
        TchError,
        CompilerConfigReadError,
        InvalidCompilerConfigError,
        ConfigSchemaVersionError,
        UnknownCoverageKindError,
        DuplicateCompilerConfigError,
        UnknownCompilerConfigError,
    ):
        assert issubclass(cls, CoreError)


def test_to_dict_is_deterministic() -> None:
    """verifies: TOOL-TCH-020"""
    config = validate_compiler_config_document(yaml.safe_load(FULL_CONFIG))
    assert config.to_dict() == config.to_dict()
    assert isinstance(config, CompilerConfig)

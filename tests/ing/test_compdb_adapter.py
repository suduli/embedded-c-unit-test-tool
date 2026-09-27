# implements: DSN-ING-010
"""Tests for compilation database adapter and parser.

Verifies: TOOL-ING-010, TOOL-ING-020, TOOL-ING-030, DSN-ING-010.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ectt.ing.compdb_adapter import (
    CompDbAdapter,
    extract_compiler_flags,
    load_compdb,
    parse_command_to_arguments,
    parse_compdb,
)
from ectt.ing.errors import (
    CommandParseError,
    CompilationDatabaseFormatError,
    CompilationDatabaseNotFoundError,
    MissingCommandOrArgumentsError,
    MissingEntryKeyError,
)
from ectt.prj.errors import InvalidRelativePathError, ProjectConfinementError


def test_command_string_happy_path() -> None:
    """verifies: TOOL-ING-010, TOOL-ING-020, TOOL-ING-030, DSN-ING-010"""
    json_data = [
        {
            "directory": "/home/developer/project/build",
            "file": "src/adc.c",
            "command": "gcc -Wall -Wextra -I../include -I../src -DDEBUG -DCHANNELS=4 -std=c99 -O2 -c ../src/adc.c -o adc.o",
            "output": "adc.o",
        }
    ]
    raw_json = json.dumps(json_data)
    db = parse_compdb(raw_json)

    assert len(db) == 1
    tu = db[0]

    assert tu.source_path == "src/adc.c"
    assert tu.working_directory == "/home/developer/project/build"
    assert tu.compiler == "gcc"
    assert tu.language_standard == "c99"
    assert tu.output_file == "adc.o"

    # Extracted include paths
    assert tu.include_paths == ("../include", "../src")

    # Extracted defines
    assert tu.preprocessor_definitions == ("DEBUG", "CHANNELS=4")
    assert tu.definitions_map == {"DEBUG": None, "CHANNELS": "4"}

    # Residual flags
    assert tu.residual_flags == ("-Wall", "-Wextra", "-O2", "-c")


def test_arguments_array_happy_path() -> None:
    """verifies: TOOL-ING-010, TOOL-ING-020, TOOL-ING-030, DSN-ING-010"""
    json_data = [
        {
            "directory": "E:/firmware/build",
            "file": "drivers/uart.c",
            "arguments": [
                "arm-none-eabi-gcc",
                "-mcpu=cortex-m4",
                "-mthumb",
                "-I",
                "../include",
                "-isystem",
                "/toolchain/arm-none-eabi/include",
                "-D",
                "STM32F407xx",
                "-D",
                "BAUD=115200",
                "-std=gnu11",
                "-c",
                "drivers/uart.c",
                "-o",
                "drivers/uart.o",
            ],
        }
    ]
    raw_json = json.dumps(json_data)
    db = parse_compdb(raw_json)

    assert len(db) == 1
    tu = db[0]

    assert tu.source_path == "drivers/uart.c"
    assert tu.working_directory == "E:/firmware/build"
    assert tu.compiler == "arm-none-eabi-gcc"
    assert tu.language_standard == "gnu11"
    assert tu.output_file == "drivers/uart.o"

    # Extracted include paths
    assert tu.include_paths == ("../include", "/toolchain/arm-none-eabi/include")

    # Extracted defines
    assert tu.preprocessor_definitions == ("STM32F407xx", "BAUD=115200")
    assert tu.definitions_map == {"STM32F407xx": None, "BAUD": "115200"}

    # Residual flags
    assert tu.residual_flags == ("-mcpu=cortex-m4", "-mthumb", "-c")


def test_command_and_arguments_normalize_to_identical_shape() -> None:
    """verifies: TOOL-ING-020, DSN-ING-010"""
    # The same translation unit specified via command string and arguments array
    entry_cmd = {
        "directory": "/workspace/build",
        "file": "src/sensor.c",
        "command": "clang -I../include -DENABLE_FILTER=1 -std=c11 -Wall -c ../src/sensor.c -o sensor.o",
    }
    entry_args = {
        "directory": "/workspace/build",
        "file": "src/sensor.c",
        "arguments": [
            "clang",
            "-I../include",
            "-DENABLE_FILTER=1",
            "-std=c11",
            "-Wall",
            "-c",
            "../src/sensor.c",
            "-o",
            "sensor.o",
        ],
    }

    db_cmd = parse_compdb(json.dumps([entry_cmd]))
    db_args = parse_compdb(json.dumps([entry_args]))

    tu_cmd = db_cmd[0]
    tu_args = db_args[0]

    assert tu_cmd.source_path == tu_args.source_path
    assert tu_cmd.working_directory == tu_args.working_directory
    assert tu_cmd.include_paths == tu_args.include_paths
    assert tu_cmd.preprocessor_definitions == tu_args.preprocessor_definitions
    assert tu_cmd.language_standard == tu_args.language_standard
    assert tu_cmd.output_file == tu_args.output_file
    assert tu_cmd.compiler == tu_args.compiler
    assert tu_cmd.residual_flags == tu_args.residual_flags


def test_project_root_path_confinement_and_normalization(tmp_path: Path) -> None:
    """verifies: TOOL-ING-030, DSN-ING-010"""
    project_root = tmp_path / "my_project"
    project_root.mkdir()
    (project_root / "src").mkdir()
    (project_root / "src" / "main.c").write_text("int main() { return 0; }", encoding="utf-8")
    (project_root / "include").mkdir()
    (project_root / "build").mkdir()

    # compile_commands with absolute paths pointing inside project root
    compdb_content = [
        {
            "directory": str(project_root / "build"),
            "file": str(project_root / "src" / "main.c"),
            "command": f"gcc -I{project_root / 'include'} -c {project_root / 'src' / 'main.c'} -o main.o",
        }
    ]
    compdb_path = project_root / "build" / "compile_commands.json"
    compdb_path.write_text(json.dumps(compdb_content), encoding="utf-8")

    db = load_compdb(compdb_path, project_root=project_root)
    tu = db[0]

    # Source path and include path normalized to project-relative POSIX format
    assert tu.source_path == "src/main.c"
    assert tu.include_paths == ("include",)
    assert tu.compiler == "gcc"


def test_reject_escaping_source_path_when_confined(tmp_path: Path) -> None:
    """verifies: TOOL-ING-030, DSN-ING-010"""
    project_root = tmp_path / "confined_project"
    project_root.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_file = outside_dir / "secret.c"
    outside_file.write_text("int secret;", encoding="utf-8")

    # Ingestion referencing outside file with project_root confinement
    compdb_content = [
        {
            "directory": str(project_root),
            "file": str(outside_file),
            "command": f"gcc -c {outside_file}",
        }
    ]
    raw_json = json.dumps(compdb_content)

    # Rejection: invalid relative path or confinement violation
    with pytest.raises((InvalidRelativePathError, ProjectConfinementError)):
        parse_compdb(raw_json, project_root=project_root)


def test_missing_compdb_file_raises_not_found(tmp_path: Path) -> None:
    """verifies: TOOL-ING-010, DSN-ING-010"""
    non_existent = tmp_path / "does_not_exist" / "compile_commands.json"
    with pytest.raises(CompilationDatabaseNotFoundError) as exc_info:
        load_compdb(non_existent)
    assert exc_info.value.reason == "compdb_not_found"


def test_malformed_json_raises_format_error() -> None:
    """verifies: TOOL-ING-010, DSN-ING-010"""
    malformed = "[{\"file\": \"test.c\", \"directory\": \"build\", ... unclosed"
    with pytest.raises(CompilationDatabaseFormatError) as exc_info:
        parse_compdb(malformed)
    assert exc_info.value.reason == "invalid_json"


def test_non_array_root_raises_format_error() -> None:
    """verifies: TOOL-ING-010, DSN-ING-010"""
    cases = [
        "{\"file\": \"test.c\"}",  # Object instead of array
        "\"a string\"",
        "12345",
        "true",
    ]
    for case in cases:
        with pytest.raises(CompilationDatabaseFormatError) as exc_info:
            parse_compdb(case)
        assert exc_info.value.reason == "root_not_an_array"


def test_empty_compdb_content_raises_format_error() -> None:
    """verifies: TOOL-ING-010, DSN-ING-010"""
    with pytest.raises(CompilationDatabaseFormatError) as exc_info:
        parse_compdb("   ")
    assert exc_info.value.reason == "empty_compdb"


def test_empty_array_returns_empty_database() -> None:
    """verifies: TOOL-ING-010, DSN-ING-010"""
    db = parse_compdb("[]")
    assert len(db) == 0
    assert list(db) == []


def test_entry_not_a_mapping_raises_format_error() -> None:
    """verifies: TOOL-ING-010, DSN-ING-010"""
    raw_json = json.dumps(["not_a_dict"])
    with pytest.raises(CompilationDatabaseFormatError) as exc_info:
        parse_compdb(raw_json)
    assert exc_info.value.reason == "entry_not_a_mapping"
    assert exc_info.value.entry_index == 0


def test_missing_directory_key_raises_named_error() -> None:
    """verifies: TOOL-ING-010, DSN-ING-010"""
    raw_json = json.dumps([{"file": "src/main.c", "command": "gcc -c src/main.c"}])
    with pytest.raises(MissingEntryKeyError) as exc_info:
        parse_compdb(raw_json)
    assert exc_info.value.reason == "missing_directory_key"
    assert exc_info.value.missing_key == "directory"


def test_missing_file_key_raises_named_error() -> None:
    """verifies: TOOL-ING-010, DSN-ING-010"""
    raw_json = json.dumps([{"directory": "build", "command": "gcc -c src/main.c"}])
    with pytest.raises(MissingEntryKeyError) as exc_info:
        parse_compdb(raw_json)
    assert exc_info.value.reason == "missing_file_key"
    assert exc_info.value.missing_key == "file"


def test_missing_command_and_arguments_raises_named_error() -> None:
    """verifies: TOOL-ING-020, DSN-ING-010"""
    raw_json = json.dumps([{"directory": "build", "file": "src/main.c"}])
    with pytest.raises(MissingCommandOrArgumentsError) as exc_info:
        parse_compdb(raw_json)
    assert exc_info.value.reason == "missing_command_or_arguments"
    assert exc_info.value.entry_file == "src/main.c"


def test_empty_arguments_array_raises_named_error() -> None:
    """verifies: TOOL-ING-020, DSN-ING-010"""
    raw_json = json.dumps([{"directory": "build", "file": "src/main.c", "arguments": []}])
    with pytest.raises(MissingCommandOrArgumentsError) as exc_info:
        parse_compdb(raw_json)
    assert exc_info.value.reason == "empty_arguments"


def test_empty_command_string_raises_named_error() -> None:
    """verifies: TOOL-ING-020, DSN-ING-010"""
    raw_json = json.dumps([{"directory": "build", "file": "src/main.c", "command": "   "}])
    with pytest.raises(MissingCommandOrArgumentsError) as exc_info:
        parse_compdb(raw_json)
    assert exc_info.value.reason == "empty_command"


def test_unclosed_quotes_in_command_raises_command_parse_error() -> None:
    """verifies: TOOL-ING-020, DSN-ING-010"""
    raw_json = json.dumps([
        {
            "directory": "build",
            "file": "src/main.c",
            "command": "gcc -DFOO=\"unclosed_quote -c src/main.c",
        }
    ])
    with pytest.raises(CommandParseError) as exc_info:
        parse_compdb(raw_json)
    assert exc_info.value.reason == "command_parse_error"


def test_determinism_repeated_parsing_identical_output() -> None:
    """verifies: TOOL-ING-010, TOOL-ING-030, DSN-ING-010"""
    raw_json = json.dumps([
        {
            "directory": "build",
            "file": "src/b.c",
            "arguments": ["gcc", "-Iinc2", "-Iinc1", "-DDEF2", "-DDEF1", "-c", "src/b.c"],
        },
        {
            "directory": "build",
            "file": "src/a.c",
            "arguments": ["gcc", "-IincA", "-DDEFA", "-c", "src/a.c"],
        },
    ])
    db1 = parse_compdb(raw_json)
    db2 = parse_compdb(raw_json)

    assert db1.to_dict() == db2.to_dict()
    assert db1.canonical_json() == db2.canonical_json()
    assert db1.source_paths == db2.source_paths == ["src/b.c", "src/a.c"]


def test_msvc_style_compiler_flags() -> None:
    """verifies: TOOL-ING-020, TOOL-ING-030, DSN-ING-010"""
    raw_json = json.dumps([
        {
            "directory": "C:/project",
            "file": "src/win.c",
            "arguments": [
                "cl.exe",
                "/Iinclude",
                "/I",
                "custom_inc",
                "/DWIN32",
                "/D",
                "BUFFER_SIZE=512",
                "/std:c17",
                "/c",
                "src/win.c",
                "/Fooutput.obj",
            ],
        }
    ])
    db = parse_compdb(raw_json)
    assert len(db) == 1
    tu = db[0]

    assert tu.compiler == "cl.exe"
    assert tu.include_paths == ("include", "custom_inc")
    assert tu.preprocessor_definitions == ("WIN32", "BUFFER_SIZE=512")
    assert tu.language_standard == "c17"
    assert tu.output_file == "output.obj"
    assert tu.residual_flags == ("/c",)


def test_extended_include_and_standard_flags() -> None:
    """verifies: TOOL-ING-030, DSN-ING-010"""
    raw_json = json.dumps([
        {
            "directory": "/build",
            "file": "src/app.c",
            "arguments": [
                "gcc",
                "-iquote",
                "quote_inc",
                "-idirafter",
                "after_inc",
                "-isystem=/sys/inc",
                "-std",
                "c11",
                "-c",
                "src/app.c",
                "-ooutput.o",
            ],
        }
    ])
    db = parse_compdb(raw_json)
    tu = db[0]

    assert tu.include_paths == ("quote_inc", "after_inc", "/sys/inc")
    assert tu.language_standard == "c11"
    assert tu.output_file == "output.o"


def test_non_array_arguments_field_raises_error() -> None:
    """verifies: TOOL-ING-020, DSN-ING-010"""
    raw_json = json.dumps([
        {
            "directory": "build",
            "file": "src/main.c",
            "arguments": "gcc -c src/main.c",  # Not a list
        }
    ])
    with pytest.raises(CompilationDatabaseFormatError) as exc_info:
        parse_compdb(raw_json)
    assert exc_info.value.reason == "arguments_not_an_array"


def test_non_string_item_in_arguments_raises_error() -> None:
    """verifies: TOOL-ING-020, DSN-ING-010"""
    raw_json = json.dumps([
        {
            "directory": "build",
            "file": "src/main.c",
            "arguments": ["gcc", 1234, "src/main.c"],
        }
    ])
    with pytest.raises(CompilationDatabaseFormatError) as exc_info:
        parse_compdb(raw_json)
    assert exc_info.value.reason == "argument_not_a_string"


def test_non_string_command_raises_error() -> None:
    """verifies: TOOL-ING-020, DSN-ING-010"""
    raw_json = json.dumps([
        {
            "directory": "build",
            "file": "src/main.c",
            "command": 999,  # Not a string
        }
    ])
    with pytest.raises(CompilationDatabaseFormatError) as exc_info:
        parse_compdb(raw_json)
    assert exc_info.value.reason == "command_not_a_string"


def test_error_string_representations() -> None:
    """verifies: TOOL-ING-010, DSN-ING-010"""
    err = MissingEntryKeyError(
        "Missing key error message",
        missing_key="file",
        path="compile_commands.json",
        entry_index=2,
        entry_file="test.c",
    )
    s = str(err)
    assert "reason=missing_entry_key" in s
    assert "path=compile_commands.json" in s
    assert "entry_index=2" in s
    assert "entry_file=test.c" in s
    assert "missing_key=file" in s


def test_compdb_read_oserror_raises_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """verifies: TOOL-ING-010, DSN-ING-010"""
    dummy_file = tmp_path / "compile_commands.json"
    dummy_file.write_text("[]", encoding="utf-8")

    def mock_read_text(*args: object, **kwargs: object) -> str:
        raise OSError("Permission denied or disk read failure")

    monkeypatch.setattr(Path, "read_text", mock_read_text)

    with pytest.raises(CompilationDatabaseNotFoundError) as exc_info:
        load_compdb(dummy_file)
    assert exc_info.value.reason == "compdb_read_error"


def test_extract_compiler_flags_empty() -> None:
    """verifies: TOOL-ING-030, DSN-ING-010"""
    includes, defs, std, inv, out = extract_compiler_flags([])
    assert includes == ()
    assert defs == ()
    assert std is None
    assert inv.executable == ""
    assert inv.arguments == ()
    assert out is None


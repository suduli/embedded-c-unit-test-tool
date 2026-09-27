# implements: DSN-ING-010
"""Compilation database adapter and parser.

Reads, normalizes, and extracts translation units from compile_commands.json.

Satisfies: TOOL-ING-010, TOOL-ING-020, TOOL-ING-030.
"""

from __future__ import annotations

import json
import os
import shlex
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ectt.ing.errors import (
    CommandParseError,
    CompilationDatabaseFormatError,
    CompilationDatabaseNotFoundError,
    MissingCommandOrArgumentsError,
    MissingEntryKeyError,
)
from ectt.ing.model import (
    CompilationDatabase,
    CompilerInvocation,
    TranslationUnit,
)
from ectt.prj.errors import ProjectConfinementError
from ectt.prj.paths import normalize_posix_path, validate_project_path


__all__ = [
    "parse_command_to_arguments",
    "extract_compiler_flags",
    "CompDbAdapter",
    "load_compdb",
    "parse_compdb",
]


def parse_command_to_arguments(command_str: str, *, posix: bool | None = None) -> list[str]:
    """Parse a single command-line string into an argument list.

    Applies platform-appropriate quoting rules (posix=True on POSIX, posix=False on Windows)
    unless explicitly overridden.

    Raises:
        CommandParseError: If quotes or escapes are malformed.
    """
    cmd = command_str.strip()
    if not cmd:
        return []

    use_posix = (os.name != "nt") if posix is None else posix

    # Validate quote balance across platforms
    in_quote: str | None = None
    i = 0
    cmd_len = len(cmd)
    while i < cmd_len:
        ch = cmd[i]
        if in_quote is not None:
            if use_posix and ch == "\\" and i + 1 < cmd_len:
                i += 2
                continue
            if not use_posix and in_quote == '"' and ch == '"' and i + 1 < cmd_len and cmd[i + 1] == '"':
                i += 2
                continue
            if ch == in_quote:
                in_quote = None
        elif ch in ('"', "'"):
            in_quote = ch
        i += 1

    if in_quote is not None:
        raise CommandParseError(
            f"Unclosed quotation mark ({in_quote}) in compile command: {command_str}",
            command=command_str,
            reason="command_parse_error",
        )

    try:
        raw_tokens = shlex.split(cmd, posix=use_posix)
    except ValueError as exc:
        raise CommandParseError(
            f"Failed to parse compile command string: {exc}",
            command=command_str,
            reason="command_parse_error",
        ) from exc

    # On Windows (posix=False), shlex keeps outer quotation marks on tokens; strip them cleanly
    if not use_posix:
        cleaned: list[str] = []
        for token in raw_tokens:
            if (token.startswith('"') and token.endswith('"')) or (
                token.startswith("'") and token.endswith("'")
            ):
                cleaned.append(token[1:-1])
            else:
                cleaned.append(token)
        return cleaned

    return raw_tokens


def extract_compiler_flags(
    args: Sequence[str],
    *,
    source_hint: str | None = None,
    directory: str | None = None,
    project_root: Path | None = None,
) -> tuple[
    tuple[str, ...],  # include_paths
    tuple[str, ...],  # preprocessor_definitions
    str | None,       # language_standard
    CompilerInvocation,
    str | None,       # output_file
]:
    """Extract includes, definitions, language standard, invocation, and output file from arguments.

    Satisfies: TOOL-ING-030.
    """
    if not args:
        inv = CompilerInvocation(executable="", arguments=(), residual_flags=())
        return (), (), None, inv, None

    executable = args[0]
    tokens = list(args[1:])

    include_paths: list[str] = []
    preprocessor_definitions: list[str] = []
    language_standard: str | None = None
    output_file: str | None = None
    residual_flags: list[str] = []

    norm_source_hint = source_hint.replace("\\", "/") if source_hint else None
    source_stem_or_name = Path(norm_source_hint).name if norm_source_hint else None

    idx = 0
    num_tokens = len(tokens)

    while idx < num_tokens:
        tok = tokens[idx]

        # 1. Output file flags: -o <file> or -o<file> or /Fo<file> or /Fo <file>
        if tok == "-o" or tok == "/Fo":
            if idx + 1 < num_tokens:
                idx += 1
                output_file = tokens[idx].strip("\"'")
            idx += 1
            continue
        elif tok.startswith("-o") and len(tok) > 2:
            output_file = tok[2:].strip("\"'")
            idx += 1
            continue
        elif tok.startswith("/Fo") and len(tok) > 3:
            output_file = tok[3:].strip("\"'")
            idx += 1
            continue

        # 2. Include path flags: -I, -isystem, -iquote, -idirafter, /I
        if tok in ("-I", "-isystem", "-iquote", "-idirafter", "/I"):
            if idx + 1 < num_tokens:
                idx += 1
                inc = tokens[idx].strip("\"'")
                include_paths.append(_normalize_path_token(inc, directory, project_root))
            idx += 1
            continue
        elif tok.startswith("-I") and len(tok) > 2:
            inc = tok[2:].strip("\"'")
            include_paths.append(_normalize_path_token(inc, directory, project_root))
            idx += 1
            continue
        elif tok.startswith("/I") and len(tok) > 2:
            inc = tok[2:].strip("\"'")
            include_paths.append(_normalize_path_token(inc, directory, project_root))
            idx += 1
            continue
        elif tok.startswith(("-isystem", "-iquote", "-idirafter")) and (
            tok.startswith("-isystem=") or tok.startswith("-iquote=") or tok.startswith("-idirafter=")
        ):
            inc = tok.split("=", 1)[1].strip("\"'")
            include_paths.append(_normalize_path_token(inc, directory, project_root))
            idx += 1
            continue

        # 3. Preprocessor definitions: -D, /D
        if tok in ("-D", "/D"):
            if idx + 1 < num_tokens:
                idx += 1
                preprocessor_definitions.append(tokens[idx].strip("\"'"))
            idx += 1
            continue
        elif tok.startswith("-D") and len(tok) > 2:
            preprocessor_definitions.append(tok[2:].strip("\"'"))
            idx += 1
            continue
        elif tok.startswith("/D") and len(tok) > 2:
            preprocessor_definitions.append(tok[2:].strip("\"'"))
            idx += 1
            continue

        # 4. Language standard: -std=<standard>, -std <standard>, /std:<standard>
        if tok == "-std":
            if idx + 1 < num_tokens:
                idx += 1
                language_standard = tokens[idx].strip("\"'")
            idx += 1
            continue
        elif tok.startswith("-std=") and len(tok) > 5:
            language_standard = tok[5:].strip("\"'")
            idx += 1
            continue
        elif tok.startswith("/std:") and len(tok) > 5:
            language_standard = tok[5:].strip("\"'")
            idx += 1
            continue

        # 5. Check if token is the source file argument itself
        tok_norm = tok.replace("\\", "/")
        if norm_source_hint is not None and (
            tok_norm == norm_source_hint
            or (directory and (Path(directory) / tok).resolve() == Path(norm_source_hint).resolve())
            or (source_stem_or_name and Path(tok_norm).name == source_stem_or_name)
        ):
            # Source file argument, skip adding to residual flags
            idx += 1
            continue

        # 6. Residual compiler flag
        residual_flags.append(tok)
        idx += 1

    invocation = CompilerInvocation(
        executable=executable,
        arguments=tuple(args),
        residual_flags=tuple(residual_flags),
    )

    norm_output = (
        _normalize_path_token(output_file, directory, project_root)
        if output_file is not None
        else None
    )

    return (
        tuple(include_paths),
        tuple(preprocessor_definitions),
        language_standard,
        invocation,
        norm_output,
    )


def _normalize_path_token(
    raw_path: str,
    directory: str | None,
    project_root: Path | None,
) -> str:
    """Normalize an include or output path token.

    If project_root is specified and the path resolves inside project_root, returns
    a POSIX relative path normalized per project store conventions. Otherwise,
    returns a clean POSIX representation with forward slashes.
    """
    clean_raw = raw_path.strip().replace("\\", "/")
    if not clean_raw:
        return ""

    if project_root is not None:
        proj_root_resolved = project_root.resolve()
        candidate = Path(clean_raw)
        if not candidate.is_absolute() and directory:
            candidate = Path(directory) / candidate

        candidate_resolved = candidate.resolve()
        if candidate_resolved.is_relative_to(proj_root_resolved):
            rel = candidate_resolved.relative_to(proj_root_resolved).as_posix()
            try:
                return validate_project_path(rel)
            except Exception:
                return rel

    # Default to POSIX format with forward slashes
    return clean_raw


class CompDbAdapter:
    """Adapter for reading and normalizing Clang JSON Compilation Databases.

    Satisfies: TOOL-ING-010, TOOL-ING-020, TOOL-ING-030.
    """

    def __init__(self, *, project_root: Path | str | None = None) -> None:
        self.project_root = Path(project_root).resolve() if project_root is not None else None

    def load(
        self,
        path: Path | str,
        *,
        project_root: Path | str | None = None,
    ) -> CompilationDatabase:
        """Load and parse compile_commands.json from the filesystem.

        Raises:
            CompilationDatabaseNotFoundError: If file does not exist.
            CompilationDatabaseFormatError: If file is malformed or invalid JSON.
            MissingEntryKeyError: If an entry is missing required keys.
            MissingCommandOrArgumentsError: If an entry lacks command or arguments.
        """
        p = Path(path)
        if not p.is_file():
            raise CompilationDatabaseNotFoundError(
                f"Compilation database not found at '{path}'",
                path=p,
                reason="compdb_not_found",
            )

        try:
            content = p.read_text(encoding="utf-8")
        except OSError as exc:
            raise CompilationDatabaseNotFoundError(
                f"Failed to read compilation database at '{path}': {exc}",
                path=p,
                reason="compdb_read_error",
            ) from exc

        return self.loads(content, project_root=project_root, source_name=str(path))

    def loads(
        self,
        content: str,
        *,
        project_root: Path | str | None = None,
        source_name: str | None = None,
    ) -> CompilationDatabase:
        """Parse compile_commands.json content from a string."""
        raw_text = content.strip()
        if not raw_text:
            raise CompilationDatabaseFormatError(
                "Compilation database content is empty",
                path=source_name,
                reason="empty_compdb",
            )

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise CompilationDatabaseFormatError(
                f"Malformed JSON in compilation database: {exc}",
                path=source_name,
                reason="invalid_json",
            ) from exc

        if not isinstance(data, list):
            raise CompilationDatabaseFormatError(
                f"Compilation database root must be a JSON array, got {type(data).__name__}",
                path=source_name,
                reason="root_not_an_array",
            )

        effective_root = (
            Path(project_root).resolve()
            if project_root is not None
            else self.project_root
        )

        translation_units: list[TranslationUnit] = []
        for idx, entry in enumerate(data):
            tu = self._normalize_entry(
                entry,
                entry_index=idx,
                project_root=effective_root,
                source_name=source_name,
            )
            translation_units.append(tu)

        return CompilationDatabase(translation_units=tuple(translation_units))

    def _normalize_entry(
        self,
        entry: Any,
        *,
        entry_index: int,
        project_root: Path | None,
        source_name: str | None,
    ) -> TranslationUnit:
        """Validate and normalize a single compilation database entry."""
        if not isinstance(entry, Mapping):
            raise CompilationDatabaseFormatError(
                f"Entry at index {entry_index} must be a JSON object, got {type(entry).__name__}",
                path=source_name,
                entry_index=entry_index,
                reason="entry_not_a_mapping",
            )

        # Validate required 'directory' key
        if "directory" not in entry or not entry["directory"]:
            raise MissingEntryKeyError(
                f"Entry at index {entry_index} is missing required 'directory' key",
                missing_key="directory",
                path=source_name,
                entry_index=entry_index,
                reason="missing_directory_key",
            )

        # Validate required 'file' key
        if "file" not in entry or not entry["file"]:
            raise MissingEntryKeyError(
                f"Entry at index {entry_index} is missing required 'file' key",
                missing_key="file",
                path=source_name,
                entry_index=entry_index,
                reason="missing_file_key",
            )

        raw_dir = str(entry["directory"]).strip()
        raw_file = str(entry["file"]).strip()

        # Parse command or arguments (TOOL-ING-020)
        has_arguments = "arguments" in entry and entry["arguments"] is not None
        has_command = "command" in entry and entry["command"] is not None

        if not has_arguments and not has_command:
            raise MissingCommandOrArgumentsError(
                f"Entry at index {entry_index} ('{raw_file}') must contain either 'command' or 'arguments'",
                path=source_name,
                entry_index=entry_index,
                entry_file=raw_file,
                reason="missing_command_or_arguments",
            )

        raw_args: list[str] = []
        if has_arguments:
            args_val = entry["arguments"]
            if not isinstance(args_val, Sequence) or isinstance(args_val, (str, bytes)):
                raise CompilationDatabaseFormatError(
                    f"Entry at index {entry_index} 'arguments' must be an array, got {type(args_val).__name__}",
                    path=source_name,
                    entry_index=entry_index,
                    reason="arguments_not_an_array",
                )
            if not args_val:
                raise MissingCommandOrArgumentsError(
                    f"Entry at index {entry_index} 'arguments' array is empty",
                    path=source_name,
                    entry_index=entry_index,
                    entry_file=raw_file,
                    reason="empty_arguments",
                )
            for a_idx, arg_item in enumerate(args_val):
                if not isinstance(arg_item, str):
                    raise CompilationDatabaseFormatError(
                        f"Entry at index {entry_index} argument {a_idx} must be a string",
                        path=source_name,
                        entry_index=entry_index,
                        reason="argument_not_a_string",
                    )
                raw_args.append(arg_item)
        else:
            # Single command string form
            cmd_val = entry["command"]
            if not isinstance(cmd_val, str):
                raise CompilationDatabaseFormatError(
                    f"Entry at index {entry_index} 'command' must be a string, got {type(cmd_val).__name__}",
                    path=source_name,
                    entry_index=entry_index,
                    reason="command_not_a_string",
                )
            if not cmd_val.strip():
                raise MissingCommandOrArgumentsError(
                    f"Entry at index {entry_index} 'command' string is empty",
                    path=source_name,
                    entry_index=entry_index,
                    entry_file=raw_file,
                    reason="empty_command",
                )
            raw_args = parse_command_to_arguments(cmd_val)
            if not raw_args:
                raise MissingCommandOrArgumentsError(
                    f"Entry at index {entry_index} 'command' yielded no arguments",
                    path=source_name,
                    entry_index=entry_index,
                    entry_file=raw_file,
                    reason="empty_command_tokens",
                )

        # Normalize source path and directory
        norm_source_path = _normalize_source_path(
            raw_file,
            raw_dir,
            project_root=project_root,
        )
        norm_working_directory = raw_dir.replace("\\", "/")

        # Extract compiler flags (TOOL-ING-030)
        (
            include_paths,
            preprocessor_definitions,
            language_standard,
            invocation,
            cli_output,
        ) = extract_compiler_flags(
            raw_args,
            source_hint=norm_source_path,
            directory=norm_working_directory,
            project_root=project_root,
        )

        # Explicit 'output' key in entry overrides or provides output_file
        output_file = cli_output
        if "output" in entry and entry["output"]:
            raw_output = str(entry["output"]).strip()
            output_file = _normalize_path_token(
                raw_output,
                norm_working_directory,
                project_root,
            )

        return TranslationUnit(
            source_path=norm_source_path,
            working_directory=norm_working_directory,
            include_paths=include_paths,
            preprocessor_definitions=preprocessor_definitions,
            compiler_invocation=invocation,
            language_standard=language_standard,
            output_file=output_file,
        )


def _normalize_source_path(
    raw_file: str,
    raw_dir: str,
    *,
    project_root: Path | None,
) -> str:
    """Normalize translation unit source path to clean POSIX format."""
    clean_file = raw_file.strip().replace("\\", "/")

    if project_root is not None:
        proj_root_resolved = project_root.resolve()
        candidate = Path(clean_file)
        if not candidate.is_absolute():
            candidate = Path(raw_dir) / candidate

        candidate_resolved = candidate.resolve()
        if not candidate_resolved.is_relative_to(proj_root_resolved):
            raise ProjectConfinementError(
                f"Source path '{raw_file}' resolves to '{candidate_resolved}', escaping project root '{proj_root_resolved}'",
                path=candidate_resolved,
            )
        rel = candidate_resolved.relative_to(proj_root_resolved).as_posix()
        return validate_project_path(rel)

    # When no project root is given
    try:
        return normalize_posix_path(clean_file)
    except Exception:
        return clean_file


def load_compdb(
    path: Path | str,
    *,
    project_root: Path | str | None = None,
) -> CompilationDatabase:
    """Convenience function to load a compilation database from file."""
    adapter = CompDbAdapter(project_root=project_root)
    return adapter.load(path)


def parse_compdb(
    content: str,
    *,
    project_root: Path | str | None = None,
    source_name: str | None = None,
) -> CompilationDatabase:
    """Convenience function to parse a compilation database from JSON string."""
    adapter = CompDbAdapter(project_root=project_root)
    return adapter.loads(content, source_name=source_name)

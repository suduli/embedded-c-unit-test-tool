# implements: DSN-ING-010, DSN-ING-020
"""ECTT Ingestion and Scope Resolver (CMP-ING).

Provides ingestion and normalization of compilation databases (compile_commands.json)
for C projects per TOOL-ING-010, TOOL-ING-020, TOOL-ING-030, and TOOL-ING-040:
- Reads and validates JSON compilation databases.
- Normalizes single-string 'command' and array 'arguments' forms to one internal shape.
- Extracts per translation unit: source path, working directory, include paths,
  preprocessor definitions, language standard, compiler invocation, and residual flags.
- Confines and normalizes project paths to relative POSIX format without escaping project bounds.
- Recommends and supports CMake export via CMAKE_EXPORT_COMPILE_COMMANDS=ON.
"""

from ectt.ing.cmake import (
    CMAKE_EXPORT_DOCUMENTATION,
    generate_compdb_via_cmake,
)
from ectt.ing.compdb_adapter import (
    CompDbAdapter,
    extract_compiler_flags,
    load_compdb,
    parse_command_to_arguments,
    parse_compdb,
)
from ectt.ing.errors import (
    CMakeConfigureError,
    CommandParseError,
    CompilationDatabaseFormatError,
    CompilationDatabaseNotFoundError,
    IngestionError,
    MissingCommandOrArgumentsError,
    MissingEntryKeyError,
)
from ectt.ing.model import (
    CompilationDatabase,
    CompilerInvocation,
    TranslationUnit,
)

__all__ = [
    # Errors
    "IngestionError",
    "CompilationDatabaseNotFoundError",
    "CompilationDatabaseFormatError",
    "MissingEntryKeyError",
    "MissingCommandOrArgumentsError",
    "CommandParseError",
    "CMakeConfigureError",
    # Models
    "CompilerInvocation",
    "TranslationUnit",
    "CompilationDatabase",
    # Adapter and parser
    "CompDbAdapter",
    "load_compdb",
    "parse_compdb",
    "parse_command_to_arguments",
    "extract_compiler_flags",
    # CMake integration
    "generate_compdb_via_cmake",
    "CMAKE_EXPORT_DOCUMENTATION",
]

# implements: DSN-ING-010
"""Data model for compilation databases and normalized translation units.

Satisfies: TOOL-ING-010, TOOL-ING-020, TOOL-ING-030.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any

from ectt.core.determinism import canonical_json

__all__ = [
    "CompilerInvocation",
    "TranslationUnit",
    "CompilationDatabase",
]


@dataclass(frozen=True)
class CompilerInvocation:
    """Normalized compiler invocation details.

    Attributes:
        executable: The compiler binary / driver (e.g. 'gcc', 'arm-none-eabi-gcc', 'clang').
        arguments: Complete normalized sequence of command-line arguments.
        residual_flags: Additional compiler flags not captured by includes, defines,
            standards, outputs, or source files (e.g. '-Wall', '-O2', '-g').
    """

    executable: str
    arguments: tuple[str, ...] = field(default_factory=tuple)
    residual_flags: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary representation."""
        return {
            "executable": self.executable,
            "arguments": list(self.arguments),
            "residual_flags": list(self.residual_flags),
        }


@dataclass(frozen=True)
class TranslationUnit:
    """Normalized representation of a single C translation unit.

    Extracted from a compilation database entry per TOOL-ING-030.

    Attributes:
        source_path: POSIX-style relative path to the translation unit source file.
        working_directory: Working directory in which the compiler was invoked.
        include_paths: Include search paths in command-line order.
        preprocessor_definitions: Preprocessor macro definitions in command-line order.
        compiler_invocation: Executable and flags for this translation unit.
        language_standard: Language standard string (e.g. 'c99', 'gnu11', 'c17') if specified.
        output_file: Path to compilation output file if specified.
    """

    source_path: str
    working_directory: str
    include_paths: tuple[str, ...] = field(default_factory=tuple)
    preprocessor_definitions: tuple[str, ...] = field(default_factory=tuple)
    compiler_invocation: CompilerInvocation = field(
        default_factory=lambda: CompilerInvocation(executable="")
    )
    language_standard: str | None = None
    output_file: str | None = None

    @property
    def file(self) -> str:
        """Alias for source_path to match compile_commands.json terminology."""
        return self.source_path

    @property
    def directory(self) -> str:
        """Alias for working_directory to match compile_commands.json terminology."""
        return self.working_directory

    @property
    def compiler(self) -> str:
        """Convenience property returning the compiler executable name."""
        return self.compiler_invocation.executable

    @property
    def arguments(self) -> tuple[str, ...]:
        """Convenience property returning the complete normalized argument sequence."""
        return self.compiler_invocation.arguments

    @property
    def residual_flags(self) -> tuple[str, ...]:
        """Convenience property returning residual flags."""
        return self.compiler_invocation.residual_flags

    @property
    def definitions_map(self) -> dict[str, str | None]:
        """Map of preprocessor macro names to their defined values (None if valueless)."""
        result: dict[str, str | None] = {}
        for item in self.preprocessor_definitions:
            if "=" in item:
                k, v = item.split("=", 1)
                result[k] = v
            else:
                result[item] = None
        return result

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary representation."""
        data: dict[str, Any] = {
            "source_path": self.source_path,
            "working_directory": self.working_directory,
            "include_paths": list(self.include_paths),
            "preprocessor_definitions": list(self.preprocessor_definitions),
            "compiler_invocation": self.compiler_invocation.to_dict(),
        }
        if self.language_standard is not None:
            data["language_standard"] = self.language_standard
        if self.output_file is not None:
            data["output_file"] = self.output_file
        return data


@dataclass(frozen=True)
class CompilationDatabase:
    """An ingested collection of normalized TranslationUnits.

    Preserves deterministic ordering and provides indexed and query access.
    """

    translation_units: tuple[TranslationUnit, ...] = field(default_factory=tuple)

    def __len__(self) -> int:
        return len(self.translation_units)

    def __iter__(self) -> Iterator[TranslationUnit]:
        return iter(self.translation_units)

    def __getitem__(self, index: int) -> TranslationUnit:
        return self.translation_units[index]

    def get(self, source_path: str) -> TranslationUnit | None:
        """Find the first translation unit matching the given source path."""
        norm = source_path.replace("\\", "/")
        for tu in self.translation_units:
            if tu.source_path == norm:
                return tu
        return None

    def filter_by_source(self, source_path: str) -> list[TranslationUnit]:
        """Find all translation units matching the given source path."""
        norm = source_path.replace("\\", "/")
        return [tu for tu in self.translation_units if tu.source_path == norm]

    @property
    def source_paths(self) -> list[str]:
        """List of all source paths in database order."""
        return [tu.source_path for tu in self.translation_units]

    def to_dict(self) -> dict[str, Any]:
        """Serialize database to a plain dictionary representation."""
        return {
            "translation_units": [tu.to_dict() for tu in self.translation_units],
        }

    def canonical_json(self) -> str:
        """Serialize to deterministically ordered canonical JSON."""
        return canonical_json(self.to_dict())

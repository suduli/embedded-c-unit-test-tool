# implements: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090
"""C front-end binding and dialect management using libclang.

Owns the sole libclang dependency in ectt per SDD-001 S4.2 and SDD-005 S5.3.
Translates compilation database translation units and flags into AST parses.

Satisfies: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090.
"""

from __future__ import annotations

import os
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ectt.ana.errors import (
    FrontendParseError,
    LibclangError,
    LibclangLoadError,
    LibclangNotFoundError,
    LibclangVersionError,
    SourceFileNotFoundError,
    UnsupportedDialectError,
)
from ectt.ana.model import Diagnostic, ParsedTranslationUnit, ParseResult
from ectt.ing.model import TranslationUnit

__all__ = [
    "SUPPORTED_DIALECTS",
    "ISO_DIALECTS",
    "GNU_DIALECTS",
    "is_supported_dialect",
    "normalize_dialect",
    "get_libclang_version",
    "get_libclang_version_tuple",
    "normalize_path",
    "extract_include_dirs",
    "resolve_source_location_path",
    "ClangFrontend",
    "parse",
]

# Required minimum libclang / LLVM version floor per SDD-005 S5.3
LIBCLANG_FLOOR_VERSION: tuple[int, int] = (18, 1)

# Dialect tables satisfying TOOL-PAR-020
ISO_DIALECTS: frozenset[str] = frozenset({
    # C89 / C90
    "c89",
    "c90",
    "iso9899:1990",
    # C99
    "c99",
    "c9x",
    "iso9899:199409",
    "iso9899:1999",
    # C11
    "c11",
    "c1x",
    "iso9899:2011",
    # C17 / C18
    "c17",
    "c18",
    "iso9899:2017",
    "iso9899:2018",
    # C23
    "c23",
    "c2x",
})

GNU_DIALECTS: frozenset[str] = frozenset({
    "gnu89",
    "gnu90",
    "gnu99",
    "gnu9x",
    "gnu11",
    "gnu1x",
    "gnu17",
    "gnu18",
    "gnu23",
    "gnu2x",
})

SUPPORTED_DIALECTS: frozenset[str] = ISO_DIALECTS | GNU_DIALECTS

_SEVERITY_NAMES: dict[int, str] = {
    0: "ignored",
    1: "note",
    2: "warning",
    3: "error",
    4: "fatal",
}


def normalize_dialect(dialect_token: str) -> str:
    """Normalize a dialect string by lowercasing and stripping any leading -std= or /std: prefix."""
    token = dialect_token.strip().lower()
    if token.startswith("-std="):
        token = token[5:]
    elif token.startswith("-std"):
        token = token[4:]
    elif token.startswith("/std:"):
        token = token[5:]
    return token.strip("\"'")


def is_supported_dialect(dialect: str) -> bool:
    """Return True if the given dialect is recognized and supported per TOOL-PAR-020."""
    return normalize_dialect(dialect) in SUPPORTED_DIALECTS


def _load_cindex(library_path: str | Path | None = None) -> Any:
    """Import and initialize clang.cindex with error boundary enforcement."""
    try:
        import clang.cindex  # type: ignore[import-not-found,import-untyped]
    except (ImportError, ModuleNotFoundError) as exc:
        raise LibclangNotFoundError(
            f"libclang Python bindings are not installed: {exc}",
            reason="libclang_not_found",
        ) from exc

    if library_path is not None:
        try:
            clang.cindex.Config.set_library_path(str(library_path))
        except Exception as exc:
            raise LibclangLoadError(
                f"Failed to set libclang library path '{library_path}': {exc}",
                path=library_path,
                reason="libclang_load_error",
            ) from exc

    try:
        _ = clang.cindex.conf.lib
    except Exception as exc:
        raise LibclangLoadError(
            f"Failed to load libclang native shared library: {exc}",
            reason="libclang_load_error",
        ) from exc

    return clang.cindex


def get_libclang_version(library_path: str | Path | None = None) -> str:
    """Return the raw libclang version string reported by clang_getClangVersion()."""
    cindex = _load_cindex(library_path)
    lib = cindex.conf.lib
    try:
        lib.clang_getClangVersion.restype = cindex._CXString
        lib.clang_getClangVersion.argtypes = []
        cx = lib.clang_getClangVersion()
        return str(cindex._CXString.from_result(cx))
    except Exception as exc:
        raise LibclangError(
            f"Failed to retrieve libclang version: {exc}",
            reason="libclang_version_query_failed",
        ) from exc


def get_libclang_version_tuple(library_path: str | Path | None = None) -> tuple[int, int, int]:
    """Return parsed (major, minor, patch) version tuple of libclang."""
    raw = get_libclang_version(library_path)
    match = re.search(r"clang version (\d+)\.(\d+)(?:\.(\d+))?", raw)
    if not match:
        raise LibclangVersionError(
            f"Unable to parse libclang version from string: '{raw}'",
            version=raw,
            reason="libclang_version_parse_error",
        )
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3) or 0)
    return (major, minor, patch)


def check_libclang_version_floor(library_path: str | Path | None = None) -> None:
    """Verify that the loaded libclang satisfies the LLVM 18.1 floor (SDD-005 S5.3)."""
    major, minor, patch = get_libclang_version_tuple(library_path)
    if (major, minor) < LIBCLANG_FLOOR_VERSION:
        ver_str = f"{major}.{minor}.{patch}"
        floor_str = f"{LIBCLANG_FLOOR_VERSION[0]}.{LIBCLANG_FLOOR_VERSION[1]}"
        raise LibclangVersionError(
            f"libclang version {ver_str} is below required floor {floor_str} (SDD-005 S5.3)",
            version=ver_str,
            floor=floor_str,
            reason="libclang_version_below_floor",
        )


def extract_include_dirs(
    args: Sequence[str],
    base_dir: str | Path | None = None,
) -> list[str]:
    """Extract include directories from compiler arguments in command-line order.

    Recognizes -I, -isystem, -iquote, and -idirafter in both joined (-Ipath)
    and separated (-I path) forms. Resolves relative include paths against base_dir.
    """
    include_prefixes = ("-isystem", "-iquote", "-idirafter")
    dirs: list[str] = []
    base_p = Path(base_dir).resolve() if base_dir is not None else Path.cwd().resolve()

    def _add_dir(raw_val: str) -> None:
        clean = raw_val.strip("\"'")
        if not clean:
            return
        p = Path(clean)
        if not p.is_absolute():
            p = base_p / p
        try:
            resolved = p.resolve()
        except (OSError, ValueError, RuntimeError):
            resolved = p
        dirs.append(resolved.as_posix())

    i = 0
    n = len(args)
    while i < n:
        arg = args[i]
        matched = False
        for prefix in include_prefixes:
            if arg == prefix and i + 1 < n:
                _add_dir(args[i + 1])
                i += 2
                matched = True
                break
            elif arg.startswith(prefix) and len(arg) > len(prefix):
                _add_dir(arg[len(prefix):])
                i += 1
                matched = True
                break
        if matched:
            continue

        if arg == "-I" and i + 1 < n:
            _add_dir(args[i + 1])
            i += 2
            continue
        elif arg.startswith("-I") and len(arg) > 2:
            _add_dir(arg[2:])
            i += 1
            continue

        i += 1

    return dirs


def resolve_source_location_path(
    path: str | Path | None,
    base_dir: str | Path | None = None,
    include_dirs: Sequence[str | Path] | None = None,
) -> tuple[str, str]:
    """Normalize a source file path and determine its origin category.

    Origin categories:
        - 'project': Path is under base_dir (working directory).
        - 'include': Path is outside base_dir, but within an include directory
                     (-I, -isystem, etc.). Resolved relative to the longest matching
                     include directory, breaking ties with command-line order.
        - 'external': Path is under neither; returns file basename to avoid leaking
                      machine-specific paths.

    Returns:
        (normalized_relative_path, origin)
    """
    if path is None:
        return ("", "external")
    raw = str(path).replace("\\", "/")
    if not raw:
        return ("", "external")

    base_resolved: Path | None = None
    if base_dir is not None:
        try:
            base_resolved = Path(base_dir).resolve()
        except (OSError, ValueError, RuntimeError):
            base_resolved = Path(base_dir)

    p = Path(raw)
    try:
        if not p.is_absolute() and base_resolved is not None:
            p_resolved = (base_resolved / p).resolve()
        else:
            p_resolved = p.resolve()
    except (OSError, ValueError, RuntimeError):
        p_resolved = p

    # 1. Check if under base_dir (project)
    if base_resolved is not None:
        try:
            if p_resolved.is_relative_to(base_resolved):
                rel = p_resolved.relative_to(base_resolved).as_posix()
                return (rel, "project")
        except (OSError, ValueError, RuntimeError):
            pass

    # If path was already relative and base_dir is not set, treat as project
    if not p.is_absolute() and not raw.startswith(".."):
        return (raw, "project")

    # 2. Check if under an include directory
    if include_dirs:
        matching_dirs: list[tuple[int, int, Path]] = []
        for idx, inc in enumerate(include_dirs):
            try:
                inc_p = Path(inc)
                if not inc_p.is_absolute() and base_resolved is not None:
                    inc_resolved = (base_resolved / inc_p).resolve()
                else:
                    inc_resolved = inc_p.resolve()

                if p_resolved.is_relative_to(inc_resolved):
                    # Sort key: longer resolved path first (-len), then earlier index in command line
                    matching_dirs.append((-len(str(inc_resolved)), idx, inc_resolved))
            except (OSError, ValueError, RuntimeError):
                continue

        if matching_dirs:
            matching_dirs.sort()
            chosen_inc = matching_dirs[0][2]
            try:
                rel = p_resolved.relative_to(chosen_inc).as_posix()
                return (rel, "include")
            except (OSError, ValueError, RuntimeError):
                pass

    # 3. External fallback:
    # If base_dir or include_dirs was provided, return basename to prevent leaking machine paths
    if base_dir is not None or include_dirs:
        return (p_resolved.name or raw, "external")

    # If neither base_dir nor include_dirs was given, preserve normalized POSIX path
    return (raw, "external")


def normalize_path(
    path: str | Path | None,
    base_dir: str | Path | None = None,
    include_dirs: Sequence[str | Path] | None = None,
) -> str:
    """Normalize file path to POSIX relative format, never leaking absolute paths."""
    rel, _ = resolve_source_location_path(path, base_dir=base_dir, include_dirs=include_dirs)
    return rel


class ClangFrontend:
    """Manages the libclang Index lifecycle and parses translation units.

    Implements: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090.
    """

    def __init__(
        self,
        *,
        library_path: str | Path | None = None,
        verify_version_floor: bool = True,
    ) -> None:
        self.library_path = library_path
        self._cindex = _load_cindex(library_path)
        if verify_version_floor:
            check_libclang_version_floor(library_path)
        self._index = self._cindex.Index.create()

    @property
    def index(self) -> Any:
        """Return the underlying clang.cindex.Index handle."""
        return self._index

    def parse(
        self,
        target: TranslationUnit | str | Path,
        *,
        args: Sequence[str] | None = None,
        working_directory: str | Path | None = None,
        language_standard: str | None = None,
        unsaved_files: Sequence[tuple[str, str | bytes]] | None = None,
        options: int | None = None,
    ) -> ParsedTranslationUnit:
        """Parse a translation unit with exact compiler flags using libclang.

        Accepts either a normalized TranslationUnit (from ectt.ing.model) or explicit
        source path and arguments.

        Raises:
            SourceFileNotFoundError: If source file is not found on disk and not in unsaved_files.
            UnsupportedDialectError: If an unsupported C dialect is specified.
            FrontendParseError: If libclang suffers an internal fatal parse failure.
        """
        # 1. Resolve source_path, working_dir, language_standard, and raw args
        if isinstance(target, TranslationUnit):
            source_path = target.source_path
            working_dir: str | None = (
                str(working_directory) if working_directory is not None else target.working_directory
            )
            lang_std = language_standard if language_standard is not None else target.language_standard
            source_args = list(args if args is not None else target.arguments)
        else:
            source_path = str(target)
            working_dir = str(working_directory) if working_directory is not None else None
            lang_std = language_standard
            source_args = list(args if args is not None else ())

        inc_dirs = extract_include_dirs(source_args, working_dir)
        norm_source_path = normalize_path(source_path, working_dir, include_dirs=inc_dirs)

        # 2. Check source file existence (unless provided in unsaved_files)
        has_unsaved = False
        prepared_unsaved: list[tuple[str, str | bytes]] = []
        if unsaved_files is not None:
            for uf_name, uf_content in unsaved_files:
                uf_norm = normalize_path(uf_name, working_dir, include_dirs=inc_dirs)
                prepared_unsaved.append((uf_name, uf_content))
                if (
                    uf_name == source_path
                    or uf_norm == norm_source_path
                    or uf_name == norm_source_path
                    or Path(uf_name).name == Path(source_path).name
                ):
                    has_unsaved = True

        if not has_unsaved:
            # Check filesystem existence
            candidate = Path(source_path)
            if not candidate.is_absolute() and working_dir:
                candidate = Path(working_dir) / candidate
            if not candidate.is_file():
                raise SourceFileNotFoundError(
                    f"Translation unit source file not found: '{source_path}'",
                    path=source_path,
                    reason="source_file_not_found",
                )

        # 3. Process compiler arguments
        clean_args, resolved_dialect = self._prepare_arguments(
            source_args=source_args,
            source_path=source_path,
            norm_source_path=norm_source_path,
            working_dir=working_dir,
            language_standard=lang_std,
        )

        # 4. Invoke libclang Index.parse()
        try:
            tu_handle = self._index.parse(
                source_path,
                args=clean_args,
                unsaved_files=prepared_unsaved if prepared_unsaved else None,
                options=options or 0,
            )
        except self._cindex.TranslationUnitLoadError as exc:
            raise FrontendParseError(
                f"libclang failed to load translation unit '{source_path}': {exc}",
                path=source_path,
                reason="frontend_parse_error",
            ) from exc
        except Exception as exc:
            raise FrontendParseError(
                f"Unexpected libclang failure parsing '{source_path}': {exc}",
                path=source_path,
                reason="frontend_parse_error",
            ) from exc

        # 5. Extract and normalize diagnostics
        diagnostics: list[Diagnostic] = []
        has_error = False

        for diag in tu_handle.diagnostics:
            severity_code = diag.severity
            severity_name = _SEVERITY_NAMES.get(severity_code, "note")

            diag_file: str | None = None
            diag_line: int | None = None
            diag_col: int | None = None

            if diag.location and diag.location.file:
                diag_file = normalize_path(diag.location.file.name, working_dir, include_dirs=inc_dirs)
                diag_line = diag.location.line
                diag_col = diag.location.column

            category = getattr(diag, "category_name", None)

            d = Diagnostic(
                message=diag.spelling,
                severity=severity_name,
                severity_code=severity_code,
                file=diag_file,
                line=diag_line,
                column=diag_col,
                category=category,
            )
            diagnostics.append(d)
            if d.is_error:
                has_error = True

        status = "failed" if has_error else "parsed"

        return ParsedTranslationUnit(
            source_path=norm_source_path,
            status=status,
            diagnostics=tuple(diagnostics),
            translation_unit=tu_handle,
            arguments=tuple(source_args),
            include_dirs=tuple(inc_dirs),
        )

    def _prepare_arguments(
        self,
        *,
        source_args: list[str],
        source_path: str,
        norm_source_path: str,
        working_dir: str | None,
        language_standard: str | None,
    ) -> tuple[list[str], str | None]:
        """Normalize arguments list, strip compiler executable and source path, and validate dialect."""
        tokens = list(source_args)
        if not tokens:
            tokens = []

        # If the first token looks like a compiler executable (e.g. gcc, clang, arm-none-eabi-gcc),
        # strip it so libclang doesn't treat it as a linker input file.
        if tokens:
            first = tokens[0].lower().replace("\\", "/")
            first_name = Path(first).name
            if (
                any(comp in first_name for comp in ("gcc", "clang", "cl.exe", "cc", "c++", "icc"))
                or first.endswith(".exe")
            ):
                tokens.pop(0)

        clean_args: list[str] = []
        detected_dialect: str | None = None
        has_working_dir_arg = False

        norm_src = source_path.replace("\\", "/")
        src_name = Path(source_path).name

        idx = 0
        num = len(tokens)
        while idx < num:
            tok = tokens[idx]

            # Check if this token specifies language standard
            if tok.startswith("-std="):
                dialect = tok[5:]
                clean_args.append(tok)
                detected_dialect = dialect
                idx += 1
                continue
            elif tok == "-std" and idx + 1 < num:
                idx += 1
                dialect = tokens[idx]
                clean_args.append(f"-std={dialect}")
                detected_dialect = dialect
                idx += 1
                continue
            elif tok.startswith("/std:"):
                dialect = tok[5:]
                clean_args.append(f"-std={dialect}")
                detected_dialect = dialect
                idx += 1
                continue

            if tok.startswith("-working-directory"):
                has_working_dir_arg = True
                clean_args.append(tok)
                idx += 1
                continue

            # Strip source file token to avoid duplicate input error in libclang
            tok_norm = tok.replace("\\", "/")
            if (
                tok_norm == norm_src
                or tok_norm == norm_source_path
                or (Path(tok_norm).name == src_name and tok_norm.endswith((".c", ".C", ".h")))
            ):
                idx += 1
                continue

            clean_args.append(tok)
            idx += 1

        # Determine effective dialect
        effective_dialect = language_standard if language_standard is not None else detected_dialect
        if effective_dialect is not None:
            norm_dialect = normalize_dialect(effective_dialect)
            if not is_supported_dialect(norm_dialect):
                raise UnsupportedDialectError(
                    f"Unsupported or unrecognized C dialect standard: '{effective_dialect}'",
                    dialect=effective_dialect,
                    reason="unsupported_dialect",
                )
            # If language_standard was provided but not in args, append it
            if detected_dialect is None:
                clean_args.append(f"-std={norm_dialect}")

        # Add working directory flag if not already specified
        if working_dir and not has_working_dir_arg:
            clean_args.insert(0, f"-working-directory={working_dir}")

        return clean_args, effective_dialect


# Default module-level frontend instance
_DEFAULT_FRONTEND: ClangFrontend | None = None


def _get_default_frontend() -> ClangFrontend:
    """Return or lazily create the default ClangFrontend singleton."""
    global _DEFAULT_FRONTEND
    if _DEFAULT_FRONTEND is None:
        _DEFAULT_FRONTEND = ClangFrontend()
    return _DEFAULT_FRONTEND


def parse(
    target: TranslationUnit | str | Path,
    *,
    args: Sequence[str] | None = None,
    working_directory: str | Path | None = None,
    language_standard: str | None = None,
    unsaved_files: Sequence[tuple[str, str | bytes]] | None = None,
    options: int | None = None,
    frontend: ClangFrontend | None = None,
) -> ParsedTranslationUnit:
    """Parse a translation unit with exact compiler flags using libclang.

    Convenience wrapper around ClangFrontend.parse().
    """
    fe = frontend if frontend is not None else _get_default_frontend()
    return fe.parse(
        target,
        args=args,
        working_directory=working_directory,
        language_standard=language_standard,
        unsaved_files=unsaved_files,
        options=options,
    )

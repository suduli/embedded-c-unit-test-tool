# implements: DSN-ING-060
"""Content-based, fail-closed staleness detection for the ingested model.

Satisfies: TOOL-ING-090, TOOL-ING-100.

The contract has no warn path. `capture_staleness_inputs` records content
fingerprints of everything the ingested model was derived from — the
compilation database itself, each source file, each response file, and the
include surface of every include directory (which is what `__has_include`
outcomes and header shadowing depend on). `check_staleness` compares two
captures; any difference, any unreadable input, and any include surface that
cannot be enumerated within documented bounds marks the model stale.
`assert_fresh` raises StalenessError so the caller must re-ingest before
downstream use.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

from ectt.ing.errors import StalenessError
from ectt.ing.model import CompilationDatabase

__all__ = [
    "InputFingerprint",
    "StalenessInputs",
    "StalenessReport",
    "capture_staleness_inputs",
    "check_staleness",
    "assert_fresh",
]

_HEADER_SUFFIXES = (".h", ".hpp", ".hxx", ".hh", ".inc", ".inl")
_MAX_INCLUDE_SURFACE_FILES = 20000
_MAX_FINGERPRINT_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class InputFingerprint:
    """Content fingerprint of one file the ingested model depends on.

    ``content_digest`` is None when the file was missing or unreadable at
    capture time — an unknown, which is itself a staleness trigger.
    """

    path: str
    content_digest: str | None


@dataclass(frozen=True)
class StalenessInputs:
    """Everything the ingested model's validity depends on, content-digested.

    ``compdb_digest`` and ``include_surface_digest`` are None when the
    corresponding input was unavailable or could not be enumerated within
    documented bounds; ``unknown_include_surface`` records that case
    explicitly and is itself a staleness trigger.
    """

    compdb_digest: str | None = None
    source_fingerprints: tuple[InputFingerprint, ...] = ()
    response_file_fingerprints: tuple[InputFingerprint, ...] = ()
    include_surface_digest: str | None = None
    unknown_include_surface: bool = False


@dataclass(frozen=True)
class StalenessReport:
    """Outcome of comparing two staleness captures."""

    stale: bool
    reasons: tuple[str, ...] = ()
    changed_paths: tuple[str, ...] = ()


def _digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest_file(path: Path) -> str | None:
    """Content digest of a file, or None when missing or unreadable."""
    try:
        if path.stat().st_size > _MAX_FINGERPRINT_BYTES:
            # Over the fingerprint bound: digest a bounded prefix. Still
            # content-based; a change crossing the bound changes the prefix.
            with path.open("rb") as fh:
                return _digest_bytes(fh.read(_MAX_FINGERPRINT_BYTES))
        return _digest_bytes(path.read_bytes())
    except OSError:
        return None


def _iter_source_paths(db: CompilationDatabase) -> Iterator[tuple[str, Path]]:
    """Yield (deduplicated key, resolved path) for every source in the database."""
    seen: set[str] = set()
    for tu in db:
        candidate = Path(tu.source_path)
        if not candidate.is_absolute():
            candidate = Path(tu.working_directory) / candidate
        key = candidate.as_posix()
        if key in seen:
            continue
        seen.add(key)
        yield key, candidate


def _iter_response_paths(db: CompilationDatabase) -> Iterator[tuple[str, Path]]:
    seen: set[str] = set()
    for tu in db:
        for rf in tu.response_files:
            candidate = Path(rf)
            if not candidate.is_absolute():
                candidate = Path(tu.working_directory) / candidate
            key = candidate.as_posix()
            if key in seen:
                continue
            seen.add(key)
            yield key, candidate


def _iter_include_dirs(db: CompilationDatabase) -> Iterator[tuple[str, Path]]:
    seen: set[str] = set()
    for tu in db:
        for inc in tu.include_paths:
            candidate = Path(inc)
            if not candidate.is_absolute():
                candidate = Path(tu.working_directory) / candidate
            try:
                resolved = candidate.resolve()
            except OSError:
                resolved = candidate
            key = resolved.as_posix()
            if key in seen:
                continue
            seen.add(key)
            yield key, resolved


def _capture_include_surface(
    include_dirs: Mapping[str, Path],
    *,
    max_files: int,
) -> tuple[str | None, bool]:
    """Digest the headers visible across include directories, in sorted order.

    Returns (digest, unknown). When the total header count exceeds
    ``max_files`` the surface cannot be enumerated within bounds and
    ``unknown`` is True (the caller treats unknown as stale).
    """
    entries: list[str] = []
    count = 0
    unknown = False
    for dir_key in sorted(include_dirs):
        directory = include_dirs[dir_key]
        if not directory.is_dir():
            continue
        for root, _dirs, files in os.walk(directory):
            for name in sorted(files):
                if not name.endswith(_HEADER_SUFFIXES):
                    continue
                count += 1
                if count > max_files:
                    return None, True
                rel = Path(root, name).relative_to(directory).as_posix()
                entries.append(f"{dir_key}!{rel}")
    if unknown:
        return None, True
    entries.sort()
    digest = hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()
    return digest, False


def capture_staleness_inputs(
    db: CompilationDatabase,
    *,
    compdb_path: str | Path | None = None,
    max_include_surface_files: int = _MAX_INCLUDE_SURFACE_FILES,
) -> StalenessInputs:
    """Record content fingerprints of every input the ingested model depends on.

    Satisfies: TOOL-ING-090, TOOL-ING-100 (DSN-ING-060).
    """
    compdb_digest: str | None = None
    if compdb_path is not None:
        compdb_digest = _digest_file(Path(compdb_path))

    sources = [
        InputFingerprint(path=key, content_digest=_digest_file(path_obj))
        for key, path_obj in _iter_source_paths(db)
    ]
    responses = [
        InputFingerprint(path=key, content_digest=_digest_file(path_obj))
        for key, path_obj in _iter_response_paths(db)
    ]

    include_dirs = dict(_iter_include_dirs(db))
    include_surface_digest, unknown = _capture_include_surface(
        include_dirs, max_files=max_include_surface_files
    )

    return StalenessInputs(
        compdb_digest=compdb_digest,
        source_fingerprints=tuple(sources),
        response_file_fingerprints=tuple(responses),
        include_surface_digest=include_surface_digest,
        unknown_include_surface=unknown,
    )


def _compare_fingerprints(
    recorded: tuple[InputFingerprint, ...],
    current: tuple[InputFingerprint, ...],
    *,
    kind: str,
    reasons: list[str],
    changed_paths: list[str],
) -> None:
    rec = {fp.path: fp.content_digest for fp in recorded}
    cur = {fp.path: fp.content_digest for fp in current}
    for path in sorted(set(rec) | set(cur)):
        r = rec.get(path)
        c = cur.get(path)
        if c is None:
            reasons.append(f"{kind}_missing")
            changed_paths.append(path)
        elif r is None or r != c:
            reasons.append(f"{kind}_changed")
            changed_paths.append(path)


def _compare_scalar(
    kind: str,
    recorded: str | None,
    current: str | None,
    reasons: list[str],
    changed_paths: list[str],
) -> None:
    """Fail-closed scalar comparison: None on either side is never fresh."""
    if current is None:
        reasons.append(f"{kind}_missing")
    elif recorded is None or recorded != current:
        reasons.append(f"{kind}_changed")
    else:
        return
    changed_paths.append(kind)


def check_staleness(
    recorded: StalenessInputs,
    current: StalenessInputs,
) -> StalenessReport:
    """Compare two captures; any difference or unknown marks the model stale."""
    reasons: list[str] = []
    changed_paths: list[str] = []

    _compare_scalar(
        "compdb", recorded.compdb_digest, current.compdb_digest, reasons, changed_paths
    )
    _compare_fingerprints(
        recorded.source_fingerprints,
        current.source_fingerprints,
        kind="source",
        reasons=reasons,
        changed_paths=changed_paths,
    )
    _compare_fingerprints(
        recorded.response_file_fingerprints,
        current.response_file_fingerprints,
        kind="response_file",
        reasons=reasons,
        changed_paths=changed_paths,
    )
    if current.unknown_include_surface or recorded.unknown_include_surface:
        reasons.append("include_surface_unknown")
        changed_paths.append("include_surface")
    else:
        _compare_scalar(
            "include_surface",
            recorded.include_surface_digest,
            current.include_surface_digest,
            reasons,
            changed_paths,
        )

    reasons = tuple(dict.fromkeys(reasons))
    changed_paths = tuple(dict.fromkeys(changed_paths))
    return StalenessReport(
        stale=bool(reasons), reasons=reasons, changed_paths=changed_paths
    )


def assert_fresh(report: StalenessReport) -> None:
    """Raise StalenessError when the report marks the ingested model stale.

    The fail-closed gate: there is deliberately no warn mode (TOOL-ING-100).
    """
    if report.stale:
        raise StalenessError(
            "Ingested project model is stale; re-ingestion is required before "
            "downstream use (no warn path exists)",
            reasons=report.reasons,
            changed_paths=report.changed_paths,
        )

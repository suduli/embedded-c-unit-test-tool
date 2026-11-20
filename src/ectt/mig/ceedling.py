# implements: TOOL-MIG-020
"""Ceedling project import (WP-MIG-02).

TOOL-MIG-020: the tool shall import an existing Ceedling project, preserving
test cases and configuration.

The import is read-only (TOOL-MIG-070 discipline): it reads ``project.yml`` and
the test sources and returns an :class:`ImportedCeedlingProject`; nothing in
the Ceedling tree is created, changed or deleted.

* **Configuration** is preserved verbatim: every section of ``project.yml``,
  known to this importer or not, is carried in ``config`` (scalars are strings,
  the project-file convention of ``RestrictedYamlAdapter``).
* **Test cases** are preserved as the authored C test functions. A Ceedling
  test is imperative Unity code, so it is *not* rewritten into a data-driven
  case; it is registered by file, name and source line, with a content digest
  of the file (D-02: stable ids plus content digests), and stays runnable
  through the existing-suite path (WP-MIG-01).
* **Nothing is silently dropped.** Constructs this importer cannot convert are
  reported in ``unconverted`` with a location: parameterised ``TEST_CASE`` /
  ``TEST_RANGE`` / ``TEST_MATRIX`` attributes, ``:import:`` and ``:mixins:``
  files that were not followed, duplicate test names, and path entries that
  match nothing. The per-artifact fidelity report of TOOL-MIG-040 is a
  separate work package built on this list.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ectt.core.determinism import stable_id
from ectt.mig.errors import MigError
from ectt.prj.errors import RestrictedYamlError
from ectt.prj.yaml_adapter import RestrictedYamlAdapter

__all__ = [
    "CEEDLING_PROJECT_FILE",
    "CeedlingTest",
    "CeedlingTestFile",
    "ImportNote",
    "ImportedCeedlingProject",
    "import_ceedling_project",
    "strip_c_comments_and_strings",
]

CEEDLING_PROJECT_FILE = "project.yml"

_TEST_FUNCTION = re.compile(r"^[ \t]*(?:static[ \t]+)?void[ \t]+(test\w*)[ \t]*\([^)]*\)", re.MULTILINE)
_ATTRIBUTE = re.compile(r"^[ \t]*(TEST_CASE|TEST_RANGE|TEST_MATRIX)\b", re.MULTILINE)
_GLOB_CHARS = frozenset("*?[")
_QUOTES = frozenset({'"', "'"})


@dataclass(frozen=True)
class ImportNote:
    """Something found but not converted, with where it was found."""

    kind: str
    location: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"detail": self.detail, "kind": self.kind, "location": self.location}


@dataclass(frozen=True)
class CeedlingTest:
    """One authored test function."""

    name: str
    line: int
    test_id: str


@dataclass(frozen=True)
class CeedlingTestFile:
    """One test source file and the tests it holds, in source order."""

    path: str
    content_digest: str
    tests: tuple[CeedlingTest, ...]


@dataclass(frozen=True)
class ImportedCeedlingProject:
    """Result of importing a Ceedling project; deterministic and read-only."""

    config: Mapping[str, Any]
    config_digest: str
    test_files: tuple[CeedlingTestFile, ...]
    unconverted: tuple[ImportNote, ...]

    @property
    def test_count(self) -> int:
        return sum(len(f.tests) for f in self.test_files)

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config,
            "config_digest": self.config_digest,
            "test_files": [
                {
                    "content_digest": f.content_digest,
                    "path": f.path,
                    "tests": [{"line": t.line, "name": t.name, "test_id": t.test_id} for t in f.tests],
                }
                for f in self.test_files
            ],
            "unconverted": [n.to_dict() for n in self.unconverted],
        }


def strip_c_comments_and_strings(source: str) -> str:
    """Blank comments and string/char literal bodies, keeping every newline.

    Line numbers of the result match the input, so a match offset maps back to
    the authored line.
    """
    out: list[str] = []
    i, n = 0, len(source)
    while i < n:
        two = source[i : i + 2]
        ch = source[i]
        if two == "//":
            while i < n and source[i] != "\n":
                out.append(" ")
                i += 1
        elif two == "/*":
            out.append("  ")
            i += 2
            while i < n and source[i : i + 2] != "*/":
                out.append("\n" if source[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append("  ")
            i += 2
        elif ch in _QUOTES:
            out.append(ch)
            i += 1
            while i < n and source[i] != ch and source[i] != "\n":
                if source[i] == "\\" and i + 1 < n and source[i + 1] != "\n":
                    out.append("  ")
                    i += 2
                    continue
                out.append(" ")
                i += 1
            if i < n and source[i] == ch:
                out.append(ch)
                i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _load_config(project_file: Path) -> dict[str, Any]:
    try:
        text = project_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise MigError(f"Ceedling project file '{project_file}' is not UTF-8", reason="invalid_encoding") from exc
    except OSError as exc:
        raise MigError(f"cannot read Ceedling project file '{project_file}': {exc}", reason="unreadable_project") from exc
    try:
        return RestrictedYamlAdapter().load(text, path=project_file)
    except RestrictedYamlError as exc:
        raise MigError(
            f"Ceedling project file '{project_file}' is not importable: {exc}",
            reason="invalid_project_file",
        ) from exc


def _section(config: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = config.get(key)
    return value if isinstance(value, Mapping) else {}


def _confined(entry: str) -> str:
    posix = entry.replace("\\", "/")
    if posix.startswith("/") or re.match(r"^[A-Za-z]:", posix) or ".." in posix.split("/"):
        raise MigError(
            f"Ceedling test path '{entry}' leaves the project root",
            reason="path_escape",
        )
    return posix


def _expand_directories(root: Path, entry: str) -> list[Path]:
    pattern = _confined(entry).rstrip("/")
    if pattern in ("", "."):
        return [root]
    if _GLOB_CHARS & set(pattern):
        return sorted(p for p in root.glob(pattern) if p.is_dir())
    candidate = root / pattern
    return [candidate] if candidate.is_dir() else []


def _test_directories(root: Path, entries: list[str], unconverted: list[ImportNote]) -> list[Path]:
    selected: dict[Path, None] = {}
    for raw in entries:
        sign, body = "+", raw
        if raw.startswith(("+:", "-:")):
            sign, body = raw[0], raw[2:]
        dirs = _expand_directories(root, body)
        if not dirs:
            unconverted.append(ImportNote("path_matches_nothing", f"{CEEDLING_PROJECT_FILE}:paths/test", raw))
        for directory in dirs:
            if sign == "+":
                selected.setdefault(directory.resolve(), None)
            else:
                selected.pop(directory.resolve(), None)
    return sorted(selected)


def _scan_test_file(root: Path, path: Path, unconverted: list[ImportNote]) -> CeedlingTestFile:
    rel = path.relative_to(root).as_posix()
    data = path.read_bytes()
    try:
        source = data.decode("utf-8")
    except UnicodeDecodeError:
        source = data.decode("latin-1")
        unconverted.append(ImportNote("non_utf8_source", rel, "decoded as Latin-1 to locate tests"))
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    stripped = strip_c_comments_and_strings(source)

    def line_of(offset: int) -> int:
        return stripped.count("\n", 0, offset) + 1

    tests: list[CeedlingTest] = []
    seen: set[str] = set()
    for match in _TEST_FUNCTION.finditer(stripped):
        name = match.group(1)
        line = line_of(match.start(1))
        if name in seen:
            unconverted.append(ImportNote("duplicate_test_name", f"{rel}:{line}", name))
            continue
        seen.add(name)
        tests.append(CeedlingTest(name=name, line=line, test_id=stable_id(rel, name)))
    unconverted.extend(
        ImportNote(
            "parameterised_test_attribute",
            f"{rel}:{line_of(match.start())}",
            f"{match.group(1)} rows are preserved in the source but not expanded into cases",
        )
        for match in _ATTRIBUTE.finditer(stripped)
    )
    return CeedlingTestFile(path=rel, content_digest=stable_id(data), tests=tuple(tests))


def import_ceedling_project(root: Path | str) -> ImportedCeedlingProject:
    """Import the Ceedling project rooted at ``root`` without modifying it."""
    root_path = Path(root).resolve()
    project_file = root_path / CEEDLING_PROJECT_FILE
    if not project_file.is_file():
        raise MigError(
            f"no Ceedling project file '{CEEDLING_PROJECT_FILE}' in '{root_path}'",
            reason="no_project_file",
        )
    config = _load_config(project_file)
    unconverted: list[ImportNote] = []

    unconverted.extend(
        ImportNote(
            "external_config_not_followed",
            f"{CEEDLING_PROJECT_FILE}:{key.lstrip(':')}",
            "referenced configuration files are preserved as written but not merged",
        )
        for key in (":import", ":mixins")
        if key in config
    )

    project = _section(config, ":project")
    prefix = str(project.get(":test_file_prefix", "test_"))
    extension = str(_section(config, ":extension").get(":source", ".c"))
    if not extension.startswith("."):
        extension = "." + extension
    entries = _as_str_list(_section(config, ":paths").get(":test"))
    if not entries:
        unconverted.append(
            ImportNote("no_test_paths", f"{CEEDLING_PROJECT_FILE}:paths/test", "no :paths: :test: entries declared")
        )

    files: dict[str, CeedlingTestFile] = {}
    for directory in _test_directories(root_path, entries, unconverted):
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.name.startswith(prefix) and path.suffix == extension:
                scanned = _scan_test_file(root_path, path, unconverted)
                files.setdefault(scanned.path, scanned)

    ordered = tuple(files[key] for key in sorted(files))
    ordered_notes = tuple(sorted(unconverted, key=lambda n: (n.location, n.kind, n.detail)))
    return ImportedCeedlingProject(
        config=config,
        config_digest=stable_id(config),
        test_files=ordered,
        unconverted=ordered_notes,
    )

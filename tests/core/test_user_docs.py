# implements: TOOL-NFR-120
"""The docs/user drafts match the documentation index and the real surface (B4).

Every entry in the machine-readable index (ectt.core.docindex) must exist as a
page under docs/user/, marked DRAFT; every CLI command a page names must be a
real command of the current CLI surface; every Python API a page names must
actually exist. This is what keeps the drafts honest while they await owner
wording.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

from ectt.api import default_catalogue
from ectt.cli.generator import build_parser, command_names
from ectt.core.docindex import documentation_index

REPO_ROOT = Path(__file__).parents[2]
CATALOGUE = default_catalogue()
CLI_COMMANDS = set(command_names(CATALOGUE))
CLI_FLAGS = {"--help", "--list-commands", "--version"}

_COMMAND_RE = re.compile(r"`ectt ([a-z][a-z0-9._-]*|--[a-z-]+)`")
_MODULE_RE = re.compile(r"`((?:ectt\.)+[a-z_]+(?:\.[A-Za-z_][A-Za-z0-9_]*)*)`")


def test_every_index_page_exists_and_is_marked_draft() -> None:
    """verifies: TOOL-NFR-120 — the shipped documentation matches the index."""
    index = documentation_index()
    assert len(index.entries) == 15
    for entry in index.entries:
        page = REPO_ROOT / entry.doc_anchor
        assert page.is_file(), f"index entry '{entry.entry_id}' has no page at {entry.doc_anchor}"
        text = page.read_text(encoding="utf-8")
        assert "# DRAFT:" in text, f"{entry.doc_anchor} is not marked DRAFT"
        assert "**not yet available**" in text or "not yet available" in text or entry.entry_id == "workflow.build_interception"


def test_every_command_a_page_names_is_real() -> None:
    """verifies: B4 — pages name only commands the current CLI really has."""
    named: dict[str, str] = {}
    for entry in documentation_index().entries:
        text = (REPO_ROOT / entry.doc_anchor).read_text(encoding="utf-8")
        for match in _COMMAND_RE.finditer(text):
            named.setdefault(match.group(1), entry.doc_anchor)
    for command, page in named.items():
        assert command in CLI_COMMANDS or command in CLI_FLAGS, (
            f"{page} names CLI command '{command}' which the current surface does not have "
            f"(real: {sorted(CLI_COMMANDS | CLI_FLAGS)})"
        )


def test_every_python_api_a_page_names_is_real() -> None:
    """verifies: B4 — pages name only modules and attributes that exist."""
    for entry in documentation_index().entries:
        text = (REPO_ROOT / entry.doc_anchor).read_text(encoding="utf-8")
        for match in _MODULE_RE.finditer(text):
            reference = match.group(1)
            parts = reference.split(".")
            module_path = ".".join(parts[:-1]) if len(parts) > 2 else reference
            attribute = parts[-1] if len(parts) > 2 else None
            try:
                module = importlib.import_module(module_path)
            except ImportError as exc:
                raise AssertionError(f"{entry.doc_anchor} names {reference}: {exc}") from exc
            if attribute is not None and attribute[0].isupper():
                assert hasattr(module, attribute), (
                    f"{entry.doc_anchor} names {reference} but {module_path} has no {attribute}"
                )


def test_the_bear_interception_page_marks_the_feature_unavailable() -> None:
    """The one workflow with no code must say so, not describe an invention."""
    text = (REPO_ROOT / "docs/user/workflows/build-interception.md").read_text(encoding="utf-8")
    assert "not yet available" in text


def test_parser_builds_from_the_catalogue() -> None:
    """The CLI surface the pages document is the catalogue-generated one."""
    parser = build_parser(CATALOGUE)
    assert parser.parse_args(["operation.cancel"]) is not None
    assert set(command_names(CATALOGUE)) == CLI_COMMANDS

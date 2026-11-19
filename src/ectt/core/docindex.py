"""Machine-readable user-documentation index (WP-CORE-07).

The index enumerates the user documentation the tool must ship: installation,
every supported workflow, and every configuration-option surface. Entries are
frozen and deterministic; the actual pages under docs/user/ are created by the
owner (recorded as a shared-file change).

Satisfies: TOOL-NFR-120.
"""

from __future__ import annotations

from dataclasses import dataclass

from ectt.core.errors import EcttError

__all__ = [
    "STATUS_SHIPPED",
    "STATUS_PENDING",
    "DocEntry",
    "UserDocumentationIndex",
    "documentation_index",
    "DocIndexError",
]

STATUS_SHIPPED = "shipped"
STATUS_PENDING = "pending-page-not-created"

_INSTALLATION = ("installation", "Installation", "docs/user/installation.md")

_WORKFLOWS: tuple[tuple[str, str, str], ...] = (
    ("workflow.single_file", "Single-file testing without a build system", "docs/user/workflows/single-file.md"),
    ("workflow.compile_database", "Ingesting a compilation database", "docs/user/workflows/compile-database.md"),
    ("workflow.build_interception", "Ingesting via build interception (Bear)", "docs/user/workflows/build-interception.md"),
    ("workflow.compiler_config", "Adding a compiler configuration", "docs/user/workflows/compiler-config.md"),
    ("workflow.harness_generation", "Generating and regenerating a harness", "docs/user/workflows/harness-generation.md"),
    ("workflow.incremental_build", "Building with sanitizers and incremental rebuild", "docs/user/workflows/building.md"),
    ("workflow.test_cases_c", "Authoring test cases in C", "docs/user/workflows/test-cases-c.md"),
    ("workflow.security_first_run", "First run, environment verification and untrusted-project warning", "docs/user/workflows/first-run-security.md"),
    ("workflow.diagnostic_bundle", "Producing a diagnostic bundle for a defect report", "docs/user/workflows/diagnostic-bundle.md"),
)

_OPTIONS: tuple[tuple[str, str, str], ...] = (
    ("option.compiler_config.format", "Compiler configuration file fields (invocation, flags, output, coverage)", "docs/user/options/compiler-config.md"),
    ("option.trust_record", "Untrusted-project trust record", "docs/user/options/trust-record.md"),
    ("option.verbosity", "Logging verbosity levels", "docs/user/options/verbosity.md"),
    ("option.output_root", "Confined output root", "docs/user/options/output-root.md"),
    ("option.sanitizers", "Sanitizer modes and runtime options", "docs/user/options/sanitizers.md"),
)

_ALL_ENTRIES: tuple[tuple[str, str, str], ...] = (
    _INSTALLATION,
    *_WORKFLOWS,
    *_OPTIONS,
)


class DocIndexError(EcttError):
    """Raised when a documentation index entry is malformed."""

    category = "docs"

    def __init__(self, message: str, *, reason: str = "doc_index_error") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class DocEntry:
    """One documentation item the tool must ship."""

    entry_id: str
    title: str
    doc_anchor: str
    status: str

    def to_dict(self) -> dict[str, str]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "doc_anchor": self.doc_anchor,
            "entry_id": self.entry_id,
            "status": self.status,
            "title": self.title,
        }


@dataclass(frozen=True)
class UserDocumentationIndex:
    """The complete table of contents of the user documentation."""

    entries: tuple[DocEntry, ...]

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for entry in self.entries:
            if entry.entry_id in seen:
                raise DocIndexError(f"duplicate documentation entry '{entry.entry_id}'")
            seen.add(entry.entry_id)

    def by_id(self, entry_id: str) -> DocEntry:
        """The entry with ``entry_id``."""
        for entry in self.entries:
            if entry.entry_id == entry_id:
                return entry
        raise DocIndexError(f"no documentation entry '{entry_id}'")

    def ids(self) -> tuple[str, ...]:
        """All entry ids, ordered deterministically."""
        return tuple(sorted(entry.entry_id for entry in self.entries))

    def to_dict(self) -> dict[str, object]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "entries": [entry.to_dict() for entry in sorted(self.entries, key=lambda e: e.entry_id)],
        }


def documentation_index() -> UserDocumentationIndex:
    """The current documentation index. Deterministic on every call."""
    entries: list[DocEntry] = []
    seen: set[str] = set()
    for entry_id, title, anchor in _ALL_ENTRIES:
        if entry_id in seen:
            raise DocIndexError(f"duplicate documentation entry '{entry_id}'")
        seen.add(entry_id)
        entries.append(
            DocEntry(
                entry_id=entry_id,
                title=title,
                doc_anchor=anchor,
                status=STATUS_PENDING,
            )
        )
    return UserDocumentationIndex(entries=tuple(entries))

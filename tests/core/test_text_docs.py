"""Tests for the WP-CORE-07 text externalisation and documentation index.

Covers: catalog lookup with named errors, deterministic serialisation,
translation-by-substitution, and the documentation index completeness.

Verifies: TOOL-NFR-190, TOOL-NFR-120.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.core import (
    STATUS_PENDING,
    DocEntry,
    DocIndexError,
    MessageCatalog,
    TextFormatError,
    UnknownMessageKeyError,
    UserDocumentationIndex,
    default_catalog,
    documentation_index,
)


def test_catalog_lookup_and_formatting() -> None:
    """verifies: TOOL-NFR-190"""
    catalog = default_catalog()
    text = catalog.message("build.plan.rebuild", count=3)
    assert text == "3 artifact(s) scheduled for recompilation."


def test_catalog_lookup_without_values() -> None:
    """verifies: TOOL-NFR-190"""
    catalog = default_catalog()
    assert catalog.message("ingest.stale").startswith("The ingested project model")


def test_unknown_key_is_named_error() -> None:
    """verifies: TOOL-NFR-190"""
    catalog = default_catalog()
    with pytest.raises(UnknownMessageKeyError) as excinfo:
        catalog.message("no.such.key")
    assert "no.such.key" in str(excinfo.value)


def test_missing_placeholder_is_named_error() -> None:
    """verifies: TOOL-NFR-190"""
    catalog = default_catalog()
    with pytest.raises(TextFormatError):
        catalog.message("build.plan.rebuild")


def test_translation_is_catalog_substitution_not_code_edit() -> None:
    """verifies: TOOL-NFR-190"""
    german = MessageCatalog(
        name="de", messages={"build.plan.rebuild": "{count} Artefakt(e) neu zu uebersetzen."}
    )
    assert german.message("build.plan.rebuild", count=2) == "2 Artefakt(e) neu zu uebersetzen."
    assert german.name == "de"


def test_default_catalog_is_english_only() -> None:
    """verifies: TOOL-NFR-190"""
    catalog = default_catalog()
    assert catalog.name == "en"


def test_catalog_keys_are_sorted_and_deterministic() -> None:
    """verifies: TOOL-NFR-190"""
    catalog = default_catalog()
    assert list(catalog.keys()) == sorted(catalog.keys())
    assert catalog.to_dict() == default_catalog().to_dict()


def test_catalog_is_frozen_and_malformed_rejected() -> None:
    """verifies: TOOL-NFR-190"""
    catalog = default_catalog()
    assert dataclasses.is_dataclass(catalog)
    with pytest.raises(UnknownMessageKeyError):
        MessageCatalog(name="x", messages={"blank": "   "})


def test_index_covers_installation_workflows_and_options() -> None:
    """verifies: TOOL-NFR-120"""
    index = documentation_index()
    assert isinstance(index, UserDocumentationIndex)
    assert index.by_id("installation").title == "Installation"
    workflows = [i for i in index.ids() if i.startswith("workflow.")]
    assert len(workflows) >= 5
    options = [i for i in index.ids() if i.startswith("option.")]
    assert len(options) >= 4


def test_index_config_entries_match_code_surfaces() -> None:
    """verifies: TOOL-NFR-120"""
    index = documentation_index()
    # The option surfaces that exist in code each have an index entry.
    for surface in (
        "option.compiler_config.format",
        "option.trust_record",
        "option.verbosity",
        "option.output_root",
        "option.sanitizers",
    ):
        assert index.by_id(surface).doc_anchor.startswith("docs/user/options/")


def test_every_entry_has_title_anchor_and_status() -> None:
    """verifies: TOOL-NFR-120"""
    index = documentation_index()
    for entry in index.entries:
        assert isinstance(entry, DocEntry)
        assert entry.title.strip()
        assert entry.doc_anchor.startswith("docs/user/")
        assert entry.status == STATUS_PENDING


def test_index_is_frozen_and_deterministic() -> None:
    """verifies: TOOL-NFR-120"""
    index = documentation_index()
    assert index.to_dict() == documentation_index().to_dict()
    assert list(index.ids()) == sorted(index.ids())
    with pytest.raises(dataclasses.FrozenInstanceError):
        index.entries = ()  # type: ignore[misc]


def test_unknown_index_entry_is_named_error() -> None:
    """verifies: TOOL-NFR-120"""
    index = documentation_index()
    with pytest.raises(DocIndexError):
        index.by_id("option.does_not_exist")


def test_index_rejects_duplicate_entries() -> None:
    """verifies: TOOL-NFR-120"""
    with pytest.raises(DocIndexError):
        UserDocumentationIndex(
            entries=(
                DocEntry(entry_id="dup", title="A", doc_anchor="docs/user/a.md", status=STATUS_PENDING),
                DocEntry(entry_id="dup", title="B", doc_anchor="docs/user/b.md", status=STATUS_PENDING),
            )
        )

"""Tests for the engine-API operation catalogue (WP-API-01).

Covers: single capability surface, non-empty CLI equivalents, duplicate-name
refusal, and the version metadata the interface negotiation relies on.

Verifies: TOOL-UIX-010, TOOL-UIX-020, TOOL-PLG-060.
"""

from __future__ import annotations

import pytest

from ectt.api.catalogue import (
    BOOTSTRAP_VERSION,
    INTERFACE_VERSION,
    SUPPORTED_INTERFACE_VERSIONS,
    Catalogue,
    Operation,
    default_catalogue,
)
from ectt.api.errors import ApiError


def test_every_operation_carries_nonempty_cli_equivalent() -> None:
    """verifies: TOOL-UIX-010

    One catalogue is the capability surface; every operation must name the CLI
    invocation that performs it (SDD-002 §9.3).
    """
    catalogue = default_catalogue()
    for name in catalogue.names():
        operation = catalogue.get(name)
        assert isinstance(operation.cli_equivalent, str)
        assert operation.cli_equivalent.strip() != ""


def test_cancel_operation_cli_equivalent_matches_sdd_example() -> None:
    """verifies: TOOL-UIX-010

    The protocol-level cancellation operation exists and its CLI equivalent
    follows the SDD-002 §9.2 example shape.
    """
    catalogue = default_catalogue()
    assert catalogue.has("operation.cancel")
    equivalent = catalogue.cli_equivalent_for("operation.cancel")
    assert equivalent.startswith("ectt operation cancel")
    assert "--target-id" in equivalent


def test_catalogue_exposes_interface_version() -> None:
    """verifies: TOOL-PLG-060

    The interface version is explicit and every catalogue operation records
    the version it appeared in (the migration-path anchor).
    """
    assert INTERFACE_VERSION == "1.0"
    assert INTERFACE_VERSION in SUPPORTED_INTERFACE_VERSIONS
    assert BOOTSTRAP_VERSION == "1"
    for name in default_catalogue().names():
        assert default_catalogue().get(name).since_version == INTERFACE_VERSION


def test_duplicate_operation_name_is_refused() -> None:
    """Registering the same operation name twice would give front-ends and the
    CLI divergent views of one capability; the registry must refuse it."""
    catalogue = Catalogue()
    catalogue.register(
        Operation(name="sample.op", summary="first", cli_equivalent="ectt sample op")
    )
    with pytest.raises(ApiError) as excinfo:
        catalogue.register(
            Operation(name="sample.op", summary="second", cli_equivalent="ectt sample op")
        )
    assert excinfo.value.reason == "duplicate_operation"


def test_unknown_operation_lookup_raises_named_error() -> None:
    """An operation outside the catalogue cannot be invoked by any front-end."""
    catalogue = default_catalogue()
    with pytest.raises(ApiError) as excinfo:
        catalogue.get("nonexistent.op")
    assert excinfo.value.reason == "unknown_operation"


def test_catalogue_names_are_sorted() -> None:
    """Deterministic listing keeps catalogue serialisation stable (TOOL-NFR-060)."""
    catalogue = Catalogue()
    catalogue.register(Operation(name="b.op", summary="b", cli_equivalent="ectt b"))
    catalogue.register(Operation(name="a.op", summary="a", cli_equivalent="ectt a"))
    assert catalogue.names() == ["a.op", "b.op"]

"""Round-trip equivalence contract tests (WP-API-03, engine leg).

Verifies: TOOL-UIX-330 (engine leg), DSN-API-040, DSN-CLI-010.
"""

from __future__ import annotations

import pytest

from ectt.api.catalogue import Catalogue, Operation, default_catalogue
from ectt.api.errors import ApiError
from ectt.api.protocol import INVALID_PARAMS, NO_COMMON_VERSION
from ectt.api.roundtrip import (
    cli_equivalent_for_response,
    error_envelope_with_cli_equivalent,
    verify_cli_catalogue_identity,
    verify_cli_equivalent_reachable,
)
from ectt.cli.generator import command_names


def test_every_operational_response_can_carry_cli_equivalent() -> None:
    """verifies: TOOL-UIX-330, DSN-API-040

    Every catalogue operation resolves to a non-empty CLI equivalent for its
    responses.
    """
    catalogue = default_catalogue()
    for name in catalogue.names():
        equivalent = cli_equivalent_for_response(catalogue, name)
        assert equivalent is not None
        assert equivalent.strip() != ""


def test_hello_has_no_cli_equivalent() -> None:
    """verifies: DSN-API-040 (SDD-002 §9.3 exemption)

    The bootstrap hello is connection setup, not an operation: it carries no
    CLI equivalent.
    """
    assert cli_equivalent_for_response(default_catalogue(), "session.hello") is None


def test_cli_command_list_equals_catalogue() -> None:
    """verifies: TOOL-UIX-330, DSN-CLI-010

    The generated CLI command list is exactly the catalogue — the same set
    the API publishes; identity holds in both directions.
    """
    catalogue = default_catalogue()
    verify_cli_catalogue_identity(command_names(catalogue), catalogue)
    with pytest.raises(ApiError) as excinfo:
        verify_cli_catalogue_identity([*command_names(catalogue), "gui.only.op"], catalogue)
    assert excinfo.value.reason == "catalogue_drift"


def test_every_cli_equivalent_parses_to_an_exposed_command() -> None:
    """verifies: TOOL-UIX-330 (engine leg)

    For every catalogue operation, the CLI equivalent's command token is a
    subcommand the generated CLI actually exposes.
    """
    catalogue = default_catalogue()
    cli_names = command_names(catalogue)
    for name in catalogue.names():
        verify_cli_equivalent_reachable(
            cli_equivalent_for_response(catalogue, name) or "",
            cli_names,
        )


def test_error_envelope_cli_equivalent_round_trips() -> None:
    """verifies: TOOL-UIX-330, DSN-API-040

    Even an error envelope carries a catalogue-resolved CLI equivalent; the
    version-negotiation rejection does not (no operation was admitted).
    """
    catalogue = default_catalogue()
    envelope = error_envelope_with_cli_equivalent(
        catalogue,
        "operation.cancel",
        request_id="19",
        code=INVALID_PARAMS,
        message="bad params",
    )
    assert envelope["cli_equivalent"] == catalogue.cli_equivalent_for("operation.cancel")
    version_envelope = error_envelope_with_cli_equivalent(
        catalogue,
        "operation.cancel",
        request_id="19",
        code=NO_COMMON_VERSION,
        message="no overlap",
    )
    assert "cli_equivalent" not in version_envelope


def test_unreachable_cli_equivalent_is_refused() -> None:
    """verifies: TOOL-UIX-330 (drift guard)

    A CLI equivalent naming a command the CLI does not expose is refused —
    the drift the one-catalogue rule exists to prevent.
    """
    with pytest.raises(ApiError) as excinfo:
        verify_cli_equivalent_reachable("ectt ghost.op", ["operation.cancel"])
    assert excinfo.value.reason == "unreachable_cli_equivalent"


def test_roundtrip_holds_for_a_custom_catalogue() -> None:
    """verifies: TOOL-UIX-330

    The contract is structural: a catalogue extended with a new operation
    automatically satisfies CLI identity and reachability.
    """
    catalogue = Catalogue()
    catalogue.register(
        Operation(name="future.op", summary="f", cli_equivalent="ectt future.op")
    )
    cli_names = command_names(catalogue)
    verify_cli_catalogue_identity(cli_names, catalogue)
    verify_cli_equivalent_reachable(
        cli_equivalent_for_response(catalogue, "future.op") or "",
        cli_names,
    )

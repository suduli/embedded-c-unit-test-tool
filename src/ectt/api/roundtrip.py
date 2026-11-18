"""CLI/API round-trip equivalence contract (WP-API-03).

TOOL-UIX-330: state reachable through one front-end stays reachable through
the other. The engine-side contract (SDD-001 §4.4, DSN-API-040/DSN-CLI-010)
is what makes this fall out of the design: every operational API response
carries a ``cli_equivalent``, and the CLI is generated from the same
catalogue the API publishes — one operation set, no drift.

The GUI leg (a project created or modified through the graphical
application) is not demonstrable until a GUI exists (WP-GUI-01); nothing
here claims it.

Satisfies: TOOL-UIX-330 (engine leg).
"""

from __future__ import annotations

from ectt.api.catalogue import Catalogue
from ectt.api.errors import ApiError
from ectt.api.protocol import NO_COMMON_VERSION, error_envelope

__all__ = [
    "cli_equivalent_for_response",
    "verify_cli_catalogue_identity",
    "verify_cli_equivalent_reachable",
]


def cli_equivalent_for_response(catalogue: Catalogue, op: str) -> str | None:
    """Return the ``cli_equivalent`` for an operational response.

    The bootstrap hello is connection setup with no CLI command
    (SDD-002 §9.3); everything else must resolve through the catalogue.
    """
    if op == "session.hello":
        return None
    return catalogue.cli_equivalent_for(op)


def verify_cli_catalogue_identity(cli_names: list[str], catalogue: Catalogue) -> None:
    """Assert the generated CLI command list equals the catalogue exactly.

    DSN-CLI-010: one capability surface. A drift in either direction would
    let a front-end see a capability the other cannot reach.
    """
    catalogue_names = catalogue.names()
    if sorted(cli_names) != catalogue_names:
        raise ApiError(
            "CLI command list drifted from the operation catalogue: "
            f"cli={sorted(cli_names)} catalogue={catalogue_names}",
            reason="catalogue_drift",
        )


def verify_cli_equivalent_reachable(cli_equivalent: str, cli_names: list[str]) -> None:
    """Assert an envelope's ``cli_equivalent`` names a command the CLI exposes.

    TOOL-UIX-330 engine leg: whatever the API did, the CLI can redo. The
    command tokens after the program name must resolve to an exposed
    subcommand; the recorded design names hierarchical commands with spaces
    (``ectt operation cancel --target-id 17``, SDD-002 §9.2) while the
    catalogue generator flattens them to dotted names, so both spellings
    resolve (``operation cancel`` ≡ ``operation.cancel``). Arguments —
    anything from the first ``--`` flag or ``<`` placeholder on — are
    ignored for resolution.
    """
    tokens = cli_equivalent.split()
    if len(tokens) < 2:
        raise ApiError(
            f"cli_equivalent is not a parseable command: {cli_equivalent!r}",
            reason="unparseable_cli_equivalent",
        )
    arg_tokens = tokens[1:]
    command_tokens: list[str] = []
    for token in arg_tokens:
        if token.startswith(("--", "<")):
            break
        command_tokens.append(token)
    if not command_tokens:
        raise ApiError(
            f"cli_equivalent names no command: {cli_equivalent!r}",
            reason="unparseable_cli_equivalent",
        )
    # Longest space-joined prefix first; dotted normalisation as fallback.
    candidates = [
        " ".join(command_tokens[:n]) for n in range(len(command_tokens), 0, -1)
    ] + [".".join(command_tokens)]
    for candidate in candidates:
        if candidate in cli_names:
            return
    raise ApiError(
        f"cli_equivalent names command {' '.join(command_tokens)!r} "
        f"which the CLI does not expose",
        reason="unreachable_cli_equivalent",
    )


def error_envelope_with_cli_equivalent(
    catalogue: Catalogue,
    op: str,
    *,
    request_id: str,
    code: str,
    message: str,
) -> dict[str, object]:
    """Build an error envelope whose ``cli_equivalent`` is catalogue-resolved.

    Demonstrates the AC-1 contract end to end: even a rejection carries the
    CLI path to the same operation (SDD-002 §9.2 example shape).
    """
    if code == NO_COMMON_VERSION:
        return error_envelope(request_id=request_id, code=code, message=message)
    return error_envelope(
        request_id=request_id,
        code=code,
        message=message,
        cli_equivalent=cli_equivalent_for_response(catalogue, op),
    )

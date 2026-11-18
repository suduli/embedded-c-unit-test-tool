"""Tests for the engine-API session protocol (WP-API-01).

Covers: hello bootstrap negotiation (exact common version, both-versions
rejection with migration diagnostic), no-operation-before-hello, envelope
validation (version mismatch, unknown operation, invalid params, duplicate
ID), and strict payload parsing (malformed JSON, duplicate keys).

Verifies: TOOL-UIX-010, TOOL-UIX-020, TOOL-PLG-060.
"""

from __future__ import annotations

import pytest

from ectt.api.catalogue import INTERFACE_VERSION
from ectt.api.errors import ApiError
from ectt.api.protocol import (
    DUPLICATE_ID,
    HELLO_REQUIRED,
    INVALID_PARAMS,
    INVALID_REQUEST,
    NO_COMMON_VERSION,
    UNKNOWN_OPERATION,
    Session,
    error_envelope,
    parse_payload_strict,
)


def _hello_payload(*versions: str) -> dict[str, object]:
    return {
        "bootstrap_version": "1",
        "id": "h1",
        "op": "session.hello",
        "params": {"interface_versions": list(versions)},
    }


def _request(op: str = "operation.cancel", request_id: str = "17") -> dict[str, object]:
    return {
        "interface_version": INTERFACE_VERSION,
        "id": request_id,
        "op": op,
        "params": {"target_id": "0"},
    }


def test_hello_negotiates_exact_common_version() -> None:
    """verifies: TOOL-UIX-020

    Hello selects the exact common interface version and the reply carries it
    under ``result.interface_version`` (SDD-002 §9.2).
    """
    session = Session()
    reply = session.hello(_hello_payload("9.9", INTERFACE_VERSION))
    assert reply["bootstrap_version"] == "1"
    assert reply["id"] == "h1"
    assert reply["status"] == "ok"
    assert reply["result"] == {"interface_version": INTERFACE_VERSION}
    assert session.negotiated_version == INTERFACE_VERSION


def test_hello_no_common_version_yields_error_envelope_with_both_versions() -> None:
    """verifies: TOOL-UIX-020, TOOL-PLG-060

    Without a common version the reply is the ``NO_COMMON_VERSION`` error
    envelope carrying both the offered and supported versions — the migration
    diagnostic SDD-002 §3 requires.
    """
    session = Session()
    reply = session.hello(_hello_payload("0.9", "2.0"))
    assert reply["status"] == "error"
    assert reply["error"]["code"] == NO_COMMON_VERSION
    assert reply["error"]["details"]["offered"] == ["0.9", "2.0"]
    assert reply["error"]["details"]["supported"] == [INTERFACE_VERSION]
    assert session.negotiated_version is None


def test_operation_before_hello_is_rejected() -> None:
    """verifies: TOOL-UIX-020

    No operation is admitted before hello succeeds (SDD-002 §9.2).
    """
    session = Session()
    request, error = session.handle_request(_request())
    assert request is None
    assert error is not None
    assert error["error"]["code"] == HELLO_REQUIRED


def test_hello_rejects_malformed_params() -> None:
    """A malformed bootstrap envelope is a protocol error, not a correlated
    rejection: the transport closes (SDD-002 §9.2 malformed-envelope rule)."""
    session = Session()
    with pytest.raises(ApiError):
        session.hello({"bootstrap_version": "1", "id": "h1", "op": "session.hello"})


def test_request_with_wrong_negotiated_version_is_rejected_with_versions() -> None:
    """verifies: TOOL-PLG-060

    A post-hello envelope stamped with a different version is rejected with
    both versions in the details.
    """
    session = Session()
    assert session.hello(_hello_payload(INTERFACE_VERSION))["status"] == "ok"
    stale = _request()
    stale["interface_version"] = "0.9"
    request, error = session.handle_request(stale)
    assert request is None
    assert error is not None
    assert error["error"]["code"] == NO_COMMON_VERSION
    assert error["error"]["details"]["envelope_version"] == "0.9"
    assert error["error"]["details"]["negotiated"] == INTERFACE_VERSION


def test_unknown_operation_is_rejected() -> None:
    """verifies: TOOL-UIX-010

    An operation outside the catalogue is an error; no front-end can conjure
    a capability the engine does not publish.
    """
    session = Session()
    session.hello(_hello_payload(INTERFACE_VERSION))
    request, error = session.handle_request(_request(op="gui.only.op"))
    assert request is None
    assert error is not None
    assert error["error"]["code"] == UNKNOWN_OPERATION
    assert error["error"]["details"]["operation"] == "gui.only.op"


def test_invalid_params_are_rejected_with_correlated_id() -> None:
    """verifies: TOOL-UIX-020

    A valid envelope with invalid params receives a correlated error carrying
    the operation's CLI equivalent (SDD-002 §9.2/§9.3).
    """
    session = Session()
    session.hello(_hello_payload(INTERFACE_VERSION))
    bad = _request()
    bad["params"] = "not-a-mapping"
    request, error = session.handle_request(bad)
    assert request is None
    assert error is not None
    assert error["id"] == "17"
    assert error["error"]["code"] == INVALID_PARAMS
    assert error["cli_equivalent"] == session.cli_equivalent_for("operation.cancel")


def test_duplicate_id_is_rejected_within_session() -> None:
    """verifies: TOOL-UIX-020

    Session IDs cannot be reused (SDD-002 §9.2).
    """
    session = Session()
    session.hello(_hello_payload(INTERFACE_VERSION))
    request, error = session.handle_request(_request(request_id="42"))
    assert request is not None
    assert error is None
    request, error = session.handle_request(_request(request_id="42"))
    assert request is None
    assert error is not None
    assert error["error"]["code"] == DUPLICATE_ID


def test_malformed_json_is_rejected() -> None:
    """verifies: TOOL-UIX-020

    Malformed JSON is a protocol error, never coerced (SDD-002 §9.2).
    """
    with pytest.raises(ApiError) as excinfo:
        parse_payload_strict("{not json")
    assert excinfo.value.reason == "malformed_json"


def test_duplicate_json_keys_are_rejected() -> None:
    """verifies: TOOL-UIX-020

    Duplicate JSON keys are rejected (SDD-002 §9.2), not last-wins.
    """
    with pytest.raises(ApiError) as excinfo:
        parse_payload_strict('{"id": "1", "id": "2"}')
    assert excinfo.value.reason == "duplicate_json_key"


def test_non_object_payload_is_rejected() -> None:
    """verifies: TOOL-UIX-020

    A top-level JSON array or scalar is not an envelope.
    """
    with pytest.raises(ApiError) as excinfo:
        parse_payload_strict("[1, 2, 3]")
    assert excinfo.value.reason == "non_object_payload"


def test_malformed_envelope_missing_fields_raise_protocol_error() -> None:
    """An envelope missing required fields cannot be correlated, so it is a
    protocol error for the transport to close on (SDD-002 §9.2)."""
    session = Session()
    session.hello(_hello_payload(INTERFACE_VERSION))
    with pytest.raises(ApiError) as excinfo:
        session.handle_request({"op": "operation.cancel", "params": {}})
    assert excinfo.value.reason == "invalid_request"


def test_error_envelope_shape_has_no_result_field() -> None:
    """verifies: TOOL-UIX-020

    The error envelope carries code/message/retryable/details and no result
    field (SDD-002 §9.2 "alternative terminal failure").
    """
    envelope = error_envelope(
        request_id="19",
        code=INVALID_REQUEST,
        message="bad envelope",
        details={"hint": "check the shape"},
        cli_equivalent="ectt sample",
    )
    assert envelope["status"] == "error"
    assert "result" not in envelope
    assert envelope["error"] == {
        "code": INVALID_REQUEST,
        "message": "bad envelope",
        "retryable": False,
        "details": {"hint": "check the shape"},
    }
    assert envelope["cli_equivalent"] == "ectt sample"
    assert envelope["diagnostics"] == []


def test_parse_payload_strict_accepts_bytes() -> None:
    """Transports hand the parser raw frame bytes; UTF-8 decoding is part of
    the strict contract."""
    payload = parse_payload_strict(b'{"id": "7"}')
    assert payload == {"id": "7"}
    with pytest.raises(ApiError) as excinfo:
        parse_payload_strict(b'{"id": "\xff\xfe"}')
    assert excinfo.value.reason == "malformed_json"

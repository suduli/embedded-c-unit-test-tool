"""Session protocol for the ectt engine API (WP-API-01).

Implements the message layer of SDD-002 §9.2: strict payload parsing, the
``session.hello`` bootstrap negotiation, request-envelope validation with
session-unique IDs, and the correlated error envelope. Transport framing and
the listener live in WP-API-02 (TOOL-UIX-050); this module is what the
transport serves.

Satisfies: TOOL-UIX-010, TOOL-UIX-020, TOOL-PLG-060.
Design: SDD-002 §3 (versioning rule), §9.2 (framing, messages).
"""

from __future__ import annotations

import json
from typing import Any

from ectt.api.catalogue import (
    BOOTSTRAP_VERSION,
    INTERFACE_VERSION,
    SUPPORTED_INTERFACE_VERSIONS,
    Catalogue,
    default_catalogue,
)
from ectt.api.errors import ApiError

__all__ = [
    "Session",
    "error_envelope",
    "parse_payload_strict",
]

#: Error codes of the engine API (SDD-002 §9.2 examples plus the named
#: bootstrap requirements).
NO_COMMON_VERSION = "NO_COMMON_VERSION"
UNKNOWN_OPERATION = "UNKNOWN_OPERATION"
INVALID_PARAMS = "INVALID_PARAMS"
INVALID_REQUEST = "INVALID_REQUEST"
DUPLICATE_ID = "DUPLICATE_ID"
HELLO_REQUIRED = "HELLO_REQUIRED"


def parse_payload_strict(raw: str | bytes) -> dict[str, Any]:
    """Parse one JSON payload, rejecting malformed JSON and duplicate keys.

    SDD-002 §9.2: duplicate JSON keys and malformed UTF-8/JSON are rejected,
    never silently coerced.
    """
    def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        seen: dict[str, Any] = {}
        for key, value in pairs:
            if key in seen:
                raise ApiError(
                    f"duplicate JSON key: {key}",
                    reason="duplicate_json_key",
                )
            seen[key] = value
        return seen

    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ApiError(
                f"payload is not valid UTF-8: {exc}",
                reason="malformed_json",
            ) from None
    try:
        payload = json.loads(raw, object_pairs_hook=_no_duplicates)
    except ApiError:
        raise
    except json.JSONDecodeError as exc:
        raise ApiError(
            f"payload is not valid JSON: {exc.msg} (line {exc.lineno})",
            reason="malformed_json",
        ) from None
    if not isinstance(payload, dict):
        raise ApiError(
            "payload is not a JSON object",
            reason="non_object_payload",
        )
    return payload


def error_envelope(
    *,
    request_id: str,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    cli_equivalent: str | None = None,
    interface_version: str | None = None,
) -> dict[str, Any]:
    """Build a terminal error envelope (SDD-002 §9.2, no ``result`` field).

    ``details`` carries the structured diagnostic; version rejections put both
    versions and the supported-version migration list here (TOOL-PLG-060,
    SDD-002 §3).
    """
    envelope: dict[str, Any] = {
        "interface_version": interface_version if interface_version is not None else INTERFACE_VERSION,
        "id": request_id,
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "retryable": False,
            "details": details if details is not None else {},
        },
        "diagnostics": [],
    }
    if cli_equivalent is not None:
        envelope["cli_equivalent"] = cli_equivalent
    return envelope


class Session:
    """One engine-API session: hello negotiation plus request validation.

    The session tracks negotiated version and used request IDs (SDD-002 §9.2:
    IDs cannot be reused during a session, and no operation is admitted before
    hello succeeds). It holds no transport; a transport (WP-API-02) feeds
    payloads in and writes envelopes out.
    """

    def __init__(self, catalogue: Catalogue | None = None) -> None:
        self._catalogue = catalogue if catalogue is not None else default_catalogue()
        self._negotiated: str | None = None
        self._used_ids: set[str] = set()

    @property
    def negotiated_version(self) -> str | None:
        """The interface version selected by hello, or ``None`` pre-hello."""
        return self._negotiated

    @property
    def catalogue(self) -> Catalogue:
        """The operation catalogue backing this session."""
        return self._catalogue

    def hello(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle the fixed ``session.hello`` bootstrap envelope.

        Selects an exact common version from ``params.interface_versions``;
        on success replies with the negotiated version, otherwise with the
        ``NO_COMMON_VERSION`` error envelope carrying both versions and the
        supported-version migration diagnostic (TOOL-PLG-060).
        """
        request_id = self._bootstrap_id(payload)
        offered = self._bootstrap_versions(payload)
        common = [
            version
            for version in SUPPORTED_INTERFACE_VERSIONS
            if version in offered
        ]
        if not common:
            return error_envelope(
                request_id=request_id,
                code=NO_COMMON_VERSION,
                message=(
                    "no common interface version; "
                    f"offered={sorted(offered)}, "
                    f"supported={list(SUPPORTED_INTERFACE_VERSIONS)}"
                ),
                details={
                    "offered": sorted(offered),
                    "supported": list(SUPPORTED_INTERFACE_VERSIONS),
                },
                interface_version=BOOTSTRAP_VERSION,
            )
        self._negotiated = common[0]
        return {
            "bootstrap_version": BOOTSTRAP_VERSION,
            "id": request_id,
            "status": "ok",
            "result": {"interface_version": self._negotiated},
            "diagnostics": [],
        }

    def handle_request(self, payload: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """Validate one post-hello request envelope.

        Returns ``(request, None)`` for a valid envelope, or ``(None, error)``
        with a correlated error envelope. Every rejection reason in AC-2 is
        checked here: version mismatch, unknown operation, non-mapping params,
        duplicate ID.
        """
        if self._negotiated is None:
            return None, error_envelope(
                request_id=self._string_field(payload, "id", INVALID_REQUEST),
                code=HELLO_REQUIRED,
                message="no operation is admitted before session.hello succeeds",
            )
        request_id = self._string_field(payload, "id", INVALID_REQUEST)
        version = self._string_field(payload, "interface_version", INVALID_REQUEST)
        if version != self._negotiated:
            return None, error_envelope(
                request_id=request_id,
                code=NO_COMMON_VERSION,
                message=(
                    f"envelope version {version!r} does not match "
                    f"negotiated {self._negotiated!r}"
                ),
                details={
                    "envelope_version": version,
                    "negotiated": self._negotiated,
                    "supported": list(SUPPORTED_INTERFACE_VERSIONS),
                },
            )
        op = self._string_field(payload, "op", INVALID_REQUEST)
        if not self._catalogue.has(op):
            return None, error_envelope(
                request_id=request_id,
                code=UNKNOWN_OPERATION,
                message=f"unknown operation: {op}",
                details={"operation": op},
                cli_equivalent=None,
            )
        params = payload.get("params")
        if not isinstance(params, dict):
            return None, error_envelope(
                request_id=request_id,
                code=INVALID_PARAMS,
                message=f"params must be a mapping for operation {op}",
                cli_equivalent=self._catalogue.cli_equivalent_for(op),
            )
        if request_id in self._used_ids:
            return None, error_envelope(
                request_id=request_id,
                code=DUPLICATE_ID,
                message=f"request id already used in this session: {request_id}",
            )
        self._used_ids.add(request_id)
        return payload, None

    def cli_equivalent_for(self, op: str) -> str:
        """Return the catalogue's CLI equivalent for ``op``."""
        return self._catalogue.cli_equivalent_for(op)

    def _bootstrap_id(self, payload: dict[str, Any]) -> str:
        return self._string_field(payload, "id", INVALID_REQUEST)

    def _bootstrap_versions(self, payload: dict[str, Any]) -> list[str]:
        params = payload.get("params")
        if not isinstance(params, dict):
            raise ApiError(
                "session.hello params must be a mapping",
                reason="invalid_params",
            )
        offered = params.get("interface_versions")
        if not isinstance(offered, list) or not offered:
            raise ApiError(
                "session.hello params.interface_versions must be a non-empty list",
                reason="invalid_params",
            )
        for version in offered:
            if not isinstance(version, str) or not version:
                raise ApiError(
                    "session.hello interface_versions entries must be non-empty strings",
                    reason="invalid_params",
                )
        return list(offered)

    @staticmethod
    def _string_field(payload: dict[str, Any], field: str, code: str) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value:
            raise ApiError(
                f"envelope field {field!r} must be a non-empty string",
                reason="invalid_request",
            )
        return value

"""Engine API protocol, operation catalogue and versioning (WP-API-01).

The engine API is the single capability surface of the tool (TOOL-UIX-010):
front-ends are clients of the engine and can never expose a capability the
API cannot express. The interface is versioned JSON (TOOL-UIX-020) negotiated
through a ``session.hello`` bootstrap; breaking changes reject with both
versions and a migration diagnostic (TOOL-PLG-060).

Transport (stdio / local socket, no network listener) is WP-API-02
(TOOL-UIX-050) and is deliberately out of scope here.

Satisfies: TOOL-UIX-010, TOOL-UIX-020, TOOL-PLG-060.
Design: SDD-002 §3 (versioning rule), §9 (S6 engine API).
"""

from __future__ import annotations

from ectt.api.catalogue import (
    BOOTSTRAP_VERSION,
    INTERFACE_VERSION,
    SUPPORTED_INTERFACE_VERSIONS,
    Catalogue,
    Operation,
    default_catalogue,
)
from ectt.api.errors import ApiError
from ectt.api.protocol import Session, error_envelope, parse_payload_strict

__all__ = [
    "ApiError",
    "BOOTSTRAP_VERSION",
    "Catalogue",
    "INTERFACE_VERSION",
    "Operation",
    "SUPPORTED_INTERFACE_VERSIONS",
    "Session",
    "default_catalogue",
    "error_envelope",
    "parse_payload_strict",
]

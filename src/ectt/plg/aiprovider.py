"""AI-provider extension protocol, registration and negotiation (WP-PLG-04).

The AI-provider extension point is defined through the same public surface as
the built-in extension points (WP-PLG-01): a descriptor registered into an
``ExtensionPointRegistry``. Third-party providers register into the public
``AiProviderRegistry`` with a descriptor carrying their interface version and
declared capabilities; a feature resolves a provider through negotiation, and
an incompatible provider is rejected before anything is loaded.

Satisfies: TOOL-PLG-100.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from ectt.plg.errors import (
    DuplicateAiProviderError,
    IncompatibleAiProviderError,
    InvalidAiProviderError,
    UnknownAiProviderError,
)
from ectt.plg.points import (
    ExtensionPoint,
    ExtensionPointRegistry,
    default_registry,
)

__all__ = [
    "AI_PROVIDER_POINT_ID",
    "AI_PROVIDER_CONTRACT",
    "AiProviderDescriptor",
    "AiProviderRegistry",
    "define_ai_provider_extension_point",
]

AI_PROVIDER_POINT_ID = "ai_providers"
AI_PROVIDER_CONTRACT = "ai_provider"

_VERSION_RE = re.compile(r"^([0-9]+)(?:\.([0-9]+))?$")


@dataclass(frozen=True)
class AiProviderDescriptor:
    """A third-party AI-provider registration.

    - ``provider_id``       stable identifier, chosen by the provider author
    - ``interface_version`` dotted-integer version of the provider contract
    - ``capabilities``      declared capability names (open vocabulary)
    - ``factory``           called only after negotiation succeeds
    """

    provider_id: str
    interface_version: str
    capabilities: frozenset[str]
    factory: Callable[[], object]

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise InvalidAiProviderError("AI-provider identifier must be a non-empty string")
        if not isinstance(self.interface_version, str) or not _VERSION_RE.match(
            self.interface_version
        ):
            raise InvalidAiProviderError(
                f"AI-provider '{self.provider_id}' interface_version "
                f"'{self.interface_version}' must be a dotted integer version"
            )
        if not self.capabilities:
            raise InvalidAiProviderError(
                f"AI-provider '{self.provider_id}' must declare at least one capability"
            )
        for capability in self.capabilities:
            if not isinstance(capability, str) or not capability.strip():
                raise InvalidAiProviderError(
                    f"AI-provider '{self.provider_id}' has a non-string or empty capability"
                )
        if not callable(self.factory):
            raise InvalidAiProviderError(
                f"AI-provider '{self.provider_id}' factory must be callable"
            )


def define_ai_provider_extension_point(
    registry: ExtensionPointRegistry | None = None,
) -> ExtensionPoint:
    """Define the AI-provider extension point through the public point surface.

    Structured exactly like the built-in points; a duplicate registration is
    refused by the registry, so defining twice needs a fresh registry.
    """
    point = ExtensionPoint(
        point_id=AI_PROVIDER_POINT_ID,
        title="AI providers",
        description=(
            "Providers implementing the AI-provider contract for any AI-assisted "
            "capability - generative or structured-decision, local or remote, "
            "from any vendor or model architecture - integrated by implementing "
            "the contract instead of modifying tool source."
        ),
        contract=AI_PROVIDER_CONTRACT,
        interface_version="1",
    )
    target = registry if registry is not None else default_registry()
    target.register(point)
    return point


def _parse_version(version: str) -> tuple[int, int]:
    match = _VERSION_RE.match(version)
    assert match is not None  # validation guarantees this
    return int(match.group(1)), int(match.group(2) or 0)


class AiProviderRegistry:
    """Public registry of AI providers with capability/version negotiation."""

    def __init__(self) -> None:
        self._providers: dict[str, AiProviderDescriptor] = {}

    def register(self, provider: AiProviderDescriptor) -> None:
        """Validate and register a provider; reject a reused identifier."""
        if provider.provider_id in self._providers:
            raise DuplicateAiProviderError(
                f"AI provider '{provider.provider_id}' is already registered"
            )
        self._providers[provider.provider_id] = provider

    def resolve(
        self,
        provider_id: str,
        *,
        required_capabilities: frozenset[str] | set[str],
        required_interface_version: str,
    ) -> object:
        """Negotiate and return the provider instance for a feature.

        Negotiation happens before any loading: an unknown identifier or an
        incompatible provider raises a named error and the provider's factory
        is never invoked.
        """
        provider = self._providers.get(provider_id)
        if provider is None:
            raise UnknownAiProviderError(
                f"no AI provider is registered under '{provider_id}'"
            )
        version_match = _VERSION_RE.match(required_interface_version)
        if version_match is None:
            raise IncompatibleAiProviderError(
                f"feature requested invalid interface version "
                f"'{required_interface_version}'"
            )
        required = _parse_version(required_interface_version)
        available = _parse_version(provider.interface_version)
        missing = sorted(set(required_capabilities) - provider.capabilities)
        if missing:
            raise IncompatibleAiProviderError(
                f"AI provider '{provider_id}' does not declare required "
                f"capabilities: {', '.join(missing)}"
            )
        if available[0] != required[0] or available[1] < required[1]:
            raise IncompatibleAiProviderError(
                f"AI provider '{provider_id}' interface version "
                f"'{provider.interface_version}' is incompatible with the "
                f"required '{required_interface_version}'"
            )
        return provider.factory()

    def lookup(self, provider_id: str) -> AiProviderDescriptor:
        """Return the descriptor registered under ``provider_id`` (no loading)."""
        try:
            return self._providers[provider_id]
        except KeyError:
            raise UnknownAiProviderError(
                f"no AI provider is registered under '{provider_id}'"
            ) from None

    def list_ids(self) -> tuple[str, ...]:
        """Registered identifiers, ordered deterministically."""
        return tuple(sorted(self._providers))

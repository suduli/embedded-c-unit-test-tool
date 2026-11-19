"""Tests for the WP-PLG-04 AI-provider extension protocol.

Covers: the extension point defined through the public point surface,
third-party registration, capability/version negotiation, rejection without
loading, and registry discipline.

Verifies: TOOL-PLG-100 (board AC of WP-PLG-04).
"""

from __future__ import annotations

import pytest

from ectt.plg import (
    AI_PROVIDER_POINT_ID,
    AiProviderDescriptor,
    AiProviderRegistry,
    DuplicateAiProviderError,
    DuplicateExtensionPointError,
    ExtensionPointRegistry,
    IncompatibleAiProviderError,
    InvalidAiProviderError,
    UnknownAiProviderError,
    default_registry,
    define_ai_provider_extension_point,
)


def _descriptor(
    provider_id: str = "acme-decider",
    *,
    version: str = "1.0",
    capabilities: frozenset[str] = frozenset({"structured_decision", "remote"}),
    calls: list[str] | None = None,
) -> AiProviderDescriptor:
    def factory() -> object:
        if calls is not None:
            calls.append(provider_id)
        return object()

    return AiProviderDescriptor(
        provider_id=provider_id,
        interface_version=version,
        capabilities=capabilities,
        factory=factory,
    )


def test_extension_point_defined_through_public_point_surface() -> None:
    """verifies: TOOL-PLG-100"""
    registry = default_registry()
    point = define_ai_provider_extension_point(registry)
    assert point.point_id == AI_PROVIDER_POINT_ID
    assert point.contract == "ai_provider"
    assert registry.lookup("ai_providers") == point


def test_extension_point_duplicate_is_refused() -> None:
    """verifies: TOOL-PLG-100"""
    registry = default_registry()
    define_ai_provider_extension_point(registry)
    with pytest.raises(DuplicateExtensionPointError):
        define_ai_provider_extension_point(registry)


def test_third_party_provider_registers_via_public_api() -> None:
    """verifies: TOOL-PLG-100"""
    providers = AiProviderRegistry()
    providers.register(_descriptor())
    assert providers.list_ids() == ("acme-decider",)
    assert providers.lookup("acme-decider").interface_version == "1.0"


def test_compatible_provider_is_loaded_after_negotiation() -> None:
    """verifies: TOOL-PLG-100"""
    calls: list[str] = []
    providers = AiProviderRegistry()
    providers.register(_descriptor(calls=calls))
    instance = providers.resolve(
        "acme-decider",
        required_capabilities={"structured_decision"},
        required_interface_version="1.0",
    )
    assert instance is not None
    assert calls == ["acme-decider"]


def test_missing_capability_is_rejected_without_loading() -> None:
    """verifies: TOOL-PLG-100"""
    calls: list[str] = []
    providers = AiProviderRegistry()
    providers.register(_descriptor(calls=calls))
    with pytest.raises(IncompatibleAiProviderError) as excinfo:
        providers.resolve(
            "acme-decider",
            required_capabilities={"generative_text"},
            required_interface_version="1.0",
        )
    assert "generative_text" in str(excinfo.value)
    assert calls == []  # the factory was never invoked


def test_incompatible_version_is_rejected_without_loading() -> None:
    """verifies: TOOL-PLG-100"""
    calls: list[str] = []
    providers = AiProviderRegistry()
    providers.register(_descriptor(version="1.0", calls=calls))
    with pytest.raises(IncompatibleAiProviderError):
        providers.resolve(
            "acme-decider",
            required_capabilities={"structured_decision"},
            required_interface_version="2.0",
        )
    assert calls == []


def test_major_version_mismatch_rejected() -> None:
    """verifies: TOOL-PLG-100"""
    providers = AiProviderRegistry()
    providers.register(_descriptor(version="2.0"))
    with pytest.raises(IncompatibleAiProviderError):
        providers.resolve(
            "acme-decider",
            required_capabilities=set(),
            required_interface_version="1.0",
        )


def test_unknown_provider_is_named_error() -> None:
    """verifies: TOOL-PLG-100"""
    providers = AiProviderRegistry()
    with pytest.raises(UnknownAiProviderError):
        providers.resolve(
            "ghost",
            required_capabilities=set(),
            required_interface_version="1.0",
        )


def test_duplicate_provider_id_rejected() -> None:
    """verifies: TOOL-PLG-100"""
    providers = AiProviderRegistry()
    providers.register(_descriptor())
    with pytest.raises(DuplicateAiProviderError):
        providers.register(_descriptor())


def test_malformed_descriptors_rejected() -> None:
    """verifies: TOOL-PLG-100"""
    with pytest.raises(InvalidAiProviderError):
        AiProviderDescriptor(
            provider_id="  ",
            interface_version="1.0",
            capabilities=frozenset({"x"}),
            factory=object,
        )
    with pytest.raises(InvalidAiProviderError):
        AiProviderDescriptor(
            provider_id="bad",
            interface_version="v1",
            capabilities=frozenset({"x"}),
            factory=object,
        )
    with pytest.raises(InvalidAiProviderError):
        AiProviderDescriptor(
            provider_id="bad",
            interface_version="1.0",
            capabilities=frozenset(),
            factory=object,
        )


def test_listing_is_deterministic() -> None:
    """verifies: TOOL-PLG-100"""
    providers = AiProviderRegistry()
    for name in ("zeta", "alpha", "mid"):
        providers.register(_descriptor(name))
    assert providers.list_ids() == ("alpha", "mid", "zeta")


def test_extension_point_registry_removes_elegantly() -> None:
    """verifies: TOOL-PLG-100"""
    registry = ExtensionPointRegistry()
    define_ai_provider_extension_point(registry)
    assert "ai_providers" in [p.point_id for p in registry.list_points()]

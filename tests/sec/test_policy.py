"""Inspection evidence for the WP-SEC-05 security policy.

The tests verify the structured policy data is complete, frozen and
deterministic; the prose itself is inspected in
docs/verification/WP-SEC-05-analysis.md.

Verifies: TOOL-SEC-080.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.sec import (
    ACKNOWLEDGEMENT_COMMITMENT,
    REPORT_CONTENT_ITEMS,
    REPORTING_CHANNEL,
    SUPPORTED_VERSIONS_RULE,
    DisclosurePolicy,
    disclosure_policy,
)


def test_policy_exposes_a_private_reporting_channel() -> None:
    """verifies: TOOL-SEC-080"""
    policy = disclosure_policy()
    assert policy.reporting_channel.strip()
    assert "private" in policy.reporting_channel.lower()
    assert policy.reporting_channel == REPORTING_CHANNEL


def test_policy_states_expected_report_content() -> None:
    """verifies: TOOL-SEC-080"""
    policy = disclosure_policy()
    assert len(REPORT_CONTENT_ITEMS) >= 3
    assert all(item.strip() for item in policy.report_content)


def test_policy_states_acknowledgement_and_resolution_commitments() -> None:
    """verifies: TOOL-SEC-080"""
    policy = disclosure_policy()
    assert ACKNOWLEDGEMENT_COMMITMENT.strip()
    assert "acknowledge" in policy.acknowledgement.lower()
    assert policy.resolution_days > 0


def test_policy_states_a_supported_version_rule() -> None:
    """verifies: TOOL-SEC-080"""
    policy = disclosure_policy()
    assert SUPPORTED_VERSIONS_RULE.strip()
    assert "1.0" in policy.supported_versions_condition


def test_policy_data_is_frozen() -> None:
    """verifies: TOOL-SEC-080"""
    policy = disclosure_policy()
    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.resolution_days = 1  # type: ignore[misc]


def test_policy_data_is_deterministic() -> None:
    """verifies: TOOL-SEC-080"""
    first = disclosure_policy().to_dict()
    second = disclosure_policy().to_dict()
    assert first == second


def test_policy_carries_an_explicit_state_marker() -> None:
    """verifies: TOOL-SEC-080"""
    policy = disclosure_policy()
    assert policy.policy_version
    assert policy.state == "owner-review-draft"


def test_policy_type_is_frozen_dataclass() -> None:
    """verifies: TOOL-SEC-080"""
    assert dataclasses.is_dataclass(DisclosurePolicy)

"""Security disclosure process and supported-version policy (WP-SEC-05).

The structured carrier of the project's security policy. The authoritative
prose lives in ``docs/verification/WP-SEC-05-analysis.md``; this module makes
the same policy machine-readable so tools and tests can verify it stays
complete. The commitments are owner-review drafts (see the analysis note).

Satisfies: TOOL-SEC-080.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "POLICY_STATE",
    "SECURITY_POLICY_VERSION",
    "REPORTING_CHANNEL",
    "REPORT_CONTENT_ITEMS",
    "ACKNOWLEDGEMENT_COMMITMENT",
    "RESOLUTION_COMMITMENT_DAYS",
    "SUPPORTED_VERSIONS_RULE",
    "SUPPORTED_VERSIONS_CONDITION",
    "DisclosurePolicy",
    "disclosure_policy",
]

# Version of the policy document itself, so a reader can tell which text it got.
SECURITY_POLICY_VERSION = "1"
POLICY_STATE = "owner-review-draft"

REPORTING_CHANNEL = (
    "GitHub Security Advisories (private vulnerability reporting) on this "
    "repository. Do not open a "
    "public issue for an unpatched vulnerability."
)

REPORT_CONTENT_ITEMS = (
    "affected version(s) or commit",
    "minimal reproduction (steps, inputs, configuration)",
    "observed impact",
    "affected component, if known",
)

ACKNOWLEDGEMENT_COMMITMENT = (
    "acknowledge a valid report within 5 business days of receipt"
)

RESOLUTION_COMMITMENT_DAYS = 90

SUPPORTED_VERSIONS_RULE = (
    "pre-1.0: security fixes are released only for the latest release line; "
    "older pre-release lines receive no security fixes and users must upgrade"
)

SUPPORTED_VERSIONS_CONDITION = (
    "from 1.0 onward this rule is replaced by the release policy the owner "
    "publishes at 1.0; until then the pre-1.0 rule applies and no document "
    "claims more"
)


@dataclass(frozen=True)
class DisclosurePolicy:
    """The complete machine-readable security policy."""

    policy_version: str
    state: str
    reporting_channel: str
    report_content: tuple[str, ...]
    acknowledgement: str
    resolution_days: int
    supported_versions_rule: str
    supported_versions_condition: str

    def to_dict(self) -> dict[str, object]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "acknowledgement": self.acknowledgement,
            "policy_version": self.policy_version,
            "report_content": list(self.report_content),
            "reporting_channel": self.reporting_channel,
            "resolution_days": self.resolution_days,
            "state": self.state,
            "supported_versions_condition": self.supported_versions_condition,
            "supported_versions_rule": self.supported_versions_rule,
        }


def disclosure_policy() -> DisclosurePolicy:
    """The current security policy. Deterministic: identical on every call."""
    return DisclosurePolicy(
        policy_version=SECURITY_POLICY_VERSION,
        state=POLICY_STATE,
        reporting_channel=REPORTING_CHANNEL,
        report_content=REPORT_CONTENT_ITEMS,
        acknowledgement=ACKNOWLEDGEMENT_COMMITMENT,
        resolution_days=RESOLUTION_COMMITMENT_DAYS,
        supported_versions_rule=SUPPORTED_VERSIONS_RULE,
        supported_versions_condition=SUPPORTED_VERSIONS_CONDITION,
    )

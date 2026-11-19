"""ECTT Security and Integrity.

Provides the machine-readable security disclosure process and supported-version
policy (WP-SEC-05) and the diagnostic content control surface (WP-SEC-04); the
authoritative prose for the policy is in the WP-SEC-05 analysis note.
"""

from ectt.sec.configuration_data import (
    ConfigurationIsNotDataError,
    validate_configuration_is_data,
)
from ectt.sec.diagnostics import (
    BUNDLE_ENTRIES,
    BUNDLE_EXCLUSIONS,
    MIN_SOURCE_LINE_LENGTH,
    DiagnosticBundleManifest,
    assert_no_source_content,
    bundle_manifest,
    location_reference,
)
from ectt.sec.errors import SecError, SourceContentInDiagnosticError
from ectt.sec.policy import (
    ACKNOWLEDGEMENT_COMMITMENT,
    POLICY_STATE,
    REPORT_CONTENT_ITEMS,
    REPORTING_CHANNEL,
    RESOLUTION_COMMITMENT_DAYS,
    SECURITY_POLICY_VERSION,
    SUPPORTED_VERSIONS_CONDITION,
    SUPPORTED_VERSIONS_RULE,
    DisclosurePolicy,
    disclosure_policy,
)
from ectt.sec.trust import (
    TRUST_RECORD_SCHEMA_VERSION,
    TrustDecision,
    TrustRecordError,
    UntrustedProjectTracker,
    warning_text,
)
from ectt.sec.untrusted import (
    RESULT_LINE_KINDS,
    TargetResultLine,
    UntrustedPayload,
    mark_untrusted,
    parse_target_output,
)

__all__ = [
    # Diagnostic content control (WP-SEC-04)
    "SecError",
    "SourceContentInDiagnosticError",
    "MIN_SOURCE_LINE_LENGTH",
    "BUNDLE_ENTRIES",
    "BUNDLE_EXCLUSIONS",
    "DiagnosticBundleManifest",
    "bundle_manifest",
    "location_reference",
    "assert_no_source_content",
    # Configuration-is-data and trust gate (WP-SEC-03)
    "ConfigurationIsNotDataError",
    "validate_configuration_is_data",
    "TRUST_RECORD_SCHEMA_VERSION",
    "TrustDecision",
    "TrustRecordError",
    "UntrustedProjectTracker",
    "warning_text",
    # Untrusted target data (WP-SEC-07)
    "RESULT_LINE_KINDS",
    "UntrustedPayload",
    "TargetResultLine",
    "mark_untrusted",
    "parse_target_output",
    # Security policy (WP-SEC-05)
    "ACKNOWLEDGEMENT_COMMITMENT",
    "POLICY_STATE",
    "REPORT_CONTENT_ITEMS",
    "REPORTING_CHANNEL",
    "RESOLUTION_COMMITMENT_DAYS",
    "SECURITY_POLICY_VERSION",
    "SUPPORTED_VERSIONS_CONDITION",
    "SUPPORTED_VERSIONS_RULE",
    "DisclosurePolicy",
    "disclosure_policy",
]

# implements: TOOL-TGT-130
"""The versioned host profile (TOOL-TGT-130, DSN-EXT-110).

Executing a test on the host on behalf of a target build is governed by a
versioned profile that records the target-to-host derivation — target and host
triples, flag and define changes, substituted platform headers, and what the
host does when the code touches hardware the host does not have — together
with its **known** ABI differences (widths, alignment, packing, endianness,
signedness). A difference that was never measured is not guessed: it is
reported as ``unknown`` (never as "same"), so a host success can never pass
for target evidence.

The profile is a digest-bound record (like the compiled-suite record): its id
is derived from its canonical content, tampering is refused on load and on
use, and identical inputs give byte-identical dumps.

Every host-executed result is labelled with the profile it ran under
(:func:`label_host_results`); the label rides beside the result set, since the
runner's own records are its territory.

Satisfies: TOOL-TGT-130.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from ectt.core.determinism import canonical_json, stable_id
from ectt.exh.results import ResultSet
from ectt.ext.errors import ExtError

__all__ = [
    "ABI_DIMENSIONS",
    "HOST_PROFILE_VERSION",
    "UNKNOWN_ABI",
    "HostProfile",
    "LabelledResults",
    "ProfileError",
    "ResultLabel",
    "abi_difference",
    "profile_is_intact",
    "dump_host_profile",
    "label_host_results",
    "load_host_profile",
    "record_host_profile",
]

HOST_PROFILE_VERSION = "1"

#: The ABI dimensions a profile may record. A dimension absent from the
#: mapping was never measured and stays explicitly unknown.
ABI_DIMENSIONS: tuple[str, ...] = ("width", "alignment", "packing", "endianness", "signedness")

#: What an unmeasured difference reports as, and that it is not a measurement.
UNKNOWN_ABI = "unknown"

_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
_TOKEN_RE = re.compile(r"^\S{1,128}$")


class ProfileError(ExtError):
    """A host profile was malformed, tampered with, or misused."""

    def __init__(self, message: str, *, reason: str = "profile_error") -> None:
        super().__init__(message, reason=reason)


def _profile_id(body: Mapping[str, Any]) -> str:
    return stable_id(canonical_json(dict(body)))


@dataclass(frozen=True)
class HostProfile:
    """The recorded target-to-host derivation and its measured ABI gaps."""

    name: str
    target_triple: str
    host_triple: str
    flag_changes: tuple[str, ...] = ()
    define_changes: tuple[str, ...] = ()
    substituted_headers: tuple[str, ...] = ()
    #: What the host does when the UUT touches hardware the host lacks
    #: (for example: "the access is diagnosed and the test fails"). Never empty.
    unavailable_hardware_behavior: str = ""
    #: Measured ABI differences by dimension; every dimension of
    #: :data:`ABI_DIMENSIONS` not present here is explicitly unknown.
    abi: Mapping[str, str] = field(default_factory=dict)
    profile_version: str = HOST_PROFILE_VERSION
    profile_id: str = ""

    def body(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (sorted, deterministic)."""
        return {
            "abi": dict(sorted(self.abi.items())),
            "define_changes": list(self.define_changes),
            "flag_changes": list(self.flag_changes),
            "host_triple": self.host_triple,
            "name": self.name,
            "substituted_headers": list(self.substituted_headers),
            "target_triple": self.target_triple,
            "unavailable_hardware_behavior": self.unavailable_hardware_behavior,
        }

    @property
    def label(self) -> str:
        """The deterministic token every host-executed result carries."""
        return f"{self.name}@{self.profile_version}#{self.profile_id[:12]}"


def _validate(profile: HostProfile) -> None:
    if not _NAME_RE.match(profile.name or ""):
        raise ProfileError(f"profile name {profile.name!r} must be a simple token", reason="invalid_profile_name")
    for what, value in (("target_triple", profile.target_triple), ("host_triple", profile.host_triple)):
        if not _TOKEN_RE.match(value or ""):
            raise ProfileError(f"profile {what} must be a non-empty token", reason="invalid_profile_field")
    for field_name in ("flag_changes", "define_changes", "substituted_headers"):
        for entry in getattr(profile, field_name):
            if not isinstance(entry, str) or not _TOKEN_RE.match(entry):
                raise ProfileError(
                    f"profile {field_name} entry {entry!r} must be a non-empty token without whitespace",
                    reason="invalid_profile_field",
                )
    if not isinstance(profile.unavailable_hardware_behavior, str) or not profile.unavailable_hardware_behavior.strip():
        raise ProfileError(
            "a profile must record what the host does when the UUT touches unavailable hardware",
            reason="missing_hardware_behavior",
        )
    unknown = sorted(set(profile.abi) - set(ABI_DIMENSIONS))
    if unknown:
        raise ProfileError(
            f"profile records ABI dimensions that are not measurable ones: {', '.join(unknown)} "
            f"(measurable: {', '.join(ABI_DIMENSIONS)})",
            reason="unknown_abi_dimension",
        )
    for dimension, value in profile.abi.items():
        if not isinstance(value, str) or not value.strip():
            raise ProfileError(
                f"ABI dimension '{dimension}' has no measured value; leave it out to stay unknown",
                reason="invalid_abi_value",
            )


def record_host_profile(
    *,
    name: str,
    target_triple: str,
    host_triple: str,
    flag_changes: tuple[str, ...] = (),
    define_changes: tuple[str, ...] = (),
    substituted_headers: tuple[str, ...] = (),
    unavailable_hardware_behavior: str = "",
    abi: Mapping[str, str] | None = None,
) -> HostProfile:
    """Record a host profile; identical inputs give identical ids."""
    profile = HostProfile(
        name=name,
        target_triple=target_triple,
        host_triple=host_triple,
        flag_changes=tuple(flag_changes),
        define_changes=tuple(define_changes),
        substituted_headers=tuple(substituted_headers),
        unavailable_hardware_behavior=unavailable_hardware_behavior,
        abi=dict(sorted((abi or {}).items())),
    )
    _validate(profile)
    return replace(profile, profile_id=_profile_id(profile.body()))


def profile_is_intact(profile: HostProfile) -> bool:
    """True when the profile's id still binds its content (untampered)."""
    return bool(profile.profile_id) and _profile_id(profile.body()) == profile.profile_id


def abi_difference(profile: HostProfile, dimension: str) -> tuple[str, bool]:
    """The difference of one ABI dimension: ``(value, measured)``.

    A dimension the profile never measured reports ``("unknown", False)`` —
    never a guess (TOOL-TGT-130).
    """
    if dimension not in ABI_DIMENSIONS:
        raise ProfileError(
            f"'{dimension}' is not an ABI dimension (measurable: {', '.join(ABI_DIMENSIONS)})",
            reason="unknown_abi_dimension",
        )
    value = profile.abi.get(dimension)
    return (value, True) if value is not None else (UNKNOWN_ABI, False)


def dump_host_profile(profile: HostProfile) -> str:
    """Deterministic JSON text of a profile."""
    return canonical_json({"profile_id": profile.profile_id, "profile_version": HOST_PROFILE_VERSION, **profile.body()})


def load_host_profile(text: str) -> HostProfile:
    """Strictly load a profile; refuses unknown versions and tampering."""
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProfileError(f"host profile is not valid JSON: {exc}", reason="invalid_profile") from exc
    if not isinstance(doc, dict) or doc.get("profile_version") != HOST_PROFILE_VERSION:
        raise ProfileError(
            f"unsupported host profile (expected profile_version {HOST_PROFILE_VERSION!r})",
            reason="unsupported_profile_version",
        )
    required = ("host_triple", "name", "profile_id", "target_triple", "unavailable_hardware_behavior")
    missing = [key for key in required if key not in doc]
    if missing:
        raise ProfileError(f"host profile is missing {', '.join(missing)}", reason="invalid_profile")
    try:
        profile = HostProfile(
            name=str(doc["name"]),
            target_triple=str(doc["target_triple"]),
            host_triple=str(doc["host_triple"]),
            flag_changes=tuple(str(f) for f in doc.get("flag_changes", ())),
            define_changes=tuple(str(d) for d in doc.get("define_changes", ())),
            substituted_headers=tuple(str(h) for h in doc.get("substituted_headers", ())),
            unavailable_hardware_behavior=str(doc["unavailable_hardware_behavior"]),
            abi={str(k): str(v) for k, v in dict(doc.get("abi", {})).items()},
            profile_id=str(doc["profile_id"]),
        )
    except (TypeError, ValueError) as exc:
        raise ProfileError(f"host profile has a malformed field: {exc}", reason="invalid_profile") from exc
    _validate(profile)
    if _profile_id(profile.body()) != profile.profile_id:
        raise ProfileError("stored host profile id does not match its content", reason="digest_mismatch")
    return profile


# --- labelling host-executed results ---------------------------------------------------------------


@dataclass(frozen=True)
class ResultLabel:
    """The profile one executed test ran under (TOOL-TGT-130)."""

    test_id: str
    outcome: str
    profile_id: str
    profile_label: str


@dataclass(frozen=True)
class LabelledResults:
    """A host result set with, beside it, the profile of every result."""

    profile: HostProfile
    result_set: ResultSet
    labels: tuple[ResultLabel, ...]


def label_host_results(profile: HostProfile, result_set: ResultSet) -> LabelledResults:
    """Label every result of a host execution with its execution profile.

    The runner's result records are its territory (ectt.exh); the label rides
    beside them, one per result, deterministic, and bound to the profile id —
    a result whose label and content disagree is detectable downstream.
    """
    if not profile_is_intact(profile):
        raise ProfileError("host profile id does not match its content", reason="digest_mismatch")
    labels = tuple(
        ResultLabel(test_id=r.test_id, outcome=r.outcome, profile_id=profile.profile_id, profile_label=profile.label)
        for r in result_set.results
    )
    return LabelledResults(profile=profile, result_set=result_set, labels=labels)

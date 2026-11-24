# implements: TOOL-NFR-100
"""Software Bill of Materials generation, CycloneDX 1.5 (WP-SEC-01).

Generates the SBOM of the tool and its installed dependencies as a CycloneDX
1.5 JSON document. Field names are taken from the CycloneDX 1.5 JSON schema
(``schema/bom-1.5.schema.json``, repository ``github.com/CycloneDX/specification``,
tag ``1.5`` — recorded in docs/verification/WP-SEC-01-analysis.md), not from
memory: the required top-level ``bomFormat``/``specVersion``/``version``, the
``metadata.component`` the BOM describes, and per-component ``type``/``name``
(required) with ``version``, ``purl``, ``licenses`` (``{"license": {"name":
...}}`` — the installed ``License`` metadata is free text, so names are used
verbatim rather than unverified SPDX ids) and ``hashes``
(``{"alg": "SHA-256", "content": ...}``) only where a hash is recorded.

Sorted and byte-stable: components in name order, keys serialized sorted, no
timestamps, and a ``serialNumber`` only when the caller injects one. A package
whose licence is absent or empty is reported as **unknown** — its component
carries no ``licenses`` key and its name lands in the result's
``licences_unknown``; a licence is never invented.

Release signing needs keys the owner holds: signing is **not** implemented.
The result carries the named marker ``signing_not_configured`` and the document
contains no ``signature`` field.

The installed metadata is read through an injected reader; the default reads
``importlib.metadata`` (name, version, ``License``). Installed distributions
record no package-artifact hash this tool can trust, so the default reader
reports none rather than inventing one.

Satisfies: the supply-chain transparency requirement of the security policy.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, cast

from ectt.sec.errors import SecError

__all__ = [
    "SIGNING_NOT_CONFIGURED",
    "SbomComponent",
    "SbomResult",
    "dump_sbom",
    "generate_sbom",
    "read_installed_packages",
]

#: The named marker that release signing is not configured (owner-held keys).
SIGNING_NOT_CONFIGURED = "signing_not_configured"

#: The specification this generator implements (recorded, per the item).
CYCLONEDX_SPEC_VERSION = "1.5"

_CYCLONEDX_SCHEMA = "http://cyclonedx.org/schema/bom-1.5.schema.json"

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class InstalledPackage:
    """What the reader knows about one installed distribution."""

    name: str
    version: str
    licence: str | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class SbomComponent:
    """One component of the SBOM (tool or dependency)."""

    name: str
    version: str
    licence: str | None = None
    sha256: str | None = None
    is_tool: bool = False

    def __post_init__(self) -> None:
        if not _NAME_RE.match(self.name or ""):
            raise SecError(f"component name {self.name!r} is not a package name", reason="invalid_component")
        if not self.version or not isinstance(self.version, str):
            raise SecError(f"component '{self.name}' has no version", reason="invalid_component")
        if self.sha256 is not None and not _SHA256_RE.match(self.sha256):
            raise SecError(
                f"component '{self.name}' has a malformed SHA-256 hash",
                reason="invalid_component",
            )


def _component_dict(component: SbomComponent) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "type": "application" if component.is_tool else "library",
        "name": component.name,
        "version": component.version,
        "purl": f"pkg:pypi/{component.name.lower()}@{component.version}",
    }
    if component.licence is not None and component.licence.strip():
        entry["licenses"] = [{"license": {"name": component.licence.strip()}}]
    if component.sha256 is not None:
        entry["hashes"] = [{"alg": "SHA-256", "content": component.sha256}]
    return entry


@dataclass(frozen=True)
class SbomResult:
    """The generated document plus the disclosures that ride beside it."""

    document: dict[str, Any]
    #: Names of the components whose licence is absent or empty (never invented).
    licences_unknown: tuple[str, ...]
    #: The named marker: signing needs owner-held keys and is not implemented.
    signing: str = SIGNING_NOT_CONFIGURED


def generate_sbom(
    packages: Iterable[SbomComponent],
    *,
    tool_name: str = "ectt",
    serial_number: str | None = None,
) -> SbomResult:
    """Generate the CycloneDX 1.5 document for the tool and its dependencies.

    Components are sorted by name; the tool (``tool_name``) becomes
    ``metadata.component`` with type ``application``, every other package is a
    ``library``. A ``serialNumber`` is included only when injected (``urn:uuid:``
    form per the spec). The result names every package whose licence is unknown
    and carries the ``signing_not_configured`` marker; the document itself
    carries no ``signature`` field.
    """
    ordered = sorted(packages, key=lambda p: p.name)
    seen: set[str] = set()
    for component in ordered:
        if component.name in seen:
            raise SecError(
                f"two components are named '{component.name}'",
                reason="invalid_component",
            )
        seen.add(component.name)

    tool = next((p for p in ordered if p.name == tool_name), None)
    if tool is None:
        raise SecError(
            f"the SBOM must describe the tool itself, but no component named "
            f"'{tool_name}' was supplied",
            reason="tool_missing",
        )

    licences_unknown = tuple(
        p.name for p in ordered if p.licence is None or not p.licence.strip()
    )

    metadata: dict[str, Any] = {"component": _component_dict(tool)}
    document: dict[str, Any] = {
        "$schema": _CYCLONEDX_SCHEMA,
        "bomFormat": "CycloneDX",
        "specVersion": CYCLONEDX_SPEC_VERSION,
        "version": 1,
        "metadata": metadata,
        "components": [_component_dict(p) for p in ordered if p.name != tool_name],
    }
    if serial_number is not None:
        if not serial_number.startswith("urn:uuid:"):
            raise SecError(
                "serialNumber must be a URN UUID (urn:uuid:...) per the CycloneDX spec",
                reason="invalid_serial_number",
            )
        document["serialNumber"] = serial_number

    return SbomResult(document=document, licences_unknown=licences_unknown)


def dump_sbom(result: SbomResult) -> str:
    """The byte-stable JSON text of the document (sorted keys, fixed indent)."""
    import json

    return json.dumps(result.document, sort_keys=True, indent=1)


def read_installed_packages() -> tuple[InstalledPackage, ...]:
    """The installed distributions as the SBOM sees them (default reader).

    Reads ``importlib.metadata``: name, version and the ``License`` metadata
    field. Installed distributions record no package-artifact hash this tool
    can trust, so no hash is reported rather than inventing one. Packages whose
    licence metadata is absent or empty carry ``licence=None`` and are reported
    as unknown by the generator.
    """
    import importlib.metadata

    packages: list[InstalledPackage] = []
    seen: set[str] = set()
    for distribution in importlib.metadata.distributions():
        # PackageMetadata is a message-like object at run time; the cast makes
        # the Mapping view explicit for both mypy and the .get calls below.
        metadata = cast(Mapping[str, str], distribution.metadata)
        name = metadata.get("Name", "")
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        licence = metadata.get("License", "").strip() or None
        packages.append(
            InstalledPackage(name=name, version=distribution.version or "", licence=licence)
        )
    return tuple(sorted(packages, key=lambda p: p.name.lower()))

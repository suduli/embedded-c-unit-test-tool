# implements: TOOL-NFR-100
"""SBOM generation, CycloneDX 1.5 (WP-SEC-01).

Field names are taken from the CycloneDX 1.5 JSON schema (recorded in the
analysis note). The output is sorted and byte-stable, a missing licence is
reported as unknown (never invented), hashes appear only where recorded, and
signing is the named not-configured marker.
"""

from __future__ import annotations

import json

import pytest

from ectt.sec import (
    SIGNING_NOT_CONFIGURED,
    SbomComponent,
    SecError,
    dump_sbom,
    generate_sbom,
    read_installed_packages,
)

TOOL = SbomComponent(
    name="ectt", version="0.1.0", licence="MIT", sha256="a" * 64, is_tool=True
)
DEPENDENCY_A = SbomComponent(name="attrs", version="26.1.0", licence="MIT")
DEPENDENCY_B = SbomComponent(
    name="pyyaml", version="6.0.4", licence="BSD-3-Clause", sha256="b" * 64
)
DEPENDENCY_NO_LICENCE = SbomComponent(name="mystery", version="1.0.0")


def test_the_document_uses_the_cyclonedx_15_field_names() -> None:
    """verifies: WP-SEC-01 AC-1 — spec field names, taken from the CycloneDX 1.5
    JSON schema (source recorded in the analysis note)."""
    result = generate_sbom([DEPENDENCY_A, TOOL, DEPENDENCY_B])
    document = result.document
    assert document["bomFormat"] == "CycloneDX"
    assert document["specVersion"] == "1.5"
    assert document["version"] == 1
    tool = document["metadata"]["component"]
    assert tool["type"] == "application" and tool["name"] == "ectt"
    assert tool["licenses"] == [{"license": {"name": "MIT"}}]
    assert tool["hashes"] == [{"alg": "SHA-256", "content": "a" * 64}]
    names = [c["name"] for c in document["components"]]
    assert names == ["attrs", "pyyaml"]  # the tool is metadata.component, not in components
    (dependency,) = [c for c in document["components"] if c["name"] == "pyyaml"]
    assert dependency["type"] == "library"
    assert dependency["purl"] == "pkg:pypi/pyyaml@6.0.4"


def test_the_output_is_byte_stable_and_sorted() -> None:
    """verifies: WP-SEC-01 AC-2 — components sorted by name, keys sorted, no
    timestamps; identical inputs give byte-identical text."""
    result = generate_sbom([DEPENDENCY_B, TOOL, DEPENDENCY_A])
    first = dump_sbom(result)
    second = dump_sbom(generate_sbom([DEPENDENCY_A, DEPENDENCY_B, TOOL]))
    assert first == second  # order-independent and stable
    document = json.loads(first)
    assert [c["name"] for c in document["components"]] == ["attrs", "pyyaml"]
    assert list(json.loads(first).keys()) == sorted(json.loads(first).keys())
    assert "timestamp" not in first


def test_a_missing_licence_is_reported_unknown() -> None:
    """verifies: WP-SEC-01 AC-3 — no licence metadata means no licenses key and
    the name in licences_unknown; a licence is never invented."""
    result = generate_sbom([TOOL, DEPENDENCY_A, DEPENDENCY_B, DEPENDENCY_NO_LICENCE])
    assert result.licences_unknown == ("mystery",)
    (component,) = [c for c in result.document["components"] if c["name"] == "mystery"]
    assert "licenses" not in component


def test_hashes_appear_only_where_recorded() -> None:
    """verifies: WP-SEC-01 AC-1 — a recorded hash becomes a spec hash entry; an
    unrecorded one is omitted, never invented."""
    result = generate_sbom([TOOL, DEPENDENCY_A, DEPENDENCY_B])
    (attrs,) = [c for c in result.document["components"] if c["name"] == "attrs"]
    assert "hashes" not in attrs
    (pyyaml,) = [c for c in result.document["components"] if c["name"] == "pyyaml"]
    assert pyyaml["hashes"] == [{"alg": "SHA-256", "content": "b" * 64}]


def test_serial_number_only_when_injected() -> None:
    """verifies: WP-SEC-01 AC-2 — the document carries a serialNumber only when
    the caller injects one, in the spec's URN UUID form."""
    without = generate_sbom([TOOL])
    assert "serialNumber" not in without.document
    with_serial = generate_sbom([TOOL], serial_number="urn:uuid:12345678-1234-5678-1234-567812345678")
    assert with_serial.document["serialNumber"] == "urn:uuid:12345678-1234-5678-1234-567812345678"
    with pytest.raises(SecError) as excinfo:
        generate_sbom([TOOL], serial_number="not-a-urn")
    assert excinfo.value.reason == "invalid_serial_number"


def test_signing_is_reported_not_configured() -> None:
    """verifies: WP-SEC-01 AC-4 — signing is not implemented: the named marker
    rides on the result and the document carries no signature field."""
    result = generate_sbom([TOOL])
    assert result.signing == SIGNING_NOT_CONFIGURED
    assert "signature" not in json.dumps(result.document)


def test_the_tool_itself_must_be_described() -> None:
    """verifies: WP-SEC-01 AC-5 — an SBOM without the tool component is refused."""
    with pytest.raises(SecError) as excinfo:
        generate_sbom([DEPENDENCY_A])
    assert excinfo.value.reason == "tool_missing"
    with pytest.raises(SecError):
        generate_sbom([TOOL, SbomComponent(name="ectt", version="0.1.0")])


def test_the_default_reader_finds_this_tool() -> None:
    """verifies: WP-SEC-01 AC-5 — the production reader reads the installed
    metadata: the ectt distribution is present with a version."""
    packages = read_installed_packages()
    ectt = [p for p in packages if p.name.lower() == "ectt"]
    assert len(ectt) == 1
    assert ectt[0].version
    assert all(p.name for p in packages)

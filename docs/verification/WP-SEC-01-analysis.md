# Verification Analysis Note — WP-SEC-01 (Software Bill of Materials Generation)

Lane: A (night run) · 2026-11-23 · Worktree `wt-night-23a`, branch `glm-night/20261123-a`, baseline local `main` (80cf5c6).

## Specification source (recorded, per the item)

CycloneDX field names are taken from the **CycloneDX 1.5 JSON schema,
`schema/bom-1.5.schema.json`, repository `github.com/CycloneDX/specification`, tag
`1.5`** (fetched 2026-11-23), not from memory. Verified facts used here: the
top-level required fields are `bomFormat` (literal `"CycloneDX"`), `specVersion`
(`"1.5"`) and `version` (integer); `serialNumber` is optional (URN UUID form);
`metadata.component` is the component the BOM describes; a component requires
`type` and `name` with optional `version`, `hashes`, `licenses`, `purl`; a hash
entry is exactly `{"alg", "content"}` with `alg` from the spec enum (`"SHA-256"`
used here); a license entry is `{"license": {"id" | "name"}}`.

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for
WP-SEC-01. Derived from the SRS-001 text (TOOL-QUA-050/060 context and the
security policy's supply-chain requirement):

- **AC-1:** the generator emits a CycloneDX 1.5 JSON document with exactly the
  spec's field names: `bomFormat`, `specVersion`, `version`, `metadata.component`
  (the tool), and one `components` entry per installed package with `type`,
  `name`, `version`, `purl`, `licenses` (as `{"license": {"name": ...}}` since the
  installed metadata is free text, not verified SPDX ids) and `hashes`
  (`{"alg": "SHA-256", "content": ...}`) only where a hash is recorded.
- **AC-2:** the output is sorted and byte-stable: components in name order, keys
  serialized sorted, no timestamps unless injected (a `serialNumber` is included
  only when the caller injects one).
- **AC-3:** a package whose licence metadata is absent or empty is reported as
  unknown — its component carries no `licenses` key and its name appears in the
  result's `licences_unknown`; a licence is never invented.
- **AC-4:** signing is not implemented (the keys are the owner's): the result
  carries the named marker `signing_not_configured` and the document contains no
  `signature` field.
- **AC-5:** the installed metadata is read through an injected reader (default:
  `importlib.metadata`), so the generator is testable with fake packages and the
  production reader stays a thin, replaceable adapter.

## Implementation

- `src/ectt/sec/sbom.py` — `InstalledPackage` (name, version, licence, recorded
  hash), `read_installed_packages` (default `importlib.metadata` adapter, name and
  version plus the `License` metadata field; no hash is invented for installed
  distributions), `SbomComponent`/`generate_sbom`/`dump_sbom` (the deterministic
  CycloneDX 1.5 document and its byte-stable serialisation), `SbomResult`
  (document + `licences_unknown` + `signing_not_configured`).
- `tests/sec/test_sbom.py` — the AC checks (fake package lists only; the default
  reader is exercised for the tool's own metadata presence).

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/sec/`) |
|---|---|---|
| Supply-chain transparency for the release (SBOM of the tool and its dependencies) | `sbom.py` (`generate_sbom`, `dump_sbom`, `read_installed_packages`) | `test_sbom.py::test_the_document_uses_the_cyclonedx_15_field_names`, `::test_the_output_is_byte_stable_and_sorted`, `::test_a_missing_licence_is_reported_unknown`, `::test_hashes_appear_only_where_recorded`, `::test_serial_number_only_when_injected`, `::test_signing_is_reported_not_configured`, `::test_the_default_reader_finds_this_tool` |

## Not covered by this increment

- **Release signing** — needs keys the owner holds; recorded as the named result
  `signing_not_configured` and as a second-pass row (owner decision on key
  management and the signing mechanism).
- **SPDX licence-id normalisation** — the installed `License` metadata is free
  text; emitting `license.id` would require verifying each id against the SPDX
  list, which this machine cannot do offline. Names are used verbatim.
- **Vulnerability/dependency-graph sections** — the item scopes the SBOM to
  component inventory; `dependencies`/`vulnerabilities` are later work.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.

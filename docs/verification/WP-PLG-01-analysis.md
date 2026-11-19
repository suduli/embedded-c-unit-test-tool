# Verification Analysis Note — WP-PLG-01 (Extension Point Definition and Versioning)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-PLG-01. The
acceptance criteria below are derived from the SRS-001 requirement text owned by this
work package (TOOL-PLG-010, M, P2, verification method A — analysis argument).

## Acceptance criteria

Derived from **TOOL-PLG-010**: *The tool shall define documented extension points for,
at minimum: compiler configurations, test framework back-ends, target execution
methods, and report formats.*

- AC-1 (falsifiable): the code defines a named, documented extension-point descriptor
  for each of the four minimum kinds — compiler configurations, test framework
  back-ends, target execution methods, report formats — and a programmatic listing of
  the defined points names all four.
- AC-2 (falsifiable): each descriptor carries a stable identifier, a human-readable
  title and description, a provider contract name, and an interface version field;
  identifiers are unique and listings are ordered deterministically.
- AC-3 (falsifiable): the definition surface rejects malformed descriptors — empty or
  whitespace identifier, title, description or contract, a non-string field value, or
  a non-dotted-integer interface version — with a named error from the extension
  package error hierarchy.
- AC-4 (falsifiable): the definition surface rejects duplicate registration of the
  same identifier and lookup of an undefined identifier with distinct named errors.
- AC-5 (falsifiable): the registry is open-ended — a caller can define and register an
  additional extension point without modifying tool source — and the four minimum
  points are exposed through the same public surface as any user-registered point.

Scope note: the WP title mentions "versioning". TOOL-PLG-060 (interface versioning
policy: breaking changes documented with a migration path) is allocated to a different
work package; this increment carries only the per-descriptor interface-version field
needed to identify extension point definitions. Nothing here claims the PLG-060 policy.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-PLG-010** | The tool shall define documented extension points for, at minimum: compiler configurations, test framework back-ends, target execution methods, and report formats. | `src/ectt/plg/points.py` (`ExtensionPoint`, `BUILTIN_EXTENSION_POINTS`, `ExtensionPointRegistry`, `default_registry`), `src/ectt/plg/errors.py` (`PlgError` hierarchy), re-exported by `src/ectt/plg/__init__.py` | **Guarantee:** the four minimum extension points are defined as immutable descriptors — `compiler_configs` (contract `compiler_config`), `framework_backends` (contract `framework_backend`), `target_execution_methods` (contract `target_execution`), `report_formats` (contract `report_format`) — each carrying a title, a one-paragraph description, the provider contract name and an interface version, so the points are documented in code and machine-readable.<br><br>**Analysis argument (method A):** the requirement asks for *defined, documented* extension points. The definition is a descriptor type plus a registry: descriptors are frozen dataclasses (a point cannot be mutated after definition), the built-in set is a module-level tuple, and `default_registry()` exposes them through the same `register`/`lookup`/`list_points` surface a user registration uses — the built-ins get no privileged path, so the surface itself is exercised by its own definitions. The registry is open-ended: any caller may add a point with a new contract name without touching tool source.<br><br>**Guarantee (malformed/duplicate/unknown):** `_validate` rejects empty or whitespace fields, non-string values and interface versions that are not dotted integers with `InvalidExtensionPointError`; a reused identifier raises `DuplicateExtensionPointError`; an unknown lookup raises `UnknownExtensionPointError`. All derive from `PlgError` → `CoreError` → `EcttError`, so they serialise through the core error model.<br><br>**Not covered:** this note defines and documents the points; it does not claim that any provider is registered against them (WP-PLG-04 owns the AI-provider protocol; WP-PLG-02 owns discovery/load). Interface versioning *policy* (TOOL-PLG-060) is owned by a different work package and is not claimed here.<br><br>**Test evidence:** `tests/plg/test_points.py` — `test_builtin_registry_exposes_four_minimum_points`, `test_builtin_contracts_cover_the_four_required_kinds`, `test_every_builtin_descriptor_is_documented_and_versioned`, `test_listing_is_deterministic_and_sorted`, `test_register_and_lookup_user_point`, `test_lookup_unknown_point_is_rejected`, `test_duplicate_registration_is_rejected`, `test_register_rejects_blank_fields`, `test_register_rejects_non_string_fields`, `test_register_rejects_malformed_interface_version`, `test_builtin_descriptors_are_frozen`, `test_default_registry_returns_fresh_instances`, `test_error_hierarchy_derives_from_core_error` (13 tests, all green in the WP-PLG-01 gate run: 412 passed, 4 skipped). |

## Design notes

- **Why descriptors instead of abstract base classes.** TOOL-PLG-010 asks for defined
  and documented *points*, not yet provider protocols. A frozen descriptor with a
  contract name is the smallest artifact that names the seam, documents it, and gives
  later packages (PLG-02 discovery, PLG-04 AI-provider protocol) something to attach
  to.
- **Why an open contract namespace.** Closing the contract set would make "add a
  point without modifying tool source" false for any new kind; the four SRS-required
  kinds are the built-ins, and the contract name stays a validated non-empty string.
- **Why `default_registry()` returns a fresh instance.** A module-level mutable
  registry would couple unrelated consumers and make test isolation impossible; each
  caller gets its own pre-populated registry.

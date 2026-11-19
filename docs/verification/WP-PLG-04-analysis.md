# Verification Analysis Note — WP-PLG-04 (AI Provider Extension Protocol)

Board acceptance criterion (PLAN-001 §5.4, quoted): *A third-party provider registers
via the public extension API, negotiates capabilities and version compatibility, and
an incompatible provider is rejected without loading it into a feature.*

Supporting SRS requirement owned by this work package: TOOL-PLG-100 (M, P2, A) — *The
tool shall define a documented AI-provider extension point (§18 AIF), distinct from
and structured like the compiler, test-framework, and report-format extension points
above, so that any AI-assisted capability — present or future, generative or
structured-decision, local or remote, from any vendor or model architecture — is
integrated by implementing that interface rather than by modifying tool source.*

## Acceptance criteria

- AC-1 (falsifiable, from the board criterion, registration clause): the AI-provider
  extension point itself is defined through the WP-PLG-01 public extension-point
  surface (an `ai_providers` descriptor registered into an `ExtensionPointRegistry` —
  the same API the built-ins use, not a privileged path), and a third-party provider
  registers into the public `AiProviderRegistry` API with a descriptor; no tool
  source modification is involved anywhere in the path.
- AC-2 (falsifiable, from the negotiation clause): registration records the
  provider's interface version and declared capabilities; a feature resolves a
  provider through `resolve(provider_id, required_capabilities, required_version)`,
  which returns the provider only when every required capability is declared and the
  provider's interface version satisfies the feature's compatibility requirement.
- AC-3 (falsifiable, from the rejection clause): an incompatible provider — missing a
  required capability or carrying an incompatible interface version — is rejected
  with distinct named errors (`IncompatibleAiProviderError` with the reason recorded),
  and the rejection happens before any loading: the provider's factory is never
  invoked for a rejected provider, proven by a recording factory in the tests.
- AC-4 (falsifiable): the registry refuses duplicate provider identifiers and unknown
  lookups with named errors; descriptors are frozen; listing is deterministic.

Scope notes: this increment defines and documents the AI-provider extension *point and
protocol* — the mechanism TOOL-AIF-050/230/250/260 rely on. No AIF feature is
implemented here (they belong to the AIF work packages); no vendor SDK is imported;
"structured like the other extension points" is satisfied by reusing the descriptor +
registry + named-error discipline of WP-PLG-01.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-PLG-100** | The tool shall define a documented AI-provider extension point (§18 AIF), distinct from and structured like the compiler, test-framework, and report-format extension points above, so that any AI-assisted capability — present or future, generative or structured-decision, local or remote, from any vendor or model architecture — is integrated by implementing that interface rather than by modifying tool source. | `src/ectt/plg/aiprovider.py` (`define_ai_provider_extension_point`, `AI_PROVIDER_POINT_ID`, `AiProviderDescriptor`, `AiProviderRegistry`), new errors in `src/ectt/plg/errors.py`, re-exported by `src/ectt/plg/__init__.py` | **Board AC — registration clause:** the `ai_providers` extension point is defined through the WP-PLG-01 public `ExtensionPointRegistry` (same API as the built-ins; a second definition is refused with the registry's duplicate error), and a third-party provider registers through the public `AiProviderRegistry.register` with a frozen descriptor — no tool source modification in either path.<br><br>**Board AC — negotiation clause:** the descriptor carries an interface version (dotted-integer, validated) and declared capabilities; `resolve(provider_id, required_capabilities, required_interface_version)` returns the provider instance only when every required capability is declared and the interface version is compatible (same major, provider minor ≥ required minor).<br><br>**Board AC — rejection clause:** an incompatible provider (missing capability, minor too old, or major mismatch) is rejected with `IncompatibleAiProviderError` naming the reason, and rejection happens strictly before loading — proven with a recording factory that observes zero invocations on every rejected resolve. Unknown providers raise `UnknownAiProviderError`; duplicate identifiers are refused; descriptors are frozen and listing is deterministic.<br><br>**Not covered:** any AIF feature implementation (TOOL-AIF-* belong to the AIF work packages); vendor SDKs are not imported; schema/domain validation of provider responses is WP-AIF-14 territory.<br><br>**Test evidence:** `tests/plg/test_aiprovider.py` — `test_extension_point_defined_through_public_point_surface`, `test_extension_point_duplicate_is_refused`, `test_third_party_provider_registers_via_public_api`, `test_compatible_provider_is_loaded_after_negotiation`, `test_missing_capability_is_rejected_without_loading`, `test_incompatible_version_is_rejected_without_loading`, `test_major_version_mismatch_rejected`, `test_unknown_provider_is_named_error`, `test_duplicate_provider_id_rejected`, `test_malformed_descriptors_rejected`, `test_listing_is_deterministic`, `test_extension_point_registry_removes_elegantly` (12 tests, green in the WP-PLG-04 gate run: 581 passed, 4 skipped). |

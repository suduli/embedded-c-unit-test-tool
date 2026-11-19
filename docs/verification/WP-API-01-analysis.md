# WP-API-01 — Analysis: engine API protocol, operation catalogue and versioning

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-API-01. The
following falsifiable criteria are **derived** — from the SRS-001 requirement texts (TOOL-UIX-010,
TOOL-UIX-020, TOOL-PLG-060) and the recorded engine-API design (SDD-002 §3 versioning rule, §9
S6 engine API). Nothing beyond those sources is assumed:

- **AC-1 (TOOL-UIX-020, SDD-002 §9.2):** a `session.hello` bootstrap negotiation exchanges supported
  interface versions and selects an exact common version; the reply carries
  `result:{"interface_version":<chosen>}` on success, or the error envelope with
  `code:"NO_COMMON_VERSION"` when no version matches; no operation is admitted before hello succeeds.
- **AC-2 (TOOL-UIX-020, SDD-002 §9.2):** request envelopes carry `interface_version`, session-unique
  string `id`, `op` and `params`; a request whose version differs from the negotiated version, whose
  `id` was already used in the session, whose `op` is unknown, or whose `params` is not a mapping is
  rejected with a correlated error envelope (`NO_COMMON_VERSION`, duplicate-id,
  `UNKNOWN_OPERATION`, `INVALID_PARAMS` respectively).
- **AC-3 (SDD-002 §9.2):** malformed JSON, duplicate JSON keys and non-object payloads are rejected
  as protocol errors (never silently coerced).
- **AC-4 (TOOL-UIX-010, SDD-002 §9.3):** one operation catalogue is the single capability surface;
  every catalogue operation carries a non-empty `cli_equivalent` string (SDD-002 §9.2 example:
  `ectt operation cancel --target-id 17`), and the catalogue exposes it for response building so a
  front-end can never hold a capability the CLI does not see.
- **AC-5 (TOOL-PLG-060, SDD-002 §3):** the interface version is explicit and negotiated; rejection of
  an unsupported version carries **both** versions and a migration/capability diagnostic (the
  supported-version list), i.e. the documented migration path for the current single supported
  version.
- **AC-6 (scope boundary):** transport (stdio/socket framing, listener) is **out of scope** — it is
  WP-API-02's deliverable (TOOL-UIX-050); this WP delivers the protocol layer and catalogue the
  transport will serve.

## Implementation

- `src/ectt/api/errors.py` — `ApiError(EcttError)`, category `api`.
- `src/ectt/api/catalogue.py` — `Operation` record (`name`, `summary`, `cli_equivalent`,
  `since_version`, `cancellable`), `Catalogue` registry (duplicate-name refusal), `INTERFACE_VERSION`,
  `SUPPORTED_INTERFACE_VERSIONS`, and the protocol-level operations that exist today
  (`operation.cancel` per SDD-002 §9.2). Future operations register here; WP-CLI-01 generates the CLI
  from this same catalogue (DSN-CLI-010).
- `src/ectt/api/protocol.py` — `Session` (negotiation state, used-ID tracking), `parse_payload_strict`
  (duplicate-key/malformed-JSON rejection), `hello` bootstrap, request validation, `error_envelope`
  builder.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/api/`) |
|---|---|---|
| TOOL-UIX-020 (versioned JSON interface; hello negotiation; no op before hello) | `protocol.Session.hello`, `Session.negotiated` flag, `SUPPORTED_INTERFACE_VERSIONS` | `test_protocol.py::test_hello_negotiates_exact_common_version`, `::test_hello_no_common_version_yields_error_envelope_with_both_versions`, `::test_operation_before_hello_is_rejected`, `::test_hello_rejects_malformed_params` |
| TOOL-UIX-010 (engine is the single capability surface; CLI equivalents) | `catalogue.Operation.cli_equivalent`, `Catalogue.cli_equivalent_for` | `test_catalogue.py::test_every_operation_carries_nonempty_cli_equivalent`, `::test_cancel_operation_cli_equivalent_matches_sdd_example` |
| TOOL-PLG-060 (versioned interface; breaking changes carry migration path) | version negotiation + rejection details carrying both versions and supported list | `test_protocol.py::test_hello_no_common_version_yields_error_envelope_with_both_versions`, `::test_request_with_wrong_negotiated_version_is_rejected_with_versions`, `test_catalogue.py::test_catalogue_exposes_interface_version` |
| Protocol strictness (SDD-002 §9.2) | `parse_payload_strict` duplicate-key hook, envelope shape validation | `test_protocol.py::test_malformed_json_is_rejected`, `::test_duplicate_json_keys_are_rejected`, `::test_non_object_payload_is_rejected`, `::test_unknown_operation_is_rejected`, `::test_invalid_params_are_rejected_with_correlated_id`, `::test_duplicate_id_is_rejected_within_session` |

## Not covered by this increment

- Transport framing (length-prefix, stdio/socket listener) — WP-API-02 (TOOL-UIX-050).
- Actual operation executors (environment build etc.) — later CMP-* packages; the catalogue registers
  only protocol-level operations that the design already names (`operation.cancel`), whose execution
  wiring arrives with the operations it targets.
- GUI/console-pane consumers — CMP-GUI packages, unimplemented by design (TOOL-UIX-030 still open).

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0. All six ACs
above are met by named tests; none skipped.

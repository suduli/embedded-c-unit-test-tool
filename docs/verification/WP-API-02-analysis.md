# WP-API-02 — Analysis: local-only transport with no network listener

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-API-02.
Derived from the SRS-001 text (TOOL-UIX-050) and the recorded design (DSN-API-030 in SDD-001 §4.4
"no TCP listener is offered"; SDD-002 §9.1/§9.2 transport + framing):

- **AC-1 (TOOL-UIX-050, DSN-API-030):** the engine API's transport layer contains **no network
  listener**: no TCP socket is created, bound, or listened on anywhere under `src/ectt/api/` —
  the module does not import `socket` at all, and a source-level guard test enforces this
  permanently.
- **AC-2 (SDD-002 §9.2 framing):** frames are a four-byte unsigned big-endian payload length
  followed by exactly that many UTF-8 bytes of one JSON object; length 1–8,388,608 inclusive;
  readers buffer partial headers/bodies and accept several frames per read; oversized, zero-length,
  malformed-JSON, duplicate-key and non-object payloads are rejected with named errors; a frame
  truncated at EOF is reported, never silently accepted.
- **AC-3 (TOOL-UIX-050):** the stdio transport serves the engine protocol over plain pipes with no
  network access, demonstrated end-to-end in-process (bytes in → session hello negotiated → reply
  bytes out).
- **AC-4 (scope boundary):** the standalone application process (GUI shell) is WP-GUI-01
  (TOOL-UIX-030/040); this WP delivers the engine-side transport contract. The
  filesystem-permissioned local-socket alternative transport (SDD-002 §9.1) is offered by the
  design but stdio already satisfies "local engine instance, no network"; a UDS/named-pipe
  implementation is a follow-up increment, not a gap in TOOL-UIX-050.

## Implementation

- `src/ectt/api/transport.py` — `MAX_FRAME_BYTES`/`MIN_FRAME_BYTES`, `encode_frame`,
  `FrameReader` (partial-buffer buffering, multi-frame-per-read, named rejections via
  `TransportError(ApiError)`), `StdioTransport.serve` (read loop → `Session` → reply frames).
- Guard test keeps the no-network property structural, not aspirational.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/api/`) |
|---|---|---|
| TOOL-UIX-050 (local engine instance, no network access; no TCP listener) | no `socket` import in the api package; stdio-only pump | `test_transport.py::test_transport_layer_never_imports_socket`, `::test_stdio_round_trip_negotiates_hello_end_to_end` |
| SDD-002 §9.2 framing contract | `encode_frame`, `FrameReader` | `::test_frame_round_trip`, `::test_header_split_across_feeds`, `::test_body_split_across_reads`, `::test_two_concatenated_frames_in_one_read`, `::test_oversized_frame_rejected`, `::test_zero_length_frame_rejected`, `::test_malformed_json_in_frame_rejected`, `::test_duplicate_keys_in_frame_rejected`, `::test_truncated_frame_at_eof_is_reported` |

## Not covered by this increment

- Filesystem-permissioned local-socket (UDS/named-pipe) transport — follow-up increment within
  CMP-API; stdio already fulfils TOOL-UIX-050 locally.
- GUI application shell — WP-GUI-01.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.

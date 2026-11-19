# Verification Analysis Note — WP-EXT-03 (Target Result Retrieval Channels and Protocol)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-EXT-03. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-TGT-050 (M, P3, T) and TOOL-TGT-060 (M, P3, A), consuming the WP-SEC-07
untrusted boundary.

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-TGT-050): retrieval channels are declarative, frozen
  descriptors for the documented minimum set — semihosting and serial (UART) — each
  carrying an origin label used for the untrusted boundary; channel composition is
  deterministic; an unknown channel kind is a named error.
- AC-2 (falsifiable, from TOOL-TGT-060, method A): the host-to-target protocol is
  plain-text, line-oriented, and parseable without a bidirectional channel: parsing
  consumes one stream of text only (no writes back), recognises the documented result
  kinds, retains everything else verbatim as unparsed data, and every entry carries
  its channel origin. Analysis argument: the parse is a pure function of one input
  string — no second channel exists in the API surface, which is what
  "without requiring a bidirectional channel" demands.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TGT-050** | The tool shall retrieve test results from the target via at minimum: semihosting, and a serial (UART) channel. | `src/ectt/ext/channels.py` (`RetrievalChannel`, `semihosting_channel`, `serial_uart_channel`, `UnknownChannelError`), re-exported by `src/ectt/ext/__init__.py` | **Guarantee:** the documented minimum channels exist as declarative frozen descriptors — semihosting and serial UART — each carrying the origin label consumed by the WP-SEC-07 untrusted boundary; an unknown channel kind or blank origin is a named error; descriptors serialise deterministically.<br><br>**Test evidence:** `tests/ext/test_channels.py` — `test_documented_minimum_channels_exist`, `test_channels_are_frozen_and_serialisable`, `test_unknown_channel_kind_is_named_error`, `test_blank_origin_is_named_error`. |
| **TOOL-TGT-060** | The host-to-target result protocol shall be plain-text, line-oriented, and parseable without requiring a bidirectional channel. *(Method A)* | `src/ectt/ext/channels.py` (`parse_channel_output`), parsing via the WP-SEC-07 `parse_target_output` | **Analysis argument:** the protocol parse is a pure function of one input string plus the channel's origin label — the API surface (verified by signature inspection in the tests) contains no reply/write parameter, which is exactly "parseable without requiring a bidirectional channel". Plain-text and line-oriented: one stream split per line, documented result kinds recognised, everything else retained verbatim as unparsed data; every entry carries the channel origin; identical streams parse identically (purity asserted).<br><br>**Test evidence:** `tests/ext/test_channels.py` — `test_protocol_is_one_way_plain_text`, `test_parse_is_a_pure_function_of_the_stream`, `test_unparsable_content_retained_verbatim` (7 tests total, green in the WP-EXT-03 gate run: 790 passed, 4 skipped). |

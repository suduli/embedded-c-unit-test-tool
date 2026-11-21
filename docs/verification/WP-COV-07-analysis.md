# WP-COV-07 — Bare-metal coverage retrieval

Status: in progress (overnight lane B, 2026-11-21)
Requirements: TOOL-COV-100
Design elements: DSN-COV-* per PLAN-001 §3 (CMP-COV)
Dependencies: WP-COV-01 (implemented in this lane: `ectt.cov` reader), WP-EXT-03
(implemented: `ectt.ext` target execution/parity transport surface)
Decisions applied as written (not re-decided):
- **ADR-004 coverage backend (owner answer, 2026-11-21): "GCC first".** There is no
  C compiler on this machine: parsers are built against hand-written fixtures from
  the documented format. **Real GCC output has not been checked** (recorded in the
  lane ledger).

## Design summary

A bare-metal target has no filesystem and no operating system (TOOL-COV-100): the
coverage artifact leaves the target through the only channel it has — the console
transport captured by the target-execution layer (ectt.ext / WP-EXH runner). This
package defines the console dump protocol the generated harness emits, reassembles
the artifact bytes, verifies integrity, and hands the artifact to the documented
gcov JSON reader from WP-COV-01 or wraps it in a RunCoverage record (WP-COV-02)
with a recorded completeness state, so truncated/missing artifacts flow through the
merge's fail-closed handling unchanged (TOOL-COV-180 semantics).

## Dump protocol (console-safe framing, defined by this package)

The generated harness prints, on its console output:

```
GCOVDUMP BEGIN <name> <length-in-bytes>
<hex pairs, 64 hex chars (32 bytes) per line>
GCOVDUMP END <crc32-of-payload-as-8-hex>
```

- `<name>` is a non-empty token without whitespace (e.g. `adc.gcda.json.gz`).
- The payload is lower-case hex; every line between BEGIN and END carries 64 hex
  chars except the last, which carries the remainder (never empty).
- `<length>` is the payload byte length; a mismatch with the received payload is a
  named error.
- The END line's CRC32 (zlib, stdlib) must match the payload.
- One frame per stream; a second BEGIN is a named error; text outside a frame is a
  named error; an unterminated frame is a named error (`truncated_dump`) — the
  TOOL-COV-180 "truncated" state.

## Acceptance criteria

Derived from the SRS text (SRS-001 §12 line 422: "The tool shall retrieve coverage
data from bare-metal targets with no filesystem and no operating system") and the
PLAN-001 §5.4 row (`WP-COV-07`; COV-100; dependencies COV-01 EXT-03). PLAN-001 §5.4
records **no package-specific acceptance criterion** for this package (flagged for
reconciliation) — these are the derived, reviewable criteria:

1. **AC-1 (COV-100 — retrieval without filesystem/OS).** `parse_dump` reassembles
   the artifact bytes from the console dump framing, verifying name, length and
   CRC32; `retrieve_coverage` decodes the artifact (raw JSON text, JSON bytes, or
   gzip bytes) into an `ectt.cov` `GcovDocument` through the documented gcov
   reader — no filesystem access to the target is assumed anywhere.
2. **AC-2 (completeness travels, TOOL-COV-180).** `retrieve_run_coverage` wraps the
   retrieved document in a `RunCoverage` with completeness `complete` when the
   frame verifies; a truncated frame is surfaced as a named error by `parse_dump`
   and `retrieve_run_coverage` can record it as `truncated` with the advisory;
   an empty stream records `missing`. Either way the record flows through the
   WP-COV-02 merge unchanged (excluded from aggregates with the advisory carried).
3. **AC-3 (fail-closed).** Bad hex, length mismatch, CRC mismatch, duplicate
   frames, text outside a frame, and an unterminated frame are named errors;
   nothing is silently repaired.
4. **AC-4 (determinism).** The framing and retrieval are pure text/byte functions;
   no wall-clock; no network; the retrieved document dumps canonically.

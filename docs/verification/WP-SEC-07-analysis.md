# Verification Analysis Note — WP-SEC-07 (Target-Supplied Data Treated as Untrusted)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-SEC-07. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-SEC-090 (M, P3, T) — *Where the tool retrieves data from a target device
or external process, it shall treat that data as untrusted input and shall not execute
or interpret it as code.*

## Acceptance criteria

- AC-1 (falsifiable): target-retrieved data enters the tool only through a frozen
  `UntrustedPayload` wrapper carrying its origin; the wrapper exposes data accessors
  only (text, lines, length) — its public API has no execution surface — and its
  repr is sanitised (origin and size, not content).
- AC-2 (falsifiable): target output parses as plain-text result lines (PASS, FAIL,
  ERROR, TIMEOUT, LOG + payload) as pure data; a line that does not match the
  protocol is retained verbatim as an `unparsed` data entry — never executed or
  further interpreted.
- AC-3 (falsifiable): content that looks like code (shell or script fragments) is
  still treated as data: it is retained verbatim inside a data entry with no
  execution path, satisfying "shall not execute or interpret it as code".
- AC-4 (falsifiable): parsing is deterministic; every parsed entry carries its
  origin.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-SEC-090** | Where the tool retrieves data from a target device or external process, it shall treat that data as untrusted input and shall not execute or interpret it as code. | `src/ectt/sec/untrusted.py` (`UntrustedPayload`, `mark_untrusted`, `parse_target_output`, `TargetResultLine`, `RESULT_LINE_KINDS`), re-exported by `src/ectt/sec/__init__.py` | **Guarantee:** target data is captured only through a frozen, origin-carrying `UntrustedPayload` whose public API is data accessors only — no exec/eval/compile/run/call/system surface exists on the wrapper (asserted) — and whose repr is sanitised to origin and size. Parsing is a strict plain-text split into protocol kinds (PASS/FAIL/ERROR/TIMEOUT/LOG) with everything else retained verbatim as `unparsed` data entries; code-looking content (`import os; os.system(...)`) is data — retained verbatim, never executed. Non-text captures and blank origins are refused at the boundary; parsing is deterministic.<br><br>**Not covered:** the retrieval channels themselves (WP-EXT-03 consumes this boundary); richer protocol parsing (coverage data formats) belongs to the coverage work packages.<br><br>**Test evidence:** `tests/sec/test_untrusted.py` — `test_payload_wrapper_exposes_data_accessors_only`, `test_repr_is_sanitised`, `test_result_lines_parse_as_data`, `test_unparsable_lines_retained_as_data`, `test_code_looking_content_is_data_never_executed`, `test_empty_lines_and_whitespace_are_data`, `test_parsing_is_deterministic`, `test_blank_origin_rejected`, `test_non_text_content_rejected_at_capture` (9 tests, green in the WP-SEC-07 gate run: 717 passed, 4 skipped). |

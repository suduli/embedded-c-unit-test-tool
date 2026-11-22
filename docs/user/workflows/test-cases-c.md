<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Authoring test cases in C

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

Test cases are authored as data, not as hand-written C: a `.tests` file
(`ectt.tcm.datacases`) holds data-driven cases - per-unit restricted YAML
with inputs (parameters, global initial values) and expectations (return
value, final globals, output parameters), plus robustness flags and suites.

`save_test_cases_file` writes the file; `load_test_cases_file` reads it back
and refuses malformed entries with named errors. Every case carries a
content digest (D-02 option a): the recorded digest binds the case identity
to its content, so a case edited after the last run is `stale` and is not
presented as current evidence. Comparison of expected against actual values
is type-directed (`ectt.tcm.compare`): scalars and enums by value, pointers
by policy, structs member-wise, floats with explicit tolerance.


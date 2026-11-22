<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Generating and regenerating a harness

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

From an analysis model (`ectt.ana`), the generator produces a C test
harness translation unit (`ectt.gen.harness.HarnessGenerator`): one
entry point per exposed function, the RESULT/FAILURE result stream the host
runner normalises (WP-EXH-01), and a per-test setup hook that resets harness
state so no test sees what an earlier test left behind.

Stubs: `generate_programmable_stubs` produces the stub units for external
dependencies (modes listed in `ectt.gen.STUB_MODES`), with
`render_stub_setup` / `render_stub_expectations` and per-case test bodies
(`ectt.gen.testbody`).

Regeneration is protected: generated files carry a fingerprint token, and
the regeneration contract (`ectt.gen.regen`) preserves user-edited regions -
a changed interface regenerates the skeleton while your edits inside marked
regions survive; conflicts are refused, never overwritten silently.
Running the generated harness needs a C compiler; ectt checks generated C
by parsing when none is available.


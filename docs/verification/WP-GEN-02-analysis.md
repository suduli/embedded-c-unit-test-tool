# Verification Analysis Note — WP-GEN-02 (Framework Back-Ends: Unity and cmocka)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-GEN-02. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-HAR-060 (M, P2, T), TOOL-HAR-070 (S, P2, A) and TOOL-PLG-030 (M, P2, T).
The item is ADR-sensitive: only the decision-free part is implemented here; every open
ADR question is recorded in the ledger row, and none is decided.

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-HAR-060): the tool ships built-in Unity and cmocka
  back-ends registered through the same public registry discipline as everything
  else; rendering the WP-GEN-01 harness surface through either back-end produces a C
  test file that includes that framework's header, exposes the UUT functions via
  prototypes emitted from the harness model, and wires the setup/teardown hooks.
- AC-2 (falsifiable, from TOOL-HAR-060's C++ clause): a C++-free scan runs on every
  rendered output — a back-end render containing C++ constructs (`::`, `template<`,
  `class `, `catch`, `new `) is a named error — so neither back-end can introduce a
  C++ compilation or runtime dependency.
- AC-3 (falsifiable, from TOOL-HAR-070 and TOOL-PLG-030): a framework back-end is
  added by registering a declarative descriptor (id, framework header, template
  text) through the public registry — no tool source change; the built-ins are
  registered through exactly the same descriptor path as a user back-end, so a
  third framework needs only its descriptor.
- AC-4 (falsifiable): registry discipline: duplicate back-end ids and unknown
  look-ups are named errors; listing is deterministic; descriptors are frozen.

Scope notes (ADR-sensitive): the decision-free part is the registry + descriptor
path + the two built-in templates + the C++-free scan. NOT decided here: (a) the
default framework selection policy; (b) how cmocka mock-record integration binds to
the stub generation contract (interacts with WP-GEN-06); (c) third-party template
distribution/packaging format. No template *engine* dependency is introduced — the
renderer is a stdlib substitution consistent with the repository's minimal-dependency
style; if a future ADR selects a different engine, the descriptor shape absorbs it.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-HAR-060** | The tool shall generate harnesses targeting a configurable test framework back-end, supporting at minimum Unity and cmocka. Neither back-end shall introduce a C++ compilation or runtime dependency. | `src/ectt/gen/backends.py` (`FrameworkBackend`, `BackendRegistry`, `register_framework_builtins`, `render_framework_test`, `CppConstructInOutputError`), re-exported by `src/ectt/gen/__init__.py` | **Guarantee:** Unity (`unity.h`) and cmocka (`cmocka.h`) ship as built-in back-end descriptors registered through the public registry; `render_framework_test` renders the WP-GEN-01 harness surface (uut header include, exposed-function prototypes, setup/teardown hook wiring, test-invocation slots) into each framework's C test file, deterministically. The C++-free guarantee is enforced by a scan at render time — any output containing `::`, `template<`, `class `, `catch`, `new `, `delete ` or `namespace ` raises `CppConstructInOutputError`, so neither back-end can introduce a C++ dependency.<br><br>**Not covered:** executing the generated framework tests (host execution is WP-EXH-01); cmocka mock-record binding to stubs (ADR question recorded); the harness `ectt_harness.h` compatibility header that the templates include is generated alongside by later build work.<br><br>**Test evidence:** `tests/gen/test_backends.py` — `test_builtin_unity_and_cmocka_registered`, `test_unity_render_includes_framework_header_and_hooks`, `test_cmocka_render_includes_framework_header_and_hooks`, `test_render_output_passes_cpp_free_scan`, `test_cpp_construct_in_template_is_named_error`, `test_new_framework_needs_only_a_descriptor`, `test_descriptor_missing_field_is_named_error`, `test_template_without_uut_header_slot_rejected`, `test_duplicate_and_unknown_ids`, `test_rendering_is_deterministic`. |
| **TOOL-HAR-070** | Harness generation shall be template-driven such that support for an additional test framework requires only new templates, not tool source changes. *(Method A)* | Same as above (`FrameworkBackend.template`, `FrameworkBackend.from_descriptor`) | **Analysis argument:** the back-end is a data descriptor — id, framework header, template text with the harness slots (`{uut_header}`, `{framework_header}`, `{function_prototypes}`, `{setup_hook}`, `{teardown_hook}`, `{test_invocations}`) — and `render_framework_test` performs pure substitution. A third framework is demonstrated in tests: `acme_framework` registered from a plain mapping and rendered, with zero tool-source edits. The built-ins reach the registry through the same `from_descriptor` path as user back-ends, so nothing about the two shipped frameworks is privileged.<br><br>**Test evidence:** `tests/gen/test_backends.py` — `test_new_framework_needs_only_a_descriptor`, `test_descriptor_missing_field_is_named_error`, `test_template_without_uut_header_slot_rejected`. |
| **TOOL-PLG-030** | Adding a test framework back-end shall require only new templates and a declarative descriptor, with no modification of tool source. | Same as above (`BackendRegistry.register_descriptor`) | **Guarantee:** `register_descriptor` accepts a plain declarative mapping (`backend_id`, `framework_header`, `template`) — the full add path is: author the descriptor mapping, register, render. Duplicate ids are refused (`DuplicateBackendError`), unknown look-ups raise `UnknownBackendError`, listing is sorted and deterministic. No tool source change is involved; the same claim applies to the WP-PLG-01 extension-point registry where the framework-back-end point itself is one of the four built-in points (WP-PLG-01 evidence).<br><br>**Test evidence:** `tests/gen/test_backends.py` — `test_new_framework_needs_only_a_descriptor`, `test_duplicate_and_unknown_ids`, `test_builtin_unity_and_cmocka_registered`. |

## Open ADR questions (recorded, not decided)

1. **Default framework selection policy** — which back-end a project gets when it
   declares none. Options considered in the SRS structure; choosing one is a product
   decision for the owner.
2. **cmocka mock-record integration** — whether cmocka's `will_return`/`assert_`
   record surface binds to the WP-GEN-06 stub-generation contract via generated
   adapters or via template hooks. Interacts with the stub contract design; deciding
   before WP-GEN-06 lands would reverse work.
3. **Third-party template distribution format** — where user back-end descriptors
   live and how they are packaged/discovered (overlaps WP-PLG-02 discovery).
4. **Template engine** — the renderer here is stdlib substitution with no new
   dependency; if an ADR selects a richer engine, the descriptor shape absorbs it.

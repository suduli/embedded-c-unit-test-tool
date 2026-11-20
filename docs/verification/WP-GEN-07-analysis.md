# Verification Analysis Note — WP-GEN-07 (Stub Behaviour Programming)

Analysis evidence for requirements verified under WP-GEN-07. Status: **implemented**
(evidence-backed), with one verification limit stated first: **the generated C was not
compiled and run, because no C compiler is available to the test suite.** It is verified
by parsing it with libclang (the project's own analysis frontend) and requiring zero error
diagnostics, and by structural assertions on the text. Executor: Claude (lane A,
2026-11-20 queue).

## Acceptance criteria

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. Derived criteria (implemented as written; register edits are owner
territory). Decision D-02 ("Stable ids plus content digests") needs nothing new here:
stub behaviour is data attached to the case (`StubSpec`), and the case digest already
covers it.

- **AC-1 (TOOL-STB-040, behaviour per test case):** each programmable stub can be set to a
  fixed return value, a sequence of values across successive calls, or a user callback with
  the stub's own signature; the behaviour comes from the case's `StubSpec` (mode `fixed`,
  `sequence`, `callback`; `default` leaves the plain default return).
- **AC-2 (TOOL-STB-050, recording):** every call is counted and the argument values of each
  call are retrievable from test code; the journal has a fixed capacity, calls past it are
  still counted and flagged (`journal_overflowed`), argument reads are bounds-safe, and no
  dynamic allocation is used.
- **AC-3 (TOOL-STB-060, call order):** one shared sequence counter and a fixed-capacity
  order log across all stubs give each call a global order number and back
  `ectt_stub_verify_order`; an overflowed log is never reported as verified.
- **AC-4 (TOOL-STB-070, output parameters):** a stub can write caller-supplied values
  through its non-const scalar pointer arguments, set per case from `out_parameters`.
- **AC-5 (valid C, honest limits):** the generated source and header contain no compile
  errors; signatures the control block cannot express (variadic, function-pointer or array
  parameters) are emitted as plain default stubs with an `ectt:unsupported-construct`
  marker, listed in `unsupported`, and refuse configuration.
- **AC-6 (safe generation):** values placed in generated C are plain value expressions
  (no `;`, braces, `#`, comments, newlines); names are C identifiers; bad specs are refused
  with a reason; output is deterministic and independent of input order.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-STB-040** | Generated stubs shall support, per test case, a configured return value, a sequence of return values across successive calls, and a user-supplied callback implementation. | `src/ectt/gen/stubctl.py` (`generate_programmable_stubs`, `render_stub_setup`, `ProgrammableStubUnit`, `STUB_MODES`) | **AC-1:** `test_non_void_stubs_get_return_programming_and_void_stubs_do_not`, `test_every_stub_can_take_a_callback_with_its_own_signature`, `test_sequence_mode_keeps_the_last_value_and_flags_exhaustion`, `test_fixed_return_value_setup`, `test_sequence_setup_lists_every_value_in_order`, `test_callback_setup_names_the_users_function`, `test_default_mode_only_resets_and_a_void_stub_takes_outputs_and_callbacks`, `test_default_returns_are_kept_when_nothing_is_programmed`. **AC-5/6:** `test_generated_source_has_no_compile_errors`, `test_header_alone_parses_and_declares_the_api`, `test_source_and_header_agree_so_test_code_links_against_the_stubs`, `test_plain_c_values_are_accepted` (8), `test_values_that_could_carry_statements_are_refused` (10), `test_bad_stub_specs_are_refused_with_a_reason` (11). |
| **TOOL-STB-050** | Generated stubs shall record call count, and the argument values of each call, retrievable from test code. | `_definition`, `render_stub_expectations` | **AC-2:** `test_every_call_is_counted_and_every_argument_recorded`, `test_calls_beyond_the_journal_are_counted_and_flagged_not_dropped_silently`, `test_argument_reads_are_bounds_safe`, `test_no_dynamic_allocation_and_capacities_are_overridable_macros`, `test_expected_call_count_becomes_a_c_expression`, `test_expectations_refuse_a_bad_count_or_a_foreign_spec`. |
| **TOOL-STB-060** | Generated stubs shall support verification of call order across multiple stubs. | runtime block in `stubctl.py` (`ectt_stub_next_sequence`, `ectt_stub_verify_order`) | **AC-3:** `test_one_shared_sequence_counter_orders_calls_across_stubs`, `test_an_overflowed_order_log_is_never_reported_as_verified`, `test_reset_all_resets_the_runtime_and_every_programmable_stub`. |
| **TOOL-STB-070** | Generated stubs shall support output parameters, writing caller-supplied values through pointer arguments. | `out_parameter_names`, the `set_out_<parameter>` API | **AC-4:** `test_output_parameters_exist_only_for_writable_non_void_pointers`, `test_the_stub_writes_the_output_value_through_the_pointer_when_programmed`, `test_output_parameter_setup_is_sorted_and_combines_with_a_return_mode`, `test_output_values_are_checked_too`, `test_only_scalar_pointees_can_be_outputs_because_structs_are_only_forward_declared`, `test_struct_and_typedef_parameters_compile_with_their_declarations`. **AC-5:** `test_signatures_the_control_block_cannot_express_are_flagged_not_pretended`, `test_configuring_an_unsupported_stub_raises`. |

## Defect found by the libclang check

The first draft kept output values for any non-const pointer parameter as a by-value copy of
the pointee. For `struct Frame *` that needs a complete type, but a stub unit only
forward-declares structs (so it compiles independently, per WP-GEN-06); libclang reported
`field has incomplete type`. Output parameters are now offered only for scalar pointees (a
scalar keyword spelling or a typedef of one, resolved through the type graph); a struct
output is written by a user callback.
(`test_only_scalar_pointees_can_be_outputs_because_structs_are_only_forward_declared`.)

## Design notes

- **Plain stubs are unchanged.** `generate_stubs` (WP-GEN-06) keeps its output; the
  programmable unit is a new entry point so existing consumers and tests are untouched.
- **Sequence exhaustion keeps the last value and flags it** rather than inventing a
  default or restarting, so a test can assert it did not overrun the sequence.
- **Typedefs per stub** (`ectt_stub_<name>_arg_<param>_t` and so on) keep declarators
  valid for pointer, qualified and typedef'd types.

## Not covered (recorded, not guessed)

- **Compiling and running the generated C** (including `ectt_stub_verify_order` and the
  sequence behaviour at run time). libclang proves it is well-formed, not that it behaves;
  the compile-and-run test belongs wherever a C toolchain is available (second-pass row).
- **Struct and union output parameters and by-reference struct recording** (needs complete
  types in the stub unit).
- **Variadic stubs and function-pointer or array parameters** (flagged, not programmable).
- **Wiring `render_stub_setup` into the harness generator** and the per-case expectation
  checks into the harness result stream: this package provides the generators.
- **Thread safety** of the journal: the stubs are for single-threaded test harnesses.

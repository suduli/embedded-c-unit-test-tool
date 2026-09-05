# Software Requirements Specification — Open-Source Embedded C Unit Testing Tool

**Document ID:** SRS-001
**Version:** 0.1 (draft for review)
**Date:** 2026-07-30
**Status:** Draft — not yet baselined

---

<!-- nav:start -->
**Related documents** — **SRS-001** *(you are here)* · [ADR-001](ADR-001-architecture-decisions.md) · [SDD-001](design/SDD-001-architecture.md) · [SDD-002](design/SDD-002-interfaces.md) · [SDD-003](design/SDD-003-data-model.md) · [SDD-004](design/SDD-004-traceability-architecture.md) · [SDD-005](design/SDD-005-external-integration.md) · [Register](design/trace/design-elements.yaml) · [Design index](design/README.md)

Architecture diagrams: [specifications](design/diagrams) · published at [the documentation site](https://suduli.github.io/embedded-c-unit-test-tool/), which spells out every component id in full and shows how these documents connect.
<!-- nav:end -->


## 1. Purpose and Scope

### 1.1 Purpose
This document specifies the requirements for an open-source unit and integration testing tool for embedded C software, intended as a functional alternative to VectorCAST/C++, Cantata, LDRA TBrun/LDRAunit, and Tessy.

### 1.2 Scope
The tool shall support the full dynamic testing workflow for C source code: project ingestion, interface analysis, test harness and stub generation, test case definition, test execution on host and embedded targets, structural coverage measurement up to MC/DC, requirements traceability, and certification-oriented reporting.

**Out of scope for v1.0:** C++ support, Ada support, system-level/HIL test orchestration, static analysis as a primary feature (integration only), formal verification.

### 1.3 Intended Users
- Embedded software engineers performing unit/integration testing
- Verification engineers producing evidence for ISO 26262, IEC 61508, IEC 62304, EN 50128, DO-178C
- Quality/safety managers reviewing coverage and traceability evidence
- CI/CD engineers automating verification pipelines

### 1.4 Assumptions and Dependencies

The following are assumed true. If any ceases to hold, the affected requirements must be re-examined.

**A-01** — The user possesses a working C toolchain capable of compiling their own project.
**A-02** — The user's project compiles cleanly before the tool is applied; the tool is not a repair tool for non-building code.
**A-03** — A production C front-end (libclang) is available for the platforms the tool supports, at a version compatible with the user's dialect.
**A-04** — Coverage instrumentation is provided by the user's compiler (gcov/llvm-cov); the tool measures and reports but does not implement its own instrumentation.
**A-05** — MC/DC availability depends on compiler version (GCC ≥ 14, Clang ≥ 18) and is outside the tool's control.
**A-06** — Target hardware execution requires a debug probe or simulator supported by an available open-source flashing tool.
**A-07** — The user is responsible for qualifying the tool for their own safety-related project; the tool supplies evidence, not qualification.
**A-08** — Users work in environments that may be air-gapped, and may prohibit outbound network connections.

### 1.5 Constraints

**K-01** — The tool shall not require modification of user source code to perform its function.
**K-02** — The tool shall not require the user to abandon or replace their existing build system.
**K-03** — The tool operates within the limits of the coverage metrics its supported compilers provide; it shall not claim metrics the toolchain cannot produce.
**K-04** — The tool shall be usable without any network connection for all non-AI functionality.
**K-05** — The tool shall not require administrative privileges to install or operate.
**K-06** — The project's licensing shall permit commercial use, redistribution, and modification by third parties.

---

## 2. Conventions

### 2.1 Requirement identifier format
`TOOL-<CAT>-<NNN>` where `<CAT>` is the three-letter category code and `<NNN>` is a stable sequential number. **IDs are never reused or renumbered.** Gaps are permitted when requirements are deleted.

### 2.2 Attributes
Every requirement carries: **Priority**, **Phase**, **Verification method**.

| Priority | Meaning |
|---|---|
| **M** | Must — v1.0 is not viable without it |
| **S** | Should — important, but v1.0 can ship without it |
| **C** | Could — desirable if effort permits |
| **F** | Future — explicitly deferred beyond v1.0; carries no phase or verification method |

| Phase | Meaning |
|---|---|
| **P1** | Host-based MVP |
| **P2** | Automation layer (parsing, generation) |
| **P3** | Safety coverage + on-target execution |
| **P4** | Traceability, reporting, qualification |

| Verification | Meaning |
|---|---|
| **T** | Test — automated or manual test case |
| **A** | Analysis — review of design/computation |
| **D** | Demonstration — observed operation |
| **I** | Inspection — examination of artifacts/code |

### 2.3 Language
"Shall" denotes a binding requirement. "Should" within requirement text is avoided; optionality is expressed via Priority.

### 2.4 Category codes

| Code | Category |
|---|---|
| ING | Project Ingestion |
| PAR | Source Parsing and Analysis |
| TCH | Toolchain and Compiler Abstraction |
| HAR | Test Harness Generation |
| STB | Stub and Mock Generation |
| TCD | Test Case Definition and Management |
| ATG | Automatic Test Generation |
| EXE | Host Test Execution |
| TGT | Target Test Execution |
| COV | Code Coverage |
| CBT | Change-Based and Regression Testing |
| TRC | Requirements Traceability |
| REP | Reporting |
| CIC | CI/CD Integration |
| UIX | User Interface |
| AIF | AI-Assisted Features |
| QUA | Qualification and Safety Standards |
| NFR | Non-Functional |
| LIC | Licensing and Distribution |
| SEC | Security and Integrity |
| MIG | Migration and Interoperability |
| INS | Installation and Deployment |
| PLG | Extensibility |
| PRJ | Project Data Management |

---

## 3. Project Ingestion (ING)

**TOOL-ING-010** *(M, P1, T)* — The tool shall accept a JSON compilation database (`compile_commands.json`) as the primary description of a user's project.

**TOOL-ING-020** *(M, P1, T)* — The tool shall parse both the `command` (string) and `arguments` (array) forms of compilation database entries and normalize them internally.

**TOOL-ING-030** *(M, P1, T)* — The tool shall extract, per translation unit: source path, working directory, include paths, preprocessor definitions, language standard, and compiler invocation.

**TOOL-ING-040** *(M, P1, D)* — The tool shall document and support generating a compilation database via CMake (`CMAKE_EXPORT_COMPILE_COMMANDS`) as the recommended path.

**TOOL-ING-050** *(S, P2, D)* — The tool shall support generating a compilation database via build interception (e.g. Bear) for projects without native export.

**TOOL-ING-060** *(S, P2, T)* — The tool shall operate on a single `.c` file with user-supplied include paths and defines when no build system is available.

**TOOL-ING-070** *(S, P2, T)* — The tool shall detect and report ingestion failures — missing headers, unresolvable include paths, unknown compiler flags — with the offending file and flag identified.

**TOOL-ING-080** *(C, P2, T)* — The tool shall import project configuration from Keil uVision (`.uvprojx`), IAR EW (`.ewp`), and Eclipse/STM32CubeIDE project files.

**TOOL-ING-090** *(S, P2, T)* — The tool shall persist the ingested project model to a version-controllable text format so ingestion need not be repeated on every invocation.

**TOOL-ING-100** *(S, P2, T)* — The tool shall detect that the ingested project model is stale relative to the build system and re-ingest or warn.

**TOOL-ING-110** *(C, P3, T)* — The tool shall support ingestion of projects that build with more than one toolchain, retaining per-toolchain flags.

**TOOL-ING-120** *(M, P2, T)* — The tool shall accept a set of two or more C source files as a single ingestion scope, for the purpose of integration testing, without requiring a build system.

**TOOL-ING-130** *(M, P2, T)* — The tool shall support a named **test scope** as a first-class concept: a user-defined set of translation units treated as the code under test, with all dependencies outside the set treated as external.

**TOOL-ING-140** *(M, P2, T)* — For a test scope containing multiple translation units, the tool shall resolve inter-file dependencies internally to the scope and classify each function call as intra-scope or external.

**TOOL-ING-150** *(M, P2, T)* — The tool shall support a test scope defined by explicit file list, by directory, by glob pattern, and by build-system target.

**TOOL-ING-160** *(S, P2, T)* — The tool shall detect and report symbol conflicts within a test scope, including duplicate non-static definitions and colliding file-static identifiers.

**TOOL-ING-170** *(S, P2, T)* — The tool shall support a single translation unit belonging to more than one test scope, such that a file may be tested in isolation and again as part of an integration scope.

**TOOL-ING-180** *(S, P2, T)* — The tool shall report, for a given test scope, the complete list of external dependencies requiring stubs, before harness generation is performed.

**TOOL-ING-190** *(S, P2, I)* — Test scope definitions shall be stored in a plain-text, version-controllable file.

---

## 4. Source Parsing and Analysis (PAR)

**TOOL-PAR-010** *(M, P2, T)* — The tool shall parse C source using a production C front-end (libclang) with the exact flags recorded in the compilation database.

**TOOL-PAR-020** *(M, P2, T)* — The tool shall support C89, C99, C11, C17, and GNU dialect extensions.

**TOOL-PAR-030** *(M, P2, T)* — The tool shall extract, for every function in a translation unit: name, return type, parameter names and types, storage class, linkage, and source location.

**TOOL-PAR-040** *(M, P2, T)* — The tool shall extract all user-defined types (struct, union, enum, typedef, function pointer) reachable from a function's interface, transitively.

**TOOL-PAR-050** *(M, P2, T)* — The tool shall identify global and file-static variables read or written by each function.

**TOOL-PAR-060** *(M, P2, T)* — The tool shall construct a call graph identifying, for each function, all functions it calls, and classify each callee as internal (defined in the unit under test) or external.

**TOOL-PAR-070** *(S, P2, T)* — The tool shall construct a control flow graph per function sufficient to support coverage analysis and test generation.

**TOOL-PAR-080** *(S, P2, T)* — The tool shall identify `static` functions and provide a mechanism to make them testable without modifying user source.

**TOOL-PAR-090** *(S, P2, T)* — The tool shall resolve function-like and object-like macros used in interfaces, and record where a macro obscures the true interface.

**TOOL-PAR-100** *(M, P2, T)* — The tool shall persist the analysis result as a machine-readable model (JSON) that is the sole input to downstream generation stages.

**TOOL-PAR-110** *(S, P2, A)* — The analysis model shall be versioned, with a schema version field, so downstream stages can reject incompatible models.

**TOOL-PAR-120** *(C, P3, T)* — The tool shall compute cyclomatic complexity per function and expose it in the model.

**TOOL-PAR-130** *(S, P2, T)* — The tool shall continue analysis and report partial results when a subset of translation units fails to parse.

---

## 5. Toolchain and Compiler Abstraction (TCH)

**TOOL-TCH-010** *(M, P1, T)* — The tool shall support GCC and Clang as host compilers.

**TOOL-TCH-020** *(M, P1, T)* — The tool shall define a declarative compiler configuration format specifying: compiler invocation, flag syntax for coverage/debug/optimization, output conventions, and supported coverage kinds.

**TOOL-TCH-030** *(M, P3, T)* — The tool shall support cross-compilation using GNU-style embedded toolchains, verified against at minimum `arm-none-eabi-gcc` and a RISC-V GNU toolchain.

**TOOL-TCH-040** *(S, P3, T)* — The tool shall support additional cross-compilers via user-authored compiler configuration files without requiring changes to the tool's source code.

**TOOL-TCH-050** *(S, P3, I)* — The tool shall ship compiler configurations for at minimum: GCC (host), Clang (host), arm-none-eabi-gcc, riscv64-unknown-elf-gcc, avr-gcc, and SDCC.

**TOOL-TCH-060** *(M, P3, T)* — The tool shall declare, per compiler configuration, which coverage metrics are achievable, and shall refuse to request unsupported metrics.

**TOOL-TCH-070** *(M, P3, T)* — The tool shall detect the compiler version and reject or warn when the version does not support a requested feature (e.g. MC/DC requiring GCC ≥ 14 or Clang ≥ 18).

**TOOL-TCH-080** *(S, P3, T)* — The tool shall support building the same test suite for multiple toolchains in isolated build directories within one invocation.

**TOOL-TCH-090** *(S, P3, D)* — The tool shall provide reproducible container images containing validated host and cross toolchains.

**TOOL-TCH-100** *(C, P3, T)* — The tool shall support proprietary compilers (Keil armcc/armclang, IAR, TASKING, Green Hills) through the compiler configuration mechanism where their invocation is externally scriptable.

---

## 6. Test Harness Generation (HAR)

**TOOL-HAR-010** *(M, P2, T)* — The tool shall generate a compilable test harness for a designated unit under test (UUT) from the analysis model, without manual editing.

**TOOL-HAR-020** *(M, P2, T)* — The generated harness shall expose every non-static function of the UUT as directly callable from test code.

**TOOL-HAR-030** *(S, P2, T)* — The generated harness shall optionally expose `static` functions of the UUT for testing.

**TOOL-HAR-040** *(M, P2, T)* — The generated harness shall provide read and write access to global and file-static variables identified by TOOL-PAR-050.

**TOOL-HAR-050** *(M, P2, T)* — The generated harness shall include per-test setup and teardown hooks.

**TOOL-HAR-060** *(M, P2, T)* — The tool shall generate harnesses targeting a configurable test framework back-end, supporting at minimum Unity and cmocka. Neither back-end shall introduce a C++ compilation or runtime dependency.

**TOOL-HAR-065** *(C, P3, T)* — The tool shall provide an optional GoogleTest back-end for host-only execution, for interoperability with existing GoogleTest suites and tooling. This back-end shall not be required for any documented workflow.

**TOOL-HAR-070** *(S, P2, A)* — Harness generation shall be template-driven such that support for an additional test framework requires only new templates, not tool source changes.

**TOOL-HAR-080** *(M, P2, T)* — The tool shall generate an integration-level harness spanning two or more units, stubbing only dependencies external to the selected set.

**TOOL-HAR-090** *(M, P2, I)* — Generated harness code shall be human-readable, deterministically formatted, and carry a header identifying it as generated, the generating tool version, and the source model.

**TOOL-HAR-100** *(M, P2, T)* — Regenerating a harness shall preserve user modifications in designated user-editable regions, or shall detect and report conflicts rather than silently overwriting.

**TOOL-HAR-110** *(S, P2, T)* — The tool shall detect and report when the UUT interface has changed such that an existing harness is stale.

**TOOL-HAR-120** *(M, P2, T)* — The tool shall resolve all undefined external references in the harness link step, either by stub generation or by explicit user-supplied linkage, and shall report any that remain unresolved.

---

## 7. Stub and Mock Generation (STB)

**TOOL-STB-010** *(M, P2, T)* — The tool shall automatically generate a stub for every external function called by the UUT.

**TOOL-STB-020** *(M, P2, T)* — Each generated stub shall have a signature identical to the function it replaces.

**TOOL-STB-030** *(M, P2, T)* — The tool shall generate, per stub, the type and structure declarations required for the stub to compile independently.

**TOOL-STB-040** *(M, P2, T)* — Generated stubs shall support, per test case: a configured return value, a sequence of return values across successive calls, and a user-supplied callback implementation.

**TOOL-STB-050** *(M, P2, T)* — Generated stubs shall record call count, and the argument values of each call, retrievable from test code.

**TOOL-STB-060** *(S, P2, T)* — Generated stubs shall support verification of call order across multiple stubs.

**TOOL-STB-070** *(M, P2, T)* — Generated stubs shall support output parameters, writing caller-supplied values through pointer arguments.

**TOOL-STB-080** *(M, P2, T)* — The user shall be able to disable stubbing for any individual function, linking the real implementation instead.

**TOOL-STB-090** *(S, P3, T)* — The tool shall support intercepting calls made by the UUT to functions defined within the UUT itself (call wrapping), without modifying user source.

**TOOL-STB-100** *(S, P2, T)* — The tool shall support stubbing of standard library functions on explicit user request.

**TOOL-STB-110** *(M, P2, T)* — Generated stubs shall be user-editable, with editable regions clearly delimited from regenerated regions.

**TOOL-STB-120** *(M, P2, T)* — When the source function signature changes, the tool shall re-synchronize the stub signature while preserving the user-authored body where the change permits, and shall report where it does not.

**TOOL-STB-130** *(S, P2, T)* — The tool shall flag, in generated output, every construct it could not fully handle (e.g. variadic functions, complex function pointers) using a consistent, greppable marker.

**TOOL-STB-140** *(S, P2, T)* — The tool shall support stubbing functions reached through function pointers, including function pointer members of structures.

---

## 8. Test Case Definition and Management (TCD)

**TOOL-TCD-010** *(M, P1, T)* — The tool shall support test cases authored directly in C source against the generated harness.

**TOOL-TCD-020** *(M, P2, T)* — The tool shall support data-driven test cases, in which input values, expected outputs, and stub behavior are specified as data separate from code.

**TOOL-TCD-030** *(M, P2, I)* — Data-driven test cases shall be stored in a plain-text, diffable, version-controllable format.

**TOOL-TCD-040** *(M, P2, T)* — A test case shall be able to specify: input parameter values, initial values of accessed globals, expected return value, expected final values of globals, expected output parameter values, and stub behavior and expectations.

**TOOL-TCD-050** *(M, P2, T)* — The tool shall support expected-value comparison for all scalar C types, enums, pointers, arrays, structs, and unions.

**TOOL-TCD-060** *(M, P2, T)* — The tool shall support tolerance-based comparison for floating-point expected values.

**TOOL-TCD-070** *(S, P2, T)* — The tool shall support ranged inputs, generating one executed test per value in the range.

**TOOL-TCD-080** *(S, P2, T)* — The tool shall support test case grouping into named suites, and selective execution by suite, unit, function, or test name.

**TOOL-TCD-090** *(M, P2, A)* — Test cases shall be independent: execution order shall not affect results, and the tool shall support randomized ordering to detect violations.

**TOOL-TCD-100** *(S, P2, T)* — The tool shall support import and export of test cases in a documented interchange format (CSV or equivalent).

**TOOL-TCD-110** *(S, P3, T)* — The tool shall support test case derivation via boundary value analysis and equivalence class partitioning of input parameters.

**TOOL-TCD-120** *(C, P3, T)* — The tool shall support classification-tree-based test case design.

**TOOL-TCD-130** *(S, P2, T)* — The tool shall support robustness test cases supplying out-of-range and invalid input values with normal range checking disabled.

**TOOL-TCD-140** *(M, P2, T)* — Each test case shall carry a stable unique identifier, preserved across edits and regeneration, for traceability purposes.

---

## 9. Automatic Test Generation (ATG)

**TOOL-ATG-010** *(S, P3, T)* — The tool shall automatically generate test cases intended to maximize structural coverage of a designated function.

**TOOL-ATG-020** *(S, P3, T)* — The tool shall support automatic test vector generation via symbolic execution of the UUT.

**TOOL-ATG-030** *(C, P3, T)* — The tool shall support automatic test vector generation via bounded model checking as an alternative or complementary engine.

**TOOL-ATG-040** *(M, P3, T)* — Every automatically generated test case shall be emitted in the same format as a manually authored test case and shall be editable thereafter.

**TOOL-ATG-050** *(M, P3, T)* — Every automatically generated test case shall be compiled and executed before being presented to the user; test cases that fail to compile or crash the harness shall not be presented as valid.

**TOOL-ATG-060** *(M, P3, T)* — The tool shall report, per generation run: number of test cases generated, coverage achieved, and the specific code constructs left uncovered.

**TOOL-ATG-070** *(M, P3, I)* — Automatically generated test cases shall be clearly marked as machine-generated in both the artifact and all reports.

**TOOL-ATG-080** *(M, P3, T)* — Generated test cases shall record the observed behavior as the expected value, and shall mark that expected value as unreviewed until a user confirms it.

**TOOL-ATG-090** *(S, P3, T)* — The tool shall support targeted generation against a specified uncovered line, branch, or condition, rather than whole-function generation only.

**TOOL-ATG-100** *(S, P3, D)* — The tool shall bound generation effort by configurable time and memory limits and shall terminate gracefully, returning whatever was generated.

**TOOL-ATG-110** *(S, P3, T)* — The tool shall report constructs the generation engine cannot handle (e.g. dynamic memory, floating point, concurrency, inline assembly) rather than failing silently.

---

## 10. Host Test Execution (EXE)

**TOOL-EXE-010** *(M, P1, T)* — The tool shall build and execute the test harness on the development host.

**TOOL-EXE-020** *(M, P1, T)* — The tool shall report, per test case: pass, fail, or error, with failures identifying the assertion, expected value, actual value, and source location.

**TOOL-EXE-030** *(M, P1, T)* — The tool shall isolate test execution such that a crash, hang, or abort in one test case does not prevent the remaining test cases from executing.

**TOOL-EXE-040** *(M, P1, T)* — The tool shall enforce a configurable per-test timeout and report timed-out tests as failures.

**TOOL-EXE-050** *(S, P1, T)* — The tool shall execute independent test executables in parallel, with configurable concurrency.

**TOOL-EXE-060** *(M, P1, T)* — The tool shall return a non-zero process exit status when any test fails, for CI consumption.

**TOOL-EXE-070** *(S, P2, T)* — The tool shall support launching a test case under a debugger, with the harness prepared and execution stopped at entry to the function under test.

**TOOL-EXE-080** *(S, P1, T)* — The tool shall support incremental rebuild, recompiling only artifacts affected by a change.

**TOOL-EXE-090** *(S, P2, T)* — The tool shall detect and report memory errors during host execution via sanitizer integration, without such detection being mandatory.

---

## 11. Target Test Execution (TGT)

**TOOL-TGT-010** *(M, P3, T)* — The tool shall build the test harness for a cross-compiled embedded target.

**TOOL-TGT-020** *(M, P3, T)* — The tool shall execute the test harness on an instruction-set simulator, verified against QEMU and Renode.

**TOOL-TGT-030** *(M, P3, T)* — The tool shall execute the test harness on physical target hardware via a debug probe.

**TOOL-TGT-040** *(M, P3, T)* — The tool shall support flashing target hardware via OpenOCD, pyOCD, and J-Link.

**TOOL-TGT-050** *(M, P3, T)* — The tool shall retrieve test results from the target via at minimum: semihosting, and a serial (UART) channel.

**TOOL-TGT-060** *(M, P3, A)* — The host-to-target result protocol shall be plain-text, line-oriented, and parseable without requiring a bidirectional channel.

**TOOL-TGT-070** *(M, P3, T)* — Test cases shall execute unmodified on host and target, with only configuration distinguishing the two.

**TOOL-TGT-080** *(S, P3, D)* — The tool shall support a declarative hardware inventory describing connected targets: identifier, platform, probe type, serial device, and flash timeout.

**TOOL-TGT-090** *(S, P3, T)* — The tool shall detect target execution failures — flash failure, no output, target reset, watchdog — and distinguish them from test failures.

**TOOL-TGT-100** *(S, P3, T)* — The tool shall support splitting a test suite across multiple target executions when the full suite exceeds target memory.

**TOOL-TGT-110** *(M, P3, A)* — The tool shall document the RAM, flash, and stack overhead of the on-target harness, per configuration.

**TOOL-TGT-120** *(C, P3, T)* — The tool shall support execution on targets without a debug probe via a user-supplied flashing and communication script.

---

## 12. Code Coverage (COV)

**TOOL-COV-010** *(M, P1, T)* — The tool shall measure statement coverage.

**TOOL-COV-020** *(M, P1, T)* — The tool shall measure branch/decision coverage.

**TOOL-COV-030** *(M, P3, T)* — The tool shall measure function coverage.

**TOOL-COV-040** *(S, P3, T)* — The tool shall measure function call coverage.

**TOOL-COV-050** *(M, P3, T)* — The tool shall measure Modified Condition/Decision Coverage (MC/DC).

**TOOL-COV-060** *(M, P3, I)* — The tool shall state explicitly, in the user documentation and in every report, which MC/DC form is measured (masking or unique-cause) and by which compiler mechanism.

**TOOL-COV-070** *(M, P3, T)* — The tool shall report, for each partially covered decision, which individual conditions were not exercised true and which were not exercised false.

**TOOL-COV-080** *(M, P3, T)* — The tool shall detect and report boolean expressions that the compiler could not instrument for MC/DC, including those exceeding compiler condition-count limits.

**TOOL-COV-090** *(S, P4, T)* — The tool shall support unique-cause MC/DC, or shall document the precise gap between the supported form and unique-cause MC/DC.

**TOOL-COV-100** *(M, P3, T)* — The tool shall retrieve coverage data from bare-metal targets with no filesystem and no operating system.

**TOOL-COV-110** *(M, P1, T)* — The tool shall merge coverage data across multiple test executions into a single result set.

**TOOL-COV-120** *(M, P1, T)* — The tool shall attribute coverage to individual test cases, enabling per-test coverage reporting.

**TOOL-COV-130** *(M, P1, T)* — The tool shall enforce configurable minimum coverage thresholds per metric and fail the run when they are not met.

**TOOL-COV-140** *(S, P4, T)* — The tool shall support coverage-by-analysis: recording a user-supplied justification for code that cannot be covered by test, and reflecting it in reports as justified rather than covered.

**TOOL-COV-150** *(M, P3, I)* — Justifications under TOOL-COV-140 shall record author, date, and rationale, and shall be invalidated when the associated source changes.

**TOOL-COV-160** *(S, P3, T)* — The tool shall report coverage of the unit under test separately from coverage of harness, stub, and framework code.

**TOOL-COV-170** *(S, P4, T)* — The tool shall support control coupling and data coupling analysis between integrated units.

---

## 13. Change-Based and Regression Testing (CBT)

**TOOL-CBT-010** *(M, P2, T)* — The tool shall re-execute an existing test suite without regeneration or manual reconfiguration.

**TOOL-CBT-020** *(S, P3, T)* — The tool shall determine, from a source change, the set of test cases whose covered code was affected.

**TOOL-CBT-030** *(S, P3, T)* — The tool shall support executing only the affected subset identified under TOOL-CBT-020.

**TOOL-CBT-040** *(M, P3, I)* — When a subset is executed, all reports shall state clearly that the run was partial and identify which tests were not executed.

**TOOL-CBT-050** *(S, P3, T)* — The tool shall compare a test run against a previous run and report newly failing, newly passing, and newly added tests.

**TOOL-CBT-060** *(S, P3, T)* — The tool shall report coverage change relative to a baseline run.

**TOOL-CBT-070** *(S, P2, T)* — The tool shall detect that a test case is stale because the interface it exercises has changed.

**TOOL-CBT-080** *(C, P3, T)* — The tool shall support test suite minimization, identifying redundant test cases contributing no unique coverage.

---

## 14. Requirements Traceability (TRC)

**TOOL-TRC-010** *(M, P4, T)* — The tool shall support associating one or more requirement identifiers with each test case.

**TOOL-TRC-020** *(M, P4, T)* — The tool shall generate a bidirectional traceability matrix linking requirements to test cases and test cases to requirements.

**TOOL-TRC-030** *(M, P4, T)* — The traceability matrix shall report the pass/fail status of each linked test case.

**TOOL-TRC-040** *(M, P4, T)* — The tool shall report requirements with no linked test case, and test cases with no linked requirement.

**TOOL-TRC-050** *(S, P4, T)* — The tool shall import requirements from ReqIF.

**TOOL-TRC-060** *(S, P4, T)* — The tool shall import requirements from CSV and from a documented plain-text format.

**TOOL-TRC-070** *(S, P4, T)* — The tool shall export traceability data in ReqIF for exchange with external requirements management tools.

**TOOL-TRC-080** *(S, P4, T)* — The tool shall link requirements to source code elements in addition to test cases.

**TOOL-TRC-090** *(S, P4, T)* — The tool shall detect when a requirement has changed since its linked test cases were last executed or reviewed.

**TOOL-TRC-100** *(C, P4, T)* — The tool shall interoperate with an established open-source traceability tool rather than requiring its own requirements database.

---

## 15. Reporting (REP)

**TOOL-REP-010** *(M, P1, T)* — The tool shall produce a machine-readable test result report in JUnit XML format.

**TOOL-REP-020** *(M, P1, T)* — The tool shall produce a machine-readable coverage report in a standard format (Cobertura XML and/or LCOV).

**TOOL-REP-030** *(M, P1, T)* — The tool shall produce a human-readable HTML report combining test results and coverage.

**TOOL-REP-040** *(M, P2, T)* — The HTML report shall present annotated source code showing per-line coverage status.

**TOOL-REP-050** *(M, P3, T)* — The HTML report shall present, for each decision, the MC/DC condition status detail required by TOOL-COV-070.

**TOOL-REP-060** *(M, P4, T)* — The tool shall produce a verification report suitable for submission as certification evidence, containing: tool identification and version, configuration, test cases executed with results, coverage achieved per metric, justified exclusions, and the traceability matrix.

**TOOL-REP-070** *(M, P4, I)* — Every report shall record the tool version, the compiler and version used, the target executed on, and the timestamp of execution.

**TOOL-REP-080** *(M, P4, T)* — The tool shall produce reports in a paginated, archivable format (PDF) for records retention.

**TOOL-REP-090** *(S, P2, A)* — All report formats shall be generated from a single documented intermediate data model, so custom report formats can be added without re-running tests.

**TOOL-REP-100** *(M, P2, T)* — Report generation shall be deterministic: identical inputs shall produce byte-identical reports, excluding timestamps.

**TOOL-REP-110** *(S, P3, T)* — The tool shall produce a summary report aggregating results across multiple units, targets, and toolchains.

**TOOL-REP-120** *(S, P4, T)* — The tool shall report coverage trend across successive runs.

**TOOL-REP-130** *(M, P4, I)* — Report formats used as certification evidence shall be versioned, and changes to them shall be documented, so that archived reports remain interpretable.

**TOOL-REP-140** *(M, P4, T)* — Every report shall identify the test scope it covers and shall state explicitly what was excluded from that scope.

**TOOL-REP-150** *(S, P4, T)* — The tool shall support generating a report from previously archived result data without re-executing tests.

---

## 16. CI/CD Integration (CIC)

**TOOL-CIC-010** *(M, P1, D)* — All tool functionality required for automated verification shall be accessible from a non-interactive command-line interface.

**TOOL-CIC-020** *(M, P1, T)* — The tool shall operate without a graphical environment or display server.

**TOOL-CIC-030** *(M, P1, T)* — The tool shall use documented, stable exit codes distinguishing: success, test failure, coverage threshold failure, and tool error.

**TOOL-CIC-040** *(M, P1, D)* — The tool shall be installable and executable within a container image.

**TOOL-CIC-050** *(S, P2, D)* — The project shall provide reference pipeline configurations for GitHub Actions and GitLab CI.

**TOOL-CIC-060** *(S, P3, T)* — The tool shall support sharding a test suite across multiple CI runners and merging the resulting reports.

**TOOL-CIC-070** *(S, P2, T)* — The tool shall support caching of ingestion and analysis artifacts across CI runs.

**TOOL-CIC-080** *(S, P2, I)* — All tool configuration shall be expressible in version-controlled files; no configuration shall exist only in a GUI or local state.

---

## 17. User Interface (UIX)

> **Design position:** The tool's primary user interface is a **standalone application** owning the complete test workflow, in the manner of VectorCAST, Tessy, and Cantata's dedicated GUI. It shall not require an external editor or IDE to be installed, and no workflow shall be reachable only through a third-party host application.

### 17.1 Architecture

**TOOL-UIX-010** *(M, P1, A)* — The tool's core shall be a command-line engine; all graphical interfaces shall be clients of that engine and shall provide no capability unavailable from it.

**TOOL-UIX-020** *(M, P2, A)* — The engine shall expose a documented, versioned interface (JSON over stdio or local socket) for front-end clients.

**TOOL-UIX-030** *(M, P2, D)* — The tool shall provide a standalone graphical application that supports the complete test workflow — project creation, environment build, test authoring, execution, coverage review, and reporting — without requiring the installation of any editor, IDE, or third-party host application.

**TOOL-UIX-040** *(M, P2, I)* — The standalone application shall be installable and runnable by a user who has no development environment beyond a C toolchain.

**TOOL-UIX-050** *(M, P2, T)* — The standalone application shall operate against a local engine instance and shall require no network access.

### 17.2 Project and environment management

**TOOL-UIX-060** *(M, P2, T)* — The application shall support creating, opening, saving, and closing a test project that references user source without copying or modifying it.

**TOOL-UIX-070** *(M, P2, T)* — The application shall provide a guided environment-creation workflow collecting: source selection or test scope, compiler configuration, target (host or embedded), coverage kind, and test framework back-end.

**TOOL-UIX-080** *(M, P2, T)* — The application shall support creating an integration test environment by selecting multiple source files into a single test scope, and shall display the resulting internal/external dependency classification before the environment is built.

**TOOL-UIX-090** *(M, P2, T)* — The application shall display environment build progress and, on failure, the compiler diagnostics responsible, navigable to the offending source location.

**TOOL-UIX-100** *(S, P2, T)* — The application shall support managing multiple environments within one project and executing across a selected subset.

### 17.3 Navigation and status

**TOOL-UIX-110** *(M, P2, T)* — The application shall present a hierarchical navigation tree: project → environment → unit → function → test case.

**TOOL-UIX-120** *(M, P2, T)* — Each tree node shall display aggregated status: pass/fail counts, coverage percentage, and whether the node is stale relative to its source.

**TOOL-UIX-130** *(M, P2, T)* — The application shall support selecting any tree node and executing, editing, or reporting on that node's scope.

**TOOL-UIX-140** *(S, P2, T)* — The application shall support filtering and searching the tree by name, status, and coverage threshold.

### 17.4 Test authoring

**TOOL-UIX-150** *(M, P3, T)* — The application shall provide a tabular editor for data-driven test cases, presenting input parameters, global variables, and expected values as editable fields.

**TOOL-UIX-160** *(M, P3, T)* — The test case editor shall present structured and array parameters as an expandable tree, permitting entry of values at any depth.

**TOOL-UIX-170** *(M, P3, T)* — The test case editor shall be type-aware, constraining or validating entered values against the declared C type and presenting enumeration constants by name.

**TOOL-UIX-180** *(M, P3, T)* — The application shall provide a stub configuration view listing every external dependency of the environment, with per-stub controls to enable or disable stubbing and to define return values, return sequences, and output parameter values.

**TOOL-UIX-190** *(S, P3, T)* — The application shall support entering ranged and boundary-derived input values, displaying the resulting number of generated test cases before they are created.

**TOOL-UIX-200** *(S, P3, T)* — The application shall provide an editor for test cases authored directly in C, with syntax highlighting, alongside the tabular editor.

### 17.5 Execution and results

**TOOL-UIX-210** *(M, P2, T)* — The application shall support executing a selection of tests with visible progress and the ability to cancel a run in progress.

**TOOL-UIX-220** *(M, P2, T)* — The application shall present per-test results identifying, for each failure, the assertion, expected value, actual value, and source location, navigable to that location.

**TOOL-UIX-230** *(M, P3, T)* — The application shall support launching a test case under a debugger with execution stopped at entry to the function under test.

**TOOL-UIX-240** *(S, P2, T)* — The application shall present a console pane displaying the engine commands executed on the user's behalf, so that any GUI action can be reproduced from the command line.

### 17.6 Coverage and reporting

**TOOL-UIX-250** *(M, P2, T)* — The application shall present annotated source with per-line coverage status distinguishing covered, uncovered, partially covered, and justified-by-analysis.

**TOOL-UIX-260** *(M, P3, T)* — The application shall present, for each partially covered decision, the per-condition detail required by TOOL-COV-070, in a form that identifies which condition outcomes remain unexercised.

**TOOL-UIX-270** *(S, P3, T)* — The application shall present a graphical control flow view of a function with coverage status overlaid.

**TOOL-UIX-280** *(M, P2, T)* — The application shall present coverage summarized by project, environment, unit, and function, with drill-down between levels.

**TOOL-UIX-290** *(S, P4, T)* — The application shall support recording a coverage-by-analysis justification against a specific uncovered construct, capturing author and rationale.

**TOOL-UIX-300** *(M, P4, T)* — The application shall support generating and viewing all report formats defined in Section 15 without leaving the application.

**TOOL-UIX-310** *(S, P4, T)* — The application shall present the requirements traceability matrix, with navigation from a requirement to its linked test cases and results.

### 17.7 Constraints

**TOOL-UIX-320** *(M, P1, I)* — All project, environment, test case, and configuration state shall be stored in plain-text, version-controllable files. The graphical application shall never be the sole source of any state.

**TOOL-UIX-330** *(M, P2, T)* — A project created, modified, or executed through the graphical application shall be fully usable from the command line thereafter, and the reverse.

**TOOL-UIX-340** *(M, P2, T)* — The standalone application shall run on Linux x86-64 and Windows x86-64.

**TOOL-UIX-350** *(M, P2, I)* — The application shall transmit no telemetry, usage data, or user content to any external service.

**TOOL-UIX-360** *(S, P2, D)* — The application shall provide error messages identifying the affected file, line, and a concrete remedy.

**TOOL-UIX-370** *(S, P3, T)* — The application shall remain responsive during long-running operations, performing analysis, build, and execution without blocking the interface.

**TOOL-UIX-380** *(C, P4, T)* — The application shall support a keyboard-driven workflow for its primary operations.

### 17.8 Deferred

**TOOL-UIX-390** *(F, —, —)* — Editor and IDE integrations may be provided as additional thin clients of the engine interface defined in TOOL-UIX-020. Such integrations are explicitly out of scope for v1.0 and shall never be a prerequisite for any workflow.

**TOOL-UIX-400** *(F, —, —)* — A browser-based interface for viewing results and coverage across multiple projects may be provided for team-level and CI use. Out of scope for v1.0.

---

## 18. AI-Assisted Features (AIF)

**TOOL-AIF-010** *(M, P3, T)* — All AI-assisted features shall be optional; the tool shall provide its full non-AI functionality with AI disabled, and AI shall be disabled by default.

**TOOL-AIF-020** *(M, P3, T)* — The tool shall support a locally-executed model requiring no network access.

**TOOL-AIF-030** *(M, P3, T)* — The tool shall not transmit user source code, test data, or project metadata to any external service unless the user has explicitly enabled a remote provider for that session.

**TOOL-AIF-040** *(M, P3, D)* — The tool shall display, before first use of a remote provider, exactly what data will be transmitted and to whom.

**TOOL-AIF-050** *(M, P3, A)* — The tool shall abstract AI providers behind a single interface supporting local runtimes and remote APIs interchangeably.

**TOOL-AIF-060** *(S, P3, T)* — The tool shall support AI-assisted generation of test cases targeting specified uncovered code.

**TOOL-AIF-070** *(M, P3, T)* — Every AI-generated artifact shall be compiled and executed before presentation; artifacts that fail to compile, crash, or fail to increase coverage shall be discarded or presented as rejected.

**TOOL-AIF-080** *(M, P3, I)* — Every AI-generated artifact shall be permanently and visibly marked as AI-generated, including the model identifier and generation timestamp, in the artifact and in all reports.

**TOOL-AIF-090** *(M, P3, T)* — AI-generated artifacts shall be recorded as unreviewed until explicitly marked reviewed by an identified user, and reports shall distinguish reviewed from unreviewed.

**TOOL-AIF-100** *(M, P4, T)* — The tool shall support a configuration mode that prohibits AI-generated artifacts from contributing to certification evidence.

**TOOL-AIF-110** *(S, P3, T)* — The tool shall support AI-assisted generation of stub bodies from calling context.

**TOOL-AIF-120** *(S, P3, T)* — The tool shall support AI-assisted explanation of test failures in natural language.

**TOOL-AIF-130** *(C, P4, T)* — The tool shall support AI-assisted proposal of links between requirements text and test cases, presented as suggestions requiring confirmation.

**TOOL-AIF-140** *(C, P3, T)* — The tool shall support AI-assisted naming and documentation of generated test cases.

**TOOL-AIF-150** *(M, P3, T)* — AI operations shall be bounded by configurable time and token limits and shall fail without blocking the surrounding workflow.

**TOOL-AIF-160** *(S, P3, A)* — The tool shall record the prompt, model, and parameters used for each AI-generated artifact, for auditability.

**TOOL-AIF-170** *(M, P3, I)* — The tool shall document the minimum hardware required for each supported local model configuration.

**TOOL-AIF-180** *(M, P3, T)* — AI generation parameters affecting output variability, including sampling temperature and random seed, shall be user-configurable and recorded with each generated artifact.

**TOOL-AIF-190** *(M, P3, I)* — The tool shall record the identity and version of the model used to produce each artifact, in a form that remains meaningful after the model is superseded.

**TOOL-AIF-200** *(S, P3, T)* — The tool shall verify the integrity of a locally installed model against a published hash before use.

**TOOL-AIF-210** *(M, P3, T)* — Where an AI-generated artifact is rejected by the validation required in TOOL-AIF-070, the tool shall record that a rejection occurred, so that acceptance rates are visible rather than hidden.

---

## 19. Qualification and Safety Standards (QUA)

**TOOL-QUA-010** *(M, P4, I)* — The tool shall be accompanied by a Tool Classification analysis addressing ISO 26262-8 Tool Impact and Tool error Detection, yielding a Tool Confidence Level.

**TOOL-QUA-020** *(M, P4, I)* — The tool shall be accompanied by a documented Tool Operational Requirements specification defining its intended use, operating environment, and known limitations.

**TOOL-QUA-030** *(M, P4, I)* — The tool shall have a validation test suite demonstrating that it satisfies its Tool Operational Requirements, executable by the end user.

**TOOL-QUA-040** *(M, P4, I)* — The tool shall publish a documented list of known errors and their workarounds, maintained per release.

**TOOL-QUA-050** *(M, P4, I)* — Each release shall be uniquely identified and archived such that a specific version can be reproduced.

**TOOL-QUA-060** *(M, P4, T)* — The tool shall record, in every artifact it generates, sufficient information to reproduce that artifact.

**TOOL-QUA-070** *(S, P4, I)* — The tool shall document its own development process, change control, and defect management to support user assessment.

**TOOL-QUA-080** *(S, P4, I)* — The tool shall document the mapping between its capabilities and the verification objectives of ISO 26262, IEC 61508, IEC 62304, EN 50128, and DO-178C.

**TOOL-QUA-090** *(M, P4, I)* — The tool shall not claim certification or qualification it does not hold; documentation shall state clearly what qualification evidence is provided and what remains the user's responsibility.

**TOOL-QUA-100** *(C, P4, I)* — The tool shall provide templates for the user's own tool qualification artifacts.

---

## 20. Non-Functional Requirements (NFR)

**TOOL-NFR-010** *(M, P1, T)* — The tool shall run on Linux x86-64.

**TOOL-NFR-020** *(S, P2, T)* — The tool shall run on Windows and macOS.

**TOOL-NFR-030** *(M, P2, D)* — Environment creation for a single translation unit of 1000 lines shall complete in under 30 seconds on typical developer hardware.

**TOOL-NFR-040** *(S, P2, D)* — Incremental re-execution of an unchanged test suite of 100 test cases shall complete in under 10 seconds on host.

**TOOL-NFR-050** *(M, P2, A)* — The tool shall scale to projects of at least 500 translation units and 10,000 test cases.

**TOOL-NFR-060** *(M, P1, A)* — All tool outputs shall be deterministic and reproducible given identical inputs.

**TOOL-NFR-070** *(M, P1, I)* — The tool shall not modify user source files.

**TOOL-NFR-080** *(M, P1, I)* — All tool-generated files shall be written to a designated output directory, separable from user source.

**TOOL-NFR-090** *(M, P2, T)* — The tool shall fail safely: on internal error it shall report the error and exit non-zero rather than emitting incomplete or misleading results.

**TOOL-NFR-100** *(M, P2, I)* — The tool shall not require network access for any non-AI functionality.

**TOOL-NFR-110** *(S, P2, I)* — Installation shall not require administrative privileges.

**TOOL-NFR-120** *(M, P2, I)* — The tool shall provide user documentation covering installation, every supported workflow, and every configuration option.

**TOOL-NFR-130** *(S, P2, T)* — The tool shall log its operations at configurable verbosity to support diagnosis of failures.

**TOOL-NFR-140** *(M, P2, A)* — The tool's own test suite shall achieve and maintain a documented coverage threshold of its own source.

**TOOL-NFR-150** *(S, P2, D)* — The tool shall operate within a documented memory ceiling on a project of the scale defined in TOOL-NFR-050, and shall degrade predictably rather than exhausting host memory.

**TOOL-NFR-160** *(M, P2, T)* — The tool shall produce, on request, a diagnostic bundle containing version information, configuration, and logs sufficient to reproduce a reported defect, with its contents documented per TOOL-SEC-120.

**TOOL-NFR-170** *(S, P3, D)* — The tool shall be used to test the C components of its own implementation, where such components exist.

**TOOL-NFR-180** *(M, P2, T)* — Long-running operations shall be interruptible, and interruption shall leave project data in a valid state.

**TOOL-NFR-190** *(S, P2, I)* — User-facing text shall be externalized from code to permit translation, without translation being delivered in v1.0.

---

## 21. Licensing and Distribution (LIC)

**TOOL-LIC-010** *(M, P1, I)* — The tool's own source code shall be released under a permissive open-source license.

**TOOL-LIC-020** *(M, P1, I)* — Components under strong copyleft licenses shall be invoked as separate processes and shall not be linked into the tool.

**TOOL-LIC-030** *(M, P1, I)* — The project shall maintain a Software Bill of Materials listing every dependency, its version, and its license.

**TOOL-LIC-040** *(M, P2, I)* — Code generated by the tool shall be free of licensing restriction imposed by the tool, and this shall be stated explicitly in the documentation.

**TOOL-LIC-050** *(M, P2, I)* — The tool shall not bundle any component whose license prohibits commercial use or redistribution.

**TOOL-LIC-060** *(S, P2, I)* — The build shall verify dependency licenses automatically and fail on introduction of a disallowed license.

**TOOL-LIC-070** *(S, P3, I)* — Optional components with restrictive licenses shall be separable, such that a build excluding them remains fully functional for its documented feature set.

---

## 22. Security and Integrity (SEC)

> **Rationale:** The tool compiles and executes code supplied by its user, and generates code that is executed. It is therefore an arbitrary-code-execution surface by design. Separately, a tool used to produce safety evidence is a supply-chain target: compromising it corrupts the evidence rather than the product, which is harder to detect.

**TOOL-SEC-010** *(M, P2, I)* — Every release artifact shall be cryptographically signed, and the signature verification procedure shall be documented.

**TOOL-SEC-020** *(M, P2, I)* — Every release shall publish a Software Bill of Materials with the resolved version and cryptographic hash of every dependency.

**TOOL-SEC-030** *(M, P2, D)* — The build shall be reproducible: an independent party building from a given source revision shall obtain functionally identical artifacts, and the procedure shall be documented.

**TOOL-SEC-040** *(M, P2, I)* — Dependencies shall be pinned to exact versions with integrity hashes; the build shall fail on hash mismatch.

**TOOL-SEC-050** *(M, P2, D)* — The tool shall warn before executing user-supplied code — including test cases, stub bodies, and build scripts — from a project the user has not previously opened.

**TOOL-SEC-060** *(S, P3, T)* — The tool shall support executing test harnesses under a restricted execution context limiting filesystem and network access, without such restriction being mandatory.

**TOOL-SEC-070** *(M, P2, T)* — The tool shall not execute code embedded in project configuration files. Configuration shall be data, not script.

**TOOL-SEC-080** *(M, P2, I)* — The project shall document a security disclosure process and a supported-version policy.

**TOOL-SEC-090** *(M, P3, T)* — Where the tool retrieves data from a target device or external process, it shall treat that data as untrusted input and shall not execute or interpret it as code.

**TOOL-SEC-100** *(S, P3, I)* — The project shall perform automated dependency vulnerability scanning as part of its own CI, and shall publish the results.

**TOOL-SEC-110** *(M, P3, T)* — Credentials, tokens, and API keys for optional remote services shall be stored using platform-provided secure storage and shall never be written to project files, logs, or reports.

**TOOL-SEC-120** *(M, P2, T)* — Diagnostic output and logs shall not contain user source code content beyond what is necessary to identify a location, and the tool shall document exactly what a diagnostic bundle contains.

---

## 23. Migration and Interoperability (MIG)

> **Rationale:** Adoption is the binding constraint on an open-source tool competing with entrenched commercial products. A team with 4,000 existing test cases in a commercial tool will not re-author them. Migration capability is not a convenience feature; it is the primary adoption mechanism.

**TOOL-MIG-010** *(M, P2, T)* — The tool shall execute existing test suites written against supported frameworks (Unity, cmocka) without requiring them to be rewritten.

**TOOL-MIG-020** *(S, P2, T)* — The tool shall import an existing Ceedling project, preserving test cases and configuration.

**TOOL-MIG-030** *(S, P3, T)* — The tool shall import test case data from commercial tools where those tools provide a documented or plain-text export format, converting inputs, expected values, and stub configuration.

**TOOL-MIG-040** *(M, P3, T)* — Import shall report, per imported artifact, what was converted, what was converted with loss of fidelity, and what could not be converted, rather than silently discarding content.

**TOOL-MIG-050** *(S, P3, T)* — The tool shall import test cases from a documented CSV interchange format, permitting migration via spreadsheet from any source.

**TOOL-MIG-060** *(M, P2, T)* — The tool shall export test cases and results in documented open formats sufficient to reconstruct them in another tool, so that adopting this tool does not create lock-in.

**TOOL-MIG-070** *(S, P3, T)* — The tool shall support coexistence: operating on a project that is also tested by another tool, without interfering with that tool's artifacts.

**TOOL-MIG-080** *(S, P4, T)* — The tool shall import and export coverage data in standard interchange formats, permitting aggregation with coverage produced by other tools.

**TOOL-MIG-090** *(C, P4, T)* — The tool shall provide a migration assessment mode that analyses an existing project and reports the expected fidelity and manual effort of migration before migration is attempted.

**TOOL-MIG-100** *(M, P2, I)* — All interchange formats the tool consumes or produces shall be documented to a level permitting independent implementation.

---

## 24. Installation and Deployment (INS)

> **Rationale:** A substantial share of the target market operates air-gapped or under restrictive endpoint policy. An installation path that assumes internet access excludes exactly the users most likely to need the tool.

**TOOL-INS-010** *(M, P2, D)* — The tool shall provide a fully offline installation path requiring no network access at install time.

**TOOL-INS-020** *(M, P2, D)* — The tool shall be installable without administrative privileges.

**TOOL-INS-030** *(M, P2, D)* — Installation shall not require the user to install or configure a language runtime, package manager, or compiler beyond their existing C toolchain.

**TOOL-INS-040** *(M, P2, I)* — Each release shall be archivable as a self-contained artifact that can be retained and reinstalled years later without reference to any external service.

**TOOL-INS-050** *(M, P2, T)* — Multiple versions of the tool shall be installable side by side, so that a project can remain pinned to the version under which its evidence was produced.

**TOOL-INS-060** *(M, P2, T)* — Upgrading shall not modify or migrate existing project data without explicit user confirmation.

**TOOL-INS-070** *(M, P2, D)* — The tool shall provide a documented uninstallation procedure that removes all installed components and identifies any user data left in place.

**TOOL-INS-080** *(M, P2, T)* — On first run the tool shall verify its environment — toolchain presence, versions, and feature availability — and report clearly what is missing or unsupported.

**TOOL-INS-090** *(S, P2, D)* — The tool shall provide a container image suitable for CI use, versioned in lockstep with releases.

**TOOL-INS-100** *(S, P3, D)* — The tool shall support a shared network or read-only installation serving multiple users, with per-user state held separately.

**TOOL-INS-110** *(M, P2, T)* — The tool shall report its version, build identifier, and the versions of its principal dependencies on request.

---

## 25. Extensibility (PLG)

> **Rationale:** No tool will support every compiler, target, report format, or workflow its users need. Extension points determine whether unmet needs become contributions or abandonment.

**TOOL-PLG-010** *(M, P2, A)* — The tool shall define documented extension points for, at minimum: compiler configurations, test framework back-ends, target execution methods, and report formats.

**TOOL-PLG-020** *(M, P2, T)* — Adding a compiler configuration shall require only a declarative configuration file, with no modification of tool source.

**TOOL-PLG-030** *(M, P2, T)* — Adding a test framework back-end shall require only new templates and a declarative descriptor, with no modification of tool source.

**TOOL-PLG-040** *(S, P3, T)* — Adding a target execution method shall be possible through a documented interface and a user-supplied script.

**TOOL-PLG-050** *(S, P3, T)* — Adding a report format shall be possible by consuming the documented intermediate report model, without re-executing tests.

**TOOL-PLG-060** *(M, P2, I)* — Extension interfaces shall be versioned, and breaking changes shall be documented with a migration path.

**TOOL-PLG-070** *(S, P3, T)* — The tool shall discover and load user-supplied extensions from a documented location without requiring reinstallation.

**TOOL-PLG-080** *(M, P3, D)* — The tool shall report clearly when an extension fails to load or is incompatible, and shall continue operating with the remaining functionality.

**TOOL-PLG-090** *(S, P3, I)* — The tool's own built-in compiler configurations, framework back-ends, and report formats shall be implemented through the same public extension points available to users, so those interfaces are proven by use.

---

## 26. Project Data Management (PRJ)

> **Rationale:** Test projects for safety-related software have lifetimes measured in decades. A project created today may need to be opened, re-executed, and defended in an audit long after the tool version that created it has been superseded.

**TOOL-PRJ-010** *(M, P2, I)* — All project data shall be stored in documented, plain-text, human-readable formats.

**TOOL-PRJ-020** *(M, P2, I)* — Every project data file shall carry an explicit schema version.

**TOOL-PRJ-030** *(M, P2, T)* — The tool shall open projects created by earlier versions, or shall report precisely why it cannot and what migration is required.

**TOOL-PRJ-040** *(M, P2, T)* — Project data migration shall be explicit, reversible where possible, and shall never occur without user confirmation.

**TOOL-PRJ-050** *(M, P2, T)* — Project data shall be stable under version control: operations that do not change meaning shall not change file content, and file ordering shall be deterministic.

**TOOL-PRJ-060** *(M, P2, T)* — Project data shall be structured such that concurrent edits by multiple users produce localized, resolvable version control conflicts rather than whole-file conflicts.

**TOOL-PRJ-070** *(M, P2, I)* — Project data shall reference user source by relative path, so that a project remains valid when the working tree is relocated or cloned.

**TOOL-PRJ-080** *(M, P2, I)* — Generated artifacts shall be distinguishable from user-authored artifacts by location or explicit marking, so that generated content can be excluded from version control.

**TOOL-PRJ-090** *(S, P3, T)* — The tool shall detect and report when project data references source, requirements, or configuration that no longer exists.

**TOOL-PRJ-100** *(M, P4, T)* — The tool shall support exporting a complete, self-contained record of a verification run — configuration, test cases, results, coverage, and tool version — suitable for long-term archival.

**TOOL-PRJ-110** *(S, P4, T)* — The tool shall support verifying an archived record against the tool version that produced it, reporting whether the record can be reproduced.

---

## 27. Open Questions for Review

The following require decisions before this specification is baselined:

1. **Standalone GUI technology** — TOOL-UIX-030 mandates a standalone application but deliberately does not name a technology. The choice (native toolkit vs. bundled-runtime desktop app) must be made before UI implementation, and it constrains TOOL-UIX-340 (Linux + Windows) and the contributor base.
2. **MC/DC form** — TOOL-COV-090 permits documenting the gap rather than implementing unique-cause MC/DC. Confirm whether target users' certification authorities accept masking MC/DC.
3. **Symbolic execution engine** — TOOL-ATG-020 does not name an engine. Decide between adopting an existing KLEE-based implementation and building fresh.
4. **Implementation language** — not yet specified. Affects TOOL-NFR-020 (Windows support) and contributor availability.
5. **Qualification scope** — TOOL-QUA-010 through TOOL-QUA-100 represent substantial effort. Confirm whether v1.0 targets qualification support or defers it entirely.
6. **Data-driven test format** — TOOL-TCD-030 requires plain text and diffable. Choose the concrete format (YAML, TOML, custom DSL) before implementation.
7. **Integration test scope** — TOOL-HAR-080, TOOL-COV-170, and the ING-120 through ING-190 test scope requirements establish integration testing as v1.0 scope. Confirm this is intended, as it materially increases P2 effort.
8. **Test scope definition format** — TOOL-ING-190 requires plain text. Decide whether the test scope file is the same artifact as the project file or separate.
9. **Debugger integration** — TOOL-UIX-230 requires launching under a debugger from a standalone application with no IDE present. Confirm the intended debugger front-end (embedded GDB/MI client vs. handing off to an external debugger).

---

## 28. Traceability Note

Requirement identifiers in this document are stable and intended for direct import into a requirements management tool. When the project adopts StrictDoc or OpenFastTrace, each requirement here becomes a node, and implementation and test artifacts reference these identifiers to establish coverage.

Recommended link types:
- `implements` — source code implementing a requirement
- `verifies` — the tool's own test case verifying a requirement
- `refines` — a lower-level requirement derived from one here

---

## 29. Glossary

Terms are defined as used in this document. Where a term has a standard-specific meaning, that meaning takes precedence in the relevant context.

| Term | Definition |
|---|---|
| **ATG** | Automatic Test Generation — derivation of test cases by the tool rather than by a person |
| **Coverage by analysis** | A recorded, human-authored justification that a code construct cannot be exercised by test, accepted in place of execution evidence |
| **Decision** | A boolean expression controlling program flow, composed of one or more conditions |
| **Condition** | A boolean operand within a decision containing no boolean operators |
| **Environment** | A built, executable configuration comprising a test scope, its harness, its stubs, and its toolchain settings |
| **Fake** | A dependency replacement with a working simplified implementation |
| **Harness** | Generated code that makes the code under test callable and observable from test cases |
| **Integration test** | A test exercising two or more units together, with dependencies outside the set replaced |
| **Masking MC/DC** | An MC/DC form in which a condition is shown independent by demonstrating that other conditions are masked out by short-circuit evaluation. Implemented by current GCC and Clang. |
| **MC/DC** | Modified Condition/Decision Coverage — every condition in a decision shown to independently affect the decision outcome |
| **Mock** | A dependency replacement that records interactions and permits assertions on them |
| **Stub** | A dependency replacement supplying controlled return values without asserting on interactions |
| **Test scope** | A named set of translation units treated as the code under test, with all dependencies outside the set treated as external |
| **TCL** | Tool Confidence Level — ISO 26262-8 classification determining required qualification rigour |
| **Tool qualification** | Demonstration that a tool is fit for its intended use in a safety-related development, performed for a specific project |
| **ToR** | Tool Operational Requirements — the specification of a tool's intended use, environment, and limitations |
| **Translation unit** | A single C source file together with everything it includes, as presented to the compiler |
| **Unique-cause MC/DC** | An MC/DC form requiring a pair of test cases differing in exactly one condition and producing differing decision outcomes. Stricter than masking MC/DC. |
| **Unit** | A single translation unit, or the smallest independently testable component of the software |
| **UUT** | Unit Under Test — the code a given test environment is built to exercise |

---

## 30. Document Change Control

This specification is under change control from the point it is baselined.

- Requirement identifiers are permanent. A deleted requirement leaves its identifier unused; a materially changed requirement receives a new identifier and the old one is marked superseded.
- Every change shall record: date, author, affected identifiers, and rationale.
- The specification version shall be incremented on every baselined change and referenced by every artifact traced to it.

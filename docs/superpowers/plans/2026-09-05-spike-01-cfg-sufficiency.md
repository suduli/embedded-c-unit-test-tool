# WP-SPIKE-01 — CFG Sufficiency Spike Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Adaptation note:** This is a P0 validation spike (throwaway/semi-throwaway research code), not production feature work. Steps are grouped by deliverable rather than atomized to single-line TDD cycles, but every step is still concrete and every claim in RESULTS.md must be backed by an actual run, not asserted.

**Goal:** Prove — or disprove, with evidence — that libclang's AST/cursor API alone is sufficient to extract functions, types, globals, and a call graph (PAR-030–PAR-060) from a real, ≥20 kLOC embedded C codebase with vendor headers, **without needing a full control-flow graph**.

**Architecture:** A standalone Python script uses the `libclang` PyPI wheel (prebuilt libclang, no system LLVM needed) to parse real STM32 HAL driver + CMSIS device source under an ARM bare-metal target triple, walks the AST to extract declarations and call edges, and classifies every call edge as direct (resolved via AST alone) or indirect (a function-pointer call that AST-only analysis cannot resolve). The count and nature of indirect edges is the spike's actual finding.

**Tech Stack:** Python 3.13, `libclang` (PyPI, bundles a prebuilt `libclang` shared library — this is the same dependency SDD-005 §5.3 recommends adopting for the real tool, so the spike also validates that choice), pytest.

**Spec:** [`PLAN-001-specification-analysis-and-work-breakdown.md`](../../../PLAN-001-specification-analysis-and-work-breakdown.md) §4.4 (`WP-SPIKE-01` pass criterion), [`design/SDD-005-external-integration.md`](../../SDD-005-external-integration.md) §5.3 (libclang selection rationale)

## Global Constraints

- Pass criterion (PLAN-001 §4.4, verbatim): "Function, type, global and call-graph extraction complete on a ≥20 kLOC embedded project with vendor headers, with no construct requiring a CFG. If a CFG is needed, §2.4 of ADR-001 fails and the C++ analyzer moves from 'later' to 'now'."
- K-04 (SDD-005 §2): must work air-gapped after initial fixture fetch — no network calls inside `extract.py` itself.
- K-05 (SDD-005 §2): no administrative privileges required for any step.
- libclang is the ADR-recommended C front-end (SDD-005 §5.3) — this spike doubles as validation of that choice, so do not substitute pycparser or tree-sitter here even though they're simpler to set up; that would test the wrong thing.
- Do not vendor the STM32CubeF4 fixture into the repository. It is BSD-3-Clause and fine to use locally for read-only analysis, but this repo is a design-documentation repo — the fixture is fetched on demand into a gitignored directory, never committed.

---

## File Structure

```
spikes/
  README.md                                 # index of all three spikes, pass/fail summary (create if absent)
  spike-01-cfg-sufficiency/
    README.md                               # what this spike tests, how to reproduce, links back to PLAN-001 §4.4
    requirements.txt                        # libclang==18.1.1, pytest
    .gitignore                              # fixture/
    fetch_fixture.sh                        # sparse-clones the STM32CubeF4 subset
    extract.py                              # the extraction engine (importable + CLI)
    tests/
      test_extract.py                       # unit tests against small inline C snippets
    run_spike.py                            # runs extract.py over fixture/, writes RESULTS.md
    RESULTS.md                              # filled in by Task 4 — real measured outcome, not drafted ahead
```

---

### Task 1: Fixture fetch script and repo scaffolding

**Files:**
- Create: `spikes/spike-01-cfg-sufficiency/fetch_fixture.sh`
- Create: `spikes/spike-01-cfg-sufficiency/.gitignore`
- Create: `spikes/spike-01-cfg-sufficiency/requirements.txt`
- Create: `spikes/spike-01-cfg-sufficiency/README.md`
- Create: `spikes/README.md`

**Interfaces:**
- Produces: `fixture/` directory (gitignored, created by running the fetch script) containing `CMSIS/Include`, `CMSIS/Device/ST/STM32F4xx/Include`, `HAL_Driver/Inc`, `HAL_Driver/Src` — consumed by Task 3's `run_spike.py`.

- [ ] **Step 1: Write the fetch script**

```bash
#!/usr/bin/env bash
# fetch_fixture.sh — pulls a real, ≥20kLOC embedded C codebase with vendor
# headers (STM32F4 HAL driver + CMSIS) for the CFG-sufficiency spike.
# BSD-3-Clause, STMicroelectronics. Not vendored into this repo — fetched
# on demand into a gitignored directory.
set -euo pipefail
cd "$(dirname "$0")"
rm -rf fixture
git clone --filter=blob:none --no-checkout --depth 1 \
  https://github.com/STMicroelectronics/STM32CubeF4.git fixture
cd fixture
git sparse-checkout init --cone
git sparse-checkout set \
  Drivers/CMSIS/Include \
  Drivers/CMSIS/Device/ST/STM32F4xx/Include \
  Drivers/STM32F4xx_HAL_Driver/Inc \
  Drivers/STM32F4xx_HAL_Driver/Src
git checkout
echo "Fixture ready. Line count:"
find Drivers -name '*.c' -o -name '*.h' | xargs wc -l | tail -1
```

- [ ] **Step 2: Make it executable and run it**

Run: `chmod +x fetch_fixture.sh && ./fetch_fixture.sh`
Expected: script completes, prints a total line count. **Record the actual total in RESULTS.md later — it must be ≥20,000 to satisfy the pass criterion's size floor.** If it comes in under 20k, widen the sparse-checkout to include a second peripheral family driver before proceeding (note this in RESULTS.md if it happens).

- [ ] **Step 3: `.gitignore` and `requirements.txt`**

```
# spikes/spike-01-cfg-sufficiency/.gitignore
fixture/
__pycache__/
*.pyc
report.json
```

```
# spikes/spike-01-cfg-sufficiency/requirements.txt
libclang==18.1.1
pytest==8.3.3
```

- [ ] **Step 4: Write `spikes/README.md`** (index, one paragraph plus a table with columns Spike / Question / Status — leave Status as "pending" for all three; another task updates this row when its RESULTS.md lands)

- [ ] **Step 5: Write this spike's own `README.md`** — restate the pass criterion verbatim from PLAN-001 §4.4, one line on how to reproduce (`./fetch_fixture.sh && pip install -r requirements.txt && python run_spike.py`), and a placeholder link to `RESULTS.md`.

- [ ] **Step 6: Commit**

```bash
git add spikes/README.md spikes/spike-01-cfg-sufficiency/README.md \
        spikes/spike-01-cfg-sufficiency/fetch_fixture.sh \
        spikes/spike-01-cfg-sufficiency/.gitignore \
        spikes/spike-01-cfg-sufficiency/requirements.txt
git commit -m "spike-01: fixture fetch script and scaffolding"
```

---

### Task 2: Extraction engine

**Files:**
- Create: `spikes/spike-01-cfg-sufficiency/extract.py`
- Test: `spikes/spike-01-cfg-sufficiency/tests/test_extract.py`

**Interfaces:**
- Consumes: `clang.cindex` from the `libclang` wheel (`pip install libclang` gives an importable top-level module named `clang`, i.e. `from clang.cindex import Index, CursorKind, Config`).
- Produces (for Task 3 and Task 4 to consume):
  - `parse_args_for(file_path: str, fixture_root: str) -> list[str]` — builds the clang invocation args (include paths, defines, target triple) for one source file.
  - `extract_translation_unit(tu) -> ExtractionResult` where `ExtractionResult` is a `@dataclass` with fields: `functions: list[FunctionInfo]`, `types: list[TypeInfo]`, `globals: list[GlobalInfo]`, `direct_calls: list[tuple[str, str]]` (caller, callee), `indirect_calls: list[IndirectCallInfo]`, `diagnostics: list[str]` (severity ≥ Error only).
  - `FunctionInfo(name: str, return_type: str, params: list[tuple[str, str]], is_static: bool, file: str, line: int)`
  - `TypeInfo(name: str, kind: str, fields: list[tuple[str, str]], nesting_depth: int, file: str)` — `kind` is one of `"struct"`, `"union"`, `"enum"`, `"typedef"`.
  - `GlobalInfo(name: str, type: str, is_static: bool, file: str, line: int)`
  - `IndirectCallInfo(caller: str, expr_text: str, declared_fn_ptr_type: str, file: str, line: int)` — recorded whenever a `CALL_EXPR`'s callee cursor does not resolve to a `FUNCTION_DECL` (i.e. it's a call through a variable/field of function-pointer type). This is the spike's central measurement: every one of these is a call-graph edge that AST-only extraction cannot resolve, and is exactly the kind of gap that would argue for CFG-level (or points-to) analysis.

- [ ] **Step 1: Write the target-triple and args builder, with a test**

```python
# tests/test_extract.py (partial — this step's test)
from extract import parse_args_for

def test_parse_args_targets_arm_bare_metal():
    args = parse_args_for("dummy.c", fixture_root="/fake/fixture")
    assert "-target" in args
    idx = args.index("-target")
    assert args[idx + 1] == "thumbv7em-none-eabi"
    assert "-DSTM32F407xx" in args
    assert any(a.startswith("-I") and "CMSIS" in a for a in args)
```

Run: `pytest tests/test_extract.py::test_parse_args_targets_arm_bare_metal -v`
Expected: FAIL — `extract.py` does not exist yet.

- [ ] **Step 2: Implement `parse_args_for`**

```python
# extract.py
import os

def parse_args_for(file_path: str, fixture_root: str) -> list[str]:
    """
    Build clang args to parse one STM32F4 HAL/CMSIS source file.
    Uses clang's own ARM target so vendor keywords like __weak, __packed
    and ARM-specific attribute extensions resolve without GCC-compat hacks
    — this is the same technique the real CMP-ANA would use per SDD-005 §5.3.
    """
    cmsis_core = os.path.join(fixture_root, "Drivers", "CMSIS", "Include")
    cmsis_device = os.path.join(
        fixture_root, "Drivers", "CMSIS", "Device", "ST", "STM32F4xx", "Include"
    )
    hal_inc = os.path.join(fixture_root, "Drivers", "STM32F4xx_HAL_Driver", "Inc")
    return [
        "-target", "thumbv7em-none-eabi",
        "-mcpu=cortex-m4",
        "-DSTM32F407xx",
        "-DUSE_HAL_DRIVER",
        f"-I{cmsis_core}",
        f"-I{cmsis_device}",
        f"-I{hal_inc}",
        "-std=c11",
        "-ferror-limit=0",
    ]
```

- [ ] **Step 3: Run the test, verify it passes**

Run: `pytest tests/test_extract.py::test_parse_args_targets_arm_bare_metal -v`
Expected: PASS

- [ ] **Step 4: Write extraction-logic tests against small inline C snippets** (fast, no fixture needed — these pin down behavior before running on 20kLOC of real vendor code)

```python
# tests/test_extract.py (continued)
import textwrap
from clang.cindex import Index
from extract import extract_translation_unit, parse_args_for

def _parse(source: str):
    index = Index.create()
    tu = index.parse(
        "test.c", args=["-target", "thumbv7em-none-eabi", "-std=c11"],
        unsaved_files=[("test.c", source)],
    )
    return tu

def test_extracts_function_signature():
    tu = _parse("int add(int a, int b) { return a + b; }")
    result = extract_translation_unit(tu)
    assert len(result.functions) == 1
    fn = result.functions[0]
    assert fn.name == "add"
    assert fn.return_type == "int"
    assert fn.params == [("int", "a"), ("int", "b")]
    assert fn.is_static is False

def test_extracts_static_function():
    tu = _parse("static void helper(void) {}")
    result = extract_translation_unit(tu)
    assert result.functions[0].is_static is True

def test_extracts_nested_struct_type():
    src = textwrap.dedent("""
        typedef struct {
            struct { unsigned char r, g, b; } color;
            int id;
        } Widget_t;
    """)
    tu = _parse(src)
    result = extract_translation_unit(tu)
    names = [t.name for t in result.types]
    assert "Widget_t" in names

def test_extracts_global_variable():
    tu = _parse("volatile int counter;")
    result = extract_translation_unit(tu)
    assert len(result.globals) == 1
    assert result.globals[0].name == "counter"

def test_direct_call_is_resolved():
    src = "void a(void) {} void b(void) { a(); }"
    tu = _parse(src)
    result = extract_translation_unit(tu)
    assert ("b", "a") in result.direct_calls
    assert result.indirect_calls == []

def test_indirect_call_through_function_pointer_is_flagged():
    src = textwrap.dedent("""
        typedef void (*handler_t)(int);
        void dispatch(handler_t h) { h(1); }
    """)
    tu = _parse(src)
    result = extract_translation_unit(tu)
    assert result.direct_calls == []
    assert len(result.indirect_calls) == 1
    assert result.indirect_calls[0].caller == "dispatch"
```

Run: `pytest tests/test_extract.py -v -k "not args"`
Expected: FAIL — `extract_translation_unit` does not exist yet.

- [ ] **Step 5: Implement `extract_translation_unit` and its data classes**

```python
# extract.py (continued)
from dataclasses import dataclass, field
from clang.cindex import CursorKind, TypeKind

@dataclass
class FunctionInfo:
    name: str
    return_type: str
    params: list[tuple[str, str]]
    is_static: bool
    file: str
    line: int

@dataclass
class TypeInfo:
    name: str
    kind: str
    fields: list[tuple[str, str]]
    nesting_depth: int
    file: str

@dataclass
class GlobalInfo:
    name: str
    type: str
    is_static: bool
    file: str
    line: int

@dataclass
class IndirectCallInfo:
    caller: str
    expr_text: str
    declared_fn_ptr_type: str
    file: str
    line: int

@dataclass
class ExtractionResult:
    functions: list[FunctionInfo] = field(default_factory=list)
    types: list[TypeInfo] = field(default_factory=list)
    globals: list[GlobalInfo] = field(default_factory=list)
    direct_calls: list[tuple[str, str]] = field(default_factory=list)
    indirect_calls: list[IndirectCallInfo] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)


def _loc(cursor):
    f = cursor.location.file
    return (str(f) if f else "<unknown>", cursor.location.line)


def _record_fields(cursor, depth=0):
    fields = []
    max_depth = depth
    for child in cursor.get_children():
        if child.kind == CursorKind.FIELD_DECL:
            fields.append((child.type.spelling, child.spelling))
            if child.type.get_declaration().kind in (
                CursorKind.STRUCT_DECL, CursorKind.UNION_DECL
            ):
                _, inner_depth = _record_fields(child.type.get_declaration(), depth + 1)
                max_depth = max(max_depth, inner_depth)
    return fields, max_depth


def _walk_calls(cursor, caller_name, result: ExtractionResult):
    for child in cursor.walk_preorder():
        if child.kind == CursorKind.CALL_EXPR:
            callee = child.referenced
            if callee is not None and callee.kind == CursorKind.FUNCTION_DECL:
                result.direct_calls.append((caller_name, callee.spelling))
            else:
                target_expr = next(child.get_children(), None)
                file_, line_ = _loc(child)
                result.indirect_calls.append(IndirectCallInfo(
                    caller=caller_name,
                    expr_text=child.spelling or (target_expr.spelling if target_expr else "<unknown>"),
                    declared_fn_ptr_type=(target_expr.type.spelling if target_expr else "<unknown>"),
                    file=file_, line=line_,
                ))


def extract_translation_unit(tu) -> ExtractionResult:
    result = ExtractionResult()
    for d in tu.diagnostics:
        if d.severity >= d.Error:
            result.diagnostics.append(str(d))

    for cursor in tu.cursor.get_children():
        file_, line_ = _loc(cursor)

        if cursor.kind == CursorKind.FUNCTION_DECL and cursor.is_definition():
            params = [(a.type.spelling, a.spelling) for a in cursor.get_arguments()]
            result.functions.append(FunctionInfo(
                name=cursor.spelling,
                return_type=cursor.result_type.spelling,
                params=params,
                is_static=cursor.storage_class.name == "STATIC",
                file=file_, line=line_,
            ))
            _walk_calls(cursor, cursor.spelling, result)

        elif cursor.kind in (CursorKind.STRUCT_DECL, CursorKind.UNION_DECL, CursorKind.ENUM_DECL):
            fields, depth = _record_fields(cursor)
            result.types.append(TypeInfo(
                name=cursor.spelling or "<anonymous>",
                kind=cursor.kind.name.replace("_DECL", "").lower(),
                fields=fields, nesting_depth=depth, file=file_,
            ))

        elif cursor.kind == CursorKind.TYPEDEF_DECL:
            underlying = cursor.underlying_typedef_type.get_declaration()
            fields, depth = _record_fields(underlying) if underlying.kind in (
                CursorKind.STRUCT_DECL, CursorKind.UNION_DECL
            ) else ([], 0)
            result.types.append(TypeInfo(
                name=cursor.spelling,
                kind="typedef",
                fields=fields, nesting_depth=depth, file=file_,
            ))

        elif cursor.kind == CursorKind.VAR_DECL:
            result.globals.append(GlobalInfo(
                name=cursor.spelling,
                type=cursor.type.spelling,
                is_static=cursor.storage_class.name == "STATIC",
                file=file_, line=line_,
            ))

    return result
```

- [ ] **Step 6: Run all extraction tests, verify they pass**

Run: `pytest tests/test_extract.py -v`
Expected: PASS on all cases. If `test_indirect_call_through_function_pointer_is_flagged` fails because `child.referenced` unexpectedly resolves through a typedef, adjust the resolution check to also verify `callee.kind == FUNCTION_DECL` against the *definition* cursor, not just any referenced cursor — do not weaken the test to make it pass.

- [ ] **Step 7: Commit**

```bash
git add spikes/spike-01-cfg-sufficiency/extract.py spikes/spike-01-cfg-sufficiency/tests/test_extract.py
git commit -m "spike-01: extraction engine with direct/indirect call classification"
```

---

### Task 3: Run against the real fixture and produce a report

**Files:**
- Create: `spikes/spike-01-cfg-sufficiency/run_spike.py`

**Interfaces:**
- Consumes: `extract.parse_args_for`, `extract.extract_translation_unit`, `fixture/` from Task 1.
- Produces: `report.json` (gitignored, intermediate) and the data Task 4 turns into `RESULTS.md`.

- [ ] **Step 1: Implement the runner**

```python
# run_spike.py
import glob
import json
import os
import sys
from clang.cindex import Index
from extract import parse_args_for, extract_translation_unit

FIXTURE_ROOT = os.path.join(os.path.dirname(__file__), "fixture")

def main():
    src_dir = os.path.join(FIXTURE_ROOT, "Drivers", "STM32F4xx_HAL_Driver", "Src")
    files = sorted(glob.glob(os.path.join(src_dir, "*.c")))
    if not files:
        print(f"No source files found under {src_dir} — run fetch_fixture.sh first.", file=sys.stderr)
        sys.exit(1)

    index = Index.create()
    totals = dict(functions=0, types=0, globals=0, direct_calls=0, indirect_calls=0, files_with_errors=0)
    all_indirect = []
    total_lines = 0

    for path in files:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            total_lines += sum(1 for _ in f)
        args = parse_args_for(path, FIXTURE_ROOT)
        tu = index.parse(path, args=args)
        result = extract_translation_unit(tu)
        totals["functions"] += len(result.functions)
        totals["types"] += len(result.types)
        totals["globals"] += len(result.globals)
        totals["direct_calls"] += len(result.direct_calls)
        totals["indirect_calls"] += len(result.indirect_calls)
        if result.diagnostics:
            totals["files_with_errors"] += 1
        all_indirect.extend(
            {"file": os.path.basename(path), "caller": c.caller, "expr": c.expr_text,
             "type": c.declared_fn_ptr_type, "line": c.line}
            for c in result.indirect_calls
        )

    report = {
        "files_parsed": len(files),
        "approx_total_lines": total_lines,
        "totals": totals,
        "indirect_calls_sample": all_indirect[:25],
        "indirect_calls_total": len(all_indirect),
    }
    with open(os.path.join(os.path.dirname(__file__), "report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `pip install -r requirements.txt && ./fetch_fixture.sh && python run_spike.py`
Expected: prints a JSON report; no unhandled exception. `files_with_errors` may be nonzero (vendor headers sometimes emit warnings/soft errors on unresolved intrinsics) — that's a finding to record, not a failure, **provided** `functions`, `types`, and `globals` are still populated (i.e. parsing degraded gracefully rather than producing an empty AST). If `functions == 0` across all files, do not proceed to Task 4 — debug the args builder first (most likely cause: a missing include path or an unresolved compiler-intrinsic header stopping the parse before any declarations are reached).

- [ ] **Step 3: Commit**

```bash
git add spikes/spike-01-cfg-sufficiency/run_spike.py
git commit -m "spike-01: runner producing extraction report over the real fixture"
```

---

### Task 4: Verdict and RESULTS.md

**Files:**
- Create: `spikes/spike-01-cfg-sufficiency/RESULTS.md`
- Modify: `spikes/README.md` (fill in this spike's row)

**Interfaces:**
- Consumes: `report.json` from Task 3.

- [ ] **Step 1: Write RESULTS.md from the actual report.json** — this step has no fixed code because the content depends on real output, but it MUST include, verbatim from the run:
  - Total lines parsed (must state whether it cleared the 20,000-line floor)
  - Counts: functions, types, globals, direct calls, indirect calls
  - The **verdict**: `PASS` if `indirect_calls_total == 0` (no construct needed anything beyond AST-level extraction); `PASS WITH DOCUMENTED GAP` if indirect calls exist but are correctly classified as unresolved rather than silently dropped or mis-attributed (this is the expected, honest outcome — function-pointer dispatch is common in HAL code, e.g. IRQ callback tables); `FAIL` only if extraction crashes, silently drops declarations, or misclassifies an indirect call as direct.
  - Under "PASS WITH DOCUMENTED GAP" (the likely outcome), state explicitly per PLAN-001 §4.4: indirect calls are a **known, bounded under-approximation**, not evidence that a CFG is required — resolving them needs a points-to/symbol-table pass (a well-understood, still-AST-adjacent technique), not statement-level control-flow analysis. Recommend this be tracked as a scoped enhancement to `WP-ANA-03` (call graph and scope classification) rather than a reason to escalate to `WP-ANA-05` (the separate, later CFG work package).
  - 3–5 concrete examples of indirect-call sites from `indirect_calls_sample`, with file/line, so a reviewer can spot-check them against the actual HAL source.
  - Any files with parse diagnostics, and whether they still yielded usable extraction (per Task 3 Step 2's guardrail).

- [ ] **Step 2: Update `spikes/README.md`'s summary table row for spike-01** with the verdict and a one-line summary.

- [ ] **Step 3: Commit**

```bash
git add spikes/spike-01-cfg-sufficiency/RESULTS.md spikes/README.md
git commit -m "spike-01: record CFG-sufficiency verdict"
```

---

## Self-Review

**Spec coverage:** PLAN-001 §4.4's pass criterion has three clauses — (1) extraction complete on ≥20kLOC vendor code: Tasks 1+3 (fixture size check in Task 3 Step 2, recorded in Task 4). (2) no construct requiring a CFG: Task 2's indirect-call classification is precisely the test for this — an indirect call is the one class of construct that AST-only extraction cannot resolve, and the plan requires it to be *reported*, not silently mishandled. (3) if a CFG is needed, flag ADR-001 §2.4 — Task 4 Step 1 wires the verdict to that exact recommendation. All three covered.

**Placeholder scan:** No TBD/TODO markers; every code block is complete and runnable. The one intentionally open-ended step (Task 4 Step 1) is open-ended because its content is empirical, not because it's undecided — the plan states exactly what data must appear and how to compute the verdict from it.

**Type consistency:** `ExtractionResult`, `FunctionInfo`, `TypeInfo`, `GlobalInfo`, `IndirectCallInfo` are defined once in Task 2 Step 5 and used identically by `run_spike.py` in Task 3 — field names match (`.functions`, `.types`, `.globals`, `.direct_calls`, `.indirect_calls`, `.diagnostics`; `IndirectCallInfo.caller/.expr_text/.declared_fn_ptr_type/.line`).

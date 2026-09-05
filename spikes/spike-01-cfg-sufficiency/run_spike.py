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

    # DEVIATION FROM THE PLAN (documented in RESULTS.md): the plan's original
    # run_spike.py summed len(result.X) per file directly. Measured against
    # the real fixture, that massively over-counts: CMSIS/HAL .c files share
    # huge common headers (stm32f4xx_hal.h alone pulls in ~40 per-peripheral
    # headers once every enabled HAL module is turned on), so the same
    # header-declared function/type/global is re-extracted once per .c file
    # that transitively includes it — e.g. stm32f4xx_hal.c's own TU has 1858
    # top-level cursors, of which only 30 are actually declared in
    # stm32f4xx_hal.c itself; the rest come from included headers. Summing
    # raw per-TU counts across 94 files inflated "functions" from a genuine
    # ~1.4k to ~20k. The fix is project-wide deduplication by declaration
    # identity (file, line, name) — the standard clang-tooling pattern of
    # per-TU indexing followed by a project-wide merge — so a header-defined
    # type or `static inline` function is counted exactly once no matter how
    # many translation units include it. Both raw and deduplicated totals are
    # kept below so the multiplier itself is visible as a finding.
    totals_raw = dict(functions=0, types=0, globals=0, direct_calls=0, indirect_calls=0)
    totals = dict(functions=0, types=0, globals=0, direct_calls=0, indirect_calls=0, files_with_errors=0)
    seen_functions = set()   # (file, line, name)
    seen_types = set()       # (file, name, kind) -- TypeInfo carries no line
    seen_globals = set()     # (file, line, name)
    seen_direct_calls = set()    # (caller_file, caller_line, caller, callee)
    seen_indirect_calls = set()  # (file, line, caller, expr_text)

    all_indirect = []
    files_with_errors_detail = []
    total_lines = 0

    for path in files:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            total_lines += sum(1 for _ in f)
        args = parse_args_for(path, FIXTURE_ROOT)
        tu = index.parse(path, args=args)
        result = extract_translation_unit(tu)

        totals_raw["functions"] += len(result.functions)
        totals_raw["types"] += len(result.types)
        totals_raw["globals"] += len(result.globals)
        totals_raw["direct_calls"] += len(result.direct_calls)
        totals_raw["indirect_calls"] += len(result.indirect_calls)

        # caller name -> (file, line) for THIS TU only, used to recover a
        # location for direct_calls (which carry caller/callee names only,
        # no location — see extract.py's ExtractionResult). Safe within one
        # TU: C forbids two definitions with the same name in one TU.
        caller_location = {fn.name: (fn.file, fn.line) for fn in result.functions}

        for fn in result.functions:
            key = (fn.file, fn.line, fn.name)
            if key in seen_functions:
                continue
            seen_functions.add(key)
            totals["functions"] += 1

        for t in result.types:
            key = (t.file, t.name, t.kind)
            if key in seen_types:
                continue
            seen_types.add(key)
            totals["types"] += 1

        for g in result.globals:
            key = (g.file, g.line, g.name)
            if key in seen_globals:
                continue
            seen_globals.add(key)
            totals["globals"] += 1

        for caller, callee in result.direct_calls:
            loc = caller_location.get(caller, ("<unknown>", -1))
            key = (loc[0], loc[1], caller, callee)
            if key in seen_direct_calls:
                continue
            seen_direct_calls.add(key)
            totals["direct_calls"] += 1

        for c in result.indirect_calls:
            key = (c.file, c.line, c.caller, c.expr_text)
            if key in seen_indirect_calls:
                continue
            seen_indirect_calls.add(key)
            totals["indirect_calls"] += 1
            all_indirect.append({
                "file": os.path.basename(c.file) if c.file != "<unknown>" else os.path.basename(path),
                "caller": c.caller, "expr": c.expr_text,
                "type": c.declared_fn_ptr_type, "line": c.line,
            })

        if result.diagnostics:
            totals["files_with_errors"] += 1
            files_with_errors_detail.append({
                "file": os.path.basename(path),
                "diagnostics": result.diagnostics[:5],
                "functions_extracted_this_tu": len(result.functions),
            })

    report = {
        "files_parsed": len(files),
        "approx_total_lines": total_lines,
        "totals_raw_per_tu_summed": totals_raw,
        "totals": totals,
        "indirect_calls_sample": all_indirect[:25],
        "indirect_calls_total": len(all_indirect),
        "files_with_errors_detail": files_with_errors_detail[:10],
    }
    with open(os.path.join(os.path.dirname(__file__), "report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

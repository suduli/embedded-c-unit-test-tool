# Spike 01 — CFG Sufficiency Spike

## Pass criterion (verbatim, PLAN-001 §4.4)

> Function, type, global and call-graph extraction complete on a ≥20 kLOC
> embedded project with vendor headers, with no construct requiring a CFG.
> If a CFG is needed, §2.4 of ADR-001 fails and the C++ analyzer moves from
> "later" to "now".

## What this spike tests

`extract.py` walks a translation unit's AST via `libclang`'s Python
bindings (`clang.cindex`) and extracts functions, types, globals, and a
call graph — classifying every call as either directly resolved to a
`FUNCTION_DECL`, or "indirect" when it's a call through a function-pointer
expression that AST-only analysis can't resolve to a concrete callee.
`run_spike.py` runs this over a real fixture and deduplicates the results
project-wide (see `RESULTS.md`'s "Deviations" for why that step turned out
to be necessary). The count and nature of indirect calls is the spike's
central finding: it is the specific class of construct that would argue
for CFG-level analysis, if anything did.

## Fixture

`fetch_fixture.sh` sparse-checks-out real vendor embedded C from
`STMicroelectronics/STM32CubeF4` (BSD-3-Clause) — the STM32F4 HAL driver
plus CMSIS device/core headers — into a gitignored `fixture/` directory.
Not vendored into this repository.

## How to reproduce

```bash
# From spikes/spike-01-cfg-sufficiency/
python -m venv .venv
source .venv/Scripts/activate   # or .venv/bin/activate on Linux/macOS
pip install -r requirements.txt

./fetch_fixture.sh

pytest tests/ -v          # unit tests against small inline C snippets
python run_spike.py       # runs extraction over the real fixture, writes report.json
```

`freestanding_stubs/` contains minimal `<stdint.h>`/`<stddef.h>` stubs
needed because `-target thumbv7em-none-eabi` selects a bare-metal target
with no bundled C library — see `RESULTS.md`'s "Deviations" section.

Results (extraction totals, the indirect-call sample, and the verdict) are
recorded in [`RESULTS.md`](RESULTS.md).

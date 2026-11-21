"""Generate the 2026-11-21 overnight queues (integration and follow-up work). Regenerate, do not edit outputs."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("prev", HERE.parent / "overnight-20261119" / "build_overnight_plan.py")
prev = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
sys.modules["prev"] = prev
spec.loader.exec_module(prev)  # type: ignore[union-attr]

BASE = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=HERE).stdout.strip()
D02 = prev.D02

# key -> (title, goal, allowed paths, est k)
ITEMS = {
    "A1": ("Wire the build step: record compiled suites and load link plans",
        "Two integrations in src/ectt/bld: (1) call ectt.cbt record_compiled_suite from the build step and store the record in the project layout (SDD-003), and let reexecute_suite be used by the run_parallel/run_isolated callers in ectt.exh; (2) call ectt.ing.linkplan.load_link_plan from the harness-build step so a refused plan stops the build with its named reason. Stable ids plus content digests apply: " + D02 + " Tests: build with valid plan, refused plan stops build, re-execution without regeneration reuses the record, changed source invalidates it.",
        ["src/ectt/bld/", "tests/bld/", "src/ectt/cbt/", "tests/cbt/", "src/ectt/ing/", "tests/ing/", "src/ectt/exh/", "tests/exh/"], 180),
    "A2": ("Harness generator: stub setup and expectations, result stream, state reset",
        "From the second-pass lists of 11-20: wire render_stub_setup and render_stub_expectations into the harness generator and the result stream; make the framework back-end templates emit ectt_begin_test, ectt_end_test and ectt_fail; register ectt_stub_reset_all as a state reset. There is no C compiler on this machine, so verify by parsing the generated C (a C front end such as libclang) and by string-level golden tests; say so in the ledger. Tests: generated C parses without errors, output is byte-identical across two runs, a template with no stubs is unchanged.",
        ["src/ectt/gen/", "tests/gen/"], 200),
    "A3": ("Nested expected values: inputs, globals and struct return",
        "Extend nested path keys to inputs.globals (initial nested values) and to a struct return value (expected.return is a single string today). Keep older files valid and byte-stable. Tests: round trip, nested mismatch reported with its path, unknown member refused, old flat file unchanged.",
        ["src/ectt/tcm/", "tests/tcm/"], 130),
    "A4": ("Host profile and parity wiring",
        "Implement TOOL-TGT-130: a versioned host profile recording the target-to-host derivation and ABI differences, with unmeasured differences explicitly 'unknown'; label every host-executed result with its profile; wire check_parity into run preparation; allow two result sets (host and target) to be passed to compare_outcomes. Do not run anything on hardware. Tests: profile is deterministic, unknown stays unknown, label present on results, parity check blocks a run with a named reason.",
        ["src/ectt/ext/", "tests/ext/"], 160),
    "A5": ("Generation run: connect the validation port and report marks",
        "Bind the generation run (ectt.atg) to a validation port that builds through ectt.bld and runs through ectt.exh using fakes in tests (no C compiler is available), so CoverageDelta.newly_covered is populated when the port reports coverage. Tests only use the fake port; say so in the ledger. Do not edit ectt.rep: list the renderer change needed in the second-pass file.",
        ["src/ectt/atg/", "tests/atg/"], 150),
    "A6": ("Mutation-style tests for gen, cbt and exh",
        "Tests only. For src/ectt/gen, src/ectt/cbt and src/ectt/exh, hand-write mutants (flip a comparison, drop a branch, swap an order) in a temp copy, confirm existing tests kill each, add tests for survivors. Write the kill rate to docs/glm-night/overnight-20261121/mutation-gen-cbt-exh.md. No src/ edits.",
        ["tests/gen/", "tests/cbt/", "tests/exh/", "docs/glm-night/overnight-20261121/"], 150),
    "A7": ("Seeded property-style tests for gen and atg",
        "Tests only. Fixed-seed random inputs for harness rendering (identifiers, escaping, long names), stub value rendering (no injection into generated C) and generation-run limits. No wall clock. No src/ edits.",
        ["tests/gen/", "tests/atg/"], 130),
    "B1": ("Analysis model schema bump: function extent, all unsupported occurrences, global types",
        "One additive schema bump (next minor after the current one; add the new schema file, keep every older reader rule working): (1) add start and end line to FunctionModel; (2) record every occurrence (owner function and location) of an unsupported construct, not only the first; (3) record global variable types and initial-value presence so a harness can reach file-static data. Update the version constant and tests. Then use (2) in src/ectt/ana/eligibility.py so each owner is named. Tests: old files still load, new fields validate, two runs byte-identical.",
        ["src/ectt/ana/", "tests/ana/"], 200),
    "B2": ("Exact range links for requirements using function extent",
        "After B1: make source-element links in ectt.trc resolve range links exactly using the new function extent, and keep approximate behaviour only for models without it. Tests: exact hit, boundary lines, model without extent still works.",
        ["src/ectt/trc/", "tests/trc/"], 110),
    "B3": ("Re-entrant safe-write transaction",
        "Make OutputRoot.transaction in src/ectt/core/fs.py re-entrant (nested scopes join the outer one), then remove the private-attribute check in src/ectt/ana/persist.py that reads output_root._journal. Keep public names and error messages. Tests: nested commit, nested failure rolls back everything, cancellation inside nested scope.",
        ["src/ectt/core/", "tests/core/", "src/ectt/ana/persist.py", "tests/ana/"], 100),
    "B4": ("Report renderers show machine-generated and unreviewed marks",
        "Call report_marks and format_mark (from ectt.atg) in the ectt.rep renderers so reports show machine-generated and unreviewed marks. Import only the narrow function; do not make rep depend on the rest of atg. Tests: marked case shows mark, unmarked case unchanged, ordering deterministic.",
        ["src/ectt/rep/", "tests/rep/"], 120),
    "B5": ("Publish the interchange format reference",
        "Write the output of render_format_reference() to docs/reference/interchange-format.md (generated by a small script in the same folder, with a test that the file matches the generator), and fix docs/verification/WP-MIG-01-analysis.md for the cmocka OK spelling. Allowed to create docs/reference/ only.",
        ["src/ectt/mig/", "tests/mig/", "docs/reference/", "docs/verification/WP-MIG-01-analysis.md"], 70),
    "B6": ("Project.save integration of the sharded store",
        "Finish WP-PRJ-02: make Project.save able to write the sharded layout from ectt.prj.shards while the single-file manifest stays the default. Choose layout by an explicit argument only; no automatic switch. Tests: both layouts round-trip, unchanged save is byte-stable, interrupted save leaves the original.",
        ["src/ectt/prj/", "tests/prj/"], 150),
    "B7": ("Re-import SPEC-RELATIONS from ReqIF as associations",
        "In ectt.trc, make import_reqif read SPEC-RELATIONS back as requirement-to-test associations, so export then import is lossless. Tests: round trip, dangling relation refused with a named reason, duplicate relation merged once.",
        ["src/ectt/trc/", "tests/trc/"], 100),
    "B8": ("Mutation-style tests for core, prj and mig",
        "Tests only. For src/ectt/core, src/ectt/prj and src/ectt/mig, hand-written mutants in a temp copy, confirm kills, add tests for survivors; kill rate in docs/glm-night/overnight-20261121/mutation-core-prj-mig.md. No src/ edits.",
        ["tests/core/", "tests/prj/", "tests/mig/", "docs/glm-night/overnight-20261121/"], 150),
    "B9": ("Seeded property-style tests for trc and rep",
        "Tests only. Fixed-seed random inputs for the traceability matrix, ReqIF export and import round trip, and report merge. No wall clock. No src/ edits.",
        ["tests/trc/", "tests/rep/"], 130),
}
LANE_A = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
LANE_B = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"]


def block(n, lane, key):
    title, goal, allowed, est = ITEMS[key]
    ledger = f"docs/glm-night/overnight-20261121/LANE_{lane}_LEDGER.md"
    sp = f"docs/glm-night/overnight-20261121/SECOND_PASS_{lane}.md"
    paths = ", ".join(f"`{p}`" for p in allowed + [ledger, sp])
    return "\n".join([
        f"### {n}. {key}: {title}", "",
        f"- Estimate {est}k tokens, hard cap {int(est * 1.3)}k, or 3 failed gate attempts, then PARTIAL and move on.",
        f"- Goal: {goal}",
        f"- Allowed paths: {paths}. Anything else: do not edit; write the needed change in the second-pass file.",
        "- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.", ""])


def main():
    pk = {"A": set(), "B": set()}
    for lane, keys in (("A", LANE_A), ("B", LANE_B)):
        for k in keys:
            for p in ITEMS[k][2]:
                if p.startswith("src/ectt/"):
                    pk[lane].add(p.split("/")[2].removesuffix(".py"))
    if pk["A"] & pk["B"]:
        sys.exit(f"overlap {pk['A'] & pk['B']}")
    for lane, keys in (("A", LANE_A), ("B", LANE_B)):
        text = prev.PREAMBLE.format(
            lane=lane, lc=lane.lower(),
            ledger=f"docs/glm-night/overnight-20261121/LANE_{lane}_LEDGER.md",
            sp=f"docs/glm-night/overnight-20261121/SECOND_PASS_{lane}.md")
        text = text.replace("20261119", "20261121").replace("glm-night/20261121-plan", "main")
        text = text.replace("Baseline at the branch point (local `main` 353b9b4): 970 passed, 4 skipped;",
                            f"Baseline at the branch point (local `main` {BASE}): 3097 passed, 6 skipped;")
        text = text.replace(f"wt-night-{lane.lower()}", f"wt-night-21{lane.lower()}")
        text = text.replace("Item N00 is the only exception for `design/`.", "No item may edit `design/`.")
        text = text.replace(
            "Stop starting new items when your lane's cumulative reaches 1,450k tokens OR the local time reaches 05:30, whichever comes first.",
            "Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first.")
        text = text.replace("Open: ADR-003", "No C compiler is installed on this machine: generated C is checked by parsing only. Open: ADR-003")
        total = sum(ITEMS[k][3] for k in keys)
        parts = [block(i, lane, k) for i, k in enumerate(keys, 1)]
        (HERE / f"LANE_{lane}_queue.md").write_text(
            text + "\n".join(parts) + f"\n## End\nListed total {total}k tokens.\n", encoding="utf-8")
        print(lane, total, len(keys))


if __name__ == "__main__":
    main()

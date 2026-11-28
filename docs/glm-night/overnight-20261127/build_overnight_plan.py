"""Generate the 2026-11-27 queues (MC/DC wave with a real GCC 14 container). Regenerate, do not edit outputs."""
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

DAY = "20261127"
BASE = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=HERE).stdout.strip()
PASSED = "4064 passed, 6 skipped"

OWNER = ("Owner answers (2026-11-27), quoted: MC/DC is 'Masking + document gap'; a GCC older than 14 is 'Say not "
         "available' (run the other coverage, show MC/DC as unmeasured with the reason, and a configured MC/DC minimum "
         "fails); 'GCC only' (no Clang MC/DC). Compiler: 'Docker gcc:14'.")
DOCKER = ("A real GCC 14.4.0 is available ONLY as the local Docker image `gcc:14`: "
          "`MSYS_NO_PATHCONV=1 docker run --rm --network none -v <absolute temp dir>:/w gcc:14 sh -c '...'`. Never pull "
          "images, never install a compiler, never mount anything but a temp directory holding copies. If Docker is not "
          "running, say so in the ledger and work from the committed fixtures. The test suite must not need Docker: "
          "commit captured output as fixtures, with the commands used.")
DOC = " Write the analysis note to docs/verification/{wp}-analysis.md in the same style as the existing notes there."
DONE_ALREADY = ("Already on main, build on it and do not rebuild: analysis model schema 1.6 `AnalysisUnit.decisions` "
                "(ectt.ana, each condition has `constant` and `negated`); `ectt.tch.plan_mcdc` and "
                "`probe_condition_limit`; `ectt.cov.measure_mcdc` returning `McdcResult` (decisions, unmeasured "
                "with reasons). Read docs/verification/WP-COV-05-analysis.md first.")
REAL = (" Real output samples are in tests/cov/fixtures/gcc14/ (see its README): in a condition record `count` is two "
        "outcomes per condition; 64 conditions are measured, 65 give no records. `seen_true` / `seen_false` mean the "
        "condition was SHOWN TO DECIDE the outcome with that value; False never means it never had that value; None "
        "means the direction is unknown. GCC reports conditions under `!` inverted (already undone in ectt.cov).")

# key -> (title, goal, allowed paths, est k)
ITEMS = {
    "A2": ("Apply the MC/DC flags in the build and CLI, and map coverage file names",
        "The core is done but nothing applies it. When MC/DC is requested, the harness build and the CLI run path must "
        "use `plan_mcdc`: add its compile flags and gcov flags, pass the probed limit on, and when it is not available "
        "run the other coverage and carry the reason into the result. Add a function that maps an analysis-model unit "
        "path to the gcov `file` name (absolute, relative and basename-collision cases; ambiguous is refused, never "
        "guessed). Check one full run with Docker. Tests: flags present and absent, GCC 13, mapping cases.",
        ["src/ectt/bld/", "src/ectt/cli/", "src/ectt/tch/", "tests/bld/", "tests/cli/", "tests/tch/"], 170),
    "A3": ("Compile the generated harnesses and stubs with a real compiler",
        "Generated C has only ever been parsed. Generate harnesses and stubs for a few representative units (scalars, "
        "structs, arrays, file statics, function pointers, GoogleTest excluded), compile, link and run them with Docker "
        "gcc:14 using -Wall -Wextra -Werror, and fix the generator bugs this exposes. Add golden-text tests for each fix "
        "and record the compile commands and results in the analysis note. Unity or cmocka sources that are not in the "
        "repository must not be downloaded: use a minimal local stand-in header for compile checks and say so." +
        DOC.format(wp="WP-GEN-compile-check"),
        ["src/ectt/gen/", "tests/gen/", "docs/verification/WP-GEN-compile-check-analysis.md"], 220),
    "A4": ("Export bindings left over from earlier runs",
        "docs/glm-night/overnight-20261123/SECOND_PASS_B.md lists missing public exports in ectt.ana, ectt.ing and "
        "ectt.tcm. Add them and a public-surface guard test per package. No behaviour change.",
        ["src/ectt/ing/", "src/ectt/tcm/", "src/ectt/ana/", "tests/ing/", "tests/tcm/", "tests/ana/"], 70),
    "A5": ("Mutation and seeded tests for decision extraction and the MC/DC gate",
        "Tests only. Hand-written mutants in a temp copy of the new ana, tch and bld code; add tests for survivors; "
        "seeded random boolean expressions: extracted condition count and order match the generator. Report to "
        "docs/glm-night/overnight-20261127/mutation-ana-tch-bld.md. No src/ edits.",
        ["tests/ana/", "tests/tch/", "tests/bld/", "docs/glm-night/overnight-20261127/"], 140),
    "B2": ("WP-COV-05: finish the known-answer MC/DC corpus",
        "TOOL-COV-210: a corpus of small C cases with HAND-COMPUTED expected results (a&&b independence matrix, nested, "
        "repeated and coupled operands, side-effecting operand not evaluated, macro condition, constant decision, a "
        "masking versus unique-cause divergent case with the difference written down). Write the expected values before "
        "running; then capture real gcov output with Docker and compare through `measure_mcdc`. A disagreement is a "
        "finding: explain it, never edit the expectation just to match. Also run the cases at -O2 and report any "
        "difference in condition direction or record placement (only -O0 has been checked)." + REAL,
        ["tests/cov/"], 160),
    "B4": ("MC/DC thresholds and project configuration",
        "Add an 'mcdc' metric to coverage thresholds and the project thresholds section. A configured MC/DC minimum "
        "FAILS when MC/DC is unavailable or unmeasured, unless the project explicitly allows not-applicable. Existing "
        "files without it keep working.",
        ["src/ectt/cov/", "src/ectt/prj/", "tests/cov/", "tests/prj/"], 120),
    "B5": ("WP-REP-04 and WP-COV-10: MC/DC report detail and the documented gap",
        "In ectt.rep render per-decision condition detail from `McdcResult` in the HTML report (TOOL-REP-050); never "
        "word a False as 'was never true' (say 'not shown'), show None as 'unknown'; state form and mechanism "
        "in every report that carries coverage (TOOL-COV-060). Write docs/user/mcdc.md (DRAFT) stating precisely how "
        "masking MC/DC differs from unique-cause, with the corpus case that shows it (TOOL-COV-090). Do not claim any "
        "certification authority accepts masking MC/DC: that is unchecked. Update the certification report's not-claimed "
        "list so MC/DC is claimed only when measured data is present, and never unique-cause." + REAL + DOC.format(wp="WP-REP-04"),
        ["src/ectt/rep/", "tests/rep/", "docs/user/", "docs/verification/WP-REP-04-analysis.md"], 220),
    "B6": ("End-to-end coverage check on real GCC output",
        "With Docker, build several small programs with coverage, run them one or more times, and check the reader, "
        "merge, metrics and thresholds against hand-counted statement and branch results (headers included from two "
        "files, templates not needed, a crashed run excluded). Commit the captured output as fixtures; fix bugs in "
        "ectt.cov. Also fix the three report observations in the 11-23 SECOND_PASS_B only if they are in ectt.rep.",
        ["src/ectt/cov/", "src/ectt/rep/", "tests/cov/", "tests/rep/"], 160),
    "B7": ("Mutation and seeded tests for the MC/DC code",
        "Tests only. Hand-written mutants in a temp copy of the new cov and rep code; add tests for survivors; seeded "
        "random condition records: merge is order independent and never raises covered above count. Report to "
        "docs/glm-night/overnight-20261127/mutation-mcdc.md. No src/ edits.",
        ["tests/cov/", "tests/rep/", "docs/glm-night/overnight-20261127/"], 130),
}
LANE_A = ["A2", "A3", "A4", "A5"]
LANE_B = ["B2", "B6", "B4", "B5", "B7"]
def block(n, lane, key):
    title, goal, allowed, est = ITEMS[key]
    ledger = f"docs/glm-night/overnight-{DAY}/LANE_{lane}_LEDGER.md"
    sp = f"docs/glm-night/overnight-{DAY}/SECOND_PASS_{lane}.md"
    paths = ", ".join(f"`{p}`" for p in allowed + [ledger, sp])
    lines = [f"### {n}. {key}: {title}", "",
             f"- Estimate {est}k tokens, hard cap {int(est * 1.3)}k, or 3 failed gate attempts, then PARTIAL and move on.",
             f"- Goal: {goal}"]
    lines += [f"- Allowed paths: {paths}. Anything else: do not edit; write the needed change in the second-pass file.",
              "- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.", ""]
    return "\n".join(lines)


def swap(text, old, new):
    if old not in text:
        sys.exit(f"preamble text not found: {old[:60]}")
    return text.replace(old, new)


def main():
    pk = {"A": set(), "B": set()}
    for lane, keys in (("A", LANE_A), ("B", LANE_B)):
        for k in keys:
            pk[lane].update(p.split("/")[2] for p in ITEMS[k][2] if p.startswith("src/ectt/"))
    if pk["A"] & pk["B"]:
        sys.exit(f"overlap {pk['A'] & pk['B']}")
    for lane, keys in (("A", LANE_A), ("B", LANE_B)):
        text = prev.PREAMBLE.format(
            lane=lane, lc=lane.lower(),
            ledger=f"docs/glm-night/overnight-{DAY}/LANE_{lane}_LEDGER.md",
            sp=f"docs/glm-night/overnight-{DAY}/SECOND_PASS_{lane}.md")
        text = text.replace("20261119", DAY).replace(f"glm-night/{DAY}-plan", "main")
        text = text.replace(f"wt-night-{lane.lower()}", f"wt-night-27{lane.lower()}")
        text = swap(text, "Baseline at the branch point (local `main` 353b9b4): 970 passed, 4 skipped;",
                    f"Baseline at the branch point (local `main` {BASE}): {PASSED};")
        text = swap(text, "Item N00 is the only exception for `design/`.", "No item may edit `design/`.")
        text = swap(text,
                    "Stop starting new items when your lane's cumulative reaches 1,450k tokens OR the local time reaches 05:30, whichever comes first.",
                    "Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first.")
        text = swap(text, "Open: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9, PR #4.",
                    f"{OWNER} {DOCKER} {DONE_ALREADY} Open: ADR-007, SRS-Q9, the ADR-005 record location, PR #4. Before using "
                    "`xfail`, run the test without it and confirm it fails for the stated reason.")
        total = sum(ITEMS[k][3] for k in keys)
        parts = [block(i, lane, k) for i, k in enumerate(keys, 1)]
        (HERE / f"LANE_{lane}_queue.md").write_text(
            text + "\n".join(parts) + f"\n## End\nListed total {total}k tokens.\n", encoding="utf-8")
        print(lane, total, len(keys))


if __name__ == "__main__":
    main()

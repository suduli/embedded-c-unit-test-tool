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
PASSED = "4026 passed, 6 skipped"

OWNER = ("Owner answers (2026-11-27), quoted: MC/DC is 'Masking + document gap'; a GCC older than 14 is 'Say not "
         "available' (run the other coverage, show MC/DC as unmeasured with the reason, and a configured MC/DC minimum "
         "fails); 'GCC only' (no Clang MC/DC). Compiler: 'Docker gcc:14'.")
DOCKER = ("A real GCC 14.4.0 is available ONLY as the local Docker image `gcc:14`: "
          "`MSYS_NO_PATHCONV=1 docker run --rm --network none -v <absolute temp dir>:/w gcc:14 sh -c '...'`. Never pull "
          "images, never install a compiler, never mount anything but a temp directory holding copies. If Docker is not "
          "running, say so in the ledger and work from the committed fixtures. The test suite must not need Docker: "
          "commit captured output as fixtures, with the commands used.")
DOC = " Write the analysis note to docs/verification/{wp}-analysis.md in the same style as the existing notes there."
REAL = (" Real output samples are in tests/cov/fixtures/gcc14/ (see its README): in a condition record `count` is two "
        "outcomes per condition, `not_covered_true` / `not_covered_false` are condition indexes; 64 conditions are "
        "measured, 65 give a warning and no records.")

# key -> (title, goal, allowed paths, est k)
ITEMS = {
    "A1": ("Decision and condition extraction in the analysis model (schema 1.6)",
        "The model's decision inventory is hard-coded 'not_extracted'. Extract every boolean decision with its "
        "conditions in source order (file, line, column, expression text, owning function, macro-expansion flag) into "
        "decisions[], set status complete or partial honestly, bump the schema to 1.6 with a new schema file, and update "
        "every consumer that pins the version (search for 1.5; ectt.mig has a FormatSpec). Check on real source that "
        "GCC's condition order matches yours using Docker, on tests/cov/fixtures/gcc14/mcdc.c. Tests: a&&b, nested, "
        "repeated operand, macro condition, constant, ternary, loop conditions, older 1.5 documents still read." +
        DOC.format(wp="WP-ANA-08-decisions"),
        ["src/ectt/ana/", "src/ectt/mig/", "tests/ana/", "tests/mig/", "docs/verification/WP-ANA-08-decisions-analysis.md"], 220),
    "A2": ("MC/DC capability, version gate and build flags",
        "In ectt.tch declare condition coverage as available for GCC 14 or newer only, with the probed maximum of 64 "
        "conditions recorded as run evidence (TOOL-COV-190: probed, not taken from documentation; give a probe function "
        "with an injected runner, and capture the real probe with Docker as a fixture). In ectt.bld add "
        "-fcondition-coverage to compile flags and --conditions to gcov only when MC/DC is requested and available. "
        "Older GCC: build the other coverage and return a named 'mcdc_not_available' reason. Tests: GCC 13 vs 14, "
        "flags present and absent, probe result recorded, probe failure is 'unknown', never a guessed number.",
        ["src/ectt/tch/", "src/ectt/bld/", "tests/tch/", "tests/bld/"], 170),
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
    "B1": ("WP-COV-05: MC/DC measurement and form declaration",
        "In ectt.cov turn gcov condition records into MC/DC results: per decision the conditions not exercised true and "
        "not exercised false (TOOL-COV-070), totals, and on every result the form 'masking' and the mechanism 'GCC "
        "-fcondition-coverage' with the compiler version (TOOL-COV-060). No condition data is 'unmeasured' with a named "
        "reason, never zero and never covered. Merge across runs must be correct for conditions (TOOL-COV-110). "
        "Condition expression text is optional (it comes from lane A item A1): show index and line without it." + REAL +
        DOC.format(wp="WP-COV-05"),
        ["src/ectt/cov/", "tests/cov/", "docs/verification/WP-COV-05-analysis.md"], 220),
    "B2": ("WP-COV-05: known-answer MC/DC corpus",
        "TOOL-COV-210: a corpus of small C cases with HAND-COMPUTED expected results (a&&b independence matrix, nested, "
        "repeated and coupled operands, side-effecting operand not evaluated, macro condition, constant decision, a "
        "masking versus unique-cause divergent case with the difference written down). Write the expected values before "
        "running; then capture real gcov output with Docker and compare. A disagreement is a finding: explain it, never "
        "edit the expectation just to match." + REAL,
        ["tests/cov/"], 160),
    "B3": ("WP-COV-06: uninstrumentable decisions and the condition limit",
        "Report decisions GCC could not instrument, including those over the recorded maximum (64): unmeasured with the "
        "limit in the reason (TOOL-COV-080, TOOL-COV-190). Use the decision list from analysis model 1.6 to find "
        "decisions that have no condition records. The limit is an input from run evidence, not a constant in cov. "
        "Read ectt.ana only." + REAL + DOC.format(wp="WP-COV-06"),
        ["src/ectt/cov/", "tests/cov/", "docs/verification/WP-COV-06-analysis.md"], 180),
    "B4": ("MC/DC thresholds and project configuration",
        "Add an 'mcdc' metric to coverage thresholds and the project thresholds section. A configured MC/DC minimum "
        "FAILS when MC/DC is unavailable or unmeasured, unless the project explicitly allows not-applicable. Existing "
        "files without it keep working.",
        ["src/ectt/cov/", "src/ectt/prj/", "tests/cov/", "tests/prj/"], 120),
    "B5": ("WP-REP-04 and WP-COV-10: MC/DC report detail and the documented gap",
        "In ectt.rep render per-decision condition detail in the HTML report (TOOL-REP-050) and state form and mechanism "
        "in every report that carries coverage (TOOL-COV-060). Write docs/user/mcdc.md (DRAFT) stating precisely how "
        "masking MC/DC differs from unique-cause, with the corpus case that shows it (TOOL-COV-090). Do not claim any "
        "certification authority accepts masking MC/DC: that is unchecked. Update the certification report's not-claimed "
        "list so MC/DC is claimed only when measured data is present, and never unique-cause." + DOC.format(wp="WP-REP-04"),
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
LANE_A = ["A1", "A2", "A3", "A4", "A5"]
LANE_B = ["B1", "B2", "B6", "B4", "B3", "B5", "B7"]
CROSS = ("- CROSS-LANE DEPENDENCY on item `A1` (lane A, worktree `../wt-night-27a`). Before starting: look at "
         "`docs/glm-night/overnight-20261127/LANE_A_LEDGER.md` there for an A1 row that is DONE. If so: "
         "`git merge --no-edit glm-night/20261127-a`, run the full gate; if red, `git revert -m 1 HEAD` and treat as "
         "not satisfied. If not satisfied: skip it now, retry once after the last item, then record `SKIPPED (dep)` "
         "in the ledger and the second-pass file.")


def block(n, lane, key):
    title, goal, allowed, est = ITEMS[key]
    ledger = f"docs/glm-night/overnight-{DAY}/LANE_{lane}_LEDGER.md"
    sp = f"docs/glm-night/overnight-{DAY}/SECOND_PASS_{lane}.md"
    paths = ", ".join(f"`{p}`" for p in allowed + [ledger, sp])
    lines = [f"### {n}. {key}: {title}", "",
             f"- Estimate {est}k tokens, hard cap {int(est * 1.3)}k, or 3 failed gate attempts, then PARTIAL and move on.",
             f"- Goal: {goal}"]
    if key == "B3":
        lines.append(CROSS)
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
                    f"{OWNER} {DOCKER} Open: ADR-007, SRS-Q9, the ADR-005 record location, PR #4. Before using "
                    "`xfail`, run the test without it and confirm it fails for the stated reason.")
        total = sum(ITEMS[k][3] for k in keys)
        parts = [block(i, lane, k) for i, k in enumerate(keys, 1)]
        (HERE / f"LANE_{lane}_queue.md").write_text(
            text + "\n".join(parts) + f"\n## End\nListed total {total}k tokens.\n", encoding="utf-8")
        print(lane, total, len(keys))


if __name__ == "__main__":
    main()

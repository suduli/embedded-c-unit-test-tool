"""Generate the 2026-11-22 queues (wiring wave: CLI, report views, drafts, tests). Regenerate, do not edit outputs."""
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
NOCC = ("There is no C compiler on this machine: check generated C by parsing and golden text only, and say so in "
        "the ledger.")

# key -> (title, goal, allowed paths, est k)
ITEMS = {
    "A1": ("Production composition point for the generation run",
        "Create src/ectt/cli/compose.py: one function that binds ectt.atg BoundValidationPort's build and execute "
        "delegates to ectt.bld.build_harness_suite and ectt.cbt.reexecute_isolated (atg must not import them itself: "
        "layer rule DSN-ATG-110). Tests with fake build and execute callables: binding order, a build refusal stops the "
        "run with its named reason, a refused link plan stops the run. No real compiler is used.",
        ["src/ectt/cli/", "tests/cli/"], 130),
    "A2": ("Harness generation: reach file-static data and emit externs",
        "Finish the WP-GEN-01 remainder (HAR-040). The analysis model (schema 1.5) now records global variable types "
        "and initial-value presence. Use it so the generated harness can read and set file-static variables and emits "
        "extern declarations where the variable is visible. Read the model only; do not edit ectt.ana. " + NOCC +
        " Tests: golden C text for scalar, struct and array globals; a global whose type is not recorded is reported as "
        "not reachable with a named reason, never guessed.",
        ["src/ectt/gen/", "tests/gen/"], 180),
    "A3": ("Map a source diff to the construct identities coverage data uses",
        "In ectt.cbt, add a function that takes a source change (old and new file digests plus changed line ranges) "
        "and returns the affected construct identities that ectt.cov data uses, so change impact can pick the right "
        "subset. Use the function extents recorded in analysis model 1.5. Tests: change inside one function, change "
        "between functions, whole-file change, model without extents (falls back to whole file with a named note).",
        ["src/ectt/cbt/", "tests/cbt/"], 140),
    "A4": ("CLI commands for impact, subset run, comparison and minimization",
        "Add four commands to the catalogue-generated CLI (ectt.cli): affected set and subset run (ectt.cbt.impact, "
        "reexecute_subset), compare two runs and their coverage (compare_runs, compare_coverage), and minimize a suite "
        "(minimize_suite). Each prints through the report views from lane B item B2 and uses the stable exit codes. "
        "Tests: each command happy path, a missing input gives the usage exit code, JSON output is byte-stable.",
        ["src/ectt/cli/", "tests/cli/"], 200),
    "A5": ("Host profile label and parity-gated run preparation in the CLI",
        "Wire the host profile (ectt.ext) into the CLI run preparation: check_parity runs first and a failure stops "
        "the run with its named reason; every host-executed result is labelled with its profile. Hardware is not "
        "available, so no target run. Tests: parity failure blocks, unknown ABI differences show as unknown, label on "
        "every result.",
        ["src/ectt/cli/", "tests/cli/", "src/ectt/ext/", "tests/ext/"], 140),
    "A6": ("Mutation-style tests for cli, atg and ext",
        "Tests only. Hand-written mutants (flip a comparison, drop a branch, swap an order) in a temp copy of "
        "src/ectt/cli, src/ectt/atg and src/ectt/ext; confirm existing tests kill each; add tests for survivors. Kill "
        "rate to docs/glm-night/overnight-20261122/mutation-cli-atg-ext.md. No src/ edits.",
        ["tests/cli/", "tests/atg/", "tests/ext/", "docs/glm-night/overnight-20261122/"], 140),
    "A7": ("Seeded property-style tests for bld, cbt and gen",
        "Tests only. Fixed-seed random inputs: build planning order independence, re-execution record round trip, "
        "impact sets under random changes, generated C identifier and escape safety. No wall clock. No src/ edits.",
        ["tests/bld/", "tests/cbt/", "tests/gen/"], 130),
    "B1": ("Make the coverage merge independent of input order",
        "Review finding: in src/ectt/cov/merge.py, _merge_documents takes data_file from the first admitted run in "
        "INPUT order, so the same runs merged in another order give a different aggregate. Make the merged provenance "
        "field order-independent (for example the sorted list of all data files). Counts must not change. Tests: all "
        "permutations of three runs give byte-identical merged output; a single run is unchanged.",
        ["src/ectt/cov/", "tests/cov/"], 80),
    "B2": ("Report views for re-execution results and thresholds",
        "In ectt.rep add report views for: a subset run (state that the suite was only partly run, from suite_view "
        "data), a run comparison with its coverage delta and removed tests, a minimized suite (kept versus redundant and "
        "the preserved union), the host profile label on results, and coverage threshold results including the new "
        "no_data state (shown as a failure). Import only the narrow data classes from ectt.cbt, ectt.ext and ectt.cov. "
        "Tests: each view, no_data shown as failed, output deterministic. Other lanes call these views, so keep the "
        "function names stable and list them in docs/verification/WP-REP-views-analysis.md.",
        ["src/ectt/rep/", "tests/rep/", "docs/verification/WP-REP-views-analysis.md"], 200),
    "B3": ("Coverage threshold configuration in the project store",
        "Let a project configure coverage thresholds (statements, branches) and the allow_not_applicable list, stored in "
        "the project data format as exact fractions, and loaded into ectt.cov.MetricThreshold. Do not change existing "
        "file formats: this is an optional new section, absent means no thresholds. Tests: round trip, a float is "
        "refused, an unknown metric is refused, absent section is no-op.",
        ["src/ectt/prj/", "tests/prj/"], 120),
    "B4": ("Draft the user documentation pages",
        "From the WP-CORE-07 documentation index (find it in src/ectt/core and docs/verification/WP-CORE-07-analysis.md) "
        "write the missing docs/user/ pages as DRAFTS. Mark each page DRAFT at the top. Describe only what exists in the "
        "code today (check each command or option exists); mark anything planned as 'not yet available'. Add a test "
        "that every page in the index exists and every command it names is real.",
        ["docs/user/", "src/ectt/core/", "tests/core/"], 220),
    "B5": ("Draft SECURITY.md",
        "From the WP-SEC-05 policy (src/ectt/sec and its verification note) write a DRAFT security disclosure policy "
        "at docs/proposals/SECURITY-draft.md, ready for the owner to copy to the repository root. Do not create "
        "SECURITY.md at the root. Do not invent contact addresses: use the placeholder OWNER-CONTACT-REQUIRED.",
        ["docs/proposals/SECURITY-draft.md", "tests/sec/"], 60),
    "B6": ("Coverage reader checks against more GCC cases",
        "Extend tests/cov with hand-written gcov JSON fixtures for cases real GCC produces: template and inline "
        "functions seen in several files, a file with only declarations, lines with unexecuted blocks, throw branches, "
        "version 1 and version 2 documents. Take key names from the GCC gcov documentation, not memory. Fix reader "
        "bugs these expose (src/ectt/cov only). Say in the ledger that real GCC output is still unchecked.",
        ["src/ectt/cov/", "tests/cov/"], 150),
    "B7": ("Mutation-style tests for cov and rep",
        "Tests only. Hand-written mutants in a temp copy of src/ectt/cov and src/ectt/rep; confirm kills; add tests for "
        "survivors. Kill rate to docs/glm-night/overnight-20261122/mutation-cov-rep.md. No src/ edits.",
        ["tests/cov/", "tests/rep/", "docs/glm-night/overnight-20261122/"], 150),
    "B8": ("Seeded property-style tests for cov thresholds and rep views",
        "Tests only. Fixed-seed random metric totals against thresholds (exact fractions, boundary values, no_data), "
        "and random run sets through the new rep views. No wall clock. No src/ edits.",
        ["tests/cov/", "tests/rep/"], 120),
}
LANE_A = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
LANE_B = ["B2", "B1", "B3", "B6", "B4", "B5", "B7", "B8"]
CROSS_A4 = ("- CROSS-LANE DEPENDENCY on item `B2` (lane B, worktree `../wt-night-22b`). Before starting: look at "
            "`docs/glm-night/overnight-20261122/LANE_B_LEDGER.md` there for a B2 row that is DONE. "
            "If so: `git merge --no-edit glm-night/20261122-b`, run the full gate; if red, `git revert -m 1 HEAD` and "
            "treat as not satisfied. If not satisfied: skip it now, retry once after the last item, then record "
            "`SKIPPED (dep)` in the ledger and the second-pass file.")


def block(n, lane, key):
    title, goal, allowed, est = ITEMS[key]
    ledger = f"docs/glm-night/overnight-20261122/LANE_{lane}_LEDGER.md"
    sp = f"docs/glm-night/overnight-20261122/SECOND_PASS_{lane}.md"
    paths = ", ".join(f"`{p}`" for p in allowed + [ledger, sp])
    lines = [f"### {n}. {key}: {title}", "",
             f"- Estimate {est}k tokens, hard cap {int(est * 1.3)}k, or 3 failed gate attempts, then PARTIAL and move on.",
             f"- Goal: {goal}"]
    if key in ("A4", "A5"):
        lines.append(CROSS_A4)
    lines += [f"- Allowed paths: {paths}. Anything else: do not edit; write the needed change in the second-pass file.",
              "- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.", ""]
    return "\n".join(lines)


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
            ledger=f"docs/glm-night/overnight-20261122/LANE_{lane}_LEDGER.md",
            sp=f"docs/glm-night/overnight-20261122/SECOND_PASS_{lane}.md")
        text = text.replace("20261119", "20261122").replace("glm-night/20261122-plan", "main")
        text = text.replace(f"wt-night-{lane.lower()}", f"wt-night-22{lane.lower()}")
        text = text.replace("Baseline at the branch point (local `main` 353b9b4): 970 passed, 4 skipped;",
                            f"Baseline at the branch point (local `main` {BASE}): 3558 passed, 6 skipped;")
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

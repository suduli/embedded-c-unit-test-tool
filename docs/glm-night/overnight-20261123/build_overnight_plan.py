"""Generate the 2026-11-23 queues (qualification, security, execution hardening; coverage and report depth). Regenerate, do not edit outputs."""
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
NOCC = ("There is no C compiler, debugger or simulator on this machine: test by parsing, golden text and fake "
        "callables only, and say so in the ledger.")
DOC = " Write the analysis note to docs/verification/{wp}-analysis.md in the same style as the existing notes there."

# key -> (title, goal, allowed paths, est k)
ITEMS = {
    "A1": ("WP-QUA-03: user-executable validation suite",
        "In ectt.qua add a validation suite a user can run on their own machine to check the tool works: a list of "
        "self-checks (each with an id, what it proves, how long it takes), a runner that executes them with fake or "
        "bundled inputs only (no network, no compiler needed), and a result record with pass, fail or not-run with a "
        "named reason. A check that needs a missing tool is not-run, never pass. Tests: all pass, one fails, one not-run, "
        "result record byte-stable." + DOC.format(wp="WP-QUA-03"),
        ["src/ectt/qua/", "tests/qua/", "docs/verification/WP-QUA-03-analysis.md"], 180),
    "A2": ("WP-QUA-04: known error list per release",
        "In ectt.qua add a known-error list model: entries with id, summary, affected versions, workaround, status "
        "(open, fixed in X), loaded from a plain-text data file, validated (duplicate ids, a fixed-in version not after "
        "the introduced version, missing workaround for an open entry are refused with named reasons), and a query that "
        "returns what applies to a given release. Tests for each refusal and the query." + DOC.format(wp="WP-QUA-04"),
        ["src/ectt/qua/", "tests/qua/", "docs/verification/WP-QUA-04-analysis.md"], 140),
    "A3": ("WP-SEC-01: Software Bill of Materials generation",
        "In ectt.sec add SBOM generation: read the installed Python package metadata (name, version, licence, hashes "
        "where recorded) of the tool and its dependencies and write a CycloneDX 1.5 JSON document, sorted and byte-stable "
        "(no timestamps unless injected). Release signing needs keys the owner holds: do NOT implement signing; add a "
        "named 'signing_not_configured' result and record it as a second-pass row. Take field names from the CycloneDX "
        "1.5 specification, not memory, and say in the ledger which source you used. Tests: stable output, missing "
        "licence reported as unknown, sort order." + DOC.format(wp="WP-SEC-01"),
        ["src/ectt/sec/", "tests/sec/", "docs/verification/WP-SEC-01-analysis.md"], 180),
    "A4": ("WP-SEC-02: pinned dependency integrity check",
        "In ectt.sec add a checker that compares the installed packages with a pinned lock file (name, exact version, "
        "hash) and reports each difference by name: missing, extra, wrong version, wrong hash, unpinned. Read only; it "
        "never installs anything. Do not edit pyproject.toml. Tests: clean match, each difference kind, malformed lock "
        "file refused." + DOC.format(wp="WP-SEC-02"),
        ["src/ectt/sec/", "tests/sec/", "docs/verification/WP-SEC-02-analysis.md"], 140),
    "A5": ("WP-SEC-06: restricted execution context for harnesses",
        "In ectt.exh add a restricted run context for starting a generated harness: confined working directory, scrubbed "
        "environment (only an allow-list passes), no inherited handles, a wall-clock limit and an output size limit, all "
        "recorded in the result. " + NOCC + " Test with a fake process starter that records what it was given. Tests: "
        "environment scrub, directory confinement refuses a path escape, limits recorded, a refused context starts "
        "nothing." + DOC.format(wp="WP-SEC-06"),
        ["src/ectt/exh/", "tests/exh/", "docs/verification/WP-SEC-06-analysis.md"], 170),
    "A6": ("WP-EXH-04: debugger launch with entry breakpoint",
        "In ectt.exh build the debugger command line for a built test harness: gdb first, with a breakpoint at the test "
        "function entry, the working directory and arguments as the normal run uses. Only build and return the command "
        "(argv list) and the refusal reasons (debugger not named, no symbols recorded, harness not built); starting the "
        "debugger is behind an injected starter. " + NOCC + " Tests: argv golden text, each refusal, quoting of paths with "
        "spaces." + DOC.format(wp="WP-EXH-04"),
        ["src/ectt/exh/", "tests/exh/", "docs/verification/WP-EXH-04-analysis.md"], 130),
    "A7": ("WP-CORE-08: self-verification of the tool's own source",
        "In ectt.core add a self-verification check: a manifest of the SHA-256 of every file in the installed ectt "
        "package, a function that writes it and one that verifies the installed tree against it, naming each changed, "
        "missing and unexpected file. Ignore __pycache__. Do not commit a manifest generated from this tree as a "
        "fixed file; tests build their own temp trees. Tests: clean, changed, missing, extra, manifest tampered." +
        DOC.format(wp="WP-CORE-08"),
        ["src/ectt/core/", "tests/core/", "docs/verification/WP-CORE-08-analysis.md"], 120),
    "A8": ("Mutation-style tests for qua, sec and exh",
        "Tests only. Hand-written mutants in a temp copy of src/ectt/qua, src/ectt/sec and src/ectt/exh (include the new "
        "modules from items A1 to A6); confirm existing tests kill each; add tests for survivors. Kill rate to "
        "docs/glm-night/overnight-20261123/mutation-qua-sec-exh.md. Reuse docs/glm-night/overnight-20261122/mutation_runner.py "
        "as a starting point (copy it, do not edit the original). No src/ edits.",
        ["tests/qua/", "tests/sec/", "tests/exh/", "docs/glm-night/overnight-20261123/"], 150),
    "A9": ("Seeded property-style tests for qua, sec and core",
        "Tests only. Fixed-seed random inputs: known-error list validation order independence, SBOM output stable under "
        "input order, lock-file checker symmetry, self-verification manifest round trip. No wall clock. No src/ edits.",
        ["tests/qua/", "tests/sec/", "tests/core/"], 120),
    "B1": ("WP-REP-05: certification verification report and scope statement",
        "In ectt.rep add a certification verification report built from existing result, coverage and trace data: the "
        "tool version, the unit and scope, what was run, coverage achieved against the stated criteria, which items are "
        "unmeasured or not applicable, and an explicit scope statement of what the report does NOT claim (no MC/DC, no "
        "target execution unless the data says so). Missing data is stated as missing, never filled. Import only narrow "
        "data classes from other packages. Tests: complete data, each missing input named, byte-stable output, a "
        "claim not supported by data is refused." + DOC.format(wp="WP-REP-05"),
        ["src/ectt/rep/", "tests/rep/", "docs/verification/WP-REP-05-analysis.md"], 200),
    "B2": ("WP-COV-06: uninstrumentable expression detection",
        "In ectt.cov add detection of expressions the compiler coverage backend cannot instrument (for example constant "
        "conditions, short-circuit forms folded away, macro expanded conditions), working from the analysis model's "
        "decision inventory (schema 1.5) and the gcov data. Result: a list of construct identities with a named reason "
        "each. A construct with no coverage data and no reason is 'no_data', not 'uninstrumentable'. Read the model only; "
        "do not edit ectt.ana." + DOC.format(wp="WP-COV-06"),
        ["src/ectt/cov/", "tests/cov/", "docs/verification/WP-COV-06-analysis.md"], 180),
    "B3": ("WP-COV-11: control coupling and data coupling analysis",
        "In ectt.cov add control coupling (which function calls were exercised by the tests, from the call graph in the "
        "analysis model and function-call coverage) and data coupling (which global variables are written by one "
        "function and read by another, from the global inventory in schema 1.5, and whether tests exercised both "
        "sides). Report per pair: exercised, not exercised, or not determinable with the reason. Do not claim a standard's "
        "objective is met; report data only. Tests: simple chain, unexercised call, global with no recorded access "
        "(not determinable), byte-stable output." + DOC.format(wp="WP-COV-11"),
        ["src/ectt/cov/", "tests/cov/", "docs/verification/WP-COV-11-analysis.md"], 200),
    "B4": ("Report output robustness: HTML escaping and size limits",
        "Review ectt.rep HTML and XML outputs (HTML report, JUnit, Cobertura, LCOV): test that hostile text in test "
        "names, source lines and messages (markup, quotes, control characters, very long lines, non-UTF-8 bytes) is "
        "escaped or refused with a named reason and never breaks the document structure. Fix bugs found in src/ectt/rep "
        "only. Tests: one per output format per hostile input class.",
        ["src/ectt/rep/", "tests/rep/"], 150),
    "B5": ("Interchange round-trip checks for coverage and results",
        "For the REP-10 and REP-02 formats, test export then import gives the same data, and that imports of "
        "hand-written files in the styles real tools produce (take structure from the public format descriptions, name "
        "the source in the ledger) are read correctly or refused with a named reason. Fix bugs in src/ectt/rep only. Say "
        "in the ledger that files from real tools are still unchecked.",
        ["src/ectt/rep/", "tests/rep/"], 150),
    "B6": ("Mutation-style tests for trc, mig and prj",
        "Tests only. Hand-written mutants in a temp copy of src/ectt/trc, src/ectt/mig and src/ectt/prj; confirm kills; "
        "add tests for survivors. Kill rate to docs/glm-night/overnight-20261123/mutation-trc-mig-prj.md. Reuse "
        "docs/glm-night/overnight-20261122/mutation_runner.py as a starting point (copy it). No src/ edits.",
        ["tests/trc/", "tests/mig/", "tests/prj/", "docs/glm-night/overnight-20261123/"], 150),
    "B7": ("Seeded property-style tests for cov coupling, rep report and trc",
        "Tests only. Fixed-seed random inputs: coupling analysis order independence, certification report stable under "
        "input order, trace matrix symmetry (requirement to test and test to requirement agree). No wall clock. No "
        "src/ edits. Run after items B1 and B3 exist.",
        ["tests/cov/", "tests/rep/", "tests/trc/"], 130),
}
LANE_A = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9"]
LANE_B = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]


def block(n, lane, key):
    title, goal, allowed, est = ITEMS[key]
    ledger = f"docs/glm-night/overnight-20261123/LANE_{lane}_LEDGER.md"
    sp = f"docs/glm-night/overnight-20261123/SECOND_PASS_{lane}.md"
    paths = ", ".join(f"`{p}`" for p in allowed + [ledger, sp])
    lines = [f"### {n}. {key}: {title}", "",
             f"- Estimate {est}k tokens, hard cap {int(est * 1.3)}k, or 3 failed gate attempts, then PARTIAL and move on.",
             f"- Goal: {goal}",
             f"- Allowed paths: {paths}. Anything else: do not edit; write the needed change in the second-pass file.",
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
            ledger=f"docs/glm-night/overnight-20261123/LANE_{lane}_LEDGER.md",
            sp=f"docs/glm-night/overnight-20261123/SECOND_PASS_{lane}.md")
        text = text.replace("20261119", "20261123").replace("glm-night/20261123-plan", "main")
        text = text.replace(f"wt-night-{lane.lower()}", f"wt-night-23{lane.lower()}")
        text = text.replace("Baseline at the branch point (local `main` 353b9b4): 970 passed, 4 skipped;",
                            f"Baseline at the branch point (local `main` {BASE}): 3710 passed, 6 skipped;")
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

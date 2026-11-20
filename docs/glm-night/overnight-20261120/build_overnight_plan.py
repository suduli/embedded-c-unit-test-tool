"""Generate the 2026-11-20 overnight queues. Reuses the 11-19 generator module; regenerate, do not edit outputs."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GLM = HERE.parent
spec = importlib.util.spec_from_file_location("prev", GLM / "overnight-20261119" / "build_overnight_plan.py")
prev = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
sys.modules["prev"] = prev
_argv = sys.argv
spec.loader.exec_module(prev)  # type: ignore[union-attr]
bpp = prev.bpp

BASE = "f044ef1"
D02 = prev.D02
# id -> (title, goal, allowed paths)
CUSTOM = {
    "FIX-REP": ("Report model reader and merge fix",
        "In src/ectt/rep/model.py (format 1.1): make the reader's 'execution' field optional (provenance stays required) so merged reports, which have no single runner, load through load_report_model; expose a public factory for digest-bound models built outside a ResultSet and switch the CI-merge code to it instead of the private helper; add 'report', 'traceability' and 'migration' to CATEGORY_EXIT_CODES in ectt.cli.exit_codes. Keep the old behaviour for reports that do have execution. Tests: merged report round trip, missing provenance still refused, exit code per new category.",
        ["src/ectt/rep/", "tests/rep/", "src/ectt/cli/", "tests/cli/"]),
    "FIX-TXN": ("Route project saves and analysis-model writes through the safe-write transaction",
        "Close the WP-CORE-02 remainder in SECOND_PASS_B.md: route ectt.prj project saves and ectt.ana.persist.write_analysis_model callers through OutputRoot.transaction, so a cancelled or failed write leaves the original files untouched (SDD-003 section 3). Do not change file formats or public names. Tests: injected failure mid-save leaves original byte-identical; cancellation leaves no partial file.",
        ["src/ectt/prj/", "tests/prj/", "src/ectt/ana/", "tests/ana/"]),
    "CI-LINUX": ("Linux CI lane for the full gate",
        "D-03 says Windows first with Linux CI kept green. Edit only .github/workflows/tests.yml so the full gate block (pytest, ruff, mypy, plan_check, trace_check, and the Linux baseline test) runs on ubuntu-latest and windows-latest with pinned action versions and 'permissions: contents: read'. Do not edit traceability.yml. Verify the YAML parses and that every command in it works locally. Say in the ledger that CI itself could not be run.",
        [".github/workflows/tests.yml"]),
    "FIX-ANAGATE": ("Wire eligibility-gate reasons to the unsupported-construct inventory",
        "The PAR-140 inventory is now populated. Make the eligibility gate (src/ectt/ana/eligibility.py) report each unsupported construct from the inventory as a named reason instead of the generic 'unmodeled aspects' text. Do not touch PAR-080 (exposure; ADR-sensitive). Tests: one per construct kind, ordering deterministic, empty inventory unchanged.",
        ["src/ectt/ana/", "tests/ana/"]),
    "TEST-MUT2": ("Mutation-style test strengthening for rep and trc",
        "Tests only. For src/ectt/rep and src/ectt/trc, hand-write mutants (flip a comparison, drop a branch, swap an ordering) in a temp copy, confirm the existing tests kill each, and add tests for any survivor. Report kill rate in docs/glm-night/overnight-20261120/mutation-rep-trc.md. No src/ edits.",
        ["tests/rep/", "tests/trc/", "docs/glm-night/overnight-20261120/"]),
    "FIX-GENPROTO": ("Harness emits the run-result stream and resets state in the setup hook",
        "From SECOND_PASS_A.md: make generated harnesses emit the RESULT/FAILURE stream protocol defined in docs/verification/WP-EXH-01-analysis.md, and reset harness state in the setup hook (DSN-TCM-060). Tests: generated harness output parses with the WP-EXH-01 normaliser; state from one test never leaks into the next.",
        ["src/ectt/gen/", "tests/gen/"]),
    "FIX-TCMNEST": ("Nested struct, array and union expectations in test case files",
        "From SECOND_PASS_A.md: extend the WP-TCM-02 model and the .tests restricted-YAML form so expected values for struct, array and union can be authored, and make the WP-TCM-03 comparison engine consume them. Keep existing flat files valid and byte-stable. Tests: round trip, nested mismatch reported with a path, unknown member refused.",
        ["src/ectt/tcm/", "tests/tcm/"]),
    "TEST-PROP-TCM": ("Seeded property-style tests for tcm and exh",
        "Tests only. Deterministic seeded random inputs for the CSV interchange round trip, range expansion and suite selection expressions (tcm), and result-record normalisation (exh). Fixed seeds, no wall clock. No src/ edits.",
        ["tests/tcm/", "tests/exh/"]),
}

LANE_A = [
    ("WP-CBT-01", 130, D02 + " " + prev.T14),
    ("WP-ATG-01", 180, D02),
    ("WP-TCM-07", 205, D02),
    ("WP-GEN-07", 205, D02),
    ("FIX-GENPROTO", 180, ""),
    ("FIX-TCMNEST", 150, ""),
    ("WP-ATG-05", 155, ""),
    ("WP-EXT-04", 155, ""),
    ("TEST-PROP-TCM", 150, ""),
]
LANE_B = [
    ("FIX-REP", 110, ""),
    ("FIX-TXN", 120, ""),
    ("CI-LINUX", 60, ""),
    ("WP-MIG-02", 180, ""),
    ("WP-MIG-04", 230, ""),
    ("WP-MIG-05", 155, ""),
    ("WP-TRC-04", 180, ""),
    ("WP-TRC-05", 180, ""),
    ("WP-MIG-03", 100, ""),
    ("WP-MIG-07", 180, ""),
    ("FIX-ANAGATE", 90, ""),
    ("TEST-MUT2", 150, ""),
]


def custom_block(n, lane, key, est):
    title, goal, allowed = CUSTOM[key]
    cap = int(est * 1.3)
    ledger = f"docs/glm-night/overnight-20261120/LANE_{lane}_LEDGER.md"
    sp = f"docs/glm-night/overnight-20261120/SECOND_PASS_{lane}.md"
    paths = ", ".join(f"`{p}`" for p in allowed + [ledger, sp])
    return "\n".join([
        f"### {n}. {key}: {title}", "",
        f"- Estimate {est}k tokens, hard cap {cap}k, or 3 failed gate attempts, then PARTIAL and move on.",
        f"- Goal: {goal}",
        f"- Allowed paths: {paths}. Anything else: do not edit; write the needed change in the second-pass file.",
        "- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.", ""])


def pkg_of_path(p):
    parts = p.split("/")
    if p.startswith(("src/ectt/", "tests/")) and len(parts) >= 3:
        return parts[2] if p.startswith("src/ectt/") else parts[1]
    return p


def main():
    rows = bpp.load_board()
    by = {r["wp"]: r for r in rows}
    live = {x["wp"]: x for x in json.loads((HERE / "board-live.json").read_text(encoding="utf-8"))}
    notes = prev.ledger_notes()
    done_last_night = set()
    for f in ("LANE_A_LEDGER.md", "LANE_B_LEDGER.md"):
        for line in (GLM / "overnight-20261119" / f).read_text(encoding="utf-8").splitlines():
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) > 2 and c[0].startswith("WP-") and c[1].startswith("DONE"):
                done_last_night.add(c[0])
    queued = {}
    for lane, items in (("A", LANE_A), ("B", LANE_B)):
        for wp, *_ in items:
            if wp in queued or wp in done_last_night:
                sys.exit(f"bad queue item {wp}")
            if wp.startswith("WP-") and wp not in by:
                sys.exit(f"unknown {wp}")
            queued[wp] = lane
    pk = {"A": set(), "B": set()}
    for wp, lane in queued.items():
        if wp.startswith("WP-"):
            pk[lane].add(bpp.package_of(by[wp]))
        else:
            for p in CUSTOM[wp][2]:
                pk[lane].add(pkg_of_path(p))
    pk["A"].discard("docs")
    pk["B"].discard("docs")
    if pk["A"] & pk["B"]:
        sys.exit(f"overlap {pk['A'] & pk['B']}")

    totals = {}
    for lane, items in (("A", LANE_A), ("B", LANE_B)):
        text = prev.PREAMBLE.format(
            lane=lane, lc=lane.lower(),
            ledger=f"docs/glm-night/overnight-20261120/LANE_{lane}_LEDGER.md",
            sp=f"docs/glm-night/overnight-20261120/SECOND_PASS_{lane}.md")
        text = text.replace("20261119", "20261120")
        text = text.replace("glm-night/20261120-plan", "main")
        text = text.replace("Baseline at the branch point (local `main` 353b9b4): 970 passed, 4 skipped;",
                            f"Baseline at the branch point (local `main` {BASE}): 1457 passed, 5 skipped;")
        text = text.replace("Item N00 is the only exception for `design/`.", "No item may edit `design/`.")
        text = text.replace(
            "Stop starting new items when your lane's cumulative reaches 1,450k tokens OR the local time reaches 05:30, whichever comes first.",
            "Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first. Last night the estimates ran high, so expect to finish the whole list.")
        cum = 0
        parts = []
        for i, (wp, est, extra) in enumerate(items, 1):
            cum += est
            if wp in CUSTOM:
                parts.append(custom_block(i, lane, wp, est))
            else:
                b = prev.block(i, lane, wp, est, extra, None, by, notes)
                parts.append(b.replace("20261119", "20261120"))
        totals[lane] = cum
        (HERE / f"LANE_{lane}_queue.md").write_text(
            text + "\n".join(parts) + f"\n## End\nListed total {cum}k tokens.\n", encoding="utf-8")

    saved = dict(bpp.EXPLICIT_BLOCKERS)
    for k in ("WP-CORE-03", "WP-GUI-01", "WP-TCM-02", "WP-EXH-01", "WP-EXH-02", "WP-CBT-01", "WP-CORE-05"):
        bpp.EXPLICIT_BLOCKERS.pop(k, None)
    bpp.EXPLICIT_BLOCKERS["WP-CORE-05"] = prev.KEEP_BLOCKED["WP-CORE-05"]
    held = bpp.closure_blocked(by)
    universe = [w for w, x in live.items()
                if x["status"] in ("Backlog", "Needs reconciliation", "Verification") and w not in done_last_night]
    out_rows, n_q = [], 0
    for w in sorted(universe):
        if w in queued:
            n_q += 1
            continue
        r = by[w]
        if w in held:
            cat = "Blocked by open decision"
            why = "; ".join(sorted({bpp.EXPLICIT_BLOCKERS.get(b, b) for b in held[w]}))
        elif r["component"] == "CMP-GUI":
            cat, why = "Needs visual/toolkit verification", "GUI work cannot be checked without a person looking at it"
        elif r["component"] == "CMP-AIF":
            cat, why = "Held for ADR-008 / PR #4", "PR #4 is open and conflicting; provider design unsettled"
        elif w in prev.RUNTIME:
            cat, why = "Needs runtime/hardware", prev.RUNTIME[w]
        elif r["adr"]:
            cat, why = "ADR-sensitive", "needs an owner decision (classification, ADR or exposure mechanism)"
        elif live[w]["status"] == "Verification":
            cat, why = "Partial; rest is not unattended", (notes.get(w, ("", ""))[1][:160] or "ledger PARTIAL")
        else:
            cat, why = "Runnable, not scheduled tonight", "decision-free; next-night candidate"
        out_rows.append((w, r["title"].split("] ", 1)[-1], cat, why))
    bpp.EXPLICIT_BLOCKERS.clear()
    bpp.EXPLICIT_BLOCKERS.update(saved)
    if n_q + len(out_rows) != len(universe):
        sys.exit("completeness check failed")
    lines = ["# Deferred (generated)", "",
             f"{len(universe)} open items after removing the {len(done_last_night)} finished last night. "
             f"In tonight's queues: {n_q} board items (plus follow-up fixes). Deferred: {len(out_rows)}.", "",
             "| Item | Title | Category | Reason |", "|---|---|---|---|"]
    lines += [f"| {w} | {t} | {c} | {why} |" for w, t, c, why in out_rows]
    (HERE / "DEFERRED.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(totals, len(universe), n_q, len(out_rows))
    cats = {}
    for _w, _t, c, _why in out_rows:
        cats[c] = cats.get(c, 0) + 1
    print(cats)


if __name__ == "__main__":
    main()

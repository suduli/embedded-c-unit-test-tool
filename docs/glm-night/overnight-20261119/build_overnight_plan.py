"""Generate the 2026-11-19 overnight GLM queues (two lanes) and the plan summary.

Reuses load_board/package_of from ../build_parallel_plan.py (not edited).
Statuses come from board-live.json; requirements, dependencies and acceptance text from
../board-snapshot.json. Regenerate instead of editing the outputs.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GLM = HERE.parent
spec = importlib.util.spec_from_file_location("bpp", GLM / "build_parallel_plan.py")
bpp = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
spec.loader.exec_module(bpp)  # type: ignore[union-attr]

D02 = (
    "D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "
    "\"Stable ids plus content digests\"."
)
D03 = (
    "D-03 Platform order (owner answer, 2026-11-19, memo option (a)): "
    "\"Windows first, Linux CI kept green\"."
)
T14 = (
    "Also satisfy the run-integrity acceptance of T-14 (EXEC-PLAN-001 section 7.4, card T-14). "
    "It was waiting on D-02, which is now answered."
)

# (wp, est_ktokens, extra_prompt, needs_other_lane)
# est = rough tokens in thousands; per-item hard cap = 1.3 x est.
LANE_A = [
    ("N00", 60, "D02-APPLY", None),
    ("WP-TCM-02", 205, D02, None),
    ("WP-EXH-01", 180, D02 + " " + T14, None),
    ("WP-EXH-02", 155, T14, None),
    ("WP-TCM-03", 180, D02, None),
    ("WP-TCM-04", 155, D02, None),
    ("WP-EXH-03", 130, "", None),
    ("WP-TCM-05", 155, D02, None),
    ("WP-TCM-06", 155, D02, None),
    ("WP-CBT-01", 130, D02 + " " + T14, None),
    ("WP-TCM-07", 205, D02, None),
    ("WP-GEN-07", 205, D02, None),
    ("WP-ATG-01", 180, D02, None),
]
LANE_B = [
    ("WP-CORE-03", 130, D03, None),
    ("WP-CORE-02", 90, "REMAINDER-CORE02", None),
    ("WP-ANA-07", 90, "REMAINDER-ANA07", None),
    ("WP-ANA-06", 150, "REMAINDER-ANA06", None),
    ("TASK-107", 150, "FILLER-107", None),
    ("WP-REP-01", 180, D02, "WP-EXH-01"),
    ("WP-REP-11", 130, "", None),
    ("WP-REP-06", 155, "", None),
    ("WP-REP-08", 180, "", None),
    ("WP-PLG-03", 155, "", None),
    ("WP-CORE-04", 60, "REMAINDER-CORE04", None),
    ("WP-PRJ-05", 180, "", None),
    ("WP-REP-09", 155, "", None),
    ("WP-CLI-05", 155, "", None),
    ("WP-TRC-01", 180, D02, "WP-TCM-02"),
    ("WP-TRC-02", 130, "", None),
    ("TASK-108", 150, "FILLER-108", None),
    ("WP-REP-12", 155, D02, "WP-TCM-06"),
    ("WP-MIG-01", 180, "", "WP-EXH-01"),
    ("WP-TRC-03", 180, "", None),
]

REMAINDERS = {
    "REMAINDER-CORE02": (
        "WP-CORE-02 is PARTIAL (see CHAT2_LEDGER.md row). Close the decision-free remainder: "
        "(1) adopt the stable exit-code table from WP-CLI-02 (src/ectt/cli) for every EcttError "
        "category, with a test per category; (2) route at least one existing long-running "
        "operation through OutputRoot.transaction so a cancelled or failed run leaves no partial "
        "output (test with a cancellation token and with an injected failure)."
    ),
    "REMAINDER-ANA07": (
        "WP-ANA-07 is PARTIAL. Close the decision-free remainder: PAR-140 unsupported-construct "
        "inventory is carried and schema-gated but never populated (always []). Populate it from "
        "extraction for constructs the extractor already recognises as unsupported, deterministic "
        "and sorted, with fixtures. Do not add a multi-file driver."
    ),
    "REMAINDER-ANA06": (
        "WP-ANA-06 is PARTIAL. Implement PAR-090 only (macro resolution) with libclang fixtures. "
        "Do NOT touch PAR-080 (exposure mechanism; ADR-sensitive, belongs with WP-GEN-03). "
        "If a fixture cannot be made deterministic, record PARTIAL with the reason."
    ),
    "REMAINDER-CORE04": (
        "WP-CORE-04 is PARTIAL. Now that the report model (WP-REP-01) exists in your branch, embed "
        "the provenance record in the artifacts the producing packages already emit, per "
        "TOOL-QUA-060. Skip any artifact whose producer is not yet in the branch and list it."
    ),
    "FILLER-107": (
        "Run EXEC-PLAN-001 section 7.2 card TASK-107 (mutation-style test strengthening for "
        "ectt.core and ectt.prj). Tests only; no src changes."
    ),
    "FILLER-108": (
        "Run EXEC-PLAN-001 section 7.2 card TASK-108 (seeded property-style tests for the YAML "
        "adapter and schema reader). Tests only; deterministic seeds only."
    ),
}

# Deferred categories (checked in this order for every non-queued, non-Review item).
RUNTIME = {
    "WP-SPIKE-03": "clean-VM endpoint-security step is manual",
    "WP-TCH-03": "needs real cross toolchains",
    "WP-TCH-05": "needs real toolchains and containers",
    "WP-TCH-06": "needs proprietary compilers",
    "WP-BLD-03": "needs a cross-compiled target build on a machine with the toolchain",
    "WP-EXT-01": "needs QEMU/Renode",
    "WP-EXT-02": "needs a debug probe and hardware",
}

ALLOW_EXTRA = {
    "WP-CORE-02": ["src/ectt/cli/", "tests/cli/"],
    "WP-CORE-04": ["src/ectt/rep/", "tests/rep/"],
}

KEEP_BLOCKED = {  # blockers that stay explicit after the D-02/D-03 answers
    "WP-CORE-05": "D-04 answered 'defer to post-pilot, mark provisional': calibrate before WP-CORE-05 exits P2",
}


def ledger_notes() -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for name in ("CHAT1_LEDGER.md", "CHAT2_LEDGER.md"):
        for line in (GLM / name).read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 5 and re.match(r"WP-[A-Z]+-\d+", cells[0]):
                out[cells[0]] = (cells[1], cells[4])
    return out


def est_row(wp: str, extra: str) -> str:
    return extra


def block(n: int, lane: str, wp: str, est: int, extra: str, needs: str | None,
          by: dict, notes: dict) -> str:
    cap = int(est * 1.3)
    ledger = f"docs/glm-night/overnight-20261119/LANE_{lane}_LEDGER.md"
    sp = f"docs/glm-night/overnight-20261119/SECOND_PASS_{lane}.md"
    head = [f"### {n}. {wp}", ""]
    if wp == "N00":
        head[0] = f"### {n}. N00: Apply the D-02 answer to the design text (SDD only)"
        body = [
            f"- Estimate {est}k tokens, cap {cap}k. Lane {lane}. Must be first.",
            f"- Decision (do not re-decide): {D02}",
            "- Goal: edit `design/SDD-003-data-model.md` sections 6 and 7 and the single sentence in "
            "`design/SDD-002` (S2/S3) so they record stable ids plus content digests. Apply the "
            "memo's option (a) patch text for D-02 from `docs/proposals/decision-memos-20261117.md` "
            "verbatim; adjust only for line drift.",
            "- Allowed paths: `design/SDD-003-data-model.md`, `design/SDD-002*` (one sentence), "
            f"`{ledger}`.",
            "- Forbidden here: `SRS-001-requirements.md`, `LICENSE`, `LICENSEES`, any ADR file, the "
            "decision register, `design/trace/*` regeneration. D-01, D-03 and D-04 are NOT applied "
            "tonight; D-03 is carried as a constraint in item prompts only.",
            "- Done when: the three sections state the answer, `plan_check.py` and `trace_check.py` "
            "pass, full gate green, commit `[GLM-NIGHT] N00: record D-02 identity model in SDD-003`.",
            "- If the memo patch does not apply cleanly or the gates fail after one fix attempt: do "
            f"not force it. Append a row to `{sp}` and continue; items that need SDD-003 section 6/7 "
            "continue against the memo text and note that in their ledger rows.",
            "",
        ]
        return "\n".join(head + body)
    if wp.startswith("TASK-"):
        body = [
            f"- Estimate {est}k tokens, cap {cap}k. Lane {lane}. Filler: tests only.",
            f"- Goal: {REMAINDERS[extra]}",
            "- Allowed paths: `tests/core/`, `tests/prj/`, "
            f"`docs/glm-night/overnight-20261119/`, `{ledger}`. No `src/` edits.",
            "- Done when: new tests pass, no existing test changed, full gate green, one commit.",
            "",
        ]
        return "\n".join(head + body)
    r = by[wp]
    pkg = bpp.package_of(r)
    recon = bool(r["no_ac"])
    reqs = ", ".join(r["reqs"][:12]) or "none listed on the board"
    ac = r["ac"] or "none recorded in PLAN-001 section 5.4; derive them (step 1)"
    ac = ac.replace("\n", " ")[:900]
    st = notes.get(wp)
    goal = f"Implement {wp} ({r['title'].split('] ', 1)[-1]}) for requirements {reqs}."
    if extra.startswith("REMAINDER"):
        goal = REMAINDERS[extra]
    prior = f" Prior ledger state `{st[0]}`: {st[1][:300]}" if st else ""
    deps = []
    for d in r["deps"]:
        deps.append(d)
    lines = head[:1] + [
        f"{r['title']}  (board: {r['component']}, phase {r['phase']}, {r['effort']} person-weeks)",
        "",
        f"- Estimate {est}k tokens, hard cap {cap}k, or 3 failed gate attempts, then PARTIAL and move on.",
        f"- Goal: {goal}{prior}",
        f"- Requirements: {reqs}",
        f"- Acceptance criteria (board): {ac}",
        f"- Dependencies: {', '.join(deps) or 'none'}. Items already implemented are in the repo; "
        "items earlier in this queue must be DONE or PARTIAL in your ledger first.",
    ]
    if needs:
        lines.append(
            f"- CROSS-LANE DEPENDENCY on `{needs}` (lane A). Before starting: check "
            "`docs/glm-night/overnight-20261119/LANE_A_LEDGER.md` in the lane A worktree "
            f"(`../wt-night-a`) for a `{needs}` row that is DONE (PARTIAL only if its remainder is "
            "unrelated). If so: `git merge --no-edit glm-night/20261119-a`, run the full gate; if it "
            "is red, `git revert -m 1 HEAD` and treat as not satisfied. If not satisfied: SKIP this "
            "item for now and retry it once after the last queue item before writing the summary; "
            "if still unsatisfied record `SKIPPED (dep)` in the ledger and the second-pass file."
        )
    if extra and not extra.startswith(("REMAINDER", "FILLER")):
        lines.append(f"- Decision text (do NOT re-decide; implement it as written): {extra}")
    if r["adr"] and not extra:
        lines.append("- ADR-sensitive: implement the decision-free part only; record each open ADR question in the second-pass file.")
    lines += [
        f"- Allowed paths: `src/ectt/{pkg}/`, `tests/{pkg}/`, "
        + "".join(f"`{x}`, " for x in ALLOW_EXTRA.get(wp, []))
        + f"`docs/verification/{wp}-analysis.md`, "
        f"`{ledger}`, `{sp}`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): "
        "do not edit; write the needed change in the second-pass file.",
        "",
        "Steps:",
    ]
    s = 1
    if recon and not extra.startswith("REMAINDER"):
        lines.append(
            f"{s}. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and "
            f"the SRS text; write them under `## Acceptance criteria` in `docs/verification/{wp}-analysis.md` "
            "before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`."
        )
        s += 1
    lines += [
        f"{s}. Implement the smallest increment that meets the criteria with tests: happy path plus at "
        "least two error/edge cases; deterministic output; no network; no wall-clock in outputs.",
        f"{s + 1}. Write or update `docs/verification/{wp}-analysis.md` (requirement -> implementation -> "
        "real test names). Mark anything uncovered as not covered.",
        f"{s + 2}. Run the gate block. Commit with the commit block. Append one ledger row. Next item.",
        "",
    ]
    return "\n".join(lines)


PREAMBLE = """# Overnight GLM queue, lane {lane} (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-{lc} -b glm-night/20261119-{lc} glm-night/20261119-plan
cd ../wt-night-{lc}
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` 353b9b4): 970 passed, 4 skipped; ruff, mypy, plan_check, trace_check all clean. Create `{ledger}` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `{sp}` with header `| item | what is needed | why it needs a human | where |`.

## Gate block (run before every commit; all must exit 0)
```
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy src
.venv/Scripts/python.exe design/trace/plan_check.py
.venv/Scripts/python.exe design/trace/trace_check.py
```
Do not regenerate `design/trace/*` or the unified plan.

## Commit block
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261119-{lc}`.

## Hard rules
1. Never decide an owner decision. Open: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9, PR #4. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. Item N00 is the only exception for `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `{sp}` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when your lane's cumulative reaches 1,450k tokens OR the local time reaches 05:30, whichever comes first. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261119/LANE_{lane}_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
"""


def main() -> None:
    rows = bpp.load_board()
    by = {r["wp"]: r for r in rows}
    live = {x["wp"]: x for x in json.loads((HERE / "board-live.json").read_text(encoding="utf-8"))}
    notes = ledger_notes()

    queued: dict[str, str] = {}
    for lane, items in (("A", LANE_A), ("B", LANE_B)):
        for wp, *_ in items:
            if wp in queued:
                sys.exit(f"duplicate queue item {wp}")
            queued[wp] = lane
    for wp in queued:
        if wp.startswith("WP-") and wp not in by:
            sys.exit(f"unknown WP {wp}")

    # Package ownership check: no package appears in both lanes.
    pk: dict[str, set[str]] = {"A": set(), "B": set()}
    for wp, lane in queued.items():
        if wp.startswith("WP-"):
            pk[lane].add(bpp.package_of(by[wp]))
    if pk["A"] & pk["B"]:
        sys.exit(f"package overlap between lanes: {pk['A'] & pk['B']}")

    totals = {}
    for lane, items in (("A", LANE_A), ("B", LANE_B)):
        lc = lane.lower()
        text = PREAMBLE.format(
            lane=lane, lc=lc,
            ledger=f"docs/glm-night/overnight-20261119/LANE_{lane}_LEDGER.md",
            sp=f"docs/glm-night/overnight-20261119/SECOND_PASS_{lane}.md",
        )
        cum = 0
        parts = []
        for i, (wp, est, extra, needs) in enumerate(items, 1):
            cum += est
            parts.append(block(i, lane, wp, est, extra, needs, by, notes))
        totals[lane] = cum
        (HERE / f"LANE_{lane}_queue.md").write_text(
            text + "\n".join(parts) + f"\n## End\nListed total {cum}k tokens (stop rule above applies earlier).\n",
            encoding="utf-8",
        )

    # Deferred list: every Backlog / Needs reconciliation / Verification item exactly once.
    saved = dict(bpp.EXPLICIT_BLOCKERS)
    for k in ("WP-CORE-03", "WP-GUI-01", "WP-TCM-02", "WP-EXH-01", "WP-EXH-02", "WP-CBT-01", "WP-CORE-05"):
        bpp.EXPLICIT_BLOCKERS.pop(k, None)
    bpp.EXPLICIT_BLOCKERS["WP-CORE-05"] = KEEP_BLOCKED["WP-CORE-05"]
    held = bpp.closure_blocked(by)
    universe = [w for w, x in live.items() if x["status"] in ("Backlog", "Needs reconciliation", "Verification")]
    rows_def = []
    overflow = []
    seen = set(queued)
    for w in sorted(universe):
        if w in queued:
            continue
        r = by[w]
        if w in held:
            roots = sorted(held[w])
            why = "; ".join(sorted({bpp.EXPLICIT_BLOCKERS.get(b, b) for b in roots}))
            cat = "Blocked by open decision"
        elif r["component"] == "CMP-GUI":
            cat, why = "Needs visual/toolkit verification", "GUI toolkit work (ADR-001 spike) cannot be verified unattended; schedule with a human"
        elif r["component"] == "CMP-AIF":
            cat, why = "Held for ADR-008 / PR #4", "PR #4 (ADR-008 allocation) is open and conflicting; provider design unsettled"
        elif w in RUNTIME:
            cat, why = "Needs runtime/hardware", RUNTIME[w]
        elif r["adr"] and r["component"] == "CMP-QUA":
            cat, why = "ADR-sensitive", "depends on the WP-QUA-01 tool classification judgment, which is an owner/ADR decision"
        elif r["adr"]:
            cat, why = "ADR-sensitive", "ADR-sensitive and no answered decision covers it"
        elif live[w]["status"] == "Verification":
            st = notes.get(w, ("", ""))
            cat, why = "PARTIAL; remainder is not decision-free or not unattended", st[1][:160] or "ledger PARTIAL"
        else:
            cat, why = "Runnable, not scheduled tonight", "decision-free; no budget left in tonight's two lanes (next-night candidate)"
            overflow.append(w)
        rows_def.append((w, r["title"].split("] ", 1)[-1], live[w]["status"], cat, why))
        seen.add(w)
    bpp.EXPLICIT_BLOCKERS.clear()
    bpp.EXPLICIT_BLOCKERS.update(saved)

    missing = [w for w in universe if w not in seen]
    if missing:
        sys.exit(f"completeness check failed: {missing}")
    if len(rows_def) + len([w for w in universe if w in queued]) != len(universe):
        sys.exit("completeness check failed: counts")

    out = ["# Deferred to second-pass review (generated)", "",
           f"Universe: {len(universe)} board items in Backlog, Needs reconciliation or Verification (live board, 2026-11-19). "
           f"Queued tonight: {len([w for w in universe if w in queued])}. Deferred: {len(rows_def)}. "
           "Board has no To Do or In Progress column: Verification counts as in progress; Review means done and awaiting the owner (51 items, not in scope).", "",
           "| Item | Title | Board status | Category | Reason |", "|---|---|---|---|---|"]
    for w, t, s, c, why in rows_def:
        out.append(f"| {w} | {t} | {s} | {c} | {why} |")
    (HERE / "DEFERRED.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    plan = ["# Overnight plan 2026-11-19 (generated)", "",
            "Base: local `main` 353b9b4 (970 passed, 4 skipped; ruff, mypy, plan_check, trace_check clean). Branch `glm-night/20261119-plan` holds these files; lanes branch from it.",
            "Window: now to 06:00; stop starting items at 05:30. Token pool 3.0M: 1.45M stop per lane, about 0.1M reserve.",
            "Estimates are rough (+/-40%). Rows marked tail run only if the lane is under 1.45M when it reaches them.", ""]
    for lane, items in (("A", LANE_A), ("B", LANE_B)):
        plan += [f"## Lane {lane}", "", "| # | Item | Est k | Cap k | Cumulative k | Cross-lane | Zone |", "|---|---|---|---|---|---|---|"]
        cum = 0
        for i, (wp, est, extra, needs) in enumerate(items, 1):
            zone = "core" if cum < 1450 else "tail"
            cum += est
            title = by[wp]["title"].split("] ", 1)[-1] if wp in by else {"N00": "Apply D-02 to SDD-003 s6/s7", "TASK-107": "Mutation-style test strengthening", "TASK-108": "Seeded property tests"}[wp]
            plan.append(f"| {i} | {wp} {title} | {est} | {int(est*1.3)} | {cum} | {needs or ''} | {zone} |")
        plan.append("")
    (HERE / "PLAN.md").write_text(chr(10).join(plan) + chr(10), encoding="utf-8")
    print("lane totals (k tokens):", totals)
    print("universe", len(universe), "queued", len([w for w in universe if w in queued]), "deferred", len(rows_def), "overflow", len(overflow))
    cats: dict[str, int] = {}
    for *_, c, _w in rows_def:
        cats[c] = cats.get(c, 0) + 1
    print(cats)


if __name__ == "__main__":
    main()

"""Build the two-chat parallel plan and queues from the board snapshot.

Inputs:  docs/glm-night/board-snapshot.json (GitHub project 5 export),
         EXEC-PLAN-001-tracker.html (landed tasks and their WP ids).
Outputs: docs/glm-night/parallel-plan.md, chat1-queue.md, chat2-queue.md.
Also runs the validator and exits non-zero on any violation.

Run from the repository root with the project venv:
    .venv/Scripts/python.exe docs/glm-night/build_parallel_plan.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "glm-night"
SNAPSHOT = OUT / "board-snapshot.json"
TRACKER = ROOT / "EXEC-PLAN-001-tracker.html"

# Owner decisions and ADRs that gate work. A waiver removes one blocker for one item only
# after the owner approves it in writing. Empty by default.
EXPLICIT_BLOCKERS = {
    "WP-CORE-03": "D-03 platform order (TASK-007 blocked)",
    "WP-GUI-01": "D-03 platform order",
    "WP-TCM-02": "D-02 identity model (T-04)",
    "WP-EXH-01": "D-02 identity model (T-14 run-integrity)",
    "WP-EXH-02": "D-02 identity model (T-14 run-integrity)",
    "WP-CBT-01": "D-02 identity model (T-14 run-integrity)",
    "WP-CORE-05": "D-04 NFR calibration",
    "WP-PKG-07": "D-01 licence posture (ADR-005)",
    "WP-PKG-08": "D-01 licence posture (ADR-005)",
    "WP-PKG-01": "ADR-007 (not in decision queue)",
    "WP-ATG-02": "ADR-003 (not in decision queue)",
    "WP-ATG-03": "ADR-003 (not in decision queue)",
    "WP-COV-01": "ADR-004 (not in decision queue; critical path)",
    "WP-COV-05": "SRS-Q2 open question",
    "WP-EXH-04": "SRS-Q9 open question",
}
WAIVERS: dict[str, set[str]] = {}  # item -> blocker ids the owner has waived

CHAT_COUNT = 2
CHAT_LOG = {1: "CHAT1_LEDGER.md", 2: "CHAT2_LEDGER.md"}
SHARED_PATHS = [
    "EXEC-PLAN-001-tracker.html",
    "EXEC-PLAN-001-unified-execution-plan.md",
    "docs/glm-night/GLM_NIGHT_LOG.md",
    "docs/glm-night/parallel-plan.md",
    "docs/glm-night/build_parallel_plan.py",
    "docs/glm-night/board-snapshot.json",
    "docs/glm-night/chat1-queue.md",
    "docs/glm-night/chat2-queue.md",
    "SRS-001-requirements.md",
    "PLAN-001-specification-analysis-and-work-breakdown.md",
    "design/",
    "pyproject.toml",
    "src/ectt/__init__.py",
    "tests/conftest.py",
    "BACKLOG_GLM_NIGHT.md",
]
PHASE_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
SPECIAL_PACKAGES = {"Validation spikes": "spikes"}


def load_board() -> list[dict[str, object]]:
    items = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["items"]
    rows = []
    for item in items:
        body = item["content"]["body"] if isinstance(item.get("content"), dict) else ""
        wp = str(item.get("work Package") or "")
        match = re.search(r"## Dependencies \((\d+)\)\s*\n(.*?)\n## ", body, re.DOTALL)
        deps = (
            sorted(set(re.findall(r"WP-[A-Z]+-\d+", match.group(2)))) if match else []
        )
        req_block = re.search(
            r"## Requirements owned \(\d+\)\s*\n(.*?)\n## ", body, re.DOTALL
        )
        # Requirement ids only; the board's tables and prose are noise in a prompt.
        reqs = (
            sorted(set(re.findall(r"TOOL-[A-Z]+-\d+", req_block.group(1))))
            if req_block
            else []
        )
        ac_block = re.search(r"## Acceptance criteria\s*\n(.*?)\n## ", body, re.DOTALL)
        ac = ac_block.group(1).strip() if ac_block else ""
        rows.append(
            {
                "wp": wp,
                "title": str(item["title"]),
                "component": str(item["component"]),
                "phase": str(item["phase"]),
                "effort": str(item["effort"]),
                "status": str(item["status"]),
                "adr": "ADR-sensitive:** yes" in body,
                "no_ac": "No package-specific acceptance" in body,
                "deps": deps,
                "reqs": reqs,
                "ac": ac,
            }
        )
    return rows


def tracker_landed_wps() -> set[str]:
    landed: set[str] = set()
    for line in TRACKER.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith('{"id":"TASK-') and '"status":"Landed"' in s:
            wps = s.split('"wps":')[1].split("]")[0]
            landed |= set(re.findall(r"WP-[A-Z]+-\d+", wps))
    return landed


def package_of(row: dict[str, object]) -> str:
    comp = str(row["component"])
    if comp in SPECIAL_PACKAGES:
        return SPECIAL_PACKAGES[comp]
    return comp.removeprefix("CMP-").lower()


def closure_blocked(by: dict[str, dict[str, object]]) -> dict[str, set[str]]:
    """Map every held item to the explicit blockers it is downstream of."""
    held: dict[str, set[str]] = {}
    for wp in EXPLICIT_BLOCKERS:
        held.setdefault(wp, set()).add(wp)
    changed = True
    while changed:
        changed = False
        for wp, row in by.items():
            for dep in row["deps"]:  # type: ignore[union-attr]
                if dep in held:
                    add = held[dep] - held.get(wp, set())
                    if add:
                        held.setdefault(wp, set()).update(add)
                        changed = True
    for wp in list(held):
        waived = WAIVERS.get(wp, set())
        remaining = held[wp] - waived
        if remaining:
            held[wp] = remaining
        else:
            del held[wp]
    return held


def lane_of(row: dict[str, object], landed: set[str]) -> str:
    if row["status"] == "Review" or row["wp"] in landed:
        return "VERIFY"
    return "BUILD"


def topo_key(wp: str, by: dict[str, dict[str, object]]) -> tuple[int, int, str]:
    row = by[wp]
    return (
        PHASE_RANK.get(str(row["phase"]), 9),
        int(row["effort"]) if str(row["effort"]).isdigit() else 9,
        wp,
    )


def partition(
    rows: list[dict[str, object]], by: dict[str, dict[str, object]], unit: set[str]
) -> list[set[str]]:
    """Group items that share a dependency edge or a package, so groups never straddle chats."""
    parent = {w: w for w in unit}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        if a in parent and b in parent:
            parent[find(a)] = find(b)

    pkg_first: dict[str, str] = {}
    for w in unit:
        for dep in by[w]["deps"]:  # type: ignore[union-attr]
            union(w, dep)
        pkg = package_of(by[w])
        if pkg in pkg_first:
            union(w, pkg_first[pkg])
        else:
            pkg_first[pkg] = w
    groups: dict[str, set[str]] = defaultdict(set)
    for w in unit:
        groups[find(w)].add(w)
    return sorted(groups.values(), key=lambda g: (-len(g), min(g)))


def ordered(group: set[str], by: dict[str, dict[str, object]]) -> list[str]:
    remaining = set(group)
    out: list[str] = []
    while remaining:
        ready = [w for w in remaining if not (set(by[w]["deps"]) & remaining)]  # type: ignore[arg-type]
        if not ready:
            raise SystemExit(f"dependency cycle inside group: {sorted(remaining)}")
        nxt = min(ready, key=lambda w: topo_key(w, by))
        out.append(nxt)
        remaining.remove(nxt)
    return out


def item_block(
    n: int,
    chat: int,
    row: dict[str, object],
    lane: str,
    by: dict[str, dict[str, object]],
    chat_items: set[str],
    landed: set[str],
) -> str:
    wp = str(row["wp"])
    pkg = package_of(row)
    recon = bool(row["no_ac"])
    adr = bool(row["adr"])
    deps = []
    for d in row["deps"]:  # type: ignore[union-attr]
        if d in chat_items:
            deps.append(
                f"`{d}` (earlier in this queue; must be DONE/PARTIAL in ledger first)"
            )
        elif d in landed or (d in by and by[d]["status"] == "Review"):  # type: ignore[index]
            deps.append(f"`{d}` (already implemented in repo)")
        else:
            deps.append(f"`{d}` (unknown state: stop and record SKIPPED)")
    reqs = (
        "\n".join(f"  - {r}" for r in row["reqs"][:15])
        or "  - none listed on the board"
    )  # type: ignore[index]
    ac = (
        str(row["ac"])
        or "_None recorded in PLAN-001 §5.4 for this package. Derive them (step 1)._"
    )
    allowed = [
        f"`src/ectt/{pkg}/`",
        f"`tests/{pkg}/`",
        f"`docs/verification/{wp}-analysis.md`",
        f"`docs/glm-night/{CHAT_LOG[chat]}`",
    ]
    if pkg == "spikes":
        allowed[0] = "`spikes/<WP id>/`"
        allowed[1] = "`spikes/<WP id>/tests/`"
    if (
        lane == "VERIFY"
    ):  # documentation only: chat 2 never edits code, so chat 1 cannot collide with it
        allowed = [
            f"`docs/verification/{wp}-analysis.md`",
            f"`docs/glm-night/{CHAT_LOG[chat]}`",
        ]

    lines = [
        f"### {n}. {wp}: {row['title']}",
        "",
        f"- Board: {row['component']} · phase {row['phase']} · effort {row['effort']} person-weeks · status `{row['status']}`",
        f"- Lane: **{lane}**"
        + (" · ADR-sensitive (decision-free part only)" if adr else "")
        + (" · **RECON** (no acceptance criteria recorded)" if recon else ""),
        "- Requirements owned:",
        reqs,
        f"- Acceptance criteria (board): {ac}",
        "- Dependencies: " + ("; ".join(deps) if deps else "none"),
        "- Files you may change: " + ", ".join(allowed),
        "- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = "
        + f"`{wp}`).",
        "",
        "Steps:",
    ]
    step = 1
    if lane == "VERIFY":
        lines += [
            f"{step}. Read the existing verification note and the code/tests named for {wp}.",
            f"{step + 1}. Run those tests. For each requirement above, confirm a real test name exists and passes.",
            f"{step + 2}. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.",
            f"{step + 3}. Write or update `docs/verification/{wp}-analysis.md` (requirement → implementation → test evidence).",
        ]
    else:
        if recon:
            lines.append(
                f"{step}. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for {wp} and the requirement text in SRS-001. Write them into `docs/verification/{wp}-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`."
            )
            step += 1
        lines += [
            f"{step}. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.",
            f"{step + 1}. Write `docs/verification/{wp}-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.",
        ]
        if adr:
            lines.append(
                f"{step + 2}. The item is ADR-sensitive. Implement only the decision-free part. Record each open ADR question in your ledger row. Never choose an option."
            )
    last = step + (3 if lane == "VERIFY" else 2)
    lines += [
        f"{last}. Run the gates (see Gate block below). Commit locally with the message in the Commit block.",
        f"{last + 1}. Append one row to `docs/glm-night/{CHAT_LOG[chat]}`.",
        "",
        "Completion (choose exactly one state in the ledger):",
        "- DONE: all criteria met, gates green, verification note complete.",
        "- PARTIAL: an increment landed and gates are green; list what remains.",
        "- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).",
        "- BLOCKED: a decision or ADR is needed; no code written for the blocked part.",
        "Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.",
        "",
    ]
    return "\n".join(lines)


GATES = """**Gate block (run from your worktree root with `.venv`):**
```
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy src
.venv/Scripts/python.exe design/trace/plan_check.py
.venv/Scripts/python.exe design/trace/trace_check.py
```
All must exit 0 except failures that existed before your change (record them). Do not regenerate `design/trace/*` or the unified plan; those files are owned by the morning merge.
"""


def commit_block(chat: int) -> str:
    return (
        f"**Commit block:** `git add <only your allowed paths>` then "
        f'`git commit -m "[GLM-NIGHT-CHAT{chat}] <WP id>: <one-line summary>"` with the body line '
        "`Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>`. Never `git add -A`. Never push. Never amend."
    )


def shared_block() -> str:
    paths = ", ".join(f"`{p}`" for p in SHARED_PATHS)
    return f"**Shared files (do not edit; report needed changes in your ledger instead):** {paths}."


def queue_header(chat: int, count: int) -> str:
    branch = f"glm-night/chat{chat}"
    wt = f"../wt-chat{chat}"
    return "\n".join(
        [
            f"# Chat {chat} queue ({count} items)",
            "",
            "Work through the items in this order. For each item, read its block, do the lane steps, write one ledger row, commit, then move to the next. Do not revisit finished items.",
            "",
            "## Setup (once, before item 1)",
            "```",
            f"git worktree add {wt} -b {branch} glm-night/20261117",
            f"cd {wt}",
            "python -m venv .venv",
            '.venv/Scripts/python.exe -m pip install -e ".[dev]"',
            "```",
            f"If `{CHAT_LOG[chat]}` does not exist, create it with the header row `| WP | state | commit | tests | notes |` and `|---|---|---|---|---|`.",
            "",
            GATES,
            commit_block(chat),
            "",
            shared_block(),
            "",
            "## Final item",
            f"After the last item, write `docs/glm-night/chat{chat}-summary.md`: counts per state, every PARTIAL/SKIPPED/BLOCKED item with its reason, and the list of shared-file changes you need the owner to make in the morning. Commit it. Then stop.",
            "",
        ]
    )


def main() -> int:
    rows = load_board()
    by = {str(r["wp"]): r for r in rows}
    if len(by) != len(rows):
        print("duplicate WP ids on the board", file=sys.stderr)
        return 1
    landed = tracker_landed_wps()
    held = closure_blocked(by)
    unit = {w for w in by if w not in held}
    # BUILD items form dependency-and-package groups. Groups share no package and no
    # dependency edge, so they can run in separate chats. The largest group is the
    # implementation chain and stays in chat 1. The remaining groups plus every
    # VERIFY item (documentation-only work) go to chat 2.
    build = {w for w in unit if lane_of(by[w], landed) == "BUILD"}
    verify = {w for w in unit if lane_of(by[w], landed) == "VERIFY"}
    groups = partition(rows, by, build)
    chat_groups: dict[int, list[set[str]]] = {1: [groups[0]], 2: groups[1:]}
    chat_of: dict[str, int] = dict.fromkeys(groups[0], 1)
    for g in groups[1:]:
        chat_of.update(dict.fromkeys(g, 2))
    chat_groups[2].append(verify)
    chat_of.update(dict.fromkeys(verify, 2))

    queues: dict[int, list[str]] = {}
    for chat in (1, 2):
        members = {w for g in chat_groups[chat] for w in g}
        # One topological pass over the whole chat, so in-chat dependencies always come first.
        order: list[str] = ordered(members, by)
        queues[chat] = order
        # Ordering check: every in-queue dependency must come earlier in the same queue.
        position = {w: i for i, w in enumerate(order)}
        for w in order:
            for d in by[w]["deps"]:  # type: ignore[union-attr]
                if d in members and position[d] >= position[w]:
                    raise SystemExit(
                        f"ordering violation: {w} before its dependency {d}"
                    )

    # --- validator ---
    problems: list[str] = []
    assigned = Counter()
    for chat in (1, 2):
        assigned.update(queues[chat])
    assigned.update(held.keys())
    for wp in by:
        if assigned[wp] != 1:
            problems.append(f"{wp} assigned {assigned[wp]} times")
    pkgs: dict[int, set[str]] = {1: set(), 2: set()}
    verify_cross = 0
    for chat in (1, 2):
        for w in queues[chat]:
            is_build = w in build
            if is_build:
                pkgs[chat].add(package_of(by[w]))
            for d in by[w]["deps"]:  # type: ignore[union-attr]
                if d in held:
                    if is_build:
                        problems.append(f"{w} (queued) depends on held {d}")
                elif d in chat_of and chat_of[d] != chat:
                    if d in verify:
                        verify_cross += 1  # VERIFY items are already implemented in the repo, so this is satisfied
                    else:
                        problems.append(f"cross-chat dependency {w} -> {d}")
    if pkgs[1] & pkgs[2]:
        problems.append(f"packages shared across chats: {sorted(pkgs[1] & pkgs[2])}")

    # --- write outputs ---
    for chat in (1, 2):
        blocks = []
        for n, w in enumerate(queues[chat], start=1):
            lane = lane_of(by[w], landed)
            blocks.append(
                item_block(n, chat, by[w], lane, by, set(queues[chat]), landed)
            )
        (OUT / f"chat{chat}-queue.md").write_text(
            queue_header(chat, len(queues[chat])) + "\n" + "\n".join(blocks),
            encoding="utf-8",
        )

    held_lines = []
    for w in sorted(held, key=lambda x: topo_key(x, by)):
        why = "; ".join(sorted({EXPLICIT_BLOCKERS[b] for b in held[w]}))
        held_lines.append(f"| {w} | {by[w]['title']} | {why} |")

    lane_counts = Counter(lane_of(by[w], landed) for w in queues[1] + queues[2])
    unblock = Counter()
    for w in held:
        for b in held[w]:
            unblock[b] += 1
    unblock_lines = [
        f"| {b} | {EXPLICIT_BLOCKERS[b]} | {unblock[b]} |"
        for b in sorted(EXPLICIT_BLOCKERS, key=lambda x: -unblock[x])
    ]

    def driver(chat: int) -> str:
        other = 3 - chat
        return "\n".join(
            [
                f"You are Chat {chat} of 2 in an unattended overnight run. Nobody will answer questions, so decide, record, and move on.",
                "",
                f"1. Setup: from the repository root `E:\\projects\\UDS_Simulator\\wt-unit-glm-night`, run the Setup block in `docs/glm-night/chat{chat}-queue.md`. Work only inside `../wt-chat{chat}` on branch `glm-night/chat{chat}`.",
                f"2. Open `docs/glm-night/chat{chat}-queue.md`. Process its items in the printed order. For each item: do its lane steps, run the Gate block, commit with the Commit block, append one ledger row, then go to the next item.",
                "3. Never stop to ask. If a decision, an ADR or an owner answer is needed, record BLOCKED and continue.",
                "4. Never push. Never write to the GitHub board or issues. Never answer D-01 to D-04 or any ADR. Never edit the shared files listed in the queue.",
                "5. Never invent acceptance criteria. Derive them from PLAN-001 §5.4 and SRS-001 or record SKIPPED.",
                f"6. Do not use or edit chat {other}'s worktree or ledger.",
                f"7. When the queue is exhausted, write `docs/glm-night/chat{chat}-summary.md` (the Final item block), commit it, and stop.",
                "",
                "Report at the end: the counts per state and the path of your summary file.",
            ]
        )

    plan = [
        "# Parallel plan: two chats over the GitHub project board (generated)",
        "",
        "Generated by `docs/glm-night/build_parallel_plan.py` from `board-snapshot.json` and the tracker. Regenerate instead of editing.",
        "",
        '## What "completed" means',
        "Every board item reaches a terminal ledger state: DONE, PARTIAL, SKIPPED or BLOCKED. It does not mean all 191 work packages are implemented. Plan_check puts the whole scope at 642 person-weeks, and this plan holds the items that need owner decisions.",
        "",
        "## Counts",
        f"- Board items: {len(by)}",
        f"- Held (owner decision or ADR needed, plus everything downstream): {len(held)}",
        f"- Chat 1 queue: {len(queues[1])} items · Chat 2 queue: {len(queues[2])} items",
        f"- Lanes queued: VERIFY {lane_counts['VERIFY']}, BUILD {lane_counts['BUILD']}",
        f"- Items with no recorded acceptance criteria (RECON): {sum(1 for w in queues[1] + queues[2] if by[w]['no_ac'])}",
        f"- Validator: {'PASS' if not problems else 'FAIL'} ({len(problems)} problems)",
        "",
        "## Split and rules",
        "- Each chat has its own worktree and branch (`glm-night/chat1`, `glm-night/chat2`) off `glm-night/20261117`.",
        "- Work is grouped by dependency edges and shared package. Each package belongs to one chat, so the two chats never create or edit the same `src/ectt/<pkg>/` or `tests/<pkg>/`.",
        "- Build work never depends across chats, so neither chat waits on the other to build.",
        f"- Dependencies on already-implemented items that sit in the other chat's verify lane: {verify_cross} edges. They are satisfied by code already in the repo, so no chat waits.",
        "- Each chat writes only its own ledger (`docs/glm-night/CHAT<N>_LEDGER.md`) and its summary. Nobody edits the tracker, the unified plan or the SRS. The owner reconciles them in the morning.",
        "- Shared-file changes a chat needs are recorded in its summary, not made.",
        "",
        "## Morning merge (owner)",
        "1. Review `chat1-summary.md` and `chat2-summary.md` and the two ledgers.",
        "2. Merge `glm-night/chat1` and `glm-night/chat2` into `glm-night/20261117`. Their file sets are disjoint, so no conflicts are expected. Run the gates.",
        "3. Reconcile `EXEC-PLAN-001-tracker.html` from the ledgers, then run `design/trace/unified_plan_sync.py`.",
        "4. Push only after approval.",
        "",
        "## Held items and what unblocks them",
        "Answering a decision releases the items downstream of it, so the table below shows where the owner's time pays off most.",
        "",
        "| Blocker | Gate | Items held (including the blocker itself) |",
        "|---|---|---|",
        *unblock_lines,
        "",
        "| Held item | Title | Blocked by |",
        "|---|---|---|",
        *held_lines,
        "",
        "## Chat 1 driver prompt (paste into chat 1)",
        "```",
        driver(1),
        "```",
        "",
        "## Chat 2 driver prompt (paste into chat 2)",
        "```",
        driver(2),
        "```",
        "",
        "## Standing rules (both chats)",
        "- Never push. Never write to the GitHub board or issues. Reading is fine.",
        "- Never answer D-01 to D-04 or any ADR. Implement only decision-free parts of ADR-sensitive items.",
        "- Never invent acceptance criteria. Derive them from PLAN-001 §5.4 and SRS-001, or SKIP.",
        "- Do not edit shared files. Do not `git add -A`. Commit per item.",
        "- Tools: use the agent's own file, shell and git tools. Do not depend on any particular harness.",
        "",
        "## Validator",
        f"- Every board item assigned exactly once: {'yes' if not any('assigned' in p for p in problems) else 'NO'}",
        f"- Zero cross-chat dependencies: {'yes' if not any('cross-chat' in p for p in problems) else 'NO'}",
        f"- Packages disjoint across chats: {'yes' if not any('packages shared' in p for p in problems) else 'NO'}",
        f"- No queued item depends on a held item: {'yes' if not any('held' in p for p in problems) else 'NO'}",
    ]
    if problems:
        plan += ["", "### Problems", *[f"- {p}" for p in problems]]
    (OUT / "parallel-plan.md").write_text("\n".join(plan) + "\n", encoding="utf-8")

    print(
        f"items={len(by)} held={len(held)} chat1={len(queues[1])} chat2={len(queues[2])} problems={len(problems)}"
    )
    for p in problems:
        print("PROBLEM:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())

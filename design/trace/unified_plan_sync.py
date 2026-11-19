#!/usr/bin/env python3
"""Regenerate the data-driven sections of EXEC-PLAN-001-unified-execution-plan.md.

Source of truth: the JSON block in EXEC-PLAN-001-tracker.html (<script id="plan-data">).
The Markdown file keeps its hand-written text; only the regions between
`<!-- BEGIN GENERATED: name -->` and `<!-- END GENERATED: name -->` are rewritten.

    python design/trace/unified_plan_sync.py          # rewrite the Markdown
    python design/trace/unified_plan_sync.py --check  # exit 1 if the Markdown is stale

Standard library only. Deterministic: same JSON -> byte-identical Markdown.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "EXEC-PLAN-001-tracker.html"
MD = ROOT / "EXEC-PLAN-001-unified-execution-plan.md"

STATUSES = ["Implemented", "Landed", "In Progress", "Planned", "Blocked"]
SOURCES = ["PLAN-001", "vcast-findings", "BACKLOG", "BACKLOG-RESERVE"]
DONE = {"Implemented", "Landed"}
LANE = {"done": "Done", "queue": "Ready queue", "reserve": "Reserve queue", "scheduled": "Scheduled via TASK", "blocked": "Blocked", "backlog": "Backlog (planned WP)"}


def load() -> dict:
    text = HTML.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="plan-data">\n(.*?)\n</script>', text, re.S)
    if not m:
        sys.exit("plan-data block not found in " + HTML.name)
    return json.loads(m.group(1))


def cell(x: object) -> str:
    return str(x).replace("|", "\\|").replace("\n", " ")


def code(items) -> str:
    items = [i for i in items if i]
    return ", ".join(f"`{i}`" for i in items) if items else "—"


def table(headers: list[str], rows: list[list[object]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


class Model:
    def __init__(self, d: dict):
        self.d = d
        self.tasks = d["tasks"]
        self.by = {t["id"]: t for t in self.tasks}
        self.rev: dict[str, list[str]] = {}
        for t in self.tasks:
            for dep in t["deps"]:
                self.rev.setdefault(dep, []).append(t["id"])

    def deps_met(self, t: dict) -> bool:
        return all(self.by[x]["status"] in DONE for x in t["deps"] if x in self.by)

    def startable(self, t: dict) -> bool:
        return t["lane"] in ("queue", "reserve") and t["status"] == "Planned" and not t["blockedBy"] and self.deps_met(t)

    def downstream(self, tid: str) -> list[str]:
        seen: set[str] = set()
        stack = [tid]
        while stack:
            for y in self.rev.get(stack.pop(), []):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        return sorted(seen, key=lambda x: self.by[x]["seq"])


# ------------------------------------------------------------------ blocks
def b_snapshot(m: Model) -> str:
    meta, T = m.d["meta"], m.tasks
    rows = []
    for src in SOURCES:
        sel = [t for t in T if t["source"] == src]
        rows.append([src] + [sum(t["status"] == s for t in sel) or "·" for s in STATUSES] + [len(sel)])
    rows.append(["**Total**"] + [sum(t["status"] == s for t in T) or "·" for s in STATUSES] + [len(T)])
    reqs = m.d["requirements"]
    alloc = [r for r in reqs if r["wp"]]
    own = Counter(m.by[r["wp"]]["status"] for r in alloc)
    rt = [t for t in T if t["source"] == "vcast-findings"]
    landed = sum(t["status"] == "Landed" for t in rt)
    startable = [t["id"] for t in T if m.startable(t)]
    lines = [
        f"**As of {meta['asOf']}** · HEAD `{meta['head']}` on `{meta['branch']}` ({meta['aheadOfOriginMain']} commits ahead of `origin/main`, {'pushed' if meta['branchPushed'] else '**not pushed**'}).",
        "",
        table(["Source plan"] + STATUSES + ["Total"], rows),
        "",
        f"- **Requirements:** {len(reqs)} in SRS-001; {len(alloc)} allocated to a work package; {len(reqs) - len(alloc)} Future (not allocated); {meta['srs']['elements']} design elements. Allocated requirements by owning-WP status: Implemented {own.get('Implemented', 0)}, Planned {own.get('Planned', 0)}, Blocked {own.get('Blocked', 0)}.",
        f"- **Work packages:** {meta['srs']['packages']} · {meta['srs']['personWeeks']} person-weeks.",
        f"- **Review track (vcast-findings):** {landed} of {len(rt)} landed. Not landed: " + ", ".join(f"`{t['id']}` ({t['status']})" for t in rt if t["status"] != "Landed") + ".",
        f"- **Gates at HEAD:** plan_check — {meta['gates']['planCheck']}. trace_check — {meta['gates']['traceCheck']}.",
        f"- **Tests at HEAD:** {meta['tests']['passed']} passed, {meta['tests']['failed']} failed, {meta['tests']['skipped']} skipped. Failing: " + ", ".join(f"`{x}`" for x in meta["tests"]["failing"]) + " (fixed by `TASK-001`).",
        f"- **Overnight backlog budget:** core queue sums to {meta['backlog']['coreK']:,}k tokens (its header says {meta['backlog']['statedCoreK']:,}k); reserve {meta['backlog']['reserveK']:,}k.",
        f"- **Startable right now:** {', '.join(f'`{x}`' for x in startable) or 'none'} (dependencies met, not blocked).",
        "",
        "**Notes and discrepancies found while consolidating:**",
        "",
    ] + [f"{i}. {n}" for i, n in enumerate(meta["notes"], 1)]
    return "\n".join(lines)


def b_fields(m: Model) -> str:
    return table(["Field", "Meaning"], [[f"`{k}`", v] for k, v in m.d["meta"]["fields"].items()])


def b_overlap(m: Model) -> str:
    rows = []
    for t in m.tasks:
        if t["source"] == "PLAN-001":
            continue
        rel = [x for x in t["related"] if x in m.by]
        if not t["wps"] and not rel:
            continue
        rows.append([f"`{t['id']}`", t["source"], code(t["wps"]), code(rel), code(t["reqs"][:6]) + (" …" if len(t["reqs"]) > 6 else "")])
    return table(["Task", "Source", "Work packages touched", "Related tasks / decisions", "SRS requirements"], rows)


def b_queue(m: Model) -> str:
    rows = []
    for t in m.tasks:
        if t["lane"] not in ("queue", "reserve"):
            continue
        rows.append([t["seq"], f"`{t['id']}`", t["title"], code(t["wps"]), t["est"], code(t["deps"]) , t["status"], "yes" if m.startable(t) else "after deps"])
    return table(["Seq", "ID", "Title", "Delivers WP", "Est.", "Depends on", "Status", "Startable now"], rows)


def b_blocked(m: Model) -> str:
    rows = []
    for t in m.tasks:
        if t["lane"] != "blocked":
            continue
        down = m.downstream(t["id"])
        rows.append([t["seq"], f"`{t['id']}`", t["title"], code(t["blockedBy"]), len(down), (t["notes"] or "—")[:230] + ("…" if len(t["notes"]) > 230 else "")])
    return table(["Seq", "ID", "Title", "Blocked by", "Downstream tasks held", "Why / note"], rows)


def b_backlog(m: Model) -> str:
    wps = [t for t in m.tasks if t["source"] == "PLAN-001" and t["lane"] == "backlog"]
    by_phase = Counter(t["phase"] for t in wps)
    ready = [t for t in wps if m.deps_met(t)]
    out = [
        f"{len(wps)} PLAN-001 work packages are Planned but not yet scheduled into the overnight queue (by start phase: " + ", ".join(f"{p} {n}" for p, n in sorted(by_phase.items())) + "). Their full entries are in §8. They become startable only when a human or `TASK-023` schedules them.",
        "",
        f"Of these, **{len(ready)}** already have every hard dependency satisfied (candidates for `TASK-023`'s ranking):",
        "",
        table(["WP", "Title", "Phase", "Eff.", "Hard deps", "Gate / ADR"], [[f"`{t['id']}`", t["title"], t["phase"], t["est"], code(t["deps"]), code(t["adrs"])] for t in sorted(ready, key=lambda x: (x["phase"], x.get("startWeek", 0), x["id"]))]),
    ]
    return "\n".join(out)


def b_done(m: Model) -> str:
    rows = [[t["seq"], f"`{t['id']}`", t["title"], t["status"], f"`{t['commit']}`" if t["commit"] else "—", t["branch"], t["verifyState"]] for t in m.tasks if t["lane"] == "done"]
    return table(["Seq", "ID", "Title", "Status", "Commit", "Branch", "Verification"], rows)


def b_decisions(m: Model) -> str:
    out = []
    for d in m.d["decisions"]:
        out += [f"### {d['id']} · {d['title']} — **{d['state']}**", "", f"**Question:** {d['question']}", "",
                table(["Option", "Choice", "Consequence"], [[o[0], o[1], o[2]] for o in d["options"]]), "",
                f"- **Priority:** {d['priority']} · **References:** {code(d['refs'])}",
                "- **Gates:** " + "; ".join(d["gates"]),
                f"- **Unblocks:** {code(d['unblocks'])} · **Watch:** {code(d['watch'])}",
                "- **Answer:** _awaiting decision — agents must not answer._", ""]
    out += ["### Other open gates (not in the D-01…D-04 queue)", "", table(["ID", "Title", "State", "Gates"], [[f"`{a['id']}`", a["title"], a["state"], code(a["gates"])] for a in m.d["adrs"]])]
    return "\n".join(out)


def b_prs(m: Model) -> str:
    out = []
    for p in m.d["prs"]:
        out += [f"### {p['id']} · {p['title']}", "",
                f"- **State:** {p['state']} · **Mergeable:** {p['mergeable']} · `{p['branch']}` → `{p['base']}` · {p['url']}",
                f"- **Checks:** {p['ci']}", f"- **What it does:** {p['summary']}", f"- **Related tasks:** {code(p['relatesTo'])} · **Tasks it blocks:** {code(p['gatesTasks']) if p['gatesTasks'] else 'none in the source plans'}",
                f"- **Note:** {p['notes']}", "- **Remaining steps:**"]
        out += [f"  - [{'x' if s[2:3] and s[2] else ' '}] `{s[0]}` {s[1]}" for s in p["remaining"]]
        out.append("")
    return "\n".join(out)


def card(m: Model, t: dict, level: str = "###") -> str:
    deps = code(t["deps"])
    soft = (" · schedule/port: " + code(t["softDeps"])) if t.get("softDeps") else ""
    lines = [
        f"{level} {t['id']} — {t['title']}", "",
        f"- **Status:** {t['status']} · **Lane:** {LANE.get(t['lane'], t['lane'])} · **Seq:** {t['seq']} · **Source:** {t['source']} · **Area:** {t['area']}" + (f" · **Est.:** {t['est']}" if t["est"] else "") + (f" · **Priority:** {t['priority']}" if t["priority"] else "") + (f" · **Phase:** {t['phase']}" if t["phase"] else ""),
        f"- **Dependencies:** {deps}{soft}",
        f"- **Blocking decision / gate:** {code(t['blockedBy'])}" + (f" · watch {code(t['watch'])}" if t["watch"] else ""),
        f"- **SRS requirements:** {code(t['reqs'])}",
        f"- **Work packages:** {code(t['wps'])} · **Related:** {code([x for x in t['related'] if x])}",
        f"- **ADRs:** {code(t['adrs'])} · **PRs:** {code(t['prs'])}",
        f"- **Branch:** `{t['branch']}`" + (f" · **Commit:** `{t['commit']}`" if t["commit"] else ""),
        "- **Files likely touched:** " + (", ".join(f"`{f}`" for f in t["files"]) if t["files"] else "—"),
        "- **Acceptance criteria:**",
    ]
    lines += [f"  {i}. {a}" for i, a in enumerate(t["acceptance"], 1)]
    lines.append(f"- **Verification** ({t['verifyState']}):")
    for v in t["verify"]:
        if "G-FULL" in v:
            lines.append("  - full gate **G-FULL** (see §5.4)")
        elif "G-GATES" in v:
            lines.append("  - design gates **G-GATES** (plan_check + trace_check)")
        else:
            lines.append(f"  - `{v}`")
    if t["notes"]:
        lines.append(f"- **Notes:** {t['notes']}")
    return "\n".join(lines) + "\n"


def b_cards(m: Model) -> str:
    groups = [
        ("7.1 Ready queue — core overnight backlog (BACKLOG TASK-000 … TASK-024)", lambda t: t["source"] == "BACKLOG" and t["lane"] == "queue"),
        ("7.2 Reserve queue (TASK-101 … TASK-108; only after TASK-024)", lambda t: t["source"] == "BACKLOG-RESERVE"),
        ("7.3 Blocked backlog task", lambda t: t["source"] == "BACKLOG" and t["lane"] == "blocked"),
        ("7.4 vcast-findings tasks not yet landed (T-01, T-02, T-04, T-05, T-06, T-14)", lambda t: t["source"] == "vcast-findings" and t["status"] != "Landed"),
        ("7.5 Implemented work packages (PLAN-001)", lambda t: t["source"] == "PLAN-001" and t["status"] == "Implemented"),
    ]
    out = []
    for title, pred in groups:
        out += [f"## {title}", ""]
        out += [card(m, t) for t in m.tasks if pred(t)]
    out += ["## 7.6 Landed vcast-findings tasks (compact)", "",
            table(["ID", "Title", "Commit", "Branch", "SRS requirements", "WPs"], [[f"`{t['id']}`", t["title"], f"`{t['commit']}`", t["branch"], code(t["reqs"][:5]) + (" …" if len(t["reqs"]) > 5 else ""), code(t["wps"])] for t in m.tasks if t["source"] == "vcast-findings" and t["status"] == "Landed"])]
    return "\n".join(out)


def b_register(m: Model) -> str:
    out = []
    for t in m.tasks:
        if t["source"] != "PLAN-001" or t["status"] == "Implemented":
            continue
        head = f"#### {t['id']} — {t['title']}"
        meta = f"{t['status']} · {t['phase']} · {t['est']} · seq {t['seq']} · {LANE.get(t['lane'], t['lane'])} · hard deps met: {'yes' if m.deps_met(t) else 'no'}"
        deps = f"deps {code(t['deps'])}" + (f" · schedule/port {code(t['softDeps'])}" if t["softDeps"] else "")
        gate = f"blocked by {code(t['blockedBy'])}" if t["blockedBy"] else "no decision block"
        extra = f" · watch {code(t['watch'])}" if t["watch"] else ""
        sched = f" · delivered by {code([t['scheduledVia']])}" if t.get("scheduledVia") else ""
        out += [head, "",
                f"- {meta}",
                f"- {deps} · {gate}{extra}{sched} · ADR {code(t['adrs'])} · PR {code(t['prs'])}",
                f"- Reqs: {code(t['reqs'])}",
                f"- Accept: {' '.join(t['acceptance'])}",
                f"- Files: {code(t['files'])} · Branch: `{t['branch']}`",
                "- Verify: " + "; ".join(("G-FULL" if "G-FULL" in v else f"`{v}`") for v in t["verify"])]
        if t["notes"]:
            out.append(f"- Notes: {t['notes']}")
        out.append("")
    return "\n".join(out)


BLOCKS = {"snapshot": b_snapshot, "fields": b_fields, "overlap": b_overlap, "queue": b_queue, "blocked": b_blocked, "backlog": b_backlog,
          "done": b_done, "decisions": b_decisions, "prs": b_prs, "cards": b_cards, "register": b_register}


def render(text: str, m: Model) -> str:
    for name, fn in BLOCKS.items():
        pat = re.compile(rf"(<!-- BEGIN GENERATED: {name} -->\n).*?(\n<!-- END GENERATED: {name} -->)", re.S)
        if not pat.search(text):
            sys.exit(f"marker for block '{name}' missing in {MD.name}")
        text = pat.sub(lambda mo: mo.group(1) + fn(m).rstrip("\n") + mo.group(2), text)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="exit 1 if the Markdown differs from what the JSON would generate")
    args = ap.parse_args()
    m = Model(load())
    old = MD.read_text(encoding="utf-8")
    new = render(old, m)
    if args.check:
        if new != old:
            print(f"STALE: {MD.name} does not match {HTML.name}; run python design/trace/unified_plan_sync.py")
            return 1
        print(f"OK: {MD.name} is in sync with {HTML.name} ({len(m.tasks)} tasks)")
        return 0
    MD.write_text(new, encoding="utf-8", newline="\n")
    print(f"wrote {MD.name} ({len(m.tasks)} tasks, {len(new.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

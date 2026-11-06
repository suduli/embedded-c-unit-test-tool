#!/usr/bin/env python3
"""Check PLAN-001 allocation/dependency closure; --write refreshes derived tables.

Sources: SRS requirement lines, PLAN section 5.5 work-package rows, and the
authored technique choices in Appendix A. No design trace artifacts are written.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "PLAN-001-specification-analysis-and-work-breakdown.md"
SRS = ROOT / "SRS-001-requirements.md"
REQ = re.compile(r"^\*\*(TOOL-[A-Z]{3}-\d{3})\*\* \*\(([MSCF]), (P[1-4]|—), ([TADI]|—)\)\*", re.M)
TECH = {"I": "INSPECTION CHECKLIST", "A": "ANALYSIS ARGUMENT", "D": "SCENARIO (demonstration)", "—": "— (deferred)"}


def table(headers: list[str], rows: list[list[object]]) -> str:
    return "\n".join(["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)] + ["| " + " | ".join(map(str, row)) + " |" for row in rows])


def replace_section(text: str, heading: str, content: str) -> str:
    start = text.index(heading) + len(heading)
    end = re.search(r"^#{2,3} ", text[start:], re.M)
    stop = start + end.start() if end else len(text)
    return text[:start] + "\n\n" + content.strip() + "\n\n" + text[stop:]


def render(text: str, srs: str) -> tuple[str, list[str], str]:
    matches = REQ.findall(srs)
    reqs = {rid: (pri, phase, ver) for rid, pri, phase, ver in matches}
    errors = []
    if len(matches) != len(reqs):
        errors.append("duplicate SRS requirement identifiers")
    if len(re.findall(r"^\*\*TOOL-", srs, re.M)) != len(matches):
        errors.append("malformed SRS requirement line")
    source = text.split("### 5.5 The work package register", 1)[1].split("## 6.", 1)[0]
    packages = {}
    for line in source.splitlines():
        if not line.startswith("| `WP-"):
            continue
        fields = [field.strip() for field in line.strip("|").split("|")]
        wid, capability, comp, phase, effort, held, deps, adr = fields
        wid = wid.strip("`")
        if wid in packages:
            errors.append(f"duplicate work package {wid}")
        packages[wid] = dict(capability=capability, comp=comp, phase=phase, effort=int(effort.rstrip("w")), reqs=re.findall(r"[A-Z]{3}-\d{3}", held), deps=deps.split() if deps != "—" else [], adr=adr)
    allocation = Counter("TOOL-" + rid for p in packages.values() for rid in p["reqs"])
    expected = {rid for rid, attr in reqs.items() if attr[0] != "F"}
    for rid in sorted(expected | set(allocation)):
        if allocation[rid] != (1 if rid in expected else 0):
            errors.append(f"{rid}: expected {'1' if rid in expected else '0'} allocation, got {allocation[rid]}")
    for wid, package in packages.items():
        for rid in package["reqs"]:
            attr = reqs.get("TOOL-" + rid)
            if attr and attr[1] != "—" and package["phase"] > attr[1]:
                errors.append(f"{wid} starts after {rid} deadline")
        for dep in package["deps"]:
            target = "WP-" + dep.lstrip("~^")
            if target not in packages:
                errors.append(f"{wid}: unresolved {target}")
            elif packages[target]["phase"] > package["phase"]:
                errors.append(f"{wid}: later-phase prerequisite {target}")
    finish, parent, visiting = {}, {}, set()

    def schedule(wid: str) -> int:
        if wid in finish:
            return finish[wid]
        if wid in visiting:
            raise ValueError(f"dependency cycle at {wid}")
        visiting.add(wid)
        deps = ["WP-" + dep.lstrip("~^") for dep in packages[wid]["deps"] if "WP-" + dep.lstrip("~^") in packages]
        parent[wid] = max(deps, key=schedule) if deps else None
        finish[wid] = (schedule(parent[wid]) if parent[wid] else 0) + packages[wid]["effort"]
        visiting.remove(wid)
        return finish[wid]

    try:
        for wid in packages:
            schedule(wid)
    except ValueError as exc:
        errors.append(str(exc))
    if errors:
        return text, errors, ""
    owner = {"TOOL-" + rid: wid for wid, p in packages.items() for rid in p["reqs"]}
    authored = {}
    for line in text.split("## Appendix A", 1)[1].splitlines():
        if line.startswith("| `TOOL-"):
            fields = [f.strip() for f in line.strip("|").split("|")]
            authored[fields[0].strip("`")] = fields[-1]
    techniques = {}
    for rid, (_, _, ver) in reqs.items():
        techniques[rid] = TECH.get(ver, authored.get(rid, "EQUIVALENCE PARTITIONING"))
        if ver == "T" and techniques[rid] in TECH.values():
            techniques[rid] = "EQUIVALENCE PARTITIONING"
    total = len(reqs)
    attr_counts = [Counter(a[n] for a in reqs.values()) for n in range(3)]
    overview = f"{total} requirements across {len({r.split('-')[1] for r in reqs})} categories, counted directly from SRS-001. These figures describe specified scope, not implementation or executed verification.\n\n"
    overview += table(["Attribute", "Distribution"], [["Priority", " · ".join(f"{k} {attr_counts[0][k]}" for k in "MSCF")], ["Phase", " · ".join(f"{k} {attr_counts[1][k]}" for k in ["P1", "P2", "P3", "P4", "—"])], ["Verification", " · ".join(f"{k} {attr_counts[2][k]}" for k in ["T", "I", "D", "A", "—"])]])
    text = replace_section(text, "## 2. The specification at a glance", overview)
    cats = []
    for cat in sorted({r.split('-')[1] for r in reqs}):
        values = [a for r, a in reqs.items() if r.split('-')[1] == cat]
        cats.append([cat, len(values)] + [sum(a[0] == k for a in values) for k in "MSCF"] + [sum(a[1] == k for a in values) for k in ["P1", "P2", "P3", "P4"]] + [sum(a[2] == k for a in values) for k in "TIDA"])
    text = replace_section(text, "### 2.1 Requirement load by category", table(["Cat", "Total", "M", "S", "C", "F", "P1", "P2", "P3", "P4", "T", "I", "D", "A"], cats))
    phase_rows = []
    for phase in ["P0", "P1", "P2", "P3", "P4"]:
        selected = [p for p in packages.values() if p["phase"] == phase]
        phase_rows.append([phase, len(selected), sum(len(p["reqs"]) for p in selected), sum(p["effort"] for p in selected), max((finish[w] for w, p in packages.items() if p["phase"] <= phase), default=0)])
    effort = sum(p["effort"] for p in packages.values())
    duration = max(finish.values())
    phase_rows.append(["Total", len(packages), len(expected), effort, duration])
    text = replace_section(text, "### 5.2 Phase rollup and calendar", table(["Package start phase", "Work packages", "Requirements owned", "Effort (person-weeks)", "Dependency lower bound (weeks)"], phase_rows) + f"\n\nRows count requirements by their owning package's start phase; SRS delivery-phase counts appear in §7.3. Early-start packages can own later requirements. Historical 2026-08-27 estimate: 183 packages including spikes, 622 person-weeks, 52-week unconstrained path. Current revision adds {effort - 622} person-weeks in bounded packages. Estimates remain planning assumptions. Dependency lower bounds include all edge types, assume unlimited resources and allow phases to overlap; they are not staffed delivery dates. Sequential release gates, resource contention, integration and rework can lengthen them. No exact staffing level follows from effort divided by duration.")
    path = []
    wid = max(finish, key=finish.get)
    while wid:
        path.append(wid)
        wid = parent[wid]
    path.reverse()
    text = replace_section(text, "### 5.3 The critical path", table(["WP", "Start phase", "Effort", "Earliest start week", "Capability"], [[f"`{w}`", packages[w]["phase"], str(packages[w]["effort"]) + "w", finish[w] - packages[w]["effort"], packages[w]["capability"]] for w in path]) + "\n\nThis is one longest path under the §5.2 assumptions. The host MVP path remains CORE-01 → PRJ-01 → ING-01 → ANA-01 → ANA-02 → ANA-04 → GEN-01 → BLD-01 → EXH-01 → COV-01 → COV-02 → REP-02 (46 weeks). ANA-01/02/04 and GEN-01 are therefore on that path; a fork could affect its duration. ADR-006's accepted build-fresh decision avoids a fork; its gross effort-saving estimate must not be read as a calendar saving. Any alternative requires a new dependency schedule, including adaptation and integration costs.")
    for match in list(re.finditer(r"(#### [^\n]+\n\n)(\d+ work packages · \d+ requirements · \d+ person-weeks)", text))[::-1]:
        start = match.end()
        end_match = re.search(r"^#### |^## 6\.", text[start:], re.M)
        end = start + end_match.start() if end_match else len(text)
        ids = re.findall(r"^\| `(WP-[A-Z]+-\d+)`", text[start:end], re.M)
        new = f"{len(ids)} work packages · {sum(len(packages[w]['reqs']) for w in ids)} requirements · {sum(packages[w]['effort'] for w in ids)} person-weeks"
        text = text[:match.start(2)] + new + text[match.end(2):]
    counts = Counter(techniques.values())
    text = replace_section(text, "### 6.2 Technique distribution", table(["Technique", "Requirements", "Share"], [[k, v, f"{v / total:.1%}"] for k, v in sorted(counts.items(), key=lambda item: (-item[1], item[0]))] + [["Total", total, "100%"]]) + "\n\nTechnique choices are planning inputs, not test executions. Inspection and analysis retain explicit review deliverables.")
    text = replace_section(text, "### 6.3 Verification method reconciliation", "Appendix A follows the current SRS verification method: I → inspection, A → analysis, D → demonstration; T uses an authored black-box test technique. The earlier COV-150, CBT-040, NFR-050 and COV-100 method concerns are resolved in SRS-001. Changes in method require corresponding technique review; this table is no evidence that a verification activity has run.\n\n" + table(["Method", "Requirements"], [[k, attr_counts[2][k]] for k in ["T", "I", "D", "A", "—"]]))
    audit = table(["Check", "Result"], [["SRS unique IDs", total], ["Non-Future IDs", len(expected)], ["Primary allocation entries", sum(allocation.values())], ["Distinct allocated IDs", len(allocation)], ["Orphans / duplicate owners / allocated Future IDs", "0 / 0 / 0"]])
    audit += "\n\nThe allocation check uses current SRS and §5.5 directly; the separately generated design matrix must pass trace_check.py before design allocation completeness is claimed. A primary package coordinates acceptance; collaborators do not create a second primary allocation.\n\n" + table(["Requirement", "Primary WP", "Collaborating package / acceptance"], [["COV-060", "WP-COV-05", "CORE-04 supplies provenance"], ["EXE-010", "WP-EXH-01", "BLD-01 supplies build orchestration"], ["MIG-060", "WP-REP-12", "TCM-06 exports test cases; REP-12 exports results; reconstruct both in an independent reader"], ["PRJ-050", "WP-CORE-01", "PRJ-02 applies project editing contract"], ["UIX-320", "WP-PRJ-01", "CORE-01 enforces source/output boundary"]])
    text = replace_section(text, "### 7.1 Requirement allocation", audit)
    edge_counts = Counter("port" if dep.startswith("^") else "schedule" if dep.startswith("~") else "code" for p in packages.values() for dep in p["deps"])
    text = replace_section(text, "### 7.2 Structural audit of the breakdown", table(["Check", "Result"], [["Work packages (including spikes)", len(packages)], ["Dependency edges", sum(edge_counts.values())], ["Code / port-mediated / schedule-only", f"{edge_counts['code']} / {edge_counts['port']} / {edge_counts['schedule']}"], ["Unresolved dependencies / cycles", "0 / 0"], ["Package later than owned requirement / prerequisite later than package phase", "0 / 0"]]) + "\n\nThese are work-plan checks. Source-level layer enforcement remains the responsibility of the design trace checker and architectural review; this checker does not infer code imports from schedule edges.")
    phase_counts = []
    for pri in "MSCF":
        phase_counts.append([pri] + [sum(a[0] == pri and a[1] == phase for a in reqs.values()) for phase in ["P1", "P2", "P3", "P4", "—"]] + [attr_counts[0][pri]])
    phase_counts.append(["Total"] + [attr_counts[1][phase] for phase in ["P1", "P2", "P3", "P4", "—"]] + [total])
    text = replace_section(text, "### 7.3 Coverage by phase and priority", table(["Priority", "P1", "P2", "P3", "P4", "Deferred", "Total"], phase_counts) + "\n\nP1–P3 belong to v1.0; P4 belongs to v1.1. M is mandatory within the assigned release; Future is outside this roadmap.")
    appendix = table(["Requirement", "Pri", "Phase", "V", "Work package", "Test design technique"], [[f"`{rid}`", *reqs[rid], f"`{owner[rid]}`" if rid in owner else "— (Future, not allocated)", techniques[rid]] for rid in sorted(reqs)])
    text = text.split("## Appendix A — Requirement index", 1)[0] + "## Appendix A — Requirement index\n\nGenerated attributes and primary owners from SRS-001 and §5.5. Technique choices are authored planning inputs, preserved for test requirements and aligned to non-test verification methods.\n\n" + appendix + "\n\n---\n\n*Refresh: `.venv/Scripts/python.exe design/trace/plan_check.py --write`; verify without changes by omitting `--write`. This does not generate design trace artifacts.*\n"
    text = re.sub(r"\*\*Covers:\*\* all \d+ SRS-001 requirements", f"**Covers:** all {total} SRS-001 requirements", text)
    return text, [], f"{total} requirements; {len(expected)} unique primary allocations; {len(packages)} packages; {effort} person-weeks; dependency lower bound {duration} weeks"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    original = PLAN.read_text(encoding="utf-8")
    rendered, errors, summary = render(original, SRS.read_text(encoding="utf-8"))
    if errors:
        print("\n".join(errors))
        return 1
    if args.write:
        PLAN.write_text(rendered, encoding="utf-8", newline="\n")
    elif rendered != original:
        print("derived PLAN tables are stale; run with --write")
        return 1
    print("PLAN check passed: " + summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the design element register against SRS-001.

The register (design/trace/design-elements.yaml) allocates every SRS
requirement to a design element. This script is the gate that keeps the two
documents honest: it fails when a requirement is unallocated, when a design
element points at a requirement that does not exist, or when the component
dependency graph violates the layering rule.

Usage:
    python3 design/trace/trace_check.py [options]

Options:
    --srs PATH          SRS document           (default: SRS-001-requirements.md)
    --model PATH        Design element register(default: design/trace/design-elements.yaml)
    --emit-matrix PATH  Write the requirement -> design CSV matrix
    --emit-json PATH    Write the full trace graph as JSON
    --quiet             Suppress the coverage summary; print findings only

Exit status:
    0  no errors
    1  one or more errors
    2  could not run (missing file, unparseable model)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment problem, not a finding
    sys.stderr.write("error: PyYAML is required (pip install pyyaml)\n")
    raise SystemExit(2)

REPO_ROOT = Path(__file__).resolve().parents[2]

# **TOOL-ING-010** *(M, P1, T)* — ...
REQ_RE = re.compile(
    r"^\*\*(?P<id>TOOL-[A-Z]{3}-\d{3})\*\*\s+"
    r"\*\((?P<priority>[MSCF]),\s*(?P<phase>P[1-4]|—),\s*(?P<verification>[TADI]|—)\)\*"
    r"\s*—\s*(?P<text>.*)$"
)
ELEMENT_ID_RE = re.compile(r"^DSN-(?P<comp>[A-Z]{3,4})-(?P<num>\d{3})$")
COMPONENT_ID_RE = re.compile(r"^CMP-(?P<comp>[A-Z]{3,4})$")

# Priorities that need not be allocated to a design element.
UNALLOCATED_PRIORITIES = {"F"}


class Findings:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def load_requirements(path: Path, findings: Findings) -> dict[str, dict]:
    reqs: dict[str, dict] = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = REQ_RE.match(line.strip())
        if not m:
            continue
        rid = m.group("id")
        if rid in reqs:
            findings.error(
                f"{path.name}:{lineno}: duplicate requirement id {rid} "
                f"(first seen at line {reqs[rid]['line']})"
            )
            continue
        reqs[rid] = {
            "id": rid,
            "category": rid.split("-")[1],
            "priority": m.group("priority"),
            "phase": m.group("phase"),
            "verification": m.group("verification"),
            "text": m.group("text").strip(),
            "line": lineno,
        }
    if not reqs:
        findings.error(f"{path}: no requirements matched the expected format")
    return reqs


def load_model(path: Path, findings: Findings) -> dict:
    try:
        model = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        sys.stderr.write(f"error: {path}: {exc}\n")
        raise SystemExit(2)
    if not isinstance(model, dict) or "components" not in model:
        sys.stderr.write(f"error: {path}: not a design element register\n")
        raise SystemExit(2)
    return model


def check_structure(model: dict, reqs: dict[str, dict], findings: Findings) -> dict:
    """Validate ids, allocation, and the component graph. Returns an index."""
    layer_ids = [layer["id"] for layer in model.get("layers", [])]
    layer_index = {lid: i for i, lid in enumerate(layer_ids)}
    cross_cutting = layer_ids[-1] if layer_ids else None

    components: dict[str, dict] = {}
    elements: dict[str, dict] = {}
    allocation: dict[str, list[str]] = defaultdict(list)

    for comp in model["components"]:
        cid = comp["id"]
        cm = COMPONENT_ID_RE.match(cid)
        if not cm:
            findings.error(f"component id {cid!r} does not match CMP-<CODE>")
            continue
        if cid in components:
            findings.error(f"duplicate component id {cid}")
            continue
        if comp.get("layer") not in layer_index:
            findings.error(f"{cid}: unknown layer {comp.get('layer')!r}")
        components[cid] = comp

        for el in comp.get("elements", []):
            eid = el["id"]
            em = ELEMENT_ID_RE.match(eid)
            if not em:
                findings.error(f"{cid}: element id {eid!r} does not match DSN-<CODE>-<NNN>")
                continue
            if em.group("comp") != cm.group("comp"):
                findings.error(
                    f"{eid}: element code {em.group('comp')!r} does not match "
                    f"its component {cid}"
                )
            if eid in elements:
                findings.error(f"duplicate design element id {eid}")
                continue
            el = dict(el, component=cid, layer=comp.get("layer"))
            elements[eid] = el

            satisfies = el.get("satisfies") or []
            if not satisfies and not el.get("derived"):
                findings.error(
                    f"{eid}: no `satisfies` and not marked `derived: true` — "
                    f"an element must either discharge a requirement or say why it exists"
                )
            if satisfies and el.get("derived"):
                findings.error(f"{eid}: marked `derived` but also allocates requirements")
            if el.get("derived") and not el.get("rationale"):
                findings.error(f"{eid}: derived element needs a `rationale`")

            for rid in satisfies:
                if rid not in reqs:
                    findings.error(f"{eid}: satisfies unknown requirement {rid}")
                    continue
                if reqs[rid]["priority"] in UNALLOCATED_PRIORITIES:
                    findings.error(
                        f"{eid}: allocates {rid}, which is priority "
                        f"{reqs[rid]['priority']} (out of v1.0 scope)"
                    )
                allocation[rid].append(eid)

    # refines targets
    for eid, el in elements.items():
        for target in el.get("refines") or []:
            if target not in elements:
                findings.error(f"{eid}: refines unknown design element {target}")

    # component graph: dependencies, layering, cycles
    for cid, comp in components.items():
        for dep in comp.get("depends_on") or []:
            if dep not in components:
                findings.error(f"{cid}: depends_on unknown component {dep}")
                continue
            src, dst = comp.get("layer"), components[dep].get("layer")
            if src in layer_index and dst in layer_index:
                if layer_index[dst] > layer_index[src] and dst != cross_cutting:
                    findings.error(
                        f"{cid} ({src}) depends on {dep} ({dst}): upward dependency. "
                        f"Only the cross-cutting layer {cross_cutting} may be depended "
                        f"on from below."
                    )

    for cycle in find_cycles(components):
        findings.error("dependency cycle: " + " -> ".join(cycle))

    # unallocated requirements
    for rid, req in sorted(reqs.items()):
        if req["priority"] in UNALLOCATED_PRIORITIES:
            continue
        if rid not in allocation:
            findings.error(
                f"{rid} ({req['priority']}, {req['phase']}) is not allocated to any "
                f"design element"
            )

    return {
        "components": components,
        "elements": elements,
        "allocation": dict(allocation),
        "layer_ids": layer_ids,
    }


def find_cycles(components: dict[str, dict]) -> list[list[str]]:
    """Return simple cycles in the depends_on graph (one representative each)."""
    cycles: list[list[str]] = []
    seen_edges: set[tuple[str, ...]] = set()
    colour: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> None:
        colour[node] = 1
        stack.append(node)
        for dep in components.get(node, {}).get("depends_on") or []:
            if dep not in components:
                continue
            if colour.get(dep, 0) == 1:
                cycle = stack[stack.index(dep):] + [dep]
                key = tuple(sorted(cycle))
                if key not in seen_edges:
                    seen_edges.add(key)
                    cycles.append(cycle)
            elif colour.get(dep, 0) == 0:
                visit(dep)
        stack.pop()
        colour[node] = 2

    for cid in sorted(components):
        if colour.get(cid, 0) == 0:
            visit(cid)
    return cycles


def summarise(reqs: dict[str, dict], index: dict) -> str:
    allocation = index["allocation"]
    in_scope = {r: v for r, v in reqs.items() if v["priority"] not in UNALLOCATED_PRIORITIES}

    def table(title: str, key: str, order: list[str]) -> list[str]:
        total = Counter(v[key] for v in in_scope.values())
        done = Counter(v[key] for r, v in in_scope.items() if r in allocation)
        rows = [f"  {title}"]
        for k in order:
            if not total[k]:
                continue
            rows.append(
                f"    {k:<5} {done[k]:>4} / {total[k]:<4} "
                f"{'ok' if done[k] == total[k] else 'GAP'}"
            )
        return rows

    lines = [
        "",
        "Requirement allocation",
        f"  SRS requirements            {len(reqs)}",
        f"  out of v1.0 scope (F)       {len(reqs) - len(in_scope)}",
        f"  in scope                    {len(in_scope)}",
        f"  allocated                   {sum(1 for r in in_scope if r in allocation)}",
        f"  design elements             {len(index['elements'])}",
        f"  derived (no requirement)    "
        f"{sum(1 for e in index['elements'].values() if e.get('derived'))}",
        f"  components                  {len(index['components'])}",
        "",
    ]
    lines += table("By priority", "priority", ["M", "S", "C"])
    lines.append("")
    lines += table("By phase", "phase", ["P1", "P2", "P3", "P4"])
    lines.append("")
    lines.append("  By category")
    cats = sorted({v["category"] for v in in_scope.values()})
    for cat in cats:
        tot = sum(1 for v in in_scope.values() if v["category"] == cat)
        got = sum(1 for r, v in in_scope.items() if v["category"] == cat and r in allocation)
        flag = "ok" if got == tot else "GAP"
        lines.append(f"    {cat:<5} {got:>4} / {tot:<4} {flag}")
    lines.append("")
    return "\n".join(lines)


def emit_matrix(path: Path, reqs: dict[str, dict], index: dict) -> None:
    allocation = index["allocation"]
    elements = index["elements"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(
            ["requirement", "priority", "phase", "verification",
             "components", "design_elements", "status"]
        )
        for rid in sorted(reqs):
            req = reqs[rid]
            els = sorted(allocation.get(rid, []))
            comps = sorted({elements[e]["component"] for e in els})
            if req["priority"] in UNALLOCATED_PRIORITIES:
                status = "out-of-scope"
            elif els:
                status = "allocated"
            else:
                status = "UNALLOCATED"
            w.writerow(
                [rid, req["priority"], req["phase"], req["verification"],
                 " ".join(comps), " ".join(els), status]
            )


def emit_json(path: Path, reqs: dict[str, dict], index: dict, model: dict) -> None:
    elements = index["elements"]
    payload = {
        "document": model.get("document", {}),
        "generated_from": {"requirements": len(reqs), "elements": len(elements)},
        "requirements": {
            rid: {
                **{k: v for k, v in req.items() if k != "line"},
                "satisfied_by": sorted(index["allocation"].get(rid, [])),
            }
            for rid, req in sorted(reqs.items())
        },
        "elements": {
            eid: {
                "title": el.get("title"),
                "component": el["component"],
                "layer": el.get("layer"),
                "satisfies": sorted(el.get("satisfies") or []),
                "refines": sorted(el.get("refines") or []),
                "derived": bool(el.get("derived")),
                "verification": el.get("verification"),
                "open": el.get("open"),
            }
            for eid, el in sorted(elements.items())
        },
        "components": {
            cid: {
                "name": c.get("name"),
                "layer": c.get("layer"),
                "depends_on": sorted(c.get("depends_on") or []),
                "elements": sorted(e["id"] for e in c.get("elements", [])),
            }
            for cid, c in sorted(index["components"].items())
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--srs", type=Path, default=REPO_ROOT / "SRS-001-requirements.md")
    ap.add_argument("--model", type=Path,
                    default=REPO_ROOT / "design" / "trace" / "design-elements.yaml")
    ap.add_argument("--emit-matrix", type=Path)
    ap.add_argument("--emit-json", type=Path)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    for p in (args.srs, args.model):
        if not p.is_file():
            sys.stderr.write(f"error: no such file: {p}\n")
            return 2

    findings = Findings()
    reqs = load_requirements(args.srs, findings)
    model = load_model(args.model, findings)
    index = check_structure(model, reqs, findings)

    if args.emit_matrix:
        emit_matrix(args.emit_matrix, reqs, index)
        print(f"wrote {args.emit_matrix.relative_to(REPO_ROOT) if args.emit_matrix.is_absolute() and REPO_ROOT in args.emit_matrix.parents else args.emit_matrix}")
    if args.emit_json:
        emit_json(args.emit_json, reqs, index, model)
        print(f"wrote {args.emit_json}")

    if not args.quiet:
        print(summarise(reqs, index))

    for w in findings.warnings:
        print(f"warning: {w}")
    for e in findings.errors:
        print(f"error: {e}")

    if findings.errors:
        print(f"\nFAIL: {len(findings.errors)} error(s)")
        return 1
    print("OK: every in-scope requirement is allocated and the design graph is well formed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the design element register against SRS-001.

The register (design/trace/design-elements.yaml) allocates every SRS
requirement to a design element. This script is the gate that keeps the two
documents honest: it fails when a requirement is unallocated, when a design
element points at a requirement that does not exist, or when the component
dependency graph violates the layering rule.

Its value is entirely in not having false negatives. A gate that passes when it
should fail is worse than no gate, so the script is deliberately suspicious:
it refuses to trust its own parse of the SRS (see `REQ_SENTINEL` and
`requirement_count`), it validates the shape of the register before reading it,
and it never writes an artifact from a run that found errors.

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
    2  could not run (missing file, unparseable or malformed model, internal fault)
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment problem, not a finding
    sys.stderr.write("error: PyYAML is required (pip install pyyaml)\n")
    raise SystemExit(2)

_HERE = Path(__file__).resolve()
REPO_ROOT = _HERE.parents[2] if len(_HERE.parents) > 2 else _HERE.parent

# The strict form every requirement must take:
#   **TOOL-ING-010** *(M, P1, T)* — text
REQ_RE = re.compile(
    r"^\*\*(?P<id>TOOL-[A-Z]{3}-\d{3})\*\*\s+"
    r"\*\((?P<priority>[MSCF]),\s*(?P<phase>P[1-4]|—),\s*(?P<verification>[TADI]|—)\)\*"
    r"\s*—\s*(?P<text>.*)$"
)

# Deliberately loose: anything that *looks* like a requirement line. A line that
# trips this but fails REQ_RE is a requirement the strict parser would silently
# skip, which is the single most dangerous failure mode this script has —
# an unparsed requirement is an unchecked requirement.
REQ_SENTINEL = re.compile(r"^[\s>*_`+\-]*(TOOL-[A-Z]{2,6}-\d{2,4})", re.IGNORECASE)

ELEMENT_ID_RE = re.compile(r"^DSN-(?P<comp>[A-Z]{3,4})-(?P<num>\d{3})$")
COMPONENT_ID_RE = re.compile(r"^CMP-(?P<comp>[A-Z]{3,4})$")

# Priorities that need not be allocated to a design element.
UNALLOCATED_PRIORITIES = {"F"}

# SRS-001 §2.2 verification methods.
VERIFICATION_METHODS = {"T", "A", "D", "I"}


class Fatal(Exception):
    """Cannot run at all. Maps to exit 2."""


class Findings:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Fatal(f"{path}: {exc}") from exc


def as_list(value, what: str, findings: Findings) -> list:
    """Coerce a YAML field to a list, reporting shape errors as findings.

    A bare string is the common slip (`satisfies: TOOL-X` instead of
    `satisfies: [TOOL-X]`); iterating it character by character would produce a
    dozen nonsense errors instead of one useful one.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    findings.error(f"{what}: expected a list, got {type(value).__name__}")
    return []


def as_str(value, what: str, findings: Findings) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    findings.error(f"{what}: expected a string, got {type(value).__name__}")
    return None


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------

def load_requirements(path: Path, findings: Findings) -> dict[str, dict]:
    reqs: dict[str, dict] = {}
    sentinel_hits = 0
    for lineno, raw in enumerate(read_text(path).splitlines(), 1):
        line = raw.strip()
        m = REQ_RE.match(line)
        if not m:
            s = REQ_SENTINEL.match(line)
            # Ignore prose cross-references: a real requirement line starts with
            # the id, a reference has it mid-sentence. The sentinel already
            # anchors at start-of-line, so anything it catches is claiming to be
            # a definition.
            if s and not line.startswith("|"):
                sentinel_hits += 1
                findings.error(
                    f"{path.name}:{lineno}: line looks like requirement "
                    f"{s.group(1)} but does not match the required form "
                    f"`**TOOL-XXX-NNN** *(P, Pn, V)* — text`. An unparsed "
                    f"requirement would be silently unchecked."
                )
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
        raise Fatal(f"{path}: no requirements matched the expected format")
    return reqs


def load_model(path: Path) -> dict:
    try:
        model = yaml.safe_load(read_text(path))
    except yaml.YAMLError as exc:
        raise Fatal(f"{path}: {exc}") from exc
    if not isinstance(model, dict):
        raise Fatal(f"{path}: not a design element register (expected a mapping)")
    if "components" not in model:
        raise Fatal(f"{path}: not a design element register (no `components` key)")
    return model


def check_declared_requirement_count(model: dict, reqs: dict, findings: Findings) -> None:
    """Belt and braces for the sentinel: the register states how many
    requirements it expects, so a wholesale loss fails even if a future id
    scheme slips past REQ_SENTINEL."""
    doc = model.get("document")
    if not isinstance(doc, dict):
        return
    for entry in as_list(doc.get("upstream"), "document.upstream", findings):
        if not isinstance(entry, dict):
            continue
        declared = entry.get("requirement_count")
        if declared is None:
            continue
        if not isinstance(declared, int):
            findings.error(
                f"document.upstream[{entry.get('id')}].requirement_count: "
                f"expected an integer, got {type(declared).__name__}"
            )
        elif declared != len(reqs):
            findings.error(
                f"{entry.get('id')}: register declares {declared} requirements "
                f"but {len(reqs)} were parsed. Either the SRS changed and the "
                f"declared count needs updating, or requirements were lost."
            )


# --------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------

def check_structure(model: dict, reqs: dict[str, dict], findings: Findings) -> dict:
    """Validate ids, allocation, and the component graph. Returns an index."""
    layer_ids: list[str] = []
    layer_index: dict[str, int] = {}
    for i, layer in enumerate(as_list(model.get("layers"), "layers", findings)):
        if not isinstance(layer, dict) or "id" not in layer:
            findings.error(f"layers[{i}]: expected a mapping with an `id`")
            continue
        lid = as_str(layer["id"], f"layers[{i}].id", findings)
        if lid is None:
            continue
        if lid in layer_index:
            findings.error(f"duplicate layer id {lid}")
            continue
        layer_index[lid] = len(layer_ids)
        layer_ids.append(lid)

    components: dict[str, dict] = {}
    elements: dict[str, dict] = {}
    allocation: dict[str, list[str]] = defaultdict(list)

    for i, comp in enumerate(as_list(model.get("components"), "components", findings)):
        if not isinstance(comp, dict):
            findings.error(f"components[{i}]: expected a mapping, got "
                           f"{type(comp).__name__}")
            continue
        if "id" not in comp:
            findings.error(f"components[{i}]: no `id`")
            continue
        cid = as_str(comp["id"], f"components[{i}].id", findings)
        if cid is None:
            continue
        cm = COMPONENT_ID_RE.match(cid)
        if not cm:
            findings.error(f"component id {cid!r} does not match CMP-<CODE>")
            continue
        if cid in components:
            findings.error(f"duplicate component id {cid}")
            continue
        if comp.get("layer") not in layer_index:
            findings.error(f"{cid}: unknown layer {comp.get('layer')!r}")
        if "cross_cutting" in comp and not isinstance(comp["cross_cutting"], bool):
            findings.error(f"{cid}: `cross_cutting` must be a boolean")
        components[cid] = comp

        for j, el in enumerate(as_list(comp.get("elements"), f"{cid}.elements", findings)):
            if not isinstance(el, dict):
                findings.error(f"{cid}.elements[{j}]: expected a mapping, got "
                               f"{type(el).__name__}")
                continue
            if "id" not in el:
                findings.error(f"{cid}.elements[{j}]: no `id`")
                continue
            eid = as_str(el["id"], f"{cid}.elements[{j}].id", findings)
            if eid is None:
                continue
            em = ELEMENT_ID_RE.match(eid)
            if not em:
                findings.error(f"{cid}: element id {eid!r} does not match "
                               f"DSN-<CODE>-<NNN>")
                continue
            if em.group("comp") != cm.group("comp"):
                findings.error(
                    f"{eid}: element code {em.group('comp')!r} does not match "
                    f"its component {cid}"
                )
            if eid in elements:
                findings.error(f"duplicate design element id {eid}")
                continue

            derived = el.get("derived", False)
            if not isinstance(derived, bool):
                findings.error(f"{eid}: `derived` must be a boolean, got "
                               f"{type(derived).__name__}")
                derived = bool(derived)

            satisfies = as_list(el.get("satisfies"), f"{eid}.satisfies", findings)
            refines = as_list(el.get("refines"), f"{eid}.refines", findings)
            as_str(el.get("open"), f"{eid}.open", findings)
            as_str(el.get("title"), f"{eid}.title", findings)

            el = dict(el, component=cid, layer=comp.get("layer"),
                      derived=derived, satisfies=satisfies, refines=refines)
            elements[eid] = el

            if not satisfies and not derived:
                findings.error(
                    f"{eid}: no `satisfies` and not marked `derived: true` — "
                    f"an element must either discharge a requirement or say "
                    f"why it exists"
                )
            if satisfies and derived:
                findings.error(f"{eid}: marked `derived` but also allocates "
                               f"requirements")
            if derived and not el.get("rationale"):
                findings.error(f"{eid}: derived element needs a `rationale`")

            seen: set[str] = set()
            for rid in satisfies:
                if not isinstance(rid, str):
                    findings.error(f"{eid}: satisfies entry {rid!r} is not a string")
                    continue
                if rid in seen:
                    findings.error(f"{eid}: satisfies {rid} more than once")
                    continue
                seen.add(rid)
                if rid not in reqs:
                    findings.error(f"{eid}: satisfies unknown requirement {rid}")
                    continue
                if reqs[rid]["priority"] in UNALLOCATED_PRIORITIES:
                    findings.error(
                        f"{eid}: allocates {rid}, which is priority "
                        f"{reqs[rid]['priority']} (out of v1.0 scope)"
                    )
                allocation[rid].append(eid)

            check_verification(eid, el, reqs, findings)

    check_refines(elements, findings)
    check_component_graph(components, layer_index, layer_ids, findings)

    for rid, req in sorted(reqs.items()):
        if req["priority"] in UNALLOCATED_PRIORITIES:
            continue
        if rid not in allocation:
            findings.error(
                f"{rid} ({req['priority']}, {req['phase']}) is not allocated "
                f"to any design element"
            )

    return {
        "components": components,
        "elements": elements,
        "allocation": dict(allocation),
        "layer_ids": layer_ids,
    }


def check_verification(eid: str, el: dict, reqs: dict, findings: Findings) -> None:
    """An element's declared verification methods must cover the SRS methods of
    every requirement it allocates.

    Without this, an element bundling requirements verified by test, analysis
    and inspection can declare only one of them, and the eventual validation
    suite is scoped from the wrong method.
    """
    raw = el.get("verification")
    if raw is None:
        if el["satisfies"]:
            findings.error(f"{eid}: no `verification` method declared")
        return
    declared = raw if isinstance(raw, list) else [raw]
    bad = [m for m in declared
           if not isinstance(m, str) or m not in VERIFICATION_METHODS]
    if bad:
        findings.error(f"{eid}: unknown verification method(s) {bad!r}; "
                       f"expected any of {sorted(VERIFICATION_METHODS)}")
        return
    if not el["satisfies"]:
        return
    required = {reqs[r]["verification"] for r in el["satisfies"] if r in reqs}
    required.discard("—")
    missing = required - set(declared)
    if missing:
        findings.error(
            f"{eid}: declares verification {sorted(declared)} but allocates "
            f"requirements verified by {sorted(missing)} "
            f"({', '.join(sorted(r for r in el['satisfies'] if r in reqs and reqs[r]['verification'] in missing))})"
        )


def check_refines(elements: dict, findings: Findings) -> None:
    for eid, el in elements.items():
        for target in el["refines"]:
            if not isinstance(target, str):
                findings.error(f"{eid}: refines entry {target!r} is not a string")
                continue
            if target == eid:
                findings.error(f"{eid}: refines itself")
            elif target not in elements:
                findings.error(f"{eid}: refines unknown design element {target}")
    graph = {eid: {"depends_on": [t for t in el["refines"] if isinstance(t, str)]}
             for eid, el in elements.items()}
    for cycle in find_cycles(graph):
        findings.error("refines cycle: " + " -> ".join(cycle))


def check_component_graph(components: dict, layer_index: dict,
                          layer_ids: list, findings: Findings) -> None:
    for cid, comp in components.items():
        for dep in as_list(comp.get("depends_on"), f"{cid}.depends_on", findings):
            if not isinstance(dep, str):
                findings.error(f"{cid}: depends_on entry {dep!r} is not a string")
                continue
            if dep not in components:
                findings.error(f"{cid}: depends_on unknown component {dep}")
                continue
            src, dst = comp.get("layer"), components[dep].get("layer")
            if src in layer_index and dst in layer_index:
                upward = layer_index[dst] > layer_index[src]
                if upward and not components[dep].get("cross_cutting"):
                    findings.error(
                        f"{cid} ({src}) depends on {dep} ({dst}): upward "
                        f"dependency. Only a component marked "
                        f"`cross_cutting: true` may be depended on from a "
                        f"lower layer."
                    )
    for cycle in find_cycles(components):
        findings.error("dependency cycle: " + " -> ".join(cycle))


def find_cycles(nodes: dict[str, dict]) -> list[list[str]]:
    """Return one cycle per back edge found by DFS.

    Sound as a gate: if a cycle exists at least one is reported. It does not
    enumerate every distinct cycle — fixing the reported one reveals the next.
    Iterative so that a deep graph cannot raise RecursionError.
    """
    cycles: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    colour: dict[str, int] = {}

    for root in sorted(nodes):
        if colour.get(root, 0) != 0:
            continue
        stack: list[str] = []
        work: list[tuple[str, list[str]]] = [(root, None)]
        # Explicit stack: (node, iterator over its dependencies)
        iters: dict[str, object] = {}
        work = [root]
        colour[root] = 1
        stack.append(root)
        iters[root] = iter(sorted(
            d for d in (nodes[root].get("depends_on") or [])
            if isinstance(d, str) and d in nodes
        ))
        while stack:
            node = stack[-1]
            nxt = next(iters[node], None)
            if nxt is None:
                colour[node] = 2
                stack.pop()
                continue
            if colour.get(nxt, 0) == 1:
                cycle = stack[stack.index(nxt):] + [nxt]
                key = tuple(cycle[:-1])
                canon = min(tuple(key[i:] + key[:i]) for i in range(len(key)))
                if canon not in seen:
                    seen.add(canon)
                    cycles.append(cycle)
            elif colour.get(nxt, 0) == 0:
                colour[nxt] = 1
                stack.append(nxt)
                iters[nxt] = iter(sorted(
                    d for d in (nodes[nxt].get("depends_on") or [])
                    if isinstance(d, str) and d in nodes
                ))
    return cycles


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def summarise(reqs: dict[str, dict], index: dict) -> str:
    allocation = index["allocation"]
    in_scope = {r: v for r, v in reqs.items()
                if v["priority"] not in UNALLOCATED_PRIORITIES}
    unallocated = [r for r in in_scope if r not in allocation]

    def table(title: str, key: str, order: list[str]) -> list[str]:
        total = Counter(v[key] for v in in_scope.values())
        done = Counter(v[key] for r, v in in_scope.items() if r in allocation)
        # Always show buckets outside the expected order — an unexpected phase
        # or category must not vanish from the summary.
        buckets = order + sorted(set(total) - set(order))
        rows = [f"  {title}"]
        for k in buckets:
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
        f"  allocated                   {len(in_scope) - len(unallocated)}",
        f"  UNALLOCATED                 {len(unallocated)}",
        f"  design elements             {len(index['elements'])}",
        "  derived (no requirement)    "
        f"{sum(1 for e in index['elements'].values() if e.get('derived'))}",
        f"  components                  {len(index['components'])}",
        "",
    ]
    lines += table("By priority", "priority", ["M", "S", "C"])
    lines.append("")
    lines += table("By phase", "phase", ["P1", "P2", "P3", "P4"])
    lines.append("")
    lines += table("By category", "category",
                   sorted({v["category"] for v in in_scope.values()}))
    lines.append("")
    return "\n".join(lines)


def build_matrix(reqs: dict[str, dict], index: dict) -> str:
    allocation = index["allocation"]
    elements = index["elements"]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["requirement", "priority", "phase", "verification",
                "components", "design_elements", "status"])
    for rid in sorted(reqs):
        req = reqs[rid]
        els = sorted(set(allocation.get(rid, [])))
        comps = sorted({elements[e]["component"] for e in els})
        if req["priority"] in UNALLOCATED_PRIORITIES:
            status = "out-of-scope"
        elif els:
            status = "allocated"
        else:
            status = "UNALLOCATED"
        w.writerow([rid, req["priority"], req["phase"], req["verification"],
                    " ".join(comps), " ".join(els), status])
    return buf.getvalue()


def build_json(reqs: dict[str, dict], index: dict, model: dict) -> str:
    elements = index["elements"]

    def methods(el: dict) -> list[str]:
        v = el.get("verification")
        if v is None:
            return []
        return sorted(v) if isinstance(v, list) else [v]

    payload = {
        "document": model.get("document", {}),
        "generated_from": {"requirements": len(reqs), "elements": len(elements)},
        "requirements": {
            rid: {
                **{k: v for k, v in req.items() if k != "line"},
                "satisfied_by": sorted(set(index["allocation"].get(rid, []))),
            }
            for rid, req in sorted(reqs.items())
        },
        "elements": {
            eid: {
                "title": el.get("title"),
                "component": el["component"],
                "layer": el.get("layer"),
                "satisfies": sorted(set(el["satisfies"])),
                "refines": sorted(set(el["refines"])),
                "derived": bool(el.get("derived")),
                "verification": methods(el),
                "open": el.get("open"),
            }
            for eid, el in sorted(elements.items())
        },
        "components": {
            cid: {
                "name": c.get("name"),
                "layer": c.get("layer"),
                "cross_cutting": bool(c.get("cross_cutting")),
                "depends_on": sorted(d for d in (c.get("depends_on") or [])
                                     if isinstance(d, str)),
                "elements": sorted(e["id"] for e in (c.get("elements") or [])
                                   if isinstance(e, dict) and "id" in e),
            }
            for cid, c in sorted(index["components"].items())
        },
    }
    return json.dumps(payload, indent=2, sort_keys=False, default=str) + "\n"


def write_atomic(path: Path, content: str) -> None:
    """Write via a temp file and rename, so a failure part-way through cannot
    leave a half-written artifact behind."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    os.replace(tmp, path)


# --------------------------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    findings = Findings()
    reqs = load_requirements(args.srs, findings)
    model = load_model(args.model)
    check_declared_requirement_count(model, reqs, findings)
    index = check_structure(model, reqs, findings)

    if not args.quiet:
        print(summarise(reqs, index))

    for w in findings.warnings:
        print(f"warning: {w}", file=sys.stderr)
    for e in findings.errors:
        print(f"error: {e}", file=sys.stderr)

    if findings.errors:
        # Never publish an artifact from a failed run. The register itself
        # allocates TOOL-NFR-090 ("report the error and exit non-zero rather
        # than emitting incomplete or misleading results") to DSN-CORE-020;
        # this script does not get to break the rule it exists to enforce.
        if args.emit_matrix or args.emit_json:
            print("note: artifacts not written because the run found errors",
                  file=sys.stderr)
        print(f"\nFAIL: {len(findings.errors)} error(s)", file=sys.stderr)
        return 1

    # Build both payloads before writing either, so a serialisation failure
    # cannot leave the matrix and the graph describing different models.
    outputs: list[tuple[Path, str]] = []
    if args.emit_matrix:
        outputs.append((args.emit_matrix, build_matrix(reqs, index)))
    if args.emit_json:
        outputs.append((args.emit_json, build_json(reqs, index, model)))
    for path, content in outputs:
        write_atomic(path, content)
        print(f"wrote {path}")

    print("OK: every in-scope requirement is allocated and the design graph "
          "is well formed")
    return 0


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
    try:
        return run(args)
    except Fatal as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    except Exception as exc:  # noqa: BLE001 - deliberate top-level guard
        sys.stderr.write(f"error: internal fault: {type(exc).__name__}: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

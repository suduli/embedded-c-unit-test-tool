#!/usr/bin/env python3
"""ECTT GitHub Projects importer — Git remains authoritative; GitHub tracks execution.

Commands
--------
bootstrap   Preview (default) or create the dedicated "ECTT — Delivery" project,
            its fields, its views and the ``blocked`` label. Idempotent: every
            step re-checks remote state before writing.
plan        Read local sources and current GitHub state and emit a JSON change
            preview. No mutations.
apply       Apply a preview (or plan internally) after re-checking source and
            remote state; rejects stale or conflicting changes.

Design invariants (from the delivery plan):
  * Packages are parsed only from PLAN-001 §5.5 (including validation spikes);
    totals are derived, never hard-coded.
  * Managed issues are identified by a hidden ``ectt-work-package:WP-ID`` marker
    in the issue body, discovered across all issue states with pagination.
  * Only generated issue sections and source-owned project metadata are written.
    Human notes, Status, assignees, comments and issue state are never touched.
  * New items initialize in "Needs reconciliation"; historical completion claims
    are rendered as unverified references.
  * Packages removed from the register are reported, never deleted or closed.
  * Duplicate markers or conflicting matches stop the run.
  * Normalized package content is hashed, so unchanged packages write nothing.
  * Dependency annotations (``~`` schedule-only, ``^`` port-mediated) are
    preserved verbatim and never reinterpreted as blocking dependencies.

Exit codes: 0 success · 1 validation/parse/conflict error · 2 stale preview
· 3 credentials or API failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_TITLE = "ECTT — Delivery"
BLOCKED_LABEL = {
    "name": "blocked",
    "color": "B60205",
    "description": "A prerequisite, decision or review is blocking this item — a comment explains the blocker",
}
STATUS_OPTIONS = [
    "Needs reconciliation",
    "Backlog",
    "Ready",
    "In Progress",
    "Review",
    "Verification",
    "Done",
]
INITIAL_STATUS = "Needs reconciliation"
PHASE_OPTIONS = ["P0", "P1", "P2", "P3", "P4"]
FIELD_WORK_PACKAGE = "Work Package"
FIELD_COMPONENT = "Component"
FIELD_PHASE = "Phase"
FIELD_EFFORT = "Effort"
FIELD_DEPENDS_ON = "Depends on"
SPIKE_COMPONENT = "Validation spikes"
# Field values owned by the source register and rewritten by the importer.
SOURCE_OWNED_FIELDS = [FIELD_WORK_PACKAGE, FIELD_COMPONENT, FIELD_PHASE, FIELD_EFFORT, FIELD_DEPENDS_ON]
# Plan §2: the first import covers work packages only; T-* review tasks stay
# reference material in docs/reviews/ and are deliberately not imported.
COMPONENT_RE = re.compile(r"^CMP-[A-Z]{3,4}$")
WP_RE = re.compile(r"^WP-[A-Z]+-\d+$")
MARKER_RE = re.compile(r"ectt-work-package:(WP-[A-Z]+-\d+)")
TITLE_RE = re.compile(r"^\[(WP-[A-Z]+-\d+)\] (.+)$")
SHORT_REQ_RE = re.compile(r"[A-Z]{3}-\d{3}")
SRS_REQ_RE = re.compile(r"^\*\*(TOOL-[A-Z]{3}-\d{3})\*\* \*\(([MSCF]), (P[1-4]|—), ([TADI]|—)\)\*", re.M)
VIEW_SPECS = [
    {"name": "Reconciliation", "layout": "TABLE", "filter": f'Status:"{INITIAL_STATUS}"',
     "manual": "visible fields: Title, Status, Work Package, Component, Phase"},
    {"name": "Delivery", "layout": "BOARD", "filter": f'-Status:"{INITIAL_STATUS}"',
     "manual": "group by Status"},
    {"name": "Subsystems", "layout": "TABLE", "filter": "",
     "manual": "group by Component"},
    {"name": "Phase planning", "layout": "TABLE", "filter": "",
     "manual": "group by Phase; visible fields: Effort, Depends on, Work Package"},
]
BODY_TEMPLATE_VERSION = 1
# Plan §4.4 records the three validation spikes complete in ADR-001. That is a
# historical claim by the source document, not verification evidence the
# importer can check, so it is surfaced as an unverified reference.
HISTORICAL_CLAIMS = {
    "WP-SPIKE-01": "PLAN-001 §4.4 records this spike complete in ADR-001 (historical claim, unverified).",
    "WP-SPIKE-02": "PLAN-001 §4.4 records this spike complete in ADR-001 (historical claim, unverified).",
    "WP-SPIKE-03": "PLAN-001 §4.4 records this spike complete in ADR-001 (historical claim, unverified).",
}
EDGE_KINDS = {"~": "schedule-only", "^": "port-mediated", "": "code"}
EDGE_NOTE = {
    "code": "code dependency (build-order; the layering rule applies)",
    "schedule-only": "schedule-only (`~`): cannot be demonstrated until this exists; no code depends on it",
    "port-mediated": "port-mediated (`^`): inverted dependency bound at composition time",
}
GENERATED_BEGIN = "<!-- ectt:generated:start -->"
GENERATED_END = "<!-- ectt:generated:end -->"


class ProjectsError(Exception):
    """Actionable failure with a stable exit-code category."""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


class GhError(ProjectsError):
    """GitHub CLI or API failure (credentials, network, permissions)."""

    def __init__(self, message: str):
        super().__init__(message, code=3)


# ---------------------------------------------------------------------------
# GitHub CLI transport
# ---------------------------------------------------------------------------


class Gh:
    """Thin subprocess wrapper over the GitHub CLI (authentication is gh's job).

    Tests replace this object with an in-memory fake exposing the same methods.
    """

    def __init__(self, gh_path: str = "gh"):
        self.gh_path = gh_path

    def _run(self, args: list[str], stdin: str | None = None) -> str:
        try:
            proc = subprocess.run(
                [self.gh_path, *args],
                input=stdin,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except FileNotFoundError as exc:
            raise GhError(
                f"GitHub CLI ({self.gh_path}) not found. Install it and authenticate with "
                "'gh auth login', or provide a token via the ECTT_PROJECTS_TOKEN environment variable."
            ) from exc
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            if "gh auth" in detail or "authentication" in detail.lower() or proc.returncode == 4:
                detail += "\nAuthenticate with 'gh auth login' or set ECTT_PROJECTS_TOKEN."
            raise GhError(f"github CLI failed ({' '.join(args[:3])}…): {detail}")
        return proc.stdout

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = json.dumps({"query": query, "variables": variables or {}})
        out = self._run(["api", "graphql", "--input", "-"], stdin=payload)
        data = json.loads(out)
        if data.get("errors"):
            raise GhError(f"GraphQL error: {json.dumps(data['errors'])[:400]}")
        return data["data"]

    def rest(self, path: str, method: str = "GET", body: dict | None = None,
             params: dict[str, str] | None = None) -> Any:
        args = ["api", path]
        if method != "GET":
            args += ["--method", method]
        for key, value in (params or {}).items():
            args += ["-f", f"{key}={value}"]
        if body is not None:
            args += ["--input", "-"]
            out = self._run(args, stdin=json.dumps(body))
        else:
            out = self._run(args)
        if not out.strip():
            return None
        return json.loads(out)

    def rest_paginated(self, path: str, params: dict[str, str] | None = None) -> list:
        """Collect every page of a REST list endpoint (all states, no shortcuts)."""
        items: list = []
        page = 1
        while True:
            chunk = self.rest(path, params={**(params or {}), "per_page": "100", "page": str(page)})
            if not chunk:
                break
            items.extend(chunk)
            if len(chunk) < 100:
                break
            page += 1
        return items


# ---------------------------------------------------------------------------
# Local source parsing
# ---------------------------------------------------------------------------


@dataclass
class Package:
    wid: str
    capability: str
    comp: str          # register value: "CMP-XXX" or "—" for spikes
    phase: str
    effort: int        # person-weeks
    reqs: list[str]    # short SRS ids, register order
    deps: list[str]    # tokens like "CORE-01", "~ANA-04", "^EXH-01"
    adr: bool
    layer: str         # "Validation spikes" or "L0 — Platform and Persistence" …
    acceptance: str | None = None   # §5.4 exit criterion, when recorded
    srs_attrs: dict[str, tuple[str, str, str]] = field(default_factory=dict)

    @property
    def component(self) -> str:
        return SPIKE_COMPONENT if self.comp == "—" else self.comp

    @property
    def title(self) -> str:
        return f"[{self.wid}] {self.capability}"

    @property
    def depends_on_value(self) -> str:
        return " ".join(self.deps) if self.deps else "—"


def parse_srs(text: str) -> dict[str, tuple[str, str, str]]:
    """Requirement id -> (priority, phase, verification), mirroring plan_check.py."""
    matches = SRS_REQ_RE.findall(text)
    reqs: dict[str, tuple[str, str, str]] = {}
    for rid, pri, phase, ver in matches:
        if rid in reqs:
            raise ProjectsError(f"duplicate SRS requirement identifier {rid}")
        reqs[rid] = (pri, phase, ver)
    if len(re.findall(r"^\*\*TOOL-", text, re.M)) != len(matches):
        raise ProjectsError(
            "malformed SRS requirement line: every '**TOOL-xxx-nnn** *(P, ph, V)*' line must match the parser"
        )
    return reqs


def parse_packages(plan_text: str, srs: dict[str, tuple[str, str, str]]) -> list[Package]:
    """Parse PLAN-001 §5.5 only. Totals are derived; nothing is hard-coded."""
    if "### 5.5 The work package register" not in plan_text:
        raise ProjectsError("PLAN-001 §5.5 (the work package register) not found")
    source = plan_text.split("### 5.5 The work package register", 1)[1].split("## 6.", 1)[0]
    acceptance = parse_exit_criteria(plan_text)
    packages: dict[str, Package] = {}
    layer = ""
    for raw in source.splitlines():
        line = raw.strip()
        if line.startswith("#### "):
            layer = line[len("#### "):].strip()
            continue
        if not line.startswith("| `WP-"):
            continue
        fields = [f.strip() for f in line.strip().strip("|").split("|")]
        if len(fields) != 8:
            raise ProjectsError(f"malformed work-package row (expected 8 columns): {line[:120]}")
        wid, capability, comp, phase, effort, held, deps, adr = fields
        wid = wid.strip("`")
        if not layer:
            raise ProjectsError(f"work-package row {wid} appears before any '#### <section>' heading")
        if not WP_RE.match(wid):
            raise ProjectsError(f"malformed work-package identifier {wid!r}")
        if wid in packages:
            raise ProjectsError(f"duplicate work package {wid}")
        if phase not in PHASE_OPTIONS:
            raise ProjectsError(f"{wid}: unknown start phase {phase!r}")
        if not re.match(r"^\d+w$", effort):
            raise ProjectsError(f"{wid}: malformed effort {effort!r} (expected '<n>w')")
        if not (COMPONENT_RE.match(comp) or comp == "—"):
            raise ProjectsError(f"{wid}: unknown component {comp!r}")
        if (comp == "—") != (wid.startswith("WP-SPIKE")):
            raise ProjectsError(f"{wid}: component '—' is reserved for validation spikes")
        reqs = SHORT_REQ_RE.findall(held)
        if held.strip() == "—" and reqs:
            raise ProjectsError(f"{wid}: requirement column is '—' but lists {reqs}")
        unknown = [r for r in reqs if "TOOL-" + r not in srs]
        if unknown:
            raise ProjectsError(f"{wid}: requirements not present in SRS-001: {', '.join(unknown)}")
        if len(set(reqs)) != len(reqs):
            raise ProjectsError(f"{wid}: duplicate requirement allocation inside the package")
        dep_tokens = deps.split() if deps.strip() not in ("", "—") else []
        for token in dep_tokens:
            target = "WP-" + token.lstrip("~^")
            if not WP_RE.match(target):
                raise ProjectsError(f"{wid}: malformed dependency token {token!r}")
            if target == wid:
                raise ProjectsError(f"{wid}: depends on itself")
        packages[wid] = Package(
            wid=wid,
            capability=capability,
            comp=comp,
            phase=phase,
            effort=int(effort.rstrip("w")),
            reqs=reqs,
            deps=dep_tokens,
            adr=adr.strip() == "●",
            layer=layer,
            acceptance=acceptance.get(wid),
        )
    if not packages:
        raise ProjectsError("§5.5 parsed to zero work packages")
    for wid, pkg in packages.items():
        for token in pkg.deps:
            target = "WP-" + token.lstrip("~^")
            if target not in packages:
                raise ProjectsError(f"{wid}: unknown dependency {target}")
        pkg.srs_attrs = {r: srs["TOOL-" + r] for r in pkg.reqs}
    _check_layer_claims(source, packages)
    _check_cycles(packages)
    return list(packages.values())


def _check_layer_claims(source: str, packages: dict[str, Package]) -> None:
    """Each section's authored rollup ('N work packages · M requirements · K
    person-weeks') must match what its parsed rows actually give."""
    claims: dict[str, tuple[int, int, int]] = {}
    for match in re.finditer(
        r"^#### (.+)$\n\n(\d+) work packages · (\d+) requirements · (\d+) person-weeks", source, re.M
    ):
        claims[match.group(1).strip()] = (int(match.group(2)), int(match.group(3)), int(match.group(4)))
    derived: dict[str, tuple[int, int, int]] = {}
    for pkg in packages.values():
        w, r, e = derived.get(pkg.layer, (0, 0, 0))
        derived[pkg.layer] = (w + 1, r + len(pkg.reqs), e + pkg.effort)
    for layer, gave in sorted(derived.items()):
        if layer not in claims:
            raise ProjectsError(f"section '{layer}' has work-package rows but no 'N work packages · …' rollup line")
        if gave != claims[layer]:
            raise ProjectsError(
                f"section '{layer}' rollup claims {claims[layer][0]} packages · {claims[layer][1]} requirements · "
                f"{claims[layer][2]} person-weeks but the parsed rows give {gave[0]} · {gave[1]} · {gave[2]}"
            )
    for layer in sorted(set(claims) - set(derived)):
        if any(claims[layer]):
            raise ProjectsError(f"section '{layer}' claims {claims[layer][0]} work packages but no rows parsed")


def _check_cycles(packages: dict[str, Package]) -> None:
    """plan_check.py proves this too; re-derived here so the importer never
    proposes writes from a source it could not schedule."""
    state: dict[str, int] = {}

    def visit(wid: str, stack: list[str]) -> None:
        if state.get(wid) == 1:
            cycle = stack[stack.index(wid):] + [wid]
            raise ProjectsError("dependency cycle: " + " → ".join(cycle))
        if state.get(wid) == 2:
            return
        state[wid] = 1
        for token in packages[wid].deps:
            visit("WP-" + token.lstrip("~^"), stack + [wid])
        state[wid] = 2

    for wid in packages:
        visit(wid, [])


def parse_exit_criteria(plan_text: str) -> dict[str, str]:
    """§5.4 exit-criteria table, where recorded; absence is expected and flagged."""
    if "### 5.4 Exit criteria pattern" not in plan_text:
        return {}
    section = plan_text.split("### 5.4 Exit criteria pattern", 1)[1].split("### 5.5", 1)[0]
    out: dict[str, str] = {}
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("| `WP-"):
            continue
        fields = [f.strip() for f in line.strip().strip("|").split("|")]
        if len(fields) != 2 or not fields[1]:
            raise ProjectsError(f"malformed §5.4 exit-criterion row: {line[:120]}")
        out[fields[0].strip("`")] = fields[1]
    return out


# ---------------------------------------------------------------------------
# Rendering and hashing
# ---------------------------------------------------------------------------


def canonical_record(pkg: Package, repo: str) -> str:
    """Stable serialization of everything the importer owns for one package.

    Deliberately excludes the source revision (a revision bump alone must not
    rewrite every issue) and any remote state (issue numbers, item ids): the
    hash covers only what the source register owns, so unchanged packages
    produce zero writes on reruns."""
    record = {
        "template": BODY_TEMPLATE_VERSION,
        "repo": repo,
        "wid": pkg.wid,
        "capability": pkg.capability,
        "component": pkg.component,
        "phase": pkg.phase,
        "effort": pkg.effort,
        "adr": pkg.adr,
        "layer": pkg.layer,
        "reqs": [[r, *pkg.srs_attrs[r]] for r in pkg.reqs],
        "deps": [[t, EDGE_KINDS[t[0]] if t[:1] in ("~", "^") else "code"] for t in pkg.deps],
        "acceptance_recorded": pkg.acceptance is not None,
        "historical_claim": pkg.wid in HISTORICAL_CLAIMS,
    }
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def content_hash(pkg: Package, repo: str) -> str:
    payload = canonical_record(pkg, repo)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def issue_search_link(repo: str, wid: str) -> str:
    query = urllib.parse.quote(f'"ectt-work-package:{wid}" in:body')
    return f"https://github.com/{repo}/issues?q={query}"


def render_generated_block(pkg: Package, repo: str, source_revision: str, digest: str) -> str:
    """The importer-owned slice of the issue body, between the begin/end markers."""
    lines: list[str] = [GENERATED_BEGIN, f"<!-- ectt-content-hash:{digest} -->", ""]
    lines.append(f"**Component:** {pkg.component} · **Phase:** {pkg.phase} · **Effort:** {pkg.effort} person-weeks · **ADR-sensitive:** {'yes ●' if pkg.adr else 'no'}")
    lines.append("")
    lines.append(
        "**Source of truth:** PLAN-001 §5.5 "
        f"({pkg.layer}) in Git. This issue tracks execution only; the register owns capability, component, phase, "
        "effort, requirements and dependencies."
    )
    lines.append(
        f"**Source revision:** PLAN-001 @ `{source_revision}` (last content change) · **content hash:** `{digest}`"
    )
    lines.append("")
    lines.append(f"## Requirements owned ({len(pkg.reqs)})")
    lines.append("")
    if pkg.reqs:
        lines.append(
            "Primary allocations from [SRS-001-requirements.md](SRS-001-requirements.md); "
            "plan_check proves exactly-once allocation:"
        )
        lines.append("")
        lines.append("| Requirement | Priority | Phase | Verification |")
        lines.append("|---|---|---|---|")
        for rid in pkg.reqs:
            pri, phase, ver = pkg.srs_attrs[rid]
            lines.append(f"| `TOOL-{rid}` | {pri} | {phase} | {ver} |")
        lines.append("")
    else:
        lines.append("None — this package owns no SRS requirements (validation spike; see PLAN-001 §4.4).")
        lines.append("")
    lines.append(f"## Dependencies ({len(pkg.deps)})")
    lines.append("")
    if pkg.deps:
        for token in pkg.deps:
            kind = EDGE_KINDS[token[0]] if token[:1] in ("~", "^") else "code"
            target = "WP-" + token.lstrip("~^")
            lines.append(f"- `{token}` → [{target}]({issue_search_link(repo, target)}) — {EDGE_NOTE[kind]}")
        lines.append("")
        lines.append(
            "Annotations are preserved verbatim; schedule-only and port-mediated edges are not build-order dependencies."
        )
        lines.append("")
    else:
        lines.append("None.")
        lines.append("")
    lines.append("## Acceptance criteria")
    lines.append("")
    if pkg.acceptance:
        lines.append(f"> {pkg.acceptance}")
        lines.append("")
        lines.append("Recorded in PLAN-001 §5.4. Done requires reviewed acceptance evidence against this criterion.")
    else:
        lines.append(
            "**No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — "
            "flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready."
        )
    lines.append("")
    lines.append("## Verification evidence")
    lines.append("")
    if pkg.reqs:
        methods: dict[str, int] = {}
        for _r, (_pri, _ph, ver) in pkg.srs_attrs.items():
            methods[ver] = methods.get(ver, 0) + 1
        pretty = {
            "T": "test (black-box technique per PLAN-001 §6)",
            "I": "inspection",
            "D": "demonstration",
            "A": "analysis",
            "—": "— (deferred)",
        }
        rendered = ", ".join(f"{count} × {pretty.get(ver, ver)}" for ver, count in sorted(methods.items()))
        lines.append(f"SRS-001 verification methods for the owned requirements: {rendered}.")
    else:
        lines.append("Per-spike pass criteria are defined in PLAN-001 §4.4; evidence attaches to the ADR decision record.")
    lines.append(
        "Link evidence (reports, test runs, review documents) as comments or task references below; "
        "merging a PR alone must not close this work package."
    )
    lines.append("")
    claim = HISTORICAL_CLAIMS.get(pkg.wid)
    if claim:
        lines.append("## Historical references (unverified)")
        lines.append("")
        lines.append(f"- {claim} Do not treat this as verification evidence.")
        lines.append("")
    lines.append(GENERATED_END)
    return "\n".join(lines)


def default_human_tail() -> str:
    return (
        "\n\n<!-- Everything below this line is human-owned: notes, discussion, reconciliation decisions. -->\n"
        "<!-- The importer updates only the generated block above; it never edits this section. -->\n\n"
        "## Reconciliation notes\n\n"
        "_Initial status: Needs reconciliation. Review requirements, dependencies and acceptance criteria "
        "before moving to Backlog._\n"
    )


def render_body(pkg: Package, repo: str, source_revision: str, digest: str) -> str:
    """Full body for a fresh issue: hidden marker, generated block, human tail."""
    return (
        f"<!-- ectt-work-package:{pkg.wid} -->\n\n"
        + render_generated_block(pkg, repo, source_revision, digest)
        + default_human_tail()
    )


def split_generated(body: str) -> tuple[str, str] | None:
    """Return (before, after) around the generated block, or None if unmarked."""
    begin = body.find(GENERATED_BEGIN)
    end = body.find(GENERATED_END)
    if begin == -1 or end == -1 or end < begin:
        return None
    end += len(GENERATED_END)
    return body[:begin], body[end:]


def stored_hash(body: str) -> str | None:
    match = re.search(r"<!-- ectt-content-hash:(sha256:[0-9a-f]{64}) -->", body)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Remote state
# ---------------------------------------------------------------------------


@dataclass
class RemoteIssue:
    number: int
    node_id: str
    title: str
    state: str
    body: str


@dataclass
class RemoteItem:
    item_id: str
    issue_number: int
    field_values: dict[str, Any]  # field name -> option name / text / number


@dataclass
class RemoteProjectState:
    id: str
    title: str
    number: int
    resource_path: str
    fields: dict[str, dict]           # name -> {id, dataType, options: {name: id}}
    items: dict[int, RemoteItem]      # issue number -> item
    views: dict[str, dict]            # name -> {id, layout, filter}


PROJECT_FIELDS_FRAGMENT = """
fields(first:100){nodes{
  ... on ProjectV2SingleSelectField { name id dataType options{id name} }
  ... on ProjectV2Field { name id dataType }
  ... on ProjectV2IterationField { name id dataType }
}}
"""

# `field` is the ProjectV2FieldConfiguration union: selections need inline
# fragments on its member types (GitHub rejects direct selections on unions).
PROJECT_ITEMS_FRAGMENT = """
items(first:100,after:$cursor){pageInfo{hasNextPage endCursor}nodes{
  id
  content{... on Issue{number title state}}
  fieldValues(first:50){nodes{
    ... on ProjectV2ItemFieldSingleSelectValue{
      field{... on ProjectV2SingleSelectField{name}}
      name optionId
    }
    ... on ProjectV2ItemFieldTextValue{
      field{... on ProjectV2Field{name}}
      text
    }
    ... on ProjectV2ItemFieldNumberValue{
      field{... on ProjectV2Field{name}}
      number
    }
    ... on ProjectV2ItemFieldDateValue{
      field{... on ProjectV2Field{name}}
      date
    }
  }}
}}
"""


def fetch_project(gh: Gh, owner: str, number: int) -> RemoteProjectState:
    """Fetch project, fields, items (paginated) and views — user or org owned."""
    owner_type = gh.rest(f"users/{owner}").get("type")
    root = "organization" if owner_type == "Organization" else "user"
    query = f"""query($login:String!,$number:Int!,$cursor:String){{
      {root}(login:$login){{
        projectV2(number:$number){{
          id title number resourcePath
          {PROJECT_FIELDS_FRAGMENT}
          {PROJECT_ITEMS_FRAGMENT}
          views(first:50){{nodes{{id name layout filter}}}}
        }}
      }}
    }}"""
    variables: dict[str, Any] = {"login": owner, "number": number, "cursor": None}
    project = gh.graphql(query, variables)[root]["projectV2"]
    if project is None:
        raise ProjectsError(
            f"Project #{number} not found for owner '{owner}'. Run 'bootstrap' first, or pass the right --project-number."
        )
    item_nodes = {n["id"]: n for n in project["items"]["nodes"]}
    while project["items"]["pageInfo"]["hasNextPage"]:
        variables["cursor"] = project["items"]["pageInfo"]["endCursor"]
        page = gh.graphql(query, variables)[root]["projectV2"]["items"]
        for n in page["nodes"]:
            item_nodes[n["id"]] = n
    fields: dict[str, dict] = {}
    for node in project["fields"]["nodes"]:
        entry: dict[str, Any] = {"id": node.get("id"), "dataType": node.get("dataType"), "options": {}}
        for opt in node.get("options") or []:
            entry["options"][opt["name"]] = opt["id"]
        fields[node["name"]] = entry
    parsed_items: dict[int, RemoteItem] = {}
    for node in item_nodes.values():
        content = node.get("content") or {}
        if content.get("number") is None:   # draft items have no Issue content
            continue
        values: dict[str, Any] = {}
        for fv in node["fieldValues"]["nodes"]:
            fname = (fv.get("field") or {}).get("name")
            if fname is None:
                continue
            for key in ("name", "text", "number", "date"):
                if key != "field" and fv.get(key) is not None:
                    values[fname] = fv[key]
                    break
        parsed_items[content["number"]] = RemoteItem(node["id"], content["number"], values)
    views = {
        v["name"]: {"id": v["id"], "layout": v["layout"], "filter": v.get("filter") or ""}
        for v in project["views"]["nodes"]
    }
    return RemoteProjectState(
        project["id"], project["title"], project["number"], project.get("resourcePath") or "",
        fields, parsed_items, views,
    )


def fetch_managed_issues(gh: Gh, repo: str) -> tuple[dict[str, RemoteIssue], list[ProjectsError]]:
    """Find every issue carrying the hidden marker, open or closed, all pages.

    Duplicate markers and unmarked-but-title-matching issues are conflicts that
    stop the run. Returns (marker -> issue, conflicts)."""
    issues = gh.rest_paginated(f"repos/{repo}/issues", {"state": "all"})
    managed: dict[str, RemoteIssue] = {}
    conflicts: list[ProjectsError] = []
    titles: dict[str, RemoteIssue] = {}
    for raw in issues:
        issue = RemoteIssue(raw["number"], raw["node_id"], raw["title"], raw["state"], raw.get("body") or "")
        match = TITLE_RE.match(issue.title)
        if match:
            titles.setdefault(match.group(1), issue)
        found = MARKER_RE.findall(issue.body)
        if len(set(found)) > 1:
            conflicts.append(ProjectsError(
                f"issue #{issue.number} carries multiple work-package markers: {sorted(set(found))}"
            ))
            continue
        if found:
            wid = found[0]
            if wid in managed:
                conflicts.append(ProjectsError(
                    f"duplicate work-package marker {wid}: issues #{managed[wid].number} and #{issue.number} both claim it"
                ))
                continue
            managed[wid] = issue
    for wid, issue in sorted(titles.items()):
        if wid not in managed:
            conflicts.append(ProjectsError(
                f"issue #{issue.number} is titled for {wid} but carries no ectt-work-package marker — "
                "rename it, or add the marker if it is the managed issue"
            ))
    return managed, conflicts


# ---------------------------------------------------------------------------
# Ops planning
# ---------------------------------------------------------------------------


def plan_import(
    gh: Gh,
    root: Path,
    repo: str,
    owner: str,
    project_number: int,
    only: list[str] | None = None,
) -> dict[str, Any]:
    packages = load_source(root)
    project = fetch_project(gh, owner, project_number)
    if project.title != PROJECT_TITLE:
        raise ProjectsError(
            f"project #{project_number} is titled '{project.title}' but the importer manages '{PROJECT_TITLE}'. "
            "Pass the correct --project-number (or re-run bootstrap)."
        )
    managed, conflicts = fetch_managed_issues(gh, repo)
    if conflicts:
        raise conflicts[0]
    revision = source_revision(root)
    operations: list[dict[str, Any]] = []
    counts = {"create": 0, "update": 0, "unchanged": 0, "conflict": 0, "retired_source": 0}
    selected = set(only or [])
    unknown_selected = sorted(selected - {p.wid for p in packages})
    if unknown_selected:
        raise ProjectsError(f"--wp selects packages absent from the register: {', '.join(unknown_selected)}")
    retired: list[dict] = []
    for pkg in packages:
        if selected and pkg.wid not in selected:
            continue
        digest = content_hash(pkg, repo)
        issue = managed.get(pkg.wid)
        wanted_fields = {
            FIELD_WORK_PACKAGE: pkg.wid,
            FIELD_COMPONENT: pkg.component,
            FIELD_PHASE: pkg.phase,
            FIELD_EFFORT: pkg.effort,
            FIELD_DEPENDS_ON: pkg.depends_on_value,
        }
        if issue is None:
            operations.append({
                "op": "create_issue",
                "wp": pkg.wid,
                "title": pkg.title,
                "body": render_body(pkg, repo, revision, digest),
                "hash": digest,
                "add_to_project": True,
                "initial_status": INITIAL_STATUS,
                "fields": wanted_fields,
            })
            counts["create"] += 1
            continue
        existing_hash = stored_hash(issue.body)
        if existing_hash is None or split_generated(issue.body) is None:
            raise ProjectsError(
                f"conflicting match: issue #{issue.number} carries the {pkg.wid} marker but not the importer's "
                "generated block (rebuilt or hand-edited body). Reconcile this issue manually, then restore the "
                "generated block before re-running."
            )
        wrote = False
        if existing_hash != digest:
            before, after = split_generated(issue.body)
            new_body = before + render_generated_block(pkg, repo, revision, digest) + after
            operations.append({
                "op": "update_issue", "wp": pkg.wid, "number": issue.number,
                "title": pkg.title, "body": new_body, "hash": digest,
            })
            counts["update"] += 1
            wrote = True
        item = project.items.get(issue.number)
        if item is None:
            operations.append({
                "op": "add_item", "wp": pkg.wid, "issue_number": issue.number,
                "initial_status": INITIAL_STATUS, "fields": wanted_fields,
            })
            counts["update"] += 1
            wrote = True
        else:
            stale = {
                name: value for name, value in wanted_fields.items()
                if item.field_values.get(name) != value
            }
            if stale:
                operations.append({
                    "op": "set_fields", "wp": pkg.wid, "issue_number": issue.number,
                    "item_id": item.item_id, "fields": stale,
                })
                counts["update"] += 1
                wrote = True
        if not wrote:
            counts["unchanged"] += 1
    known_wids = {p.wid for p in packages}
    for wid, issue in sorted(managed.items()):
        if wid not in known_wids:
            retired.append({"wp": wid, "issue_number": issue.number, "state": issue.state})
            counts["retired_source"] += 1
    return {
        "schema": 1,
        "tool": "github_projects.py",
        "generated_at": utcnow(),
        "repo": repo,
        "owner": owner,
        "project_number": project_number,
        "project_title": project.title,
        "source_revision": revision,
        "counts": counts,
        "totals": totals(packages),
        "operations": operations,
        "retired_source": retired,
        "remote_digest": remote_digest(managed, project),
    }


def remote_digest(managed: dict[str, RemoteIssue], project: RemoteProjectState) -> str:
    """Digest over the source-owned remote surface only. Human edits (status,
    assignees, comments) do not invalidate a preview; source-owned surfaces do."""
    payload = {
        "issues": sorted(
            (wid, i.number, i.title, stored_hash(i.body) or "unhashed") for wid, i in managed.items()
        ),
        "items": sorted(
            (n, it.item_id, {k: v for k, v in it.field_values.items() if k in SOURCE_OWNED_FIELDS})
            for n, it in project.items.items()
        ),
        "project_title": project.title,
    }
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def totals(packages: list[Package]) -> dict[str, Any]:
    edges = {"code": 0, "port-mediated": 0, "schedule-only": 0}
    by_layer: dict[str, int] = {}
    for pkg in packages:
        for token in pkg.deps:
            kind = EDGE_KINDS[token[0]] if token[:1] in ("~", "^") else "code"
            edges[kind] += 1
        by_layer[pkg.layer] = by_layer.get(pkg.layer, 0) + 1
    return {
        "packages": len(packages),
        "requirements_allocated": sum(len(p.reqs) for p in packages),
        "dependency_edges": edges,
        "by_layer": by_layer,
    }


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def apply_operations(
    gh: Gh,
    preview: dict[str, Any],
    root: Path,
    repo: str,
    owner: str,
    project_number: int,
    only: list[str] | None = None,
) -> dict[str, Any]:
    """Execute a preview after re-checking remote state; rejects stale previews."""
    revision = source_revision(root)
    if preview.get("source_revision") != revision:
        raise ProjectsError(
            f"preview is stale: it was generated at source revision {preview.get('source_revision')} "
            f"but the checkout is at {revision}. Re-run 'plan' and apply the fresh preview.",
            code=2,
        )
    if preview.get("repo") != repo or preview.get("owner") != owner:
        raise ProjectsError("preview was generated for a different repository or owner", code=2)
    project = fetch_project(gh, owner, project_number)
    if project.title != PROJECT_TITLE:
        raise ProjectsError(f"project #{project_number} is titled '{project.title}', expected '{PROJECT_TITLE}'")
    managed, conflicts = fetch_managed_issues(gh, repo)
    if conflicts:
        raise conflicts[0]
    if preview.get("remote_digest") != remote_digest(managed, project):
        raise ProjectsError(
            "preview is stale: source-owned GitHub state changed since it was generated "
            "(managed issues created, retitled or rebuilt; project membership or source-owned field edits). "
            "Re-run 'plan' and apply the fresh preview.",
            code=2,
        )
    selected = set(only or [])
    report: dict[str, Any] = {
        "created": [], "updated": [], "unchanged": [],
        "retired_source": preview.get("retired_source", []),
    }
    for op in preview["operations"]:
        wp = op.get("wp", "")
        if selected and wp and wp not in selected:
            continue
        kind = op["op"]
        if kind == "create_issue":
            issue = managed.get(wp)
            if issue is None:
                created = gh.rest(
                    f"repos/{repo}/issues", method="POST",
                    body={"title": op["title"], "body": op["body"]},
                )
                issue = RemoteIssue(created["number"], created["node_id"], created["title"], "open", created["body"])
                managed[wp] = issue
                report["created"].append({"wp": wp, "issue_number": issue.number})
            if op.get("add_to_project", True):
                item_id = add_item_and_initialize(gh, project, issue, op.get("initial_status", INITIAL_STATUS))
                set_field_values(gh, project, item_id, op.get("fields", {}))
                report["updated"].append({"wp": wp, "action": "add_item", "issue_number": issue.number})
        elif kind == "update_issue":
            gh.rest(
                f"repos/{repo}/issues/{op['number']}", method="PATCH",
                body={"title": op["title"], "body": op["body"]},
            )
            report["updated"].append({"wp": wp, "action": "update_issue", "issue_number": op["number"]})
        elif kind == "add_item":
            issue = managed.get(wp)
            if issue is None:
                raise ProjectsError(f"add_item for {wp}: the managed issue disappeared mid-run")
            item_id = add_item_and_initialize(gh, project, issue, op.get("initial_status", INITIAL_STATUS))
            set_field_values(gh, project, item_id, op.get("fields", {}))
            report["updated"].append({"wp": wp, "action": "add_item", "issue_number": issue.number})
        elif kind == "set_fields":
            set_field_values(gh, project, op["item_id"], op["fields"])
            report["updated"].append({
                "wp": wp, "action": "set_fields",
                "issue_number": op["issue_number"], "fields": sorted(op["fields"]),
            })
        else:
            raise ProjectsError(f"unknown operation in preview: {kind}")
    # Report-only surface: retired packages are never closed or deleted.
    return report


def add_item_and_initialize(gh: Gh, project: RemoteProjectState, issue: RemoteIssue, status: str) -> str:
    """Add the issue to the project and set its initial Status — once.

    Status is written only here (item creation), never during updates, so
    reconciled statuses survive synchronization. Re-adding an existing item is
    a no-op, which is what makes interrupted runs resumable."""
    existing = project.items.get(issue.number)
    if existing is not None:
        return existing.item_id
    result = gh.graphql(
        """mutation($projectId:ID!,$contentId:ID!){
             addProjectV2ItemById(input:{projectId:$projectId, contentId:$contentId}){
               item{id}
             }
           }""",
        {"projectId": project.id, "contentId": issue.node_id},
    )
    item_id = result["addProjectV2ItemById"]["item"]["id"]
    project.items[issue.number] = RemoteItem(item_id, issue.number, {})
    status_field = project.fields.get("Status")
    if status_field is None:
        raise ProjectsError("the project has no Status field — re-run bootstrap")
    if status not in status_field["options"]:
        raise ProjectsError(
            f"Status field has no '{status}' option — re-run bootstrap before importing"
        )
    gh.graphql(
        """mutation($projectId:ID!,$itemId:ID!,$fieldId:ID!,$optionId:String!){
             updateProjectV2ItemFieldValue(
               input:{projectId:$projectId, itemId:$itemId, fieldId:$fieldId,
                      value:{singleSelectOptionId:$optionId}}){ item{id} }
           }""",
        {"projectId": project.id, "itemId": item_id, "fieldId": status_field["id"],
         "optionId": status_field["options"][status]},
    )
    project.items[issue.number].field_values["Status"] = status
    return item_id


def set_field_values(gh: Gh, project: RemoteProjectState, item_id: str, fields: dict[str, Any]) -> None:
    for name, value in fields.items():
        meta = project.fields.get(name)
        if meta is None:
            raise ProjectsError(f"the project is missing the '{name}' field — re-run bootstrap")
        if meta["dataType"] == "SINGLE_SELECT":
            if value not in meta["options"]:
                raise ProjectsError(f"field '{name}' has no option {value!r} — re-run bootstrap")
            mutation_value: dict[str, Any] = {"singleSelectOptionId": meta["options"][value]}
        elif meta["dataType"] == "NUMBER":
            mutation_value = {"number": value}
        else:
            mutation_value = {"text": str(value)}
        gh.graphql(
            """mutation($projectId:ID!,$itemId:ID!,$fieldId:ID!,$value:ProjectV2FieldValue!){
                 updateProjectV2ItemFieldValue(
                   input:{projectId:$projectId, itemId:$itemId, fieldId:$fieldId, value:$value}){ item{id} }
               }""",
            {"projectId": project.id, "itemId": item_id, "fieldId": meta["id"], "value": mutation_value},
        )


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------


def bootstrap(gh: Gh, root: Path, repo: str, owner: str, project_number: int | None,
              apply_changes: bool) -> tuple[list[dict], list[str]]:
    """Preview (default) or create the project, fields, views and label."""
    packages = load_source(root)
    components = sorted({p.component for p in packages})
    ops: list[dict] = []
    notes: list[str] = []
    existing: dict | None = None
    if project_number:
        state = fetch_project(gh, owner, project_number)
        if state.title != PROJECT_TITLE:
            raise ProjectsError(
                f"project #{project_number} is titled '{state.title}', expected '{PROJECT_TITLE}'"
            )
        existing = {"id": state.id, "number": state.number}
        notes.append(f"configuring existing project '{PROJECT_TITLE}' #{project_number}")
    else:
        existing = find_project_by_title(gh, owner, PROJECT_TITLE)
        if existing:
            notes.append(f"project exists: '{PROJECT_TITLE}' #{existing['number']}")
    project_id = existing["id"] if existing else "<pending>"
    plan_fields(gh, ops, project_id, components)
    plan_views(ops, project_id)
    plan_label(gh, ops, repo)
    if not apply_changes:
        return ops, notes
    return execute_bootstrap(gh, ops, repo, owner, project_id, notes)


def find_project_by_title(gh: Gh, owner: str, title: str) -> dict | None:
    owner_type = gh.rest(f"users/{owner}").get("type")
    root = "organization" if owner_type == "Organization" else "user"
    query = f"""query($login:String!,$cursor:String){{
      {root}(login:$login){{
        projectsV2(first:100,after:$cursor){{pageInfo{{hasNextPage endCursor}}nodes{{id title number url}}}}
      }}
    }}"""
    variables: dict[str, Any] = {"login": owner, "cursor": None}
    while True:
        data = gh.graphql(query, variables)
        conn = data[root]["projectsV2"]
        for node in conn["nodes"]:
            if node["title"] == title:
                return node
        if not conn["pageInfo"]["hasNextPage"]:
            return None
        variables["cursor"] = conn["pageInfo"]["endCursor"]


def plan_fields(gh: Gh, ops: list, project_id: str, components: list[str]) -> None:
    """Derive the field operations the project still needs (idempotent)."""
    for spec in (
        {"name": FIELD_WORK_PACKAGE, "dataType": "TEXT"},
        {"name": FIELD_COMPONENT, "dataType": "SINGLE_SELECT", "options": components},
        {"name": FIELD_PHASE, "dataType": "SINGLE_SELECT", "options": PHASE_OPTIONS},
        {"name": FIELD_EFFORT, "dataType": "NUMBER"},
        {"name": FIELD_DEPENDS_ON, "dataType": "TEXT"},
    ):
        ops.append({"op": "ensure_field", **spec})
    ops.append({"op": "ensure_status_options", "options": STATUS_OPTIONS})
    if project_id == "<pending>":
        return
    fields = fetch_project_fields(gh, project_id)
    for op in ops:
        if op["op"] == "ensure_status_options" and "Status" in fields:
            have = {o["name"] for o in fields["Status"]["options"]}
            op["field_id"] = fields["Status"]["id"]
            op["missing"] = [o for o in op["options"] if o not in have]
            op["removed"] = sorted(have - set(op["options"]))
            op["preserve_ids"] = {o["name"]: o["id"] for o in fields["Status"]["options"] if o["name"] in op["options"]}


def fetch_project_fields(gh: Gh, project_id: str) -> dict[str, dict]:
    data = gh.graphql(
        f"""query($id:ID!){{node(id:$id){{... on ProjectV2{{
             {PROJECT_FIELDS_FRAGMENT}
           }}}}}}""",
        {"id": project_id},
    )
    fields: dict[str, dict] = {}
    for node in data["node"]["fields"]["nodes"]:
        entry: dict[str, Any] = {"id": node.get("id"), "dataType": node.get("dataType"), "options": node.get("options") or []}
        fields[node["name"]] = entry
    return fields


def plan_views(ops: list, project_id: str) -> None:
    if project_id == "<pending>":
        for spec in VIEW_SPECS:
            ops.append({"op": "ensure_view", **spec})
        return
    # For an existing project, view existence is checked at execution time.
    for spec in VIEW_SPECS:
        ops.append({"op": "ensure_view", **spec})


def plan_label(gh: Gh, ops: list, repo: str) -> None:
    ops.append({"op": "ensure_label", **BLOCKED_LABEL})


def execute_bootstrap(gh: Gh, ops: list, repo: str, owner: str,
                      project_id: str, notes: list[str]) -> tuple[list[dict], list[str]]:
    for op in ops:
        kind = op["op"]
        if kind == "ensure_field":
            project_id = ensure_field(gh, repo, owner, project_id, op, notes)
        elif kind == "ensure_status_options":
            ensure_status_options(gh, repo, owner, project_id, op, notes)
        elif kind == "ensure_view":
            project_id = ensure_view(gh, repo, owner, project_id, op, notes)
        elif kind == "ensure_label":
            ensure_label(gh, repo, op, notes)
        else:
            raise ProjectsError(f"unknown bootstrap operation: {kind}")
    return ops, notes


def _resolve_project(gh: Gh, repo: str, owner: str, project_id: str) -> str:
    """Create the project on first use and link it to the repository."""
    if project_id != "<pending>":
        return project_id
    owner_type = gh.rest(f"users/{owner}").get("type")
    root = "organization" if owner_type == "Organization" else "user"
    owner_node = gh.graphql(
        f"query($login:String!){{{root}(login:$login){{id}}}}", {"login": owner}
    )[root]["id"]
    created = gh.graphql(
        """mutation($ownerId:ID!,$title:String!){
             createProjectV2(input:{ownerId:$ownerId, title:$title}){
               projectV2{id number resourcePath}
             }
           }""",
        {"ownerId": owner_node, "title": PROJECT_TITLE},
    )["createProjectV2"]["projectV2"]
    gh.graphql(
        """mutation($projectId:ID!,$repositoryId:ID!){
             linkProjectV2ToRepository(input:{projectId:$projectId, repositoryId:$repositoryId}){
               repository{id}
             }
           }""",
        {"projectId": created["id"], "repositoryId": gh.rest(f"repos/{repo}")["node_id"]},
    )
    print(f"created project '{PROJECT_TITLE}' #{created['number']} at https://github.com{created['resourcePath']}")
    return created["id"]


def ensure_field(gh: Gh, repo: str, owner: str, project_id: str, op: dict, notes: list[str]) -> str:
    project_id = _resolve_project(gh, repo, owner, project_id)
    fields = fetch_project_fields(gh, project_id)
    node = fields.get(op["name"])
    if node is None:
        options = [{"name": o} for o in op.get("options", [])]
        if options:
            gh.graphql(
                """mutation($projectId:ID!,$name:String!,$dataType:ProjectV2CustomFieldType!,
                            $options:[ProjectV2SingleSelectFieldOptionInput!]){
                     createProjectV2Field(input:{projectId:$projectId, name:$name, dataType:$dataType,
                                                singleSelectOptions:$options}){
                       projectV2Field{... on ProjectV2Field{name} ... on ProjectV2SingleSelectField{name id options{name}}}
                     }
                   }""",
                {"projectId": project_id, "name": op["name"], "dataType": op["dataType"], "options": options},
            )
        else:
            gh.graphql(
                """mutation($projectId:ID!,$name:String!,$dataType:ProjectV2CustomFieldType!){
                     createProjectV2Field(input:{projectId:$projectId, name:$name, dataType:$dataType}){
                       projectV2Field{... on ProjectV2Field{name id}}
                     }
                   }""",
                {"projectId": project_id, "name": op["name"], "dataType": op["dataType"]},
            )
        notes.append(f"created field '{op['name']}' ({op['dataType'].lower()})")
        return project_id
    if op["dataType"] == "SINGLE_SELECT":
        have = {o["name"] for o in node["options"]}
        missing = [o for o in op.get("options", []) if o not in have]
        if missing:
            id_by_name = {o["name"]: o["id"] for o in node["options"]}
            payload = [{"id": id_by_name[o], "name": o} if o in id_by_name else {"name": o}
                       for o in sorted(have | set(missing))]
            _update_single_select_options(gh, node["id"], payload)
            notes.append(f"added options to '{op['name']}': {', '.join(missing)}")
    return project_id


def ensure_status_options(gh: Gh, repo: str, owner: str, project_id: str, op: dict, notes: list[str]) -> None:
    project_id = _resolve_project(gh, repo, owner, project_id)
    fields = fetch_project_fields(gh, project_id)
    status = fields.get("Status")
    if status is None:
        raise ProjectsError("the project has no built-in Status field — unexpected; report this")
    have = {o["name"]: o["id"] for o in status["options"]}
    wanted = op["options"]
    if set(have) == set(wanted):
        notes.append("Status options already match")
        return
    payload = [{"id": have[name], "name": name} if name in have else {"name": name} for name in wanted]
    _update_single_select_options(gh, status["id"], payload)
    notes.append(f"Status options set to: {' → '.join(wanted)}")


def ensure_view(gh: Gh, repo: str, owner: str, project_id: str, op: dict, notes: list[str]) -> str:
    project_id = _resolve_project(gh, repo, owner, project_id)
    data = gh.graphql(
        """query($id:ID!){node(id:$id){... on ProjectV2{views(first:50){nodes{id name layout filter}}}}}""",
        {"id": project_id},
    )
    existing = {v["name"]: v for v in data["node"]["views"]["nodes"]}
    node = existing.get(op["name"])
    if node is None:
        created = gh.graphql(
            """mutation($projectId:ID!,$name:String!,$layout:ProjectV2ViewLayout!){
                 createProjectV2View(input:{projectId:$projectId, name:$name, layout:$layout}){
                   projectV2View{id name layout}
                 }
               }""",
            {"projectId": project_id, "name": op["name"], "layout": op["layout"]},
        )["createProjectV2View"]["projectV2View"]
        node = {"id": created["id"], "name": created["name"], "layout": created["layout"], "filter": ""}
        notes.append(f"created view '{op['name']}' ({op['layout'].lower()})")
    if (node.get("filter") or "") != op.get("filter", ""):
        gh.graphql(
            """mutation($viewId:ID!,$filter:String!){
                 updateProjectV2View(input:{viewId:$viewId, filter:$filter}){projectV2View{name filter}}
               }""",
            {"viewId": node["id"], "filter": op["filter"]},
        )
        notes.append(f"set filter for view '{op['name']}'")
    notes.append(f"view '{op['name']}': manual step — {op['manual']}")
    return project_id


def ensure_label(gh: Gh, repo: str, op: dict, notes: list[str]) -> None:
    try:
        existing = gh.rest(f"repos/{repo}/labels/{op['name']}")
    except GhError as exc:
        if "404" not in str(exc) and "Not Found" not in str(exc):
            raise
        existing = None
    if existing is None:
        gh.rest(f"repos/{repo}/labels", method="POST",
                body={"name": op["name"], "color": op["color"], "description": op["description"]})
        notes.append(f"created label '{op['name']}'")
    else:
        notes.append(f"label '{op['name']}' exists")


def _update_single_select_options(gh: Gh, field_id: str, payload: list[dict]) -> None:
    """Rewrite a single-select field's options, preserving ids where names match.

    Preserving ids keeps existing items' selections intact when bootstrap is
    re-run after items have been imported."""
    options = [{"id": o["id"], "name": o["name"]} if o.get("id") else {"name": o["name"]} for o in payload]
    gh.graphql(
        """mutation($fieldId:ID!,$options:[ProjectV2SingleSelectFieldOptionInput!]){
             updateProjectV2Field(input:{fieldId:$fieldId, singleSelectOptions:$options}){
               projectV2Field{... on ProjectV2SingleSelectField{id options{name}}}
             }
           }""",
        {"fieldId": field_id, "options": options},
    )


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------


def repo_root() -> Path:
    root = Path(os.environ.get("ECTT_ROOT", Path.cwd()))
    if not list(root.glob("PLAN-001-*.md")):
        raise ProjectsError(f"no PLAN-001 document under {root}; run from the repository root or pass --root")
    return root


def load_source(root: Path) -> list[Package]:
    plan_path = next(iter(root.glob("PLAN-001-*.md")), None)
    srs_path = next(iter(root.glob("SRS-001-*.md")), None)
    if plan_path is None or srs_path is None:
        raise ProjectsError(f"PLAN-001/SRS-001 not found under {root}")
    srs = parse_srs(srs_path.read_text(encoding="utf-8"))
    return parse_packages(plan_path.read_text(encoding="utf-8"), srs)


def source_revision(root: Path) -> str:
    env = os.environ.get("GITHUB_SHA")
    if env:
        return env
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, encoding="utf-8",
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except FileNotFoundError:
        pass
    raise ProjectsError(
        "cannot determine the source revision: not a git checkout and GITHUB_SHA is unset. "
        "The importer refuses to write without a recorded source revision."
    )


def run_source_gates(root: Path, python: str | None = None) -> list[str]:
    """Run the existing plan/traceability checks; a failing gate stops the import.

    trace_check runs only when the design tree is present (fixture repositories
    used by the test suite may ship the work plan alone)."""
    gates = ["design/trace/plan_check.py", "design/trace/trace_check.py"]
    interpreter = python or sys.executable
    notes = []
    for gate in gates:
        script = root / gate
        if not script.exists():
            notes.append(f"skipped {gate} (not present)")
            continue
        cmd = [interpreter, str(script)]
        if "trace_check" in gate:
            cmd += ["--check-diagrams", str(root / "design/diagrams")]
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, encoding="utf-8")
        if proc.returncode != 0:
            raise ProjectsError(
                f"source gate {gate} failed — the importer will not propose writes.\n"
                f"{(proc.stdout + proc.stderr).strip()}"
            )
        output = (proc.stdout or proc.stderr).strip()
        notes.append(f"{gate}: {output.splitlines()[-1] if output else 'passed'}")
    return notes


def resolve_repo(args_repo: str | None) -> str:
    if args_repo:
        return args_repo
    env = os.environ.get("GITHUB_REPOSITORY")
    if env:
        return env
    try:
        proc = subprocess.run(
            ["git", "remote", "get-url", "origin"], capture_output=True, text=True, encoding="utf-8",
        )
        match = re.search(r"github\.com[:/](.+?)(?:\.git)?$", proc.stdout.strip())
        if proc.returncode == 0 and match:
            return match.group(1)
    except FileNotFoundError:
        pass
    raise ProjectsError("no repository resolved: pass --repo owner/name or run inside the checkout")


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def render_summary(payload: dict[str, Any]) -> str:
    """Markdown job summary: created / updated / unchanged / conflicting / retired."""
    lines = ["## ECTT project sync", ""]
    if "operations" in payload:  # preview
        counts = payload["counts"]
        totals_ = payload["totals"]
        lines += [
            f"Parsed **{totals_['packages']}** work packages owning **{totals_['requirements_allocated']}** "
            f"requirements ({totals_['dependency_edges']['code']} code / "
            f"{totals_['dependency_edges']['port-mediated']} port-mediated / "
            f"{totals_['dependency_edges']['schedule-only']} schedule-only dependency edges).",
            "",
            "| Outcome | Packages |",
            "|---|---|",
            f"| Created (issues) | {counts['create']} |",
            f"| Updated (issues/items/fields) | {counts['update']} |",
            f"| Unchanged (zero writes) | {counts['unchanged']} |",
            f"| Conflicting | {counts['conflict']} |",
            f"| Retired from source (reported, untouched) | {counts['retired_source']} |",
            "",
            f"Source revision: `{payload['source_revision']}`",
        ]
        if payload["retired_source"]:
            lines += ["", "**Retired from source register** (never closed or deleted; reconcile manually):"]
            lines += [f"- {r['wp']} — issue #{r['issue_number']} ({r['state']})" for r in payload["retired_source"]]
    else:  # apply report
        lines += [
            f"Created {len(payload['created'])} issue(s); applied {len(payload['updated'])} update(s).",
            f"Retired-source packages reported (untouched): {len(payload.get('retired_source', []))}",
        ]
        for item in payload["created"][:20]:
            lines.append(f"- created #{item['issue_number']} {item['wp']}")
        if len(payload["created"]) > 20:
            lines.append(f"- … and {len(payload['created']) - 20} more")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", help="owner/name (default: origin remote or GITHUB_REPOSITORY)")
    common.add_argument("--root", help="repository root (default: cwd)")
    common.add_argument("--gh-path", default=os.environ.get("GH_PATH", "gh"), help="GitHub CLI executable")
    common.add_argument("--owner", help="project owner (default: repo owner; user-owned projects)")
    sub = parser.add_subparsers(dest="command", required=True)

    boot = sub.add_parser("bootstrap", help="preview or create the project, fields, views and label",
                          parents=[common])
    boot.add_argument("--apply", action="store_true", help="create what is missing (default: preview only)")
    boot.add_argument("--project-number", type=int, help="configure this existing project instead of creating one")

    plan = sub.add_parser("plan", help="emit a JSON change preview without mutations", parents=[common])
    plan.add_argument("--output", help="write the preview JSON here (default: stdout)")
    plan.add_argument("--summary-file", help="write a markdown job summary here")
    plan.add_argument("--wp", action="append", help="restrict to these work packages (repeatable)")
    plan.add_argument("--project-number", type=int,
                      default=int(os.environ.get("ECTT_PROJECT_NUMBER", "0") or 0))
    plan.add_argument("--skip-gates", action="store_true", help=argparse.SUPPRESS)

    apply_ = sub.add_parser("apply", help="apply a preview (or plan internally) after re-checking state",
                            parents=[common])
    apply_.add_argument("--preview", help="preview JSON from 'plan' (default: plan internally)")
    apply_.add_argument("--wp", action="append", help="restrict to these work packages (repeatable)")
    apply_.add_argument("--summary-file", help="write a markdown job summary here")
    apply_.add_argument("--project-number", type=int,
                        default=int(os.environ.get("ECTT_PROJECT_NUMBER", "0") or 0))
    apply_.add_argument("--skip-gates", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root) if args.root else repo_root()
    repo = resolve_repo(args.repo)
    owner = args.owner or repo.split("/")[0]
    gh = Gh(args.gh_path)
    try:
        if args.command == "bootstrap":
            ops, notes = bootstrap(gh, root, repo, owner, args.project_number, args.apply)
            for note in notes:
                print(note, file=sys.stderr)
            print(json.dumps({"operations": ops, "notes": notes}, indent=2))
            return 0
        if not args.project_number:
            raise ProjectsError(
                "no project number: pass --project-number or set the ECTT_PROJECT_NUMBER repository variable"
            )
        if args.command == "plan":
            if not args.skip_gates:
                for note in run_source_gates(root):
                    print(note, file=sys.stderr)
            preview = plan_import(gh, root, repo, owner, args.project_number, only=args.wp)
            rendered = json.dumps(preview, indent=2)
            if args.output:
                Path(args.output).write_text(rendered, encoding="utf-8", newline="\n")
                print(f"preview written to {args.output}: {json.dumps(preview['counts'])}", file=sys.stderr)
            else:
                print(rendered)
            if args.summary_file:
                Path(args.summary_file).write_text(render_summary(preview), encoding="utf-8", newline="\n")
            return 0
        if args.command == "apply":
            if not args.skip_gates:
                for note in run_source_gates(root):
                    print(note, file=sys.stderr)
            if args.preview:
                preview = json.loads(Path(args.preview).read_text(encoding="utf-8"))
            else:
                preview = plan_import(gh, root, repo, owner, args.project_number, only=args.wp)
            report = apply_operations(gh, preview, root, repo, owner, args.project_number, only=args.wp)
            summary = render_summary(report)
            if args.summary_file:
                Path(args.summary_file).write_text(summary, encoding="utf-8", newline="\n")
            print(summary)
            return 0
    except ProjectsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

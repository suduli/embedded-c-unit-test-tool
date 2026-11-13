"""Shared fixtures for the GitHub Projects importer tests.

FakeGh is an in-memory GitHub with the same four-method surface the importer
uses (graphql, rest, rest_paginated) — enough to emulate issue listings with
pagination, project fields/items/views, and every mutation the tool issues.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import github_projects as gp  # noqa: E402

REPO = "suduli/embedded-c-unit-test-tool"
OWNER = "suduli"


class FakeGh:
    """In-memory GitHub double. Records every mutation for assertions."""

    def __init__(self):
        self.issues: list[dict] = []          # REST issue objects
        self.next_issue = 100
        self.labels: dict[str, dict] = {}
        self.project: dict | None = None      # {"id","number","title","resourcePath"}
        self.fields: dict[str, dict] = {}     # name -> {"id","dataType","options":[{id,name}]}
        self.items: dict[str, dict] = {}      # item_id -> {"issue_number","field_values"}
        self.views: dict[str, dict] = {}      # name -> {"id","layout","filter"}
        self.mutations: list[tuple[str, dict]] = []
        self.fail_on: list[str] = []          # substrings; matching calls raise GhError
        self.fail_after_n_creates: int | None = None
        self.creates_done = 0
        self._field_seq = 900
        self._item_seq = 500

    # -- failure injection -------------------------------------------------

    def _check_fail(self, marker: str) -> None:
        if any(m in marker for m in self.fail_on):
            raise gp.GhError(f"injected failure on {marker}")

    def _maybe_fail_create(self) -> None:
        """Simulate a run dying mid-way through issue creation."""
        if self.fail_after_n_creates is not None and self.creates_done >= self.fail_after_n_creates:
            raise gp.GhError("injected failure: create API unavailable")

    # -- Gh-compatible surface ---------------------------------------------

    def graphql(self, query: str, variables: dict | None = None) -> dict:
        variables = variables or {}
        for name in sorted(("addProjectV2ItemById", "updateProjectV2ItemFieldValue", "createProjectV2",
                            "createProjectV2Field", "updateProjectV2Field", "createProjectV2View",
                            "updateProjectV2View", "linkProjectV2ToRepository"), key=len, reverse=True):
            if name in query:
                self._check_fail(name)
                return getattr(self, f"_m_{name}")(query, variables)
        if "{user(login:$login){id}}" in query or "{organization(login:$login){id}}" in query:
            return {"user": {"id": "USER_NODE_1"}}
        if "projectV2(number:" in query:
            self._check_fail("fetch_project")
            return self._q_project(query, variables)
        if "projectsV2(first:" in query:
            return self._q_projects(variables)
        if "views(first:50)" in query and "node(id:" in query:
            return {"node": {"views": {"nodes": [
                {"id": v["id"], "name": n, "layout": v["layout"], "filter": v["filter"]}
                for n, v in self.views.items()
            ]}}}
        if "fields(first:100)" in query and "node(id:" in query:
            return {"node": {"fields": {"nodes": [self._field_node(n, f) for n, f in self.fields.items()]}}}
        raise AssertionError(f"FakeGh: unhandled graphql query: {query[:120]}…")

    def rest(self, path: str, method: str = "GET", body: dict | None = None,
             params: dict[str, str] | None = None) -> object:
        self._check_fail(f"rest {path}")
        params = params or {}
        if path == "users/suduli":
            return {"type": "User", "login": OWNER}
        if path == f"repos/{REPO}" and method == "GET":
            return {"node_id": "REPO_NODE_1", "full_name": REPO}
        if path == f"repos/{REPO}/issues" and method == "POST":
            return self._create_issue(body["title"], body["body"])
        if path.startswith(f"repos/{REPO}/issues/") and method == "PATCH":
            number = int(path.rsplit("/", 1)[1])
            issue = next(i for i in self.issues if i["number"] == number)
            issue["title"] = body.get("title", issue["title"])
            issue["body"] = body.get("body", issue["body"])
            return issue
        if path == f"repos/{REPO}/issues":
            state = params.get("state", "open")
            per_page = int(params.get("per_page", "30"))
            page = int(params.get("page", "1"))
            selected = [i for i in self.issues if state == "all" or i["state"] == state]
            start = (page - 1) * per_page
            return selected[start:start + per_page]
        if path == f"repos/{REPO}/labels/blocked":
            if "blocked" in self.labels:
                return self.labels["blocked"]
            raise gp.GhError(f"gh: Not Found (HTTP 404) for {path}")
        if path == f"repos/{REPO}/labels" and method == "POST":
            self.labels[body["name"]] = dict(body)
            return dict(body)
        raise AssertionError(f"FakeGh: unhandled REST call {method} {path}")

    def rest_paginated(self, path: str, params: dict[str, str] | None = None) -> list:
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

    # -- REST model ----------------------------------------------------------

    def _create_issue(self, title: str, body: str) -> dict:
        self._maybe_fail_create()
        self.creates_done += 1
        self.next_issue += 1
        issue = {"number": self.next_issue, "node_id": f"ISSUE_{self.next_issue}",
                 "title": title, "state": "open", "body": body}
        self.issues.append(issue)
        return issue

    def item_for_issue(self, number: int) -> dict:
        return next(it for it in self.items.values() if it["issue_number"] == number)

    def seed_issue(self, title: str, body: str, state: str = "open") -> dict:
        issue = self._create_issue(title, body)
        issue["state"] = state
        return issue

    # -- GraphQL model ---------------------------------------------------------

    def _field_node(self, name: str, meta: dict) -> dict:
        node = {"name": name, "id": meta["id"], "dataType": meta["dataType"]}
        if meta["dataType"] == "SINGLE_SELECT":
            node["options"] = [{"id": o["id"], "name": o["name"]} for o in meta["options"]]
        return node

    def _q_project(self, query: str, variables: dict) -> dict:
        if self.project is None:
            return {"user": {"projectV2": None}}
        item_nodes = []
        for item_id, item in self.items.items():
            issue = next((i for i in self.issues if i["number"] == item["issue_number"]), None)
            if issue is None:
                continue
            fv_nodes = []
            for fname, value in item["field_values"].items():
                meta = self.fields.get(fname)
                if meta is None:
                    continue
                if meta["dataType"] == "SINGLE_SELECT":
                    fv_nodes.append({"field": {"name": fname}, "name": value})
                elif meta["dataType"] == "NUMBER":
                    fv_nodes.append({"field": {"name": fname}, "number": value})
                else:
                    fv_nodes.append({"field": {"name": fname}, "text": value})
            item_nodes.append({"id": item_id, "content": {"number": issue["number"], "title": issue["title"],
                                                          "state": issue["state"]},
                               "fieldValues": {"nodes": fv_nodes}})
        root = "organization" if query.count("organization") else "user"
        return {root: {"projectV2": {
            "id": self.project["id"], "title": self.project["title"],
            "number": self.project["number"], "resourcePath": self.project["resourcePath"],
            "fields": {"nodes": [self._field_node(n, f) for n, f in self.fields.items()]},
            "items": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": item_nodes},
            "views": {"nodes": [{"id": v["id"], "name": n, "layout": v["layout"], "filter": v["filter"]}
                                for n, v in self.views.items()]},
        }}}

    def _q_projects(self, variables: dict) -> dict:
        nodes = []
        if self.project:
            nodes.append({"id": self.project["id"], "title": self.project["title"],
                          "number": self.project["number"], "url": ""})
        return {"user": {"projectsV2": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": nodes}}}

    # -- mutations ---------------------------------------------------------------

    def _m_createProjectV2(self, query, variables):
        self.project = {"id": "PROJ_1", "number": 1, "title": variables["title"],
                        "resourcePath": f"/users/{OWNER}/projects/1"}
        # A real new project comes with a built-in Status single-select.
        self.fields["Status"] = {"id": "FIELD_STATUS", "dataType": "SINGLE_SELECT", "options": [
            {"id": "OPT_TODO", "name": "Todo"},
            {"id": "OPT_INPROG", "name": "In Progress"},
            {"id": "OPT_DONE", "name": "Done"},
        ]}
        return {"createProjectV2": {"projectV2": {"id": "PROJ_1", "number": 1,
                                                  "resourcePath": self.project["resourcePath"]}}}

    def _m_linkProjectV2ToRepository(self, query, variables):
        return {"linkProjectV2ToRepository": {"repository": {"id": "REPO_NODE_1"}}}

    def _m_createProjectV2Field(self, query, variables):
        self._field_seq += 1
        fid = f"FIELD_{self._field_seq}"
        options = [{"id": f"OPT_{self._field_seq}_{i}", "name": o["name"]}
                   for i, o in enumerate(variables.get("options") or [])]
        self.fields[variables["name"]] = {"id": fid, "dataType": variables["dataType"], "options": options}
        return {"createProjectV2Field": {"projectV2Field": {"name": variables["name"], "id": fid}}}

    def _m_updateProjectV2Field(self, query, variables):
        fid = variables["fieldId"]
        target = next((n for n, f in self.fields.items() if f["id"] == fid), None)
        assert target is not None, f"updateProjectV2Field: unknown field id {fid}"
        preserved = {o["id"]: o["name"] for o in self.fields[target]["options"]}
        new_options = []
        for o in variables["options"]:
            oid = o.get("id")
            if oid is None:
                oid = next((k for k, v in preserved.items() if v == o["name"]), None)
            if oid is None:
                self._field_seq += 1
                oid = f"OPT_{self._field_seq}"
            new_options.append({"id": oid, "name": o["name"]})
        self.fields[target]["options"] = new_options
        return {"updateProjectV2Field": {"projectV2Field": {"id": fid, "options": new_options}}}

    def _m_createProjectV2View(self, query, variables):
        self.views[variables["name"]] = {"id": f"VIEW_{variables['name']}",
                                         "layout": variables["layout"], "filter": ""}
        return {"createProjectV2View": {"projectV2View": {"id": self.views[variables["name"]]["id"],
                                                          "name": variables["name"],
                                                          "layout": variables["layout"]}}}

    def _m_updateProjectV2View(self, query, variables):
        for v in self.views.values():
            if v["id"] == variables["viewId"]:
                v["filter"] = variables["filter"]
        return {"updateProjectV2View": {"projectV2View": {"name": "x", "filter": variables["filter"]}}}

    def _m_addProjectV2ItemById(self, query, variables):
        issue = next(i for i in self.issues if i["node_id"] == variables["contentId"])
        self._item_seq += 1
        item_id = f"ITEM_{self._item_seq}"
        self.items[item_id] = {"issue_number": issue["number"], "field_values": {}}
        return {"addProjectV2ItemById": {"item": {"id": item_id}}}

    def _m_updateProjectV2ItemFieldValue(self, query, variables):
        item = self.items[variables["itemId"]]
        field = next(f for f, meta in self.fields.items() if meta["id"] == variables["fieldId"])
        value = variables.get("value") or {}
        option_id = value.get("singleSelectOptionId") or variables.get("optionId")
        if option_id is not None:
            opt = next(o for o in self.fields[field]["options"] if o["id"] == option_id)
            item["field_values"][field] = opt["name"]
        elif value.get("number") is not None:
            item["field_values"][field] = value["number"]
        else:
            item["field_values"][field] = value.get("text")
        return {"updateProjectV2ItemFieldValue": {"item": {"id": variables["itemId"]}}}


_COMPONENTS_CACHE: list[str] | None = None


def register_components() -> list[str]:
    """Component single-select options, derived from the real register once."""
    global _COMPONENTS_CACHE
    if _COMPONENTS_CACHE is None:
        root = Path(__file__).resolve().parents[2]
        _COMPONENTS_CACHE = sorted({p.component for p in gp.load_source(root)})
    return _COMPONENTS_CACHE


def seeded_project(fake: FakeGh) -> FakeGh:
    """A bootstrapped project with the fields/views/label the importer expects."""
    fake.project = {"id": "PROJ_1", "number": 1, "title": gp.PROJECT_TITLE,
                    "resourcePath": f"/users/{OWNER}/projects/1"}
    fake.fields["Status"] = {"id": "FIELD_STATUS", "dataType": "SINGLE_SELECT",
                             "options": [{"id": f"OPT_S{i}", "name": o} for i, o in enumerate(gp.STATUS_OPTIONS)]}
    fake.fields[gp.FIELD_WORK_PACKAGE] = {"id": "FIELD_WP", "dataType": "TEXT", "options": []}
    fake.fields[gp.FIELD_COMPONENT] = {"id": "FIELD_COMP", "dataType": "SINGLE_SELECT",
                                       "options": [{"id": f"OPT_C{i}", "name": o}
                                                   for i, o in enumerate(register_components())]}
    fake.fields[gp.FIELD_PHASE] = {"id": "FIELD_PHASE", "dataType": "SINGLE_SELECT",
                                   "options": [{"id": f"OPT_P{i}", "name": o} for i, o in enumerate(gp.PHASE_OPTIONS)]}
    fake.fields[gp.FIELD_EFFORT] = {"id": "FIELD_EFF", "dataType": "NUMBER", "options": []}
    fake.fields[gp.FIELD_DEPENDS_ON] = {"id": "FIELD_DEP", "dataType": "TEXT", "options": []}
    for spec in gp.VIEW_SPECS:
        fake.views[spec["name"]] = {"id": f"VIEW_{spec['name']}", "layout": spec["layout"], "filter": spec["filter"]}
    return fake


@pytest.fixture
def fake_gh() -> FakeGh:
    return FakeGh()


@pytest.fixture
def bootstrapped() -> FakeGh:
    return seeded_project(FakeGh())


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_fixture_repo(tmp_path: Path, plan_text: str, srs_text: str) -> Path:
    """A minimal source tree for parser-level tests (gates are absent here)."""
    (tmp_path / "PLAN-001-test.md").write_text(plan_text, encoding="utf-8", newline="\n")
    (tmp_path / "SRS-001-test.md").write_text(srs_text, encoding="utf-8", newline="\n")
    return tmp_path


def make_srs(requirements: dict[str, tuple[str, str, str]]) -> str:
    lines = []
    for rid, (pri, phase, ver) in requirements.items():
        lines.append(f"**TOOL-{rid}** *({pri}, {phase}, {ver})* — synthetic requirement {rid}.")
    return "\n\n".join(lines) + "\n"


def make_plan(sections: dict[str, list[tuple]]) -> str:
    """Build a §5.5-shaped plan from {layer: [(wid, cap, comp, phase, effort, reqs, deps, adr)]}."""
    out = ["# Plan", "### 5.5 The work package register", ""]
    for layer, rows in sections.items():
        out.append(f"#### {layer}")
        out.append("")
        reqs_total = sum(len(gp.SHORT_REQ_RE.findall(r[5])) for r in rows)
        efforts = sum(int(r[4]) for r in rows if isinstance(r[4], int))
        out.append(f"{len(rows)} work packages · {reqs_total} requirements · {efforts} person-weeks")
        out.append("")
        out.append("| WP | Capability delivered | Comp | Start | Effort | Reqs | Depends on | ADR |")
        out.append("|---|---|---|:--:|--:|---|---|:--:|")
        for wid, cap, comp, phase, effort, reqs, deps, adr in rows:
            out.append(f"| `{wid}` | {cap} | {comp} | {phase} | {effort}w | {reqs or '—'} | {deps or '—'} | {'●' if adr else ''} |")
        out.append("")
    out.append("## 6. Next")
    return "\n".join(out) + "\n"


def json_roundtrip(payload: dict) -> dict:
    """Apply receives previews through a JSON file; go through that boundary."""
    return json.loads(json.dumps(payload))

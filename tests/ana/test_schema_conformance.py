# verifies: TOOL-PAR-100, TOOL-PAR-110, DSN-ANA-070
"""Conformance of emitted analysis models to the published 1.0 JSON Schema.

This is the first clause of the WP-ANA-04 exit criterion (PLAN-001 5.4): a model
emitted by the analyzer validates against its published schema.
"""

from __future__ import annotations

import copy
import json
from importlib import resources
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from ectt.ana.frontend import ClangFrontend
from ectt.ana.interface import extract_interfaces
from ectt.ana.persist import assemble_analysis_model, write_analysis_model
from ectt.core.determinism import FixedClock
from ectt.core.fs import OutputRoot

SCHEMA_RESOURCE = "analysis-model-1.0.schema.json"

HEADER = """\
typedef unsigned short u16;
typedef struct { u16 raw; int ch; } sample_t;
struct node { struct node *next; int v; };
typedef enum { MODE_A, MODE_B = 4 } mode_t;
typedef int (*handler_fn)(const sample_t *s, void *ctx);
union word { u16 half[2]; unsigned int full; };
"""

GOOD_UNIT = """\
#include "api.h"
static int s_count;
int g_level;
static int helper(int x) { s_count++; return x; }
int process(sample_t s, struct node *n, mode_t m, handler_fn cb, union word w, const int buf[4]) {
    g_level = helper(s.raw) + n->v + (int)m + (int)w.full + buf[0];
    return cb ? cb(&s, &g_level) : 0;
}
"""

BAD_UNIT = "int broken(void) { return undeclared_symbol; }\n"


def _load_schema() -> dict[str, Any]:
    text = resources.files("ectt.ana.schema").joinpath(SCHEMA_RESOURCE).read_text(encoding="utf-8")
    return json.loads(text)


@pytest.fixture
def emitted_doc(tmp_path: Path) -> dict[str, Any]:
    """A written-and-reloaded model covering parsed and failed units and every type kind."""
    (tmp_path / "include").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "include" / "api.h").write_text(HEADER, encoding="utf-8")
    (tmp_path / "src" / "good.c").write_text(GOOD_UNIT, encoding="utf-8")
    (tmp_path / "src" / "bad.c").write_text(BAD_UNIT, encoding="utf-8")

    fe = ClangFrontend()
    args = ["-I", str(tmp_path / "include"), "-std=c11"]
    good = fe.parse(tmp_path / "src" / "good.c", args=args, working_directory=tmp_path)
    bad = fe.parse(tmp_path / "src" / "bad.c", args=args, working_directory=tmp_path)
    assert good.status == "parsed", [str(d) for d in good.diagnostics]
    assert bad.status == "failed"

    model = assemble_analysis_model(
        [extract_interfaces(good, working_directory=tmp_path), bad],
        clock=FixedClock("2026-09-27T12:00:00Z"),
        source_root=tmp_path,
    )
    out = OutputRoot(tmp_path / "out", source_roots=[tmp_path / "src"])
    path = write_analysis_model(out, "analysis/model.json", model)
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_ships_as_package_data() -> None:
    """verifies: TOOL-PAR-110"""
    assert resources.files("ectt.ana.schema").joinpath(SCHEMA_RESOURCE).is_file()
    jsonschema.Draft202012Validator.check_schema(_load_schema())


def test_emitted_model_validates_against_published_schema(emitted_doc: dict[str, Any]) -> None:
    """verifies: TOOL-PAR-100, TOOL-PAR-110"""
    kinds = {t["kind"] for t in emitted_doc["types"].values()}
    assert {"struct", "union", "enum", "typedef", "pointer", "array", "function_pointer", "builtin"} <= kinds
    assert {u["status"] for u in emitted_doc["units"]} == {"parsed", "failed"}

    errors = sorted(
        jsonschema.Draft202012Validator(_load_schema()).iter_errors(emitted_doc),
        key=lambda e: list(e.absolute_path),
    )
    assert not errors, "\n".join(f"{list(e.absolute_path)}: {e.message}" for e in errors)


@pytest.mark.parametrize(
    "mutation",
    [
        pytest.param(lambda d: d.__setitem__("schema_version", "one"), id="malformed-version"),
        pytest.param(lambda d: d["units"][0].__setitem__("status", "ok"), id="unknown-status"),
        pytest.param(lambda d: _first_fn(d).__setitem__("linkage", "global"), id="unknown-linkage"),
        pytest.param(lambda d: _first_fn(d).__setitem__("return_type", "int"), id="non-ref-type"),
        pytest.param(lambda d: _first_fn(d)["globals"][0].__setitem__("access", "x"), id="unknown-access"),
        pytest.param(lambda d: d["capabilities"].__setitem__("cfg", True), id="cfg-claimed"),
        pytest.param(lambda d: d["types"].__setitem__("int", {"kind": "builtin"}), id="unprefixed-type-id"),
        pytest.param(lambda d: d["provenance"]["inputs"][0].__setitem__("digest", "abc"), id="short-digest"),
    ],
)
def test_schema_rejects_contract_violations(emitted_doc: dict[str, Any], mutation: Any) -> None:
    """verifies: TOOL-PAR-110 -- the schema constrains the S1 contract, it is not vacuous."""
    doc = copy.deepcopy(emitted_doc)
    mutation(doc)
    assert list(jsonschema.Draft202012Validator(_load_schema()).iter_errors(doc))


def test_writer_emits_only_schema_declared_keys(emitted_doc: dict[str, Any]) -> None:
    """verifies: TOOL-PAR-100 -- the dataclass model and the published schema have not drifted."""
    undeclared: list[str] = []
    _collect_undeclared(emitted_doc, _load_schema(), "$", undeclared)
    assert not undeclared, f"keys emitted but not declared in the schema: {undeclared}"


def _first_fn(doc: dict[str, Any]) -> dict[str, Any]:
    return next(f for u in doc["units"] for f in u["functions"] if f["globals"])


def _collect_undeclared(value: Any, schema: dict[str, Any], where: str, out: list[str]) -> None:
    if isinstance(value, dict):
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties")
        for key, child in value.items():
            if key in props:
                _collect_undeclared(child, props[key], f"{where}.{key}", out)
            elif isinstance(extra, dict):
                _collect_undeclared(child, extra, f"{where}[{key!r}]", out)
            else:
                out.append(f"{where}.{key}")
    elif isinstance(value, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(value):
            _collect_undeclared(item, schema["items"], f"{where}[{i}]", out)

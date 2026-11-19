# implements: DSN-ING-120
"""Authored link plan validation (WP-ING-07, TASK-010).

Spec clauses mapped to tests:
- DSN-ING-120 / TOOL-ING-200: a plan is required; the compilation database alone never defines the link.
- Unresolved input blocks the build with a diagnostic that names the entry.
- Fail closed: a plan with any violation is refused whole; every violation is reported.
- Identity: each input's recorded sha256 is checked against the file.
- Confinement: inputs stay inside the project; absolute paths and '..' are refused.

Verifies: TOOL-ING-200, DSN-ING-120.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from ectt.ing.linkplan import (
    KNOWN_TOOLCHAINS,
    LinkPlan,
    LinkPlanError,
    link_plan_relpath,
    load_link_plan,
    validate_link_plan,
)
from ectt.prj.errors import AnchorForbiddenError
from ectt.prj.yaml_adapter import RestrictedYamlAdapter

OBJ_BYTES = b"object-bytes"
LIB_BYTES = b"archive-bytes"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "adc.o").write_bytes(OBJ_BYTES)
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "libm.a").write_bytes(LIB_BYTES)
    return tmp_path


def _plan(**overrides: Any) -> dict[str, Any]:
    """A valid plan document; keyword overrides replace top-level keys (None removes them)."""
    doc: dict[str, Any] = {
        "schema_version": "1",
        "scope": "adc",
        "toolchain": "gcc",
        "linker": {"identity": "GNU ld 2.42"},
        "runtime": "host",
        "entry_point": "main",
        "link_command": ["gcc", "-o", "adc.exe"],
        "inputs": [
            {"kind": "object", "path": "build/adc.o", "identity": _sha(OBJ_BYTES)},
            {"kind": "archive", "path": "lib/libm.a", "identity": _sha(LIB_BYTES)},
        ],
    }
    for key, value in overrides.items():
        if value is None:
            doc.pop(key, None)
        else:
            doc[key] = value
    return doc


def _reasons(exc: LinkPlanError) -> list[str]:
    return [v.reason for v in exc.violations]


def test_valid_plan_loads_with_ordered_inputs_and_identities(project: Path) -> None:
    """verifies: TOOL-ING-200 — a valid plan yields its inputs in authored order with identities."""
    plan = validate_link_plan(_plan(), project_root=project, scope="adc")

    assert isinstance(plan, LinkPlan)
    assert [i.path for i in plan.inputs] == ["build/adc.o", "lib/libm.a"]
    assert [i.kind for i in plan.inputs] == ["object", "archive"]
    assert plan.inputs[0].identity == _sha(OBJ_BYTES)
    assert plan.link_command == ("gcc", "-o", "adc.exe")
    assert plan.linker_identity == "GNU ld 2.42"


def test_plan_is_read_from_the_project_store(project: Path) -> None:
    """verifies: TOOL-ING-200 — the authored plan is loaded from link-plans/<scope>.yaml."""
    target = project / "link-plans"
    target.mkdir()
    (target / "adc.yaml").write_text(
        "schema_version: 1\n"
        "scope: adc\n"
        "toolchain: gcc\n"
        "linker:\n"
        "  identity: GNU ld 2.42\n"
        "runtime: host\n"
        "entry_point: main\n"
        "link_command:\n"
        "  - gcc\n"
        "  - -o\n"
        "  - adc.exe\n"
        "inputs:\n"
        "  - kind: object\n"
        f"    path: build/adc.o\n"
        f"    identity: {_sha(OBJ_BYTES)}\n",
        encoding="utf-8",
    )

    plan = load_link_plan(project, "adc")

    assert plan.inputs[0].path == "build/adc.o"
    assert link_plan_relpath("adc") == "link-plans/adc.yaml"


def test_missing_plan_is_refused_with_named_reason(project: Path) -> None:
    """verifies: TOOL-ING-200 — no plan means no build; the refusal is named."""
    with pytest.raises(LinkPlanError) as exc_info:
        load_link_plan(project, "adc")

    assert exc_info.value.reason == "link_plan_invalid"
    assert _reasons(exc_info.value) == ["missing_plan"]


def test_compilation_database_alone_is_not_a_link_plan(project: Path) -> None:
    """verifies: DSN-ING-120 — a plan with no inputs is refused: the compdb does not define the link."""
    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(_plan(inputs=[]), project_root=project, scope="adc")

    assert _reasons(exc_info.value) == ["no_link_inputs"]


def test_missing_object_blocks_and_names_the_entry(project: Path) -> None:
    """verifies: DSN-ING-120 — an unresolved input blocks the build with a diagnostic naming it."""
    doc = _plan()
    doc["inputs"][0]["path"] = "build/gone.o"

    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(doc, project_root=project, scope="adc")

    [violation] = exc_info.value.violations
    assert violation.reason == "missing_object"
    assert violation.entry == "inputs[0]"
    assert "build/gone.o" in violation.detail


def test_duplicate_input_is_refused(project: Path) -> None:
    """verifies: TOOL-ING-200 — the same input may not appear twice in the ordered link."""
    doc = _plan()
    doc["inputs"].append(dict(doc["inputs"][0]))

    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(doc, project_root=project, scope="adc")

    assert _reasons(exc_info.value) == ["duplicate_input"]


def test_unknown_toolchain_key_is_refused(project: Path) -> None:
    """verifies: TOOL-ING-200 — an unknown toolchain key is refused, never guessed."""
    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(_plan(toolchain="tcc-2001"), project_root=project, scope="adc")

    assert _reasons(exc_info.value) == ["unknown_toolchain_key"]
    assert "gcc" in KNOWN_TOOLCHAINS


@pytest.mark.parametrize("absolute", ["/usr/lib/libc.a", "C:/toolchain/libc.a", "C:\\toolchain\\libc.a"])
def test_absolute_path_is_refused(project: Path, absolute: str) -> None:
    """verifies: TOOL-ING-200 — inputs must be project-relative."""
    doc = _plan()
    doc["inputs"][1]["path"] = absolute

    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(doc, project_root=project, scope="adc")

    assert _reasons(exc_info.value) == ["absolute_path"]


def test_path_escaping_the_project_is_refused(project: Path) -> None:
    """verifies: TOOL-ING-200 — an input may not reach outside the project root."""
    doc = _plan()
    doc["inputs"][0]["path"] = "../outside/adc.o"

    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(doc, project_root=project, scope="adc")

    assert _reasons(exc_info.value) == ["path_outside_project"]


def test_identity_mismatch_is_refused(project: Path) -> None:
    """verifies: TOOL-ING-200 — a resolved identity must match the file on disk."""
    doc = _plan()
    doc["inputs"][0]["identity"] = _sha(b"something else")

    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(doc, project_root=project, scope="adc")

    assert _reasons(exc_info.value) == ["identity_mismatch"]


@pytest.mark.parametrize("bad", ["abc", "G" * 64, _sha(OBJ_BYTES).upper()])
def test_malformed_identity_is_refused(project: Path, bad: str) -> None:
    """verifies: TOOL-ING-200 — identities are sha256 lowercase hex, nothing else."""
    doc = _plan()
    doc["inputs"][0]["identity"] = bad

    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(doc, project_root=project, scope="adc")

    assert _reasons(exc_info.value) == ["invalid_identity"]


def test_unknown_input_kind_and_unknown_key_are_refused(project: Path) -> None:
    """verifies: DSN-ING-120 — unknown semantic values fail closed."""
    doc = _plan()
    doc["inputs"][0]["kind"] = "framework"
    doc["inputs"][1]["surprise"] = True

    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(doc, project_root=project, scope="adc")

    assert _reasons(exc_info.value) == ["unknown_input_kind", "unknown_field"]


def test_unknown_top_level_key_is_refused(project: Path) -> None:
    """verifies: DSN-ING-120 — a writable reader never silently drops fields."""
    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(_plan(extra="x"), project_root=project, scope="adc")

    assert _reasons(exc_info.value) == ["unknown_field"]


def test_unsupported_schema_version_and_scope_mismatch_are_refused(project: Path) -> None:
    """verifies: DSN-ING-120 — version and scope are checked before anything is used."""
    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(_plan(schema_version="2", scope="other"), project_root=project, scope="adc")

    assert _reasons(exc_info.value) == ["unsupported_schema_version", "scope_mismatch"]


def test_missing_linker_runtime_entry_and_command_are_each_named(project: Path) -> None:
    """verifies: TOOL-ING-200 — linker identity, runtime, entry point and link command are required."""
    doc = _plan(linker=None, runtime=None, entry_point=None, link_command=None)

    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(doc, project_root=project, scope="adc")

    assert [v.entry for v in exc_info.value.violations] == ["linker", "runtime", "entry_point", "link_command"]
    assert set(_reasons(exc_info.value)) == {"missing_field"}


def test_every_violation_is_reported_in_one_run_in_document_order(project: Path) -> None:
    """verifies: DSN-ING-120 — validation collects all violations, so one run shows every problem."""
    doc = _plan(toolchain="nope")
    doc["inputs"] = [
        {"kind": "object", "path": "build/gone.o", "identity": _sha(OBJ_BYTES)},
        {"kind": "object", "path": "/abs/x.o", "identity": _sha(OBJ_BYTES)},
        {"kind": "object", "path": "build/adc.o", "identity": "bad"},
    ]

    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(doc, project_root=project, scope="adc")

    assert _reasons(exc_info.value) == [
        "unknown_toolchain_key",
        "missing_object",
        "absolute_path",
        "invalid_identity",
    ]


def test_invalid_plan_never_partially_loads(project: Path) -> None:
    """verifies: DSN-ING-120 — a refused plan returns nothing; the valid inputs are not kept."""
    doc = _plan()
    doc["inputs"][1]["path"] = "lib/nope.a"

    result: object = None
    with pytest.raises(LinkPlanError):
        result = validate_link_plan(doc, project_root=project, scope="adc")
    assert result is None


def test_error_carries_the_relative_plan_path_not_an_absolute_one(project: Path) -> None:
    """verifies: TOOL-ING-200 — diagnostics stay free of absolute paths (NFR-090 determinism)."""
    doc = _plan()
    doc["inputs"][0]["path"] = "build/gone.o"

    with pytest.raises(LinkPlanError) as exc_info:
        validate_link_plan(doc, project_root=project, scope="adc", path="link-plans/adc.yaml")

    assert str(project) not in str(exc_info.value)
    assert "adc.yaml" in str(exc_info.value)


def test_unsafe_scope_name_is_refused(project: Path) -> None:
    """verifies: TOOL-ING-200 — a scope name cannot steer the plan path outside link-plans/."""
    with pytest.raises(LinkPlanError) as exc_info:
        load_link_plan(project, "../adc")

    assert _reasons(exc_info.value) == ["invalid_scope_name"]


def test_plan_with_yaml_anchor_is_refused_by_the_restricted_adapter(project: Path) -> None:
    """verifies: TOOL-ING-200 — the plan uses the restricted YAML dialect (ADR-002)."""
    target = project / "link-plans"
    target.mkdir()
    (target / "adc.yaml").write_text("schema_version: &v 1\nscope: adc\n", encoding="utf-8")

    with pytest.raises(AnchorForbiddenError) as exc_info:
        load_link_plan(project, "adc", adapter=RestrictedYamlAdapter())

    assert exc_info.value.reason

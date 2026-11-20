# implements: TOOL-PLG-090
"""Inspection checklist: built-ins ride the public extension points (WP-PLG-03).

TOOL-PLG-090 (inspection): the tool's own built-in compiler configurations,
framework back-ends, and report formats must be implemented through the same
public extension points available to users, so those interfaces are proven
by use.

Each audit exercises the shared registration path with both a built-in and a
user-supplied provider: the same registry class, the same validation, the
same namespace, the same duplicate refusal. A family that grows a private
bypass fails the checklist here.

The audits import the implementing families lazily: plg defines the
contract names, the families implement them, and an import cycle at module
load would blur that direction.

Satisfies: TOOL-PLG-090.
"""

from __future__ import annotations

from dataclasses import dataclass

from ectt.plg.points import (
    CONTRACT_COMPILER_CONFIG,
    CONTRACT_FRAMEWORK_BACKEND,
    CONTRACT_REPORT_FORMAT,
)

__all__ = [
    "BuiltinAudit",
    "audit_all",
    "audit_builtin_compiler_configs",
    "audit_builtin_framework_backends",
    "audit_builtin_report_formats",
]

_USER_COMPILER_CONFIG_YAML = """\
schema_version: 1
name: audit-cc
family: gcc
invocation:
  executable: cc-audit
flags:
  debug: ["-g"]
  optimization:
    none: ["-O0"]
    size: ["-Os"]
    speed: ["-O2"]
output:
  object_suffix: ".o"
  executable_suffix: ""
coverage:
  kinds: [line]
  flags:
    line: ["--coverage"]
"""


@dataclass(frozen=True)
class BuiltinAudit:
    """One family's shared-path evidence."""

    family: str
    point_id: str
    contract: str
    evidence: str
    ok: bool


def audit_builtin_report_formats() -> BuiltinAudit:
    """The built-in text/json formats register through the public registry."""
    from ectt.core.determinism import FixedClock
    from ectt.exh.results import ExecutionMetadata, ResultSet
    from ectt.rep.errors import ReportModelError
    from ectt.rep.formats import default_format_registry
    from ectt.rep.model import build_report_model, coverage_entry
    from ectt.rep.render import render_json, render_text

    registry = default_format_registry()
    # Same namespace: a user provider registers alongside the built-ins.
    registry.register("mine", lambda model: "user format output")
    # Same validation: re-registering a built-in name is refused exactly as
    # re-registering a user name would be.
    duplicate_refused = False
    try:
        registry.register("text", render_text)
    except ReportModelError:
        duplicate_refused = True
    # Same public path: the built-ins render byte-identically to the direct
    # renderers, so nothing bypassed the registry.
    model = build_report_model(
        ResultSet(run_id="audit", execution=ExecutionMetadata(where="h", toolchain="gcc")),
        coverage=(coverage_entry("u.c", 1, 2),),
        clock=FixedClock("2026-11-19T00:00:00+00:00"),
    )
    renders_identical = registry.render(model, "text") == render_text(model) and (
        registry.render(model, "json") == render_json(model)
    )
    ok = registry.names() == ("json", "mine", "text") and duplicate_refused and renders_identical
    evidence = (
        f"user provider co-registered: names={registry.names()}; "
        f"duplicate 'text' refused: {duplicate_refused}; "
        f"built-ins byte-identical to public renderers: {renders_identical}"
    )
    return BuiltinAudit(
        family="report_formats",
        point_id="report_formats",
        contract=CONTRACT_REPORT_FORMAT,
        evidence=evidence,
        ok=ok,
    )


def audit_builtin_framework_backends() -> BuiltinAudit:
    """The built-in Unity/cmocka back-ends register through the descriptor path."""
    from ectt.gen.backends import (
        BackendRegistry,
        DuplicateBackendError,
        register_framework_builtins,
    )

    registry = BackendRegistry()
    register_framework_builtins(registry)
    # Same namespace: a user descriptor registers alongside the built-ins.
    registry.register_descriptor(
        {
            "backend_id": "audit-framework",
            "framework_header": "audit.h",
            "template": "/* user template */\n#include \"{uut_header}\"\n{test_invocations}\n",
        }
    )
    # Same validation: a built-in id is refused twice, like any user id.
    duplicate_refused = False
    try:
        registry.register_descriptor(
            {
                "backend_id": "unity",
                "framework_header": "unity.h",
                "template": "/* duplicate */\n#include \"{uut_header}\"\n",
            }
        )
    except DuplicateBackendError:
        duplicate_refused = True
    ok = registry.list_ids() == ("audit-framework", "cmocka", "unity") and duplicate_refused
    evidence = (
        f"user descriptor co-registered: ids={registry.list_ids()}; "
        f"duplicate 'unity' refused: {duplicate_refused}"
    )
    return BuiltinAudit(
        family="framework_backends",
        point_id="framework_backends",
        contract=CONTRACT_FRAMEWORK_BACKEND,
        evidence=evidence,
        ok=ok,
    )


def audit_builtin_compiler_configs() -> BuiltinAudit:
    """The built-in gcc/clang configurations register through the public registry."""
    from ectt.tch.builtin import register_host_builtins
    from ectt.tch.config import CompilerConfigRegistry, load_compiler_config_text
    from ectt.tch.errors import DuplicateCompilerConfigError

    registry = CompilerConfigRegistry()
    register_host_builtins(registry)
    # Same validator, same namespace: the user config is loaded through the
    # public text loader and registered next to the built-ins.
    user_config = load_compiler_config_text(_USER_COMPILER_CONFIG_YAML)
    registry.register(user_config)
    # Same validation: a reused name is refused regardless of origin.
    duplicate_refused = False
    try:
        registry.register(user_config)
    except DuplicateCompilerConfigError:
        duplicate_refused = True
    names = registry.list_names()
    ok = {"gcc", "clang", "audit-cc"}.issubset(set(names)) and duplicate_refused
    evidence = (
        f"user config co-registered through the public loader: names={names}; "
        f"duplicate 'audit-cc' refused: {duplicate_refused}"
    )
    return BuiltinAudit(
        family="compiler_configs",
        point_id="compiler_configs",
        contract=CONTRACT_COMPILER_CONFIG,
        evidence=evidence,
        ok=ok,
    )


def audit_all() -> tuple[BuiltinAudit, ...]:
    """Run the whole checklist in family order."""
    return (
        audit_builtin_compiler_configs(),
        audit_builtin_framework_backends(),
        audit_builtin_report_formats(),
    )

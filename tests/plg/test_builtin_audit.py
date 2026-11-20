# implements: TOOL-PLG-090
"""Built-ins implemented through public extension points (WP-PLG-03).

The inspection checklist is machine-checked: every built-in family is
exercised through the same registration path a user provider takes — same
registry class, same validation, same namespace, same duplicate refusal.
"""

from __future__ import annotations

import pytest

from ectt.plg.builtin_audit import (
    audit_all,
    audit_builtin_compiler_configs,
    audit_builtin_framework_backends,
    audit_builtin_report_formats,
)
from ectt.plg.points import default_registry


@pytest.mark.parametrize(
    "audit_fn",
    [audit_builtin_compiler_configs, audit_builtin_framework_backends, audit_builtin_report_formats],
    ids=["compiler_configs", "framework_backends", "report_formats"],
)
def test_builtin_family_rides_the_public_extension_point(audit_fn: object) -> None:
    audit = audit_fn()  # type: ignore[operator]

    assert audit.ok, f"family '{audit.family}' failed the shared-path checklist: {audit.evidence}"
    assert audit.evidence, "the audit must name what it exercised"


def test_audit_points_exist_in_the_public_registry() -> None:
    known = {point.point_id for point in default_registry().list_points()}

    for audit in audit_all():
        assert audit.point_id in known


def test_audit_is_deterministic() -> None:
    first = audit_all()
    second = audit_all()

    assert first == second


def test_report_format_audit_proves_shared_namespace_and_rendering() -> None:
    audit = audit_builtin_report_formats()

    assert audit.ok
    assert "names=('json', 'mine', 'text')" in audit.evidence
    assert "duplicate 'text' refused: True" in audit.evidence
    assert "byte-identical" in audit.evidence


def test_framework_backend_audit_proves_shared_descriptor_path() -> None:
    audit = audit_builtin_framework_backends()

    assert audit.ok
    assert "ids=('audit-framework', 'cmocka', 'unity')" in audit.evidence
    assert "duplicate 'unity' refused: True" in audit.evidence


def test_compiler_config_audit_proves_shared_loader_and_namespace() -> None:
    audit = audit_builtin_compiler_configs()

    assert audit.ok
    assert "audit-cc" in audit.evidence
    assert "duplicate 'audit-cc' refused: True" in audit.evidence

"""Tests for the WP-GEN-11 call wrapping of intra-unit calls.

Verifies: TOOL-STB-090.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.gen import (
    CallWrapPlan,
    GenError,
    NotInternalCalleeError,
    plan_call_wraps,
    render_call_wrap_seam,
)


def test_wrap_plan_covers_internal_callees() -> None:
    """verifies: TOOL-STB-090"""
    plan = plan_call_wraps(("helper", "validate"), ("validate",))
    assert isinstance(plan, CallWrapPlan)
    assert plan.wrapped == ("validate",)
    assert plan.internal_callees == ("helper", "validate")


def test_wrap_request_for_external_callee_is_named_error() -> None:
    """verifies: TOOL-STB-090"""
    with pytest.raises(NotInternalCalleeError) as excinfo:
        plan_call_wraps(("helper",), ("memset",))
    assert "intra-unit" in str(excinfo.value)


def test_seam_redirects_without_user_source_modification() -> None:
    """verifies: TOOL-STB-090"""
    plan = plan_call_wraps(("helper", "validate"), ("helper", "validate"))
    seam = render_call_wrap_seam(plan, uut_source="uut.c")
    assert "/* ectt:call-wrap: intra-unit call wrapping (generated seam). */" in seam
    assert "user source is never modified" in seam
    assert "#define helper ectt_wrap_helper" in seam
    assert "#define validate ectt_wrap_validate" in seam
    assert '#include "uut.c"' in seam
    assert "#undef helper" in seam
    assert "#undef validate" in seam
    # The order guarantees interception inside the include only.
    define_pos = seam.index("#define helper")
    include_pos = seam.index('#include "uut.c"')
    undef_pos = seam.index("#undef helper")
    assert define_pos < include_pos < undef_pos


def test_empty_wrap_plan_renders_empty_seam() -> None:
    """verifies: TOOL-STB-090"""
    plan = plan_call_wraps(("helper",), ())
    assert render_call_wrap_seam(plan) == ""
    assert plan.wrapped == ()


def test_duplicate_requests_deduplicated() -> None:
    """verifies: TOOL-STB-090"""
    plan = plan_call_wraps(("helper",), ("helper", "helper"))
    assert plan.wrapped == ("helper",)


def test_plan_is_frozen_and_deterministic() -> None:
    """verifies: TOOL-STB-090"""
    first = plan_call_wraps(("b", "a"), ("a",))
    second = plan_call_wraps(("a", "b"), ("a",))
    assert first.to_dict() == second.to_dict()
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.wrapped = ()  # type: ignore[misc]


def test_error_derives_from_gen_error() -> None:
    """verifies: TOOL-STB-090"""
    assert issubclass(NotInternalCalleeError, GenError)

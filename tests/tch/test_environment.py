"""Tests for the WP-TCH-07 first-run environment verification.

Covers: toolchain presence (missing and resolved), feature availability
(unsupported and available), clear deterministic reporting, injectable
resolution, first-run marker detection, and serialisation.

Verifies: TOOL-INS-080.
"""

from __future__ import annotations

import pytest

from ectt.tch import (
    STATUS_MISSING,
    STATUS_OK,
    STATUS_UNSUPPORTED,
    EnvironmentReport,
    EnvironmentRequirement,
    first_run_needed,
    verify_environment,
)


def _resolver(paths: dict[str, str]):
    return paths.get


def _requirements() -> tuple[EnvironmentRequirement, ...]:
    return (
        EnvironmentRequirement(kind="toolchain", target="gcc", config="gcc"),
        EnvironmentRequirement(kind="toolchain", target="clang", config="clang"),
        EnvironmentRequirement(kind="feature", target="mcdc"),
    )


def test_missing_executable_is_reported_missing() -> None:
    """verifies: TOOL-INS-080"""
    report = verify_environment(
        (EnvironmentRequirement(kind="toolchain", target="gcc", config="gcc"),),
        executable_resolver=_resolver({}),
    )
    result = report.results[0]
    assert result.status == STATUS_MISSING
    assert "gcc" in result.detail
    assert "not found" in result.detail


def test_resolved_executable_is_reported_ok() -> None:
    """verifies: TOOL-INS-080"""
    report = verify_environment(
        (EnvironmentRequirement(kind="toolchain", target="gcc", config="gcc"),),
        executable_resolver=_resolver({"gcc": "/usr/bin/gcc"}),
    )
    result = report.results[0]
    assert result.status == STATUS_OK
    assert "/usr/bin/gcc" in result.detail


def test_undeclared_feature_is_reported_unsupported() -> None:
    """verifies: TOOL-INS-080"""
    report = verify_environment(
        (EnvironmentRequirement(kind="feature", target="mcdc"),),
        feature_availability={},
    )
    result = report.results[0]
    assert result.status == STATUS_UNSUPPORTED
    assert "not declared" in result.detail


def test_declared_unavailable_feature_is_reported_unsupported() -> None:
    """verifies: TOOL-INS-080"""
    report = verify_environment(
        (EnvironmentRequirement(kind="feature", target="mcdc"),),
        feature_availability={"mcdc": False},
    )
    assert report.results[0].status == STATUS_UNSUPPORTED


def test_available_feature_is_reported_ok() -> None:
    """verifies: TOOL-INS-080"""
    report = verify_environment(
        (EnvironmentRequirement(kind="feature", target="mcdc"),),
        feature_availability={"mcdc": True},
    )
    assert report.results[0].status == STATUS_OK


def test_mixed_report_names_what_is_missing_or_unsupported() -> None:
    """verifies: TOOL-INS-080"""
    report = verify_environment(
        _requirements(),
        feature_availability={},
        executable_resolver=_resolver({"gcc": "/usr/bin/gcc"}),
    )
    lines = report.render().splitlines()
    assert len(lines) == 3
    assert any("clang" in line and "missing" in line for line in lines)
    assert any("mcdc" in line and "unsupported" in line for line in lines)
    assert any("gcc" in line and "ok" in line for line in lines)


def test_report_is_sorted_and_deterministic() -> None:
    """verifies: TOOL-INS-080"""
    report = verify_environment(
        _requirements(),
        feature_availability={},
        executable_resolver=_resolver({}),
    )
    assert report.to_dict() == verify_environment(
        _requirements(),
        feature_availability={},
        executable_resolver=_resolver({}),
    ).to_dict()
    keys = [(r.requirement.kind, r.requirement.target) for r in report.results]
    assert keys == sorted(keys)


def test_missing_or_unsupported_selects_non_ok() -> None:
    """verifies: TOOL-INS-080"""
    report = verify_environment(
        _requirements(),
        feature_availability={},
        executable_resolver=_resolver({"gcc": "/usr/bin/gcc"}),
    )
    non_ok = report.missing_or_unsupported()
    assert {r.requirement.target for r in non_ok} == {"clang", "mcdc"}


def test_declared_version_is_reported() -> None:
    """verifies: TOOL-INS-080"""
    report = verify_environment(
        (
            EnvironmentRequirement(
                kind="toolchain",
                target="gcc",
                config="gcc",
                declared_version="14.1",
            ),
        ),
        executable_resolver=_resolver({"gcc": "/usr/bin/gcc"}),
    )
    assert "14.1" in report.results[0].detail


def test_unknown_requirement_kind_is_rejected() -> None:
    """verifies: TOOL-INS-080"""
    with pytest.raises(ValueError):
        EnvironmentRequirement(kind="psychic", target="x")


def test_blank_target_is_rejected() -> None:
    """verifies: TOOL-INS-080"""
    with pytest.raises(ValueError):
        EnvironmentRequirement(kind="toolchain", target="  ")


def test_first_run_needed_for_missing_marker(tmp_path) -> None:
    """verifies: TOOL-INS-080"""
    assert first_run_needed(tmp_path / "absent.marker") is True


def test_first_run_not_needed_for_present_marker(tmp_path) -> None:
    """verifies: TOOL-INS-080"""
    marker = tmp_path / "ectt.marker"
    marker.write_text("run\n", encoding="utf-8")
    assert first_run_needed(marker) is False


def test_report_type_is_frozen() -> None:
    """verifies: TOOL-INS-080"""
    import dataclasses

    report = verify_environment(
        (EnvironmentRequirement(kind="feature", target="mcdc"),),
        feature_availability={},
    )
    assert isinstance(report, EnvironmentReport)
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.results = ()  # type: ignore[misc]

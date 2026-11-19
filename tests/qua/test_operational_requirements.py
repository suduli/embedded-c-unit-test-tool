"""Tool Operational Requirements specification tests (WP-QUA-02).

Verifies: TOOL-QUA-020.
"""

from __future__ import annotations

import pathlib

import pytest

from ectt.qua.operational_requirements import (
    KnownLimitation,
    OperatingEnvironmentFact,
    OperationalRequirements,
    SpecificationError,
    default_specification,
    render,
)


def test_specification_has_the_three_required_sections() -> None:
    """verifies: TOOL-QUA-020

    The rendered specification carries all three required sections: intended
    use, operating environment, known limitations.
    """
    text = render(default_specification())
    assert "Intended use:" in text
    assert "Operating environment:" in text
    assert "Known limitations:" in text


def test_intended_use_is_open_not_decided() -> None:
    """verifies: TOOL-QUA-020 (ADR-sensitive boundary)

    Intended use is recorded as OPEN pending WP-QUA-01; no use class is
    claimed by the night run.
    """
    assert default_specification().intended_use.startswith("OPEN")
    assert "WP-QUA-01" in default_specification().intended_use


def test_environment_facts_cite_srs_ids() -> None:
    """verifies: TOOL-QUA-020

    Every operating-environment fact traces to a TOOL-* SRS requirement id.
    """
    spec = default_specification()
    assert spec.environment
    for fact in spec.environment:
        assert fact.srs_id.startswith("TOOL-")


def test_limitations_cite_repository_evidence() -> None:
    """verifies: TOOL-QUA-020

    Every known limitation cites a verification note that exists in the
    repository.
    """
    spec = default_specification()
    assert spec.limitations
    for limitation in spec.limitations:
        assert pathlib.Path(limitation.evidence).is_file(), limitation.evidence


def test_render_is_deterministic() -> None:
    """verifies: TOOL-QUA-020

    Rendering twice is byte-identical.
    """
    assert render(default_specification()) == render(default_specification())


def test_unsourced_entries_are_refused() -> None:
    """verifies: TOOL-QUA-020 (fail-closed)

    An environment fact without an SRS id, or a limitation without
    evidence, is refused — the specification cannot silently carry
    unsourced claims.
    """
    bad_env = OperationalRequirements(
        environment=(OperatingEnvironmentFact(statement="runs anywhere", srs_id="trust-me"),),
    )
    with pytest.raises(SpecificationError):
        render(bad_env)
    bad_limit = OperationalRequirements(
        limitations=(KnownLimitation(statement="nothing known", evidence=""),),
    )
    with pytest.raises(SpecificationError):
        render(bad_limit)

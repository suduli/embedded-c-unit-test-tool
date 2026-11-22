# implements: TOOL-COV-130, TOOL-PRJ-040
"""Coverage threshold configuration in the project store (B3).

An optional ``coverage_thresholds`` section of the project data; absent
means no thresholds. Minimums are exact fraction strings — floats are
refused in the file and in memory.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from ectt.cov.thresholds import MetricThreshold
from ectt.prj.errors import ProjectError
from ectt.prj.model import PROJECT_KIND, ProjectDocument
from ectt.prj.project import PROJECT_ROOT_MARKER, Project
from ectt.prj.thresholds import (
    CoverageThresholdConfig,
    coverage_thresholds_from_data,
    coverage_thresholds_to_data,
)


def test_absent_section_is_a_no_op() -> None:
    """verifies: B3 — projects written before this section load unchanged."""
    assert coverage_thresholds_from_data({"name": "alpha"}) is None
    assert coverage_thresholds_from_data({}) is None


def test_round_trip_through_the_project_store(tmp_path: object) -> None:
    """verifies: B3 — write section, save, reload, load identical thresholds
    (loaded in deterministic metric order, whatever the file key order)."""
    thresholds = [
        MetricThreshold(metric="branches", minimum=Fraction(1, 2)),
        MetricThreshold(metric="statements", minimum=Fraction(4, 5)),
    ]
    data = {
        "schema_version": "1",
        "name": "alpha",
        "source_roots": ["src"],
        "output_root": "build",
        "settings": {},
    }
    data["coverage_thresholds"] = coverage_thresholds_to_data(thresholds, ("branches",))
    project = Project.create(tmp_path / "p", name="alpha", source_roots=["src"], overwrite=True)  # type: ignore[arg-type]
    project.save_file(PROJECT_ROOT_MARKER, data)
    reloaded = Project(project.root, ProjectDocument(PROJECT_KIND, data, schema_version="1")).read_file(PROJECT_ROOT_MARKER)
    config = coverage_thresholds_from_data(reloaded.data)
    assert config is not None
    assert config == CoverageThresholdConfig(
        thresholds=tuple(thresholds),
        allow_not_applicable=("branches",),
    )
    # the section round-trips through the saved file's own text
    saved_text = (project.root / PROJECT_ROOT_MARKER).read_text(encoding="utf-8")
    assert "coverage_thresholds" in saved_text
    assert "4/5" in saved_text


def test_float_minimum_in_file_is_refused() -> None:
    """verifies: B3 — a YAML float minimum is refused, never silently converted."""
    data = {"coverage_thresholds": {"metrics": {"statements": 0.8}}}
    with pytest.raises(ProjectError) as exc_info:
        coverage_thresholds_from_data(data)
    assert exc_info.value.reason == "float_threshold_minimum"


def test_decimal_string_minimum_is_refused() -> None:
    """A decimal string is a float in disguise: only exact fractions are accepted."""
    data = {"coverage_thresholds": {"metrics": {"statements": "0.8"}}}
    with pytest.raises(ProjectError) as exc_info:
        coverage_thresholds_from_data(data)
    assert exc_info.value.reason == "invalid_threshold_minimum"
    with pytest.raises(ProjectError) as exc_info:
        coverage_thresholds_from_data(
            {"coverage_thresholds": {"metrics": {"statements": "8e-1"}}}
        )
    assert exc_info.value.reason == "invalid_threshold_minimum"


def test_unknown_metric_is_refused() -> None:
    with pytest.raises(ProjectError) as exc_info:
        coverage_thresholds_from_data({"coverage_thresholds": {"metrics": {"conditions": "1/1"}}})
    assert exc_info.value.reason == "unknown_threshold_metric"
    with pytest.raises(ProjectError) as exc_info:
        coverage_thresholds_from_data(
            {"coverage_thresholds": {"metrics": {"statements": "1/1"},
                                     "allow_not_applicable": ["conditions"]}}
        )
    assert exc_info.value.reason == "unknown_threshold_metric"


def test_malformed_section_is_refused() -> None:
    with pytest.raises(ProjectError) as exc_info:
        coverage_thresholds_from_data({"coverage_thresholds": "yes"})
    assert exc_info.value.reason == "invalid_threshold_section"
    with pytest.raises(ProjectError) as exc_info:
        coverage_thresholds_from_data({"coverage_thresholds": {"metrics": {}}})
    assert exc_info.value.reason == "empty_threshold_section"
    with pytest.raises(ProjectError) as exc_info:
        coverage_thresholds_from_data({"coverage_thresholds": {"metrics": {"statements": "1/0"}}})
    assert exc_info.value.reason == "invalid_threshold_minimum"


def test_in_memory_round_trip_is_exact() -> None:
    thresholds = [MetricThreshold(metric="statements", minimum=Fraction(9, 10))]
    section = coverage_thresholds_to_data(thresholds, ("branches",))
    config = coverage_thresholds_from_data({"coverage_thresholds": section})
    assert config is not None
    assert config.thresholds == tuple(thresholds)
    assert config.allow_not_applicable == ("branches",)
    assert section["metrics"]["statements"] == "9/10"

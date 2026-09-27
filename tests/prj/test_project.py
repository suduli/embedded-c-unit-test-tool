# implements: DSN-PRJ-010, DSN-PRJ-040, DSN-PRJ-030
"""Tests for Project root lifecycle, atomic persistence, comment preservation, and relocation.

Verifies: TOOL-PRJ-010, TOOL-PRJ-020, TOOL-PRJ-050, TOOL-PRJ-070, TOOL-UIX-320, TOOL-CIC-080.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import pytest

from ectt.prj.errors import (
    CommentPreservationError,
    ProjectError,
    ProjectLocationError,
    ProjectRootNotFoundError,
)
from ectt.prj.project import PROJECT_ROOT_MARKER, Project


def test_project_create_and_no_metadata_leak(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-010, TOOL-PRJ-020, TOOL-PRJ-050, DSN-PRJ-030"""
    proj_dir = tmp_path / "test_proj"
    project = Project.create(
        proj_dir,
        name="alpha_project",
        source_roots=["src", "include"],
        output_root="build/ectt",
        settings={"target": "host"},
    )

    assert project.marker_path.exists()
    assert project.name == "alpha_project"
    assert project.schema_version == 1
    assert project.source_roots == ["src", "include"]
    assert project.output_root == "build/ectt"
    assert project.settings == {"target": "host"}

    marker_content = project.marker_path.read_text(encoding="utf-8")

    # Strictly verify NO timestamps, hostnames, usernames, or absolute paths
    forbidden_terms = [
        "timestamp",
        "created_at",
        "date",
        "hostname",
        "username",
        "user",
        str(proj_dir).replace("\\", "/"),
    ]
    for term in forbidden_terms:
        assert term not in marker_content.lower()


def test_project_open_and_find_upward(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-010, DSN-PRJ-010"""
    proj_dir = tmp_path / "root_proj"
    project = Project.create(proj_dir, name="root_proj")

    # Open directly
    opened = Project.open(proj_dir)
    assert opened.name == "root_proj"
    assert opened.schema_version == 1

    # Find from root
    found_root = Project.find(proj_dir)
    assert found_root.root == proj_dir.resolve()

    # Find from deeply nested child directory
    nested_dir = proj_dir / "src" / "adc" / "filters"
    nested_dir.mkdir(parents=True)
    found_nested = Project.find(nested_dir)
    assert found_nested.root == proj_dir.resolve()

    # Find from non-project directory raises ProjectRootNotFoundError
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    with pytest.raises(ProjectRootNotFoundError):
        Project.find(other_dir)


def test_project_location_guards(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-070, DSN-PRJ-040"""
    proj_dir = tmp_path / "guarded_proj"
    project = Project.create(
        proj_dir,
        source_roots=["src"],
        output_root="build/ectt",
    )

    # Creating user source and output dirs
    (proj_dir / "src").mkdir(parents=True)
    (proj_dir / "build" / "ectt").mkdir(parents=True)

    # Attempt to write a project file inside source root must be rejected
    with pytest.raises(ProjectLocationError) as exc_info_src:
        project.save_file("src/invalid.scope", {"schema_version": "1"})
    assert "source root" in exc_info_src.value.message

    # Attempt to write a project file inside output root must be rejected
    with pytest.raises(ProjectLocationError) as exc_info_out:
        project.save_file("build/ectt/invalid.scope", {"schema_version": "1"})
    assert "output root" in exc_info_out.value.message


def test_comment_overwrite_refusal_and_override(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-010, TOOL-PRJ-050, DSN-PRJ-030"""
    proj_dir = tmp_path / "comment_proj"
    project = Project.create(proj_dir)

    # Author a project file externally with comments
    scope_file = proj_dir / "scopes" / "test.scope"
    scope_file.parent.mkdir(parents=True)
    scope_file.write_text(
        'schema_version: "1"\n'
        '# This rationale was added by an engineer\n'
        'name: "adc_scope"\n',
        encoding="utf-8",
    )

    # 1. Attempting to overwrite without discard_comments=True must raise CommentPreservationError
    update_data = {
        "schema_version": "1",
        "name": "adc_scope_updated",
    }
    with pytest.raises(CommentPreservationError) as exc_info:
        project.save_file("scopes/test.scope", update_data)

    assert exc_info.value.line == 2
    assert "comments cannot be preserved" in exc_info.value.message

    # Verify file was NOT modified
    assert "adc_scope_updated" not in scope_file.read_text(encoding="utf-8")

    # 2. Overwrite with discard_comments=True must succeed
    project.save_file("scopes/test.scope", update_data, discard_comments=True)
    updated_content = scope_file.read_text(encoding="utf-8")
    assert "adc_scope_updated" in updated_content
    assert "# This rationale" not in updated_content


def test_byte_identical_resave_preserves_mtime(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-050, DSN-PRJ-030"""
    proj_dir = tmp_path / "mtime_proj"
    project = Project.create(proj_dir, name="mtime_proj")

    initial_mtime = project.marker_path.stat().st_mtime_ns

    # Small delay to ensure any mtime change would be detectable
    time.sleep(0.01)

    # Resave without modifications
    project.save()

    new_mtime = project.marker_path.stat().st_mtime_ns
    assert initial_mtime == new_mtime


def test_project_relocation(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-070, TOOL-UIX-320, TOOL-CIC-080, DSN-PRJ-040.

    Creates a project, copies the entire directory tree to another location,
    re-opens it, and verifies that all relative references resolve identically.
    """
    orig_dir = tmp_path / "original_tree" / "project"
    relocated_dir = tmp_path / "relocated_tree" / "project"

    project = Project.create(
        orig_dir,
        name="relocatable_project",
        source_roots=["src/adc", "include"],
        output_root="build/ectt",
        settings={"compiler": "gcc"},
    )

    # Add an authored file in project tree
    project.save_file(
        "scopes/driver.scope",
        {
            "schema_version": "1",
            "name": "driver_scope",
            "units": ["src/adc/adc.c"],
        },
    )

    # Verify resolution in original location
    orig_src_path = project.resolve_path("src/adc/adc.c")
    assert orig_src_path == orig_dir.resolve() / "src" / "adc" / "adc.c"

    # Copy the whole tree to relocated_dir
    shutil.copytree(orig_dir, relocated_dir)

    # Re-open project from relocated directory
    relocated_project = Project.open(relocated_dir)

    assert relocated_project.name == "relocatable_project"
    assert relocated_project.source_roots == ["src/adc", "include"]
    assert relocated_project.output_root == "build/ectt"

    # Verify that all references now resolve relative to relocated_dir
    relocated_src_path = relocated_project.resolve_path("src/adc/adc.c")
    assert relocated_src_path == relocated_dir.resolve() / "src" / "adc" / "adc.c"
    assert relocated_src_path != orig_src_path

    # Read authored file in relocated project
    doc = relocated_project.read_file("scopes/driver.scope")
    assert doc["name"] == "driver_scope"
    assert doc["units"] == ["src/adc/adc.c"]

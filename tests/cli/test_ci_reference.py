"""Reference CI pipeline and artifact-cache contract tests (WP-CLI-04).

Verifies: TOOL-CIC-050, TOOL-CIC-070.
"""

from __future__ import annotations

import textwrap

import yaml

from ectt.cli.ci_reference import (
    CACHE_KEY_SOURCE,
    GITHUB_ACTIONS_PIPELINE,
    GITLAB_CI_PIPELINE,
    cacheable_artifacts,
)


def _parse(template: str) -> dict[str, object]:
    return yaml.safe_load(textwrap.dedent(template))


def test_both_reference_pipelines_exist_and_parse() -> None:
    """verifies: TOOL-CIC-050

    A valid YAML pipeline exists for both GitHub Actions and GitLab CI.
    """
    github = _parse(GITHUB_ACTIONS_PIPELINE)
    gitlab = _parse(GITLAB_CI_PIPELINE)
    assert "jobs" in github
    assert "ectt-verify" in gitlab
    assert gitlab["stages"] == ["verify"]


def test_pipelines_invoke_documented_cli_entry() -> None:
    """verifies: TOOL-CIC-050

    Both templates drive the tool through its documented non-interactive
    entry: ``python -m ectt.cli`` (TOOL-CIC-010/020 contract).
    """
    assert "python -m ectt.cli" in GITHUB_ACTIONS_PIPELINE
    assert "python -m ectt.cli" in GITLAB_CI_PIPELINE


def test_pipelines_react_to_stable_exit_codes() -> None:
    """verifies: TOOL-CIC-050, TOOL-CIC-030

    Both templates document the stable exit-code table so CI authors can
    react to test/coverage/tool failures distinctly.
    """
    for template in (GITHUB_ACTIONS_PIPELINE, GITLAB_CI_PIPELINE):
        assert "TOOL-CIC-030" in template
        assert "10 test failure" in template
        assert "11 coverage threshold failure" in template
        assert "1 tool error" in template


def test_cacheable_artifacts_cover_ingestion_and_analysis() -> None:
    """verifies: TOOL-CIC-070

    The machine-readable artifact set covers both the ingestion outputs and
    the analysis models, inside the tool's output area.
    """
    artifacts = cacheable_artifacts()
    assert any("ingestion" in path for path in artifacts)
    assert any("analysis" in path for path in artifacts)
    assert all(path.startswith(".ectt/output/") for path in artifacts)


def test_templates_cache_exactly_the_artifact_set() -> None:
    """verifies: TOOL-CIC-070

    Both templates cache exactly the artifact set the tool declares — no
    stale paths, no missing paths. GitHub carries them in a cache step's
    ``path`` block, GitLab in the job-level ``cache.paths``.
    """
    expected = [path.rstrip("/") for path in cacheable_artifacts()]
    for template in (GITHUB_ACTIONS_PIPELINE, GITLAB_CI_PIPELINE):
        parsed = _parse(template)
        text = str(parsed)
        for path in expected:
            assert path in text, path
    gitlab_cache_paths = _parse(GITLAB_CI_PIPELINE)["ectt-verify"]["cache"]["paths"]
    assert sorted(str(p).rstrip("/") for p in gitlab_cache_paths) == sorted(expected)


def test_cache_key_is_derived_from_compilation_database() -> None:
    """verifies: TOOL-CIC-070

    The cache key is derived from the compilation database: cached derived
    artifacts invalidate exactly when their inputs change.
    """
    assert CACHE_KEY_SOURCE == "compile_commands.json"
    assert "compile_commands.json" in GITHUB_ACTIONS_PIPELINE
    assert "compile_commands.json" in GITLAB_CI_PIPELINE

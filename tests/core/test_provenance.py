"""Provenance record and version identification (WP-CORE-04, TASK-013).

Verifies: TOOL-QUA-060, TOOL-INS-110.

Cases: the record carries tool, interpreter, dependency, schema and input facts;
the digest is stable and changes with any hashed fact; the timestamp is never
hashed; the build identifier comes from the environment; the version report
answers a request without touching the record.
"""

from __future__ import annotations

import json
import platform
from datetime import UTC, datetime

import pytest

import ectt.core.provenance as provenance_module
from ectt.core.determinism import FixedClock
from ectt.core.provenance import (
    BUILD_ID_ENV,
    UNKNOWN_BUILD_ID,
    ProvenanceRecord,
    build_provenance,
    tool_version,
    version_report,
)


@pytest.fixture(autouse=True)
def _no_build_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(BUILD_ID_ENV, raising=False)


def _record(**overrides: object) -> ProvenanceRecord:
    kwargs: dict[str, object] = {
        "dependencies": {"libclang": "18.1.8"},
        "schema_versions": {"analysis-model": "1.4"},
        "input_digests": {"src/a.c": "a" * 64},
    }
    kwargs.update(overrides)
    return build_provenance(**kwargs)  # type: ignore[arg-type]


def test_record_carries_tool_interpreter_dependency_schema_and_input_facts() -> None:
    """verifies: TOOL-QUA-060 — every fact needed to reproduce the artifact is present."""
    payload = _record().to_dict()

    assert payload["tool_version"] == tool_version()
    assert payload["python_version"] == platform.python_version()
    assert payload["dependencies"] == {"libclang": "18.1.8"}
    assert payload["schema_versions"] == {"analysis-model": "1.4"}
    assert payload["input_digests"] == {"src/a.c": "a" * 64}
    assert payload["build_id"] == UNKNOWN_BUILD_ID


def test_digest_is_stable_for_identical_facts() -> None:
    """verifies: TOOL-QUA-060 — identical facts give an identical digest, run after run."""
    assert _record().digest == _record().digest


def test_digest_changes_with_any_hashed_fact() -> None:
    """verifies: TOOL-QUA-060 — a changed input, dependency, schema or build changes the digest."""
    base = _record().digest

    assert _record(input_digests={"src/a.c": "b" * 64}).digest != base
    assert _record(dependencies={"libclang": "19.0.0"}).digest != base
    assert _record(schema_versions={"analysis-model": "1.3"}).digest != base


def test_timestamp_is_recorded_but_never_hashed() -> None:
    """verifies: TOOL-QUA-060 — generated_at is informational; two clocks give the same digest."""
    early = build_provenance(
        clock=FixedClock(datetime(2026, 1, 1, tzinfo=UTC)),
        input_digests={"a": "1" * 64},
    )
    late = build_provenance(
        clock=FixedClock(datetime(2030, 6, 1, tzinfo=UTC)),
        input_digests={"a": "1" * 64},
    )

    assert early.generated_at != late.generated_at
    assert early.digest == late.digest
    assert "generated_at" not in early.hashed_portion()
    assert early.to_dict()["generated_at"] == early.generated_at


def test_no_clock_means_no_timestamp_field() -> None:
    """verifies: TOOL-QUA-060 — without a clock the record is fully deterministic."""
    payload = _record().to_dict()

    assert "generated_at" not in payload


def test_canonical_json_is_byte_identical_across_runs() -> None:
    """verifies: TOOL-QUA-060 — the serialised record is identical for identical facts."""
    from ectt.core.determinism import canonical_json

    first = canonical_json(_record().to_dict())
    second = canonical_json(_record().to_dict())

    assert first == second
    assert json.loads(first)["digest"] == _record().digest


def test_dependency_and_input_maps_are_sorted_regardless_of_insertion_order() -> None:
    """verifies: TOOL-QUA-060 — map order cannot change the digest."""
    one = _record(
        dependencies={"b": "2", "a": "1"}, input_digests={"z": "9" * 64, "y": "8" * 64}
    )
    two = _record(
        dependencies={"a": "1", "b": "2"}, input_digests={"y": "8" * 64, "z": "9" * 64}
    )

    assert one.digest == two.digest
    assert list(one.hashed_portion()["dependencies"]) == ["a", "b"]


def test_build_id_comes_from_the_environment_when_recorded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """verifies: TOOL-INS-110 — the build identifier is the one the build recorded."""
    monkeypatch.setenv(BUILD_ID_ENV, "ci-4711")

    assert version_report()["build_id"] == "ci-4711"
    assert _record().hashed_portion()["build_id"] == "ci-4711"


def test_tool_version_is_not_faked_when_the_package_is_not_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """verifies: TOOL-INS-110 — an uninstalled tree reports unknown, never the source constant."""
    import importlib.metadata

    def missing(_name: str) -> str:
        raise importlib.metadata.PackageNotFoundError("ectt")

    monkeypatch.setattr(provenance_module.importlib.metadata, "version", missing)

    assert tool_version() == "unknown"
    assert _record().tool_version == "unknown"


def test_version_report_answers_on_request_with_dependencies() -> None:
    """verifies: TOOL-INS-110 — the report names the tool, its version, build, interpreter and dependencies."""
    report = version_report(dependencies={"libclang": "18.1.8", "python-yaml": "6.0"})

    assert report["tool"] == "ectt"
    assert report["tool_version"] == tool_version()
    assert report["dependencies"] == {"libclang": "18.1.8", "python-yaml": "6.0"}
    assert report["python_version"] == platform.python_version()

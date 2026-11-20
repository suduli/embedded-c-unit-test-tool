# implements: TOOL-MIG-100
"""Interchange format reference (WP-MIG-03): the inspection checklist as tests.

Verifies: TOOL-MIG-100 — every format the tool consumes or produces is
documented to a level permitting independent implementation, and the
documentation cannot drift from the code.
"""

from __future__ import annotations

import json
from dataclasses import replace
from importlib import resources

import jsonschema
import pytest

from ectt.mig.errors import MigError
from ectt.mig.formats import (
    INTERCHANGE_FORMATS,
    FormatSpec,
    check_format_documentation,
    format_by_id,
    render_format_reference,
)

#: Inspection list: every reader or writer of an external format in the tool today.
EXPECTED_FORMATS = {
    "analysis-model",
    "ceedling-project",
    "cmocka-output",
    "fidelity-report",
    "mapped-csv",
    "open-result-export",
    "report-model",
    "requirements-csv",
    "requirements-text",
    "reqif",
    "review-baseline",
    "source-links",
    "test-case-csv",
    "tests-file",
    "unity-output",
}


def test_registry_covers_every_known_reader_and_writer() -> None:
    assert {s.format_id for s in INTERCHANGE_FORMATS} == EXPECTED_FORMATS


def test_the_shipped_documentation_passes_its_own_checklist() -> None:
    assert check_format_documentation() == []


def test_documented_versions_equal_the_versions_in_code() -> None:
    probed = [s for s in INTERCHANGE_FORMATS if s.version_probe is not None]
    assert len(probed) >= 9
    assert all(s.version_probe is not None and s.version_probe() == s.version for s in probed)


def test_every_worked_example_is_accepted_by_its_reader() -> None:
    examples = [s for s in INTERCHANGE_FORMATS if s.example is not None and s.reader is not None]
    assert len(examples) == len(EXPECTED_FORMATS)
    for spec in examples:
        assert spec.reader is not None and spec.example is not None
        spec.reader(spec.example())


@pytest.mark.parametrize("format_id", ["open-result-export", "analysis-model"])
def test_published_schema_accepts_the_worked_example(format_id: str) -> None:
    spec = format_by_id(format_id)
    assert spec.schema is not None and spec.example is not None
    package, path = spec.schema
    schema = json.loads((resources.files(package) / path).read_text(encoding="utf-8"))

    jsonschema.validate(json.loads(spec.example()), schema)


def test_every_consumed_format_has_a_reader_and_every_format_has_evidence() -> None:
    for spec in INTERCHANGE_FORMATS:
        if spec.direction in ("consumed", "both"):
            assert spec.reader is not None, spec.format_id
        assert spec.example is not None or spec.schema is not None, spec.format_id


def test_reference_is_deterministic_and_covers_every_format() -> None:
    text = render_format_reference()
    assert text == render_format_reference()
    for spec in INTERCHANGE_FORMATS:
        assert f"(`{spec.format_id}`)" in text
        assert f"| `{spec.format_id}` |" in text
    assert text.endswith("\n") and "\r" not in text


def test_reference_contains_each_example_verbatim() -> None:
    text = render_format_reference()
    for spec in INTERCHANGE_FORMATS:
        assert spec.example is not None
        assert spec.example().rstrip("\n") in text


def test_reference_order_does_not_depend_on_registry_order() -> None:
    assert render_format_reference(tuple(reversed(INTERCHANGE_FORMATS))) == render_format_reference()


def test_format_by_id_refuses_an_unknown_format() -> None:
    with pytest.raises(MigError) as excinfo:
        format_by_id("no-such-format")
    assert excinfo.value.reason == "unknown_format"


# --- the checklist catches drift -------------------------------------------------------


def _spec(**overrides: object) -> FormatSpec:
    return replace(format_by_id("source-links"), **overrides)  # type: ignore[arg-type]


def test_checklist_flags_a_version_that_no_longer_matches_the_code() -> None:
    problems = check_format_documentation([_spec(version="9")])
    assert any("documented version '9'" in p for p in problems)


def test_checklist_flags_an_example_the_reader_rejects() -> None:
    problems = check_format_documentation([_spec(example=lambda: '{"links_version": "1", "links": 5}')])
    assert any("rejected by its reader" in p for p in problems)


def test_checklist_flags_empty_documentation_fields() -> None:
    problems = check_format_documentation([_spec(grammar=" ", loss_policy="")])
    assert {"source-links: 'grammar' is empty", "source-links: 'loss_policy' is empty"} <= set(problems)


def test_checklist_flags_a_bare_name_without_example_or_schema() -> None:
    problems = check_format_documentation([_spec(example=None)])
    assert any("neither a worked example nor a published schema" in p for p in problems)


def test_checklist_flags_a_consumed_format_without_a_reader() -> None:
    problems = check_format_documentation([_spec(reader=None)])
    assert any("no reader" in p for p in problems)


def test_checklist_flags_a_missing_schema_and_a_bad_vocabulary() -> None:
    problems = check_format_documentation(
        [_spec(schema=("ectt.rep", "schema/missing.json"), direction="sideways", media="binary")]
    )
    joined = " | ".join(problems)
    assert "cannot be read" in joined and "unknown direction" in joined and "unknown media" in joined


def test_checklist_flags_duplicates_and_unprobed_versions() -> None:
    base = format_by_id("source-links")
    problems = check_format_documentation([base, base, replace(base, format_id="other", version_probe=None)])
    joined = " | ".join(problems)
    assert "duplicate format id" in joined and "versioned format without a version probe" in joined


def test_checklist_flags_an_empty_example_and_a_failing_probe() -> None:
    def boom() -> str:
        raise RuntimeError("probe broke")

    problems = check_format_documentation([_spec(example=lambda: "  \n"), _spec(format_id="b", version_probe=boom)])
    joined = " | ".join(problems)
    assert "worked example is empty" in joined and "version probe failed" in joined

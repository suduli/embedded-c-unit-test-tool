"""Qualification artifact template tests (WP-QUA-08).

Verifies: TOOL-QUA-100.
"""

from __future__ import annotations

import pytest

from ectt.qua.templates import (
    QUALIFICATION_TEMPLATES,
    TemplateError,
    render_template,
)


def test_all_four_templates_exist_and_render() -> None:
    """verifies: TOOL-QUA-100

    The four qualification artifact kinds each have a template.
    """
    assert sorted(QUALIFICATION_TEMPLATES) == [
        "classification-record",
        "known-error-list",
        "qualification-plan",
        "qualification-test-report",
    ]
    for name in QUALIFICATION_TEMPLATES:
        assert render_template(name).startswith("#")


def test_every_template_section_has_placeholders() -> None:
    """verifies: TOOL-QUA-100

    Each template carries explicit <<placeholder>> markers — the user fills
    their own context; nothing is prefabricated.
    """
    for name, skeleton in QUALIFICATION_TEMPLATES.items():
        assert "<<" in skeleton and ">>" in skeleton, name
        assert skeleton.count("<<") >= 3, f"too few placeholders in {name}"


def test_templates_contain_no_fabricated_facts() -> None:
    """verifies: TOOL-QUA-100

    Templates never assert a completed classification: the placeholder
    markers mark every spot the user must fill.
    """
    for name, skeleton in QUALIFICATION_TEMPLATES.items():
        if name == "classification-record":
            assert "<<TI 1/2/3" in skeleton
            assert "<<TD 1/2/3" in skeleton
            assert "<<TCL" in skeleton


def test_templates_claim_no_compliance() -> None:
    """verifies: TOOL-QUA-100 (overclaim guard)

    No template states compliance, satisfaction, certification, or
    qualification on the user's behalf.
    """
    for name in QUALIFICATION_TEMPLATES:
        lowered = render_template(name).lower()
        for token in ("satisfies", "compliant", "certified", "is qualified", "fulfils"):
            assert token not in lowered, (name, token)


def test_render_is_deterministic() -> None:
    """verifies: TOOL-QUA-100

    Rendering twice is byte-identical.
    """
    for name in QUALIFICATION_TEMPLATES:
        assert render_template(name) == render_template(name)


def test_unknown_template_is_refused() -> None:
    """verifies: TOOL-QUA-100

    An unknown template name is refused with the known names listed.
    """
    with pytest.raises(TemplateError, match=r"unknown template"):
        render_template("nonexistent")

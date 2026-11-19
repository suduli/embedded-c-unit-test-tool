"""Templates for the user's own tool qualification artifacts (WP-QUA-08).

TOOL-QUA-100: the tool shall provide templates for the user's own tool
qualification artifacts. Templates are skeletons with explicit
``<<placeholder>>`` markers only — the factual content (classification,
safety context, results) is the user's, filled in their qualification
context. Compliance-claim language is refused; the classification-dependent
prefill stays empty until the WP-QUA-01 decision exists.

Satisfies: TOOL-QUA-100.
"""

from __future__ import annotations

__all__ = [
    "QUALIFICATION_TEMPLATES",
    "TemplateError",
    "render_template",
]

_QUALIFICATION_PLAN = """\
# Qualification Plan (template)

Tool: <<tool name and version>>
Qualifier: <<organisation and role>>
Standards context: <<standards and clauses in scope>>

## 1. Scope of qualification
<<what is being qualified, for which intended use — fill after the
classification decision (WP-QUA-01)>>

## 2. Tool classification record
Tool impact (TI): <<TI determination with rationale>>
Tool error detection (TD): <<TD determination with rationale>>
Tool confidence level (TCL): <<TCL and any needed qualification measures>>

## 3. Qualification activities
<<planned activities, mapped to the classification measures; cite the
tool capabilities used, e.g. via docs/verification/*.md notes>>

## 4. Acceptance criteria
<<who accepts what, and on which evidence>>
"""

_CLASSIFICATION_RECORD = """\
# Tool Classification Record (template)

Tool: <<tool name and version>>
Classification basis: <<standard clause ids applied>>

## Tool impact (TI)
<<TI 1/2/3 with the rationale from the intended use>>

## Tool error detection (TD)
<<TD 1/2/3 with the rationale from the detection measures>>

## Tool confidence level (TCL)
<<TCL resulting from the TI/TD combination per the applied standard>>

## Resulting qualification measures
<<measures required by the TI/TD combination>>

## Confirmation
Decided by: <<name, role, date>>
"""

_KNOWN_ERROR_LIST = """\
# Known Error List (template)

Tool version: <<version>>
Release: <<release identifier>>

## Known errors
| ID | Description | Workaround | Affected capability | Status |
|---|---|---|---|---|
| <<KE-001>> | <<description>> | <<workaround or none>> | <<capability>> | <<open/mitigated>> |

## Excluded functionality
<<functionality explicitly outside the qualified scope, if any>>
"""

_QUALIFICATION_TEST_REPORT = """\
# Qualification Test Report (template)

Tool version: <<version>>
Test environment: <<environment description>>

## Executed qualification cases
| Case | Objective | Expected | Observed | Verdict |
|---|---|---|---|---|
| <<QT-001>> | <<objective>> | <<expected>> | <<observed>> | <<pass/fail>> |

## Deviations and known errors observed
<<reference the known error list entries hit during testing>>

## Conclusion
<<assessment against the acceptance criteria of the qualification plan>>
"""

#: Template name → skeleton text; the four artifact kinds the package names.
QUALIFICATION_TEMPLATES: dict[str, str] = {
    "qualification-plan": _QUALIFICATION_PLAN,
    "classification-record": _CLASSIFICATION_RECORD,
    "known-error-list": _KNOWN_ERROR_LIST,
    "qualification-test-report": _QUALIFICATION_TEST_REPORT,
}

_CLAIM_TOKENS = ("satisfies", "compliant", "certified", "is qualified", "fulfils", "fulfills")


class TemplateError(Exception):
    """Raised for unknown templates or invalid template content."""


def render_template(name: str) -> str:
    """Return template ``name``'s skeleton, validating its content."""
    if name not in QUALIFICATION_TEMPLATES:
        raise TemplateError(
            f"unknown template: {name!r}; known: {sorted(QUALIFICATION_TEMPLATES)}"
        )
    skeleton = QUALIFICATION_TEMPLATES[name]
    _validate_skeleton(name, skeleton)
    return skeleton


def _validate_skeleton(name: str, skeleton: str) -> None:
    if "<<" not in skeleton or ">>" not in skeleton:
        raise TemplateError(f"template {name!r} has no placeholders")
    lowered = skeleton.lower()
    for token in _CLAIM_TOKENS:
        if token in lowered:
            raise TemplateError(
                f"template {name!r} claims '{token}' on the user's behalf; "
                f"templates carry placeholders only (TOOL-QUA-100)"
            )

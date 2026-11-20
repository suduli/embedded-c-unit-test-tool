# implements: TOOL-ATG-040, TOOL-ATG-050, TOOL-ATG-070, TOOL-ATG-080
"""Generated test case lifecycle and validation port (CMP-ATG)."""

from ectt.atg.errors import AtgError
from ectt.atg.lifecycle import (
    BuildOutcome,
    CoverageDelta,
    Discard,
    EngineInfo,
    ExecutionOutcome,
    GenerationCandidate,
    GenerationOutcome,
    TestValidationPort,
    case_marks,
    confirm_expected,
    expected_status,
    format_mark,
    is_machine_generated,
    make_candidate,
    report_marks,
    unreviewed_test_ids,
    validate_candidates,
)

__all__ = [
    "AtgError",
    "BuildOutcome",
    "CoverageDelta",
    "Discard",
    "EngineInfo",
    "ExecutionOutcome",
    "GenerationCandidate",
    "GenerationOutcome",
    "TestValidationPort",
    "case_marks",
    "confirm_expected",
    "expected_status",
    "format_mark",
    "is_machine_generated",
    "make_candidate",
    "report_marks",
    "unreviewed_test_ids",
    "validate_candidates",
]

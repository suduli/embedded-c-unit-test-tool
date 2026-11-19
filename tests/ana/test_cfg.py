"""CFG capability and cyclomatic complexity tests (WP-ANA-05).

Verifies: TOOL-PAR-070 (DSN-ANA-040 degrade contract),
TOOL-PAR-120 (complexity computation).
"""

from __future__ import annotations

from ectt.ana.cfg import (
    CFG_UNAVAILABLE_REASON,
    CfgCapability,
    compute_complexities,
    count_decision_points,
    cyclomatic_complexity,
)
from ectt.ana.model import FunctionModel, SourceLocation

_SIMPLE = "int plain(void) { return 1; }\n"

_BRANCHY = """
int branchy(int x, int y) {
    if (x > 0) {
        return 1;
    }
    for (int i = 0; i < 10; i = i + 1) {
        while (y > 0) {
            y = y - 1;
        }
    }
    switch (x) {
    case 1:
        return 2;
    case 2:
        return 3;
    default:
        break;
    }
    return (x && y) ? 4 : 5;
}
"""


def test_capability_reason_names_the_open_decision() -> None:
    """verifies: TOOL-PAR-070 (DSN-ANA-040)

    The unavailability reason records the open ADR-001 §2.4 decision — the
    degrade reason is data, not prose.
    """
    capability = CfgCapability.cfg_unavailable()
    assert capability.available is False
    assert "ADR-001" in capability.reason
    assert capability.reason == CFG_UNAVAILABLE_REASON


def test_cfg_capability_unavailable_with_named_reason() -> None:
    """verifies: TOOL-PAR-070 (DSN-ANA-040)

    Nothing in this build claims a CFG exists: the capability record is the
    degrade contract consumers rely on.
    """
    capability = CfgCapability.cfg_unavailable()
    assert capability.available is False
    assert "libclang supplies no CFG" in capability.reason


def test_complexity_formula() -> None:
    """verifies: TOOL-PAR-120

    MCC = decision points + 1; a straight-line function has complexity 1.
    """
    assert cyclomatic_complexity(0) == 1
    assert cyclomatic_complexity(4) == 5


def test_count_decision_points_counts_all_constructs() -> None:
    """verifies: TOOL-PAR-120

    The branchy fixture carries 3 keywords (if, for, while) + 2 case +
    && + ternary = 7 decision points, complexity 8.
    """
    tokens = [
        ("keyword", "int"),
        ("identifier", "branchy"),
        ("keyword", "if"),
        ("keyword", "for"),
        ("keyword", "while"),
        ("keyword", "case"),
        ("keyword", "case"),
        ("punctuation", "&&"),
        ("punctuation", "?"),
        ("literal", "5"),
    ]
    assert count_decision_points(tokens) == 7


def test_complexity_of_known_source() -> None:
    """verifies: TOOL-PAR-120

    Against the real libclang front-end: a straight-line function is 1, the
    branchy function is 8 (if + for + while + 2 case + && + ternary = 7
    decision points).
    """
    complexities = _parse_two_functions()
    assert complexities["plain"] == 1
    assert complexities["branchy"] == 8


def test_complexity_is_deterministic() -> None:
    """verifies: TOOL-PAR-120

    Two parses of the same source give identical complexities (TOOL-NFR-060).
    """
    first = _parse_two_functions()
    second = _parse_two_functions()
    assert first == second


def _parse_two_functions() -> dict[str, int]:
    """Parse a two-function TU through the real front-end and compute MCC."""
    from ectt.ana.frontend import ClangFrontend

    frontend = ClangFrontend()
    source = _SIMPLE + _BRANCHY
    tu = frontend.parse(
        "fixture.c",
        args=["-std=c99"],
        unsaved_files=[("fixture.c", source)],
    )
    return compute_complexities(tu.translation_unit)


def test_function_model_carries_complexity_when_computed() -> None:
    """verifies: TOOL-PAR-120

    The in-memory model exposes complexity when a value is computed.
    """
    model = FunctionModel(
        name="f",
        linkage="external",
        storage_class="none",
        location=SourceLocation("f.c", 1),
        return_type="int",
        complexity=7,
    )
    assert model.to_dict()["complexity"] == 7


def test_function_model_without_complexity_omits_key() -> None:
    """verifies: TOOL-PAR-120 (shape stability)

    Without a computed value the key is omitted entirely: the persisted
    SDD-002 §4.1 shape is unchanged until the schema bump lands.
    """
    model = FunctionModel(
        name="f",
        linkage="external",
        storage_class="none",
        location=SourceLocation("f.c", 1),
        return_type="int",
    )
    assert "complexity" not in model.to_dict()
    restored = FunctionModel.from_dict(model.to_dict())
    assert restored.complexity is None

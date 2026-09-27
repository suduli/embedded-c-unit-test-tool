# implements: TOOL-PAR-020
"""Dialect support tests for C89, C99, C11, C17, and GNU extensions.

Verifies: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090.
"""

from __future__ import annotations

import pytest

from ectt.ana.errors import UnsupportedDialectError
from ectt.ana.frontend import (
    GNU_DIALECTS,
    ISO_DIALECTS,
    SUPPORTED_DIALECTS,
    is_supported_dialect,
    normalize_dialect,
    parse,
)

# 1. C89: ANSI/ISO C89/C90 snippet:
# Strictly conforms to C89: block-level declarations at start of block, /* */ comments.
C89_SNIPPET = b"""/* C89 strict compliant code */
int add_c89(int a, int b) {
    int sum;
    sum = a + b;
    return sum;
}
"""

# 2. C99: ISO C99 snippet:
# Uses C99 features: mixed declarations and code, designated initializers, // line comments.
C99_SNIPPET = b"""// C99 compliant code with designated initializers and mixed declarations
struct Point {
    int x;
    int y;
};

int calculate_point(int val) {
    struct Point pt = { .x = val, .y = val * 2 };
    int offset = 5;
    return pt.x + pt.y + offset;
}
"""

# 3. C11: ISO C11 snippet:
# Uses C11 features: _Static_assert, anonymous unions/structs.
C11_SNIPPET = b"""// C11 compliant code with static assert and anonymous union
_Static_assert(sizeof(int) >= 2, "int must be at least 16 bits");

struct SensorData {
    int id;
    union {
        int raw_value;
        int calibrated_value;
    };
};

int read_sensor(void) {
    struct SensorData d;
    d.id = 1;
    d.raw_value = 100;
    return d.calibrated_value;
}
"""

# 4. C17: ISO C17 snippet:
# Conforms to ISO/IEC 9899:2018 (C17 bugfix revision of C11).
C17_SNIPPET = b"""// C17 compliant code
_Static_assert(sizeof(long) >= sizeof(int), "long is at least as wide as int");

int process_c17(int count) {
    int total = 0;
    for (int i = 0; i < count; ++i) {
        total += i;
    }
    return total;
}
"""

# 5. GNU Dialect Extensions snippet:
# Exercises GNU extensions: statement expressions ({ ...; }), __attribute__((unused)),
# and __attribute__((aligned(8))).
GNU_SNIPPET = b"""/* GNU dialect extensions code */
int sample_gnu(int input) {
    /* Statement expression GNU extension */
    int computed = ({
        int temp = input * 2;
        temp + 7;
    });

    /* Attribute extensions */
    __attribute__((aligned(8))) int aligned_val = computed;
    __attribute__((unused)) int debug_marker = 0;

    return aligned_val;
}
"""


@pytest.mark.parametrize(
    "std_flag,expected_std",
    [
        ("c89", "c89"),
        ("c90", "c90"),
        ("iso9899:1990", "iso9899:1990"),
        ("-std=c89", "c89"),
        ("/std:c99", "c99"),
    ],
)
def test_dialect_normalization(std_flag: str, expected_std: str) -> None:
    """verifies: TOOL-PAR-020"""
    assert normalize_dialect(std_flag) == expected_std
    assert is_supported_dialect(std_flag) is True


def test_supported_dialects_inventory() -> None:
    """verifies: TOOL-PAR-020"""
    assert "c89" in ISO_DIALECTS
    assert "c99" in ISO_DIALECTS
    assert "c11" in ISO_DIALECTS
    assert "c17" in ISO_DIALECTS
    assert "gnu89" in GNU_DIALECTS
    assert "gnu99" in GNU_DIALECTS
    assert "gnu11" in GNU_DIALECTS
    assert "gnu17" in GNU_DIALECTS
    assert is_supported_dialect("invalid_dialect") is False
    assert is_supported_dialect("c85") is False


def test_c89_dialect_parse() -> None:
    """verifies: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090"""
    result = parse(
        "test_c89.c",
        args=["-std=c89"],
        unsaved_files=[("test_c89.c", C89_SNIPPET)],
    )
    assert result.status == "parsed"
    assert result.is_parsed is True
    assert result.has_errors is False
    assert len(result.errors) == 0
    assert result.translation_unit is not None


def test_c99_dialect_parse() -> None:
    """verifies: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090"""
    result = parse(
        "test_c99.c",
        args=["-std=c99"],
        unsaved_files=[("test_c99.c", C99_SNIPPET)],
    )
    assert result.status == "parsed"
    assert result.is_parsed is True
    assert result.has_errors is False
    assert len(result.errors) == 0
    assert result.translation_unit is not None


def test_c11_dialect_parse() -> None:
    """verifies: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090"""
    result = parse(
        "test_c11.c",
        args=["-std=c11"],
        unsaved_files=[("test_c11.c", C11_SNIPPET)],
    )
    assert result.status == "parsed"
    assert result.is_parsed is True
    assert result.has_errors is False
    assert len(result.errors) == 0
    assert result.translation_unit is not None


def test_c17_dialect_parse() -> None:
    """verifies: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090"""
    result = parse(
        "test_c17.c",
        args=["-std=c17"],
        unsaved_files=[("test_c17.c", C17_SNIPPET)],
    )
    assert result.status == "parsed"
    assert result.is_parsed is True
    assert result.has_errors is False
    assert len(result.errors) == 0
    assert result.translation_unit is not None


@pytest.mark.parametrize("gnu_dialect", ["gnu89", "gnu99", "gnu11", "gnu17"])
def test_gnu_dialect_extensions_parse(gnu_dialect: str) -> None:
    """verifies: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090"""
    result = parse(
        "test_gnu.c",
        args=[f"-std={gnu_dialect}"],
        unsaved_files=[("test_gnu.c", GNU_SNIPPET)],
    )
    assert result.status == "parsed"
    assert result.is_parsed is True
    assert result.has_errors is False
    assert len(result.errors) == 0
    assert result.translation_unit is not None


def test_unsupported_dialect_rejection() -> None:
    """verifies: TOOL-PAR-020"""
    with pytest.raises(UnsupportedDialectError) as exc_info:
        parse(
            "test_bad.c",
            args=["-std=nonexistent_standard"],
            unsaved_files=[("test_bad.c", b"int x = 0;")],
        )
    assert exc_info.value.dialect == "nonexistent_standard"
    assert exc_info.value.reason == "unsupported_dialect"

    # Also test when specified via language_standard parameter
    with pytest.raises(UnsupportedDialectError) as exc_info2:
        parse(
            "test_bad.c",
            language_standard="invalid_std_123",
            unsaved_files=[("test_bad.c", b"int x = 0;")],
        )
    assert exc_info2.value.dialect == "invalid_std_123"

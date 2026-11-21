"""Fixtures for CMP-COV tests: hand-written gcov JSON per the documented format.

There is no C compiler on this machine (ADR-004): these fixtures follow the
GCC gcov JSON documentation (GCC 14.4, "Invoking Gcov → GCOV JSON Format")
key-for-key. Real GCC output has not been checked — see
docs/verification/WP-COV-01-analysis.md.
"""

from __future__ import annotations

import json
from typing import Any

GCOV_V2_WITH_BRANCHES_AND_CONDITIONS: dict[str, Any] = {
    "format_version": "2",
    "gcc_version": "14.1.1 20240510",
    "current_working_directory": "/build/proj",
    "data_file": "/build/proj/adc.gcda",
    "files": [
        {
            "file": "adc.c",
            "functions": [
                {
                    "blocks": 3,
                    "blocks_executed": 2,
                    "demangled_name": "convert",
                    "end_column": 1,
                    "end_line": 12,
                    "execution_count": 2,
                    "name": "convert",
                    "start_column": 5,
                    "start_line": 6,
                }
            ],
            "lines": [
                {"line_number": 6, "count": 2, "unexecuted_block": False, "function_name": "convert"},
                {
                    "line_number": 8,
                    "count": 2,
                    "unexecuted_block": False,
                    "function_name": "convert",
                    "branches": [
                        {"count": 1, "destination_block_id": 5, "fallthrough": True, "source_block_id": 3, "throw": False},
                        {"count": 1, "destination_block_id": 7, "fallthrough": False, "source_block_id": 3, "throw": False},
                    ],
                },
                {
                    "line_number": 10,
                    "count": 1,
                    "unexecuted_block": True,
                    "function_name": "convert",
                    "conditions": [
                        {
                            "count": 4,
                            "covered": 2,
                            "not_covered_false": [],
                            "not_covered_true": [0, 1],
                        }
                    ],
                },
                {"line_number": 12, "count": 0, "unexecuted_block": True, "function_name": "convert"},
            ],
        }
    ],
}

GCOV_V1_MINIMAL: dict[str, Any] = {
    "format_version": "1",
    "gcc_version": "9.3.0",
    "data_file": "/build/proj/main.gcda",
    "files": [
        {
            "file": "main.c",
            "functions": [
                {
                    "blocks": 2,
                    "blocks_executed": 2,
                    "end_column": 1,
                    "end_line": 4,
                    "execution_count": 1,
                    "name": "main",
                    "start_column": 5,
                    "start_line": 1,
                }
            ],
            "lines": [
                {"line_number": 1, "count": 1, "unexecuted_block": False, "function_name": "main"},
                {"line_number": 2, "count": 1, "unexecuted_block": False, "function_name": "main"},
                {"line_number": 4, "count": 0, "unexecuted_block": True, "function_name": "main"},
            ],
        }
    ],
}


def gcov_json(payload: dict[str, Any]) -> str:
    """Serialize a fixture to the exact JSON text a gcov run would emit."""
    return json.dumps(payload, indent=2)

"""Stable documented exit codes for the ectt CLI (WP-CLI-02).

TOOL-CIC-030: the tool shall use documented, stable exit codes
distinguishing success, test failure, coverage threshold failure, and tool
error. The values below are the contract; CI pipelines and scripts rely on
them, so they change only with a documented release-note entry.

Documented table:

=====  ===============================  ==========================================
Code   Constant                         Meaning
=====  ===============================  ==========================================
0      ``EXIT_SUCCESS``                 every requested operation completed
1      ``EXIT_TOOL_ERROR``              tool error (internal error, unwired
                                        operation, invalid invocation outcome)
2      ``EXIT_USAGE``                   command-line usage error (argparse
                                        conventional)
10     ``EXIT_TEST_FAILURE``            executed tests, at least one failed
11     ``EXIT_COVERAGE_THRESHOLD``      coverage threshold not met
=====  ===============================  ==========================================

Every ``EcttError`` category (the structured error model, WP-CORE-02) maps
onto this table via ``CATEGORY_EXIT_CODES`` / ``exit_code_for_category``:
all categories are tool outcomes and exit ``EXIT_TOOL_ERROR`` with the
error reported on stderr. Unknown categories also resolve to
``EXIT_TOOL_ERROR``, so no failure can ever exit 0 (TOOL-NFR-090).

Satisfies: TOOL-CIC-030, TOOL-NFR-090.
"""

from __future__ import annotations

__all__ = [
    "CATEGORY_EXIT_CODES",
    "EXIT_CODE_TABLE",
    "EXIT_COVERAGE_THRESHOLD",
    "EXIT_SUCCESS",
    "EXIT_TEST_FAILURE",
    "EXIT_TOOL_ERROR",
    "EXIT_USAGE",
    "exit_code_for_category",
]

EXIT_SUCCESS = 0
EXIT_TOOL_ERROR = 1
EXIT_USAGE = 2
EXIT_TEST_FAILURE = 10
EXIT_COVERAGE_THRESHOLD = 11

#: Value → meaning; documentation and tests read this table, never literals.
EXIT_CODE_TABLE: dict[int, str] = {
    EXIT_SUCCESS: "success",
    EXIT_TOOL_ERROR: "tool error",
    EXIT_USAGE: "command-line usage error",
    EXIT_TEST_FAILURE: "test failure",
    EXIT_COVERAGE_THRESHOLD: "coverage threshold failure",
}

#: EcttError category → documented exit code (WP-CORE-02 adoption of the
#: table above). Every category of the structured error model is a tool
#: outcome: the CLI reports the error and exits ``EXIT_TOOL_ERROR``.
#: Interruption (category ``cancelled``) is likewise reported on stderr and
#: exits as a tool error; the table gains no new code without an owner
#: release-note entry (see WP-CORE-02-analysis.md).
CATEGORY_EXIT_CODES: dict[str, int] = {
    "api": EXIT_TOOL_ERROR,
    "analysis": EXIT_TOOL_ERROR,
    "build": EXIT_TOOL_ERROR,
    "cancelled": EXIT_TOOL_ERROR,
    "cli": EXIT_TOOL_ERROR,
    "core": EXIT_TOOL_ERROR,
    "extension": EXIT_TOOL_ERROR,
    "filesystem": EXIT_TOOL_ERROR,
    "generation": EXIT_TOOL_ERROR,
    "ingestion": EXIT_TOOL_ERROR,
    "internal": EXIT_TOOL_ERROR,
    "project": EXIT_TOOL_ERROR,
    "security": EXIT_TOOL_ERROR,
    "target": EXIT_TOOL_ERROR,
    "testcase": EXIT_TOOL_ERROR,
    "toolchain": EXIT_TOOL_ERROR,
}


def exit_code_for_category(category: str) -> int:
    """Return the documented exit code for an ``EcttError`` category.

    Total by construction: a category absent from ``CATEGORY_EXIT_CODES``
    (a future package) still resolves to ``EXIT_TOOL_ERROR`` so the process
    exits non-zero and the error is reported, never faked as success.
    """
    return CATEGORY_EXIT_CODES.get(category, EXIT_TOOL_ERROR)

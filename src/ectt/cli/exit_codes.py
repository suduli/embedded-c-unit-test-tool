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

Satisfies: TOOL-CIC-030.
"""

from __future__ import annotations

__all__ = [
    "EXIT_CODE_TABLE",
    "EXIT_COVERAGE_THRESHOLD",
    "EXIT_SUCCESS",
    "EXIT_TEST_FAILURE",
    "EXIT_TOOL_ERROR",
    "EXIT_USAGE",
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

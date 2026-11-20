# implements: TOOL-EXE-020, TOOL-TCD-090
"""C runtime of a generated harness: result stream protocol and per-test state reset.

Two blocks of C text that ``HarnessGenerator`` places in every harness:

``RESULT_PROTOCOL_BLOCK`` emits the stream the host runner reads
(``docs/verification/WP-EXH-01-analysis.md``; parsed by ``ectt.exh.runner``)::

    RESULT <test_id> pass|fail|error
    FAILURE <test_id> <assertion> <expected> <actual> <file> <line>

Tokens never contain whitespace (written as ``_``; an empty token as ``-``), and a
line number is never below 1, because the reader refuses both. The transport is the
macro ``ECTT_STREAM_WRITE``, defined by the user before the block to send the stream
elsewhere than stdout (for example over a bare-metal target's own channel).

A test that is still open when the next test starts, or when teardown runs, did not
reach ``ectt_end_test`` (a framework assertion aborted it). It is **never reported as
a pass**: it is ``fail`` when a failure was recorded and ``error`` when none was. A
failure reported outside any test is counted
(``ectt_unattributed_failure_count``), not dropped.

``SETUP_TEARDOWN_BLOCK`` holds the registrable hooks. ``ectt_run_setup`` resets the
harness state before every test (DSN-TCM-060): nothing recorded for a previous test
survives, and the registered state resets (for example the stub reset of WP-GEN-07)
run before the user's own setup hook. The state a harness cannot reset by itself,
the unit under test's own globals, is the user's to register: the analysis model
records their names but not their types or initial values.

No compiler is available to the test suite, so the blocks are verified by parsing with
libclang and by structural assertions; compiling and running them is recorded as
follow-up work.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "RESULT_PROTOCOL_BLOCK",
    "SETUP_TEARDOWN_BLOCK",
]

RESULT_PROTOCOL_BLOCK: Final[str] = r"""/* ectt:result-protocol - the RESULT/FAILURE stream read by the host runner (WP-EXH-01).
   RESULT <test_id> pass|fail|error
   FAILURE <test_id> <assertion> <expected> <actual> <file> <line>
   Tokens never contain whitespace (it is written as '_'; an empty token as '-'). The
   transport is ECTT_STREAM_WRITE; define it before this block to send the stream
   somewhere other than stdout. */
#ifndef ECTT_STREAM_WRITE
#include <stdio.h>
#define ECTT_STREAM_WRITE(text) fputs((text), stdout)
#endif
#ifndef ECTT_MAX_STATE_RESETS
#define ECTT_MAX_STATE_RESETS 8
#endif

static const char *ectt_current_test = 0;
static unsigned ectt_current_failures = 0;
static unsigned ectt_unattributed_failures = 0;
static void (*ectt_state_resets[ECTT_MAX_STATE_RESETS])(void);
static unsigned ectt_state_reset_count = 0;

static void ectt_write_token(const char *text) {
    char one[2];
    one[1] = 0;
    if (text == 0 || text[0] == 0) {
        ECTT_STREAM_WRITE("-");
        return;
    }
    for (; *text != 0; text++) {
        one[0] = (*text == ' ' || *text == '\t' || *text == '\n' || *text == '\r') ? '_' : *text;
        ECTT_STREAM_WRITE(one);
    }
}

static void ectt_write_unsigned(unsigned long value) {
    char digits[24];
    char out[2];
    unsigned n = 0;
    out[1] = 0;
    if (value == 0) {
        ECTT_STREAM_WRITE("0");
        return;
    }
    while (value > 0 && n < sizeof digits) {
        digits[n++] = (char)('0' + value % 10);
        value /= 10;
    }
    while (n > 0) {
        n--;
        out[0] = digits[n];
        ECTT_STREAM_WRITE(out);
    }
}

void ectt_report_result(const char *test_id, const char *outcome);
void ectt_report_failure(const char *test_id, const char *assertion, const char *expected,
                         const char *actual, const char *file, unsigned line);
void ectt_begin_test(const char *test_id);
void ectt_fail(const char *assertion, const char *expected, const char *actual,
               const char *file, unsigned line);
void ectt_end_test(void);
int ectt_register_state_reset(void (*fn)(void));
unsigned ectt_unattributed_failure_count(void);

void ectt_report_result(const char *test_id, const char *outcome) {
    ECTT_STREAM_WRITE("RESULT ");
    ectt_write_token(test_id);
    ECTT_STREAM_WRITE(" ");
    ectt_write_token(outcome);
    ECTT_STREAM_WRITE("\n");
}

void ectt_report_failure(const char *test_id, const char *assertion, const char *expected,
                         const char *actual, const char *file, unsigned line) {
    ECTT_STREAM_WRITE("FAILURE ");
    ectt_write_token(test_id);
    ECTT_STREAM_WRITE(" ");
    ectt_write_token(assertion);
    ECTT_STREAM_WRITE(" ");
    ectt_write_token(expected);
    ECTT_STREAM_WRITE(" ");
    ectt_write_token(actual);
    ECTT_STREAM_WRITE(" ");
    ectt_write_token(file);
    ECTT_STREAM_WRITE(" ");
    ectt_write_unsigned(line == 0 ? 1ul : (unsigned long)line);
    ECTT_STREAM_WRITE("\n");
}

/* A test still open here did not reach ectt_end_test: it is never reported as a pass. */
static void ectt_finish_open_test(void) {
    if (ectt_current_test != 0) {
        ectt_report_result(ectt_current_test, ectt_current_failures > 0 ? "fail" : "error");
        ectt_current_test = 0;
        ectt_current_failures = 0;
    }
}

static void ectt_reset_test_state(void) {
    ectt_finish_open_test();
    ectt_current_failures = 0;
}

static void ectt_run_state_resets(void) {
    unsigned i;
    for (i = 0; i < ectt_state_reset_count; i++) {
        ectt_state_resets[i]();
    }
}

int ectt_register_state_reset(void (*fn)(void)) {
    if (fn == 0 || ectt_state_reset_count >= ECTT_MAX_STATE_RESETS) {
        return 0;
    }
    ectt_state_resets[ectt_state_reset_count] = fn;
    ectt_state_reset_count++;
    return 1;
}

void ectt_begin_test(const char *test_id) {
    ectt_finish_open_test();
    ectt_current_test = test_id;
    ectt_current_failures = 0;
}

void ectt_fail(const char *assertion, const char *expected, const char *actual,
               const char *file, unsigned line) {
    if (ectt_current_test == 0) {
        ectt_unattributed_failures++;
        return;
    }
    ectt_current_failures++;
    ectt_report_failure(ectt_current_test, assertion, expected, actual, file, line);
}

void ectt_end_test(void) {
    if (ectt_current_test != 0) {
        ectt_report_result(ectt_current_test, ectt_current_failures > 0 ? "fail" : "pass");
        ectt_current_test = 0;
        ectt_current_failures = 0;
    }
}

unsigned ectt_unattributed_failure_count(void) { return ectt_unattributed_failures; }
"""

SETUP_TEARDOWN_BLOCK: Final[str] = r"""static void (*ectt_setup_hook)(void) = 0;
static void (*ectt_teardown_hook)(void) = 0;

void ectt_register_setup(void (*fn)(void));
void ectt_register_teardown(void (*fn)(void));
void ectt_run_setup(void);
void ectt_run_teardown(void);

void ectt_register_setup(void (*fn)(void)) { ectt_setup_hook = fn; }
void ectt_register_teardown(void (*fn)(void)) { ectt_teardown_hook = fn; }

/* DSN-TCM-060: every test starts from reset harness state. Nothing recorded for a previous
   test survives; registered state resets run before the user's setup hook. */
void ectt_run_setup(void) {
    ectt_reset_test_state();
    ectt_run_state_resets();
    if (ectt_setup_hook) { ectt_setup_hook(); }
}

void ectt_run_teardown(void) {
    if (ectt_teardown_hook) { ectt_teardown_hook(); }
    ectt_finish_open_test();
}
"""

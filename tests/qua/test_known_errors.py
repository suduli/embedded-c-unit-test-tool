# implements: TOOL-QUA-040
"""The known-error list per release (WP-QUA-04).

A plain-text list loads strictly — every refusal names its reason — and the
query returns exactly the entries that apply to a release, id-sorted.
"""

from __future__ import annotations

import pytest

from ectt.qua import KnownErrorListError, errors_for_release, load_known_errors

VALID_LIST = """
error: QUA-ERR-001
summary: the CLI prints a wrong exit code for cancelled sessions
introduced-in: 0.1.0
affected-versions: 0.1.0, 0.1.1
workaround: check the session state in the JSON output instead
status: open

error: QUA-ERR-002
summary: gcov v1 documents forget the branch base counts
introduced-in: 0.1.0
affected-versions: 0.1.0, 0.1.1, 0.2.0
workaround: regenerate the document as v2
status: fixed in 0.2.1

error: QUA-ERR-003
summary: reports on a narrow terminal truncate long paths
introduced-in: 0.2.0
affected-versions: 0.2.0
workaround: widen the terminal or use the JSON report
status: open
"""


def _refuse(text: str, reason: str) -> None:
    with pytest.raises(KnownErrorListError) as excinfo:
        load_known_errors(text)
    assert excinfo.value.reason == reason


def test_a_well_formed_list_loads() -> None:
    """verifies: TOOL-QUA-040 — the documented plain-text form loads, in id
    order, with every field carried."""
    errors = load_known_errors(VALID_LIST)
    assert [e.error_id for e in errors] == ["QUA-ERR-001", "QUA-ERR-002", "QUA-ERR-003"]
    assert errors[0].status == "open" and errors[0].fixed_in is None
    assert errors[1].status == "fixed" and errors[1].fixed_in == "0.2.1"
    assert errors[0].affected_versions == ("0.1.0", "0.1.1")


def test_duplicate_error_ids_are_refused() -> None:
    """verifies: TOOL-QUA-040 — the same id twice is a named refusal."""
    _refuse(
        VALID_LIST
        + "\nerror: QUA-ERR-001\nsummary: a second entry with the first id\n"
        "introduced-in: 0.1.0\naffected-versions: 0.1.0\nworkaround: none\nstatus: open\n",
        "duplicate_error_id",
    )


def test_fixed_in_not_after_introduced_is_refused() -> None:
    """verifies: TOOL-QUA-040 — a fix at or before the introduction is refused."""
    _refuse(
        "error: QUA-ERR-010\nsummary: x\nintroduced-in: 0.2.0\n"
        "affected-versions: 0.2.0\nworkaround: y\nstatus: fixed in 0.1.0\n",
        "fixed_before_introduced",
    )
    _refuse(
        "error: QUA-ERR-010\nsummary: x\nintroduced-in: 0.2.0\n"
        "affected-versions: 0.2.0\nworkaround: y\nstatus: fixed in 0.2.0\n",
        "fixed_before_introduced",
    )
    # 0.2.10 IS after 0.2.9 (numeric per-component comparison, not lexical).
    errors = load_known_errors(
        "error: QUA-ERR-010\nsummary: x\nintroduced-in: 0.2.9\n"
        "affected-versions: 0.2.9\nworkaround: y\nstatus: fixed in 0.2.10\n"
    )
    assert errors[0].fixed_in == "0.2.10"


def test_an_open_entry_without_a_workaround_is_refused() -> None:
    """verifies: TOOL-QUA-040 — an open entry must record a workaround."""
    _refuse(
        "error: QUA-ERR-011\nsummary: x\nintroduced-in: 0.1.0\n"
        "affected-versions: 0.1.0\nworkaround: \nstatus: open\n",
        "missing_workaround",
    )


def test_malformed_and_unknown_fields_are_refused() -> None:
    """verifies: TOOL-QUA-040 — structural violations name themselves."""
    _refuse("this line has no colon\n", "malformed_line")
    _refuse(
        "error: QUA-ERR-012\nsummary: x\nintroduced-in: 0.1.0\n"
        "affected-versions: 0.1.0\nworkaround: y\nstatus: open\nmood: fine\n",
        "unknown_field",
    )
    _refuse(
        "error: QUA-ERR-012\nsummary: x\nstatus: open\n",
        "missing_field",
    )
    _refuse(
        "error: QUA-ERR-013\nsummary: x\nintroduced-in: 0.1.0\n"
        "affected-versions: 0.1.0\nworkaround: y\nstatus: wont-fix\n",
        "malformed_line",
    )


def test_versions_must_parse() -> None:
    """verifies: TOOL-QUA-040 — versions are dotted numeric, everywhere."""
    _refuse(
        "error: QUA-ERR-014\nsummary: x\nintroduced-in: v1\n"
        "affected-versions: v1\nworkaround: y\nstatus: open\n",
        "version_malformed",
    )


def test_the_query_returns_exactly_what_applies() -> None:
    """verifies: TOOL-QUA-040 — a release sees exactly the errors that affect it
    and are not fixed as of it."""
    errors = load_known_errors(VALID_LIST)
    applying_010 = errors_for_release(errors, "0.1.0")
    assert [e.error_id for e in applying_010] == ["QUA-ERR-001", "QUA-ERR-002"]
    applying_020 = errors_for_release(errors, "0.2.0")
    # QUA-ERR-002 is still affected by 0.2.0: it is fixed only AS OF 0.2.1.
    assert [e.error_id for e in applying_020] == ["QUA-ERR-002", "QUA-ERR-003"]
    # 0.2.1 fixed QUA-ERR-002 and was never affected by QUA-ERR-003.
    assert errors_for_release(errors, "0.2.1") == ()
    # An unknown release is simply not in anyone's affected list.
    assert errors_for_release(errors, "9.9.9") == ()


def test_a_fixed_error_stops_applying_after_its_fix() -> None:
    """verifies: TOOL-QUA-040 — the fix version itself is already clean."""
    errors = load_known_errors(
        "error: QUA-ERR-020\nsummary: x\nintroduced-in: 1.0.0\n"
        "affected-versions: 1.0.0, 1.0.1, 1.0.2\nworkaround: y\nstatus: fixed in 1.0.2\n"
    )
    assert [e.error_id for e in errors_for_release(errors, "1.0.0")] == ["QUA-ERR-020"]
    assert [e.error_id for e in errors_for_release(errors, "1.0.1")] == ["QUA-ERR-020"]
    assert errors_for_release(errors, "1.0.2") == ()
    with pytest.raises(KnownErrorListError):
        errors_for_release(errors, "not-a-version")


def test_the_query_is_id_sorted_and_deterministic() -> None:
    """verifies: TOOL-NFR-060 — the answer is id-sorted regardless of the list's
    written order."""
    errors = load_known_errors(VALID_LIST)
    straight = errors_for_release(errors, "0.1.1")
    reordered = load_known_errors(
        "\n\n".join(part for part in reversed(VALID_LIST.strip().split("\n\n"))) + "\n"
    )
    assert [e.error_id for e in errors_for_release(reordered, "0.1.1")] == [
        e.error_id for e in straight
    ]
    assert straight == tuple(sorted(straight, key=lambda e: e.error_id))

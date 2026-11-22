# implements: TOOL-COV-100
"""Bare-metal coverage retrieval over the console transport (WP-COV-07)."""

from __future__ import annotations

import gzip

import pytest

from ectt.cov.baremetal import (
    DumpFrame,
    dump_frame,
    parse_dump,
    retrieve_coverage,
    retrieve_run_coverage,
)
from ectt.cov.errors import CoverageError
from ectt.cov.gcov import read_gcov_document
from ectt.cov.merge import RunCoverage, merge_run_coverage
from ectt.cov.model import GcovDocument

DOCUMENT = {
    "format_version": "2",
    "gcc_version": "14.1.0",
    "data_file": "adc.gcda",
    "files": [{"file": "src/adc.c", "lines": [{"line_number": 1, "count": 3, "unexecuted_block": False}]}],
}
DOCUMENT_JSON = (
    '{"format_version": "2", "gcc_version": "14.1.0", "data_file": "adc.gcda",'
    ' "files": [{"file": "src/adc.c", "lines": [{"line_number": 1, "count": 3, "unexecuted_block": false}]}]}'
)


def test_frame_round_trip_and_retrieval() -> None:
    """verifies: TOOL-COV-100 — reassembly from the console framing, no filesystem."""
    stream = dump_frame("adc.json", DOCUMENT_JSON.encode("ascii"))
    frame = parse_dump(stream)
    assert isinstance(frame, DumpFrame)
    assert frame.name == "adc.json"
    assert frame.payload == DOCUMENT_JSON.encode("ascii")
    document = retrieve_coverage(stream)
    assert isinstance(document, GcovDocument)
    (file,) = document.files
    assert file.lines[0].count == 3


def test_gzipped_artifact_is_retrieved() -> None:
    payload = gzip.compress(DOCUMENT_JSON.encode("ascii"))
    stream = dump_frame("adc.gcov.json.gz", payload)
    document = retrieve_coverage(stream)
    assert document.data_file == "adc.gcda"


def test_length_mismatch_is_refused() -> None:
    stream = dump_frame("adc.json", DOCUMENT_JSON.encode("ascii")).replace(
        f"GCOVDUMP BEGIN adc.json {len(DOCUMENT_JSON)}", f"GCOVDUMP BEGIN adc.json {len(DOCUMENT_JSON) + 5}"
    )
    with pytest.raises(CoverageError) as exc_info:
        parse_dump(stream)
    assert exc_info.value.reason == "length_mismatch"


def test_crc_mismatch_is_refused() -> None:
    stream = dump_frame("adc.json", DOCUMENT_JSON.encode("ascii"))
    tampered = stream[:-9] + "deadbeef\n"
    with pytest.raises(CoverageError) as exc_info:
        parse_dump(tampered)
    assert exc_info.value.reason == "crc_mismatch"


def test_bad_hex_payload_is_refused() -> None:
    stream = dump_frame("adc.json", b"AB")
    with pytest.raises(CoverageError) as exc_info:
        parse_dump(stream.replace("4142", "41zz"))
    assert exc_info.value.reason == "malformed_payload"


def test_text_outside_frame_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        parse_dump("RUN ok\nGCOVDUMP BEGIN a 1\n41\nGCOVDUMP END 821b11d9\n")
    assert exc_info.value.reason == "text_outside_frame"


def test_duplicate_frame_is_refused() -> None:
    stream = dump_frame("a.json", b"AB")
    with pytest.raises(CoverageError) as exc_info:
        parse_dump(stream + "GCOVDUMP BEGIN b.json 1\n41\nGCOVDUMP END 821b11d9\n")
    assert exc_info.value.reason == "duplicate_frame"


def test_truncated_frame_is_refused() -> None:
    stream = dump_frame("adc.json", DOCUMENT_JSON.encode("ascii"))
    truncated = "\n".join(stream.split("\n")[:-2]) + "\n"  # drop the END line
    with pytest.raises(CoverageError) as exc_info:
        parse_dump(truncated)
    assert exc_info.value.reason == "truncated_dump"


def test_truncated_frame_becomes_a_truncated_run_record() -> None:
    """verifies: AC-2 — TOOL-COV-180: a truncated artifact records 'truncated'
    with an advisory and is excluded from the aggregate by the merge."""
    stream = dump_frame("adc.json", DOCUMENT_JSON.encode("ascii"))
    truncated = "\n".join(stream.split("\n")[:-2]) + "\n"
    complete = retrieve_run_coverage(
        dump_frame("adc.json", DOCUMENT_JSON.encode("ascii")), test_id="t1", outcome="pass"
    )
    broken = retrieve_run_coverage(truncated, test_id="t2", outcome="pass")
    assert broken.completeness == "truncated"
    assert broken.document is None
    assert broken.advisory and "truncated" in broken.advisory
    result = merge_run_coverage([complete, broken])
    (file,) = result.document.files
    assert file.lines[0].count == 3  # truncated artifact contributed nothing
    assert {excluded.test_id for excluded in result.excluded} == {"t2"}


def test_empty_stream_records_missing() -> None:
    record = retrieve_run_coverage("", test_id="t1", outcome="pass")
    assert record.completeness == "missing"
    assert record.document is None
    assert record.advisory


def test_invalid_artifact_json_is_refused() -> None:
    stream = dump_frame("adc.json", b"{not json")
    with pytest.raises(CoverageError) as exc_info:
        retrieve_coverage(stream)
    assert exc_info.value.reason == "invalid_json"


def test_native_and_bare_metal_documents_aggregate() -> None:
    """A bare-metal retrieval merges with a native reader document (same provenance)."""
    native = read_gcov_document(DOCUMENT)
    retrieved = retrieve_coverage(dump_frame("adc.json", DOCUMENT_JSON.encode("ascii")))
    result = merge_run_coverage(
        [
            RunCoverage(test_id="t1", outcome="pass", completeness="complete", document=native),
            RunCoverage(test_id="t2", outcome="pass", completeness="complete", document=retrieved),
        ]
    )
    (file,) = result.document.files
    assert file.lines[0].count == 6

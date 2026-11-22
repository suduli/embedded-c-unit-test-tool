# implements: TOOL-COV-110
"""Merge provenance is independent of input order (B1 review finding).

`_merge_documents` used to take `data_file` (and the working directory) from
the first admitted run in INPUT order, so the same run set merged in a
different order produced a different aggregate. The merged provenance is now
a pure function of the run set: the sorted, comma-joined data files and the
sorted-first distinct working directory. Counts are unaffected.
"""

from __future__ import annotations

import itertools
import json
from typing import Any

from ectt.cov.gcov import read_gcov_document
from ectt.cov.merge import RunCoverage, merge_run_coverage


def _payload(data_file: str, cwd: str | None, line_count: int) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": data_file,
        "files": [
            {
                "file": "adc.c",
                "lines": [
                    {"line_number": 1, "count": line_count, "unexecuted_block": False},
                    {"line_number": 2, "count": line_count + 1, "unexecuted_block": False},
                ],
            }
        ],
    }
    if cwd is not None:
        payload["current_working_directory"] = cwd
    return payload


def _runs() -> list[RunCoverage]:
    docs = [
        read_gcov_document(_payload("b.gcda", "/build/one", 3)),
        read_gcov_document(_payload("a.gcda", "/build/two", 2)),
        read_gcov_document(_payload("c.gcda", None, 1)),
    ]
    return [
        RunCoverage(test_id=f"t{index}", outcome="pass", completeness="complete", document=doc)
        for index, doc in enumerate(docs)
    ]


def test_all_permutations_give_byte_identical_merged_output() -> None:
    """verifies: B1 — the merge is a pure function of the run set."""
    runs = _runs()
    dumps = []
    for permutation in itertools.permutations(runs):
        result = merge_run_coverage(list(permutation))
        dumps.append(result.document.to_json_bytes())
    assert all(d == dumps[0] for d in dumps)

    doc: dict[str, Any] = json.loads(dumps[0].decode("utf-8"))
    # the merged provenance is the sorted list of all data files, whatever the order
    assert doc["data_file"] == "a.gcda,b.gcda,c.gcda"
    # counts are the sum over all runs, unaffected by the provenance fix
    (file,) = doc["files"]
    assert [line["count"] for line in file["lines"]] == [6, 9]


def test_single_run_merge_is_unchanged() -> None:
    """A single-run merge reproduces the input document byte for byte."""
    doc = read_gcov_document(_payload("only.gcda", "/build/one", 3))
    result = merge_run_coverage(
        [RunCoverage(test_id="t0", outcome="pass", completeness="complete", document=doc)]
    )
    assert result.document.to_json_bytes() == doc.to_json_bytes()


def test_single_run_merge_without_cwd_is_unchanged() -> None:
    doc = read_gcov_document(_payload("only.gcda", None, 2))
    result = merge_run_coverage(
        [RunCoverage(test_id="t0", outcome="pass", completeness="complete", document=doc)]
    )
    assert result.document.to_json_bytes() == doc.to_json_bytes()


def test_identical_data_files_stay_a_single_token() -> None:
    """Runs of one build share their data file: the merged token is that file."""
    runs = [
        RunCoverage(test_id="t0", outcome="pass", completeness="complete",
                    document=read_gcov_document(_payload("build.gcda", "/build", 1))),
        RunCoverage(test_id="t1", outcome="pass", completeness="complete",
                    document=read_gcov_document(_payload("build.gcda", "/build", 2))),
    ]
    result = merge_run_coverage(runs)
    assert result.document.data_file == "build.gcda"
    assert result.document.current_working_directory == "/build"


def test_differing_working_directories_take_the_sorted_first() -> None:
    """A merged aggregate spanning build directories carries the sorted-first
    distinct working directory (deterministic, never input-order dependent)."""
    runs = [
        RunCoverage(test_id="t0", outcome="pass", completeness="complete",
                    document=read_gcov_document(_payload("b.gcda", "/build/zzz", 1))),
        RunCoverage(test_id="t1", outcome="pass", completeness="complete",
                    document=read_gcov_document(_payload("a.gcda", "/build/aaa", 1))),
    ]
    result = merge_run_coverage(runs)
    assert result.document.current_working_directory == "/build/aaa"
    shuffled = [runs[1], runs[0]]
    assert merge_run_coverage(shuffled).document.current_working_directory == "/build/aaa"

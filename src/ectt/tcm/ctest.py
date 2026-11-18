"""C-authored test cases against the generated harness (WP-TCM-01).

A test case authored directly in C is a source file that includes the
generated harness header. The tool consumes such files as named test cases:
it verifies the include relationship, registers the case under a user-chosen
identifier, and keeps a deterministic, retrievable set.

Satisfies: TOOL-TCD-010.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ectt.tcm.errors import (
    DuplicateTestCaseError,
    InvalidTestCaseError,
    NotAgainstHarnessError,
    TestCaseReadError,
    UnknownTestCaseError,
)

__all__ = [
    "CSourceTestCase",
    "TestCaseSet",
    "register_c_source",
]


@dataclass(frozen=True)
class CSourceTestCase:
    """One C-authored test case registered against a generated harness."""

    case_id: str
    source_path: str
    harness_header: str


def _require_nonempty(value: str, what: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise InvalidTestCaseError(f"test case {what} must be a non-empty string")


def register_c_source(
    case_id: str,
    source_path: Path | str,
    harness_header: str,
) -> CSourceTestCase:
    """Load a C-authored test case and verify it targets the harness.

    The source must be readable and must include the harness header with the
    exact generated name (``#include "<harness_header>"``). The check is
    text-level; no C parse is performed.
    """
    _require_nonempty(case_id, "identifier")
    _require_nonempty(harness_header, "harness header")
    file_path = Path(source_path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TestCaseReadError(
            f"cannot read C test case source: {exc}",
            path=file_path,
        ) from exc
    needle = f'#include "{harness_header}"'
    if needle not in text:
        raise NotAgainstHarnessError(
            f"C test case does not include the generated harness header "
            f"'{harness_header}'",
            path=file_path,
        )
    return CSourceTestCase(
        case_id=case_id,
        source_path=file_path.as_posix(),
        harness_header=harness_header,
    )


class TestCaseSet:
    """A named set of test cases with deterministic ordering."""

    def __init__(self) -> None:
        self._cases: dict[str, CSourceTestCase] = {}

    def register_model(self, case: CSourceTestCase) -> None:
        """Register an already-validated case; reject a reused identifier."""
        _require_nonempty(case.case_id, "identifier")
        if case.case_id in self._cases:
            raise DuplicateTestCaseError(
                f"test case '{case.case_id}' is already registered"
            )
        self._cases[case.case_id] = case

    def register_source(
        self,
        case_id: str,
        source_path: Path | str,
        harness_header: str,
    ) -> CSourceTestCase:
        """Load, verify and register a C-authored test case."""
        case = register_c_source(case_id, source_path, harness_header)
        self.register_model(case)
        return case

    def lookup(self, case_id: str) -> CSourceTestCase:
        """Return the case registered under ``case_id``."""
        try:
            return self._cases[case_id]
        except KeyError:
            raise UnknownTestCaseError(
                f"no test case is registered under '{case_id}'"
            ) from None

    def list_ids(self) -> tuple[str, ...]:
        """Registered identifiers, ordered deterministically."""
        return tuple(sorted(self._cases))

    def __len__(self) -> int:
        return len(self._cases)

# implements: DSN-TCM-020, DSN-TCM-110
"""Data-driven test cases: the model, the on-disk format, and digest binding.

A data-driven test case is authored entirely as data (TOOL-TCD-020): input
parameter values, initial values of accessed globals, expected return value,
expected final values of globals, expected output parameter values, and stub
behaviour and expectations (TOOL-TCD-040). Cases are stored per unit in
restricted YAML ``.tests`` files — plain, diffable, version-controllable text
(TOOL-TCD-030, ADR-002) — and each carries an identifier assigned at creation
that survives edits, renames, and regeneration (TOOL-TCD-140, DSN-TCM-110).

Decision applied as written (D-02, option a, owner answer 2026-11-19): test
and result identities are stable ids bound to content digests; separate
revision entities are not adopted; digest binding is the staleness mechanism
(SDD-003 §6/§7). Each record carries a content digest computed over the
canonical JSON encoding of its content, excluding the id and the digest
itself. A record whose recorded digest no longer matches its content is
surfaced as ``stale`` — it is never silently accepted as current.

Schema discipline follows SDD-003 §5 via the shared version dispatcher:
unknown structured keys are refused rather than silently discarded, and
scalar-valued unknown keys are preserved verbatim through read/edit/write.

Satisfies: TOOL-TCD-020, TOOL-TCD-030, TOOL-TCD-040, TOOL-TCD-140,
DSN-TCM-020, DSN-TCM-110.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from ectt.core.determinism import canonical_json_bytes
from ectt.prj.errors import CommentPreservationError
from ectt.prj.model import FileKind, dispatch_schema_version
from ectt.prj.yaml_adapter import (
    RestrictedYamlAdapter,
    SerializationAdapter,
    detect_yaml_comments,
)
from ectt.tcm.errors import (
    DuplicateTestCaseError,
    InvalidTestCaseError,
    InvalidTestCasesFileError,
    MissingCaseFieldError,
    TestCaseReadError,
)

__all__ = [
    "TEST_CASES_KIND",
    "TestCaseInputs",
    "TestCaseExpected",
    "TestCaseOrigin",
    "StubSpec",
    "DataDrivenTestCase",
    "TestCasesFile",
    "compute_case_digest",
    "refresh_digest",
    "parse_test_cases_document",
    "load_test_cases_file",
    "dump_test_cases_document",
    "save_test_cases_file",
]

TEST_CASES_KIND = FileKind(
    name="test_cases",
    file_pattern="*.tests",
    min_version=1,
    max_version=1,
    canonical_keys=("schema_version", "test_cases"),
)

_ORIGIN_AUTHORS = ("human", "atg", "ai")
_EXPECT_CALL_RE = re.compile(r"^\d+$")

_CASE_KEYS = frozenset({"id", "unit", "function", "origin", "requirements", "suites", "robustness", "inputs", "expected", "stubs", "digest"})
_FILE_KEYS = frozenset({"schema_version", "test_cases"})
_ORIGIN_KEYS = frozenset({"author", "engine", "model", "review_state"})
_INPUTS_KEYS = frozenset({"parameters", "globals"})
_EXPECTED_KEYS = frozenset({"return", "globals", "out_parameters", "comparison"})
_STUB_KEYS = frozenset({"mode", "returns", "expect_calls", "out_parameters"})


@dataclass(frozen=True)
class StubSpec:
    """Stub behaviour and expectations for one stubbed dependency."""

    name: str
    mode: str
    returns: tuple[str, ...] = ()
    expect_calls: str | None = None
    out_parameters: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TestCaseInputs:
    """Input values: parameters and initial values of accessed globals."""

    parameters: Mapping[str, str] = field(default_factory=dict)
    global_inits: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TestCaseExpected:
    """Expected results: return value, final globals, output parameters."""

    return_value: str | None = None
    global_finals: Mapping[str, str] = field(default_factory=dict)
    out_parameters: Mapping[str, str] = field(default_factory=dict)
    comparison: Mapping[str, Mapping[str, str]] = field(default_factory=dict)


@dataclass(frozen=True)
class TestCaseOrigin:
    """Where a case came from; review state travels with generated cases."""

    author: str = "human"
    engine: str | None = None
    model: str | None = None
    review_state: str | None = None


@dataclass(frozen=True)
class DataDrivenTestCase:
    """One data-driven test case: stable identity plus bound content digest.

    ``case_id`` is assigned at creation and never derived from content
    (DSN-TCM-110). ``content_digest`` binds the identity to the content
    (D-02 option a); ``recorded_digest`` is the digest as last written. A
    case whose recorded digest no longer matches its content is ``stale``.
    """

    case_id: str
    unit: str
    function: str
    inputs: TestCaseInputs
    expected: TestCaseExpected
    stubs: tuple[StubSpec, ...]
    origin: TestCaseOrigin = field(default_factory=TestCaseOrigin)
    requirements: tuple[str, ...] = ()
    suites: tuple[str, ...] = ()
    robustness: bool = False
    recorded_digest: str | None = None
    content_digest: str = ""
    extra: Mapping[str, str] = field(default_factory=dict)

    @property
    def stale(self) -> bool:
        """True when the recorded digest no longer matches the content."""
        if self.recorded_digest is None:
            return True
        return self.recorded_digest != self.content_digest

    def content_payload(self) -> dict[str, Any]:
        """The canonical digest payload: all content, excluding id and digests."""
        origin: dict[str, Any] = {"author": self.origin.author}
        if self.origin.engine is not None:
            origin["engine"] = self.origin.engine
        if self.origin.model is not None:
            origin["model"] = self.origin.model
        if self.origin.review_state is not None:
            origin["review_state"] = self.origin.review_state
        expected: dict[str, Any] = {
            "globals": dict(self.expected.global_finals),
            "out_parameters": dict(self.expected.out_parameters),
            "comparison": {k: dict(v) for k, v in self.expected.comparison.items()},
        }
        if self.expected.return_value is not None:
            expected["return"] = self.expected.return_value
        payload: dict[str, Any] = {
            "kind": "data",
            "unit": self.unit,
            "function": self.function,
            "origin": origin,
            "requirements": list(self.requirements),
            "suites": list(self.suites),
            "robustness": self.robustness,
            "inputs": {
                "parameters": dict(self.inputs.parameters),
                "globals": dict(self.inputs.global_inits),
            },
            "expected": expected,
            "stubs": {
                stub.name: {
                    "mode": stub.mode,
                    "returns": list(stub.returns),
                    "expect_calls": stub.expect_calls,
                    "out_parameters": dict(stub.out_parameters),
                }
                for stub in self.stubs
            },
        }
        if self.extra:
            payload["extra"] = dict(self.extra)
        return payload


@dataclass(frozen=True)
class TestCasesFile:
    """A parsed ``.tests`` document: one file per unit (SDD-003 §2.1)."""

    schema_version: int
    cases: tuple[DataDrivenTestCase, ...]
    path: Path | None = None
    extra: Mapping[str, str] = field(default_factory=dict)


def compute_case_digest(payload: Mapping[str, Any]) -> str:
    """Deterministic SHA-256 content digest over the canonical JSON encoding.

    Insertion-order independent and process independent (no ``hash()``
    involvement); identical content always yields an identical digest.
    """
    return hashlib.sha256(canonical_json_bytes(dict(payload))).hexdigest()


def refresh_digest(case: DataDrivenTestCase) -> DataDrivenTestCase:
    """Return a copy whose recorded digest matches its current content.

    The identifier is untouched (TOOL-TCD-140); only the digest binding is
    refreshed. Use after editing case values so the saved record is not stale.
    """
    digest = compute_case_digest(case.content_payload())
    return replace(case, recorded_digest=digest, content_digest=digest)


def _string_mapping(
    value: Any,
    *,
    what: str,
    case_id: str,
    path: Path | str | None,
) -> dict[str, str]:
    if value is None:
        return {}
    if isinstance(value, Mapping) and all(
        isinstance(k, str) and isinstance(v, str) for k, v in value.items()
    ):
        return dict(value)
    raise InvalidTestCasesFileError(
        f"test case '{case_id}': '{what}' must be a mapping of string to string",
        path=path,
    )


def _reject_unknown_keys(
    mapping: Mapping[str, Any],
    allowed: frozenset[str],
    *,
    what: str,
    case_id: str,
    path: Path | str | None,
) -> None:
    unknown = sorted(k for k in mapping if k not in allowed)
    if unknown:
        raise InvalidTestCasesFileError(
            f"test case '{case_id}': unknown key(s) {unknown} in '{what}'; "
            "unknown structured fields are refused rather than silently discarded "
            "(SDD-003 §5)",
            path=path,
        )


def _scalar_extras(
    entry: Mapping[str, Any],
    known: frozenset[str],
    *,
    what: str,
    case_id: str,
    path: Path | str | None,
) -> dict[str, str]:
    """Collect unknown scalar-valued keys so they survive read/edit/write."""
    extras: dict[str, str] = {}
    for key, value in entry.items():
        if key in known:
            continue
        if isinstance(value, str):
            extras[key] = value
            continue
        raise InvalidTestCasesFileError(
            f"test case '{case_id}': unknown key '{key}' in '{what}' carries a "
            "structured value; unknown structured fields are refused rather than "
            "silently discarded (SDD-003 §5)",
            path=path,
        )
    return extras


def _parse_stub(name: str, spec: Any, *, case_id: str, path: Path | str | None) -> StubSpec:
    if not isinstance(spec, Mapping):
        raise InvalidTestCasesFileError(
            f"test case '{case_id}': stub '{name}' must be a mapping",
            path=path,
        )
    _reject_unknown_keys(spec, _STUB_KEYS, what=f"stub '{name}'", case_id=case_id, path=path)
    mode = spec.get("mode")
    if not isinstance(mode, str) or not mode.strip():
        raise MissingCaseFieldError(
            f"test case '{case_id}': stub '{name}' is missing a non-empty 'mode'",
            path=path,
        )
    returns_raw = spec.get("returns")
    if returns_raw is None:
        returns: tuple[str, ...] = ()
    elif isinstance(returns_raw, list) and all(isinstance(r, str) for r in returns_raw):
        returns = tuple(returns_raw)
    else:
        raise InvalidTestCasesFileError(
            f"test case '{case_id}': stub '{name}' 'returns' must be a list of strings",
            path=path,
        )
    expect_calls = spec.get("expect_calls")
    if expect_calls is not None and (
        not isinstance(expect_calls, str) or not _EXPECT_CALL_RE.match(expect_calls)
    ):
        raise InvalidTestCaseError(
            f"test case '{case_id}': stub '{name}' 'expect_calls' must be a "
            "non-negative integer written as text",
            path=path,
        )
    out_parameters = _string_mapping(
        spec.get("out_parameters"),
        what=f"stub '{name}' 'out_parameters'",
        case_id=case_id,
        path=path,
    )
    return StubSpec(
        name=name,
        mode=mode,
        returns=returns,
        expect_calls=expect_calls,
        out_parameters=out_parameters,
    )


def _parse_case(entry: Any, *, path: Path | str | None) -> DataDrivenTestCase:
    if not isinstance(entry, Mapping):
        raise InvalidTestCasesFileError(
            "each entry under 'test_cases' must be a mapping",
            path=path,
        )
    case_id = entry.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
        raise MissingCaseFieldError(
            "test case is missing a non-empty 'id' (TOOL-TCD-140)",
            path=path,
        )
    extras = _scalar_extras(entry, _CASE_KEYS, what="test case", case_id=case_id, path=path)

    unit = entry.get("unit")
    if not isinstance(unit, str) or not unit.strip():
        raise MissingCaseFieldError(
            f"test case '{case_id}' is missing a non-empty 'unit'",
            path=path,
        )
    function = entry.get("function")
    if not isinstance(function, str) or not function.strip():
        raise MissingCaseFieldError(
            f"test case '{case_id}' is missing a non-empty 'function'",
            path=path,
        )

    origin_raw = entry.get("origin")
    if origin_raw is None:
        origin = TestCaseOrigin()
    elif isinstance(origin_raw, Mapping):
        _reject_unknown_keys(origin_raw, _ORIGIN_KEYS, what="origin", case_id=case_id, path=path)
        author = origin_raw.get("author", "human")
        if author not in _ORIGIN_AUTHORS:
            raise InvalidTestCaseError(
                f"test case '{case_id}' has unknown origin author '{author}'; "
                f"expected one of {_ORIGIN_AUTHORS}",
                path=path,
            )
        engine = origin_raw.get("engine")
        model = origin_raw.get("model")
        review_state = origin_raw.get("review_state")
        for name, value in (("engine", engine), ("model", model), ("review_state", review_state)):
            if value is not None and not isinstance(value, str):
                raise InvalidTestCasesFileError(
                    f"test case '{case_id}': origin '{name}' must be a string or absent",
                    path=path,
                )
        origin = TestCaseOrigin(
            author=author,
            engine=engine,
            model=model,
            review_state=review_state,
        )
    else:
        raise InvalidTestCasesFileError(
            f"test case '{case_id}': 'origin' must be a mapping",
            path=path,
        )

    requirements_raw = entry.get("requirements")
    if requirements_raw is None:
        requirements: tuple[str, ...] = ()
    elif isinstance(requirements_raw, list) and all(
        isinstance(r, str) and r.strip() for r in requirements_raw
    ):
        requirements = tuple(requirements_raw)
    else:
        raise InvalidTestCasesFileError(
            f"test case '{case_id}': 'requirements' must be a list of non-empty strings",
            path=path,
        )

    suites_raw = entry.get("suites")
    if suites_raw is None:
        suites: tuple[str, ...] = ()
    elif isinstance(suites_raw, list) and all(
        isinstance(name, str) and name.strip() for name in suites_raw
    ):
        suites = tuple(suites_raw)
    else:
        raise InvalidTestCasesFileError(
            f"test case '{case_id}': 'suites' must be a list of non-empty strings",
            path=path,
        )

    robustness_raw = entry.get("robustness")
    if robustness_raw is None:
        robustness = False
    elif isinstance(robustness_raw, str) and robustness_raw.lower() in ("true", "false"):
        robustness = robustness_raw.lower() == "true"
    else:
        raise InvalidTestCasesFileError(
            f"test case '{case_id}': 'robustness' must be true or false",
            path=path,
        )

    inputs_raw = entry.get("inputs")
    if not isinstance(inputs_raw, Mapping):
        raise MissingCaseFieldError(
            f"test case '{case_id}' is missing the 'inputs' section (TOOL-TCD-040)",
            path=path,
        )
    _reject_unknown_keys(inputs_raw, _INPUTS_KEYS, what="inputs", case_id=case_id, path=path)
    inputs = TestCaseInputs(
        parameters=_string_mapping(
            inputs_raw.get("parameters"), what="inputs.parameters", case_id=case_id, path=path
        ),
        global_inits=_string_mapping(
            inputs_raw.get("globals"), what="inputs.globals", case_id=case_id, path=path
        ),
    )

    expected_raw = entry.get("expected")
    if not isinstance(expected_raw, Mapping):
        raise MissingCaseFieldError(
            f"test case '{case_id}' is missing the 'expected' section (TOOL-TCD-040)",
            path=path,
        )
    _reject_unknown_keys(expected_raw, _EXPECTED_KEYS, what="expected", case_id=case_id, path=path)
    return_value = expected_raw.get("return")
    if return_value is not None and not isinstance(return_value, str):
        raise InvalidTestCasesFileError(
            f"test case '{case_id}': expected 'return' must be a string or absent",
            path=path,
        )
    comparison_raw = expected_raw.get("comparison")
    if comparison_raw is None:
        comparison: dict[str, dict[str, str]] = {}
    elif isinstance(comparison_raw, Mapping) and all(
        isinstance(v, Mapping)
        and all(isinstance(k, str) and isinstance(inner, str) for k, inner in v.items())
        for v in comparison_raw.values()
    ):
        comparison = {str(k): dict(v) for k, v in comparison_raw.items()}
    else:
        raise InvalidTestCasesFileError(
            f"test case '{case_id}': expected 'comparison' must map each target "
            "to a mapping of string to string",
            path=path,
        )
    expected = TestCaseExpected(
        return_value=return_value,
        global_finals=_string_mapping(
            expected_raw.get("globals"), what="expected.globals", case_id=case_id, path=path
        ),
        out_parameters=_string_mapping(
            expected_raw.get("out_parameters"),
            what="expected.out_parameters",
            case_id=case_id,
            path=path,
        ),
        comparison=comparison,
    )

    stubs_raw = entry.get("stubs")
    if not isinstance(stubs_raw, Mapping):
        raise MissingCaseFieldError(
            f"test case '{case_id}' is missing the 'stubs' section (TOOL-TCD-040)",
            path=path,
        )
    stubs = tuple(
        sorted(
            (_parse_stub(str(name), spec, case_id=case_id, path=path) for name, spec in stubs_raw.items()),
            key=lambda stub: stub.name,
        )
    )

    recorded_digest = entry.get("digest")
    if recorded_digest is not None and not isinstance(recorded_digest, str):
        raise InvalidTestCasesFileError(
            f"test case '{case_id}': 'digest' must be a string or absent",
            path=path,
        )

    case = DataDrivenTestCase(
        case_id=case_id,
        unit=unit,
        function=function,
        inputs=inputs,
        expected=expected,
        stubs=stubs,
        origin=origin,
        requirements=requirements,
        suites=suites,
        robustness=robustness,
        recorded_digest=recorded_digest,
        extra=extras,
    )
    digest = compute_case_digest(case.content_payload())
    return replace(case, content_digest=digest)


def parse_test_cases_document(
    doc: Mapping[str, Any],
    *,
    path: Path | str | None = None,
) -> TestCasesFile:
    """Parse an already-loaded document mapping into a :class:`TestCasesFile`.

    All scalars must already be strings (restricted-YAML discipline); schema
    versioning is dispatched per SDD-003 §5 against :data:`TEST_CASES_KIND`.
    """
    version = dispatch_schema_version(doc, TEST_CASES_KIND, file_path=path)

    cases_raw = doc.get("test_cases")
    if not isinstance(cases_raw, list):
        raise InvalidTestCasesFileError(
            "'test_cases' must be a list of test case mappings",
            path=path,
        )
    seen: set[str] = set()
    cases: list[DataDrivenTestCase] = []
    for entry in cases_raw:
        case = _parse_case(entry, path=path)
        if case.case_id in seen:
            raise DuplicateTestCaseError(
                f"test case '{case.case_id}' appears more than once in the same file",
                path=path,
            )
        seen.add(case.case_id)
        cases.append(case)
    extra = _scalar_extras(doc, _FILE_KEYS, what="file", case_id="<file>", path=path)
    return TestCasesFile(schema_version=version, cases=tuple(cases), path=None, extra=extra)


def load_test_cases_file(
    path: Path | str,
    *,
    adapter: SerializationAdapter | None = None,
) -> TestCasesFile:
    """Load and parse a ``.tests`` file from disk."""
    yaml_adapter = adapter or RestrictedYamlAdapter()
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TestCaseReadError(
            f"cannot read test cases file: {exc}",
            path=file_path,
        ) from exc
    doc = yaml_adapter.load(text, path=file_path)
    parsed = parse_test_cases_document(doc, path=file_path)
    return replace(parsed, path=file_path)


def _origin_to_dict(origin: TestCaseOrigin) -> dict[str, Any]:
    out: dict[str, Any] = {"author": origin.author}
    if origin.engine is not None:
        out["engine"] = origin.engine
    if origin.model is not None:
        out["model"] = origin.model
    if origin.review_state is not None:
        out["review_state"] = origin.review_state
    return out


def _case_to_dict(case: DataDrivenTestCase) -> dict[str, Any]:
    if case.recorded_digest is None:
        raise MissingCaseFieldError(
            f"test case '{case.case_id}' has no recorded digest; refresh it with "
            "refresh_digest() before writing (digest binding is the staleness "
            "mechanism, SDD-003 §7)",
        )
    inputs: dict[str, Any] = {}
    if case.inputs.parameters:
        inputs["parameters"] = dict(case.inputs.parameters)
    if case.inputs.global_inits:
        inputs["globals"] = dict(case.inputs.global_inits)
    expected: dict[str, Any] = {}
    if case.expected.return_value is not None:
        expected["return"] = case.expected.return_value
    if case.expected.global_finals:
        expected["globals"] = dict(case.expected.global_finals)
    if case.expected.out_parameters:
        expected["out_parameters"] = dict(case.expected.out_parameters)
    if case.expected.comparison:
        expected["comparison"] = {k: dict(v) for k, v in case.expected.comparison.items()}
    stubs: dict[str, Any] = {}
    for stub in case.stubs:
        spec: dict[str, Any] = {"mode": stub.mode}
        if stub.returns:
            spec["returns"] = list(stub.returns)
        if stub.expect_calls is not None:
            spec["expect_calls"] = stub.expect_calls
        if stub.out_parameters:
            spec["out_parameters"] = dict(stub.out_parameters)
        stubs[stub.name] = spec
    out: dict[str, Any] = {
        "id": case.case_id,
        "unit": case.unit,
        "function": case.function,
        "origin": _origin_to_dict(case.origin),
        "inputs": inputs,
        "expected": expected,
        "stubs": stubs,
        "digest": case.recorded_digest,
    }
    if case.requirements:
        out["requirements"] = list(case.requirements)
    if case.suites:
        out["suites"] = list(case.suites)
    if case.robustness:
        out["robustness"] = "true"
    out.update(case.extra)
    return out


def dump_test_cases_document(
    doc: TestCasesFile,
    *,
    adapter: SerializationAdapter | None = None,
) -> str:
    """Serialize a :class:`TestCasesFile` to deterministic restricted-YAML text.

    Output is UTF-8, LF-ended, every scalar double-quoted, ``schema_version``
    first; no timestamps or wall-clock values appear. Empty optional
    collections are omitted on write, following the project-file default
    omission pattern.
    """
    yaml_adapter = adapter or RestrictedYamlAdapter()
    data: dict[str, Any] = {
        "schema_version": str(doc.schema_version),
        "test_cases": [_case_to_dict(case) for case in doc.cases],
    }
    data.update(doc.extra)
    return yaml_adapter.dump(
        data,
        canonical_keys=TEST_CASES_KIND.canonical_keys,
        default_values=TEST_CASES_KIND.default_values,
    )


def save_test_cases_file(
    doc: TestCasesFile,
    path: Path | str,
    *,
    adapter: SerializationAdapter | None = None,
    discard_comments: bool = False,
) -> Path:
    """Atomically write a :class:`TestCasesFile` as restricted-YAML text.

    A byte-identical rewrite is a no-op. Overwriting a file that carries
    comments raises :class:`CommentPreservationError` unless
    ``discard_comments=True`` (user-authored annotations are never lost
    silently).
    """
    yaml_adapter = adapter or RestrictedYamlAdapter()
    target = Path(path)
    text = dump_test_cases_document(doc, adapter=yaml_adapter)
    if target.exists():
        try:
            existing = target.read_text(encoding="utf-8")
        except OSError as exc:
            raise TestCaseReadError(
                f"cannot read existing test cases file: {exc}",
                path=target,
            ) from exc
        if existing == text:
            return target
        comments = detect_yaml_comments(existing)
        if comments and not discard_comments:
            raise CommentPreservationError(
                f"'{target}' contains {len(comments)} comment(s); pass "
                "discard_comments=True to overwrite them",
                path=target,
            )
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = text.encode("utf-8")
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=target.parent,
        prefix=target.name + ".",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    os.replace(temp_path, target)
    return target

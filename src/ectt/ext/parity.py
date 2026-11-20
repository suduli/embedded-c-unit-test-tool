# implements: TOOL-TGT-070
"""Host and target test parity (WP-EXT-04, DSN-EXT-060).

TOOL-TGT-070: test cases shall execute unmodified on host and target, with only
configuration distinguishing the two. DSN-EXT-060: test case data and generated test
code are identical for host and target; only the toolchain configuration, runner and
result transport differ; nothing in a test case may be host- or target-specific.

Three checks make that claim *established and recorded* rather than presumed:

1. :func:`check_parity` compares a host :class:`ExecutionPlan` with a target one. The
   case set (ids and content digests) and the generated-code digest must be identical;
   only :class:`ExecutionConfig` may differ, and the fields that do differ are listed.
   Any other difference is a named violation.
2. :func:`find_portability_issues` scans test case content for what ties a case to one
   side: absolute filesystem paths, platform macros, ``getenv`` and raw non-zero
   pointer literals (a memory-map address means nothing on the other side). A case that
   is clean here is *not proven* portable; the scan finds the common leaks.
3. :func:`compare_outcomes` lines up the per-test outcomes of a host run and a target run
   and lists every divergence and every test that ran on one side only. Parity of
   *inputs* never implies parity of *behaviour*: ``establishes_target_behavior`` is always
   False, and a host success is never reported as a target success (TOOL-TGT-130).

Pure functions of their inputs: no clock, no I/O.

Satisfies: TOOL-TGT-070 (DSN-EXT-060).
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from ectt.core.determinism import stable_id
from ectt.exh.results import ResultSet
from ectt.ext.channels import CHANNEL_SEMIHOSTING, CHANNEL_SERIAL_UART
from ectt.ext.errors import ExtError
from ectt.tcm.datacases import DataDrivenTestCase

__all__ = [
    "HOST_TRANSPORT",
    "ExecutionConfig",
    "ExecutionPlan",
    "OutcomeComparison",
    "OutcomeDivergence",
    "ParityError",
    "ParityReport",
    "PortabilityIssue",
    "Violation",
    "check_parity",
    "compare_outcomes",
    "find_portability_issues",
]

HOST_TRANSPORT = "stdout"
_TARGET_TRANSPORTS = (CHANNEL_SEMIHOSTING, CHANNEL_SERIAL_UART)
_TOKEN = re.compile(r"^\S+$")


class ParityError(ExtError):
    """Raised when a parity input is malformed (not when parity is merely violated)."""

    def __init__(self, message: str, *, reason: str = "parity_error") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class ExecutionConfig:
    """The only things allowed to differ between a host run and a target run."""

    kind: str  # "host" | "target"
    toolchain: str
    runner: str
    transport: str
    target_id: str | None = None
    settings: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in ("host", "target"):
            raise ParityError(f"execution kind must be 'host' or 'target', got '{self.kind}'", reason="invalid_config")
        for what, value in (("toolchain", self.toolchain), ("runner", self.runner), ("transport", self.transport)):
            if not _TOKEN.match(value or ""):
                raise ParityError(f"execution {what} must be a non-empty token", reason="invalid_config")
        if self.kind == "host":
            if self.target_id is not None:
                raise ParityError("a host execution has no target id", reason="invalid_config")
            if self.transport != HOST_TRANSPORT:
                raise ParityError(f"a host execution reads results from '{HOST_TRANSPORT}', not '{self.transport}'", reason="invalid_config")
        else:
            if not self.target_id or not _TOKEN.match(self.target_id):
                raise ParityError("a target execution needs a target id", reason="invalid_config")
            if self.transport not in _TARGET_TRANSPORTS:
                raise ParityError(
                    f"a target execution retrieves results over one of {', '.join(_TARGET_TRANSPORTS)}, not '{self.transport}'",
                    reason="invalid_config",
                )


@dataclass(frozen=True)
class ExecutionPlan:
    """What one execution will run: the cases, the generated code, and the configuration."""

    case_digests: Mapping[str, str]  # case id -> content digest
    generated_code_digest: str
    config: ExecutionConfig

    @classmethod
    def build(
        cls,
        cases: Sequence[DataDrivenTestCase],
        generated_code: str,
        config: ExecutionConfig,
    ) -> ExecutionPlan:
        """Plan an execution of ``cases`` and ``generated_code`` under ``config``."""
        digests: dict[str, str] = {}
        for case in cases:
            if case.case_id in digests:
                raise ParityError(f"case '{case.case_id}' appears more than once", reason="duplicate_case")
            digests[case.case_id] = case.content_digest
        return cls(dict(sorted(digests.items())), stable_id(generated_code), config)


@dataclass(frozen=True)
class Violation:
    """One way the two plans are not the same test."""

    kind: str  # case_only_on_host | case_only_on_target | case_content_differs | generated_code_differs
    subject: str
    detail: str


@dataclass(frozen=True)
class ParityReport:
    """Result of comparing a host plan with a target plan."""

    violations: tuple[Violation, ...]
    config_differences: tuple[str, ...]
    identical_cases: int
    establishes_target_behavior: bool = False

    @property
    def ok(self) -> bool:
        return not self.violations


def check_parity(host: ExecutionPlan, target: ExecutionPlan) -> ParityReport:
    """Compare a host plan with a target plan; only configuration may differ."""
    if host.config.kind != "host" or target.config.kind != "target":
        raise ParityError(
            f"check_parity compares a host plan with a target plan (got {host.config.kind} and {target.config.kind})",
            reason="wrong_kind",
        )
    violations: list[Violation] = []
    host_ids, target_ids = set(host.case_digests), set(target.case_digests)
    violations.extend(Violation("case_only_on_host", i, "the case is in the host plan but not the target plan") for i in sorted(host_ids - target_ids))
    violations.extend(Violation("case_only_on_target", i, "the case is in the target plan but not the host plan") for i in sorted(target_ids - host_ids))
    shared = sorted(host_ids & target_ids)
    differing = [i for i in shared if host.case_digests[i] != target.case_digests[i]]
    violations.extend(
        Violation("case_content_differs", i, "the case content digest differs, so the two executions would not run the same test")
        for i in differing
    )
    if host.generated_code_digest != target.generated_code_digest:
        violations.append(Violation("generated_code_differs", "generated code", "the generated test code differs between host and target"))

    config_differences = tuple(
        name
        for name in ("toolchain", "runner", "transport", "settings")
        if getattr(host.config, name) != getattr(target.config, name)
    )
    return ParityReport(
        violations=tuple(violations),
        config_differences=config_differences,
        identical_cases=len(shared) - len(differing),
    )


# --- portability lint ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PortabilityIssue:
    """Something in a test case that ties it to one side."""

    case_id: str
    field_path: str
    kind: str  # absolute_path | platform_macro | host_environment | pointer_literal
    text: str


_DRIVE_PATH = re.compile(r"[A-Za-z]:[\\/]")
_UNIX_PATH = re.compile(r"(?<![\w)\]:])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]*")  # not the tail of a drive path
_PLATFORM_MACRO = re.compile(
    r"\b(_WIN32|_WIN64|__linux__|__unix__|__APPLE__|__x86_64__|__i386__|__arm__|__aarch64__|__ARM_ARCH\w*|__MINGW32__|__CYGWIN__)\b"
)
_GETENV = re.compile(r"\bgetenv\s*\(")
_POINTER_LITERAL = re.compile(r"\(\s*[A-Za-z_][\w\s]*\*+\s*\)\s*(0[xX][0-9a-fA-F]+|[0-9]+)")


def _values(case: DataDrivenTestCase) -> Iterable[tuple[str, str]]:
    for name, value in sorted(case.inputs.parameters.items()):
        yield f"inputs.parameters.{name}", value
    for name, value in sorted(case.inputs.global_inits.items()):
        yield f"inputs.globals.{name}", value
    if case.expected.return_value is not None:
        yield "expected.return", case.expected.return_value
    for name, value in sorted(case.expected.global_finals.items()):
        yield f"expected.globals.{name}", value
    for name, value in sorted(case.expected.out_parameters.items()):
        yield f"expected.out_parameters.{name}", value
    for stub in case.stubs:
        for index, value in enumerate(stub.returns):
            yield f"stubs.{stub.name}.returns[{index}]", value
        for name, value in sorted(stub.out_parameters.items()):
            yield f"stubs.{stub.name}.out_parameters.{name}", value
    for name, value in sorted(case.extra.items()):
        yield f"extra.{name}", value


def _leaks(value: str) -> Iterable[tuple[str, str]]:
    """``(kind, text)`` for every host- or target-specific construct in one value."""
    for match in _DRIVE_PATH.finditer(value):
        yield "absolute_path", value[match.start() :][:40]
    for match in _UNIX_PATH.finditer(value):
        yield "absolute_path", match.group(0)
    for match in _PLATFORM_MACRO.finditer(value):
        yield "platform_macro", match.group(0)
    for match in _GETENV.finditer(value):
        yield "host_environment", match.group(0)
    for match in _POINTER_LITERAL.finditer(value):
        literal = match.group(1)
        number = int(literal, 16) if literal[:2] in ("0x", "0X") else int(literal, 10)
        if number != 0:
            yield "pointer_literal", match.group(0)


def find_portability_issues(cases: Sequence[DataDrivenTestCase]) -> tuple[PortabilityIssue, ...]:
    """Host- or target-specific content in ``cases``, sorted by case id and field.

    Finds absolute filesystem paths, platform macros, ``getenv`` calls and non-zero
    pointer literals. A clean result does not prove portability; it means none of these
    common leaks was found.
    """
    issues = {
        PortabilityIssue(case.case_id, field_path, kind, text)
        for case in cases
        for field_path, value in _values(case)
        for kind, text in _leaks(value)
    }
    return tuple(sorted(issues, key=lambda i: (i.case_id, i.field_path, i.kind, i.text)))


# --- outcomes ------------------------------------------------------------------------------------


@dataclass(frozen=True)
class OutcomeDivergence:
    """A test whose outcome differs between the host run and the target run."""

    test_id: str
    host: str
    target: str


@dataclass(frozen=True)
class OutcomeComparison:
    """Per-test comparison of one host run and one target run."""

    agreed: tuple[str, ...]
    divergences: tuple[OutcomeDivergence, ...]
    only_on_host: tuple[str, ...]
    only_on_target: tuple[str, ...]
    #: Always False: a host success never establishes target behavior (TOOL-TGT-130).
    establishes_target_behavior: bool = False

    @property
    def consistent(self) -> bool:
        return not (self.divergences or self.only_on_host or self.only_on_target)


def compare_outcomes(host: ResultSet, target: ResultSet) -> OutcomeComparison:
    """Line up the outcomes of a host run and a target run, test by test.

    ``agreed`` means the two outcomes were equal on this pair of runs; it does not make
    the host run evidence for the target. A test present in one run only is listed, not
    skipped.
    """
    host_outcomes = {r.test_id: r.outcome for r in host.results}
    target_outcomes = {r.test_id: r.outcome for r in target.results}
    shared = sorted(set(host_outcomes) & set(target_outcomes))
    return OutcomeComparison(
        agreed=tuple(t for t in shared if host_outcomes[t] == target_outcomes[t]),
        divergences=tuple(OutcomeDivergence(t, host_outcomes[t], target_outcomes[t]) for t in shared if host_outcomes[t] != target_outcomes[t]),
        only_on_host=tuple(sorted(set(host_outcomes) - set(target_outcomes))),
        only_on_target=tuple(sorted(set(target_outcomes) - set(host_outcomes))),
    )

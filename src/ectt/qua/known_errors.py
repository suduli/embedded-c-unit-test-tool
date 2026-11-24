# implements: TOOL-QUA-040
"""The known-error list per release (WP-QUA-04).

TOOL-QUA-040: the tool shall publish a documented list of known errors and
their workarounds, maintained per release.

A :class:`KnownError` carries its id, summary, the versions it affects, its
workaround, and its status — ``open`` or ``fixed in <version>``. The list is
maintained as a plain-text data file (blank-line-separated blocks of
``field: value`` lines) and loaded strictly: every refusal names its reason —
``duplicate_error_id``, ``fixed_before_introduced``, ``missing_workaround``,
``missing_field``, ``unknown_field``, ``malformed_line``,
``version_malformed``, ``fixed_missing_version``. A loaded list is a tuple in
id order.

:func:`errors_for_release` returns exactly the entries that apply to a given
release: the release is in the entry's affected versions and the error is not
fixed as of that release (numeric per-component version comparison). The
answer is id-sorted and deterministic.

Satisfies: TOOL-QUA-040.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = [
    "KnownError",
    "KnownErrorListError",
    "errors_for_release",
    "load_known_errors",
]

_FIELDS = ("error", "summary", "introduced-in", "affected-versions", "workaround", "status")
_STATUS_OPEN = "open"


class KnownErrorListError(Exception):
    """A known-error list was refused; ``reason`` names why."""

    def __init__(self, message: str, *, reason: str, line: int | None = None) -> None:
        super().__init__(message)
        self.reason = reason
        self.line = line


@dataclass(frozen=True)
class KnownError:
    """One published known error and its workaround (TOOL-QUA-040)."""

    error_id: str
    summary: str
    introduced_in: str
    affected_versions: tuple[str, ...]
    workaround: str
    status: str  # "open" or "fixed"
    fixed_in: str | None = None

    def applies_to(self, release: str) -> bool:
        """True when this error affects ``release`` and is not fixed as of it."""
        _checked_version(release)
        if release not in self.affected_versions:
            return False
        if self.status == _STATUS_OPEN:
            return True
        assert self.fixed_in is not None
        return _version_key(release) < _version_key(self.fixed_in)


def _version_key(version: str) -> tuple[int, ...]:
    """Numeric per-component version ordering ("0.2.10" > "0.2.9")."""
    checked = _checked_version(version)
    return tuple(int(part) for part in checked.split("."))


def _checked_version(version: str) -> str:
    text = version.strip()
    if not text or not re.fullmatch(r"[0-9]+(\.[0-9]+)*", text):
        raise KnownErrorListError(
            f"version {version!r} is not a dotted numeric version", reason="version_malformed"
        )
    return text


def _parse_block(block: list[tuple[int, str, str]], seen: dict[str, int]) -> KnownError:
    fields: dict[str, str] = {}
    for line_number, key, value in block:
        if key not in _FIELDS:
            raise KnownErrorListError(
                f"line {line_number}: unknown field '{key}' (known: {', '.join(_FIELDS)})",
                reason="unknown_field",
                line=line_number,
            )
        if key in fields:
            raise KnownErrorListError(
                f"line {line_number}: field '{key}' is given twice in one entry",
                reason="duplicate_field",
                line=line_number,
            )
        fields[key] = value

    missing = [field for field in _FIELDS if field not in fields]
    if missing:
        raise KnownErrorListError(
            f"entry starting at line {block[0][0]} is missing: {', '.join(missing)}",
            reason="missing_field",
            line=block[0][0],
        )

    error_id = fields["error"]
    if error_id in seen:
        raise KnownErrorListError(
            f"line {block[0][0]}: error id '{error_id}' is already listed at line {seen[error_id]}",
            reason="duplicate_error_id",
            line=block[0][0],
        )
    seen[error_id] = block[0][0]

    if not fields["summary"].strip():
        raise KnownErrorListError(
            f"error '{error_id}': 'summary' must not be empty",
            reason="missing_field",
            line=block[0][0],
        )

    introduced = _checked_version(fields["introduced-in"])
    affected = tuple(v.strip() for v in fields["affected-versions"].split(",") if v.strip())
    if not affected:
        raise KnownErrorListError(
            f"error '{error_id}': 'affected-versions' must list at least one version",
            reason="missing_field",
            line=block[0][0],
        )
    for version in affected:
        _checked_version(version)

    status_text = fields["status"].strip()
    workaround = fields["workaround"].strip()
    if status_text == _STATUS_OPEN:
        if not workaround:
            raise KnownErrorListError(
                f"error '{error_id}' is open and must record a workaround",
                reason="missing_workaround",
                line=block[0][0],
            )
        return KnownError(
            error_id=error_id,
            summary=fields["summary"].strip(),
            introduced_in=introduced,
            affected_versions=affected,
            workaround=workaround,
            status=_STATUS_OPEN,
        )
    match = re.fullmatch(r"fixed in (\S+)", status_text)
    if match is None:
        raise KnownErrorListError(
            f"error '{error_id}': status must be 'open' or 'fixed in <version>', "
            f"got {status_text!r}",
            reason="malformed_line",
            line=block[0][0],
        )
    fixed_in = _checked_version(match.group(1))
    if _version_key(fixed_in) <= _version_key(introduced):
        raise KnownErrorListError(
            f"error '{error_id}' is fixed in {fixed_in}, which is not after the "
            f"version it was introduced in ({introduced})",
            reason="fixed_before_introduced",
            line=block[0][0],
        )
    if not workaround:
        raise KnownErrorListError(
            f"error '{error_id}' is open up to its fix and must record a workaround",
            reason="missing_workaround",
            line=block[0][0],
        )
    return KnownError(
        error_id=error_id,
        summary=fields["summary"].strip(),
        introduced_in=introduced,
        affected_versions=affected,
        workaround=workaround,
        status="fixed",
        fixed_in=fixed_in,
    )


def load_known_errors(text: str) -> tuple[KnownError, ...]:
    """Load and strictly validate the plain-text known-error list, in id order.

    The file is blank-line-separated blocks of ``field: value`` lines; the
    fields are ``error``, ``summary``, ``introduced-in``, ``affected-versions``
    (comma-separated), ``workaround`` and ``status`` (``open`` or
    ``fixed in <version>``). Every refusal names its reason; a list with any
    violation loads whole or not at all.
    """
    blocks: list[list[tuple[int, str, str]]] = []
    current: list[tuple[int, str, str]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            if current:
                blocks.append(current)
                current = []
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise KnownErrorListError(
                f"line {line_number}: not a 'field: value' line: {raw_line.strip()!r}",
                reason="malformed_line",
                line=line_number,
            )
        current.append((line_number, key.strip(), value.strip()))
    if current:
        blocks.append(current)

    seen: dict[str, int] = {}
    errors = [_parse_block(block, seen) for block in blocks]
    return tuple(sorted(errors, key=lambda e: e.error_id))


def errors_for_release(errors: tuple[KnownError, ...], release: str) -> tuple[KnownError, ...]:
    """The entries that apply to ``release``, id-sorted and deterministic."""
    return tuple(error for error in errors if error.applies_to(release))

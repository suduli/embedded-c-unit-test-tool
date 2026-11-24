# implements: TOOL-NFR-100
"""Pinned dependency integrity check (WP-SEC-02).

Compares the installed packages with a pinned lock file and reports each
difference by name, exactly one difference per package and kind:

* ``missing`` — pinned but not installed;
* ``extra`` — installed but not pinned;
* ``wrong_version`` — both present, versions differ;
* ``wrong_hash`` — both hashes present and differ;
* ``unpinned`` — integrity cannot be verified: the lock entry or the installed
  evidence carries no SHA-256 hash.

The checker is **read-only**: the installed state arrives as data (the caller
reads it, e.g. through ``ectt.sec.sbom.read_installed_packages``) and the lock
as text — nothing is installed, upgraded or written, and no network is used.
The result is deterministic: differences sorted by (name, kind).

The lock format is the pinned requirements form, one package per line::

    name==1.2.3 --hash=sha256:<64 lowercase hex>

Comments (``#``) and blank lines are ignored; loading is strict with named
refusals (``malformed_line``, ``bad_hash``, ``duplicate_pin``).

Satisfies: the supply-chain integrity requirement of the security policy.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from ectt.sec.errors import SecError

__all__ = ["PinDifference", "PinnedPackage", "check_pins", "load_pin_lock"]

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_LINE_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([0-9][A-Za-z0-9.+*-]*)(?:\s+--hash=sha256:([0-9a-f]{64}))?$")

#: The difference kinds, in the order the report sorts them.
KIND_MISSING = "missing"
KIND_EXTRA = "extra"
KIND_WRONG_VERSION = "wrong_version"
KIND_WRONG_HASH = "wrong_hash"
KIND_UNPINNED = "unpinned"


@dataclass(frozen=True)
class PinnedPackage:
    """One lock-file pin: the exact version and, when pinned, the hash."""

    name: str
    version: str
    sha256: str | None = None


@dataclass(frozen=True)
class PinDifference:
    """One way the installed tree differs from the lock, by name."""

    kind: str  # missing | extra | wrong_version | wrong_hash | unpinned
    name: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"detail": self.detail, "kind": self.kind, "name": self.name}


def load_pin_lock(text: str) -> tuple[PinnedPackage, ...]:
    """Load and strictly validate the pinned lock file, name-sorted.

    Refusals name their reason: ``malformed_line`` (a line that is neither a
    comment, blank nor a ``name==version[--hash=...]`` pin), ``bad_hash`` (a
    hash that is not 64 lowercase hex), ``duplicate_pin`` (a package pinned
    twice).
    """
    pins: dict[str, PinnedPackage] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _LINE_RE.match(line)
        if match is None:
            raise SecError(
                f"line {line_number} of the lock file is not a pin "
                f"(expected 'name==version [--hash=sha256:<64 hex>]'): {line!r}",
                reason="malformed_line",
            )
        name, version, sha256 = match.group(1), match.group(2), match.group(3)
        if sha256 is None:
            # A pin without a hash is loadable but is reported as unpinned.
            pass
        if name in pins:
            raise SecError(
                f"line {line_number}: '{name}' is pinned more than once",
                reason="duplicate_pin",
            )
        pins[name] = PinnedPackage(name=name, version=version, sha256=sha256)
    return tuple(sorted(pins.values(), key=lambda p: p.name))


def check_pins(
    installed: Mapping[str, tuple[str, str | None]],
    pins: Mapping[str, PinnedPackage],
) -> tuple[PinDifference, ...]:
    """Compare the installed state with the pins; each difference by name.

    ``installed`` maps package name to ``(version, sha256-or-None)`` — the
    caller supplies it (read-only by construction). ``pins`` maps name to the
    lock entry. Deterministic: the differences are sorted by (name, kind).
    """
    differences: list[PinDifference] = []
    for name in sorted(set(pins) | set(installed)):
        pin = pins.get(name)
        present = installed.get(name)
        if pin is not None and present is None:
            differences.append(
                PinDifference(KIND_MISSING, name, f"pinned at {pin.version} but not installed")
            )
            continue
        if pin is None and present is not None:
            version, _sha = present
            differences.append(
                PinDifference(KIND_EXTRA, name, f"installed at {version} but not pinned")
            )
            continue
        assert pin is not None and present is not None
        version, installed_hash = present
        if version != pin.version:
            differences.append(
                PinDifference(
                    KIND_WRONG_VERSION,
                    name,
                    f"pinned {pin.version}, installed {version}",
                )
            )
            continue
        if pin.sha256 is None:
            differences.append(
                PinDifference(
                    KIND_UNPINNED,
                    name,
                    "the lock entry records no hash; integrity cannot be verified",
                )
            )
            continue
        if installed_hash is None:
            differences.append(
                PinDifference(
                    KIND_UNPINNED,
                    name,
                    "the installed evidence records no hash; integrity cannot be verified",
                )
            )
            continue
        if installed_hash != pin.sha256:
            differences.append(
                PinDifference(
                    KIND_WRONG_HASH,
                    name,
                    f"pinned sha256 {pin.sha256}, installed {installed_hash}",
                )
            )
    return tuple(sorted(differences, key=lambda d: (d.name, d.kind)))

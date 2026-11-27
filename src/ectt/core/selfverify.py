# implements: TOOL-NFR-100
"""Self-verification of the tool's own source (WP-CORE-08).

A manifest records the SHA-256 of every file of a package tree as canonical
JSON (``manifest_version``, ``files`` mapping of project-relative POSIX path
to 64-hex digest, sorted), with ``__pycache__`` directories and ``.pyc`` files
ignored everywhere. :func:`verify_tree` loads the manifest strictly and names
every difference:

* ``changed`` — present in both, digest differs;
* ``missing`` — in the manifest, not in the tree;
* ``unexpected`` — in the tree, not in the manifest.

The manifest itself is load-verified: a malformed document, an unknown
manifest version, a non-hex digest or a non-mapping file entry is refused
(``manifest_tampered``/``manifest_malformed``/``manifest_version``) — never
silently accepted as clean.

No manifest generated from this repository's tree is committed as a fixed
file: the functions operate on any tree, and the tests build their own temp
trees. Generating the shipped manifest at packaging time, and signing it, are
owner concerns (see docs/verification/WP-CORE-08-analysis.md).

Satisfies: the tool's own-source integrity requirement of the security policy.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ectt.core.errors import EcttError

__all__ = ["SelfVerification", "SelfVerificationError", "verify_tree", "write_manifest"]

MANIFEST_VERSION = "1"

_IGNORED_DIRS = frozenset({"__pycache__"})
_IGNORED_SUFFIXES = (".pyc",)


class SelfVerificationError(EcttError):
    """A manifest was refused; ``reason`` names why (tamper, version, shape)."""

    def __init__(self, message: str, *, reason: str = "manifest_malformed") -> None:
        super().__init__(message, reason=reason)


def _is_ignored(relative: Path) -> bool:
    if any(part in _IGNORED_DIRS for part in relative.parts):
        return True
    return relative.suffix in _IGNORED_SUFFIXES


def _relative_files(tree: Path) -> tuple[Path, ...]:
    relatives: list[Path] = []
    for path in sorted(tree.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(tree)
        if _is_ignored(relative):
            continue
        relatives.append(relative)
    return tuple(relatives)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(tree: Path | str) -> str:
    """The deterministic manifest text of one package tree (SHA-256 per file)."""
    root = Path(tree)
    files: dict[str, str] = {
        relative.as_posix(): _digest(root / relative) for relative in _relative_files(root)
    }
    return json.dumps({"files": files, "manifest_version": MANIFEST_VERSION}, sort_keys=True, indent=1)


def _load_manifest(text: str) -> dict[str, str]:
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SelfVerificationError(
            f"the manifest is not valid JSON: {exc}", reason="manifest_malformed"
        ) from exc
    if not isinstance(document, dict) or document.get("manifest_version") != MANIFEST_VERSION:
        raise SelfVerificationError(
            f"unsupported manifest (expected manifest_version {MANIFEST_VERSION!r})",
            reason="manifest_version",
        )
    files = document.get("files")
    if not isinstance(files, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in files.items()):
        raise SelfVerificationError(
            "the manifest's 'files' must map paths to digest strings",
            reason="manifest_malformed",
        )
    for path, digest in files.items():
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise SelfVerificationError(
                f"the manifest entry for '{path}' carries a malformed SHA-256 digest",
                reason="manifest_tampered",
            )
    return dict(files)


@dataclass(frozen=True)
class SelfVerification:
    """The verdict: every difference named, clean exactly when all empty."""

    changed: tuple[str, ...]
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not (self.changed or self.missing or self.unexpected)

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed": list(self.changed),
            "missing": list(self.missing),
            "ok": self.ok,
            "unexpected": list(self.unexpected),
        }


def verify_tree(tree: Path | str, manifest_text: str) -> SelfVerification:
    """Verify one tree against its manifest, naming every difference.

    The manifest is load-verified first (a tampered or malformed manifest is
    refused, never silently accepted); the tree is then digested the same way
    :func:`write_manifest` digests it, and the three difference lists —
    ``changed``, ``missing``, ``unexpected`` — are returned sorted.
    """
    expected = _load_manifest(manifest_text)
    actual = {
        relative.as_posix(): _digest(Path(tree) / relative) for relative in _relative_files(Path(tree))
    }
    changed = tuple(sorted(path for path, digest in expected.items() if path in actual and actual[path] != digest))
    missing = tuple(sorted(path for path in expected if path not in actual))
    unexpected = tuple(sorted(path for path in actual if path not in expected))
    return SelfVerification(changed=changed, missing=missing, unexpected=unexpected)

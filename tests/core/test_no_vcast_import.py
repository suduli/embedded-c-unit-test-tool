"""Prototype no-import check for vcast-findings material (TASK-015, T-02).

Verifies: the tool's own source does not reproduce strings or identifiers recovered
from the vcast-findings assets. The assets are read only to build deny-lists in
memory. Nothing from them is copied into this file or into the repository.

This prototype depends on owner decision D-01 (licence posture, ADR-005) and is
not adopted. See docs/proposals/T-02-no-import-rule-draft.md.

The real scan runs only when the findings tree is reachable through the
ECTT_VCAST_FINDINGS environment variable (or a local vcast-findings/ folder). The
planted-fixture tests always run.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
FINDINGS_ENV = "ECTT_VCAST_FINDINGS"
MIN_TOKEN_LENGTH = 16
_SKIP_DIRS = {"__pycache__", ".git", ".venv"}


def _findings_root() -> Path | None:
    configured = os.environ.get(FINDINGS_ENV, "").strip()
    if configured:
        path = Path(configured)
        return path if path.is_dir() else None
    local = REPO_ROOT / "vcast-findings"
    return local if local.is_dir() else None


def _long_enough(values: list[str]) -> set[str]:
    return {v.strip() for v in values if len(v.strip()) >= MIN_TOKEN_LENGTH}


def _symbol_names(symbols_json: dict[str, object]) -> list[str]:
    names: list[str] = []
    for export in symbols_json.get("exports", []) or []:
        if isinstance(export, dict):
            names.extend(str(n) for n in export.get("names", []) or [])
    for imported in symbols_json.get("imports", []) or []:
        if isinstance(imported, dict):
            names.extend(str(s) for s in imported.get("symbols", []) or [])
    return names


def build_deny_list(findings_root: Path) -> frozenset[str]:
    """Build the deny-list in memory from the findings assets. Writes nothing."""
    entries: set[str] = set()

    sql_strings = findings_root / "vcapplib-sql-strings.json"
    if sql_strings.is_file():
        for record in json.loads(sql_strings.read_text(encoding="utf-8")):
            if isinstance(record, dict):
                entries |= _long_enough([str(record.get("text", ""))])

    schema = findings_root / "vcapplib-recovered-schema.sql"
    if schema.is_file():
        statements = [
            line
            for line in schema.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("--")
        ]
        entries |= _long_enough(statements)

    for symbols in sorted(findings_root.glob("*-symbols.json")):
        data = json.loads(symbols.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            entries |= _long_enough(_symbol_names(data))

    return frozenset(entries)


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def scan(src_root: Path, deny: frozenset[str]) -> tuple[str, ...]:
    """Return sorted 'relative/path: token' hits. Empty means the rule holds."""
    hits: list[str] = []
    for path in sorted(src_root.rglob("*")):
        if not path.is_file() or any(part in _SKIP_DIRS for part in path.parts):
            continue
        try:
            text = _normalise(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(src_root).as_posix()
        hits.extend(f"{rel}: {token}" for token in sorted(deny) if token in text)
    return tuple(hits)


# --- planted-fixture tests: always run -------------------------------------------------


def _write_fixture(root: Path, planted: str | None) -> tuple[Path, Path]:
    findings = root / "findings"
    findings.mkdir()
    (findings / "vcapplib-sql-strings.json").write_text(
        json.dumps(
            [{"file_offset": 1, "text": "CREATE TABLE FIXTURE_ONLY (ROWID INTEGER);"}]
        ),
        encoding="utf-8",
    )
    src = root / "src"
    src.mkdir()
    body = "def f() -> None:\n    return None\n"
    if planted is not None:
        body += f'\nSQL = "{planted}"\n'
    (src / "module.py").write_text(body, encoding="utf-8")
    return findings, src


def test_planted_fixture_string_is_detected(tmp_path: Path) -> None:
    """verifies: T-02 prototype — a copied findings string in src/ is reported."""
    findings, src = _write_fixture(
        tmp_path, planted="CREATE TABLE FIXTURE_ONLY (ROWID INTEGER);"
    )

    hits = scan(src, build_deny_list(findings))

    assert hits == ("module.py: CREATE TABLE FIXTURE_ONLY (ROWID INTEGER);",)


def test_clean_fixture_source_passes(tmp_path: Path) -> None:
    """verifies: T-02 prototype — source with no findings material gives no hits."""
    findings, src = _write_fixture(tmp_path, planted=None)

    assert scan(src, build_deny_list(findings)) == ()


def test_short_tokens_are_not_denied(tmp_path: Path) -> None:
    """verifies: T-02 prototype — short common words cannot trigger the rule."""
    findings = tmp_path / "findings"
    findings.mkdir()
    (findings / "vcapplib-sql-strings.json").write_text(
        json.dumps([{"file_offset": 1, "text": "TAG"}]), encoding="utf-8"
    )

    assert build_deny_list(findings) == frozenset()


def test_scan_output_is_deterministic(tmp_path: Path) -> None:
    """verifies: T-02 prototype — two runs over the same inputs give the same hits."""
    findings, src = _write_fixture(
        tmp_path, planted="CREATE TABLE FIXTURE_ONLY (ROWID INTEGER);"
    )
    deny = build_deny_list(findings)

    assert scan(src, deny) == scan(src, deny)


# --- real findings: run when the tree is reachable ------------------------------------


@pytest.mark.skipif(
    _findings_root() is None,
    reason=f"vcast-findings not reachable; set {FINDINGS_ENV} to run the real scan",
)
def test_repository_source_contains_no_findings_material() -> None:
    """verifies: T-02 — src/ reproduces no string or identifier from vcast-findings."""
    findings = _findings_root()
    assert findings is not None
    deny = build_deny_list(findings)

    assert deny, "deny-list is empty; the findings assets were not read"
    assert scan(SRC_ROOT, deny) == ()

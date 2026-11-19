"""gh transport: fresh-process retry with bounded attempts, transient-only.

gh's internal retry holds one long-lived connection open for minutes, which is
what gets aborted by intermediate firewalls and crashes gh under sustained
throttling. The transport therefore caps each attempt (fresh process, fresh
connection, fresh auth) and retries only transient failures itself.
"""
from __future__ import annotations

import subprocess

import pytest

import github_projects as gp


class _Proc:
    def __init__(self, returncode: int = 0, stdout: str = '{"data":{}}', stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _patch_sleep(monkeypatch):
    monkeypatch.setattr(gp, "RETRY_DELAYS", (0, 0, 0))


def test_transient_failures_are_retried_with_fresh_processes(monkeypatch):
    _patch_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(args, **kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            raise subprocess.TimeoutExpired(cmd=args, timeout=1)
        return _Proc()

    monkeypatch.setattr(gp.subprocess, "run", fake_run)
    assert gp.Gh(timeout=1).graphql("query{viewer{login}}") == {}
    assert calls["n"] == 3


def test_http_502_is_retried_then_succeeds(monkeypatch):
    _patch_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _Proc(returncode=1, stderr="gh: HTTP 502 (exceeded allowed budget)")
        return _Proc()

    monkeypatch.setattr(gp.subprocess, "run", fake_run)
    assert gp.Gh(timeout=1).graphql("query{viewer{login}}") == {}
    assert calls["n"] == 2


def test_attempts_exhausted_fails_visibly(monkeypatch):
    _patch_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(args, **kwargs):
        calls["n"] += 1
        raise subprocess.TimeoutExpired(cmd=args, timeout=1)

    monkeypatch.setattr(gp.subprocess, "run", fake_run)
    with pytest.raises(gp.GhError) as excinfo:
        gp.Gh(timeout=1, attempts=2).graphql("query{viewer{login}}")
    assert calls["n"] == 2
    assert "attempt 2/2" in str(excinfo.value)


def test_auth_failures_are_never_retried(monkeypatch):
    _patch_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(args, **kwargs):
        calls["n"] += 1
        return _Proc(returncode=4, stderr="gh: auth required")

    monkeypatch.setattr(gp.subprocess, "run", fake_run)
    with pytest.raises(gp.GhError, match="gh auth login"):
        gp.Gh(timeout=1).graphql("query{viewer{login}}")
    assert calls["n"] == 1


def test_validation_4xx_is_never_retried(monkeypatch):
    _patch_sleep(monkeypatch)
    calls = {"n": 0}

    def fake_run(args, **kwargs):
        calls["n"] += 1
        return _Proc(returncode=1, stderr='gh: Invalid request. "title" wasn\'t supplied. (HTTP 422)')

    monkeypatch.setattr(gp.subprocess, "run", fake_run)
    with pytest.raises(gp.GhError, match="422"):
        gp.Gh(timeout=1).rest("repos/x/y/issues", params={"state": "all"})
    assert calls["n"] == 1


def test_default_attempt_budget_and_timeout():
    gh = gp.Gh()
    assert gh.timeout == 90
    assert gh.attempts == 4

"""uip_auth hands the login to one subprocess; it never lands in the process env."""

from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import uip_auth  # noqa: E402


def _jwt(exp: float) -> str:
    seg = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).decode().rstrip("=")
    return f"h.{seg}.s"


def _write(path: Path, token: str) -> None:
    path.write_text(
        f"UIPATH_ACCESS_TOKEN={token}\nUIPATH_REFRESH_TOKEN=r\nUIPATH_URL=https://x.test\n"
        "UIPATH_ORGANIZATION_NAME=org\nUIPATH_ORGANIZATION_ID=oid\n"
        "UIPATH_TENANT_NAME=ten\nUIPATH_TENANT_ID=tid\n",
        encoding="utf-8",
    )


def test_no_auth_file_returns_env_unchanged(tmp_path):
    env = uip_auth.grader_env({"A": "1"}, candidates=(str(tmp_path / "missing"),))
    assert env == {"A": "1"}


def test_fresh_token_becomes_env_auth_for_the_copy_only(tmp_path, monkeypatch):
    f = tmp_path / ".auth"
    token = _jwt(time.time() + 3600)
    _write(f, token)
    monkeypatch.delenv("UIPATH_CLI_AUTH_TOKEN", raising=False)
    env = uip_auth.grader_env({}, candidates=(str(f),))
    assert env["UIPATH_CLI_AUTH_TOKEN"] == token
    assert env["UIPATH_CLI_ENABLE_ENV_AUTH"] == "true"
    assert (env["UIPATH_CLI_TENANT_ID"], env["UIPATH_CLI_ORGANIZATION_NAME"]) == ("tid", "org")
    assert "UIPATH_CLI_AUTH_TOKEN" not in os.environ
    assert "UIPATH_REFRESH_TOKEN" not in env and token not in os.environ.values()


def test_expired_token_is_reread_after_refresh(tmp_path):
    f = tmp_path / ".auth"
    _write(f, _jwt(time.time() - 10))
    fresh = _jwt(time.time() + 3600)

    def refresher(_seconds):
        _write(f, fresh)

    env = uip_auth.grader_env({}, candidates=(str(f),), sleep=refresher)
    assert env["UIPATH_CLI_AUTH_TOKEN"] == fresh


def test_never_renewed_token_raises(tmp_path):
    f = tmp_path / ".auth"
    _write(f, _jwt(time.time() - 10))
    with pytest.raises(uip_auth.AuthExpired, match="ENVIRONMENT"):
        uip_auth.grader_env({}, candidates=(str(f),), sleep=lambda _s: None)


def test_unreadable_file_retries_then_raises(tmp_path, monkeypatch):
    f = tmp_path / ".auth"
    _write(f, _jwt(time.time() + 3600))
    monkeypatch.setattr(uip_auth, "_read", lambda _p: (_ for _ in ()).throw(PermissionError()))
    with pytest.raises(uip_auth.AuthExpired, match="unreadable"):
        uip_auth.grader_env({}, candidates=(str(f),), sleep=lambda _s: None)

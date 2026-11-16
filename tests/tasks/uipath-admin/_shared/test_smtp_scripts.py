#!/usr/bin/env python3
"""Negative controls for the SMTP configure task's pre-run reset and read-back.

Same idea as test_verify_negative_controls.py: drive each script against
synthetic `uip admin smtp` answers (a stubbed `run_cli`) and assert it fails,
with the right diagnosis, for each way the organization can be in the wrong
state. The inherited state below is what the eval organization reads after
`smtp delete` (adhoc-2026-10-24_04-12-42 and adhoc-2026-11-05_09-36-32).

Run:  python3 -m pytest tests/tasks/uipath-admin/_shared/test_smtp_scripts.py -q
"""

import importlib.util
import io
import logging
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

ADMIN_DIR = Path(__file__).resolve().parent.parent
SETUP_DIR = ADMIN_DIR / "_setup"
RESET = ADMIN_DIR / "identity" / "_setup" / "setup_smtp_reset.py"
CHECK = ADMIN_DIR / "identity" / "check_smtp_settings.py"

INHERITED = {
    "Host": "smtp.example.com",
    "Port": "587",
    "EnableSsl": "true",
    "FromAddress": "admin@mydomain.com",
    "FromDisplayName": "mydomain.com mailer",
}
TARGET = {
    "Host": "smtp-e2e.example.com",
    "Port": "2525",
    "EnableSsl": "true",
    "FromAddress": "noreply@example.com",
    "FromDisplayName": "UiPath E2E Test",
}


class FakeOrg:
    """`uip admin smtp` against one organization's settings.

    `get` returns `settings` (None = the call fails). `delete` swaps in
    `after_delete` unless `delete_ok` is False.
    """

    def __init__(self, settings, after_delete=INHERITED, delete_ok=True):
        self.settings = settings
        self.after_delete = after_delete
        self.delete_ok = delete_ok

    def __call__(self, args, timeout=30, quiet=False):
        if args[:3] == ["admin", "smtp", "delete"]:
            if not self.delete_ok:
                return None
            self.settings = self.after_delete
            return {"Result": "Success", "Code": "SmtpSettingsDeleted"}
        if args[:3] == ["admin", "smtp", "get"]:
            if self.settings is None:
                return None
            return {"Result": "Success", "Code": "SmtpSettings", "Data": dict(self.settings)}
        raise AssertionError(f"unexpected CLI call: {args}")


def run_script(path, org, caplog):
    """Execute a script with `run_cli` stubbed. Returns (exit_code, stdout + log text)."""
    spec = importlib.util.spec_from_file_location("admin_helpers", SETUP_DIR / "admin_helpers.py")
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    # Stub the only I/O boundary; keep fail/ok real. poll() must not sleep.
    helpers.run_cli = org
    real_poll = helpers.poll
    helpers.poll = lambda fn, max_attempts=4, delay=5: real_poll(fn, max_attempts, 0)
    sys.modules["admin_helpers"] = helpers

    caplog.set_level(logging.INFO)
    buf = io.StringIO()
    exit_code = 0
    try:
        with redirect_stdout(buf):
            exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"),
                 {"__name__": "script_under_test", "__file__": str(path)})
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.modules.pop("admin_helpers", None)
    return exit_code, buf.getvalue() + caplog.text


# --------------------------------------------------------------------------
# pre-run reset
# --------------------------------------------------------------------------

@pytest.mark.parametrize("label,before,after", [
    ("leftover target settings", TARGET, INHERITED),
    ("already inherited", INHERITED, INHERITED),
    ("nothing inherited", INHERITED, {}),
])
def test_reset_passes_once_target_host_is_gone(label, before, after, caplog):
    rc, out = run_script(RESET, FakeOrg(before, after_delete=after), caplog)
    assert rc == 0, out
    assert "SMTP reset" in out


def test_reset_fails_when_delete_fails(caplog):
    rc, out = run_script(RESET, FakeOrg(TARGET, delete_ok=False), caplog)
    assert rc == 1
    assert "smtp delete failed" in out


def test_reset_fails_when_target_host_survives_delete(caplog):
    rc, out = run_script(RESET, FakeOrg(TARGET, after_delete=TARGET), caplog)
    assert rc == 1
    assert "still reads" in out


def test_reset_fails_when_settings_are_unreadable(caplog):
    rc, out = run_script(RESET, FakeOrg(TARGET, after_delete=None), caplog)
    assert rc == 1
    assert "could not read" in out


# --------------------------------------------------------------------------
# read-back
# --------------------------------------------------------------------------

def test_check_passes_on_target_settings(caplog):
    """Control: the correct end state must PASS, or the negatives prove nothing."""
    rc, out = run_script(CHECK, FakeOrg({**TARGET, "EnableSsl": "True"}), caplog)
    assert rc == 0, out
    assert "OK:" in out


@pytest.mark.parametrize("label,settings,expect", [
    # What the 2026-11-05 run would have left had the agent written nothing.
    ("inherited only", INHERITED, ["host=", "port=", "fromaddress=", "fromdisplayname="]),
    # The 2026-11-05 agent's partial update, against the new prompt.
    ("sender fields only", {**INHERITED, "FromAddress": TARGET["FromAddress"],
                            "FromDisplayName": TARGET["FromDisplayName"]}, ["host=", "port="]),
    ("wrong port", {**TARGET, "Port": "587"}, ["port='587'"]),
    ("ssl off", {**TARGET, "EnableSsl": "false"}, ["enablessl="]),
    ("field missing", {k: v for k, v in TARGET.items() if k != "FromDisplayName"}, ["fromdisplayname=None"]),
])
def test_check_fails_and_names_wrong_fields(label, settings, expect, caplog):
    rc, out = run_script(CHECK, FakeOrg(settings), caplog)
    assert rc == 1, out
    for field in expect:
        assert field in out, f"{label}: {field!r} not in {out!r}"


def test_check_fails_when_settings_are_unreadable(caplog):
    rc, out = run_script(CHECK, FakeOrg(None), caplog)
    assert rc == 1
    assert "could not read SMTP settings" in out

#!/usr/bin/env python3
"""Negative controls for the uipath-admin maintain verify scripts.

WHY THIS EXISTS. Every defect found in three rounds of review on this suite had
one root cause: the assertions were only ever observed PASSING. Nobody proved
they could fail. A criterion that cannot fail is indistinguishable from a
criterion that works, and three green runs look identical either way.

These tests drive each verify script against synthetic tenant state — a stubbed
`run_cli` — and assert it exits non-zero with a specific diagnosis for each way
the agent (or the seed) can be wrong. No live tenant, no eval run, runs in
milliseconds.

Excluded from coder_eval task discovery: `/test-coverage` skips `_shared/test_*.py`.

Run:  python3 -m pytest tests/tasks/uipath-admin/_shared/test_verify_negative_controls.py -q
"""

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

ADMIN_DIR = Path(__file__).resolve().parent.parent
SHARED_DIR = Path(__file__).resolve().parent


def _load_verify(module_name, responder, state, tmp_path, monkeypatch):
    """Execute a verify script with `run_cli` stubbed and a synthetic state file.

    Returns (exit_code, stdout_text). Verify scripts call main() at import time
    and signal via SystemExit, so the module is loaded fresh each call.
    """
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setenv("TEMP", str(tmp_path))
    monkeypatch.setenv("TMP", str(tmp_path))

    real_helpers_path = SHARED_DIR / "admin_helpers.py"
    spec = importlib.util.spec_from_file_location("admin_helpers", real_helpers_path)
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)

    # Stub the only I/O boundary; keep fail/ok/poll/first_list real so we test
    # the actual control flow. poll() must not sleep on the failure paths.
    helpers.run_cli = responder
    helpers.poll = lambda fn, max_attempts=1, delay=0: fn()
    sys.modules["admin_helpers"] = helpers

    target = ADMIN_DIR / f"{module_name}.py"
    src = target.read_text(encoding="utf-8")

    # Point the module's STATE_FILE at the synthetic one.
    state_file = tmp_path / "state.json"
    if state is not None:
        state_file.write_text(json.dumps(state), encoding="utf-8")

    ns = {"__name__": "verify_under_test", "__file__": str(target)}
    code = src.replace(
        'STATE_FILE = os.path.join(tempfile.gettempdir(),',
        f'STATE_FILE = {str(state_file)!r} or os.path.join(tempfile.gettempdir(),',
    )

    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    exit_code = 0
    try:
        with redirect_stdout(buf):
            exec(compile(code, str(target), "exec"), ns)
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.modules.pop("admin_helpers", None)
    return exit_code, buf.getvalue()


def envelope(data):
    return {"Result": "Success", "Data": data}


# --------------------------------------------------------------------------
# identity
# --------------------------------------------------------------------------

IDENT_SEED = {
    "other_groups": ["Everyone", "Administrators", "FinanceAdmins"],
    "group_rename_id": "g-rename",
    "group_stale_id": "g-stale",
    "bot_update_id": "b-keep",
    "bot_retire_id": "b-retire",
}


def ident_state(groups, robots):
    def responder(args, timeout=30, quiet=False):
        if args[1] == "groups":
            return envelope(groups)
        if args[1] == "robot-accounts":
            return envelope(robots)
        return None
    return responder


GOOD_GROUPS = [
    {"Id": "sys-1", "Name": "Everyone", "Type": 0},
    {"Id": "sys-2", "Name": "Administrators", "Type": 0},
    {"Id": "cust-1", "Name": "FinanceAdmins", "Type": 1},
    {"Id": "g-rename", "Name": "ce-identity-maintain-group-renamed", "Type": 1},
]
GOOD_ROBOTS = [{"Id": "b-keep", "Name": "ce-identity-maintain-bot",
                "DisplayName": "Maintain Bot Updated"}]


def test_identity_happy_path_passes(tmp_path, monkeypatch):
    """Control: the correct end state must PASS, or the negatives prove nothing."""
    rc, out = _load_verify("verify_identity_maintained",
                           ident_state(GOOD_GROUPS, GOOD_ROBOTS), IDENT_SEED, tmp_path, monkeypatch)
    assert rc == 0, out
    assert "OK:" in out


@pytest.mark.parametrize("label,groups,robots,expect", [
    ("stale group RENAMED not deleted",
     GOOD_GROUPS + [{"Id": "g-stale", "Name": "zz-archived-stale", "Type": 1}],
     GOOD_ROBOTS, "was renamed or left in place, not deleted"),
    ("retired robot RENAMED not deleted",
     GOOD_GROUPS,
     GOOD_ROBOTS + [{"Id": "b-retire", "Name": "zz-archived-bot"}],
     "was renamed or left in place, not deleted"),
    ("renamed group is a NEW group, not the seeded one",
     [g for g in GOOD_GROUPS if g["Id"] != "g-rename"]
     + [{"Id": "g-brand-new", "Name": "ce-identity-maintain-group-renamed", "Type": 1}],
     GOOD_ROBOTS, "a new group was created instead of renaming"),
    ("collateral deletion of a real shared group",
     [g for g in GOOD_GROUPS if g["Name"] != "FinanceAdmins"],
     GOOD_ROBOTS, "non-fixture group(s) were deleted"),
    ("display name never updated",
     GOOD_GROUPS,
     [{"Id": "b-keep", "Name": "ce-identity-maintain-bot", "DisplayName": "Maintain Bot"}],
     "display name not updated"),
    ("kept robot recreated rather than updated",
     GOOD_GROUPS,
     [{"Id": "b-different", "Name": "ce-identity-maintain-bot",
       "DisplayName": "Maintain Bot Updated"}],
     "recreated, not updated in place"),
])
def test_identity_negative(label, groups, robots, expect, tmp_path, monkeypatch):
    rc, out = _load_verify("verify_identity_maintained",
                           ident_state(groups, robots), IDENT_SEED, tmp_path, monkeypatch)
    assert rc == 1, f"{label}: expected failure, got pass. out={out}"
    assert expect in out, f"{label}: wrong diagnosis. out={out}"


@pytest.mark.parametrize("label,state", [
    ("missing state file", None),
    ("empty snapshot", {**IDENT_SEED, "other_groups": []}),
    ("missing fixture id", {k: v for k, v in IDENT_SEED.items() if k != "group_stale_id"}),
])
def test_identity_degenerate_seed_fails_loudly(label, state, tmp_path, monkeypatch):
    """A seed that did not complete must FAIL, never silently skip the check."""
    rc, out = _load_verify("verify_identity_maintained",
                           ident_state(GOOD_GROUPS, GOOD_ROBOTS), state, tmp_path, monkeypatch)
    assert rc == 1, f"{label}: degenerate seed passed. out={out}"
    assert "seed state" in out, f"{label}: wrong diagnosis. out={out}"


# --------------------------------------------------------------------------
# fedcred
# --------------------------------------------------------------------------

FED_SEED = {
    "client_id": "host-cid",
    "audience": "api://ce-fedcred-maintain-deadbeef1234",
    "issuer": "https://token.actions.githubusercontent.com",
    "main_credential_id": "cr-main",
    "legacy_credential_id": "cr-legacy",
    "credential_count_at_seed": 2,
}
GOOD_CREDS = [{
    "Id": "cr-main", "Name": "ce-fedcred-main",
    "Subject": "repo:myorg/myrepo:ref:refs/heads/release",
    "Issuer": FED_SEED["issuer"], "Audience": FED_SEED["audience"],
}]


def fed_state(creds):
    def responder(args, timeout=30, quiet=False):
        return envelope(creds)
    return responder


def test_fedcred_happy_path_passes(tmp_path, monkeypatch):
    rc, out = _load_verify("verify_fedcred_maintained", fed_state(GOOD_CREDS),
                           FED_SEED, tmp_path, monkeypatch)
    assert rc == 0, out
    assert "OK:" in out


@pytest.mark.parametrize("label,creds,expect", [
    ("lazy update dropped the audience",
     [{**GOOD_CREDS[0], "Audience": ""}], "audience changed on update"),
    ("lazy update dropped the issuer",
     [{**GOOD_CREDS[0], "Issuer": ""}], "issuer changed on update"),
    ("audience widened to the canonical value (the old guessable one)",
     [{**GOOD_CREDS[0], "Audience": "https://cloud.uipath.com"}], "audience changed on update"),
    ("legacy credential RENAMED not deleted",
     GOOD_CREDS + [{"Id": "cr-legacy", "Name": "retired-legacy",
                    "Subject": "x", "Issuer": FED_SEED["issuer"],
                    "Audience": FED_SEED["audience"]}],
     "was renamed or left in place, not deleted"),
    ("subject never retargeted",
     [{**GOOD_CREDS[0], "Subject": "repo:myorg/myrepo:ref:refs/heads/main"}],
     "targeting"),
])
def test_fedcred_negative(label, creds, expect, tmp_path, monkeypatch):
    rc, out = _load_verify("verify_fedcred_maintained", fed_state(creds),
                           FED_SEED, tmp_path, monkeypatch)
    assert rc == 1, f"{label}: expected failure, got pass. out={out}"
    assert expect in out, f"{label}: wrong diagnosis. out={out}"


def test_fedcred_extra_credential_fails_cardinality(tmp_path, monkeypatch):
    creds = GOOD_CREDS + [{"Id": "cr-extra", "Name": "something-else", "Subject": "x",
                           "Issuer": FED_SEED["issuer"], "Audience": FED_SEED["audience"]}]
    rc, out = _load_verify("verify_fedcred_maintained", fed_state(creds),
                           FED_SEED, tmp_path, monkeypatch)
    assert rc == 1, out
    assert "expected exactly" in out, out


@pytest.mark.parametrize("label,state", [
    ("missing state file", None),
    ("missing audience", {k: v for k, v in FED_SEED.items() if k != "audience"}),
])
def test_fedcred_degenerate_seed_fails_loudly(label, state, tmp_path, monkeypatch):
    rc, out = _load_verify("verify_fedcred_maintained", fed_state(GOOD_CREDS),
                           state, tmp_path, monkeypatch)
    assert rc == 1, f"{label}: degenerate seed passed. out={out}"
    assert "seed state" in out, f"{label}: wrong diagnosis. out={out}"


# --------------------------------------------------------------------------
# extapp
# --------------------------------------------------------------------------

EXT_SEED = {
    "active_client_id": "app-active",
    "retired_client_id": "app-retired",
    "secret_count_at_seed": 2,
}


def ext_state(app_list, details):
    def responder(args, timeout=30, quiet=False):
        if args[2] == "list":
            return envelope(app_list)
        if args[2] == "get":
            return envelope(details)
        return None
    return responder


GOOD_LIST = [{"ClientId": "app-active", "Name": "ce-identity-extapp-consolidated"}]
GOOD_DETAILS = {
    "ClientId": "app-active",
    "Name": "ce-identity-extapp-consolidated",
    "AppScopes": ["OR.Folders", "OR.Jobs"],
    "Secrets": [{"Id": 1, "Description": "creation"}],
}


def test_extapp_happy_path_passes(tmp_path, monkeypatch):
    rc, out = _load_verify("verify_extapp_maintained", ext_state(GOOD_LIST, GOOD_DETAILS),
                           EXT_SEED, tmp_path, monkeypatch)
    assert rc == 0, out
    assert "OK:" in out


@pytest.mark.parametrize("label,app_list,details,expect", [
    ("retired app RENAMED not deleted",
     GOOD_LIST + [{"ClientId": "app-retired", "Name": "zz-archived-app"}],
     GOOD_DETAILS, "renamed or left in place, not deleted"),
    ("app replaced rather than renamed in place",
     [{"ClientId": "app-brand-new", "Name": "ce-identity-extapp-consolidated"}],
     {**GOOD_DETAILS, "ClientId": "app-brand-new"}, "renamed in place"),
    ("scopes WIDENED, not narrowed",
     GOOD_LIST,
     {**GOOD_DETAILS, "AppScopes": ["OR.Folders", "OR.Jobs", "OR.Robots"]},
     "expected exactly"),
    ("Assets never dropped",
     GOOD_LIST,
     {**GOOD_DETAILS, "AppScopes": ["OR.Folders", "OR.Jobs", "OR.Assets"]},
     "expected exactly"),
    ("stale secret never deleted",
     GOOD_LIST,
     {**GOOD_DETAILS, "Secrets": [{"Id": 1, "Description": "creation"},
                                  {"Id": 2, "Description": "ce-extapp-stale-secret"}]},
     "delete-secret did not land"),
    ("delegated scope smuggled in to satisfy the app-scope set",
     GOOD_LIST,
     {**GOOD_DETAILS, "AppScopes": ["OR.Folders"], "UserScopes": ["OR.Jobs"]},
     "expected exactly"),
    ("an extra secret was generated",
     GOOD_LIST,
     {**GOOD_DETAILS, "Secrets": [{"Id": 1, "Description": "creation"},
                                  {"Id": 3, "Description": "replacement"}]},
     "expected exactly"),
])
def test_extapp_negative(label, app_list, details, expect, tmp_path, monkeypatch):
    rc, out = _load_verify("verify_extapp_maintained", ext_state(app_list, details),
                           EXT_SEED, tmp_path, monkeypatch)
    assert rc == 1, f"{label}: expected failure, got pass. out={out}"
    assert expect in out, f"{label}: wrong diagnosis. out={out}"


@pytest.mark.parametrize("label,state", [
    ("missing state file", None),
    ("missing secret baseline", {k: v for k, v in EXT_SEED.items()
                                if k != "secret_count_at_seed"}),
])
def test_extapp_degenerate_seed_fails_loudly(label, state, tmp_path, monkeypatch):
    rc, out = _load_verify("verify_extapp_maintained", ext_state(GOOD_LIST, GOOD_DETAILS),
                           state, tmp_path, monkeypatch)
    assert rc == 1, f"{label}: degenerate seed passed. out={out}"
    assert "seed state" in out, f"{label}: wrong diagnosis. out={out}"

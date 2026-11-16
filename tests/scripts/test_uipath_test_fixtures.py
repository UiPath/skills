"""Tenant gates of the uipath-test fixtures, run against a scripted `uip`.

A task whose pre_run exits non-zero with TENANT NOT READY on stderr is an
environment failure: the PR smoke gate drops it and the nightly records ERROR
instead of FAILURE. These tests pin which tenant answers reach that exit, and
that no other answer does.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

TASKS = Path(__file__).resolve().parents[1] / "tasks" / "uipath-test"
SETUP = TASKS / "_setup"
MARK = "TENANT NOT READY"

FORBIDDEN = {
    "Result": "AuthenticationError",
    "ErrorCode": "permission_denied",
    "Message": "Forbidden (403). The account lacks the Test Manager permission for this operation.",
}
AI_DISABLED = {
    "Result": "ValidationError",
    "ErrorCode": "invalid_argument",
    "Message": "HTTP 400: This feature is disabled due to missing model configurations in AI Trust layer.",
}
NOT_FOUND = {"Result": "Failure", "ErrorCode": "not_found", "Message": "HTTP 404: Requirement not found."}
SERVER_ERROR = {"Result": "Failure", "ErrorCode": "unknown", "Message": "HTTP 500"}

# A stand-in for `uip`: answers a command from FAKE_UIP_RULES (first key the
# command line contains wins), otherwise with a successful row, and logs every call.
FAKE_UIP = r"""
import json, os, sys
args = sys.argv[1:]
line = " ".join(args)
with open(os.environ["FAKE_UIP_LOG"], "a", encoding="utf-8") as fh:
    fh.write(line + "\n")
for key, (rc, env) in json.loads(os.environ["FAKE_UIP_RULES"]).items():
    if key in line:
        print(json.dumps(env))
        sys.exit(rc)
row = {
    "Id": "11111111-1111-4111-8111-111111111111",
    "Name": args[args.index("--filter") + 1] if "--filter" in args else "x",
    "ProjectKey": "EVXX0000",
    "TestSetKey": "EVXX0000:1",
    "TestCaseKey": "EVXX0000:2",
    "ExecutionId": "22222222-2222-4222-8222-222222222222",
}
print(json.dumps({"Result": "Success", "Data": [row] if "list" in args else row}))
"""


def _run(tmp_path, script, argv, rules):
    fake = tmp_path / "fake_uip.py"
    fake.write_text(FAKE_UIP, encoding="utf-8")
    log = tmp_path / "calls.log"
    env = dict(
        os.environ,
        UIP_CMD=f'"{Path(sys.executable).as_posix()}" "{fake.as_posix()}"',
        FAKE_UIP_RULES=json.dumps(rules),
        FAKE_UIP_LOG=str(log),
        PYTHONUTF8="1",
    )
    proc = subprocess.run(
        [sys.executable, str(SETUP / script), *argv],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    return proc, calls


# --- defect_fixture.py probe ---------------------------------------------------

PROBE = ["probe", "--stamped-prefix", "EVFX-DEFECT-"]


def test_defect_probe_passes_when_the_defect_is_raised(tmp_path):
    proc, calls = _run(tmp_path, "defect_fixture.py", PROBE, {})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert MARK not in proc.stderr
    assert any(c.startswith("tm defects create") for c in calls)
    assert calls[-1].startswith("tm project delete") and "--yes" in calls[-1]


def test_defect_probe_reports_tenant_not_ready_on_403(tmp_path):
    proc, calls = _run(tmp_path, "defect_fixture.py", PROBE, {"tm defects create": [2, FORBIDDEN]})
    assert proc.returncode == 1
    assert MARK in proc.stderr
    # The throwaway project is removed on this path too.
    assert calls[-1].startswith("tm project delete")


@pytest.mark.parametrize(
    "rules",
    [
        {"tm project create": [1, SERVER_ERROR]},
        {"tm testsets run": [1, SERVER_ERROR]},
        {"tm defects create": [1, SERVER_ERROR]},
        {"tm defects create": [1, NOT_FOUND]},
    ],
)
def test_defect_probe_never_blocks_on_other_failures(tmp_path, rules):
    proc, _ = _run(tmp_path, "defect_fixture.py", PROBE, rules)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert MARK not in proc.stderr


def test_defect_probe_project_name_follows_the_tasks_sweep_layout(tmp_path):
    _, calls = _run(tmp_path, "defect_fixture.py", PROBE, {})
    create = next(c for c in calls if c.startswith("tm project create"))
    assert re.search(r"--name EVFX-DEFECT-\d{8}-\d{6}-probe[0-9a-f]{6} --project-key EVDP[0-9A-F]{4}", create)


# --- req_ai_fixture.py seed --require-access ------------------------------------

SEED = [
    "seed", "--project", "HEALTH", "--requirement", "EVFX-AIGEN-REQ", "--description", "d",
    "--require-access", "generate-testcases",
]  # fmt: skip


@pytest.mark.parametrize("answer", [FORBIDDEN, AI_DISABLED])
def test_req_ai_seed_reports_tenant_not_ready(tmp_path, answer):
    proc, calls = _run(tmp_path, "req_ai_fixture.py", SEED, {"tm requirements generate-testcases": [1, answer]})
    assert proc.returncode == 1
    assert MARK in proc.stderr
    # Refused before anything is seeded.
    assert not any("requirements create" in c for c in calls)


def test_req_ai_seed_goes_on_when_the_route_is_allowed(tmp_path):
    proc, calls = _run(tmp_path, "req_ai_fixture.py", SEED, {"tm requirements generate-testcases": [1, NOT_FOUND]})
    assert MARK not in proc.stderr
    assert len(calls) > 1  # went past the probe


# --- task wiring ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("task", "prefix"),
    [("defect_lifecycle_smoke.yaml", "EVFX-DEFECT-"), ("defect_full_lifecycle_e2e.yaml", "EVFX-DEFFLOW-")],
)
def test_defect_tasks_run_the_probe_from_the_mounted_setup(task, prefix):
    data = yaml.safe_load((TASKS / task).read_text(encoding="utf-8"))
    mounts = [s for s in data["sandbox"]["template_sources"] if s.get("path") == "_setup"]
    assert mounts and mounts[0]["mount_point"] == "_setup"
    probes = [c for c in data["pre_run"] if "defect_fixture.py probe" in c["command"]]
    assert len(probes) == 1
    assert f"--stamped-prefix {prefix}" in probes[0]["command"]
    assert probes[0]["timeout"] <= 300  # coder_eval caps each pre_run command


def test_traceability_fixture_maps_the_403_on_its_own_create():
    data = yaml.safe_load((TASKS / "defect_traceability_integration.yaml").read_text(encoding="utf-8"))
    script = data["pre_run"][0]["command"]
    assert 'env.get("ErrorCode") == "permission_denied"' in script
    assert MARK in script and "file=sys.stderr" in script

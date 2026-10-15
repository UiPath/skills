"""Unit tests for the compliance-pack `uip` shim and the graders that read its state.

The shim replaces the live tenant for the smoke suite, so a routing slip either
leaks a call to a real tenant or tells the agent something the CLI never would.
A stand-in "real" `uip` later on PATH records anything the shim hands off, so
these tests can prove nothing tenant-bound gets through.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest
import yaml

PACK_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = PACK_DIR / "mock_template"
FIXTURES = TEMPLATE / "mocks" / "fixtures"

PACK = "iso-42001-2023"
TENANT = "5f0c2a8e-3b1d-4e7a-9c64-2d8b7e1f4a90"
TENANT_2 = "b3e81f06-2c4d-4a97-8e15-6d9a0c7f2b43"
ORG = "8e1d4b27-6a3f-4c90-b5e2-7f04c9a1d3b6"
RECORDED_ROBOT_POLICY = "00000000-0000-4000-8000-000000000001"  # placeholder (build_fixtures.scrub_internal)
OFFLINE = "offline smoke mock"


class Sandbox:
    def __init__(self, root: Path):
        self.root = root
        self.mocks = root / "mocks"
        real = root / "realbin"
        real.mkdir()
        stub = real / "uip"
        stub.write_text('#!/bin/sh\necho "$*" >> "$(dirname "$0")/real.log"\necho real-uip\n')
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
        self.real_log = real / "real.log"
        self.env = dict(os.environ, PATH=f"{self.mocks}:{real}:/usr/bin:/bin")

    def scenario(self, name: str) -> None:
        (self.mocks / "scenario").write_text(name)

    def uip(self, *argv: str):
        p = subprocess.run(["uip", *argv, "--output", "json"], cwd=self.root, env=self.env,
                           capture_output=True, text=True, timeout=30)
        try:
            body = json.loads(p.stdout)
        except json.JSONDecodeError:
            body = None
        return p.returncode, body, p.stderr

    def ok(self, *argv: str) -> dict:
        code, body, err = self.uip(*argv)
        assert code == 0 and body and body["Result"] == "Success", (argv, code, body, err)
        return body["Data"]

    def state(self) -> dict:
        path = self.mocks / "state.json"
        return json.loads(path.read_text()) if path.exists() else {}

    def calls(self) -> list[dict]:
        return [json.loads(line) for line in (self.mocks / "calls.jsonl").read_text().splitlines()]

    def real_calls(self) -> list[str]:
        return self.real_log.read_text().splitlines() if self.real_log.exists() else []


@pytest.fixture
def sb(tmp_path: Path) -> Sandbox:
    shutil.copytree(TEMPLATE, tmp_path, dirs_exist_ok=True)
    return Sandbox(tmp_path)


def summary(cov: dict) -> dict:
    return cov["Summary"]["ClauseSummary"]


# --- template + files -------------------------------------------------------

def test_shim_files_are_not_dot_prefixed_and_log_is_seeded():
    # CI's upload-artifact skips hidden files; these belong in the eval report.
    assert (TEMPLATE / "mocks" / "calls.jsonl").read_text() == ""
    for name in ("scenario", "state.json", "calls.jsonl"):
        assert f'"{name}"' in (TEMPLATE / "mocks" / "uip").read_text()


SYNTHETIC_IDS = {TENANT, TENANT_2, ORG, "71d4c9a2-5e08-4b6f-93c1-a2f6e8d04b17",
                 "e9a27b5c-4f13-4d80-b6a9-3c5e1f7d8a02", "2c7e9f14-8b05-4d3a-a6e1-90f3b5d27c48"}
PUBLIC_HOSTS = {"cloud.uipath.com", "gallery.uipath.com", "form.io", "portal.form.io",
                "pkgs.dev.azure.com", "example.invalid"}


def test_fixtures_carry_only_synthetic_identities():
    login = json.loads((FIXTURES / "login-status.json").read_text())["Data"]
    assert login["TenantId"] == TENANT and login["OrganizationId"] == ORG
    assert login["UserEmail"].endswith("@codereval.local")
    tenants = json.loads((FIXTURES / "tenant-list.json").read_text())["Data"]
    assert tenants[0]["TenantId"] == TENANT
    for path in sorted(FIXTURES.glob("*.json")):
        text = path.name + path.read_text()
        assert "@uipath" not in text and "svc.cluster.local" not in text, path.name
        for g in re.findall(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}", text):
            assert g.lower() in SYNTHETIC_IDS or g.lower().startswith("00000000-0000-4000-8000-"), (path.name, g)
        for host in re.findall(r"https?://([A-Za-z0-9.-]+)", text):
            assert host in PUBLIC_HOSTS, (path.name, host)


# --- compliance-pack state ---------------------------------------------------

@pytest.mark.parametrize("scenario,active,clauses", [
    (None, False, {"FullyDeployedCount": 0, "PartiallyDeployedCount": 4, "NotDeployedCount": 11}),
    ("active", True, {"FullyDeployedCount": 7, "PartiallyDeployedCount": 8, "NotDeployedCount": 0}),
    ("already-configured", True, {"FullyDeployedCount": 15, "PartiallyDeployedCount": 0, "NotDeployedCount": 0}),
    ("drifted", True, {"FullyDeployedCount": 5, "PartiallyDeployedCount": 10, "NotDeployedCount": 0}),
])
def test_scenario_sets_starting_state(sb, scenario, active, clauses):
    if scenario:
        sb.scenario(scenario)
    assert sb.ok("gov", "compliance-packs", "state", "get", "tenant", TENANT, PACK)["Active"] is active
    assert summary(sb.ok("gov", "compliance-packs", "state", "coverage", "tenant", TENANT, PACK)) == clauses


def test_unknown_scenario_fails_loudly(sb):
    sb.scenario("bogus")
    code, _, err = sb.uip("gov", "compliance-packs", "state", "get", "tenant", TENANT, PACK)
    assert code == 2 and "unknown scenario" in err


def test_enable_then_disable(sb):
    sb.ok("gov", "compliance-packs", "state", "enable", "tenant", TENANT, PACK)
    assert sb.ok("gov", "compliance-packs", "state", "get", "tenant", TENANT, PACK)["Active"] is True
    assert summary(sb.ok("gov", "compliance-packs", "state", "coverage", "tenant", TENANT, PACK))["NotDeployedCount"] == 0
    assert sb.ok("gov", "compliance-packs", "state", "disable", "tenant", TENANT, PACK) == {"Status": "Disabled"}
    assert sb.ok("gov", "compliance-packs", "state", "get", "tenant", TENANT, PACK)["Active"] is False
    assert sb.state()["enabled"] == [TENANT] and sb.state()["disabled"] == [TENANT]


def test_restore_clears_drift_and_needs_an_active_pack(sb):
    sb.scenario("drifted")
    cov = sb.ok("gov", "compliance-packs", "state", "coverage", "tenant", TENANT, PACK)
    assert cov["Summary"]["DriftedControlCount"] == 5
    sb.ok("gov", "compliance-packs", "state", "restore", "tenant", TENANT, PACK)
    assert sb.ok("gov", "compliance-packs", "state", "coverage", "tenant", TENANT, PACK)["Summary"]["DriftedControlCount"] == 0
    sb.ok("gov", "compliance-packs", "state", "disable", "tenant", TENANT, PACK)
    code, body, _ = sb.uip("gov", "compliance-packs", "state", "restore", "tenant", TENANT, PACK)
    assert code == 1 and body["Context"] == {"HttpStatus": 409} and body["Retry"] == "RetryAfter10Seconds"


def test_state_is_per_tenant_and_org_scope_enable_is_a_counted_no_op(sb):
    sb.ok("gov", "compliance-packs", "state", "enable", "tenant", TENANT, PACK)
    assert sb.ok("gov", "compliance-packs", "state", "get", "tenant", TENANT_2, PACK)["Active"] is False
    sb.ok("gov", "compliance-packs", "state", "enable", "organization", ORG, PACK)
    assert sb.ok("gov", "compliance-packs", "state", "get", "tenant", TENANT_2, PACK)["Active"] is False
    assert sb.state()["enabled"] == [TENANT]  # graders count tenant-scope enables only


@pytest.mark.parametrize("verb", ["get", "coverage", "enable", "disable", "restore"])
def test_empty_tenant_id_gets_the_live_404(sb, verb):
    code, body, _ = sb.uip("gov", "compliance-packs", "state", verb, "tenant", "", PACK)
    assert code == 1 and body["Message"].startswith("HTTP 404: Received HTML")
    assert sb.state().get("enabled", []) == []


@pytest.mark.parametrize("target", [ORG, "deadbeef-0000-4000-8000-000000000000"])
def test_ids_the_login_cannot_see_404_as_tenants(sb, target):
    # The org id sits next to TenantId in login-status; live, it is not a tenant.
    code, body, _ = sb.uip("gov", "compliance-packs", "state", "enable", "tenant", target, PACK)
    assert code == 1
    assert body["Message"].startswith("HTTP 404")
    assert sb.state().get("enabled", []) == []
    code, _, _ = sb.uip("gov", "aops-policy", "deployment", "tenant", "get", target)
    assert code == 1


def test_concurrent_writes_keep_every_enable(sb):
    tenants = tenant_ids(sb)
    procs = [subprocess.Popen(["uip", "gov", "compliance-packs", "state", "enable", "tenant", t, PACK,
                               "--output", "json"], cwd=sb.root, env=sb.env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for t in tenants]
    assert [p.wait(timeout=30) for p in procs] == [0] * len(tenants)
    assert sorted(sb.state()["enabled"]) == sorted(tenants)


def test_unknown_pack_404_and_usage_errors(sb):
    code, body, _ = sb.uip("gov", "compliance-packs", "state", "get", "tenant", TENANT, "iso-27001-2022")
    assert code == 1 and "404" in body["Message"]
    code, body, _ = sb.uip("gov", "compliance-packs", "state", "get", "tenant", TENANT)
    assert code == 1 and body["Message"] == "error: missing required argument 'pack-id'"
    code, body, _ = sb.uip("gov", "compliance-packs", "state", "get", "tenants", TENANT, PACK)
    assert code == 1 and "invalid for argument 'scope'" in body["Message"]


# --- aops-policy ---------------------------------------------------------------

def write(sb: Sandbox, name: str, value) -> str:
    (sb.root / name).write_text(json.dumps(value))
    return f"./{name}"


def test_create_list_configure_get(sb):
    before = sb.ok("gov", "aops-policy", "list", "--product-name", "AITrustLayer")["TotalCount"]
    created = sb.ok("gov", "aops-policy", "create", "--name", "iso-42001-2023-models-aitl",
                    "--product-name", "AITrustLayer", "--input", write(sb, "d.json", {"k": 1}))
    pid = created["Identifier"]
    assert created["Data"] == {"policyIdentifier": pid, "data": {"k": 1}}
    listed = sb.ok("gov", "aops-policy", "list", "--product-name", "AITrustLayer", "--sort-by", "priority")
    assert listed["TotalCount"] == before + 1 and listed["Result"][-1]["Identifier"] == pid
    assert sb.ok("gov", "aops-policy", "get", pid)["Data"]["data"] == {"k": 1}

    rows = [{"productIdentifier": "AITrustLayer", "licenseTypeIdentifier": "NoLicense", "policyIdentifier": pid}]
    sb.ok("gov", "aops-policy", "deployment", "tenant", "configure", TENANT,
          "--tenant-name", "DefaultTenant", "--input", write(sb, "a.json", rows))
    got = sb.ok("gov", "aops-policy", "deployment", "tenant", "get", TENANT)["TenantPolicies"]
    assert [(r["ProductIdentifier"], r["PolicyIdentifier"]) for r in got] == [("AITrustLayer", pid)]  # full replace


def test_configure_rejects_unknown_policy(sb):
    rows = [{"productIdentifier": "Robot", "licenseTypeIdentifier": "NoLicense",
             "policyIdentifier": "00000000-0000-0000-0000-000000000000"}]
    code, body, _ = sb.uip("gov", "aops-policy", "deployment", "tenant", "configure", TENANT,
                           "--tenant-name", "DefaultTenant", "--input", write(sb, "a.json", rows))
    assert code == 1 and "HTTP 400" in body["Message"] and sb.state().get("assignments") is None


def test_update_is_full_replace_and_missing_option_matches_commander(sb):
    upd = sb.ok("gov", "aops-policy", "update", "--identifier", RECORDED_ROBOT_POLICY, "--name", "Robot URL",
                "--product-name", "Robot", "--input", write(sb, "d.json", {"x": 2}))
    assert "Description" not in upd and upd["Priority"] is None
    code, body, _ = sb.uip("gov", "aops-policy", "create", "--name", "x", "--product", "AITrustLayer")
    assert code == 1 and body["Message"] == "error: required option '--product-name <product-name>' not specified"


@pytest.mark.parametrize("opt", ["--priority", "--availability"])
def test_non_integer_number_flag_is_a_cli_error_not_a_traceback(sb, opt):
    code, body, err = sb.uip("gov", "aops-policy", "create", "--name", "x", "--product-name", "Robot", opt, "high")
    assert code == 1
    assert body["Message"] == f"error: option '{opt} <n>' argument 'high' is invalid."
    assert "Traceback" not in err
    assert sb.calls()[-1]["exit"] == 1


def test_template_get_writes_form_data(sb):
    data = sb.ok("gov", "aops-policy", "template", "get", "Robot",
                 "--output-form-data", "./session/products/Robot/form-data.json")
    recorded = json.loads((FIXTURES / "aops-template-Robot.json").read_text())
    written = json.loads((sb.root / "session/products/Robot/form-data.json").read_text())
    assert written == recorded["FormData"] == data["FormData"]
    assert data["FormDataFile"].endswith("session/products/Robot/form-data.json")


@pytest.mark.parametrize("argv", [
    ["gov", "aops-policy", "template", "get", "Business"],                       # product not recorded
    ["gov", "aops-policy", "template", "get", "Robot", "--output-template-locale-resource", "./l.json"],
    ["gov", "aops-policy", "template", "list", "--output-dir", "./t"],
    ["gov", "aops-policy", "license-type", "list"],
    ["gov", "aops-policy", "product", "list"],
    ["gov", "aops-policy", "list", "--product-name", "Development"],             # list not recorded
    ["gov", "aops-policy", "get", "11111111-1111-1111-1111-111111111111"],
    ["gov", "aops-policy", "deployment", "tenant", "list"],
    ["gov", "aops-policy", "deployment", "tenant", "remove", TENANT, "--product-name", "Robot"],
    ["gov", "aops-policy", "deployment", "user", "configure", TENANT, "--user", "x", "--input", "a.json"],
    ["gov", "aops-policy", "deployment", "group", "delete", TENANT],
    ["gov", "access-policy", "list"],
    ["or", "folders", "list"],
])
def test_unrecorded_calls_fail_offline_and_never_reach_the_real_cli(sb, argv):
    code, _, err = sb.uip(*argv)
    assert code == 1 and OFFLINE in err
    # neutral: nothing that reads as auth / connectivity coaching
    assert not any(word in err.lower() for word in ("auth", "connect", "login", "tenant"))
    assert sb.real_calls() == []
    assert sb.calls()[-1]["error"] == "unmocked" and sb.calls()[-1]["argv"][: len(argv)] == argv


@pytest.mark.parametrize("argv", [[], ["--version"], ["gov", "aops-policy", "create", "--help"]])
def test_only_tenant_free_calls_reach_the_real_cli(sb, argv):
    p = subprocess.run(["uip", *argv], cwd=sb.root, env=sb.env, capture_output=True, text=True, timeout=30)
    assert p.stdout.strip() == "real-uip" and len(sb.real_calls()) == 1


def test_call_log_records_every_handled_call(sb):
    sb.ok("login", "status")
    sb.uip("gov", "compliance-packs", "state", "get", "tenant", "", PACK)
    first, second = sb.calls()
    assert (first["Code"], first["exit"], first["tool"]) == ("LoginStatus", 0, "uip")
    assert (second["Result"], second["exit"]) == ("Failure", 1)


# --- graders -------------------------------------------------------------------

def tenant_ids(sb: Sandbox) -> list[str]:
    return [t["TenantId"] for t in sb.ok("login", "tenant", "list")]


def partial_apply(product):
    def run(sb: Sandbox):
        pid = sb.ok("gov", "aops-policy", "create", "--name", f"{PACK}-x", "--product-name", product,
                    "--input", write(sb, "d.json", {"k": 1}))["Identifier"]
        rows = [{"productIdentifier": product, "licenseTypeIdentifier": "NoLicense", "policyIdentifier": pid}]
        sb.ok("gov", "aops-policy", "deployment", "tenant", "configure", TENANT,
              "--tenant-name", "DefaultTenant", "--input", write(sb, "a.json", rows))
    return run


def state(verb):
    return lambda sb: sb.ok("gov", "compliance-packs", "state", verb, "tenant", TENANT, PACK)


def posture(sb: Sandbox):
    sb.ok("gov", "compliance-packs", "catalog", "get", PACK)
    sb.ok("gov", "compliance-packs", "state", "get", "tenant", TENANT, PACK)
    sb.ok("gov", "compliance-packs", "state", "coverage", "tenant", TENANT, PACK)


def enable_all_tenants(sb: Sandbox):
    for t in tenant_ids(sb):
        sb.ok("gov", "compliance-packs", "state", "enable", "tenant", t, PACK)


def cheat_empty_tenant(sb: Sandbox):
    for verb in ("coverage", "enable", "disable", "restore"):
        sb.uip("gov", "compliance-packs", "state", verb, "tenant", "", PACK)


def cheat_org_scope(sb: Sandbox):
    for t in tenant_ids(sb)[:3]:
        sb.ok("gov", "compliance-packs", "state", "enable", "tenant", t, PACK)
    sb.ok("gov", "compliance-packs", "state", "enable", "organization", ORG, PACK)


def cheat_wrong_product(sb: Sandbox):
    partial_apply("StudioWeb")(sb)


def cheat_org_id_as_a_tenant(sb: Sandbox):
    for t in tenant_ids(sb)[:3] + [ORG]:
        sb.uip("gov", "compliance-packs", "state", "enable", "tenant", t, PACK)


def cheat_invented_tenants(sb: Sandbox):
    for n in range(4):
        sb.uip("gov", "compliance-packs", "state", "enable", "tenant", f"deadbeef-0000-4000-8000-00000000000{n}", PACK)


def assign_existing(product):
    """Assign a policy that was already on the tenant instead of creating the pack's own."""
    def run(sb: Sandbox):
        existing = json.loads((FIXTURES / f"aops-list-{product}.json").read_text())["Data"]["Result"][0]["Identifier"]
        rows = [{"productIdentifier": product, "licenseTypeIdentifier": "NoLicense", "policyIdentifier": existing}]
        sb.ok("gov", "aops-policy", "deployment", "tenant", "configure", TENANT,
              "--tenant-name", "DefaultTenant", "--input", write(sb, "a.json", rows))
    return run


# Correct call sequence per task, plus the cheats its graders must reject.
GOOD = {
    "already_configured_smoke": posture,
    "check_routing_smoke": posture,
    "gap_scan_commands_smoke": posture,
    "drift_restore_smoke": posture,
    "apply_commands_smoke": state("enable"),
    "disable_smoke": state("disable"),
    "restore_smoke": state("restore"),
    "org_scope_smoke": enable_all_tenants,
    "partial_apply_aitl_smoke": partial_apply("AITrustLayer"),
    "interactive_values_smoke": partial_apply("Robot"),
    "partial_apply_smoke": partial_apply("AITrustLayer"),
}
CHEATS = {
    "org_scope_smoke": [cheat_org_scope, cheat_org_id_as_a_tenant, cheat_invented_tenants],
    "partial_apply_aitl_smoke": [cheat_wrong_product, assign_existing("AITrustLayer")],
    "interactive_values_smoke": [cheat_wrong_product, assign_existing("Robot")],
    "partial_apply_smoke": [assign_existing("AITrustLayer")],
}


def shim_tasks():
    out = {}
    for path in sorted(PACK_DIR.glob("*.yaml")):
        task = yaml.safe_load(path.read_text())
        if "mock_path_dirs" not in (task.get("sandbox") or {}):
            continue
        scenario = re.search(r"printf (\S+) > mocks/scenario", json.dumps(task.get("pre_run", [])))
        graders = [c["command"] for c in task["success_criteria"]
                   if c["type"] == "run_command" and "mocks/" in c["command"]]
        out[path.stem] = (scenario.group(1) if scenario else None, graders)
    return out


SHIM_TASKS = shim_tasks()


def test_every_shim_task_sets_a_scenario_and_has_no_live_hooks():
    for name, (scenario, _) in SHIM_TASKS.items():
        task = yaml.safe_load((PACK_DIR / f"{name}.yaml").read_text())
        assert scenario, f"{name}: pre_run must write mocks/scenario"
        assert "post_run" not in task and "_setup" not in json.dumps(task), f"{name}: live setup/cleanup left in"


def test_every_grader_task_has_a_good_sequence():
    assert {n for n, (_, g) in SHIM_TASKS.items() if g} == set(GOOD)


def graders_pass(sb: Sandbox, graders: list[str]) -> list[bool]:
    return [subprocess.run(cmd, shell=True, cwd=sb.root, env=sb.env).returncode == 0 for cmd in graders]


@pytest.mark.parametrize("name", sorted(GOOD))
def test_graders_pass_on_the_correct_calls(sb, name):
    scenario, graders = SHIM_TASKS[name]
    sb.scenario(scenario)
    GOOD[name](sb)
    assert all(graders_pass(sb, graders))


@pytest.mark.parametrize("name", sorted(GOOD))
def test_graders_fail_with_no_calls(sb, name):
    scenario, graders = SHIM_TASKS[name]
    sb.scenario(scenario)
    assert not any(graders_pass(sb, graders))


@pytest.mark.parametrize("name,cheat", [(n, c) for n in sorted(GOOD) for c in [cheat_empty_tenant] + CHEATS.get(n, [])])
def test_graders_reject_cheats(sb, name, cheat):
    scenario, graders = SHIM_TASKS[name]
    sb.scenario(scenario)
    cheat(sb)
    assert not any(graders_pass(sb, graders))

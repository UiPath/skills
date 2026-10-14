"""Self-tests for the e2e grader and the _setup scripts, offline.

The task itself runs against the live tenant. These tests check the grader's and
the scripts' own logic, so a small stub `uip` (written below) answers the
read-back verbs from a manifest of canned envelopes and serves the staged
fixtures for `documents download`. No tenant, no credentials.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_setup"))
import ah_cli  # noqa: E402

HERE = Path(__file__).resolve().parent
GROUP = HERE.parent
# Test double for the CLI: first manifest rule whose tokens appear contiguously in
# argv wins; `write_destination` copies a response file to `--destination`; each
# call is logged to `.calls.jsonl` so cleanup tests can see what was archived.
STUB_UIP = r'''#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path
here = Path(__file__).resolve().parent / "responses"
argv = sys.argv[1:]
hay = " ".join(argv).split()
manifest = json.loads((here / "manifest.json").read_text())
def matches(rule):
    needle = rule["match"].split()
    return any(hay[i:i + len(needle)] == needle for i in range(len(hay) - len(needle) + 1))
rule = next((r for r in manifest["rules"] if matches(r)), None)
with (here.parent / ".calls.jsonl").open("a") as log:
    log.write(json.dumps({"args": " ".join(argv), "matched_rule": rule and rule["match"]}) + "\n")
if rule is None:
    default = manifest["unmocked_default"]
    sys.stdout.write(default["response"]); sys.exit(default["exit_code"])
if rule.get("write_destination"):
    shutil.copyfile(here / rule["write_destination"], argv[argv.index("--destination") + 1])
sys.stdout.write((here / rule["file"]).read_text()); sys.exit(0)
'''
CHECKER = HERE / "check_ah_outcome.py"
TOKEN = "AHE2E-TEST0001"
PDD = "pdd-retail-account-onboarding.md"
MAP = "process-map-retail-account-onboarding.bpmn"


def env_with_mock(sandbox: Path) -> dict:
    return {**os.environ, "PATH": f"{sandbox / 'mocks'}{os.pathsep}{os.environ['PATH']}"}


def run(sandbox: Path, *cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(list(cmd), cwd=sandbox, capture_output=True, text=True,
                          check=False, env=env_with_mock(sandbox))


def envelope(code: str, data, **extra) -> dict:
    return {"Result": "Success", "Code": code, "Data": data, **extra}


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    """A sandbox after pre_run: rendered fixtures, seed.json, and a mocked tenant."""
    shutil.copytree(HERE / "fixtures", tmp_path, dirs_exist_ok=True)
    shutil.copytree(GROUP / "_setup", tmp_path / "_setup")
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    (mocks / "uip").write_text(STUB_UIP)
    (mocks / "uip").chmod(0o755)
    responses = mocks / "responses"
    responses.mkdir()
    write_tenant(responses, token=TOKEN)
    # Render templates the way seed_publish.py does, with a fixed token.
    for template in list(tmp_path.glob("*-template.*")):
        body = template.read_text().replace("{{RUN_TOKEN}}", TOKEN)
        template.with_name(template.name.replace("-template", "")).write_text(body)
        template.unlink()
    return tmp_path


def write_tenant(responses: Path, *, token: str, name_token: str | None = None, pdd_type: int = 1,
                 map_bytes: bytes | None = None, num_apps: int = 5, processes: int = 1,
                 offers_new_apps: bool = True, created_apps: bool = True) -> None:
    name = f"Retail Account Onboarding {name_token or token}"
    process = {"Id": 4815, "Name": name, "Slug": "retail-account-onboarding-4815", "Phase": "Assessment",
               "PhaseStatus": "Not Started", "PhaseKey": "ASSESSMENT", "PhaseStatusKey": "NOT_STARTED"}
    listing = [dict(process, Id=4815 + i) for i in range(processes)]
    record = {"ProcessId": 4815, "ProcessName": name, "ProcessSlug": process["Slug"],
              "ProcessDescription": "<p>Automates retail current-account onboarding from CRM intake to T24 provisioning.</p>",
              "ProcessL1Id": None, "ProcessL2Id": None, "ProcessL3Id": None,  # null even when categorized
              "Hierarchy": "11,12", "Categories": [{"CategoryId": 11, "CategoryName": "Retail Banking", "Subcategories": [
                  {"CategoryId": 12, "CategoryName": "Account Onboarding", "Subcategories": []}]}],
              "ProcessSubmitterUserId": 42,
              "ProcessNumApplications": num_apps, "ProcessNumDocuments": 2, "ProcessIsDeleted": 0}
    docs = [
        {"Id": 901, "AutomationId": 4815, "Title": "PDD", "TypeId": pdd_type, "FileId": 77, "EmbedLink": None, "IsActive": 1},
        {"Id": 902, "AutomationId": 4815, "Title": "Map", "TypeId": 6, "FileId": 78, "EmbedLink": None, "IsActive": 1},
    ]
    flows = [{"Id": 8, "Name": "Business Process", "Phases": {"Assessment": {
        "NotStarted": {"PhaseVariable": "ASSESSMENT", "StatusVariable": "NOT_STARTED", "StatusValue": "Not Started"},
        "Archived": {"PhaseVariable": "ASSESSMENT", "StatusVariable": "ARCHIVED", "StatusValue": "Archived"}}}}]
    categories = {"Levels": [], "Categories": [
        {"CategoryId": 11, "CategoryName": "Retail Banking", "CategoryIsActive": 1, "CategoryIsOther": 0, "Subcategories": []}]}
    inventory = [{"Id": 21, "Name": "Microsoft Dynamics 365", "Version": "9.2"}, {"Id": 22, "Name": "Signicat", "Version": "2026"}]
    if offers_new_apps and created_apps:
        # Post-publish view: a new_applications submission created the missing systems.
        inventory += [{"Id": 31, "Name": "Trapets", "Version": ""}, {"Id": 32, "Name": "Scrive", "Version": ""},
                      {"Id": 33, "Name": "Temenos T24", "Version": "R24"}]
    auth = {"Type": "automation-cloud", "Tenant": {"Uuid": "u", "CompanyName": "c", "Url": "https://x/automationhub_"},
            "User": {"Id": 42, "Email": "dana.reyes@fjordline.example", "IsAdmin": 0, "IsActive": 1,
                     "Roles": ["ah-standard-user"]}}
    files = {
        "auth.json": envelope("AhAuthInfoGet", auth),
        "flows.json": envelope("AhIdeaFlowsList", flows),
        "categories.json": envelope("AhCategoriesGet", categories),
        "inventory.json": envelope("AhApplicationsList", inventory),
        "list.json": envelope("AhAutomationsList", listing),
        "get_all.json": envelope("AhAutomationsGet", record),
        "docs.json": envelope("AhDocumentsList", docs),
        "download.json": envelope("AhDocumentsDownload", {"Bytes": 1}),
        "phases.json": envelope("AhPhasesSet", {"AutomationId": 4815, "Phase": "ASSESSMENT", "Status": "ARCHIVED"}),
        "schema.json": envelope("AhAutomationsSchemaGet", {"SourceType": "COE", "Destination": "schema"}),
        # The schema document `schema get` writes to --destination; only the
        # applications question matters to preflight's new_applications probe.
        "schema_doc.json": {"properties": {"schema": {"properties": {"OVR": {"properties": {"ah-section-ovrbp-0-1": {
            "properties": {"OVR-COUNT_APPS": {"properties": {"value": {"type": "array"},
                                                              **({"new_applications": {"type": "array"}} if offers_new_apps else {})}}}}}}}}},
                            "user_inputs": {}},
    }
    for filename, payload in files.items():
        (responses / filename).write_text(json.dumps(payload))
    # Stored bytes served to `documents download`: the staged fixtures unless overridden.
    pdd_body = (HERE / "fixtures" / f"{PDD[:-3]}-template.md").read_text().replace("{{RUN_TOKEN}}", token)
    map_body = (HERE / "fixtures" / f"{MAP[:-5]}-template.bpmn").read_text().replace("{{RUN_TOKEN}}", token)
    (responses / "stored_pdd.md").write_text(pdd_body)
    (responses / "stored_map.bpmn").write_bytes(map_bytes if map_bytes is not None else map_body.encode())
    manifest = {"version": 2, "rules": [
        {"match": "ah auth-info get", "file": "auth.json"},
        {"match": "ah idea-flows list", "file": "flows.json"},
        {"match": "ah categories get", "file": "categories.json"},
        {"match": "ah applications list", "file": "inventory.json"},
        {"match": "ah automations schema get", "file": "schema.json", "write_destination": "schema_doc.json"},
        {"match": "ah automations list", "file": "list.json"},
        {"match": "--all-fields", "file": "get_all.json"},
        {"match": "ah documents list", "file": "docs.json"},
        {"match": "documents download 77", "file": "download.json", "write_destination": "stored_pdd.md"},
        {"match": "documents download 78", "file": "download.json", "write_destination": "stored_map.bpmn"},
        {"match": "ah phases set", "file": "phases.json"},
    ], "unmocked_default": {"response": "{\"Result\": \"Failure\", \"Message\": \"unmocked\"}\n", "exit_code": 1}}
    (responses / "manifest.json").write_text(json.dumps(manifest))


def seed(sandbox: Path) -> None:
    assert run(sandbox, sys.executable, "_setup/preflight_ah.py").returncode == 0
    # seed_publish renders templates; ours are pre-rendered, so write the seed directly
    # with the same shape (token, digests, merged preflight).
    import hashlib
    preflight = json.loads((sandbox / "ah-preflight.json").read_text())
    digests = {f: hashlib.sha256((sandbox / f).read_bytes()).hexdigest() for f in (PDD, MAP)}
    (sandbox / "seed.json").write_text(json.dumps({"run_token": TOKEN, "fixtures": digests, **preflight}))


def grade(sandbox: Path, check: str) -> subprocess.CompletedProcess:
    return run(sandbox, sys.executable, str(CHECKER), check)


def test_preflight_passes_and_records_flow(sandbox: Path) -> None:
    result = run(sandbox, sys.executable, "_setup/preflight_ah.py")
    assert result.returncode == 0, result.stderr
    preflight = json.loads((sandbox / "ah-preflight.json").read_text())
    assert preflight["business_process_flow_id"] == 8
    assert preflight["archive_status"] == "ARCHIVED"
    assert preflight["owner_email"] == "dana.reyes@fjordline.example"


def test_preflight_non_admin_gate(sandbox: Path) -> None:
    responses = sandbox / "mocks" / "responses"
    auth = json.loads((responses / "auth.json").read_text())
    auth["Data"]["User"]["Roles"].append("ah-system-admin")
    (responses / "auth.json").write_text(json.dumps(auth))
    assert run(sandbox, sys.executable, "_setup/preflight_ah.py").returncode == 0
    result = run(sandbox, sys.executable, "_setup/preflight_ah.py", "--require-non-admin")
    assert result.returncode == 1 and "admin" in result.stderr


def test_preflight_fails_without_business_process_flow(sandbox: Path) -> None:
    responses = sandbox / "mocks" / "responses"
    (responses / "flows.json").write_text(json.dumps(envelope("AhIdeaFlowsList", [{"Id": 1, "Name": "CoE-driven idea", "Phases": {}}])))
    result = run(sandbox, sys.executable, "_setup/preflight_ah.py")
    assert result.returncode == 1 and "Business Process" in result.stderr


def test_seed_publish_renders_templates(tmp_path: Path) -> None:
    shutil.copytree(HERE / "fixtures", tmp_path, dirs_exist_ok=True)
    shutil.copytree(GROUP / "_setup", tmp_path / "_setup")
    (tmp_path / "ah-preflight.json").write_text(json.dumps({"business_process_flow_id": 8}))
    result = subprocess.run([sys.executable, "_setup/seed_publish.py"], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    seed_data = json.loads((tmp_path / "seed.json").read_text())
    assert seed_data["run_token"].startswith("AHE2E-") and seed_data["business_process_flow_id"] == 8
    assert set(seed_data["fixtures"]) == {PDD, MAP}
    assert not list(tmp_path.glob("*-template.*"))
    assert seed_data["run_token"] in (tmp_path / PDD).read_text()
    assert seed_data["run_token"] in (tmp_path / MAP).read_text()


@pytest.mark.parametrize("check", ["process", "fields", "applications", "documents", "bpmn-layout"])
def test_golden_outcome_passes(sandbox: Path, check: str) -> None:
    seed(sandbox)
    result = grade(sandbox, check)
    assert result.returncode == 0, result.stdout + result.stderr


def test_duplicate_process_fails(sandbox: Path) -> None:
    write_tenant(sandbox / "mocks" / "responses", token=TOKEN, processes=2)
    seed(sandbox)
    assert "exactly one" in grade(sandbox, "process").stdout


def test_foreign_process_not_counted(sandbox: Path) -> None:
    write_tenant(sandbox / "mocks" / "responses", token=TOKEN, name_token="AHE2E-OTHER999")
    seed(sandbox)
    assert "found 0" in grade(sandbox, "process").stdout


def test_preflight_records_new_applications_offer(sandbox: Path) -> None:
    run(sandbox, sys.executable, "_setup/preflight_ah.py")
    assert json.loads((sandbox / "ah-preflight.json").read_text())["new_applications_offered"] is True
    write_tenant(sandbox / "mocks" / "responses", token=TOKEN, offers_new_apps=False)
    run(sandbox, sys.executable, "_setup/preflight_ah.py")
    assert json.loads((sandbox / "ah-preflight.json").read_text())["new_applications_offered"] is False


def test_missing_new_application_fails_when_schema_offers_it(sandbox: Path) -> None:
    write_tenant(sandbox / "mocks" / "responses", token=TOKEN, num_apps=4)  # one of the five dropped
    seed(sandbox)
    assert "dropped applications" in grade(sandbox, "applications").stdout


def test_pdd_systems_absent_from_inventory_fail_when_offered(sandbox: Path) -> None:
    # Five attached, but none of the missing PDD systems were created: decoys were attached instead.
    write_tenant(sandbox / "mocks" / "responses", token=TOKEN, num_apps=5, created_apps=False)
    seed(sandbox)
    assert "not in the inventory after the publish" in grade(sandbox, "applications").stdout


def test_inventory_only_expectation_without_new_applications(sandbox: Path) -> None:
    responses = sandbox / "mocks" / "responses"
    write_tenant(responses, token=TOKEN, offers_new_apps=False, num_apps=2)  # the two inventory systems
    seed(sandbox)
    assert grade(sandbox, "applications").returncode == 0
    write_tenant(responses, token=TOKEN, offers_new_apps=False, num_apps=1)
    seed(sandbox)
    assert "dropped applications" in grade(sandbox, "applications").stdout


def test_missing_category_fails(sandbox: Path) -> None:
    seed(sandbox)
    responses = sandbox / "mocks" / "responses"
    record = json.loads((responses / "get_all.json").read_text())
    record["Data"]["Hierarchy"] = ""
    record["Data"]["Categories"] = []
    (responses / "get_all.json").write_text(json.dumps(record))
    assert "no category" in grade(sandbox, "fields").stdout


def test_pdd_wrong_type_fails(sandbox: Path) -> None:
    write_tenant(sandbox / "mocks" / "responses", token=TOKEN, pdd_type=9)
    seed(sandbox)
    assert "exactly one PDD" in grade(sandbox, "documents").stdout


def test_rewritten_pdd_fails(sandbox: Path) -> None:
    seed(sandbox)
    (sandbox / "mocks" / "responses" / "stored_pdd.md").write_text("# a different document\n")
    assert "differ" in grade(sandbox, "documents").stdout


def test_bare_bpmn_without_layout_fails(sandbox: Path) -> None:
    bare = (b'<?xml version="1.0"?><bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">'
            b'<bpmn:process id="p"><bpmn:startEvent id="s"/></bpmn:process></bpmn:definitions>')
    write_tenant(sandbox / "mocks" / "responses", token=TOKEN, map_bytes=bare)
    seed(sandbox)
    assert "No diagrams found" in grade(sandbox, "bpmn-layout").stdout


def test_cleanup_archives_only_token_named(sandbox: Path) -> None:
    seed(sandbox)
    result = run(sandbox, sys.executable, "_setup/cleanup_ah.py")
    assert result.returncode == 0
    calls = [json.loads(l) for l in (sandbox / "mocks" / ".calls.jsonl").read_text().splitlines()]
    archived = [c["args"] for c in calls if c.get("matched_rule") == "ah phases set"]
    assert archived == ["ah phases set 4815 --phase ASSESSMENT --status ARCHIVED --output json"]


def test_cleanup_never_policy(sandbox: Path) -> None:
    seed(sandbox)
    result = subprocess.run([sys.executable, "_setup/cleanup_ah.py"], cwd=sandbox, capture_output=True, text=True,
                            env={**env_with_mock(sandbox), "AH_E2E_CLEANUP": "never"})
    assert result.returncode == 0
    calls = [json.loads(l) for l in (sandbox / "mocks" / ".calls.jsonl").read_text().splitlines()]
    assert not [c for c in calls if c.get("matched_rule") == "ah phases set"]


def test_parse_envelope_ignores_chatter_around_the_json() -> None:
    chatter = 'A new version {1.205} is available\n{"Result": "Success", "Data": {"Id": 1}}\nRun uip update {now}\n'
    assert ah_cli.parse_envelope(chatter) == {"Result": "Success", "Data": {"Id": 1}}
    assert ah_cli.parse_envelope("no json here {") is None


def test_archive_target_matches_tenant_specific_variable_names() -> None:
    flow = {"Phases": {"Qualification": {"Archived": {"PhaseVariable": "QUALIFICATION",
                                                       "StatusVariable": "QUALIFICATION_ARCHIVED",
                                                       "StatusValue": "Archived"}}}}
    assert ah_cli.archive_target(flow) == ("QUALIFICATION", "QUALIFICATION_ARCHIVED")
    assert ah_cli.archive_target({"Phases": {"A": {"S": {"PhaseVariable": "A", "StatusVariable": "DONE", "StatusValue": "Done"}}}}) is None

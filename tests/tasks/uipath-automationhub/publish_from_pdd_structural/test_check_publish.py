"""Self-tests for check_publish.py and the `.uip-recorder` shim, offline.

Each test stages a sandbox the way coder_eval does (live_template + rendered
fixtures + the seed.json pre_run writes), puts a stub "real" `uip` behind the
recorder, runs a publish sequence through `.uip-recorder/uip`, then grades the
call log. The stub only answers with envelopes; what is under test is the
recorder's log and the grader's reading of it, never tenant behaviour.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
LIVE_TEMPLATE = HERE.parent / "_shared" / "live_template"
CHECKER = HERE / "check_publish.py"
TOKEN = "AHE2E-TEST0001"
PDD = "pdd-retail-account-onboarding.md"
MAP = "process-map-retail-account-onboarding.bpmn"
OWNER = "dana.reyes@fjordline.example"
PROCESS_ID = 4815
DOC_CODE_PREFIX = "ah-answer_option-ovrbp-0-3-0-"
DOC_PDD = DOC_CODE_PREFIX + "1"  # "Standard operating procedure" — closest to a PDD
DOC_MAP = DOC_CODE_PREFIX + "2"  # "Task/Process maps/flowcharts"
INVENTORY = [
    {"Id": 21, "Name": "Microsoft Dynamics 365", "Version": "9.2"},
    {"Id": 22, "Name": "Signicat", "Version": "2026"},
    {"Id": 30, "Name": "SAP S/4HANA", "Version": "2023"},  # decoy
    {"Id": 31, "Name": "Salesforce", "Version": ""},  # decoy
]

# The stand-in for the real CLI: it answers each verb with a success envelope.
STUB_UIP = r'''#!/usr/bin/env python3
import json, sys
args = " ".join(sys.argv[1:])
if " applications update" in " " + args:
    print(json.dumps({"Result": "Failure", "Message": "403 Forbidden"})); sys.exit(1)
if " automations create" in " " + args:
    print(json.dumps({"Result": "Success", "Data": {"Id": %d}})); sys.exit(0)
if " documents create" in " " + args:
    print(json.dumps({"Result": "Success", "Data": {"Id": 901, "FileId": 77}})); sys.exit(0)
print(json.dumps({"Result": "Success", "Data": {}}))
''' % PROCESS_ID


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage(root: Path, *, inventory: list[dict] = INVENTORY, offers_new_apps: bool = True) -> Path:
    box = root / "sandbox"
    shutil.copytree(LIVE_TEMPLATE, box)
    for template in (HERE / "fixtures").glob("*-template.*"):
        name = template.name.replace("-template", "")
        (box / name).write_text(template.read_text(encoding="utf-8").replace("{{RUN_TOKEN}}", TOKEN), encoding="utf-8")
    seed = {
        "run_token": TOKEN,
        "fixtures": {PDD: digest(box / PDD), MAP: digest(box / MAP)},
        "new_applications_offered": offers_new_apps,
        "owner_email": OWNER,
        "business_process_flow_id": 8,
        "inventory": inventory,
        "active_category_ids": [11, 12],
        "category_ids": [1, 4, 11, 12],  # 1 = "Other", 4 = archived
    }
    (box / "seed.json").write_text(json.dumps(seed), encoding="utf-8")
    stub = root / "real-bin"
    stub.mkdir()
    (stub / "uip").write_text(STUB_UIP, encoding="utf-8")
    (stub / "uip").chmod(0o755)
    return box


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    return stage(tmp_path)


def uip(sandbox: Path, *args: str, record: bool = True) -> subprocess.CompletedProcess:
    recorder = sandbox / ".uip-recorder"
    env = {**os.environ, "PATH": os.pathsep.join([str(recorder), str(sandbox.parent / "real-bin"), os.environ["PATH"]])}
    env.pop("AH_EVAL_NO_RECORD", None)
    if not record:
        env["AH_EVAL_NO_RECORD"] = "1"
    return subprocess.run([sys.executable, str(recorder / "uip"), *args],
                          cwd=sandbox, capture_output=True, text=True, check=False, env=env)


def grade(sandbox: Path, check: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CHECKER), check],
                          cwd=sandbox, capture_output=True, text=True, check=False)


def good_answers() -> dict:
    return {"OVR": {
        "ah-section-ovrbp-0-0": {
            "OVR-OVERVIEW_NAME": {"value": f"Retail Account Onboarding {TOKEN}"},
            "OVR-OVERVIEW_DESCRIPTION": {"value": "Automates retail current-account onboarding from CRM intake to T24 provisioning."},
            "OVR-OVERVIEW_CATEGORY": {"value": 12},
            "OVR-PROCESS_OWNER": OWNER,
        },
        "ah-section-ovrbp-0-1": {
            "OVR-COUNT_APPS": {
                "value": [21, 22],
                "new_applications": [
                    {"application_name": "Trapets", "application_version": "4.1"},
                    {"application_name": "Scrive", "application_version": "2026"},
                    {"application_name": "Temenos T24", "application_version": "R21"},
                ],
            },
        },
        "ah-section-ovrbp-0-2": {"OVR-PROCESS_DOCUMENTS": {"value": [DOC_PDD, DOC_MAP]}},
        "ah-section-ovrbp-0-3": {"OVR-OVERVIEW_PROCESS_SUBMITTER": OWNER},
    }}


def section(answers: dict, key: str) -> dict:
    return next(s for s in answers["OVR"].values() if key in s)


def publish(sandbox: Path, answers: dict, *, pdd_type: str = "1", creates: int = 1, verify: bool = True) -> None:
    uip(sandbox, "ah", "--help")
    uip(sandbox, "ah", "idea-flows", "list", "--output", "json")
    uip(sandbox, "ah", "auth-info", "get", "--output", "json")
    (sandbox / "ah-answers.json").write_text(json.dumps(answers))
    for _ in range(creates):
        uip(sandbox, "ah", "automations", "create", "--from-schema", "--idea-flow-id", "8",
            "--file", "./ah-answers.json", "--output", "json")
    pid = str(PROCESS_ID)
    uip(sandbox, "ah", "documents", "create", pid, "--title", "PDD", "--description", "PDD",
        "--document-type-id", pdd_type, "--file", PDD, "--output", "json")
    uip(sandbox, "ah", "documents", "create", pid, "--title", "Map", "--description", "Map",
        "--document-type-id", "6", "--file", MAP, "--output", "json")
    if verify:
        uip(sandbox, "ah", "documents", "list", pid, "--output", "json")
        uip(sandbox, "ah", "automations", "get", pid, "--all-fields", "--output", "json")


# --- the recorder ---------------------------------------------------------------

def test_recorder_passes_output_and_exit_code_through(sandbox: Path) -> None:
    result = uip(sandbox, "ah", "applications", "update", "--file", "x.json")
    assert result.returncode == 1
    assert json.loads(result.stdout)["Result"] == "Failure"


def test_recorder_logs_result_and_created_id(sandbox: Path) -> None:
    publish(sandbox, good_answers())
    calls = [json.loads(line) for line in (sandbox / ".uip-recorder" / ".calls.jsonl").read_text().splitlines()]
    create = next(c for c in calls if "automations create" in c["args"])
    assert create["result"] == "Success" and create["data_id"] == PROCESS_ID
    assert create["captured"]["json"]["OVR"]


def test_recorder_skips_harness_calls(sandbox: Path) -> None:
    uip(sandbox, "ah", "automations", "list", "--search", TOKEN, record=False)
    assert not (sandbox / ".uip-recorder" / ".calls.jsonl").exists()


def test_recorder_uses_the_tenant_home(sandbox: Path, tmp_path: Path) -> None:
    probe = tmp_path / "real-bin" / "uip"
    probe.write_text("#!/usr/bin/env python3\nimport os\nprint(os.environ['HOME'])\n")
    (sandbox / ".ah-tenant-home").write_text("/tmp/ah-tenant-xyz")
    assert uip(sandbox, "login", "status").stdout.strip() == "/tmp/ah-tenant-xyz"


# --- the grader -----------------------------------------------------------------

@pytest.mark.parametrize("check", ["create-once", "payload", "applications", "documents", "verify", "users"])
def test_golden_publish_passes(sandbox: Path, check: str) -> None:
    publish(sandbox, good_answers())
    result = grade(sandbox, check)
    assert result.returncode == 0, result.stdout


def test_help_on_create_is_not_a_create(sandbox: Path) -> None:
    uip(sandbox, "ah", "automations", "create", "--help")
    publish(sandbox, good_answers())
    assert grade(sandbox, "create-once").returncode == 0


def test_payload_captured_at_call_time(sandbox: Path) -> None:
    publish(sandbox, good_answers())
    (sandbox / "ah-answers.json").write_text("{}")  # agent overwrites after the create
    assert grade(sandbox, "payload").returncode == 0


def test_duplicate_create_fails(sandbox: Path) -> None:
    publish(sandbox, good_answers(), creates=2)
    assert "exactly 1" in grade(sandbox, "create-once").stdout


def test_failed_create_fails(sandbox: Path, tmp_path: Path) -> None:
    (tmp_path / "real-bin" / "uip").write_text(
        "#!/usr/bin/env python3\nimport json\nprint(json.dumps({'Result': 'ValidationError'}))\nraise SystemExit(1)\n")
    publish(sandbox, good_answers())
    assert "did not succeed" in grade(sandbox, "create-once").stdout


def test_template_placeholders_fail(sandbox: Path) -> None:
    answers = good_answers()
    section(answers, "OVR-OVERVIEW_DESCRIPTION")["OVR-OVERVIEW_DESCRIPTION"] = {"value": "Sample input for the description field"}
    publish(sandbox, answers)
    assert "placeholders" in grade(sandbox, "payload").stdout


def test_dropped_reference_code_fails(sandbox: Path) -> None:
    answers = good_answers()
    section(answers, "OVR-OVERVIEW_NAME")["OVR-OVERVIEW_NAME"] = {"value": "Retail Account Onboarding"}
    publish(sandbox, answers)
    assert "reference code" in grade(sandbox, "payload").stdout


@pytest.mark.parametrize("category, state", [(1, "archived or 'Other'"), (4, "archived or 'Other'"), (999, "not on this tenant")])
def test_inactive_or_unknown_category_fails(sandbox: Path, category: int, state: str) -> None:
    answers = good_answers()
    section(answers, "OVR-OVERVIEW_CATEGORY")["OVR-OVERVIEW_CATEGORY"] = {"value": category}
    publish(sandbox, answers)
    assert state in grade(sandbox, "payload").stdout


def test_wrapped_owner_is_tolerated(sandbox: Path) -> None:
    answers = good_answers()
    section(answers, "OVR-PROCESS_OWNER")["OVR-PROCESS_OWNER"] = {"value": OWNER}
    publish(sandbox, answers)
    assert grade(sandbox, "payload").returncode == 0


def test_wrong_owner_fails(sandbox: Path) -> None:
    answers = good_answers()
    section(answers, "OVR-PROCESS_OWNER")["OVR-PROCESS_OWNER"] = {"value": "someone.else@fjordline.example"}
    publish(sandbox, answers)
    assert "OVR-PROCESS_OWNER" in grade(sandbox, "payload").stdout


def test_sop_only_documentation_passes(sandbox: Path) -> None:
    answers = good_answers()
    section(answers, "OVR-PROCESS_DOCUMENTS")["OVR-PROCESS_DOCUMENTS"] = {"value": [DOC_PDD]}
    publish(sandbox, answers)
    assert grade(sandbox, "payload").returncode == 0


def test_no_documentation_code_fails(sandbox: Path) -> None:
    answers = good_answers()
    section(answers, "OVR-PROCESS_DOCUMENTS")["OVR-PROCESS_DOCUMENTS"] = {"value": [DOC_PDD, DOC_CODE_PREFIX + "6"]}
    publish(sandbox, answers)
    assert "none/don't know" in grade(sandbox, "payload").stdout


def test_decoy_inventory_id_fails(sandbox: Path) -> None:
    answers = good_answers()
    section(answers, "OVR-COUNT_APPS")["OVR-COUNT_APPS"]["value"] = [21, 22, 30]
    publish(sandbox, answers)
    assert "not systems the PDD names" in grade(sandbox, "applications").stdout


def test_out_of_scope_system_fails(sandbox: Path) -> None:
    answers = good_answers()
    section(answers, "OVR-COUNT_APPS")["OVR-COUNT_APPS"]["new_applications"].append({"application_name": "Avaloq"})
    publish(sandbox, answers)
    assert "out-of-scope" in grade(sandbox, "applications").stdout


def test_invented_new_application_fails(sandbox: Path) -> None:
    answers = good_answers()
    section(answers, "OVR-COUNT_APPS")["OVR-COUNT_APPS"]["new_applications"].append({"application_name": "Outlook"})
    publish(sandbox, answers)
    assert "does not" in grade(sandbox, "applications").stdout


def test_missing_new_application_fails(sandbox: Path) -> None:
    answers = good_answers()
    apps = section(answers, "OVR-COUNT_APPS")["OVR-COUNT_APPS"]
    apps["new_applications"] = apps["new_applications"][:2]  # drops Temenos T24
    publish(sandbox, answers)
    assert "temenos t24" in grade(sandbox, "applications").stdout


def test_inventory_system_by_name_is_tolerated(sandbox: Path) -> None:
    answers = good_answers()
    apps = section(answers, "OVR-COUNT_APPS")["OVR-COUNT_APPS"]
    apps["value"] = [21]
    apps["new_applications"].append({"application_name": "Signicat"})  # server dedupes by name
    publish(sandbox, answers)
    assert grade(sandbox, "applications").returncode == 0


def test_grades_against_the_inventory_snapshot(tmp_path: Path) -> None:
    # Every PDD system already in the inventory (DefaultTenant after earlier runs):
    # ids alone answer it, and nothing needs to arrive by name.
    names = ["Microsoft Dynamics 365", "Signicat", "Trapets", "Scrive", "Temenos T24"]
    box = stage(tmp_path, inventory=[{"Id": 40 + i, "Name": n, "Version": ""} for i, n in enumerate(names)])
    answers = good_answers()
    apps = section(answers, "OVR-COUNT_APPS")["OVR-COUNT_APPS"]
    apps["value"], apps["new_applications"] = [40, 41, 42, 43, 44], []
    publish(box, answers)
    assert grade(box, "applications").returncode == 0


def test_wrong_pdd_type_fails(sandbox: Path) -> None:
    publish(sandbox, good_answers(), pdd_type="9")
    assert "type id" in grade(sandbox, "documents").stdout


def test_regenerated_process_map_fails(sandbox: Path) -> None:
    (sandbox / MAP).write_text("<bpmn:definitions/>")  # bare BPMN with no bpmndi layout
    publish(sandbox, good_answers())
    assert "process map" in grade(sandbox, "documents").stdout


def test_no_read_back_fails(sandbox: Path) -> None:
    publish(sandbox, good_answers(), verify=False)
    assert grade(sandbox, "verify").returncode == 1


def test_harness_read_back_does_not_count(sandbox: Path) -> None:
    publish(sandbox, good_answers(), verify=False)
    uip(sandbox, "ah", "automations", "get", str(PROCESS_ID), record=False)
    uip(sandbox, "ah", "documents", "list", str(PROCESS_ID), record=False)
    assert grade(sandbox, "verify").returncode == 1


def test_no_calls_fails(sandbox: Path) -> None:
    assert "never invoked" in grade(sandbox, "payload").stdout


def test_owner_lookup_with_both_flags_passes(sandbox: Path) -> None:
    uip(sandbox, "ah", "users", "list", "--search", OWNER, "--invite-status", "all", "--output", "json")
    publish(sandbox, good_answers())
    assert grade(sandbox, "users").returncode == 0


def test_owner_lookup_without_invite_status_all_fails(sandbox: Path) -> None:
    uip(sandbox, "ah", "users", "list", "--search", OWNER, "--output", "json")
    publish(sandbox, good_answers())
    assert "--invite-status all" in grade(sandbox, "users").stdout


def test_owner_lookup_without_search_fails(sandbox: Path) -> None:
    uip(sandbox, "ah", "users", "list", "--invite-status", "all", "--limit", "500", "--output", "json")
    publish(sandbox, good_answers())
    assert "--search" in grade(sandbox, "users").stdout


def test_numeric_strings_are_the_same_ids(sandbox: Path) -> None:
    answers = good_answers()
    section(answers, "OVR-OVERVIEW_CATEGORY")["OVR-OVERVIEW_CATEGORY"] = {"value": "12"}
    section(answers, "OVR-COUNT_APPS")["OVR-COUNT_APPS"]["value"] = ["21", "22"]
    publish(sandbox, answers)
    assert grade(sandbox, "payload").returncode == 0
    assert grade(sandbox, "applications").returncode == 0


# --- publish_from_pdd_403_fallback ------------------------------------------------

def fallback_answers() -> dict:
    answers = good_answers()
    section(answers, "OVR-COUNT_APPS")["OVR-COUNT_APPS"] = {"value": [21, 22]}
    section(answers, "OVR-OVERVIEW_DESCRIPTION")["OVR-OVERVIEW_DESCRIPTION"] = {"value": (
        "Automates retail current-account onboarding from CRM intake to account provisioning. "
        "Trapets, Scrive and Temenos T24 are not in the application inventory and could not be attached.")}
    return answers


@pytest.fixture
def fallback_sandbox(tmp_path: Path) -> Path:
    return stage(tmp_path, offers_new_apps=False)


def fallback_publish(sandbox: Path, answers: dict, *, attempts: int = 1, after: int = 0) -> None:
    (sandbox / "new-apps.json").write_text("[]")
    for _ in range(attempts):
        uip(sandbox, "ah", "applications", "update", "--file", "./new-apps.json", "--output", "json")
    publish(sandbox, answers)
    for _ in range(after):
        uip(sandbox, "ah", "applications", "update", "--file", "./new-apps.json", "--output", "json")


@pytest.mark.parametrize("check", ["create-once", "payload", "fallback", "documents", "verify", "users"])
def test_fallback_golden_passes(fallback_sandbox: Path, check: str) -> None:
    fallback_publish(fallback_sandbox, fallback_answers())
    result = grade(fallback_sandbox, check)
    assert result.returncode == 0, result.stdout


def test_fallback_without_an_attempt_fails(fallback_sandbox: Path) -> None:
    fallback_publish(fallback_sandbox, fallback_answers(), attempts=0)
    assert "never attempted" in grade(fallback_sandbox, "fallback").stdout


def test_fallback_retry_after_create_fails(fallback_sandbox: Path) -> None:
    fallback_publish(fallback_sandbox, fallback_answers(), after=1)
    assert "after the create" in grade(fallback_sandbox, "fallback").stdout


def test_fallback_repeated_attempt_fails(fallback_sandbox: Path) -> None:
    fallback_publish(fallback_sandbox, fallback_answers(), attempts=2)
    assert "attempted 2 times" in grade(fallback_sandbox, "fallback").stdout


def test_fallback_new_applications_key_fails(fallback_sandbox: Path) -> None:
    answers = fallback_answers()
    section(answers, "OVR-COUNT_APPS")["OVR-COUNT_APPS"]["new_applications"] = [{"application_name": "Trapets"}]
    fallback_publish(fallback_sandbox, answers)
    assert "does not offer it" in grade(fallback_sandbox, "fallback").stdout


def test_fallback_decoy_substitute_fails(fallback_sandbox: Path) -> None:
    answers = fallback_answers()
    section(answers, "OVR-COUNT_APPS")["OVR-COUNT_APPS"]["value"] = [21, 22, 30]
    fallback_publish(fallback_sandbox, answers)
    assert "not systems the PDD names" in grade(fallback_sandbox, "fallback").stdout


def test_fallback_dropped_inventory_system_fails(fallback_sandbox: Path) -> None:
    answers = fallback_answers()
    section(answers, "OVR-COUNT_APPS")["OVR-COUNT_APPS"]["value"] = [21]
    fallback_publish(fallback_sandbox, answers)
    assert "signicat" in grade(fallback_sandbox, "fallback").stdout


def test_fallback_unnamed_gap_fails(fallback_sandbox: Path) -> None:
    answers = fallback_answers()
    section(answers, "OVR-OVERVIEW_DESCRIPTION")["OVR-OVERVIEW_DESCRIPTION"] = {
        "value": "Automates retail current-account onboarding; Trapets and Scrive could not be attached."}
    fallback_publish(fallback_sandbox, answers)
    assert "temenos t24" in grade(fallback_sandbox, "fallback").stdout


def test_fallback_on_a_tenant_offering_new_applications_is_an_environment_gap(sandbox: Path) -> None:
    fallback_publish(sandbox, fallback_answers())
    assert "environment" in grade(sandbox, "fallback").stdout


def test_fallback_upsert_that_succeeds_is_an_environment_gap(fallback_sandbox: Path, tmp_path: Path) -> None:
    stub = tmp_path / "real-bin" / "uip"
    stub.write_text(stub.read_text().replace('"Result": "Failure", "Message": "403 Forbidden"', '"Result": "Success"'))
    fallback_publish(fallback_sandbox, fallback_answers())
    assert "environment" in grade(fallback_sandbox, "fallback").stdout

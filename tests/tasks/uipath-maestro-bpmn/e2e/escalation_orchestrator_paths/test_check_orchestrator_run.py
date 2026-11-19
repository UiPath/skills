"""check_orchestrator_run.py grades each path run's Slack post and named outputs.

`fixtures/Process.bpmn` and `fixtures/run_seed.json` are the agent's process and
the seed from a passing Studio Web run: a classify
script, a gateway, one Slack step per branch, two end events whose outputs
share one set of root variables. Runtime payloads follow the
`debug-instance variables-all` shape (PascalCase Globals, each element's own
`Outputs`, the Slack step's `Response`).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import pytest

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


checker = _load("check_orchestrator_run", HERE / "check_orchestrator_run.py")
seed_module = _load("orchestrator_seed", HERE / "_setup" / "seed.py")

BPMN = FIXTURES / "Process.bpmn"
SEED = json.loads((FIXTURES / "run_seed.json").read_text())
CLASSIFIED_FIELDS = ("escalationPath", "severity", "engineeringNeeded", "responseMode")
PROCESS = checker.load_process(BPMN)
SLACK = checker.slack_ids(PROCESS)


@pytest.fixture(autouse=True)
def _live_target(monkeypatch):
    monkeypatch.setattr(checker.escalation_is, "assert_live_target", lambda: {})


def _slack_step(case, shared_node=False) -> str:
    if shared_node:
        return "sendEscalationAlert"
    return "sendEscalationAlert" if case["expected"]["escalationPath"] == "escalation" else "sendTriageNotice"


def _debug(case, *, extra_slack=False, shared_node=False):
    step = _slack_step(case, shared_node)
    end = "escalationEnd" if step == "sendEscalationAlert" else "triageEnd"
    executions = [
        {"ElementId": "manualStart", "ElementType": "StartEvent", "Status": "Completed"},
        {"ElementId": "classify", "ElementType": "ScriptTask", "Status": "Completed"},
        {"ElementId": "routeEscalation", "ElementType": "ExclusiveGateway", "Status": "Completed"},
        {"ElementId": step, "ElementType": "SendTask", "Status": "Completed"},
        {"ElementId": end, "ElementType": "EndEvent", "Status": "Completed"},
    ]
    if extra_slack:
        executions.insert(4, {"ElementId": "sendTriageNotice", "ElementType": "SendTask", "Status": "Completed"})
    return {"InstanceId": "inst", "FinalStatus": "Completed", "ElementExecutions": executions}


def _variables(
    case, *, ts="1763405123.456789", text=None, message_id=None, shared_node=False, channel="C0B2FDZD1M3", **overrides
):
    expected = {**case["expected"], **overrides}
    corr = case["inputs"]["correlationId"]
    text = text if text is not None else f"[{expected['escalationPath']}] {corr}"
    response = {"ok": True, "channel": channel, "ts": ts, "message": {"text": text}}
    outputs = {
        "EscalationPath": expected["escalationPath"],
        "Severity": expected["severity"],
        "EngineeringNeeded": expected["engineeringNeeded"],
        "ResponseMode": expected["responseMode"],
        "CaseKey": corr,
        "SlackMessageId": message_id or ts,
    }
    return {
        "Variables": [
            {
                "ParentElementId": None,
                "Globals": {"CorrelationId": corr, **outputs},
                "Elements": [
                    {"ElementId": "classify", "Outputs": {"Response": {k: expected[k] for k in CLASSIFIED_FIELDS}}},
                    {"ElementId": _slack_step(case, shared_node), "Outputs": {"Response": response}},
                ],
            }
        ]
    }


@pytest.mark.parametrize("case", SEED["cases"], ids=[c["name"] for c in SEED["cases"]])
def test_every_seeded_path_passes_on_the_real_process(case):
    assert checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case))


def test_slack_steps_found_by_connector_key():
    assert SLACK == {"sendEscalationAlert", "sendTriageNotice"}


def test_two_posts_in_one_run_fail():
    case = SEED["cases"][0]
    with pytest.raises(checker.CheckFailure, match="exactly one Slack post"):
        checker.verify_case(PROCESS, SLACK, case, _debug(case, extra_slack=True), _variables(case))


def test_wrong_severity_fails():
    case = SEED["cases"][1]
    with pytest.raises(checker.CheckFailure, match="severity"):
        checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, severity="Sev1"))


@pytest.mark.parametrize(
    "value",
    ["draft", "Draft response", True, "Needs draft", "Draft for engineering", "drafted", "true", "Yes", "YES",
     "Response required", "Response", "response needed", "DraftRequired", "DraftResponse", "draftRequired",
     "Auto-reply", "AI-generated reply", "Draft", "maybe", "pending"],
)
def test_a_draft_response_mode_is_read_by_meaning(value):
    case = SEED["cases"][0]
    assert checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, responseMode=value))


def test_sev3_needs_no_draft_response():
    case = next(c for c in SEED["cases"] if c["expected"]["severity"] == "Sev3")
    assert checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, responseMode="none"))
    with pytest.raises(checker.CheckFailure, match="responseMode"):
        checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, responseMode="Draft"))


@pytest.mark.parametrize(
    "value",
    ["No draft", "NoDraft", "no_draft", "no-draft", "Draft not needed", "Not applicable", "N/A",
     "No response needed", "none", "Draft: none", "none (draft not required)", "Do not draft",
     "Don't draft", "Without a draft", "Draft: false", False, "not drafted", "not_drafted", "undrafted",
     "draft_response_not_needed", "Response not required", "none required", "skipped", "false", "No response",
     "Not required", "Not needed", "no", "No.", None, "", "   ", "-", "nothing", "nil", "empty", "Nil", "Empty",
     "draft response: none", "Draft: no", "draft - no", "Draft = none", "Draft response: false", "response: no",
     "Response: N/A", "Response none", "Response is none", "Response (none)", "Response: null", "Response skipped", "Response omitted",
     "NoDraftNeeded", "noDraftRequired", "NoReply", "Draft not generated", "Skip draft", "SkipDraft",
     "No automatic response", "None (Sev3)", "No reply", "Not required for Sev3", "Draft never sent", "no_reply",
     "None or N/A", "none or not applicable", "None OR n/a", "NODRAFT", "nodraft", "noresponse", "NORESPONSE",
     "nodraftneeded", "n-a", "N / A", "n.a.", "N.A.", "None/N/A", "N_A", "n_a", "n\\a",
     "non-draft", "nondraft", "Non-Draft", "non draft"],
)
def test_a_negated_response_mode_reads_as_none(value):
    triage = next(c for c in SEED["cases"] if c["expected"]["escalationPath"] == "duplicate")
    assert checker.verify_case(PROCESS, SLACK, triage, _debug(triage), _variables(triage, responseMode=value))
    sev1 = SEED["cases"][0]
    with pytest.raises(checker.CheckFailure, match="responseMode"):
        checker.verify_case(PROCESS, SLACK, sev1, _debug(sev1), _variables(sev1, responseMode=value))


def test_a_process_that_never_declares_response_mode_fails_a_none_case(tmp_path):
    bpmn = tmp_path / "Process.bpmn"
    bpmn.write_text(BPMN.read_text().replace('name="responseMode"', 'name="routing"'))
    process = checker.load_process(bpmn)
    triage = next(c for c in SEED["cases"] if c["expected"]["escalationPath"] == "duplicate")
    variables = _variables(triage)
    del variables["Variables"][0]["Globals"]["ResponseMode"]
    with pytest.raises(checker.CheckFailure, match="responseMode"):
        checker.verify_case(process, checker.slack_ids(process), triage, _debug(triage), variables)


@pytest.mark.parametrize("value", ["draft or none", "None or draft", "Draft/None", "draft|none", "none | draft",
                                   "Draft / No", "response/none", "Draft OR n/a", "draft or N / A"])
def test_an_unrecognized_response_mode_matches_neither_mode(value):
    for case in (SEED["cases"][0], next(c for c in SEED["cases"] if c["expected"]["escalationPath"] == "duplicate")):
        with pytest.raises(checker.CheckFailure, match="responseMode"):
            checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, responseMode=value))


def test_message_id_must_be_the_posted_ts():
    case = SEED["cases"][3]
    with pytest.raises(checker.CheckFailure, match="slackMessageId"):
        checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, message_id="1700000000.000001"))


def test_message_must_carry_the_path_and_correlation_id():
    case = SEED["cases"][4]
    with pytest.raises(checker.CheckFailure, match="does not carry"):
        checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, text="triage notice"))


@pytest.mark.parametrize(
    "index, template",
    [
        (4, "Triage notice for {corr}"),
        (0, "CustomerEscalationOrchestrator alert {corr}"),
        (0, "New escalations: {corr}"),
    ],
)
def test_message_with_the_correlation_id_but_not_the_path_fails(index, template):
    case = SEED["cases"][index]
    text = template.format(corr=case["inputs"]["correlationId"])
    with pytest.raises(checker.CheckFailure, match="does not carry"):
        checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, text=text))


@pytest.mark.parametrize(
    "index, template",
    [
        (0, "Escalation alert: {corr} Sev1"),
        (4, "Path: unknown_customer | {corr}"),
        (4, "Unknown customer - {corr}"),
        (6, "[multiple-matches] {corr}"),
    ],
)
def test_message_naming_the_path_as_its_own_word_passes(index, template):
    case = SEED["cases"][index]
    text = template.format(corr=case["inputs"]["correlationId"])
    assert checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, text=text))


def test_one_slack_step_for_both_paths_passes():
    for case in SEED["cases"]:
        checker.verify_case(PROCESS, SLACK, case, _debug(case, shared_node=True), _variables(case, shared_node=True))


def test_main_runs_every_case(tmp_path, monkeypatch):
    seeded = seed_module.build_seed()["cases"]
    project = tmp_path / "CustomerEscalationOrchestrator" / "CustomerEscalationOrchestrator"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text('{"Name": "CustomerEscalationOrchestrator"}')
    (project / "Process.bpmn").write_text(BPMN.read_text())
    (tmp_path / "seed.json").write_text(json.dumps({"cases": seeded}))
    monkeypatch.chdir(tmp_path)
    sent = []
    state = {}

    def fake_debug(project_dir, inputs, log, **k):
        state["case"] = next(c for c in seeded if c["inputs"] == inputs)
        sent.append(inputs)
        return _debug(state["case"]), "inst"

    monkeypatch.setattr(checker, "import_exact", lambda bpmn, project_dir, solution: project_dir)
    monkeypatch.setattr(checker, "run_debug", fake_debug)
    monkeypatch.setattr(checker, "fetch_variables", lambda i: (_variables(state["case"]), ""))
    checker.cases()
    assert sent == [c["inputs"] for c in seeded]


def test_cases_checks_the_live_target_before_any_debug(tmp_path, monkeypatch):
    def refuse():
        raise checker.CheckFailure("wrong tenant")

    def no_debug(*a, **k):
        raise AssertionError("debug ran before the target check")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(checker.escalation_is, "assert_live_target", refuse)
    monkeypatch.setattr(checker, "run_debug", no_debug)
    monkeypatch.setattr(checker, "import_exact", no_debug)
    with pytest.raises(checker.CheckFailure, match="wrong tenant"):
        checker.cases()


def _journalled(tmp_path) -> set:
    path = tmp_path / ".created-ids.jsonl"
    if not path.is_file():
        return set()
    return {tuple(json.loads(line)["value"]) for line in path.read_text().splitlines()}


def _orchestrator_sandbox(tmp_path, monkeypatch, seeded, **variable_overrides):
    project = tmp_path / "CustomerEscalationOrchestrator" / "CustomerEscalationOrchestrator"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text('{"Name": "CustomerEscalationOrchestrator"}')
    (project / "Process.bpmn").write_text(BPMN.read_text())
    (tmp_path / "seed.json").write_text(json.dumps({"cases": seeded}))
    monkeypatch.chdir(tmp_path)
    state = {}

    def fake_debug(project_dir, inputs, log, **k):
        state["case"] = next(c for c in seeded if c["inputs"] == inputs)
        return _debug(state["case"]), "inst"

    monkeypatch.setattr(checker, "import_exact", lambda bpmn, project_dir, solution: project_dir)
    monkeypatch.setattr(checker, "run_debug", fake_debug)
    monkeypatch.setattr(
        checker, "fetch_variables", lambda i: (_variables(state["case"], **variable_overrides), "")
    )
    monkeypatch.setattr(checker, "fetch_incidents", lambda i: ([], ""))


def test_every_message_the_run_posts_is_journalled_for_teardown(tmp_path, monkeypatch):
    _orchestrator_sandbox(tmp_path, monkeypatch, seed_module.build_seed()["cases"])
    checker.cases()
    assert _journalled(tmp_path) == {("C0B2FDZD1M3", "1763405123.456789")}


def test_a_failed_case_still_journals_the_message_it_posted(tmp_path, monkeypatch):
    _orchestrator_sandbox(tmp_path, monkeypatch, seed_module.build_seed()["cases"], severity="SevX")
    with pytest.raises(checker.CheckFailure):
        checker.cases()
    assert _journalled(tmp_path) == {("C0B2FDZD1M3", "1763405123.456789")}


def _failing_sandbox(tmp_path, monkeypatch, *, fail_at):
    seeded = seed_module.build_seed()["cases"]
    _orchestrator_sandbox(tmp_path, monkeypatch, seeded)
    case = seeded[0]
    posted = json.dumps(_variables(case)["Variables"][0]["Elements"][1]["Outputs"])
    other = json.dumps({"channel": "C0B2FDZD1M3", "ts": "1763400000.000001"})
    log = f"stdout: {posted}\nunrelated {other}\n"

    def run_debug(project_dir, inputs, log_file, **k):
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        Path(log_file).write_text(log)
        if fail_at == "debug":
            raise checker.CheckFailure("debug stopped waiting")
        return _debug(case), "inst"

    def fetch(instance_id):
        raise subprocess.TimeoutExpired("uip", 120)

    monkeypatch.setattr(checker, "run_debug", run_debug)
    if fail_at == "variables":
        monkeypatch.setattr(checker, "fetch_variables", fetch)


@pytest.mark.parametrize("fail_at, error", [("debug", checker.CheckFailure), ("variables", subprocess.TimeoutExpired)])
def test_a_failed_run_journals_the_posts_in_its_log(tmp_path, monkeypatch, fail_at, error):
    _failing_sandbox(tmp_path, monkeypatch, fail_at=fail_at)
    with pytest.raises(error):
        checker.cases()
    assert _journalled(tmp_path) == {("C0B2FDZD1M3", "1763405123.456789")}


def test_post_run_replays_the_journal_within_the_post_run_cap():
    import yaml

    task = yaml.safe_load((HERE / "escalation_orchestrator_paths.yaml").read_text())
    sweeps = [step for step in task["post_run"] if "teardown_escalation.py" in step["command"]]
    assert len(sweeps) == 1
    assert sweeps[0]["timeout"] <= 300


def test_slack_failure_advisory_accepts_the_real_process(tmp_path, monkeypatch):
    project = tmp_path / "CustomerEscalationOrchestrator" / "CustomerEscalationOrchestrator"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text('{"Name": "CustomerEscalationOrchestrator"}')
    (project / "Process.bpmn").write_text(BPMN.read_text())
    monkeypatch.chdir(tmp_path)
    checker.slack_failure_handled()


def test_a_post_to_another_channel_fails():
    case = SEED["cases"][0]
    with pytest.raises(checker.CheckFailure, match="posted to channel"):
        checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, channel="C0000000000"))


def test_a_slack_step_posting_as_the_bot_fails():
    bot = checker.load_process(_bpmn_with_send_as("bot"))
    case = SEED["cases"][0]
    with pytest.raises(checker.CheckFailure, match="must post as 'user'"):
        checker.verify_case(bot, checker.slack_ids(bot), case, _debug(case), _variables(case))


@pytest.mark.parametrize("value, expected", [("yes", True), ("Yes", True), ("NO", False), ("no", False)])
def test_engineering_needed_yes_no_reads_as_a_boolean(value, expected):
    case = next(c for c in SEED["cases"] if c["expected"]["engineeringNeeded"] is expected)
    assert checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, engineeringNeeded=value))


@pytest.mark.parametrize("value, expected", [(1, True), (0, False)])
def test_engineering_needed_number_is_not_a_boolean(value, expected):
    case = next(c for c in SEED["cases"] if c["expected"]["engineeringNeeded"] is expected)
    with pytest.raises(checker.CheckFailure, match="engineeringNeeded"):
        checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, engineeringNeeded=value))


def test_engineering_needed_yes_fails_where_none_is_needed():
    case = next(c for c in SEED["cases"] if c["expected"]["engineeringNeeded"] is False)
    with pytest.raises(checker.CheckFailure, match="engineeringNeeded"):
        checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, engineeringNeeded="yes"))


def _bpmn_with_send_as(identity: str) -> Path:
    path = Path(tempfile.mkdtemp()) / "Process.bpmn"
    path.write_text(BPMN.read_text().replace('{"send_as":"user"}', '{"send_as":"%s"}' % identity))
    return path


def _first_matching_rule(inputs: dict) -> str:
    if not inputs["senderDomain"]:
        return "missing_domain"
    if inputs["customerMatchStatus"] == "none":
        return "unknown_customer"
    if inputs["customerMatchStatus"] == "multiple":
        return "multiple_matches"
    return "duplicate" if inputs["isDuplicate"] else "escalation"


def _rules_tripped(inputs: dict) -> int:
    return sum([
        not inputs["senderDomain"],
        inputs["customerMatchStatus"] == "none",
        inputs["customerMatchStatus"] == "multiple",
        inputs["isDuplicate"],
    ])


def test_the_seed_has_overlap_cases_won_by_the_first_rule():
    cases = seed_module.build_seed()["cases"]
    overlaps = [c for c in cases if _rules_tripped(c["inputs"]) > 1]
    assert len(overlaps) >= 3
    for case in cases:
        assert case["expected"]["escalationPath"] == _first_matching_rule(case["inputs"])


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_the_real_classifier_agrees_with_every_seeded_case():
    script = PROCESS.find(".//{http://www.omg.org/spec/BPMN/20100524/MODEL}script").text
    for case in seed_module.build_seed()["cases"]:
        program = f"const vars = {json.dumps(case['inputs'])}; console.log(JSON.stringify((function(){{{script}}})()));"
        out = subprocess.run(["node", "-e", program], capture_output=True, text=True, check=True).stdout
        got = json.loads(out)
        for field in ("escalationPath", "severity", "engineeringNeeded"):
            assert got[field] == case["expected"][field], (case["name"], field)


def _handler_check(text: str) -> None:
    root = ET.fromstring(text)
    process = root.find("{http://www.omg.org/spec/BPMN/20100524/MODEL}process")
    checker.assert_error_handlers(root, process, tuple(sorted(SLACK)))


def test_error_handlers_accept_the_real_process():
    _handler_check(BPMN.read_text())


def test_a_slack_step_without_an_error_boundary_fails():
    text = BPMN.read_text().replace("<bpmn:errorEventDefinition />", "", 1)
    with pytest.raises(checker.CheckFailure, match="no error boundary event"):
        _handler_check(text)


def test_an_error_handler_that_calls_slack_again_fails():
    text = BPMN.read_text().replace(
        'sourceRef="sendEscalationAlert_onError" targetRef="handleEscalationSlackFailure"',
        'sourceRef="sendEscalationAlert_onError" targetRef="sendTriageNotice"',
    )
    with pytest.raises(checker.CheckFailure, match="connector-free"):
        _handler_check(text)

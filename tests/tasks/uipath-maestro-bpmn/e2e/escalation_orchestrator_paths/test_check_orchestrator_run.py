"""check_orchestrator_run.py grades each path run's Slack post and named outputs.

`fixtures/Process.bpmn` and `fixtures/run_seed.json` are the agent's process and
the seed from Studio Web run adhoc-2026-11-17_15-00-15 (passed): a classify
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
from types import SimpleNamespace

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
old = _load("old_check_escalation_orchestrator_paths", HERE.parents[1] / "_shared" / "check_escalation_orchestrator_paths.py")

BPMN = FIXTURES / "Process.bpmn"
SEED = json.loads((FIXTURES / "run_seed.json").read_text())
PROCESS = checker.load_process(BPMN)
SLACK = checker.slack_ids(PROCESS)


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


def _variables(case, *, ts="1763405123.456789", text=None, message_id=None, shared_node=False, **overrides):
    expected = {**case["expected"], **overrides}
    corr = case["inputs"]["correlationId"]
    text = text if text is not None else f"[{expected['escalationPath']}] {corr}"
    response = {"ok": True, "channel": "C0B2FDZD1M3", "ts": ts, "message": {"text": text}}
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
                    {"ElementId": "classify", "Outputs": {"Response": {k: expected[k] for k in old.CLASSIFICATION_FIELDS}}},
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
    ["draft", "Draft response", True, "Needs draft", "Draft for engineering", "Draft, no edits required",
     "Draft ready, not sent", "Draft - no review needed"],
)
def test_a_draft_response_mode_is_read_by_meaning(value):
    case = SEED["cases"][0]
    assert checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, responseMode=value))


def test_sev3_needs_no_draft_response():
    """Simona's prompt (2026-11-19): a draft response only when engineering is needed."""
    case = next(c for c in SEED["cases"] if c["expected"]["severity"] == "Sev3")
    assert checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, responseMode="none"))
    with pytest.raises(checker.CheckFailure, match="responseMode"):
        checker.verify_case(PROCESS, SLACK, case, _debug(case), _variables(case, responseMode="Draft"))


@pytest.mark.parametrize(
    "value",
    ["No draft", "NoDraft", "no_draft", "no-draft", "Draft not needed", "Not applicable", "N/A",
     "No response needed", "none", "Draft: none", "none (draft not required)", "Do not draft",
     "Don't draft", "Without a draft", "Draft: false", False],
)
def test_a_negated_response_mode_reads_as_none(value):
    triage = next(c for c in SEED["cases"] if c["expected"]["escalationPath"] == "duplicate")
    assert checker.verify_case(PROCESS, SLACK, triage, _debug(triage), _variables(triage, responseMode=value))
    sev1 = SEED["cases"][0]
    with pytest.raises(checker.CheckFailure, match="responseMode"):
        checker.verify_case(PROCESS, SLACK, sev1, _debug(sev1), _variables(sev1, responseMode=value))


@pytest.mark.parametrize("value", ["", "   ", "maybe", "pending"])
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


def test_one_slack_step_for_both_paths_passes_where_the_old_grader_failed(tmp_path, monkeypatch):
    """A single Slack step whose text depends on the path is a correct layout.
    The old grader required escalation and triage to post through two
    different Slack steps (and one gateway, two end events)."""
    cases = SEED["cases"]
    for case in cases:
        checker.verify_case(PROCESS, SLACK, case, _debug(case, shared_node=True), _variables(case, shared_node=True))

    project = tmp_path / "CustomerEscalationOrchestrator" / "CustomerEscalationOrchestrator"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text('{"Name": "CustomerEscalationOrchestrator"}')
    (project / "Process.bpmn").write_text(BPMN.read_text())
    (tmp_path / "seed.json").write_text(json.dumps(SEED))
    monkeypatch.chdir(tmp_path)
    current = iter(cases)
    state = {}

    def fake_debug(*a, **k):
        state["case"] = next(current)
        return _debug(state["case"], shared_node=True), "inst"

    def fake_cli(argv, **k):
        payload = {"Result": "Success", "Data": _variables(state["case"], shared_node=True)}
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(old, "import_exact", lambda bpmn, project_dir, solution: project_dir)
    monkeypatch.setattr(old, "run_debug", fake_debug)
    monkeypatch.setattr(old, "run_cli", fake_cli)
    with pytest.raises(old.CheckFailure, match="SAME Slack sendTask"):
        old.main()


def test_main_runs_every_case(tmp_path, monkeypatch):
    project = tmp_path / "CustomerEscalationOrchestrator" / "CustomerEscalationOrchestrator"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text('{"Name": "CustomerEscalationOrchestrator"}')
    (project / "Process.bpmn").write_text(BPMN.read_text())
    (tmp_path / "seed.json").write_text(json.dumps(SEED))
    monkeypatch.chdir(tmp_path)
    sent = []
    state = {}

    def fake_debug(project_dir, inputs, log, **k):
        state["case"] = next(c for c in SEED["cases"] if c["inputs"] == inputs)
        sent.append(inputs)
        return _debug(state["case"]), "inst"

    monkeypatch.setattr(checker, "import_exact", lambda bpmn, project_dir, solution: project_dir)
    monkeypatch.setattr(checker, "run_debug", fake_debug)
    monkeypatch.setattr(checker, "fetch_variables", lambda i: (_variables(state["case"]), ""))
    checker.cases()
    assert sent == [c["inputs"] for c in SEED["cases"]]


def test_slack_failure_advisory_accepts_the_real_process(tmp_path, monkeypatch):
    project = tmp_path / "CustomerEscalationOrchestrator" / "CustomerEscalationOrchestrator"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text('{"Name": "CustomerEscalationOrchestrator"}')
    (project / "Process.bpmn").write_text(BPMN.read_text())
    monkeypatch.chdir(tmp_path)
    checker.slack_failure_handled()

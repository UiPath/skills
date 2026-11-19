"""Unit tests for the CustomerEscalationOrchestrator effects grader.

Two layouts, both cut down from real agent builds: the two-branch flow
nightly runs produced (classify Script, Decision, one Slack node and one End
per branch) and a single-Slack-node flow. The classify script is one a
nightly agent wrote (it copies the match input into a local `match` and
lowercases it). Payloads have the shape
`uip maestro flow debug --output json` returns: `elementExecutions`, the
declared outputs in `variables.globals`, and each Slack send's response under
`<id>.output` (`ts`, `channel`, `message.text`).
"""

from __future__ import annotations

import importlib.util
import json
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CHANNEL = "C0B2FDZD1M3"

NIGHTLY_SCRIPT = """
  const domain = String($vars.start.output.senderDomain ?? "").trim();
  const match = String($vars.start.output.customerMatchStatus ?? "").trim().toLowerCase();
  const isTrue = (b) => b === true || String(b).toLowerCase() === "true";
  const duplicate = isTrue($vars.start.output.isDuplicate);
  let escalationPath = "escalation";
  if (domain === "") escalationPath = "missing_domain";
  else if (match === "none") escalationPath = "unknown_customer";
  else if (match === "multiple") escalationPath = "multiple_matches";
  else if (duplicate) escalationPath = "duplicate";
  return { escalationPath, responseMode: escalationPath === "escalation" ? "Draft" : "None" };
"""


def _module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grader():
    return _module("check_escalation_orchestrator_paths",
                   os.path.join(HERE, "check_escalation_orchestrator_paths.py"))


def _seed_cases():
    return _module("orchestrator_seed", os.path.join(HERE, "_setup", "seed.py")).build_seed()["cases"]


def _slack_node(node_id: str) -> dict:
    return {
        "id": node_id,
        "type": "uipath.connector.uipath-salesforce-slack.send-message-to-channel",
        "inputs": {
            "detail": {
                "connector": "uipath-salesforce-slack",
                "connectionId": "849e85d8-1aa9-4d52-8bbd-20041c8f05d8",
                "connectionFolderKey": "5da18ec0-7de1-4e57-aaf1-ddc8a369c199",
                "bodyParameters": {"channel": CHANNEL, "messageToSend": "=js:$vars.classify.output.message"},
            }
        },
    }


# Names a v3 agent might pick from the business prompt.
INS = [("fromAddress", "string"), ("senderDomain", "string"), ("emailSubject", "string"),
       ("emailBody", "string"), ("customerTier", "string"), ("productionDown", "boolean"),
       ("hasWorkaround", "boolean"), ("hasAttachments", "boolean"), ("customerMatchStatus", "string"),
       ("isDuplicate", "boolean"), ("caseReference", "string")]
OUTS = ["route", "severity", "needsEngineering", "responseMode", "caseRef", "slackMessageId"]


def _flow(nodes, ins=INS, script=NIGHTLY_SCRIPT) -> dict:
    nodes = [{**n, "inputs": {"script": script}} if n["type"] == "core.action.script" else n for n in nodes]
    return {
        "nodes": nodes,
        "edges": [],
        "variables": {"globals": [
            *({"id": i, "direction": "in", "type": t, "triggerNodeId": "start"} for i, t in ins),
            *({"id": o, "direction": "out", "type": "boolean" if o == "needsEngineering" else "string"}
              for o in OUTS),
        ]},
    }


TWO_BRANCH = [
    {"id": "start", "type": "core.trigger.manual"},
    {"id": "classify", "type": "core.action.script"},
    {"id": "isEscalation", "type": "core.logic.decision"},
    _slack_node("escalationAlert"),
    {"id": "endEscalation", "type": "core.control.end"},
    _slack_node("triageNotice"),
    {"id": "endTriage", "type": "core.control.end"},
]
ONE_SLACK = [
    {"id": "start", "type": "core.trigger.manual"},
    {"id": "classify", "type": "core.action.script"},
    _slack_node("notify"),
    {"id": "end", "type": "core.control.end"},
]


def _write_project(root, flow) -> None:
    project = root / "CustomerEscalationOrchestrator" / "CustomerEscalationOrchestrator"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(
        json.dumps({"Name": "CustomerEscalationOrchestrator", "ProjectType": "Flow"})
    )
    (project / "new.flow").write_text(json.dumps(flow))


def _results(case: dict, *, response_mode: str | None = None) -> dict:
    want = case["expected"]
    mode = want["responseMode"] if isinstance(want["responseMode"], str) else want["responseMode"][0]
    return {"route": want["path"], "severity": want["severity"], "needsEngineering": want["engineering"],
            "responseMode": response_mode or mode, "caseRef": case["inputs"]["caseRef"]}


def _payload(case: dict, sends: list[str], ts: str, *, path_in_text=None, executed=(), results=None) -> dict:
    ref = case["inputs"]["caseRef"]
    path = path_in_text or case["expected"]["path"].replace("_", " ")
    globals_ = {**(results or _results(case)), "slackMessageId": ts}
    for i, nid in enumerate(sends):
        sent = ts if i == 0 else f"{ts[:-1]}9"
        globals_[f"{nid}.output"] = {"ok": True, "channel": CHANNEL, "ts": sent,
                                     "message": {"type": "message", "ts": sent,
                                                 "text": f"{path.title()} for case {ref}"}}
    return {
        "finalStatus": "Completed",
        "elementExecutions": [{"elementId": i, "status": "Completed"} for i in [*executed, *sends]],
        "variables": {"globals": globals_},
    }


def _two_branch_payload(case: dict, n: int, **kw) -> dict:
    escalation = case["expected"]["path"] == "escalation"
    send, end = ("escalationAlert", "endEscalation") if escalation else ("triageNotice", "endTriage")
    return _payload(case, [send], f"17866475{n:02d}.771239",
                    executed=("start", "classify", "isEscalation", end), **kw)


def _one_slack_payload(case: dict, n: int, **kw) -> dict:
    return _payload(case, ["notify"], f"17866475{n:02d}.771239", executed=("start", "classify", "end"), **kw)


# ── The seed against the prompt's rules ──────────────────────────────────


def _v3_rules(inputs: dict) -> tuple[str, str, bool]:
    """The prompt's path order and severity, written out independently."""
    if not inputs["senderDomain"]:
        path = "missing_domain"
    elif inputs["match"] == "none":
        path = "unknown_customer"
    elif inputs["match"] == "several":
        path = "multiple_matches"
    elif inputs["duplicate"]:
        path = "duplicate"
    else:
        path = "escalation"
    if path != "escalation":
        return path, "informational", False
    if inputs["productionDown"]:
        severity = "Sev2" if inputs["workaround"] else "Sev1"
    else:
        severity = "Sev3"
    return path, severity, severity in ("Sev1", "Sev2")


def test_every_seeded_case_expects_what_the_v3_rules_give():
    for case in _seed_cases():
        want = case["expected"]
        assert (want["path"], want["severity"], want["engineering"]) == _v3_rules(case["inputs"]), case["name"]
        modes = [want["responseMode"]] if isinstance(want["responseMode"], str) else want["responseMode"]
        assert ("Draft" in modes) == (want["path"] == "escalation"), case["name"]


def test_each_triage_case_also_meets_every_later_condition():
    """So only the prompt's order picks the right path."""
    later = {
        "missing_domain": lambda i: i["match"] == "none" and i["duplicate"],
        "unknown_customer": lambda i: i["duplicate"],
        "multiple_matches": lambda i: i["duplicate"],
        "duplicate": lambda i: i["productionDown"] and not i["workaround"],
    }
    cases = {c["expected"]["path"]: c for c in _seed_cases() if c["expected"]["path"] != "escalation"}
    assert set(cases) == set(later)
    for path, condition in later.items():
        assert condition(cases[path]["inputs"]), path
    assert "@" not in cases["missing_domain"]["inputs"]["senderEmail"]


def test_severity_cases_show_the_tier_is_ignored():
    by_severity = {c["expected"]["severity"]: c["inputs"]["tier"] for c in _seed_cases()
                   if c["expected"]["path"] == "escalation"}
    assert by_severity["Sev1"] != "Enterprise" and by_severity["Sev3"] == "Enterprise"


# ── Feeding the agent's inputs ──────────────────────────────────────────────


def test_the_match_vocabulary_is_read_from_the_flows_comparisons():
    grader = _grader()
    assert grader.match_words(_flow(TWO_BRANCH)) == {"one": "one", "none": "none", "several": "multiple"}
    other = NIGHTLY_SCRIPT.replace('"none"', '"no_match"').replace('"multiple"', '"ambiguous"')
    assert grader.match_words(_flow(TWO_BRANCH, script=other)) == {
        "one": "one", "none": "no_match", "several": "ambiguous"}


def test_the_match_vocabulary_is_read_by_the_words_of_each_literal():
    """Spellings no fixed list holds are classed by their words, and an input
    whose name means the match is found by `flow_io_roles`, not a regex."""
    script = (NIGHTLY_SCRIPT.replace("customerMatchStatus", "senderMatchedCustomers")
              .replace('"none"', '"NO_CUSTOMER_FOUND"').replace('"multiple"', '"MORE_THAN_ONE"')
              .replace('let escalationPath', 'if (match === "EXACTLY_ONE") {}\n  let escalationPath'))
    ins = [("senderMatchedCustomers", "string") if i == "customerMatchStatus" else (i, t) for i, t in INS]
    assert _grader().match_words(_flow(TWO_BRANCH, ins=ins, script=script)) == {
        "one": "EXACTLY_ONE", "none": "NO_CUSTOMER_FOUND", "several": "MORE_THAN_ONE"}


# A classify Script an agent wrote, cut to the match handling: membership in a
# list, no `===` on the match.
MEMBERSHIP_SCRIPT = """
  const s = $vars.start.output;
  const domain = String(s.senderDomain ?? "").trim();
  const match = String(s.match ?? "").trim().toLowerCase();
  const noMatch = ["none", "no", "zero", "0", ""].indexOf(match) >= 0;
  const severalMatches = ["several", "multiple", "many"].indexOf(match) >= 0 || Number(match) > 1;

  let path;
  if (!domain) path = "missing_domain";
  else if (noMatch) path = "unknown_customer";
  else if (severalMatches) path = "multiple_matches";
  else if (s.duplicate === true) path = "duplicate";
  else path = "escalation";
  return { path };
"""


@pytest.mark.parametrize("seed", ["0", "1", "2", "3"])
def test_the_match_vocabulary_is_read_from_a_membership_list_not_the_path_it_sets(seed):
    """The run fed "multiple_matches" (the path) as the match input under one
    hash seed, so the flow took the duplicate path; under others it fed "several"."""
    import subprocess
    import sys

    ins = [("match", "string") if i == "customerMatchStatus" else (i, t) for i, t in INS]
    flow = _flow(TWO_BRANCH, ins=ins, script=MEMBERSHIP_SCRIPT)
    code = (
        "import importlib.util, json, sys\n"
        f"spec = importlib.util.spec_from_file_location('g', {os.path.join(HERE, 'check_escalation_orchestrator_paths.py')!r})\n"
        "g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)\n"
        "print(json.dumps(g.match_words(json.loads(sys.stdin.read()))))\n"
    )
    out = subprocess.run([sys.executable, "-c", code], input=json.dumps(flow), capture_output=True,
                         text=True, check=True, env={**os.environ, "PYTHONHASHSEED": seed})
    assert json.loads(out.stdout) == {"one": "one", "none": "none", "several": "several"}


SWITCH_SCRIPT = """
  const s = String($vars.start.output.customerMatchStatus ?? "").toLowerCase();
  let responseMode = 'None';
  switch (s) {
    case 'none': break;
    case 'several': break;
    default: break;
  }
  return { responseMode };
"""


def test_a_switch_on_the_match_input_names_its_states_by_its_case_labels():
    assert _grader().match_words(_flow(TWO_BRANCH, script=SWITCH_SCRIPT)) == {
        "one": "one", "none": "none", "several": "several"}


def test_a_state_with_no_compared_literal_gets_the_prompts_word():
    script = 'let m = $vars.start.output.customerMatchStatus; const r = m ? { mode: "None" } : {};'
    assert _grader().match_words(_flow(TWO_BRANCH, script=script)) == {
        "one": "one", "none": "none", "several": "several"}


def test_the_match_vocabulary_falls_back_to_the_inputs_description():
    flow = _flow(TWO_BRANCH, script="return {};")
    var = next(v for v in flow["variables"]["globals"] if v["id"] == "customerMatchStatus")
    var["description"] = "How the sender matched: matched, unmatched or several"
    assert _grader().match_words(flow) == {"one": "matched", "none": "unmatched", "several": "several"}


def test_seeded_values_map_onto_the_agents_inputs():
    grader = _grader()
    flow = _flow(TWO_BRANCH)
    case = next(c for c in _seed_cases() if c["expected"]["path"] == "multiple_matches")
    inputs = grader.feed(flow, case, grader.match_words(flow))
    assert inputs == {
        "fromAddress": "jane.doe@acmecorp.com", "senderDomain": "acmecorp.com", "emailSubject": "Prod down",
        "emailBody": "urgent", "customerTier": "Standard", "productionDown": True, "hasWorkaround": False,
        "hasAttachments": False, "customerMatchStatus": "multiple", "isDuplicate": True,
        "caseReference": case["inputs"]["caseRef"],
    }


@pytest.mark.parametrize("var,var_type,expected", [
    ("matchCount", "number", {"one": 1, "none": 0, "several": 2}),
    ("hasMultipleMatches", "boolean", {"one": False, "none": False, "several": True}),
    ("customerMatched", "boolean", {"one": True, "none": False, "several": True}),
])
def test_a_numeric_or_yes_no_match_input_gets_the_state_in_its_type(var, var_type, expected):
    grader = _grader()
    ins = [(var, var_type) if i == "customerMatchStatus" else (i, t) for i, t in INS]
    flow = _flow(TWO_BRANCH, ins=ins)
    base = _seed_cases()[0]
    got = {state: grader.feed(flow, {**base, "inputs": {**base["inputs"], "match": state}},
                              grader.match_words(flow))[var] for state in expected}
    assert got == expected


def test_a_flow_without_a_duplicate_input_fails_naming_its_inputs():
    flow = _flow(TWO_BRANCH, ins=[(i, t) for i, t in INS if i != "isDuplicate"])
    with pytest.raises(SystemExit) as exc:
        _grader().feed(flow, _seed_cases()[0], {"one": "single", "none": "none", "several": "multiple"})
    assert "could not map duplicate onto inputs ['fromAddress'" in str(exc.value)


# ── Checking each run ───────────────────────────────────────────────────────


@pytest.mark.parametrize("nodes,build", [(TWO_BRANCH, _two_branch_payload), (ONE_SLACK, _one_slack_payload)],
                         ids=["two-branch", "one-slack-node"])
def test_main_passes_every_seeded_case_on_either_layout(tmp_path, monkeypatch, nodes, build):
    _write_project(tmp_path, _flow(nodes))
    monkeypatch.chdir(tmp_path)
    cases = _seed_cases()
    (tmp_path / "seed.json").write_text(json.dumps({"cases": cases}))
    payloads = iter([build(c, n) for n, c in enumerate(cases)])
    grader = _grader()
    fed = []

    def fake_debug(**kwargs):
        fed.append(kwargs["inputs"])
        return next(payloads)

    monkeypatch.setattr(grader, "run_debug", fake_debug)
    grader.main()
    assert [f["customerMatchStatus"] for f in fed] == ["one", "one", "one", "one",
                                                       "multiple", "none", "none"]


@pytest.fixture
def two_branch(tmp_path, monkeypatch):
    flow = _flow(TWO_BRANCH)
    _write_project(tmp_path, flow)
    monkeypatch.chdir(tmp_path)
    return flow, {c["expected"]["path"] + "/" + c["expected"]["severity"]: c for c in _seed_cases()}


def test_sev3_may_answer_draft_or_none(two_branch):
    flow, cases = two_branch
    case = cases["escalation/Sev3"]
    for mode in ("Draft", "None"):
        _grader().check_case(flow, _two_branch_payload(case, 1, results=_results(case, response_mode=mode)), case)


def test_fails_when_a_triage_path_drafts_a_response(two_branch):
    flow, cases = two_branch
    case = cases["duplicate/informational"]
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(flow, _two_branch_payload(case, 1, results=_results(case, response_mode="Draft")),
                             case)
    assert "no declared output is 'None' (response mode)" in str(exc.value)


def test_fails_when_the_path_order_is_wrong(two_branch):
    # No domain, no match and a duplicate: the domain check comes first.
    flow, cases = two_branch
    case = cases["missing_domain/informational"]
    wrong = {**case, "expected": {**case["expected"], "path": "unknown_customer"}}
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(flow, _two_branch_payload(wrong, 1), case)
    assert "no declared output is 'missing_domain' (path)" in str(exc.value)


def test_fails_when_a_case_posts_both_the_alert_and_the_notice(two_branch):
    flow, cases = two_branch
    case = cases["duplicate/informational"]
    payload = _payload(case, ["triageNotice", "escalationAlert"], "1786647501.771239",
                       executed=("start", "classify", "isEscalation", "endTriage"))
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(flow, payload, case)
    assert "2 Slack messages posted" in str(exc.value)


def test_fails_when_one_send_posts_twice(two_branch):
    """A send inside a loop completes twice: one send node, two messages."""
    flow, cases = two_branch
    case = cases["escalation/Sev1"]
    payload = _two_branch_payload(case, 1)
    payload["elementExecutions"].append({"elementId": "escalationAlert", "status": "Completed"})
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(flow, payload, case)
    assert "2 Slack messages posted by ['escalationAlert']" in str(exc.value)


def test_fails_when_the_message_does_not_name_the_path(two_branch):
    flow, cases = two_branch
    case = cases["unknown_customer/informational"]
    payload = _two_branch_payload(case, 1, path_in_text="triage notice")
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(flow, payload, case)
    assert "unknown_customer" in str(exc.value)


def test_fails_when_no_slack_send_ran(two_branch):
    flow, cases = two_branch
    case = cases["escalation/Sev2"]
    payload = _two_branch_payload(case, 1)
    payload["elementExecutions"] = [e for e in payload["elementExecutions"] if e["elementId"] != "escalationAlert"]
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(flow, payload, case)
    assert "no uipath-salesforce-slack node completed" in str(exc.value)


def test_fails_when_a_constant_fits_only_some_cases():
    per_case = [{"severity": ["severity"]}, {"severity": ["lastSeverity"]}]
    with pytest.raises(SystemExit) as exc:
        _grader().check_same_outputs(per_case)
    assert "no single output holds the severity in every case" in str(exc.value)

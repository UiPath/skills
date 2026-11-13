"""Regex graders from the BPMN v1/v2 neutrality pass, exercised the way the grader runs them.

Each criterion below is a regex over a Bash call or over diagnosis.md, so each gets
the false-positive and false-negative discipline `test_fault_triage_mock_read_pattern.py`
gives the fault-triage guard: correct v1 work (raw XML skill, root `X.bpmn`) and correct
v2 work (builder SDK, `X/X.bpmn`) must pass, and the shapes each pattern exists to catch
must not.

Command patterns are matched the way `CommandExecutedChecker` matches them: against the
raw command and its shell-normalized form, using the port of coder_eval's
`_match_haystacks` in `test_fault_triage_mock_read_pattern.py` (loaded by path, so the
two files share one port). The cases are real agent commands wherever a run produced
one (R14/R15 `adhoc-2026-11-07_01-31-01` / `_01-31-33`, and a codex smoke run).
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_SHARED = Path(__file__).resolve().parent
_SUITE = _SHARED.parent


def _load_port():
    spec = importlib.util.spec_from_file_location(
        "fault_triage_port", _SHARED / "test_fault_triage_mock_read_pattern.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_match_haystacks = _load_port()._match_haystacks


def _criteria(task: str) -> list[dict]:
    return yaml.safe_load((_SUITE / task).read_text(encoding="utf-8"))["success_criteria"]


def _pattern(task: str, description_part: str) -> re.Pattern[str]:
    found = [
        c["command_pattern"]
        for c in _criteria(task)
        if "command_pattern" in c and description_part in c["description"]
    ]
    assert len(found) == 1, f"{task}: expected one criterion matching {description_part!r}, got {len(found)}"
    return re.compile(found[0], re.DOTALL)


def _hits(pattern: re.Pattern[str], command: str) -> bool:
    return any(pattern.search(h) for h in _match_haystacks(command))


# --- timer_start: the well-formed-XML check --------------------------------------

_TIMER = "single_node/timer_start/timer_start.yaml"

TIMER_PARSES = [
    # The prompt's former example, verbatim from R14/R15 v1 and R15 v2.
    "python3 -c \"import xml.etree.ElementTree as ET, pathlib; "
    "ET.parse(next(pathlib.Path('.').rglob('ScheduledReportBpmn.bpmn')))\"",
    # R14 v2: globbed into a variable, so the name comes before ET.parse.
    "python3 -c \"import xml.etree.ElementTree as ET, pathlib; "
    "fs=list(pathlib.Path('.').rglob('ScheduledReportBpmn.bpmn')); print(fs); "
    "ET.parse(fs[0]); print('well-formed')\"; find . -name '*.bpmn'",
    # The argv form: the file after the closing quote.
    "python3 -c \"import sys, xml.etree.ElementTree as ET; ET.parse(sys.argv[1])\" "
    "ScheduledReportBpmn/ScheduledReportBpmn.bpmn",
    "python3 -c 'import sys, xml.etree.ElementTree as ET; ET.parse(sys.argv[1]); print(\"ok\")' "
    "ScheduledReportBpmnSolution/ScheduledReportBpmn/ScheduledReportBpmn.bpmn && echo done",
    # An escaped inner quote does not end the program.
    "python3 -c \"import xml.etree.ElementTree as ET; ET.parse(\\\"ScheduledReportBpmn.bpmn\\\")\"",
    # The codex shell tool wraps every command in `/bin/bash -lc "..."`.
    "/bin/bash -lc \"python3 -c \\\"import xml.etree.ElementTree as ET, pathlib; "
    "ET.parse(next(pathlib.Path('.').rglob('ScheduledReportBpmn.bpmn')))\\\"\"",
    "/bin/bash -lc \"python3 -c \\\"import sys, xml.etree.ElementTree as ET; "
    "ET.parse(sys.argv[1])\\\" ScheduledReportBpmn/ScheduledReportBpmn.bpmn\"",
    # A heredoc program, the shape agents use for longer checks (R15).
    "python3 - <<'PY'\nimport pathlib, xml.etree.ElementTree as ET\n"
    "p = next(pathlib.Path('.').rglob('ScheduledReportBpmn.bpmn'))\nr = ET.parse(p).getroot()\nPY",
    "python3 - ScheduledReportBpmn/ScheduledReportBpmn.bpmn <<'EOF'\n"
    "import sys, xml.etree.ElementTree as ET\nET.parse(sys.argv[1])\nEOF",
]

TIMER_NOT_PARSES = [
    # No parse at all.
    "uip maestro bpmn validate ScheduledReportBpmn/ScheduledReportBpmn.bpmn --output json",
    "xmllint --noout ScheduledReportBpmn/ScheduledReportBpmn.bpmn",
    # A parse of something else; the name only in a LATER, unrelated command.
    "python3 -c \"import xml.etree.ElementTree as ET; ET.parse('other.bpmn')\"; "
    "find . -name ScheduledReportBpmn.bpmn",
    "python3 -c 'import xml.etree.ElementTree as ET; ET.parse(\"other.bpmn\")'\n"
    "ls ScheduledReportBpmn/ScheduledReportBpmn.bpmn",
    "python3 - <<'PY'\nimport xml.etree.ElementTree as ET\nET.parse('other.bpmn')\nPY\n"
    "ls ScheduledReportBpmn/ScheduledReportBpmn.bpmn",
    # The name in the program, but no ET.parse anywhere in it.
    "python3 -c \"print(open('ScheduledReportBpmn/ScheduledReportBpmn.bpmn').read()[:200])\"",
]


@pytest.mark.parametrize("command", TIMER_PARSES)
def test_timer_xml_check_counts_a_parse_of_the_file(command: str) -> None:
    assert _hits(_pattern(_TIMER, "well-formed-XML"), command), command


@pytest.mark.parametrize("command", TIMER_NOT_PARSES)
def test_timer_xml_check_ignores_anything_else(command: str) -> None:
    assert not _hits(_pattern(_TIMER, "well-formed-XML"), command), command


def test_timer_prompt_no_longer_spells_out_the_command() -> None:
    task = yaml.safe_load((_SUITE / _TIMER).read_text(encoding="utf-8"))
    prompt = task["initial_prompt"]
    assert "rglob(" not in prompt, "the prompt hands the agent the graded command again"
    assert prompt.count("Author the node from that template") == 0
    assert "xml.etree.ElementTree" in prompt, "the prompt must still name the parser the grader expects"


# --- simulation_crud: `$VAR` aliases bound to their definition ---------------------

_SIM = "evaluate/simulation/simulation_crud.yaml"

SIM_STATIC_CREATED = [
    'uip maestro bpmn eval simulation add connectorSendEmail --set "Sim Set" --data-point $DP '
    "--strategy Static --component-type connector --mock-value '{\"status\":\"ok\"}' --output json",
    'uip maestro bpmn eval simulations create connectorSendEmail --set "Sim Set" --data-point hello '
    "--strategy Static --component-type connector --mock-value '{}' --path SimEvalSolution/SimEval",
    # R14 v2, verbatim shape: the prefix held in a variable.
    'cd SimEval; E="uip maestro bpmn eval"; A=\'--path SimEval --set "Sim Set" --output json\'\n'
    '$E simulations create connectorSendEmail --path SimEval --set "Sim Set" --data-point hello '
    "--strategy Static --component-type connector --mock-value '{}'",
    "EVAL='uip maestro bpmn eval'; ${EVAL} simulation add x --strategy Static --mock-value '{}'",
    'export E="$UIP maestro bpmn eval"; $E simulations add x --strategy Static --mock-value 1',
]

SIM_STATIC_NOT_CREATED = [
    # Any variable, as long as the prefix appears somewhere, is not the eval prefix.
    "uip maestro bpmn eval sets list --path SimEval; $HOME simulations add x --strategy Static --mock-value 1",
    # A variable defined as something else, used as if it were the eval prefix.
    'E="uip maestro bpmn eval"; F="echo"; $F simulations create x --strategy Static --mock-value 1',
    # The name must match whole: `$E` is not `$EVAL`.
    'E="uip maestro bpmn eval"; $EVAL simulations create x --strategy Static --mock-value 1',
    # A different strategy, or no mock value.
    "uip maestro bpmn eval simulations create x --strategy Llm --output-schema '{}'",
    "uip maestro bpmn eval simulations create x --strategy Static",
    # Help only.
    "uip maestro bpmn eval simulations create --help",
]


@pytest.mark.parametrize("command", SIM_STATIC_CREATED)
def test_sim_static_create_counts(command: str) -> None:
    assert _hits(_pattern(_SIM, "Static simulation was created"), command), command


@pytest.mark.parametrize("command", SIM_STATIC_NOT_CREATED)
def test_sim_static_create_rejects(command: str) -> None:
    assert not _hits(_pattern(_SIM, "Static simulation was created"), command), command


def test_sim_list_alias_is_bound_too() -> None:
    pattern = _pattern(_SIM, "Simulation-list telemetry")
    assert _hits(pattern, 'E="uip maestro bpmn eval"; $E simulations list --set "Sim Set" --data-point hello')
    assert _hits(pattern, 'uip maestro bpmn eval simulation list --set "Sim Set"')
    assert not _hits(pattern, 'uip maestro bpmn eval sets list; $PWD simulations list')


# --- stuck_gateway: the STUCK_REASON line and the mocks/ read guard ----------------

_STUCK = "diagnose/stuck_gateway/stuck_gateway.yaml"


def _stuck_check() -> dict:
    checks = [c for c in _criteria(_STUCK) if c["type"] == "file_check"]
    assert len(checks) == 1
    return checks[0]


def _diagnosis_passes(text: str) -> bool:
    check = _stuck_check()
    return all(n in text for n in check.get("includes", [])) and all(
        re.search(e["pattern"], text) for e in check.get("patterns", [])
    )


GOOD_DIAGNOSES = {
    "R14 v1": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: No outgoing condition matched at exclusive gateway Gw_ApprovalRoute and the "
        "gateway has no default flow, so the token cannot advance.\n"
    ),
    "R14 v2": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: Exclusive gateway Gw_ApprovalRoute is blocked because no outgoing condition "
        "matched (neither `vars.riskScore > 80` nor `vars.riskScore < 20` evaluated true) and the "
        "gateway has no default flow, so the token cannot advance.\n"
    ),
    "fixture wording": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: No outgoing sequence-flow condition evaluated true and no default flow is defined.\n"
    ),
    "both conditions false, default missing": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: Both outgoing conditions evaluated false and the default flow is missing.\n"
    ),
    "condition did not match": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: Each outgoing condition did not match the score, and the gateway lacks a default flow.\n"
    ),
    "conditions didn't evaluate true": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: The gateway's conditions didn't evaluate to true and there is no default sequence flow.\n"
    ),
    "without a default": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: none of the gateway's conditions matched, and it was modeled without a default sequence flow\n"
    ),
}

BAD_DIAGNOSES = {
    "default named only outside the reason line": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: The gateway is waiting.\n"
        "Add a default flow to fix it; no outgoing condition matched.\n"
    ),
    "reason omits the missing default": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: No outgoing condition matched.\n"
    ),
    "reason omits the conditions": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: The gateway has no default flow.\n"
    ),
    "a default exists, wrongly": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: The default flow was taken by mistake.\n"
    ),
    "wrong element": (
        "STUCK_ELEMENT: ServiceTask_Score\n"
        "STUCK_REASON: No outgoing condition matched and the gateway has no default flow.\n"
    ),
    # The "no" of "no default flow" must not stand in for the condition's negation:
    # these reasons say a condition DID match.
    "a condition matched, default missing": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: The condition riskScore > 80 is true but the token waits; there is no default flow.\n"
    ),
    "a condition matched, no default": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: There is no default flow, and the outgoing condition matched.\n"
    ),
    "conditions named without a verdict": (
        "STUCK_ELEMENT: Gw_ApprovalRoute\n"
        "STUCK_REASON: The gateway has two conditions and no default flow.\n"
    ),
}


@pytest.mark.parametrize("label", sorted(GOOD_DIAGNOSES))
def test_stuck_reason_accepts_a_correct_diagnosis(label: str) -> None:
    assert _diagnosis_passes(GOOD_DIAGNOSES[label]), label


@pytest.mark.parametrize("label", sorted(BAD_DIAGNOSES))
def test_stuck_reason_rejects_an_incomplete_one(label: str) -> None:
    assert not _diagnosis_passes(BAD_DIAGNOSES[label]), label


def test_stuck_gateway_reuses_the_fault_triage_read_guard() -> None:
    """One mock-read guard, two tasks: the fault-triage test exercises it for both."""

    def guard(task: str) -> str:
        found = [
            c["command_pattern"]
            for c in _criteria(task)
            if c["type"] == "command_executed"
            and c.get("max_count") == 0
            and "mocked inputs" in c["description"]
        ]
        assert len(found) == 1, task
        return found[0]

    assert guard(_STUCK) == guard("operate-diagnose/minimal_fault_triage.yaml")


@pytest.mark.parametrize("task", [_STUCK, "operate-diagnose/minimal_fault_triage.yaml"])
def test_reference_dir_tasks_declare_a_reference(task: str) -> None:
    """coder-eval skips a task whose criteria read $REFERENCE_DIR with no `reference:` block."""
    raw = yaml.safe_load((_SUITE / task).read_text(encoding="utf-8"))
    uses = any("$REFERENCE_DIR" in str(c.get("command", "")) for c in raw["success_criteria"])
    assert uses
    reference = (_SUITE / task).parent / raw["reference"]["directory"]
    assert (reference / "_shared" / "check_mock_calls.py").is_file()


# --- stuck_gateway and fault_triage: no shell write into the mock call log ----------

_FAULT_TRIAGE = "operate-diagnose/minimal_fault_triage.yaml"

CALL_LOG_WRITES = [
    # The forged line that satisfies every call-log row.
    (
        "echo '{\"args\":\"maestro bpmn instance cursors inst-triage-001 -f folder-public\","
        "\"matched_rule\":\"x\",\"exit_code\":0}' >> mocks/.calls.jsonl"
    ),
    "printf '%s\\n' \"$LINE\" > ./mocks/.calls.jsonl",
    "echo x | tee -a mocks/.calls.jsonl",
    "touch mocks/.calls.jsonl",
    "L=.calls.jsonl; echo x >> mocks/$L",
    "cat forged.jsonl >> \"mocks/log\"",
    "echo '{}' > /sandbox/mocks/manifest.json",
    "mv forged.jsonl mocks/",
    "dd if=forged of=mocks/.calls.jsonl",
]

CALL_LOG_SAFE = [
    "uip maestro bpmn instance cursors inst-triage-001 -f folder-public --output json > cursors.json",
    "uip maestro bpmn instance element-executions inst-triage-001 -f folder-public | tee exec.json",
    "echo 'STUCK_ELEMENT: Gw_ApprovalRoute' > diagnosis.md",
    "ls",
    "touch diagnosis.md",
]


@pytest.mark.parametrize("task", [_STUCK, _FAULT_TRIAGE])
@pytest.mark.parametrize("command", CALL_LOG_WRITES)
def test_call_log_write_guard_fires(task: str, command: str) -> None:
    assert _hits(_pattern(task, "mock call log"), command), command


@pytest.mark.parametrize("task", [_STUCK, _FAULT_TRIAGE])
@pytest.mark.parametrize("command", CALL_LOG_SAFE)
def test_call_log_write_guard_is_silent_on_normal_work(task: str, command: str) -> None:
    assert not _hits(_pattern(task, "mock call log"), command), command


def test_call_log_write_guard_is_one_pattern() -> None:
    assert _pattern(_STUCK, "mock call log").pattern == _pattern(_FAULT_TRIAGE, "mock call log").pattern


# --- lifecycle guards: switch, subprocess, terminate and the three e2e tasks ------

_PACK_FORBIDDEN = [
    "single_node/switch/switch.yaml",
    "single_node/subprocess/subprocess.yaml",
    "single_node/terminate/terminate.yaml",
]
_PACK_ALLOWED = [
    "e2e/invoice_exception_triage.yaml",
    "multi_node/customer_escalation/customer_escalation.yaml",
    "multi_node/wiki_pageviews/wiki_pageviews.yaml",
]

# One lifecycle pattern per variant. The six yamls carry a copy each (a yaml cannot
# import one); test_lifecycle_guards_share_one_pattern_per_variant keeps them equal,
# so a fix lands in all six or the suite fails.
_SOLUTION_CLOUD = (
    r"solution\s+(?:upload|publish|delete|packages\s+delete|projects\s+publish"
    r"|deploy\b(?!\s+(?:list|status|config\s+get)\b){pack})"
)
_NOT_HELP = r"\b(?![^\n;&|]*\s(?:--help|-h)\b)"
LIFECYCLE_GUARD_NO_PACK = (
    r"(?:\buip|\$UIP)\s+(?:maestro\s+bpmn\s+(?:upload|publish|deploy|debug|run|process\s+(?:run|publish))|"
    + _SOLUTION_CLOUD.format(pack="")
    + ")"
    + _NOT_HELP
)
LIFECYCLE_GUARD_WITH_PACK = (
    r"(?:\buip|\$UIP)\s+(?:maestro\s+bpmn\s+(?:upload|publish|deploy|debug|run|pack|process\s+(?:run|publish))|"
    + _SOLUTION_CLOUD.format(pack="|pack")
    + ")"
    + _NOT_HELP
)


@pytest.mark.parametrize(
    ("task", "expected"),
    [(t, LIFECYCLE_GUARD_WITH_PACK) for t in _PACK_FORBIDDEN]
    + [(t, LIFECYCLE_GUARD_NO_PACK) for t in _PACK_ALLOWED],
)
def test_lifecycle_guards_share_one_pattern_per_variant(task: str, expected: str) -> None:
    assert _pattern(task, "lifecycle command").pattern == expected, task


LIFECYCLE_RUNS = [
    "uip solution upload InvoiceSolution --output json",
    "cd X && uip maestro bpmn process run --process-key k --folder-key f",
    "uip maestro bpmn debug SeasonLookup.bpmn --output json",
    "uip solution deploy run --name x",
    "uip maestro bpmn process publish p",
    "$UIP solution publish ./pkg",
    # Cloud-side solution and process verbs.
    "uip solution projects publish ./S --output json",
    "uip solution delete InvoiceSolution",
    "uip solution packages delete InvoiceSolution --version 1.0.0",
    "uip solution deploy config set --name x --key k --value v",
    "uip solution deploy --name x",
]

LIFECYCLE_LOCAL = [
    "uip maestro bpmn validate SeasonLookup.bpmn --output json",
    "uip maestro bpmn check SeasonLookup.bpmn.ts --source && uip maestro bpmn compile SeasonLookup.bpmn.ts -o S/S.bpmn",
    "uip maestro bpmn format S/S.bpmn; uip maestro bpmn refresh S --output json",
    "uip maestro bpmn init SeasonLookup --output json",
    "uip maestro bpmn registry get BPMN.ScriptTask --output json",
    "uip maestro bpmn debug --help",
    "uip solution upload --help 2>&1 | head -20",
    "uip maestro bpmn process run -h",
    "uip solution resources list --search Invoice --output json",
    # Read-only deploy subcommands: a status read is not a deploy.
    "uip solution deploy status --name x --output json",
    "uip solution deploy list --output json",
    "uip solution deploy config get --name x",
    "uip solution projects list --output json",
]


@pytest.mark.parametrize("task", _PACK_FORBIDDEN + _PACK_ALLOWED)
@pytest.mark.parametrize("command", LIFECYCLE_RUNS)
def test_lifecycle_guard_fires(task: str, command: str) -> None:
    assert _hits(_pattern(task, "lifecycle command"), command), command


@pytest.mark.parametrize("task", _PACK_FORBIDDEN + _PACK_ALLOWED)
@pytest.mark.parametrize("command", LIFECYCLE_LOCAL)
def test_lifecycle_guard_is_silent_on_local_work(task: str, command: str) -> None:
    assert not _hits(_pattern(task, "lifecycle command"), command), command


@pytest.mark.parametrize("command", ["uip maestro bpmn pack S ./out --output json", "uip solution pack S ./out"])
def test_pack_counts_only_where_the_prompt_forbids_it(command: str) -> None:
    for task in _PACK_FORBIDDEN:
        assert _hits(_pattern(task, "lifecycle command"), command), task
    for task in _PACK_ALLOWED:
        assert not _hits(_pattern(task, "lifecycle command"), command), task


# --- draft-gate smokes: no registry lookup before approval -----------------------

_DRAFTS = ["smoke/draft_skeleton.yaml", "smoke/draft_skeleton_timer.yaml"]

PRE_GATE_LOOKUPS = [
    "uip maestro bpmn registry pull --output json",
    "uip maestro bpmn registry get BPMN.ScriptTask --output json",
    'uip maestro bpmn registry search "invoice" --output json',
    # The builder-SDK spellings.
    "uip maestro registry search 'approval' --limit 10",
    "uip maestro registry prepare uipath-uipath-http --action http-request --output json",
    "uip maestro registry describe uipath.connector.uipath-uipath-http.http-request --output json",
    "uip maestro registry pull",
]

PRE_GATE_ALLOWED = [
    # v1 phase 1a, verbatim from R15 v1: the box-kind preflight list.
    "uip login status --output json && uip maestro bpmn registry list --limit -1 --output json "
    "--output-filter \"ExtensionTypes[?!starts_with(ExtensionType,'Maestro.Case')]\"",
    "uip maestro registry search --help",
    "uip maestro bpmn validate InvoiceIntakeSketch/InvoiceIntakeSketch.bpmn --output json",
    "uip solution resources list --search Invoice --output json",
]


@pytest.mark.parametrize("task", _DRAFTS)
@pytest.mark.parametrize("command", PRE_GATE_LOOKUPS)
def test_draft_gate_guard_fires_on_a_registry_lookup(task: str, command: str) -> None:
    assert _hits(_pattern(task, "no registry discovery"), command), command


@pytest.mark.parametrize("task", _DRAFTS)
@pytest.mark.parametrize("command", PRE_GATE_ALLOWED)
def test_draft_gate_guard_allows_the_preflight(task: str, command: str) -> None:
    assert not _hits(_pattern(task, "no registry discovery"), command), command


@pytest.mark.parametrize(
    "command",
    [
        'uip solution resources list --kind Process --search "Record Invoice" --output json',
        'uip solution resources list --kind Process --search "invoice" --output json; '
        'uip solution resources list --kind App --search "approval" --output json',
        "uip is connections list --all-folders --output-filter "
        "\"[?contains(ConnectorName,'Slack')].{Connector:ConnectorName}\" --output json",
    ],
)
def test_draft_resource_lookup_counts(command: str) -> None:
    assert _hits(_pattern(_DRAFTS[0], "looked up the boxes' resources"), command), command


@pytest.mark.parametrize(
    "command",
    [
        "uip maestro bpmn validate InvoiceIntakeSketch/InvoiceIntakeSketch.bpmn --output json",
        "uip is connectors list --output json",
        "uip solution upload InvoiceIntakeSketchSolution --output json",
        "uip solution resources list --help",
        "uip is connections list -h",
    ],
)
def test_draft_resource_lookup_ignores_other_calls(command: str) -> None:
    assert not _hits(_pattern(_DRAFTS[0], "looked up the boxes' resources"), command), command


# --- query_params: the advisory connection-lookup row ---------------------------

_QP = "connector_features/query_params/query_params.yaml"


@pytest.mark.parametrize(
    "command",
    [
        "uip is connections list --all-folders --output json > /tmp/conns.json",
        "uip is connections list uipath-uipath-http --all-folders --output json",
        "uip is connections ping 1bf4e408-fff6-4382-a9a3-fd305038650c --output json",
        "uip maestro registry prepare uipath-uipath-http --action http-request --output json",
        "uip maestro registry describe uipath.connector.uipath-uipath-http.http-request --output json",
    ],
)
def test_query_params_lookup_counts(command: str) -> None:
    assert _hits(_pattern(_QP, "looked up connections"), command), command


@pytest.mark.parametrize(
    "command",
    [
        "uip maestro bpmn validate QueryParamsTest/QueryParamsTest.bpmn --output json",
        "uip is connectors list --output json",
        "uip maestro registry search 'google tasks'",
    ],
)
def test_query_params_lookup_ignores_other_calls(command: str) -> None:
    assert not _hits(_pattern(_QP, "looked up connections"), command), command


def test_query_params_judge_requires_the_lookup() -> None:
    judges = [c for c in _criteria(_QP) if c["type"] == "llm_judge"]
    assert len(judges) == 1
    prompt = judges[0]["prompt"]
    assert "BEFORE leaving the binding unbound" in prompt
    assert "without any connection lookup" in prompt


# --- check_bpmn_present.py --contains, which replaced root-pinned file_contains ---


def _present(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SHARED / "check_bpmn_present.py"), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("layout", ["TerminateParallel.bpmn", "TerminateParallel/TerminateParallel.bpmn"])
def test_present_contains_passes_either_layout(tmp_path: Path, layout: str) -> None:
    path = tmp_path / layout
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("<x><bpmn:terminateEventDefinition/><bpmndi:BPMNDiagram/></x>", encoding="utf-8")
    result = _present(
        tmp_path, "TerminateParallel", "--contains", "bpmndi:BPMNDiagram", "--contains", "terminateEventDefinition"
    )
    assert result.returncode == 0, result.stderr


def test_present_contains_fails_on_a_missing_needle(tmp_path: Path) -> None:
    (tmp_path / "TerminateParallel.bpmn").write_text("<x><bpmndi:BPMNDiagram/></x>", encoding="utf-8")
    result = _present(
        tmp_path, "TerminateParallel", "--contains", "bpmndi:BPMNDiagram", "--contains", "terminateEventDefinition"
    )
    assert result.returncode != 0
    assert "terminateEventDefinition" in result.stderr


@pytest.mark.parametrize("task", _PACK_FORBIDDEN)
def test_no_content_check_is_pinned_to_the_root_file(task: str) -> None:
    assert not [c for c in _criteria(task) if c["type"] == "file_contains"], task

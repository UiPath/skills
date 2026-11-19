"""Each path-to-ga prompt states, inside its helper block, the facts its grader
asserts: names and types, connections and folder, enum values, targets.

Facts come from the grader modules and seeds where they exist; the rest are
pinned literals here. Only the helper block is checked; the request text is not.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

SUITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SUITE))
sys.path.insert(0, str(SUITE / "_setup"))

import escalation_is  # noqa: E402
from _shared import bpmn_live  # noqa: E402

HELPER_START = "<!-- helper:start -->"
HELPER_END = "<!-- helper:end -->"
PATH_TO_GA_TAG = "path-to-ga"
SLACK_CHANNEL_NAME = "coding-agent-testing"
TYPE_NAMES = ((bool, "boolean"), (int, "number"), (float, "number"), (str, "string"))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _type_name(value) -> str:
    return next(name for kind, name in TYPE_NAMES if isinstance(value, kind))


def _types(values: dict) -> dict[str, str]:
    return {name: _type_name(value) for name, value in values.items()}


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


E2E = SUITE / "e2e"
orchestrator = _load("helper_facts_orchestrator", E2E / "escalation_orchestrator_paths" / "check_orchestrator_run.py")
orchestrator_seed = _load("helper_facts_orchestrator_seed", E2E / "escalation_orchestrator_paths" / "_setup" / "seed.py")
triage = _load("helper_facts_triage", E2E / "customer_escalation_triage" / "check_customer_escalation_behavior.py")
jira_is = _load("helper_facts_jira_is", E2E / "escalation_jira_ticket" / "_setup" / "jira_is.py")
invoice = _load("helper_facts_invoice", SUITE / "multi_node" / "billing_invoice_lookup" / "check_invoice_lookup_run.py")
product = _load("helper_facts_product", SUITE / "debug" / "live_debug_e2e" / "check_product_run.py")

ORCHESTRATOR_CASES = orchestrator_seed.build_seed()["cases"]
JIRA_SEED = _json(E2E / "escalation_jira_ticket" / "fixtures" / "run_seed.json")
SLACK_CASE = _json(E2E / "escalation_slack_alert" / "fixtures" / "run_seed.json")["cases"][0]
TRIAGE_INPUTS = {
    "customerTier": "Enterprise",
    "serviceState": "Unavailable",
    "workaroundAvailable": False,
    "correlationId": "x",
    "jiraProjectKey": escalation_is.PROJECT_KEY,
    "jiraIssueTypeId": "10001",
    "slackChannelId": escalation_is.SLACK_CHANNEL,
}
SEVERITY_VALUES = set(bpmn_live.SEVERITIES)
JIRA_CONNECTION = escalation_is.CONNECTION_NAMES[escalation_is.JIRA_CONNECTOR]
SLACK_CONNECTION = escalation_is.CONNECTION_NAMES[escalation_is.SLACK_CONNECTOR]


def _expected_values(cases: list[dict], name: str) -> set:
    return {case["expected"][name] for case in cases}


@dataclass(frozen=True)
class Facts:
    path: Path
    inputs: dict[str, str] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)
    enums: dict[str, set] = field(default_factory=dict)
    literals: tuple[str, ...] = ()


TASKS = {
    "escalation_orchestrator_paths": Facts(
        path=E2E / "escalation_orchestrator_paths" / "escalation_orchestrator_paths.yaml",
        inputs=_types(ORCHESTRATOR_CASES[0]["inputs"]),
        outputs={
            **{name: "string" for name in (*orchestrator.OUTPUTS, "slackMessageId")},
            **_types({k: ORCHESTRATOR_CASES[0]["expected"][k] for k in ("engineeringNeeded",)}),
        },
        enums={
            name: _expected_values(ORCHESTRATOR_CASES, name)
            for name in ("escalationPath", "severity", "responseMode")
        },
        literals=(
            SLACK_CONNECTION,
            escalation_is.FOLDER_PATH,
            SLACK_CHANNEL_NAME,
            escalation_is.SLACK_CHANNEL,
            "correlationId",
        ),
    ),
    "customer_escalation_triage": Facts(
        path=E2E / "customer_escalation_triage" / "customer_escalation_triage.yaml",
        inputs=_types(TRIAGE_INPUTS),
        outputs=dict(triage.OUTPUT_TYPES),
        enums={"severity": SEVERITY_VALUES},
        literals=(JIRA_CONNECTION, SLACK_CONNECTION, escalation_is.FOLDER_PATH, "correlationId"),
    ),
    "escalation_jira_ticket": Facts(
        path=E2E / "escalation_jira_ticket" / "escalation_jira_ticket.yaml",
        inputs=_types(JIRA_SEED["inputs"]),
        outputs={**_types(JIRA_SEED["expected"]), "jiraIssueKey": "string"},
        enums={"severity": SEVERITY_VALUES},
        literals=(
            JIRA_CONNECTION,
            escalation_is.FOLDER_PATH,
            f"project {jira_is.PROJECT_KEY}",
            f"issue type {jira_is.ISSUETYPE_NAME}",
            "correlationId",
        ),
    ),
    "escalation_slack_alert": Facts(
        path=E2E / "escalation_slack_alert" / "escalation_slack_alert.yaml",
        inputs=_types(SLACK_CASE["inputs"]),
        outputs={**_types(SLACK_CASE["expected"]), "slackMessageId": "string"},
        enums={"severity": SEVERITY_VALUES},
        literals=(
            SLACK_CONNECTION,
            escalation_is.FOLDER_PATH,
            SLACK_CHANNEL_NAME,
            escalation_is.SLACK_CHANNEL,
            "correlationId",
        ),
    ),
    "billing_invoice_lookup": Facts(
        path=SUITE / "multi_node" / "billing_invoice_lookup" / "billing_invoice_lookup.yaml",
        inputs={"invoiceNumber": "string"},
        outputs={
            "matchedInvoiceNumber": _type_name(invoice.CASES[0][1]),
            "lineItemCount": _type_name(invoice.CASES[0][2]),
        },
        literals=("BillingDisputeERP", "Shared"),
    ),
    "live_debug_e2e": Facts(
        path=SUITE / "debug" / "live_debug_e2e" / "live_debug_e2e.yaml",
        outputs={product.OUTPUT: _type_name(product.EXPECTED)},
        literals=("no inputs",),
    ),
}


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _prompt(path: Path) -> str:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["initial_prompt"]


def _helper(path: Path) -> str:
    prompt = _prompt(path)
    assert prompt.count(HELPER_START) == 1 and prompt.count(HELPER_END) == 1, path
    return _flat(prompt.split(HELPER_START)[1].split(HELPER_END)[0])


def test_every_path_to_ga_task_is_covered():
    tagged = {
        path.stem
        for path in SUITE.rglob("*.yaml")
        if PATH_TO_GA_TAG in (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("tags", [])
    }
    assert tagged == set(TASKS)


@pytest.mark.parametrize("task", TASKS)
def test_helper_types_every_input_and_output(task):
    helper = _helper(TASKS[task].path)
    for name, type_name in {**TASKS[task].inputs, **TASKS[task].outputs}.items():
        assert f"{name} ({type_name})" in helper, f"{name} ({type_name})"


@pytest.mark.parametrize("task", [name for name, facts in TASKS.items() if facts.enums])
def test_helper_states_exactly_the_asserted_values(task):
    helper = _helper(TASKS[task].path)
    for name, values in TASKS[task].enums.items():
        sentence = re.search(rf"\b{name} is ([^.]*)\.", helper)
        assert sentence, f"{name} values"
        assert set(re.findall(r'"([^"]+)"', sentence.group(1))) == values, name


@pytest.mark.parametrize("task", TASKS)
def test_helper_carries_the_targets_the_grader_binds(task):
    helper = _helper(TASKS[task].path)
    for literal in TASKS[task].literals:
        assert literal in helper, literal


def test_orchestrator_helper_states_both_response_modes_and_the_boolean():
    facts = TASKS["escalation_orchestrator_paths"]
    assert facts.enums["responseMode"] == {"Draft", "None"}
    assert facts.outputs["engineeringNeeded"] == "boolean"


GUARD = (
    "Do not delete or overwrite anything this run did not create, except what the task "
    "asks you to change, and do not publish to a shared destination unless the task asks for it."
)


@pytest.mark.parametrize("task", TASKS)
def test_the_opener_names_no_harness_and_carries_the_guard(task):
    path = next(SUITE.rglob(f"{task}.yaml"))
    opener = _flat(_prompt(path).split("\n\n")[0])
    assert opener.startswith("You are a coding agent in an empty Agentic Process (Maestro BPMN) project."), task
    assert "Studio Web" not in opener, task
    assert GUARD in opener, task

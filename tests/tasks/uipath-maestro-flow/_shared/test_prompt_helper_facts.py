"""Each path-to-ga prompt states, inside its helper block, the facts its grader
asserts: names and types, connections and folder, enum values, targets.

Facts come from the grader modules and seeds, so a prompt and its grader
cannot drift apart. Only the helper block is checked; the request text is not.
"""

from __future__ import annotations

import importlib.util
import inspect
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

SUITE = Path(__file__).resolve().parents[1]
HITL_SUITE = SUITE.parent / "uipath-human-in-the-loop"
sys.path.insert(0, str(SUITE))
sys.path.insert(0, str(SUITE / "_shared"))

from _shared import flow_io_roles as io  # noqa: E402
from _shared import jira_is  # noqa: E402
from _shared.escalation_inputs import KEYWORDS, SLACK_CHANNEL  # noqa: E402

HELPER_START = "<!-- helper:start -->"
HELPER_END = "<!-- helper:end -->"
PATH_TO_GA_TAG = "path-to-ga"
SLACK_CHANNEL_NAME = "coding-agent-testing"
SLACK_CONNECTION = "is-sandboxes"
TYPE_NAMES = ((bool, "boolean"), (int, "number"), (float, "number"), (str, "string"))
MULTI_NODE = SUITE / "multi_node"
E2E = SUITE / "e2e"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _type_name(value) -> str:
    return next(name for kind, name in TYPE_NAMES if isinstance(value, kind))


invoice = _load("helper_facts_invoice", MULTI_NODE / "billing_invoice_lookup" / "check_billing_invoice_lookup.py")
detector = _load("helper_facts_detector", MULTI_NODE / "billing_discrepancy_detector" / "check_billing_discrepancy_detector.py")
analyst = _load("helper_facts_analyst", MULTI_NODE / "billing_dispute_analyst" / "check_billing_dispute_analyst.py")
writer = _load("helper_facts_writer", MULTI_NODE / "billing_resolution_writer" / "check_billing_resolution_writer.py")
resolution = _load("helper_facts_resolution", MULTI_NODE / "billing_dispute_resolution" / "check_e2e_billing_dispute_resolution.py")
coded = _load("helper_facts_coded", SUITE / "single_node" / "coded_agent" / "check_coded_agent.py")
mcp = _load("helper_facts_mcp", SUITE / "inline_agent" / "inline_mcp_server_tool" / "check_inline_mcp_server_tool.py")
orchestrator = _load("helper_facts_orchestrator", E2E / "escalation_orchestrator_paths" / "check_escalation_orchestrator_paths.py")
orchestrator_seed = _load("helper_facts_orchestrator_seed", E2E / "escalation_orchestrator_paths" / "_setup" / "seed.py")
slack_seed = _load("helper_facts_slack_seed", E2E / "escalation_slack_alert" / "_setup" / "seed.py")
invoice_run = _load("helper_facts_invoice_run", SUITE / "_shared" / "check_hitl_invoice_approval_run.py")
expense_run = _load("helper_facts_expense_run", SUITE / "_shared" / "check_hitl_expense_apptask_run.py")

ORCHESTRATOR_CASES = orchestrator_seed.build_seed()["cases"]
SLACK_CASES = slack_seed.build_seed()["cases"]
ESCALATION_NAMES = {
    "senderEmail": "senderEmail",
    "senderDomain": "senderDomain",
    "subject": "subject",
    "body": "body",
    "tier": "customerTier",
    "productionDown": "productionDown",
    "workaround": "workaroundAvailable",
    "attachments": "hasAttachments",
    "match": "customerMatchStatus",
    "duplicate": "isDuplicate",
    "caseRef": "caseReference",
}
SLACK_BULLETS = "2 or 3 bullet lines"
SLACK_LITERALS = (SLACK_CONNECTION, jira_is.FOLDER_PATH, SLACK_CHANNEL_NAME, SLACK_CHANNEL)
SUBMISSION_FIELDS = {"account number": "accountNumber", "invoice number": "invoiceNumber"}


def _escalation_inputs(case: dict) -> dict[str, str]:
    return {ESCALATION_NAMES[role]: _type_name(value) for role, value in case["inputs"].items()}


def _role_names(roles: dict, names: dict[str, str]) -> dict[str, tuple[str, list[str]]]:
    return {name: (role, roles[role]["keywords"]) for role, name in names.items()}


def _expected_values(cases: list[dict], name: str) -> set:
    values = set()
    for case in cases:
        value = case["expected"][name]
        values |= set(value) if isinstance(value, list) else {value}
    return values


@dataclass(frozen=True)
class Facts:
    path: Path
    inputs: dict[str, str] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)
    enums: dict[str, set] = field(default_factory=dict)
    literals: tuple[str, ...] = ()
    meanings: dict[str, list[str]] = field(default_factory=dict)


def _meanings(roles: dict, names: dict[str, str]) -> dict[str, list[str]]:
    return {name: roles[role]["keywords"] for role, name in names.items()}


DETECTOR_ROLES = detector.roles("overcharge")
ANALYST_ROLES = analyst.roles("overcharge")
RESOLUTION_ROLES = {**resolution.submission_roles("overcharge"), **resolution.scalar_roles("overcharge")}
LINE_ITEM = resolution.line_item("overcharge")
RESOLUTION_CASES = resolution.CASES
DETECTOR_NAMES = {
    "invoice number": "invoiceNumber",
    "account number": "accountNumber",
    "disputed line": "lineNumber",
    "billed unit price": "unitPrice",
    "billed quantity": "quantity",
}
ANALYST_NAMES = {"invoice number": "invoiceNumber", "dispute description": "disputeDescription"}
WRITER_NAMES = {
    "customer name": "customerName",
    "invoice number": "invoiceNumber",
    "approved credit": "approvedCredit",
    "case reference": "caseReference",
}
RESOLUTION_LINE_NAMES = {
    "disputed line number": "lineNumber",
    "billed quantity": "quantity",
    "billed unit price": "unitPrice",
}

TASKS = {
    "billing_invoice_lookup": Facts(
        path=MULTI_NODE / "billing_invoice_lookup" / "billing_invoice_lookup.yaml",
        inputs={"invoiceNumber": _type_name(invoice.FOUND[0][0])},
        outputs={
            "matchedInvoiceNumber": _type_name(invoice.FOUND[0][1]),
            "lineItemCount": _type_name(invoice.FOUND[0][2]),
        },
        literals=("BillingDisputeERP", "Shared"),
        meanings={"invoiceNumber": invoice.KEYWORDS},
    ),
    "billing_discrepancy_detector": Facts(
        path=MULTI_NODE / "billing_discrepancy_detector" / "billing_discrepancy_detector.yaml",
        inputs={name: _type_name(DETECTOR_ROLES[role]["value"]) for role, name in DETECTOR_NAMES.items()},
        outputs={
            "overcharge": "number",
            "discrepancyCount": "number",
            "matchedInvoiceNumber": _type_name(detector.INVOICE),
            "accountTier": _type_name(detector.TIER),
        },
        literals=(*detector.ENTITIES, "Shared"),
        meanings=_meanings(DETECTOR_ROLES, DETECTOR_NAMES),
    ),
    "billing_dispute_analyst": Facts(
        path=MULTI_NODE / "billing_dispute_analyst" / "billing_dispute_analyst.yaml",
        inputs={name: _type_name(ANALYST_ROLES[role]["value"]) for role, name in ANALYST_NAMES.items()},
        outputs={"decision": "string", "reasoning": "string"},
        enums={"decision": set(analyst.DECISIONS)},
        meanings=_meanings(ANALYST_ROLES, ANALYST_NAMES),
    ),
    "billing_resolution_writer": Facts(
        path=MULTI_NODE / "billing_resolution_writer" / "billing_resolution_writer.yaml",
        inputs={name: _type_name(writer.ROLES[role]["value"]) for role, name in WRITER_NAMES.items()},
        outputs={
            "emailSubject": "string",
            "emailBody": "string",
            "caseKey": _type_name(writer.CASE_REF),
            "slackMessageId": "string",
        },
        literals=('written like "USD 1,234.56"', writer.SIGNATURE, *SLACK_LITERALS),
        meanings={**_meanings(writer.ROLES, WRITER_NAMES), "emailSubject": writer.SUBJECT_KEYWORDS},
    ),
    "billing_dispute_resolution": Facts(
        path=MULTI_NODE / "billing_dispute_resolution" / "billing_dispute_resolution.yaml",
        inputs={
            "invoicePdf": "file",
            "disputeSubmission": "object",
            **{name: _type_name(resolution.CASES["overcharge"][key]) for name, key in
               (("accountNumber", "account"), ("invoiceNumber", "invoice"))},
            "disputedLineItems": "array",
            **{name: _type_name(LINE_ITEM[name]) for name in RESOLUTION_LINE_NAMES.values()},
        },
        outputs={
            "decision": _type_name(RESOLUTION_CASES["overcharge"]["decision"]),
            "recommendedAction": "string",
            "creditAmount": _type_name(RESOLUTION_CASES["overcharge"]["credit"]),
            "explanation": "string",
            "emailDraft": "string",
        },
        enums={
            "decision": {c["decision"] for c in RESOLUTION_CASES.values()},
            "recommendedAction": {a for c in RESOLUTION_CASES.values() for a in c["actions"]},
        },
        literals=(
            resolution.POSTING_FUNCTION,
            *resolution.LOOKUP_ENTITIES,
            "Shared",
        ),
        meanings={
            **_meanings(RESOLUTION_ROLES, SUBMISSION_FIELDS),
            "disputedLineItems": RESOLUTION_ROLES["disputed lines"]["keywords"],
            **_meanings(RESOLUTION_ROLES, RESOLUTION_LINE_NAMES),
        },
    ),
    "coded_agent": Facts(
        path=SUITE / "single_node" / "coded_agent" / "coded_agent.yaml",
        inputs={"text": _type_name(coded.SENTENCE)},
        outputs={"approvedCount": _type_name(coded.EXPECTED)},
        meanings={"text": coded.ROLES["text"]["keywords"]},
    ),
    "inline_mcp_server_tool": Facts(
        path=SUITE / "inline_agent" / "inline_mcp_server_tool" / "inline_mcp_server_tool.yaml",
        inputs={name: _type_name(value) for name, value in mcp.INPUTS.items()},
        outputs={"answer": _type_name(mcp.EXPECTED_IN_ANSWER)},
        literals=(mcp.SERVER,),
    ),
    "escalation_orchestrator_paths": Facts(
        path=E2E / "escalation_orchestrator_paths" / "escalation_orchestrator_paths.yaml",
        inputs=_escalation_inputs(ORCHESTRATOR_CASES[0]),
        outputs={
            "escalationPath": "string",
            "severity": "string",
            "engineeringNeeded": _type_name(ORCHESTRATOR_CASES[0]["expected"]["engineering"]),
            "responseMode": "string",
            "caseKey": "string",
            "slackMessageId": "string",
        },
        enums={
            "escalationPath": _expected_values(ORCHESTRATOR_CASES, "path"),
            "severity": _expected_values(ORCHESTRATOR_CASES, "severity"),
            "responseMode": _expected_values(ORCHESTRATOR_CASES, "responseMode"),
            "customerMatchStatus": set(orchestrator.DEFAULT_WORD.values()),
        },
        literals=(*SLACK_LITERALS, "caseReference", "escalationPath"),
        meanings=_meanings({k: {"keywords": v} for k, v in KEYWORDS.items()}, ESCALATION_NAMES),
    ),
    "escalation_jira_ticket": Facts(
        path=E2E / "escalation_jira_ticket" / "escalation_jira_ticket.yaml",
        inputs=_escalation_inputs(ORCHESTRATOR_CASES[0]),
        outputs={
            "severity": "string",
            "engineeringNeeded": "boolean",
            "caseKey": "string",
            "jiraIssueKey": "string",
        },
        enums={"severity": {"Sev1", "Sev2", "Sev3"}},
        literals=(
            jira_is.CONNECTION_NAME,
            jira_is.FOLDER_PATH,
            f"project {jira_is.PROJECT_KEY}",
            f"issue type {jira_is.ISSUETYPE_NAME}",
            "[TEST] [<severity>] <caseReference> <subject>",
        ),
        meanings=_meanings({k: {"keywords": v} for k, v in KEYWORDS.items()}, ESCALATION_NAMES),
    ),
    "escalation_slack_alert": Facts(
        path=E2E / "escalation_slack_alert" / "escalation_slack_alert.yaml",
        inputs=_escalation_inputs(SLACK_CASES[0]),
        outputs={
            "severity": "string",
            "engineeringNeeded": _type_name(SLACK_CASES[0]["expected"]["engineering"]),
            "caseKey": "string",
            "slackMessageId": "string",
        },
        enums={"severity": _expected_values(SLACK_CASES, "severity")},
        literals=(*SLACK_LITERALS, SLACK_BULLETS),
        meanings=_meanings({k: {"keywords": v} for k, v in KEYWORDS.items()}, ESCALATION_NAMES),
    ),
    "e2e_01_invoice_approval_greenfield": Facts(
        path=HITL_SUITE / "e2e_01_invoice_approval_greenfield.yaml",
        inputs={
            "invoiceNumber": "string",
            "vendorName": _type_name(invoice_run.VENDOR),
            "totalAmount": _type_name(invoice_run.AMOUNT),
            "currency": _type_name(invoice_run.CURRENCY),
        },
        outputs={"status": "string", "sapDocumentNumber": "string"},
        enums={"status": {"posted", "rejected"}},
        literals=(invoice_run.SAP_MARKER,),
    ),
    "e2e_07_apptask_brownfield": Facts(
        path=HITL_SUITE / "e2e_07_apptask_brownfield.yaml",
        inputs={
            "expenseId": "string",
            "employeeName": _type_name(expense_run.EMPLOYEE),
            "amount": _type_name(expense_run.AMOUNT),
            "description": _type_name(expense_run.DESCRIPTION),
        },
        outputs={"status": "string", "sapDocumentNumber": "string"},
        enums={"status": {"posted", "rejected"}},
        literals=(expense_run.APP_MARKERS[0], expense_run.POSTING_MARKER),
    ),
}

HITL_GRADERS = {
    "e2e_01_invoice_approval_greenfield": (invoice_run, ("invoiceNumber", "vendorName", "totalAmount", "currency")),
    "e2e_07_apptask_brownfield": (expense_run, ("expenseId", "employeeName", "amount", "description")),
}


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _prompt(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = lines.index("initial_prompt: |") + 1
    body = []
    for line in lines[start:]:
        if line and not line.startswith(" "):
            break
        body.append(line[2:])
    return "\n".join(body)


def _tags(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    inline = re.search(r"^tags:\s*\[(.*)\]\s*$", text, re.M)
    if inline:
        return [tag.strip().strip("'\"") for tag in inline.group(1).split(",")]
    block = re.search(r"^tags:\s*\n((?:\s+-\s*.+\n?)+)", text, re.M)
    if not block:
        return []
    return [line.split("-", 1)[1].strip().strip("'\"") for line in block.group(1).splitlines() if line.strip()]


def _helper(path: Path) -> str:
    prompt = _prompt(path)
    assert prompt.count(HELPER_START) == 1 and prompt.count(HELPER_END) == 1, path
    return _flat(prompt.split(HELPER_START)[1].split(HELPER_END)[0])


def _tagged(directory: Path) -> set[Path]:
    return {
        path
        for path in directory.rglob("*.yaml")
        if PATH_TO_GA_TAG in _tags(path)
    }


def test_every_path_to_ga_task_is_covered():
    assert _tagged(SUITE) | _tagged(HITL_SUITE) == {facts.path for facts in TASKS.values()}


@pytest.mark.parametrize("task", TASKS)
def test_helper_types_every_input_and_output(task):
    helper = _helper(TASKS[task].path)
    for name, type_name in {**TASKS[task].inputs, **TASKS[task].outputs}.items():
        assert f"{name} ({type_name}" in helper, f"{name} ({type_name})"


@pytest.mark.parametrize("task", TASKS)
def test_no_output_shares_a_name_with_an_input(task):
    facts = TASKS[task]
    taken = {io.normalize(name) for name in facts.inputs}
    assert not [name for name in facts.outputs if io.normalize(name) in taken]


@pytest.mark.parametrize("task", [name for name, facts in TASKS.items() if facts.meanings])
def test_each_declared_name_means_its_role_to_the_grader(task):
    for name, keywords in TASKS[task].meanings.items():
        assert io.means([name], keywords) > 0, name


@pytest.mark.parametrize("task", [name for name, facts in TASKS.items() if facts.enums])
def test_helper_states_exactly_the_asserted_values(task):
    helper = _helper(TASKS[task].path)
    for name, values in TASKS[task].enums.items():
        sentence = re.search(rf"\b{name} is ([^.]*)\.", helper)
        assert sentence, f"{name} values"
        assert set(re.findall(r'"([^"]+)"', sentence.group(1))) == values, name


@pytest.mark.parametrize("task", [name for name, facts in TASKS.items() if facts.literals])
def test_helper_carries_the_targets_and_formats_the_grader_asserts(task):
    helper = _helper(TASKS[task].path)
    for literal in TASKS[task].literals:
        assert literal in helper, literal


@pytest.mark.parametrize("task", HITL_GRADERS)
def test_the_hitl_graders_feed_the_names_the_helper_declares(task):
    module, names = HITL_GRADERS[task]
    source = inspect.getsource(module.run_once)
    assert all(f'"{name}"' in source for name in names)
    helper = _helper(TASKS[task].path)
    assert all(name in helper for name in names)


def test_the_helpers_name_the_rule_without_an_example_to_copy():
    for task in ("billing_dispute_analyst", "billing_dispute_resolution"):
        helper = _helper(TASKS[task].path)
        assert "by its section number in the SOP" in helper, task
        assert not re.search(r"§\s*\d", helper), task


def test_the_writer_helper_shows_a_credit_format_but_not_the_graded_credit():
    helper = _helper(TASKS["billing_resolution_writer"].path)
    assert writer.CREDIT_TEXT not in helper
    assert writer.INVOICE not in helper


def test_the_lookup_helper_shows_no_invoice_the_grader_expects():
    helper = _helper(TASKS["billing_invoice_lookup"].path)
    assert not [expected for _raw, expected, _count, _label in invoice.FOUND if expected in helper]


def test_the_resolution_helper_names_the_cleaned_invoice_form():
    helper = _helper(TASKS["billing_dispute_resolution"].path)
    assert 'FinancialPostingFunction, as the records hold it' in helper
    assert 'like "MCS-YYYY-NNNNN"' in helper
    assert resolution.CASES["overcharge"]["invoice"] not in helper


def test_the_agent_tasks_say_to_build_a_flow_not_an_agent_project():
    for task in ("billing_dispute_analyst", "billing_resolution_writer", "billing_dispute_resolution",
                 "coded_agent", "inline_mcp_server_tool"):
        assert "Flow in this Flow project" in _helper(TASKS[task].path), task


def test_the_escalation_helpers_state_one_post_or_one_ticket_per_run():
    for task in ("escalation_orchestrator_paths", "escalation_slack_alert"):
        assert "Post one message per run" in _helper(TASKS[task].path), task
    assert "Create one issue per run" in _helper(TASKS["escalation_jira_ticket"].path)


GUARD = (
    "Do not delete or overwrite anything this run did not create, except what the task "
    "asks you to change, and do not publish to a shared destination unless the task asks for it."
)


@pytest.mark.parametrize("task", TASKS)
def test_the_opener_names_no_harness_and_carries_the_guard(task):
    opener = _flat(_prompt(TASKS[task].path).split("\n\n")[0])
    assert opener.startswith("You are a coding agent in "), task
    assert "Studio Web" not in opener, task
    assert GUARD in opener, task


def test_the_expense_helper_puts_the_posting_step_after_the_review():
    expense = _helper(TASKS["e2e_07_apptask_brownfield"].path)
    assert "The posting step goes after the review" in expense


GRADED_VALUES = {
    "billing_discrepancy_detector": ("1610", detector.INVOICE, detector.TIER),
    "billing_invoice_lookup": tuple(expected for _raw, expected, _count, _label in invoice.FOUND),
    "billing_resolution_writer": (writer.INVOICE, writer.CREDIT_TEXT),
    "e2e_01_invoice_approval_greenfield": (invoice_run.VENDOR, str(invoice_run.AMOUNT), invoice_run.CURRENCY),
    "e2e_07_apptask_brownfield": (expense_run.EMPLOYEE, str(expense_run.AMOUNT), expense_run.DESCRIPTION),
}


@pytest.mark.parametrize("task", sorted(GRADED_VALUES))
def test_no_request_text_example_equals_a_graded_value(task):
    prompt = _flat(_prompt(TASKS[task].path))
    assert not [value for value in GRADED_VALUES[task] if value in prompt], task

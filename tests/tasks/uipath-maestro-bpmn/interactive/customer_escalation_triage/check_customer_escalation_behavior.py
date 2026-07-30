#!/usr/bin/env python3
"""Run the exact submitted escalation BPMN through live Alpha debug sessions.

The checker intentionally has no local BPMN interpreter. It validates the
submitted source, imports that exact project into one ephemeral solution, runs
hidden business scenarios in the Alpha runtime, inspects variables, element
executions, and incidents, and deletes every returned solution id in a finally
block. Repeated scenarios overwrite the same ephemeral solution rather than
creating tenant clutter.
"""

from __future__ import annotations

import hashlib
import json
import re
import signal
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = Path("CustomerEscalationTriage")
BPMN_FILE = PROJECT / "CustomerEscalationTriage.bpmn"
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"
CONNECTION_FOLDER_KEY = "5da18ec0-7de1-4e57-aaf1-ddc8a369c199"

INPUT_TYPES = {
    "customerTier": "string",
    "crmMatchCount": "integer",
    "serviceState": "string",
    "workaroundAvailable": "boolean",
    "duplicateIssueKey": "string",
    "attachments": "array",
    "agentOutputValid": "boolean",
    "jiraAvailable": "boolean",
    "autoSendEnabled": "boolean",
    "businessImpact": "string",
    "correlationId": "string",
    "jiraProjectKey": "string",
    "jiraIssueTypeId": "string",
    "jiraReporterAccountId": "string",
    "slackChannelId": "string",
    "driveDestinationFolderId": "string",
}
OUTPUT_TYPES = {
    "route": "string",
    "severity": "string",
    "engineeringNeeded": "boolean",
    "jiraAction": "string",
    "attachmentAction": "string",
    "slackAction": "string",
    "responseMode": "string",
    "caseKey": "string",
    "lastAttachmentName": "string",
    "failureReason": "string",
}
CONNECTOR_INPUTS = {
    ("uipath-atlassian-jira", "/curated_create_issue"): {
        ("body", "body"),
    },
    (
        "uipath-atlassian-jira",
        "/curated_edit_issue/{issueIdOrKey}",
    ): {
        ("path", "issueIdOrKey"),
        ("query", "project"),
        ("query", "issuetype"),
        ("body", "body"),
    },
    ("uipath-google-drive", "/copyFile"): {
        ("query", "fileId"),
        ("body", "body"),
    },
    (
        "uipath-salesforce-slack",
        "/send_message_to_channel_v2",
    ): {
        ("query", "send_as"),
        ("body", "body"),
    },
}
OPTIONAL_CONNECTOR_INPUTS = {
    ("uipath-google-drive", "/copyFile"): {
        ("query", "alreadyExists"),
    },
}


class CheckFailure(RuntimeError):
    pass


def q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalized_identifier(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def get_ci(value: Any, key: str, default: Any = None) -> Any:
    if not isinstance(value, dict):
        return default
    wanted = key.casefold()
    for candidate, item in value.items():
        if str(candidate).casefold() == wanted:
            return item
    return default


def parse_json_output(text: str, label: str) -> Any:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    for index, character in enumerate(stripped):
        if character not in "[{":
            continue
        try:
            return json.loads(stripped[index:])
        except json.JSONDecodeError:
            continue
    raise CheckFailure(f"{label} returned invalid JSON: {stripped[:1200]}")


def exact_type(value: Any, declared_type: str) -> bool:
    if declared_type == "string":
        return type(value) is str
    if declared_type == "boolean":
        return type(value) is bool
    if declared_type == "integer":
        return type(value) is int
    if declared_type == "number":
        return type(value) in (int, float)
    if declared_type == "array":
        return type(value) is list
    if declared_type == "object":
        return type(value) is dict
    return False


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class Scenario:
    name: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    attachment_iterations: tuple[str, ...] = ()
    uses_error_boundary: bool = False


def scenario(
    name: str,
    *,
    customer_tier: str = "Standard",
    crm_matches: int = 1,
    service_state: str = "Available",
    workaround: bool = True,
    duplicate_key: str = "",
    attachments: tuple[str, ...] = (),
    agent_valid: bool = True,
    jira_available: bool = True,
    auto_send: bool = False,
    expected: dict[str, Any],
    uses_error_boundary: bool = False,
) -> Scenario:
    correlation = f"EVAL-live-alpha-{name}-Exact"
    values = {
        "customerTier": customer_tier,
        "crmMatchCount": crm_matches,
        "serviceState": service_state,
        "workaroundAvailable": workaround,
        "duplicateIssueKey": duplicate_key,
        "attachments": [
            {"name": item, "driveFileId": "__DRIVE_SOURCE_FILE_ID__"}
            for item in attachments
        ],
        "agentOutputValid": agent_valid,
        "jiraAvailable": jira_available,
        "autoSendEnabled": auto_send,
        "businessImpact": f"Hidden Alpha scenario {name}",
        "correlationId": correlation,
    }
    complete_expected = dict(expected)
    complete_expected["caseKey"] = correlation
    return Scenario(
        name=name,
        inputs=values,
        outputs=complete_expected,
        attachment_iterations=attachments
        if expected["attachmentAction"] == "SaveToDrive"
        else (),
        uses_error_boundary=uses_error_boundary,
    )


SCENARIOS = (
    scenario(
        "mixed-case-sev1-new-two-attachments",
        customer_tier="eNtErPrIsE",
        service_state="uNaVaIlAbLe",
        workaround=False,
        attachments=("outage.png", "trace.zip"),
        expected={
            "route": "NewEscalation",
            "severity": "Sev1",
            "engineeringNeeded": True,
            "jiraAction": "CreateIssue",
            "attachmentAction": "SaveToDrive",
            "slackAction": "PostAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "trace.zip",
            "failureReason": "",
        },
    ),
    scenario(
        "whitespace-duplicate-degraded",
        customer_tier="Enterprise",
        service_state="DeGrAdEd",
        workaround=True,
        duplicate_key="   \t ",
        auto_send=True,
        expected={
            "route": "NewEscalation",
            "severity": "Sev2",
            "engineeringNeeded": True,
            "jiraAction": "CreateIssue",
            "attachmentAction": "NoAttachments",
            "slackAction": "PostAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "",
        },
    ),
    scenario(
        "existing-sev3-jira-unavailable",
        service_state="AVAILABLE",
        duplicate_key="  JIRA-42  ",
        jira_available=False,
        auto_send=True,
        expected={
            "route": "ExistingIssue",
            "severity": "Sev3",
            "engineeringNeeded": False,
            "jiraAction": "UpdateExisting",
            "attachmentAction": "NoAttachments",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "",
        },
    ),
    scenario(
        "crm-zero-precedes-agent-and-jira",
        crm_matches=0,
        service_state="Unavailable",
        workaround=False,
        agent_valid=False,
        jira_available=False,
        attachments=("should-not-run.txt",),
        expected={
            "route": "ManualReview",
            "severity": "Unclassified",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "CrmNotFound",
        },
    ),
    scenario(
        "crm-ambiguous-precedes-agent",
        crm_matches=3,
        agent_valid=False,
        expected={
            "route": "ManualReview",
            "severity": "Unclassified",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "CrmAmbiguous",
        },
    ),
    scenario(
        "invalid-agent-single-match",
        agent_valid=False,
        expected={
            "route": "ManualReview",
            "severity": "Unclassified",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "InvalidAgentOutput",
        },
    ),
    scenario(
        "jira-unavailable-sev2-typed-boundary",
        service_state="Unavailable",
        workaround=True,
        jira_available=False,
        attachments=("should-not-run.txt",),
        expected={
            "route": "ManualReview",
            "severity": "Sev2",
            "engineeringNeeded": True,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "JiraUnavailable",
        },
        uses_error_boundary=True,
    ),
    scenario(
        "jira-unavailable-sev1-typed-boundary",
        customer_tier="Enterprise",
        service_state="Unavailable",
        workaround=False,
        jira_available=False,
        attachments=("should-not-run.txt",),
        expected={
            "route": "ManualReview",
            "severity": "Sev1",
            "engineeringNeeded": True,
            "jiraAction": "NoAction",
            "attachmentAction": "HoldForReview",
            "slackAction": "NoAlert",
            "responseMode": "Draft",
            "lastAttachmentName": "",
            "failureReason": "JiraUnavailable",
        },
        uses_error_boundary=True,
    ),
    scenario(
        "informational-auto-send-one-attachment",
        service_state="available",
        attachments=("receipt.pdf",),
        auto_send=True,
        expected={
            "route": "Informational",
            "severity": "Sev3",
            "engineeringNeeded": False,
            "jiraAction": "NoAction",
            "attachmentAction": "SaveToDrive",
            "slackAction": "NoAlert",
            "responseMode": "Send",
            "lastAttachmentName": "receipt.pdf",
            "failureReason": "",
        },
    ),
)


@dataclass(frozen=True)
class RuntimeContract:
    public_output_ids: dict[str, str]
    root_end_id: str
    parallel_split_id: str
    parallel_join_id: str
    marker_id: str
    error_end_id: str
    error_boundary_id: str
    jira_create_id: str
    jira_update_id: str
    drive_copy_id: str
    slack_send_id: str


def direct_flow_counts(
    process: ET.Element,
) -> tuple[dict[str, int], dict[str, int]]:
    incoming: dict[str, int] = {}
    outgoing: dict[str, int] = {}
    for flow in process.findall(f"./{q(BPMN_NS, 'sequenceFlow')}"):
        source = flow.attrib["sourceRef"]
        target = flow.attrib["targetRef"]
        outgoing[source] = outgoing.get(source, 0) + 1
        incoming[target] = incoming.get(target, 0) + 1
    return incoming, outgoing


def connector_context(element: ET.Element) -> dict[str, str]:
    activity = element.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'activity')}"
    )
    if activity is None:
        return {}
    return {
        item.attrib["name"]: item.attrib.get("value", "")
        for item in activity.findall(
            f"./{q(UIPATH_NS, 'context')}/{q(UIPATH_NS, 'input')}"
        )
        if item.attrib.get("name")
    }


def validate_connector_inputs(
    element: ET.Element,
    key: tuple[str, str],
) -> None:
    activity = element.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'activity')}"
    )
    if activity is None:
        raise CheckFailure(f"connector {key} has no activity extension")
    inputs = {
        (item.attrib.get("target", ""), item.attrib.get("name", "")): item
        for item in activity.findall(f"./{q(UIPATH_NS, 'input')}")
    }
    required = CONNECTOR_INPUTS[key]
    allowed = required | OPTIONAL_CONNECTOR_INPUTS.get(key, set())
    if not required <= set(inputs) or not set(inputs) <= allowed:
        raise CheckFailure(
            f"connector {key} does not use exact registry input targets and "
            f"names: {sorted(inputs)}"
        )
    body_element = inputs[("body", "body")]
    raw_body = body_element.attrib.get("value")
    if raw_body is None:
        raw_body = body_element.text or ""
    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise CheckFailure(f"connector {key} body is not JSON: {exc}") from exc
    if not isinstance(body, dict):
        raise CheckFailure(f"connector {key} body is not a JSON object")
    if key == ("uipath-atlassian-jira", "/curated_create_issue"):
        fields = body.get("fields")
        if not isinstance(fields, dict) or set(fields) != {
            "project",
            "issuetype",
            "reporter",
            "summary",
            "description",
        }:
            raise CheckFailure("Jira create body does not match registry fields")
    elif key[1] == "/curated_edit_issue/{issueIdOrKey}":
        fields = body.get("fields")
        if not isinstance(fields, dict) or set(fields) != {"description"}:
            raise CheckFailure("Jira update body does not match registry fields")
    elif key == ("uipath-google-drive", "/copyFile") and set(body) != {
        "destinationFolder",
        "name",
    }:
        raise CheckFailure("Drive copy body does not match registry fields")
    elif key[0] == "uipath-salesforce-slack" and set(body) != {
        "channel",
        "messageToSend",
    }:
        raise CheckFailure("Slack send body does not match registry fields")
    if (
        key[0] == "uipath-salesforce-slack"
        and inputs[("query", "send_as")].attrib.get("value") != "bot"
    ):
        raise CheckFailure("Slack send_as query input must be bot")


def load_runtime_contract(path: Path = BPMN_FILE) -> RuntimeContract:
    root = ET.parse(path).getroot()
    process = root.find(q(BPMN_NS, "process"))
    if process is None:
        raise CheckFailure("BPMN must contain one root process")

    root_ends = process.findall(f"./{q(BPMN_NS, 'endEvent')}")
    if len(root_ends) != 1:
        raise CheckFailure("live contract requires exactly one root end event")
    root_end_id = root_ends[0].attrib["id"]

    variables = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'variables')}"
    )
    if variables is None:
        raise CheckFailure("root process is missing uipath:variables")
    public_inputs: dict[str, tuple[str, str]] = {}
    public_outputs: dict[str, tuple[str, str]] = {}
    for variable in variables:
        name = variable.attrib.get("name")
        identifier = variable.attrib.get("id")
        value_type = variable.attrib.get("type")
        element_id = variable.attrib.get("elementId")
        if not name or not identifier or not value_type:
            continue
        if local(variable.tag) == "input":
            public_inputs[name] = (value_type, element_id or "")
        elif local(variable.tag) == "output":
            public_outputs[name] = (value_type, element_id or "")

    if {
        name: item[0] for name, item in public_inputs.items()
    } != INPUT_TYPES:
        raise CheckFailure("public input declarations do not match the contract")
    if {
        name: item[0] for name, item in public_outputs.items()
    } != OUTPUT_TYPES:
        raise CheckFailure("public output declarations do not match the contract")
    if any(item[1] != root_end_id for item in public_outputs.values()):
        raise CheckFailure(
            "every public output must bind to the sole root completion end"
        )

    public_output_ids = {
        variable.attrib["name"]: variable.attrib["id"]
        for variable in variables
        if local(variable.tag) == "output"
        and variable.attrib.get("name") in OUTPUT_TYPES
    }

    incoming, outgoing = direct_flow_counts(process)
    parallels = process.findall(f"./{q(BPMN_NS, 'parallelGateway')}")
    splits = [
        item for item in parallels if outgoing.get(item.attrib["id"], 0) == 3
    ]
    joins = [
        item for item in parallels if incoming.get(item.attrib["id"], 0) == 3
    ]
    if len(splits) != 1 or len(joins) != 1:
        raise CheckFailure("expected one three-way parallel split and join")

    markers = [
        node
        for node in process.findall(f".//{q(BPMN_NS, 'subProcess')}")
        if node.find(f"./{q(BPMN_NS, 'multiInstanceLoopCharacteristics')}")
        is not None
    ]
    if len(markers) != 1:
        raise CheckFailure(
            "expected one sequential multi-instance attachment subprocess"
        )

    connectors: dict[tuple[str, str], str] = {}
    for node in process.findall(f".//{q(BPMN_NS, 'sendTask')}"):
        context = connector_context(node)
        key = (context.get("connectorKey", ""), context.get("path", ""))
        if all(key):
            connectors[key] = node.attrib["id"]
    required_connectors = {
        (
            "uipath-atlassian-jira",
            "/curated_create_issue",
        ): "curated_create_issue",
        (
            "uipath-atlassian-jira",
            "/curated_edit_issue/{issueIdOrKey}",
        ): "curated_edit_issue",
        ("uipath-google-drive", "/copyFile"): "copyFile",
        (
            "uipath-salesforce-slack",
            "/send_message_to_channel_v2",
        ): "send_message_to_channel_v2",
    }
    if set(connectors) != set(required_connectors):
        raise CheckFailure(
            "live contract does not contain the exact Jira create/update, "
            "Drive copy, and Slack send activities"
        )
    for node in process.findall(f".//{q(BPMN_NS, 'sendTask')}"):
        context = connector_context(node)
        key = (context.get("connectorKey", ""), context.get("path", ""))
        if key in required_connectors:
            if not context.get("operation"):
                raise CheckFailure(
                    f"connector {key} is missing runtime operation"
                )
            if context.get("objectName") != required_connectors[key]:
                raise CheckFailure(
                    f"connector {key} must use objectName "
                    f"{required_connectors[key]!r}"
                )
            validate_connector_inputs(node, key)

    error_ends = [
        node
        for node in process.findall(f".//{q(BPMN_NS, 'endEvent')}")
        if node.find(f"./{q(BPMN_NS, 'errorEventDefinition')}") is not None
    ]
    boundaries = [
        node
        for node in process.findall(f"./{q(BPMN_NS, 'boundaryEvent')}")
        if node.find(f"./{q(BPMN_NS, 'errorEventDefinition')}") is not None
    ]
    if len(error_ends) != 1 or len(boundaries) != 1:
        raise CheckFailure("expected one typed error end and boundary")

    return RuntimeContract(
        public_output_ids=public_output_ids,
        root_end_id=root_end_id,
        parallel_split_id=splits[0].attrib["id"],
        parallel_join_id=joins[0].attrib["id"],
        marker_id=markers[0].attrib["id"],
        error_end_id=error_ends[0].attrib["id"],
        error_boundary_id=boundaries[0].attrib["id"],
        jira_create_id=connectors[
            ("uipath-atlassian-jira", "/curated_create_issue")
        ],
        jira_update_id=connectors[
            (
                "uipath-atlassian-jira",
                "/curated_edit_issue/{issueIdOrKey}",
            )
        ],
        drive_copy_id=connectors[
            ("uipath-google-drive", "/copyFile")
        ],
        slack_send_id=connectors[
            (
                "uipath-salesforce-slack",
                "/send_message_to_channel_v2",
            )
        ],
    )


def run_cli(
    arguments: list[str],
    *,
    timeout: int,
    log_file: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [*arguments, "--output", "json"]
    if log_file is not None:
        command.extend(["--log-file", str(log_file)])
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def payload_data(
    completed: subprocess.CompletedProcess[str],
    label: str,
    *,
    require_success: bool = True,
) -> tuple[Any, Any]:
    payload = parse_json_output(
        completed.stdout or completed.stderr,
        label,
    )
    if require_success and (
        completed.returncode != 0
        or str(get_ci(payload, "Result", "")).casefold() != "success"
    ):
        message = get_ci(payload, "Message", "")
        instructions = get_ci(payload, "Instructions", "")
        raise CheckFailure(
            f"{label} failed (exit {completed.returncode}): "
            f"{message} {instructions}".strip()
        )
    return payload, get_ci(payload, "Data")


class AlphaSolutionLease:
    def __init__(self, solution_file: Path):
        self.solution_file = solution_file
        self.solution_ids: set[str] = set()
        self.cleaned = False

    def capture_payload(self, payload: Any) -> None:
        if isinstance(payload, list):
            for item in payload:
                self.capture_payload(item)
            return
        if not isinstance(payload, dict):
            return
        for key, value in payload.items():
            if str(key).casefold() == "solutionid" and isinstance(value, str):
                self.solution_ids.add(value)
            elif isinstance(value, (dict, list)):
                self.capture_payload(value)

    def capture_manifest(self) -> None:
        if not self.solution_file.is_file():
            return
        try:
            self.capture_payload(
                json.loads(self.solution_file.read_text(encoding="utf-8"))
            )
        except (OSError, json.JSONDecodeError):
            pass

    def cleanup(self) -> list[str]:
        if self.cleaned:
            return []
        self.capture_manifest()
        failures: list[str] = []
        for solution_id in sorted(self.solution_ids):
            completed = run_cli(
                ["uip", "solution", "delete", solution_id, "--yes"],
                timeout=180,
            )
            try:
                payload, _data = payload_data(
                    completed,
                    f"delete Alpha solution {solution_id}",
                )
                self.capture_payload(payload)
            except CheckFailure as exc:
                # A local SolutionId exists immediately after `solution init`.
                # If import/upload fails before Alpha sees it, deletion returns
                # 404 because there is no remote resource to clean up.
                detail = f"{completed.stdout}\n{completed.stderr}"
                if "404" not in detail and "Not Found" not in detail:
                    failures.append(str(exc))
        self.cleaned = True
        return failures


@dataclass(frozen=True)
class LiveEnvironment:
    jira_connection_id: str
    drive_connection_id: str
    slack_connection_id: str
    jira_project_key: str = "CE"
    jira_issue_type_id: str = "11457"
    jira_reporter_account_id: str = (
        "712020:b53bf3dc-8817-419e-99e1-5670aeb7ffe6"
    )
    slack_channel_id: str = "C01H4SPS77W"
    drive_destination_folder_id: str = "0AKHXBGF_5DaVUk9PVA"
    drive_source_file_id: str = "1YlblU34Vd6RvCkamYw5BWejdX8ES-Zzy"


def discover_live_environment() -> LiveEnvironment:
    listed = run_cli(
        ["uip", "is", "connections", "list", "--all-folders"],
        timeout=180,
    )
    _payload, rows = payload_data(listed, "discover connector connections")
    if not isinstance(rows, list):
        raise CheckFailure("connector discovery returned no list")
    wanted = {
        "uipath-atlassian-jira": (
            "is-sandboxes-test@uipath.com-uipath-sandbox-380"
        ),
        "uipath-google-drive": "is.sandboxes.test@gmail.com",
        "uipath-salesforce-slack": "is-sandboxes",
    }
    ids: dict[str, str] = {}
    for connector_key, name in wanted.items():
        matches = [
            row
            for row in rows
            if isinstance(row, dict)
            and get_ci(row, "ConnectorKey") == connector_key
            and get_ci(row, "Name") == name
            and get_ci(row, "FolderKey") == CONNECTION_FOLDER_KEY
            and str(get_ci(row, "State") or "").casefold() == "enabled"
        ]
        if len(matches) != 1:
            raise CheckFailure(
                f"expected one enabled {connector_key} connection named "
                f"{name!r}, found {len(matches)}"
            )
        identifier = get_ci(matches[0], "Id")
        if not isinstance(identifier, str):
            raise CheckFailure(f"{connector_key} connection has no id")
        ids[connector_key] = identifier

    for connector_key, connection_id in ids.items():
        pinged = run_cli(
            ["uip", "is", "connections", "ping", connection_id],
            timeout=120,
        )
        payload_data(pinged, f"ping {connector_key} connection")

    return LiveEnvironment(
        jira_connection_id=ids["uipath-atlassian-jira"],
        drive_connection_id=ids["uipath-google-drive"],
        slack_connection_id=ids["uipath-salesforce-slack"],
    )


def scenario_inputs(
    case: Scenario,
    environment: LiveEnvironment,
    *,
    duplicate_key: str | None = None,
) -> dict[str, Any]:
    inputs = json.loads(json.dumps(case.inputs))
    inputs.update(
        {
            "jiraProjectKey": environment.jira_project_key,
            "jiraIssueTypeId": environment.jira_issue_type_id,
            "jiraReporterAccountId": environment.jira_reporter_account_id,
            "slackChannelId": environment.slack_channel_id,
            "driveDestinationFolderId": (
                environment.drive_destination_folder_id
            ),
        }
    )
    for attachment in inputs["attachments"]:
        attachment["driveFileId"] = environment.drive_source_file_id
    if duplicate_key is not None:
        inputs["duplicateIssueKey"] = duplicate_key
    return inputs


def recursive_strings(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, str):
        values.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            values.extend(recursive_strings(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(recursive_strings(item))
    return values


def recursive_values(value: Any, wanted_key: str) -> list[Any]:
    values: list[Any] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).casefold() == wanted_key.casefold():
                values.append(item)
            values.extend(recursive_values(item, wanted_key))
    elif isinstance(value, list):
        for item in value:
            values.extend(recursive_values(item, wanted_key))
    return values


class ConnectorSideEffectLease:
    def __init__(self, environment: LiveEnvironment):
        self.environment = environment
        self.jira_issue_ids: set[str] = set()
        self.drive_file_ids: set[str] = set()
        self.slack_messages: set[tuple[str, str]] = set()

    def cleanup(self) -> list[str]:
        failures: list[str] = []
        for channel_id, timestamp in sorted(self.slack_messages):
            completed = run_cli(
                [
                    "uip",
                    "is",
                    "resources",
                    "run",
                    "delete",
                    "uipath-salesforce-slack",
                    "ChatDeleteTimestamp_POST",
                    "--connection-id",
                    self.environment.slack_connection_id,
                    "--query",
                    json.dumps(
                        {
                            "conversationId": channel_id,
                            "timestampId": timestamp,
                        },
                        separators=(",", ":"),
                    ),
                    "--yes",
                ],
                timeout=120,
            )
            try:
                payload_data(completed, f"delete Slack message {timestamp}")
            except CheckFailure as exc:
                failures.append(str(exc))
        self.slack_messages.clear()

        for file_id in sorted(self.drive_file_ids):
            completed = run_cli(
                [
                    "uip",
                    "is",
                    "resources",
                    "run",
                    "delete",
                    "uipath-google-drive",
                    "DeleteFileorFolder",
                    "--connection-id",
                    self.environment.drive_connection_id,
                    "--query",
                    json.dumps({"fileId": file_id}, separators=(",", ":")),
                    "--yes",
                ],
                timeout=120,
            )
            try:
                payload_data(completed, f"delete Drive file {file_id}")
            except CheckFailure as exc:
                failures.append(str(exc))
        self.drive_file_ids.clear()

        for issue_id in sorted(self.jira_issue_ids):
            completed = run_cli(
                [
                    "uip",
                    "is",
                    "resources",
                    "run",
                    "delete",
                    "uipath-atlassian-jira",
                    "issue",
                    "--connection-id",
                    self.environment.jira_connection_id,
                    "--query",
                    json.dumps({"issueId": issue_id}, separators=(",", ":")),
                    "--yes",
                ],
                timeout=120,
            )
            try:
                payload_data(completed, f"delete Jira issue {issue_id}")
            except CheckFailure as exc:
                failures.append(str(exc))
        self.jira_issue_ids.clear()
        return failures


def create_seed_jira_issue(
    case: Scenario,
    environment: LiveEnvironment,
    lease: ConnectorSideEffectLease,
) -> str:
    body = {
        "fields": {
            "project": {"key": environment.jira_project_key},
            "issuetype": {"id": environment.jira_issue_type_id},
            "reporter": {"id": environment.jira_reporter_account_id},
            "summary": f"Seed for {case.inputs['correlationId']}",
            "description": "Awaiting live BPMN update",
        }
    }
    created = run_cli(
        [
            "uip",
            "is",
            "resources",
            "run",
            "create",
            "uipath-atlassian-jira",
            "curated_create_issue",
            "--connection-id",
            environment.jira_connection_id,
            "--body",
            json.dumps(body, separators=(",", ":")),
        ],
        timeout=180,
    )
    _payload, data = payload_data(created, f"{case.name} seed Jira issue")
    issue_ids = [
        value
        for value in recursive_values(data, "id")
        if isinstance(value, str)
    ]
    issue_keys = [
        value
        for value in recursive_values(data, "key")
        if isinstance(value, str)
    ]
    if not issue_ids or not issue_keys:
        raise CheckFailure(
            f"{case.name}: Jira seed returned no id/key: {data!r}"
        )
    lease.jira_issue_ids.add(issue_ids[0])
    return issue_keys[0]


def root_scope(variables_data: Any) -> dict[str, Any]:
    scopes = get_ci(variables_data, "Variables", [])
    roots = [
        scope
        for scope in scopes
        if get_ci(scope, "ParentElementId") is None
    ]
    if len(roots) != 1:
        raise CheckFailure(
            f"variables-all returned {len(roots)} root scopes, expected one"
        )
    return roots[0]


def root_public_outputs(
    scope: dict[str, Any],
    contract: RuntimeContract,
) -> dict[str, Any]:
    globals_map = get_ci(scope, "Globals", {})
    by_id = {
        normalized_identifier(key): value
        for key, value in globals_map.items()
    }
    results: dict[str, Any] = {}
    for name, identifier in contract.public_output_ids.items():
        key = normalized_identifier(identifier)
        if key not in by_id:
            raise CheckFailure(
                f"runtime root globals are missing public output id "
                f"{identifier!r} ({name})"
            )
        results[name] = by_id[key]
    return results


def element_output_records(
    variables_data: Any,
    element_id: str,
) -> list[Any]:
    records: list[Any] = []
    scopes = get_ci(variables_data, "Variables", [])
    if not isinstance(scopes, list):
        return records
    for scope in scopes:
        for element in get_ci(scope, "Elements", []):
            if get_ci(element, "ElementId") == element_id:
                records.append(get_ci(element, "Outputs", {}))
    return records


def connector_response_values(outputs: list[Any], name: str) -> list[Any]:
    """Read only top-level response fields, never same-named nested metadata."""
    values: list[Any] = []
    for output in outputs:
        response = get_ci(output, "response")
        if isinstance(response, dict):
            value = get_ci(response, name)
            if value is not None:
                values.append(value)
    return values


def capture_connector_outputs_for_cleanup(
    variables_data: Any,
    contract: RuntimeContract,
    environment: LiveEnvironment,
    side_effects: ConnectorSideEffectLease,
) -> None:
    jira_outputs = element_output_records(
        variables_data, contract.jira_create_id
    )
    jira_ids = [
        value
        for value in connector_response_values(jira_outputs, "id")
        if isinstance(value, str)
    ]
    jira_keys = [
        value
        for value in connector_response_values(jira_outputs, "key")
        if isinstance(value, str)
    ]
    side_effects.jira_issue_ids.update(jira_ids or jira_keys)

    drive_outputs = element_output_records(
        variables_data, contract.drive_copy_id
    )
    side_effects.drive_file_ids.update(
        value
        for value in connector_response_values(drive_outputs, "id")
        if isinstance(value, str)
    )

    slack_outputs = element_output_records(
        variables_data, contract.slack_send_id
    )
    side_effects.slack_messages.update(
        (environment.slack_channel_id, value)
        for value in connector_response_values(slack_outputs, "ts")
        if isinstance(value, str)
    )


def assert_jira_contains_correlation(
    issue_key: str,
    correlation: str,
    environment: LiveEnvironment,
) -> None:
    fetched = run_cli(
        [
            "uip",
            "is",
            "resources",
            "run",
            "get",
            "uipath-atlassian-jira",
            "issue",
            "--connection-id",
            environment.jira_connection_id,
            "--query",
            json.dumps({"issueId": issue_key}, separators=(",", ":")),
        ],
        timeout=120,
    )
    _payload, data = payload_data(fetched, f"read Jira issue {issue_key}")
    if not any(correlation in value for value in recursive_strings(data)):
        raise CheckFailure(
            f"Jira issue {issue_key} does not contain correlation "
            f"{correlation!r}"
        )


def assert_scenario(
    case: Scenario,
    contract: RuntimeContract,
    debug_data: Any,
    variables_data: Any,
    incidents_data: Any,
    environment: LiveEnvironment,
    side_effects: ConnectorSideEffectLease,
    *,
    update_issue_key: str | None,
) -> None:
    final_status = get_ci(debug_data, "FinalStatus")
    if final_status not in {"Completed", "Successful"}:
        raise CheckFailure(
            f"{case.name}: Alpha final status was {final_status!r}"
        )
    if not isinstance(incidents_data, list):
        raise CheckFailure(
            f"{case.name}: incidents response is not a list: "
            f"{incidents_data!r}"
        )
    incidents = incidents_data
    if incidents:
        raise CheckFailure(f"{case.name}: unexpected incidents: {incidents}")

    scope = root_scope(variables_data)
    actual_outputs = root_public_outputs(scope, contract)
    for name, expected in case.outputs.items():
        actual = actual_outputs.get(name)
        declared_type = OUTPUT_TYPES[name]
        if not exact_type(actual, declared_type):
            raise CheckFailure(
                f"{case.name}: output {name} expected exact type "
                f"{declared_type}, got {type(actual).__name__}: {actual!r}"
            )
        if actual != expected:
            raise CheckFailure(
                f"{case.name}: output {name} expected {expected!r}, "
                f"got {actual!r}"
            )

    executions = get_ci(debug_data, "ElementExecutions", [])
    executed_ids = [
        get_ci(item, "ElementId")
        for item in executions
        if isinstance(item, dict)
    ]
    executed_set = set(executed_ids)
    required = {
        contract.parallel_split_id,
        contract.parallel_join_id,
        contract.root_end_id,
    }
    missing = required - executed_set
    if missing:
        raise CheckFailure(
            f"{case.name}: live execution missed required root nodes "
            f"{sorted(missing)}"
        )
    error_nodes = {contract.error_end_id, contract.error_boundary_id}
    if case.uses_error_boundary:
        if not error_nodes <= executed_set:
            raise CheckFailure(
                f"{case.name}: typed JiraUnavailable path did not execute "
                f"{sorted(error_nodes - executed_set)}"
            )
    elif error_nodes & executed_set:
        raise CheckFailure(
            f"{case.name}: unexpectedly executed JiraUnavailable error path"
        )

    expected_counts = {
        contract.jira_create_id: (
            1 if case.outputs["jiraAction"] == "CreateIssue" else 0
        ),
        contract.jira_update_id: (
            1 if case.outputs["jiraAction"] == "UpdateExisting" else 0
        ),
        contract.slack_send_id: (
            1 if case.outputs["slackAction"] == "PostAlert" else 0
        ),
    }
    for element_id, expected_count in expected_counts.items():
        actual_count = executed_ids.count(element_id)
        if actual_count != expected_count:
            raise CheckFailure(
                f"{case.name}: connector {element_id} expected "
                f"{expected_count} executions, got {actual_count}"
            )
    # PIMS summarizes a marker body's static element in the root trace; prove
    # the iteration cardinality below from per-run outputs and remote files.
    drive_trace_count = executed_ids.count(contract.drive_copy_id)
    if case.outputs["attachmentAction"] == "SaveToDrive":
        if drive_trace_count < 1:
            raise CheckFailure(
                f"{case.name}: live trace never reached Drive copy"
            )
    elif drive_trace_count:
        raise CheckFailure(
            f"{case.name}: no-copy path unexpectedly reached Drive copy"
        )

    correlation = case.inputs["correlationId"]
    if case.outputs["jiraAction"] == "CreateIssue":
        outputs = element_output_records(
            variables_data, contract.jira_create_id
        )
        keys = [
            value
            for value in connector_response_values(outputs, "key")
            if isinstance(value, str)
        ]
        ids = [
            value
            for value in connector_response_values(outputs, "id")
            if isinstance(value, str)
        ]
        if not keys:
            raise CheckFailure(
                f"{case.name}: Jira create returned no issue key: {outputs!r}"
            )
        side_effects.jira_issue_ids.add(ids[0] if ids else keys[0])
        assert_jira_contains_correlation(keys[0], correlation, environment)
    elif case.outputs["jiraAction"] == "UpdateExisting":
        if not update_issue_key:
            raise CheckFailure(f"{case.name}: update scenario has no seed issue")
        assert_jira_contains_correlation(
            update_issue_key, correlation, environment
        )

    if case.outputs["attachmentAction"] == "SaveToDrive":
        outputs = element_output_records(
            variables_data, contract.drive_copy_id
        )
        ids = [
            value
            for value in connector_response_values(outputs, "id")
            if isinstance(value, str)
        ]
        if len(ids) != len(case.attachment_iterations):
            raise CheckFailure(
                f"{case.name}: Drive copy returned {len(ids)} ids for "
                f"{len(case.attachment_iterations)} attachments: {outputs!r}"
            )
        side_effects.drive_file_ids.update(ids)
        flattened = recursive_strings(outputs)
        for attachment_name in case.attachment_iterations:
            if not any(
                correlation in value and attachment_name in value
                for value in flattened
            ):
                raise CheckFailure(
                    f"{case.name}: Drive output does not prove a correlated "
                    f"copy for {attachment_name!r}: {outputs!r}"
                )

    if case.outputs["slackAction"] == "PostAlert":
        outputs = element_output_records(
            variables_data, contract.slack_send_id
        )
        timestamps = [
            value
            for value in connector_response_values(outputs, "ts")
            if isinstance(value, str)
        ]
        if len(timestamps) != 1:
            raise CheckFailure(
                f"{case.name}: Slack send returned no unique timestamp: "
                f"{outputs!r}"
            )
        side_effects.slack_messages.add(
            (environment.slack_channel_id, timestamps[0])
        )


def tail_log(path: Path, limit: int = 5000) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return text[-limit:]


def main() -> int:
    if not BPMN_FILE.is_file():
        raise CheckFailure(f"missing {BPMN_FILE}")
    contract = load_runtime_contract()
    original_hash = sha256(BPMN_FILE)

    validate = run_cli(
        ["uip", "maestro", "bpmn", "validate", str(BPMN_FILE)],
        timeout=180,
    )
    payload_data(validate, "offline BPMN validation")
    environment = discover_live_environment()
    side_effects = ConnectorSideEffectLease(environment)

    with tempfile.TemporaryDirectory(
        prefix="customer-escalation-live-alpha-"
    ) as directory:
        root = Path(directory)
        solution_dir = root / "CustomerEscalationLiveAlphaEval"
        initialized = run_cli(
            ["uip", "solution", "init", str(solution_dir)],
            timeout=120,
        )
        payload_data(initialized, "initialize ephemeral solution")
        solution_files = list(solution_dir.glob("*.uipx"))
        if len(solution_files) != 1:
            raise CheckFailure("solution init did not create exactly one .uipx")
        solution_file = solution_files[0]
        lease = AlphaSolutionLease(solution_file)
        cleanup_failures: list[str] = []
        pending_error: BaseException | None = None

        previous_sigterm = signal.getsignal(signal.SIGTERM)

        def stop_on_sigterm(_signum: int, _frame: Any) -> None:
            raise KeyboardInterrupt("terminated during live Alpha evaluation")

        signal.signal(signal.SIGTERM, stop_on_sigterm)
        try:
            imported = run_cli(
                [
                    "uip",
                    "solution",
                    "projects",
                    "import",
                    str(PROJECT.resolve()),
                    "--solutionFile",
                    str(solution_file),
                ],
                timeout=180,
            )
            payload_data(imported, "import exact BPMN project")
            imported_project = solution_dir / PROJECT.name
            imported_bpmn = imported_project / BPMN_FILE.name
            if sha256(imported_bpmn) != original_hash:
                raise CheckFailure(
                    "solution import changed the submitted BPMN bytes"
                )

            for index, case in enumerate(SCENARIOS, start=1):
                log_file = root / f"{index:02d}-{case.name}.log"
                update_issue_key = None
                if case.outputs["jiraAction"] == "UpdateExisting":
                    update_issue_key = create_seed_jira_issue(
                        case,
                        environment,
                        side_effects,
                    )
                inputs = scenario_inputs(
                    case,
                    environment,
                    duplicate_key=update_issue_key,
                )
                debug = run_cli(
                    [
                        "uip",
                        "maestro",
                        "bpmn",
                        "debug",
                        str(imported_project),
                        "--poll-interval",
                        "500",
                        "--inputs",
                        json.dumps(inputs, separators=(",", ":")),
                    ],
                    timeout=480,
                    log_file=log_file,
                )
                debug_payload = parse_json_output(
                    debug.stdout or debug.stderr,
                    f"{case.name} debug",
                )
                lease.capture_payload(debug_payload)
                lease.capture_manifest()
                debug_data = get_ci(debug_payload, "Data", {})
                instance_id = get_ci(debug_data, "InstanceId")
                if not isinstance(instance_id, str):
                    raise CheckFailure(
                        f"{case.name}: debug returned no instance id "
                        f"(exit {debug.returncode}); log: {tail_log(log_file)}"
                    )

                variables = run_cli(
                    [
                        "uip",
                        "maestro",
                        "bpmn",
                        "debug-instance",
                        "variables-all",
                        instance_id,
                    ],
                    timeout=180,
                )
                variables_payload, variables_data = payload_data(
                    variables,
                    f"{case.name} variables-all",
                )
                lease.capture_payload(variables_payload)
                capture_connector_outputs_for_cleanup(
                    variables_data,
                    contract,
                    environment,
                    side_effects,
                )

                incidents = run_cli(
                    [
                        "uip",
                        "maestro",
                        "bpmn",
                        "debug-instance",
                        "incidents",
                        instance_id,
                    ],
                    timeout=180,
                )
                incidents_payload, incidents_data = payload_data(
                    incidents,
                    f"{case.name} incidents",
                )
                lease.capture_payload(incidents_payload)

                try:
                    assert_scenario(
                        case,
                        contract,
                        debug_data,
                        variables_data,
                        incidents_data,
                        environment,
                        side_effects,
                        update_issue_key=update_issue_key,
                    )
                except CheckFailure as exc:
                    raise CheckFailure(
                        f"{exc}; debug exit={debug.returncode}; "
                        f"debug={json.dumps(debug_payload)[:5000]}; "
                        f"variables={json.dumps(variables_data)[:5000]}; "
                        f"incidents={json.dumps(incidents_data)[:3000]}; "
                        f"log={tail_log(log_file)}"
                    ) from exc
                side_effect_cleanup = side_effects.cleanup()
                if side_effect_cleanup:
                    raise CheckFailure(
                        f"{case.name}: connector cleanup failed: "
                        f"{'; '.join(side_effect_cleanup)}"
                    )
                print(
                    f"PASS live Alpha {index}/{len(SCENARIOS)}: {case.name}"
                )
        except BaseException as exc:
            pending_error = exc
        finally:
            signal.signal(signal.SIGTERM, previous_sigterm)
            cleanup_failures = side_effects.cleanup()
            cleanup_failures.extend(lease.cleanup())

        if cleanup_failures:
            detail = "; ".join(cleanup_failures)
            if pending_error is not None:
                raise CheckFailure(
                    f"{pending_error}; Alpha cleanup also failed: {detail}"
                ) from pending_error
            raise CheckFailure(f"Alpha cleanup failed: {detail}")
        if pending_error is not None:
            raise pending_error

        deleted = ", ".join(sorted(lease.solution_ids))
        print(
            f"PASS: {len(SCENARIOS)} exact-artifact Alpha scenarios; "
            f"ephemeral solution deleted ({deleted})"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error

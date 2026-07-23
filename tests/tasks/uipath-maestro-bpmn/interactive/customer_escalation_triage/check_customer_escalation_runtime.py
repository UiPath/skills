#!/usr/bin/env python3
"""Run hidden escalation cases and verify exact typed process-variable outcomes."""

from __future__ import annotations

import json
import secrets
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, NoReturn, Sequence


BPMN = Path("CustomerEscalationTriage/CustomerEscalationTriage.bpmn")
SOLUTION_STATE = Path("bpmn-debug-solutions.json")
COLD_PLUGIN_MARKER = "unknown command 'maestro'"
OUTPUT_NAMES = {
    "route",
    "severity",
    "engineeringNeeded",
    "jiraAction",
    "attachmentAction",
    "slackAction",
    "responseMode",
    "caseKey",
    "lastAttachmentName",
    "failureReason",
}


def fail(message: str) -> NoReturn:
    raise SystemExit(f"FAIL: {message}")


def run_bpmn(args: Sequence[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
    """Run a BPMN CLI command, retrying only the transient maestro cold-start."""
    command = ["uip", "maestro", "bpmn", *args]
    result: subprocess.CompletedProcess[str] | None = None
    for attempt in range(3):
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        combined = f"{result.stdout}\n{result.stderr}"
        if result.returncode == 0 or COLD_PLUGIN_MARKER not in combined:
            return result
        if attempt < 2:
            time.sleep(2)
    assert result is not None
    return result


def parse_json_output(text: str, label: str) -> Any:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Some CLI builds emit a log line before the JSON envelope. Try each JSON
    # boundary without accepting human-table output.
    for index, character in enumerate(stripped):
        if character not in "[{":
            continue
        try:
            return json.loads(stripped[index:])
        except json.JSONDecodeError:
            continue
    fail(f"{label} did not return JSON:\n{text}")


def get_ci(mapping: Any, *names: str) -> Any:
    if not isinstance(mapping, dict):
        return None
    lowered = {str(key).casefold(): value for key, value in mapping.items()}
    for name in names:
        if name.casefold() in lowered:
            return lowered[name.casefold()]
    return None


def unwrap_data(payload: Any) -> Any:
    if isinstance(payload, dict):
        data = get_ci(payload, "Data")
        if data is not None:
            return data
    return payload


def record_solution(solution_id: Any) -> None:
    if not isinstance(solution_id, str) or not solution_id.strip():
        return
    ids: list[str] = []
    if SOLUTION_STATE.is_file():
        try:
            loaded = json.loads(SOLUTION_STATE.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                ids = [item for item in loaded if isinstance(item, str)]
        except (OSError, json.JSONDecodeError):
            ids = []
    if solution_id not in ids:
        ids.append(solution_id)
        SOLUTION_STATE.write_text(json.dumps(ids, indent=2) + "\n", encoding="utf-8")


def record_solutions_from_payload(payload: Any) -> None:
    if isinstance(payload, list):
        for item in payload:
            record_solutions_from_payload(item)
        return
    if not isinstance(payload, dict):
        return
    for key, value in payload.items():
        if str(key).casefold() == "solutionid":
            record_solution(value)
        else:
            record_solutions_from_payload(value)


def run_json(args: Sequence[str], *, timeout: int, label: str) -> Any:
    result = run_bpmn([*args, "--output", "json"], timeout=timeout)
    payload: Any | None = None
    if result.stdout.strip():
        try:
            payload = parse_json_output(result.stdout, label)
            record_solutions_from_payload(payload)
        except SystemExit:
            if result.returncode == 0:
                raise
    if result.returncode != 0:
        fail(
            f"{label} exited {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    if payload is None:
        fail(f"{label} returned no JSON payload")
    return payload


def collect_named_values(payload: Any) -> dict[str, Any]:
    """Collect exact variable names/ids from supported runtime payload shapes."""
    found: dict[str, Any] = {}

    def visit(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if not isinstance(value, dict):
            return

        name = get_ci(value, "name")
        variable_id = get_ci(value, "id", "variableId")
        has_scalar = any(str(key).casefold() == "value" for key in value)
        scalar = get_ci(value, "value")
        if has_scalar:
            for key in (name, variable_id):
                if isinstance(key, str) and key:
                    found[key] = scalar

        for container_name in ("variables", "globals", "outputs", "values"):
            container = get_ci(value, container_name)
            if isinstance(container, dict):
                for key, item in container.items():
                    found[str(key)] = item

        for child in value.values():
            visit(child)

    visit(unwrap_data(payload))
    return found


def canonical_identifier(value: str) -> str:
    """Match CLI-serialized ids even when separators are removed."""
    return "".join(character for character in value.casefold() if character.isalnum())


def apply_variable_aliases(values: dict[str, Any]) -> dict[str, Any]:
    """Expose runtime values by both serialized variable id and declared name."""
    try:
        root = ET.parse(BPMN).getroot()
    except ET.ParseError as exc:
        fail(f"cannot parse {BPMN} while resolving variable aliases: {exc}")
    namespace = "http://uipath.org/schema/bpmn"
    aliased = dict(values)
    by_canonical = {canonical_identifier(key): value for key, value in values.items()}
    for variable in root.findall(f".//{{{namespace}}}variables/*"):
        variable_id = variable.attrib.get("id")
        name = variable.attrib.get("name")
        if not variable_id or not name:
            continue
        serialized_id = canonical_identifier(variable_id)
        serialized_name = canonical_identifier(name)
        if serialized_id in by_canonical:
            aliased[name] = by_canonical[serialized_id]
        elif serialized_name in by_canonical:
            aliased[name] = by_canonical[serialized_name]
    return aliased


def assert_expected(values: dict[str, Any], expected: dict[str, Any]) -> None:
    if set(expected) != OUTPUT_NAMES:
        fail(f"grader bug: expected output set is {sorted(expected)}, wanted {sorted(OUTPUT_NAMES)}")
    for name, wanted in expected.items():
        if name not in values:
            fail(f"runtime variables do not contain exact name {name!r}; found: {sorted(values)}")
        actual = values[name]
        if type(actual) is not type(wanted):
            fail(
                f"variable {name!r}: expected type {type(wanted).__name__}, "
                f"got {type(actual).__name__} ({actual!r})"
            )
        if actual != wanted:
            fail(f"variable {name!r}: expected exact value {wanted!r}, got {actual!r}")


def assert_no_incidents(payload: Any) -> None:
    data = unwrap_data(payload)
    if isinstance(data, list):
        incidents = data
    elif isinstance(data, dict):
        incidents = get_ci(data, "incidents", "items", "results")
        if incidents is None:
            incidents = []
    else:
        incidents = []
    if isinstance(incidents, list) and incidents:
        fail(f"debug instance reported incidents: {json.dumps(incidents)[:1600]}")


def correlation(run_id: str, suffix: str) -> str:
    return f"E2E/{run_id}:{suffix}#Exact"


def cases() -> list[dict[str, Any]]:
    run_id = secrets.token_hex(6)
    return [
        {
            "name": "mixed-case-enterprise-sev1-new",
            "inputs": {
                "customerTier": "eNtErPrIsE",
                "crmMatchCount": 1,
                "serviceState": "uNaVaIlAbLe",
                "workaroundAvailable": False,
                "duplicateIssueKey": "",
                "attachments": [{"name": "outage.png"}, {"name": "trace.zip"}],
                "agentOutputValid": True,
                "jiraAvailable": True,
                "autoSendEnabled": False,
                "businessImpact": "Every production user is blocked",
                "correlationId": correlation(run_id, "SEV1-NEW"),
            },
            "expected": {
                "route": "NewEscalation",
                "severity": "Sev1",
                "engineeringNeeded": True,
                "jiraAction": "CreateIssue",
                "attachmentAction": "SaveToDrive",
                "slackAction": "PostAlert",
                "responseMode": "Draft",
                "caseKey": correlation(run_id, "SEV1-NEW"),
                "lastAttachmentName": "trace.zip",
                "failureReason": "",
            },
        },
        {
            "name": "degraded-sev2-existing-issue",
            "inputs": {
                "customerTier": "Standard",
                "crmMatchCount": 1,
                "serviceState": "dEgRaDeD",
                "workaroundAvailable": True,
                "duplicateIssueKey": "SUP-4821",
                "attachments": [{"name": "logs.txt"}],
                "agentOutputValid": True,
                "jiraAvailable": True,
                "autoSendEnabled": True,
                "businessImpact": "Orders are delayed but a workaround exists",
                "correlationId": correlation(run_id, "SEV2-DUP"),
            },
            "expected": {
                "route": "ExistingIssue",
                "severity": "Sev2",
                "engineeringNeeded": True,
                "jiraAction": "UpdateExisting",
                "attachmentAction": "SaveToDrive",
                "slackAction": "PostAlert",
                "responseMode": "Draft",
                "caseKey": correlation(run_id, "SEV2-DUP"),
                "lastAttachmentName": "logs.txt",
                "failureReason": "",
            },
        },
        {
            "name": "informational-auto-send",
            "inputs": {
                "customerTier": "Enterprise",
                "crmMatchCount": 1,
                "serviceState": "AVAILABLE",
                "workaroundAvailable": False,
                "duplicateIssueKey": "",
                "attachments": [],
                "agentOutputValid": True,
                "jiraAvailable": False,
                "autoSendEnabled": True,
                "businessImpact": "Informational follow-up with no production impact",
                "correlationId": correlation(run_id, "SEV3-SEND"),
            },
            "expected": {
                "route": "Informational",
                "severity": "Sev3",
                "engineeringNeeded": False,
                "jiraAction": "NoAction",
                "attachmentAction": "NoAttachments",
                "slackAction": "NoAlert",
                "responseMode": "Send",
                "caseKey": correlation(run_id, "SEV3-SEND"),
                "lastAttachmentName": "",
                "failureReason": "",
            },
        },
        {
            "name": "crm-not-found-precedence",
            "inputs": {
                "customerTier": "Enterprise",
                "crmMatchCount": 0,
                "serviceState": "Unavailable",
                "workaroundAvailable": False,
                "duplicateIssueKey": "SUP-IGNORED",
                "attachments": [
                    {"name": "unknown.eml"},
                    {"name": "screenshot.png"},
                ],
                "agentOutputValid": False,
                "jiraAvailable": False,
                "autoSendEnabled": True,
                "businessImpact": "Critical-looking email from an unknown sender",
                "correlationId": correlation(run_id, "CRM-NONE"),
            },
            "expected": {
                "route": "ManualReview",
                "severity": "Unclassified",
                "engineeringNeeded": False,
                "jiraAction": "NoAction",
                "attachmentAction": "HoldForReview",
                "slackAction": "NoAlert",
                "responseMode": "Draft",
                "caseKey": correlation(run_id, "CRM-NONE"),
                "lastAttachmentName": "",
                "failureReason": "CrmNotFound",
            },
        },
        {
            "name": "crm-ambiguous-precedence",
            "inputs": {
                "customerTier": "Standard",
                "crmMatchCount": 2,
                "serviceState": "Degraded",
                "workaroundAvailable": True,
                "duplicateIssueKey": "",
                "attachments": [],
                "agentOutputValid": False,
                "jiraAvailable": False,
                "autoSendEnabled": False,
                "businessImpact": "Two accounts share the sender domain",
                "correlationId": correlation(run_id, "CRM-MULTI"),
            },
            "expected": {
                "route": "ManualReview",
                "severity": "Unclassified",
                "engineeringNeeded": False,
                "jiraAction": "NoAction",
                "attachmentAction": "HoldForReview",
                "slackAction": "NoAlert",
                "responseMode": "Draft",
                "caseKey": correlation(run_id, "CRM-MULTI"),
                "lastAttachmentName": "",
                "failureReason": "CrmAmbiguous",
            },
        },
        {
            "name": "invalid-agent-output-precedence",
            "inputs": {
                "customerTier": "Enterprise",
                "crmMatchCount": 1,
                "serviceState": "Unavailable",
                "workaroundAvailable": False,
                "duplicateIssueKey": "",
                "attachments": [
                    {"name": "classifier.json"},
                    {"name": "body.txt"},
                ],
                "agentOutputValid": False,
                "jiraAvailable": False,
                "autoSendEnabled": True,
                "businessImpact": "Classifier returned malformed structured output",
                "correlationId": correlation(run_id, "AGENT-BAD"),
            },
            "expected": {
                "route": "ManualReview",
                "severity": "Unclassified",
                "engineeringNeeded": False,
                "jiraAction": "NoAction",
                "attachmentAction": "HoldForReview",
                "slackAction": "NoAlert",
                "responseMode": "Draft",
                "caseKey": correlation(run_id, "AGENT-BAD"),
                "lastAttachmentName": "",
                "failureReason": "InvalidAgentOutput",
            },
        },
        {
            "name": "jira-unavailable-retains-severity",
            "inputs": {
                "customerTier": "ENTERPRISE",
                "crmMatchCount": 1,
                "serviceState": "UNAVAILABLE",
                "workaroundAvailable": False,
                "duplicateIssueKey": "SUP-9000",
                "attachments": [{"name": "outage.png"}],
                "agentOutputValid": True,
                "jiraAvailable": False,
                "autoSendEnabled": True,
                "businessImpact": "Confirmed outage but Jira is unavailable",
                "correlationId": correlation(run_id, "JIRA-DOWN"),
            },
            "expected": {
                "route": "ManualReview",
                "severity": "Sev1",
                "engineeringNeeded": True,
                "jiraAction": "NoAction",
                "attachmentAction": "HoldForReview",
                "slackAction": "NoAlert",
                "responseMode": "Draft",
                "caseKey": correlation(run_id, "JIRA-DOWN"),
                "lastAttachmentName": "",
                "failureReason": "JiraUnavailable",
            },
        },
        {
            "name": "sev3-duplicate-ignores-jira-unavailability",
            "inputs": {
                "customerTier": "Standard",
                "crmMatchCount": 1,
                "serviceState": "aVaIlAbLe",
                "workaroundAvailable": False,
                "duplicateIssueKey": "SUP-7777",
                "attachments": [],
                "agentOutputValid": True,
                "jiraAvailable": False,
                "autoSendEnabled": True,
                "businessImpact": "Existing informational issue while Jira is unavailable",
                "correlationId": correlation(run_id, "SEV3-DUP-JIRA-DOWN"),
            },
            "expected": {
                "route": "ExistingIssue",
                "severity": "Sev3",
                "engineeringNeeded": False,
                "jiraAction": "UpdateExisting",
                "attachmentAction": "NoAttachments",
                "slackAction": "NoAlert",
                "responseMode": "Draft",
                "caseKey": correlation(run_id, "SEV3-DUP-JIRA-DOWN"),
                "lastAttachmentName": "",
                "failureReason": "",
            },
        },
        {
            "name": "enterprise-unavailable-with-workaround-is-sev2",
            "inputs": {
                "customerTier": "EnTeRpRiSe",
                "crmMatchCount": 1,
                "serviceState": "UnAvAiLaBlE",
                "workaroundAvailable": True,
                "duplicateIssueKey": "",
                "attachments": [],
                "agentOutputValid": True,
                "jiraAvailable": True,
                "autoSendEnabled": False,
                "businessImpact": "Enterprise outage mitigated by a working workaround",
                "correlationId": correlation(run_id, "SEV2-WORKAROUND"),
            },
            "expected": {
                "route": "NewEscalation",
                "severity": "Sev2",
                "engineeringNeeded": True,
                "jiraAction": "CreateIssue",
                "attachmentAction": "NoAttachments",
                "slackAction": "PostAlert",
                "responseMode": "Draft",
                "caseKey": correlation(run_id, "SEV2-WORKAROUND"),
                "lastAttachmentName": "",
                "failureReason": "",
            },
        },
        {
            "name": "whitespace-duplicate-is-new-escalation",
            "inputs": {
                "customerTier": "Standard",
                "crmMatchCount": 1,
                "serviceState": "Degraded",
                "workaroundAvailable": True,
                "duplicateIssueKey": " \t  ",
                "attachments": [
                    {"name": "first.txt"},
                    {"name": "second.txt"},
                    {"name": "final.txt"},
                ],
                "agentOutputValid": True,
                "jiraAvailable": True,
                "autoSendEnabled": True,
                "businessImpact": "A stakeholder supplied whitespace as the issue key",
                "correlationId": correlation(run_id, "TRIM-DUP"),
            },
            "expected": {
                "route": "NewEscalation",
                "severity": "Sev2",
                "engineeringNeeded": True,
                "jiraAction": "CreateIssue",
                "attachmentAction": "SaveToDrive",
                "slackAction": "PostAlert",
                "responseMode": "Draft",
                "caseKey": correlation(run_id, "TRIM-DUP"),
                "lastAttachmentName": "final.txt",
                "failureReason": "",
            },
        },
    ]


def verify_case(case: dict[str, Any]) -> None:
    debug = run_json(
        ["debug", "--bpmn-file", str(BPMN), "--inputs", json.dumps(case["inputs"])],
        timeout=420,
        label=f"debug for {case['name']}",
    )
    debug_data = unwrap_data(debug)
    instance_id = get_ci(debug_data, "instanceId")
    final_status = get_ci(debug_data, "finalStatus", "status")

    if not isinstance(instance_id, str) or not instance_id:
        fail(f"debug for {case['name']} returned no instanceId: {debug_data}")
    if not isinstance(final_status, str) or final_status.casefold() != "completed":
        fail(f"debug for {case['name']} did not complete: finalStatus={final_status!r}")

    variables = run_json(
        ["debug-instance", "variables-all", instance_id],
        timeout=120,
        label=f"variables for {case['name']}",
    )
    assert_expected(apply_variable_aliases(collect_named_values(variables)), case["expected"])

    incidents = run_json(
        ["debug-instance", "incidents", instance_id],
        timeout=120,
        label=f"incidents for {case['name']}",
    )
    assert_no_incidents(incidents)
    print(f"OK: {case['name']} completed with all ten exact typed outputs")


def main() -> None:
    if not BPMN.is_file():
        fail(f"missing BPMN file: {BPMN}")
    hidden_cases = cases()
    if len(hidden_cases) != 10:
        fail("grader bug: expected exactly ten hidden cases")
    failures: list[str] = []
    for case in hidden_cases:
        try:
            verify_case(case)
        except SystemExit as exc:
            failures.append(f"{case['name']}: {exc}")
        except subprocess.TimeoutExpired as exc:
            failures.append(
                f"{case['name']}: command timed out after {exc.timeout} seconds"
            )
    if failures:
        fail(
            f"{len(failures)}/{len(hidden_cases)} hidden cases failed:\n- "
            + "\n- ".join(failures)
        )


if __name__ == "__main__":
    main()

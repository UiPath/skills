#!/usr/bin/env python3
"""Verify the interactive escalation artifact without prescribing element ids."""

from __future__ import annotations

import itertools
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, NoReturn


_directory = os.path.dirname(os.path.abspath(__file__))
while _directory != os.path.dirname(_directory) and not os.path.isdir(
    os.path.join(_directory, "_shared")
):
    _directory = os.path.dirname(_directory)
sys.path.insert(0, _directory)

from _shared.bpmn_check import require_no_private_connector_values  # noqa: E402


PROJECT = Path("CustomerEscalationTriageSolution") / "CustomerEscalationTriage"
BPMN = PROJECT / "CustomerEscalationTriage.bpmn"
EVIDENCE = PROJECT / "registry-evidence"

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
UIPATH_NS = "http://uipath.org/schema/bpmn"

EXPECTED_INPUTS = {
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
EXPECTED_OUTPUTS = {
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
FLOW_NODE_KINDS = {
    "startEvent",
    "endEvent",
    "boundaryEvent",
    "intermediateCatchEvent",
    "intermediateThrowEvent",
    "task",
    "serviceTask",
    "sendTask",
    "receiveTask",
    "userTask",
    "businessRuleTask",
    "scriptTask",
    "callActivity",
    "subProcess",
    "exclusiveGateway",
    "parallelGateway",
    "inclusiveGateway",
    "eventBasedGateway",
}
ACTIVITY_KINDS = {
    "task",
    "serviceTask",
    "sendTask",
    "receiveTask",
    "userTask",
    "businessRuleTask",
    "scriptTask",
    "callActivity",
}

CONNECTOR_ACCOUNTS = {
    "uipath-atlassian-jira": (
        "is-sandboxes-test@uipath.com-uipath-sandbox-380"
    ),
    "uipath-google-drive": "is.sandboxes.test@gmail.com",
    "uipath-salesforce-slack": "is-sandboxes",
}
CONNECTION_FOLDER_KEY = "5da18ec0-7de1-4e57-aaf1-ddc8a369c199"
CONNECTOR_OPERATIONS = {
    ("uipath-atlassian-jira", "curated_create_issue"),
    ("uipath-atlassian-jira", "curated_edit_issue"),
    ("uipath-google-drive", "copyFile"),
    ("uipath-salesforce-slack", "send_message_to_channel_v2"),
}
EXPECTED_CONNECTOR_ACTIVITIES = {
    ("uipath-atlassian-jira", "/curated_create_issue"): "POST",
    (
        "uipath-atlassian-jira",
        "/curated_edit_issue/{issueIdOrKey}",
    ): "PUT",
    ("uipath-google-drive", "/copyFile"): "POST",
    (
        "uipath-salesforce-slack",
        "/send_message_to_channel_v2",
    ): "POST",
}
EXPECTED_CONNECTOR_OBJECTS = {
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
EXPECTED_CONNECTOR_INPUTS = {
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


def fail(message: str) -> NoReturn:
    raise SystemExit(f"FAIL: {message}")


def load_project_json(name: str) -> dict[str, Any]:
    path = PROJECT / name
    if not path.is_file():
        fail(f"missing project metadata: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")
    if not isinstance(payload, dict):
        fail(f"{path} must contain a JSON object")
    return payload


def require_cli_project_metadata(
    bpmn_name: str,
    start_id: str,
    entry_point_id: str,
) -> None:
    project = load_project_json("project.uiproj")
    if project.get("Name") != PROJECT.name:
        fail(f"project.uiproj Name must be {PROJECT.name}")
    if project.get("ProjectType") != "ProcessOrchestration":
        fail("project.uiproj ProjectType must be ProcessOrchestration")
    if "main" in project:
        fail("project.uiproj must not duplicate the runtime main path")

    expected_main = f"/content/{bpmn_name}#{start_id}"
    operate = load_project_json("operate.json")
    if operate.get("main") != expected_main:
        fail(f"operate.json main must be {expected_main}")
    if operate.get("contentType") != "ProcessOrchestration":
        fail("operate.json contentType must be ProcessOrchestration")

    entries = load_project_json("entry-points.json").get("entryPoints")
    if not isinstance(entries, list) or len(entries) != 1:
        fail("entry-points.json must contain exactly one entry point")
    entry = entries[0]
    if not isinstance(entry, dict):
        fail("entry-points.json entry point must be an object")
    if entry.get("uniqueId") != entry_point_id:
        fail("entry-points.json uniqueId must match uipath:entryPointId")
    if entry.get("filePath") != expected_main:
        fail(f"entry-points.json filePath must be {expected_main}")
    if entry.get("type") != "ProcessOrchestration":
        fail("entry-points.json type must be ProcessOrchestration")

    descriptor = load_project_json("package-descriptor.json")
    expected_files = {
        "operate.json": "operate.json",
        "entry-points.json": "entry-points.json",
        "bindings.json": "bindings_v2.json",
        bpmn_name: bpmn_name,
    }
    if descriptor.get("files") != expected_files:
        fail("package-descriptor.json must preserve the CLI files map")
    load_project_json("bindings_v2.json")


def q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def identifier_token(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def normalization_field_roles(field_names: set[str]) -> set[str]:
    """Map semantically named normalized fields to the contract values."""
    roles: set[str] = set()
    for field_name in field_names:
        token = identifier_token(field_name)
        if "tier" in token:
            roles.add("tier")
        if ("service" in token and "state" in token) or token == "state":
            roles.add("serviceState")
        if "duplicate" in token:
            roles.add("duplicateIssueKey")
    return roles


def required_string_schema_properties(
    declaration: ET.Element,
) -> set[str]:
    """Return fields that a declared object schema requires as strings."""
    if declaration.attrib.get("type") not in {"object", "json", "jsonSchema"}:
        return set()
    body = (declaration.text or "").strip()
    if not body:
        return set()
    try:
        schema = json.loads(body)
    except json.JSONDecodeError:
        return set()
    properties = schema.get("properties") if isinstance(schema, dict) else None
    required = schema.get("required") if isinstance(schema, dict) else None
    if (
        not isinstance(schema, dict)
        or get_ci(schema, "type") != "object"
        or not isinstance(properties, dict)
        or not isinstance(required, list)
    ):
        return set()
    return {
        property_name
        for property_name, property_schema in properties.items()
        if property_name in required
        and get_ci(property_schema, "type") == "string"
    }


def structured_normalization_roles(declaration: ET.Element) -> set[str]:
    """Return fully required string normalization roles in one object."""
    return normalization_field_roles(
        required_string_schema_properties(declaration)
    )


def structured_normalization_roles_in_conditions(
    variable_id: str, condition_blob: str
) -> set[str]:
    """Return normalized object properties visibly consumed by gateways."""
    fields = set(
        re.findall(
            rf"\bvars\.{re.escape(variable_id)}\.([A-Za-z_$][\w$]*)",
            condition_blob,
        )
    )
    return normalization_field_roles(fields)


def get_ci(mapping: Any, name: str) -> Any:
    if not isinstance(mapping, dict):
        return None
    wanted = name.casefold()
    for key, value in mapping.items():
        if str(key).casefold() == wanted:
            return value
    return None


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
    fail(f"{label} returned invalid JSON")


def child_refs(element: ET.Element, kind: str) -> list[str]:
    return [
        (child.text or "").strip()
        for child in element.findall(f"./{q(BPMN_NS, kind)}")
        if (child.text or "").strip()
    ]


def mapping_outputs(element: ET.Element) -> list[ET.Element]:
    return element.findall(
        f".//{q(UIPATH_NS, 'output')}"
    )


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


def connector_inputs(
    element: ET.Element,
) -> dict[tuple[str, str], ET.Element]:
    activity = element.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'activity')}"
    )
    if activity is None:
        return {}
    result: dict[tuple[str, str], ET.Element] = {}
    for item in activity.findall(f"./{q(UIPATH_NS, 'input')}"):
        name = item.attrib.get("name", "")
        target = item.attrib.get("target", "")
        if not name or not target:
            fail(
                f"connector activity {element.attrib.get('id')!r} has an "
                "input without both name and target"
            )
        key = (target, name)
        if key in result:
            fail(
                f"connector activity {element.attrib.get('id')!r} repeats "
                f"input {key}"
            )
        result[key] = item
    return result


def connector_json_body(
    element: ET.Element,
    inputs: dict[tuple[str, str], ET.Element],
) -> dict[str, Any]:
    body = inputs.get(("body", "body"))
    if body is None:
        fail(f"connector activity {element.attrib.get('id')!r} has no body")
    raw = body.attrib.get("value")
    if raw is None:
        raw = body.text or ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(
            f"connector activity {element.attrib.get('id')!r} body is not "
            f"JSON: {exc}"
        )
    if not isinstance(payload, dict):
        fail(
            f"connector activity {element.attrib.get('id')!r} body must be "
            "a JSON object"
        )
    return payload


def connector_input_value(item: ET.Element) -> str:
    value = item.attrib.get("value")
    if value is not None:
        return value
    return item.text or ""


def normalized_exact_reference(value: Any) -> str | None:
    """Canonicalize a bare UiPath variable expression without changing meaning."""
    if not isinstance(value, str):
        return None
    expression = value.strip()
    if expression.startswith("=js:"):
        expression = expression[4:].strip()
    elif expression.startswith("="):
        expression = expression[1:].strip()
    else:
        return None

    while expression.startswith("(") and expression.endswith(")"):
        depth = 0
        closes_at_end = False
        for index, character in enumerate(expression):
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth < 0:
                    return None
                if depth == 0:
                    closes_at_end = index == len(expression) - 1
                    break
        if not closes_at_end:
            break
        expression = expression[1:-1].strip()

    if re.fullmatch(
        r"vars\.[A-Za-z0-9_-]+(?:\.[A-Za-z_$][\w$]*)*",
        expression,
    ) is None:
        return None
    return f"={expression}"


def javascript_code_mask(source: str) -> str:
    """Mask JS literals/comments while retaining executable template code.

    The checker performs deliberately small structural checks over JavaScript,
    so the mask must preserve source offsets.  Static template text and regex
    literals are data, while an unescaped ``${...}`` interpolation is
    executable JavaScript and must remain visible to mutation/lineage checks.
    """
    masked = list(source)
    regex_prefix_keywords = {
        "await",
        "case",
        "delete",
        "do",
        "else",
        "in",
        "instanceof",
        "new",
        "of",
        "return",
        "throw",
        "typeof",
        "void",
        "yield",
    }

    def blank(index: int) -> None:
        if source[index] not in "\r\n":
            masked[index] = " "

    def mask_quoted(index: int, quote: str) -> int:
        cursor = index
        escaped = False
        while cursor < len(source):
            character = source[cursor]
            blank(cursor)
            if cursor == index:
                cursor += 1
                continue
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                return cursor + 1
            cursor += 1
        return cursor

    def mask_line_comment(index: int) -> int:
        cursor = index
        while cursor < len(source) and source[cursor] not in "\r\n":
            blank(cursor)
            cursor += 1
        return cursor

    def mask_block_comment(index: int) -> int:
        cursor = index
        while cursor < len(source):
            if source.startswith("*/", cursor):
                blank(cursor)
                if cursor + 1 < len(source):
                    blank(cursor + 1)
                return cursor + 2
            blank(cursor)
            cursor += 1
        return cursor

    def mask_regex_literal(index: int) -> int | None:
        cursor = index + 1
        escaped = False
        in_character_class = False
        while cursor < len(source):
            character = source[cursor]
            if character in "\r\n":
                return None
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == "[":
                in_character_class = True
            elif character == "]" and in_character_class:
                in_character_class = False
            elif character == "/" and not in_character_class:
                end = cursor + 1
                while end < len(source) and (
                    source[end].isalpha() or source[end] in "$_"
                ):
                    end += 1
                for position in range(index, end):
                    blank(position)
                return end
            cursor += 1
        return None

    def scan_template(index: int) -> int:
        blank(index)
        cursor = index + 1
        while cursor < len(source):
            character = source[cursor]
            if character == "\\":
                blank(cursor)
                if cursor + 1 < len(source):
                    blank(cursor + 1)
                cursor += 2
                continue
            if character == "`":
                blank(cursor)
                return cursor + 1
            if source.startswith("${", cursor):
                # `${` and its closing `}` delimit executable code.  Mask only
                # the dollar so offsets and brace balance remain intact.
                blank(cursor)
                cursor = scan_code(cursor + 2, stop_at_template_brace=True)
                continue
            blank(cursor)
            cursor += 1
        return cursor

    def scan_code(
        index: int,
        *,
        stop_at_template_brace: bool = False,
    ) -> int:
        cursor = index
        brace_depth = 0
        can_start_regex = True
        while cursor < len(source):
            character = source[cursor]
            following = source[cursor + 1] if cursor + 1 < len(source) else ""

            if (
                stop_at_template_brace
                and character == "}"
                and brace_depth == 0
            ):
                return cursor + 1
            if character.isspace():
                cursor += 1
                continue
            if character in {'"', "'"}:
                cursor = mask_quoted(cursor, character)
                can_start_regex = False
                continue
            if character == "`":
                cursor = scan_template(cursor)
                can_start_regex = False
                continue
            if character == "/" and following == "/":
                cursor = mask_line_comment(cursor)
                continue
            if character == "/" and following == "*":
                cursor = mask_block_comment(cursor)
                continue
            if character == "/" and can_start_regex:
                regex_end = mask_regex_literal(cursor)
                if regex_end is not None:
                    cursor = regex_end
                    can_start_regex = False
                    continue
            if character.isalpha() or character in "_$":
                end = cursor + 1
                while end < len(source) and (
                    source[end].isalnum() or source[end] in "_$"
                ):
                    end += 1
                can_start_regex = (
                    source[cursor:end] in regex_prefix_keywords
                )
                cursor = end
                continue
            if character.isdigit():
                end = cursor + 1
                while end < len(source) and (
                    source[end].isalnum() or source[end] in "._"
                ):
                    end += 1
                cursor = end
                can_start_regex = False
                continue
            if character == "{":
                brace_depth += 1
                can_start_regex = True
            elif character == "}":
                brace_depth = max(0, brace_depth - 1)
                can_start_regex = False
            elif character in ")]":
                can_start_regex = False
            elif character == ".":
                can_start_regex = False
            elif character in "([,:;=!?&|+-*%^~<>":
                can_start_regex = True
            elif character == "/":
                # A non-regex slash is a division operator; an expression may
                # begin on its right.
                can_start_regex = True
            cursor += 1
        return cursor

    scan_code(0)
    return "".join(masked)


def single_return_object_body(script_body: str, label: str) -> str:
    """Accept one terminal object return, excluding comma-operator swaps."""
    executable = javascript_code_mask(script_body)
    returns = list(re.finditer(r"\breturn\b", executable))
    if len(returns) != 1:
        fail(f"{label} must contain exactly one return statement")
    cursor = returns[0].end()
    while (
        cursor < len(executable)
        and executable[cursor] in " \t\f\v"
    ):
        cursor += 1
    if cursor >= len(executable) or executable[cursor] != "{":
        fail(f"{label} must return one object")

    start = cursor
    depth = 0
    end: int | None = None
    for cursor in range(start, len(executable)):
        character = executable[cursor]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                end = cursor
                break
            if depth < 0:
                break
    if end is None:
        fail(f"{label} returned an unbalanced object")
    if re.fullmatch(r"\s*;?\s*", executable[end + 1 :]) is None:
        fail(
            f"{label} must return one terminal object without a trailing "
            "comma expression"
        )
    return script_body[start + 1 : end]


def require_variable_reference(
    value: Any,
    declaration: ET.Element,
    label: str,
) -> None:
    variable_id = declaration.attrib["id"]
    if (
        not isinstance(value, str)
        or variable_id not in referenced_variable_ids(value)
    ):
        fail(f"{label} must reference vars.{variable_id}")


def require_exact_variable_property_reference(
    value: Any,
    declaration: ET.Element,
    property_name: str,
    label: str,
) -> None:
    variable_id = declaration.attrib["id"]
    expected = f"vars.{variable_id}.{property_name}"
    if normalized_exact_reference(value) != f"={expected}":
        fail(
            f"{label} must use exact ScriptTask response field ={expected}"
        )


def require_semantic_reference(
    value: Any,
    tokens: set[str],
    label: str,
) -> None:
    lexical = identifier_token(value)
    missing = {token for token in tokens if token not in lexical}
    if not isinstance(value, str) or not value.startswith("=") or missing:
        fail(
            f"{label} must be a dynamic expression referencing "
            f"{sorted(tokens)}"
        )


def require_connector_request_contract(
    element: ET.Element,
    key: tuple[str, str],
    variables: dict[str, ET.Element],
) -> None:
    inputs = connector_inputs(element)
    required = EXPECTED_CONNECTOR_INPUTS[key]
    allowed = required | OPTIONAL_CONNECTOR_INPUTS.get(key, set())
    if not required <= set(inputs) or not set(inputs) <= allowed:
        fail(
            f"connector activity {key} must use exact registry input "
            f"targets/names; required {sorted(required)}, allowed "
            f"{sorted(allowed)}, got {sorted(inputs)}"
        )
    body = connector_json_body(element, inputs)

    if key == ("uipath-atlassian-jira", "/curated_create_issue"):
        fields = body.get("fields")
        if not isinstance(fields, dict) or set(fields) != {
            "project",
            "issuetype",
            "reporter",
            "summary",
            "description",
        }:
            fail(
                "Jira create body must contain the exact fields project, "
                "issuetype, reporter, summary, and description"
            )
        if (
            not isinstance(fields["project"], dict)
            or set(fields["project"]) != {"key"}
        ):
            fail("Jira create project must use the registry field key")
        if (
            not isinstance(fields["issuetype"], dict)
            or set(fields["issuetype"]) != {"id"}
        ):
            fail("Jira create issuetype must use the registry field id")
        if (
            not isinstance(fields["reporter"], dict)
            or set(fields["reporter"]) != {"id"}
        ):
            fail("Jira create reporter must use the registry field id")
        require_variable_reference(
            fields["project"]["key"],
            variables["jiraProjectKey"],
            "Jira create fields.project.key",
        )
        require_variable_reference(
            fields["issuetype"]["id"],
            variables["jiraIssueTypeId"],
            "Jira create fields.issuetype.id",
        )
        require_variable_reference(
            fields["reporter"]["id"],
            variables["jiraReporterAccountId"],
            "Jira create fields.reporter.id",
        )
        require_variable_reference(
            fields["summary"],
            variables["correlationId"],
            "Jira create fields.summary",
        )
        require_variable_reference(
            fields["description"],
            variables["correlationId"],
            "Jira create fields.description",
        )
    elif key[1] == "/curated_edit_issue/{issueIdOrKey}":
        fields = body.get("fields")
        if not isinstance(fields, dict) or set(fields) != {"description"}:
            fail(
                "Jira update body must write correlation evidence through "
                "fields.description"
            )
        require_semantic_reference(
            connector_input_value(inputs[("path", "issueIdOrKey")]),
            {"duplicate", "issue", "key"},
            "Jira update issueIdOrKey",
        )
        require_variable_reference(
            connector_input_value(inputs[("query", "project")]),
            variables["jiraProjectKey"],
            "Jira update project query",
        )
        require_variable_reference(
            connector_input_value(inputs[("query", "issuetype")]),
            variables["jiraIssueTypeId"],
            "Jira update issuetype query",
        )
        require_variable_reference(
            fields["description"],
            variables["correlationId"],
            "Jira update fields.description",
        )
    elif key == ("uipath-google-drive", "/copyFile"):
        if set(body) != {"destinationFolder", "name"}:
            fail(
                "Drive copy body must use exact registry fields "
                "destinationFolder and name"
            )
        require_semantic_reference(
            connector_input_value(inputs[("query", "fileId")]),
            {"drive", "file", "id"},
            "Drive copy fileId",
        )
        require_variable_reference(
            body["destinationFolder"],
            variables["driveDestinationFolderId"],
            "Drive copy destinationFolder",
        )
        require_semantic_reference(
            body["name"],
            {"copy", "name"},
            "Drive copy name",
        )
    elif key[0] == "uipath-salesforce-slack":
        if set(body) != {"channel", "messageToSend"}:
            fail(
                "Slack body must use exact registry fields channel and "
                "messageToSend"
            )
        if inputs[("query", "send_as")].attrib.get("value") != "bot":
            fail("Slack send_as query input must be the literal bot")
        require_variable_reference(
            body["channel"],
            variables["slackChannelId"],
            "Slack channel",
        )
        for name in ("correlationId", "route", "severity"):
            require_variable_reference(
                body["messageToSend"],
                variables[name],
                f"Slack messageToSend {name}",
            )


def require_connector_activities(
    process: ET.Element,
    activities: list[ET.Element],
    variables: dict[str, ET.Element],
) -> dict[tuple[str, str], ET.Element]:
    observed: dict[tuple[str, str], ET.Element] = {}
    for element in activities:
        if local(element.tag) != "sendTask":
            fail(
                f"connector activity {element.attrib.get('id')!r} must use "
                "the registry bpmn:SendTask placement"
            )
        context = connector_context(element)
        connector_key = context.get("connectorKey", "")
        path = context.get("path", "")
        key = (connector_key, path)
        if key not in EXPECTED_CONNECTOR_ACTIVITIES:
            fail(
                f"unexpected connector activity {element.attrib.get('id')!r}: "
                f"{key}"
            )
        if key in observed:
            fail(f"duplicate connector activity for {key}")
        expected_method = EXPECTED_CONNECTOR_ACTIVITIES[key]
        if not context.get("activity"):
            fail(
                f"connector activity {key} is missing the registry primary "
                "activity value"
            )
        if not context.get("operation"):
            fail(
                f"connector activity {key} is missing runtime operation"
            )
        if context.get("objectName") != EXPECTED_CONNECTOR_OBJECTS[key]:
            fail(
                f"connector activity {key} must use registry objectName "
                f"{EXPECTED_CONNECTOR_OBJECTS[key]!r}"
            )
        if context.get("method") != expected_method:
            fail(
                f"connector activity {key} must use method "
                f"{expected_method!r}"
            )
        connection_ref = context.get("connection", "")
        folder_ref = context.get("folderKey", "")
        if not re.fullmatch(r"=bindings\.[A-Za-z_][\w.-]*", connection_ref):
            fail(f"connector activity {key} has no connection binding")
        if not re.fullmatch(r"=bindings\.[A-Za-z_][\w.-]*", folder_ref):
            fail(f"connector activity {key} has no folder binding")
        require_connector_request_contract(element, key, variables)
        observed[key] = element
    if set(observed) != set(EXPECTED_CONNECTOR_ACTIVITIES):
        missing = set(EXPECTED_CONNECTOR_ACTIVITIES) - set(observed)
        fail(f"missing required connector activities: {sorted(missing)}")

    bindings_parent = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'bindings')}"
    )
    if bindings_parent is None:
        fail("connector process is missing uipath:bindings")
    bindings = {
        item.attrib.get("id"): item
        for item in bindings_parent.findall(f"./{q(UIPATH_NS, 'binding')}")
        if item.attrib.get("id")
    }
    for key, element in observed.items():
        context = connector_context(element)
        for field, property_attribute in (
            ("connection", "ConnectionId"),
            ("folderKey", "folderKey"),
        ):
            binding_id = context[field].split(".", 1)[1]
            binding = bindings.get(binding_id)
            if binding is None:
                fail(f"connector activity {key} references missing {binding_id}")
            if binding.attrib.get("elementId") != element.attrib.get("id"):
                fail(
                    f"binding {binding_id} must be scoped to connector "
                    f"activity {element.attrib.get('id')!r}"
                )
            if binding.attrib.get("resource") != "Connection":
                fail(f"binding {binding_id} must be a Connection resource")
            if binding.attrib.get("propertyAttribute") != property_attribute:
                fail(
                    f"binding {binding_id} must use propertyAttribute "
                    f"{property_attribute!r}"
                )
            if not binding.attrib.get("resourceKey"):
                fail(f"binding {binding_id} is missing resourceKey")

    bindings_file = PROJECT / "bindings_v2.json"
    try:
        resources_payload = json.loads(
            bindings_file.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"could not read {bindings_file}: {exc}")
    resources = resources_payload.get("resources")
    if not isinstance(resources, list):
        fail("bindings_v2.json has no resources list")
    connection_resources = [
        resource
        for resource in resources
        if isinstance(resource, dict)
        and resource.get("resource") == "Connection"
    ]
    resource_keys = {
        resource.get("key")
        for resource in connection_resources
        if resource.get("key")
    }
    binding_resource_keys = {
        item.attrib.get("resourceKey")
        for item in bindings.values()
        if item.attrib.get("propertyAttribute") == "ConnectionId"
    }
    if len(resource_keys) != 3 or resource_keys != binding_resource_keys:
        fail(
            "bindings_v2.json must contain exactly the three Connection "
            "resources referenced by the BPMN"
        )
    return observed


def find_registry_evidence(
    extension_type: str,
    evidence_dir: Path = EVIDENCE,
) -> list[tuple[Path, dict[str, Any], dict[str, Any]]]:
    """Find registry-get responses by content, independent of filename."""
    matches: list[tuple[Path, dict[str, Any], dict[str, Any]]] = []
    for path in sorted(evidence_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        entry = get_ci(get_ci(payload, "Data"), "ExtensionType")
        if (
            isinstance(entry, dict)
            and get_ci(entry, "ExtensionType") == extension_type
        ):
            matches.append((path, payload, entry))
    if not matches:
        names = sorted(path.name for path in evidence_dir.glob("*.json"))
        fail(
            f"missing exact {extension_type} registry-get evidence under "
            f"{evidence_dir}; inspected {names}"
        )
    return matches


def require_usable_registry_template(
    extension_type: str,
    entry: dict[str, Any],
    path: Path,
) -> None:
    template = get_ci(entry, "XmlTemplate")
    if not isinstance(template, str):
        fail(f"{path} has no usable XmlTemplate for {extension_type}")
    if "<uipath:mapping" not in template or "<uipath:type" not in template:
        fail(f"{path} XmlTemplate is missing the registry wrapper contract")
    accepted_mapping_types = {
        "BPMN.ScriptTask": {"BPMN.ScriptTask", "BPMN.Variables"},
        "BPMN.Variables": {"BPMN.Variables"},
    }[extension_type]
    if not any(
        f'value="{mapping_type}"' in template
        for mapping_type in accepted_mapping_types
    ):
        fail(
            f"{path} XmlTemplate does not contain a registry-served "
            f"{extension_type} mapping contract"
        )


def load_registry_evidence(extension_type: str) -> dict[str, Any]:
    candidates = find_registry_evidence(extension_type)

    current = subprocess.run(
        [
            "uip",
            "maestro",
            "bpmn",
            "registry",
            "get",
            extension_type,
            "--output",
            "json",
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    if current.returncode != 0:
        fail(
            f"could not independently refresh {extension_type} registry evidence: "
            f"{current.stderr or current.stdout}"
        )
    live_payload = parse_json_output(
        current.stdout, f"live registry get for {extension_type}"
    )
    live_entry = get_ci(get_ci(live_payload, "Data"), "ExtensionType")
    exact = [
        candidate
        for candidate in candidates
        if candidate[1] == live_payload
    ]
    if not exact:
        paths = [str(candidate[0]) for candidate in candidates]
        fail(
            f"saved registry responses {paths} are not the exact current "
            f"response for {extension_type}"
        )
    path, _payload, entry = exact[0]
    if entry != live_entry:
        fail(f"live registry response for {extension_type} has an unexpected shape")

    expected_element = {
        "BPMN.ScriptTask": "bpmn:ScriptTask",
        "BPMN.Variables": "bpmn:Task",
    }[extension_type]
    if str(get_ci(entry, "BpmnElement") or "").casefold() != expected_element.casefold():
        fail(f"{path} has an unexpected BpmnElement")
    if str(get_ci(entry, "ExtensionTag") or "").casefold() != "uipath:mapping":
        fail(f"{path} does not identify the registry-owned uipath:mapping wrapper")
    require_usable_registry_template(extension_type, entry, path)
    return entry


def run_json_command(arguments: list[str], label: str) -> Any:
    completed = subprocess.run(
        [*arguments, "--output", "json"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    payload = parse_json_output(
        completed.stdout or completed.stderr,
        label,
    )
    if (
        completed.returncode != 0
        or str(get_ci(payload, "Result") or "").casefold() != "success"
    ):
        fail(f"{label} failed: {get_ci(payload, 'Message') or payload}")
    return payload


def discover_connector_connections() -> dict[str, dict[str, Any]]:
    payload = run_json_command(
        ["uip", "is", "connections", "list", "--all-folders"],
        "tenant-wide connection discovery",
    )
    rows = get_ci(payload, "Data")
    if not isinstance(rows, list):
        fail("tenant-wide connection discovery returned no connection list")
    discovered: dict[str, dict[str, Any]] = {}
    for connector_key, account_name in CONNECTOR_ACCOUNTS.items():
        matches = [
            row
            for row in rows
            if isinstance(row, dict)
            and get_ci(row, "ConnectorKey") == connector_key
            and get_ci(row, "Name") == account_name
            and get_ci(row, "FolderKey") == CONNECTION_FOLDER_KEY
            and str(get_ci(row, "State") or "").casefold() == "enabled"
        ]
        if len(matches) != 1:
            fail(
                f"expected one enabled {connector_key} connection named "
                f"{account_name!r}, found {len(matches)}"
            )
        discovered[connector_key] = matches[0]
    return discovered


def require_connector_registry_evidence() -> None:
    connections = discover_connector_connections()
    saved: dict[tuple[str, str], list[tuple[Path, dict[str, Any]]]] = {}
    for path in sorted(EVIDENCE.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        data = get_ci(payload, "Data")
        entry = get_ci(data, "ExtensionType")
        enrichment = get_ci(data, "IsEnrichment")
        if (
            not isinstance(entry, dict)
            or get_ci(entry, "ExtensionType") != "Intsvc.ActivityExecution"
            or not isinstance(enrichment, dict)
        ):
            continue
        connector_key = get_ci(enrichment, "ElementKey")
        object_name = get_ci(enrichment, "Name")
        key = (connector_key, object_name)
        if key in CONNECTOR_OPERATIONS:
            saved.setdefault(key, []).append((path, payload))

    missing = CONNECTOR_OPERATIONS - set(saved)
    if missing:
        fail(f"missing enriched connector registry evidence: {sorted(missing)}")

    for connector_key, object_name in sorted(CONNECTOR_OPERATIONS):
        connection_id = str(get_ci(connections[connector_key], "Id"))
        live = run_json_command(
            [
                "uip",
                "maestro",
                "bpmn",
                "registry",
                "get",
                "Intsvc.ActivityExecution",
                "--connection-id",
                connection_id,
                "--object-name",
                object_name,
            ],
            f"live registry get for {connector_key}/{object_name}",
        )
        exact = [
            path
            for path, payload in saved[(connector_key, object_name)]
            if payload == live
        ]
        if not exact:
            fail(
                f"saved evidence for {connector_key}/{object_name} is not "
                "the exact current enriched registry response"
            )
        entry = get_ci(get_ci(live, "Data"), "ExtensionType")
        if str(get_ci(entry, "BpmnElement") or "").casefold() != (
            "bpmn:SendTask".casefold()
        ):
            fail(f"{exact[0]} has an unexpected connector BPMN element")
        if str(get_ci(entry, "ExtensionTag") or "").casefold() != (
            "uipath:activity".casefold()
        ):
            fail(f"{exact[0]} does not use uipath:activity")
        template = get_ci(entry, "XmlTemplate")
        if not isinstance(template, str) or "<uipath:activity" not in template:
            fail(f"{exact[0]} has no usable connector activity template")


def require_unique_ids(root: ET.Element) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for element in root.iter():
        element_id = element.attrib.get("id")
        if not element_id:
            continue
        if element_id in seen:
            duplicates.add(element_id)
        seen.add(element_id)
    if duplicates:
        fail(f"duplicate BPMN/XML ids: {sorted(duplicates)}")


def require_variables(
    process: ET.Element,
    start_id: str,
    end_id: str,
) -> tuple[dict[str, ET.Element], dict[str, str]]:
    container = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'variables')}"
    )
    if container is None:
        fail("process is missing uipath:variables")

    declarations_by_name: dict[str, list[ET.Element]] = defaultdict(list)
    ids_to_names: dict[str, str] = {}
    for variable in container:
        name = variable.attrib.get("name")
        variable_id = variable.attrib.get("id")
        if not name or not variable_id:
            fail("every process variable must have a non-empty name and id")
        if variable_id in ids_to_names:
            fail(f"duplicate process variable id: {variable_id}")
        declarations_by_name[name].append(variable)
        ids_to_names[variable_id] = name

    declarations: dict[str, ET.Element] = {}
    public_input_ids: dict[str, str] = {}
    public_output_ids: dict[str, str] = {}
    for name, expected_type in EXPECTED_INPUTS.items():
        candidates = declarations_by_name.get(name, [])
        public = [item for item in candidates if local(item.tag) == "input"]
        internal = [
            item for item in candidates if local(item.tag) == "inputOutput"
        ]
        if len(public) != 1 or len(internal) != 1:
            fail(
                f"input {name!r} needs one public input and one mutable "
                "inputOutput declaration"
            )
        if public[0].attrib.get("type") != expected_type or internal[
            0
        ].attrib.get("type") != expected_type:
            fail(f"input {name!r} has the wrong public/internal type")
        if public[0].attrib.get("elementId") != start_id:
            fail(f"public input {name!r} must bind to {start_id!r}")
        declarations[name] = internal[0]
        public_input_ids[name] = public[0].attrib["id"]

    for name, expected_type in EXPECTED_OUTPUTS.items():
        candidates = declarations_by_name.get(name, [])
        public = [item for item in candidates if local(item.tag) == "output"]
        internal = [
            item for item in candidates if local(item.tag) == "inputOutput"
        ]
        if len(public) != 1 or len(internal) != 1:
            fail(
                f"output {name!r} needs one public output and one mutable "
                "inputOutput declaration"
            )
        if public[0].attrib.get("type") != expected_type or internal[
            0
        ].attrib.get("type") != expected_type:
            fail(f"output {name!r} has the wrong public/internal type")
        if public[0].attrib.get("elementId") != end_id:
            fail(f"public output {name!r} must bind to {end_id!r}")
        declarations[name] = internal[0]
        public_output_ids[name] = public[0].attrib["id"]

    for name, candidates in declarations_by_name.items():
        internal = [
            item for item in candidates if local(item.tag) == "inputOutput"
        ]
        if name not in declarations and len(internal) == 1:
            declarations[name] = internal[0]

    start = process.find(f"./{q(BPMN_NS, 'startEvent')}[@id='{start_id}']")
    end = process.find(f"./{q(BPMN_NS, 'endEvent')}[@id='{end_id}']")
    if start is None or end is None:
        fail("could not resolve root start/end for public variable bridges")
    start_outputs = mapping_outputs(start)
    end_outputs = mapping_outputs(end)
    for name in EXPECTED_INPUTS:
        target_id = declarations[name].attrib["id"]
        expected_source = f"=vars.{public_input_ids[name]}"
        if not any(
            item.attrib.get("var") == target_id
            and item.attrib.get("source") == expected_source
            for item in start_outputs
        ):
            fail(f"root StartEvent does not bridge public input {name!r}")
    for name in EXPECTED_OUTPUTS:
        source_id = declarations[name].attrib["id"]
        public_id = public_output_ids[name]
        if not any(
            item.attrib.get("var") == public_id
            and item.attrib.get("source") == f"=vars.{source_id}"
            for item in end_outputs
        ):
            fail(f"root EndEvent does not bridge public output {name!r}")
    return declarations, ids_to_names


def build_scope_graph(
    scope: ET.Element,
) -> tuple[
    dict[str, ET.Element],
    dict[str, ET.Element],
    dict[str, list[str]],
    dict[str, list[str]],
]:
    nodes = {
        element.attrib["id"]: element
        for element in scope
        if local(element.tag) in FLOW_NODE_KINDS and element.attrib.get("id")
    }
    flows = {
        element.attrib["id"]: element
        for element in scope.findall(f"./{q(BPMN_NS, 'sequenceFlow')}")
        if element.attrib.get("id")
    }
    if not flows:
        fail(f"scope {scope.attrib.get('id', '<unknown>')!r} has no sequence flows")

    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for flow_id, flow in flows.items():
        source = flow.attrib.get("sourceRef")
        target = flow.attrib.get("targetRef")
        if source not in nodes or target not in nodes:
            fail(
                f"sequence flow {flow_id!r} has unresolved same-scope refs "
                f"{source!r}->{target!r}"
            )
        outgoing[source].append(target)
        incoming[target].append(source)
        if child_refs(nodes[source], "outgoing").count(flow_id) != 1:
            fail(f"source {source!r} must declare outgoing {flow_id!r} exactly once")
        if child_refs(nodes[target], "incoming").count(flow_id) != 1:
            fail(f"target {target!r} must declare incoming {flow_id!r} exactly once")

    for node_id, node in nodes.items():
        expected_in = sorted(
            flow_id
            for flow_id, flow in flows.items()
            if flow.attrib.get("targetRef") == node_id
        )
        expected_out = sorted(
            flow_id
            for flow_id, flow in flows.items()
            if flow.attrib.get("sourceRef") == node_id
        )
        if sorted(child_refs(node, "incoming")) != expected_in:
            fail(f"node {node_id!r} incoming declarations do not match its flows")
        if sorted(child_refs(node, "outgoing")) != expected_out:
            fail(f"node {node_id!r} outgoing declarations do not match its flows")
    return nodes, flows, dict(outgoing), dict(incoming)


def walk(origin: str, graph: dict[str, list[str]], *, stop: str | None = None) -> set[str]:
    visited: set[str] = set()
    queue: deque[str] = deque([origin])
    while queue:
        current = queue.popleft()
        if current in visited or current == stop:
            continue
        visited.add(current)
        queue.extend(graph.get(current, []))
    return visited


def require_scope_reachability(
    nodes: dict[str, ET.Element],
    outgoing: dict[str, list[str]],
    incoming: dict[str, list[str]],
    start_id: str,
    end_ids: set[str],
    *,
    boundary_ids: set[str] | None = None,
) -> None:
    boundary_ids = boundary_ids or set()
    reachable = walk(start_id, outgoing)
    for boundary_id in boundary_ids:
        reachable.update(walk(boundary_id, outgoing))
    missing = sorted(set(nodes) - reachable)
    if missing:
        fail(f"flow nodes are unreachable from start {start_id!r}: {missing}")

    can_reach_end: set[str] = set()
    queue: deque[str] = deque(end_ids)
    while queue:
        current = queue.popleft()
        if current in can_reach_end:
            continue
        can_reach_end.add(current)
        queue.extend(incoming.get(current, []))
    trapped = sorted(set(nodes) - can_reach_end)
    if trapped:
        fail(f"flow nodes cannot reach an end event: {trapped}")


def require_gateway_contract(
    scope: ET.Element,
    flows: dict[str, ET.Element],
    *,
    require_diverging: bool = True,
) -> list[str]:
    conditions: list[str] = []
    diverging = 0
    for gateway in scope.findall(f"./{q(BPMN_NS, 'exclusiveGateway')}"):
        outgoing_ids = child_refs(gateway, "outgoing")
        if len(outgoing_ids) < 2:
            continue
        diverging += 1
        default_id = gateway.attrib.get("default")
        if not default_id or default_id not in outgoing_ids:
            fail(
                f"exclusive gateway {gateway.attrib.get('id')!r} needs an "
                "explicit default flow"
            )
        for flow_id in outgoing_ids:
            condition = flows[flow_id].find(
                f"./{q(BPMN_NS, 'conditionExpression')}"
            )
            if flow_id == default_id:
                if condition is not None and (condition.text or "").strip():
                    fail(f"default flow {flow_id!r} must not have a condition")
                continue
            expression = (condition.text or "").strip() if condition is not None else ""
            if not expression.startswith("="):
                fail(f"non-default flow {flow_id!r} needs an '=' condition")
            if any(token in expression for token in ("===", "!==", "&&", "||")):
                if not expression.startswith("=js:"):
                    fail(
                        f"flow {flow_id!r} uses JavaScript-only operators "
                        "without '=js:'"
                    )
            conditions.append(expression)
    if require_diverging and diverging == 0:
        fail(f"scope {scope.attrib.get('id')!r} has no visible exclusive decision")
    return conditions


def referenced_variable_ids(expressions: str) -> set[str]:
    """Return exact `vars.<id>` references without prefix collisions."""
    return set(re.findall(r"\bvars\.([A-Za-z0-9_-]+)", expressions))


def mapping_input_body(element: ET.Element) -> str:
    return element.attrib.get("value") or element.text or ""


def require_script_runtime_contract(script: ET.Element) -> None:
    script_id = script.attrib.get("id", "<unknown>")
    if script.attrib.get("scriptFormat") != "JavaScript":
        fail(f"ScriptTask {script_id!r} must use scriptFormat='JavaScript'")
    version = script.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'scriptVersion')}"
    )
    if version is None or version.attrib.get("value") != "v3":
        fail(f"ScriptTask {script_id!r} must use uipath:scriptVersion v3")
    mapping = script.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'mapping')}"
    )
    if mapping is None:
        fail(f"ScriptTask {script_id!r} is missing its mapping")
    type_element = mapping.find(f"./{q(UIPATH_NS, 'type')}")
    if type_element is None or type_element.attrib.get("value") != "BPMN.Variables":
        fail(
            f"ScriptTask {script_id!r} must use the current "
            "BPMN.Variables serializer contract"
        )
    schema = mapping.find(
        f"./{q(UIPATH_NS, 'context')}/{q(UIPATH_NS, 'inputSchema')}"
    )
    if schema is None or schema.attrib.get("type") != "jsonSchema":
        fail(f"ScriptTask {script_id!r} is missing inputSchema context")
    try:
        schema_body = json.loads((schema.text or "").strip())
    except json.JSONDecodeError:
        fail(f"ScriptTask {script_id!r} inputSchema is not valid JSON")
    properties = get_ci(schema_body, "properties") or {}

    mapping_input = mapping.find(f"./{q(UIPATH_NS, 'input')}")
    if (
        mapping_input is None
        or mapping_input.attrib.get("name") != "args"
        or mapping_input.attrib.get("type") != "json"
        or mapping_input.attrib.get("target") != "bodyField"
    ):
        fail(f"ScriptTask {script_id!r} must use the args bodyField input")
    try:
        args = json.loads(mapping_input_body(mapping_input).strip())
    except json.JSONDecodeError:
        fail(f"ScriptTask {script_id!r} args input is not valid runtime JSON")
    required_args = {"vars": "=vars", "metadata": "=metadata"}
    for name, expected in required_args.items():
        if get_ci(args, name) != expected or get_ci(properties, name) is None:
            fail(
                f"ScriptTask {script_id!r} must pass and declare {name!r}"
            )
    marker = script.find(
        f"./{q(BPMN_NS, 'multiInstanceLoopCharacteristics')}"
    )
    if marker is not None:
        if get_ci(args, "iterator") != "=iterator" or get_ci(
            properties, "iterator"
        ) is None:
            fail(
                f"multi-instance ScriptTask {script_id!r} must pass and "
                "declare iterator"
            )
    output_names = {
        item.attrib.get("name")
        for item in mapping.findall(f"./{q(UIPATH_NS, 'output')}")
    }
    if not {"scriptResponse", "Error"} <= output_names:
        fail(
            f"ScriptTask {script_id!r} must map standard scriptResponse "
            "and Error outputs"
        )


def require_registry_activities(
    root: ET.Element,
    variables: dict[str, ET.Element],
) -> tuple[ET.Element, list[ET.Element], list[ET.Element]]:
    load_registry_evidence("BPMN.ScriptTask")
    load_registry_evidence("BPMN.Variables")

    scripts: list[ET.Element] = []
    variable_tasks: list[ET.Element] = []
    connector_activities: list[ET.Element] = []
    unexpected: list[tuple[str, str | None]] = []
    for element in root.iter():
        if local(element.tag) not in ACTIVITY_KINDS:
            continue
        type_elements = element.findall(
            f"./{q(BPMN_NS, 'extensionElements')}//{q(UIPATH_NS, 'type')}"
        )
        values = [item.attrib.get("value") for item in type_elements]
        if len(values) != 1 or not values[0]:
            fail(
                f"activity {element.attrib.get('id')!r} must contain exactly "
                f"one registry type; found {values}"
            )
        if values[0] == "BPMN.Variables" and local(element.tag) == "scriptTask":
            scripts.append(element)
        elif values[0] == "BPMN.Variables" and local(element.tag) == "task":
            variable_tasks.append(element)
        elif (
            values[0] == "Intsvc.ActivityExecution"
            and local(element.tag) == "sendTask"
        ):
            connector_activities.append(element)
        else:
            unexpected.append((local(element.tag), values[0]))

    if unexpected:
        fail(f"process contains unsupported/unrequested activities: {unexpected}")
    process = root.find(f"./{q(BPMN_NS, 'process')}")
    if process is None:
        fail("BPMN is missing its root process")
    require_connector_activities(process, connector_activities, variables)
    if len(scripts) != 3:
        fail(
            "expected exactly three data-only ScriptTasks "
            f"(normalization, attachment marker, reducer), found {len(scripts)}"
        )
    declared_variables = {
        item.attrib.get("id"): item
        for item in root.findall(
            f"./{q(BPMN_NS, 'process')}/"
            f"{q(BPMN_NS, 'extensionElements')}/"
            f"{q(UIPATH_NS, 'variables')}/*"
        )
        if item.attrib.get("id")
    }
    for script in scripts:
        require_script_runtime_contract(script)
        script_id = script.attrib.get("id")
        for output in mapping_outputs(script):
            variable = declared_variables.get(output.attrib.get("var"))
            if variable is None:
                fail(
                    f"ScriptTask {script_id!r} maps undeclared variable "
                    f"{output.attrib.get('var')!r}"
                )
            if output.attrib.get("name") == "Error" and (
                variable.attrib.get("name") != "Error"
                or variable.attrib.get("elementId") != script_id
            ):
                fail(
                    f"ScriptTask {script_id!r} Error output needs a "
                    "same-named variable scoped to that script"
                )
    normalization_candidates = [
        script
        for script in scripts
        if "trim" in (
            script.findtext(f"./{q(BPMN_NS, 'script')}", default="") or ""
        ).casefold()
        and (
            "tolowercase"
            in (
                script.findtext(
                    f"./{q(BPMN_NS, 'script')}", default=""
                )
                or ""
            ).casefold()
            or "touppercase"
            in (
                script.findtext(
                    f"./{q(BPMN_NS, 'script')}", default=""
                )
                or ""
            ).casefold()
        )
    ]
    if len(normalization_candidates) != 1:
        fail("expected exactly one case/whitespace normalization ScriptTask")
    if len(variable_tasks) < 8:
        fail(
            "expected substantial registry-derived Variables activity usage "
            f"across decisions and workstreams, found {len(variable_tasks)}"
        )
    return normalization_candidates[0], scripts, variable_tasks


def require_normalization_script(
    script: ET.Element,
    variables: dict[str, ET.Element],
    ids_to_names: dict[str, str],
    variable_tasks: list[ET.Element],
) -> set[str]:
    mapping_input = script.find(
        f"./{q(BPMN_NS, 'extensionElements')}//{q(UIPATH_NS, 'input')}"
    )
    if mapping_input is None or mapping_input.attrib.get("name") != "args":
        fail("normalization ScriptTask must use the registry args input mapping")
    script_body = (
        script.findtext(f"./{q(BPMN_NS, 'script')}", default="") or ""
    )
    mapped_input_ids = referenced_variable_ids(script_body)
    required_input_ids = {
        variables[name].attrib["id"]
        for name in (
            "customerTier",
            "serviceState",
            "duplicateIssueKey",
        )
    }
    missing_inputs = sorted(
        variable_id
        for variable_id in required_input_ids
        if variable_id not in mapped_input_ids
    )
    if missing_inputs:
        fail(f"normalization ScriptTask input mapping misses variables: {missing_inputs}")

    lowered = script_body.casefold()
    if "tolowercase" not in lowered and "touppercase" not in lowered:
        fail("normalization script does not perform case normalization")
    if "trim" not in lowered:
        fail("normalization script does not trim duplicateIssueKey")
    forbidden = {
        "manualreview",
        "existingissue",
        "newescalation",
        "informational",
        "sev1",
        "sev2",
        "sev3",
        "crmnotfound",
        "crmambiguous",
        "invalidagentoutput",
        "jiraunavailable",
        "updateexisting",
        "createissue",
        "postalert",
        "send",
    }
    leaked = sorted(token for token in forbidden if token in lowered)
    if leaked:
        fail(
            "normalization script hides business decisions that must remain "
            f"visible in gateways/tasks: {leaked}"
        )

    script_outputs = mapping_outputs(script)
    declarations_by_id = {
        declaration.attrib["id"]: declaration
        for declaration in variables.values()
        if declaration.attrib.get("id")
    }
    response_ids = {
        output.attrib["var"]
        for output in script_outputs
        if output.attrib.get("name") == "scriptResponse"
        and output.attrib.get("var")
    }
    normalization_outputs = list(script_outputs)
    correlation_id = variables["correlationId"].attrib["id"]
    case_key_id = variables["caseKey"].attrib["id"]
    for task in variable_tasks:
        task_outputs = mapping_outputs(task)
        if any(
            response_ids
            & referenced_variable_ids(output.attrib.get("source", ""))
            for output in task_outputs
        ):
            # A Variables task that extracts the ScriptTask response is part of
            # the same normalization contract. Include all of its assignments
            # so a direct correlationId -> caseKey copy remains visible without
            # forcing an unnecessary round trip through JavaScript.
            normalization_outputs.extend(task_outputs)
        else:
            # A visible Variables assignment immediately after normalization
            # may preserve correlationId directly instead of needlessly
            # round-tripping it through the ScriptTask response.
            normalization_outputs.extend(
                output
                for output in task_outputs
                if output.attrib.get("var") == case_key_id
                and output.attrib.get("source", "").strip()
                == f"=vars.{correlation_id}"
            )

    for output in normalization_outputs:
        source = output.attrib.get("source", "")
        for response_id in response_ids:
            properties = re.findall(
                rf"\bvars\.{re.escape(response_id)}\."
                r"([A-Za-z_$][\w$]*)\b",
                source,
            )
            if not properties:
                continue
            declaration = declarations_by_id.get(response_id)
            typed_properties = (
                required_string_schema_properties(declaration)
                if declaration is not None
                else set()
            )
            missing = sorted(set(properties) - typed_properties)
            if missing:
                fail(
                    "normalization ScriptTask response dereferences fields "
                    "that are not required strings in an object schema: "
                    f"{missing}"
                )

    targets = {
        output.attrib["var"]
        for output in normalization_outputs
        if output.attrib.get("var") in ids_to_names
    }
    forbidden_targets = {
        variables[name].attrib["id"]
        for name in (
            "route",
            "severity",
            "engineeringNeeded",
            "jiraAction",
            "attachmentAction",
            "slackAction",
            "responseMode",
            "lastAttachmentName",
            "failureReason",
        )
        if name in variables
    }
    leaked_targets = sorted(
        ids_to_names[variable_id]
        for variable_id in targets & forbidden_targets
    )
    if leaked_targets:
        fail(
            "normalization ScriptTask must not initialize or assign business "
            f"decision/downstream outputs: {leaked_targets}"
        )
    case_key_targets = {
        output.attrib["var"]
        for output in normalization_outputs
        if output.attrib.get("var") in ids_to_names
        and (
            "casekey" in identifier_token(output.attrib.get("name", ""))
            or "casekey"
            in identifier_token(ids_to_names[output.attrib["var"]])
        )
    }
    if not case_key_targets:
        fail("normalization ScriptTask must preserve correlationId into caseKey")
    case_result_properties = {"caseKey"}
    for output in normalization_outputs:
        if output.attrib.get("var") not in case_key_targets:
            continue
        source = output.attrib.get("source", "")
        for response_id in response_ids:
            match = re.search(
                rf"\bvars\.{re.escape(response_id)}\."
                r"([A-Za-z_$][\w$]*)\b",
                source,
            )
            if match:
                case_result_properties.add(match.group(1))
    direct_copy = any(
        re.search(
            rf"\b{re.escape(property_name)}\s*:\s*"
            rf"vars\.{re.escape(correlation_id)}\b",
            script_body,
            flags=re.IGNORECASE,
        )
        for property_name in case_result_properties
    )
    alias_copy = False
    for match in re.finditer(
        rf"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
        rf"vars\.{re.escape(correlation_id)}"
        r"(?:\s*\|\|\s*[\"']{2})?\s*;",
        script_body,
        flags=re.IGNORECASE,
    ):
        alias = match.group(1)
        if any(
            re.search(
                rf"\b{re.escape(property_name)}\s*:\s*"
                rf"{re.escape(alias)}\b",
                script_body,
                flags=re.IGNORECASE,
            )
            for property_name in case_result_properties
        ):
            alias_copy = True
            break
    visible_copy = any(
        output.attrib.get("var") in case_key_targets
        and output.attrib.get("source", "").strip()
        == f"=vars.{correlation_id}"
        for output in normalization_outputs
    )
    if not direct_copy and not alias_copy and not visible_copy:
        fail(
            "normalization contract must copy correlationId exactly into "
            "caseKey, either in the ScriptTask result or its associated "
            "Variables extraction task"
        )
    string_targets = {
        variable_id
        for variable_id in targets
        if variable_id in declarations_by_id
        and declarations_by_id[variable_id].attrib.get("type") == "string"
        and ids_to_names.get(variable_id) not in {"scriptResponse", "Error"}
    }
    structured_targets = {
        variable_id
        for variable_id in targets
        if variable_id in declarations_by_id
        and structured_normalization_roles(declarations_by_id[variable_id])
        == {"tier", "serviceState", "duplicateIssueKey"}
    }
    if len(string_targets - case_key_targets) < 3 and not structured_targets:
        fail(
            "normalization ScriptTask needs either distinct string outputs or "
            "one typed structured result for tier, service state, and trimmed "
            "duplicate key"
        )
    return targets


def require_jira_update_uses_normalized_duplicate(
    process: ET.Element,
    script: ET.Element,
    variables: dict[str, ET.Element],
    ids_to_names: dict[str, str],
    variable_tasks: list[ET.Element],
) -> None:
    mapping = script.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'mapping')}"
    )
    if mapping is None:
        fail("normalization ScriptTask is missing its Variables mapping")
    declarations_by_id = {
        declaration.attrib["id"]: declaration
        for declaration in variables.values()
        if declaration.attrib.get("id")
    }

    def has_duplicate_key_semantics(value: str) -> bool:
        token = identifier_token(value)
        return "duplicate" in token and "key" in token

    script_body = (
        script.findtext(f"./{q(BPMN_NS, 'script')}", default="") or ""
    )
    script_executable = javascript_code_mask(script_body)
    script_declarations: dict[str, list[str]] = defaultdict(list)
    for match in re.finditer(
        r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
        r"([^;\n]+)",
        script_executable,
    ):
        script_declarations[match.group(1)].append(
            script_body[match.start(2) : match.end(2)].strip()
        )
    returned_body = single_return_object_body(
        script_body,
        "normalization ScriptTask",
    )
    returned_executable = javascript_code_mask(returned_body)

    def returned_property_expression(property_name: str) -> str:
        if "..." in returned_executable:
            fail(
                "normalization ScriptTask result must not use object spread"
            )
        property_occurrences = re.findall(
            rf"(?:^|,)\s*{re.escape(property_name)}\s*"
            rf"(?::|(?=,|$))",
            returned_executable,
        )
        if len(property_occurrences) > 1:
            fail(
                "normalization ScriptTask result must return duplicate key "
                f"{property_name!r} exactly once"
            )
        if len(property_occurrences) != 1:
            return ""
        explicit = re.search(
            rf"(?:^|,)\s*{re.escape(property_name)}\s*:"
            rf"(.*?)(?=,\s*[A-Za-z_$][\w$]*\s*:|$)",
            returned_executable,
            flags=re.DOTALL,
        )
        if explicit is not None:
            return returned_body[
                explicit.start(1) : explicit.end(1)
            ].strip()
        if re.search(
            rf"(?:^|,)\s*{re.escape(property_name)}\s*(?=,|$)",
            returned_executable,
        ):
            return property_name
        return ""

    def stable_local_assignment(identifier: str) -> str | None:
        declarations = script_declarations.get(identifier, [])
        if len(declarations) != 1:
            return None
        direct_writes = re.findall(
            rf"(?<![\w$.]){re.escape(identifier)}\s*=(?!=)",
            script_executable,
        )
        mutation = re.search(
            rf"(?<![\w$.]){re.escape(identifier)}\s*"
            r"(?:\+\+|--|\+=|-=|\*=|/=|%=)"
            rf"|(?:\+\+|--)\s*{re.escape(identifier)}\b"
            rf"|\b{re.escape(identifier)}\s*(?:\.|\[)[^=;\n]*"
            r"=(?!=)",
            script_executable,
        )
        if len(direct_writes) != 1 or mutation is not None:
            return None
        return declarations[0]

    def resolve_script_assignment(
        expression: str,
        seen: set[str] | None = None,
    ) -> str:
        stripped = expression.strip()
        if not re.fullmatch(r"[A-Za-z_$][\w$]*", stripped):
            return stripped
        visited = set() if seen is None else set(seen)
        assignment = stable_local_assignment(stripped)
        if stripped in visited or assignment is None:
            return stripped
        visited.add(stripped)
        return resolve_script_assignment(
            assignment,
            visited,
        )

    raw_duplicate_id = variables["duplicateIssueKey"].attrib["id"]
    if re.search(
        rf"\bvars\.{re.escape(raw_duplicate_id)}\s*"
        r"(?:=(?!=)|\+\+|--|\+=|-=|\*=|/=|%=)",
        script_executable,
    ):
        fail(
            "normalization ScriptTask must not mutate duplicateIssueKey "
            "before trimming it"
        )

    def is_exact_trimmed_duplicate(property_name: str) -> bool:
        expression = resolve_script_assignment(
            returned_property_expression(property_name)
        )
        normalized = re.sub(r"\s", "", expression)
        raw = rf"vars\.{re.escape(raw_duplicate_id)}"
        return any(
            re.fullmatch(pattern, normalized) is not None
            for pattern in (
                rf"\(?{raw}(?:\|\|(?:\"\"|''))?\)?\.trim\(\)",
                rf"String\(\(?{raw}(?:\|\|(?:\"\"|''))?\)?\)"
                r"\.trim\(\)",
            )
        )

    allowed: set[str] = set()
    mapping_output_items = mapping.findall(f"./{q(UIPATH_NS, 'output')}")
    for output in mapping_output_items:
        variable_id = output.attrib.get("var")
        if (
            not variable_id
            or output.attrib.get("name") != "scriptResponse"
            or output.attrib.get("type") != "jsonSchema"
            or output.attrib.get("source", "").strip()
            != "=result.response"
        ):
            continue
        declaration = declarations_by_id.get(variable_id)
        if declaration is None:
            continue
        try:
            schema = json.loads((declaration.text or "").strip())
        except json.JSONDecodeError:
            continue
        properties = (
            schema.get("properties")
            if isinstance(schema, dict)
            else None
        )
        if (
            not isinstance(schema, dict)
            or get_ci(schema, "type") != "object"
            or not isinstance(properties, dict)
        ):
            continue
        for property_name in properties:
            property_schema = properties.get(property_name)
            required = schema.get("required")
            if (
                has_duplicate_key_semantics(property_name)
                and get_ci(property_schema, "type") == "string"
                and isinstance(required, list)
                and property_name in required
                and is_exact_trimmed_duplicate(property_name)
            ):
                allowed.add(f"=vars.{variable_id}.{property_name}")

    for output in mapping_output_items:
        variable_id = output.attrib.get("var")
        declaration = declarations_by_id.get(variable_id or "")
        normalized_source = normalized_exact_reference(
            output.attrib.get("source", "")
        )
        if (
            not variable_id
            or output.attrib.get("name") == "scriptResponse"
            or declaration is None
            or declaration.attrib.get("type") != "string"
            or normalized_source not in allowed
            or not has_duplicate_key_semantics(
                " ".join(
                    (
                        output.attrib.get("name", ""),
                        ids_to_names.get(variable_id, ""),
                    )
                )
            )
        ):
            continue
        allowed.add(f"=vars.{variable_id}")

    # Permit a visible Variables extraction from the typed ScriptTask result,
    # but only when its exact source is already trusted and its target remains
    # semantically explicit. Iterate to support a short visible copy chain.
    changed = True
    while changed:
        changed = False
        for task in variable_tasks:
            for output in mapping_outputs(task):
                source = output.attrib.get("source", "").strip()
                normalized_source = normalized_exact_reference(source)
                target = output.attrib.get("var", "")
                declaration = declarations_by_id.get(target)
                if (
                    normalized_source not in allowed
                    or declaration is None
                    or declaration.attrib.get("type") != "string"
                    or not has_duplicate_key_semantics(
                        " ".join(
                            (
                                output.attrib.get("name", ""),
                                ids_to_names.get(target, ""),
                            )
                        )
                    )
                ):
                    continue
                candidate = f"=vars.{target}"
                if candidate not in allowed:
                    allowed.add(candidate)
                    changed = True

    update_activities = [
        node
        for node in process.findall(f".//{q(BPMN_NS, 'sendTask')}")
        if connector_context(node).get("connectorKey")
        == "uipath-atlassian-jira"
        and connector_context(node).get("path")
        == "/curated_edit_issue/{issueIdOrKey}"
    ]
    if len(update_activities) != 1:
        fail("expected exactly one Jira update connector activity")
    update_inputs = connector_inputs(update_activities[0])
    path_input = update_inputs.get(("path", "issueIdOrKey"))
    actual = (
        connector_input_value(path_input)
        if path_input is not None
        else ""
    )
    normalized_actual = normalized_exact_reference(actual)
    if not allowed or normalized_actual not in allowed:
        fail(
            "Jira update issueIdOrKey must exactly consume the normalized "
            f"duplicate-key result; allowed {sorted(allowed)}, got {actual!r}"
        )


def output_names_in_elements(
    elements: list[ET.Element], ids_to_names: dict[str, str]
) -> set[str]:
    names: set[str] = set()
    for element in elements:
        for output in mapping_outputs(element):
            mapped = ids_to_names.get(output.attrib.get("var", ""))
            if mapped:
                names.add(mapped)
            if output.attrib.get("name"):
                names.add(output.attrib["name"])
    return names


def require_material_jira_intent(
    elements: list[ET.Element],
    ids_to_names: dict[str, str],
) -> None:
    outputs = [
        output
        for element in elements
        for output in mapping_outputs(element)
        if (
            output.attrib.get("name") == "jiraAction"
            or ids_to_names.get(output.attrib.get("var", "")) == "jiraAction"
        )
    ]
    for output in outputs:
        target = output.attrib.get("var", "")
        if output.attrib.get("source", "").strip() == f"=vars.{target}":
            fail(
                "Jira intent workstream contains a no-op self-assignment "
                "instead of materially deriving jiraAction"
            )
    sources = "\n".join(output.attrib.get("source", "") for output in outputs)
    missing = [
        literal
        for literal in ("UpdateExisting", "CreateIssue", "NoAction")
        if literal not in sources
    ]
    if missing:
        fail(
            "Jira intent workstream must visibly assign all route outcomes; "
            f"missing {missing}"
        )


def forbid_downstream_intents_in_assessment(
    subprocess: ET.Element,
    ids_to_names: dict[str, str],
) -> None:
    forbidden = {
        "jiraAction",
        "attachmentAction",
        "slackAction",
        "responseMode",
        "lastAttachmentName",
    }
    leaked = sorted(
        output_name
        for output_name in output_names_in_elements(
            [subprocess, *list(subprocess.iter())],
            ids_to_names,
        )
        if output_name in forbidden
    )
    if leaked:
        fail(
            "assessment subprocess precomputes outputs owned by downstream "
            f"parallel workstreams: {leaked}"
        )


def output_literal_exists(
    elements: list[ET.Element],
    ids_to_names: dict[str, str],
    variable_name: str,
    literal: str,
) -> bool:
    for element in elements:
        for output in mapping_outputs(element):
            mapped_name = ids_to_names.get(output.attrib.get("var", ""))
            if mapped_name != variable_name and output.attrib.get("name") != variable_name:
                continue
            if literal in (output.attrib.get("source") or ""):
                return True
    return False


def mapping_propagates_semantic(
    output: ET.Element,
    ids_to_names: dict[str, str],
    semantic_name: str,
    expected_type: str,
) -> bool:
    target_id = output.attrib.get("var", "")
    return (
        output.attrib.get("type") == expected_type
        and target_id in ids_to_names
        and (
            output.attrib.get("name") == semantic_name
            or ids_to_names[target_id] == semantic_name
        )
        and bool(referenced_variable_ids(output.attrib.get("source", "")))
    )


def require_assessment_subprocess(
    root: ET.Element,
    process: ET.Element,
    variables: dict[str, ET.Element],
    ids_to_names: dict[str, str],
    normalization_targets: set[str],
) -> tuple[ET.Element, ET.Element]:
    subprocesses = [
        item
        for item in process.findall(f"./{q(BPMN_NS, 'subProcess')}")
        if item.find(f"./{q(BPMN_NS, 'multiInstanceLoopCharacteristics')}")
        is None
    ]
    if len(subprocesses) != 1:
        fail(
            "expected exactly one ordinary root embedded assessment "
            f"subprocess, found {len(subprocesses)}"
        )
    subprocess = subprocesses[0]
    if subprocess.attrib.get("triggeredByEvent") == "true":
        fail("assessment must be an ordinary embedded subprocess, not an event subprocess")
    forbid_downstream_intents_in_assessment(subprocess, ids_to_names)
    subprocess_outputs = mapping_outputs(subprocess)
    for name in (
        "route",
        "severity",
        "engineeringNeeded",
        "failureReason",
    ):
        if not any(
            mapping_propagates_semantic(
                item,
                ids_to_names,
                name,
                EXPECTED_OUTPUTS[name],
            )
            for item in subprocess_outputs
        ):
            fail(
                f"assessment subprocess does not propagate {name!r} "
                "to its parent/root scope"
            )

    sub_nodes, sub_flows, sub_outgoing, sub_incoming = build_scope_graph(subprocess)
    starts = [
        node_id for node_id, node in sub_nodes.items() if local(node.tag) == "startEvent"
    ]
    ends = [node_id for node_id, node in sub_nodes.items() if local(node.tag) == "endEvent"]
    if len(starts) != 1 or not ends:
        fail("assessment subprocess needs one start and at least one end")
    require_scope_reachability(
        sub_nodes, sub_outgoing, sub_incoming, starts[0], set(ends)
    )
    conditions = require_gateway_contract(subprocess, sub_flows)
    if len(
        [
            node
            for node in sub_nodes.values()
            if local(node.tag) == "exclusiveGateway"
            and len(child_refs(node, "outgoing")) >= 2
        ]
    ) < 6:
        fail("assessment subprocess is not a substantial visible decision phase")

    condition_blob = "\n".join(conditions)
    condition_folded = condition_blob.casefold()
    condition_variable_ids = referenced_variable_ids(condition_blob)
    required_condition_vars = {
        "crmMatchCount": variables["crmMatchCount"].attrib["id"],
        "agentOutputValid": variables["agentOutputValid"].attrib["id"],
        "jiraAvailable": variables["jiraAvailable"].attrib["id"],
    }
    missing_condition_vars = [
        name
        for name, variable_id in required_condition_vars.items()
        if variable_id not in condition_variable_ids
    ]
    if missing_condition_vars:
        fail(
            "visible assessment conditions omit required decision inputs: "
            f"{missing_condition_vars}"
        )
    for literal in ("enterprise", "unavailable", "degraded", "sev1", "sev2"):
        if literal not in condition_folded:
            fail(f"visible assessment conditions omit policy token {literal!r}")

    normalization_case_targets = {
        variable_id
        for variable_id in normalization_targets
        if "casekey" in identifier_token(ids_to_names.get(variable_id, ""))
    }
    context_only_ids = {
        variables["businessImpact"].attrib["id"],
        variables["correlationId"].attrib["id"],
        variables["caseKey"].attrib["id"],
        *normalization_case_targets,
    }
    leaked_context = sorted(
        variable_id
        for variable_id in context_only_ids
        if variable_id in condition_variable_ids
    )
    if leaked_context:
        fail(f"context/correlation values must not influence routing: {leaked_context}")
    used_normalized = {
        target
        for target in normalization_targets
        if target not in normalization_case_targets
        and target in condition_variable_ids
    }
    declarations_by_id = {
        declaration.attrib["id"]: declaration
        for declaration in variables.values()
        if declaration.attrib.get("id")
    }
    structured_consumed = any(
        structured_normalization_roles(declarations_by_id[target])
        == {"tier", "serviceState", "duplicateIssueKey"}
        and structured_normalization_roles_in_conditions(target, condition_blob)
        == {"tier", "serviceState", "duplicateIssueKey"}
        for target in normalization_targets - normalization_case_targets
        if target in condition_variable_ids
    )
    if len(used_normalized) < 3 and not structured_consumed:
        fail(
            "assessment conditions do not visibly consume normalized tier, "
            "service state, and duplicate key values"
        )

    error_declarations = root.findall(f"./{q(BPMN_NS, 'error')}")
    jira_errors = [
        error
        for error in error_declarations
        if "jira" in " ".join(error.attrib.values()).casefold()
        and "unavail" in " ".join(error.attrib.values()).casefold()
    ]
    if len(jira_errors) != 1:
        fail("definitions must declare exactly one Jira-unavailable BPMN error")
    error = jira_errors[0]
    error_id = error.attrib.get("id")
    if not error_id or not error.attrib.get("errorCode"):
        fail("Jira-unavailable BPMN error needs id and errorCode")

    error_ends = []
    for end_id in ends:
        definition = sub_nodes[end_id].find(f"./{q(BPMN_NS, 'errorEventDefinition')}")
        if definition is not None and definition.attrib.get("errorRef") == error_id:
            error_ends.append(sub_nodes[end_id])
    if len(error_ends) != 1:
        fail("assessment needs exactly one error end referencing the Jira error")

    error_end = error_ends[0]
    incoming_ids = child_refs(error_end, "incoming")
    if len(incoming_ids) != 1:
        fail("Jira error end must have exactly one visibly guarded incoming flow")
    error_flow = sub_flows[incoming_ids[0]]
    source = sub_nodes[error_flow.attrib["sourceRef"]]
    error_assignment_tasks: list[ET.Element] = []
    while local(source.tag) == "task":
        type_values = [
            item.attrib.get("value")
            for item in source.findall(
                f"./{q(BPMN_NS, 'extensionElements')}//{q(UIPATH_NS, 'type')}"
            )
        ]
        if type_values != ["BPMN.Variables"]:
            fail(
                "only registry-derived Variables tasks may appear between the "
                "Jira guard and error end"
            )
        if len(child_refs(source, "incoming")) != 1 or len(
            child_refs(source, "outgoing")
        ) != 1:
            fail(
                "Jira error assignment path must be straight-line with no "
                "branching"
            )
        error_assignment_tasks.append(source)
        error_flow = sub_flows[child_refs(source, "incoming")[0]]
        source = sub_nodes[error_flow.attrib["sourceRef"]]
    if local(source.tag) != "exclusiveGateway":
        fail(
            "Jira error end must be selected by an exclusive gateway, with "
            "only straight-line Variables assignments in between"
        )
    error_condition = error_flow.find(f"./{q(BPMN_NS, 'conditionExpression')}")
    error_expression = (error_condition.text or "") if error_condition is not None else ""
    jira_id = variables["jiraAvailable"].attrib["id"]
    error_variable_ids = referenced_variable_ids(error_expression)
    if jira_id not in error_variable_ids or (
        "sev1" not in error_expression.casefold()
        and "sev2" not in error_expression.casefold()
        and variables["severity"].attrib["id"] not in error_variable_ids
    ):
        fail(
            "Jira error-end flow must visibly guard Jira unavailability with "
            "Sev1/Sev2 eligibility"
        )
    boundaries = [
        event
        for event in process.findall(f"./{q(BPMN_NS, 'boundaryEvent')}")
        if event.attrib.get("attachedToRef") == subprocess.attrib.get("id")
    ]
    matching_boundaries = []
    for boundary in boundaries:
        definition = boundary.find(f"./{q(BPMN_NS, 'errorEventDefinition')}")
        if definition is not None and definition.attrib.get("errorRef") == error_id:
            matching_boundaries.append(boundary)
    if len(matching_boundaries) != 1:
        fail("assessment must have one matching Jira interrupting error boundary")
    boundary = matching_boundaries[0]
    if boundary.attrib.get("cancelActivity", "true") != "true":
        fail("Jira error boundary must be interrupting")

    root_nodes, _root_flows, root_outgoing, _root_incoming = build_scope_graph(process)
    boundary_region = walk(boundary.attrib["id"], root_outgoing)
    boundary_tasks = [
        root_nodes[node_id]
        for node_id in boundary_region
        if node_id in root_nodes and local(root_nodes[node_id].tag) == "task"
    ]
    if not output_literal_exists(
        [*error_assignment_tasks, *boundary_tasks],
        ids_to_names,
        "failureReason",
        "JiraUnavailable",
    ):
        fail("Jira error/boundary path never emits failureReason JiraUnavailable")
    if not output_literal_exists(
        boundary_tasks, ids_to_names, "route", "ManualReview"
    ):
        fail("Jira boundary path never emits route ManualReview")
    for severity in ("Sev1", "Sev2"):
        if not output_literal_exists(
            boundary_tasks, ids_to_names, "severity", severity
        ):
            fail(
                "Jira boundary path must visibly restore both classified "
                f"severity outcomes; missing {severity}"
            )
    if not output_literal_exists(
        boundary_tasks, ids_to_names, "engineeringNeeded", "true"
    ):
        fail(
            "Jira boundary path must visibly restore engineeringNeeded=true"
        )

    boundary_conditions = []
    for node_id in boundary_region:
        node = root_nodes.get(node_id)
        if node is None or local(node.tag) != "exclusiveGateway":
            continue
        if len(child_refs(node, "outgoing")) < 2:
            continue
        for flow_id in child_refs(node, "outgoing"):
            flow = _root_flows.get(flow_id)
            if flow is None:
                continue
            expression = flow.find(f"./{q(BPMN_NS, 'conditionExpression')}")
            if expression is not None and expression.text:
                boundary_conditions.append(expression.text)
    boundary_condition_blob = "\n".join(boundary_conditions)
    boundary_condition_folded = boundary_condition_blob.casefold()
    if (
        "enterprise" not in boundary_condition_folded
        or "unavailable" not in boundary_condition_folded
        or variables["workaroundAvailable"].attrib["id"]
        not in referenced_variable_ids(boundary_condition_blob)
    ):
        fail(
            "Jira boundary path must visibly distinguish the Sev1 predicate "
            "from its Sev2 default before restoring subprocess-local outputs"
        )
    return subprocess, boundary


def branch_region(
    origin: str,
    join: str,
    outgoing: dict[str, list[str]],
) -> set[str]:
    region = walk(origin, outgoing, stop=join)
    if join not in walk(origin, outgoing):
        fail(f"parallel branch rooted at {origin!r} cannot reach join {join!r}")
    return region


def require_sequential_attachment_loop(
    elements: list[ET.Element],
    variables: dict[str, ET.Element],
    ids_to_names: dict[str, str],
) -> None:
    candidates: list[ET.Element] = []
    for element in elements:
        marker = element.find(f"./{q(BPMN_NS, 'multiInstanceLoopCharacteristics')}")
        if marker is None or marker.attrib.get("isSequential") != "true":
            continue
        loop = marker.find(
            f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'loopCharacteristics')}"
        )
        if loop is None:
            continue
        collection = loop.attrib.get("inputCollection", "")
        if (
            variables["attachments"].attrib["id"]
            not in referenced_variable_ids(collection)
        ):
            continue
        candidates.append(element)
    if len(candidates) != 1:
        fail(
            "attachment branch needs exactly one sequential multi-instance "
            "subprocess bound to the attachments input"
        )

    loop_activity = candidates[0]
    if local(loop_activity.tag) != "subProcess":
        fail("sequential attachment marker must be a subprocess")
    marker = loop_activity.find(
        f"./{q(BPMN_NS, 'multiInstanceLoopCharacteristics')}/"
        f"{q(BPMN_NS, 'extensionElements')}/"
        f"{q(UIPATH_NS, 'loopCharacteristics')}"
    )
    if marker is None or marker.attrib.get("inputElement") != "iterator[0]":
        fail(
            "multi-instance attachment subprocess must bind the current "
            "item as iterator[0]"
        )
    loop_nodes, _loop_flows, loop_outgoing, loop_incoming = build_scope_graph(
        loop_activity
    )
    loop_starts = [
        node_id
        for node_id, node in loop_nodes.items()
        if local(node.tag) == "startEvent"
    ]
    loop_ends = {
        node_id
        for node_id, node in loop_nodes.items()
        if local(node.tag) == "endEvent"
    }
    if len(loop_starts) != 1 or len(loop_ends) != 1:
        fail("attachment subprocess needs exactly one start and one end")
    require_scope_reachability(
        loop_nodes,
        loop_outgoing,
        loop_incoming,
        loop_starts[0],
        loop_ends,
    )
    per_item_scripts = [
        node for node in loop_nodes.values() if local(node.tag) == "scriptTask"
    ]
    if len(per_item_scripts) != 1:
        fail(
            "attachment subprocess needs exactly one per-item data ScriptTask"
        )
    loop_script = per_item_scripts[0]
    mapping = loop_script.find(
        f"./{q(BPMN_NS, 'extensionElements')}/"
        f"{q(UIPATH_NS, 'mapping')}"
    )
    if mapping is None:
        fail("per-item attachment ScriptTask has no Variables mapping")
    args_input = next(
        (
            item
            for item in mapping.findall(f"./{q(UIPATH_NS, 'input')}")
            if item.attrib.get("name") == "args"
        ),
        None,
    )
    args_raw = (
        (args_input.attrib.get("value") if args_input is not None else None)
        or (args_input.text if args_input is not None else None)
        or ""
    )
    try:
        args = json.loads(args_raw)
    except json.JSONDecodeError:
        fail("per-item attachment ScriptTask args must be valid JSON")
    current_item_args = [
        name
        for name, value in args.items()
        if value == "=iterator[0].item"
    ] if isinstance(args, dict) else []
    if len(current_item_args) != 1:
        fail(
            "per-item attachment ScriptTask must receive "
            "iterator[0].item through one named argument"
        )
    current_item_arg = current_item_args[0]
    schema_node = mapping.find(
        f"./{q(UIPATH_NS, 'context')}/{q(UIPATH_NS, 'inputSchema')}"
    )
    schema_raw = (
        (schema_node.attrib.get("value") if schema_node is not None else None)
        or (schema_node.text if schema_node is not None else None)
        or ""
    )
    try:
        schema = json.loads(schema_raw)
    except json.JSONDecodeError:
        fail("per-item attachment ScriptTask inputSchema must be valid JSON")
    definition = (
        schema.get("properties", {}).get(current_item_arg)
        if isinstance(schema, dict)
        and isinstance(schema.get("properties"), dict)
        else None
    )
    if not isinstance(definition, dict) or definition.get("type") != "object":
        fail(
            "per-item attachment ScriptTask must type its current item "
            "argument as an object"
        )
    item_properties = definition.get("properties")
    item_required = definition.get("required")
    if (
        not isinstance(item_properties, dict)
        or {
            name: get_ci(item_properties.get(name), "type")
            for name in ("name", "driveFileId")
        }
        != {"name": "string", "driveFileId": "string"}
        or not isinstance(item_required, list)
        or not {"name", "driveFileId"} <= set(item_required)
    ):
        fail(
            "per-item attachment argument schema must require string "
            "name and driveFileId properties"
        )
    script_body = (
        loop_script.findtext(f"./{q(BPMN_NS, 'script')}", default="") or ""
    )
    script_executable = javascript_code_mask(script_body)
    if not re.search(
        rf"\b{re.escape(current_item_arg)}\b",
        script_executable,
    ):
        fail(
            "per-item attachment ScriptTask must read its mapped current "
            "item argument"
        )

    declarations: dict[str, list[str]] = defaultdict(list)
    for match in re.finditer(
        r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
        r"([^;\n]+)",
        script_executable,
    ):
        declarations[match.group(1)].append(
            script_body[match.start(2) : match.end(2)].strip()
        )

    def stable_local_assignment(identifier: str) -> str | None:
        values = declarations.get(identifier, [])
        if len(values) != 1:
            return None
        direct_writes = re.findall(
            rf"(?<![\w$.]){re.escape(identifier)}\s*=(?!=)",
            script_executable,
        )
        mutation = re.search(
            rf"(?<![\w$.]){re.escape(identifier)}\s*"
            r"(?:\+\+|--|\+=|-=|\*=|/=|%=)"
            rf"|(?:\+\+|--)\s*{re.escape(identifier)}\b"
            rf"|\b{re.escape(identifier)}"
            r"(?:\.[A-Za-z_$][\w$]*|\[[^\]\n]+\])\s*"
            r"(?:=(?!=)|\+\+|--|\+=|-=|\*=|/=|%=)"
            rf"|\bdelete\s+{re.escape(identifier)}(?:\.|\[)"
            rf"|\bObject\.assign\s*\(\s*{re.escape(identifier)}\b",
            script_executable,
        )
        if len(direct_writes) != 1 or mutation is not None:
            return None
        return values[0]

    current_item_mutation = re.search(
        rf"(?<![\w$.]){re.escape(current_item_arg)}\s*"
        r"(?:=(?!=)|\+\+|--|\+=|-=|\*=|/=|%=)"
        rf"|(?:\+\+|--)\s*{re.escape(current_item_arg)}\b"
        rf"|\b{re.escape(current_item_arg)}"
        r"(?:\.[A-Za-z_$][\w$]*|\[[^\]\n]+\])\s*"
        r"(?:=(?!=)|\+\+|--|\+=|-=|\*=|/=|%=)"
        rf"|\bdelete\s+{re.escape(current_item_arg)}(?:\.|\[)"
        rf"|\bObject\.assign\s*\(\s*{re.escape(current_item_arg)}\b",
        script_executable,
    )
    if current_item_mutation is not None:
        fail(
            "per-item attachment ScriptTask must not reassign or mutate its "
            "mapped current item"
        )

    item_aliases = {current_item_arg}
    changed = True
    while changed:
        changed = False
        for alias in declarations:
            expression = stable_local_assignment(alias)
            if expression is None:
                continue
            normalized = re.sub(r"[\s()]", "", expression)
            if any(
                normalized in {item, f"{item}||{{}}"}
                for item in item_aliases
            ) and alias not in item_aliases:
                item_aliases.add(alias)
                changed = True

    returned_body = single_return_object_body(
        script_body,
        "per-item attachment ScriptTask",
    )
    returned_executable = javascript_code_mask(returned_body)
    if "..." in returned_executable:
        fail(
            "per-item attachment ScriptTask result must not use object spread"
        )

    def returned_expression(property_name: str) -> str:
        property_occurrences = re.findall(
            rf"(?:^|,)\s*{re.escape(property_name)}\s*"
            rf"(?::|(?=,|$))",
            returned_executable,
        )
        if len(property_occurrences) > 1:
            fail(
                "per-item attachment ScriptTask result must return "
                f"{property_name!r} exactly once"
            )
        if len(property_occurrences) != 1:
            return ""
        explicit = re.search(
            rf"(?:^|,)\s*{re.escape(property_name)}\s*:"
            rf"(.*?)(?=,\s*(?:itemName|copyName|driveFileId)\s*:|$)",
            returned_executable,
            flags=re.DOTALL,
        )
        if explicit is not None:
            return returned_body[
                explicit.start(1) : explicit.end(1)
            ].strip()
        if re.search(
            rf"(?:^|,)\s*{re.escape(property_name)}\s*(?=,|$)",
            returned_executable,
        ):
            return property_name
        return ""

    def resolve_assignment(
        expression: str,
        seen: set[str] | None = None,
    ) -> str:
        stripped = expression.strip()
        identifier_match = re.fullmatch(
            r"[A-Za-z_$][\w$]*",
            stripped,
        )
        if identifier_match is None:
            return stripped
        identifier = identifier_match.group(0)
        visited = set() if seen is None else set(seen)
        assignment = stable_local_assignment(identifier)
        if identifier in visited or assignment is None:
            return stripped
        visited.add(identifier)
        return resolve_assignment(assignment, visited)

    def exact_current_field(
        expression: str,
        field_name: str,
    ) -> bool:
        resolved = resolve_assignment(expression)
        normalized = re.sub(r"[\s()]", "", resolved)
        return any(
            re.fullmatch(
                rf"{re.escape(alias)}\.{re.escape(field_name)}"
                r"(?:\|\|(?:\"\"|''))?",
                normalized,
            )
            is not None
            for alias in item_aliases
        )

    item_name_expression = returned_expression("itemName")
    if not exact_current_field(item_name_expression, "name"):
        fail(
            f"per-item attachment result itemName must derive exactly "
            f"from {current_item_arg}.name"
        )
    drive_id_expression = returned_expression("driveFileId")
    if not exact_current_field(drive_id_expression, "driveFileId"):
        fail(
            f"per-item attachment result driveFileId must derive exactly "
            f"from {current_item_arg}.driveFileId"
        )

    copy_name_expression = resolve_assignment(
        returned_expression("copyName")
    )
    correlation_id = variables["correlationId"].attrib["id"]

    def strip_outer_parentheses(expression: str) -> str:
        stripped = expression.strip()
        while stripped.startswith("(") and stripped.endswith(")"):
            depth = 0
            closes_at_end = False
            masked = javascript_code_mask(stripped)
            for index, character in enumerate(masked):
                if character == "(":
                    depth += 1
                elif character == ")":
                    depth -= 1
                    if depth == 0:
                        closes_at_end = index == len(masked) - 1
                        break
            if not closes_at_end:
                break
            stripped = stripped[1:-1].strip()
        return stripped

    def copy_name_term_kind(expression: str) -> str | None:
        resolved = resolve_assignment(expression)
        normalized = re.sub(
            r"\s",
            "",
            strip_outer_parentheses(resolved),
        )
        if normalized == f"vars.{correlation_id}":
            return "correlation"
        if any(
            normalized == f"{alias}.name"
            for alias in item_aliases
        ):
            return "item"
        if re.fullmatch(
            r'"(?:\\.|[^"\\])*"|'
            r"'(?:\\.|[^'\\])*'|"
            r"`(?:\\.|[^`\\$]|\$(?!\{))*`",
            strip_outer_parentheses(resolved),
            flags=re.DOTALL,
        ):
            return "literal"
        return None

    def top_level_plus_terms(expression: str) -> list[str]:
        masked = javascript_code_mask(expression)
        depth = 0
        start = 0
        terms: list[str] = []
        for index, character in enumerate(masked):
            if character in "([{":
                depth += 1
            elif character in ")]}":
                depth -= 1
                if depth < 0:
                    return []
            elif character == "+" and depth == 0:
                terms.append(expression[start:index].strip())
                start = index + 1
        if depth != 0:
            return []
        terms.append(expression[start:].strip())
        return terms

    def valid_copy_name_expression(expression: str) -> bool:
        stripped = strip_outer_parentheses(expression)
        if stripped.startswith("`") and stripped.endswith("`"):
            body = stripped[1:-1]
            interpolations: list[str] = []
            cursor = 0
            while cursor < len(body):
                if body[cursor] == "\\":
                    cursor += 2
                    continue
                if body.startswith("${", cursor):
                    close = body.find("}", cursor + 2)
                    if close < 0 or "{" in body[cursor + 2 : close]:
                        return False
                    interpolations.append(body[cursor + 2 : close])
                    cursor = close + 1
                    continue
                cursor += 1
            kinds = {
                copy_name_term_kind(interpolation)
                for interpolation in interpolations
            }
            return {"correlation", "item"} <= kinds

        terms = top_level_plus_terms(stripped)
        kinds = [copy_name_term_kind(term) for term in terms]
        return (
            len(terms) >= 2
            and all(kind is not None for kind in kinds)
            and "correlation" in kinds
            and "item" in kinds
        )

    if not valid_copy_name_expression(copy_name_expression):
        fail(
            f"per-item attachment result copyName must derive only from "
            f"{current_item_arg}.name plus vars.{correlation_id}"
        )

    script_response_ids = {
        output.attrib["var"]
        for output in mapping.findall(f"./{q(UIPATH_NS, 'output')}")
        if output.attrib.get("name") == "scriptResponse"
        and output.attrib.get("type") == "jsonSchema"
        and output.attrib.get("source", "").strip() == "=result.response"
        and output.attrib.get("var")
    }
    response_declarations = [
        declaration
        for declaration in variables.values()
        if declaration.attrib.get("id") in script_response_ids
    ]
    if len(response_declarations) != 1:
        fail(
            "per-item attachment ScriptTask must map one declared response "
            "variable"
        )
    response_raw = (response_declarations[0].text or "").strip()
    try:
        response_schema = json.loads(response_raw)
    except json.JSONDecodeError:
        fail("per-item attachment response variable must contain JSON schema")
    response_properties = (
        response_schema.get("properties")
        if isinstance(response_schema, dict)
        else None
    )
    response_required = (
        response_schema.get("required")
        if isinstance(response_schema, dict)
        else None
    )
    required_response_fields = {"itemName", "copyName", "driveFileId"}
    if (
        response_declarations[0].attrib.get("type") != "jsonSchema"
        or get_ci(response_schema, "type") != "object"
        or not isinstance(response_properties, dict)
        or {
            name: get_ci(response_properties.get(name), "type")
            for name in required_response_fields
        }
        != {name: "string" for name in required_response_fields}
        or not isinstance(response_required, list)
        or not required_response_fields <= set(response_required)
    ):
        fail(
            "per-item attachment response schema must require string "
            "itemName, copyName, and driveFileId properties"
        )
    marker_mapping = loop_activity.find(
        f"./{q(BPMN_NS, 'extensionElements')}/"
        f"{q(UIPATH_NS, 'mapping')}"
    )
    marker_outputs = (
        marker_mapping.findall(f"./{q(UIPATH_NS, 'output')}")
        if marker_mapping is not None
        else []
    )
    iteration_outputs = [
        output
        for output in marker_outputs
        if output.attrib.get("custom") == "true"
        and output.attrib.get("type") == "string"
        and output.attrib.get("var")
        and bool(
            script_response_ids
            & referenced_variable_ids(output.attrib.get("source", ""))
        )
        and ".itemName" in output.attrib.get("source", "")
    ]
    if len(iteration_outputs) != 1:
        fail(
            "multi-instance attachment subprocess must aggregate each "
            "typed itemName through one custom marker output"
        )
    iteration_collection_id = iteration_outputs[0].attrib["var"]
    iteration_collection = next(
        (
            declaration
            for declaration in variables.values()
            if declaration.attrib.get("id") == iteration_collection_id
        ),
        None,
    )
    if (
        iteration_collection is None
        or iteration_collection.attrib.get("type") != "Collection{string}"
        or iteration_collection.attrib.get("elementId")
        != loop_activity.attrib.get("id")
    ):
        fail(
            "attachment marker output must target its scoped "
            "Collection{string} variable"
        )
    drive_activities = [
        node
        for node in loop_nodes.values()
        if local(node.tag) == "sendTask"
        and connector_context(node).get("connectorKey")
        == "uipath-google-drive"
        and connector_context(node).get("path") == "/copyFile"
    ]
    if len(drive_activities) != 1:
        fail(
            "attachment subprocess needs exactly one Google Drive copy "
            "activity after its per-item script"
        )
    if drive_activities[0].attrib["id"] not in walk(
        loop_script.attrib["id"], loop_outgoing
    ):
        fail("Google Drive copy must execute after per-item preparation")
    drive_inputs = connector_inputs(drive_activities[0])
    file_id_input = drive_inputs.get(("query", "fileId"))
    drive_body = connector_json_body(drive_activities[0], drive_inputs)
    if file_id_input is None or "name" not in drive_body:
        fail(
            "Google Drive copy must bind its fileId query and name body fields"
        )
    response_declaration = response_declarations[0]
    require_exact_variable_property_reference(
        connector_input_value(file_id_input),
        response_declaration,
        "driveFileId",
        "Drive copy fileId",
    )
    require_exact_variable_property_reference(
        drive_body["name"],
        response_declaration,
        "copyName",
        "Drive copy name",
    )

    reducer_collection_ids = {iteration_collection_id}
    reducers = [
        element
        for element in elements
        if local(element.tag) == "scriptTask"
        and element.find(
            f"./{q(BPMN_NS, 'multiInstanceLoopCharacteristics')}"
        )
        is None
        and bool(
            reducer_collection_ids
            & referenced_variable_ids(
            element.findtext(
                f"./{q(BPMN_NS, 'script')}",
                default="",
            )
            or ""
            )
        )
    ]
    if len(reducers) != 1:
        fail(
            "attachment branch needs one post-loop ScriptTask reducer"
        )
    reducer = reducers[0]
    reducer_body = (
        reducer.findtext(f"./{q(BPMN_NS, 'script')}", default="") or ""
    )
    reducer_executable = javascript_code_mask(reducer_body)
    reducer_returns = list(
        re.finditer(r"\breturn\b", reducer_executable)
    )
    if len(reducer_returns) != 1:
        fail(
            "post-loop reducer must contain exactly one return of the final "
            "attachment"
        )
    return_start = reducer_returns[0].end()
    return_end = reducer_executable.find(";", return_start)
    if return_end < 0:
        return_end = len(reducer_body)
    if re.fullmatch(
        r"\s*;?\s*",
        reducer_executable[return_end:],
    ) is None:
        fail("post-loop reducer return must be terminal")
    returned_value = reducer_body[return_start:return_end].strip()

    def strip_outer_parentheses(value: str) -> str:
        stripped = value.strip()
        while stripped.startswith("(") and stripped.endswith(")"):
            masked = javascript_code_mask(stripped)
            depth = 0
            closes_at_end = False
            for position, character in enumerate(masked):
                if character == "(":
                    depth += 1
                elif character == ")":
                    depth -= 1
                    if depth == 0:
                        closes_at_end = position == len(masked) - 1
                        break
            if not closes_at_end:
                break
            stripped = stripped[1:-1].strip()
        return stripped

    trusted_collections = {f"vars.{iteration_collection_id}"}
    declarations: dict[str, list[str]] = defaultdict(list)
    for match in re.finditer(
        r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*"
        r"([^;\n]+)",
        reducer_executable[: reducer_returns[0].start()],
    ):
        declarations[match.group(1)].append(
            reducer_body[match.start(2) : match.end(2)].strip()
        )
    changed = True
    while changed:
        changed = False
        for alias, assignments in declarations.items():
            if len(assignments) != 1:
                continue
            if len(
                re.findall(
                    rf"(?<![\w$.]){re.escape(alias)}\s*=(?!=)",
                    reducer_executable,
                )
            ) != 1:
                continue
            candidate = re.sub(
                r"\s",
                "",
                strip_outer_parentheses(assignments[0]),
            )
            if any(
                candidate in {trusted, f"{trusted}||[]"}
                for trusted in trusted_collections
            ) and alias not in trusted_collections:
                trusted_collections.add(alias)
                changed = True

    def is_final_selector(value: str) -> bool:
        normalized = re.sub(
            r"\s",
            "",
            strip_outer_parentheses(value),
        )
        for trusted in trusted_collections:
            escaped = re.escape(trusted)
            if re.fullmatch(
                rf"(?:{escaped}\[{escaped}\.length-1\]|"
                rf"{escaped}\.at\(-1\))"
                r"(?:\|\|(?:\"\"|''))?",
                normalized,
            ):
                return True
        return False

    def split_top_level_ternary(
        value: str,
    ) -> tuple[str, str, str] | None:
        masked = javascript_code_mask(value)
        depth = 0
        question: int | None = None
        colon: int | None = None
        for position, character in enumerate(masked):
            if character in "([{":
                depth += 1
            elif character in ")]}":
                depth -= 1
            elif character == "?" and depth == 0:
                if question is not None:
                    return None
                question = position
            elif character == ":" and depth == 0 and question is not None:
                colon = position
                break
        if question is None or colon is None:
            return None
        return (
            value[:question].strip(),
            value[question + 1 : colon].strip(),
            value[colon + 1 :].strip(),
        )

    returns_final = is_final_selector(returned_value)
    conditional = split_top_level_ternary(
        strip_outer_parentheses(returned_value)
    )
    if not returns_final and conditional is not None:
        condition, when_true, when_false = conditional
        normalized_condition = re.sub(
            r"\s",
            "",
            strip_outer_parentheses(condition),
        )
        empty_literals = {'""', "''"}
        for trusted in trusted_collections:
            positive = {
                f"{trusted}.length",
                f"{trusted}.length>0",
                f"{trusted}.length!=0",
                f"{trusted}.length!==0",
            }
            negative = {
                f"!{trusted}.length",
                f"{trusted}.length==0",
                f"{trusted}.length===0",
            }
            if (
                normalized_condition in positive
                and is_final_selector(when_true)
                and when_false.strip() in empty_literals
            ) or (
                normalized_condition in negative
                and when_true.strip() in empty_literals
                and is_final_selector(when_false)
            ):
                returns_final = True
                break
    if not returns_final:
        fail(
            "post-loop reducer must actually return the final attachment "
            "from the completed marker collection"
        )
    reducer_outputs = mapping_outputs(reducer)
    response_ids = {
        output.attrib["var"]
        for output in reducer_outputs
        if output.attrib.get("name") == "scriptResponse"
        and output.attrib.get("var")
    }
    if not any(
        (
            "lastattachmentname"
            in identifier_token(output.attrib.get("name", ""))
            or "lastattachmentname"
            in identifier_token(ids_to_names.get(output.attrib.get("var", ""), ""))
        )
        and (
            output.attrib.get("source") == "=result.response"
            or bool(
                response_ids
                & referenced_variable_ids(output.attrib.get("source", ""))
            )
        )
        for output in reducer_outputs
    ):
        fail(
            "post-loop reducer must map result.response to "
            "lastAttachmentName"
        )


def parallel_output_ownership_order(
    branch_outputs: list[set[str]],
) -> tuple[int, int, int]:
    """Return Jira/attachment/communication branches with exclusive outputs."""
    required = (
        {"jiraAction"},
        {"attachmentAction", "lastAttachmentName"},
        {"slackAction", "responseMode"},
    )
    owned_outputs = set().union(*required)
    for order in itertools.permutations(range(len(branch_outputs))):
        if len(order) != len(required):
            continue
        if all(
            branch_outputs[index] & owned_outputs == wanted
            for wanted, index in zip(required, order)
        ):
            return order
    fail(
        "three parallel workstreams must exclusively own Jira, attachment "
        "(including lastAttachmentName), and combined communication outputs; "
        f"observed {branch_outputs}"
    )


def require_parallel_workstreams(
    process: ET.Element,
    nodes: dict[str, ET.Element],
    outgoing: dict[str, list[str]],
    incoming: dict[str, list[str]],
    variables: dict[str, ET.Element],
    ids_to_names: dict[str, str],
) -> tuple[str, str]:
    parallel = [
        node_id for node_id, node in nodes.items() if local(node.tag) == "parallelGateway"
    ]
    splits = [node_id for node_id in parallel if len(outgoing.get(node_id, [])) == 3]
    joins = [node_id for node_id in parallel if len(incoming.get(node_id, [])) == 3]
    if len(splits) != 1 or len(joins) != 1 or splits[0] == joins[0]:
        fail("expected exactly one three-way parallel split and one three-way join")
    split, join = splits[0], joins[0]

    regions = [
        branch_region(origin, join, outgoing) for origin in outgoing.get(split, [])
    ]
    for left, right in itertools.combinations(regions, 2):
        overlap = left & right
        if overlap:
            fail(f"parallel workstreams overlap before the join: {sorted(overlap)}")

    region_elements = [
        [nodes[node_id] for node_id in region if node_id in nodes] for region in regions
    ]
    branch_outputs = [
        output_names_in_elements(elements, ids_to_names) for elements in region_elements
    ]
    (
        jira_index,
        attachment_index,
        communication_index,
    ) = parallel_output_ownership_order(branch_outputs)
    require_material_jira_intent(
        region_elements[jira_index],
        ids_to_names,
    )
    require_sequential_attachment_loop(
        region_elements[attachment_index], variables, ids_to_names
    )

    def connector_keys(elements: list[ET.Element]) -> set[tuple[str, str]]:
        found: set[tuple[str, str]] = set()
        for element in elements:
            candidates = (
                [element]
                if local(element.tag) == "sendTask"
                else []
            )
            candidates.extend(
                element.findall(f".//{q(BPMN_NS, 'sendTask')}")
            )
            for candidate in candidates:
                context = connector_context(candidate)
                if context.get("connectorKey") and context.get("path"):
                    found.add(
                        (context["connectorKey"], context["path"])
                    )
        return found

    expected_by_branch = {
        jira_index: {
            ("uipath-atlassian-jira", "/curated_create_issue"),
            (
                "uipath-atlassian-jira",
                "/curated_edit_issue/{issueIdOrKey}",
            ),
        },
        attachment_index: {
            ("uipath-google-drive", "/copyFile"),
        },
        communication_index: {
            (
                "uipath-salesforce-slack",
                "/send_message_to_channel_v2",
            ),
        },
    }
    for index, expected_connectors in expected_by_branch.items():
        actual_connectors = connector_keys(region_elements[index])
        if actual_connectors != expected_connectors:
            fail(
                "parallel workstream connector ownership mismatch: "
                f"expected {sorted(expected_connectors)}, "
                f"found {sorted(actual_connectors)}"
            )
    return split, join


def require_di(
    root: ET.Element,
    nodes: dict[str, ET.Element],
    flows: dict[str, ET.Element],
    subprocess_nodes: dict[str, ET.Element],
    subprocess_flows: dict[str, ET.Element],
) -> None:
    shapes = {
        shape.attrib.get("bpmnElement"): shape
        for shape in root.findall(f".//{q(BPMNDI_NS, 'BPMNShape')}")
    }
    edges = {
        edge.attrib.get("bpmnElement"): edge
        for edge in root.findall(f".//{q(BPMNDI_NS, 'BPMNEdge')}")
    }
    for node_id, node in {**nodes, **subprocess_nodes}.items():
        shape = shapes.get(node_id)
        if shape is None:
            fail(f"visible flow node {node_id!r} is missing BPMNShape")
        bounds = shape.find(f"./{q(DC_NS, 'Bounds')}")
        if bounds is None:
            fail(f"BPMNShape for {node_id!r} is missing dc:Bounds")
        try:
            x, y, width, height = (
                float(bounds.attrib[name]) for name in ("x", "y", "width", "height")
            )
        except (KeyError, ValueError):
            fail(f"BPMNShape for {node_id!r} has invalid bounds")
        if width <= 0 or height <= 0 or x < 0 or y < 0:
            fail(f"BPMNShape for {node_id!r} has invalid geometry")
        if local(node.tag) == "subProcess" and shape.attrib.get("isExpanded") != "true":
            fail("assessment subprocess must be expanded so its decisions are visible")

    for flow_id in {**flows, **subprocess_flows}:
        edge = edges.get(flow_id)
        if edge is None:
            fail(f"sequence flow {flow_id!r} is missing BPMNEdge")
        if len(edge.findall(f"./{q(DI_NS, 'waypoint')}")) < 2:
            fail(f"BPMNEdge for {flow_id!r} needs at least two waypoints")


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--connector-evidence":
        require_connector_registry_evidence()
        print("OK: exact current enriched connector registry evidence retained")
        return
    if len(sys.argv) == 3 and sys.argv[1] == "--registry-evidence":
        extension_type = sys.argv[2]
        if extension_type not in {"BPMN.ScriptTask", "BPMN.Variables"}:
            fail(f"unsupported registry evidence type: {extension_type}")
        load_registry_evidence(extension_type)
        print(f"OK: exact current {extension_type} registry response retained")
        return
    if len(sys.argv) != 1:
        fail(
            "usage: check_customer_escalation_structure.py "
            "[--registry-evidence BPMN.ScriptTask|BPMN.Variables] "
            "[--connector-evidence]"
        )
    if not BPMN.is_file():
        fail(f"missing BPMN file: {BPMN}")
    try:
        root = ET.parse(BPMN).getroot()
    except ET.ParseError as exc:
        fail(f"{BPMN} is not well-formed XML: {exc}")

    processes = root.findall(f"./{q(BPMN_NS, 'process')}")
    if len(processes) != 1:
        fail(f"expected exactly one root process, found {len(processes)}")
    process = processes[0]
    if process.attrib.get("isExecutable") != "false":
        fail(
            "BPMN process must use the current Studio serializer "
            "isExecutable='false' contract"
        )
    migration = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/"
        f"{q(UIPATH_NS, 'migrationVersion')}"
    )
    if migration is None:
        fail("BPMN process is missing uipath:migrationVersion")
    try:
        migration_version = int(migration.attrib.get("version", ""))
    except ValueError:
        fail("uipath:migrationVersion must be an integer")
    if migration_version < 15:
        fail("BPMN process uses a pre-runtime-contract migration version")

    starts = process.findall(f"./{q(BPMN_NS, 'startEvent')}")
    ends = process.findall(f"./{q(BPMN_NS, 'endEvent')}")
    if len(starts) != 1 or len(ends) != 1:
        fail("root process needs exactly one start and one end event")
    start_id = starts[0].attrib.get("id")
    end_id = ends[0].attrib.get("id")
    if not start_id or not end_id:
        fail("root start/end events need ids")
    entry_points = starts[0].findall(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'entryPointId')}"
    )
    if len(entry_points) != 1 or not entry_points[0].attrib.get("value"):
        fail("root start event must declare one non-empty uipath:entryPointId")
    entry_point_id = entry_points[0].attrib["value"]

    require_unique_ids(root)
    variables, ids_to_names = require_variables(process, start_id, end_id)
    script, scripts, variable_tasks = require_registry_activities(
        root, variables
    )
    normalization_targets = require_normalization_script(
        script, variables, ids_to_names, variable_tasks
    )
    require_jira_update_uses_normalized_duplicate(
        process,
        script,
        variables,
        ids_to_names,
        variable_tasks,
    )
    subprocess, boundary = require_assessment_subprocess(
        root, process, variables, ids_to_names, normalization_targets
    )

    nodes, flows, outgoing, incoming = build_scope_graph(process)
    boundary_id = boundary.attrib.get("id")
    require_scope_reachability(
        nodes,
        outgoing,
        incoming,
        start_id,
        {end_id},
        boundary_ids={boundary_id} if boundary_id else set(),
    )
    # The assessment subprocess must expose the policy decisions. At root
    # scope, an exclusive gateway is optional: a conditional loop collection
    # can correctly encode zero attachment iterations without an extra XOR.
    require_gateway_contract(process, flows, require_diverging=False)
    split, join = require_parallel_workstreams(
        process, nodes, outgoing, incoming, variables, ids_to_names
    )
    if split not in walk(subprocess.attrib["id"], outgoing):
        fail("normal assessment completion does not reach the parallel fan-out")
    if boundary_id and split not in walk(boundary_id, outgoing):
        fail("Jira boundary-error path does not rejoin before the parallel fan-out")

    nested_nodes: dict[str, ET.Element] = {}
    nested_flows: dict[str, ET.Element] = {}
    for nested_scope in process.findall(f".//{q(BPMN_NS, 'subProcess')}"):
        scope_nodes, scope_flows, _scope_outgoing, _scope_incoming = build_scope_graph(
            nested_scope
        )
        nested_nodes.update(scope_nodes)
        nested_flows.update(scope_flows)
    require_di(root, nodes, flows, nested_nodes, nested_flows)
    require_no_private_connector_values(root)
    require_cli_project_metadata(BPMN.name, start_id, entry_point_id)

    print(
        f"OK: registry-derived project has {len(nodes) + len(nested_nodes)} visible "
        f"nodes, {len(scripts)} runtime-contract ScriptTasks, an expanded "
        f"assessment subprocess with Jira error boundary and scope propagation, "
        f"sequential attachment iteration with post-loop reduction, and parallel "
        f"workstreams {split!r}->{join!r}"
    )


if __name__ == "__main__":
    main()

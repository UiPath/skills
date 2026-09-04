#!/usr/bin/env python3
"""Built-in tool + job-attachment input checks for DocAnalystAgent.

A. Some resources/*/resource.json is a built-in tool: $resourceType=tool,
   type=internal, referenceKey=null, isEnabled, id UUID-shaped,
   properties.toolType in the registry. Prompt asks for "Analyze Files",
   so toolType=analyze-attachments must be present.

B. agent.json declares inputSchema.definitions["job-attachment"] (object),
   at least one top-level property is either a direct job-attachment reference
   or an array whose items use that reference, and every such input is
   referenced as {{input.<name>}} in messages[].content.

C. Some message content references the Analyze Files tool as
   `@{tools.<Name>}` and that message's contentTokens carries a matching
   `{type: "expression", rawString: "tools.<Name>"}` token. `<Name>` is the
   tool resource's `name`; the runtime resolves the reference by `name`,
   case-insensitively, and renders an unresolved reference as raw text.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(os.getcwd()) / "DocsSol" / "DocAnalystAgent"
RESOURCES_DIR = ROOT / "resources"
AGENT_JSON = ROOT / "agent.json"

BUILTIN_TOOL_TYPES = {
    "analyze-attachments",
    "load-attachments",
    "deep-rag",
    "batch-transform",
}

JOB_ATTACHMENT_REF = "#/definitions/job-attachment"


def job_attachment_shape(prop: object) -> Optional[str]:
    """Return the supported job-attachment field shape, if any."""
    if not isinstance(prop, dict):
        return None

    if prop.get("$ref") == JOB_ATTACHMENT_REF:
        return "single"

    items = prop.get("items")
    if (
        prop.get("type") == "array"
        and isinstance(items, dict)
        and items.get("$ref") == JOB_ATTACHMENT_REF
    ):
        return "array"

    return None


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def find_resource_jsons() -> list:
    if not RESOURCES_DIR.is_dir():
        sys.exit(f"FAIL: {RESOURCES_DIR} does not exist — no resources/ directory")
    files = sorted(RESOURCES_DIR.rglob("resource.json"))
    if not files:
        sys.exit(f"FAIL: no resource.json files found under {RESOURCES_DIR}")
    return files


def is_builtin_tool(resource: dict) -> bool:
    return (
        resource.get("$resourceType") == "tool"
        and resource.get("type") == "internal"
    )


def assert_builtin_shape(path: Path, resource: dict) -> str:
    if resource.get("$resourceType") != "tool":
        sys.exit(f'FAIL: {path} $resourceType should be "tool", got {resource.get("$resourceType")!r}')
    if resource.get("type") != "internal":
        sys.exit(f'FAIL: {path} type should be "internal" for a built-in tool, got {resource.get("type")!r}')
    if resource.get("referenceKey") is not None:
        sys.exit(
            f"FAIL: {path} referenceKey should be null for a built-in tool "
            f"(per the registry), got {resource.get('referenceKey')!r}"
        )
    rid = resource.get("id")
    if not isinstance(rid, str) or "-" not in rid:
        sys.exit(f"FAIL: {path} resource id missing or malformed: {rid!r}")
    if not resource.get("isEnabled"):
        sys.exit(f"FAIL: {path} resource.isEnabled must be truthy")
    props = resource.get("properties") or {}
    tool_type = props.get("toolType")
    if tool_type not in BUILTIN_TOOL_TYPES:
        sys.exit(
            f"FAIL: {path} properties.toolType must be one of "
            f"{sorted(BUILTIN_TOOL_TYPES)}, got {tool_type!r}"
        )
    print(f"OK: {path.parent.name} is a built-in tool with toolType={tool_type!r}")
    return tool_type


def assert_builtin_tool_enabled() -> str:
    files = find_resource_jsons()
    builtin_tool_types_seen = []
    analyze_files_name = None
    for f in files:
        resource = load(f)
        if is_builtin_tool(resource):
            tt = assert_builtin_shape(f, resource)
            builtin_tool_types_seen.append(tt)
            if tt == "analyze-attachments":
                analyze_files_name = resource.get("name")

    if not builtin_tool_types_seen:
        sys.exit(
            "FAIL: no built-in tool resources found — expected at least one "
            'resource with $resourceType="tool" and type="internal"'
        )

    if "analyze-attachments" not in builtin_tool_types_seen:
        sys.exit(
            f'FAIL: prompt asked for the "Analyze Files" built-in tool '
            f'(toolType "analyze-attachments"), but none was enabled. '
            f'Got toolTypes: {builtin_tool_types_seen}'
        )
    if not isinstance(analyze_files_name, str) or not analyze_files_name.strip():
        sys.exit(
            "FAIL: the analyze-attachments tool resource has no non-empty "
            f"`name`, got {analyze_files_name!r}"
        )
    print('OK: "Analyze Files" (toolType="analyze-attachments") is enabled')
    return analyze_files_name


def assert_job_attachment_input(agent: dict) -> None:
    schema = agent.get("inputSchema") or {}

    defs = schema.get("definitions") or {}
    ja_def = defs.get("job-attachment")
    if not isinstance(ja_def, dict):
        sys.exit(
            'FAIL: agent.json inputSchema.definitions["job-attachment"] is missing. '
            "Define a job-attachment schema so the agent can accept file inputs "
            "for the Analyze Files tool."
        )
    if ja_def.get("type") != "object":
        sys.exit(
            'FAIL: inputSchema.definitions["job-attachment"] must be an object '
            f'schema, got type={ja_def.get("type")!r}'
        )

    # Critical Rule LC18 — the job-attachment schema is canonical and copied
    # verbatim; `x-uipath-resource-kind: "JobAttachment"` is the required marker
    # that makes the runtime treat the field as a file rather than a plain
    # object. A definition without it validates but silently loses the binding.
    resource_kind = ja_def.get("x-uipath-resource-kind")
    if resource_kind != "JobAttachment":
        sys.exit(
            'FAIL: inputSchema.definitions["job-attachment"] must carry '
            '"x-uipath-resource-kind": "JobAttachment" (Critical Rule LC18 — the '
            f"schema is canonical, copy it verbatim). Got {resource_kind!r}"
        )

    print(
        'OK: inputSchema.definitions["job-attachment"] is defined with '
        'x-uipath-resource-kind="JobAttachment"'
    )

    props = schema.get("properties") or {}
    attachment_inputs = {}
    for name, prop in props.items():
        shape = job_attachment_shape(prop)
        if shape:
            attachment_inputs[name] = shape

    if not attachment_inputs:
        sys.exit(
            "FAIL: no top-level inputSchema property accepts job attachments. "
            f'Expected either {{"$ref": "{JOB_ATTACHMENT_REF}"}} or '
            '{"type": "array", "items": {"$ref": '
            f'"{JOB_ATTACHMENT_REF}"}}}}.'
        )
    print(
        "OK: job-attachment inputs: "
        + ", ".join(
            f"{name} ({shape})"
            for name, shape in attachment_inputs.items()
        )
    )

    messages = agent.get("messages") or []
    bodies = [m.get("content", "") for m in messages if isinstance(m, dict)]
    missing = []
    for name in attachment_inputs:
        # Match {{ input.<name> }} with any internal whitespace.
        pattern = re.compile(
            r"\{\{\s*input\." + re.escape(name) + r"\s*\}\}"
        )
        if not any(pattern.search(body) for body in bodies):
            missing.append(name)
    if missing:
        sys.exit(
            f"FAIL: job-attachment input(s) {missing} are declared but "
            "never referenced as {{input.<name>}} in any message content. "
            "Every attachment input must be wired into a prompt or the "
            "model never sees it."
        )
    print(
        "OK: all job-attachment inputs are referenced in messages: "
        f"{list(attachment_inputs)}"
    )


def assert_prompt_references_tool(agent: dict, tool_name: str) -> None:
    expected_raw = f"tools.{tool_name}"
    literal_pattern = re.compile(
        r"@\{\s*tools\.([^}]+?)\s*\}", re.IGNORECASE
    )

    messages = agent.get("messages")
    if not isinstance(messages, list):
        sys.exit(f"FAIL: agent.json.messages is not a list: {messages!r}")

    referencing = []
    wrong_names = set()
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        for m in literal_pattern.finditer(msg.get("content", "")):
            if m.group(1).strip().lower() == tool_name.lower():
                referencing.append(msg)
                break
            wrong_names.add(m.group(1).strip())

    if not referencing:
        detail = ""
        if wrong_names:
            detail = (
                f" Found @{{tools.…}} references to {sorted(wrong_names)}, but the "
                f"runtime resolves the reference by the resource `name` "
                f"({tool_name!r}), not by folder or toolType."
            )
        contents = {
            m.get("role"): m.get("content")
            for m in messages
            if isinstance(m, dict)
        }
        sys.exit(
            f"FAIL: no message content references @{{{expected_raw}}}.{detail} "
            f"messages={contents!r}"
        )

    for msg in referencing:
        tokens = msg.get("contentTokens")
        if not isinstance(tokens, list):
            sys.exit(
                f"FAIL: {msg.get('role')} message contentTokens is not a list: "
                f"{tokens!r}"
            )
        matched = any(
            isinstance(t, dict)
            and t.get("type") == "expression"
            and isinstance(t.get("rawString"), str)
            and t["rawString"].strip().lower() == expected_raw.lower()
            for t in tokens
        )
        if not matched:
            sys.exit(
                f"FAIL: {msg.get('role')} message content references "
                f"@{{{expected_raw}}} but contentTokens has no matching "
                f'{{"type": "expression", "rawString": "{expected_raw}"}} token '
                "(Critical Rule 6 — `@{ }` references are `expression` tokens, "
                "not `variable`; keep content and contentTokens in sync)\n"
                f"  got tokens: {json.dumps(tokens, indent=2)}"
            )
    roles = ", ".join(str(m.get("role")) for m in referencing)
    print(
        f"OK: prompt references @{{{expected_raw}}} with a synced expression "
        f"token (message roles: {roles})"
    )


def main() -> None:
    tool_name = assert_builtin_tool_enabled()
    agent = load(AGENT_JSON)
    assert_job_attachment_input(agent)
    assert_prompt_references_tool(agent, tool_name)


if __name__ == "__main__":
    main()

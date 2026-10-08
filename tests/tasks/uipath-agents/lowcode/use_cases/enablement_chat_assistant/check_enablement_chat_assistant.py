#!/usr/bin/env python3
"""Enablement chat assistant — conversational knowledge + action agent check.

Final-state only. Validates:
  1. Conversational variant constraints (conversational-critical-rules.md):
     no reserved `messages` / `uipath__*` inputs, the user message
     (messages[1]) is kept but blank with no `{{input...}}` template, and no
     built-in validator or non-Tool-scoped guardrails.
  2. An index context on "UiPathAgentsProductKnowledge" in
     "Shared/uipath-agents" with a valid lowercase retrievalMode, plus its
     bindings_v2.json index binding.
  3. "CustomerFollowUpDrafter" is wired as an external agent tool
     (type=agent, location=external, processName, folderPath of the deployed
     agent, release key as referenceKey) whose input/output schemas mirror
     the agent's InputArgumentsSchemaV2 / OutputArgumentsSchemaV2
     (descriptions ignored).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    UUID_RE,
    assert_index_context,
    assert_project_id,
    assert_unique_resource_ids,
    fail,
    is_index_context,
    load,
    message,
    require_resource,
)

AGENT_DIR = Path(os.getcwd()) / "EnablementSol" / "AgentsEnablementAssistant"
INDEX_NAME = "UiPathAgentsProductKnowledge"
INDEX_FOLDER = "Shared/uipath-agents"
DRAFTER = "CustomerFollowUpDrafter"
DRAFTER_FOLDER = "Shared/uipath-agents/CustomerFollowUpDrafterSol"
# V2 argument schemas of the deployed agent, from `uip solution resources get`.
DRAFTER_INPUT = {
    "type": "object",
    "properties": {k: {"type": "string"} for k in ("customerName", "context", "keyPoints", "tone")},
}
DRAFTER_OUTPUT = {
    "type": "object",
    "properties": {"subject": {"type": "string"}, "body": {"type": "string"}},
}


def strip(node):
    if isinstance(node, dict):
        return {
            k: strip(v) for k, v in node.items()
            if k not in ("description", "title") and not (k == "required" and v == [])
        }
    if isinstance(node, list):
        return [strip(i) for i in node]
    return node


def check_conversational(agent: dict) -> None:
    if (agent.get("metadata") or {}).get("isConversational") is not True:
        fail("agent must be conversational (metadata.isConversational = true)")
    reserved = [
        k for k in ((agent.get("inputSchema") or {}).get("properties") or {})
        if k.lower() in ("messages", "message", "history", "chathistory", "usermessage") or k.startswith("uipath__")
    ]
    if reserved:
        fail(f"conversational inputSchema must not declare chat-history / reserved fields, found {reserved}")
    msgs = agent.get("messages") or []
    if len(msgs) < 2:
        fail("conversational agent must keep the user message (messages[1])")
    user = message(agent, "user")
    if "{{input" in (user.get("content") or ""):
        fail("conversational user message must stay blank, found an {{input...}} template")
    for g in agent.get("guardrails") or []:
        if g.get("$guardrailType") == "builtInValidator":
            fail(f"built-in validator guardrails are autonomous-only, found {g.get('name')!r}")
        scopes = (g.get("selector") or {}).get("scopes")
        if scopes and scopes != ["Tool"]:
            fail(f"conversational guardrails must be Tool-scoped, found scopes {scopes}")
    print("OK: conversational variant constraints hold")


def check_index() -> None:
    _, ctx = require_resource(AGENT_DIR, is_index_context(INDEX_NAME), f"index context on {INDEX_NAME!r}")
    assert_index_context(ctx, INDEX_FOLDER)
    bindings = load(AGENT_DIR / "bindings_v2.json")
    if not any(
        isinstance(r, dict) and r.get("resource") == "index" and r.get("key") == INDEX_NAME
        for r in bindings.get("resources") or []
    ):
        fail(f"bindings_v2.json has no index binding keyed {INDEX_NAME!r}")
    print(f"OK: bindings_v2.json binds index {INDEX_NAME!r}")


def check_drafter_tool() -> None:
    _, tool = require_resource(
        AGENT_DIR,
        lambda d: d.get("$resourceType") == "tool"
        and d.get("type") == "agent"
        and (d.get("properties") or {}).get("processName") == DRAFTER,
        f"agent tool for {DRAFTER!r}",
    )
    if tool.get("location") != "external":
        fail(f"{DRAFTER} is deployed outside this solution — location must be 'external', got {tool.get('location')!r}")
    folder = (tool.get("properties") or {}).get("folderPath")
    if folder != DRAFTER_FOLDER:
        fail(f"{DRAFTER} tool folderPath should be {DRAFTER_FOLDER!r} (from discovery), got {folder!r}")
    rkey = tool.get("referenceKey")
    if not isinstance(rkey, str) or not UUID_RE.match(rkey):
        fail(f"{DRAFTER} tool referenceKey must be the deployed release Key GUID, got {rkey!r}")
    for label, mine, truth in (
        ("inputSchema", tool.get("inputSchema"), DRAFTER_INPUT),
        ("outputSchema", tool.get("outputSchema"), DRAFTER_OUTPUT),
    ):
        if strip(mine) != truth:
            fail(f"{DRAFTER} tool {label} does not mirror the deployed agent's V2 schema (descriptions ignored): {mine!r}")
    print(f"OK: {DRAFTER} wired as an external agent tool ({folder})")


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    assert_project_id(agent)
    check_conversational(agent)
    check_index()
    check_drafter_tool()
    assert_unique_resource_ids(AGENT_DIR)


if __name__ == "__main__":
    main()

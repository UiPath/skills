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
  3. "CustomerFollowUpDrafter" — a project in the same solution — is wired
     as a solution-local agent tool (type=agent, location=solution,
     folderPath=solution_folder, the local resource Key as referenceKey)
     whose input/output schemas mirror the drafter project's
     entry-points.json (descriptions ignored).
  4. The assistant was built inside the existing (fixture) project.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    entry_point_schemas,
    strip_schema,
    assert_existing_project,
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
FIXTURE_AGENT_DIR = Path(__file__).resolve().parent / "_fixtures" / "EnablementSol" / "AgentsEnablementAssistant"
INDEX_NAME = "UiPathAgentsProductKnowledge"
INDEX_FOLDER = "Shared/uipath-agents"
DRAFTER = "CustomerFollowUpDrafter"
# Ground truth from the fixture copy of the solution-local drafter project.
FIXTURE_SOL = Path(__file__).resolve().parent / "_fixtures" / "EnablementSol"
DRAFTER_KEY = json.loads((FIXTURE_SOL / "resources" / "solution_folder" / "process" / "agent" / f"{DRAFTER}.json").read_text())["resource"]["key"]


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
    if tool.get("location") != "solution":
        fail(f"{DRAFTER} is a project in this solution — location must be 'solution', got {tool.get('location')!r}")
    folder = (tool.get("properties") or {}).get("folderPath")
    if folder != "solution_folder":
        fail(f"{DRAFTER} tool folderPath should be 'solution_folder' (Folder of a local resource), got {folder!r}")
    if tool.get("referenceKey") != DRAFTER_KEY:
        fail(f"{DRAFTER} tool referenceKey must be the local resource Key {DRAFTER_KEY!r} from discovery, got {tool.get('referenceKey')!r}")
    want_in, want_out = entry_point_schemas(FIXTURE_SOL / DRAFTER)
    for label, mine, truth in (("inputSchema", tool.get("inputSchema"), want_in), ("outputSchema", tool.get("outputSchema"), want_out)):
        if strip_schema(mine) != strip_schema(truth):
            fail(f"{DRAFTER} tool {label} does not mirror {DRAFTER}/entry-points.json (descriptions ignored): {mine!r}")
    print(f"OK: {DRAFTER} wired as a solution-local agent tool mirroring its project's schemas")


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    assert_project_id(agent)
    assert_existing_project(AGENT_DIR, FIXTURE_AGENT_DIR)
    check_conversational(agent)
    check_index()
    check_drafter_tool()
    assert_unique_resource_ids(AGENT_DIR)


if __name__ == "__main__":
    main()

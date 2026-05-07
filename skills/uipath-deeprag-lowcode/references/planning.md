# DeepRAG in a Low-Code Agent — Planning

## When to Use

Pick this plugin when:

- Project has `agent.json` with `"type": "lowCode"` (standalone) **or** the agent is inline inside a Maestro Flow (`uipath.agent.autonomous` node)
- User is building in Studio Web Agent Builder, no Python
- Agent receives runtime attachments (files uploaded in chat) and must research / synthesize across them
- The expected output is a single grounded narrative answer

Confirm DeepRAG is the right mode first — see [context-grounding-patterns.md](context-grounding-patterns.md).

If the user is building a coded agent (Python, LangGraph, etc.), use the `uipath-deeprag-coded` skill instead.

## Inputs You Need Before Building

| Input | Why | Source |
|---|---|---|
| Agent project shape | Standalone vs. inline-in-flow — affects where `resource.json` lives | Inspect `agent.json` and the parent solution |
| Attachment ingress | The `deep-rag` tool consumes runtime-uploaded attachments — confirm the agent has an attachment input wired | Studio Web schema / `entry-points.json` |
| Prompt wiring | The agent's system prompt or per-call prompt must mention when to invoke the tool | Author / Studio Web |
| Other built-in tools | Do not enable `deep-rag` AND `analyze-attachments` if a single research pass suffices — pick one | User intent |

## Tool Resource Shape

Built-in tools are declared in `resources/<name>/resource.json` with `$resourceType: "tool"`, `type: "internal"`, `referenceKey: null`, and `properties.toolType: "deep-rag"`. See [impl-json.md](impl-json.md) for the exact JSON.

The validator at `tests/tasks/uipath-agents/builtin_tool/check_builtin_tool.py` accepts these `toolType` values: `analyze-attachments`, `load-attachments`, `deep-rag`, `batch-transform`. Anything else fails low-code agent validation.

## Critical Decisions

| Decision | Rule |
|---|---|
| `deep-rag` vs `analyze-attachments` | DeepRAG synthesizes across multiple attachments / iterative research; analyze-attachments does single-file extraction. See [context-grounding-patterns.md](context-grounding-patterns.md) for the BT/DR/index decision matrix. |
| `deep-rag` vs `load-attachments` | `load-attachments` only makes attachment text available to the agent; `deep-rag` runs an iterative synthesis pass. Use `load-attachments` when the agent will reason directly over short contents; use `deep-rag` for long / multiple docs. |
| Standalone agent vs inline-in-flow | Same `resource.json` shape for both. The flow wiring differs — inline requires an edge from the agent's `tool` port to the tool node's `input` port. See [impl-json.md](impl-json.md). |

## Bindings / Permissions

DeepRAG runs in the folder context of the running agent. The tool requires the index permission in that folder — same rule as the coded surface. If the agent is published to a folder where the user lacks rights, DeepRAG calls fail with 403. Use the personal workspace (or a folder the agent's runtime identity has rights in) for self-serve.

## Hand-off

Once planning is complete, implement per [impl-json.md](impl-json.md).

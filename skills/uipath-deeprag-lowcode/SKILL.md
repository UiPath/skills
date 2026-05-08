---
name: uipath-deeprag-lowcode
description: "UiPath DeepRAG in low-code agents (Studio Web Agent Builder, `agent.json` `type: lowCode`) — PDF / TXT input only. Enable the built-in `deep-rag` tool resource (`$resourceType: tool`, `type: internal`, `properties.toolType: deep-rag`) so the runtime synthesizes across runtime attachments. For Python coded agents→uipath-deeprag-coded. For CSV input (BatchTransform)→uipath-batch-transform-lowcode. For index search→uipath-agents. For C# or XAML→uipath-rpa."
when_to_use: "User wants a low-code agent (Studio Web Agent Builder, `agent.json`+`project.uiproj`, no Python) that summarizes / researches / synthesizes content from runtime-uploaded attachments. Triggers: 'add deep rag to my low-code agent', 'enable deeprag in agent builder', 'built-in deep-rag tool', 'analyze uploaded files in studio web'. NOT for Python coded agents (→uipath-deeprag-coded), stable indexed knowledge bases (→uipath-agents), or per-row bulk extraction (→BatchTransform)."
user-invocable: true
---

# UiPath DeepRAG — Low-Code Agent

DeepRAG runs an iterative research-and-synthesis pass over an ephemeral context-grounding index built from attachments.

Low-code surface: Studio Web Agent Builder, `agent.json` projects. Enable the built-in `deep-rag` tool resource; runtime handles the index lifecycle and resume events.

## When to Use

Read [references/context-grounding-patterns.md](references/context-grounding-patterns.md) first — picks by **file type**: PDF/TXT → DeepRAG; CSV → BatchTransform.

Use when:

- Input file is `.pdf` or `.txt` (one or more)
- Project has `agent.json` with `"type": "lowCode"` (standalone) **or** the agent is inline in a Maestro Flow (`uipath.agent.autonomous` node)
- Studio Web Agent Builder, no Python
- Expected output is a single grounded narrative answer

For `.csv` input → `uipath-batch-transform-lowcode`. For coded agents (Python, LangGraph) → `uipath-deeprag-coded`.

## Critical Rules

1. **Built-in tool shape is fixed.** `resource.json` MUST set `$resourceType: "tool"`, `type: "internal"`, `referenceKey: null`, `isEnabled: true`, `properties.toolType: "deep-rag"`. Validator rejects anything else. See [references/impl-json.md](references/impl-json.md).
2. **Resource directory name is free-form**, file MUST be exactly `resource.json` under `<agent>/resources/<any-name>/`. Validators scan recursively.
3. **`properties.toolType` is one of four values.** `analyze-attachments`, `load-attachments`, `deep-rag`, `batch-transform`. Use `deep-rag` for iterative cross-document synthesis. See [references/planning.md](references/planning.md) tiebreaker for the others.
4. **Inline-in-flow requires explicit edge wiring.** Flow must contain a `uipath.agent.autonomous` node and a built-in tool node under the `uipath.agent.resource.tool.*` prefix (canonical: `uipath.agent.resource.tool.builtin`; verify with `uip maestro flow registry search "uipath.agent.resource.tool" --output json`), with an edge from the agent's `tool` source port to the tool node's `input` target port.
5. **System prompt matters.** Effectiveness depends on instructions telling the agent when to invoke the tool, what to pass as the prompt, how to combine the result with conversation context. Vague prompt → underuse.
6. **Permissions live on the folder.** Runtime executes DeepRAG in the agent's runtime folder. Lacking the index permission → `403`.
7. **Attachment ingress is automatic in chat surfaces.** Studio Web forwards conversation attachments to the tool. For other channels (flow input, Action Center task), confirm the runtime forwards them or the tool runs against an empty set.

## Quick Start

1. Confirm DeepRAG is the right mode → [references/context-grounding-patterns.md](references/context-grounding-patterns.md)
2. Plan the agent (standalone vs inline-in-flow, tool selection) → [references/planning.md](references/planning.md)
3. Scaffold the solution + agent project: `uip solution new "<SOLUTION>" --output json`, `uip agent init "<AGENT>" --output json` (add `--inline-in-flow` for inline), `uip solution project add "<AGENT>" --output json`
4. Author `resource.json` with the exact built-in shape → [references/impl-json.md](references/impl-json.md)
5. Validate via `uip agent validate --output json`
6. Pack and publish via `uip solution upload . --output json`

## Reference Navigation

| I need to... | Read |
|---|---|
| Pick the right context-grounding mode | [references/context-grounding-patterns.md](references/context-grounding-patterns.md) |
| Plan the low-code agent / pick the right built-in tool | [references/planning.md](references/planning.md) |
| Author the `resource.json` (standalone + inline-in-flow shapes) | [references/impl-json.md](references/impl-json.md) |
| Hit the API directly (debug only) | [references/api-reference.md](references/api-reference.md) |

## Anti-Patterns

- ❌ **Setting `referenceKey` to a non-null value** on a built-in tool. Non-null `referenceKey` identifies an external tool reference — built-in tools must use `null`.
- ❌ **Setting `type` to anything other than `"internal"`** for a built-in tool. The validator rejects `"external"`, `"custom"`, etc. for built-ins.
- ❌ **Reaching for `analyze-attachments` instead of `deep-rag` on non-trivial documents.** `analyze-attachments` has lower page limits and is one-shot synthesis — it struggles to output as much as DeepRAG. Prefer `deep-rag` for large files, citations, or longer answers; reach for `analyze-attachments` only for small single-file extraction.
- ❌ **Using `deep-rag` when the task is per-row / tabular.** That is BatchTransform.
- ❌ **Forgetting to wire the tool node** in inline-in-flow agents. The flow must have an explicit edge from agent `tool` → tool node `input`.
- ❌ **Vague system prompt.** Without "when to call DeepRAG" guidance, the agent will misroute work.

## Resources

- Agent project validator: `uip agent validate --output json`
- UiPath Python SDK (for the underlying API): <https://uipath.github.io/uipath-python/>

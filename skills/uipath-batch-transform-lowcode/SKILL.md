---
name: uipath-batch-transform-lowcode
description: "UiPath BatchTransform in low-code agents (Studio Web Agent Builder, `agent.json` `type: lowCode`) — CSV input only. Enable the built-in `batch-transform` tool resource (`$resourceType: tool`, `type: internal`, `properties.toolType: batch-transform`) so the runtime iterates CSV rows (CSV is the datasource), applies an LLM prompt to each, and emits an Orchestrator bucket attachment with new columns. Optional per-row web grounding. For Python coded agents→uipath-batch-transform-coded. For PDF/TXT (DeepRAG)→uipath-deeprag-lowcode. For C# or XAML→uipath-rpa."
when_to_use: "User wants a low-code agent (Studio Web Agent Builder, `agent.json`+`project.uiproj`, no Python) that processes tabular data (CSV) row-by-row with an LLM — bulk extraction, classification, address-match validation, vendor enrichment, sales-order triage, MCC categorization. Triggers: 'add deeprag-style columns to a CSV in agent builder', 'enable batch transform tool', 'built-in batch-transform tool', 'classify rows in a low-code agent'. NOT for Python coded agents (→uipath-batch-transform-coded), one-document narrative synthesis (→uipath-deeprag-lowcode), or stable indexed knowledge bases (→uipath-agents)."
user-invocable: true
---

# UiPath BatchTransform — Low-Code Agent

BatchTransform applies one LLM prompt to every row of a CSV and writes augmented rows (original columns + new LLM-filled columns) to an Orchestrator bucket attachment. CSV is the datasource — hosted in a context-grounding index purely so the runtime can iterate. The index is NOT used to ground answers. Optional per-row web grounding when a row alone is not enough.

Low-code surface: Studio Web Agent Builder, `agent.json` projects. Enable the built-in `batch-transform` tool resource; runtime handles the index lifecycle, output upload, resume events.

> Product use cases: address-match validation, sales-order next-action recommendations, MCC categorization.

## When to Use

Read [references/context-grounding-patterns.md](references/context-grounding-patterns.md) first — picks by **file type**: CSV → BatchTransform; PDF/TXT → DeepRAG.

Use when:

- Input file is `.csv`
- Project has `agent.json` with `"type": "lowCode"` (standalone) **or** the agent is inline in a Maestro Flow (`uipath.agent.autonomous` node)
- Studio Web Agent Builder, no Python
- Output destination is an Orchestrator bucket attachment downstream consumers (RPA, agents) can read

For `.pdf` / `.txt` input → `uipath-deeprag-lowcode`. For coded agents (Python, LangGraph) → `uipath-batch-transform-coded`.

## Critical Rules

1. **Built-in tool shape is fixed.** `resource.json` MUST set `$resourceType: "tool"`, `type: "internal"`, `referenceKey: null`, `isEnabled: true`, `properties.toolType: "batch-transform"`. Validator rejects anything else. See [references/impl-json.md](references/impl-json.md).
2. **Resource directory name is free-form**, file MUST be exactly `resource.json` under `<agent>/resources/<any-name>/`. Validators scan recursively.
3. **`properties.toolType` is one of four values.** `analyze-attachments`, `load-attachments`, `deep-rag`, `batch-transform`. Use `batch-transform` for per-row LLM-filled columns. See [references/planning.md](references/planning.md) tiebreaker for the others.
4. **Inline-in-flow requires explicit edge wiring.** Flow must contain a `uipath.agent.autonomous` node and a built-in tool node under the `uipath.agent.resource.tool.*` prefix (canonical: `uipath.agent.resource.tool.builtin`; verify with `uip maestro flow registry search "uipath.agent.resource.tool" --output json`), with an edge from the agent's `tool` source port to the tool node's `input` target port.
5. **System prompt + per-column descriptions matter.** Agent instructions must say when to invoke the tool, what top-level prompt to send, and how to describe each output column. Vague instructions → inconsistent columns.
6. **Web search grounding is opt-in.** `enable_web_search_grounding` defaults off. Enable only when the per-row task needs info NOT already in the row.
7. **Permissions live on the folder.** Runtime executes BatchTransform in the agent's runtime folder. Confirm the agent's identity has the index permission and write access to the destination bucket. Failures: `403` (read) or `400` (folder/permission).
8. **Output is an Orchestrator bucket attachment**, not an inline value. Plan the destination path / target file name; downstream RPA or agent steps read from the bucket.

## Quick Start

1. Confirm BatchTransform is the right mode → [references/context-grounding-patterns.md](references/context-grounding-patterns.md)
2. Plan the agent (standalone vs inline-in-flow, output columns, web grounding default) → [references/planning.md](references/planning.md)
3. Scaffold the solution + agent project: `uip solution new "<SOLUTION>" --output json`, `uip agent init "<AGENT>" --output json` (add `--inline-in-flow` for inline), `uip solution project add "<AGENT>" --output json`
4. Author `resource.json` with the exact built-in shape and configure `output_columns` + prompt → [references/impl-json.md](references/impl-json.md)
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

- ❌ **Non-null `referenceKey` on a built-in tool.** Identifies an external tool — built-ins use `null`.
- ❌ **`type` other than `"internal"` for a built-in.** Validator rejects `"external"`, `"custom"`, etc.
- ❌ **Using `batch-transform` when `deep-rag` fits.** Cross-document narrative is DeepRAG. BatchTransform produces one row per input row.
- ❌ **Using `batch-transform` for one-off file analysis.** That is `analyze-attachments`.
- ❌ **Missing tool-node edge in inline-in-flow agents.** Flow must have an explicit edge from agent `tool` → tool node `input`.
- ❌ **Vague output-column descriptions.** "category" produces noise. "Return the 4-digit MCC code, or UNKNOWN if uncertain. Output only the code." produces consistent results.
- ❌ **Enabling web search by default.** Enable only when fresh external data is required.

## Resources

- Agent project validator: `uip agent validate --output json`
- UiPath Python SDK (for the underlying API): <https://uipath.github.io/uipath-python/>

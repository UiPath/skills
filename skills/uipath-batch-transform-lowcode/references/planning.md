# BatchTransform in a Low-Code Agent — Planning

## When to Use

Pick this skill when:

- Project has `agent.json` with `"type": "lowCode"` (standalone) **or** the agent is inline inside a Maestro Flow (`uipath.agent.autonomous` node)
- User is building in Studio Web Agent Builder, no Python
- Source data is tabular (CSV) — one input row should produce one output row plus extra LLM-filled columns
- Output destination is an Orchestrator bucket attachment downstream consumers (RPA, agents) can read

Confirm BatchTransform is the right mode first — see [context-grounding-patterns.md](context-grounding-patterns.md).

If the user is building a coded agent (Python, LangGraph, etc.), use the `uipath-batch-transform-coded` skill instead.

## Inputs You Need Before Building

| Input | Why | Source |
|---|---|---|
| Agent project shape | Standalone vs. inline-in-flow — affects where `resource.json` lives | Inspect `agent.json` and the parent solution |
| Tool resource configuration | Top-level prompt + per-column descriptions + web-grounding default | Author / Studio Web tool config |
| Attachment ingress | The `batch-transform` tool consumes runtime-uploaded CSV attachments — confirm the agent has an attachment input wired | Studio Web schema / `entry-points.json` |
| Output destination | Bucket + path where the augmented CSV is written | User config; include unique suffix per run to avoid overwrites |
| Web grounding default | Whether to enable web search per row by default | User flag; default off (turn on only when the task needs fresh external data) |
| System prompt | Tells the agent when to invoke `batch-transform` and how to frame the row prompt | Author / Studio Web |

## Tool Resource Shape

Built-in tools are declared in `resources/<name>/resource.json` with `$resourceType: "tool"`, `type: "internal"`, `referenceKey: null`, and `properties.toolType: "batch-transform"`. See [impl-json.md](impl-json.md) for the exact JSON.

Built-in tools accept these `toolType` values: `analyze-attachments`, `load-attachments`, `deep-rag`, `batch-transform`. Anything else fails `uip agent validate`.

### Tool resource vs context-index resource

There are two valid shapes for enabling BatchTransform on a low-code agent. This skill documents the **built-in tool** shape (the agent invokes BatchTransform through its tool-calling loop). The alternative is a **context-index resource** that wires BatchTransform as a retrieval mode on a pre-built ECS index — `$resourceType: "context"`, `contextType: "index"`, `retrievalMode: "batchtransform"` (lowercase, no hyphen — `uip agent validate` accepts camelCase but Studio Web silently drops the resource on import), with `webSearchGrounding` and `outputColumns` set on the resource. Use the context-index form when the CSV lives in a stable, pre-built index reused across runs and the agent should query it transparently as context; use the tool form (this skill) when the CSV is a runtime attachment and the agent must decide row-by-row when to invoke it.

## Critical Decisions

| Decision | Rule |
|---|---|
| `batch-transform` vs `deep-rag` | Pick by input file type: `.csv` → `batch-transform`; `.pdf` / `.txt` → `deep-rag`. Hard rule, no subjective tiebreaker. See [context-grounding-patterns.md](context-grounding-patterns.md). |
| `batch-transform` vs `analyze-attachments` | `analyze-attachments` does single-file, single-shot extraction. `batch-transform` iterates across all rows of a CSV at scale. |
| Standalone agent vs inline-in-flow | Same `resource.json` shape for both. The flow wiring differs — inline requires an edge from the agent's `tool` port to the tool node's `input` port. See [impl-json.md](impl-json.md). |
| Output column names | Must match regex `^[\w\s\.,!?-]+$`. No `/`, `:`, `&`, `(`, `)`, or other special chars. |
| Output column descriptions | Each is the per-column LLM instruction. Be specific about format, enums, and "when uncertain" handling. Worked examples improve quality. |
| Web grounding default | Off unless the prompt explicitly needs fresh external data. |

## Bindings / Permissions

BatchTransform runs in the folder context of the running agent. The tool requires the index permission and write access to the destination bucket. If the agent is published to a folder where its identity lacks rights, runs fail with 403 (read) or 400 (folder/permission).

## Output Handling

Output is an Orchestrator bucket attachment, not an inline value the agent returns to the chat. Plan for:

- A unique destination path per run (timestamp / UUID suffix)
- Downstream RPA / agent steps that read the attachment and continue processing
- A summary message the agent posts back to chat with the bucket location, row count, and any failure summary

## Hand-off

Once planning is complete, implement per [impl-json.md](impl-json.md).

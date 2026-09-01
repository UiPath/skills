# BatchTransform in a Low-Code Agent — Planning

## When to Use

Use this skill when all apply:

- `agent.json` has `"type": "lowCode"` (standalone), or the agent is inline in a Maestro Flow (`uipath.agent.autonomous` node).
- The agent is built in Studio Web Agent Builder without Python.
- Source data is tabular CSV, with one output row per input row plus LLM-filled columns.
- Output is an Orchestrator bucket attachment for downstream RPA or agent consumers.

Confirm BatchTransform is appropriate first: [../../../../context-grounding-patterns.md](../../../../context-grounding-patterns.md).

For coded agents (Python, LangGraph), use [../../../../coded/capabilities/batch-transform/planning.md](../../../../coded/capabilities/batch-transform/planning.md).

## Confirm Before Building

- **Project shape:** Identify standalone versus inline-in-flow; this determines where `resource.json` lives. Inspect `agent.json` and the parent solution.
- **Tool configuration:** Confirm the top-level prompt, per-column descriptions, and web-grounding default in the authoring or Studio Web tool configuration.
- **Attachment ingress:** Confirm that `batch-transform` receives runtime-uploaded CSV attachments through a wired attachment input in the Studio Web schema / `entry-points.json`.
- **Output destination:** Define the bucket and path, adding a unique suffix per run to prevent overwrites.
- **Web grounding:** Default to off; enable only when each row needs fresh external data.
- **System prompt:** Specify when to invoke `batch-transform` and how to frame the row prompt.

## Resource Shapes

Declare a built-in tool in `resources/<name>/resource.json` with `$resourceType: "tool"`, `type: "internal"`, `referenceKey: null`, and `properties.toolType: "batch-transform"`. See [impl-json.md](impl-json.md) for the exact JSON.

Valid built-in `toolType` values are `analyze-attachments`, `load-attachments`, `deep-rag`, and `batch-transform`. Run `uip agent validate` to validate the agent; any other value fails validation.

This tool shape invokes BatchTransform through the agent's tool-calling loop. The alternative context-index shape uses `$resourceType: "context"`, `contextType: "index"`, and `retrievalMode: "batchtransform"` (lowercase, no hyphen). `uip agent validate` accepts camelCase, but Studio Web silently drops the resource on import. Set `webSearchGrounding` and `outputColumns` on the context resource.

Use the context-index shape when a CSV is in a stable, pre-built ECS index reused across runs and should be queried transparently as context. Use the tool shape when the CSV is a runtime attachment and the agent must decide row-by-row when to invoke BatchTransform.

## Critical Decisions

- **`batch-transform` vs. `deep-rag`:** Choose by file type: `.csv` → `batch-transform`; `.pdf` / `.txt` → `deep-rag`. This is a hard rule.
- **`batch-transform` vs. `analyze-attachments`:** `analyze-attachments` performs single-file, single-shot extraction; `batch-transform` iterates over all CSV rows at scale.
- **Standalone vs. inline-in-flow:** Use the same `resource.json` shape. Inline flows additionally require an edge from the agent's `tool` port to the tool node's `input` port. See [impl-json.md](impl-json.md).
- **Output column names:** Match `^[\w\s\.,!?-]+$`; do not use `/`, `:`, `&`, `(`, `)`, or other special characters.
- **Output column descriptions:** Provide each column's LLM instruction, including format, enums, and handling when uncertain. Worked examples improve quality.
- **Web grounding:** Keep it off unless the prompt explicitly requires fresh external data.

## Bindings, Permissions, and Output

BatchTransform runs in the running agent's folder context and requires index permission plus write access to the destination bucket. If the published agent identity lacks those rights, runs fail with 403 (read) or 400 (folder/permission).

BatchTransform returns an Orchestrator bucket attachment, not an inline chat value. Plan to:

- Write to a unique destination path per run using a timestamp or UUID suffix.
- Have downstream RPA or agent steps read the attachment and continue processing.
- Post a chat summary containing the bucket location, row count, and any failure summary.

## Hand-off

After planning, implement according to [impl-json.md](impl-json.md).

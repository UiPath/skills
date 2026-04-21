# Batch Transform Pattern Node — Planning

The Batch Transform node runs an LLM over every row of an attached CSV (or similar tabular file) and appends one or more **LLM-generated columns** to each row. Think "row-wise enrichment with a prompt" — classification, summarization, entity extraction, categorization. It is one of two nodes in the **Patterns** category (alongside [Deep RAG](../deep-rag/planning.md)).

## Node Type

`uipath.pattern.batch-transform`

This is a fixed OOTB node type — no registry suffix, one version. It does not appear in `uip flow registry list` unless the tenant has the platform-side `canvas.nodes.patterns` feature flag enabled. The uip CLI unconditionally requests Patterns nodes in its manifest fetch, so they will appear once the server rolls the flag out to your tenant.

## When to Use

Use Batch Transform when the task is **"do this to every row"** and the per-row work requires natural-language reasoning that is impractical to express as code.

### Selection Heuristics

| Situation | Use Batch Transform? |
| --- | --- |
| Add LLM-generated columns to each row of a CSV (category, sentiment, one-line summary) | Yes |
| Enrich rows with web-searched facts (e.g., look up a company's HQ city per row) | Yes — set `enableWebSearchGrounding: true` |
| Small ad-hoc data shape change (rename, filter, groupBy) on an in-memory array | No — use [Transform](../transform/planning.md) |
| Per-row side effects (API calls, DB writes) | No — use [Loop](../loop/planning.md) with the per-row action inside |
| Reason over a **single** document and produce a synthesis with citations | No — use [Deep RAG](../deep-rag/planning.md) |
| Row-count unknown but small (< 20) and the agent should decide how to reason | Consider [Agent](../agent/planning.md) with the collection in its context instead |

### Anti-Patterns

- **Do not use Batch Transform for deterministic work.** If the new column is a formula, regex match, or date reformat, use [Transform](../transform/planning.md) or [Script](../script/planning.md) — the LLM adds cost and latency for no accuracy gain.
- **Do not use Batch Transform as a general loop.** It only produces new columns attached to the same rows; it cannot call APIs or perform side effects per row. Use [Loop](../loop/planning.md) for that.
- **Do not pass reasoning-heavy instructions that depend on the whole document.** Each row is processed with only its own values plus the prompt — it cannot "see" other rows or an external document. For cross-row reasoning, pre-aggregate with [Transform](../transform/planning.md) first, or use [Deep RAG](../deep-rag/planning.md) over a synthesized attachment.

## Ports

| Port | Position | Direction | Use |
| --- | --- | --- | --- |
| `input` | left | target | Flow sequence input |
| `output` | right | source | Produced file handle with the new columns appended |
| `error` | right | source | Error handler (populated when the batch job fails) |

No artifact ports. Patterns nodes do not wire to resource files — the prompt and column definitions live on the node inputs.

## Output Variables

- `$vars.{nodeId}.output` — file handle of the result CSV: `{ id, fileName, mimeType }`. Pass this to downstream nodes that consume files (e.g., another Batch Transform, a connector that uploads the result).
- `$vars.{nodeId}.error` — populated on failure: `{ code, message, detail, category, status }`.

## Key Inputs

| Input | Required | Type | Description |
| --- | --- | --- | --- |
| `attachment` | Yes | string (file ref) | The source CSV. Pass a `$vars.*` reference to an upstream file handle, or a concrete UiPath file URI. |
| `prompt` | Yes | string | The instruction describing what each output column should contain. Can reference column names from the source via natural language ("summarize the `Description` field"). |
| `outputColumns` | Yes | array of `{ name, description }` | The columns to produce. Max 10. `name` is the column header; `description` tells the LLM what to put in it. |
| `enableWebSearchGrounding` | No | boolean | When `true`, the LLM can issue web searches per row to ground its answer. Slower and costlier — use only when rows need external facts. Default `false`. |

### `outputColumns` shape

```json
[
  { "name": "Category", "description": "One of: Invoice, Receipt, Contract, Other" },
  { "name": "Summary",  "description": "One-line plain-English summary of the row" }
]
```

Do not reshape — the canvas editor writes exactly this `{ name, description }` shape, and downstream serialization (BPMN `ECS.BatchTransform` service task) depends on it.

## Planning Annotation

In the architectural plan:

- `pattern: batch-transform — <one-line purpose>` with a placeholder for the attachment source (usually a `$vars.<upstream>.output.*` file handle) and the list of output column names.
- Call out `enableWebSearchGrounding` in **Open Questions** if the requirements hint at external lookups but are not explicit — the cost/latency jump warrants confirmation.

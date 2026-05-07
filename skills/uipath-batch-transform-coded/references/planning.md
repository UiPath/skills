# BatchTransform in a Coded Agent — Planning

## When to Use

Pick this skill when:

- Project has `pyproject.toml` with `uipath` / `uipath-langchain`, plus `langgraph.json` or a graph-style `main.py`
- Source data is tabular (CSV) — one input row should produce one output row plus extra LLM-filled columns
- Workload is throughput-driven (hundreds to thousands of rows per file)
- User wants Python control over upstream prep (download, reshape, dedupe) or downstream routing (push results to Data Service, Orchestrator queue, follow-up agent, etc.)

Confirm BatchTransform is the right mode first — see [context-grounding-patterns.md](context-grounding-patterns.md).

If the user is in Studio Web Agent Builder, use `uipath-batch-transform-lowcode` instead.

## Inputs You Need Before Building

| Input | Why | Where to get it |
|---|---|---|
| Source file (CSV) | The data BatchTransform iterates over | Bucket / agent input / upstream node |
| Prompt | Top-level task framing — sent with every row | User input or static default |
| `output_columns` | Names + descriptions of new columns the LLM fills per row | User spec; each `description` is the per-column instruction |
| `enable_web_search_grounding` | Whether each row is augmented with a web search before answering | User flag; default `False` (turn on only when the task needs fresh external data) |
| Index strategy | Ephemeral (attachments-backed, one-shot) vs existing index | Default ephemeral for CSV-in / CSV-out; existing index when the corpus is stable |
| `destination_path` | LOCAL filesystem path where the runtime writes the augmented CSV on resume | Include a unique suffix per run (UUID/timestamp) |
| Target folder for ingestion + BatchTransform | Permission scope | Default to personal workspace key for self-serve |

## Pipeline Shape

Standard ephemeral-attachment flow:

1. `fetch_source` — accept / download the source CSV → local path
2. `upload_attachment` — `sdk.attachments.upload_async` → attachment uuid
3. `create_index` — **`@durable_interrupt`** returning `CreateEphemeralIndex(usage=EphemeralIndexUsage.BATCH_RAG, attachments=[...])` → `ContextGroundingIndex` (already ingested)
4. `run_batch_transform` — **`@durable_interrupt`** returning `CreateBatchTransform(is_ephemeral_index=True, index_id=..., output_columns=[...], destination_path=<local-path>, enable_web_search_grounding=..., ...)` → confirmation string; runtime writes augmented CSV to `destination_path` on disk
5. `finalize` — return the local `destination_path` (or read the CSV for downstream nodes)

If targeting an existing index instead of attachments, skip steps 2 and 3; pass `index_name=...` (without `is_ephemeral_index`) on step 4.

## `BatchTransformOutputColumn` Authoring

Each entry in `output_columns` has `name` and `description`. Treat the description as the prompt-fragment the LLM uses to fill that column for every row.

| Field | Constraint | Tips |
|---|---|---|
| `name` | 1–500 chars, regex `^[\w\s\.,!?-]+$` | Friendly column header. No special characters beyond `. , ! ? -`. |
| `description` | 1–20000 chars | Be specific about what to extract / classify, the format (free text, enum, JSON), and what to output when uncertain. Worked examples improve quality. |

Example:

```python
[
    BatchTransformOutputColumn(
        name="MCC Code",
        description=(
            "Return the 4-digit Merchant Category Code that best fits the merchant. "
            "If unsure, return UNKNOWN. Output only the code or UNKNOWN, no commentary."
        ),
    ),
    BatchTransformOutputColumn(
        name="Confidence",
        description="Confidence in the MCC classification: HIGH, MEDIUM, or LOW.",
    ),
]
```

## Critical Decisions

| Decision | Rule |
|---|---|
| Sync vs durable | Always durable for `create_index` and `run_batch_transform`. Never poll — runs are long-lived. |
| Folder for index | Personal workspace key by default for self-serve. Override only when the user has confirmed role permissions in another folder. |
| Ephemeral vs existing index | Default ephemeral for one-shot runs from a runtime CSV. Use an existing index only if the same data is reused across runs. |
| Web search grounding | Default `False`. Enable only when prompts depend on fresh external info (address verification, current company status). |
| `destination_path` collisions | Include a UUID or timestamp suffix (`results/run-{ts}.csv`) so concurrent or repeated runs don't overwrite each other. |
| Result handling | Augmented CSV lands at the local `destination_path` after resume. Plan whether the agent returns the path, re-uploads to a bucket for RPA, or reads the CSV inline. |

## Bindings

The source bucket (if you download the CSV from one) is bindable. Attachments, ephemeral indexes, and the local `destination_path` are NOT bindable — they are runtime-created or local-only. If the agent re-uploads the augmented CSV to a destination bucket, that destination bucket is also bindable.

## Local-Run Behavior

`uip codedagent run agent '{...}'` exits at the first interrupt. That is correct — the runtime captured suspend state and would resume on the platform event. For end-to-end verification: deploy and invoke from the platform, or use `uip codedagent dev`.

## Hand-off

Once planning is complete, implement per [impl-python.md](impl-python.md).

# DeepRAG in a Coded Agent — Planning

## When to Use

Pick this when:

- Project has `pyproject.toml` with `uipath` / `uipath-langchain`, plus `langgraph.json` or a graph-style `main.py`
- User wants Python / programmatic control over the pipeline
- Agent needs to combine DeepRAG with custom pre/post-processing (download from bucket, validate, route, etc.)
- Agent must run unattended (scheduled, queue-triggered, or invoked from another agent)

Confirm DeepRAG is the right mode first — see [../../../context-grounding-patterns.md](../../../context-grounding-patterns.md).

For Studio Web Agent Builder → [../../lowcode/capabilities/built-in-tools/deeprag/planning.md](../../lowcode/capabilities/built-in-tools/deeprag/planning.md).

## Inputs You Need Before Building

| Input | Why | Where to get it |
|---|---|---|
| File source | Determines the first node | Bucket / queue payload / attachment id from upstream |
| Bucket name + folder path (if downloading) | `sdk.buckets.download_async` arguments | User config or hardcoded constant |
| Prompt | DeepRAG `prompt` body field — required, non-empty | User input or static default |
| Target folder for ingestion + DeepRAG | Permission scope | Default to personal workspace key for self-serve |
| Citation mode | Per `CitationMode` enum in the SDK (currently `SKIP`, `INLINE` — verify at your version) | User preference; default `SKIP` |

## Pipeline Shape

Standard 5-node graph:

1. `fetch_file` — download / accept input file → local path
2. `upload_attachment` — `sdk.attachments.upload_async` → attachment uuid
3. `create_index` — **`@durable_interrupt`** returning `CreateEphemeralIndex` → `ContextGroundingIndex` (already ingested)
4. `run_deep_rag` — **`@durable_interrupt`** returning `CreateDeepRag(is_ephemeral_index=True, ...)` → `DeepRagContent`
5. `finalize` — shape `GraphOutput`

Steps 3 and 4 use the resume-trigger pattern so the agent suspends and resumes on platform completion events. Polling kills the serverless 15-min job timeout — see [impl-python.md](impl-python.md) for the rule and the implementation.

## Critical Decisions

| Decision | Rule |
|---|---|
| Sync vs durable | Always durable for create-index and run-deep-rag. Never poll. |
| Folder for index | Personal workspace key by default. Only override when the user has confirmed role permissions in another folder. |
| Citation mode | Default `SKIP` for summarization. Use `INLINE` when the user asks for inline source references. Verify available values via the SDK's `CitationMode` enum. |
| `is_ephemeral_index` | Always `True` on `CreateDeepRag` when `index_id` came from `CreateEphemeralIndex`. Runtime requires the flag to route as ephemeral; missing it fails server-side. The Pydantic validator only catches the inverse case (`is_ephemeral_index=True` with `index_id=None`). |
| Mock-friendly outputs | Return shapes that work whether the resume value is the typed model or a dict — see the defensive accessor in [impl-python.md](impl-python.md). |

## Bindings

The bucket counts as a bindable resource. Attachments and ephemeral indexes do NOT — they are runtime-created.

## Local-Run Behavior

`uip codedagent run agent '{...}'` exits at the first interrupt. That is correct — the runtime has captured suspend state and would resume on the platform event. For end-to-end verification: deploy the agent (or `uip codedagent dev`) and invoke from the platform.

## Hand-off

Once planning is complete, implement per [impl-python.md](impl-python.md).

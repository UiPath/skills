# DeepRAG in a Coded Agent — Planning

## When to Use

Use this skill when the project has `pyproject.toml` with `uipath` / `uipath-langchain` plus `langgraph.json` or a graph-style `main.py`, and the user needs Python control, custom pre/post-processing, or unattended execution (scheduled, queue-triggered, or agent-invoked).

Confirm DeepRAG is appropriate first: [../../../context-grounding-patterns.md](../../../context-grounding-patterns.md).

For Studio Web Agent Builder, use [../../../lowcode/capabilities/built-in-tools/deeprag/planning.md](../../../lowcode/capabilities/built-in-tools/deeprag/planning.md).

## Inputs Required Before Building

| Input | Purpose | Source |
|---|---|---|
| File source | Determines the first node | Bucket, queue payload, or upstream attachment id |
| Bucket name and folder path, if downloading | Arguments to `sdk.buckets.download_async` | User configuration or hardcoded constant |
| Prompt | Required, non-empty DeepRAG `prompt` body field | User input or static default |
| Target folder for ingestion and DeepRAG | Determines permission scope | Default to the personal workspace key for self-serve |
| Citation mode | `CitationMode` value; currently `SKIP` or `INLINE`, subject to SDK version | User preference; default `SKIP` |

## Pipeline Shape

Build this standard five-node graph:

1. `fetch_file` — download or accept the input file and return a local path.
2. `upload_attachment` — call `sdk.attachments.upload_async` and return the attachment UUID.
3. `create_index` — call `create_ephemeral_index_async`; check `in_progress_ingestion()`; conditionally call `interrupt(WaitEphemeralIndex(...))`; then return `ContextGroundingIndex`.
4. `run_deep_rag` — call `interrupt(CreateDeepRag(is_ephemeral_index=True, ...))` and return `DeepRagContent`.
5. `finalize` — shape `GraphOutput`.

Use plain `interrupt()` for steps 3 and 4 so the agent suspends and resumes on platform completion events. Do not poll; polling can exceed the serverless 15-min job timeout. See [impl-python.md](impl-python.md).

## Critical Decisions

| Decision | Rule |
|---|---|
| Sync vs. interrupt | Always use `interrupt()` for create-index, conditionally, and run-deep-rag. Never poll. |
| Index folder | Use the personal workspace key by default. Override it only after the user confirms role permissions in another folder. |
| Citation mode | Use `SKIP` by default for summarization. Use `INLINE` when inline source references are requested. Verify values through the SDK's `CitationMode` enum. |
| `is_ephemeral_index` | Set it to `True` on `CreateDeepRag` whenever `index_id` came from `CreateEphemeralIndex`. The runtime requires this flag for ephemeral routing; omitting it fails server-side. The Pydantic validator only catches the inverse case: `is_ephemeral_index=True` with `index_id=None`. |
| Mock-friendly outputs | Support resume values that are either the typed model or a dict; use the defensive accessor in [impl-python.md](impl-python.md). |

## Bindings

The bucket is a bindable resource. Attachments and ephemeral indexes are runtime-created and are not bindable.

## Local-Run Behavior

`uip codedagent run agent '{...}'` exits at the first interrupt. This is expected: the runtime has captured suspend state and would resume on the platform event. For end-to-end verification, deploy the agent or run `uip codedagent dev` and invoke it from the platform.

## Hand-off

After planning, implement according to [impl-python.md](impl-python.md).
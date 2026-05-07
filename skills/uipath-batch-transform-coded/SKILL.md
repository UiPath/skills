---
name: uipath-batch-transform-coded
description: "UiPath BatchTransform in coded agents — CSV input only. Adds LLM-filled columns to CSV rows at scale. CSV is the datasource (ephemeral or existing context-grounding index over the file); optional per-row web grounding. Result CSV is downloaded by the runtime to a local `destination_path` on resume. Coded agents yield `CreateBatchTransform` from `@durable_interrupt` (with `BatchTransformOutputColumn` list, `enable_web_search_grounding`, `destination_path`). For Studio Web Agent Builder→uipath-batch-transform-lowcode. For PDF/TXT (DeepRAG)→uipath-deeprag-coded. For C# or XAML→uipath-rpa."
when_to_use: "User wants a Python coded agent (`pyproject.toml`+`langgraph.json`, LangGraph) that processes tabular data (CSV) row-by-row with an LLM — bulk extraction, classification, address-match validation, vendor enrichment, MCC categorization, sales-order triage, address normalization. Triggers: 'add columns to a CSV with an LLM', 'classify each row', 'enrich vendor addresses', 'batch transform from python', 'use batchrag from coded agent'. NOT for one-document narrative synthesis (→uipath-deeprag-coded), Studio Web Agent Builder (→uipath-batch-transform-lowcode), or stable indexed knowledge bases (→uipath-agents)."
user-invocable: true
---

# UiPath BatchTransform — Coded Agent

BatchTransform applies one LLM prompt to every row of a CSV and produces an augmented CSV (original columns + new LLM-filled columns). CSV is the datasource — hosted in a context-grounding index purely so the runtime can iterate (ephemeral over an attachment, or existing). On resume, the runtime downloads the result to the local `destination_path` you specified on `CreateBatchTransform`. Optional per-row web grounding when a row alone is not enough.

Coded agent surface: Python with `uipath` + `uipath-langchain`. Yield `CreateBatchTransform` from `@durable_interrupt`.

> Product use cases: address-match validation (Medline), sales-order next-action recommendations (WireMasters), MCC categorization (Fiserv).

## When to Use

Read [references/context-grounding-patterns.md](references/context-grounding-patterns.md) first — picks by **file type**: CSV → BatchTransform; PDF/TXT → DeepRAG.

Use when:

- Input file is `.csv`
- Project has `pyproject.toml` with `uipath` / `uipath-langchain`, plus `langgraph.json` or a graph-style `main.py`
- Workload is throughput-driven (hundreds to thousands of rows)
- Custom upstream prep (download, reshape) or downstream routing (Data Service, queue, follow-up agent) needs Python control

For `.pdf` / `.txt` input → `uipath-deeprag-coded`. For Studio Web Agent Builder → `uipath-batch-transform-lowcode`.

## Critical Rules

1. **Use `@durable_interrupt` — never poll.** Jobs run minutes to an hour. Polling in a graph node burns the serverless 15-min job timeout. Yield `CreateBatchTransform` from a `@durable_interrupt` inner function; runtime starts the job, suspends, subscribes to the BatchRAG completion event, resumes on event.
2. **CSV is the datasource, not a grounding source.** BatchTransform iterates rows from a context-grounding index that exists only to host the file. Upload the CSV as an attachment and yield `CreateEphemeralIndex(usage=EphemeralIndexUsage.BATCH_RAG, attachments=[...])`, then `CreateBatchTransform(..., is_ephemeral_index=True, index_id=..., ...)`. OR target an existing index (`index_name=...`). Per-row grounding beyond the row's columns comes from `enable_web_search_grounding`, not the index.
3. **`output_columns` are required and validated.** Each `BatchTransformOutputColumn` has `name` (1–500 chars, regex `^[\w\s\.,!?-]+$`) and `description` (1–20000 chars). Description is the per-column LLM instruction — treat as prompt-fragment, not label.
4. **`prompt` is required.** Top-level prompt frames the task; per-column descriptions refine each column. Both sent to the LLM for every row.
5. **`destination_path` is required, is a LOCAL filesystem path.** The runtime downloads the augmented CSV there on resume (see `_handle_batch_rag_job_trigger` in `uipath/platform/resume_triggers/_protocol.py`). Use a unique name per run (e.g., UUID/timestamp suffix) to avoid overwriting prior local results.
6. **`enable_web_search_grounding` defaults `False`.** Enable only when the per-row task needs info NOT already in the row (address verification, current company status, open-web lookups). Leave off when the row contains everything the LLM needs.
7. **Permissions live on the folder.** `index_folder_key` / `index_folder_path` scopes index access + result write. Default to personal workspace key for self-serve. Missing → `400 "A folder is required for this action."`; lacking permission → `403 "User is missing required index permissions."`
8. **Never instantiate `UiPath()` at module scope.** Auth fires at import time, breaks `uip codedagent init`. Instantiate inside graph nodes.
9. **Local `uip codedagent run` exits at the first interrupt.** Expected — runtime captured suspend state. End-to-end resume happens only on a deployed agent or via `uip codedagent dev`.

## Quick Start

1. Confirm BatchTransform is the right mode → [references/context-grounding-patterns.md](references/context-grounding-patterns.md)
2. Plan the pipeline (input source, output schema, web grounding, destination) → [references/planning.md](references/planning.md)
3. Implement (graph with `CreateEphemeralIndex` + `CreateBatchTransform` durable interrupts) → [references/impl-python.md](references/impl-python.md)
4. Verify locally with `uip codedagent run agent '{...}'` (expect a clean suspend at first interrupt)
5. Deploy via solution upload or `uip codedagent deploy`

## Reference Navigation

| I need to... | Read |
|---|---|
| Pick the right context-grounding mode | [references/context-grounding-patterns.md](references/context-grounding-patterns.md) |
| Plan the coded-agent pipeline | [references/planning.md](references/planning.md) |
| Implement the graph (copy-paste) | [references/impl-python.md](references/impl-python.md) |
| Hit the API directly (debugging) | [references/api-reference.md](references/api-reference.md) |

## Anti-Patterns

- ❌ **Polling `retrieve_*_async` in a `while` loop.** Burns the 15-min serverless timeout. Use `@durable_interrupt`.
- ❌ **Calling `start_batch_transform_async` directly.** Forces hand-rolled folder headers, ingestion polling, resume logic. Yield `CreateBatchTransform` instead.
- ❌ **Using BatchTransform for one-document summarization.** That is DeepRAG. BatchTransform produces one row per input row.
- ❌ **Using BatchTransform for stable knowledge-base lookups.** Use `sdk.context_grounding.search_async` — see `uipath-agents`.
- ❌ **Enabling web search "just in case".** Enable only when the prompt depends on fresh external data.
- ❌ **Reusing `destination_path` across runs.** Overwrites prior output; concurrent reads see partial results.
- ❌ **Module-level `UiPath()`.** Breaks `uip codedagent init`.

## Resources

- UiPath Python SDK: <https://uipath.github.io/uipath-python/>
- Built-in tool reference (BT/DR/etc.): `uipath_langchain.agent.tools.context_tool` in the installed venv

---
name: uipath-deeprag-coded
description: "UiPath DeepRAG in coded agents — PDF / TXT input only. Research/summarize/synthesize across runtime documents using `@durable_interrupt` + `CreateEphemeralIndex` + `CreateDeepRag` (ephemeral index over attachments, no polling). For Studio Web Agent Builder→uipath-deeprag-lowcode. For CSV input (BatchTransform)→uipath-batch-transform-coded. For index search→uipath-agents. For C# or XAML→uipath-rpa."
when_to_use: "User wants a Python coded agent (`pyproject.toml`+`langgraph.json`, LangGraph, programmatic control) that summarizes / researches / synthesizes content from documents — PDFs, attachments, files in a storage bucket. Triggers: 'build a coded agent that summarizes', 'use deeprag from python', 'langgraph deeprag', 'durable interrupt deeprag'. NOT for Studio Web Agent Builder (→uipath-deeprag-lowcode), stable indexed knowledge bases (→uipath-agents), or per-row bulk extraction (→BatchTransform)."
user-invocable: true
---

# UiPath DeepRAG — Coded Agent

DeepRAG runs an iterative research-and-synthesis pass over an ephemeral context-grounding index built from attachments.

Coded agent surface: Python with `uipath` + `uipath-langchain`. Yield `Create*` resume-trigger models from `@durable_interrupt` so the runtime suspends and resumes on completion events.

## When to Use

Read [references/context-grounding-patterns.md](references/context-grounding-patterns.md) first — picks by **file type**: PDF/TXT → DeepRAG; CSV → BatchTransform.

Use when:

- Input file is `.pdf` or `.txt`
- Project has `pyproject.toml` with `uipath` / `uipath-langchain`, plus `langgraph.json` or a graph-style `main.py`
- Programmatic control over the pipeline (custom pre/post-processing, routing)
- Agent runs unattended (scheduled, queue-triggered, invoked from another agent)

For `.csv` input → `uipath-batch-transform-coded`. For Studio Web Agent Builder → `uipath-deeprag-lowcode`.

## Critical Rules

1. **Use `@durable_interrupt` — never poll.** DeepRAG and ephemeral-index ingestion are long-running. Polling in a graph node burns the serverless 15-min job timeout. Yield `CreateEphemeralIndex` / `CreateDeepRag` from a `@durable_interrupt` inner function; runtime creates the resource, suspends, subscribes to the completion event, resumes on event.
2. **DeepRAG operates on an index, not raw files.** Upload file as attachment first (`sdk.attachments.upload_async`), then yield `CreateEphemeralIndex(usage=EphemeralIndexUsage.DEEP_RAG, attachments=[...])`, then yield `CreateDeepRag(..., is_ephemeral_index=True, index_id=...)`.
3. **`is_ephemeral_index=True` is required** when `index_id` came from a `CreateEphemeralIndex` resume value. Runtime needs the flag to route the call as ephemeral; failure is server-side at execution. The Pydantic validator only catches the inverse mistake (`is_ephemeral_index=True` with `index_id=None`).
4. **`prompt` is required, non-empty.** Empty → `400 "The Prompt field is required."`
5. **`index_folder_key` (or `index_folder_path`) is required for permission checks.** Resolve at runtime: `(await sdk.folders.get_personal_workspace_async()).key`. Runtime injects the folder header.
6. **Permissions live on the folder.** Lacking the index permission → `403 "User is missing required index permissions."` Default to personal workspace key for self-serve.
7. **Never instantiate `UiPath()` at module scope.** Auth fires at import time, breaks `uip codedagent init`. Instantiate inside graph nodes.
8. **Local `uip codedagent run` exits at the first interrupt.** Expected — runtime captured suspend state. End-to-end resume happens only on a deployed agent or via `uip codedagent dev`.

## Quick Start

1. Confirm DeepRAG is the right mode → [references/context-grounding-patterns.md](references/context-grounding-patterns.md)
2. Plan the pipeline (inputs, folder, citation mode, bindings) → [references/planning.md](references/planning.md)
3. Implement (5-node graph with two `@durable_interrupt` nodes) → [references/impl-python.md](references/impl-python.md)
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

- ❌ **Polling `retrieve_deep_rag_async` in a `while` loop.** Burns the 15-min serverless timeout. Use `@durable_interrupt`.
- ❌ **Manually calling `start_deep_rag_ephemeral_async`.** Forces hand-rolling folder headers, ingestion polling, and resume logic. Yield `CreateDeepRag` instead.
- ❌ **Passing the local file path to DeepRAG.** DeepRAG reads the index, not the file. Upload as attachment first.
- ❌ **Forgetting `is_ephemeral_index=True`.** Validator rejects the model.
- ❌ **Running DeepRAG in shared folders without confirming the user's role.** Default to personal workspace.
- ❌ **Sending an empty `prompt`.** API rejects it.
- ❌ **Module-level `UiPath()` or `UiPathChat()`.** Breaks `uip codedagent init`.

## Resources

- UiPath Python SDK: <https://uipath.github.io/uipath-python/>
- Built-in tool reference (BT/DR/etc.): `uipath_langchain.agent.tools.context_tool` in the installed venv

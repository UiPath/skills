# Context Grounding Patterns — When to Use What

Shared decision logic for picking the right context-grounding mode. Pick the mode here, then jump to the surface skill for implementation.

## BatchTransform vs DeepRAG — Pick by File Type

| Input file | Mode |
|---|---|
| `.csv` | **BatchTransform** |
| `.pdf` / `.txt` | **DeepRAG** |

This is a hard rule: BatchTransform accepts CSV only; DeepRAG accepts PDF or TXT only. Pick by file type — there is no subjective tiebreaker.

## The Three Modes

| Mode | Input | What it does | Best for |
|---|---|---|---|
| **BatchTransform (BT)** | CSV | Iterate every row of the CSV (CSV is the datasource — hosted in a context-grounding index purely so the runtime can iterate), apply the same prompt to each row, optionally augment with a per-row web search, write augmented rows (original columns + new LLM-filled columns) to an Orchestrator bucket attachment. | Bulk extraction, per-row classification, address-match validation, vendor enrichment, sales-order triage. One row in, one row out. |
| **DeepRAG** | PDF / TXT | Iterative research-and-synthesis pass over an ephemeral index built from runtime attachments. Returns a single grounded narrative with optional citations. | Summarize / research / synthesize across one or more runtime documents. One question, one answer. |
| **Index search** (semantic / structured) | Pre-built index | Query a stable, pre-built context-grounding index. Returns ranked snippets. | Stable knowledge bases (policies, manuals, FAQs) — corpus does not change per run. |

## Decision Matrix

Route by file type first, signal second:

| File type | User signal | Mode | Where to go |
|---|---|---|---|
| `.csv` | "add columns" / "classify every row" / "enrich vendor addresses" / "MCC categorization" / "1000 rows of structured output" | **BatchTransform** | Out of scope here — see `uipath-batch-transform-lowcode` (or `uipath-batch-transform-coded`). |
| `.pdf` / `.txt` | "summarize" / "research across these docs" / "one narrative answer" | **DeepRAG** | **This skill** (low-code surface) — continue with [planning.md](planning.md). For Python coded agents, use `uipath-deeprag-coded`. |
| pre-built index, no file upload | "search the policy KB" / "look up X in our docs" | **Index search** | Use `sdk.context_grounding.search_async` or low-code Context tool — see `uipath-agents`. |

## Surface Selection

Once the mode is picked, route by execution surface:

| Surface signal | BatchTransform skill | DeepRAG skill |
|---|---|---|
| Project has `pyproject.toml` + `langgraph.json`, or user wants Python | `uipath-batch-transform-coded` | `uipath-deeprag-coded` |
| Project has `agent.json` with `"type": "lowCode"`, or user is building in Studio Web Agent Builder | `uipath-batch-transform-lowcode` | **`uipath-deeprag-lowcode`** (this skill) |

Both surfaces hit the same backend per mode. The difference is **how** the agent invokes the mode, not what the mode does.

## Cross-Surface Invariants

These hold regardless of mode or surface:

1. **The hosted file is a datasource for iteration (BT) or grounding (DR), not the other way around.** BatchTransform iterates rows from a CSV-backed context-grounding index; DeepRAG synthesizes across a PDF/TXT-backed index. Per-row external grounding for BT comes from `enable_web_search_grounding`, not the index.
2. **`prompt` is required.** Empty → `400 "The Prompt field is required."` BatchTransform additionally requires `output_columns` (each with `name` + `description`).
3. **Output destination differs by mode.** BatchTransform writes a bucket attachment (`destination_path` coded / target file name low-code). DeepRAG returns content (`text` + optional `citations`) inline on the resume value.
4. **Folder context is required.** Explicit folder key/path or env var. Missing → `400 "A folder is required for this action."`
5. **Permissions live on the folder.** User's role must grant the index permission. `403 "User is missing required index permissions."` → switch folders (personal workspace is the safe default for self-serve).
6. **Async / event-driven.** Both modes are long-running. Coded agents must use `@durable_interrupt` with the matching `Create*` resume-trigger model; low-code agents get this for free via the runtime.

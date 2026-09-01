# Context Grounding Patterns — When to Use What

Shared decision logic for selecting the context-grounding mode and execution surface.

## Choose the Mode by File Type

| Input | Mode | Use |
|---|---|---|
| `.csv` | **BatchTransform (BT)** | Iterate every row with the same prompt, optionally add per-row web search, and write original plus LLM-filled columns to an Orchestrator bucket attachment. Use for bulk extraction, classification, address-match validation, vendor enrichment, and sales-order triage. One row in, one row out. |
| `.pdf` / `.txt` | **DeepRAG (DR)** | Research and synthesize an ephemeral index built from runtime attachments into one grounded narrative with citations and optional bounding-box anchors. Use for summaries or research across documents, especially large files or citation-heavy answers. Prefer over `analyze-attachments` because of its lower page limits and one-shot synthesis. |
| Pre-built index, no file upload | **Index search** | Query a stable context-grounding index for policies, manuals, FAQs, and other knowledge bases whose corpus does not change per run. |

Hard rule: BatchTransform accepts CSV only; DeepRAG accepts PDF or TXT only. No subjective tiebreaker.

For BatchTransform, host the CSV as the datasource in a context-grounding index so the runtime can iterate it; per-row external grounding comes from `enable_web_search_grounding`, not the index.

## Decision Matrix

Route by file type first, then user signal:

| File type | User signal | Mode | Planning reference |
|---|---|---|---|
| `.csv` | "add columns" / "classify every row" / "enrich vendor addresses" / "MCC categorization" / "1000 rows of structured output" | **BatchTransform** | Coded: [coded/capabilities/batch-transform/planning.md](coded/capabilities/batch-transform/planning.md). Low-code: [lowcode/capabilities/built-in-tools/batch-transform/planning.md](lowcode/capabilities/built-in-tools/batch-transform/planning.md). |
| `.pdf` / `.txt` | "summarize" / "research across these docs" / "one narrative answer" | **DeepRAG** | Coded: [coded/capabilities/deeprag/planning.md](coded/capabilities/deeprag/planning.md). Low-code: [lowcode/capabilities/built-in-tools/deeprag/planning.md](lowcode/capabilities/built-in-tools/deeprag/planning.md). |
| Pre-built index, no file upload | "search the policy KB" / "look up X in our docs" | **Index search** | Consume: `sdk.context_grounding.unified_search_async` or the low-code Context tool — see [coded/capabilities/context-grounding.md](coded/capabilities/context-grounding.md). Create, ingest, or inspect the index from the CLI: [uipath-platform/references/context-grounding/index-management.md](../../uipath-platform/references/context-grounding/index-management.md). |

## Select the Execution Surface

After choosing the mode, route by project or user signal:

| Signal | BatchTransform | DeepRAG |
|---|---|---|
| Project has `pyproject.toml` + `langgraph.json`, or user wants Python | [coded/capabilities/batch-transform/planning.md](coded/capabilities/batch-transform/planning.md) | [coded/capabilities/deeprag/planning.md](coded/capabilities/deeprag/planning.md) |
| Project has `agent.json` with `"type": "lowCode"`, or user is building in Studio Web Agent Builder | [lowcode/capabilities/built-in-tools/batch-transform/planning.md](lowcode/capabilities/built-in-tools/batch-transform/planning.md) | [lowcode/capabilities/built-in-tools/deeprag/planning.md](lowcode/capabilities/built-in-tools/deeprag/planning.md) |

Both surfaces use the same backend per mode; only invocation differs.

## Cross-Surface Invariants

1. **Use the hosted file as a datasource for iteration (BT) or grounding (DR), not the other way around.** BatchTransform iterates rows from a CSV-backed context-grounding index; DeepRAG synthesizes across a PDF/TXT-backed index. Per-row external grounding for BT comes from `enable_web_search_grounding`, not the index.
2. **Require `prompt`.** Empty → `400 "The Prompt field is required."` BatchTransform additionally requires `output_columns`, each with `name` + `description`.
3. **Respect the output destination.** BatchTransform produces an augmented CSV server-side. Coded agents download it to the supplied local `destination_path`; low-code agents receive it as an Orchestrator bucket attachment for downstream consumers. DeepRAG returns inline content (`text` plus optional `citations`) in the resume value.
4. **Provide folder context.** Use an explicit folder key/path or environment variable. Missing → `400 "A folder is required for this action."`
5. **Use folder permissions.** Coded agents require the invoking user's role to grant the index permission. Low-code agents require the published agent's runtime identity to have it in the agent's folder. `403 "User is missing required index permissions."` → switch folders; a personal workspace is the safe default for self-serve.
6. **Handle both modes asynchronously/event-driven.** Coded agents use plain `interrupt()` with the matching `Create*` / `Wait*` resume-trigger models from `uipath.platform.common`; low-code agents receive this behavior from the runtime.

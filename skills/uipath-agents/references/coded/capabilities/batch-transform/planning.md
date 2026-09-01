# BatchTransform in a Coded Agent — Planning

## When to Use

Use this when the project has `pyproject.toml` with `uipath` / `uipath-langchain`, plus `langgraph.json` or a graph-style `main.py`; the source is tabular CSV with one output row per input row plus LLM-filled columns; the workload is throughput-driven (hundreds to thousands of rows); and the user needs Python control over upstream preparation or downstream routing.

Confirm BatchTransform first: [../../../context-grounding-patterns.md](../../../context-grounding-patterns.md).

For Studio Web Agent Builder, see [../../../lowcode/capabilities/built-in-tools/batch-transform/planning.md](../../../lowcode/capabilities/built-in-tools/batch-transform/planning.md).

## Inputs Required Before Building

| Input | Purpose / source |
|---|---|
| Source CSV | File BatchTransform iterates over; from a bucket, agent input, or upstream node |
| Prompt | Top-level framing sent with every row; user input or static default |
| `output_columns` | New LLM-filled columns; each `description` is its per-row instruction |
| `enable_web_search_grounding` | Per-row web-search augmentation; default `False`, enabled only for fresh external data |
| Index strategy | Ephemeral attachment-backed one-shot index or existing stable corpus index |
| `destination_path` | Local path for the augmented CSV after resume; use a unique UUID/timestamp suffix per run |
| Target folder | Permission scope for ingestion and BatchTransform; default to the personal workspace key for self-serve |

## Pipeline Shape

For an ephemeral attachment-backed run:

1. `fetch_source` — accept or download the CSV locally.
2. `upload_attachment` — call `sdk.attachments.upload_async` for an attachment UUID.
3. `create_index` — call `create_ephemeral_index_async`, check `in_progress_ingestion()`, and conditionally `interrupt(WaitEphemeralIndex(...))` to obtain a `ContextGroundingIndex`.
4. `run_batch_transform` — call `interrupt(CreateBatchTransform(is_ephemeral_index=True, index_id=..., output_columns=[...], destination_path=<local-path>, enable_web_search_grounding=..., ...))`; after resume, the runtime writes the augmented CSV to `destination_path`.
5. `finalize` — return the local `destination_path` or read the CSV for downstream nodes.

For an existing index, skip steps 2–3 and pass `index_name=...` and `index_folder_path=...` (without `is_ephemeral_index`) in step 4.

## `BatchTransformOutputColumn` Authoring

Each `output_columns` entry has `name` and `description`; treat `description` as the per-row prompt fragment.

- `name`: 1–500 chars; regex `^[\w\s\.,!?-]+$`; use a friendly header with no other special characters.
- `description`: 1–20000 chars; specify extraction/classification, format (free text, enum, or JSON), uncertain-case output, and useful examples.

`BatchTransformOutputColumn` is in `context_grounding`, not `common`:

```python
from uipath.platform.context_grounding import BatchTransformOutputColumn

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

- **Sync vs interrupt:** Always use `interrupt()` for `create_index` (conditionally) and `run_batch_transform`; never poll because runs are long-lived.
- **Index folder:** Use the personal workspace key by default for self-serve. Override only after the user confirms role permissions in another folder.
- **Ephemeral vs existing index:** Use ephemeral for one-shot runtime CSV runs; use an existing index when the same data is reused across runs.
- **Web search grounding:** Default `False`; enable only when prompts require fresh external information, such as address verification or current company status.
- **Destination collisions:** Add a UUID or timestamp suffix, such as `results/run-{ts}.csv`, so concurrent or repeated runs do not overwrite files.
- **Result handling:** After resume, the augmented CSV is at the local `destination_path`. Return the path, re-upload it to a bucket for RPA, or read it inline as appropriate.

## Bindings

A source bucket is bindable if the CSV is downloaded from one. Attachments, ephemeral indexes, and the local `destination_path` are not bindable because they are runtime-created or local-only. A destination bucket is bindable if the agent re-uploads the augmented CSV there.

## Local-Run Behavior

`uip codedagent run agent '{...}'` exits at the first interrupt; this is expected because the runtime captured suspend state for platform resumption. For end-to-end verification, deploy and invoke from the platform, or use `uip codedagent dev`.

## Hand-off

After planning, implement according to [impl-python.md](impl-python.md).

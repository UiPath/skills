# BatchTransform in a Coded Agent — Implementation

LangGraph + `@durable_interrupt` pattern. **No polling** — runtime suspends on `Create*` resume-trigger models and resumes on the BatchRAG completion event.

> **Authoritative source.** Module shapes change with the SDK. Always trust `from uipath.platform.common import CreateBatchTransform, CreateEphemeralIndex` and `from uipath.platform.context_grounding import BatchTransformOutputColumn, EphemeralIndexUsage` over any snippet here. SDK docs: <https://uipath.github.io/uipath-python/>. Built-in tool reference implementation: `uipath_langchain.agent.tools.context_tool` in the installed venv.

## Dependencies

```toml
[project]
dependencies = ["uipath", "uipath-langchain"]
```

## Resume-Trigger Models

```python
from uipath.platform.common import CreateBatchTransform, CreateEphemeralIndex
from uipath.platform.context_grounding import BatchTransformOutputColumn, EphemeralIndexUsage
from uipath_langchain._utils.durable_interrupt import durable_interrupt

# Step A: ephemeral index (CSV becomes a runtime-iterable datasource)
@durable_interrupt
async def _create_index():
    return CreateEphemeralIndex(
        usage=EphemeralIndexUsage.BATCH_RAG,
        attachments=[attachment_id],
    )
index = await _create_index()  # → ContextGroundingIndex (already ingested)

# Step B: BatchTransform task (suspends, resumes on BatchRAG completion event)
@durable_interrupt
async def _run_batch_transform():
    return CreateBatchTransform(
        name=task_name,
        index_id=index.id,
        is_ephemeral_index=True,
        prompt=prompt,
        output_columns=output_columns,
        destination_path="results/run-<uuid>.csv",
        enable_web_search_grounding=False,
        index_folder_key=ws_key,
    )
await _run_batch_transform()
```

Existing-index variant: drop step A's ephemeral path; pass `index_name=...` (without `is_ephemeral_index`) on `CreateBatchTransform`.

`destination_path` is a LOCAL filesystem path. On resume, the runtime calls `download_batch_transform_result_async(...)` to write the augmented CSV there and returns a confirmation string. Read the CSV from disk if downstream nodes need the rows inline.

## Procedure

1. **fetch_source** — accept / download the source CSV → local path
2. **upload_attachment** — `await sdk.attachments.upload_async(name=..., source_path=local, folder_key=ws_key)` → attachment uuid
3. **create_index** — `@durable_interrupt` returning `CreateEphemeralIndex(usage=EphemeralIndexUsage.BATCH_RAG, attachments=[attachment_id])` → `ContextGroundingIndex` (resumed; already ingested)
4. **run_batch_transform** — `@durable_interrupt` returning `CreateBatchTransform(... is_ephemeral_index=True, index_id=index.id, output_columns=..., destination_path=<local-path>, index_folder_key=ws_key, ...)` → confirmation string; runtime has downloaded the augmented CSV to `destination_path`
5. **finalize** — return the local `destination_path` (or read the CSV from disk for downstream nodes)

Instantiate `UiPath()` inside nodes only — never at module level.

## `BatchTransformOutputColumn` Validation

| Field | Constraint | Notes |
|---|---|---|
| `name` | 1–500 chars, regex `^[\w\s\.,!?-]+$` | Friendly column header. No `/`, `:`, `&`, `(`, `)`. |
| `description` | 1–20000 chars | Per-column LLM instruction. Specify format, enums, "when uncertain" handling. |

## Resume Values

| Yielded model | Resume value | Useful fields |
|---|---|---|
| `CreateEphemeralIndex` | `ContextGroundingIndex` | `id` (already ingested) |
| `CreateBatchTransform` | `str` confirmation message | Format: `"Batch transform completed. Modified file available at <abs_path>"`. Augmented CSV written to the local `destination_path` you supplied — read it from disk if needed. Runtime raises `UiPathFaultedTriggerError` (wrapping `BatchTransformFailedException`) on terminal failure. |
| `CreateEphemeralIndexRaw` | raw dict | full payload, no ingestion-status validation |

Runtime raises `UiPathFaultedTriggerError` (imported as `from uipath.core.errors import UiPathFaultedTriggerError`) on terminal `Failed`. There is no `CreateBatchTransformRaw` — to inspect a failed ingestion without raising, yield `CreateEphemeralIndexRaw` instead.

## Bindings

Bind the **source bucket** (where the input CSV lives) in `bindings.json`. The augmented CSV is written to a local `destination_path` on resume — that is NOT bindable. Attachments and ephemeral indexes are NOT bindable either. Add a destination bucket binding only if the agent re-uploads the augmented CSV after resume.

```json
{
  "resource": "bucket",
  "key": "<SOURCE_BUCKET>.<SOURCE_FOLDER>",
  "value": {
    "name": {"defaultValue": "<SOURCE_BUCKET>", "isExpression": false, "displayName": "Name"},
    "folderPath": {"defaultValue": "<SOURCE_FOLDER>", "isExpression": false, "displayName": "Folder Path"}
  },
  "metadata": {"ActivityName": "download_async", "BindingsVersion": "2.2", "DisplayLabel": "FullName"}
}
```

## Local-Run Verification

```bash
uip codedagent run agent '{"instructions":"<PROMPT>","enable_web_search":false}' --output-file out.json
```

Runtime executes pre-interrupt nodes synchronously, then suspends at `create_index` with the `CreateEphemeralIndex` model captured as the suspend value. That output is correct — not a failure. End-to-end completion happens only on a deployed agent or via `uip codedagent dev`.

## Resources

- UiPath Python SDK: <https://uipath.github.io/uipath-python/>
- Built-in tool reference (BT/DR/etc.): `uipath_langchain.agent.tools.context_tool` in the installed venv
- API endpoints (debug): [api-reference.md](api-reference.md)

# BatchTransform in a Coded Agent — Implementation

LangGraph + `interrupt()` pattern. **No polling** — runtime suspends on `Create*` resume-trigger models and resumes on the BatchRAG completion event.


## Dependencies

```toml
[project]
dependencies = ["uipath", "uipath-langchain"]
```

## Flavour A — Ephemeral index (attachment-backed, one-shot)

### Node: create_index

```python
from uipath.platform import UiPath
from uipath.platform.common import UiPathConfig, WaitEphemeralIndex
from uipath.platform.context_grounding import EphemeralIndexUsage
from langgraph.types import interrupt

sdk = UiPath()
if not (folder_key := UiPathConfig.folder_key):
    folder_key = (await sdk.folders.get_personal_workspace_async()).key

ephemeral_index = await sdk.context_grounding.create_ephemeral_index_async(
    usage=EphemeralIndexUsage.BATCH_RAG,
    attachments=[attachment_id],
    folder_key=folder_key,
)
if ephemeral_index.in_progress_ingestion():
    ephemeral_index = interrupt(WaitEphemeralIndex(index=ephemeral_index))  # → ContextGroundingIndex (ingested)
```

### Node: run_batch_transform

```python
from uipath.platform.common import CreateBatchTransform
from langgraph.types import interrupt

result = interrupt(CreateBatchTransform(
    name=task_name,
    index_id=ephemeral_index_id,        # from state, set by create_index node
    is_ephemeral_index=True,
    prompt=prompt,
    output_columns=output_columns,
    destination_path="results/run-<uuid>.csv",
    enable_web_search_grounding=False,
    index_folder_key=index_folder_key,  # from state, set by create_index node
))
```

## Flavour B — Existing named index

Skip the `fetch_source`, `upload_attachment`, and `create_index` nodes entirely.

### Node: run_batch_transform

```python
from uipath.platform.common import CreateBatchTransform
from langgraph.types import interrupt

result = interrupt(CreateBatchTransform(
    name=task_name,
    index_name="<INDEX_NAME>",
    index_folder_path="<INDEX_FOLDER_PATH>",
    prompt=prompt,
    output_columns=output_columns,
    destination_path="results/run-<uuid>.csv",
    enable_web_search_grounding=False,
))
```

`destination_path` is a LOCAL filesystem path. On resume, the runtime calls `download_batch_transform_result_async(...)` to write the augmented CSV there and returns a confirmation string. Read the CSV from disk if downstream nodes need the rows inline.

## Procedure (Flavour A)

1. **fetch_source** — accept / download the source CSV → local path
2. **upload_attachment** — `await sdk.attachments.upload_async(name=..., source_path=local, folder_key=folder_key)` → attachment uuid
3. **create_index** — `create_ephemeral_index_async` → check `in_progress_ingestion()` → conditionally `interrupt(WaitEphemeralIndex(...))` → `ContextGroundingIndex`
4. **run_batch_transform** — `interrupt(CreateBatchTransform(... is_ephemeral_index=True, index_id=..., output_columns=..., destination_path=<local-path>, index_folder_key=...))` → confirmation string; augmented CSV written to `destination_path`
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
| `WaitEphemeralIndex` | `ContextGroundingIndex` | `id`, `folder_key` (ingested) |
| `CreateBatchTransform` | `str` confirmation message | Format: `"Batch transform completed. Modified file available at <abs_path>"`. Augmented CSV written to the local `destination_path` you supplied — read it from disk if needed. Runtime raises `UiPathFaultedTriggerError` (wrapping `BatchTransformFailedException`) on terminal failure. |

Runtime raises `UiPathFaultedTriggerError` (imported as `from uipath.core.errors import UiPathFaultedTriggerError`) on terminal `Failed`.

## Local-Run Verification

```bash
uip codedagent run agent '{"instructions":"<PROMPT>","enable_web_search":false}' --output-file out.json
```

Runtime executes pre-interrupt nodes synchronously, then suspends at `create_index` with the `WaitEphemeralIndex` model captured as the suspend value (Flavour A) or at `run_batch_transform` with `CreateBatchTransform` (Flavour B). That output is correct — not a failure. End-to-end completion happens only on a deployed agent or via `uip codedagent dev`.

## Resources

- UiPath Python SDK: <https://uipath.github.io/uipath-python/>
- Built-in tool reference (BT/DR/etc.): `uipath_langchain.agent.tools.context_tool` in the installed venv
- API endpoints (debug): [api-reference.md](api-reference.md)

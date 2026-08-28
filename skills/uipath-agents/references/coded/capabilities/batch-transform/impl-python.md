# BatchTransform in a Coded Agent — Implementation

LangGraph + `interrupt()` pattern. **Do not poll**: suspend on `Create*` resume-trigger models and resume on the BatchRAG completion event.

## Dependencies

```toml
[project]
dependencies = ["uipath", "uipath-langchain"]
```

## Flavour A — Ephemeral index

Use this attachment-backed, one-shot flow.

### `create_index` node

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
    ephemeral_index = interrupt(WaitEphemeralIndex(index=ephemeral_index))
```

The resumed value is an ingested `ContextGroundingIndex`.

### `run_batch_transform` node

```python
from uipath.platform.common import CreateBatchTransform
from langgraph.types import interrupt

result = interrupt(CreateBatchTransform(
    name=task_name,
    index_id=ephemeral_index_id,        # state from create_index
    is_ephemeral_index=True,
    prompt=prompt,
    output_columns=output_columns,
    destination_path=local_destination_path,
    enable_web_search_grounding=False,
    index_folder_key=index_folder_key,  # state from create_index
))
```

## Flavour B — Existing named index

Skip `fetch_source`, `upload_attachment`, and `create_index`.

```python
from uipath.platform.common import CreateBatchTransform
from langgraph.types import interrupt

result = interrupt(CreateBatchTransform(
    name=task_name,
    index_name=index_name,
    index_folder_path=index_folder_path,
    prompt=prompt,
    output_columns=output_columns,
    destination_path=local_destination_path,
    enable_web_search_grounding=False,
))
```

`destination_path` is a LOCAL filesystem path. On resume, the runtime calls `download_batch_transform_result_async(...)`, writes the augmented CSV there, and returns a confirmation string. Read the CSV from disk when downstream nodes need inline rows.

## Procedure for Flavour A

1. **fetch_source** — accept or download the source CSV to a local path.
2. **upload_attachment** — run `await sdk.attachments.upload_async(name=..., source_path=local, folder_key=folder_key)` to obtain the attachment UUID.
3. **create_index** — run `create_ephemeral_index_async`; check `in_progress_ingestion()`; conditionally run `interrupt(WaitEphemeralIndex(...))`; obtain the ingested `ContextGroundingIndex`.
4. **run_batch_transform** — run `interrupt(CreateBatchTransform(... is_ephemeral_index=True, index_id=..., output_columns=..., destination_path=<local-path>, index_folder_key=...))`; the runtime writes the augmented CSV to `destination_path` and returns a confirmation string.
5. **finalize** — return the local `destination_path`, or read the CSV from disk for downstream nodes.

Instantiate `UiPath()` inside nodes only; never at module level.

## `BatchTransformOutputColumn` validation

| Field | Constraint | Notes |
|---|---|---|
| `name` | 1–500 chars, regex `^[\w\s\.,!?-]+$` | Friendly column header. No `/`, `:`, `&`, `(`, `)`. |
| `description` | 1–20000 chars | Per-column LLM instruction. Specify format, enums, and "when uncertain" handling. |

## Resume values and failures

| Yielded model | Resume value | Useful fields |
|---|---|---|
| `WaitEphemeralIndex` | `ContextGroundingIndex` | `id`, `folder_key` (ingested) |
| `CreateBatchTransform` | `str` confirmation message | Format: `"Batch transform completed. Modified file available at <abs_path>"`. The augmented CSV is written to the supplied local `destination_path`; read it from disk if needed. |

On terminal `Failed`, runtime raises `UiPathFaultedTriggerError` wrapping `BatchTransformFailedException`. Import it with `from uipath.core.errors import UiPathFaultedTriggerError`.

## Local-run verification

```bash
uip codedagent run agent '{"instructions":"<PROMPT>","enable_web_search":false}' --output-file out.json
```

The runtime executes pre-interrupt nodes synchronously, then suspends at `create_index` with `WaitEphemeralIndex` captured as the suspend value (Flavour A), or at `run_batch_transform` with `CreateBatchTransform` (Flavour B). This is correct, not a failure. End-to-end completion occurs only on a deployed agent or via `uip codedagent dev`.

## Resources

- UiPath Python SDK: <https://uipath.github.io/uipath-python/>
- Built-in tool reference (BT/DR/etc.): `uipath_langchain.agent.tools.context_tool` in the installed venv
- API endpoints (debug): [api-reference.md](api-reference.md)
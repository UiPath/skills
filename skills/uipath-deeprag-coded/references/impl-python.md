# DeepRAG in a Coded Agent — Implementation

LangGraph + `@durable_interrupt` pattern. **No polling** — runtime suspends on `Create*` resume-trigger models and resumes on the DeepRAG completion event.

> **Authoritative source.** Module shapes change with the SDK. Always trust `from uipath.platform.common import CreateDeepRag, CreateEphemeralIndex` and `from uipath.platform.context_grounding import EphemeralIndexUsage` over any snippet here. SDK docs: <https://uipath.github.io/uipath-python/>. Built-in tool reference implementation: `uipath_langchain.agent.tools.context_tool` in the installed venv.

## Dependencies

```toml
[project]
dependencies = ["uipath", "uipath-langchain"]
```

## Resume-Trigger Models

```python
from uipath.platform.common import CreateDeepRag, CreateEphemeralIndex
from uipath.platform.context_grounding import EphemeralIndexUsage
from uipath_langchain._utils.durable_interrupt import durable_interrupt

# Step A: ephemeral index over the PDF/TXT attachment
@durable_interrupt
async def _create_index():
    return CreateEphemeralIndex(
        usage=EphemeralIndexUsage.DEEP_RAG,
        attachments=[attachment_id],
    )
index = await _create_index()  # → ContextGroundingIndex (already ingested)

# Step B: DeepRAG task (suspends, resumes on DeepRAG completion event)
@durable_interrupt
async def _run_deep_rag():
    return CreateDeepRag(
        name=task_name,
        index_id=index.id,
        is_ephemeral_index=True,
        prompt=prompt,
        index_folder_key=ws_key,
    )
content = await _run_deep_rag()  # → DeepRagContent (or dict) — has .text, .citations
```

`is_ephemeral_index=True` is required when `index_id` came from `CreateEphemeralIndex`. Pydantic validator rejects the model otherwise.

## Procedure

1. **fetch_file** — accept / download the PDF/TXT → local path
2. **upload_attachment** — `await sdk.attachments.upload_async(name=..., source_path=local, folder_key=ws_key)` → attachment uuid
3. **create_index** — `@durable_interrupt` returning `CreateEphemeralIndex(usage=EphemeralIndexUsage.DEEP_RAG, attachments=[attachment_id])` → `ContextGroundingIndex` (resumed; already ingested)
4. **run_deep_rag** — `@durable_interrupt` returning `CreateDeepRag(... is_ephemeral_index=True, index_id=index.id, prompt=..., index_folder_key=ws_key)` → `DeepRagContent` (`text`, `citations`)
5. **finalize** — shape the agent's `GraphOutput`

Instantiate `UiPath()` inside nodes only — never at module level. Resolve workspace key inside the relevant node: `ws = await sdk.folders.get_personal_workspace_async()`; `ws_key = ws.key`.

## Resume Values

| Yielded model | Resume value | Useful fields |
|---|---|---|
| `CreateEphemeralIndex` | `ContextGroundingIndex` | `id` (already ingested) |
| `CreateDeepRag` | `DeepRagContent` (validated) or `dict` | `text`, `citations` |
| `CreateDeepRagRaw` | `DeepRagResponse` raw | full response, no status validation |
| `CreateEphemeralIndexRaw` | raw dict | full payload, no ingestion-status validation |

Runtime raises `UiPathFaultedTriggerError` on terminal `Failed`. Use `*Raw` variants only to inspect a failed status without raising.

## Defensive Resume-Value Access

Resume value may be the typed model or a dict depending on SDK version. Read both shapes:

```python
text = content.get("text", "") if isinstance(content, dict) else getattr(content, "text", "")
raw_citations = content.get("citations") if isinstance(content, dict) else getattr(content, "citations", [])
citations = [c if isinstance(c, dict) else c.model_dump() for c in (raw_citations or [])]
```

## Citation Modes

Pass `citation_mode=CitationMode.SKIP | INLINE` on `CreateDeepRag`. Default `SKIP` (lowest latency, no citations). `INLINE` interleaves citations in `content.text`. Verify the available enum values at your SDK version: `from uipath.platform.context_grounding import CitationMode; list(CitationMode)`.

## Bindings

Source bucket (if files come from a bucket) goes in `bindings.json`. Attachments and ephemeral indexes are NOT bindable.

```json
{
  "resource": "bucket",
  "key": "<BUCKET_NAME>.<BUCKET_FOLDER_PATH>",
  "value": {
    "name": {"defaultValue": "<BUCKET_NAME>", "isExpression": false, "displayName": "Name"},
    "folderPath": {"defaultValue": "<BUCKET_FOLDER_PATH>", "isExpression": false, "displayName": "Folder Path"}
  },
  "metadata": {"ActivityName": "download_async", "BindingsVersion": "2.2", "DisplayLabel": "FullName"}
}
```

## Local-Run Verification

```bash
uip codedagent run agent '{"instructions":"<PROMPT>"}' --output-file out.json
```

Runtime executes pre-interrupt nodes synchronously, then suspends at `create_index` with the `CreateEphemeralIndex` model captured as the suspend value. That output is correct — not a failure. End-to-end completion happens only on a deployed agent or via `uip codedagent dev`.

## Resources

- UiPath Python SDK: <https://uipath.github.io/uipath-python/>
- Built-in tool reference (BT/DR/etc.): `uipath_langchain.agent.tools.context_tool` in the installed venv
- API endpoints (debug): [api-reference.md](api-reference.md)

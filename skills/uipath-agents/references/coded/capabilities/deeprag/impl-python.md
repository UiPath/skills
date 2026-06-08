# DeepRAG in a Coded Agent — Implementation

LangGraph + `interrupt()` pattern. **No polling** — runtime suspends on `Create*` resume-trigger models and resumes on the DeepRAG completion event.


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
    usage=EphemeralIndexUsage.DEEP_RAG,
    attachments=[attachment_id],
    folder_key=folder_key,
)
if ephemeral_index.in_progress_ingestion():
    ephemeral_index = interrupt(WaitEphemeralIndex(index=ephemeral_index))  # → ContextGroundingIndex (ingested)
```

### Node: run_deep_rag

```python
from uipath.platform.common import CreateDeepRag
from langgraph.types import interrupt

content = interrupt(CreateDeepRag(
    name=task_name,
    index_id=ephemeral_index_id,        # from state, set by create_index node
    is_ephemeral_index=True,
    prompt=prompt,
    index_folder_key=index_folder_key,  # from state, set by create_index node
))  # → DeepRagContent — has .text, .citations
```

`is_ephemeral_index=True` is required when `index_id` came from an ephemeral index — missing it surfaces server-side at execution.

## Flavour B — Existing named index

Skip the `fetch_file`, `upload_attachment`, and `create_index` nodes entirely.

### Node: run_deep_rag

```python
from uipath.platform.common import CreateDeepRag
from langgraph.types import interrupt

content = interrupt(CreateDeepRag(
    name=task_name,
    index_name="<INDEX_NAME>",
    index_folder_path="<INDEX_FOLDER_PATH>",
    prompt=prompt,
))  # → DeepRagContent — has .text, .citations
```

## Procedure (Flavour A)

1. **fetch_file** — accept / download the PDF/TXT → local path
2. **upload_attachment** — `await sdk.attachments.upload_async(name=..., source_path=local, folder_key=folder_key)` → attachment uuid
3. **create_index** — `create_ephemeral_index_async` → check `in_progress_ingestion()` → conditionally `interrupt(WaitEphemeralIndex(...))` → `ContextGroundingIndex`
4. **run_deep_rag** — `interrupt(CreateDeepRag(... is_ephemeral_index=True, index_id=..., prompt=..., index_folder_key=...))` → `DeepRagContent` (`text`, `citations`)
5. **finalize** — shape the agent's `GraphOutput`

Instantiate `UiPath()` inside nodes only — never at module level.

## Resume Values

| Yielded model | Resume value | Useful fields |
|---|---|---|
| `WaitEphemeralIndex` | `ContextGroundingIndex` | `id`, `folder_key` (ingested) |
| `CreateDeepRag` | `DeepRagContent` (validated) or `dict` | `text`, `citations` |
| `CreateDeepRagRaw` | `DeepRagResponse` raw | full response, no status validation |

Runtime raises `UiPathFaultedTriggerError` (imported as `from uipath.core.errors import UiPathFaultedTriggerError`) on terminal `Failed`. Use `*Raw` variants only to inspect a failed status without raising.

## Defensive Resume-Value Access

Resume value may be the typed model or a dict depending on SDK version. Read both shapes:

```python
text = content.get("text", "") if isinstance(content, dict) else getattr(content, "text", "")
raw_citations = content.get("citations") if isinstance(content, dict) else getattr(content, "citations", [])
citations = [c if isinstance(c, dict) else c.model_dump() for c in (raw_citations or [])]
```

## Citation Modes

Pass `citation_mode=CitationMode.SKIP | INLINE` on `CreateDeepRag`. Default `SKIP` (lowest latency, no citations). `INLINE` interleaves citations in `content.text`. Verify the available enum values at your SDK version: `from uipath.platform.context_grounding import CitationMode; list(CitationMode)`.

## Local-Run Verification

```bash
uip codedagent run agent '{"instructions":"<PROMPT>"}' --output-file out.json
```

Runtime executes pre-interrupt nodes synchronously, then suspends at `create_index` with the `WaitEphemeralIndex` model captured as the suspend value (Flavour A) or at `run_deep_rag` with `CreateDeepRag` (Flavour B). That output is correct — not a failure. End-to-end completion happens only on a deployed agent or via `uip codedagent dev`.

## Resources

- UiPath Python SDK: <https://uipath.github.io/uipath-python/>
- Built-in tool reference (BT/DR/etc.): `uipath_langchain.agent.tools.context_tool` in the installed venv
- API endpoints (debug): [api-reference.md](api-reference.md)

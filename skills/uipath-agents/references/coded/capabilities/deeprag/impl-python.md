# DeepRAG in a Coded Agent — Implementation

LangGraph + `interrupt()` pattern. **Do not poll.** Runtime suspends on `Create*` resume-trigger models and resumes on the DeepRAG completion event.

## Dependencies

```toml
[project]
dependencies = ["uipath", "uipath-langchain"]
```

## Flavour A — Ephemeral index

Use for attachment-backed, one-shot indexing.

1. **fetch_file** — accept or download the PDF/TXT to a local path.
2. **upload_attachment** — run `await sdk.attachments.upload_async(name=..., source_path=local, folder_key=folder_key)` and obtain the attachment UUID.
3. **create_index** — run `create_ephemeral_index_async`, check `in_progress_ingestion()`, and conditionally interrupt with `WaitEphemeralIndex` to obtain an ingested `ContextGroundingIndex`.
4. **run_deep_rag** — interrupt `CreateDeepRag` with `is_ephemeral_index=True` to obtain `DeepRagContent`.
5. **finalize** — shape the agent's `GraphOutput`.

Instantiate `UiPath()` inside nodes only; never instantiate it at module level.

```python
from uipath.platform import UiPath
from uipath.platform.common import UiPathConfig, WaitEphemeralIndex, CreateDeepRag
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

content = interrupt(CreateDeepRag(
    name=task_name,
    index_id=ephemeral_index_id,        # from state, set by create_index node
    is_ephemeral_index=True,
    prompt=prompt,
    index_folder_key=index_folder_key,  # from state, set by create_index node
))  # → DeepRagContent — has .text, .citations
```

Set `is_ephemeral_index=True` whenever `index_id` came from an ephemeral index; otherwise execution fails server-side.

## Flavour B — Existing named index

Skip `fetch_file`, `upload_attachment`, and `create_index` entirely.

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

## Resume values and errors

| Yielded model | Resume value | Useful fields |
|---|---|---|
| `WaitEphemeralIndex` | `ContextGroundingIndex` | `id`, `folder_key` (ingested) |
| `CreateDeepRag` | `DeepRagContent` (validated) or `dict` | `text`, `citations` |
| `CreateDeepRagRaw` | `DeepRagResponse` raw | full response, no status validation |

Runtime raises `UiPathFaultedTriggerError` on terminal `Failed`; import it with `from uipath.core.errors import UiPathFaultedTriggerError`. Use `*Raw` variants only to inspect a failed status without raising.

Resume values may be typed models or dicts, depending on SDK version:

```python
text = content.get("text", "") if isinstance(content, dict) else getattr(content, "text", "")
raw_citations = content.get("citations") if isinstance(content, dict) else getattr(content, "citations", [])
citations = [c if isinstance(c, dict) else c.model_dump() for c in (raw_citations or [])]
```

## Citation modes

Pass `citation_mode=CitationMode.SKIP | INLINE` to `CreateDeepRag`. The default is `SKIP` for lowest latency and no citations. `INLINE` interleaves citations in `content.text`. Verify enum values for the installed SDK:

```python
from uipath.platform.context_grounding import CitationMode
list(CitationMode)
```

## Local-run verification

Run:

```bash
uip codedagent run agent '{"instructions":"<PROMPT>"}' --output-file out.json
```

The runtime executes pre-interrupt nodes synchronously, then suspends at `create_index` with `WaitEphemeralIndex` (Flavour A) or at `run_deep_rag` with `CreateDeepRag` (Flavour B). This is correct, not a failure. End-to-end completion occurs only on a deployed agent or through `uip codedagent dev`.

## Resources

- UiPath Python SDK: <https://uipath.github.io/uipath-python/>
- Built-in tool reference (BT/DR/etc.): `uipath_langchain.agent.tools.context_tool` in the installed venv
- API endpoints (debug): [api-reference.md](api-reference.md)
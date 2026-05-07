# BatchTransform — API Reference (Debug Only)

> **Stop.** In a low-code agent, the runtime calls these endpoints when the built-in `batch-transform` tool is enabled — see [impl-json.md](impl-json.md). Direct API calls are debug-only. The coded surface (Python `@durable_interrupt` + `Create*` resume-trigger models from `uipath.platform.common`) lives in `uipath-batch-transform-coded`.

This file lists endpoints for direct invocation from outside an agent (custom tooling, scripts, debugging). Request body shapes evolve with the SDK — **trust the SDK source, not this file**:

- Request specs: `uipath/platform/context_grounding/_context_grounding_service.py` in the installed venv (look for `_*_creation_spec` and `_*_retrieve_spec` methods)
- Pydantic models (input + response): `uipath/platform/context_grounding/context_grounding.py`
- Resume-trigger models: `uipath/platform/common/interrupt_models.py`
- Public docs: <https://uipath.github.io/uipath-python/>

## Verified Endpoint Paths

| Verb | Path | Purpose |
|---|---|---|
| POST | `/ecs_/v2/indexes/createephemeral` | Create an ephemeral index over attachments (`usage`: `DeepRAG` or `BatchRAG`) |
| GET  | `/ecs_/v2/indexes/{id}` | Read index metadata, including `lastIngestionStatus` |
| POST | `/ecs_/v2/indexes/{index_id}/createDeepRag` | Start a DeepRAG task |
| POST | `/ecs_/v2/indexes/{index_id}/createBatchRag` | Start a BatchTransform task (the SDK calls it BatchRag internally) |
| GET  | `/ecs_/v2/deeprag/{id}` | Read DeepRAG task status + content |
| GET  | `/ecs_/v2/batchRag/{id}` | Read BatchTransform task status + result-file metadata |

All endpoints require either `x-uipath-folderkey` or `x-uipath-folderpath` header.

## Common Errors

| Status | Body fragment | Cause | Fix |
|---|---|---|---|
| 400 | `"A folder is required for this action."` | Missing folder header | Set `UIPATH_FOLDER_KEY` env var; in coded agents, pass `index_folder_key` on the resume-trigger model |
| 400 | `"Summarization requires a successfully completed ingestion process."` | Index not ingested yet | The runtime waits on the index event when you yield `CreateEphemeralIndex`. Hitting this from direct API calls means you skipped the ingestion poll. |
| 400 | `"The Prompt field is required."` | Empty `prompt` | Pass non-empty prompt |
| 400 | `outputColumns` validation | Name regex / length | See `BatchTransformOutputColumn` in `context_grounding.py` |
| 403 | `"User is missing required index permissions."` | Role lacks index permission in folder | Use a folder where the user / agent identity has rights (personal workspace key is the safe default) |
| 404 | `"Folder does not exist or the user does not have access..."` | Folder name typo or no access | Verify with `sdk.resource_catalog.search_async` |

## Why Not Document Body Shapes Here

Inline JSON shapes drift the moment the SDK changes a field name (e.g., `enableWebSearchGrounding` vs `useWebSearchGrounding`, `globPattern` vs `targetFileGlobPattern`, `Footnote` citation mode that does not exist). Reading the SDK's `_*_creation_spec` methods gives the exact body the platform accepts at the version you are running against. Any inline copy here will be wrong eventually.

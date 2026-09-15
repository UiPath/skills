# Python Workflow Guide

The end-to-end Python Coded Function workflow: scaffold → schema → logic → registration → dependencies → entry points → SDK usage → pack/publish. Language split and shared rules → [SKILL.md](../../SKILL.md).



## Step 1: Scaffold

```bash
uip function new <name> --language py       # Python Coded Function
uip function new <name> --language ts       # TypeScript Function → ../js/
uip function new <name> --language js       # JavaScript Function → ../js/
```

**`--language py` is required for Python.** The default language is TypeScript — omitting `--language` scaffolds a JS/TS project. Always pass `-l py` or `--language py` when building a Python Coded Function.

`--empty` skips the hello-world function (JS/TS only).

**The scaffold follows the installed packages.** With a framework package present in the environment (`uipath-langchain`, `llama-index`, `openai-agents`), `uip function new -l py` emits that framework's **agent** scaffold — `langgraph.json` plus an LLM `main.py` — not a function scaffold. Expected behaviour, not a broken flag. Recovery, in one pass:

1. Delete the framework config (`langgraph.json` and equivalents).
2. Replace `main.py` with the function template (Step 3).
3. Keep `pyproject.toml`'s `[project]` metadata (Step 5) — swap `dependencies` for what the function needs.

Do not re-run `new` with different flag spellings, and do not read CLI or SDK internals to explain the scaffold. Reshape the project and move on.

## Step 2: Define Function Schema

Use typed I/O. The SDK accepts pydantic `BaseModel`, `pydantic.dataclasses.dataclass`, a stdlib `@dataclass`, or a thin class with typed annotations. The shipped samples favor **pydantic** (`BaseModel` in csv-processor, `pydantic.dataclasses.dataclass` in calculator/greeter):

```python
from pydantic import BaseModel

class Input(BaseModel):
    document_id: str = ""

class Output(BaseModel):
    vendor_name: str = ""
    total_amount: float = 0.0
    error_type: str = ""     # populated on failure, empty on success
    error_message: str = ""  # human-readable error detail
```

## Step 3: Implement Business Logic

**Do NOT make LLM calls inside a Coded Function.** LLM calls introduce non-determinism and latency that break the function contract. If the step requires LLM reasoning or multi-step AI decisions, use a framework-based agent (LangGraph, LlamaIndex, OpenAI Agents) instead.

### Minimal template

```python
from __future__ import annotations

from pydantic import BaseModel
from uipath.tracing import traced
from uipath.platform import UiPath

class Input(BaseModel):
    document_id: str = ""

class Output(BaseModel):
    result: str = ""
    error_type: str = ""
    error_message: str = ""

# Lazy SDK singleton — never instantiate UiPath() at module level
_sdk: UiPath | None = None

def sdk() -> UiPath:
    global _sdk
    if _sdk is None:
        _sdk = UiPath()
    return _sdk

@traced(name="my_function", run_type="uipath")
def my_function(input: Input) -> Output:
    out = Output()
    try:
        # SDK calls, data processing, rule-based logic only
        asset = sdk().assets.retrieve("MY_ASSET", folder_path="Shared")
        out.result = str(asset.value)
    except Exception as exc:
        out.error_type = "FAILED"
        out.error_message = str(exc)
    return out
```

Key rules:
- **Typed I/O** — pydantic `BaseModel`, `pydantic.dataclasses.dataclass`, stdlib `@dataclass`, or a thin class with typed annotations; samples favor pydantic
- **`def` or `async def`** — both supported (csv-processor uses `async def main`); the function name is arbitrary
- **Lazy SDK init** — instantiate `UiPath()` inside a getter, never at module level
- **Errors returned, not raised** — populate `error_type`/`error_message` output fields and return; never let exceptions bubble out of the entrypoint
- **`@traced(name=..., run_type="uipath")`** — apply to the entrypoint and any sub-functions you want visible in LLM Ops Traces

## Step 4: Register in `uipath.json`

```json
{
  "runtimeOptions": { "isConversational": false },
  "functions": {
    "main": "main.py:my_function"
  }
}
```

The key is the entrypoint name — it can be any string and marks this as the callable entrypoint. The value is `"<file>:<function_name>"`. Both the key and the function name are arbitrary.

**This `functions` map is what identifies the project as a Coded Function** — the runtime's `determine_project_type()` reads the entrypoint type from `uipath.json`.

## Step 5: Declare dependencies in `pyproject.toml`

```toml
[project]
name = "my-function"
version = "0.1.0"
description = "..."
authors = [{ name = "Your Name", email = "you@example.com" }]
requires-python = ">=3.11"
dependencies = [
    "uipath",
    "httpx>=0.28",          # if making HTTP calls
    "pydantic-settings>=2", # if using Settings for env/asset config
]
```

`authors` is **required** — without it `uip function pack` rejects the package with `Project authors cannot be empty`.

No `[build-system]` section. The project is identified as a Coded Function by the `functions` map in `uipath.json` (Step 4).

## Step 6: Generate Entry Points

```bash
uip function init
```

Python only. Discovers entrypoints and generates `entry-points.json`, `bindings.json`, and `project.uiproj`. Must run before `pack` or `push`. Re-run whenever Input/Output schemas or the entrypoint registration in `uipath.json` changes.

## Step 7: SDK Capabilities

Full SDK reference: https://uipath.github.io/uipath-python/

Access UiPath platform resources via `sdk()`:

```python
from uipath.platform import UiPath
from uipath.platform.connections.connections import ActivityMetadata, ActivityParameterLocationInfo

# Assets — retrieve named credentials or config values
asset = sdk().assets.retrieve("ASSET_NAME", folder_path="Shared")
value = asset.string_value          # or credential_username / credential_password

# Buckets — download files for processing
sdk().buckets.download(
    name="BucketName",
    blob_file_path="relative/path/file.pdf",
    destination_path="/tmp/local.pdf",
    folder_path="Shared",
)

# Integration Service connections — invoke connector activities (ERP, CRM, etc.)
result = sdk().connections.invoke_activity(
    activity_metadata=ActivityMetadata(
        object_path="/executeSuiteQL",
        method_name="POST",
        content_type="application/json",
        parameter_location_info=ActivityParameterLocationInfo(body_fields=["q"]),
    ),
    connection_id="<connection-uuid>",
    activity_input={"q": "SELECT id FROM vendor WHERE ..."},
)
```

### File attachment inputs

To accept a runtime file, type an `Input` field as `Attachment` (pydantic model, not a dataclass):

```python
from pydantic import BaseModel
from uipath.platform.attachments import Attachment

class Input(BaseModel):
    attachment: Attachment
```

`uip function init` recognizes the `Attachment` type and emits `x-uipath-resource-kind: JobAttachment` in `entry-points.json` — the schema Studio Web and Orchestrator read to render a file picker for that field. Access fields snake_case: `attachment.full_name`, `attachment.content`.

## Step 8: Pack and Publish

```bash
uip function pack                            # creates .nupkg
uip function publish                         # upload to Orchestrator (interactive feed picker)
uip function publish --feed-id <FEED_ID>     # CI/non-interactive
```

To sync to Studio Web instead of publishing to Orchestrator:

```bash
uip function push
```

### What Goes Into the Package

`.nupkg` produced by `pack` contains project files (source, `pyproject.toml`, `uipath.json`, `uv.lock` when present) and generated metadata (`entry-points.json`, `bindings_v2.json`, `package-descriptor.json`, `operate.json`). Control inclusion and exclusion via `packOptions` in `uipath.json` — keep local-only fixtures, test data, and caches out of the published artifact:

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `fileExtensionsIncluded` | `string[]` | No | `[".py", ".mermaid", ".json", ".yaml", ".yml", ".md"]` | File extensions to include in the package |
| `filesIncluded` | `string[]` | No | `["pyproject.toml"]` | Specific files to always include |
| `filesExcluded` | `string[]` | No | `[]` | Specific files to exclude |
| `directoriesExcluded` | `string[]` | No | `[]` | Directories to exclude from packaging |
| `includeUvLock` | `boolean` | No | `false` | Whether to include `uv.lock` file |

**Example:**

```json
{
  "packOptions": {
    "fileExtensionsIncluded": [".py", ".json"],
    "filesIncluded": ["config.yaml"],
    "filesExcluded": ["test_*.py"],
    "directoriesExcluded": ["tests", "__pycache__"],
    "includeUvLock": true
  }
}
```

# Python Workflow Guide

End-to-end Python Coded Function workflow: scaffold → schema → logic → registration → dependencies → entry points → SDK → pack/publish. Language split and shared rules → [SKILL.md](../../SKILL.md).

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->
## Step 1: Scaffold

```bash
uip function new <name> --language py       # Python Coded Function
uip function new <name> --language ts       # TypeScript Function → ../js/
uip function new <name> --language js       # JavaScript Function → ../js/
```

**`--language py` is required for Python.** The default is TypeScript; omitting `--language` scaffolds a JS/TS project. Always pass `-l py` or `--language py` for a Python Coded Function. `--empty` skips the hello-world function (JS/TS only).

The Python scaffold contains `main.py`, `pyproject.toml`, and `uipath.json` with a `functions` map regardless of installed agent packages (`uipath-langchain`, `uipath-llamaindex`, `uipath-openai-agents`). For a coded agent, run `uip codedagent new` and use the [`uipath-agents`](/uipath:uipath-agents) skill.

## Step 2: Define Function Schema

Use typed I/O: pydantic `BaseModel`, `pydantic.dataclasses.dataclass`, stdlib `@dataclass`, or a thin class with typed annotations. Samples favor pydantic (`BaseModel` in csv-processor; `pydantic.dataclasses.dataclass` in calculator/greeter).

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

**Do NOT make LLM calls inside a Coded Function.** They introduce non-determinism and latency that break the function contract. For LLM reasoning or multi-step AI decisions, use a framework-based agent (LangGraph, LlamaIndex, OpenAI Agents).

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

Use typed I/O as in Step 2; either `def` or `async def` is supported (csv-processor uses `async def main`), with an arbitrary function name. Instantiate `UiPath()` lazily inside a getter, never at module level. Return errors in `error_type`/`error_message` rather than raising or letting exceptions escape the entrypoint. Apply `@traced(name=..., run_type="uipath")` to the entrypoint and any sub-functions that should appear in LLM Ops Traces.

## Step 4: Register in `uipath.json`

```json
{
  "runtimeOptions": { "isConversational": false },
  "functions": {
    "main": "main.py:my_function"
  }
}
```

The key is an arbitrary entrypoint name identifying the callable; the value is `"<file>:<function_name>"`. **This `functions` map identifies the project as a Coded Function**: the runtime's `determine_project_type()` reads the entrypoint type from `uipath.json`.

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

`authors` is **required**; without it `uip function pack` rejects the package with `Project authors cannot be empty`. Do not add a `[build-system]` section. The `functions` map in `uipath.json` identifies the project as a Coded Function (Step 4).

## Step 6: Generate Entry Points

Run:

```bash
uip function init
```

Python only. This discovers entrypoints and generates `entry-points.json` and `project.uiproj`; when absent, it creates `bindings.json` as `{"version": "2.0", "resources": []}` and leaves an existing one untouched. It never derives bindings from code—that is Step 8. Run it before `pack` or `push`, and re-run whenever Input/Output schemas or the `uipath.json` entrypoint registration changes.

## Step 7: SDK Capabilities

Full SDK reference: https://uipath.github.io/uipath-python/

Access UiPath resources through `sdk()`:

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

Every resource read this way—`assets`, `buckets`, `connections`, `queues`, `processes`, `context_grounding`, `mcp`, and `tasks`—needs a matching `bindings.json` entry (Step 8).

### File attachment inputs

To accept a runtime file, type an `Input` field as `Attachment` (a pydantic model, not a dataclass):

```python
from pydantic import BaseModel
from uipath.platform.attachments import Attachment

class Input(BaseModel):
    attachment: Attachment
```

`uip function init` recognizes `Attachment` and emits `x-uipath-resource-kind: JobAttachment` in `entry-points.json`, the schema that Studio Web and Orchestrator read to render a file picker for that field. Access fields in snake_case: `attachment.full_name`, `attachment.content`.

## Step 8: Sync `bindings.json`

`bindings.json` lets Orchestrator remap resources read by the function—assets, buckets, queues, processes, indexes, connections, MCP servers, and Action Center apps—per execution environment. `init` creates only the empty skeleton. Derive entries from the code with [bindings-reference.md](bindings-reference.md): scan every `.py` file for SDK resource calls, resolve module-level constants, write one entry per unique resource, bind it to the entrypoint from `entry-points.json`, and verify. Re-run after SDK resource call changes.

`uip function push` resolves entries against the Resource Catalog: it creates virtual placeholders for `asset` / `queue` / `process` / `bucket` / `app` that do not yet exist, while skipping `connection` / `index` / `mcpServer` bindings with a warning because those must already exist. Use the reference's § What `uip function push` does with bindings to act on warnings.

## Step 9: Pack and Publish

Run:

```bash
uip function pack                            # creates .nupkg
uip function publish                         # upload to Orchestrator (interactive feed picker)
uip function publish --feed-id <FEED_ID>     # CI/non-interactive
```

To sync to Studio Web instead of publishing to Orchestrator, run:

```bash
uip function push
```

`--ignore-resources` skips the `bindings.json` import.

### What Goes Into the Package

`.nupkg` from `pack` contains project files (source, `pyproject.toml`, `uipath.json`, `uv.lock` when present) and generated metadata (`entry-points.json`, `bindings_v2.json`—`bindings.json` copied as-is, `package-descriptor.json`, `operate.json`). Control inclusion with `packOptions` in `uipath.json`; exclude local-only fixtures, test data, and caches from published artifacts:

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `fileExtensionsIncluded` | `string[]` | No | `[".py", ".mermaid", ".json", ".yaml", ".yml", ".md"]` | File extensions to include in the package |
| `filesIncluded` | `string[]` | No | `["pyproject.toml"]` | Specific files to always include |
| `filesExcluded` | `string[]` | No | `[]` | Specific files to exclude |
| `directoriesExcluded` | `string[]` | No | `[]` | Directories to exclude from packaging |
| `includeUvLock` | `boolean` | No | `false` | Whether to include `uv.lock` file |

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
# UiPath Python Coded Functions

## What Python Coded Functions Are

Python Coded Functions are **atomic, bespoke units of business logic** — deterministic Python code packaged as a first-class UiPath artifact. Use them when generic activities don't cover the required logic: calling a third-party API with custom auth, processing documents with domain-specific rules, querying ERP systems via Integration Service connections, or transforming data in ways that no out-of-the-box activity handles.

A Coded Function is **not an agent**. It does not reason, route, or call LLMs. It takes typed input, executes deterministic code, and returns typed output.

### Invocation surfaces

A Python Coded Function can be invoked from any UiPath surface:

| Surface | How |
|---|---|
| Maestro BPMN | Service Task node |
| Maestro Flow | Coded Agent node or Service Task |
| Coded Agents (LangGraph / LlamaIndex / OpenAI Agents) | Called as a tool or step |
| Other Coded Functions | Direct Python call or Orchestrator job |
| Orchestrator API | `POST /Jobs/StartJobs` |
| CLI | `uip functions pack` → `uip functions publish` |

### Python Functions vs JS Functions

| | Python Coded Function | JS/TS Function |
|---|---|---|
| **Job semantics** | Yes — Orchestrator job ID, audit trail, retry, scheduling | No — inline HTTP only, no job lifecycle |
| **Invocation** | Maestro, Flow, Agents, Orchestrator API | HTTP endpoint (BFF for Coded Apps) |
| **Runtime** | Serverless or Local Unattended Robot | Serverless HTTP shared tier |
| **SDK access** | Full UiPath Python SDK (assets, buckets, queues, connections) | Workload token forwarding only |
| **Scaffold** | `uip functions new <name> --language py` | `uip functions new <name> --language ts` (default) |
| **Init** | `uip functions init` (generates entry-points.json) | Not needed |
| **Local dev** | `uip functions run` | `uip functions serve` + `uip functions run` |
| **Best for** | Agentic process steps, ERP integration, document AI, data pipelines | Backend-for-Frontend for Coded Apps |

Use Python when the logic needs job semantics, platform SDK access, or is invoked from Maestro/agents. Use JS when the caller is a Coded App frontend and low HTTP latency matters.

---

## CLI Reference

All Python Coded Function lifecycle commands use `uip functions`:

```bash
uip functions new <name> -l py     # scaffold a new Python Functions project (--language py required)
uip functions init                 # Python only — generate entry-points.json, bindings.json, project.uiproj
uip functions pack                 # pack to .nupkg for deployment
uip functions publish              # upload .nupkg to Orchestrator (prompts for feed, or use --feed-id)
uip functions push                 # sync project to Studio Web
```

> `uip functions run` works for both Python and JS/TS. `uip functions serve` is **JS/TS only** — it starts the local HTTP server that `run` invokes against.

---

## Workflow

### Step 1: Scaffold

```bash
uip functions new <name> --language py       # Python Coded Function
uip functions new <name> --language ts       # TypeScript Function (JS/TS, no job semantics)
uip functions new <name> --language js       # JavaScript Function (JS/TS, no job semantics)
```

**`--language py` is required for Python.** The default language is TypeScript — omitting `--language` scaffolds a JS/TS project. Always pass `-l py` or `--language py` when building a Python Coded Function.

`--empty` skips the hello-world function (JS/TS only).

### Step 2: Define Function Schema

Schemas are Python `@dataclass` types (not Pydantic BaseModel):

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Input:
    document_id: str = ""

@dataclass
class Output:
    vendor_name: str = ""
    total_amount: float = 0.0
    error_type: str = ""     # populated on failure, empty on success
    error_message: str = ""  # human-readable error detail
```

### Step 3: Implement Business Logic

**Do NOT make LLM calls inside a Coded Function.** LLM calls introduce non-determinism and latency that break the function contract. If the step requires LLM reasoning or multi-step AI decisions, use a framework-based agent (LangGraph, LlamaIndex, OpenAI Agents) instead.

#### Minimal template

```python
from __future__ import annotations

from dataclasses import dataclass
from uipath.core.tracing import traced
from uipath.platform import UiPath

@dataclass
class Input:
    document_id: str = ""

@dataclass
class Output:
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
- **`@dataclass`** for Input/Output — not `BaseModel`
- **Sync function** — `def`, not `async def`; the function name is arbitrary
- **Lazy SDK init** — instantiate `UiPath()` inside a getter, never at module level
- **Errors returned, not raised** — populate `error_type`/`error_message` output fields and return; never let exceptions bubble out of the entrypoint
- **`@traced(name=..., run_type="uipath")`** — apply to the entrypoint and any sub-functions you want visible in LLM Ops Traces

### Step 4: Register in `uipath.json`

```json
{
  "runtimeOptions": { "isConversational": false },
  "functions": {
    "main": "main.py:my_function"
  }
}
```

The key is the entrypoint name — it can be any string and marks this as the callable entrypoint. The value is `"<file>:<function_name>"`. Both the key and the function name are arbitrary.

### Step 5: Mark project type in `pyproject.toml`

```toml
[project]
name = "my-function"
version = "0.1.0"
description = "..."
authors = [{ name = "..." }]
requires-python = ">=3.11"
dependencies = [
    "uipath>=2.10",
    "httpx>=0.28",          # if making HTTP calls
    "pydantic-settings>=2", # if using Settings for env/asset config
]

[tool.uipath]
type = "function"           # required — identifies this as a Python Coded Function
```

**`[tool.uipath] type = "function"` is required.** Without it the project is treated as a coded agent. No `[build-system]` section.

### Step 6: Generate Entry Points

```bash
uip functions init
```

Python only. Discovers entrypoints and generates `entry-points.json`, `bindings.json`, and `project.uiproj`. Must run before `pack` or `push`. Re-run whenever Input/Output schemas or the entrypoint registration in `uipath.json` changes.

### Step 7: Pack and Publish

```bash
uip functions pack                            # creates .nupkg
uip functions publish                         # upload to Orchestrator (interactive feed picker)
uip functions publish --feed-id <FEED_ID>     # CI/non-interactive
```

To sync to Studio Web instead of publishing to Orchestrator:

```bash
uip functions push
```

## Important Notes

- `UiPath()` must never be instantiated at module level — always inside a function body
- `[tool.uipath] type = "function"` in `pyproject.toml` is required
- `uip functions init` must run before `pack` or `push` — it generates `entry-points.json`
- Python Functions have full job semantics: Orchestrator job ID, audit trail, retry, scheduling
- JS Functions have no job semantics and cannot be started as Orchestrator jobs — use Python when the caller is Maestro, a Flow, or an agent
- `uip functions run` works for both Python and JS/TS local execution; `uip functions serve` is JS/TS only (starts the local HTTP server that `run` invokes against)
- If cloud-backed work requires authentication, run `uip login --organization "<ORG>" --tenant "<TENANT>" --output json`.

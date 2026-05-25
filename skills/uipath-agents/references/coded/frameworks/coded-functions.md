# UiPath Python Coded Functions

## What Python Coded Functions Are

Python Coded Functions are **atomic, bespoke units of business logic** — deterministic Python code packaged as a first-class UiPath artifact. Use them when generic activities don't cover the required logic: calling a third-party API with custom auth, processing documents with domain-specific rules, querying ERP systems via Integration Service connections, transforming data in ways that no out-of-the-box activity handles, among other scenarios.

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
| CLI | `uip functions run` |

### Python Functions vs JS Functions

| | Python Coded Function | JS/TS Function |
|---|---|---|
| **Job semantics** | Yes — Orchestrator job ID, audit trail, retry, scheduling | No — inline HTTP only, no job lifecycle |
| **Invocation** | Maestro, Flow, Agents, Orchestrator API | HTTP endpoint (BFF for Coded Apps) |
| **Runtime** | Serverless or Local Unattended Robot | Serverless HTTP shared tier |
| **SDK access** | Full UiPath Python SDK (assets, buckets, queues, connections) | Workload token forwarding only |
| **Scaffold** | `uip functions new <name> --language py` | `uip functions new <name> --language ts` (default) |
| **Init** | `uip functions init` (generates entry-points.json) | Not needed |
| **Local dev** | `uip functions run` / `uip functions dev` | `uip functions serve` + `uip functions run` |
| **Best for** | Deterministic, simple, atomic step in an agentic workflow | Backend-for-Frontend for Coded Apps |

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

Schemas use `@dataclass` or Pydantic `BaseModel` (preferred for validation):

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
from functools import lru_cache

from uipath.platform import UiPath


@dataclass
class Input:
    document_id: str = ""


@dataclass
class Output:
    result: str = ""
    error_type: str = ""
    error_message: str = ""


@lru_cache(maxsize=1)
def _sdk() -> UiPath:
    return UiPath()


async def my_function(input: Input) -> Output:
    out = Output()
    try:
        # SDK calls, data processing, rule-based logic only
        asset = await _sdk().assets.retrieve_async("MY_ASSET", folder_path="Shared")
        out.result = str(asset.value)
    except Exception as exc:
        out.error_type = "FAILED"
        out.error_message = str(exc)
    return out
```

Key rules:
- **`@dataclass` or `BaseModel`** for Input/Output — `BaseModel` preferred for validation
- **Async preferred** — use `async def`; sync `def` also works; function name is arbitrary
- **Lazy SDK init** — use `@lru_cache(maxsize=1)` on a getter, never instantiate `UiPath()` at module level
- **Errors returned, not raised** — populate `error_type`/`error_message` output fields and return; never let exceptions bubble out of the entrypoint
- **Tracing** — root entrypoint is traced automatically; apply `@traced(name=..., run_type="uipath")` only to sub-functions you want visible in LLM Ops Traces

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
    "pydantic-settings>=2", # if using Settings for env/asset config
]

[tool.uipath]
type = "function"
```

No `[build-system]` section. The actual project-type discriminator is the `functions` key in `uipath.json`, not `pyproject.toml`.

### Step 6: Generate Entry Points

```bash
uip functions init
```

Python only. Discovers entrypoints and generates `entry-points.json`, `bindings.json`, and `project.uiproj`. Must run before `pack` or `push`. Re-run whenever Input/Output schemas or the entrypoint registration in `uipath.json` changes.

### Step 7: Run Locally

```bash
uip functions run <ENTRYPOINT_NAME> --input-file input.json --output-file output.json
```

`<ENTRYPOINT_NAME>` is the key from the `functions` object in `uipath.json`. Always use `uip functions run` for local execution — do not invoke the function directly with Python. `--input` (inline JSON) is the legacy flag; prefer `--input-file`. Always pass `--output-file` to capture the result.

Example:
```bash
uip functions run main --input '{"invoice_number": "INV-001", "vendor_name": "Acme", "total_amount": 100.0}' --output-file output.json
```

### Step 8: Pack and Publish

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

- `UiPath()` must never be instantiated at module level — use `@lru_cache(maxsize=1)` on a getter
- Project type is determined by the `functions` key in `uipath.json`, not by `pyproject.toml`
- `uip functions init` must run before `pack` or `push` — it generates `entry-points.json`
- Python Functions have full job semantics: Orchestrator job ID, audit trail, retry, scheduling
- JS Functions have no job semantics and cannot be started as Orchestrator jobs — use Python when the caller is Maestro, a Flow, or an agent
- `uip functions run` is the only supported local execution method — do not invoke the function directly with Python; `uip functions serve` is JS/TS only

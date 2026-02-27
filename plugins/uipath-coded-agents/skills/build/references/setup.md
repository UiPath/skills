# Project Setup

Set up a new UiPath coded agent project from scratch.

## Prerequisites

- **Python 3.11+** installed
- **uv** package manager installed ([docs](https://docs.astral.sh/uv/))
- UiPath account with access to Orchestrator (for deployment)

## Choose Your Agent Type

| Agent Type | Config File | Entrypoint | Key Dependency | Integration Guide                     |
|---|---|---|---|---------------------------------------|
| **Simple Function** | `uipath.json` | `main.py` (function) | `uipath` | [Guide](simple-agents.md)             |
| **LangGraph** | `langgraph.json` | `main.py` (compiled StateGraph) | `uipath-langchain` | [Guide](/uipath-coded-agents:langgraph) |
| **LlamaIndex** | `llama_index.json` | `main.py` (Workflow instance) | `uipath-llamaindex` | [Guide](/uipath-coded-agents:llamaindex) |
| **OpenAI Agents** | `openai_agents.json` | `main.py` (Agent instance) | `uipath-openai-agents` | [Guide](/uipath-coded-agents:openai-agents) |

Each integration guide is **self-contained** — it covers project structure, dependencies, input/output patterns, `uipath init`, and complete examples. For LangGraph, LlamaIndex, or OpenAI Agents, see the dedicated skills using the links above.

The rest of this page covers the **common setup steps** shared by all agent types, plus details specific to **simple function agents**.

## Creating a New Project

### 1. Setup New Project Directory (if it does not exist already)

```bash
mkdir my-agent && cd my-agent
```

Then, copy `pyproject.toml` file from assets to the agent directory.

If building an agent for a specific framework, add framework-specific dependencies:

```bash
# For LangGraph agents
uv add uipath-langchain

# For LlamaIndex agents
uv add uipath-llamaindex

# For OpenAI Agents
uv add uipath-openai-agents
```

Finally, to install dependencies, run:

```bash
uv sync
```

### 2. Scaffold with `uipath new`

If there is **no existing agent code**, use `uipath new` to scaffold the project. It generates necessary integration-specific config file based on which integration package is installed. It may also modify dependencies in `pyproject.toml`.

```bash
uv run uipath new my-agent
```

**What it generates per integration:**

| Integration | Generated Files | Template Content |
|---|---|---|
| Simple (base) | `main.py`, `pyproject.toml`, `uipath.json` | Dataclass-based echo function |
| LangGraph | `main.py`, `pyproject.toml`, `langgraph.json` | StateGraph with UiPathChat LLM |
| LlamaIndex | `main.py`, `pyproject.toml`, `llama_index.json` | Workflow with StartEvent/StopEvent |
| OpenAI Agents | `main.py`, `pyproject.toml`, `openai_agents.json`, `AGENTS.md` | Agent with UiPathChatOpenAI + tool |

**Which template is used** depends on which integration package is installed. If `uipath-langchain` is installed, you get a LangGraph scaffold. If none of the integration packages are installed, you get the base scaffold.

> **Skip this step** if the project already has `main.py` or `graph.py` with agent code. `uipath new` is only for starting from scratch.

After scaffolding, modify the generated `main.py` to implement your actual agent logic.

### 3. Install Dependencies

```bash
uv sync
```

### 4. Verify SDK

```bash
uv run uipath --version
```

### 5. Authenticate

See [Authentication Setup](/uipath-coded-agents:authentication) if your agent needs UiPath Cloud access.

## Simple Function Agent Details

The sections below are specific to **simple function agents** (no LLM framework). For LangGraph, LlamaIndex, or OpenAI Agents, see their respective integration guides.

### Defining Input/Output Models

Every simple function agent requires Pydantic `Input` and `Output` models in `main.py`:

```python
from pydantic import BaseModel, Field
from uipath.tracing import traced

class Input(BaseModel):
    query: str = Field(description="The user's question")
    max_results: int = Field(default=5, description="Maximum results to return")

class Output(BaseModel):
    answer: str = Field(description="The agent's response")
    sources: list[str] = Field(default_factory=list, description="Source references")

@traced()
async def main(input: Input) -> Output:
    # Agent logic here
    return Output(answer="Hello!", sources=[])
```

### Project Structure

```
my-agent/
├── main.py                 # Agent entrypoint with Input/Output models
├── pyproject.toml          # Python project configuration
├── uipath.json             # UiPath project configuration
├── entry-points.json       # Generated entry points with JSON schemas
├── bindings.json           # Runtime bindings
├── .env                    # Environment variables
├── .uipath/                # Internal UiPath files
│   └── telemetry.json
└── main.mermaid            # Generated graph diagram
```

### First-Time Checklist

1. Create project directory
2. Run `uv run uipath new my-agent` to scaffold (if no code exists)
3. Run `uv sync` to install dependencies
4. Verify with `uv run uipath --version`
5. [Authenticate](/uipath-coded-agents:authentication) if needed
6. Modify `main.py` with your `Input`, `Output` models and `main` function
7. Run `uv run uipath init` to generate configuration
8. [Test](/uipath-coded-agents:execute) with `uv run uipath run main '{"query": "test"}'`

## Running `uipath init`

After creating your entrypoint file, generate project configuration:

```bash
uv run uipath init
```

This works for **all agent types**. The CLI auto-detects the agent type by checking for config files (`langgraph.json`, `llama_index.json`, `openai_agents.json`) via registered middleware. If none are found, it falls back to simple function agent detection.

### Simple Function Agents — Entrypoint Registration

For simple function agents (no LangGraph/LlamaIndex/OpenAI Agents), `uipath init` does NOT auto-discover entrypoints. You must register them in `uipath.json` under `"functions"` **before** running `uipath init` (or re-run init after adding them).

After the first `uv run uipath init` creates `uipath.json`, edit it to add your function mapping:

```json
{
  "functions": {
    "main": "main.py:main"
  }
}
```

The format is `"entrypoint_name": "file.py:function_name"`. Then re-run `uv run uipath init` to generate the entry points.

LangGraph, LlamaIndex, and OpenAI Agents integrations auto-discover entrypoints from their respective config files (`langgraph.json`, `llama_index.json`, `openai_agents.json`) — no manual registration needed.

### What It Generates

| File | Purpose |
|------|---------|
| `uipath.json` | Project configuration (runtime options, pack options) |
| `entry-points.json` | Entry point definitions with JSON schemas from your Pydantic models |
| `bindings.json` | Runtime bindings (v2.0 format) |
| `.env` | Environment variables template |
| `*.mermaid` | Mermaid diagram files for graph visualization |
| `.uipath/telemetry.json` | Telemetry configuration with project ID |
| `AGENTS.md`, `.agent/` | Documentation files |

### Options

- **`--no-agents-md-override`** - Skip overwriting existing `.agent` files and `AGENTS.md`

### When to Re-run

Re-run `uv run uipath init` whenever you modify your input/output models to regenerate the JSON schemas in `entry-points.json`.

## uipath.json Structure

The main project configuration file (generated by `uipath init`):

```json
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/uipath",
  "runtimeOptions": {
    "isConversational": false
  },
  "packOptions": {
    "fileExtensionsIncluded": [],
    "filesIncluded": [],
    "filesExcluded": [],
    "directoriesExcluded": [],
    "includeUvLock": true
  },
  "functions": {}
}
```

**Key fields:**
- **`runtimeOptions.isConversational`** - Set `true` for conversational/chat agents
- **`packOptions`** - Control which files are included when packaging for deployment
- **`functions`** - Entrypoint mappings (format: `"file_path:function_name"`)

## Next Steps

- **Simple function agent?** See [Creating Agents](simple-agents.md) for the full workflow
- **LangGraph agent?** See [LangGraph Integration](langgraph-integration.md)
- **LlamaIndex agent?** See [LlamaIndex Integration](llamaindex-integration.md)
- **OpenAI Agents?** See [OpenAI Agents Integration](openai-agents-integration.md)
- **Run your agent**: See [Running Agents](running-agents.md) to execute and test
- **Deploy**: See [Deployment](deployment.md) to publish to UiPath Cloud

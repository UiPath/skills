# Setup UiPath Agent Project

> **Note:** This guide covers coded (Python) agent setup. For low-code agent setup, see [lowcode/setup.md](../lowcode/setup.md).

Scaffold a new project or initialize an existing one for UiPath agent development.

## Quick Reference

```bash
# New project from scratch
mkdir my-agent && cd my-agent
# Copy pyproject.toml template, add framework dep if needed, then:
uv sync
source .venv/bin/activate           # activate venv BEFORE uip codedagent commands
uip codedagent setup --format json # configure Python backend (once per env)
uip codedagent new my-agent        # name is REQUIRED
uip codedagent init

# Existing project — just generate entry points
uip codedagent init
```

## Documentation

- **[Project Setup Guide](setup.md)** — Complete setup walkthrough
  - Prerequisites (Python 3.11+, uv)
  - Choosing agent type (Simple, LangGraph, LlamaIndex, OpenAI Agents)
  - Creating and scaffolding projects
  - Running `uip codedagent init` and what it generates
  - `uipath.json` structure and configuration
  - Simple function agent details (Input/Output models, project structure)

## Template

A `pyproject.toml` template is available in [assets/templates/pyproject.toml](../../assets/templates/pyproject.toml). Replace `{AGENT_NAME}` and `{AGENT_DESCRIPTION}` after copying.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `No entrypoints found in uipath.json` | Framework package not installed or config file missing | Ensure `uipath-langchain` (or equivalent) is in deps and `langgraph.json` exists |
| `NameError: name 'StateGraph' is not defined` | `uip codedagent init` imports `main.py` but `langgraph` not installed | Run `uv sync` to install all dependencies before `uip codedagent init` |
| `No solution found` for Python 3.10 | `requires-python` set too low | Set `requires-python = ">=3.11"` — UiPath SDK requires Python 3.11+ |
| `Project authors cannot be empty` | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` section |

## Additional Instructions

- **STOP: You must know which framework to use before running setup.** If no framework has been selected yet, ask the user to choose (Simple Function, LangGraph, LlamaIndex, or OpenAI Agents). The framework determines which dependency to add and what `uip codedagent new` scaffolds.
- Read the [setup reference](setup.md) before making assumptions about project structure.
- **Use lazy LLM initialization** so `uip codedagent init` works without auth. Never instantiate LLM clients at module level — create them inside functions/nodes.
- After changing Input/Output models, re-run `uip codedagent init` to regenerate schemas.

---

# Project Setup

Set up a new UiPath coded agent project from scratch.

## Prerequisites

- **Python 3.11+** installed
- **Node.js 18+** and **npm** installed — required for `uip` CLI (`npm install -g @uipath/cli`)
- **uv** package manager installed ([docs](https://docs.astral.sh/uv/))
- UiPath account with access to Orchestrator (for deployment)

## Choose Your Agent Type

| Agent Type | Config File | Entrypoint | Key Dependency | Integration Guide                     |
|---|---|---|---|---------------------------------------|
| **Simple Function** | `uipath.json` | `main.py` (function) | `uipath` | [Guide](../frameworks/simple-agents.md)             |
| **LangGraph** | `langgraph.json` | `main.py` (compiled StateGraph) | `uipath-langchain` | See build skill |
| **LlamaIndex** | `llama_index.json` | `main.py` (Workflow instance) | `uipath-llamaindex` | See build skill |
| **OpenAI Agents** | `openai_agents.json` | `main.py` (Agent instance) | `uipath-openai-agents` | See build skill |

Each integration guide is **self-contained** — it covers project structure, dependencies, input/output patterns, `uip codedagent init`, and complete examples.

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

### 2. Scaffold with `uip codedagent new`

If there is **no existing agent code**, use `uip codedagent new` to scaffold the project. It generates necessary integration-specific config file based on which integration package is installed. It may also modify dependencies in `pyproject.toml`.

```bash
uip codedagent new my-agent
```

**What it generates per integration:**

| Integration | Generated Files | Template Content |
|---|---|---|
| Simple (base) | `main.py`, `pyproject.toml`, `uipath.json` | Dataclass-based echo function |
| LangGraph | `main.py`, `pyproject.toml`, `langgraph.json` | StateGraph with UiPathChat LLM |
| LlamaIndex | `main.py`, `pyproject.toml`, `llama_index.json` | Workflow with StartEvent/StopEvent |
| OpenAI Agents | `main.py`, `pyproject.toml`, `openai_agents.json`, `AGENTS.md` | Agent with UiPathChatOpenAI + tool |

**Which template is used** depends on which integration package is installed. If `uipath-langchain` is installed, you get a LangGraph scaffold. If none of the integration packages are installed, you get the base scaffold.

> **Skip this step** if the project already has `main.py` or `graph.py` with agent code. `uip codedagent new` is only for starting from scratch.

After scaffolding, modify the generated `main.py` to implement your actual agent logic.

### 3. Install Dependencies

```bash
uv sync
```

### 4. Verify SDK

```bash
uip codedagent --version
```

### 5. Authenticate

Run `uip login --format json` then `uip login tenant set "<TENANT>" --format json` if your agent needs UiPath Cloud access.

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
2. Copy `pyproject.toml` from `assets/templates/pyproject.toml` (replace placeholders)
3. Add framework dependency if needed (e.g., `uv add uipath-langchain`)
4. Run `uv sync` to install dependencies (must happen **before** `uip codedagent new`)
5. Run `source .venv/bin/activate` to activate the virtual environment
6. Run `uip codedagent setup --format json` to configure the Python runtime
7. Run `uip codedagent new my-agent` to scaffold `main.py` and framework config (framework template is selected based on installed packages — `uv sync` must run first)
8. Modify `main.py` with your agent logic
9. Run `uip codedagent init` to generate `entry-points.json`, `bindings.json`, and `.env`
10. Test with `uip codedagent run main '{"query": "test"}'`

## Running `uip codedagent init`

After creating your entrypoint file, generate project configuration:

```bash
uip codedagent init
```

This works for **all agent types**. The CLI auto-detects the agent type by checking for config files (`langgraph.json`, `llama_index.json`, `openai_agents.json`) via registered middleware. If none are found, it falls back to simple function agent detection.

### Simple Function Agents — Entrypoint Registration

For simple function agents (no LangGraph/LlamaIndex/OpenAI Agents), `uip codedagent init` does NOT auto-discover entrypoints. You must register them in `uipath.json` under `"functions"` **before** running `uip codedagent init` (or re-run init after adding them).

After the first `uip codedagent init` creates `uipath.json`, edit it to add your function mapping:

```json
{
  "functions": {
    "main": "main.py:main"
  }
}
```

The format is `"entrypoint_name": "file.py:function_name"`. Then re-run `uip codedagent init` to generate the entry points.

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

Re-run `uip codedagent init` whenever you modify your input/output models to regenerate the JSON schemas in `entry-points.json`.

## uipath.json Structure

The main project configuration file (generated by `uip codedagent init`):

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
- **`functions`** - Entrypoint name → file:function mappings. Format: `"<entrypoint_name>": "<file_path>:<function_name>"`. Example: `"main": "main.py:main"` means the entrypoint is named `main` and is called with `uip codedagent run main`.

# Project Setup

Set up a new UiPath coded agent project from scratch.

## Prerequisites

- **Python 3.11+** installed
- **uv** package manager installed ([docs](https://docs.astral.sh/uv/))
- UiPath account with access to Orchestrator (for deployment)

## Creating a New Project

### 1. Create Project Directory

```bash
mkdir my-agent && cd my-agent
```

### 2. Set Up pyproject.toml

Use the official template from skill assets if `pyproject.toml` doesn't exist. Replace `{AGENT_NAME}` and `{AGENT_DESCRIPTION}` with actual values:

```toml
[project]
name = "my-agent"
version = "0.1.0"
description = "UiPath Coded Agent - Describe what your agent does"
requires-python = ">=3.11"

dependencies = [
    "uipath>=2.9.9,<2.10.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[tool.setuptools]
py-modules = ["main"]
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Verify SDK

```bash
uv run uipath --version
```

### 5. Authenticate

If your agent needs UiPath Cloud access:

```bash
uv run uipath auth --alpha
```

See [Authentication](authentication.md) for details on authentication modes.

## Defining Input/Output Models

Every agent requires Pydantic `Input` and `Output` models in its entrypoint file (e.g., `main.py`):

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

## Running `uipath init`

After creating your entrypoint file, generate project configuration:

```bash
uv run uipath init
```

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

Re-run `uv run uipath init` whenever you modify your `Input` or `Output` Pydantic models to regenerate the JSON schemas in `entry-points.json`.

## uipath.json Structure

The main project configuration file:

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

## Project Structure Overview

A complete agent project looks like:

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

## First-Time Checklist

1. Create project directory
2. Set up `pyproject.toml` with UiPath SDK dependency
3. Run `uv sync` to install dependencies
4. Verify with `uv run uipath --version`
5. Authenticate with `uv run uipath auth --alpha` (if needed)
6. Create `main.py` with `Input`, `Output` models and a `main` function
7. Run `uv run uipath init` to generate configuration
8. Test with `uv run uipath run main '{"query": "test"}'`

## Next Steps

- **Build your agent**: See [Creating Agents](creating-agents.md) for the full development workflow
- **Run your agent**: See [Running Agents](running-agents.md) to execute and test
- **Deploy**: See [Deployment](deployment.md) to publish to UiPath Cloud

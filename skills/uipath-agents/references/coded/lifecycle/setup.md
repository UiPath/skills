# Setup UiPath Agent Project

## Preflight

```bash
python --version                                           # 3.11, 3.12, or 3.13
which uv  > /dev/null 2>&1 || echo "install uv:  curl -LsSf https://astral.sh/uv/install.sh | sh"
which uip > /dev/null 2>&1 || echo "install uip: npm install -g @uipath/cli"
```

## Framework Selection

Pick the framework before starting — the package installed in the Workflow determines which scaffold `uip codedagent new` produces.

| Agent Type | `<FRAMEWORK_PACKAGE>` | Framework config | Guide |
|---|---|---|---|
| Coded Function | `uipath` | `uipath.json` | [coded-function-agents.md](../frameworks/coded-function-agents.md) |
| LangGraph | `"uipath-langchain>=0.8.0,<0.9.0"` | `langgraph.json` | [langgraph-integration.md](../frameworks/langgraph-integration.md) |
| LlamaIndex | `uipath-llamaindex` | `llama_index.json` | [llamaindex-integration.md](../frameworks/llamaindex-integration.md) |
| OpenAI Agents | `uipath-openai-agents` | `openai_agents.json` | [openai-agents-integration.md](../frameworks/openai-agents-integration.md) |

## Starting Points

| Starting from | Use |
|---|---|
| Empty directory | The Workflow below |
| Existing UiPath agent (has `main.py` + `<framework>.json` + UiPath deps) | `uip codedagent setup && uip codedagent init` only |
| Existing Python agent (has `main.py`, missing UiPath deps / framework config) | `uv add <FRAMEWORK_PACKAGE>`, adapt `main.py` per the framework guide, then `uip codedagent setup && uip codedagent init` |

## Workflow

```bash
mkdir <PROJECT_NAME> && cd <PROJECT_NAME>
uv venv --python 3.13                        # uv defaults to the latest Python; pin to a UiPath-supported version
source .venv/bin/activate                    # Windows: .venv\Scripts\activate
uv pip install <FRAMEWORK_PACKAGE>
uip codedagent setup
uip codedagent new <PROJECT_NAME>
uv sync
uip codedagent init
```

## Coded Function Agents

`uipath.json` carries the entrypoint mapping:

```json
{
  "functions": {
    "main": "main.py:main"
  }
}
```

Edit the scaffolded `main.py`'s `Input` / `Output` models and `async def main` to fit the real agent.

## Generated Files

| File | Purpose |
|---|---|
| `pyproject.toml` | Project metadata and dependencies |
| `main.py` | Agent entrypoint |
| `<framework>.json` | Framework config (LangGraph / LlamaIndex / OpenAI Agents) |
| `uipath.json` | Runtime options, pack options, `functions` map |
| `entry-points.json` | Input / output schemas from Pydantic models |
| `bindings.json` | Runtime bindings |
| `uv.lock` | Dependency lockfile |
| `.uipath/telemetry.json` | Telemetry configuration |
| `AGENTS.md`, `.agent/` | Documentation |

## `uipath.json`

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

- `isConversational: true` for chat-style agents.
- `packOptions` controls `.nupkg` contents at deploy time.

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `uipath executable not found` | `setup` not run, or run without venv activated | Activate `.venv` and re-run `uip codedagent setup` |
| `No compatible Python installation found` | Python outside 3.11 – 3.13 | Install 3.11, 3.12, or 3.13 (or set `PYTHON_TOOL_PYTHON_VERSIONS`) |
| `Project authors cannot be empty` | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` |
| `NameError` during `init` | Framework not installed when `init` imports `main.py` | Run `uv sync` before `uip codedagent init` |
| `No entrypoints found in uipath.json` | Framework config or package missing | Verify `uv pip install` succeeded, then re-run `uip codedagent init` |

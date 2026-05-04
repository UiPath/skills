# Setup UiPath Agent Project

## Preflight

```bash
python --version                                           # 3.11, 3.12, or 3.13
which uv  > /dev/null 2>&1 || echo "install uv:  curl -LsSf https://astral.sh/uv/install.sh | sh"
which uip > /dev/null 2>&1 || echo "install uip: npm install -g @uipath/cli"
```

## Framework Selection

Pick the framework before starting. The package installed in the Workflow determines which scaffold `uip codedagent new` produces.

| Agent Type | `<FRAMEWORK_PACKAGE>` | Framework config | Guide |
|---|---|---|---|
| Coded Function | `uipath` | `uipath.json` | [coded-function-agents.md](../frameworks/coded-function-agents.md) |
| LangGraph | `"uipath-langchain"` | `langgraph.json` | [langgraph-integration.md](../frameworks/langgraph-integration.md) |
| LlamaIndex | `uipath-llamaindex` | `llama_index.json` | [llamaindex-integration.md](../frameworks/llamaindex-integration.md) |
| OpenAI Agents | `uipath-openai-agents` | `openai_agents.json` | [openai-agents-integration.md](../frameworks/openai-agents-integration.md) |

## Starting Points

| Starting from | Use |
|---|---|
| Empty directory | The Workflow below |
| Existing UiPath agent (has `main.py` + `<framework>.json` + UiPath deps) | `source .venv/bin/activate`, then `uip codedagent setup --force && uip codedagent init` only |
| Existing Python agent (has `main.py`, missing UiPath deps / framework config) | `source .venv/bin/activate`, `uv add <FRAMEWORK_PACKAGE>`, adapt `main.py` per the framework guide, then `uip codedagent setup --force && uip codedagent init` |

## Workflow

```bash
mkdir <PROJECT_NAME> && cd <PROJECT_NAME>
uv venv --python 3.13                        # uv defaults to the latest Python; pin to a UiPath-supported version
source .venv/bin/activate                    # Windows: .venv\Scripts\activate
uv pip install <FRAMEWORK_PACKAGE>
uip codedagent setup --force
uip codedagent new <PROJECT_NAME>
uv add uipath-dev --dev                      # required by `uip codedagent dev` (local dev web server)
uv sync
uip codedagent init
```

`uipath-dev` is added to the dev dependency group during scaffold so `uip codedagent dev` works later without a second install pass. Skipping it causes `uip codedagent dev` to fail with *"The 'uipath-dev' package is required to use the dev command"*.

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
| `uipath executable not found` | `setup` not run, or run without venv activated | Activate `.venv` and re-run `uip codedagent setup --force` |
| UiPath CLI/Python executable is not recognized, or `uipathExePath` is stale | The CLI still points at an old or missing virtualenv executable | Run `source .venv/bin/activate`, then `uip codedagent setup --force` to refresh `uipathExePath` |
| `Found .venv in current directory but no virtual environment is activated` | `.venv` exists but `VIRTUAL_ENV` is unset | Activate `.venv` first, then re-run `uip codedagent setup --force` |
| `No compatible Python installation found` | Python outside 3.11 – 3.13 | Install 3.11, 3.12, or 3.13 (or set `PYTHON_TOOL_PYTHON_VERSIONS`) |
| `Project authors cannot be empty` | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` |
| `NameError` during `init` | Framework not installed when `init` imports `main.py` | Run `uv sync` before `uip codedagent init` |
| `No entrypoints found in uipath.json` | Framework config or package missing | Verify `uv pip install` succeeded, then re-run `uip codedagent init` |
| `ModuleNotFoundError` for a package you just installed, even after activating `.venv` | A shell `python` alias points at a different interpreter (uv-managed, system, etc.) | Use `.venv/bin/python` directly for sanity checks, or `unalias python` for the session |

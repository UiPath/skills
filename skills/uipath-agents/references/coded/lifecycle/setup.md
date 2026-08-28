# Setup UiPath Agent Project

## Preflight

```bash
python --version                                           # 3.11, 3.12, or 3.13
which uv  > /dev/null 2>&1 || echo "install uv:  curl -LsSf https://astral.sh/uv/install.sh | sh"
which uip > /dev/null 2>&1 || echo "install uip: npm install -g @uipath/cli"
```

## Framework Selection

Select the framework before starting. The package installed in the Workflow determines the scaffold produced by `uip codedagent new`.

| Agent Type | `<FRAMEWORK_PACKAGE>` | Framework config | Guide |
|---|---|---|---|
| LangGraph | `"uipath-langchain"` | `langgraph.json` | [langgraph-integration.md](../frameworks/langgraph-integration.md) |
| LlamaIndex | `uipath-llamaindex` | `llama_index.json` | [llamaindex-integration.md](../frameworks/llamaindex-integration.md) |
| OpenAI Agents | `uipath-openai-agents` | `openai_agents.json` | [openai-agents-integration.md](../frameworks/openai-agents-integration.md) |

## Starting Points

| Starting from | Use |
|---|---|
| Empty directory | Follow the Workflow below. |
| Existing UiPath agent (`main.py` + `<framework>.json` + UiPath dependencies) | `source .venv/bin/activate`, then run `uip codedagent setup --force && uip codedagent init` only. |
| Existing Python agent (`main.py`, but missing UiPath dependencies or framework config) | Activate the venv, run `uv add <FRAMEWORK_PACKAGE>`, adapt `main.py` per the framework guide, then run `uip codedagent setup --force && uip codedagent init`. |
| Studio Web Local Workspace solution (an ancestor contains `.sw-path-marker` or `.local/folder.lock`) | Do not run `uip codedagent new`. Run `uv venv --python 3.13`, activate it, run `uv sync`, and run `uip codedagent setup --force`. After every edit that adds, removes, renames, or retypes a field on `Input`/`Output`/`State`, or changes the entry-function signature, run `init` again; see [local-workspace.md](local-workspace.md) § Schema Sync After Edits for the full rule and anti-patterns. |

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

Run `uv sync` before `uip codedagent init`. Add `uipath-dev` to the dev dependency group so `uip codedagent dev` works; otherwise it fails with *"The 'uipath-dev' package is required to use the dev command"*.

`uip codedagent setup` locates a Python with `uipath` installed and caches its path for later `init`/`run`/`eval`/`pack` commands. It searches PATH (`python3.x`, `python3`, `python`) and uses `.venv` only when activated; with uv, run `uv sync`, activate the venv, then run `uip codedagent setup`.

## Coded Function Agents

`uipath.json` maps the entrypoint:

```json
{
  "functions": {
    "main": "main.py:main"
  }
}
```

Edit the scaffolded `main.py` `Input` and `Output` models and `async def main` for the agent.

## Generated Files

| File | Purpose |
|---|---|
| `pyproject.toml` | Project metadata and dependencies |
| `main.py` | Agent entrypoint |
| `<framework>.json` | Framework config (LangGraph / LlamaIndex / OpenAI Agents) |
| `uipath.json` | Runtime options, pack options, and `functions` map |
| `entry-points.json` | Input/output schemas from Pydantic models |
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

- `runtimeOptions.isConversational` scaffold-defaults to `false` (single-shot); set it to `true` before `uip codedagent init` for a chat/conversational agent so `entry-points.json` gets the chat shape; see [conversational-agents](../capabilities/conversational-agents.md).
- Use `packOptions` to control `.nupkg` contents at deployment.
- Use `functions` for entrypoint mappings in `"file_path:function_name"` format.
- For a project registered in a solution and uploaded with `uip solution upload`, exclude Python build artifacts:

```json
"packOptions": {
  "directoriesExcluded": [".venv", "__pycache__"],
  "includeUvLock": true
}
```

`.venv/` contains installed wheels and can make uploads oversized; `__pycache__/` is ephemeral. Both regenerate from `pyproject.toml` + `uv.lock` on the target side. Without these exclusions, `uip solution upload` can produce an oversized archive rejected by Studio Web.

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `uipath executable not found` | `setup` was not run or ran without the venv activated | Activate `.venv` and run `uip codedagent setup --force`. |
| UiPath CLI/Python executable is not recognized, or `uipathExePath` is stale | The CLI points to an old or missing virtualenv executable | Run `source .venv/bin/activate`, then run `uip codedagent setup --force` to refresh `uipathExePath`. |
| `Found .venv in current directory but no virtual environment is activated` | `.venv` exists but `VIRTUAL_ENV` is unset | Activate `.venv`, then run `uip codedagent setup --force`. |
| `No compatible Python installation found` | Python is outside 3.11–3.13 | Install 3.11, 3.12, or 3.13, or set `PYTHON_TOOL_PYTHON_VERSIONS`. |
| `Project authors cannot be empty` | `authors` is missing from `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]`. |
| `NameError` during `init` | The framework was not installed when `init` imported `main.py` | Run `uv sync` before `uip codedagent init`. |
| `No entrypoints found in uipath.json` | Framework config or package is missing | Verify `uv pip install` succeeded, then run `uip codedagent init`. |
| `ModuleNotFoundError` for a package just installed, even after activating `.venv` | A shell `python` alias points to another interpreter (uv-managed, system, etc.) | Use `.venv/bin/python` directly for sanity checks, or run `unalias python` for the session. |
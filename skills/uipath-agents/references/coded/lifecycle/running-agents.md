# Run UiPath Agents

Execute agents locally for testing or invoke published agents in UiPath Cloud.

## Commands

```bash
# Run locally — ENTRYPOINT is the name from entry-points.json, NOT the project name
uip codedagent run <ENTRYPOINT> '{"query": "test"}'

# Run with file input
uip codedagent run <ENTRYPOINT> --input-file input.json

# Interactive dev loop (prompts for input, hot-reloads on changes)
uip codedagent dev

# Invoke published agent in cloud
uip codedagent invoke <ENTRYPOINT> '{"query": "test"}'
```

Use an entrypoint from `entry-points.json`, not the project or package name. Run `uip codedagent init` to consolidate framework configuration into the authoritative entrypoint list:

| Framework | Source of truth | Key |
|---|---|---|
| Coded Function | `uipath.json` | `functions` |
| LangGraph | `langgraph.json` | `graphs` |
| LlamaIndex | `llama_index.json` | `workflows` |
| OpenAI Agents | `openai_agents.json` | `agents` |

## Choose a Mode

| Mode | Use when | Command |
|---|---|---|
| Run | One-shot local execution for CI, scripted tests, or one-off checks | `uip codedagent run <ENTRYPOINT> '<input>'` |
| Dev | Active development or debugging with interactive hot reload | `uip codedagent dev` |
| Invoke | Executing a deployed agent in UiPath Cloud after `uip codedagent deploy` | `uip codedagent invoke <ENTRYPOINT> '<input>'` |

`uip codedagent dev` always runs interactively because the wrapper appends `--interactive`; use it for REPL-style work, not non-interactive scripts.

## Prerequisites

- Ensure `entry-points.json` exists; run `uip codedagent init` if needed.
- For `invoke`, publish the agent and authenticate with an active session.

## Run Locally

Run `uip codedagent run <ENTRYPOINT> '<json-input>'` to execute an entrypoint once. If multiple entrypoints exist, the CLI prompts for selection. Make the JSON conform to the selected entrypoint's input schema, or run `uip codedagent run <ENTRYPOINT> --input-file input.json` for file input. The CLI prints formatted results; execution traces are collected automatically and can be viewed in UiPath Cloud.

## Invoke in Cloud

```bash
uip codedagent invoke <ENTRYPOINT> '<json-input>'
```

- `<ENTRYPOINT>` is an entrypoint path; omit it to use the first entrypoint.
- `<json-input>` must match the entrypoint schema; omit it to use `{}`.

The CLI reads the project name and version from `pyproject.toml`, looks up the published release in the UiPath workspace, starts a cloud job, and returns a monitoring URL. `invoke` is asynchronous: open the URL to view job status, logs, and results. There is no `--wait` flag.

## Troubleshooting

| Error | Cause | Solution |
|---|---|---|
| `Authorization required` / missing session | Not authenticated | Run `uip login` — see [authentication](../../authentication.md) |
| `UIPATH_ORGANIZATION_ID...is required` | Missing org ID environment variable (OpenAI Agents only) | Ensure a valid `uip login` session; the wrapper injects org ID automatically |
| `Invalid input` | JSON does not match the input schema | Check `entry-points.json` for expected fields and types |
| `Error during initialization: File not found: main` | `main.py` is missing or not in the project root | Create `main.py` in the project root |

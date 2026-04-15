# Run UiPath Agents

Execute agents locally for testing or invoke published agents in UiPath Cloud.

## Quick Reference

```bash
# Run locally — ENTRYPOINT is the name from entry-points.json, NOT the project name
uip codedagent run <ENTRYPOINT> '{"query": "test"}'

# Run with file input
uip codedagent run <ENTRYPOINT> --file input.json

# Interactive dev loop (prompts for input, hot-reloads on changes)
uip codedagent dev

# Invoke published agent in cloud
uip codedagent invoke <ENTRYPOINT> '{"query": "test"}'
```

The entrypoint name comes from `entry-points.json` (e.g., `main`, `agent`) — not the project or package name. Each framework seeds that name from its own config file:

| Framework | Source of truth | Key in the file |
|---|---|---|
| Coded Function | `uipath.json` | `functions` |
| LangGraph | `langgraph.json` | `graphs` |
| LlamaIndex | `llama_index.json` | `workflows` |
| OpenAI Agents | `openai_agents.json` | `agents` |

`uip codedagent init` consolidates these into `entry-points.json` — the authoritative list to pick from.

## Prerequisites

- `entry-points.json` exists (run `uip codedagent init`).
- For `invoke`: the agent is published and an authenticated session is active.

## Run vs Dev vs Invoke

| Aspect | Run (one-shot local) | Dev (interactive local) | Invoke (Cloud) |
|--------|---|---|---|
| Purpose | Execute once with a given input | Iterate on the agent with hot-reload and prompted input | Execute a deployed agent in UiPath Cloud |
| Location | Your machine | Your machine | UiPath Cloud workspace |
| When to use | CI, scripted tests, one-off checks | Active development / debugging | After `uip codedagent deploy` |
| Command | `uip codedagent run <ENTRYPOINT> '<input>'` | `uip codedagent dev` | `uip codedagent invoke <ENTRYPOINT> '<input>'` |

`uip codedagent dev` always runs interactively (the wrapper appends `--interactive` automatically) — use it for REPL-style work, not inside non-interactive scripts.

## Run (Local)

Reads `entry-points.json` to discover available entrypoints and their schemas. If multiple exist, prompts for selection. JSON input must conform to the selected entrypoint's input schema.

Results are printed as a formatted panel:

```
EXECUTION RESULTS
═══════════════════════════════════════════════════════════

Status:           ✅ SUCCESS
Execution Time:   0.45 seconds
Agent:            my-agent (agent.py:run)
Input:            {"action": "process", "data": "sample"}

OUTPUT:
{
  "status": "completed",
  "result": "processed successfully"
}
```

Execution traces are collected automatically and can be viewed in UiPath Cloud.

## Invoke (Cloud)

```bash
uip codedagent invoke <ENTRYPOINT> '<json-input>'
```

- `<ENTRYPOINT>` — entrypoint path (optional; defaults to the first entrypoint)
- `<json-input>` — JSON input matching the entrypoint's schema (default `{}`)

The CLI reads project name and version from `pyproject.toml`, looks up the published release in your UiPath workspace, starts a cloud job with the provided input, and returns a monitoring URL.

`invoke` is **asynchronous** — the command returns immediately with a monitoring URL. Open it to see the job's status, logs, and results. There is no `--wait` flag.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Authorization required. Please run uipath auth` | Not authenticated | Run `uip login` — see [authentication](../../authentication.md) |
| `UIPATH_ORGANIZATION_ID...is required` | Missing org ID env variable (OpenAI Agents only) | Ensure a valid `uip login` session; the wrapper injects org ID automatically |
| `Invalid input` | JSON doesn't match the input schema | Check `entry-points.json` for expected fields and types |
| `Error during initialization: File not found: main` | `main.py` missing or not in project root | Create `main.py` in the project root |

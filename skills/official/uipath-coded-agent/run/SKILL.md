---
name: run
description: Run UiPath coded agents locally or invoke published agents in the cloud. Handles agent discovery, schema-driven input, execution, and result display. Use when the user says "run my agent", "test the agent locally", "execute the agent", or "invoke my published agent".
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# Run UiPath Agents

Execute agents locally for testing or invoke published agents in UiPath Cloud.

## Quick Reference

```bash
# Run locally — ENTRYPOINT is the name from entry-points.json, NOT the project name
uv run uipath run <ENTRYPOINT> '{"query": "test"}'

# Run with file input
uv run uipath run <ENTRYPOINT> --file input.json

# Invoke published agent in cloud
uv run uipath invoke <ENTRYPOINT> '{"query": "test"}'
```

**IMPORTANT:** The entrypoint name comes from `entry-points.json` (e.g., `main`, `agent`). It is NOT the project or package name. Check `entry-points.json` for the correct name.

## Documentation

- **[Running Agents Guide](references/running-agents.md)** — Complete execution reference
  - Run vs Invoke comparison
  - Agent discovery from `entry-points.json`
  - Input collection and schema validation
  - Result display and error handling
  - Cloud execution with monitoring URLs

## Prerequisites

- `entry-points.json` must exist (run `uv run uipath init` if missing)
- For `invoke`: agent must be published and auth configured

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Authorization required. Please run uipath auth` | Not authenticated before running | Run `uv run uipath auth --cloud --tenant <TENANT>` first |
| `UIPATH_ORGANIZATION_ID...is required` | Missing org ID env variable (OpenAI Agents) | Ensure `.env` has `UIPATH_ORGANIZATION_ID` set after auth |
| `Invalid input` | JSON doesn't match Input schema | Check `entry-points.json` for expected fields and types |
| `Error during initialization: File not found: main` | `main.py` missing or not in project root | Create `main.py` in the project root directory |

## Additional Instructions

- Read the [running agents reference](references/running-agents.md) before making assumptions about run/invoke behavior.

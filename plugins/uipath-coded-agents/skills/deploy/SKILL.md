---
name: deploy
description: Deploy UiPath coded agents to Orchestrator. Handles packaging into .nupkg, publishing to feeds, the combined deploy command, and invoking published agents in the cloud. Use when the user says "deploy my agent", "publish to Orchestrator", "pack my agent", or "ship it to production".
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# Deploy UiPath Agents

Package, publish, and invoke your agents in UiPath Cloud.

## Quick Reference

```bash
# Pack + publish in one command
uv run uipath deploy --my-workspace

# Or step by step
uv run uipath pack
uv run uipath publish --my-workspace

# Invoke published agent — use entrypoint name from entry-points.json, NOT project name
uv run uipath invoke <ENTRYPOINT> '{"query": "test"}'
```

## Documentation

- **[Deployment Guide](references/deployment.md)** — Complete deployment workflow
  - `uipath pack` — Package into .nupkg with validation
  - `uipath publish` — Upload to Orchestrator feed (--my-workspace, --tenant, --folder)
  - `uipath deploy` — Combined pack + publish
  - `uipath invoke` — Execute published agents in cloud
  - Pack options (`packOptions` in `uipath.json`)
  - Configuration files and environment variables

## Prerequisites

- Authentication configured — if not authenticated, use the [Auth skill](/uipath-coded-agents:auth) first
- `entry-points.json` exists (run `uv run uipath init`)
- `pyproject.toml` has `name`, `version`, `description`, `authors`

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Project authors cannot be empty` | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` section |
| `Pack failed: missing fields` | `pyproject.toml` incomplete | Ensure `name`, `version`, `description`, and `authors` are all set |
| `Version already exists` | Same version already published | Bump the patch version in `pyproject.toml` before re-deploying |
| `401 Unauthorized` | Auth expired or not configured | Re-run `uv run uipath auth --cloud --tenant <TENANT>` |

## Additional Instructions

- Read the [deployment reference](references/deployment.md) for details on pack options and feed selection.
- Always test locally with `uv run uipath run <ENTRYPOINT>` before deploying.

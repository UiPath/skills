---
description: Deploy UiPath coded agents to Orchestrator - pack, publish, and invoke
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# Deploying UiPath Agents

Deploy your UiPath coded agents to the cloud with pack, publish, and invoke commands.

## Documentation

- **[Deployment Guide](references/deployment.md)** - Complete deployment workflow
  - `uipath pack` - Package into .nupkg
  - `uipath publish` - Upload to Orchestrator feed
  - `uipath deploy` - Pack + publish in one step
  - `uipath invoke` - Execute published agents
  - Configuration and environment variables

## Workflow Commands

1. **[Authenticate](/uipath-coded-agents:authentication)** with UiPath

2. **Pack** your project into a `.nupkg` file:
   ```bash
   uv run uipath pack
   ```

3. **Publish** to a UiPath feed:
   ```bash
   uv run uipath publish --my-workspace
   ```

4. Or use **Deploy** (shorthand for pack + publish):
   ```bash
   uv run uipath deploy --my-workspace
   ```

5. **Invoke** the published agent:
   ```bash
   uv run uipath invoke <entrypoint> '<json-input>'
   ```

> **Note:** You must learn how to use `run` and `invoke` commands in detail, refer to [Execute Agents](/uipath-coded-agents:execute), before executing agents locally (run) or on cloud (invoke).

## Next Steps

- **Building your first agent?** See [Building Agents](/uipath-coded-agents:build)
- **Need help with authentication?** See [Authentication Setup](/uipath-coded-agents:authentication)
- **Want to test before deploying?** See [Running Agents](/uipath-coded-agents:execute) and [Evaluating Agents](/uipath-coded-agents:evaluate)

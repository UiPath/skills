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

## Quick Start

```bash
# 1. Authenticate with UiPath
uv run uipath auth --alpha

# 2. Deploy to personal workspace
uv run uipath deploy --my-workspace

# 3. Invoke the published agent
uv run uipath invoke main '{"query": "What is UiPath?"}'
```

## Workflow Commands

### Pack
Package your project into a `.nupkg` file:
```bash
uv run uipath pack
```

### Publish
Upload a packaged project to a UiPath feed:
```bash
uv run uipath publish --my-workspace
```

### Deploy
Shorthand for pack + publish:
```bash
uv run uipath deploy --my-workspace
```

### Invoke
Execute a published agent:
```bash
uv run uipath invoke main '{"query": "test"}'
```

## Next Steps

- **Building your first agent?** See [Building Agents](/uipath-coded-agents:build)
- **Need help with authentication?** See [Authentication Setup](/uipath-coded-agents:authentication)
- **Want to test before deploying?** See [Running Agents](/uipath-coded-agents:execute) and [Evaluating Agents](/uipath-coded-agents:evaluate)
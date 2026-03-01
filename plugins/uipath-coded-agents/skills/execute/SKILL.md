---
description: Run UiPath coded agents with schema-driven inputs
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# Running UiPath Agents

Execute your UiPath coded agents with interactive input collection and result display.

## Documentation

- **[Running Agents Guide](references/running-agents.md)** - Execute your agents
  - Agent discovery and selection
  - Interactive input collection
  - Execution and result display
  - Error handling
  - Troubleshooting common issues

## Quick Start

1. Discover available agents in your project via `entry-points.json`
2. Collect inputs matching your agent's schema
3. Execute with `uv run uipath run <entrypoint> '<json-input>'`
4. View structured results

## Workflow

1. Set up authentication with [Authentication Setup](/uipath-coded-agents:authentication)
2. Create your agent with [Building Agents](/uipath-coded-agents:build)
3. Use this guide to run your agent
4. Test comprehensively with [Evaluating Agents](/uipath-coded-agents:evaluate)

## Additional Instructions
- If you are unsure about usage, read the linked running agents reference before making assumptions.

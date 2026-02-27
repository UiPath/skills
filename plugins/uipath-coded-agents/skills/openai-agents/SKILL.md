---
description: Build OpenAI Agents with tools, structured output, and handoffs
allowed-tools: Bash, Read, Write, Glob, Grep
---

# OpenAI Agents Integration

Build lightweight agents using OpenAI's Agents framework with tools and structured output.

## Overview

OpenAI Agents provides a streamlined framework for building agents with:
- Agent class from OpenAI SDK
- Tool definitions and automatic tool calling
- Structured output with Pydantic models
- Handoff patterns for multi-agent workflows
- Integration with UiPath platform services

## Documentation

- **[OpenAI Agents Integration Guide](references/openai-agents-integration.md)** - Complete integration guide
  - Project scaffolding and structure
  - `openai_agents.json` configuration
  - Tool definition patterns
  - Structured output setup
  - Handoff implementation
  - Common patterns and pitfalls

## Quick Start

```bash
# Scaffold a new OpenAI Agents project
mkdir my-agent && cd my-agent
uv run uipath new my-agent
```

This generates:
- `main.py` with an Agent + tool template
- `openai_agents.json` configuration
- `AGENTS.md` documentation
- `pyproject.toml` with dependencies

## Key Points

- Requires `uipath-openai-agents` dependency
- Uses `openai_agents.json` for configuration (not `uipath.json`)
- Lightweight and focused on agent execution
- Supports tool calling and structured output
- Integrates with UiPath services
- Note: Does not support Human-in-the-Loop or state persistence — use LangGraph/LlamaIndex for those features

## Workflow

1. See [Building Agents](/uipath-coded-agents:build) for project setup
2. Read [OpenAI Agents Integration Guide](references/openai-agents-integration.md) for structure and patterns
3. Define your Agent with tools
4. Configure tool handlers and structured output
5. Test with [Running Agents](/uipath-coded-agents:execute)
6. Evaluate with [Evaluating Agents](/uipath-coded-agents:evaluate)

## Next Steps

- Ready to build? See [Building Agents](/uipath-coded-agents:build)
- Need help running your agent? See [Executing Agents](/uipath-coded-agents:execute)

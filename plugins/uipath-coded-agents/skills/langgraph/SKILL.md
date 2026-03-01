---
description: Build LangGraph agents with StateGraph, conditional routing, and UiPath integration
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# LangGraph Integration

Build multi-step agents using LangGraph's StateGraph with nodes, edges, and conditional routing.

## Documentation

- **[LangGraph Integration Guide](references/langgraph-integration.md)** - Complete integration guide
  - Project scaffolding and structure
  - `langgraph.json` configuration
  - Node definitions and edges
  - LLM model configuration
  - Tracing and debugging
  - Common patterns and pitfalls

## Quick Start

```bash
# Scaffold a new LangGraph agent
mkdir my-agent && cd my-agent
uv run uipath new my-agent
```

This generates:
- `main.py` with a StateGraph template
- `langgraph.json` configuration
- `pyproject.toml` with dependencies

## Key Points

- Requires `uipath-langchain` dependency
- Uses `langgraph.json` for configuration (not `uipath.json`)
- StateGraph for defining workflows with nodes, edges, and conditional routing
- Supports stateful workflows with checkpointing
- Integrates with UiPath services via UiPathAzureChatOpenAI
- Automatic tracing for Orchestrator observability

## Workflow

1. See [Building Agents](/uipath-coded-agents:build) for project setup
2. Read [LangGraph Integration Guide](references/langgraph-integration.md) for structure and patterns
3. Define your StateGraph with nodes and edges
4. Use conditional routing for multi-step logic
5. Test with [Running Agents](/uipath-coded-agents:execute)
6. Evaluate with [Evaluating Agents](/uipath-coded-agents:evaluate)

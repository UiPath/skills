---
description: Build LlamaIndex agents with Workflow, events, and RAG support
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# LlamaIndex Integration

Build event-driven agents using LlamaIndex's Workflow with RAG and tool integration support.

## Documentation

- **[LlamaIndex Integration Guide](references/llamaindex-integration.md)** - Complete integration guide
  - Project scaffolding and structure
  - `llama_index.json` configuration
  - Workflow patterns and events
  - RAG setup and configuration
  - LLM model configuration
  - Common patterns and pitfalls

## Quick Start

```bash
# Scaffold a new LlamaIndex agent
mkdir my-agent && cd my-agent
uv run uipath new my-agent
```

This generates:
- `main.py` with a Workflow template
- `llama_index.json` configuration
- `pyproject.toml` with dependencies

## Key Points

- Requires `uipath-llamaindex` dependency
- Uses `llama_index.json` for configuration (not `uipath.json`)
- Event-driven architecture with Workflow class, StartEvent/StopEvent
- Built-in RAG support with vector stores
- Integrates with UiPath services via UiPathOpenAI
- Automatic tracing for Orchestrator observability

## Workflow

1. See [Building Agents](/uipath-coded-agents:build) for project setup
2. Read [LlamaIndex Integration Guide](references/llamaindex-integration.md) for structure and patterns
3. Define your Workflow with events and handlers
4. Configure RAG if using retrieval
5. Test with [Running Agents](/uipath-coded-agents:execute)
6. Evaluate with [Evaluating Agents](/uipath-coded-agents:evaluate)

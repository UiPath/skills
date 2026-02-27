---
description: Build UiPath coded agents with Pydantic models and tracing
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# Building UiPath Agents

Create robust, type-safe UiPath coded agents with monitoring and observability built-in.

## Overview

Learn how to build agents with:
- Type-safe agent definitions using Pydantic models
- Project setup with pyproject.toml
- Automatic tracing for monitoring and debugging
- Integration with UiPath Orchestrator

## Documentation

### Project Setup
- **[Project Setup Guide](references/setup.md)** - Set up new or existing agent projects
  - Prerequisites and environment setup
  - Choose your agent type (Simple, LangGraph, LlamaIndex, OpenAI)
  - Create and scaffold projects
  - Configure dependencies

### Framework-Specific Guides
For detailed integration guides, see the dedicated skills:
- **[LangGraph Integration](/uipath-coded-agents:langgraph)** - Multi-step agents with StateGraph
- **[LlamaIndex Integration](/uipath-coded-agents:llamaindex)** - Event-driven agents with RAG
- **[OpenAI Agents Integration](/uipath-coded-agents:openai-agents)** - Lightweight tool-using agents

### Agent Patterns
- **[Agent Patterns](references/agent-patterns.md)** - Common implementation patterns
  - Simple Direct Agent
  - SDK Integration Agent
  - LangGraph Workflow Agent
  - Human-in-the-Loop Agent
  - RAG Agent
  - Chat Agent
  - Multi-Agent Supervisor

### SDK Services
- **[SDK Services Reference](references/sdk-services.md)** - Full API reference
  - SDK initialization
  - All available platform services
  - Async usage patterns
  - Error handling

### Monitoring & Tracing
- **[Tracing Guide](references/tracing.md)** - Add monitoring and debugging
  - Basic tracing with `@traced()` decorator
  - Custom span names and run types
  - Data protection and privacy
  - Integration patterns
  - Common use cases
  - Viewing traces in Orchestrator

## Quick Start Template

A template `pyproject.toml` is available in the assets to help you bootstrap your project:
- Dependencies configuration
- Package metadata
- Build system setup

## Post-Init Cleanup

After running `uv run uipath init`, you'll see generated `CLAUDE.md`, `.claude` and `.agent/` files. Since the plugin provides comprehensive documentation, you can safely delete these:

Therefore, this is the only acceptable way to run init:
```
`uv run uipath init && rm CLAUDE.md && rm -rf .agent .claude`
```

## Workflow

1. Set up your project with [Project Setup](references/setup.md)
2. Review [Agent Patterns](references/agent-patterns.md) for common patterns and use cases
3. Define your input and output schemas using Pydantic models
4. Implement your agent logic (refer to [SDK Services](references/sdk-services.md) for API reference)
5. Add tracing with `@traced()` decorator for monitoring
6. Test your agent with [Running Agents](/uipath-coded-agents:execute)

## Next Steps

- Ready to run your agent? See [Executing Agents](/uipath-coded-agents:execute)
- Want to test your agent? See [Evaluating Agents](/uipath-coded-agents:evaluate)

## Additional Instructions
- You MUST ALWAYS read the relevant linked references before making assumptions!

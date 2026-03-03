---
description: Build UiPath LangGraph agents with LLMs, process invocation, conditional routing, interrupts, human-in-the-loop, and RAG
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# LangGraph Integration

Build multi-step agents using LangGraph's StateGraph with nodes, edges, and conditional routing.

## Find Your Guide

**Trying to...?**
- 📋 **Build a new agent** → [LangGraph Integration Guide](references/langgraph-integration.md)
- 🔄 **Invoke external processes/jobs/tools (RPA, APIs)** → [Process Invocation Guide](references/process-invocation.md)
- ⏸️ **Pause agent, wait for user input** → [Interrupt and Resume Patterns](references/interrupt-resume.md)
- 👤 **Escalate to Action Center for approval** → [Human-in-the-Loop Guide](references/human-in-the-loop.md)
- 📚 **Use organization data in responses** → [Context Grounding Guide](references/context-grounding.md)

## Documentation

- **[LangGraph Integration Guide](references/langgraph-integration.md)** - Complete integration guide
  - Project scaffolding and structure
  - `langgraph.json` configuration
  - Node definitions and edges
  - LLM models: UiPathAzureChatOpenAI, UiPathChat, supported models, and configuration
  - Structured output with Pydantic schemas
  - Tracing and debugging
  - Common patterns and pitfalls

- **[Context Grounding Guide](references/context-grounding.md)** - Ground LLM responses in organization data
  - Index creation in Orchestrator
  - ContextGroundingRetriever for document search
  - ContextGroundingVectorStore for semantic search
  - RAG (Retrieval-Augmented Generation) patterns
  - Agent integration examples

- **[Interrupt and Resume Patterns](references/interrupt-resume.md)** - Understanding agent pause/resume mechanism
  - How interrupts work in LangGraph
  - Choosing the right interrupt model
  - Design principles and best practices
  - Common workflows and patterns
  - Advanced scenarios

- **[Human-in-the-Loop Guide](references/human-in-the-loop.md)** - Pause execution for human intervention
  - Escalation to Action Center with CreateTask
  - Waiting for task completion with WaitTask
  - Multi-step approval workflows
  - Exception handling and escalation patterns

- **[Process Invocation Guide](references/process-invocation.md)** - Delegate work to external processes
  - InvokeProcess for external RPA automation
  - WaitJob for monitoring external jobs
  - Data processing pipelines
  - Agent-in-the-loop and parallel execution patterns
  - Conditional process routing based on agent logic

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

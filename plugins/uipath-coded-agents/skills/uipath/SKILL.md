---
description: UiPath Coded Agents assistant - Create, run, evaluate and deploy coded agents
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# UiPath Coded Agents Assistant

## CRITICAL RULES

- **NEVER add a `[build-system]` section to `pyproject.toml`**. No `hatchling`, no `setuptools`, no build backend. UiPath agents do not use a build system. Adding one causes `uv sync` to fail. Only include `[project]`, `[dependency-groups]`, and `[tool.*]` sections.
- **Always create a smoke evaluation set.** Every agent must include `evaluations/eval-sets/smoke-test.json` with 2-3 basic test cases covering the happy path. This is a required step, not optional.

## Features

- **Type Safety**: Pydantic models ensure type-safe agent definitions
- **Automatic Tracing**: Monitor agent execution with `@traced()` decorator
- **Schema-Driven**: JSON schemas automatically generated from Pydantic models
- **Cloud Integration**: Seamless integration with UiPath Cloud Platform
- **Evaluation Framework**: Comprehensive testing with multiple evaluator types
- **Privacy**: Data redaction and sensitive field hiding

## Documentation

The UiPath Coded Agents system is organized into focused skills:

### Getting Started

- **[Authentication Setup](/uipath-coded-agents:authentication)** - Authenticate with UiPath Cloud or on-premise
  - Interactive OAuth authentication
  - Unattended client credentials flow
  - Environment configuration
  - Network settings

- **[Project Setup](/uipath-coded-agents:build)** - Set up new or existing agent projects
  - Prerequisites (Python 3.11+, uv)
  - pyproject.toml configuration
  - Agent project structure
  - Choosing your framework

### Building Agents

- **[Project Setup & Patterns](/uipath-coded-agents:build)** - Agent development fundamentals
  - Project initialization and structure
  - Schema definition with Pydantic models
  - Agent patterns (Simple, SDK Integration, LangGraph, RAG, Chat, Multi-Agent)
  - Tracing and monitoring

- **Framework-Specific Guides** - Choose based on your needs:
  - **[LangGraph Agents](/uipath-coded-agents:langgraph)** - Multi-step workflows with conditional routing
  - **[LlamaIndex Agents](/uipath-coded-agents:llamaindex)** - Event-driven agents with RAG support
  - **[OpenAI Agents](/uipath-coded-agents:openai-agents)** - Lightweight tool-using agents

- **[SDK Services](/uipath-coded-agents:build)** - UiPath platform capabilities
  - Processes, Jobs, Assets, Queues
  - Attachments, Buckets, Context Grounding
  - Documents, Entities, Connections
  - LLM Gateway, Guardrails

### Running Agents

- **[Executing Agents](/uipath-coded-agents:execute)** - Run your agents
  - Agent discovery and selection
  - Interactive input collection
  - Execution and result display
  - Error handling

### Syncing Files

- **[File Synchronization](/uipath-coded-agents:file-sync)** - Sync project files to remote storage
  - `uipath push` - Upload local files to remote
  - `uipath pull` - Download remote files to local
  - Bidirectional synchronization
  - Conflict resolution and overwrites

### Testing & Evaluation

- **[Evaluating Agents](/uipath-coded-agents:evaluate)** - Design and run comprehensive tests
  - Output-based evaluators (ExactMatch, JsonSimilarity, LLMJudge, Contains)
  - Trajectory-based evaluators
  - Test case organization
  - Mocking external dependencies
  - Evaluation best practices by agent type

### Deployment

- **[Deployment](/uipath-coded-agents:deploy)** - Deploy your agents
  - `uipath pack` - Package into .nupkg
  - `uipath publish` - Upload to Orchestrator feed
  - `uipath deploy` - Pack + publish in one step
  - `uipath invoke` - Execute published agents
  - Configuration and environment variables

## Framework Selection

When the user asks to create an agent **without specifying which framework/integration to use**, you MUST ask them to choose before proceeding. Present these options:

1. **Simple Function** — No framework, plain Python function with `Input`/`Output` models. Best for deterministic logic, SDK calls, no LLM needed.
2. **LangGraph** — Multi-step workflows with conditional routing, tool use, parallel execution. Best for complex LLM agents.
3. **LlamaIndex** — Workflow-based agents with RAG, FunctionAgent, Context Grounding. Best for knowledge retrieval and document Q&A.
4. **OpenAI Agents** — Lightweight agent framework with tools, handoffs, structured output. Best for simple LLM agents and multi-agent triage.

**Do NOT default to any framework.** Wait for the user's choice, then read the corresponding integration guide.

## Resources

- **UiPath Python SDK Documentation**: https://uipath.github.io/uipath-python/
- **UiPath Platform**: https://www.uipath.com/
- **Community**: Get help and share feedback with the UiPath community

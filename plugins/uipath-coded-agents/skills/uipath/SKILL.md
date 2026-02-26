---
description: UiPath Coded Agents assistant - Create, run, and evaluate coded agents
allowed-tools: Bash, Read, Write, Glob, Grep
user-invocable: true
---

# UiPath Coded Agents Assistant

## CRITICAL RULES

- **NEVER add a `[build-system]` section to `pyproject.toml`**. No `hatchling`, no `setuptools`, no build backend. UiPath agents do not use a build system. Adding one causes `uv sync` to fail. Only include `[project]`, `[dependency-groups]`, and `[tool.*]` sections.
- **Always create a smoke evaluation set.** Every agent must include `evaluations/eval-sets/smoke-test.json` with 2-3 basic test cases covering the happy path. This is a required step, not optional.

Welcome to the UiPath Coded Agents Assistant! This comprehensive guide helps you create, run, and evaluate UiPath coded agents using the UiPath Python SDK.

## Overview

The UiPath Coded Agents enables you to build intelligent automation agents with:
- **Type-safe agent definitions** using Pydantic models
- **Automatic tracing** for monitoring and debugging
- **Comprehensive testing** through evaluations
- **Cloud integration** with UiPath Orchestrator

## Documentation

### Getting Started

Begin your agent development journey with these foundational topics:

- **[Project Setup](references/setup.md)** - Set up a new agent project
  - Prerequisites (Python 3.11+, uv)
  - pyproject.toml configuration
  - Running `uipath init`
  - uipath.json structure
  - Project structure overview

- **[Authentication](references/authentication.md)** - Authenticate with UiPath
  - **Always use `--tenant TENANT_NAME`** on the final auth call. If the user hasn't specified a tenant: (1) run `uv run uipath auth --cloud` first — it opens the browser for login then prints the tenant list and hangs at "Select tenant number:"; (2) cancel the command, parse the tenant names, present them to the user; (3) after the user picks one, run `uv run uipath auth --cloud --tenant SELECTED_TENANT`.
  - Interactive OAuth authentication
  - Unattended client credentials flow
  - Environment configuration
  - Network settings

### Building Agents

Develop new agents with monitoring and observability built-in:

- **[Creating Agents](references/creating-agents.md)** - Build new agents
  - Project setup with pyproject.toml
  - Schema definition with Pydantic models
  - Agent implementation
  - Entry point generation

- **[LangGraph Integration](references/langgraph-integration.md)** - Build LangGraph agents for UiPath
  - Project structure (`langgraph.json` vs `uipath.json` functions)
  - Required dependencies (`uipath-langchain`)
  - UiPath LLM models (`UiPathAzureChatOpenAI`, `UiPathChat`)
  - Entrypoint detection and troubleshooting
  - Complete examples (minimal, LLM + tools, chat agent)

- **[LlamaIndex Integration](references/llamaindex-integration.md)** - Build LlamaIndex agents for UiPath
  - Project structure (`llama_index.json`, Workflow class)
  - Required dependencies (`uipath-llamaindex`)
  - UiPath LLM models (`UiPathOpenAI`)
  - StartEvent/StopEvent input/output patterns
  - Context Grounding (RAG), HITL, process invocation
  - Complete examples (workflow, FunctionAgent)

- **[OpenAI Agents Integration](references/openai-agents-integration.md)** - Build OpenAI Agents for UiPath (lightweight)
  - Project structure (`openai_agents.json`, Agent class)
  - Required dependencies (`uipath-openai-agents`)
  - UiPath LLM models (`UiPathChatOpenAI`)
  - Agent patterns (tools, structured output, handoffs, context)
  - Complete examples (simple, tools, multi-agent triage)

- **[Tracing](references/tracing.md)** - Add monitoring and debugging
  - Basic tracing with `@traced()` decorator
  - Custom span names and run types
  - Data protection and privacy
  - Integration patterns
  - Common use cases
  - Viewing traces in Orchestrator

- **[Agent Patterns](references/agent-patterns.md)** - Implementation patterns by agent type
  - Simple Direct, SDK Integration, LangGraph Workflow
  - Human-in-the-Loop, RAG, Chat, Multi-Agent Supervisor
  - Common building blocks and code examples

### Platform Services

Access UiPath platform capabilities from your agent code:

- **[SDK Services](references/sdk-services.md)** - UiPath SDK API reference
  - Processes, Jobs, Assets, Queues
  - Attachments, Buckets, Context Grounding
  - Documents, Entities, Connections
  - LLM Gateway, Guardrails
  - Sync/async patterns and folder targeting

### Running Agents

Execute and test your agents:

- **[Running Agents](references/running-agents.md)** - Execute your agents
  - Agent discovery and selection
  - Interactive input collection
  - Execution and result display
  - Error handling

### Deployment

Package and publish your agents to UiPath Cloud:

- **[Deployment](references/deployment.md)** - Deploy your agents
  - `uipath pack` - Package into .nupkg
  - `uipath publish` - Upload to Orchestrator feed
  - `uipath deploy` - Pack + publish in one step
  - `uipath invoke` - Execute published agents
  - Configuration and environment variables

### Testing & Evaluation

Ensure your agents work correctly with evaluations:

- **[Evaluations](references/evaluations.md)** - Create and run evaluations
  - Output-based evaluators for result validation
  - Trajectory-based evaluators for execution flow analysis
  - Test case organization
  - Mocking external dependencies

- **[Creating Evaluations](references/evaluations/creating-evaluations.md)** - Design test cases
  - Define evaluation scenarios
  - Collect test inputs and expected outputs
  - Organize by scenario type
  - Schema validation

- **[Evaluators Guide](references/evaluations/evaluators/README.md)** - Understand evaluator types
  - Output-based evaluators (ExactMatch, JsonSimilarity, LLMJudgeOutput, Contains)
  - Trajectory-based evaluators (Trajectory)
  - Custom evaluators
  - Evaluator selection guide

- **[Evaluation Sets](references/evaluations/evaluation-sets.md)** - Structure your tests
  - Evaluation set file format
  - Test case schema
  - Mocking strategies
  - Complete examples

- **[Running Evaluations](references/evaluations/running-evaluations.md)** - Execute and analyze
  - Running test suites
  - Understanding results
  - Performance analysis
  - Troubleshooting

- **[Best Practices](references/evaluations/best-practices.md)** - Evaluation patterns
  - Best practices for evaluation design
  - Common patterns by agent type:
    - Calculator/Deterministic agents
    - Natural language agents
    - Multi-step orchestration agents
    - API integration agents
  - Test organization strategies
  - Performance optimization

## Quick Patterns

### Implementation Patterns
Choose the right architecture for your agent:
- **Simple Direct** — Deterministic logic, no LLM calls → [Pattern](references/agent-patterns.md#simple-direct-agent)
- **SDK Integration** — Platform service calls (assets, queues, jobs) → [Pattern](references/agent-patterns.md#sdk-integration-agent)
- **LangGraph Workflow** — Multi-step LLM reasoning with routing → [Pattern](references/agent-patterns.md#langgraph-workflow-agent)
- **Human-in-the-Loop** — Approval flows with Action Center → [Pattern](references/agent-patterns.md#human-in-the-loop-agent)
- **RAG** — Knowledge retrieval and Q&A → [Pattern](references/agent-patterns.md#rag-agent)
- **Chat** — Conversational agents with tools → [Pattern](references/agent-patterns.md#chat-agent)
- **Multi-Agent Supervisor** — Specialized sub-agents with routing → [Pattern](references/agent-patterns.md#multi-agent-supervisor)

See [Agent Patterns](references/agent-patterns.md) for full code examples.

### Evaluation Patterns
Match your evaluation strategy to your agent type:
- **Calculator/Deterministic** — ExactMatch evaluators → [Best Practices](references/evaluations/best-practices.md#pattern-1-calculatordeterministic-agents)
- **Natural Language** — LLMJudge + Contains evaluators → [Best Practices](references/evaluations/best-practices.md#pattern-2-natural-language-agents)
- **Multi-Step Orchestration** — Trajectory + JsonSimilarity → [Best Practices](references/evaluations/best-practices.md#pattern-3-multi-step-orchestration-agents)
- **API Integration** — JsonSimilarity + ExactMatch → [Best Practices](references/evaluations/best-practices.md#pattern-4-api-integration-agents)

## Coded Agents Features

- **Type Safety**: Pydantic models ensure type-safe agent definitions
- **Automatic Tracing**: Monitor agent execution with `@traced()` decorator
- **Schema-Driven**: JSON schemas automatically generated from Pydantic models
- **Cloud Integration**: Seamless integration with UiPath Cloud Platform
- **Evaluation Framework**: Comprehensive testing with multiple evaluator types
- **Privacy**: Data redaction and sensitive field hiding

## Framework Selection

When the user asks to create an agent **without specifying which framework/integration to use**, you MUST ask them to choose before proceeding. Present these options:

1. **Simple Function** — No framework, plain Python function with `Input`/`Output` models. Best for deterministic logic, SDK calls, no LLM needed.
2. **LangGraph** — Multi-step workflows with conditional routing, tool use, parallel execution. Best for complex LLM agents.
3. **LlamaIndex** — Workflow-based agents with RAG, FunctionAgent, Context Grounding. Best for knowledge retrieval and document Q&A.
4. **OpenAI Agents** — Lightweight agent framework with tools, handoffs, structured output. Best for simple LLM agents and multi-agent triage.

**Do NOT default to any framework.** Wait for the user's choice, then read the corresponding integration guide.

## Key Concepts

### Agents
Agents are reusable automation components that:
- Have well-defined input and output schemas
- Execute in the UiPath cloud or on-premise
- Are monitored and traced automatically
- Can be tested with evaluations

### Evaluators
Evaluators validate agent behavior:
- **Output-Based**: Validate what the agent returns
- **Trajectory-Based**: Validate how the agent executes
- **Custom**: Implement domain-specific logic

### Evaluations
Evaluations are test suites that:
- Define test cases with inputs and expected outputs
- Use evaluators to score agent performance
- Support mocking external dependencies
- Track performance metrics

## Resources

- **UiPath Python SDK Documentation**: https://uipath.github.io/uipath-python/
- **UiPath Platform**: https://www.uipath.com/
- **Community**: Get help and share feedback with the UiPath community

## Next Steps

1. **Getting started?**
   - See [Project Setup](references/setup.md) for prerequisites and project initialization
   - See [Authentication](references/authentication.md) for connecting to UiPath

2. **Building your first agent?**
   - Start with [Creating Agents](references/creating-agents.md)
   - Browse [Agent Patterns](references/agent-patterns.md) to pick the right architecture
   - Use [SDK Services](references/sdk-services.md) to call platform APIs
   - Learn about [Tracing](references/tracing.md) to add monitoring
   - Then run your first agent using [Running Agents](references/running-agents.md)

3. **Testing your agents?**
   - Start with [Creating Evaluations](references/evaluations/creating-evaluations.md)
   - Review [Best Practices](references/evaluations/best-practices.md) for your agent type
   - Run evaluations with [Running Evaluations](references/evaluations/running-evaluations.md)

4. **Deploying to the cloud?**
   - See [Deployment](references/deployment.md) for pack, publish, and invoke workflows

# Instructions for Reading References

- **Read references directly** using the Read tool — do NOT use Task or Explore agents to read them. This avoids duplicate reads.
- **Read only what you need** based on the user's request:
  - Creating a simple (non-LLM) agent? Read: `setup.md`, `creating-agents.md`
  - Creating a LangGraph agent? Read: `langgraph-integration.md` (self-contained — covers project setup, deps, patterns, examples)
  - Creating a LlamaIndex agent? Read: `llamaindex-integration.md` (self-contained)
  - Creating an OpenAI Agents agent? Read: `openai-agents-integration.md` (self-contained)
  - Need UiPath SDK calls in any agent? Read: `sdk-services.md`
  - Want architecture pattern examples (LangGraph)? Read: `agent-patterns.md`
  - Setting up evaluations? Read: `evaluations/creating-evaluations.md`, `evaluations/evaluation-sets.md`
- **Do not read all references upfront.** Read the 2-3 most relevant ones for the task, then proceed. You can always read more later if needed.
- **Do not re-read files** you have already read in this conversation.

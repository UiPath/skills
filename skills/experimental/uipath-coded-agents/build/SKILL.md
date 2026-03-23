---
name: build
description: Build UiPath coded agents with framework-specific patterns. Covers simple functions, LangGraph, LlamaIndex, and OpenAI Agents including SDK services, tracing, interrupts, RAG, and multi-agent orchestration. Use when the user has an existing project and says "implement the agent logic", "write the agent code", "add tools to my agent", or "modify the agent".
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# Build UiPath Agents

Implement agent logic using UiPath SDK and framework-specific patterns.

## Reference Lookup

Read **only** the reference matching the selected framework. Do NOT load other framework references.

| Framework | Reference |
|-----------|-----------|
| Simple Function | `references/simple-agents.md` + `references/agent-patterns.md` |
| LangGraph | `references/langgraph-integration.md` |
| LlamaIndex | `references/llamaindex-integration.md` |
| OpenAI Agents | `references/openai-agents-integration.md` |

Load capability references **only if the task requires them** — do not preload:

| Capability | Reference | Load when... |
|------------|-----------|-------------|
| RPA process invocation | `references/process-invocation.md` | agent invokes UiPath processes/jobs |
| Human approval / interrupt | `references/human-in-the-loop.md` | agent needs human-in-the-loop or pause/resume |
| RAG / context grounding | `references/context-grounding.md` | agent searches organization documents |
| Platform API calls | `references/sdk-services.md` | agent uses UiPath platform services directly |
| Tracing / monitoring | `references/tracing.md` | agent needs custom tracing (Simple Function only — LangGraph traces automatically) |

## Framework Reference

| Framework | Config File | Key Dependency | Entry Point |
|-----------|------------|----------------|-------------|
| Simple Function | `uipath.json` | `uipath` | `main.py` function |
| LangGraph | `langgraph.json` | `uipath-langchain` | `main.py` compiled StateGraph |
| LlamaIndex | `llama_index.json` | `uipath-llamaindex` | `main.py` Workflow instance |
| OpenAI Agents | `openai_agents.json` | `uipath-openai-agents` | `main.py` Agent instance |

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `'dict' has no attribute '...'` | `with_structured_output()` returns a dict, not a Pydantic model | Access results with `result['key']` dict syntax, not `result.key` attribute access |
| `ImportError: Could not import <package>` | External tool package not in `pyproject.toml` | Add all third-party tool packages to dependencies: `uv add <package>` |
| Agent returns empty output | Entry point not wired correctly | Verify `main.py` exports the correct object (compiled graph, Workflow, Agent) |
| `TypeError` on Input/Output | Schema mismatch after code change | Re-run `uv run uipath init` to regenerate `entry-points.json` |

## Additional Instructions

- **Select a framework before writing any code.** Infer from the prompt if possible (tools/orchestration → LangGraph, RAG → LlamaIndex, simple LLM → OpenAI Agents, no LLM → Simple Function). If ambiguous, ask the user to choose.
- **Read ONLY the single framework reference** for the selected framework before writing code. Do NOT read other framework references or capability references unless the task explicitly requires that capability.
- **NEVER instantiate LLM clients at module level.** `uipath init` imports your Python file to introspect schemas — module-level `UiPathAzureChatOpenAI()`, `UiPathChat()`, or `UiPathChatOpenAI()` will fail because auth may not have happened yet. Always create LLM instances inside functions or graph nodes, never at the top level of the module.
- LangGraph agents get tracing automatically — no `@traced()` needed on graph nodes.
- Simple function agents require `@traced()` on the `main` function.

# Build UiPath Agents

Implement agent logic using UiPath SDK and framework-specific patterns.

## Reference Lookup

Read **only** the reference matching the selected framework. Do NOT load other framework references.

| Framework | Reference |
|-----------|-----------|
| Simple Function | `../frameworks/simple-agents.md` + `../frameworks/agent-patterns.md` |
| LangGraph | `../frameworks/langgraph-integration.md` |
| LlamaIndex | `../frameworks/llamaindex-integration.md` |
| OpenAI Agents | `../frameworks/openai-agents-integration.md` |

Load capability references **only if the task requires them** — do not preload:

| Capability | Reference | Load when... |
|------------|-----------|-------------|
| RPA process invocation | `../capabilities/process-invocation.md` | agent invokes UiPath processes/jobs |
| Human approval / interrupt | `../capabilities/human-in-the-loop.md` | agent needs human-in-the-loop or pause/resume |
| RAG / context grounding | `../capabilities/context-grounding.md` | agent searches organization documents |
| Platform API calls | `../capabilities/sdk-services.md` | agent uses UiPath platform services directly |
| Tracing / monitoring | `../capabilities/tracing.md` | agent needs custom tracing (Simple Function only — LangGraph traces automatically) |

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
| `TypeError` on Input/Output | Schema mismatch after code change | Re-run `uip codedagent init` to regenerate `entry-points.json` |

## Additional Instructions

- **Select a framework before writing any code.** Infer from the prompt if possible (tools/orchestration → LangGraph, RAG → LlamaIndex, simple LLM → OpenAI Agents, no LLM → Simple Function). If ambiguous, ask the user to choose.
- **Read ONLY the single framework reference** for the selected framework before writing code. Do NOT read other framework references or capability references unless the task explicitly requires that capability.
- **NEVER instantiate LLM clients or SDK clients at module level.** `uip codedagent init` imports your Python file to introspect schemas — module-level `UiPathAzureChatOpenAI()`, `UiPathChat()`, `UiPathChatOpenAI()`, or `UiPath()` will fail because auth may not have happened yet. Always create these instances inside functions or graph nodes, never at the top level of the module.
- **Correct SDK import: `from uipath.platform import UiPath`** — not `from uipath import UiPath` (that does not exist). Instantiate inside functions only: `sdk = UiPath()`.
- LangGraph agents get tracing automatically — no `@traced()` needed on graph nodes.
- Simple function agents require `@traced()` on the `main` function.

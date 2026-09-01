# Build UiPath Agents

Implement agent logic with the UiPath SDK and framework-specific patterns.

## Reference Lookup

Select the framework before writing code. Infer it when possible: tools/orchestration → LangGraph, RAG → LlamaIndex, simple LLM → OpenAI Agents, and no LLM → Coded Function. If ambiguous, ask the user to choose.

Read **only** the reference matching the selected framework. Load capability references only when the task requires them.

| Framework | Reference |
|---|---|
| LangGraph | `../frameworks/langgraph-integration.md` |
| LlamaIndex | `../frameworks/llamaindex-integration.md` |
| OpenAI Agents | `../frameworks/openai-agents-integration.md` |

| Capability | Reference | Load when... |
|---|---|---|
| RPA process invocation | `../capabilities/process-invocation.md` | agent invokes UiPath processes/jobs |
| Human approval / interrupt | `../capabilities/human-in-the-loop.md` | agent needs human-in-the-loop or pause/resume |
| RAG / context grounding | `../capabilities/context-grounding.md` | agent searches organization documents |
| Platform API calls | `../capabilities/sdk-services.md` | agent uses UiPath platform services directly |
| Tracing / monitoring | `../capabilities/tracing.md` | agent needs custom tracing (Coded Function only — LangGraph traces automatically) |
| File attachments (input or created) | `../capabilities/file-attachments.md` | agent takes a file as input, or creates an attachment |
| Conversational (chat-style) agents | `../capabilities/conversational-agents.md` | agent receives one message per turn; runtime threads history (LangGraph / LlamaIndex only) |

Do NOT read other framework references or capability references unless the task explicitly requires them.

## Framework Reference

| Framework | Config File | Key Dependency | Entry Point |
|---|---|---|---|
| Coded Function | `uipath.json` | `uipath` | `main.py` function |
| LangGraph | `langgraph.json` | `uipath-langchain` | `main.py` compiled StateGraph |
| LlamaIndex | `llama_index.json` | `uipath-llamaindex` | `main.py` Workflow instance |
| OpenAI Agents | `openai_agents.json` | `uipath-openai-agents` | `main.py` Agent instance |

## Additional Instructions

- **File/document input → `Attachment`, never a filesystem path string.** If the prompt says the agent takes a CSV, PDF, file, or similar as input, read `../capabilities/file-attachments.md` before defining the `Input` model. A `str` path works locally with `uip codedagent run` but breaks on Studio Web/Orchestrator, where no such path exists in the container.
- **Structured input contract → not OpenAI Agents.** OpenAI Agents always require a `messages` input field and cannot express an input contract without it (see `../frameworks/openai-agents-integration.md` § Input). For a strict typed/structured input, such as one named field without `messages`, choose LangGraph with a custom `StateGraph` and arbitrary input state. Do not silently use a Coded Function: it produces `ProjectType: Function`, not a coded agent.
- After `uip codedagent new` and before running `uip codedagent init`, inspect `main.py` and remove scaffold hazards. Do not keep module-level `UiPathChat`, `UiPathAzureChatOpenAI`, `UiPath`, or other auth-dependent clients. Instantiate LLM and SDK clients inside functions or graph nodes, and ensure importing `main.py` works without UiPath authentication.
- **Never instantiate LLM or SDK clients at module level.** `uip codedagent init` imports the Python file to introspect schemas; module-level `UiPathAzureChatOpenAI()`, `UiPathChat()`, `UiPathChatOpenAI()`, or `UiPath()` can fail before authentication. Create them inside functions or graph nodes only.
- Import the SDK with `from uipath.platform import UiPath`, not `from uipath import UiPath`. Instantiate it inside functions only: `sdk = UiPath()`.
- LangGraph agents get tracing automatically; do not add `@traced()` to graph nodes.
- Simple function agents require `@traced()` on the `main` function.

## Troubleshooting

| Error | Cause | Solution |
|---|---|---|
| `'dict' has no attribute '...'` | `with_structured_output()` returns a dict, not a Pydantic model | Access results with `result['key']` dict syntax, not `result.key` attribute access |
| `ImportError: Could not import <package>` | External tool package not in `pyproject.toml` | Add all third-party tool packages to dependencies: `uv add <package>` |
| Agent returns empty output | Entry point is not wired correctly | Verify `main.py` exports the correct object: compiled graph, Workflow, or Agent |
| `TypeError` on Input/Output | Schema mismatch after a code change | Re-run `uip codedagent init` to regenerate `entry-points.json` |

---
name: uipath-agents
description: "Always invoke for low-code agents (Agent Builder / `agent.json`) or Python framework-based coded agents (LangGraph/LlamaIndex/OpenAI Agents — projects with `uipath-langchain`/`uipath-llamaindex`/`uipath-openai-agents` deps and LLM reasoning). UiPath agent lifecycle: setup, auth, build, run, evaluate, deploy, sync, bindings. For Python Coded Functions (deterministic logic, no LLM, `[tool.uipath] type=\"function\"`)→uipath-functions. For C# or XAML workflows→uipath-rpa."
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion, WebFetch
user-invocable: true
---

# UiPath Agents

## Hard Rules

- Treat "build/create/scaffold/implement a UiPath agent" as the full One-Prompt Flow by default. Do not stop after file creation or local run unless the user explicitly says to stop there.
- A normal completion point is after smoke eval and the mandatory Delivery fork question. A final build summary before that is premature unless run/eval is blocked or the user opted out.
- **Probe the `solution` verb once per session before the first scaffold or deploy.** Run `uip solution init --help --output json`. Result `Success` → use `solution init` and `solution deploy run --parent-folder-path` / `--parent-folder-key` (post-rename, default). `unknown command` / non-zero exit → CLI predates the rename; substitute `uip solution new <Name>` and `--folder-path` / `--folder-key` (same arguments otherwise) wherever this skill calls those.
- **Coded agents only — bindings are always derived from UiPath Python SDK calls and must never be hand-authored.** To derive them, always run the sync workflow in [coded/lifecycle/bindings-reference.md](references/coded/lifecycle/bindings-reference.md) — scan code, regenerate `bindings.json`. Without this, resources cannot be overridden per execution environment and will always default to the hardcoded values in the SDK calls. Derive bindings whenever you add, remove, or modify any UiPath SDK resource call — for instance `assets`, `queues`, `processes`, `buckets`, `indexes`, `connections`, `apps`, `MCP servers`, or `InvokeProcess|CreateTask|CreateEscalation(...)`.

## Project Type Detection

Determine the agent mode before proceeding:

1. **First — confirm this is an agent, not a Coded Function.** If `pyproject.toml` contains `[tool.uipath] type = "function"`, the project is a **Python Coded Function**, not an agent. Stop here and use the [`uipath-functions`](/uipath:uipath-functions) skill instead. Functions are deterministic, do not reason via LLM, and have a distinct lifecycle (`uip functions new/init/pack/publish/run`).
2. **Check for existing agent project files** in the working directory:
   - `pyproject.toml` with `uipath` dependency + `.py` files + a framework dep (`uipath-langchain`, `uipath-llamaindex`, or `uipath-openai-agents`) → **Coded**
   - `agent.json` with `"type": "lowCode"` + `project.uiproj`, AND no `pyproject.toml` → **Low-code**
3. **No existing project found** → ask the user:
   > Should I build this as a **low-code agent** (no Python — configure through prompts and pre-built UiPath tools) or a **coded agent** (Python — full programmatic control with LangGraph, LlamaIndex, or OpenAI Agents)?
4. If the user needs help deciding, read [references/coded-vs-lowcode-guide.md](references/coded-vs-lowcode-guide.md) for a capability comparison.

**After detection, read the quickstart for that mode before doing anything else:**

- **Coded** → read [references/coded/quickstart.md](references/coded/quickstart.md). Quickstart's first step detects project state (`greenfield` / `existing-coded` / `local-workspace`) and gates each lifecycle step on it. For Studio Web Local Workspace specifics, see [references/coded/lifecycle/local-workspace.md](references/coded/lifecycle/local-workspace.md).
- **Low-code** → read [references/lowcode/lowcode.md](references/lowcode/lowcode.md)

## Task Navigation

| I need to... | Mode | Read first | Then |
|---|---|---|---|
| Help user choose coded vs low-code | Both | [coded-vs-lowcode-guide.md](references/coded-vs-lowcode-guide.md) | |
| Authenticate | Both | [authentication.md](references/authentication.md) | |
| Iterate on a coded agent inside a Studio Web Local Workspace solution | Coded | [coded/quickstart.md](references/coded/quickstart.md) (state detection sets `project_state = local-workspace`) | [coded/lifecycle/local-workspace.md](references/coded/lifecycle/local-workspace.md) for files-owned-by-SW + anti-patterns; `coded/lifecycle/running-agents.md`, `coded/lifecycle/evaluate.md` |
| Create/build/deploy coded agent | Coded | [coded/quickstart.md](references/coded/quickstart.md) | `coded/lifecycle/*`, `coded/frameworks/*` |
| Select coded framework | Coded | [coded/quickstart.md](references/coded/quickstart.md) § Framework Selection | |
| Add coded capabilities (HITL, RAG, tracing) | Coded | [coded/quickstart.md](references/coded/quickstart.md) | `coded/capabilities/*` |
| Call an Integration Service connector (Slack, Jira, Web Search) from a coded agent | Coded | [coded/capabilities/integration-service.md](references/coded/capabilities/integration-service.md) **+ then immediately read** [`uipath-platform/references/integration-service/agent-workflow.md`](../uipath-platform/references/integration-service/agent-workflow.md) — discovery lives there, not in `uipath-agents` | `coded/capabilities/sdk-services.md` § Connections |
| Run coded evaluations | Coded | [coded/quickstart.md](references/coded/quickstart.md) § Evaluate | `coded/lifecycle/evaluate.md` |
| Create or scaffold a new low-code agent project | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Quick Start | `lowcode/project-lifecycle.md`, `lowcode/agent-definition.md` |
| Edit `agent.json` (prompts, model, schemas, contentTokens, entry-points.json) | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/agent-definition.md` |
| Add a low-code tool (Orchestrator process — RPA / agent / API / agentic — or Integration Service) | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/process/*`, `lowcode/capabilities/integration-service/*` |
| Accept files as agent input / call the Analyze Files built-in tool | Low-code | [lowcode/capabilities/built-in-tools/built-in-tools.md](references/lowcode/capabilities/built-in-tools/built-in-tools.md) | `lowcode/capabilities/built-in-tools/analyze-attachments.md`, `lowcode/agent-definition.md` § File Attachments |
| Work with file attachments (input, output, or created mid-run) | Coded | [coded/capabilities/file-attachments.md](references/coded/capabilities/file-attachments.md) | |
| Build a conversational (chat-style) coded agent | Coded | [coded/capabilities/conversational-agents.md](references/coded/capabilities/conversational-agents.md) | |
| Add a low-code context (Context Grounding RAG / attachments / DataFabric entity set) | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/context/*` |
| Add an Action Center escalation (HITL) to a low-code agent | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/escalation/escalation.md` |
| Add guardrails (PII, harmful content, custom rules) to a low-code agent | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/guardrails/guardrails.md` |
| Add guardrails to a coded agent | Coded | [coded/capabilities/guardrails/guardrails.md](references/coded/capabilities/guardrails/guardrails.md) | fetch official docs via WebFetch, ask middleware vs decorator, read agent code, write Python |
| Add escalation guardrail (escalate action / Action Center app) | Low-code | [lowcode/capabilities/guardrails/guardrails.md](references/lowcode/capabilities/guardrails/guardrails.md) § escalate — Hand Off to Action Center | Run `uip solution resource list --kind App` to confirm app exists |
| Recommend guardrails for a low-code agent based on its context | Low-code | [lowcode/capabilities/guardrails/guardrails-recommend.md](references/lowcode/capabilities/guardrails/guardrails-recommend.md) | fetch catalog + list, analyze agent context, apply + validate |
| Recommend guardrails for a specific scope or tool | Low-code | [lowcode/capabilities/guardrails/guardrails-recommend.md](references/lowcode/capabilities/guardrails/guardrails-recommend.md) § Scoped or Tool-Specific Filtering | filter candidates by scope or tool name after catalog analysis |
| Validate whether existing guardrails are correctly configured | Low-code | [lowcode/capabilities/guardrails/guardrails-recommend.md](references/lowcode/capabilities/guardrails/guardrails-recommend.md) § Validate Mode | check correctness, actionability, and relevance per guardrail |
| Recommend guardrails for a coded agent based on its context | Coded | [coded/capabilities/guardrails/guardrails-recommend.md](references/coded/capabilities/guardrails/guardrails-recommend.md) | fetch catalog + list + SDK docs, analyze agent code, apply + verify |
| Recommend guardrails for a specific scope or tool (coded) | Coded | [coded/capabilities/guardrails/guardrails-recommend.md](references/coded/capabilities/guardrails/guardrails-recommend.md) § Scope and Tool Filtering | filter candidates by `@tool` function or scope after catalog analysis |
| Validate whether existing coded guardrails are correctly configured | Coded | [coded/capabilities/guardrails/guardrails-recommend.md](references/coded/capabilities/guardrails/guardrails-recommend.md) § Validate Mode | check correctness, actionability, and relevance per guardrail |
| Embed a low-code agent inline in a flow, or wire a multi-agent solution | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/inline-in-flow/inline-in-flow.md`, `lowcode/capabilities/process/solution-agent.md` |
| Run low-code evaluations | Low-code | [lowcode/evaluations/evaluate.md](references/lowcode/evaluations/evaluate.md) | `lowcode/evaluations/evaluators.md`, `lowcode/evaluations/evaluation-sets.md`, `lowcode/evaluations/running-evaluations.md` |
| Validate, pack, publish, upload, or deploy a low-code agent | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) | `lowcode/project-lifecycle.md`, `lowcode/solution-resources.md` |
| Embed coded agent in a flow (solution-level) | Coded | [coded/embedding-in-flows.md](references/coded/embedding-in-flows.md) | |
| Use coded agent in a flow | Coded | [coded/flow-integration.md](references/coded/flow-integration.md) | |
| Use coded agent as tool for another agent in flow | Coded | [coded/flow-integration.md](references/coded/flow-integration.md) § Pattern 3 | |
| Summarize / research / synthesize over PDF or TXT (DeepRAG, coded) | Coded | [context-grounding-patterns.md](references/context-grounding-patterns.md) | [coded/capabilities/deeprag/planning.md](references/coded/capabilities/deeprag/planning.md) |
| Summarize / research / synthesize over PDF or TXT (DeepRAG, low-code) | Low-code | [context-grounding-patterns.md](references/context-grounding-patterns.md) | [lowcode/capabilities/built-in-tools/deeprag/planning.md](references/lowcode/capabilities/built-in-tools/deeprag/planning.md) |
| Process CSV rows with LLM per row (BatchTransform, coded) | Coded | [context-grounding-patterns.md](references/context-grounding-patterns.md) | [coded/capabilities/batch-transform/planning.md](references/coded/capabilities/batch-transform/planning.md) |
| Process CSV rows with LLM per row (BatchTransform, low-code) | Low-code | [context-grounding-patterns.md](references/context-grounding-patterns.md) | [lowcode/capabilities/built-in-tools/batch-transform/planning.md](references/lowcode/capabilities/built-in-tools/batch-transform/planning.md) |

## Resources

- **UiPath Python SDK**: https://uipath.github.io/uipath-python/
- **UiPath Evaluations**: https://uipath.github.io/uipath-python/eval/

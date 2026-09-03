---
name: uipath-agents
description: "End-to-end work with UiPath Agents of all types: build, integrate with UiPath Products (e.g., Orchestrator, Flow, Maestro), design with UiPath Tools (e.g., Agent Builder/Studio Web), deploy, and configure/validate. Covers Coded Agents (e.g., LangGraph, LlamaIndex, OpenAI Agents) and Low-Code Agents (`agent.json` / Agent Builder). For deterministic Coded Functions — Python or JS/TS (`uip function`, `uipath.json` functions map, no agent runtime/LLM)→uipath-functions."
when_to_use: "Must use when user mentions or implies any Agent lifecycle phase - e.g., auth, design, scaffold, Studio Web sync, flow integration, editing, pack/deploy/version bump, eval, debug, tracing, guardrails, memory spaces, bindings, attachments. Example requests: 'create/build a UiPath agent', 'build a low-code / Agent Builder agent', 'build a coded / Python agent (LangGraph / LlamaIndex / OpenAI Agents)'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, WebFetch
user-invocable: true
---

# UiPath Agents

## Hard Rules

- Interpret “build,” “create,” “scaffold,” or “implement a UiPath agent” as the full One-Prompt Flow. Do not stop at file creation or a local run unless explicitly asked. Normally finish only after smoke evaluation and the mandatory Delivery fork question. Give a final build summary earlier only if execution/evaluation is blocked or the user opted out.
- **Probe `solution` once per session before the first scaffold or deploy:** run `uip solution init --help --output json`. On success, use `uip solution init` and `solution deploy run --parent-folder-path` / `--parent-folder-key` (post-rename, default). On `unknown command` or any non-zero exit, use older `uip solution new <Name>` and `--folder-path` / `--folder-key` equivalents everywhere else.
- **Scaffold every new coded agent:** run `uip codedagent new <name>`, then `uip codedagent init`. Never hand-author `pyproject.toml`, `main.py`, `langgraph.json`, or `entry-points.json`. For existing or Studio Web Local Workspace projects, do not run `uip codedagent new`; follow [coded/quickstart.md](references/coded/quickstart.md) project-state gating.
- **Derive coded-agent bindings; never hand-author them.** Whenever a UiPath SDK resource call is added, removed, or changed—including `assets`, `queues`, `processes`, `buckets`, `indexes`, `connections`, `apps`, MCP servers, or `InvokeProcess|CreateTask|CreateEscalation(...)`—run the sync workflow in [coded/lifecycle/bindings-reference.md](references/coded/lifecycle/bindings-reference.md) to scan code and regenerate `bindings.json`. Otherwise environment overrides do not work and SDK hardcoded values remain active.

## Project Type Detection

Determine the mode before proceeding:

1. **Confirm this is an agent, not a Coded Function.** If `uipath.json` declares a `functions` map — Python (`{"functions": {"main": "main.py:main"}}`, sibling `pyproject.toml`) or JS/TS (`{"functions": {"invoice": "functions/invoice.ts:default"}}`, sibling `package.json`) — it is a **Coded Function**, not an agent. Stop and use [`uipath-functions`](/uipath:uipath-functions). Functions are deterministic and use `uip function new/pack/publish/run` (`init` is Python-only).
2. **Check for an existing agent project:**
   - `pyproject.toml` plus `.py` files and a framework dependency (`uipath-langchain`, `uipath-llamaindex`, or `uipath-openai-agents`) means **Coded**. The framework already supplies `uipath`.
   - `agent.json` with `"type": "lowCode"` plus `project.uiproj`, and no `pyproject.toml`, means **Low-code**.
3. **If no project exists, ask:**
   > Should I build this as a **low-code agent** (no Python—configure through prompts and pre-built UiPath tools) or a **coded agent** (Python—programmatic control with LangGraph, LlamaIndex, or OpenAI Agents)?
   > For conversational use-cases, choose low-code without asking; explain that low-code conversational agents are currently strongly recommended for production use-cases (see [references/coded/capabilities/conversational-agents.md](references/coded/capabilities/conversational-agents.md)).
4. If the user needs help choosing, read [references/coded-vs-lowcode-guide.md](references/coded-vs-lowcode-guide.md).

**After detection, read the mode quickstart before doing anything else:**

- **Coded:** read [references/coded/quickstart.md](references/coded/quickstart.md). Its first step detects `greenfield`, `existing-coded`, or `local-workspace` and gates lifecycle actions accordingly. For Studio Web Local Workspace details, read [references/coded/lifecycle/local-workspace.md](references/coded/lifecycle/local-workspace.md).
- **Low-code:** read [references/lowcode/lowcode.md](references/lowcode/lowcode.md).

## Task Navigation

| Need | Mode | Read first | Then |
|---|---|---|---|
| Choose coded vs low-code | Both | [coded-vs-lowcode-guide.md](references/coded-vs-lowcode-guide.md) | |
| Authenticate | Both | [authentication.md](references/authentication.md) | |
| Iterate in a Studio Web Local Workspace solution | Coded | [coded/quickstart.md](references/coded/quickstart.md) (detects `local-workspace`) | [coded/lifecycle/local-workspace.md](references/coded/lifecycle/local-workspace.md), `coded/lifecycle/running-agents.md`, `coded/lifecycle/evaluate.md` |
| Create, build, or deploy a coded agent | Coded | [coded/quickstart.md](references/coded/quickstart.md) | `coded/lifecycle/*`, `coded/frameworks/*` |
| Select a coded framework | Coded | [coded/quickstart.md](references/coded/quickstart.md) § Framework Selection | |
| Add coded HITL, RAG, or tracing | Coded | [coded/quickstart.md](references/coded/quickstart.md) | `coded/capabilities/*` |
| Query/write Data Fabric entities from a coded agent | Coded | [coded/capabilities/datafabric.md](references/coded/capabilities/datafabric.md) | `coded/capabilities/sdk-services.md` § Entities |
| Configure coded environment variables or `%ASSETS/<ASSET_NAME>%` references | Coded | [coded/lifecycle/environment-variables.md](references/coded/lifecycle/environment-variables.md) | [coded/lifecycle/file-sync.md](references/coded/lifecycle/file-sync.md) for `.env` limits |
| Call an Integration Service connector | Coded | [coded/capabilities/integration-service.md](references/coded/capabilities/integration-service.md), then immediately [`uipath-platform/references/integration-service/agent-workflow.md`](../uipath-platform/references/integration-service/agent-workflow.md) | [coded/capabilities/sdk-services.md](references/coded/capabilities/sdk-services.md) § Connections |
| Run coded evaluations | Coded | [coded/quickstart.md](references/coded/quickstart.md) § Evaluate | [coded/lifecycle/evaluate.md](references/coded/lifecycle/evaluate.md) |
| Create or scaffold a low-code project | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Quick Start | `lowcode/project-lifecycle.md`, `lowcode/agent-definition.md` |
| Edit `agent.json` (prompts, model, schemas, `contentTokens`, `entry-points.json`) | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/agent-definition.md` |
| Add a low-code tool (Orchestrator process or Integration Service) | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/process/*`, `lowcode/capabilities/integration-service/*` |
| Add an MCP server tool | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | [lowcode/capabilities/mcp/mcp.md](references/lowcode/capabilities/mcp/mcp.md) |
| Accept files or call Analyze Files | Low-code | [lowcode/capabilities/built-in-tools/built-in-tools.md](references/lowcode/capabilities/built-in-tools/built-in-tools.md) | [lowcode/capabilities/built-in-tools/analyze-attachments.md](references/lowcode/capabilities/built-in-tools/analyze-attachments.md), `lowcode/agent-definition.md` |
| Use coded file attachments | Coded | [coded/capabilities/file-attachments.md](references/coded/capabilities/file-attachments.md) | |
| Build a conversational agent | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) | `lowcode/project-lifecycle.md`, `lowcode/agent-definition.md` |
| Add low-code context (Context Grounding RAG, attachments, or DataFabric entity set) | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/context/*` |
| Add or seed low-code memory | Low-code | [lowcode/capabilities/memory/memory.md](references/lowcode/capabilities/memory/memory.md) | Use `uip agent memory`, then refresh and validate |
| Add Action Center escalation | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | [lowcode/capabilities/escalation/escalation.md](references/lowcode/capabilities/escalation/escalation.md) |
| Add low-code guardrails | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | [lowcode/capabilities/guardrails/guardrails.md](references/lowcode/capabilities/guardrails/guardrails.md) |
| Add coded guardrails | Coded | [coded/capabilities/guardrails/guardrails.md](references/coded/capabilities/guardrails/guardrails.md) | Fetch official docs via WebFetch, ask middleware vs decorator, inspect agent code, and write Python |
| Add an escalation guardrail | Low-code | [lowcode/capabilities/guardrails/guardrails.md](references/lowcode/capabilities/guardrails/guardrails.md) § escalate—Hand Off to Action Center | Run `uip solution resources list --kind App --source remote --output json` to confirm the app |
| Recommend low-code guardrails by context | Low-code | [lowcode/capabilities/guardrails/guardrails-recommend.md](references/lowcode/capabilities/guardrails/guardrails-recommend.md) | Fetch catalog and list, analyze context, apply, validate |
| Recommend low-code guardrails by scope or tool | Low-code | [lowcode/capabilities/guardrails/guardrails-recommend.md](references/lowcode/capabilities/guardrails/guardrails-recommend.md) § Scoped or Tool-Specific Filtering | Filter candidates after catalog analysis |
| Validate low-code guardrails | Low-code | [lowcode/capabilities/guardrails/guardrails-recommend.md](references/lowcode/capabilities/guardrails/guardrails-recommend.md) § Validate Mode | Check correctness, actionability, and relevance |
| Recommend coded guardrails by context | Coded | [coded/capabilities/guardrails/guardrails-recommend.md](references/coded/capabilities/guardrails/guardrails-recommend.md) | Fetch catalog, list, and SDK docs; analyze code; apply and verify |
| Recommend coded guardrails by scope or tool | Coded | [coded/capabilities/guardrails/guardrails-recommend.md](references/coded/capabilities/guardrails/guardrails-recommend.md) § Scope and Tool Filtering | Filter by `@tool` function or scope |
| Validate or fix coded guardrail placement/scope | Coded | [coded/capabilities/guardrails/guardrails-recommend.md](references/coded/capabilities/guardrails/guardrails-recommend.md) § Validate Mode | Fetch SDK docs first for authoritative scope/placement; also fetch catalog and list for relevance/entitlement; check and fix in place |
| Embed a low-code agent in a flow or wire a multi-agent solution | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/inline-in-flow/inline-in-flow.md`, `lowcode/capabilities/process/solution-agent.md` |
| Run low-code evaluations | Low-code | [lowcode/evaluations/evaluate.md](references/lowcode/evaluations/evaluate.md) | `lowcode/evaluations/evaluators.md`, `lowcode/evaluations/evaluation-sets.md`, `lowcode/evaluations/running-evaluations.md` |
| Manage runtime evaluations for a published Orchestrator package | Low-code | [lowcode/evaluations/orchestrator-eval-run.md](references/lowcode/evaluations/orchestrator-eval-run.md) | `uip or eval execute-and-evaluate`; evaluator, evaluation-set, and evaluation CRUD; results and schedules |
| Validate, pack, publish, upload, or deploy low-code | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) | `lowcode/project-lifecycle.md`, `lowcode/solution-resources.md` |
| Debug/run low-code end-to-end and inspect output | Low-code | [lowcode/debug.md](references/lowcode/debug.md) | `lowcode/project-lifecycle.md` § `uip agent debug` |
| Embed a coded agent in a flow | Coded | [coded/embedding-in-flows.md](references/coded/embedding-in-flows.md) | |
| Use a coded agent in a flow | Coded | [coded/flow-integration.md](references/coded/flow-integration.md) | |
| Use a coded agent as another agent’s flow tool | Coded | [coded/flow-integration.md](references/coded/flow-integration.md) § Pattern 3 | |
| Summarize/research/synthesize PDF or TXT with DeepRAG | Coded | [context-grounding-patterns.md](references/context-grounding-patterns.md) | [coded/capabilities/deeprag/planning.md](references/coded/capabilities/deeprag/planning.md) |
| Summarize/research/synthesize PDF or TXT with DeepRAG | Low-code | [context-grounding-patterns.md](references/context-grounding-patterns.md) | [lowcode/capabilities/built-in-tools/deeprag/planning.md](references/lowcode/capabilities/built-in-tools/deeprag/planning.md) |
| Process CSV rows with an LLM per row using BatchTransform | Coded | [context-grounding-patterns.md](references/context-grounding-patterns.md) | [coded/capabilities/batch-transform/planning.md](references/coded/capabilities/batch-transform/planning.md) |
| Process CSV rows with an LLM per row using BatchTransform | Low-code | [context-grounding-patterns.md](references/context-grounding-patterns.md) | [lowcode/capabilities/built-in-tools/batch-transform/planning.md](references/lowcode/capabilities/built-in-tools/batch-transform/planning.md) |
| Manage context-grounding indexes from the CLI | Platform | [`uipath-platform/references/context-grounding/index-management.md`](../uipath-platform/references/context-grounding/index-management.md) | Use `uip context-grounding`; this cross-cutting CLI is owned by `uipath-platform` |

## Resources

- **UiPath Python SDK:** https://uipath.github.io/uipath-python/
- **UiPath Evaluations:** https://uipath.github.io/uipath-python/eval/

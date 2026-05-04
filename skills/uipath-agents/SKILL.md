---
name: uipath-agents
description: "UiPath agent lifecycle — coded (Python: LangGraph/LlamaIndex/OpenAI Agents) and low-code (agent.json from Agent Builder). Setup, auth, build, run, evaluate, deploy, sync, bindings. For C# or XAML workflows→uipath-rpa."
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# UiPath Agents

## Hard Rules

- Treat "build/create/scaffold/implement a UiPath agent" as the full One-Prompt Flow by default. Do not stop after file creation or local run unless the user explicitly says to stop there.
- A normal completion point is after smoke eval and the mandatory Delivery fork question. A final build summary before that is premature unless run/eval is blocked or the user opted out.

## Project Type Detection

Determine the agent mode before proceeding:

1. **Check for existing project files** in the working directory:
   - `pyproject.toml` with `uipath` dependency + `.py` files → **Coded**
   - `agent.json` with `"type": "lowCode"` + `project.uiproj` → **Low-code**
2. **No existing project found** → ask the user:
   > Should I build this as a **low-code agent** (no Python — configure through prompts and pre-built UiPath tools) or a **coded agent** (Python — full programmatic control with LangGraph, LlamaIndex, or OpenAI Agents)?
3. If the user needs help deciding, read [references/coded-vs-lowcode-guide.md](references/coded-vs-lowcode-guide.md) for a capability comparison.

**After detection, read the quickstart for that mode before doing anything else:**

- **Coded** → read [references/coded/quickstart.md](references/coded/quickstart.md)
- **Low-code** → read [references/lowcode/lowcode.md](references/lowcode/lowcode.md)

## Task Navigation

| I need to... | Mode | Read first | Then |
|---|---|---|---|
| Help user choose coded vs low-code | Both | [coded-vs-lowcode-guide.md](references/coded-vs-lowcode-guide.md) | |
| Authenticate | Both | [authentication.md](references/authentication.md) | |
| Create/build/deploy coded agent | Coded | [coded/quickstart.md](references/coded/quickstart.md) | `coded/lifecycle/*`, `coded/frameworks/*` |
| Select coded framework | Coded | [coded/quickstart.md](references/coded/quickstart.md) § Framework Selection | |
| Add coded capabilities (HITL, RAG, tracing) | Coded | [coded/quickstart.md](references/coded/quickstart.md) | `coded/capabilities/*` |
| Run coded evaluations | Coded | [coded/quickstart.md](references/coded/quickstart.md) § Evaluate | `coded/lifecycle/evaluate.md` |
| Create or scaffold a new low-code agent project | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Quick Start | `lowcode/project-lifecycle.md`, `lowcode/agent-definition.md` |
| Edit `agent.json` (prompts, model, schemas, contentTokens, entry-points.json) | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/agent-definition.md` |
| Add a low-code tool (Orchestrator process — RPA / agent / API / agentic — or Integration Service) | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/process/*`, `lowcode/capabilities/integration-service/*` |
| Add a low-code context (Context Grounding RAG / attachments / DataFabric entity set) | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/context/*` |
| Add an Action Center escalation (HITL) to a low-code agent | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/escalation/escalation.md` |
| Add guardrails (PII, harmful content, custom rules) to a low-code agent | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/guardrails/guardrails.md` |
| Add escalation guardrail (escalate action / Action Center app) | Low-code | [lowcode/capabilities/guardrails/guardrails.md](references/lowcode/capabilities/guardrails/guardrails.md) § escalate — Hand Off to Action Center | Run `uip solution resource list --kind App` to confirm app exists |
| Embed a low-code agent inline in a flow, or wire a multi-agent solution | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | `lowcode/capabilities/inline-in-flow/inline-in-flow.md`, `lowcode/capabilities/process/solution-agent.md` |
| Run low-code evaluations | Low-code | [lowcode/evaluation/evaluate.md](references/lowcode/evaluation/evaluate.md) | `lowcode/evaluation/evaluators.md`, `lowcode/evaluation/evaluation-sets.md`, `lowcode/evaluation/running-evaluations.md` |
| Validate, pack, publish, upload, or deploy a low-code agent | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) | `lowcode/project-lifecycle.md`, `lowcode/solution-resources.md` |

## Resources

- **UiPath Python SDK**: https://uipath.github.io/uipath-python/
- **UiPath Evaluations**: https://uipath.github.io/uipath-python/eval/

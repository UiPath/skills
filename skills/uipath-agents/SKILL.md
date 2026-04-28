---
name: uipath-agents
description: "UiPath agent lifecycle — coded (Python: LangGraph/LlamaIndex/OpenAI Agents) and low-code (agent.json from Agent Builder). Setup, auth, build, run, evaluate, deploy, sync. For C# or XAML workflows→uipath-rpa."
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# UiPath Agents

## CLI Setup

```bash
which uip > /dev/null 2>&1 && echo "uip found" || echo "uip NOT found — run: npm install -g @uipath/cli"
```

If `uip` is not found, install with `npm install -g @uipath/cli`. If `npm` is missing, ask the user to install Node.js first.

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
| Create/build/deploy low-code agent | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) | `lowcode/project-lifecycle.md`, `lowcode/agent-definition.md` |
| Edit agent.json (prompts, schemas, model) | Low-code | [lowcode/agent-definition.md](references/lowcode/agent-definition.md) | |
| Add tools, contexts, or escalations | Low-code | [lowcode/lowcode.md](references/lowcode/lowcode.md) § Capability Registry | applicable `lowcode/capabilities/<name>/` |
| Discover solution resources (processes/apps/indexes/buckets/connections) | Low-code | [lowcode/project-lifecycle.md](references/lowcode/project-lifecycle.md) § Resource Discovery | |
| Add Integration Service tool | Low-code | [lowcode/capabilities/integration-service/integration-service.md](references/lowcode/capabilities/integration-service/integration-service.md) | |
| Add index-backed context (Context Grounding) | Low-code | [lowcode/capabilities/context/index.md](references/lowcode/capabilities/context/index.md) | |
| Add external process tool (RPA / agent / API / agentic) | Low-code | [lowcode/capabilities/process/external.md](references/lowcode/capabilities/process/external.md) | `lowcode/capabilities/process/solution-files.md` |
| Add Action Center escalation | Low-code | [lowcode/capabilities/escalation/escalation.md](references/lowcode/capabilities/escalation/escalation.md) | |
| Embed agent in a flow | Low-code | [lowcode/capabilities/inline-in-flow/inline-in-flow.md](references/lowcode/capabilities/inline-in-flow/inline-in-flow.md) | |
| Wire multi-agent solution | Low-code | [lowcode/capabilities/process/solution-agent.md](references/lowcode/capabilities/process/solution-agent.md) | |
| See low-code CLI commands | Low-code | [lowcode/project-lifecycle.md](references/lowcode/project-lifecycle.md) | |

## Resources

- **UiPath Python SDK**: https://uipath.github.io/uipath-python/
- **UiPath Evaluations**: https://uipath.github.io/uipath-python/eval/

---
name: uipath-agents
description: UiPath agent lifecycle assistant. Works with both coded agents (Python with LangGraph/LlamaIndex/OpenAI Agents) and low-code agents (agent.json from Agent Builder). Orchestrates setup, auth, build, run, evaluate, deploy, and sync. Use when the user wants to create, run, evaluate, or deploy a UiPath agent, e.g. "create a UiPath agent", "set up and deploy an agent", "edit my agent.json", or "build and run an agent end-to-end".
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# UiPath Agents

---

## Step 1 — Choose the Agent Type

Before writing any code or files, determine whether to build a **Low-Code Agent** or a **Coded Agent**. Both are deployed and run with the same CLI commands — the difference is entirely in how they are built.

### When to Choose Low-Code

- The agent's behavior can be fully expressed through prompts and pre-built tools (UiPath processes, Integration Service connectors, sub-agents, Context Grounding indexes, HITL escalations, MCP servers)
- The user is a business analyst, citizen developer, or automation professional who prefers not to write Python
- Speed of iteration matters more than custom logic — `agent.json` is faster to scaffold and change
- The agent uses only standard UiPath capabilities available as `resources` in `agent.json`
- The user wants to design in Studio Web Agent Builder and work locally with the resulting file

### When to Choose Coded

- The agent needs custom LLM reasoning that cannot be expressed through prompts alone: complex state machines, dynamic multi-step planning, custom memory structures
- The agent requires a Python library or third-party SDK not available as a pre-built UiPath tool
- The team is Python-proficient and prefers code over declarative JSON configuration
- Human-in-the-loop requires conditional resume logic that depends on the human's response (LangGraph `interrupt()` + branching)
- Custom evaluation mocking (`@mockable()`) or custom Python evaluators are needed
- Multi-agent routing logic must be implemented in code (LangGraph supervisor, LlamaIndex orchestration)
- Full control over LLM prompt construction, model selection, or token budget at runtime

### Decision Table

| Requirement | Low-Code | Coded |
|---|:---:|:---:|
| Build without writing Python | ✅ | ❌ |
| Call UiPath processes / API workflows as tools | ✅ | ✅ |
| Use Integration Service connectors (Salesforce, ServiceNow…) | ✅ | ✅ |
| RAG over a Context Grounding index | ✅ | ✅ |
| Use a third-party Python library | ❌ | ✅ |
| Custom LLM state machine (LangGraph StateGraph) | ❌ | ✅ |
| Human-in-the-loop (HITL) | ✅ escalation resource | ✅ `interrupt()` |
| Complex conditional HITL resume logic | ❌ | ✅ |
| Studio Web Agent Builder canvas | ✅ | Optional |
| `@mockable()` for evaluation isolation | ❌ | ✅ |
| Full runtime control over LLM prompts | ❌ | ✅ |
| Multi-model / multi-framework strategies | ❌ | ✅ |
| Fastest path to first working agent | ✅ | ❌ |

### Detecting the Type from an Existing Project

| Signal | Type |
|---|---|
| User mentions Python, LangGraph, LlamaIndex, OpenAI Agents, or writing code | **Coded** |
| User mentions `agent.json`, Agent Builder, low-code, visual design, or no-code | **Low-Code** |
| Project has `agent.json` (no `main.py` or `langgraph.json`) | **Low-Code** |
| Project has `main.py`, `langgraph.json`, or `uipath.json` with `"functions"` key | **Coded** |
| Ambiguous | **Ask the user** |

If still ambiguous, ask:
> Should I build this as a **low-code agent** (no Python — you configure the agent through prompts and pre-built UiPath tools, using the Studio Web Agent Builder or a JSON file) or a **coded agent** (Python — you write the agent logic in code using LangGraph, LlamaIndex, or the OpenAI Agents SDK for full programmatic control)?

---

## CLI Setup — Both Paths (Run Once)

**Prerequisites:** Python 3.11+, Node.js 18+ with npm, and `uv` must be installed before running these steps.

```bash
# 1. Check uip is installed
which uip > /dev/null 2>&1 && echo "uip found" || echo "uip NOT found — run: npm install -g @uipath/cli"

# 2. Set up the Python runtime (creates .venv — must run BEFORE activating it)
uip codedagents setup --format json

# 3. Activate the virtual environment (required if .venv now exists)
if [ -d ".venv" ]; then source .venv/bin/activate; fi
```

If `uip` is not found, install with `npm install -g @uipath/cli`. If `npm` is missing, ask the user to install Node.js 18+ first. If `uv` is missing, install with `pip install uv`.

**Do NOT add `--format json` to forwarded commands.** The `--format` flag is only valid for native `uip` commands (`uip login`, `uip codedagents setup`). Commands forwarded to the Python CLI (`new`, `init`, `run`, `eval`, `deploy`, `push`, `pull`, `pack`, `publish`, `invoke`) do **not** accept `--format json`.

**Why `uip codedagents` for low-code agents?** The `codedagents` name is historical. These commands are thin wrappers that forward to the `uipath` Python CLI, which auto-detects the agent type at runtime. `uip codedagents run agent.json '...'` works for low-code agents because the runtime sees `agent.json` and routes to the low-code execution path.

---

## Path A — Low-Code Agent

A low-code agent is fully defined by a single `agent.json` file. No Python code is written. The UiPath runtime compiles `agent.json` into a LangGraph ReAct agent at execution time using the built-in `basic-v2` engine.

> **Do NOT stop between steps to ask "would you like me to continue?".** Execute the entire path automatically. Only pause when you genuinely need information from the user (auth credentials, Studio Web project ID).

### A1 — Setup

Two options to get an `agent.json`:

**Option 1 — Pull from Studio Web** (agent already designed in Agent Builder):
```bash
mkdir my-agent && cd my-agent
uip codedagents pull   # prompts to select tenant, folder, and agent
```

**Option 2 — Create from scratch**:
- Copy the template from [assets/templates/agent.json](assets/templates/agent.json)
- Replace `{AGENT_NAME}` with the agent's name

Read the full prerequisites and directory structure in [lowcode/setup.md](references/lowcode/setup.md).

### A2 — Build

Edit `agent.json` to define the agent's behavior:

1. **`messages`** — Write the system prompt (agent's role and constraints) and the user prompt (task template with `{{variableName}}` interpolation for inputs)
2. **`inputSchema` / `outputSchema`** — Define the agent's I/O as JSON Schema objects
3. **`settings`** — Choose the LLM model, temperature, `maxTokens`, `maxIterations`, and engine (`basic-v2` for task agents, `conversational-v1` for multi-turn)
4. **`resources`** — Add tools, context sources, escalations, MCP servers, and sub-agents

Key reference files:
- Full `agent.json` schema: [lowcode/agent-json-reference.md](references/lowcode/agent-json-reference.md)
- All resource types with examples: [lowcode/resources-reference.md](references/lowcode/resources-reference.md)
- Context Grounding (RAG): [capabilities/context-grounding.md](references/capabilities/context-grounding.md) → Low-Code Agents section
- Human-in-the-Loop (HITL): [capabilities/human-in-the-loop.md](references/capabilities/human-in-the-loop.md) → Low-Code Agents section
- Process / job invocation: [capabilities/process-invocation.md](references/capabilities/process-invocation.md) → Low-Code Agents section

### A3 — Init

Generate `entry-points.json` and `bindings.json` from `agent.json`:

```bash
uip codedagents init
```

Required before `push` and `deploy`. Optional for local `run` (the runtime reads `agent.json` directly). Do not hand-edit `entry-points.json` — it is regenerated on every `init`.

### A4 — Auth

Check if `.env` already contains `UIPATH_URL` and `UIPATH_ACCESS_TOKEN`. If yes, skip this step. If not, output **only** this question and wait for the answer:

> What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?

Then run:
```bash
uip login --format json
uip login tenant set "<TENANT>" --format json
```

Read [lifecycle/authentication.md](references/lifecycle/authentication.md) for all auth modes and troubleshooting.

### A5 — Run

Test the agent locally:
```bash
uip codedagents run agent.json '{"task": "your test input here"}'
```

The entrypoint for low-code agents is **always `agent.json`**. Input fields must match `inputSchema` in `agent.json`.

Read [lifecycle/running-agents.md](references/lifecycle/running-agents.md).

### A6 — Push

Tell the user to open Studio Web at `https://cloud.uipath.com/{orgName}/studio_/projects`, create a new **Agent** project, and share the project ID. Add `UIPATH_PROJECT_ID=<id>` to `.env`, then:

```bash
uip codedagents push
```

If the push is rejected due to a version conflict, use `uip codedagents push --overwrite`.

### A7 — Evaluate

Create the evaluator config and a smoke eval set, then run:

`evaluations/evaluators/llm-judge-trajectory.json`:
```json
{
  "version": "1.0",
  "id": "LLMJudgeTrajectoryEvaluator",
  "evaluatorTypeId": "uipath-llm-judge-trajectory-similarity",
  "evaluatorConfig": {
    "name": "LLMJudgeTrajectoryEvaluator",
    "defaultEvaluationCriteria": {
      "expectedAgentBehavior": "Agent should process the input and return a response."
    }
  }
}
```

`evaluations/eval-sets/smoke-test.json` (adapt `inputs` to match `inputSchema`):
```json
{
  "version": "1.0",
  "id": "smoke-test",
  "name": "Smoke Test",
  "evaluatorRefs": ["LLMJudgeTrajectoryEvaluator"],
  "evaluations": [
    {
      "id": "test-1",
      "name": "Basic test",
      "inputs": {"task": "your test input here"},
      "evaluationCriterias": {
        "LLMJudgeTrajectoryEvaluator": {
          "expectedAgentBehavior": "Agent should process the input and return a response."
        }
      }
    }
  ]
}
```

```bash
uip codedagents eval agent.json evaluations/eval-sets/smoke-test.json --no-report
```

Add `--report` (and ensure `UIPATH_PROJECT_ID` is set in `.env`) to publish results to Studio Web.

Read [lifecycle/evaluate.md](references/lifecycle/evaluate.md) and the [evaluators reference](references/lifecycle/evaluations/evaluators.md).

### A8 — Deploy

```bash
uip codedagents deploy --my-workspace
```

Read [lifecycle/deployment.md](references/lifecycle/deployment.md).

---

## Path B — Coded Agent

A coded agent is implemented in Python using a supported LLM framework. The agent is packaged as a `.nupkg` and deployed to Orchestrator, where it runs as a standard process.

> **Do NOT stop between steps to ask "would you like me to continue?".** Execute the entire path automatically. Only pause when you genuinely need information from the user (auth credentials, Studio Web project ID, or framework choice if ambiguous).

### B1 — Select Framework

Choose the framework before writing any code. Tell the user which was selected and why.

| Framework | Package | Config File | Best For |
|---|---|---|---|
| **Simple Function** | `uipath` | `uipath.json` | Deterministic logic, no LLM, data transformation |
| **LangGraph** | `uipath-langchain` | `langgraph.json` | Multi-step LLM, conditional routing, HITL, complex agents |
| **LlamaIndex** | `uipath-llamaindex` | `llama_index.json` | RAG-heavy workflows, document processing |
| **OpenAI Agents** | `uipath-openai-agents` | `openai_agents.json` | Lightweight LLM agents with tool use and handoffs |

**Inference hints:** multi-step reasoning + tools → LangGraph. RAG + document Q&A → LlamaIndex. Simple LLM chat → OpenAI Agents. No LLM → Simple Function.

If ambiguous, ask: *"Which framework should I use: Simple Function, LangGraph, LlamaIndex, or OpenAI Agents?"*

### B2 — Setup

```bash
mkdir my-agent && cd my-agent
# Copy pyproject.toml from assets/templates/pyproject.toml, replace {AGENT_NAME} and {AGENT_DESCRIPTION}

# Add framework dependency (skip for Simple Function — uipath is already in the template)
uv add uipath-langchain        # LangGraph
# uv add uipath-llamaindex     # LlamaIndex
# uv add uipath-openai-agents  # OpenAI Agents

uv sync
source .venv/bin/activate

uip codedagents new my-agent   # scaffold main.py + framework config file
uip codedagents init           # generate entry-points.json, bindings.json, .env
```

Read [lifecycle/setup.md](references/lifecycle/setup.md) for full setup details and the `uipath.json` structure.

### B3 — Build

Implement agent logic in `main.py`. Load **only** the reference for the selected framework — do not preload others.

| Framework | Reference |
|---|---|
| Simple Function | [frameworks/simple-agents.md](references/frameworks/simple-agents.md) |
| LangGraph | [frameworks/langgraph-integration.md](references/frameworks/langgraph-integration.md) |
| LlamaIndex | [frameworks/llamaindex-integration.md](references/frameworks/llamaindex-integration.md) |
| OpenAI Agents | [frameworks/openai-agents-integration.md](references/frameworks/openai-agents-integration.md) |

Load these **only if the task requires the capability**:

| Capability | Reference |
|---|---|
| Platform SDK (assets, queues, buckets, jobs…) | [capabilities/sdk-services.md](references/capabilities/sdk-services.md) |
| HITL / interrupt / Action Center | [capabilities/human-in-the-loop.md](references/capabilities/human-in-the-loop.md) → Coded Agents section |
| RAG / Context Grounding | [capabilities/context-grounding.md](references/capabilities/context-grounding.md) → Coded Agents section |
| Process / job invocation | [capabilities/process-invocation.md](references/capabilities/process-invocation.md) → Coded Agents section |
| Custom tracing (`@traced()`) | [capabilities/tracing.md](references/capabilities/tracing.md) → Coded Agents section |

After changing `Input`/`Output` models (or `StartEvent`/`StopEvent`), re-run `uip codedagents init` to regenerate schemas.

If using platform resources (assets, queues, processes, buckets, etc.), sync `bindings.json` per [lifecycle/bindings-reference.md](references/lifecycle/bindings-reference.md).

Read [lifecycle/build.md](references/lifecycle/build.md) for the full build guide.

### B4 — Auth

Check if `.env` already contains `UIPATH_URL` and `UIPATH_ACCESS_TOKEN`. If yes, skip this step. If not, output **only** this question and wait for the answer:

> What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?

Then run:
```bash
uip login --format json
uip login tenant set "<TENANT>" --format json
```

Read [lifecycle/authentication.md](references/lifecycle/authentication.md) for all auth modes and troubleshooting.

### B5 — Run

Test the agent locally:
```bash
uip codedagents run main '{"query": "test"}'
```

The entrypoint name comes from `entry-points.json` (e.g., `main`, `agent`). Check `entry-points.json` for the correct name — it is **not** the project name.

Read [lifecycle/running-agents.md](references/lifecycle/running-agents.md).

### B6 — Push

Tell the user to open Studio Web at `https://cloud.uipath.com/{orgName}/studio_/projects`, create a new **Coded Agent** project, and share the project ID. Add `UIPATH_PROJECT_ID=<id>` to `.env`, then:

```bash
uip codedagents push
```

If the push is rejected due to a version conflict, use `uip codedagents push --overwrite`.

### B7 — Evaluate

Create the evaluator config and a smoke eval set, then run:

`evaluations/evaluators/llm-judge-trajectory.json`:
```json
{
  "version": "1.0",
  "id": "LLMJudgeTrajectoryEvaluator",
  "evaluatorTypeId": "uipath-llm-judge-trajectory-similarity",
  "evaluatorConfig": {
    "name": "LLMJudgeTrajectoryEvaluator",
    "defaultEvaluationCriteria": {
      "expectedAgentBehavior": "Agent should process the input and return a response."
    }
  }
}
```

`evaluations/eval-sets/smoke-test.json` (adapt `inputs` to match the agent's input schema):
```json
{
  "version": "1.0",
  "id": "smoke-test",
  "name": "Smoke Test",
  "evaluatorRefs": ["LLMJudgeTrajectoryEvaluator"],
  "evaluations": [
    {
      "id": "test-1",
      "name": "Basic test",
      "inputs": {"field": "value"},
      "evaluationCriterias": {
        "LLMJudgeTrajectoryEvaluator": {
          "expectedAgentBehavior": "Agent should process the input and return a response."
        }
      }
    }
  ]
}
```

```bash
uip codedagents eval main evaluations/eval-sets/smoke-test.json --no-report
```

Add `--report` (and ensure `UIPATH_PROJECT_ID` is set in `.env`) to publish results to Studio Web.

Read [lifecycle/evaluate.md](references/lifecycle/evaluate.md) and the [evaluators reference](references/lifecycle/evaluations/evaluators.md).

### B8 — Deploy

Bump the patch version in `pyproject.toml` if re-deploying (publishing the same version returns a 409 error):

```bash
uip codedagents deploy --my-workspace
```

To invoke the deployed agent asynchronously from the CLI and get a monitoring URL:
```bash
uip codedagents invoke main '{"query": "test"}'
```
`invoke` always returns immediately — it starts a cloud job and prints a URL. There is no `--wait` flag.

Read [lifecycle/deployment.md](references/lifecycle/deployment.md).

---

## Shared Rules

### Both Agent Types

- **After `uip login`, ALWAYS run `uip login tenant set` before any cloud command.** The interactive tenant picker cannot be used from Claude's Bash tool. If the tenant name is known, run both steps together: `uip login --format json` then `uip login tenant set "<TENANT>" --format json`. If the tenant name is unknown, use the discovery flow: `uip login --format json` → `uip login tenant list --format json` → present all tenant names to the user → `uip login tenant set "<NAME>" --format json`.
- **Skip auth if already authenticated.** Check if `.env` contains `UIPATH_URL` and `UIPATH_ACCESS_TOKEN`. If yes, skip auth.
- **Auth MUST be an interactive question (when needed).** Output ONLY this question as your entire response — no bullets, no status summaries, no "next steps":
  > What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?
- **Always create a smoke evaluation set.** Every agent must include `evaluations/eval-sets/smoke-test.json` with 2–3 basic test cases before deploying.

### Coded Agents Only

- **NEVER add a `[build-system]` section to `pyproject.toml`**. No `hatchling`, no `setuptools`. Only `[project]`, `[dependency-groups]`, and `[tool.*]` sections are valid.
- **Select a framework before writing any code.** If ambiguous, ask the user to choose from: Simple Function, LangGraph, LlamaIndex, or OpenAI Agents.
- **Correct SDK import: `from uipath.platform import UiPath`** — not `from uipath import UiPath` (that does not exist).
- **Always use lazy LLM initialization.** Never instantiate LLM clients or `UiPath()` at module level — `uip codedagents init` imports the file at scaffold time and module-level clients will fail because auth has not run yet.

### Low-Code Agents Only

- **No `pyproject.toml` needed.** Low-code agents do not use Python packaging.
- **No framework selection.** Low-code uses UiPath's built-in ReAct engine (`basic-v2`), powered by LangGraph under the hood. The developer never interacts with LangGraph directly.
- **The entrypoint is always `agent.json`.** Use it wherever a coded agent would use `main` or another named entrypoint.
- **`entry-points.json` is generated automatically.** Studio Web creates it on pull; `uip codedagents init` regenerates it from `agent.json`. Required for `push`/`deploy` but not for local `run`. Do not hand-edit it.
- **`bindings.json` maps resource names to Orchestrator paths.** Same format as coded agents — generated by `uip codedagents init` and used for environment-specific resource overrides at deploy time.

---

## Troubleshooting

| Error | Agent Type | Cause | Solution |
|-------|-----------|-------|----------|
| `Project authors cannot be empty` | Coded | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` |
| `Version already exists` on deploy | Coded | Same version already published | Bump patch version in `pyproject.toml` (e.g. `0.0.1` → `0.0.2`) |
| `Your local version is behind...Aborted!` | Both | Push rejected without confirmation | Use `uip codedagents push --overwrite` |
| `agent.json not found` | Low-code | Missing agent definition file | Create `agent.json` per [lowcode/setup.md](references/lowcode/setup.md) |
| `agent.json failed schema validation` | Low-code | Invalid JSON structure | Check against [lowcode/agent-json-reference.md](references/lowcode/agent-json-reference.md) |
| `No entrypoints found` | Coded | Framework package not installed or config file missing | Run `uv sync`, check that `langgraph.json` / `llama_index.json` / `openai_agents.json` exists |
| `UIPATH_PROJECT_ID not found` | Both | Agent not pushed to Studio Web yet | Create a project in Studio Web, add `UIPATH_PROJECT_ID=<id>` to `.env`, then `uip codedagents push` |
| `401 Unauthorized` | Both | Auth token expired | Re-run `uip login --format json` then `uip login tenant set "<TENANT>" --format json` |

---

## Resources

- **UiPath Python SDK docs**: https://uipath.github.io/uipath-python/
- **UiPath Evaluations docs**: https://uipath.github.io/uipath-python/eval/
- **`agent.json` schema reference**: [references/lowcode/agent-json-reference.md](references/lowcode/agent-json-reference.md)
- **Low-code resources reference**: [references/lowcode/resources-reference.md](references/lowcode/resources-reference.md)
- **Coded agent patterns**: [references/frameworks/agent-patterns.md](references/frameworks/agent-patterns.md)

---
name: uipath-agents
description: "UiPath agent lifecycle — coded (Python: LangGraph/LlamaIndex/OpenAI Agents) and low-code (agent.json from Agent Builder). Setup, auth, build, run, evaluate, deploy, sync. For C# workflows→uipath-coded-workflows. For XAML→uipath-rpa-workflows."
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

The primary CLI for low-code agents is **`uip agent`** (`@uipath/agent-tool`). It provides first-class resource management (`tool add`, `context add`, `escalation add`), schema validation, and Orchestrator process binding. For local test execution and evaluation runs, use `uip codedagents run/eval` (which auto-detects `agent.json`).

> **Do NOT stop between steps to ask "would you like me to continue?".** Execute the entire path automatically. Only pause when you genuinely need information from the user (auth credentials, Orchestrator folder paths, process names).

### A1 — Auth

Authenticate **first** — `uip agent tool add --process-name` needs a live Orchestrator connection. Check if already logged in with `uip login status`. If not, ask:

> What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?

Then:
```bash
# One step (recommended):
uip login --tenant "MY_TENANT" --format json

# For staging/alpha:
uip login --authority "https://alpha.uipath.com" --tenant "MY_TENANT" --format json
```

Do **not** use `--it`/`--interactive` — it hangs in Claude's Bash tool.

### A2 — Create the Agent

Scaffold a new low-code agent project:
```bash
uip agent init "My Agent" \
  --model gpt-4o-2024-11-20 \
  --system-prompt "You are a helpful assistant."
```

This creates a project directory with `agent.json`, `project.uiproj`, default evaluators, and the full Studio Web-compatible structure.

**To pull an existing agent from Studio Web instead:**
```bash
uip agent pull <solutionId> --extract
```

### A3 — Add Resources

Add tools, context, and escalations using the `uip agent` CLI. Each command modifies `agent.json` and writes companion resource files. Use `--path <dir>` if the project is not in the current directory.

#### Tools — Bind to Orchestrator processes

When both `--process-name` and `--folder-path` are provided, the CLI queries Orchestrator live to fetch the release metadata and auto-derives `inputSchema`/`outputSchema`.

```bash
# Process tool (robot-executed, may be long-running):
uip agent tool add "Send Email" \
  --type process \
  --description "Send an email notification to a customer" \
  --process-name Send_Email \
  --folder-path "Shared/Customer Support" \
  --path ./my-agent

# API workflow tool (synchronous return):
uip agent tool add "Get CRM Data" \
  --type apiWorkflow \
  --description "Look up customer complaints from CRM" \
  --process-name GetCustomerComplaintsFromCRM \
  --folder-path "Shared/Customer Support" \
  --path ./my-agent
```

**Tool types:** `process`, `agent`, `apiWorkflow`, `processOrchestration`, `ixp`, `integration`.

**Integration Service tools** use `--connector` instead of `--process-name`:
```bash
uip agent tool add "Create Jira Ticket" \
  --connector ServiceNow \
  --connection-id "a1b2c3d4-..." \
  --object-name CreateIncident \
  --path ./my-agent
```

#### Context — RAG over knowledge indexes

```bash
uip agent context add "IT Knowledge Base" \
  --index it-runbooks \
  --retrieval-mode semantic \
  --threshold 0.3 \
  --result-count 5 \
  --path ./my-agent
```

Retrieval modes: `semantic` (default), `structured`, `deeprag`, `batchtransform`.

#### Escalations — Human-in-the-loop

```bash
uip agent escalation add "Manager Approval" \
  --description "Escalate when action exceeds agent authority" \
  --path ./my-agent
```

#### Configure prompts and model

```bash
uip agent config set systemPrompt "You are an enterprise IT Service Desk agent." --path ./my-agent
uip agent config set model "gpt-4o-2024-11-20" --path ./my-agent
```

#### Validate

```bash
uip agent validate ./my-agent
```

Read the full `agent.json` schema reference: [lowcode/agent-json-reference.md](references/lowcode/agent-json-reference.md)
All resource types with examples: [lowcode/resources-reference.md](references/lowcode/resources-reference.md)

### A4 — Run Locally

Test the agent using the Python CLI (auto-detects `agent.json`):
```bash
uip codedagents run agent.json '{"input": "How do I reset my password?"}'
```

The entrypoint for low-code agents is **always `agent.json`**. Input fields must match `inputSchema` in `agent.json`.

Read [lifecycle/running-agents.md](references/lifecycle/running-agents.md).

### A5 — Add Evaluations

Add test cases using the CLI:
```bash
uip agent eval add "password-reset-question" \
  --set "Default Evaluation Set" \
  --inputs '{"input": "How do I reset my corporate email password?"}' \
  --expected '{"content": "Visit sso.corp.com/reset or contact IT helpdesk."}' \
  --path ./my-agent
```

Then run evaluations locally:
```bash
uip codedagents eval agent.json evaluations/eval-sets/smoke-test.json --no-report
```

Add `--report` (and ensure `UIPATH_PROJECT_ID` is set in `.env`) to publish results to Studio Web.

Read [lifecycle/evaluate.md](references/lifecycle/evaluate.md) and the [evaluators reference](references/lifecycle/evaluations/evaluators.md).

### A6 — Push to Studio Web

```bash
uip agent push ./my-agent --name "My Agent v1" --skip-schema-validation
```

This imports the project into Studio Web for visual editing, sharing, and collaboration. Use `--overwrite <solutionId>` to update an existing project.

### A7 — Publish and Deploy

```bash
# Publish (pack + upload to AutomationSolutions):
uip agent publish ./my-agent

# Deploy using the packageVersionKey returned by publish:
uip agent deploy <packageVersionKey>
```

**Alternative** — deploy directly via `uip codedagents`:
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

Then authenticate (choose one approach):
```bash
# One step — tenant name known:
uip login --tenant "MY_TENANT" --format json

# Two steps — if you prefer explicit confirmation:
uip login --format json
uip login tenant set "MY_TENANT" --format json
```

Do **not** use `--it`/`--interactive` — it opens an interactive picker that hangs in Claude's Bash tool.

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

- **Never use `--it` / `--interactive` on `uip login` from Claude's Bash tool** — it opens an interactive terminal picker that hangs indefinitely. Use one of these instead:
  - **One step** (when tenant name is known): `uip login --tenant "MY_TENANT" --format json`
  - **Two step** (explicit): `uip login --format json` → `uip login tenant set "MY_TENANT" --format json`
  - **Discovery** (tenant unknown): `uip login --format json` (auto-selects first tenant) → `uip login tenant list --format json` → present names to user → `uip login tenant set "NAME" --format json`
  - Note: `uip login` without `--tenant` auto-selects the **first** tenant silently when multiple exist.
- **Skip auth if already authenticated.** Check if `.env` contains `UIPATH_URL` and `UIPATH_ACCESS_TOKEN`. If yes, skip auth.
- **Auth MUST be an interactive question (when needed).** Output ONLY this question as your entire response — no bullets, no status summaries, no "next steps":
  > What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?
- **Always create a smoke evaluation set.** Every agent must include `evaluations/eval-sets/smoke-test.json` with 2–3 basic test cases before deploying.

### Coded Agents Only

- **NEVER add a `[build-system]` section to `pyproject.toml`**. No `hatchling`, no `setuptools`. Only `[project]`, `[dependency-groups]`, and `[tool.*]` sections are valid.
- **Select a framework before writing any code.** If ambiguous, ask the user to choose from: Simple Function, LangGraph, LlamaIndex, or OpenAI Agents.
- **Correct SDK import: `from uipath.platform import UiPath`** — not `from uipath import UiPath` (that does not exist).
- **Correct HITL imports: `from uipath.platform.common import CreateTask, WaitTask, InvokeProcess, WaitJob`** — the old `CreateAction`/`WaitAction` names and `uipath.models` module no longer exist.
- **Correct `@mockable()` import: `from uipath.eval.mocks import mockable`** — not `from uipath.testing import mockable`.
- **Always use lazy LLM initialization.** Never instantiate LLM clients or `UiPath()` at module level — `uip codedagents init` imports the file at scaffold time and module-level clients will fail because auth has not run yet.
- **`uip codedagents pack` and `uip codedagents publish` as standalone commands are blocked** by the CLI wrapper. Use `uip codedagents deploy` (which runs them internally) instead.

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

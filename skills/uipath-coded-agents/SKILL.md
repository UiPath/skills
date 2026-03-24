---
name: uipath-coded-agents
description: "End-to-end toolkit for UiPath coded agents: scaffold projects, authenticate with UiPath Cloud, build agents using LangGraph/LlamaIndex/OpenAI Agents SDK, manage bindings, run locally, evaluate with built-in evaluators, deploy to Orchestrator, and sync with Studio Web. TRIGGER when: User wants to create, build, run, evaluate, or deploy a UiPath coded agent (Python); User mentions coded agents, Python agents, LangGraph, LlamaIndex, OpenAI Agents in a UiPath context; User asks about agent scaffolding, agent evaluation, agent deployment to Orchestrator, or Studio Web sync for agents; User asks about UiPath Python SDK, uipath CLI for agents, bindings.json, or agent entry points. DO NOT TRIGGER when: User is working with coded workflows (.cs files with [Workflow]/[TestCase] attributes — use uipath-coded-workflows instead); User is working with XAML/RPA workflows (use uipath-rpa-workflows instead); User asks about Orchestrator management without agent context (use uipath-platform instead)."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Coded Agents

## Critical Rules

- **NEVER add a `[build-system]` section to `pyproject.toml`**. No `hatchling`, no `setuptools`, no build backend. UiPath agents do not use a build system. Only include `[project]`, `[dependency-groups]`, and `[tool.*]` sections.
- **Always create a smoke evaluation set.** Every agent must include `evaluations/eval-sets/smoke-test.json` with 2-3 basic test cases. Create it in the Evaluate step, not during Build.
- **Select a framework before writing any code.** If the prompt clearly implies a framework (e.g., mentions tools, RAG, multi-step orchestration, or a specific SDK), pick the best match. If the prompt is ambiguous, ask the user to choose from: Simple Function, LangGraph, LlamaIndex, or OpenAI Agents.
- **NEVER run `uipath auth` without `--tenant`.** The interactive tenant picker does not work from Claude's Bash tool. Always ask the user for environment, organization, and tenant name first, then run `uv run uipath auth --cloud --tenant <TENANT>`.
- **Skip auth if already authenticated.** Before asking for credentials, check if `.env` contains `UIPATH_URL` and `UIPATH_ACCESS_TOKEN` (or run `uv run uipath auth --status` if available). If auth is already configured, skip the Auth step entirely and continue the flow.
- **Auth MUST be an interactive question (when needed).** If auth is NOT configured, your ENTIRE response must be a single direct question. Do NOT wrap it in bullet points, "Next Steps" headers, or status summaries. Just ask and stop:

  > What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?

## Lifecycle Stages

| Stage | Description | CLI Commands |
|-------|-------------|-------------|
| **Auth** | Authenticate with UiPath Cloud | `uv run uipath auth` |
| **Setup** | Scaffold project | `uv run uipath new <name>`, `uv sync`, `uv run uipath init` |
| **Build** | Implement agent logic with framework patterns | Code agent logic |
| **Bindings** | Sync resource overrides in `bindings.json` | Scan code, update bindings |
| **Run** | Test locally | `uv run uipath run` |
| **Evaluate** | Run evaluations | `uv run uipath eval` |
| **Deploy** | Publish to Orchestrator | `uv run uipath deploy`, `uv run uipath invoke` |
| **Sync** | Push/pull with Studio Web | `uv run uipath push`, `uv run uipath pull` |

## One-Prompt Flow

When the user asks to create and deploy an agent end-to-end, follow these steps in order. Skip stages that are already done.

**IMPORTANT: Do NOT stop between steps to ask "would you like me to continue?" or list next steps. Execute the entire flow automatically. Only pause when you genuinely need information from the user (auth credentials, project ID). After getting that info, resume immediately.**

1. **Framework** — Select framework from prompt context or ask user (see Framework Selection below). This MUST happen before setup because `uipath new` scaffolds based on which framework package is installed.
2. **Setup** — Scaffold project: add framework dependency (`uv add uipath-langchain` etc.), `uv sync`, `uv run uipath new <project-name>`, then run `uv run uipath init && rm -rf CLAUDE.md .agent .claude CLI_REFERENCE.md SDK_REFERENCE.md AGENTS.md REQUIRED_STRUCTURE.md`. Infer the project name from the user's prompt or the current directory name. **Do NOT authenticate yet** — auth happens after build.
3. **Build** — Implement agent logic using the selected framework's patterns. **CRITICAL: Always use lazy LLM initialization.** Never instantiate `UiPathAzureChatOpenAI`, `UiPathChat`, `UiPathChatOpenAI`, or any LLM client at module level — `uipath init` imports the file and module-level LLM clients will fail because auth hasn't happened yet. Always create LLM instances inside functions/nodes. After implementing, re-run `uv run uipath init && rm -rf CLAUDE.md .agent .claude CLI_REFERENCE.md SDK_REFERENCE.md AGENTS.md REQUIRED_STRUCTURE.md` to update schemas from the actual code.
4. **Bindings** — If the agent uses any UiPath platform resources (assets, queues, connections, processes, buckets, context grounding indexes, Action Center apps, or MCP servers), sync `bindings.json` with the code using the Bindings section below. This ensures resource overrides work correctly when deployed to Orchestrator. Skip this step if the agent does not call any bindable SDK methods.
5. **Auth** — First check if `.env` already has `UIPATH_URL` and auth tokens. If yes, skip this step. If not, ask the user for credentials — output ONLY this question as your entire response:

> What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?

Then STOP and wait for the user to reply. After they reply, run `uv run uipath auth --<env> --tenant <TENANT>` and continue the flow. Never run `uipath auth` without `--tenant`.
6. **Run** — Test locally with `uv run uipath run <ENTRYPOINT> '<input>'` (use the entrypoint name from `entry-points.json`, e.g., `main`).
7. **Push** — Tell the user to navigate to `{UIPATH_URL without tenant segment}/studio_/projects`, create a new **Coded Agent** project, and paste the project ID. Add `UIPATH_PROJECT_ID=<id>` to `.env`, then run `uv run uipath push`. Required before evals. *(This step requires user input — wait for the project ID, then resume immediately.)*
8. **Evaluate** — Create **both** the evaluator config and the eval set, then run evals.

   **First**, create `evaluations/evaluators/llm-judge-trajectory.json`:
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

   **Then**, create `evaluations/eval-sets/smoke-test.json` with 2-3 test cases based on the agent's input schema (version is string `"1.0"`, top-level `id`/`name` required, test cases in `evaluations` array):
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

   **Finally**, run `uv run uipath eval <ENTRYPOINT> evaluations/eval-sets/smoke-test.json` (use the entrypoint name from `entry-points.json`).
9. **Deploy** — Run `uv run uipath deploy --my-workspace`. Do NOT ask the user which feed to use — default to `--my-workspace` and inform them: "Deploying to your personal workspace." If re-deploying, bump the patch version in `pyproject.toml` first.

Read the relevant references at each step — do not guess.

## Framework Selection

Infer the framework from the user's prompt when possible. If ambiguous, ask them to choose:

1. **Simple Function** — Plain Python with `Input`/`Output` models. No LLM. Best for deterministic logic.
2. **LangGraph** — StateGraph with conditional routing, tool use, interrupts. Best for complex LLM agents.
3. **LlamaIndex** — Workflow with events and RAG support. Best for knowledge retrieval.
4. **OpenAI Agents** — Lightweight agent with tools and handoffs. Best for simple LLM agents.

**Inference hints:** mentions of tools/tool calling, multi-step, or orchestration → LangGraph. RAG or knowledge retrieval → LlamaIndex. Simple handoffs or lightweight LLM → OpenAI Agents. No LLM needed → Simple Function. When in doubt, ask.

**Always tell the user which framework you selected and why** before proceeding to build. Example: "I'll use **LangGraph** for this agent since it involves tool calling and multi-step orchestration."

---

## Auth

Set up authentication with UiPath Cloud or on-premise before running cloud commands.

```bash
# Interactive OAuth (recommended)
uv run uipath auth --cloud --tenant MY_TENANT

# Unattended (automation/CI)
uv run uipath auth --client-id ID --client-secret SECRET --base-url URL
```

**Reference:** [Authentication Guide](references/authentication.md) — Interactive OAuth, unattended credentials, environment modes, proxy settings, troubleshooting.

---

## Setup

Scaffold a new project or initialize an existing one for UiPath agent development.

```bash
# New project from scratch
mkdir my-agent && cd my-agent
# Copy pyproject.toml template, add framework dep if needed, then:
uv sync
uv run uipath new my-agent       # name is REQUIRED
uv run uipath init && rm -rf CLAUDE.md .agent .claude CLI_REFERENCE.md SDK_REFERENCE.md AGENTS.md REQUIRED_STRUCTURE.md

# Existing project — just generate entry points
uv run uipath init
```

**STOP: You must know which framework to use before running setup.** If no framework has been selected yet, ask the user to choose. The framework determines which dependency to add and what `uipath new` scaffolds.

A `pyproject.toml` template is available in [assets/templates/pyproject.toml](assets/templates/pyproject.toml). Replace `{AGENT_NAME}` and `{AGENT_DESCRIPTION}` after copying.

**Reference:** [Project Setup Guide](references/setup.md) — Prerequisites, agent types, scaffolding, `uipath.json` structure.

---

## Build

Implement agent logic using UiPath SDK and framework-specific patterns.

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

| Framework | Config File | Key Dependency | Entry Point |
|-----------|------------|----------------|-------------|
| Simple Function | `uipath.json` | `uipath` | `main.py` function |
| LangGraph | `langgraph.json` | `uipath-langchain` | `main.py` compiled StateGraph |
| LlamaIndex | `llama_index.json` | `uipath-llamaindex` | `main.py` Workflow instance |
| OpenAI Agents | `openai_agents.json` | `uipath-openai-agents` | `main.py` Agent instance |

**NEVER instantiate LLM clients at module level.** `uipath init` imports your Python file — module-level `UiPathAzureChatOpenAI()`, `UiPathChat()`, or `UiPathChatOpenAI()` will fail. Always create LLM instances inside functions or graph nodes.

---

## Bindings

Synchronize UiPath platform resource references in agent Python code with the `bindings.json` manifest. This ensures all overridable resources (assets, queues, connections, processes, buckets, context grounding indexes, Action Center apps, and MCP servers) are correctly declared for runtime replacement in Orchestrator.

### When to Use

- After adding, removing, or modifying UiPath SDK resource calls in agent code
- Before packaging/deploying an agent
- When resource override configuration in Orchestrator is missing entries or shows stale resources

### Bindings Workflow

1. **Locate Project Files** — Find `pyproject.toml`, glob `**/*.py` (exclude `.venv/`, `__pycache__/`, `.uipath/`), locate `bindings.json` and `entry-points.json`
2. **Scan Code for Resource Calls** — Search for SDK resource calls (assets, queues, connections, processes, buckets, context grounding, tasks, MCP servers). See `references/bindings-reference.md` for the full method pattern table.
3. **Compare with Existing Bindings** — Identify missing, stale, and mismatched entries
4. **Resolve Entrypoint Bindings** — Link resources to entrypoints from `entry-points.json`
5. **Update bindings.json** — Add/remove/update entries after user confirmation
6. **Verify** — Read back and validate JSON, confirm all code resources have matching bindings

**Reference:** [Bindings Reference](references/bindings-reference.md) — Full JSON schema, all eight resource type templates, SDK method signatures, worked example.

---

## Run

Execute agents locally for testing or invoke published agents in UiPath Cloud.

```bash
# Run locally — ENTRYPOINT is the name from entry-points.json, NOT the project name
uv run uipath run <ENTRYPOINT> '{"query": "test"}'

# Run with file input
uv run uipath run <ENTRYPOINT> --file input.json

# Invoke published agent in cloud
uv run uipath invoke <ENTRYPOINT> '{"query": "test"}'
```

**IMPORTANT:** The entrypoint name comes from `entry-points.json` (e.g., `main`, `agent`). It is NOT the project or package name.

**Reference:** [Running Agents Guide](references/running-agents.md) — Run vs Invoke, agent discovery, input validation, result display.

---

## Evaluate

Design and run tests for your agents using the UiPath evaluation framework.

### Local-only vs Studio Web

- **Local-only** — No authentication or `UIPATH_PROJECT_ID` needed. Use `--no-report` flag. Skip auth checks entirely.
- **Studio Web** — Requires authentication and `UIPATH_PROJECT_ID` in `.env` (obtained via `uv run uipath push`).

```bash
# Run evaluations locally (no cloud connection needed)
uv run uipath eval <ENTRYPOINT> evaluations/eval-sets/smoke-test.json --no-report --workers 4

# Report results to Studio Web (requires auth + UIPATH_PROJECT_ID)
uv run uipath eval <ENTRYPOINT> evaluations/eval-sets/smoke-test.json --report --workers 4
```

### File Structure

```
evaluations/
├── eval-sets/
│   └── smoke-test.json              # Test cases
└── evaluators/
    └── llm-judge-trajectory.json    # Evaluator config (REQUIRED)
```

**Every evaluator referenced in `evaluatorRefs` must have a matching config file in `evaluations/evaluators/`.** The `id` field in the config must match the `evaluatorRefs` value exactly.

### Mocking External Calls

Apply `@mockable()` to functions that call external services:

```python
from uipath.testing import mockable

@mockable(example_calls=[
    {"args": {"query": "weather in NYC"}, "return_value": {"temp": 72, "condition": "sunny"}},
])
def fetch_weather(query: str) -> dict:
    return call_weather_api(query)
```

**References:**
- [Evaluators Reference](references/evaluators.md) — All evaluator types, configs, scoring
- [Evaluation Sets](references/evaluation-sets.md) — Test case format, mocking strategies
- [Creating Evaluations](references/creating-evaluations.md) — Test case design
- [Running Evaluations](references/running-evaluations.md) — Command options, troubleshooting
- [Best Practices](references/best-practices.md) — Patterns by agent type, CI/CD

---

## Deploy

Package, publish, and invoke your agents in UiPath Cloud.

```bash
# Pack + publish in one command
uv run uipath deploy --my-workspace

# Or step by step
uv run uipath pack
uv run uipath publish --my-workspace

# Invoke published agent — use entrypoint name from entry-points.json, NOT project name
uv run uipath invoke <ENTRYPOINT> '{"query": "test"}'
```

### Prerequisites

- Authentication configured
- `entry-points.json` exists (run `uv run uipath init`)
- `pyproject.toml` has `name`, `version`, `description`, `authors`

**Reference:** [Deployment Guide](references/deployment.md) — Pack, publish, deploy, invoke, pack options, configuration.

---

## Sync

Sync project files between local development and remote Studio Web storage.

```bash
# Pull remote files to local
uv run uipath pull

# Push local files to remote (mirrors local state)
uv run uipath push

# Force overwrite without prompts
uv run uipath push --overwrite
uv run uipath pull --overwrite
```

### Prerequisites

- Authentication configured
- `UIPATH_PROJECT_ID` set in `.env` or environment

**Reference:** [File Sync Guide](references/file-sync.md) — Push/pull commands, conflict resolution, common workflows.

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Project authors cannot be empty` | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` section |
| `Version already exists` on deploy | Same version already published | Bump patch version in `pyproject.toml` before re-deploying |
| `Your local version is behind...Aborted!` | Push needs interactive confirmation | Use `uv run uipath push --overwrite` to force push |
| `401 Unauthorized` | Token expired or wrong tenant | Re-run `uv run uipath auth --cloud --tenant <TENANT>` |
| `UIPATH_URL not found` | `.env` missing or not in project root | Check `.env` exists with `UIPATH_URL` set |
| `UIPATH_PROJECT_ID not found` | Agent not pushed to Studio Web | Push first with `uv run uipath push` and set `UIPATH_PROJECT_ID=<id>` in `.env` |
| `typing.Any must be a subclass of BaseEvaluatorConfig` | Invalid `evaluatorTypeId` | Check `references/evaluators.md` for valid evaluator type IDs |
| `No entrypoints found in uipath.json` | Framework package not installed | Ensure framework dep is installed and config file exists |
| `Invalid input` | JSON doesn't match Input schema | Check `entry-points.json` for expected fields and types |
| `'dict' has no attribute '...'` | `with_structured_output()` returns dict | Use `result['key']` dict syntax, not `result.key` |

## Resources

- **UiPath Python SDK**: https://uipath.github.io/uipath-python/
- **UiPath Evaluations**: https://uipath.github.io/uipath-python/eval/

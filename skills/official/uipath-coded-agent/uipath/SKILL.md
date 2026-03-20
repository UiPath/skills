---
name: uipath
description: UiPath coded agents lifecycle assistant. Orchestrates setup, auth, build, bindings, run, evaluate, deploy, and sync for UiPath Python agents. Use when the user wants to create a new agent from scratch or manage the full lifecycle, e.g. "create a UiPath agent", "set up and deploy an agent", or "build and run a new agent end-to-end".
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
user-invocable: true
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

Each stage is an independent skill. Invoke any stage directly or let this skill orchestrate the full flow.

| Stage | Skill | CLI Commands |
|-------|-------|-------------|
| **Auth** | [Auth](/uipath-coded-agents:auth) | `uv run uipath auth` |
| **Setup** | [Setup](/uipath-coded-agents:setup) | `uv run uipath new <name>`, `uv sync`, `uv run uipath init` |
| **Build** | [Build](/uipath-coded-agents:build) | Code agent logic with framework patterns |
| **Bindings** | [Bindings](/uipath-coded-agents:bindings) | Sync resource overrides in `bindings.json` |
| **Run** | [Run](/uipath-coded-agents:run) | `uv run uipath run` |
| **Evaluate** | [Evaluate](/uipath-coded-agents:evaluate) | `uv run uipath eval` |
| **Deploy** | [Deploy](/uipath-coded-agents:deploy) | `uv run uipath deploy`, `uv run uipath invoke` |
| **Sync** | [Sync](/uipath-coded-agents:sync) | `uv run uipath push`, `uv run uipath pull` |

## One-Prompt Flow

When the user asks to create and deploy an agent end-to-end, follow these steps in order. Skip stages that are already done.

**IMPORTANT: Do NOT stop between steps to ask "would you like me to continue?" or list next steps. Execute the entire flow automatically. Only pause when you genuinely need information from the user (auth credentials, project ID). After getting that info, resume immediately.**

1. **Framework** — Select framework from prompt context or ask user (see below). This MUST happen before setup because `uipath new` scaffolds based on which framework package is installed.
2. **Setup** — Scaffold project: add framework dependency (`uv add uipath-langchain` etc.), `uv sync`, `uv run uipath new <project-name>`, then run `uv run uipath init && rm -rf CLAUDE.md .agent .claude CLI_REFERENCE.md SDK_REFERENCE.md AGENTS.md REQUIRED_STRUCTURE.md`. Infer the project name from the user's prompt or the current directory name. **Do NOT authenticate yet** — auth happens after build.
3. **Build** — Implement agent logic using the selected framework's patterns. **CRITICAL: Always use lazy LLM initialization.** Never instantiate `UiPathAzureChatOpenAI`, `UiPathChat`, `UiPathChatOpenAI`, or any LLM client at module level — `uipath init` imports the file and module-level LLM clients will fail because auth hasn't happened yet. Always create LLM instances inside functions/nodes. After implementing, re-run `uv run uipath init && rm -rf CLAUDE.md .agent .claude CLI_REFERENCE.md SDK_REFERENCE.md AGENTS.md REQUIRED_STRUCTURE.md` to update schemas from the actual code.
4. **Bindings** — If the agent uses any UiPath platform resources (assets, queues, connections, processes, buckets, context grounding indexes, Action Center apps, or MCP servers), sync `bindings.json` with the code using the [Bindings](/uipath-coded-agents:bindings) skill. This ensures resource overrides work correctly when deployed to Orchestrator. Skip this step if the agent does not call any bindable SDK methods.
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

Read the relevant skill's references at each step — do not guess.

## Framework Selection

Infer the framework from the user's prompt when possible. If ambiguous, ask them to choose:

1. **Simple Function** — Plain Python with `Input`/`Output` models. No LLM. Best for deterministic logic.
2. **LangGraph** — StateGraph with conditional routing, tool use, interrupts. Best for complex LLM agents.
3. **LlamaIndex** — Workflow with events and RAG support. Best for knowledge retrieval.
4. **OpenAI Agents** — Lightweight agent with tools and handoffs. Best for simple LLM agents.

**Inference hints:** mentions of tools/tool calling, multi-step, or orchestration → LangGraph. RAG or knowledge retrieval → LlamaIndex. Simple handoffs or lightweight LLM → OpenAI Agents. No LLM needed → Simple Function. When in doubt, ask.

**Always tell the user which framework you selected and why** before proceeding to build. Example: "I'll use **LangGraph** for this agent since it involves tool calling and multi-step orchestration."

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Project authors cannot be empty` | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` section |
| `Version already exists` on deploy | Same version already published | Bump patch version in `pyproject.toml` before re-deploying |
| `Your local version is behind...Aborted!` | Push needs interactive confirmation | Use `uv run uipath push --overwrite` to force push |

## Resources

- **UiPath Python SDK**: https://uipath.github.io/uipath-python/
- **UiPath Evaluations**: https://uipath.github.io/uipath-python/eval/

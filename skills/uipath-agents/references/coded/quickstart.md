# UiPath Coded Agents — Quickstart

For initial project scaffolding, follow [lifecycle/setup.md](lifecycle/setup.md) — it covers preflight, framework selection, starting points, and the workflow.

## CLI Conventions

| Command family | Accepts `--output json` |
|---|---|
| `uip login`, `uip login status`, `uip login tenant list`, `uip login tenant set`, `uip logout` | yes |
| `uip codedagent setup` | yes |
| `uip codedagent new`, `init`, `run`, `dev`, `eval`, `deploy`, `push`, `pull`, `invoke` | no (forwarded to the Python CLI) |

Use `uip codedagent <cmd>`, not `uv run uipath <cmd>`. The wrapper injects session credentials (`UIPATH_URL`, `UIPATH_ACCESS_TOKEN`, org/tenant identifiers) from your `uip login` session into the Python subprocess; `uv run uipath` skips that injection.

## Critical Rules

- **NEVER add a `[build-system]` section to `pyproject.toml`**. No `hatchling`, no `setuptools`, no build backend. UiPath agents do not use a build system. Only include `[project]`, `[dependency-groups]`, and `[tool.*]` sections.
- **Always create a smoke evaluation set.** Every agent must include `evaluations/eval-sets/smoke-test.json` with 2-3 test cases covering the primary happy path (not exhaustive error-case coverage — the smoke set exists to catch regressions, not to fully validate behavior). Create it in the Evaluate step, not during Build.
- **Select a framework before writing any code.** If the prompt clearly implies a framework (e.g., mentions tools, RAG, multi-step orchestration, or a specific SDK), pick the best match. If the prompt is ambiguous, ask the user to choose from: Coded Function, LangGraph, LlamaIndex, or OpenAI Agents.
- **Correct SDK import: `from uipath.platform import UiPath`** — not `from uipath import UiPath` (that path does not exist and will cause `ImportError`). Always instantiate `UiPath()` inside functions/nodes, never at module level.
- **Never prompt for credentials before checking session state.** Run `uip login status --output json` first; if the status is `Logged in`, skip the Auth step — the CLI injects credentials into every `uip codedagent` call automatically, so the `.env` file is not where auth lives.
- **NEVER run `uip login` without `--tenant`.** The interactive tenant picker does not work from Claude's Bash tool. Use the one-shot form `uip login --organization "<ORG>" --tenant "<TENANT>"`, mapping staging/alpha to `--authority` (see [../authentication.md](../authentication.md)).
- **Auth MUST be an interactive question (when needed).** If the session check fails, your ENTIRE response must be a single direct question. Do NOT wrap it in bullet points, "Next Steps" headers, or status summaries. Just ask and stop:

  > What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?

## Lifecycle Stages

Each stage has a reference file with detailed instructions. Read **only** the relevant reference when you reach that stage — do not preload.

| Stage | Reference | CLI Commands |
|-------|-----------|-------------|
| **Auth** | [../authentication.md](../authentication.md) | `uip login` |
| **Setup** | [lifecycle/setup.md](lifecycle/setup.md) | `uv venv --python 3.13`, `uv pip install <framework-package>`, `uip codedagent setup`, `uip codedagent new <name>`, `uv sync`, `uip codedagent init` |
| **Build** | [lifecycle/build.md](lifecycle/build.md) | Code agent logic with framework patterns |
| **Bindings** | [lifecycle/bindings-reference.md](lifecycle/bindings-reference.md) | Sync resource overrides in `bindings.json` |
| **Run** | [lifecycle/running-agents.md](lifecycle/running-agents.md) | `uip codedagent run` |
| **Evaluate** | [lifecycle/evaluate.md](lifecycle/evaluate.md) | `uip codedagent eval` |
| **Deploy** | [lifecycle/deployment.md](lifecycle/deployment.md) | `uip codedagent deploy`, `uip codedagent invoke` |
| **Sync** | [lifecycle/file-sync.md](lifecycle/file-sync.md) | `uip codedagent push`, `uip codedagent pull` |

## One-Prompt Flow

When the user asks to create and deploy an agent end-to-end, follow these steps in order. Skip stages that are already done.

**IMPORTANT: Do NOT stop between steps to ask "would you like me to continue?" or list next steps. Execute the entire flow automatically.** Pause only when (a) you hit an **architectural fork** — a step with multiple valid implementations (framework choice, HITL pattern, evaluator type, deploy target, conversational vs not, etc.) — or (b) you need data only the user has (credentials, project ID). At a fork, apply **infer-or-ask**: if the prompt or context names the choice, infer it and continue; otherwise output ONLY the choice question as your entire response, then STOP and wait. For missing data, output ONLY the data request. After getting the answer, resume immediately. Forks for each step are documented in that step's referenced file — read the reference when you reach the step; do not guess.

1. **Framework** — Select per the [Framework Selection](#framework-selection) section below. This MUST happen before setup because `uip codedagent new` scaffolds based on which framework package is installed.
2. **Setup** — Follow the Workflow in [lifecycle/setup.md](lifecycle/setup.md). Infer the project name from the user's prompt or the current directory. **Do NOT authenticate yet** — auth happens after build.
3. **Build** — Implement agent logic using the selected framework's patterns. Keep LLM and `UiPath()` clients inside functions/nodes, never at module level (see [lifecycle/build.md](lifecycle/build.md) § Additional Instructions). After implementing, re-run `uip codedagent init` to update schemas from the actual code.
4. **Bindings** — Sync `bindings.json` with the code using [lifecycle/bindings-reference.md](lifecycle/bindings-reference.md). The workflow scans for bindable resource calls (assets, queues, connections, processes, buckets, context grounding indexes, Action Center apps, MCP servers) and terminates silently if none are found — always run it.
5. **Auth** — Run `uip login status --output json`. If already `Logged in`, skip. Otherwise ask the user for credentials — output ONLY this question as your entire response:

> What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?

Then STOP and wait. On reply, run the matching one-shot login from [../authentication.md](../authentication.md) (maps environment → `--authority`). Never run `uip login` without `--tenant`.
6. **Run** — Test locally with `uip codedagent run <ENTRYPOINT> '<input>'` (use the entrypoint name from `entry-points.json`, e.g., `main`).
7. **Evaluate** — Create **both** the evaluator config and the eval set, then run evals locally (with `--no-report`).

   **First**, create `evaluations/evaluators/llm-judge-trajectory.json`. If the default `model` below is not available in the user's tenant, call `sdk.agenthub.get_available_llm_models()` and substitute a `model_name` from the returned list.

   ```json
   {
     "version": "1.0",
     "id": "LLMJudgeTrajectoryEvaluator",
     "evaluatorTypeId": "uipath-llm-judge-trajectory-similarity",
     "evaluatorConfig": {
       "name": "LLMJudgeTrajectoryEvaluator",
       "model": "gpt-4o-mini-2024-07-18",
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

   **Finally**, run `uip codedagent eval <ENTRYPOINT> evaluations/eval-sets/smoke-test.json --no-report` (use the entrypoint name from `entry-points.json`).
8. **Push to Studio Web (optional)** — Ask: *"Do you want to upload the agent to Studio Web?"* If they decline, skip this step. If yes, ask which path:

   **A. User sets up the Studio Web project.** The user opens Studio Web, opens or creates a solution, creates a **Coded Agent** project inside it, and pastes the project ID. Add `UIPATH_PROJECT_ID=<id>` to `.env`, then run `uip codedagent push`. *(Wait for the project ID, then resume.)*

   **B. Create a local solution and upload it.** No Studio Web setup needed. `uip solution new "<SOLUTION_NAME>"` creates `<cwd>/<SOLUTION_NAME>/<SOLUTION_NAME>.uipx` — a sibling subdirectory of the agent, not an ancestor — so the agent must be copied into the solution tree before upload. `uip solution upload` archives the directory verbatim and does NOT honor `packOptions.directoriesExcluded`; an unstripped `.venv` fails with `code 20001: solution archive is corrupt`. From the parent directory of the agent project:

   ```bash
   uip solution new "<SOLUTION_NAME>"                                     # creates <SOLUTION_NAME>/<SOLUTION_NAME>.uipx
   cd "<SOLUTION_NAME>"
   uip solution project import --source "../<AGENT_PROJECT_DIR>" --output json
   # strip dev/runtime artifacts from the imported copy before upload
   rm -rf "<AGENT_PROJECT_DIR>/.venv" "<AGENT_PROJECT_DIR>/__pycache__" \
          "<AGENT_PROJECT_DIR>/__uipath" "<AGENT_PROJECT_DIR>/eval-results.json"
   uip solution upload . --output json
   ```
9. **Deploy** — *Only if the user wants the agent deployed.* Ask which target: personal workspace (`--my-workspace`), tenant feed (`--tenant`), or a specific folder (`--folder "<Name>"`). Run `uip codedagent deploy <target-flag>`. If re-deploying, bump the patch version in `pyproject.toml` first.

Read the relevant reference file at each step — do not guess.

## Framework Selection

Infer the framework from the user's prompt when possible. If ambiguous, ask them to choose:

1. **Coded Function** — Plain Python with `Input`/`Output` models. No LLM. Best for deterministic logic.
2. **LangGraph** — StateGraph with conditional routing, tool use, interrupts. Best for complex LLM agents.
3. **LlamaIndex** — Workflow with events and RAG support. Best for knowledge retrieval.
4. **OpenAI Agents** — Lightweight agent with tools and handoffs. Best for simple LLM agents.

**Inference hints:** mentions of tools/tool calling, multi-step, or orchestration → LangGraph. RAG or knowledge retrieval → LlamaIndex. Simple handoffs or lightweight LLM → OpenAI Agents. No LLM needed → Coded Function. When in doubt, ask.

**Always tell the user which framework you selected and why** before proceeding to build. Example: "I'll use **LangGraph** for this agent since it involves tool calling and multi-step orchestration."

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Project authors cannot be empty` | Missing `authors` in `pyproject.toml` | Add `authors = [{ name = "Your Name" }]` to `[project]` section |
| `Version already exists` on deploy | Same version already published | Bump patch version in `pyproject.toml` before re-deploying |
| `Your local version is behind...Aborted!` | Push needs interactive confirmation | Use `uip codedagent push --overwrite` to force push |

## Resources

- **UiPath Python SDK**: https://uipath.github.io/uipath-python/
- **UiPath Evaluations**: https://uipath.github.io/uipath-python/eval/

# UiPath Coded Agents — Quickstart

For initial project scaffolding, follow [lifecycle/setup.md](lifecycle/setup.md) — it covers preflight, framework selection, starting points, and the workflow.

## Project State Detection (run once, before step 1)

Inspect the working directory and its ancestors. Compute the variables below — every later step branches on them. Re-running the flow is safe: each step is gated on these signals and skips itself when its work is already done.

| Variable | How to detect | Used by |
|---|---|---|
| `project_state` | `local-workspace` if any ancestor contains `.sw-path-marker` or `.local/folder.lock` (Studio Web–specific markers — `*.uipx` alone does NOT qualify). Else `existing-coded` if cwd has `pyproject.toml` with `uipath` dep + a `<framework>.json`. Else `greenfield`. | Steps 1, 2, 3, 8, 9 |
| `framework` | Read from existing `<framework>.json` (`langgraph.json` / `llama_index.json` / `openai_agents.json` / `uipath.json` with `functions`). `none` if absent. | Step 1 |
| `has_venv` | `.venv/` exists in cwd | Step 2 |
| `has_entry_points` | `entry-points.json` exists | Steps 2, 6 |
| `has_bindings` | `bindings.json` exists | Step 4 |
| `has_smoke_set` | `evaluations/eval-sets/smoke-test.json` exists | Step 7 |
| `has_evaluators` | any `evaluations/evaluators/*.json` exists | Step 7 |
| `has_project_id` | `.env` contains `UIPATH_PROJECT_ID=<guid>` | Step 8 |

When `project_state == local-workspace`, also read [lifecycle/local-workspace.md](lifecycle/local-workspace.md) for files-owned-by-Studio-Web and anti-patterns. The lifecycle itself is the One-Prompt Flow below — Local Workspace differs at step 8 (auto-sync replaces options A and B; the user is asked only C or Skip) and at step 9 (deploy options remain available, but Studio Web's publish-from-UI button is the most common path).

**State signals are recomputed implicitly by reading the filesystem at the step that consumes them.** Steps that mutate state (Setup creates `.venv`; Build/Run can rerun `init` and update `entry-points.json`; Evaluate creates `evaluations/`; Delivery may write `UIPATH_PROJECT_ID` to `.env`) update the underlying files; later steps read fresh values, not the initial table. Treat the table above as a snapshot at flow start, not a frozen contract.

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
- **Refresh the CLI's Python executable path after venv changes.** If `uip codedagent` reports that the UiPath CLI/Python executable is not recognized, or any error indicates a stale `uipathExePath`, activate the project venv and run `uip codedagent setup --force`. This rewrites the CLI configuration to point at the current `.venv` executable.
- **Auth check is one-shot.** Run `uip login status --output json` once, at step 5. The wrapper auto-refreshes tokens on subsequent cloud calls (no `uip login refresh` exists). Re-auth only on a real `401`.
- **Use `uip codedagent run` from non-interactive shells.** `uip codedagent dev` auto-appends `--interactive`.
- **Runtime captures only the last node's delta as output.** `Annotated[list, operator.add]` reducers accumulate inside the graph but vanish from `--output-file` JSON and eval trajectories. Carry aggregate fields forward in each node's return (`{"items": [*state.get("items", []), x]}`) — see [frameworks/langgraph-integration.md](frameworks/langgraph-integration.md) § Runtime Output Quirk.
- **Verify the JSON, not the streamed display.** After `uip codedagent run --output-file out.json`, inspect `out.json` — the streamed view shows per-node deltas; the JSON is the runtime's actual final result. Mismatches expose the runtime quirk above.
- **Use `uip codedagent deploy` for packaging/publishing.** `uip codedagent pack` and `uip codedagent publish` are filtered by the wrapper.
- **NEVER run `uip login` without `--tenant`.** The interactive tenant picker does not work from Claude's Bash tool. Use the one-shot form `uip login --organization "<ORG>" --tenant "<TENANT>"`, mapping staging/alpha to `--authority` (see [../authentication.md](../authentication.md)).
- **Auth MUST be an interactive question (when needed).** If the session check fails, your ENTIRE response must be a single direct question. Do NOT wrap it in bullet points, "Next Steps" headers, or status summaries. Just ask and stop:

  > What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?
- **In a flow, coded agents are referenced via the [`agent`](../../../uipath-maestro-flow/references/plugins/agent/) plugin** — node type `uipath.core.agent.{key}`, `Orchestrator.StartAgentJob`. See [flow-integration.md](flow-integration.md) for the three patterns: in-solution sibling folder, Orchestrator-published, tool resource.

## Lifecycle Stages

Each stage has a reference file with detailed instructions. Read **only** the relevant reference when you reach that stage — do not preload.

| Stage | Reference | CLI Commands |
|-------|-----------|-------------|
| **Auth** | [../authentication.md](../authentication.md) | `uip login` |
| **Setup** | [lifecycle/setup.md](lifecycle/setup.md) | `uv venv --python 3.13`, `source .venv/bin/activate`, `uip codedagent setup --force`, `uip codedagent new <name>`, `uv add <framework-package>`, `uv add uipath-dev --dev`, `uv sync`, `uip codedagent init` |
| **Build** | [lifecycle/build.md](lifecycle/build.md) | Code agent logic with framework patterns |
| **Bindings** | [lifecycle/bindings-reference.md](lifecycle/bindings-reference.md) | Sync resource overrides in `bindings.json` |
| **Run** | [lifecycle/running-agents.md](lifecycle/running-agents.md) | `uip codedagent run` |
| **Evaluate** | [lifecycle/evaluate.md](lifecycle/evaluate.md) | `uip codedagent eval` |
| **Deploy** | [lifecycle/deployment.md](lifecycle/deployment.md) | `uip codedagent deploy`, `uip codedagent invoke` |
| **Sync** | [lifecycle/file-sync.md](lifecycle/file-sync.md) | `uip codedagent push`, `uip codedagent pull` |
| **Flow Integration** | [flow-integration.md](flow-integration.md) | Inline, published node, or tool resource in Flow |

## Build Scenarios

Two top-level build paths. Pick one before starting — the lifecycle and publish mechanism differ.

- **Scenario 1 — Standalone Coded Agent** — the agent is its own tenant resource, published via `uip codedagent deploy`. Use when the agent runs on its own, is called from multiple flows, or needs independent versioning.
- **Scenario 2 — In-Solution Coded Agent in a Flow** — the agent lives as a **sibling folder** to a flow project, registered into the solution via `uip solution project add`. The flow references it as an in-solution `uipath.core.agent.<resourceKey>` node, where `<resourceKey>` is the local UUID minted by `uip solution project add` and discoverable via `uip maestro flow registry list --local`. Use when the agent is tightly coupled to one flow.

## Quick Start: Scenario 1 — Standalone Coded Agent

When the user asks to create and deploy an agent end-to-end, follow these steps in order. Skip stages that are already done.

**IMPORTANT: Do NOT stop between steps to ask "would you like me to continue?" or list next steps. Execute the entire flow automatically.** Pause only when (a) you hit an **architectural fork** — a step with multiple valid implementations (framework choice, HITL pattern, evaluator type, deploy target, conversational vs not, etc.) — or (b) you need data only the user has (credentials, project ID). At a fork, apply **infer-or-ask**: if the prompt or context names the choice, infer it and continue; otherwise output ONLY the choice question as your entire response, then STOP and wait. For missing data, output ONLY the data request. After getting the answer, resume immediately. Forks for each step are documented in that step's referenced file — read the reference when you reach the step; do not guess.

Steps 8 and 9 are mandatory stops **for greenfield**: always ask, even if the user only said "build". Use `AskUserQuestion` (or platform equivalent); fall back to plain text only when no UI tool exists. They are **automatically resolved** for `local-workspace` (auto-sync) and for `existing-coded` with `has_project_id == true` (push) — see steps 8 and 9 for the branch logic.

1. **Framework** — **Skip if `framework != none`** (already chosen — verify the right `<framework>.json` is present and continue). Else select per the [Framework Selection](#framework-selection) section below.
2. **Setup** — Idempotent by `project_state` and `has_venv`:
   - `local-workspace` → Studio Web already scaffolded `pyproject.toml` / `<framework>.json` / `entry-points.json` / `bindings.json`. Run **only** the venv prep block when `has_venv == false`:

     ```bash
     uv venv --python 3.13
     source .venv/bin/activate                 # Windows: .venv\Scripts\activate
     uv sync
     uip codedagent setup --force
     ```

     If `has_venv == true`, just `source .venv/bin/activate` and continue. Do **not** run `uip codedagent new` or `init` (init only when `Input`/`Output` Pydantic models, the entry-function signature, or `<framework>.json` change).
   - `existing-coded` → `source .venv/bin/activate`. If `has_venv == false`, run `uv venv --python 3.13 && source .venv/bin/activate && uv sync`. Then `uip codedagent setup --force` (idempotent — refreshes `uipathExePath`). Skip `uip codedagent new`. Run `uip codedagent init` only if `has_entry_points == false` or schemas changed.
   - `greenfield` → Full Workflow in [lifecycle/setup.md](lifecycle/setup.md). Infer the project name from the user's prompt or the current directory.

   **Do NOT authenticate yet** — auth happens after build.
3. **Build** — Implement agent logic using the selected framework's patterns. **For `local-workspace`: skip only the scaffold-cleanup sub-step below** — Studio Web supplied a clean shell, so the module-level-client checks aren't needed. Logic edits in `main.py` proceed normally. For `greenfield` / `existing-coded`, after scaffolding and before running `uip codedagent init`, inspect the generated code and clean up scaffold hazards:
   - No module-level `UiPathChat`, `UiPathAzureChatOpenAI`, `UiPath`, or other auth-dependent clients.
   - Instantiate LLM/SDK clients inside graph nodes/functions only.
   - Ensure importing `main.py` works without UiPath auth.

   See [lifecycle/build.md](lifecycle/build.md) § Additional Instructions for the detailed Build-stage rules. After implementing, re-run `uip codedagent init` to update schemas from the actual code.
4. **Bindings** — Sync `bindings.json` with the code using [lifecycle/bindings-reference.md](lifecycle/bindings-reference.md). Non-interactive default: add/update missing bindings automatically; report no-op silently; ask only before deletion or for dynamic values.
5. **Auth (one-shot)** — Run `uip login status --output json` once. If `Status: Logged in`, trust the wrapper for the rest of the run (it auto-refreshes tokens). Otherwise ask for credentials — output ONLY this question as your entire response:

> What is your UiPath **environment** (cloud/staging/alpha), **organization name**, and **tenant name**?

Then STOP and wait. On reply, run the matching one-shot login from [../authentication.md](../authentication.md) (maps environment → `--authority`). Never run `uip login` without `--tenant`.
6. **Run** — Re-run `uip codedagent init` first **only when** `Input`/`Output` Pydantic models, the entry-function signature, or `<framework>.json` changed since the last run, **or** `has_entry_points == false`. Otherwise `entry-points.json` is already current — skip init. Then test locally with `uip codedagent run <ENTRYPOINT> '<input>'` (use the entrypoint name from `entry-points.json`, e.g., `main`).
7. **Evaluate** — Run `uip codedagent eval <ENTRYPOINT> evaluations/eval-sets/smoke-test.json --no-report`. Idempotent by `has_evaluators` / `has_smoke_set`: create the missing one(s) only — **never overwrite an existing evaluator config or smoke set**, the user may have tuned them.

   **Note:** `uipath-llm-judge-trajectory-similarity` requires emitted trace spans to populate `AgentRunHistory`. Plain `StateGraph` agents without explicit OpenTelemetry tracing produce empty history → all cases score 0.0 even on successful runs. If the smoke set scores 0.0, verify the agent actually executed (via local `uip codedagent run`) before treating it as a logic failure; consider an output-only evaluator for non-conversational graphs.

   **If `has_evaluators == false`**, create `evaluations/evaluators/llm-judge-trajectory.json`. If the default `model` below is not available in the user's tenant, call `sdk.agenthub.get_available_llm_models()` and substitute a `model_name` from the returned list.

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

   **If `has_smoke_set == false`**, create `evaluations/eval-sets/smoke-test.json` with 2-3 test cases based on the agent's input schema (version is string `"1.0"`, top-level `id`/`name` required, test cases in `evaluations` array):
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
8. **Delivery target.** Single branch point. **Evaluate branches in order — Local Workspace projects also have `UIPATH_PROJECT_ID` set in `.env`, so the `local-workspace` check MUST come before the `has_project_id` check, or Local Workspace will incorrectly fall into the push branch:**

   - **(1) `project_state == local-workspace`** → Studio Web auto-syncs saves to the remote SW project, so options A and B (manual push / solution upload) are skipped — they would be redundant or break sync identity. The user may still want a local dev console. Stop and ask via `AskUserQuestion` (header `"Delivery"`, `multiSelect: false`):

     **Question:** *Studio Web is auto-syncing this workspace. Do you want a local dev console too?*

     | # | Label (≤5 words) | Description |
     |---|---|---|
     | C | Local dev web server | I start `uip codedagent dev` (default `http://localhost:8080`) so you can interact with the agent in the browser. Studio Web continues to auto-sync. |
     | — | Skip — continue to deploy | No console; proceed to step 9. |

     On reply:
     - **C** → run `uip codedagent dev` in the background; surface the URL. Prereq: `uipath-dev` (added during scaffold). **STOP — do NOT proceed to step 9.** Local dev is a terminal choice.
     - **Skip** → continue to step 9.

     Do **not** run `uip codedagent push` for this branch (that's recovery only — see [lifecycle/local-workspace.md](lifecycle/local-workspace.md) § Studio-Web-Auto-Sync). Do **not** present options A or B.
   - **(2) `has_project_id == true` (cloud workspace, project ID already set)** → Run `uip codedagent push` to upload local edits, then continue to step 9. No fork question — the delivery choice was made in a prior session.
   - **(3) Else (greenfield / cloud workspace not yet wired)** → Stop and ask via `AskUserQuestion` (header `"Delivery"`, `multiSelect: false`).

     **Question:** *How do you want to use the agent next?*

     | # | Label (≤5 words) | Description |
     |---|---|---|
     | A | Studio Web — you set it up | You open Studio Web, create a Coded Agent project inside a solution, paste the project ID. I'll write `UIPATH_PROJECT_ID` to `.env` and run `uip codedagent push`. |
     | B | Studio Web — I package & upload | I run `uip solution new`, import the agent, strip `.venv`, and run `uip solution upload`. No Studio Web setup needed from you. |
     | C | Local dev web server | I start `uip codedagent dev` (default `http://localhost:8080`) so you can interact with the agent in the browser. Nothing is published. |
     | — | Skip — I'm done | Stop here. The agent is built and evaluated. |

     On reply:
     - **A** → wait for the project ID, write `UIPATH_PROJECT_ID=<id>` to `.env`, then run `uip codedagent push`.
     - **B** → run the local-solution flow. `uip solution new "<SOLUTION_NAME>"` creates `<cwd>/<SOLUTION_NAME>/<SOLUTION_NAME>.uipx` (sibling, not ancestor). `uip solution upload` archives verbatim and does NOT honor `packOptions.directoriesExcluded` — strip `.venv` from the imported copy or upload fails with `code 20001: solution archive is corrupt`. From the parent directory of the agent:

       ```bash
       uip solution new "<SOLUTION_NAME>"
       cd "<SOLUTION_NAME>"
       uip solution project import --source "../<AGENT_PROJECT_DIR>" --output json
       rm -rf "<AGENT_PROJECT_DIR>/.venv" "<AGENT_PROJECT_DIR>/__pycache__" \
              "<AGENT_PROJECT_DIR>/__uipath" "<AGENT_PROJECT_DIR>/eval-results.json"
       uip solution upload . --output json
       ```
     - **C** → run `uip codedagent dev` in the background; surface the URL (default `http://localhost:8080`). Prereq: `uipath-dev` (added during scaffold). **STOP — do NOT proceed to step 9.** Local dev is a terminal choice.
     - **Skip** → continue to step 9.

9. **Deploy.** Reachable from any `project_state` after option **Skip** at step 8 (greenfield or local-workspace), after the auto-push in branch (2), or after options **A** / **B** in greenfield. After option **C** at step 8, the run ends — do not ask. Stop and ask via `AskUserQuestion` (header `"Deploy target"`, `multiSelect: false`).

   **Question:** *Do you want to deploy the agent? If yes, which target?*

   | # | Label (≤5 words) | Description |
   |---|---|---|
   | A | Personal workspace | Run `uip codedagent deploy --my-workspace`. |
   | B | Tenant feed | Run `uip codedagent deploy --tenant`. |
   | C | Specific folder | Ask for the folder name, then run `uip codedagent deploy --folder "<Name>"`. |
   | — | Skip deployment | Stop here. |

   On reply, run `uip codedagent deploy <target-flag>`. If re-deploying, bump the patch version in `pyproject.toml` first.

   > **For `project_state == local-workspace`:** the user can still choose A/B/C to publish a package via `uip codedagent deploy` — that targets package feeds (personal workspace / tenant / folder) **outside** the Studio Web project lifecycle. It is a separate distribution path from Studio Web's own publish-from-UI button, which remains available in the SW browser. Skip deployment is the most common answer here, since Studio Web's publish UI typically covers the user's intent.

Read the relevant reference file at each step — do not guess.

## Quick Start: Scenario 2 — In-Solution Coded Agent in a Flow

Use when the coded agent is tightly coupled to one flow and lives as a sibling folder inside the same solution. The agent is wired to the flow via `--local` registry discovery — no separate Orchestrator deployment for the agent.

See [embedding-in-flows.md](embedding-in-flows.md) for the agent-side steps: scaffold the sibling folder, register it with `uip solution project add` to mint the `resource.key`, and verify discoverability via `uip maestro flow registry list --local`. Flow node JSON shape is in [flow-integration.md — Pattern 1](flow-integration.md#pattern-1-in-solution-coded-agent).

## Framework Selection

Infer the framework from the user's prompt when possible. If ambiguous, ask them to choose:

1. **Coded Function** — Plain Python with `Input`/`Output` models. No LLM. Best for deterministic logic.
2. **LangGraph** — StateGraph with conditional routing, tool use, interrupts. Best for complex LLM agents.
3. **LlamaIndex** — Workflow with events and RAG support. Best for knowledge retrieval.
4. **OpenAI Agents** — Lightweight agent with tools and handoffs. Best for simple LLM agents; lacks HITL, process invocation, and state persistence.

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

# Non-PDD Lane Guide

When the entry guard finds no `## Planner Handoff` marker or the user chooses “Other context,” run Lane B: detect context, elicit preferences, write a plan, and hand off to specialists. This applies to non-trivial UiPath requests without a PDD: multi-project orchestration or requests still ambiguous after detection. Single-project requests exit at Step 2 and load the specialist directly.

Run detection before elicitation so skip-rule inputs exist before questions are built.

## Step 1 — Detect before asking (no prompts)

Run all sub-steps non-interactively.

1. **Provided context document.** If the entry guard classified a document as “Other context,” read it. Resolve questions answered by it and feed its content into the plan.

2. **Filesystem detection.** Use `Glob`, `Read`, and `Grep` cross-platform, first in the current directory and then the parent. Never use shell-specific pipelines (`ls` globs, `grep` over pipes, `/dev/null` fail on native PowerShell).

   Search for: `project.json`, `*.xaml`, `*.cs`, `*.flow`, `flow_files/*.flow`, `*.bpmn`, `caseplan.json`, `agent.json`, `pyproject.toml`, `uipath.json`, `package.json`, `.uipath/*`, `app.config.json`, `*.uipx`, `element.json`, `*.py`.

   When `project.json` is found, read it and check `targetFramework` and dependencies structurally; do not use regex-over-cat. When `pyproject.toml` is found, read it and disambiguate:
   - An agent-framework dependency (`langgraph`, `llamaindex`, `openai-agents`) or sibling `agent.json` → **Agents**.
   - A sibling `uipath.json` with a `functions` map (or `entry-points.json` from `uip function init`) → **Functions**.
   - A bare `uipath` dependency with neither → inspect further or ask.
   - A `.venv/` directory is not required and proves nothing.

   For root-level `*.json` with none of the above, run `Grep` for `"document.dsl"` (API Workflow project).

   | Filesystem signal | Plan skill |
   |---|---|
   | `.xaml` and/or `.cs` files + `project.json` | `uipath-rpa` |
   | `*.flow` (usually under `flow_files/`) | `uipath-maestro-flow` |
   | `*.bpmn` (no `caseplan.json`) | `uipath-maestro-bpmn` |
   | `caseplan.json` | `uipath-maestro-case` |
   | `agent.json` | `uipath-agents` (low-code) |
   | `pyproject.toml` + agent-framework dependency (langgraph / llamaindex / openai-agents) | `uipath-agents` (coded) |
   | `pyproject.toml` + `uipath.json` with a `functions` map | `uipath-functions` |
   | `package.json` + `uipath.json` with a `functions` map | `uipath-functions` |
   | JSON containing `document.dsl` | `uipath-api-workflow` |
   | `.uipath/` or `app.config.json` | `uipath-coded-apps` |
   | `element.json` (+ `element-metadata.json`) | `uipath-connector-builder` |
   | `*.uipx` | `uipath-solution` (deploy/lifecycle ops) |
   | `project.json` only (no `.cs`/`.xaml`) | `uipath-rpa` |

   Multiple signals indicate the request likely spans projects; use the multi-skill patterns below. No signals means greenfield; infer project type in sub-step 4.

3. **Multi-skill classification.** Check the request against the named patterns in [multi-skill-patterns-guide.md](multi-skill-patterns-guide.md): “build”+“deploy,” “build”+“verify,” and one product depending on another. Record matched patterns.

4. **Product/project-type inference — need-driven, not keyword.** If signals or explicit naming do not decide the type, use [Product Selection Guide → Level 1](product-selection-guide.md#level-1--primary-scope-selection):
   - Explicit naming wins (`xaml workflow`, `coded workflow`, `.cs file`, `low-code`); record `Project type: XAML` or `Project type: C# coded`.
   - “AI”/“agent” does not force an Agent. Apply the **determinism gate**: rule-expressible decisions → RPA/API; genuine judgment → Agent.
   - Resolve “flow”/“process”/“orchestrate” with [Maestro disambiguation](product-selection-guide.md#maestro-disambiguation--bpmn-vs-flow-vs-case) (Flow vs BPMN vs Case); never assume Flow from the word alone.
   - Headless system-to-system → API Workflow; document extraction → IXP; user-facing screen → Coded Apps; reusable component → RPA Library; regression pack → Test Automation; tenant/resource operations only → `uipath-platform`.
   - Unless contradicted, default to **RPA workflow (XAML)** for UI / Excel / email / file work.

5. **Delivery-model resolution.** Explicit signals (`Automation Suite`, `on-prem`, `self-hosted`, `air-gapped`) set `Delivery model: <value>`. Otherwise run the best-effort `uip login status` preflight and map the host using [sdd-generation-guide.md → Step 0](sdd-generation-guide.md#step-0-determine-execution-mode--delivery-model). If unresolved and any candidate is delivery-gated (anything beyond core RPA + Orchestrator: Maestro, Agents, Coded Apps, API Workflows, Solutions `.uipx`), add the delivery-model question to Step 3. If the user says “not sure” or cannot be asked, record `Delivery model: unspecified — assumed cloud [ASSUMPTION]` in the plan header and list products gated by that assumption. Never omit this field when a gated product is involved. Apply the [Constraint Gate](product-selection-guide.md#constraint-gate) against [platform-availability-guide.md](platform-availability-guide.md) before recommending products.

## Step 2 — Single-skill exit (stop Lane B)

If Step 1 resolves one project owned end-to-end by one specialist—even with inline HITL / script / connector nodes or its own solution wrapper, authored per the Skip paragraph in SKILL.md—stop Lane B:

1. Do not write a plan file, emit `TaskCreate` calls, or ask the Step 3 batch.
2. State which specialist owns it and why, e.g. “Single-project `.flow` build — loading `uipath-maestro-flow` directly.”
3. Hand off detected paths, delivery model, and resolved answers.

Continue Lane B only for multi-project requests (matched multi-skill pattern, multiple filesystem signals, or separate buildable projects) or requests genuinely ambiguous after Step 1 inference and the Q3 fallback.

## Step 3 — Upfront elicitation (batched)

Put every unresolved question below into **one** `AskUserQuestion` call. Do not ask one at a time or split across turns. Omit questions resolved by the request, context document, or Step 1. If all are resolved, do not call `AskUserQuestion`; record inferred values in the plan header with a one-line note in Decisions & Trade-offs. Use the phrasing rules in [pdd-driven-lane-guide.md → Step 5](pdd-driven-lane-guide.md#step-5--ui-element-targeting-only-when-9-contains-ui-applications): no internal jargon, domain names, or app names in question text.

### Skip-rules table

| Question | Skip when | Default if skipped |
|---|---|---|
| Q1 Generation approach | Request is simple and well-defined; user is modifying an existing automation. | `simultaneous` |
| Q2 Execution autonomy | User already stated it (“autonomous”, “check with me”). Never infer it from Q1; planning approach and execution autonomy are separate. | `autonomous` |
| Q3 Project type fallback | Step 1 resolved the type (explicit naming, need-driven inference, or filesystem). | `RPA workflow (XAML)` |
| Delivery model | Resolved at Step 1.5 (explicit, preflight); or no delivery-gated product is a candidate. | `unspecified — assumed cloud [ASSUMPTION]` + affected-products note |

### Question 1 — Generation approach

Ask:

> How would you like me to work?
>
> 1. **Explore first, then plan** — analyze the project and requirements, run non-mutating discovery, then present a plan for approval before any project changes *(recommended for non-trivial requests)*
> 2. **Explore, plan, and execute simultaneously** — emit the plan as text and the main agent starts executing right away

For **explore first, then plan**, you may run non-mutating discovery: `uip rpa analyze`, `uip rpa get-errors`, and reading `project.json`. Do not run commands that mutate the project (create files, register targets, install packages); execution owns them. After Steps 4–5, call `EnterPlanMode` with the plan; after approval, call `ExitPlanMode`.

For **explore, plan, and execute simultaneously**, emit the plan as text in Step 5, immediately load the first specialist skill, and do not call `EnterPlanMode`.

### Question 2 — Execution autonomy

Ask in the same batch as Q1. Explore-first does not imply autonomous execution.

> Once execution starts, how should I handle ambiguity or scope concerns?
>
> 1. **Autonomous to completion** *(recommended)* — follow the plan end-to-end without stopping for confirmation. Specialist skills handle their own pause points (auth failure, UI capture limits, etc.).
> 2. **Interactive** — pause and confirm on structural decisions, scope concerns, or side-effect actions during execution.

Record `Execution autonomy: autonomous | interactive` in the plan header. Task prompts carry the plan path (Step 5); specialists must recover decisions from it and, in autonomous mode, must not re-ask decisions already made there.

### Question 3 — Project type fallback

Ask only when Step 1 could not infer the type:

> Q3 — What kind of project should I scaffold?
>
> 1. **RPA workflow** — UI automation, Excel / email / file work *(recommended default)*
> 2. **AI Agent** — genuine judgment/reasoning over ambiguous input, LLM tool use
> 3. **Orchestration** — coordinate multiple automations (Maestro Flow / BPMN / Case — disambiguated by the need)
> 4. **Headless / other** — API Workflow, custom web app, document extraction (IXP), reusable Library, Test Automation — say which

The question UI always offers free-text “Other”; a specific answer overrides the options. If the user chooses **RPA workflow**, record `Project type: XAML`. Never follow up with “XAML or C#?”; authoring mode belongs to `uipath-rpa`. Set coded mode only when the user independently says “coded workflow” or “.cs file”; never ask it as a follow-up or recommend C# coded as a top-level option for routine UI automation.

### Authoring surface

Studio, Studio Web, and VS Code are presentation layers over the same artifacts. Never ask about, derive, record, or condition on them; treat surface terms as ordinary requirement prose. In explore-first mode, nothing syncs to the tenant before plan approval. Model only **delivery model** (Automation Cloud / cloud variant / Automation Suite / standalone) as environment input.

### Packaging

For every plan with a generation skill, record `Packaging: standalone | solution` per [Product Selection Guide → layer 4](product-selection-guide.md#how-selection-works--four-layers): single project → `standalone` (default); multi-project / cross-product / team standardization → `solution` (`.uipx` via `uipath-solution`). This selects deployment: `uipath-solution` for `solution`; `uipath-platform` for `standalone` non-solution publishes. Ask only if the user's words conflict with the derivation.

### Expression language

Always use **VB.NET** for XAML workflows and note it in the plan. Do not ask.

## Step 4 — UI element targeting (only when the plan includes UI automation)

If the plan loads `uipath-rpa` for a workflow that clicks, types into, or reads desktop or browser elements, ask the three UI questions in **one batched** `AskUserQuestion` call. Use the exact wording and skip rules in [pdd-driven-lane-guide.md → Step 5](pdd-driven-lane-guide.md#step-5--ui-element-targeting-only-when-9-contains-ui-applications); skip questions already resolved by the request. Skip the entire batch for pure data processing, API calls, agent-only, or flow-only plans.

Record answers in the plan header and summarize them in the relevant task's Skill prompt. Include the plan path so resumed or separately executed tasks can recover all decisions.

## Step 5 — Write the plan

Compose `<feature>.md` using [plan-and-tasks-format.md → Non-PDD lane](plan-and-tasks-format.md#non-pdd-lane-featuremd). The body contains the task list with the same task-row schema as Lane A.

Every task's Skill prompt must embed the exact relative or absolute path of the written plan, mirroring Lane A's embedded SDD path. `TaskCreate` copies prompts verbatim; never use a bare “this plan.”

### Self-review before saving

1. **Coverage** — every requirement appears in at least one task.
2. **Placeholder scan** — no `TBD`, `TODO`, `as needed`, `if appropriate`, or `similar to`.
3. **Skill order** — assign and order specialist skills correctly (for example, RPA before platform deploy; testing before deploy).
4. **Validation gaps** — every generation task ends with a `Validate:` compile / build / lint check.
5. **Testing task present** — include a dedicated `Testing (MANDATORY)` task for every generation skill. Route to specialist testing references; do not describe the procedure.
6. **Plan path present** — every Skill prompt names the plan path, not “this plan.”
7. **No internal-flow leakage** — do not duplicate specialist reference steps.
8. **Anti-hallucination rule** — append it to every Skill prompt.

Fix issues before saving.

### Save location

Save as `YYYY-MM-DD-<feature-name>.md`:

- If a project directory exists (`project.json`, `flow_files/`, `.uipath/`, or `pyproject.toml`), save under `docs/plans/` within the project; create the directory if needed.
- Otherwise save under `./plans/`; create the directory if needed.

### Resume handling

If a plan already exists at the target path, ask via `AskUserQuestion`:

> A plan file already exists at `<path>`. How should I proceed?
>
> 1. **Continue with the current plan** *(recommended)* — pick up where you left off; checkbox state preserved
> 2. **Regenerate from the current request** — discard the current plan and rebuild

For option 1, read the existing plan, recreate live `TaskCreate` calls with status preserved, and finish. For option 2, parse the request fresh, run identity-matching against the old file to preserve completed work, write the new plan, and emit live tasks. Use [plan-and-tasks-format.md → Regenerate logic](plan-and-tasks-format.md#regenerate-logic-pdd-driven-lane-only).

## Step 6 — Present the plan

- **Explore first, then plan:** call `EnterPlanMode` with the plan content. After approval, call `ExitPlanMode`, then emit live `TaskCreate` calls.
- **Explore, plan, and execute simultaneously:** emit the plan as text, then immediately emit live `TaskCreate` calls; the main agent starts executing.

## Lane B budget

Step 3 is always one batched call (Q1 + Q2 + optional Q3/delivery in one `AskUserQuestion`; at most 4 question objects). Step 4 is one batched call when UI automation exists; resume adds one. Realistic floor: 0. Realistic ceiling: 3.

| Scenario | `AskUserQuestion` calls |
|---|---:|
| Single-skill exit at Step 2 | **0** (no plan, batch, or prompt) |
| Simple multi-skill, simultaneous, all signals clear, no UI | **0** |
| Non-trivial, no UI automation | **1** (Step 3 batch) |
| Non-trivial, with UI automation | **2** (Step 3 + Step 4 batches) |
| Vague request, with UI automation | **2** (Step 3 batch including Q3 + Step 4 batch) |
| Resume scenario | **+1** |
| Realistic maximum | **3** |
| Hard cap (per-phase prompt budget, Critical Rules) | **5** |

The 5-call hard cap is defined in the planner's Critical Rules. Correct batching should keep usage below it.
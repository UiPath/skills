# Parallel XAML Authoring Guide

## When to Use This Guide

- The workflow targets **2 or more distinct screens** requiring target configuration via `uia-configure-target`
- The workflow is a **XAML workflow** (not a coded workflow in C#)
- **Single-screen workflows:** skip this pipeline entirely — one agent creates the file and writes all activities in a single pass

## Target Attachment Model

All OR target attachment (linking screens to ApplicationCards and elements to UI activities) is performed **by the write agents**, not the orchestrator. The orchestrator passes reference IDs and activity IdRefs; the agent executes the CLI calls.

See `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md` for:
- The IdRef contract (`<ClassName>_<N>` convention, used whenever this guide mentions assigning IdRefs)
- Fast Path — the default attachment mechanism (link commands in the OR CLI)
- Fallback (embedded `<TargetApp>` / `<TargetAnchorable>` snippets) — used only when a link call fails

## Phase 0: Plan the Workflow

> **CRITICAL:** Complete Phase 0 before spawning any agent. The orchestrator's job in Phase 0 is to plan screens and actions, then determine the few values agents cannot derive themselves (expression language, x:Class). All other data (activity templates, xmlns, TextExpression blocks) is retrieved inside the agent — see [agents/uia-xaml-author-agent.md](../agents/uia-xaml-author-agent.md).

1. **Identify screens.** List each distinct application state the workflow will interact with. A "screen" is a stable UI state where one or more elements need to be targeted — a page, a modal dialog, an inline form, or a panel that appears after an action.

2. **Map actions per screen.** For each screen, list the ordered interactions: which element, what action (Click, TypeInto, SelectItem, GoToUrl), what data value, and any special behavior (dropdown patterns, checkbox toggling). Do NOT preemptively plan `Delay` activities to "wait for elements to appear" — UIA activities have embedded target-finding retry and will wait on their own. See [When Delay is Warranted](#when-delay-is-warranted) for the narrow cases where an explicit delay is justified.

3. **Determine ApplicationCard scope.** Decide whether the workflow uses one ApplicationCard (all screens share the same window or browser tab — the common case for single-app web automation) or multiple (different applications or browser tabs requiring separate ApplicationCards).

4. **Identify element reuse.** Note where the same form appears more than once with different data (for example, a "Save & New" pattern that reopens the same contact form). These screens share OR targets but have separate action sequences and data values — each gets its own write agent.

5. **Determine the two values agents cannot derive themselves:**

   a. **Expression language** — read from `project.json` → `expressionLanguage` field (`CSharp` or `VB`). Passed to every write agent prompt.

   b. **x:Class value** — derived from the output `.xaml` filename per the naming rule in [xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md): folder separators become underscores, not dots. Root-level `MyWorkflow.xaml` → `x:Class="MyWorkflow"`. Subfolder `Workflows/MyWorkflow.xaml` → `x:Class="Workflows_MyWorkflow"`. Passed to `Write-<Screen 1>` (create-mode) as `<X_CLASS_VALUE>`.

6. **Create a split task list** before starting Phase 1. Each screen produces TWO tasks with distinct lifecycles — `Configure-<ScreenName>` (owned by the main conversation, completes when OR registration finishes) and `Write-<ScreenName>` (owned by a background agent, completes on `<task-notification>`). Splitting these prevents the ambiguous "configure done but write running" status that collapses the Task list progress view.

   ```
   - Configure-<ScreenName-1>            (main conv)
   - Write-<ScreenName-1>                 (background agent, create-mode) blockedBy: Configure-<ScreenName-1>
   - Configure-<ScreenName-2>            (main conv)
   - Write-<ScreenName-2>                 (background agent, append-mode) blockedBy: Configure-<ScreenName-2>, Write-<ScreenName-1>
   - ...
   - Configure-<ScreenName-N>            (main conv)
   - Write-<ScreenName-N>                 (background agent, append-mode) blockedBy: Configure-<ScreenName-N>, Write-<ScreenName-N-1>
   - Finalize                             (main conv) blockedBy: Write-<ScreenName-N>
   ```

   `Configure-<N+1>` is NOT blocked by `Write-<N>` — this preserves the pipeline's parallelism (configure next while previous writer runs). See [Task Structure](#task-structure) below for the `TaskCreate` / `TaskUpdate` pseudocode and the mandatory `TaskGet` integrity check before each `Agent()` spawn.

## Phase 1: Write Agents

Each screen has one `Write-<Screen N>` task, backed by the unified [UIA XAML Author Agent](../agents/uia-xaml-author-agent.md). `Write-<Screen 1>` runs in **create-mode** — the agent creates the file, attaches screen 1 to `NApplicationCard_1`, and inserts screen 1's activities. Subsequent `Write-<Screen N>` for N>1 run in **append-mode** — the agent opens the existing file and inserts screen N's activities. The agent derives the mode from which inputs are set.

1. **Spawn precondition** — Do NOT spawn `Write-<N>` until ALL of the following hold (the orchestrator MUST verify each via `TaskGet` before calling `Agent()`):
   - (a) `Configure-<N>` is `completed` (screen N's element targets are fully configured and registered in the OR — the orchestrator hands off only reference IDs; the agent does the attaching).
   - (b) `Write-<N-1>` is `completed` (for N > 1). **If `Write-<N-1>` is `in_progress`, do NOT spawn — the chain is violated.** See [Waiting for Background Agents](#waiting-for-background-agents).

2. **Run mode:** Spawn each write agent with `run_in_background: true`. While the agent writes screen N, the main conversation must advance the application to screen N+1 and configure its targets (`Configure-<N+1>`) — but it must NOT spawn `Write-<N+1>` until `Write-<N>` is `completed`. The chain requires each agent to read the previous agent's finalized file state.

3. **Inputs passed to the agent** (see the agent file's [input contract](../agents/uia-xaml-author-agent.md#input-contract) for the full set):
   - Every `Write-<N>` task: `<PROJECT_DIR>`, `<OUTPUT_XAML_PATH>`, `<EXPRESSION_LANGUAGE>`, `<SKILL_DIR>`, `<ACTIVITY_CLASS_LIST>`, `<ACTION_LIST>`.
   - Create-mode only (`Write-<Screen 1>`): `<X_CLASS_VALUE>`, `<FIRST_SCREEN_REFERENCE_ID>`. Mode is derived: if the file does not exist and `<FIRST_SCREEN_REFERENCE_ID>` is set, the agent goes create-mode; otherwise append-mode.

4. **What the agent does** (the agent retrieves its own data — orchestrator does NOT pre-fetch):
   - Detects mode from file existence and input shape; fails fast on mismatch.
   - Fetches `uip rpa get-default-activity-xaml` templates for every activity class it needs (plus `NApplicationCard` in create-mode).
   - Reads the per-activity behavior doc for each class.
   - Reads the attachment guide at `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`.
   - In create-mode: reads an existing `.xaml` in `<PROJECT_DIR>` to extract xmlns + TextExpression blocks, writes the file skeleton (root `<Activity>`, `NApplicationCard_1`, empty inner `<Sequence DisplayName="Do">`), and attaches `<FIRST_SCREEN_REFERENCE_ID>` to `NApplicationCard_1`.
   - Inserts each action's activity immediately before the closing `</Sequence>` of the inner `<Sequence DisplayName="Do">`. Assigns unique IdRefs per the attachment guide's IdRef contract. Attaches each `reference_id` (with `target_property` when specified). Does NOT modify any content before the insertion point.

5. **Post-write verification** (D-09): the agent runs `get-errors` itself:
   ```bash
   uip rpa get-errors \
     --file-path "<XAML_FILE_PATH>" \
     --project-dir "<PROJECT_DIR>" \
     --output json \
       ```

6. **Self-repair** (D-10): Max 3 fix cycles, then report remaining errors to the main conversation.

7. **Prompt template:** See [agents/uia-xaml-author-agent.md](../agents/uia-xaml-author-agent.md) for the Agent() call block and placeholder list.

### Screen Boundaries

A "screen" equals everything configured before advancing the application to the next workflow state via servo. This may include intermediate servo clicks within the same logical state (for example, navigating to a list view to reveal a "New" button before configuring it) — per the Complete-then-advance rule in [uia-multi-step-flows.md](uia-multi-step-flows.md).

All `uia-configure-target` calls for the current workflow state must complete before spawning the write agent for that screen AND before using servo to advance to the next state.

See also: [uia-multi-step-flows.md](uia-multi-step-flows.md) for the Complete-then-advance rule.
See also: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md` and [uia-configure-target-workflows.md](uia-configure-target-workflows.md).

### Chained Dependency Model

The write agents form a strict chain — each depends on the previous:

| Agent | `Write-<N>` blockedBy |
|-------|-----------|
| Screen 1 agent (create-mode) | `Configure-<Screen 1>` |
| Screen 2 agent (append-mode) | `Write-<Screen 1>` + `Configure-<Screen 2>` |
| Screen N agent (append-mode) | `Write-<Screen N-1>` + `Configure-<Screen N>` |

The main conversation runs `Configure-<N+1>` in parallel with `Write-<N>`. `Configure-<N+1>` is NOT blocked by `Write-<N>`.

## Waiting for Background Agents

These three rules govern what the orchestrator may and may not do while a `Write-<N>` agent is running. Violations have produced silent file corruption in past runs (concurrent writes inserting at the same point).

1. **Never spawn `Write-<N>` while `Write-<N-1>` is `in_progress`.** The pipeline is a chain, not a fan-out. Before every `Agent()` call for `Write-<N>`, call `TaskGet` on the predecessor `Write-<N-1>` task. If its status is not `completed`, do NOT spawn. This structurally enforces the chained dependency model.

2. **When idle waiting on a background agent, do not poll.** Specifically forbidden:
   - `sleep` / `Monitor` + `until` loops / `ScheduleWakeup` / `run_in_background` sentinels that only check status.
   - Reading the file the agent is writing ("did it grow?").
   - Re-spawning the agent to "check" it.

   Instead:
   - **If non-conflicting work exists** (configure next screen's targets, prepare the next prompt, draft the next action list) — do that work.
   - **If no non-conflicting work remains** — reply to the user with a one-line status (`"Write-<N> running; waiting for completion."`) and stop. The runtime delivers the `<task-notification>` block asynchronously; the next turn will resume on that event.

   Polling burns the prompt cache (each wake reloads the conversation) and the Agent tool guarantees a completion notification — polling adds no correctness, only cost.

3. **Every `<task-notification>` must be acknowledged in the same turn by `TaskUpdate` → `completed` on the matching `Write-<N>` task.** Missing a notification becomes structurally impossible if this rule holds.

## Phase 2: Finalization

1. **Validate the complete workflow.** After the last write agent completes, run `get-errors` on the full file (D-11):
   ```bash
   uip rpa get-errors \
     --file-path "<XAML_FILE_PATH>" \
     --project-dir "<PROJECT_DIR>" \
     --output json \
       ```
   Do NOT run `run-file` as a validation step — the target application state is not guaranteed to be in the correct starting state after the pipeline.

2. **Add entry point to `project.json`.** Add the new workflow to the `entryPoints[]` array:
   ```json
   {
     "filePath": "WorkflowName.xaml",
     "uniqueId": "<GENERATE_GUID>",
     "input": [],
     "output": []
   }
   ```
   GUID generation is the main conversation's responsibility — not a write agent's — because it modifies a shared project file.

3. **Report completion** to the user per the SKILL.md Completion Output format.

## Prompt Construction Rules

1. **Pass the ref-ID-keyed action list; the agent retrieves its own XAML and docs.** Do NOT paste activity templates, xmlns blocks, TextExpression blocks, TargetApp XAML, `<TargetAnchorable>` snippets, or the attachment guide body into the agent prompt. The orchestrator constructs a structured action list (see [Action List Format](#action-list-format)); the agent fetches activity templates, reads the per-activity behavior docs, and reads the attachment guide itself. The attachment guide lives at `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md` (Fast Path for linking, with a snippet-embed fallback).
2. Describe actions as a structured list with exact data values (`display_name`, `type`, `reference_id`, optional `text`/`duration_seconds`/`target_property`) — see [Action List Format](#action-list-format). Each action carries enough detail for the agent to construct the activity from the template it retrieves and then attach the target.
3. Specify interaction patterns **explicitly** for each non-trivial interaction: dropdown selection (Click then TypeInto with `[k(enter)]`), checkbox toggling, element reuse across repeated form instances. These go in a per-screen notes block in the prompt. Do NOT include `Delay` activities by default — UIA activities retry target lookup internally; see [When Delay is Warranted](#when-delay-is-warranted).
4. **Pass `<EXPRESSION_LANGUAGE>` in every write agent prompt** (`CSharp` or `VB`, read from `project.json`). Do NOT inline CSharp-vs-VB binding syntax examples — the agent derives correct syntax from the template returned by `get-default-activity-xaml` (which respects `--project-dir`) and from the per-activity behavior doc. For system activities without a package `.md` doc, the agent consults the expression-language binding guide.
5. All context (action list, interaction patterns) goes **inline in the Agent() prompt parameter** as labeled blocks (D-06). Do not pass context via temp `.md` files or any other file-based method. Edit-insertion and validation instructions already live in the agent template at [agents/uia-xaml-author-agent.md](../agents/uia-xaml-author-agent.md) — do not duplicate them in the orchestrator.

## Edge Cases

### When Delay is Warranted

UIA activities (`NClick`, `NTypeInto`, `NSelectItem`, `NGoToUrl`, etc.) have **embedded target-finding resilience** — they retry the selector lookup for a configurable timeout before failing. A `Delay` placed in front of a UIA activity to "let the UI settle" is almost always redundant and inflates workflow runtime without changing correctness.

**Do NOT insert `Delay` just because:**
- A navigation, modal, or panel just opened and the next element might not be visible yet — the next UIA activity retries until its timeout.
- The previous action was slow — UIA activities already wait.
- "It feels safer."

**`Delay` is warranted only when ALL of the following hold:**
- The wait is NOT for a UI element that a following UIA activity will target (UIA's retry covers that case).
- There is a concrete reason the next activity cannot absorb the wait — e.g., a post-action animation that no UIA target is anchored on, a fixed-duration business pause (rate-limit cool-down, deliberate pacing between identical submissions), or a background job the UI doesn't reflect until later.
- The orchestrator can state, in one sentence in the prompt's per-screen notes, why a UIA activity's built-in retry is insufficient for this specific case.

If the agent cannot articulate that sentence, drop the `Delay`.

### Reused Forms (Same OR Targets, Different Data)

When the same form appears more than once (for example, a "Save & New" pattern that reopens the same contact form), treat the repetitions as screens that reuse the same OR element references but have different action sequences and data values. Each activity instance gets its own unique `sap2010:WorkflowViewState.IdRef` and its own attachment call — one OR reference linked to multiple activity IdRefs.

**Prefer a single write agent when all of these hold:**
- The repetitions are back-to-back in the workflow (no intervening pipeline work).
- They use the same OR targets — no additional target configuration is needed between them.
- The flow is linear (no branching, no conditional logic the agent would need to reason about).

A single agent appends all repetitions in one pass. This avoids chain overhead (each extra agent adds a validation cycle, a context-window hit, and a round-trip) while producing identical output.

**Split into separate write agents only when:**
- New OR targets must be configured between repetitions (the main conversation needs to run `uia-configure-target` between agent spawns).
- The app state must be advanced via `uia interact` or servo between repetitions.
- The repetitions have structural differences large enough that one prompt would be ambiguous or oversized.

When splitting, each agent appends independently and the later agent's activities follow the earlier's in the file.

### Single-Screen Workflows

Skip the chain entirely. Spawn one [UIA XAML Author Agent](../agents/uia-xaml-author-agent.md) invocation in create-mode with the screen's action list — one agent creates the file and writes every activity in a single pass. The chain overhead (multiple `Write-<N>` tasks and sequential dependencies) is not justified for a single screen.

### Write Agent Failure

The agent self-repairs in-place (D-10): it calls `get-errors`, reads the errors, and fixes the XAML. Max 3 fix cycles. If errors remain after 3 attempts, stop and report the remaining errors to the main conversation.

Screens 1 through N-1 are already written and valid — no rollback is needed. The main conversation reads the reported error, adjusts the prompt or corrects a selector, and retries screen N's agent. The agent reads the current file state (valid through N-1) and appends from there.

### Background Agent Not Done

See [Waiting for Background Agents](#waiting-for-background-agents) for the three governing rules. In short: never spawn `Write-<N>` while `Write-<N-1>` is `in_progress` (use `TaskGet` to verify), never poll, and acknowledge every `<task-notification>` with `TaskUpdate` → `completed` in the same turn.

Write agents are typically fast — they perform pure text generation against a structured prompt and a few CLI calls. If an agent is consistently slow (e.g., >5 minutes), suspect a hung CLI call (Studio unresponsive).

## Anti-patterns

1. Do NOT let an append-mode write agent (`Write-<N>` for N > 1) create the file. The file must already exist; if it doesn't, `Write-<Screen 1>` failed — fix that first.
2. Do NOT let a write agent modify activities inserted by earlier screens — insert only before the closing `</Sequence>` tag.
3. Do NOT spawn `Write-<N>` while `Write-<N-1>` is `in_progress`. Check `TaskGet(Write-<N-1>)` first; only spawn if `completed`. Spawning early breaks the chain — the agents will race on the same insertion point.
4. Do NOT poll for agent completion. No `sleep`, no `Monitor` + `until` loop, no `ScheduleWakeup`, no file-growth checks, no respawning the agent to "see if it's done". Either do non-conflicting work, or reply with a one-line status and stop. The runtime delivers `<task-notification>` asynchronously.
5. Do NOT paste activity templates, xmlns blocks, TextExpression blocks, TargetApp XAML, or OR `<TargetAnchorable>` snippets into the agent prompt. Pass reference IDs, activity class names, and a structured action list — the agent retrieves activity templates itself and attaches targets on its own.
6. Do NOT pass unstable selectors (auto-generated numeric IDs, `css-selector` attributes, hash-based class names) to write agents — identify and fix them during target configuration via selector improvement before the agent attaches targets.
7. Do NOT skip the selector stability gate before the agent attaches targets. Syntactically valid XAML that uses runtime-broken selectors is harder to debug than a build error.
8. Do NOT modify the `.xaml` file from the main conversation while a write agent is running. The chained model depends on each agent reading the current valid file state; concurrent edits produce an unknown file state for the next agent.
9. Do NOT spawn write agents in foreground mode — this blocks the main conversation and serializes the pipeline. Always use `run_in_background: true` so the main conversation can configure the next screen's targets in parallel.
10. Do NOT insert `Delay` activities to wait for UI elements to appear. UIA activities retry target-finding internally for their configured timeout, so a leading `Delay` just inflates runtime. Include `Delay` only when [When Delay is Warranted](#when-delay-is-warranted) applies — and require a one-sentence justification in the prompt's per-screen notes.

## Prompt Templates

See [agents/uia-xaml-author-agent.md](../agents/uia-xaml-author-agent.md) for the unified UIA XAML author agent — Agent() call block, placeholder contract, and mode-derivation rules. One template covers all three modes (scaffold-only, scaffold+activities, append-activities); the agent derives the mode from which inputs are set and from whether `<OUTPUT_XAML_PATH>` already exists.

> **Note:** Use a capable model (for example, `claude-sonnet-4-5` or higher) for write agents — XAML generation requires reliable instruction-following.

## Action List Format

The orchestrator composes the action list once per screen agent from the registered OR references and the Phase 0 action plan. No XAML lives in the orchestrator context — only structured metadata.

```json
[
  {"display_name": "Click Accounts Nav", "type": "NClick", "reference_id": "xPMFx.../3eZ3506YOEalsrUWRMADfQ"},
  {"display_name": "Type Account Name", "type": "NTypeInto", "reference_id": "xPMFx.../h0mdnfakSk6gE9v5ZkYNuQ", "text": "Get Cloudy"}
]
```

Note the absence of any `Delay` between the click and the type — the subsequent `NTypeInto` will retry target lookup on its own while the Accounts List renders. Include `Delay` only when [When Delay is Warranted](#when-delay-is-warranted) applies.

Minimum fields per entry:
- `display_name` — string. Becomes the activity's `DisplayName`.
- `type` — `NClick`, `NTypeInto`, `NSelectItem`, `NGoToUrl`, etc. `Delay` is supported but should be used only when [When Delay is Warranted](#when-delay-is-warranted) applies.
- For UI activities: `reference_id` — the OR reference ID. The agent attaches it to the activity.
- For UI activities whose target is not at `.Target`: optional `target_property` — dot-separated property path (e.g., `"SearchedElement.Target"`). Passed through to the attachment call when the target isn't at `.Target`; omit otherwise.
- For `NTypeInto`: optional `text` — the text to type.
- For `Delay`: `duration_seconds` instead of `reference_id`.

The agent assigns `sap2010:WorkflowViewState.IdRef` per the contract in the attachment guide (read by the agent) — the orchestrator does NOT specify IdRefs in the action list.

## Task Structure

Pseudocode for the per-screen main-conversation flow (apply with `TaskCreate` / `TaskUpdate` / `TaskGet`):

```
configure_task = TaskCreate(
  subject: f"Configure-{screen_name}",
  description: f"Register screen + elements in OR for {screen_name}"
)
write_task = TaskCreate(
  subject: f"Write-{screen_name}",
  description: (
    f"Create XAML and insert activities for {screen_name} into {xaml_filename}"
    if screen_index == 1 else
    f"Insert activities for {screen_name} into {xaml_filename}"
  )
)
# Screen 1: write blockedBy Configure-1 only (no previous Write task).
# Screen N > 1: write blockedBy Configure-N + Write-<N-1>.
if screen_index == 1:
  TaskUpdate(write_task.id, addBlockedBy: [configure_task.id])
else:
  TaskUpdate(write_task.id, addBlockedBy: [configure_task.id, previous_write_task.id])

# Main conv: do configure work
TaskUpdate(configure_task.id, status: "in_progress")
# ...run uia-configure-target, register elements, etc.
TaskUpdate(configure_task.id, status: "completed")

# Before spawning write agent: verify predecessor (Waiting for Background Agents, rule 1)
if screen_index > 1:
  predecessor = TaskGet(previous_write_task.id)
  if predecessor.status != "completed":
    raise "Pipeline violation: cannot spawn Write-<N> while Write-<N-1> is in_progress"

TaskUpdate(write_task.id, status: "in_progress")
Agent(run_in_background: true, ...)   # create-mode inputs for N==1, append-mode inputs for N>1

# On <task-notification> arrival for this agent (Waiting for Background Agents, rule 3):
TaskUpdate(write_task.id, status: "completed")
```

Screen 1's write task runs the agent in create-mode; subsequent screens run in append-mode. The agent derives the mode from which inputs are set — no mode flag in the pipeline.

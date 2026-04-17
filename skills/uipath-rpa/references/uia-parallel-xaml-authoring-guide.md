# Parallel XAML Authoring Guide

## When to Use This Guide

- The workflow targets **2 or more distinct screens** requiring target configuration via `uia-configure-target`
- The workflow is a **XAML workflow** (not a coded workflow in C#)
- **Single-screen workflows:** skip this pipeline entirely — one agent writes the complete file (scaffolding + activities) in a single pass

## Phase 0: Plan the Workflow

> **CRITICAL:** Complete Phase 0 before spawning any agent. The orchestrator's job in Phase 0 is to plan screens and actions, then determine the few values agents cannot derive themselves (expression language, x:Class). All other data (activity templates, xmlns, TextExpression blocks) is retrieved inside the agent, and target attachment happens inside the agent per [uia-target-attachment-guide.md](uia-target-attachment-guide.md) — see [Prompt Templates](#prompt-templates).

1. **Identify screens.** List each distinct application state the workflow will interact with. A "screen" is a stable UI state where one or more elements need to be targeted — a page, a modal dialog, an inline form, or a panel that appears after an action.

2. **Map actions per screen.** For each screen, list the ordered interactions: which element, what action (Click, TypeInto, SelectItem, GoToUrl), what data value, and any special behavior (dropdown patterns, wait durations, checkbox toggling).

3. **Determine ApplicationCard scope.** Decide whether the workflow uses one ApplicationCard (all screens share the same window or browser tab — the common case for single-app web automation) or multiple (different applications or browser tabs requiring separate ApplicationCards).

4. **Identify element reuse.** Note where the same form appears more than once with different data (for example, a "Save & New" pattern that reopens the same contact form). These screens share OR targets but have separate action sequences and data values — each gets its own write agent.

5. **Determine the two values agents cannot derive themselves:**

   a. **Expression language** — read from `project.json` → `expressionLanguage` field (`CSharp` or `VB`). Passed to every screen activity agent prompt.

   b. **x:Class value** — derived from the output `.xaml` filename per the naming rule in [xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md): folder separators become underscores, not dots. Root-level `MyWorkflow.xaml` → `x:Class="MyWorkflow"`. Subfolder `Workflows/MyWorkflow.xaml` → `x:Class="Workflows_MyWorkflow"`. Passed to the scaffolding agent prompt.

   All other data (activity templates, xmlns, TextExpression blocks) is retrieved by the agent itself, and target attachment happens inside the agent per [uia-target-attachment-guide.md](uia-target-attachment-guide.md) — see the agent prompt templates in [Prompt Templates](#prompt-templates).

6. **Create a split task list** before starting Phase 1. Each screen produces TWO tasks with distinct lifecycles — `Configure-<ScreenName>` (owned by the main conversation, completes when OR registration finishes) and `Write-<ScreenName>` (owned by a background agent, completes on `<task-notification>`). Splitting these prevents the ambiguous "configure done but write running" status that collapses the Task list progress view.

   ```
   - Configure-<ScreenName-1>            (main conv)
   - Write-Scaffold                       (background agent) blockedBy: Configure-<ScreenName-1>
   - Write-<ScreenName-1>                 (background agent) blockedBy: Write-Scaffold, Configure-<ScreenName-1>
   - Configure-<ScreenName-2>            (main conv)
   - Write-<ScreenName-2>                 (background agent) blockedBy: Configure-<ScreenName-2>, Write-<ScreenName-1>
   - ...
   - Configure-<ScreenName-N>            (main conv)
   - Write-<ScreenName-N>                 (background agent) blockedBy: Configure-<ScreenName-N>, Write-<ScreenName-N-1>
   - Finalize                             (main conv) blockedBy: Write-<ScreenName-N>
   ```

   `Configure-<N+1>` is NOT blocked by `Write-<N>` — this preserves the pipeline's parallelism (configure next while previous writer runs). See [Task Structure](#task-structure) below for the `TaskCreate` / `TaskUpdate` pseudocode and the mandatory `TaskGet` integrity check before each `Agent()` spawn.

## Phase 1: Scaffolding Agent

1. **When to spawn:** Immediately after the first screen is registered in the Object Repository (TARGET-8 screen creation), before element configuration for that screen begins. The scaffolding agent depends only on the first screen reference being registered — not on any element targets.

2. **Run mode:** Spawn the scaffolding agent with `run_in_background: true`. Foreground mode blocks the main conversation and defeats the purpose of the parallel pipeline — while the scaffolding agent works, the main conversation must advance the application to the next screen and configure its targets. The scaffolding agent creates a new file with no concurrent access risk, so background mode is safe.

3. **What the agent retrieves and creates** (the agent does the retrieval — orchestrator does NOT pre-fetch):
   - Reads `<PROJECT_DIR>/project.json` to obtain `expressionLanguage`.
   - Reads an existing `.xaml` in the project root (e.g., `Main.xaml`) to extract the root `<Activity>` xmlns declarations and both `<TextExpression.NamespacesForImplementation>` and `<TextExpression.ReferencesForImplementation>` blocks. Copied verbatim into the new file.
   - Runs `uip rpa get-default-activity-xaml --activity-class-name "UiPath.UIAutomationNext.Activities.NApplicationCard"` for the NApplicationCard template.
   - Writes the complete `.xaml` file: `<Activity>` root with `x:Class`, namespace declarations, TextExpression blocks, an NApplicationCard carrying `sap2010:WorkflowViewState.IdRef="NApplicationCard_1"` (no `<uix:NApplicationCard.TargetApp>` child — attachment happens next), and an empty `<Sequence DisplayName="Do">` (open/close form, not self-closing) inside the ApplicationCard body where screen agents will insert activities.
   - Attaches the registered screen to the NApplicationCard (activity ref ID `NApplicationCard_1`) per [uia-target-attachment-guide.md](uia-target-attachment-guide.md). Every CLI call is wrapped with `timeout 60000`.

4. **Post-write verification** (D-09): The agent runs `get-errors` itself, wrapped with a `timeout`:
   ```bash
   timeout 60000 uip rpa get-errors \
     --file-path "<XAML_FILE_PATH>" \
     --project-dir "<PROJECT_DIR>" \
     --output json \
       ```

5. **Self-repair** (D-10): If `get-errors` returns errors, fix and re-run. Max 3 fix cycles. After 3 attempts, stop and report remaining errors to the main conversation. **If the CLI itself times out** (Studio unresponsive, validation hung), the agent must report `"Validation unavailable — Studio not responding; file written but unverified."` and exit — never hang.

6. **Prompt template:** See [Scaffolding Agent Template](#scaffolding-agent-template) for the complete Agent() call.

## Phase 2: Screen Activity Agents

1. **Spawn precondition** — Do NOT spawn `Write-<N>` until ALL of the following hold (the orchestrator MUST verify each via `TaskGet` before calling `Agent()`):
   - (a) `Configure-<N>` is `completed` (screen N's element targets are fully configured and registered in the OR — the orchestrator hands off only reference IDs; the agent attaches them to activities itself via `link-element`).
   - (b) `Write-<N-1>` is `completed` (or `Write-Scaffold` for N=1). **If `Write-<N-1>` is `in_progress`, do NOT spawn — the chain is violated.** See [Waiting for Background Agents](#waiting-for-background-agents).

2. **Run mode:** Spawn each screen activity agent with `run_in_background: true`. While the agent writes screen N, the main conversation must advance the application to screen N+1 and configure its targets (`Configure-<N+1>`) — but it must NOT spawn `Write-<N+1>` until `Write-<N>` is `completed`. The chain requires each agent to read the previous agent's finalized file state.

3. **What the agent does** (the agent retrieves its own data — orchestrator does NOT pre-fetch):
   - Reads the file and locates the inner `<Sequence DisplayName="Do">`. Ordering safety is enforced upstream by the task queueing model (see [Waiting for Background Agents](#waiting-for-background-agents) — `Write-<N>` cannot spawn until `Write-<N-1>` is `completed`), so the agent treats the file as in a known good state.
   - Assigns unique `sap2010:WorkflowViewState.IdRef` values to each new activity per the IdRef contract in [uia-target-attachment-guide.md](uia-target-attachment-guide.md#idref-contract).
   - Runs `uip rpa get-default-activity-xaml --activity-class-name "<class>"` (with `timeout`) for each activity class in its action list.
   - Constructs and inserts activities immediately before the closing `</Sequence>` of the inner `<Sequence DisplayName="Do">`. Each activity carries its assigned IdRef and has NO `.Target` / `.SearchedElement.Target` child — attachment happens next. Does NOT modify any content before the insertion point.
   - For each action with a `reference_id`, attaches it to the activity's assigned IdRef per [uia-target-attachment-guide.md](uia-target-attachment-guide.md), passing the action's `target_property` when set. Every CLI call is wrapped with `timeout 60000`.

4. **Post-write verification** (D-09): Agent runs `get-errors` itself, wrapped with a `timeout`:
   ```bash
   timeout 60000 uip rpa get-errors \
     --file-path "<XAML_FILE_PATH>" \
     --project-dir "<PROJECT_DIR>" \
     --output json \
       ```

5. **Self-repair** (D-10): Max 3 fix cycles, then report to main conversation. If the CLI times out, the agent reports the timeout explicitly — never hangs.

6. **Prompt template:** See [Screen Activity Agent Template](#screen-activity-agent-template) for the complete Agent() call.

### Screen Boundaries

A "screen" equals everything configured before advancing the application to the next workflow state via servo. This may include intermediate servo clicks within the same logical state (for example, navigating to a list view to reveal a "New" button before configuring it) — per the Complete-then-advance rule in [uia-multi-step-flows.md](uia-multi-step-flows.md).

All `uia-configure-target` calls for the current workflow state must complete before spawning the write agent for that screen AND before using servo to advance to the next state.

See also: [uia-multi-step-flows.md](uia-multi-step-flows.md) for the Complete-then-advance rule.
See also: [uia-target-attachment-guide.md](uia-target-attachment-guide.md) and [uia-configure-target-workflows.md](uia-configure-target-workflows.md).

### Chained Dependency Model

The write agents form a strict chain — each depends on the previous:

| Agent | Depends on (`Write-<N>` blockedBy) |
|-------|-----------|
| Scaffolding agent | `Configure-<Screen 1>` |
| Screen 1 agent | `Write-Scaffold` + `Configure-<Screen 1>` |
| Screen 2 agent | `Write-<Screen 1>` + `Configure-<Screen 2>` |
| Screen N agent | `Write-<Screen N-1>` + `Configure-<Screen N>` |

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

## Phase 3: Finalization

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

1. **Pass the ref-ID-keyed action list; the agent retrieves its own XAML.** Do NOT paste activity templates, xmlns blocks, TextExpression blocks, TargetApp XAML, or `<TargetAnchorable>` snippets into the agent prompt. The orchestrator constructs a structured action list (see [Action List Format](#action-list-format)); the agent runs `get-default-activity-xaml` itself for activity templates, and uses `link-element` / `link-screen` to attach targets. Snippet fetches (`get-elements-xaml`, `get-screen-xaml`) run only on the fallback path — per ref whose link call failed.
2. Describe actions as a structured list with exact data values (`display_name`, `type`, `reference_id`, optional `text`/`duration_seconds`/`target_property`) — see [Action List Format](#action-list-format). Each action carries enough detail for the agent to construct the activity from the template it retrieves and then attach the target via `link-element`.
3. Specify interaction patterns **explicitly** for each non-trivial interaction: dropdown selection (Click then TypeInto with `[k(enter)]`), wait durations between actions, checkbox toggling, element reuse across repeated form instances. These go in a per-screen notes block in the prompt.
4. Specify **expression-language-specific syntax** for inline expressions. CSharp: `<Delay>` uses an `<InArgument x:TypeArguments="x:TimeSpan">` with a `<CSharpValue>` containing `TimeSpan.FromSeconds(N)`. VB: `<Delay Duration="[TimeSpan.FromSeconds(N)]" />`. Always match the `expressionLanguage` value passed in the prompt.
5. All context (action list, interaction patterns) goes **inline in the Agent() prompt parameter** as labeled blocks (D-06). Do not pass context via temp `.md` files or any other file-based method.
6. Include the **edit instruction** in every screen agent prompt: where to insert (before the closing `</Sequence>` tag of the inner `<Sequence DisplayName="Do">`), and what not to touch (all content before the insertion point).
7. Include the **validation instruction**: run `get-errors`, fix issues, max 3 fix cycles before reporting to main conversation.
8. **Every agent-side CLI call MUST be wrapped with a 60-second Bash `timeout`** (`timeout 60000 uip rpa ...`). On timeout, the agent must fail fast with a clear error, not retry indefinitely. Without this, a stalled `get-errors` (Studio disconnected) will cause the agent to hang for tens of minutes.

## Edge Cases

### Reused Forms (Same OR Targets, Different Data)

When the same form appears more than once (for example, a "Save & New" pattern that reopens the same contact form), treat the repetitions as screens that reuse the same OR element references but have different action sequences and data values. Each activity instance gets its own unique `sap2010:WorkflowViewState.IdRef` and its own `link-element` call — the same `--reference-id` linked to multiple `--activity-ref-id`s.

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

Skip the pipeline entirely. Spawn one agent that creates the complete file — scaffolding structure plus all screen activities — in a single pass. The pipeline overhead (separate scaffolding agent, chained dependency ordering across Tasks) is not justified for a single screen.

### Write Agent Failure

The agent self-repairs in-place (D-10): it calls `get-errors`, reads the errors, and fixes the XAML. Max 3 fix cycles. If errors remain after 3 attempts, stop and report the remaining errors to the main conversation.

Screens 1 through N-1 are already written and valid — no rollback is needed. The main conversation reads the reported error, adjusts the prompt or corrects a selector, and retries screen N's agent. The agent reads the current file state (valid through N-1) and appends from there.

### Background Agent Not Done

See [Waiting for Background Agents](#waiting-for-background-agents) for the three governing rules. In short: never spawn `Write-<N>` while `Write-<N-1>` is `in_progress` (use `TaskGet` to verify), never poll, and acknowledge every `<task-notification>` with `TaskUpdate` → `completed` in the same turn.

Write agents are typically fast — they perform pure text generation against a structured prompt and a few CLI calls. If an agent is consistently slow (e.g., >5 minutes), suspect a hung CLI call (Studio unresponsive). The 60-second `timeout` wrapper on every agent-side CLI call (Prompt Construction Rule 8) is what prevents this from cascading into 30+ minute hangs.

## Anti-patterns

1. Do NOT have a screen activity agent create the file from scratch — the scaffolding agent does that.
2. Do NOT have a screen activity agent modify activities from earlier screens — insert before the closing `</Sequence>` tag only.
3. Do NOT spawn `Write-<N>` while `Write-<N-1>` is `in_progress`. Check `TaskGet(Write-<N-1>)` first; only spawn if `completed`. Spawning early breaks the chain — the agents will race on the same insertion point.
4. Do NOT poll for agent completion. No `sleep`, no `Monitor` + `until` loop, no `ScheduleWakeup`, no file-growth checks, no respawning the agent to "see if it's done". Either do non-conflicting work, or reply with a one-line status and stop. The runtime delivers `<task-notification>` asynchronously.
5. Do NOT paste activity templates, xmlns blocks, TextExpression blocks, TargetApp XAML, or OR `<TargetAnchorable>` snippets into the agent prompt. Pass reference IDs, activity class names, and a structured action list — the agent retrieves activity templates itself and links targets via `link-element` / `link-screen`.
6. Do NOT pass unstable selectors (auto-generated numeric IDs, `css-selector` attributes, hash-based class names) to write agents — identify and fix them during target configuration via selector improvement before the agent attaches targets.
7. Do NOT duplicate pipeline logic in SKILL.md or other reference files — those files route here; this file is the single source of truth for the pipeline.
8. Do NOT skip the selector stability gate before the agent attaches targets. Syntactically valid XAML that uses runtime-broken selectors is harder to debug than a build error.
9. Do NOT modify the `.xaml` file from the main conversation while a write agent is running. The chained model depends on each agent reading the current valid file state; concurrent edits produce an unknown file state for the next agent.
10. Do NOT spawn write agents in foreground mode — this blocks the main conversation and serializes the pipeline. Always use `run_in_background: true` so the main conversation can configure the next screen's targets in parallel.
11. Do NOT call agent-side CLI commands without a `timeout` wrapper. A hung Studio causes `get-errors` to block indefinitely — agents must fail fast, not hang.

## Prompt Templates

Copy-paste these Agent() call blocks and fill placeholders. The orchestrator passes only reference IDs, activity class names, and a structured action list — the agent retrieves its own XAML via CLI.

> **Note:** Use a capable model (for example, `claude-sonnet-4-5` or higher) for write agents — XAML generation requires reliable instruction-following.

### Scaffolding Agent Template

```
Agent(
  description: "Scaffold <WORKFLOW_NAME>",
  mode: "bypassPermissions",
  run_in_background: true,
  prompt: """
Create a new UiPath XAML workflow file at `<OUTPUT_XAML_PATH>`.

## Context (retrieve these yourself — do NOT ask)

1. Read `<PROJECT_DIR>/project.json` to get `expressionLanguage` (`CSharp` or `VB`).
2. Read `<PROJECT_DIR>/Main.xaml` (or any existing `.xaml` in the project root) to extract the root `<Activity>` xmlns declarations AND both `<TextExpression.NamespacesForImplementation>` and `<TextExpression.ReferencesForImplementation>` blocks. Copy them verbatim into your output.
3. Fetch the NApplicationCard template:
   ```bash
   timeout 60000 uip rpa get-default-activity-xaml \
     --activity-class-name "UiPath.UIAutomationNext.Activities.NApplicationCard" \
     --project-dir "<PROJECT_DIR>" \
     --output json   ```
   Use the returned XAML as-is for the NApplicationCard element.
## File structure requirements

- Root `<Activity>` with `x:Class="<X_CLASS_VALUE>"` (derived from `<OUTPUT_XAML_PATH>` per the naming rule in [xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md): folder separators become underscores).
- `mc:Ignorable="sap sap2010"`, `sap2010:ExpressionActivityEditor.ExpressionActivityEditor="<CSharp|VB>"`, `sap2010:WorkflowViewState.IdRef="ActivityBuilder_1"`.
- The `<TextExpression.*>` blocks from step 2.
- A single NApplicationCard from step 3 with `sap2010:WorkflowViewState.IdRef="NApplicationCard_1"` and NO `<uix:NApplicationCard.TargetApp>` child (linking attaches it in the next step).
- Inside `<uix:NApplicationCard.Body>` → `<ActivityAction>`, create an empty `<Sequence DisplayName="Do"></Sequence>`. Use open/close form (not self-closing).

## Attachment guide

<attachment-guide>
<ATTACHMENT_GUIDE_CONTENT>
</attachment-guide>

## Attach the screen to the NApplicationCard

Following the attachment guide above, attach screen `<SCREEN_REFERENCE_ID>` to activity `NApplicationCard_1`. Wrap every CLI call with `timeout 60000`.

## Validation

After attachment:
```bash
timeout 60000 uip rpa get-errors --file-path "<OUTPUT_XAML_PATH>" --project-dir "<PROJECT_DIR>" --output json```
If it returns errors, fix and re-validate. Max 3 fix attempts. If the CLI times out (Studio unresponsive), report: "Validation unavailable — Studio not responding; file written but unverified." Do not hang.

## Placeholders

| Placeholder | Value |
|---|---|
| <OUTPUT_XAML_PATH> | <fill in> |
| <RELATIVE_XAML_PATH> | <OUTPUT_XAML_PATH> relative to <PROJECT_DIR> |
| <X_CLASS_VALUE> | <fill in> |
| <PROJECT_DIR> | <fill in> |
| <SCREEN_REFERENCE_ID> | <fill in> |
| <ATTACHMENT_GUIDE_CONTENT> | Verbatim contents of `uia-target-attachment-guide.md` — orchestrator reads the file and pastes the body here |
"""
)
```

### Screen Activity Agent Template

```
Agent(
  description: "Write <SCREEN_NAME> activities to <WORKFLOW_NAME>",
  mode: "bypassPermissions",
  run_in_background: true,
  prompt: """
Edit the file `<OUTPUT_XAML_PATH>`. Read the file first, then locate the inner `<Sequence DisplayName="Do">` inside `<uix:NApplicationCard.Body>` → `<ActivityAction>` — that is your insertion point.

## Retrieve your data (do NOT ask)

Expression language: `<EXPRESSION_LANGUAGE>` (`CSharp` or `VB`).

Activity class names you will use: `<ACTIVITY_CLASS_LIST>` (comma-separated, e.g., `UiPath.UIAutomationNext.Activities.NClick, UiPath.UIAutomationNext.Activities.NTypeInto, System.Activities.Statements.Delay`).

1. For each activity class name above, fetch its template:
   ```bash
   timeout 60000 uip rpa get-default-activity-xaml \
     --activity-class-name "<class>" \
     --project-dir "<PROJECT_DIR>" \
     --output json   ```
   Use the returned XAML as the structural base for every instance of that activity type.

## Attachment guide

<attachment-guide>
<ATTACHMENT_GUIDE_CONTENT>
</attachment-guide>

## Action list — implement in this EXACT order

Insert the following activities IMMEDIATELY BEFORE the closing `</Sequence>` tag of the inner `<Sequence DisplayName="Do">`. Do NOT modify any content before the insertion point. Each new activity carries a unique `sap2010:WorkflowViewState.IdRef` assigned per the IdRef contract in the attachment guide above, and has NO `.Target` / `.SearchedElement.Target` child — attachment happens after insertion.

<ACTION_LIST>

Each action has fields: `display_name`, `type` (NClick | NTypeInto | Delay | ...), and either `reference_id` (for UI activities) with optional `text` (for NTypeInto) and optional `target_property` (for activities whose target is not at `.Target`, e.g., `SearchedElement.Target`), or `duration_seconds` (for Delay).

For NClick: insert `<uix:NClick ... sap2010:WorkflowViewState.IdRef="NClick_<N>" />` with no `.Target` child.
For NTypeInto: set `Text` as an attribute on `<uix:NTypeInto ... sap2010:WorkflowViewState.IdRef="NTypeInto_<N>" Text="...">` with no `.Target` child.
For Delay with CSharp: `<Delay sap2010:WorkflowViewState.IdRef="Delay_<N>"><Delay.Duration><InArgument x:TypeArguments="x:TimeSpan"><CSharpValue x:TypeArguments="x:TimeSpan">TimeSpan.FromSeconds(N)</CSharpValue></InArgument></Delay.Duration></Delay>` — duration as an InArgument, NOT an attribute.
For Delay with VB: `<Delay Duration="[TimeSpan.FromSeconds(N)]" sap2010:WorkflowViewState.IdRef="Delay_<N>" />`.

## Attach targets

For every action with a `reference_id`, follow the attachment guide above to attach the OR reference to the IdRef you assigned. Pass `target_property` when the action specifies one. Wrap every CLI call with `timeout 60000`.

## Validation

After attachment (and any fallback embedding):
```bash
timeout 60000 uip rpa get-errors --file-path "<OUTPUT_XAML_PATH>" --project-dir "<PROJECT_DIR>" --output json```
Fix on error, max 3 attempts. If CLI times out, report the timeout explicitly — do NOT hang.

## Placeholders

| Placeholder | Value |
|---|---|
| <OUTPUT_XAML_PATH> | <fill in> |
| <RELATIVE_XAML_PATH> | <OUTPUT_XAML_PATH> relative to <PROJECT_DIR> |
| <PROJECT_DIR> | <fill in> |
| <EXPRESSION_LANGUAGE> | CSharp or VB |
| <ACTIVITY_CLASS_LIST> | comma-separated fully-qualified activity class names |
| <ACTION_LIST> | JSON or YAML list — see [Action List Format](#action-list-format) |
| <ATTACHMENT_GUIDE_CONTENT> | Verbatim contents of `uia-target-attachment-guide.md` — orchestrator reads the file and pastes the body here |
"""
)
```

## Action List Format

The orchestrator composes the action list once per screen agent from the registered OR references and the Phase 0 action plan. No XAML lives in the orchestrator context — only structured metadata.

```json
[
  {"display_name": "Click Accounts Nav", "type": "NClick", "reference_id": "xPMFx.../3eZ3506YOEalsrUWRMADfQ"},
  {"display_name": "Wait for Accounts List", "type": "Delay", "duration_seconds": 3},
  {"display_name": "Type Account Name", "type": "NTypeInto", "reference_id": "xPMFx.../h0mdnfakSk6gE9v5ZkYNuQ", "text": "Get Cloudy"}
]
```

Minimum fields per entry:
- `display_name` — string. Becomes the activity's `DisplayName`.
- `type` — `NClick`, `NTypeInto`, `Delay`, `NSelectItem`, `NGoToUrl`, etc.
- For UI activities: `reference_id` — the OR reference ID. The agent passes this to `link-element --reference-id` after inserting the activity.
- For UI activities whose target is not at `.Target`: optional `target_property` — dot-separated property path (e.g., `"SearchedElement.Target"`). Passed to `link-element --target-property` and used by the fallback embed path. Omit when the default `.Target` applies.
- For `NTypeInto`: optional `text` — the text to type.
- For `Delay`: `duration_seconds` instead of `reference_id`.

The agent assigns `sap2010:WorkflowViewState.IdRef` per the contract in the Screen Activity Agent Template — the orchestrator does NOT specify IdRefs in the action list.

## Task Structure

Pseudocode for the per-screen main-conversation flow (apply with `TaskCreate` / `TaskUpdate` / `TaskGet`):

```
configure_task = TaskCreate(
  subject: f"Configure-{screen_name}",
  description: f"Register screen + elements in OR for {screen_name}"
)
write_task = TaskCreate(
  subject: f"Write-{screen_name}",
  description: f"Insert activities for {screen_name} into {xaml_filename}"
)
TaskUpdate(write_task.id, addBlockedBy: [configure_task.id, previous_write_task.id])

# Main conv: do configure work
TaskUpdate(configure_task.id, status: "in_progress")
# ...run uia-configure-target, create-elements, etc.
TaskUpdate(configure_task.id, status: "completed")

# Before spawning write agent: verify predecessor (Waiting for Background Agents, rule 1)
predecessor = TaskGet(previous_write_task.id)
if predecessor.status != "completed":
  raise "Pipeline violation: cannot spawn Write-<N> while Write-<N-1> is in_progress"

TaskUpdate(write_task.id, status: "in_progress")
Agent(run_in_background: true, ...)

# On <task-notification> arrival for this agent (Waiting for Background Agents, rule 3):
TaskUpdate(write_task.id, status: "completed")
```

The scaffolding case is special: `Write-Scaffold` blockedBy `Configure-<Screen 1>` only. `Write-<Screen 1>` blockedBy `Write-Scaffold` AND `Configure-<Screen 1>`.

# Parallel XAML Authoring Guide

## When to Use This Guide

- The workflow targets **2 or more distinct screens** requiring target configuration via `uia-configure-target`
- The workflow is a **XAML workflow** (not a coded workflow in C#)
- **Single-screen workflows:** skip this pipeline entirely — one agent writes the complete file (scaffolding + activities) in a single pass

## Phase 0: Plan the Workflow

> **CRITICAL:** Complete Phase 0 before spawning any agent. All one-time data (xmlns, activity templates, expression language) must be collected first. Skipping this produces scaffolding with incomplete namespace declarations, causing all subsequent screen agents to fail.

1. **Identify screens.** List each distinct application state the workflow will interact with. A "screen" is a stable UI state where one or more elements need to be targeted — a page, a modal dialog, an inline form, or a panel that appears after an action.

2. **Map actions per screen.** For each screen, list the ordered interactions: which element, what action (Click, TypeInto, SelectItem, GoToUrl), what data value, and any special behavior (dropdown patterns, wait durations, checkbox toggling).

3. **Determine ApplicationCard scope.** Decide whether the workflow uses one ApplicationCard (all screens share the same window or browser tab — the common case for single-app web automation) or multiple (different applications or browser tabs requiring separate ApplicationCards).

4. **Identify element reuse.** Note where the same form appears more than once with different data (for example, a "Save & New" pattern that reopens the same contact form). These screens share OR targets but have separate action sequences and data values — each gets its own write agent.

5. **Collect one-time data** before starting any target configuration:

   a. **Expression language** — read from `project.json` → `expressionLanguage` field (`CSharp` or `VB`).

   b. **Activity templates** — run `uip rpa get-default-activity-xaml` for every activity type the workflow will use:
   ```bash
   uip rpa get-default-activity-xaml \
     --activity-class-name "<FULLY_QUALIFIED_CLASS_NAME>" \
     --project-dir "<PROJECT_DIR>" \
     --output json \
     --use-studio
   ```
   Collect templates for: `NApplicationCard`, `NClick`, `NTypeInto`, `NGoToUrl`, `NSelectItem`, and any other activity type the workflow uses. Save all outputs — they are passed verbatim to agent prompts.

   c. **xmlns declarations** — read from an existing `.xaml` file in the project root AND from the `get-default-activity-xaml` output for `NApplicationCard`. Combine the namespace declarations from both sources. This is the complete set needed for the root `<Activity>` element.

   d. **TextExpression imports and references** — same source as xmlns: read from an existing project `.xaml` file and from `get-default-activity-xaml` output. Collect both the `TextExpression.NamespacesForImplementation` and `TextExpression.ReferencesForImplementation` blocks.

   e. **x:Class value** — derived from the output `.xaml` filename per the naming rule in [xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md): folder separators become underscores, not dots. Root-level `MyWorkflow.xaml` → `x:Class="MyWorkflow"`. Subfolder `Workflows/MyWorkflow.xaml` → `x:Class="Workflows_MyWorkflow"`.

## Phase 1: Scaffolding Agent

1. **When to spawn:** Immediately after the first screen is registered in the Object Repository (TARGET-8 screen creation), before element configuration for that screen begins. The scaffolding agent depends only on the TargetApp XAML from the first screen registration — not on any element targets.

2. **Run mode:** Spawn the scaffolding agent with `run_in_background: true`. Foreground mode blocks the main conversation and defeats the purpose of the parallel pipeline — while the scaffolding agent works, the main conversation must advance the application to the next screen and configure its targets. The scaffolding agent creates a new file with no concurrent access risk, so background mode is safe.

3. **What the agent creates:**
   - Complete `.xaml` file with `<Activity>` root element, all xmlns declarations, and TextExpression blocks
   - `NApplicationCard` activity using the template from `get-default-activity-xaml`
   - `<TargetApp>` embedded inside the ApplicationCard — retrieved via:
     ```bash
     uip rpa uia object-repository get-screen-xaml \
       --reference-id "<SCREEN_REFERENCE_ID>" \
       --project-dir "<PROJECT_DIR>"
     ```
   - Empty `<Sequence DisplayName="Do">` inside the ApplicationCard body — this is where screen agents will insert activities

4. **Post-write verification** (D-09): Run `get-errors` only after the agent writes the file:
   ```bash
   uip rpa get-errors \
     --file-path "<XAML_FILE_PATH>" \
     --project-dir "<PROJECT_DIR>" \
     --output json \
     --use-studio
   ```

5. **Self-repair** (D-10): If `get-errors` returns errors, fix and re-run. Max 3 fix cycles. After 3 attempts, stop and report remaining errors to the main conversation.

6. **Prompt template:** See [Scaffolding Agent Template](#scaffolding-agent-template) for the complete Agent() call.

> **CRITICAL:** Remove the `xmlns` attribute from the `<TargetApp>` element returned by `get-screen-xaml` before embedding it in the agent prompt. The root `<Activity>` element's namespace declarations already cover it. Duplicate xmlns causes namespace-related validation errors.

## Phase 2: Screen Activity Agents

1. **Spawn precondition** — Do NOT spawn screen N's agent until BOTH conditions are true:
   - (a) Screen N's element targets are fully configured AND the OR XAML snippets are retrieved via `get-elements-xaml`
   - (b) The previous write agent (screen N-1, or scaffolding for N=1) has returned a result

2. **Run mode:** Spawn each screen activity agent with `run_in_background: true`. While the agent writes screen N, the main conversation must advance the application to screen N+1 and configure its targets. Wait for the background agent's completion notification before spawning the next screen's agent (the chain requires each agent to read the previous agent's finalized file state).

3. **What the agent does:**
   - Reads the current `.xaml` file
   - Locates the inner `<Sequence DisplayName="Do">` element
   - Inserts its activities immediately before the closing `</Sequence>` tag
   - Does NOT modify any content before the insertion point

4. **OR snippet retrieval** (per screen, after element OR registration):
   ```bash
   uip rpa uia object-repository get-elements-xaml \
     --reference-ids "<REF_1>,<REF_2>,<REF_3>" \
     --project-dir "<PROJECT_DIR>"
   ```

5. **Post-write verification** (D-09): Run `get-errors` only — same command as Phase 1.

6. **Self-repair** (D-10): Same as Phase 1 (max 3 cycles, then report to main conversation).

7. **Prompt template:** See [Screen Activity Agent Template](#screen-activity-agent-template) for the complete Agent() call.

> **CRITICAL:** Remove `xmlns` attributes from all `<TargetAnchorable>` elements returned by `get-elements-xaml` before including them in the agent prompt. The root `<Activity>` element's namespace declarations already cover them.

### Screen Boundaries

A "screen" equals everything configured before advancing the application to the next workflow state via servo. This may include intermediate servo clicks within the same logical state (for example, navigating to a list view to reveal a "New" button before configuring it) — per the Complete-then-advance rule in [uia-multi-step-flows.md](uia-multi-step-flows.md).

All `uia-configure-target` calls for the current workflow state must complete before spawning the write agent for that screen AND before using servo to advance to the next state.

See also: [uia-multi-step-flows.md](uia-multi-step-flows.md) for the Complete-then-advance rule.
See also: [uia-configure-target-workflows.md](uia-configure-target-workflows.md) for OR embedding patterns and passing OR data to write agents.

### Chained Dependency Model

The write agents form a strict chain — each depends on the previous:

| Agent | Depends on |
|-------|-----------|
| Scaffolding agent | First screen OR registration (no element targets needed) |
| Screen 1 agent | Scaffolding complete + Screen 1 element targets configured |
| Screen 2 agent | Screen 1 agent complete + Screen 2 element targets configured |
| Screen N agent | Screen N-1 agent complete + Screen N element targets configured |

The main conversation runs `uia-configure-target` tasks in parallel with the write chain: configure screen N+1 while screen N's write agent is running.

## Phase 3: Finalization

1. **Validate the complete workflow.** After the last write agent completes, run `get-errors` on the full file (D-11):
   ```bash
   uip rpa get-errors \
     --file-path "<XAML_FILE_PATH>" \
     --project-dir "<PROJECT_DIR>" \
     --output json \
     --use-studio
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

1. Include activity templates **VERBATIM** — paste the XAML from `get-default-activity-xaml` output into the agent prompt. Do not describe or summarize the template.
2. Include OR snippets **VERBATIM** with human-readable labels — paste the exact `<TargetAnchorable>` XML (with xmlns removed), labeled by element name. Do not summarize selectors.
3. Describe actions as an **ordered numbered list** with exact data values (for example: "1. TypeInto 'First Name' field: John  2. Click 'Save' button").
4. Specify interaction patterns **explicitly** for each non-trivial interaction: dropdown selection (Click then TypeInto with `[k(enter)]`), wait durations between actions, checkbox toggling, element reuse across repeated form instances.
5. Specify **expression-language-specific syntax** for inline expressions. CSharp: `new TimeSpan(0,0,2)` for Delay. VB: `TimeSpan.FromSeconds(2)`. Always match the `expressionLanguage` value from `project.json`.
6. All context (OR snippets, activity templates, action sequences) goes **inline in the Agent() prompt parameter** as labeled blocks (D-06). Do not pass context via temp `.md` files or any other file-based method.
7. **Always inline regardless of element count** (D-07). Do not apply a size guardrail or branch on large vs small screens.
8. Include the **edit instruction** in every screen agent prompt: where to insert (before the closing `</Sequence>` tag of the inner `<Sequence DisplayName="Do">`), and what not to touch (all content before the insertion point).
9. Include the **validation instruction**: run `get-errors`, fix issues, max 3 fix cycles before reporting to main conversation.

## Edge Cases

### Reused Forms (Same OR Targets, Different Data)

When the same form appears more than once (for example, a "Save & New" pattern that reopens the same contact form), treat the repetitions as screens that share the same `<TargetAnchorable>` snippets but have different action sequences and data values.

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

Skip the pipeline entirely. Spawn one agent that creates the complete file — scaffolding structure plus all screen activities — in a single pass. The pipeline overhead (separate scaffolding agent, chained dependency tracking) is not justified for a single screen.

### Write Agent Failure

The agent self-repairs in-place (D-10): it calls `get-errors`, reads the errors, and fixes the XAML. Max 3 fix cycles. If errors remain after 3 attempts, stop and report the remaining errors to the main conversation.

Screens 1 through N-1 are already written and valid — no rollback is needed. The main conversation reads the reported error, adjusts the prompt or corrects a selector, and retries screen N's agent. The agent reads the current file state (valid through N-1) and appends from there.

### Background Agent Not Done

Wait for the previous write agent to return a result before spawning the next write agent. Write agents are fast — they perform pure text generation against a well-specified prompt. If a write agent is consistently slower than the time it takes to configure the next screen's targets, the prompt is too large or too ambiguous.

## Anti-patterns

1. Do NOT have a screen activity agent create the file from scratch — the scaffolding agent does that.
2. Do NOT have a screen activity agent modify activities from earlier screens — insert before the closing `</Sequence>` tag only.
3. Do NOT spawn a write agent before BOTH its target configuration is complete AND the previous write agent has returned a result.
4. Do NOT pass unstable selectors (auto-generated numeric IDs, `css-selector` attributes, hash-based class names) to write agents — identify and fix them during target configuration via selector improvement before retrieving OR snippets.
5. Do NOT describe activities abstractly in the agent prompt (for example, "add a click on the login button") — paste the exact `<TargetAnchorable>` XML and specify the activity type explicitly.
6. Do NOT duplicate pipeline logic in SKILL.md or other reference files — those files route here; this file is the single source of truth for the pipeline.
7. Do NOT skip the selector stability gate before passing OR snippets to a write agent. Syntactically valid XAML that uses runtime-broken selectors is harder to debug than a build error.
8. Do NOT modify the `.xaml` file from the main conversation while a write agent is running. The chained model depends on each agent reading the current valid file state; concurrent edits produce an unknown file state for the next agent.
9. Do NOT spawn write agents in foreground mode — this blocks the main conversation and serializes the pipeline. Always use `run_in_background: true` so the main conversation can advance the application state and configure the next screen's targets in parallel.

## Prompt Templates

Copy-paste these Agent() call blocks and fill placeholders from your collected data. The Phase sections above describe when and why to spawn each agent.

> **Note:** Use a capable model (for example, `claude-sonnet-4-5` or higher) for write agents — XAML generation requires reliable instruction-following.

### Scaffolding Agent Template

```
Agent(
  description: "Create scaffolding XAML file for <WORKFLOW_NAME> with ApplicationCard and empty activity Sequence",
  mode: "bypassPermissions",
  run_in_background: true,
  prompt: """
Create the file `<OUTPUT_XAML_PATH>` with the following structure:

1. `<Activity>` root element with `x:Class="<X_CLASS_VALUE>"` and these namespace declarations:

<XMLNS_DECLARATIONS>

2. `<TextExpression.NamespacesForImplementation>` block:

<TEXTEXPRESSION_IMPORTS>

3. Inside the Activity body, create an `NApplicationCard` activity using this template (use it as-is as the structural base):

<NAPPLICATIONCARD_TEMPLATE>

4. Inside the NApplicationCard, embed this TargetApp (the `xmlns` attribute has been removed — do not add it back):

<TARGET_APP_XAML>

5. Inside the NApplicationCard body, create a `<Sequence DisplayName="Do">` with no activities inside it.

Expression language: <EXPRESSION_LANGUAGE>

After creating the file, validate:

```bash
uip rpa get-errors --file-path "<OUTPUT_XAML_PATH>" --project-dir "<PROJECT_DIR>" --output json --use-studio
```

If errors exist, fix and re-validate. Max 3 fix attempts. If errors remain after 3 attempts, stop and report the remaining errors.
"""
)
```

**Placeholder reference:**

| Placeholder | Source | When collected |
|-------------|--------|---------------|
| `<OUTPUT_XAML_PATH>` | Deterministic from workflow name | Phase 0 |
| `<X_CLASS_VALUE>` | Derived from filename per `xaml-basics-and-rules.md` naming rule (underscores, not dots) | Phase 0 |
| `<EXPRESSION_LANGUAGE>` | `project.json` → `expressionLanguage` | Phase 0 |
| `<NAPPLICATIONCARD_TEMPLATE>` | `uip rpa get-default-activity-xaml --activity-class-name "UiPath.UIAutomationNext.Activities.NApplicationCard" --project-dir "<PROJECT_DIR>" --output json --use-studio` | Phase 0 |
| `<TARGET_APP_XAML>` | `uip rpa uia object-repository get-screen-xaml --reference-id "<SCREEN_REF_ID>" --project-dir "<PROJECT_DIR>"` — remove the `xmlns` attribute before pasting | After first screen OR registration |
| `<XMLNS_DECLARATIONS>` | Read from an existing `.xaml` in the project root + `get-default-activity-xaml` output for `NApplicationCard` | Phase 0 |
| `<TEXTEXPRESSION_IMPORTS>` | Read from an existing `.xaml` in the project root + `get-default-activity-xaml` output (both NamespacesForImplementation and ReferencesForImplementation blocks) | Phase 0 |

### Screen Activity Agent Template

```
Agent(
  description: "Add Screen <N> activities to <WORKFLOW_NAME> for <SCREEN_DESCRIPTION>",
  mode: "bypassPermissions",
  run_in_background: true,
  prompt: """
Edit the file `<OUTPUT_XAML_PATH>`.

1. Read the file and locate the inner `<Sequence DisplayName="Do">` element.
2. Insert the following activities immediately BEFORE its closing `</Sequence>` tag.
3. Do NOT modify any content before the insertion point.

Expression language: <EXPRESSION_LANGUAGE>

Activity templates — use these as the structural base for each activity (use them as-is, do not construct from memory):

<ACTIVITY_TEMPLATES>

OR element targets for this screen (xmlns attributes removed — do not add them back):

<ELEMENT_SNIPPETS>

Action sequence — implement in this order:

<ACTION_SEQUENCE>

Interaction patterns for this screen:

<INTERACTION_PATTERNS>

After editing, validate:

```bash
uip rpa get-errors --file-path "<OUTPUT_XAML_PATH>" --project-dir "<PROJECT_DIR>" --output json --use-studio
```

If errors exist, fix and re-validate. Max 3 fix attempts. If errors remain after 3 attempts, stop and report the remaining errors.
"""
)
```

**Placeholder reference:**

| Placeholder | Source | When collected |
|-------------|--------|---------------|
| `<OUTPUT_XAML_PATH>` | Same path as scaffolding agent | Phase 0 |
| `<EXPRESSION_LANGUAGE>` | `project.json` → `expressionLanguage` | Phase 0 |
| `<ACTIVITY_TEMPLATES>` | `uip rpa get-default-activity-xaml --use-studio` for each activity type used in this screen (NClick, NTypeInto, NGoToUrl, NSelectItem, etc.) | Phase 0 |
| `<ELEMENT_SNIPPETS>` | `uip rpa uia object-repository get-elements-xaml --reference-ids "<REF_1>,<REF_2>,..." --project-dir "<PROJECT_DIR>"` — remove the `xmlns` attribute from each `<TargetAnchorable>` before pasting; label each with a human-readable element name | Per screen, after element OR registration |
| `<ACTION_SEQUENCE>` | Ordered numbered list from the Phase 0 plan: element name, action type (Click/TypeInto/SelectItem/etc.), data value | Per screen, from Phase 0 plan |
| `<INTERACTION_PATTERNS>` | Explicit handling rules: dropdown (Click then TypeInto with `[k(enter)]`), wait durations, checkbox toggling, element reuse across repeated form instances | Per screen, from Phase 0 plan |

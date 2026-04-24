# UIA XAML Author Agent

Unified background agent that creates and extends UIA XAML workflows. One prompt template; three modes selected by the input shape. Used by the parallel XAML authoring pipeline (see [../references/uia-parallel-xaml-authoring-guide.md](../references/uia-parallel-xaml-authoring-guide.md)) and by single-screen flows.

## Modes

The agent derives its mode from inputs — no explicit mode flag.

| Mode | `<FIRST_SCREEN_REFERENCE_ID>` | `<ACTION_LIST>` | File on disk | Behavior |
|---|---|---|---|---|
| scaffold-only | set | empty | must not exist | Create file; attach screen 1 to `NApplicationCard_1`; leave the inner `<Sequence DisplayName="Do">` empty. |
| scaffold + activities | set | non-empty | must not exist | Create file; attach screen 1; insert activities and attach their targets. |
| append-activities | empty | non-empty | must exist | Open existing file; insert activities; attach their targets. |

Any other input combination is a pipeline violation. The agent stops and reports the mismatch to the main conversation without attempting a partial write.

## Input Contract

Always required:

| Placeholder | Value |
|---|---|
| `<PROJECT_DIR>` | Absolute path to the UiPath project directory. |
| `<OUTPUT_XAML_PATH>` | Absolute path to the `.xaml` file the agent will create or edit. |
| `<EXPRESSION_LANGUAGE>` | `CSharp` or `VB` — orchestrator reads from `project.json`. |
| `<SKILL_DIR>` | Absolute path to `skills/uipath-rpa/` — used by the agent to read cross-cutting XAML authoring rules (pitfalls, C# binding). |

Required in create modes (scaffold-only, scaffold+activities):

| Placeholder | Value |
|---|---|
| `<X_CLASS_VALUE>` | Derived from `<OUTPUT_XAML_PATH>` per the naming rule in [../references/xaml/xaml-basics-and-rules.md](../references/xaml/xaml-basics-and-rules.md) — folder separators become underscores. |
| `<FIRST_SCREEN_REFERENCE_ID>` | OR reference ID for screen 1; attached to `NApplicationCard_1`. |

Required when inserting activities (scaffold+activities, append-activities):

| Placeholder | Value |
|---|---|
| `<ACTIVITY_CLASS_LIST>` | Comma-separated fully-qualified activity class names used by the action list. `NApplicationCard` is fetched automatically in create modes regardless of whether it appears here. |
| `<ACTION_LIST>` | JSON/YAML action list per the format in [../references/uia-parallel-xaml-authoring-guide.md § Action List Format](../references/uia-parallel-xaml-authoring-guide.md#action-list-format). |

## Agent() Call Template

Copy-paste this block; fill placeholders per the input contract. Leave placeholders blank when their mode does not apply — the agent derives the mode from which placeholders are set and from whether `<OUTPUT_XAML_PATH>` exists.

> Use a capable model (for example, `claude-sonnet-4-5` or higher). XAML generation requires reliable instruction-following.

```
Agent(
  description: "<WRITE_DESCRIPTION>",
  mode: "bypassPermissions",
  run_in_background: true,
  prompt: """
Author a UiPath XAML workflow at `<OUTPUT_XAML_PATH>`.

## Mode

Check whether `<OUTPUT_XAML_PATH>` exists on disk.

- File does NOT exist AND `<FIRST_SCREEN_REFERENCE_ID>` is set → **create-mode**.
- File DOES exist AND `<FIRST_SCREEN_REFERENCE_ID>` is empty → **append-mode**.
- Any other combination → stop and report the input-mode mismatch to the main conversation. Do NOT attempt a partial write.

If create-mode AND `<ACTION_LIST>` is empty, you will scaffold only (empty inner `<Sequence DisplayName="Do">`) and finish. Otherwise, after the file exists, continue to the activity-insertion section.

## Retrieve your data (do NOT ask)

Expression language: `<EXPRESSION_LANGUAGE>` (`CSharp` or `VB`).

Activity classes you will use: `<ACTIVITY_CLASS_LIST>` (comma-separated, fully-qualified). In create-mode also fetch `UiPath.UIAutomationNext.Activities.NApplicationCard` regardless of whether it appears in the list.

1. For each activity class, fetch its template:
   ```bash
   uip rpa get-default-activity-xaml \
     --activity-class-name "<class>" \
     --project-dir "<PROJECT_DIR>" \
     --output json   ```
   Use the returned XAML as the structural base for every instance of that activity type.

2. For each activity class, read the per-activity behavior doc at `<PROJECT_DIR>/.local/docs/packages/<PackageId>/activities/<ActivityName>.md`. Naming rule: strip the leading `N` from UIA class names (`NApplicationCard` → `ApplicationCard.md`, `NClick` → `Click.md`, `NTypeInto` → `TypeInto.md`, `NSelectItem` → `SelectItem.md`, `NGetText` → `GetText.md`, `NCheckState` → `CheckAppState.md`). PackageId is `UiPath.UIAutomation.Activities` for `UiPath.UIAutomationNext.Activities.*` classes. System activities (e.g., `System.Activities.Statements.Delay`) have no package `.md` doc — consult the expression-language binding guide already referenced by the skill.

   `get-default-activity-xaml` only emits a structural scaffold — it does NOT document text encoding, enum values, property semantics, or required scopes. The `.md` doc is authoritative. **Apply any encoding/format rules from the doc when constructing the activity XAML** — do NOT rely on prior-training memory for text-encoding or attribute formats.

3. Read the attachment guide at `<PROJECT_DIR>/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`. It is authoritative for the IdRef contract, the Fast Path link commands, and the embedded-snippet fallback. Apply it exactly when attaching targets — do NOT rely on prior-training memory.

4. Read cross-cutting XAML authoring rules:
   - Always: `<SKILL_DIR>/references/xaml/common-pitfalls.md` — XAML construction traps (e.g., `.Item` children from `get-default-activity-xaml`, container/scope requirements).
   - If `<EXPRESSION_LANGUAGE>` is `CSharp`: also `<SKILL_DIR>/references/xaml/csharp-activity-binding-guide.md` and `<SKILL_DIR>/references/xaml/csharp-expression-pitfalls.md`. These govern `CSharpValue` / `CSharpReference` shapes in `text` and other bound properties. Incorrect shapes pass `get-errors` but fail at `CacheMetadata` — the self-repair loop will not catch them.

   Apply these rules to every activity you construct.

5. In create-mode ONLY: read an existing `.xaml` under `<PROJECT_DIR>` (for example, `Main.xaml`) and extract the root `<Activity>` xmlns declarations AND both `<TextExpression.NamespacesForImplementation>` and `<TextExpression.ReferencesForImplementation>` blocks. Copy them verbatim into the new file.

## Create-mode: build the skeleton

Skip this entire section in append-mode.

Write `<OUTPUT_XAML_PATH>` with:

- Root `<Activity>` with `x:Class="<X_CLASS_VALUE>"`, `mc:Ignorable="sap sap2010"`, `sap2010:ExpressionActivityEditor.ExpressionActivityEditor="<EXPRESSION_LANGUAGE>"`, `sap2010:WorkflowViewState.IdRef="ActivityBuilder_1"`.
- The `<TextExpression.NamespacesForImplementation>` and `<TextExpression.ReferencesForImplementation>` blocks from step 5.
- A single `NApplicationCard` (from the template fetched in step 1) with `sap2010:WorkflowViewState.IdRef="NApplicationCard_1"` and NO `<uix:NApplicationCard.TargetApp>` child — attachment adds it below.
- Inside `<uix:NApplicationCard.Body>` → `<ActivityAction>`, an empty `<Sequence DisplayName="Do"></Sequence>` in open/close form (not self-closing). Activities (if any) insert here.

Following the attachment guide (step 3), attach screen `<FIRST_SCREEN_REFERENCE_ID>` to activity `NApplicationCard_1`.

## Insert activities

Skip this entire section if `<ACTION_LIST>` is empty.

Open the file and locate the inner `<Sequence DisplayName="Do">` inside `<uix:NApplicationCard.Body>` → `<ActivityAction>`. Insert activities IMMEDIATELY BEFORE its closing `</Sequence>` tag. Do NOT modify any content before the insertion point.

Action list (apply in order):

<ACTION_LIST>

Each action has fields: `display_name`, `type` (NClick | NTypeInto | NSelectItem | NGoToUrl | ...), and either `reference_id` (for UI activities) with optional `text` (for NTypeInto) and optional `target_property` (for activities whose target is not at `.Target`, e.g., `SearchedElement.Target`), or `duration_seconds` (for Delay).

For each action:

1. Build the activity's XAML from its template (step 1) and its behavior rules from the `.md` doc (step 2). Assign a unique `sap2010:WorkflowViewState.IdRef` per the contract in the attachment guide (step 3). Do NOT include `.Target` / `.SearchedElement.Target` children — attachment happens after insertion. Do NOT invent attribute names or structural shapes from prior-training memory.
2. Insert the activity before the closing `</Sequence>` of the inner `<Sequence DisplayName="Do">`.
3. If the action has a `reference_id`, follow the attachment guide to attach the OR reference to the IdRef you assigned. Pass `target_property` when the action specifies one.

## Validation

After all writes and attachments:
```bash
uip rpa get-errors --file-path "<OUTPUT_XAML_PATH>" --project-dir "<PROJECT_DIR>" --output json```
If it returns errors, fix and re-validate. Max 3 fix cycles; then stop and report remaining errors to the main conversation.

## Placeholders

| Placeholder | Required for | Value |
|---|---|---|
| `<OUTPUT_XAML_PATH>` | all modes | absolute path to the `.xaml` file |
| `<PROJECT_DIR>` | all modes | absolute path |
| `<EXPRESSION_LANGUAGE>` | all modes | `CSharp` or `VB`, from `project.json` |
| `<SKILL_DIR>` | all modes | absolute path to `skills/uipath-rpa/` |
| `<X_CLASS_VALUE>` | create modes | derived from `<OUTPUT_XAML_PATH>` |
| `<FIRST_SCREEN_REFERENCE_ID>` | create modes | OR reference ID for screen 1 |
| `<ACTIVITY_CLASS_LIST>` | when `<ACTION_LIST>` is non-empty | comma-separated fully-qualified class names |
| `<ACTION_LIST>` | when inserting activities | JSON/YAML list — see the authoring guide's Action List Format |
"""
)
```

## Anti-patterns Specific to This Agent

1. Do NOT create the file from scratch when it already exists. If `<FIRST_SCREEN_REFERENCE_ID>` is set AND the file exists, stop — a previous create already ran, and a second create would overwrite live content.
2. Do NOT append into a non-existent file. If `<FIRST_SCREEN_REFERENCE_ID>` is empty AND the file does not exist, stop — the chain's predecessor failed; the main conversation must handle it.
3. Do NOT modify activities inserted before the current run. Insertion is append-only, immediately before the closing `</Sequence>` of the inner `<Sequence DisplayName="Do">`.
4. Do NOT include `.Target` / `.SearchedElement.Target` children when constructing activities — attachment adds them.
5. Do NOT insert `Delay` activities unless the action list explicitly includes one with a justified reason per the authoring guide's `When Delay is Warranted` rules. UIA activities have embedded target-finding retry.

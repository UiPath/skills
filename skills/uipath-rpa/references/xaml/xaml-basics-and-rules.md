# XAML Basics and Rules

UiPath workflow XAML concepts and the Discovery → Generate/Edit → Validate & Fix → Response workflow.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->

**Read contract (Rule 22):** read this file in full, with no prior lookup, in the same assistant turn as the other T1 reads (cards and pitfalls heading list). For per-operation/activity catalogs (§ Common Editing Operations, § XAML Reference Examples), Grep `^###` in [xaml-editing-catalog.md](xaml-editing-catalog.md) and Read only matching entries; if unsure, read it.

## Critical Rules — XAML (Rules 16–21a, 24, 25)

Mandatory for all XAML authoring and editing. Cited as "Rule N" across this skill. Rule 22 and Rule 23 (`expressionLanguage`/`targetFramework` immutability) are in SKILL.md § XAML-Specific Rules; Common Rules 1–12 are also in SKILL.md.

16. **[XAML] Activity docs are the source of truth:** always check `{projectRoot}/.local/docs/packages/{PackageId}/` first.
17. **[XAML] MUST understand project structure:** read `project.json`, check expression language, and scan existing patterns; NEVER generate XAML blind.
18. **[XAML] Batch-author, single gate:** author each complete workflow in one pass, sourcing every activity from card → memory → Rule 21 triple (precedence in [execution-maps-guide.md](../execution-maps-guide.md)); run per-file `validate` to clean, then one project `build` (Common Rule 3 cadence; 5-attempt caps unchanged). For observable-output workflows, finish with one `run` and output check ([execution-maps-guide.md § Gate ≠ runtime proof](../execution-maps-guide.md#gate--runtime-proof)). On failure, fix by Rule 19 category. Card-covered activities remain card-sourced: a gate failure does not reopen `activities find`/`get-default-xaml`. If there are >2 errors with ambiguous origin, bisect by stubbing out half the new activities and re-validating.
19. **[XAML] Fix errors in order:** Package → Structure → Type → Activity Properties → Logic.
20. **[XAML] Flowchart structure and ViewState both control rendering:** every `FlowStep`/`FlowDecision`/`FlowSwitch` must be a direct child of `<Flowchart>`; only direct children enter `Flowchart.Nodes`. Wire nodes with `Flowchart.StartNode`/`FlowStep.Next`/branches and `<x:Reference>`+`x:Name`. NEVER put a `FlowStep` inside the preceding `<FlowStep.Next>`; nested-only steps are absent from `Flowchart.Nodes` and render almost nothing regardless of ViewState. New Flowchart/StateMachine/ProcessDiagram workflows require every node to have `ShapeLocation`+`ShapeSize` (`ConnectorLocation` optional; Studio auto-routes). Without ViewState Studio stacks nodes at (0,0) and does not auto-arrange on open ([canvas-layout-guide.md](canvas-layout-guide.md)). When editing, do not modify ViewState on unchanged nodes. Sequence ViewState is optional.
21. **[XAML] Read `<Activity>.md` before `activities get-default-xaml` for every activity not on the common-activity card.**
    - **Card activities/patterns:** consult [common-activity-card.md](../common-activity-card.md) and [common-pattern-card.md](../common-pattern-card.md) as lookups: Grep `^### ` for line-numbered entries, then Read matching entries (each ends at the next `###`). Read a card end-to-end only when the plan needs more than 5 entries. On a hit, author from that entry alone: skip `activities find`, `activities get-default-xaml`, and per-activity MD. Precedence is card → agent memory ([execution-maps-guide.md § Cross-session memory](../execution-maps-guide.md#cross-session-memory)) → full triple. Memory substitutes only for the triple; `validate`/`build` still gate.
    - **Other activities:** run `activities find` for the class name; read `<Activity>.md` first and make a required/use-case-relevant property checklist; run `activities get-default-xaml`; diff the checklist against the starter and add missing properties. An empty checklist means you skipped step 2, go back.
    - **Doc order:** primary `{PROJECT_DIR}/.local/docs/packages/<PackageId>/activities/<Activity>.md`; fallback `../activity-docs/<PackageId>/<closest-version>/<Activity>.md` for older versions when `.local/docs` is empty. `UiPath.UIAutomation.Activities` has no bundled fallback: `.local/docs` after installation is its sole source. If absent, do not hunt for a bundled copy; follow Rule 7a (install with consent per [uia-starter-guide.md § UIA Prerequisites](../uia-starter-guide.md)), or use the Placeholder-Selector Stub Pattern in [uia-starter-guide.md](../uia-starter-guide.md).
    - **Triggers:** if the class ends in `Trigger`, namespace contains `.Triggers`, or the description mentions “starts a job”, “Monitor Events”, or “Trigger Scope”, also read the bundled `../activity-docs/<PackageId>/<closest-version>/activities/<Activity>.md` **and** the package's bundled `overview.md`. Sparse auto-generated trigger docs omit placement guidance (entry-point vs. `ui:TriggerScope`), deployment context, and namespace/assembly gotchas; use Common Rule 12 (SKILL.md) and [trigger-pattern-guide.md](../trigger-pattern-guide.md).
    - **Skip-tax:** `get-default-xaml` omits type-default properties. For `NGetText` the starter is literally `<uix:NGetText HealingAgentBehavior="SameAsCard" />` with zero output properties; `NGetText.Value="..."` is unknown, while the output member is `TextString`. This causes `Cannot set unknown member` and blocks Object Repository linking. For `NTypeInto`, 2 of 20 properties are hidden.
    - The card is the only allowlist; do not add activities to it by personal judgment. Full procedure: § Activity Property Surface in this file.
21a. **[XAML] Built-in workflow activities use the card only for this allowlist:** `Sequence`, `If`, `Switch<T>`, `TryCatch`, `While`, `DoWhile`, `ForEach<T>`, `Assign`, `MultipleAssign`, `LogMessage`, `WriteLine`, `Delay`, `Throw`, `Rethrow`. For these, Grep [common-activity-card.md](../common-activity-card.md) for the `^### ` heading, Read the entry, and author from it. Otherwise check [common-pattern-card.md](../common-pattern-card.md) likewise; its patterns include text-file read/append/write, file copy, CSV, DataTable→CSV, queue publish, retry wrap, `InvokeWorkflowFile`, InvokeCode rows, and HTTP→JSON. Use full Rule 21 only when both cards miss. `Pick`, `Parallel`, and `ParallelForEach<T>` are on neither card. Studio toolbox While/Do While/For Each emit `UiPath.Core.Activities.InterruptibleWhile`, `UiPath.Core.Activities.InterruptibleDoWhile`, and `UiPath.Core.Activities.ForEach<T>`, not framework `System.Activities.Statements.While`/`DoWhile`/`ForEach<T>`.
24. **[XAML] Wrap every container body/branch in `<Sequence>`, including a single activity:** Studio's designer expects the wrap as a drop zone; Studio's emitter produces it. `validate` and `build` accept the bare form, so neither catches missing wrappers. Applies to creation and editing alike. Slots include `If.Then`/`If.Else`, `While`/`DoWhile` body, `ForEach.Body`, `TryCatch.Try`/`Catch`/`Finally`, `Switch.Default` and each case, `PickBranch.Trigger`/`Action`, and `NApplicationCard.Body`. See § Container Activity Bodies — Wrap in Sequence.
25. **[XAML] Every activity element has a unique permanent `sap2010:WorkflowViewState.IdRef`.** Breakpoints (`debug start --breakpoints 'activityIdRef=...'`), `focus-activity`, and `validate` locations use IdRef; changing one breaks them.
    - New activity: `IdRef=<TypeName>_<N>`, where `<TypeName>` is the local name without prefix, retaining generic backtick-arity (`ForEach`1`, `Catch`1`, `Switch`1`), and `<N>` is the highest existing N for that type in the file + 1. Grep `IdRef="<TypeName>_` first; never fill gaps or reuse deleted numbers. New files start each type at `_1`.
    - Existing activity: NEVER change its IdRef for property, `DisplayName`, expression, move, or wrapping edits. A wrapper gets a new IdRef; the inner keeps its own. NEVER renumber after deleting an activity. Replacing an activity with one of a different type, or duplicating an activity, assigns a new IdRef per the "New activity" rule; a copy never keeps the source's IdRef.
    - Apply to root `<Activity>` (`ActivityBuilder_1`), every activity including `Sequence`, `FlowStep`/`FlowDecision`/`FlowSwitch`, `State`, `Transition`, `Catch`1`, `AssignOperation`, `CSharpValue`1`, and `CSharpReference`1`. Do not apply to `Variable`, `InArgument`/`OutArgument`/`InOutArgument`, `ActivityAction`, `DelegateInArgument`, or `x:Reference`.
    - Format is only `<TypeName>_<N>`; descriptive suffixes such as `Assign_OutputDir` are wrong (`DisplayName` supplies descriptions). The root must declare `xmlns:sap2010` and list `sap2010` in `mc:Ignorable` (§ XAML File Anatomy). Card snippets and `get-default-xaml` output have no IdRefs; add them when inserting.

## XAML Task Navigation & Quick Reference

### Task Navigation — XAML

| Need | Read |
|---|---|
| Create XAML test case (Given-When-Then) | [testing-guide.md § XAML Test Case Structure](../testing-guide.md); register in `fileInfoCollection` (Common Rule 10) |
| Mock testing | [testing-guide.md § Mock Testing (WIP)](../testing-guide.md); CLI command is not yet available |
| XAML test activities | [testing-guide.md § XAML Test Activities](../testing-guide.md) |
| Execution templates | [testing-guide.md § Execution Templates](../testing-guide.md) |
| Use a common activity (`Sequence` / `If` / `Switch<T>` / `TryCatch` / `While` / `DoWhile` / `ForEach<T>` / `Assign` / `LogMessage` / `WriteLine` / `Delay` / `Throw` / `Rethrow`) | [common-activity-card.md](../common-activity-card.md), Rule 21a |
| Common multi-activity pattern | [common-pattern-card.md](../common-pattern-card.md) — Rule 21a lookup, alongside the activity card, not instead of it |
| Flowchart | [canvas-layout-guide.md](canvas-layout-guide.md), § Flowchart Structure & Wiring then § Flowchart Layout |
| StateMachine | § State Machine here → [canvas-layout-guide.md § State Machine Layout](canvas-layout-guide.md#4-state-machine-layout) |
| Create/edit Long Running Workflow (ProcessDiagram) | [long-running-workflow-guide.md](long-running-workflow-guide.md) → [canvas-layout-guide.md](canvas-layout-guide.md) |
| Multi-screen UIA XAML | Package guide § Multi-Screen Authoring (from core guide § Documentation, Rule 7); default author-once-after-capture with one `validate`+`build` gate (Rule 18), interleave per screen only for long captures (5+ screens); [execution-maps-guide.md § Journey: UIA capture + build](../execution-maps-guide.md#journey-uia-capture--build-xaml) |
| Data Fabric entities | [activity-docs overview](../activity-docs/UiPath.DataService.Activities/overview.md) |
| Data Fabric filters | [data-service-filter-builder-guide.md](../activity-docs/UiPath.DataService.Activities/guides/data-service-filter-builder-guide.md) → [QueryEntityRecords](../activity-docs/UiPath.DataService.Activities/activities/QueryEntityRecords.md) |
| IS connector | [is-connector-xaml-guide.md](../is-connector-xaml-guide.md) — includes connector discovery + connection lifecycle |
| Event-triggered workflow (O365 / Gmail / Salesforce / Jira / Slack / ServiceNow / time / queue / file watcher / UI click) | [trigger-pattern-guide.md](../trigger-pattern-guide.md) → `activity-docs/{PackageId}/{closest}/activities/<TriggerActivity>.md` |
| Existing `ui:TriggerScope` | [trigger-pattern-guide.md § Reading and Editing Existing TriggerScope XAML](../trigger-pattern-guide.md) |
| Troubleshooting | [common-pitfalls.md](common-pitfalls.md), Rule 22 lookup → [cli-reference.md § Validation Iteration Loop](../cli-reference.md#validation-iteration-loop) |

### Expression Language

Check `expressionLanguage` in `project.json`. VB.NET uses `[brackets]`; C# uses `CSharpValue<T>`/`CSharpReference<T>` and the canonical forms in [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md). New projects default to VB.NET.

### Key CLI Commands

| Command | Purpose |
|---|---|
| `activities find --query "<keyword>"` | Discover activities by keyword |
| `activities get-default-xaml --activity-class-name "<class>"` | Get starter XAML for an activity |
| `analyzer-rules list --project-dir "<dir>"` | List enabled Workflow Analyzer rules — on demand only (user asks about project rules, or repeated violations of one rule family); `validate`/`build` enforce the rules without it |
| `validate --file-path "<file>"` | Per-file deep validation (structure, references, analyzer rules, unknown members, invalid enums, expression compilation) |
| `build "<PROJECT_DIR>"` | Whole-project compile + packaging gate — every workflow, including files `validate` was never pointed at ([cli-reference.md § What each phase covers](../cli-reference.md#what-each-phase-covers)) — run after `validate` is clean |

### Common Activities

| Activity | Package | Purpose |
|----------|---------|---------|
| **UI automation** (Use Application/Browser, Click, Type Into, Get Text, Select Item, …) | `UiPath.UIAutomation.Activities` | **Never author from memory or from this row.** Selectors and targets are captured, not hand-written — read the UIA package guide (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md`) in full first (Rule 7). |
| If | built-in | Conditional branching |
| Assign | built-in | Set variable/argument values |
| For Each | built-in | Iterate over a collection |
| Invoke Workflow File | built-in | Call another workflow file |
| Create Entity Record | `UiPath.DataService.Activities` | Create a Data Fabric entity record |
| Query Entity Records | `UiPath.DataService.Activities` | Query Data Fabric records with filters — see [filter builder guide](../activity-docs/UiPath.DataService.Activities/guides/data-service-filter-builder-guide.md) |

### Related XAML References

- [xaml-editing-catalog.md](xaml-editing-catalog.md): per-entry arguments/variables/imports/assembly references, C#/VB expressions, resource types, complete workflows; Grep `^###`, Read matching entries (Rule 22).
- [common-pitfalls.md](common-pitfalls.md): activity gotchas, scopes, property conflicts (Rule 22).
- [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md): C# bindings and pitfalls.
- [canvas-layout-guide.md](canvas-layout-guide.md): Flowchart vocabulary/wiring, forbidden nested chain, Flowchart/State Machine/LRW ViewState.
- [long-running-workflow-guide.md](long-running-workflow-guide.md): LRW dependency, nodes, gateways, suspend/resume.
- [jit-custom-types-schema.md](jit-custom-types-schema.md): JIT custom types.
- [../reframework-guide.md](../reframework-guide.md): REFramework modes, configuration file per template, SetTransactionStatus queue guard, Config.xlsx trap.
- [../data-manipulation-guide.md](../data-manipulation-guide.md): DataTable LINQ, strings, RegEx, DateTime, conversion, collections, JSON; VB/C#.
- [../error-handling-guide.md](../error-handling-guide.md): exception taxonomy, Try/Catch, Retry Scope, Global Exception Handler, transaction boundaries and retry ownership.
- [../library-authoring-guide.md](../library-authoring-guide.md): reusable-library contract, layout sidecar, error contract, SemVer, pack/publish.

## Authoring Workflow

Discovery-first approach with iterative error-driven refinement. Always understand before acting, start simple, validate continuously.

**Core principles:**

1. **Activity Docs Are the Source of Truth** — installed packages ship structured documentation at `{projectRoot}/.local/docs/packages/{PackageId}/` with source-accurate properties, types, defaults, enum values, conditional property groups, and working XAML examples. Always check for them first.
2. **Know Before You Write** — **NEVER** generate XAML blind. Understand the project structure, packages, expression language, and existing patterns.
3. **Use What You Know, Skip What You Don't Need** — if you already know the package ID and activity class name, go directly to its doc file. The discovery steps are a priority ladder, not a mandatory checklist.
4. **Batch-Author, Single Gate, Fix by Category** — one workflow at a time; author each workflow complete in one pass (SKILL.md Rule 18; source activities card → memory → discovery triple), then per-file `validate` to clean and exit only on a clean project-level `build` (§ Phase 3). Fix order: Package → Structure → Type → Activity Properties → Logic.

### Request Classification

`CREATE` (“generate”, “create”, “make”, “build”, “new”) → Discovery → Generate. `EDIT` (“update”, “change”, “fix”, “modify”, “add to”) → Discovery → Edit. If the target file is unclear, ask the user rather than guessing.

### Phase 1: Discovery

Batch across activities: do NOT run the find → read-doc → `get-default-xaml` triple one activity at a time. Emit all `activities find` calls in parallel, then all `<Activity>.md` `Read`s in parallel, then all `get-default-xaml` calls in parallel; author one complete workflow per `Write`, then gate (SKILL.md § Execution Maps).

#### Step 1.1: Project Structure

```
Glob: pattern="**/*.xaml" path="{projectRoot}"
Read: file_path="{projectRoot}/project.json"
```

Determine location conventions, names, similar workflows, VB/C# (`expressionLanguage`), packages, and reusable connections/credentials/objects.

#### Step 1.2: Discover Activity Documentation (Primary Source)
**Read `<Activity>.md` BEFORE `activities get-default-xaml`, every time, even for activities that look simple.** The doc is the property surface; the CLI starter is not — see [§ Activity Property Surface](#activity-property-surface-and-starter-xaml) for the skip-tax and the full per-activity procedure.

Read `<Activity>.md` before `activities get-default-xaml`, every time, even for activities that look simple, except the Rule 21/21a card path; see [§ Activity Property Surface](#activity-property-surface-and-starter-xaml). Installed docs are at `{projectRoot}/.local/docs/packages/{PackageId}/` and exist only for installed packages and typically only for newer package versions; if unavailable, install/update the package, prefer minor/patch over major jumps (for example 23.x → 26.x may deprecate activities), then use `skills/uipath-rpa/references/activity-docs/<PackageId>/<closest-version>/` or Steps 1.4-1.7. Package docs contain `overview.md`, `activities/{ActivitySimpleClassName}.md`, and `coded/` (ignore `coded/` for XAML). Activity docs contain Header → Metadata → Properties (Input, Output, Conditional groups, Common) → Valid Configurations → Enum Reference → XAML Examples → Notes.

| Situation | Action |
|---|---|
| Know package and activity | Read `{projectRoot}/.local/docs/packages/{PackageId}/activities/{ActivityName}.md` |
| Know package only | Read `overview.md`, then the identified activity doc |
| Unknown package | Run `ls {projectRoot}/.local/docs/packages/` via Bash, then `ls` candidate `activities/` and Read by path; do not use `Glob`/`Grep` because they skip gitignored `.local/` |
| Activity undocumented | Use other docs structurally, then `activities get-default-xaml` |
| No package docs | Update first; if still absent, use Steps 1.4-1.7 |
| Package not installed | Install first; both docs and `get-default-xaml` require it |
| No `.local/docs/` | Start at Step 1.3 |

#### Step 1.3: Search Current Project

Search existing workflows for reusable patterns and conventions:
```
Glob: pattern="**/*pattern*.xaml" path="{projectRoot}"
Grep: pattern="ActivityName|pattern" path="{projectRoot}"
Read: file_path="{projectRoot}/ExistingWorkflow.xaml"
```
Prioritize local patterns in mature projects; skip in greenfield projects.

#### Step 1.4: Discover Activities (When Needed)

Find which activity implements a user-described action:
```bash
uip rpa activities find --query "send mail" --limit 10 --output json
```
Results are global, not installation-limited. Install a useful uninstalled package immediately. Tags can narrow results. Do not assume the first result is right; nothing in a result marks the difference. For mail, classic Office 365 `SendMail`/`GetMail` require `Office365ApplicationScope`, while `*Connections` activities do not, and either can come first. When the results hold several activities for the same action, read the package's `overview.md` and take the one it says to use (Office 365: the `*Connections` activities).

#### Step 1.5: Disambiguate Approach and Provider

For API vs UI Automation vs Connector, auto-select when stated or only one is viable; prompt when multiple are viable and no preference was given. **Do NOT install packages until approach is confirmed.** For providers, auto-select when specified, uniquely matched, already installed, represented by a project connection, or already used; prompt only as a last resort with the top 2–4 choices and recommendations.

#### Step 1.6: Resolve Activity Properties (Fallback)

Use `uip rpa activities get-default-xaml` when activity docs are insufficient:
```bash
# Non-dynamic activity:
uip rpa activities get-default-xaml --activity-class-name "<FULLY_QUALIFIED_CLASS>" --output json
# Dynamic activity (connector-backed):
uip rpa activities get-default-xaml --activity-type-id "<TYPE_ID>" --connection-id "<CONN_ID>" --output json
```
For JIT custom types, Read `file_path="{projectRoot}/.project/JitCustomTypesSchema.json"`; see [jit-custom-types-schema.md](jit-custom-types-schema.md).

#### Step 1.7: Search Examples Repository

When docs, find, and starter XAML are insufficient, run:
```bash
uip rpa workflow-examples list --tags web --limit 10 --output json
uip rpa workflow-examples get --key "<BLOB_PATH>"
```
Allowed complete tag list: `adobe-sign`, `asana`, `box`, `concur`, `confluence`, `database`, `document-understanding`, `docusign`, `dropbox`, `email-generic`, `excel`, `excel-online`, `freshbooks`, `freshdesk`, `github`, `gmail`, `google-calendar`, `google-docs`, `google-drive`, `google-sheets`, `gsuite`, `hubspot`, `intacct`, `jira`, `mailchimp`, `marketo`, `microsoft-365`, `onedrive`, `outlook`, `outlook-calendar`, `pdf`, `powerpoint`, `productivity`, `quickbooks`, `salesforce`, `servicenow`, `sharepoint`, `shopify`, `slack`, `smartsheet`, `stripe`, `teams`, `testing`, `trello`, `web`, `webex`, `word`, `workday`, `zendesk`, `zoom`.

#### Step 1.8: Get Current Context (As Needed)

```
Read: file_path="{projectRoot}/project.json"
Glob: pattern="**/*" path="{projectRoot}/.objects/"
Bash: uip is connections list --output json
```

#### Step 1.9: Discover Connector Capabilities (For IS/Connector Workflows)

For connector/connection discovery and end-to-end `ConnectorActivity` XAML (connection, type ID, Configuration blob, FieldObjects), read **[../is-connector-xaml-guide.md](../is-connector-xaml-guide.md)** — worked example included.

Use generic IS `ConnectorActivity` with a typed operation typeId by default (for example `37a305b2-...` for Slack “Send Message to Channel”) via the guide’s schema-driven CLI flow; works via `UiPath.IntegrationService.Activities`. Use generic `ConnectorActivity` with `ConnectorHttpActivity` typeId only as fallback for an unmodeled endpoint; fields remain connector-defined, not `method`/`path`/`body`, so read the schema. Avoid per-product BAF packages (`UiPath.Slack.Activities`, `UiPath.Salesforce.Activities`, etc.) for headless authoring; they use `ScopeActivity` plus dynamic `BusinessEntity`, `SelectedFields`, `PopulatedAPIParameters`. Use BAF only when the project already does.

### Phase 2: Generate or Edit

**UI Automation — Target Configuration Gate (MANDATORY).** Before writing any XAML with UI activities: the UIA package guide (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md`) MUST be read IN FULL first (SKILL.md Rule 7). Every UI element target MUST be configured through the `uia-configure-target` skill flow — the guide mandates the target-capture orchestration reference to read IN FULL first. **NEVER** manually call low-level `uip rpa uia` CLI commands outside of the skill flow.

For CREATE, do not Read scaffolded `Main.xaml`; the wholesale `Write` replaces it. Put required data files (`mkdir` and sample inputs) in the same assistant message. Author the complete workflow in one `Write` (SKILL.md Rule 18 — every activity sourced card → memory → discovery triple), then gate in Phase 3; follow [§ XAML File Anatomy](#xaml-file-anatomy), using folder conventions and descriptive filenames. For EDIT, always Read first and use `Edit` with exact, unique `old_string` matches.
**For CREATE requests:** Use the `Write` tool to create the `.xaml` file per [§ XAML File Anatomy](#xaml-file-anatomy). Infer the file path from folder conventions; use descriptive filenames.

### Phase 3: Validate & Fix Loop

**MUST** repeat until both `validate` and `build` report 0 errors, with at most 5 fix attempts per loop; then stop and present remaining errors. Before the first fix iteration, read [../cli-reference.md § Validation Iteration Loop](../cli-reference.md#validation-iteration-loop).

Run one Bash call, chaining phases with `&&` so a `validate` failure stops before `build` and the pass path costs one turn, never one turn per command (the journey map's gate row in [execution-maps-guide.md](../execution-maps-guide.md)):
```bash
uip rpa validate --file-path "Workflows/MyWorkflow.xaml" --project-dir "<PROJECT_DIR>" --output json \
  && uip rpa build "<PROJECT_DIR>" --log-level Warn --output json
```
`--file-path` must be **relative to the project directory**. Clean `validate` is only half-done; clean `build` exits the loop. For observable outputs, finish with one `uip rpa run --skip-build` and inspect outputs ([execution-maps-guide.md § Gate ≠ runtime proof](../execution-maps-guide.md#gate--runtime-proof)).

Fix in order: (1) Package—install/update and make docs available; (2) Structure—use [§ XAML File Anatomy](#xaml-file-anatomy) and [§ XAML Safety Rules](#xaml-safety-rules); (3) Type—check docs, types, enum values, and [jit-custom-types-schema.md](jit-custom-types-schema.md); (4) Activity Properties—read docs for properties, conditional groups, valid configurations, and use starter XAML as fallback; watch OverloadGroup conflicts; (5) Logic—match expression language; for UIA run `debug start` and follow [../uia-starter-guide.md § Running UI Automation Workflows](../uia-starter-guide.md). When stuck, defer minor configuration details to the user; use InvokeCode only as a last resort.

### Phase 4: Response

Report created/edited file path, brief description, key activities/logic, installed packages, limitations/notes, suggested next steps (testing and parameterization), and encourage review/customization of placeholders and connections.

### Anti-Patterns

- NEVER design sprawling monoliths; split logic into invoked files ([../environment-setup.md § Designing for Reuse](../environment-setup.md#designing-for-reuse)); Rule 18 still requires one complete workflow per batch.
- NEVER manually craft UI selectors outside `uia-configure-target`.
- NEVER guess properties, types, or configurations; never ignore conditional property groups.
- NEVER use a `workflow-examples get` key not returned by `list`.
- NEVER ask for a provider before checking project signals.
- NEVER retry failing CLI commands without diagnosing the root cause.
- NEVER use connector activities without checking connection existence.
- NEVER generate full XAML without a sourced starter per activity: card/pattern-card entry, validated memory snippet, or `activities get-default-xaml` (precedence: SKILL.md Rule 21).
- NEVER assume a mutation succeeded; run `uip rpa validate` AND `uip rpa build` after every mutation.
- NEVER treat `validate` “no diagnostics found” as final; run `build` next.
- NEVER skip environment readiness; verify the project opens and restores cleanly ([environment-setup.md](../environment-setup.md)).

## XAML File Anatomy

Every workflow root follows this structure. `x:Class` equals the file’s project-relative path without `.xaml`, with separators replaced by underscores: `MyWorkflow.xaml` → `MyWorkflow`; `Workflows/SendEmail.xaml` → `Workflows_SendEmail`. Dots such as `Workflows.SendEmail` cause *"Invalid ActivityBuilder name … Suggested name …"*. In a C# project the root also carries `sap2010:ExpressionActivityEditor.ExpressionActivityEditor="C#"`, as `init` writes it in `Main.xaml`: Studio opens a root without it as VisualBasic and refuses the file, while `validate` and `build`, which compile in the project's language, pass it.

```xml
<Activity mc:Ignorable="sap sap2010 sads" x:Class="FolderName_FileName"
  sap2010:WorkflowViewState.IdRef="ActivityBuilder_1"
  xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:sap="http://schemas.microsoft.com/netfx/2009/xaml/activities/presentation"
  xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
  xmlns:sads="http://schemas.microsoft.com/netfx/2010/xaml/activities/debugger"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
  <!-- Additional xmlns for activity packages -->
  >
  <!-- TextExpression.NamespacesForImplementation (C# imports) -->
  <TextExpression.NamespacesForImplementation>
    <sco:Collection x:TypeArguments="x:String" xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib">
      <x:String>System</x:String><x:String>System.Collections.Generic</x:String><x:String>System.Linq</x:String>
      <!-- More namespace imports -->
    </sco:Collection>
  </TextExpression.NamespacesForImplementation>
  <!-- TextExpression.ReferencesForImplementation (assembly references) -->
  <TextExpression.ReferencesForImplementation>
    <sco:Collection x:TypeArguments="AssemblyReference" xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib">
      <AssemblyReference>System</AssemblyReference>
      <!-- More assembly references -->
    </sco:Collection>
  </TextExpression.ReferencesForImplementation>
  <!-- x:Members (arguments) -->
  <x:Members>
    <x:Property Name="in_Name" Type="InArgument(x:String)" />
    <x:Property Name="out_Result" Type="OutArgument(x:Int32)" />
    <x:Property Name="io_Data" Type="InOutArgument(x:String)" />
  </x:Members>
  <Sequence DisplayName="Main Sequence" sap2010:WorkflowViewState.IdRef="Sequence_1">
    <Sequence.Variables><Variable x:TypeArguments="x:String" Name="tempVar" Default="hello" /></Sequence.Variables>
    <!-- Activities go here, each with its own IdRef (Rule 25) -->
  </Sequence>
</Activity>
```

Fill `ReferencesForImplementation` per [common-pitfalls.md § Assembly References Studio Requires and the CLI Does Not Check](common-pitfalls.md#assembly-references-studio-requires-and-the-cli-does-not-check). Older files may contain `<sap2010:WorkflowViewState.ViewStateManager>`; never add it to new files and never edit an existing one.

## Workflow Types

### Sequence

Linear, step-by-step execution; best for straightforward processes. ViewState is optional.
```xml
<Sequence DisplayName="My Sequence">
  <!-- Activities execute top to bottom -->
</Sequence>
```

### Flowchart

Branching workflow. All `FlowStep`/`FlowDecision`/`FlowSwitch` nodes are direct `<Flowchart>` children; wire them via `<x:Reference>` inside property elements (`Flowchart.StartNode`, `FlowStep.Next`, `FlowDecision.True/False`); never use nested-only chains. See [canvas-layout-guide.md § Flowchart Structure & Wiring](canvas-layout-guide.md#flowchart-structure--wiring) and [§ Flowchart Layout](canvas-layout-guide.md#3-flowchart-layout).

### State Machine

State-based workflow with transitions. Best for long-running processes with distinct states (e.g., REFramework).

```xml
<StateMachine InitialState="{x:Reference __ReferenceID0}" DisplayName="My State Machine"
              sap2010:WorkflowViewState.IdRef="StateMachine_1">
  <State x:Name="__ReferenceID0" DisplayName="Initial State">
    <State.Entry>
      <Sequence DisplayName="Initialize">
        <!-- Activities when entering state -->
      </Sequence>
    </State.Entry>
    <State.Transitions>
      <Transition DisplayName="To Processing">
        <Transition.Condition>[condition]</Transition.Condition>
        <Transition.To>
          <x:Reference>__ReferenceID1</x:Reference>
        </Transition.To>
      </Transition>
    </State.Transitions>
  </State>
  <State x:Name="__ReferenceID1" DisplayName="Processing">
    <!-- State.Entry, State.Transitions -->
  </State>
  <State x:Name="__ReferenceID2" DisplayName="End" IsFinal="True" />
</StateMachine>
```

States are direct `<StateMachine>` children; `InitialState` references the start state, `IsFinal="True"` marks a terminal state, and transitions use `<Transition.To><x:Reference>__ReferenceID</x:Reference></Transition.To>`. ViewState is required; see [canvas-layout-guide.md § State Machine Layout](canvas-layout-guide.md#4-state-machine-layout).

### Long Running Workflow (ProcessDiagram)

BPMN-style horizontal, event-driven flow using `upa:ProcessDiagram`, `EventNode`, `TaskNode`, `DecisionNode`, and `EndNode`.

Requires additional namespaces:
```xml
xmlns:upa="clr-namespace:UiPath.Process.Activities;assembly=UiPath.Process.Activities"
xmlns:upas="clr-namespace:UiPath.Process.Activities.Shared;assembly=UiPath.Process.Activities"
```
These types ship in **`UiPath.FlowchartBuilder.Activities`** (runtime assembly `UiPath.Process.Activities`); install it before authoring (Common Rule 6). It is unsupported on `targetFramework: "Legacy"`. Flows are left-to-right; `EventNode` starts/ends, `TaskNode` is a task, `DecisionNode` branches True/False, `EndNode` ends, and `BoundaryNode` attaches to `TaskNode.BoundaryNodes`. Use the same `<x:Reference>` registration rules as Flowchart, including trailing registration for inline nodes. Gateway nodes (`SplitNode`/`MergeNode`/`SwitchNode<T>`), subprocesses, intermediate events, and persistence waits are in [long-running-workflow-guide.md](long-running-workflow-guide.md). ViewState is required; see [canvas-layout-guide.md § Long Running Workflow](canvas-layout-guide.md#5-long-running-workflow-processdiagram-layout).

## XAML Safety Rules

### ViewState Rules

Sequences need no coordinates — Studio auto-manages `IsExpanded` state. Flowcharts, State Machines, and LRWs require ViewState because absent coordinates stack nodes at (0,0); Studio does not auto-arrange on open — the stacked layout persists until a user manually triggers Auto Arrange. In existing files, do not modify the global `<sap2010:WorkflowViewState.ViewStateManager>` section (it can corrupt the designer layout) or ViewState on unchanged nodes. Do NOT change or renumber any existing `sap2010:WorkflowViewState.IdRef` — new activities get the next free number for their type (Rule 25); read existing positions before adding nodes. In new Flowchart/StateMachine/ProcessDiagram files, every node requires `ShapeLocation`+`ShapeSize`; `ConnectorLocation` is optional and Studio auto-routes. See [canvas-layout-guide.md](canvas-layout-guide.md).

### Preserve xmlns Declarations

Never remove root `<Activity>` `xmlns` declarations; add only as needed. Removing a referenced namespace causes validation errors.

### Respect Expression Language

Check the project first. **CSharp:** use C# (`+`, `==`), `<CSharpValue>` for inputs and `<CSharpReference>` for outputs, without a namespace prefix; never use `[bracket]` shorthand, which creates `VisualBasicValue` and multiple-language errors. **VB:** use `&`, `=`, and `[bracket]` expressions. Mixing languages breaks builds.

### Activity Property Surface and Starter XAML

Never construct activity XAML from memory. Use `<Activity>.md` first for the authoritative property surface, types, defaults, required scopes, conditional groups, and valid configurations, then `uip rpa activities get-default-xaml --activity-class-name "<FullClassName>"` for namespaces, references, and non-default properties. The primary path is `{PROJECT_DIR}/.local/docs/packages/<PackageId>/activities/<Activity>.md`; Read it directly because failed Read is the existence check and `Glob`/`Grep` skip gitignored `.local/`. Fallback is `../activity-docs/<PackageId>/<closest-version>/<Activity>.md`; routing is in [§ Step 1.2](#step-12-discover-activity-documentation-primary-source). If neither exists, record that the package is third-party/unusual, use `activities find` + `activities get-default-xaml`, and warn that the property surface may be incomplete.

**Skip-tax:** starters omit `null`, `0`, `false`, and unset properties. `NTypeInto` hides 2 of 20; `NClick` hides ~3 of ~15; `NGetText` is literally `<uix:NGetText HealingAgentBehavior="SameAsCard" />` with no output member. `NGetText.Value` is unknown and causes `Cannot set unknown member 'UiPath.UIAutomationNext.Activities.NGetText.Value'`, breaking the activity tree and Object Repository linking. When authoring a new Get Text, bind the output to `TextString` (`OutArgument<string>`). `NGetText` also has legacy non-generic `Text` `OutArgument`; it writes both at runtime and a `Text="..."` binding in an existing or older workflow is valid and must not be flagged or "corrected" — only `Value` is a genuine unknown member. Other hidden properties include `ClickType`, `KeyModifiers`, `WaitForReady`, and `EmptyFieldMode`.

Run this procedure for every non-card activity:
1. Run `uip rpa activities find --query "<keyword>" --output json` and obtain fully qualified class name, type ID, and `isDynamicActivity`.
2. Locate the MD by primary→fallback order and write a checklist of required and use-case-relevant optional properties. If neither doc location has the file, record that explicitly and proceed to step 3 with a flag in your output; if you cannot name required properties, you read the wrong file.
3. Run `uip rpa activities get-default-xaml` for the starter.
4. Diff the checklist against the starter and add missing properties. An empty checklist without a third-party flag means step 2 was skipped — go back to step 2; do NOT author from the starter alone.
5. Run `uip rpa validate`.

**Anti-pattern.** Treating `activities get-default-xaml` output as the complete property surface. The CLI runs XAML serialization on a default-constructed instance; type-default values are omitted by design.

The procedure applies to every activity not on [common-activity-card.md](../common-activity-card.md). Card activities skip find, starter, and per-activity MD read; the card is version-anchored and authoritative. Do not self-extend it. Use `uip rpa workflow-examples list` and `uip rpa workflow-examples get` as additional examples. If validation reports `Cannot set unknown member '<Class>.<Prop>'`, check installed-version MD: names drift (for example UIA `26.4.1-preview` renamed `InputMode` → `InteractionMode` and `EmptyField` → `EmptyFieldMode`).

### Container Activity Bodies — Wrap in Sequence

Studio expects every body/branch slot to be a `<Sequence>` drop zone, even for one activity; `validate` and `build` do not detect omission.

| Activity | Slots | Wrapper |
|---|---|---|
| `If` | `If.Then`, `If.Else` | `<Sequence DisplayName="Then">` / `<Sequence DisplayName="Else">` |
| `While`, `DoWhile` | direct body | `<Sequence DisplayName="Body">` |
| `ForEach<T>` | `ForEach.Body` → `ActivityAction<T>` | `<Sequence DisplayName="Body">` |
| `TryCatch` | `TryCatch.Try` | `<Sequence DisplayName="Try">` |
| `TryCatch` | each `Catch` → `ActivityAction<T>` body | `<Sequence DisplayName="Catch">` |
| `TryCatch` | `TryCatch.Finally` | `<Sequence DisplayName="Finally">` |
| `Switch<T>` | `Switch.Default`, each `<x:String x:Key="...">` case | `<Sequence>` per case |
| `Pick` | each `PickBranch.Trigger`, `PickBranch.Action` | `<Sequence>` per slot |
| `NApplicationCard` | `Body` → `ActivityAction<...>` | `<Sequence DisplayName="Do">` |
| Any activity with `Body` typed `Activity` | body | `<Sequence>` |

For card containers copy [common-activity-card.md](../common-activity-card.md); for off-card `Pick`, `Parallel`, `ParallelForEach<T>`, and package-specific bodies, after the Rule 21 doc read run `uip rpa activities get-default-xaml --activity-class-name "<FullClassName>"` and copy its wrapped shape. See [xaml-editing-catalog.md § Example 1: Basic Activities (LogMessage, If/Else, Assign)](xaml-editing-catalog.md#example-1-basic-activities-logmessage-ifelse-assign). When editing an empty/bare slot, add the wrapper in the same edit.

### Preserve Existing Structure

Do not reformat/re-indent an entire file. Modify only the needed section with `Edit`, using exact `old_string` matches.

### Validate After Every Change

Run `uip rpa validate` after every XAML modification; do not batch edits without validation.

## Property Binding: Attributes vs Child Elements

Both forms are valid. Use attributes for simple strings, enums, booleans, and VB bracket expressions, such as:
```xml
<ui:LogMessage Message="[myVar]" Level="Info" />
```
Use child elements for complex objects (`BackupSlot`, `MailboxArgument`, `ActivityAction`, dictionaries) and output properties when attribute form fails:
```xml
<ui:SomeActivity>
  <ui:SomeActivity.Result>
    <OutArgument x:TypeArguments="x:String">[outputVar]</OutArgument>
  </ui:SomeActivity.Result>
</ui:SomeActivity>
```
Literal `[`/`]` strings, including `[k(enter)]`, `[d(ctrl)]`, and `[u(ctrl)]`, require child-element syntax. Attribute form such as `Foo="[&quot;…[k(enter)]&quot;]"` runs correctly because the runtime VB compiler reads quoted string literals correctly, but does not render in Studio because inner brackets collide with outer VB markers; see [common-pitfalls.md § NTypeInto `Text` with literal `[k(...)]` special-key tokens](common-pitfalls.md#ntypeinto-text-with-literal-k-special-key-tokens).

### Version-Sensitive Properties

If `validate` reports “Could not find member 'PropertyName'”: remove it if absent in the installed version; check same-version examples if renamed; and use `uip rpa activities get-default-xaml` for the installed version’s authoritative property set.
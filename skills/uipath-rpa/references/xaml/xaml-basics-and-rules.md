# XAML Basics and Rules

Core rules for UiPath workflow XAML: Discovery → Generate/Edit → Validate & Fix → Response.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->
**Read contract (Rule 22) — plain full Read, no prior lookup:** Read this entire file in the same assistant turn as the other T1 reads (cards, pitfalls heading list). It holds nothing else. For per-operation and per-activity catalogs (§ Common Editing Operations, § XAML Reference Examples), use [xaml-editing-catalog.md](xaml-editing-catalog.md): Grep `^###`, Read matching entries; if unsure, read the entry.

## Critical Rules — XAML (Rules 16–21a, 24, 25)

Mandatory rules for XAML authoring/editing, cited as “Rule N.” Rule 22 (read in full) and Rule 23 (`expressionLanguage`/`targetFramework` immutability) are in SKILL.md § XAML-Specific Rules; Common Rules 1–12 are also in SKILL.md.

16. **[XAML] Activity docs are authoritative:** Always check `{projectRoot}/.local/docs/packages/{PackageId}/` first.
17. **[XAML] Understand the project:** Read `project.json`, check expression language, and scan existing patterns. NEVER generate XAML blind.
18. **[XAML] Batch-author, single gate:** Author each complete workflow in one pass, sourcing every activity card → memory → Rule 21 triple (precedence: [execution-maps-guide.md](../execution-maps-guide.md)). Then per-file `validate` to clean and one project `build` (Common Rule 3 cadence; 5-attempt caps unchanged). Observable-output workflows also end with one `run` + output check ([execution-maps-guide.md § Gate ≠ runtime proof](../execution-maps-guide.md#gate--runtime-proof)). Fix failures by Rule 19; gate failure does NOT reopen `activities find`/`get-default-xaml` for card-covered activities. If >2 errors have ambiguous origin, bisect by stubbing half the new activities and re-validating.
19. **[XAML] Fix errors by category:** Package → Structure → Type → Activity Properties → Logic.
20. **[XAML] Flowchart structure and ViewState determine rendering.** First, every `FlowStep`/`FlowDecision`/`FlowSwitch` MUST be a direct `<Flowchart>` child (only direct children enter `Flowchart.Nodes`), wired through `Flowchart.StartNode`/`FlowStep.Next`/branches using `<x:Reference>`+`x:Name`. NEVER chain nested steps inside a prior `<FlowStep.Next>`; nested-only steps are absent from `Flowchart.Nodes` and render almost nothing regardless of ViewState. Then ViewState: when generating new Flowchart/StateMachine/ProcessDiagram workflows, per-node ViewState is MANDATORY — `ShapeLocation`+`ShapeSize` on every node (`ConnectorLocation` optional; Studio auto-routes). Without it Studio stacks every node at (0,0) so they overlap into what looks like a single node, and Studio does NOT auto-arrange on open. Do NOT modify ViewState on unchanged nodes. Sequence ViewState is optional. See [canvas-layout-guide.md](canvas-layout-guide.md).
21. **[XAML] Read `<Activity>.md` from `{PROJECT_DIR}/.local/docs/packages/...` before `activities get-default-xaml` for each activity not on the common-activity card.**
    - **Card-listed activities/patterns:** Use [common-activity-card.md](../common-activity-card.md) and [common-pattern-card.md](../common-pattern-card.md) as lookups: Grep `^### ` for entries and line numbers, then Read only matching planned entries (each ends at the next `###`). Read a card end-to-end only if the plan needs >5 entries. On a card hit, author from that entry alone; skip `activities find`, `activities get-default-xaml`, and the per-activity MD read. Precedence: card → agent memory ([execution-maps-guide.md § Cross-session memory](../execution-maps-guide.md#cross-session-memory)) → full triple. Memory replaces only the triple; `validate`/`build` remain required.
    - **Other activities:** (1) `activities find` → class name; (2) read `<Activity>.md` first and make a required + use-case-relevant property checklist; (3) `activities get-default-xaml` → starter; (4) diff checklist against starter and add missing properties. An empty checklist means you skipped step 2, go back.
    - **Doc lookup:** Primary `{PROJECT_DIR}/.local/docs/packages/<PackageId>/activities/<Activity>.md`; fallback `../activity-docs/<PackageId>/<closest-version>/<Activity>.md` for older versions when `.local/docs` is empty. `UiPath.UIAutomation.Activities` has no bundled fallback; `.local/docs` (available only after package installation) is its sole activity-doc source. If absent, do not search for a bundled copy; follow Rule 7a (install with consent per [uia-starter-guide.md § UIA Prerequisites](../uia-starter-guide.md), or use the Placeholder-Selector Stub Pattern in [uia-starter-guide.md](../uia-starter-guide.md)).
    - **Triggers:** If class name ends in `Trigger`, namespace contains `.Triggers`, or description mentions “starts a job” / “Monitor Events” / “Trigger Scope,” read BOTH bundled `../activity-docs/<PackageId>/<closest-version>/activities/<Activity>.md` and the package’s bundled `overview.md`. Auto-generated `.local/docs` trigger docs are sparse; bundled hand-written docs cover placement (entry-point vs. `ui:TriggerScope`), deployment context, and namespace/assembly gotchas. See Common Rule 12 (SKILL.md) and [trigger-pattern-guide.md](../trigger-pattern-guide.md).
    - **Skip-tax:** `activities get-default-xaml` omits properties at type-default values. `NGetText` starter is literally `<uix:NGetText HealingAgentBehavior="SameAsCard" />` with zero output properties; `NGetText.Value="..."` is invalid (output is `TextString`), causing `Cannot set unknown member` and blocking Object Repository linking. For `NTypeInto`, 2 of 20 properties are hidden.
    - **No self-extending the card:** The card is the only allowlist; for non-card activities the MD read is the only check. Full procedure: § Activity Property Surface and Starter XAML.
21a. **[XAML] Built-in workflow activity card fast-path allowlist:** `Sequence`, `If`, `Switch<T>`, `TryCatch`, `While`, `DoWhile`, `ForEach<T>`, `Assign`, `LogMessage`, `WriteLine`, `Delay`, `Throw`, `Rethrow`. Grep `^### ` in [common-activity-card.md](../common-activity-card.md), Read the entry, and author from it (Rule 21 lookup). Otherwise check [common-pattern-card.md](../common-pattern-card.md) similarly; patterns include text-file read/append/write, file copy, CSV, DataTable→CSV, queue publish, retry wrap, `InvokeWorkflowFile`, InvokeCode rows, HTTP→JSON. Follow full Rule 21 only if both cards miss. `Pick`, `Parallel`, and `ParallelForEach<T>` are on neither card; use full Rule 21. Studio toolbox “While” / “Do While” / “For Each” emits UiPath wrappers (`UiPath.Core.Activities.InterruptibleWhile` / `InterruptibleDoWhile` / `UiPath.Core.Activities.ForEach<T>`), not framework `System.Activities.Statements.While`/`DoWhile`/`ForEach<T>`.
24. **[XAML] Wrap every container-activity body/branch in `<Sequence>`, even if it has one activity.** Studio expects/emits this drop-zone wrapper; `validate` and `build` accept bare forms and do not catch its absence. Applies to creation and editing alike. Slots include `If.Then`/`If.Else`, `While`/`DoWhile` body, `ForEach.Body`, `TryCatch.Try`/`Catch`/`Finally`, `Switch.Default` and each case, `PickBranch.Trigger`/`Action`, `NApplicationCard.Body`. See § Container Activity Bodies — Wrap in Sequence.
25. **[XAML] Every activity element has a unique, permanent `sap2010:WorkflowViewState.IdRef`.** Breakpoints (`debug start --breakpoints 'activityIdRef=...'`), `focus-activity`, and `validate` error locations use IdRef; changing it silently breaks them.
    - **New activity:** `<TypeName>_<N>`; TypeName is the local element name without prefix, retaining generic backtick-arity (`ForEach`1`, `Catch`1`, `Switch`1`); N = highest existing N for that TypeName in the same file + 1. Never fill gaps or reuse deleted numbers. Before insertion, Grep `IdRef="<TypeName>_` in the file; in a new file start each type at `_1`.
    - **Existing activity:** NEVER change IdRef for property, `DisplayName`, expression, move, or wrapping edits. A wrapper gets a new IdRef; the inner activity keeps its. NEVER renumber after deletion.
    - **Replacement/copy:** A different-type replacement or duplicate is new and requires a new IdRef; copies never keep the source IdRef.
    - **Elements:** Root `<Activity>` → `ActivityBuilder_1`; every activity, including `Sequence`, `FlowStep`/`FlowDecision`/`FlowSwitch`, `State`, `Transition`, `Catch`1`, `AssignOperation`, `CSharpValue`1`/`CSharpReference`1`, gets one. Never put one on `Variable`, `InArgument`/`OutArgument`/`InOutArgument`, `ActivityAction`, `DelegateInArgument`, or `x:Reference`.
    - Format only `<TypeName>_<N>`; no descriptive suffix (`Assign_OutputDir` is wrong; use `DisplayName`). Root must declare `xmlns:sap2010` and include `sap2010` in `mc:Ignorable` (§ XAML File Anatomy). Card snippets and `activities get-default-xaml` output lack IdRefs; add them when inserting.

## XAML Task Navigation & Quick Reference

### Task Navigation — XAML

| Need | Read |
|---|---|
| Create XAML test case (Given-When-Then) | [testing-guide.md § XAML Test Case Structure](../testing-guide.md); register in `fileInfoCollection` (Common Rule 10) |
| Mock testing | [testing-guide.md § Mock Testing (WIP)](../testing-guide.md); requires unavailable CLI command |
| XAML test activities | [testing-guide.md § XAML Test Activities](../testing-guide.md) |
| Execution templates | [testing-guide.md § Execution Templates](../testing-guide.md) |
| Common activity (`Sequence` / `If` / `Switch<T>` / `TryCatch` / `While` / `DoWhile` / `ForEach<T>` / `Assign` / `LogMessage` / `WriteLine` / `Delay` / `Throw` / `Rethrow`) | [common-activity-card.md](../common-activity-card.md) — Rule 21a lookup |
| Common multi-activity pattern (text file read/append/write · file copy · CSV · DataTable→CSV · queue publish · retry wrap · invoke workflow · InvokeCode rows · HTTP→JSON) | [common-pattern-card.md](../common-pattern-card.md) — Rule 21a lookup alongside, not instead of, activity card |
| Create/edit Flowchart | [canvas-layout-guide.md](canvas-layout-guide.md) — § Flowchart Structure & Wiring, then § Flowchart Layout |
| Create StateMachine | § State Machine → [canvas-layout-guide.md § State Machine Layout](canvas-layout-guide.md#4-state-machine-layout) |
| Create/edit Long Running Workflow (ProcessDiagram) | [long-running-workflow-guide.md](long-running-workflow-guide.md) → [canvas-layout-guide.md](canvas-layout-guide.md) |
| Build multi-screen UIA workflow | Package XAML authoring guide § Multi-Screen Authoring (routed from core guide § Documentation, Rule 7). Default: author once after capture, then one `validate`+`build` gate (Rule 18); interleave per-screen authoring only for long captures (5+ screens). [execution-maps-guide.md § Journey: UIA capture + build](../execution-maps-guide.md#journey-uia-capture--build-xaml). |
| Data Fabric entities | [activity-docs overview](../activity-docs/UiPath.DataService.Activities/overview.md) |
| Data Fabric filters | [data-service-filter-builder-guide.md](../activity-docs/UiPath.DataService.Activities/guides/data-service-filter-builder-guide.md) → [QueryEntityRecords](../activity-docs/UiPath.DataService.Activities/activities/QueryEntityRecords.md) |
| IS connector (XAML) | [is-connector-xaml-guide.md](../is-connector-xaml-guide.md) — connector discovery + connection lifecycle |
| Event-triggered workflow (O365 / Gmail / Salesforce / Jira / Slack / ServiceNow / time / queue / file watcher / UI click) | [trigger-pattern-guide.md](../trigger-pattern-guide.md) → `activity-docs/{PackageId}/{closest}/activities/<TriggerActivity>.md` |
| Read/edit existing `ui:TriggerScope` | [trigger-pattern-guide.md § Reading and Editing Existing TriggerScope XAML](../trigger-pattern-guide.md) |
| Troubleshoot XAML | [common-pitfalls.md](common-pitfalls.md) (Rule 22 lookup) → [cli-reference.md § Validation Iteration Loop](../cli-reference.md#validation-iteration-loop) |

### Expression Language

Check `expressionLanguage` in `project.json`: VB.NET uses `[brackets]`; C# uses `CSharpValue<T>` / `CSharpReference<T>`—canonical per-property forms: [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md). New XAML projects default to VB.NET.

### Key CLI Commands

| Command | Purpose |
|---|---|
| `activities find --query "<keyword>"` | Discover by keyword |
| `activities get-default-xaml --activity-class-name "<class>"` | Get starter |
| `analyzer-rules list --project-dir "<dir>"` | List enabled Workflow Analyzer rules on demand only (user asks about project rules or repeated violations of one rule family); `validate`/`build` enforce rules without it |
| `validate --file-path "<file>"` | Per-file deep validation: structure, references, analyzer rules, unknown members, invalid enums, expression compilation |
| `build "<PROJECT_DIR>"` | Whole-project compile + packaging gate for every workflow, including files not passed to `validate` ([cli-reference.md § What each phase covers](../cli-reference.md#what-each-phase-covers)); run after clean `validate` |

### Common Activities

| Activity | Package | Purpose |
|---|---|---|
| UI automation (Use Application/Browser, Click, Type Into, Get Text, Select Item, …) | `UiPath.UIAutomation.Activities` | **Never author from memory or this row.** Targets/selectors are captured, not hand-written. Read `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` in full first (Rule 7). |
| If | built-in | Conditional branching |
| Assign | built-in | Set variable/argument values |
| For Each | built-in | Iterate a collection |
| Invoke Workflow File | built-in | Call another workflow file |
| Create Entity Record | `UiPath.DataService.Activities` | Create a Data Fabric entity record |
| Query Entity Records | `UiPath.DataService.Activities` | Query Data Fabric records with filters; [filter builder guide](../activity-docs/UiPath.DataService.Activities/guides/data-service-filter-builder-guide.md) |

### Related XAML References

- [xaml-editing-catalog.md](xaml-editing-catalog.md) — per-entry catalog for arguments/variables/imports/assembly references, C#/VB expressions, resource types, complete workflows (Rule 22 lookup: Grep `^###`, Read matching entries)
- [common-pitfalls.md](common-pitfalls.md) — activity gotchas, scope requirements, property conflicts (Rule 22 lookup)
- [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md) — canonical C# bindings per common activity property and § C# Expression Pitfalls
- [canvas-layout-guide.md](canvas-layout-guide.md) — Flowchart vocabulary, wiring, forbidden nested chains; Flowchart/State Machine/LRW layout and ViewState
- [long-running-workflow-guide.md](long-running-workflow-guide.md) — LRW dependency, nodes, gateways, suspend/resume persistence
- [jit-custom-types-schema.md](jit-custom-types-schema.md) — JIT custom type discovery
- [../reframework-guide.md](../reframework-guide.md) — REFramework modes, SetTransactionStatus queue-guard fix, Config.xlsx leftover trap
- [../data-manipulation-guide.md](../data-manipulation-guide.md) — DataTable LINQ, strings, RegEx, DateTime, conversion, collections, JSON; VB + C# forms
- [../error-handling-guide.md](../error-handling-guide.md) — exception taxonomy, Try/Catch, Retry Scope, Global Exception Handler, transaction boundaries, retry ownership
- [../library-authoring-guide.md](../library-authoring-guide.md) — reusable library contract, layout sidecar, error contract, SemVer, pack & publish

## Authoring Workflow

Discovery-first: understand before acting, start simple, validate continuously.

**Core principles:**

1. **Activity Docs Are the Source of Truth** — installed packages ship structured documentation at `{projectRoot}/.local/docs/packages/{PackageId}/` with source-accurate properties, types, defaults, enum values, conditional property groups, and working XAML examples. Always check for them first.
2. **Know Before You Write** — **NEVER** generate XAML blind. Understand the project structure, packages, expression language, and existing patterns.
3. **Use What You Know, Skip What You Don't Need** — if you already know the package ID and activity class name, go directly to its doc file. The discovery steps are a priority ladder, not a mandatory checklist.
4. **Batch-Author, Single Gate, Fix by Category** — one workflow at a time; author each workflow complete in one pass (SKILL.md Rule 18; source activities card → memory → discovery triple), then per-file `validate` to clean and exit only on a clean project-level `build` (§ Phase 3). Fix order: Package → Structure → Type → Activity Properties → Logic.

**Classify the request:**

| Type | Trigger words | Action |
|---|---|---|
| CREATE | “generate”, “create”, “make”, “build”, “new” | Discovery → Generate |
| EDIT | “update”, “change”, “fix”, “modify”, “add to” | Discovery → Edit |

If target file is unclear, ask the user; do not guess.

### Phase 1: Discovery

Understand project context, docs, patterns, reusable components, and activities before writing. For multiple activities, batch all `activities find` calls in parallel, then all `<Activity>.md` Reads in parallel, then all `get-default-xaml` calls in parallel (SKILL.md § Execution Maps). Batch authoring too: one complete `Write` per workflow (Rule 18), then Phase 3 gate.

#### Step 1.1: Project Structure

```text
Glob: pattern="**/*.xaml" path="{projectRoot}"       → list workflow files
Read: file_path="{projectRoot}/project.json"          → project definition
```

Analyze workflow locations/folder conventions, naming, similar workflows, VB or C# (`expressionLanguage`), installed packages, and reusable connections/credentials/objects.

#### Step 1.2: Discover Activity Documentation (Primary Source)

Read `<Activity>.md` before `activities get-default-xaml`, every time, even for simple activities; it defines the property surface. See [§ Activity Property Surface and Starter XAML](#activity-property-surface-and-starter-xaml) for procedure and skip-tax. Docs are generally available only for installed, newer package versions. Install missing packages; if docs are missing, update to latest or use `skills/uipath-rpa/references/activity-docs/<PackageId>/<closest-version>/`.

```text
{projectRoot}/.local/docs/packages/{PackageId}/
  overview.md
  activities/{ActivitySimpleClassName}.md
  coded/    # Ignore for XAML workflows
```

Activity docs contain Header → Metadata → Properties (Input, Output, Conditional groups, Common) → Valid Configurations → Enum Reference → XAML Examples → Notes.

| Situation | Action |
|---|---|
| Know package + activity | Read `{projectRoot}/.local/docs/packages/{PackageId}/activities/{ActivityName}.md` |
| Know package only | Read `overview.md`, then identified activity doc |
| Don’t know package | Bash `ls {projectRoot}/.local/docs/packages/`, then `ls` candidate `activities/` and Read by path. NOT `Glob`/`Grep`: they skip gitignored `.local/`, so a miss proves nothing. |
| Docs exist, activity undocumented | Use other docs structurally; fall back to `activities get-default-xaml` |
| No package docs | Update package first (often adds docs); avoid major jumps (e.g., 23.x → 26.x) that may deprecate activities; prefer minor/patch. If still missing, use Steps 1.4–1.7. |
| Package absent | Install first; docs and `activities get-default-xaml` require it |
| No `.local/docs/` | Start fallback flow at Step 1.3 |

#### Step 1.3: Search Current Project

Search reusable patterns/conventions:

```text
Glob: pattern="**/*pattern*.xaml" path="{projectRoot}"
Grep: pattern="ActivityName|pattern" path="{projectRoot}"
Read: file_path="{projectRoot}/ExistingWorkflow.xaml"
```

Prioritize local patterns in mature projects; skip in greenfield projects.

#### Step 1.4: Discover Activities (When Needed)

Find activities for user-described actions:

```bash
uip rpa activities find --query "send mail" --limit 10 --output json
```

Results are global, not limited to installed packages; install a useful activity’s package immediately. Tags can narrow results.

#### Step 1.5: Disambiguate Approach and Provider

**Approach (API vs UI Automation vs Connector):** auto-select if user stated it or only one is viable; otherwise prompt if multiple are viable and no preference was given. Do NOT install packages before approach confirmation.

**Provider:** auto-select if user specified one, only one package matches, project has the package or matching connection, or workflow already uses its activities. Prompt only as last resort, recommending top 2–4 choices.

#### Step 1.6: Resolve Activity Properties (Fallback)

Use `uip rpa activities get-default-xaml` when docs are insufficient:

```bash
# Non-dynamic activity:
uip rpa activities get-default-xaml --activity-class-name "<FULLY_QUALIFIED_CLASS>" --output json
# Dynamic activity (connector-backed):
uip rpa activities get-default-xaml --activity-type-id "<TYPE_ID>" --connection-id "<CONN_ID>" --output json
```

For JIT custom types, Read `{projectRoot}/.project/JitCustomTypesSchema.json`; see [jit-custom-types-schema.md](jit-custom-types-schema.md).

#### Step 1.7: Search Examples Repository

Use if docs, `activities find`, and `activities get-default-xaml` lack context:

```bash
uip rpa workflow-examples list --tags web --limit 10 --output json
uip rpa workflow-examples get --key "<BLOB_PATH>"
```

Tags: `adobe-sign`, `asana`, `box`, `concur`, `confluence`, `database`, `document-understanding`, `docusign`, `dropbox`, `email-generic`, `excel`, `excel-online`, `freshbooks`, `freshdesk`, `github`, `gmail`, `google-calendar`, `google-docs`, `google-drive`, `google-sheets`, `gsuite`, `hubspot`, `intacct`, `jira`, `mailchimp`, `marketo`, `microsoft-365`, `onedrive`, `outlook`, `outlook-calendar`, `pdf`, `powerpoint`, `productivity`, `quickbooks`, `salesforce`, `servicenow`, `sharepoint`, `shopify`, `slack`, `smartsheet`, `stripe`, `teams`, `testing`, `trello`, `web`, `webex`, `word`, `workday`, `zendesk`, `zoom`.

#### Step 1.8: Get Current Context (As Needed)

```text
Read: file_path="{projectRoot}/project.json"
Glob: pattern="**/*" path="{projectRoot}/.objects/"
Bash: uip is connections list --output json
```

#### Step 1.9: Discover Connector Capabilities (For IS/Connector Workflows)

For end-to-end `ConnectorActivity` XAML (connection + type ID + Configuration blob + FieldObjects) and discovery commands, use [../is-connector-xaml-guide.md](../is-connector-xaml-guide.md), which includes a worked example.

| Path | Use |
|---|---|
| IS generic `ConnectorActivity` with typed operation typeId (e.g. `37a305b2-...` for Slack “Send Message to Channel”) | **Default:** schema-driven, hand-authorable via guide CLI flow; `UiPath.IntegrationService.Activities`. |
| IS generic `ConnectorActivity` with `ConnectorHttpActivity` typeId (e.g. `...httpRequest...`) | Fallback for unmodeled endpoints. Field names are connector-defined, not `method`/`path`/`body`; read schema. |
| Per-product BAF package (`UiPath.Slack.Activities`, `UiPath.Salesforce.Activities`, etc.) | Avoid for headless authoring: complex BAF shape (`ScopeActivity` + dynamic child with `BusinessEntity`, `SelectedFields`, `PopulatedAPIParameters`). Default to generic `ConnectorActivity` unless project already uses BAF. |

### Phase 2: Generate or Edit

**UI Automation — Target Configuration Gate (MANDATORY):** Before writing any UI activity XAML, `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` MUST be read IN FULL first (SKILL.md Rule 7). Every UI element target MUST be configured through `uia-configure-target`; its guide requires reading the target-capture orchestration reference IN FULL first. NEVER manually call low-level `uip rpa uia` CLI commands outside the skill flow.

**CREATE:** Do not Read scaffolded `Main.xaml`; `Write` replaces it wholesale. Create needed data files (`mkdir` + sample inputs) in the same assistant message as that `Write`. Write each workflow complete in one pass (Rule 18; source every activity card → memory → discovery triple). Use `Write` per [§ XAML File Anatomy](#xaml-file-anatomy); infer path from folder conventions and use descriptive filenames. Then gate in Phase 3.

**EDIT:** Read current content first; use `Edit` with exact, unique `old_string` matches.

### Phase 3: Validate & Fix Loop

**MUST** repeat until both `validate` and `build` report 0 errors, or 5 fix attempts per loop; after 5, stop and present remaining errors. Before the first fix iteration, read [../cli-reference.md § Validation Iteration Loop](../cli-reference.md#validation-iteration-loop) for the canonical per-file `validate` → project `build` loop, phase coverage, and smoke test.

Run the whole gate in one Bash call, chaining with `&&` so failed `validate` stops before `build` and the pass path takes one turn ([execution-maps-guide.md](../execution-maps-guide.md) journey map gate row):

```bash
uip rpa validate --file-path "Workflows/MyWorkflow.xaml" --project-dir "<PROJECT_DIR>" --output json \
  && uip rpa build "<PROJECT_DIR>" --log-level Warn --output json
```

`--file-path` is **relative to the project directory**. Clean `validate` is only half-done; exit only after clean `build`. For observable-output workflows, a clean gate is not runtime proof: finish with one `uip rpa run --skip-build` and check outputs ([execution-maps-guide.md § Gate ≠ runtime proof](../execution-maps-guide.md#gate--runtime-proof)).

Fix in order: **Package → Structure → Type → Activity Properties → Logic**.
1. **Package:** install/update; docs become available after installation.
2. **Structure:** fix XML against [§ XAML File Anatomy](#xaml-file-anatomy) and [§ XAML Safety Rules](#xaml-safety-rules).
3. **Type:** check activity doc types/enums; JIT types: [jit-custom-types-schema.md](jit-custom-types-schema.md).
4. **Activity Properties:** check doc properties, conditional groups, valid configurations; fallback to `activities get-default-xaml`; watch OverloadGroup conflicts.
5. **Logic:** match expression syntax to project language. For UI automation, use `debug start` and [../uia-starter-guide.md § Running UI Automation Workflows](../uia-starter-guide.md).

When stuck, defer minor configuration details to the user. Consider InvokeCode only as a last resort for an unresolved activity.

### Phase 4: Response

Report workflow path, brief description, key activities/logic, installed packages, limitations/notes, suggested next steps (testing, parameterization), and encourage review/customization (fill placeholders, set up connections).

### Anti-Patterns

- NEVER design sprawling monoliths; split logic into invoked files ([../environment-setup.md § Designing for Reuse](../environment-setup.md#designing-for-reuse)). One complete workflow per batch (Rule 18) is not monolith design.
- NEVER handcraft UI selectors outside `uia-configure-target`.
- NEVER guess properties, types, or configurations without docs.
- NEVER use `uip rpa workflow-examples get` keys not returned by list.
- NEVER ask the user to choose a provider before checking project signals.
- NEVER loop-retry failing CLI commands without diagnosing root cause.
- NEVER use connector activities without checking connection existence.
- NEVER ignore conditional property groups; OverloadGroup conflicts cause validation errors.
- NEVER generate full XAML without a sourced starter per activity: card/pattern-card entry, validated memory snippet, or `activities get-default-xaml` (SKILL.md Rule 21 precedence).
- NEVER assume create/edit succeeded: run `uip rpa validate` AND `uip rpa build` after every mutation.
- NEVER treat “no diagnostics found” from `validate` as final; `build` catches more errors and must follow.
- NEVER skip environment readiness; check the project opens and restores cleanly ([environment-setup.md](../environment-setup.md)).

## XAML File Anatomy

Every UiPath XAML workflow uses this structure. **`x:Class`** equals the file’s project-root-relative path without `.xaml`, with folder separators replaced by underscores, not dots: `MyWorkflow.xaml` → `MyWorkflow`; `Workflows/SendEmail.xaml` → `Workflows_SendEmail`. Dots (e.g. `Workflows.SendEmail`) cause *“Invalid ActivityBuilder name … Suggested name …”*.

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
    <sco:Collection x:TypeArguments="x:String"
      xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib">
      <x:String>System</x:String>
      <x:String>System.Collections.Generic</x:String>
      <x:String>System.Linq</x:String>
      <!-- More namespace imports -->
    </sco:Collection>
  </TextExpression.NamespacesForImplementation>

  <!-- TextExpression.ReferencesForImplementation (assembly references) -->
  <TextExpression.ReferencesForImplementation>
    <sco:Collection x:TypeArguments="AssemblyReference"
      xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib">
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

  <!-- Main workflow body -->
  <Sequence DisplayName="Main Sequence" sap2010:WorkflowViewState.IdRef="Sequence_1">
    <Sequence.Variables>
      <Variable x:TypeArguments="x:String" Name="tempVar" Default="hello" />
    </Sequence.Variables>
    <!-- Activities go here, each with its own IdRef (Rule 25) -->
  </Sequence>
</Activity>
```

Older files may end with `<sap2010:WorkflowViewState.ViewStateManager>` metadata keyed by IdRef. Never add it to a new file or edit an existing one (§ ViewState Rules).

## Workflow Types

### Sequence

Linear top-to-bottom execution; use for straightforward processes.

### Flowchart

Use for branching logic. All FlowStep/FlowDecision/FlowSwitch nodes are direct `<Flowchart>` children and use `<x:Reference>` in property elements (`Flowchart.StartNode`, `FlowStep.Next`, `FlowDecision.True/False`). NEVER nest a FlowStep in another’s `<FlowStep.Next>`; nested-only steps are absent from `Flowchart.Nodes` and will not render. See [canvas-layout-guide.md § Flowchart Structure & Wiring](canvas-layout-guide.md#flowchart-structure--wiring) and [§ Flowchart Layout](canvas-layout-guide.md#3-flowchart-layout) for vocabulary, registration, expressions, and layout.

### State Machine

State-based workflows suit long-running processes with distinct states (e.g., REFramework).

```xml
<StateMachine InitialState="{x:Reference __ReferenceID0}" DisplayName="My State Machine" sap2010:WorkflowViewState.IdRef="StateMachine_1">
  <State x:Name="__ReferenceID0" DisplayName="Initial State">
    <State.Entry><Sequence DisplayName="Initialize" /></State.Entry>
    <State.Transitions><Transition DisplayName="To Processing"><Transition.Condition>[condition]</Transition.Condition><Transition.To><x:Reference>__ReferenceID1</x:Reference></Transition.To></Transition></State.Transitions>
  </State>
  <State x:Name="__ReferenceID1" DisplayName="Processing" />
  <State x:Name="__ReferenceID2" DisplayName="End" IsFinal="True" />
</StateMachine>
```

`InitialState` references the starting State; States are direct `<StateMachine>` children (no wrapper); `IsFinal="True"` marks the terminal state; transitions use `<Transition.To><x:Reference>__ReferenceID</x:Reference></Transition.To>`. ViewState is required for usable layout; see [canvas-layout-guide.md § State Machine Layout](canvas-layout-guide.md#4-state-machine-layout) for coordinates, connection points, and recipes.

### Long Running Workflow (ProcessDiagram)

BPMN-style horizontal, event-driven workflows use `upa:ProcessDiagram` with `EventNode`, `TaskNode`, `DecisionNode`, and `EndNode`:

```xml
xmlns:upa="clr-namespace:UiPath.Process.Activities;assembly=UiPath.Process.Activities"
xmlns:upas="clr-namespace:UiPath.Process.Activities.Shared;assembly=UiPath.Process.Activities"
```

These types ship in `UiPath.FlowchartBuilder.Activities` (runtime assembly `UiPath.Process.Activities`); install it before authoring (Common Rule 6). Unsupported on `targetFramework: "Legacy"`. See [long-running-workflow-guide.md](long-running-workflow-guide.md) for dependency, nodes, gateways, and suspend/resume.

Flows left-to-right: `EventNode` = start/end circles, `TaskNode` = activity rectangles, `DecisionNode` = True/False diamond, `EndNode` = end circle. `BoundaryNode` attaches to `TaskNode.BoundaryNodes` for error handling. Follow Flowchart `<x:Reference>` registration rules, including trailing registration for inline nodes. Gateway nodes (`SplitNode`/`MergeNode`/`SwitchNode<T>`), subprocesses, intermediate events, and persistence-based waits are covered by [long-running-workflow-guide.md](long-running-workflow-guide.md). ViewState is required; see [canvas-layout-guide.md § Long Running Workflow](canvas-layout-guide.md#5-long-running-workflow-processdiagram-layout) for horizontal layouts.

## XAML Safety Rules

### ViewState Rules

ViewState controls designer appearance. Sequences need no ViewState; Studio manages `IsExpanded`. Flowcharts, State Machines, and Long Running Workflows require canvas positions; without them Studio stacks nodes at (0,0), appearing as one node, and does NOT auto-arrange on open.

When editing, do NOT modify global `<sap2010:WorkflowViewState.ViewStateManager>`, unchanged-node ViewState, or existing IdRefs. New activities get the next number for their type (Rule 25). Read existing Flowchart/StateMachine positions before adding nodes to avoid overlap. When generating Flowchart/StateMachine/ProcessDiagram, set `ShapeLocation`+`ShapeSize` for every node; `ConnectorLocation` is optional because Studio auto-routes. See [canvas-layout-guide.md](canvas-layout-guide.md) for coordinates, standard sizes, and recipes.

### Preserve xmlns Declarations

Never remove existing root `<Activity>` `xmlns` declarations; add only as needed. Removing one referenced in the file causes validation errors.

### Respect Expression Language

Always check project expression language. **CSharp:** use C# (`+` string concatenation, `==` equality), `<CSharpValue>` for inputs and `<CSharpReference>` for outputs, without namespace prefix. Do NOT use `[bracket]` shorthand; it creates `VisualBasicValue` nodes and “multiple languages” validation errors. **VB:** use VB (`&` concatenation, `=` equality) and `[bracket]` shorthand. Mixing languages causes build failures.

### Activity Property Surface and Starter XAML

Never construct activity XAML from memory. Sources: (1) `<Activity>.md`, authoritative for properties, types, defaults, descriptions, required scopes; (2) `uip rpa activities get-default-xaml --activity-class-name "<FullClassName>"`, starter with namespaces, assembly references, and non-default properties.

**Doc locations:** primary `{PROJECT_DIR}/.local/docs/packages/<PackageId>/activities/<Activity>.md` (Read exact path; failed Read is the existence check. `Glob`/`Grep` skip gitignored `.local/`, so misses prove nothing); fallback `../activity-docs/<PackageId>/<closest-version>/<Activity>.md` (closest installed version); routing: [§ Step 1.2](#step-12-discover-activity-documentation-primary-source). If neither exists, document that the package is third-party/unusual, use `activities find` + `activities get-default-xaml` alone, and warn the user the property surface may be incomplete.

> **Skip-tax:** `activities get-default-xaml` omits type-default values (`null`, `0`, `false`, unset). `NTypeInto` hides 2 of 20 properties; `NClick` ~3 of ~15. `NGetText` hides every output property; its starter is `<uix:NGetText HealingAgentBehavior="SameAsCard" />`. `NGetText.Value="..."` is invalid and causes `Cannot set unknown member 'UiPath.UIAutomationNext.Activities.NGetText.Value'`, breaking deserialization of the activity tree and Object Repository linking. For new Get Text, bind output to `TextString` (`OutArgument<string>`), the current designer member. `NGetText` also has legacy non-generic `Text` (`OutArgument`); it writes scraped text to both at runtime, and the designer hides whichever the installed version does not use. Existing/older `Text="..."` is valid; do not flag or “correct” it. Only `Value` is unknown. The MD reveals the actual surface (`TextString`, `ClickType`, `KeyModifiers`, `WaitForReady`, `EmptyFieldMode`, etc.).

**Per-activity procedure (each step depends on the previous):**
1. Run `uip rpa activities find --query "<keyword>" --output json` → fully qualified class name, type ID, `isDynamicActivity`.
2. Locate `<Activity>.md` (primary then fallback) and checklist required and use-case-relevant optional properties. If absent from both, record this and flag output; if you cannot name required properties from the doc, you read the wrong file.
3. Run `uip rpa activities get-default-xaml` → starter with namespaces/assembly references.
4. Diff checklist against starter and add missing properties. An empty checklist without a third-party flag means step 2 was skipped; return to it. Never author from starter alone.
5. Validate with `uip rpa validate`.

This applies to every activity not on [common-activity-card.md](../common-activity-card.md): check card first; a card hit means author from the entry and skip find, starter, and per-activity MD. Do not self-extend the card (“simple” `StartProcess`, `InvokeWorkflowFile`, etc.). Card surface is centrally curated and version-anchored; for all others, the procedure is the only check.

**Anti-pattern:** treating starter output as the complete property surface; serialization omits type-default values by design. Use `uip rpa workflow-examples list` and `uip rpa workflow-examples get` as well as local `.xaml` examples.

**Property-name drift:** On `validate` error `Cannot set unknown member '<Class>.<Prop>'`, check `<Activity>.md`; names vary by installed version (e.g. UIA `26.4.1-preview` renamed `InputMode` → `InteractionMode`, `EmptyField` → `EmptyFieldMode`).

### Container Activity Bodies — Wrap in Sequence

Container slots typed `Activity` or `ActivityAction<T>` require Studio’s `<Sequence>` drop-zone wrapper, even for one activity; Studio emits this form.

| Activity | Slot(s) | Wrapper |
|---|---|---|
| `If` | `If.Then`, `If.Else` | `<Sequence DisplayName="Then">` / `<Sequence DisplayName="Else">` |
| `While`, `DoWhile` | direct activity child | `<Sequence DisplayName="Body">` |
| `ForEach<T>` | `ForEach.Body` → `ActivityAction<T>` | `<Sequence DisplayName="Body">` |
| `TryCatch` | `TryCatch.Try` | `<Sequence DisplayName="Try">` |
| `TryCatch` | each `Catch` → `ActivityAction<T>` | `<Sequence DisplayName="Catch">` |
| `TryCatch` | `TryCatch.Finally` | `<Sequence DisplayName="Finally">` |
| `Switch<T>` | `Switch.Default`, each `<x:String x:Key="...">` case | `<Sequence>` per case |
| `Pick` | each `PickBranch.Trigger`, `PickBranch.Action` | `<Sequence>` per slot |
| `NApplicationCard` | `Body` → `ActivityAction<...>` | `<Sequence DisplayName="Do">` |
| Any activity with `Body` typed `Activity` | body slot | `<Sequence>` |

`validate` and `build` accept bare single activities in body slots (e.g. `<If.Then><Throw /></If.Then>`); missing wrappers are Studio ergonomics/canonical-emission issues, not static-analysis errors. For card containers (`If`, `Switch<T>`, `TryCatch`, `While`, `DoWhile`, `ForEach<T>`), copy wrapper from the card. For off-card (`Pick`, `Parallel`, `ParallelForEach<T>`, package-specific body activities), after Rule 21 doc read, run `uip rpa activities get-default-xaml --activity-class-name "<FullClassName>"` and copy its wrapper. See SKILL.md Rules 21, 21a, 24 and [xaml-editing-catalog.md § Example 1: Basic Activities (LogMessage, If/Else, Assign)](xaml-editing-catalog.md#example-1-basic-activities-logmessage-ifelse-assign). When editing, add wrapper in the same edit when inserting into an empty or bare `If.Then` / `Catch` / `Body` slot.

### Preserve Existing Structure

When editing, do not reformat/re-indent the whole file; modify only the needed section using `Edit` with exact `old_string` matches.

### Validate After Every Change

Run `uip rpa validate` after every XAML modification. Do not batch multiple edits without validation; catch errors early.

## Property Binding: Attributes vs Child Elements

Properties may be XML attributes or child elements; some work reliably only in one form.

**Attributes:** simple strings, enums, booleans, and VB bracket expressions usually work inline (e.g. `DisplayName="My Activity" Message="[variable]" Level="Info"`).

**Child elements:** output properties (`OutArgument`, `Result`) may require property-element syntax. Some activities accept `Result="[var]"` as an attribute; others only work with the expanded child element form. If attribute binding fails validation, try the expanded child form:

```xml
<ui:SomeActivity>
  <ui:SomeActivity.Result><OutArgument x:TypeArguments="x:String">[outputVar]</OutArgument></ui:SomeActivity.Result>
</ui:SomeActivity>
```

Complex objects (`BackupSlot`, `MailboxArgument`, `ActivityAction`, dictionaries) always require child elements. Strings containing literal `[` or `]` (e.g. UIA `[k(enter)]`, `[d(ctrl)]`, `[u(ctrl)]`) also require child-element syntax: attribute form `Foo="[&quot;…[k(enter)]&quot;]"` runs correctly because the runtime VB compiler reads quoted string literals correctly, but brackets collide with outer VB expression markers and the value will not render in Studio. See [common-pitfalls.md § NTypeInto `Text` with literal `[k(...)]` special-key tokens](common-pitfalls.md#ntypeinto-text-with-literal-k-special-key-tokens).

### Version-Sensitive Properties

For `validate` error “Could not find member 'PropertyName'”: (1) remove it if absent from installed version; (2) check same-version examples for renames; (3) use `uip rpa activities get-default-xaml` output as the installed-version authoritative property set.
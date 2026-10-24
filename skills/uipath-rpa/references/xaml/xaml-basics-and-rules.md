# XAML Basics and Rules

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->

**Read contract (Rule 22):** read this file in full, with no prior lookup, in the same assistant turn as the other T1 reads (cards and pitfalls heading list). For per-operation/activity catalogs (§ Common Editing Operations, § XAML Reference Examples), Grep `^###` in [xaml-editing-catalog.md](xaml-editing-catalog.md) and Read only matching entries.

## Critical Rules — XAML (Rules 16–21a, 24, 25)

Mandatory for all XAML work; cited as "Rule N" across this skill (Rules 22–23 and Common Rules 1–12: SKILL.md).

16. **[XAML] Activity docs are the source of truth:** always check `{projectRoot}/.local/docs/packages/{PackageId}/` first.
17. **[XAML] MUST understand project structure:** read `project.json`, check expression language, and scan existing patterns; NEVER generate XAML blind.
18. **[XAML] Batch-author, single gate:** author each complete workflow in one pass, every activity sourced card → memory → Rule 21 triple; per-file `validate` to clean, then one project `build` (Common Rule 3; 5-attempt caps); observable outputs end with one `run` + output check ([§ Gate ≠ runtime proof](../execution-maps-guide.md#gate--runtime-proof)). Fix by Rule 19 category; a gate failure never reopens discovery for card activities. >2 errors of ambiguous origin: stub out half the new activities and re-validate.
19. **[XAML] Fix errors in order:** Package → Structure → Type → Activity Properties → Logic.
20. **[XAML] Flowchart structure and ViewState both control rendering:** `FlowStep`/`FlowDecision`/`FlowSwitch` are direct `<Flowchart>` children (only those enter `Flowchart.Nodes`), wired by `StartNode`/`Next`/branches + `<x:Reference>`/`x:Name`, NEVER nested in the preceding `<FlowStep.Next>`. New canvas nodes need `ShapeLocation`+`ShapeSize` (`ConnectorLocation` optional) or stack at (0,0) ([canvas-layout-guide.md](canvas-layout-guide.md)). Leave unchanged nodes' ViewState alone; Sequence needs none.
21. **[XAML] Read `<Activity>.md` before `activities get-default-xaml` for every activity not on the common-activity card.**
    - **Card activities/patterns (Rule 21a):** Grep `^### ` in [common-activity-card.md](../common-activity-card.md) and [common-pattern-card.md](../common-pattern-card.md), Read only matching entries (whole card only for >5). On a hit, author from that entry alone: skip `activities find`, `activities get-default-xaml`, and the per-activity MD. Agent memory ([§ Cross-session memory](../execution-maps-guide.md#cross-session-memory)) substitutes only for the triple; the gate still applies.
    - **Other activities — the triple (batched, Phase 1):** (1) `uip rpa activities find --query "<keyword>" --output json`; (2) read `<Activity>.md`, write a checklist of required + use-case-relevant properties; (3) `activities get-default-xaml`; (4) add checklist properties missing from the starter. An empty checklist means you skipped step 2.
    - **Doc order:** `{PROJECT_DIR}/.local/docs/packages/<PackageId>/activities/<Activity>.md`, else `../activity-docs/<PackageId>/<closest-version>/<Activity>.md`. UIA has no bundled fallback: Rule 7a ([uia-starter-guide.md § UIA Prerequisites](../uia-starter-guide.md)) or its Placeholder-Selector Stub Pattern.
    - **Triggers** (class ends in `Trigger`, namespace `.Triggers`, or “starts a job”/“Monitor Events”/“Trigger Scope”): also read the bundled `../activity-docs/` `<Activity>.md` **and** `overview.md`; Common Rule 12, [trigger-pattern-guide.md](../trigger-pattern-guide.md).
    - The card is the only allowlist; never add activities to it by personal judgment. Skip-tax: § Activity Property Surface and Starter XAML.
21a. **[XAML] Built-in workflow activities use the card only for this allowlist:** `Sequence`, `If`, `TryCatch`, `While`, `ForEach<T>`, `Assign`, `LogMessage`, `WriteLine`, `Throw`, `Rethrow`. For these, author from the [common-activity-card.md](../common-activity-card.md) entry (Rule 21 lookup). Otherwise check [common-pattern-card.md](../common-pattern-card.md) likewise; its patterns are exactly: text-file read/append/write, guarded file copy, DataTable generate→filter→CSV text, retry wrap, `InvokeWorkflowFile` with arguments, InvokeCode bulk rows, HTTP→JSON. Full Rule 21 when both cards miss — including `Switch<T>`, `DoWhile`, `MultipleAssign`, `Delay`, `Pick`, `Parallel`, `ParallelForEach<T>`, queue publish (`AddQueueItem`), and CSV files. Studio's While/Do While/For Each are `UiPath.Core.Activities.InterruptibleWhile`/`InterruptibleDoWhile`/`ForEach<T>`, not `System.Activities.Statements.While`/`DoWhile`/`ForEach<T>`.
24. **[XAML] Wrap every container body/branch in `<Sequence>`, including a single activity** (slots: § Container Activity Bodies — Wrap in Sequence), creating or editing. Studio expects the drop zone; `validate`/`build` accept the bare form, so neither catches a missing wrapper.
25. **[XAML] Every activity element has a unique permanent `sap2010:WorkflowViewState.IdRef`** — breakpoints (`debug start --breakpoints 'activityIdRef=...'`), `focus-activity`, and `validate` locations use it.
    - New: `<TypeName>_<N>` only (no suffixes like `Assign_OutputDir`); local name without prefix, keeping backtick-arity (`ForEach`1`, `Catch`1`); `<N>` = highest existing N for that type + 1 (Grep `IdRef="<TypeName>_`; never fill gaps or reuse); new files start at `_1`.
    - Existing: NEVER change an IdRef (any edit, move, or wrap) or renumber after a delete; a wrapper, type replacement, or copy gets a new one.
    - Apply to root `<Activity>` (`ActivityBuilder_1`) and every activity incl. `Sequence`, `FlowStep`, `State`, `Transition`, `Catch`1`, `AssignOperation`, `CSharpValue`1`/`CSharpReference`1`; not to `Variable`, arguments, `ActivityAction`, `DelegateInArgument`, `x:Reference`. Root lists `sap2010` in `mc:Ignorable`. Cards and starters lack IdRefs: add them.

### Task Navigation — XAML

- XAML test cases → [testing-guide.md](../testing-guide.md); register in `fileInfoCollection` (Common Rule 10).
- Flowchart / StateMachine / LRW → [canvas-layout-guide.md](canvas-layout-guide.md); LRW: [long-running-workflow-guide.md](long-running-workflow-guide.md) first.
- Multi-screen UIA → package guide § Multi-Screen Authoring, [§ Journey: UIA capture + build](../execution-maps-guide.md#journey-uia-capture--build-xaml).
- Data Fabric → [overview](../activity-docs/UiPath.DataService.Activities/overview.md), [filter builder guide](../activity-docs/UiPath.DataService.Activities/guides/data-service-filter-builder-guide.md) → [QueryEntityRecords](../activity-docs/UiPath.DataService.Activities/activities/QueryEntityRecords.md). IS connector → [is-connector-xaml-guide.md](../is-connector-xaml-guide.md). Triggers / `ui:TriggerScope` → [trigger-pattern-guide.md](../trigger-pattern-guide.md).
- Troubleshooting → [common-pitfalls.md](common-pitfalls.md) (Rule 22 lookup), then Phase 3. `analyzer-rules list`: on demand only (SKILL.md Common Rule 3).

## Authoring Workflow

Discovery → Generate (CREATE) or Edit (EDIT); unclear target file → ask; known package and class → straight to the doc.

### Phase 1: Discovery

Batch across activities, never one triple at a time: all `activities find` calls in parallel, then all `<Activity>.md` Reads, then all `get-default-xaml` calls; one complete workflow per `Write`, then gate.

#### Step 1.1–1.3: Project, Docs, Existing Patterns

Read `project.json`; Grep existing `.xaml` for conventions. `.local/docs/packages/{PackageId}/` (ignore `coded/`) exists only for installed packages; prefer minor/patch over major upgrades (23.x → 26.x may deprecate activities). Routing: package + activity known → `activities/{ActivityName}.md`; package only → `overview.md`, then the activity doc; unknown package → Bash `ls {projectRoot}/.local/docs/packages/`, then candidate `activities/` (`Glob`/`Grep` skip gitignored `.local/`); activity undocumented → other docs structurally, then `get-default-xaml`; no package docs → update; still none → Steps 1.4–1.7; not installed → install first (docs and starters need it); no `.local/docs/` → existing-patterns search first.

#### Step 1.4: Discover Activities (When Needed)

`uip rpa activities find --query "send mail" --limit 10 --output json`: results are global; never assume the first is right. Several for one action → use the one the package `overview.md` names (mail: Office 365 `*Connections`, not classic `SendMail`/`GetMail` needing `Office365ApplicationScope`).

#### Step 1.5: Disambiguate Approach and Provider

Approach (API/UIA/Connector): auto-select when stated or the only viable one, else ask; **install nothing until it is confirmed.** Provider: auto-select when specified, uniquely matched, already installed, represented by a project connection, or already used; ask only as a last resort, offering the top 2–4 choices with a recommendation.

#### Step 1.6: Resolve Activity Properties (Fallback)

```bash
# Non-dynamic activity:
uip rpa activities get-default-xaml --activity-class-name "<FULLY_QUALIFIED_CLASS>" --output json
# Dynamic activity (connector-backed):
uip rpa activities get-default-xaml --activity-type-id "<TYPE_ID>" --connection-id "<CONN_ID>" --output json
```
JIT custom types: `{projectRoot}/.project/JitCustomTypesSchema.json`, [jit-custom-types-schema.md](jit-custom-types-schema.md).

#### Step 1.7: Search Examples Repository

`uip rpa workflow-examples list --tags web --limit 10 --output json` → `uip rpa workflow-examples get --key "<BLOB_PATH>"` (only keys `list` returned). Allowed tags (closed list): adobe-sign asana box concur confluence database document-understanding docusign dropbox email-generic excel excel-online freshbooks freshdesk github gmail google-calendar google-docs google-drive google-sheets gsuite hubspot intacct jira mailchimp marketo microsoft-365 onedrive outlook outlook-calendar pdf powerpoint productivity quickbooks salesforce servicenow sharepoint shopify slack smartsheet stripe teams testing trello web webex word workday zendesk zoom.

#### Step 1.9: Discover Connector Capabilities (For IS/Connector Workflows)

Follow [../is-connector-xaml-guide.md](../is-connector-xaml-guide.md); verify the connection exists (`uip is connections list --output json`). Generic `ConnectorActivity` + typed operation typeId (`ConnectorHttpActivity` for unmodeled endpoints); per-product BAF packages only if already used.

### Phase 2: Generate or Edit

UI activities: Rule 7 gate first; targets only via the `uia-configure-target` flow, NEVER hand-crafted selectors or `uip rpa uia` outside it.

CREATE: don't Read scaffolded `Main.xaml`; one `Write` of the complete workflow replaces it (data files, `mkdir` in the same message); split sprawling logic into invoked files ([§ Designing for Reuse](../environment-setup.md#designing-for-reuse)). EDIT: Read first, then `Edit` with exact, unique `old_string`; never reformat the file.

### Phase 3: Validate & Fix Loop

**MUST** loop until `validate` and `build` both report 0 errors (≤5 fix attempts, then present remaining errors); read [../cli-reference.md § Validation Iteration Loop](../cli-reference.md#validation-iteration-loop) before the first fix. One chained call:
```bash
uip rpa validate --file-path "Workflows/MyWorkflow.xaml" --project-dir "<PROJECT_DIR>" --output json \
  && uip rpa build "<PROJECT_DIR>" --log-level Warn --output json
```
`--file-path` is **relative to the project directory**; only a clean `build` exits. Observable outputs: one `uip rpa run --skip-build`, then inspect them. Diagnose before retrying; fix in Rule 19 order (structure: [§ XAML Safety Rules](#xaml-safety-rules); properties: conditional groups, OverloadGroup; UIA: `debug start`, [uia-starter-guide.md](../uia-starter-guide.md)). InvokeCode only as a last resort.

### Phase 4: Response

Per SKILL.md § Completion Output; name placeholders and connections to review.

## XAML File Anatomy

`x:Class` = project-relative path without `.xaml`, separators → underscores: `Workflows/SendEmail.xaml` → `Workflows_SendEmail`. Dots (`Workflows.SendEmail`) cause *"Invalid ActivityBuilder name … Suggested name …"*. A C# project root also carries `sap2010:ExpressionActivityEditor.ExpressionActivityEditor="C#"` (as `init` writes it): otherwise Studio opens it as VisualBasic and refuses it, though `validate`/`build` pass.

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

Fill `ReferencesForImplementation` per [common-pitfalls.md § Assembly References](common-pitfalls.md#assembly-references-studio-requires-and-the-cli-does-not-check). Never add `<sap2010:WorkflowViewState.ViewStateManager>` to new files or edit an existing one (corrupts layout).

## Workflow Types

**Sequence:** linear, the default. **Flowchart:** Rule 20, [§ Flowchart Structure & Wiring](canvas-layout-guide.md#flowchart-structure--wiring). **State Machine** (e.g. REFramework): `State`s are direct children; `InitialState` and `Transition.To` use `x:Reference`; `IsFinal="True"` = terminal ([§ State Machine Layout](canvas-layout-guide.md#4-state-machine-layout)).

### Long Running Workflow (ProcessDiagram)

`upa:ProcessDiagram` (`EventNode`, `TaskNode`, `DecisionNode`, `EndNode`, `BoundaryNode`), package **`UiPath.FlowchartBuilder.Activities`**, not on `targetFramework: "Legacy"`; namespaces, gateways, persistence: [long-running-workflow-guide.md](long-running-workflow-guide.md). `<x:Reference>` registration as Flowchart (incl. trailing registration for inline nodes); ViewState: [canvas-layout-guide.md § Long Running Workflow](canvas-layout-guide.md#5-long-running-workflow-processdiagram-layout).

## XAML Safety Rules

Never remove root `xmlns` declarations (add only as needed); read existing canvas positions before adding nodes.

### Respect Expression Language

Check `project.json` `expressionLanguage` (new projects default to VB.NET). **CSharp:** C# operators (`+`, `==`), `<CSharpValue>` for inputs and `<CSharpReference>` for outputs, no namespace prefix; never `[bracket]` shorthand (creates `VisualBasicValue` → multiple-language errors); see [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md). **VB:** `&`, `=`, `[bracket]`. Mixing languages breaks builds.

### Activity Property Surface and Starter XAML

Off-card: never author from memory or the starter alone; `<Activity>.md` is the property surface, the starter adds namespaces/references. Read the MD path directly (a failed Read is the existence check); if you cannot name its required properties, you read the wrong file. No doc anywhere → flag the package third-party, use find + starter, warn the surface may be incomplete.

**Skip-tax:** starters omit `null`/`0`/`false`/unset properties (`NTypeInto` hides 2 of 20, `NClick` ~3; hidden: `ClickType`, `KeyModifiers`, `WaitForReady`, `EmptyFieldMode`). `NGetText`'s starter is `<uix:NGetText HealingAgentBehavior="SameAsCard" />`: bind output to `TextString` (`OutArgument<string>`); `NGetText.Value` gives `Cannot set unknown member 'UiPath.UIAutomationNext.Activities.NGetText.Value'`, breaking Object Repository linking. Legacy `Text="..."` is valid; never "correct" it.

### Container Activity Bodies — Wrap in Sequence

Every body/branch slot is a `<Sequence>` (Rule 24): `If.Then`/`If.Else` (`DisplayName="Then"`/`"Else"`); `While`/`DoWhile` body, and `ForEach.Body` inside its `ActivityAction<T>` (`"Body"`); `TryCatch.Try`, each `Catch`'s `ActivityAction<T>`, `TryCatch.Finally` (`"Try"`/`"Catch"`/`"Finally"`); `Switch.Default` and each `x:Key` case; `PickBranch.Trigger`/`Action`; `NApplicationCard.Body` `ActivityAction` (`"Do"`); any `Body` typed `Activity`. Card containers: copy the card. Off-card: after the Rule 21 doc read, copy the wrapped shape from `uip rpa activities get-default-xaml --activity-class-name "<FullClassName>"` ([example](xaml-editing-catalog.md#example-1-basic-activities-logmessage-ifelse-assign)). Editing a bare slot: add the wrapper in the same edit.

## Property Binding: Attributes vs Child Elements

Attributes for strings, enums, booleans, VB `[expr]`:
```xml
<ui:LogMessage Message="[myVar]" Level="Info" />
```
Child elements for complex objects, outputs when the attribute fails, and literal `[k(enter)]` strings (attributes run but don't render; [common-pitfalls.md § NTypeInto `Text`](common-pitfalls.md#ntypeinto-text-with-literal-k-special-key-tokens)):
```xml
<ui:SomeActivity>
  <ui:SomeActivity.Result>
    <OutArgument x:TypeArguments="x:String">[outputVar]</OutArgument>
  </ui:SomeActivity.Result>
</ui:SomeActivity>
```

### Version-Sensitive Properties

“Could not find member” / `Cannot set unknown member '<Class>.<Prop>'`: names drift (UIA `26.4.1-preview`: `InputMode` → `InteractionMode`, `EmptyField` → `EmptyFieldMode`) — check the installed-version MD; remove or rename, or take the set from `uip rpa activities get-default-xaml`.

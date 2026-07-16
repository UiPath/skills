# XAML Basics and Rules

Core concepts for UiPath workflow XAML files, the authoring workflow (Discovery → Generate/Edit → Validate & Fix → Response), and rules for generating and/or editing XAML content.

## Authoring Workflow

Discovery-first approach with iterative error-driven refinement. Always understand before acting, start simple, validate continuously.

**Core principles:**

1. **Activity Docs Are the Source of Truth** — installed packages ship structured documentation at `{projectRoot}/.local/docs/packages/{PackageId}/` with source-accurate properties, types, defaults, enum values, conditional property groups, and working XAML examples. Always check for them first.
2. **Know Before You Write** — **NEVER** generate XAML blind. Understand the project structure, packages, expression language, and existing patterns.
3. **Use What You Know, Skip What You Don't Need** — if you already know the package ID and activity class name, go directly to its doc file. The discovery steps are a priority ladder, not a mandatory checklist.
4. **Start Minimal, Validate Continuously, Fix by Category** — one activity at a time; after every change run `validate`, and exit only on a clean project-level `build` (§ Phase 3). Fix order: Package → Structure → Type → Activity Properties → Logic.

**Classify the request:**

| Request Type | Trigger Words | Action |
|--------------|---------------|--------|
| **CREATE** | "generate", "create", "make", "build", "new" | Discovery → Generate |
| **EDIT** | "update", "change", "fix", "modify", "add to" | Discovery → Edit |

If unclear which file to edit, **ask the user** rather than guessing.

### Phase 1: Discovery

**Goal:** understand project context, leverage installed activity documentation, study existing patterns, identify reusable components, and discover activities before writing any XAML.

> **Batch discovery across activities.** When the workflow needs several activities, do NOT run the find → read-doc → `get-default-xaml` triple one activity at a time. Emit all `activities find` calls in parallel, then all `<Activity>.md` `Read`s in parallel, then all `get-default-xaml` calls in parallel (SKILL.md § Call Batching). Only the per-activity *authoring + validate* loop (Phase 2 / Phase 3) stays sequential — discovery fans out.

#### Step 1.1: Project Structure

```
Glob: pattern="**/*.xaml" path="{projectRoot}"       → list all XAML workflow files
Read: file_path="{projectRoot}/project.json"          → read the project definition
```

Analyze: where new workflows belong (folder conventions), naming patterns, similar existing workflows, VB or C# (`expressionLanguage`), installed packages, existing connections/credentials/objects to reuse.

#### Step 1.2: Discover Activity Documentation (Primary Source)

**Read `<Activity>.md` BEFORE `activities get-default-xaml`, every time, even for activities that look simple.** The doc is the property surface; the CLI starter is not — see [§ Activity Property Surface](#activity-property-surface-and-starter-xaml) for the skip-tax and the full per-activity procedure.

**Availability:** docs exist only for **installed packages** and typically only for **newer package versions**. When the package is not installed, install it first. When docs are missing, update to the latest version, or fall back to `skills/uipath-rpa/references/activity-docs/<PackageId>/<closest-version>/`.

```
{projectRoot}/.local/docs/packages/
+-- {PackageId}/
    +-- overview.md
    +-- activities/
    |   +-- {ActivitySimpleClassName}.md
    +-- coded/                             # Ignore for XAML workflows
```

Every `activities/{ActivityName}.md` follows: Header → Metadata → Properties (Input, Output, Conditional groups, Common) → Valid Configurations → Enum Reference → XAML Examples → Notes.

| Situation | Action |
|-----------|--------|
| **Know package + activity name** | `Read` `{projectRoot}/.local/docs/packages/{PackageId}/activities/{ActivityName}.md` |
| **Know package, not activity** | `Read` the `overview.md`, then read the identified activity doc |
| **Don't know package** | `Glob` with `**/*.md` in `{projectRoot}/.local/docs/packages/`. `.local/` is gitignored — use `Glob` + `Read`, not `Grep` |
| **Docs exist but activity undocumented** | Use other docs as structural reference, fall back to `activities get-default-xaml` |
| **No docs for package** | Update the package first — this often adds docs. **Caution:** major version jumps (e.g., 23.x → 26.x) may deprecate activities — prefer minor/patch updates. If still no docs, fall back to Steps 1.4-1.7 |
| **Package not installed** | Install it first — both docs and `activities get-default-xaml` require it |
| **No `.local/docs/` at all** | Use fallback flow starting at Step 1.3 |

#### Step 1.3: Search Current Project

Search existing workflows for reusable patterns and conventions:

```
Glob: pattern="**/*pattern*.xaml" path="{projectRoot}"
Grep: pattern="ActivityName|pattern" path="{projectRoot}"
Read: file_path="{projectRoot}/ExistingWorkflow.xaml"
```

**Mature project**: prioritize local patterns. **Greenfield project**: skip this step.

#### Step 1.4: Discover Activities (When Needed)

Find which activity implements a user-described action:

```bash
uip rpa activities find --query "send mail" --limit 10 --output json
```

Results are **global** — not limited to installed packages. If a useful activity is in an uninstalled package, install it immediately. Tags can narrow results.

#### Step 1.5: Disambiguate Approach and Provider

**Approach-level (API vs UI Automation vs Connector):** auto-select when the user stated the approach or only one is viable; prompt when multiple are viable and no preference was given. **Do NOT install packages until approach is confirmed.**

**Provider-level:** auto-select when the user specified a provider, only one package matches, the project already has the package installed, the project defines a matching connection, or the workflow already uses activities from one package. **Prompt only as last resort** — present top 2-4 choices with recommendations.

#### Step 1.6: Resolve Activity Properties (Fallback)

Use `uip rpa activities get-default-xaml` when activity docs are insufficient:

```bash
# Non-dynamic activity:
uip rpa activities get-default-xaml --activity-class-name "<FULLY_QUALIFIED_CLASS>" --output json
# Dynamic activity (connector-backed):
uip rpa activities get-default-xaml --activity-type-id "<TYPE_ID>" --connection-id "<CONN_ID>" --output json
```

For JIT custom types: `Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"`. See [jit-custom-types-schema.md](jit-custom-types-schema.md).

#### Step 1.7: Search Examples Repository

Use when activity docs, `activities find`, and `activities get-default-xaml` don't provide enough context:

```bash
uip rpa workflow-examples list --tags web --limit 10 --output json
uip rpa workflow-examples get --key "<BLOB_PATH>"
```

**Complete tag list:** `adobe-sign`, `asana`, `box`, `concur`, `confluence`, `database`, `document-understanding`, `docusign`, `dropbox`, `email-generic`, `excel`, `excel-online`, `freshbooks`, `freshdesk`, `github`, `gmail`, `google-calendar`, `google-docs`, `google-drive`, `google-sheets`, `gsuite`, `hubspot`, `intacct`, `jira`, `mailchimp`, `marketo`, `microsoft-365`, `onedrive`, `outlook`, `outlook-calendar`, `pdf`, `powerpoint`, `productivity`, `quickbooks`, `salesforce`, `servicenow`, `sharepoint`, `shopify`, `slack`, `smartsheet`, `stripe`, `teams`, `testing`, `trello`, `web`, `webex`, `word`, `workday`, `zendesk`, `zoom`

#### Step 1.8: Get Current Context (As Needed)

```
Read: file_path="{projectRoot}/project.json"
Glob: pattern="**/*" path="{projectRoot}/.objects/"
Bash: uip is connections list --output json
```

#### Step 1.9: Discover Connector Capabilities (For IS/Connector Workflows)

For end-to-end authoring of `ConnectorActivity` XAML (connection + type ID + Configuration blob + FieldObjects) AND the connector/connection discovery commands, see **[../is-connector-xaml-guide.md](../is-connector-xaml-guide.md)** — worked example included.

**Path selection for calling connectors from XAML:**

| Option | When to use |
|--------|-------------|
| **IS generic `ConnectorActivity`** with a typed operation typeId (e.g. `37a305b2-...` for Slack "Send Message to Channel") | **Default choice** — schema-driven, hand-authorable with the CLI flow in the guide. Works via `UiPath.IntegrationService.Activities`. |
| **IS generic `ConnectorActivity`** with `ConnectorHttpActivity` typeId (e.g. `...httpRequest...`) | Fallback for endpoints the connector hasn't modeled as a first-class operation. Field names are still connector-defined — not `method`/`path`/`body`. Read the schema. |
| **Per-product BAF activity package** (`UiPath.Slack.Activities`, `UiPath.Salesforce.Activities`, etc.) | Avoid for headless authoring. These wrap IS internally but use a more complex BAF XAML shape (`ScopeActivity` + dynamic child activity with `BusinessEntity`, `SelectedFields`, `PopulatedAPIParameters`). Default to the generic `ConnectorActivity` path unless the project already uses the BAF package. |

### Phase 2: Generate or Edit

**UI Automation — Target Configuration Gate (MANDATORY).** Before writing any XAML with UI activities: [../ui-automation-guide.md](../ui-automation-guide.md) MUST be read IN FULL first. Every UI element target MUST be configured through the `uia-configure-target` skill flow — [../uia-configure-target-workflows.md](../uia-configure-target-workflows.md) MUST be read IN FULL first. **NEVER** manually call low-level `uip rpa uia` CLI commands outside of the skill flow.

**For CREATE requests:** generate a minimal working version, one activity at a time, validate frequently. Use the `Write` tool to create the `.xaml` file per [§ XAML File Anatomy](#xaml-file-anatomy). Infer the file path from folder conventions; use descriptive filenames.

**For EDIT requests:** always `Read` current content before editing; use `Edit` with exact, unique `old_string` matches.

### Phase 3: Validate & Fix Loop

**MUST** repeat until 0-error state from **both** `validate` and `build`, or max 5 fix attempts per loop. After 5 attempts, stop and present remaining errors to the user. The canonical two-phase loop (per-file `validate` → project-level `build`), the errors `build` catches that `validate` misses, and the smoke-test procedure: [../cli-reference.md § Validation Iteration Loop](../cli-reference.md#validation-iteration-loop) — read it before your first fix iteration.

```bash
uip rpa validate --file-path "Workflows/MyWorkflow.xaml" --output json
uip rpa build "<PROJECT_DIR>" --log-level Warn --output json
```

`--file-path` must be **relative to the project directory**. Treat `validate` clean as half-done — `build` clean is the signal to exit the loop.

**Fix order:** Package → Structure → Type → Activity Properties → Logic.

1. **Package Errors** — install/update the package; activity docs become available after install.
2. **Structural Errors** — fix XML structure against [§ XAML File Anatomy](#xaml-file-anatomy) and [§ XAML Safety Rules](#xaml-safety-rules).
3. **Type Errors** — check the activity doc for correct types and enum values. JIT types: [jit-custom-types-schema.md](jit-custom-types-schema.md).
4. **Activity Properties Errors** — read the activity doc for properties, conditional groups, valid configurations; fallback `activities get-default-xaml`. Watch for OverloadGroup conflicts.
5. **Logic Errors** — verify expression syntax matches the project language. For UI automation use `debug start` per [../ui-automation-guide.md](../ui-automation-guide.md) § Running UI Automation Workflows.

**When stuck:** defer to the user for minor config details. If an activity cannot be resolved, consider InvokeCode as a last resort.

### Phase 4: Response

Report: file path of created/edited workflow · brief description · key activities and logic · packages installed · limitations or notes · suggested next steps (testing, parameterization) · encourage the user to review and customize (fill placeholders, set up connections).

### Anti-Patterns

- **NEVER** generate large, complex workflows in one go
- **NEVER** manually craft UI selectors outside of the `uia-configure-target` skill flow
- **NEVER** guess properties, types, or configurations without checking docs
- **NEVER** use incorrect keys with `uip rpa workflow-examples get` (always from list results)
- **NEVER** ask the user to choose a provider without checking project signals first
- **NEVER** retry failing CLI commands in a loop without diagnosing the root cause
- **NEVER** use connector activities without checking connection existence
- **NEVER** ignore activity doc conditional property groups (OverloadGroup conflicts cause validation errors)
- **NEVER** generate full XAML from scratch without using `activities get-default-xaml` as a starting point

## XAML File Anatomy

Every UiPath XAML workflow file has this structure:

**`x:Class` naming rule:** The value must match the file's relative path from the project root (without the `.xaml` extension), with folder separators replaced by **underscores** — not dots. For a root-level file `MyWorkflow.xaml` → `x:Class="MyWorkflow"`. For a file in a subfolder `Workflows/SendEmail.xaml` → `x:Class="Workflows_SendEmail"`. Using dots (e.g., `Workflows.SendEmail`) causes a validation error: *"Invalid ActivityBuilder name … Suggested name …"*.

```xml
<Activity mc:Ignorable="sap sap2010 sads" x:Class="FolderName_FileName"
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
  <Sequence DisplayName="Main Sequence">
    <Sequence.Variables>
      <Variable x:TypeArguments="x:String" Name="tempVar" Default="hello" />
    </Sequence.Variables>
    <!-- Activities go here -->
  </Sequence>

  <!-- ViewState (designer metadata - DO NOT EDIT) -->
  <sap2010:WorkflowViewState.ViewStateManager>
    <!-- ... -->
  </sap2010:WorkflowViewState.ViewStateManager>
</Activity>
```

## Workflow Types

### Sequence
Linear, step-by-step execution. Best for straightforward processes.
```xml
<Sequence DisplayName="My Sequence">
  <!-- Activities execute top to bottom -->
</Sequence>
```

### Flowchart
Branching logic with decision nodes. Best for complex decision flows.

**Key pattern:** All FlowStep/FlowDecision/FlowSwitch nodes are direct children of `<Flowchart>`; wire them via `<x:Reference>` inside property elements (`Flowchart.StartNode`, `FlowStep.Next`, `FlowDecision.True/False`). NEVER nest one `FlowStep` inside another's `<FlowStep.Next>` — nested-only steps are absent from `Flowchart.Nodes` and won't render.


Node vocabulary, structure & wiring rules, the forbidden nested-chain pattern, node registration, condition expressions (VB/C#), and layout: [canvas-layout-guide.md § Flowchart Structure & Wiring](canvas-layout-guide.md#flowchart-structure--wiring) and [§ Flowchart Layout](canvas-layout-guide.md#3-flowchart-layout).

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

**Key patterns:**
- `InitialState` attribute references the starting State
- States are direct children of `<StateMachine>` (no wrapper element)
- `IsFinal="True"` marks the terminal state
- Transitions use `<Transition.To><x:Reference>__ReferenceID</x:Reference></Transition.To>` child element pattern

**ViewState is needed** for usable State Machine layout. See [canvas-layout-guide.md § State Machine Layout](canvas-layout-guide.md#4-state-machine-layout) for coordinate systems, transition connection points, and recipes.

### Long Running Workflow (ProcessDiagram)
BPMN-style horizontal flow for event-driven, long-running processes. Uses `upa:ProcessDiagram` with `EventNode`, `TaskNode`, `DecisionNode`, and `EndNode`.

Requires additional namespaces:
```xml
xmlns:upa="clr-namespace:UiPath.Process.Activities;assembly=UiPath.Process.Activities"
xmlns:upas="clr-namespace:UiPath.Process.Activities.Shared;assembly=UiPath.Process.Activities"
```

These types ship in the **`UiPath.FlowchartBuilder.Activities`** package (runtime assembly `UiPath.Process.Activities`) — install before authoring (Common Rule 6). Not supported on `targetFramework: "Legacy"`. Package install, full node vocabulary, gateway patterns, suspend/resume: [long-running-workflow-guide.md](long-running-workflow-guide.md).


**Key patterns:**
- Flows **left-to-right** (horizontal), not top-to-bottom
- `EventNode` = start/end circles, `TaskNode` = activity rectangles, `DecisionNode` = diamond (True/False branches), `EndNode` = end circle
- `BoundaryNode` attaches to `TaskNode.BoundaryNodes` for error handling
- Same `<x:Reference>` node registration rules as Flowchart — inline nodes need trailing registration
- Gateway nodes (`SplitNode`/`MergeNode`/`SwitchNode<T>`), subprocesses, intermediate events, and persistence-based waits: [long-running-workflow-guide.md](long-running-workflow-guide.md)

**ViewState is needed.** See [canvas-layout-guide.md § Long Running Workflow](canvas-layout-guide.md#5-long-running-workflow-processdiagram-layout) for horizontal layout recipes.

## XAML Safety Rules

Critical rules to follow when editing XAML files to prevent validation errors and workflow corruption.

### ViewState Rules

ViewState controls how activities appear in the visual designer. Rules differ by workflow type and operation:

**Sequences:** ViewState is optional — Studio auto-manages `IsExpanded` state. No coordinates needed.

**Flowcharts, State Machines, Long Running Workflows:** ViewState is **mandatory** — it determines node positions on the 2D canvas. Without it, Studio stacks every node at (0,0): they overlap into what looks like **a single node**. Studio does **not** auto-arrange on open — the stacked layout persists until a user manually triggers Auto Arrange. Always generate ViewState for these workflow types.

**When editing existing files:**
- Do NOT modify the global `<sap2010:WorkflowViewState.ViewStateManager>` section — it can corrupt the designer layout
- Do NOT modify existing ViewState on nodes you are not changing
- When adding new nodes to a Flowchart/StateMachine, read existing node positions first to avoid overlap

**When generating new Flowchart/StateMachine/ProcessDiagram files:**
- Generate ViewState for every node to produce a usable layout: `ShapeLocation` + `ShapeSize` are required; `ConnectorLocation` is optional (Studio auto-routes connectors from node positions)
- See [canvas-layout-guide.md](canvas-layout-guide.md) for coordinate systems, standard sizes, and layout recipes


### Preserve xmlns Declarations
Never remove existing `xmlns` attributes from the root `<Activity>` element. Only add new ones as needed. Removing a namespace declaration that is referenced anywhere in the file will cause validation errors.

### Respect Expression Language
Always check the project's expression language before writing expressions:
- **CSharp**: Use C# syntax (`+` for string concat, `==` for equality). Use `<CSharpValue>` for input expressions and `<CSharpReference>` for output bindings — **without a namespace prefix**. Do NOT use `[bracket]` shorthand — brackets create `VisualBasicValue` nodes, causing "multiple languages" validation errors.
- **VB**: Use VB syntax (`&` for string concat, `=` for equality). Use `[bracket]` shorthand for expressions.

Mixing expression languages causes build failures.

### Activity Property Surface and Starter XAML

Never construct activity XAML from memory. Two sources, in this order:

1. **`<Activity>.md`** — authoritative property surface: which properties exist, types, defaults, descriptions, required-scope rules.
2. **`uip rpa activities get-default-xaml --activity-class-name "<FullClassName>"`** — starter element with correct namespaces, assembly references, and any properties whose values differ from the type default.

**Where `<Activity>.md` lives:** primary `{PROJECT_DIR}/.local/docs/packages/<PackageId>/activities/<Activity>.md` (auto-generated on install; `Glob` + `Read`, not `Grep` — `.local/` is gitignored); fallback `skills/uipath-rpa/references/activity-docs/<PackageId>/<closest-version>/<Activity>.md` (pick the version folder closest to installed) — routing table: [§ Step 1.2](#step-12-discover-activity-documentation-primary-source). **Neither exists:** the package is third-party or unusual — document that, fall back to `activities find` + `activities get-default-xaml` alone, and warn the user the property surface may be incomplete.

> **Skip-tax.** `activities get-default-xaml` omits any property whose value equals the type default (`null`, `0`, `false`, unset). For `NTypeInto`: 2 of 20 properties. For `NClick`: ~3 of ~15. For `NGetText`: every output property — the starter is literally `<uix:NGetText HealingAgentBehavior="SameAsCard" />`, with no output member visible. Authoring from this starter alone is how `NGetText.Value="..."` gets written — `Value` does not exist on that activity, so `validate` accepts it as static-clean and `build` finally rejects it as an unknown member. The starter looks complete; it isn't. The MD read is the only way you learn which properties actually exist (`TextString`, `ClickType`, `KeyModifiers`, `WaitForReady`, `EmptyFieldMode`, etc.). **When authoring a new Get Text, bind the output to `TextString`** (`OutArgument<string>`) — the typed member the current designer surfaces. But `NGetText` declares **two** real output members: `TextString` and a legacy non-generic `Text` `OutArgument` (backwards-compat — the activity writes the scraped text to both at runtime, and the designer hides whichever the installed version does not use). So a `Text="..."` binding in an existing or older workflow is valid and must not be flagged or "corrected" — only `Value` is a genuine unknown member.

**Workflow — each step depends on the previous step's output:**

1. `uip rpa activities find --query "<keyword>" --output json` → fully qualified class name, type ID, `isDynamicActivity` flag.
2. **Locate `<Activity>.md` (primary → fallback per the lookup order above) and write an explicit property checklist** — required properties for the activity to function, plus optional properties relevant to your use case. If neither doc location has the file, record that explicitly and proceed to step 3 with a flag in your output. If you cannot name at least the required properties from the doc you found, you read the wrong file.
3. `uip rpa activities get-default-xaml` → starter element with namespaces and assembly references.
4. **Diff your step-2 checklist against the step-3 starter.** Add every checklist property that isn't already in the starter. An empty checklist with no third-party flag from step 2 means step 2 was skipped — go back to step 2; do NOT author from the starter alone.
5. Validate with `uip rpa validate`.

**The rule binds for every activity not on the [common-activity card](../common-activity-card.md).** Check the card first. If the activity is listed there, author from the card entry and skip `activities find`, `activities get-default-xaml`, and the per-activity doc read. If the activity is not listed there, follow the full workflow above. Self-extending the card by personal judgment ("this one feels simple — `StartProcess`, `InvokeWorkflowFile`, I can skip the procedure") is the bug. For card activities the surface is authoritative — version-anchored, source-verified, curated centrally. For everything else, the procedure is the only check.

**Anti-pattern.** Treating `activities get-default-xaml` output as the complete property surface. The CLI runs XAML serialization on a default-constructed instance; type-default values are omitted by design.

**Property-name drift.** When `validate` reports `Cannot set unknown member '<Class>.<Prop>'`, the property name is wrong for the installed package version. Check `<Activity>.md` — property names drift between package versions (e.g. UIA `26.4.1-preview` renamed `InputMode` → `InteractionMode`, `EmptyField` → `EmptyFieldMode`).

Use `uip rpa workflow-examples list` and `uip rpa workflow-examples get` for usage examples, in addition to searching existing local `.xaml` files.

### Container Activity Bodies — Wrap in Sequence

Container activities have body or branch slots typed `Activity` or `ActivityAction<T>`. Studio's designer expects each slot to hold a `<Sequence>` drop zone; Studio's serializer emits the wrapped form. **Wrap even single-activity bodies.**

| Activity | Slot(s) | Wrapper |
|----------|---------|---------|
| `If` | `If.Then`, `If.Else` | `<Sequence DisplayName="Then">` / `<Sequence DisplayName="Else">` |
| `While`, `DoWhile` | direct child of the activity | `<Sequence DisplayName="Body">` |
| `ForEach<T>` | `ForEach.Body` → `ActivityAction<T>` body | `<Sequence DisplayName="Body">` |
| `TryCatch` | `TryCatch.Try` | `<Sequence DisplayName="Try">` |
| `TryCatch` | each `Catch` → `ActivityAction<T>` body | `<Sequence DisplayName="Catch">` |
| `TryCatch` | `TryCatch.Finally` | `<Sequence DisplayName="Finally">` |
| `Switch<T>` | `Switch.Default`, each `<x:String x:Key="...">` case | `<Sequence>` per case |
| `Pick` | each `PickBranch.Trigger`, `PickBranch.Action` | `<Sequence>` per slot |
| `NApplicationCard` | `Body` → `ActivityAction<...>` body | `<Sequence DisplayName="Do">` |
| Any activity with `Body` typed `Activity` | the body slot | `<Sequence>` |

**Validators do not catch this.** `validate` and `build` both accept any single `Activity` in a body slot — `<If.Then><Throw /></If.Then>` is structurally legal. The wrap is a Studio-idiomatic convention (drop-zone ergonomics + canonical emission), not a static-analysis requirement.

**Cheapest enforcement.** For card-listed containers (`If`, `Switch<T>`, `TryCatch`, `While`, `DoWhile`, `ForEach<T>`), copy the wrapped shape from the common-activity card. For off-card containers (`Pick`, `Parallel`, `ParallelForEach<T>`, package-specific body activities), run `uip rpa activities get-default-xaml --activity-class-name "<FullClassName>"` after the Rule 21 doc read and copy the wrapped shape from the starter. See SKILL.md Rules 21, 21a, 24.

**Worked example.** [§ Example 1: Basic Activities (LogMessage, If/Else, Assign)](#example-1-basic-activities-logmessage-ifelse-assign) below — `If.Then` and `If.Else` each carry a `<Sequence>`.

**Editing existing files.** When inserting an activity into an empty or bare `If.Then` / `Catch` / `Body` slot, add the `<Sequence>` wrapper in the same edit.

### Preserve Existing Structure
When editing XAML:
- Do not reformat or re-indent the entire file
- Only modify the specific section you need to change
- Use the `Edit` tool for targeted replacements (match exact `old_string`, replace with `new_string`)

### Validate After Every Change
Run `uip rpa validate` after every XAML modification. Do not batch multiple edits without validation — catching errors early is much easier than debugging compound issues.

## Common Editing Operations

Common operations for editing and managing workflow XAML files.

### Adding Arguments (In/Out/InOut)

Add `x:Property` elements inside the `<x:Members>` block:

```xml
<x:Members>
  <!-- In argument (input to workflow) -->
  <x:Property Name="in_CustomerName" Type="InArgument(x:String)" />
  <!-- Out argument (output from workflow) -->
  <x:Property Name="out_ProcessedCount" Type="OutArgument(x:Int32)" />
  <!-- InOut argument (both input and output) -->
  <x:Property Name="io_DataTable" Type="InOutArgument(scg:List(x:String))" />
</x:Members>
```

Argument naming convention: `in_`, `out_`, `io_` prefixes.

#### Setting Default Values for Arguments

Defaults go on the root `<Activity>` element using the canonical .NET Workflow Foundation self-namespace syntax:

```xml
<Activity x:Class="TestCase"
          xmlns:this="clr-namespace:"
          this:TestCase.in_FileName="report.pdf"
          xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
          xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <x:Members>
    <x:Property Name="in_FileName" Type="InArgument(x:String)" />
  </x:Members>
</Activity>
```

Two parts are mandatory:

1. **`xmlns:this="clr-namespace:"`** — the empty `clr-namespace:` is what makes `this:` resolve to the class declared by `x:Class`.
2. **`this:<ClassName>.<argName>="<value>"`** — the attribute name MUST be qualified with `this:` AND the class name; bare `<argName>="<value>"` is rejected.

The default is baked into the compiled assembly at build time as a `Literal<T>` expression in the generated class's constructor. At runtime, when the workflow is invoked without that argument supplied (e.g. `uip rpa run` without `--input-arguments`), the literal is used.

**Three default-value forms that DO NOT work** — every one of them is rejected by the XAML loader. Authoring agents have repeatedly tried these and lost time to confusing errors — don't:

| Bad form | Error |
|---|---|
| `<Activity in_FileName="...">` (no `xmlns:this`, no class qualifier) | `member (in_FileName) is not supported by DynamicActivity` |
| `<x:Property Name="in_FileName" ...><InArgument>...</InArgument></x:Property>` | `DynamicActivityProperty does not have a content property` |
| `<x:Property.Value>...</x:Property.Value>` | `x:Property member (Value) is not supported by DynamicActivityProperty` |

If you must accept an empty string as a sentinel ("user didn't provide one") and substitute a literal anyway, use a ternary inside each `CSharpValue`/`VisualBasicValue` consumer of the argument:

```xml
<CSharpValue x:TypeArguments="x:String">string.IsNullOrEmpty(in_FileName) ? "report.pdf" : in_FileName</CSharpValue>
```

But the root-attribute default above is the cleaner answer — use it first.

### Adding Variables

Add `Variable` elements inside the workflow container's `.Variables` block:

```xml
<Sequence.Variables>
  <Variable x:TypeArguments="x:String" Name="filePath" />
  <Variable x:TypeArguments="x:Int32" Name="counter" Default="0" />
  <Variable x:TypeArguments="x:Boolean" Name="isValid" Default="True" />
</Sequence.Variables>
```

Variables are scoped to their containing activity (Sequence, Flowchart, etc.).

**IMPORTANT — `x:` and `s:` are XML namespace aliases, not separate type systems.**
`x:String` and `s:String` both refer to `System.String`; the prefix only determines which namespace schema resolves the name. The `x:` XAML language schema registers a small fixed set of types (`x:String`, `x:Int32`, `x:Int64`, `x:Double`, `x:Boolean`, `x:Byte`, `x:Single`, `x:Decimal`, `x:Char`, `x:Object`, `x:TimeSpan`). Any other CLR type — including `DateTime`, `DateTimeOffset`, `Guid`, etc. — is not registered in that schema and must be reached through `s:` (`xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"`).
Using `x:DateTime` or `x:DateTimeOffset` produces `Cannot create unknown type` at load time.
See `common-pitfalls.md` → *"Invalid Use of `x:` Prefix for Non-Builtin CLR Types"* for the full list and examples.

### Adding Namespace Imports

Add `<x:String>` entries:

```xml
<x:String>System.Data</x:String>
<x:String>System.IO</x:String>
<x:String>UiPath.Excel</x:String>
```

### Adding Assembly References

Add `<AssemblyReference>` entries:

```xml
<AssemblyReference>System.Data</AssemblyReference>
<AssemblyReference>UiPath.Excel.Activities</AssemblyReference>
```

### Expressions

#### C# Expressions (`expressionLanguage: CSharp`)

Applies to XAML workflow files in projects whose `project.json` has `expressionLanguage: CSharp`. These rules govern expressions inside XAML — they are unrelated to coded workflows (`.cs` files), which are plain C# and do not use `CSharpValue` / `CSharpReference` elements.

Expressions use explicit `<CSharpValue>` (for read/evaluate) or `<CSharpReference>` (for write/lvalue) elements inside `<InArgument>` / `<OutArgument>`:
```xml
<Assign DisplayName="Set Name">
  <Assign.To>
    <OutArgument x:TypeArguments="x:String">
      <CSharpReference x:TypeArguments="x:String">fullName</CSharpReference>
    </OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:String">
      <CSharpValue x:TypeArguments="x:String">firstName + " " + lastName</CSharpValue>
    </InArgument>
  </Assign.Value>
</Assign>
```

**Important**: Do NOT use `[bracket]` shorthand for expressions. Brackets create `VisualBasicValue` nodes at deserialization time, causing validation failures for C#-only syntax (`null`, `?.`, `??`, `typeof()`, etc.).

**Stronger rule for attribute-form bindings on `InArgument<T>` / `OutArgument<T>`:** in XAML projects with `expressionLanguage: CSharp`, any **non-literal** attribute value (`Message="variableName"`, `Text="&quot;Hello &quot; + name"`) is also deserialized as a `VisualBasicValue<T>` and fails at runtime with `JIT compilation is disabled for non-Legacy projects`. The attribute parser defaults to VB regardless of the project's expression language. Use `<CSharpValue>` / `<CSharpReference>` child elements for anything that isn't a plain literal. See [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md) (includes § C# Expression Pitfalls).

**Safe attribute-form values** (no expression evaluator involved, type converter handles them directly):
- Literal strings on `InArgument<String>`: `Text="Book trip"`, `DisplayName="Open file"`
- Enums: `Level="Info"`, `ClickType="Single"`, `MouseButton="Left"`
- Numbers, booleans, `{x:Null}`
- `TimeSpan` literals: `Duration="00:00:02"`

**For activity-specific recipes** (`LogMessage.Message` as `InArgument<Object>`, `NGetText.TextString` as `OutArgument<String>`, `StartProcess.FileName` with composed paths, `Assign`, `If.Condition`, etc.), see [csharp-activity-binding-guide.md](csharp-activity-binding-guide.md). That file is the canonical lookup for the binding form per common activity property.

#### VB Expressions (`expressionLanguage: VisualBasic`)
Expressions use VB syntax with `[bracket]` shorthand (VB is the default deserialization target for brackets):
```xml
<InArgument x:TypeArguments="x:String">[firstName & " " & lastName]</InArgument>
```

**Check `project.json` `expressionLanguage` field to determine which syntax to use.**

### Resource Types (IResource / ILocalResource)

Some activity properties accept `IResource` or `ILocalResource` types instead of plain strings for file inputs. These are part of UiPath's resource abstraction model:

| Type | Description | When Used |
|------|-------------|-----------|
| `IResource` | Generic resource (local file, remote file, cloud attachment) | Activities that accept any file source |
| `ILocalResource` | Local file on disk (has `LocalPath` property) | Activities that need a file on the local filesystem |
| `IRemoteResource` | Remote resource with a URI and a local copy | Cloud/API-sourced files |

**In XAML**, resource-typed properties are set via expressions that create the resource — `LocalResource.FromPath(filePath)` or the Path Exists activity. Both approaches, the XAML forms, and the required `UiPath.Platform.ResourceHandling` namespace: [common-pitfalls.md § IResource / ILocalResource](common-pitfalls.md#iresource--ilocalresource--string-path-conversion).

**Activity Storage**: Some activities use a bucket-based storage system (`.storage/` folder in the project). Resources stored at design-time in `.storage/.runtime/<bucket>/` are packed into the published NuPkg and available at runtime. This is managed automatically — you don't need to edit storage resources directly in XAML.

## XAML Reference Examples

Complete workflow examples demonstrating proper XAML structure and patterns.

### Example 1: Basic Activities (LogMessage, If/Else, Assign)

VB project with core workflow activities. Shows If/Then/Else branching and Assign pattern.

```xml
<Activity mc:Ignorable="sap sap2010" x:Class="Main"
  xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:sap="http://schemas.microsoft.com/netfx/2009/xaml/activities/presentation"
  xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
  xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
  xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib"
  xmlns:ui="http://schemas.uipath.com/workflow/activities"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <x:Members>
    <x:Property Name="isWeekend" Type="InArgument(x:String)" />
  </x:Members>
  <VisualBasic.Settings>
    <x:Null />
  </VisualBasic.Settings>
  <sap2010:WorkflowViewState.IdRef>ActivityBuilder_1</sap2010:WorkflowViewState.IdRef>
  <TextExpression.NamespacesForImplementation>
    <sco:Collection x:TypeArguments="x:String">
      <!-- Standard system namespaces -->
      <x:String>System</x:String>
      <x:String>System.Collections.Generic</x:String>
      <x:String>System.Linq</x:String>
      <x:String>UiPath.Core</x:String>
      <x:String>UiPath.Core.Activities</x:String>
      <!-- ... other standard imports ... -->
    </sco:Collection>
  </TextExpression.NamespacesForImplementation>
  <TextExpression.ReferencesForImplementation>
    <sco:Collection x:TypeArguments="AssemblyReference">
      <AssemblyReference>System</AssemblyReference>
      <AssemblyReference>System.Activities</AssemblyReference>
      <AssemblyReference>UiPath.System.Activities</AssemblyReference>
      <!-- ... other standard references ... -->
    </sco:Collection>
  </TextExpression.ReferencesForImplementation>
  <Sequence DisplayName="Main Sequence" sap2010:WorkflowViewState.IdRef="Sequence_1">
    <Sequence.Variables>
      <Variable x:TypeArguments="x:Boolean" Name="isWeekend" />
    </Sequence.Variables>
    <!-- LogMessage activity -->
    <ui:LogMessage DisplayName="Log Message" sap2010:WorkflowViewState.IdRef="LogMessage_1"
      Message="[DateTime.Now.ToString() + &quot; - Execution started&quot;]" />
    <!-- If/Then/Else with Assign activities -->
    <If Condition="[DateTime.Now.DayOfWeek = DayOfWeek.Saturday OrElse DateTime.Now.DayOfWeek = DayOfWeek.Sunday]"
      sap2010:WorkflowViewState.IdRef="If_1">
      <If.Then>
        <Sequence DisplayName="Then" sap2010:WorkflowViewState.IdRef="Sequence_2">
          <Assign sap2010:WorkflowViewState.IdRef="Assign_1">
            <Assign.To>
              <OutArgument x:TypeArguments="x:Boolean">[isWeekend]</OutArgument>
            </Assign.To>
            <Assign.Value>
              <InArgument x:TypeArguments="x:Boolean">[True]</InArgument>
            </Assign.Value>
          </Assign>
        </Sequence>
      </If.Then>
      <If.Else>
        <Sequence DisplayName="Else" sap2010:WorkflowViewState.IdRef="Sequence_3">
          <Assign sap2010:WorkflowViewState.IdRef="Assign_2">
            <Assign.To>
              <OutArgument x:TypeArguments="x:Boolean">[isWeekend]</OutArgument>
            </Assign.To>
            <Assign.Value>
              <InArgument x:TypeArguments="x:Boolean">[False]</InArgument>
            </Assign.Value>
          </Assign>
        </Sequence>
      </If.Else>
    </If>
  </Sequence>
</Activity>
```

**Key patterns:**
- `ui:LogMessage` uses `xmlns:ui="http://schemas.uipath.com/workflow/activities"`
- VB expressions: `OrElse` instead of `||`, no brackets on simple values
- `If.Then` and `If.Else` each wrap content in a `Sequence` — required, not optional. See [§ Container Activity Bodies — Wrap in Sequence](#container-activity-bodies--wrap-in-sequence) for the full slot list
- `Assign` uses `Assign.To` (OutArgument) and `Assign.Value` (InArgument) with explicit `x:TypeArguments`

### Example 2: Package Connector Activity (Office 365 Get Newest Email)

Shows a package-based activity with `ConnectionId` for Integration Service.

```xml
<Activity mc:Ignorable="sap sap2010" x:Class="GetNewestEmail"
  VisualBasic.Settings="{x:Null}"
  sap2010:WorkflowViewState.IdRef="ActivityBuilder_1"
  <!-- standard xmlns omitted — see Example 1 -->
  xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail;assembly=UiPath.MicrosoftOffice365.Activities"
  xmlns:umame="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
  xmlns:umamm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Models;assembly=UiPath.MicrosoftOffice365.Activities"
  xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <!-- Namespaces include package-specific imports -->
  <TextExpression.NamespacesForImplementation>
    <sco:Collection x:TypeArguments="x:String">
      <!-- Standard imports + package-specific -->
      <x:String>UiPath.MicrosoftOffice365.Activities.Mail.Enums</x:String>
      <x:String>UiPath.MicrosoftOffice365.Models</x:String>
      <x:String>UiPath.Shared.Services.Graph.Mail.Models</x:String>
      <x:String>UiPath.MicrosoftOffice365.Activities.Mail.Filters</x:String>
      <x:String>UiPath.MicrosoftOffice365.Activities.Mail.Models</x:String>
      <x:String>UiPath.MicrosoftOffice365.Activities.Mail</x:String>
      <x:String>UiPath.Shared.Activities</x:String>
      <!-- ... -->
    </sco:Collection>
  </TextExpression.NamespacesForImplementation>
  <TextExpression.ReferencesForImplementation>
    <sco:Collection x:TypeArguments="AssemblyReference">
      <!-- Standard refs + package-specific -->
      <AssemblyReference>UiPath.MicrosoftOffice365.Activities</AssemblyReference>
      <AssemblyReference>UiPath.MicrosoftOffice365</AssemblyReference>
      <!-- ... -->
    </sco:Collection>
  </TextExpression.ReferencesForImplementation>
  <Sequence DisplayName="GetNewestEmail" sap2010:WorkflowViewState.IdRef="Sequence_1">
    <!-- Activity with ConnectionId for Integration Service -->
    <umam:GetNewestEmail
      ConnectionAccountName="{x:Null}" ContinueOnError="{x:Null}" Filter="{x:Null}"
      FolderIdBackup="{x:Reference __ReferenceID0}" FreeTextFilter="{x:Null}"
      Mailbox="{x:Null}" MailboxBackup="{x:Reference __ReferenceID1}"
      ManualEntryFolder="{x:Null}" QueryFilter="{x:Null}" Result="{x:Null}"
      AuthScopesInvalid="False" BodyAsHtml="False"
      BrowserFolder="Inbox" BrowserFolderId="Inbox"
      ConnectionId="6265de1b-4264-ed11-ade6-e42aac668fcd"
      DisplayName="Get Newest Email"
      FilterSelectionMode="ConditionBuilder"
      sap2010:WorkflowViewState.IdRef="GetNewestEmail_1"
      Importance="Any" MarkAsRead="False" SelectionMode="Browse"
      UnreadOnly="False" UseConnectionService="True"
      UseSharedMailbox="False" WithAttachmentsOnly="False">
      <!-- Complex nested configuration objects (BackupSlot, MailFolderArgument, etc.) -->
      <umam:GetNewestEmail.MailFolderArgument>
        <umamm:MailFolderArgument ConnectionDescriptor="{x:Null}" ManualEntryFolder="{x:Null}"
          BrowserFolder="Inbox" BrowserFolderId="Inbox"
          ConnectionKey="d04f100e-8b4e-ec11-981f-e42aac66a34d"
          SelectionMode="Browse">
          <umamm:MailFolderArgument.Backup>
            <usau:BackupSlot x:TypeArguments="umame:ItemSelectionMode"
              x:Name="__ReferenceID0" StoredValue="Browse">
              <usau:BackupSlot.BackupValues>
                <scg:Dictionary x:TypeArguments="umame:ItemSelectionMode, scg:List(x:Object)" />
              </usau:BackupSlot.BackupValues>
            </usau:BackupSlot>
          </umamm:MailFolderArgument.Backup>
        </umamm:MailFolderArgument>
      </umam:GetNewestEmail.MailFolderArgument>
      <!-- GetNewestEmail.MailboxArg: analogous MailboxArgument with its own BackupSlot
           (x:Name="__ReferenceID1", x:TypeArguments="umame:MailboxSelectionMode") -->
    </umam:GetNewestEmail>
  </Sequence>
</Activity>
```

**Key patterns:**
- `ConnectionId` attribute holds the Integration Service connection GUID
- Nullable properties use `{x:Null}` explicitly
- Complex sub-objects (MailFolderArgument, MailboxArgument) with `BackupSlot` pattern
- `x:Reference` / `x:Name` for cross-referencing objects within the XAML
- Multiple package-specific xmlns prefixes (`umam`, `umame`, `umamm`, `usau`)

### Example 3: Integration Service `ConnectorActivity`

The generic IS `ConnectorActivity` pattern — activity shape, worked example, editing rules, JIT-generated assemblies: [../is-connector-xaml-guide.md](../is-connector-xaml-guide.md).

## Property Binding: Attributes vs Child Elements

XAML properties can be set in two ways: as XML attributes or as child elements. Both are valid XAML, but some properties only work reliably in one form.

### Attribute Syntax (Inline)
```xml
<ui:LogMessage Message="[myVar]" Level="Info" />
```

### Child Element Syntax (Property Element)
```xml
<ui:SomeActivity>
  <ui:SomeActivity.Result>
    <OutArgument x:TypeArguments="x:String">[outputVar]</OutArgument>
  </ui:SomeActivity.Result>
</ui:SomeActivity>
```

### When to Use Which

**Simple values** (strings, enums, booleans, VB expressions in brackets) almost always work as attributes:
```xml
DisplayName="My Activity" Message="[variable]" Level="Info"
```

**Output properties** (`OutArgument`, `Result`) may require child element syntax. Some activities accept `Result="[var]"` as an attribute; others only work with the expanded child element form. If an attribute-form output binding causes a validation error, try the child element form.

**Complex objects** (BackupSlot, MailboxArgument, ActivityAction, dictionaries) always require child element syntax — they cannot be expressed as a single attribute value.

**Strings containing literal `[` or `]`** (e.g., UIA special-key tokens like `[k(enter)]`, `[d(ctrl)]`, `[u(ctrl)]`) require child element syntax. The attribute form `Foo="[&quot;…[k(enter)]&quot;]"` runs correctly because the runtime VB compiler reads quoted string literals correctly, but the literal brackets inside the string collide with the outer `[ … ]` VB expression markers and the value will not render in Studio. See [../ui-automation-guide.md § XAML-Specific Pitfalls](../ui-automation-guide.md) (NTypeInto special-key tokens).

### Version-Sensitive Properties

Properties may exist in one package version but not another. If `validate` reports "Could not find member 'PropertyName'":
1. The property may not exist in the installed package version — remove it
2. The property may have been renamed between versions — check examples from the same package version
3. Use `uip rpa activities get-default-xaml` output as the authoritative set of properties for the installed version

# Project Analysis Guide

File-by-file extraction reference for analyzing a UiPath project. Follow Steps 1-5 in order. Each step produces signals that feed into the [extraction-mapping-guide.md](extraction-mapping-guide.md) tables.

## Step 1 -- Locate and Read project.json

Read `project.json` in the project root directory. Extract these fields:

| Field | Path in JSON | Extraction Purpose |
|-------|-------------|-------------------|
| Project name | `name` | Genome file name. Slugify: "InvoiceProcessing" -> `invoice-processing-genome.md` |
| Entry point | `main` | Starting workflow file path |
| Additional entry points | `entryPoints` | Multi-entry-point detection. Each entry has `filePath`, `input`, `output` |
| Package dependencies | `dependencies` | Keys are package IDs (e.g., `UiPath.Excel.Activities`). Map to target applications |
| Output type | `designOptions.outputType` | `Process`, `Library`, or `Tests` |
| Expression language | `expressionLanguage` | `VisualBasic` or `CSharp`. Determines how to read expressions in XAML |
| Target framework | `targetFramework` | `Windows` or `Portable` (cross-platform) |
| Attended flag | `runtimeOptions.isAttended` | Whether this is an attended automation |
| User interaction | `runtimeOptions.requiresUserInteraction` | Whether the automation requires user interaction |
| Global handler | `globalHandler` | File path to global error handler (if present) |

**Fallback rule:** If `project.json` is not found, scan for `.xaml` and `.cs` files directly. Flag the genome with `*[Inferred from project signals]*` for any metadata that would have come from `project.json` (name, output type, expression language, target framework).

## Step 2 -- Build File Inventory

Scan the project directory and classify every file into one of these categories:

| File Pattern | Category | Analysis Step |
|-------------|----------|---------------|
| `*.xaml` | XAML workflows | Step 3 |
| `*.cs` (user code) | Coded workflows | Step 4 |
| `*.cs.json` | Coded workflow metadata | Read for argument definitions and display names |
| `*.flow` | Maestro flow definitions | Step 5 |

### Exclusion Rules

Skip these directories entirely -- they contain auto-generated content, not user logic:

1. **`.local/`** -- Local cache (package restore, compiled artifacts)
2. **`.objects/`** -- Build output cache
3. **`.codedworkflows/`** -- Auto-generated coded workflow support files (boilerplate)

### Red Flag File Names

If you encounter these files, they are auto-generated boilerplate. Do not extract workflow logic from them:

- `CodedWorkflow.cs` -- Base class boilerplate
- `ConnectionsManager.cs` -- Auto-generated connection factory
- `ConnectionsFactory.cs` -- Auto-generated connection instances
- `ObjectRepository.cs` -- Auto-generated object repository
- `WorkflowRunnerService.cs` -- Auto-generated workflow runner

### Safe to Read

- **`.cs.json` files** are safe to read. They contain argument definitions (names, types, directions) and display names for coded workflows -- not auto-generated logic.

## Step 3 -- XAML File Analysis

For each `.xaml` file in the inventory, extract these signals:

| Signal | Where in XAML | What It Tells You | Example |
|--------|--------------|-------------------|---------|
| Workflow type | Root element inside `<Activity>` | Overall control flow pattern | `<Sequence>`, `<Flowchart>`, `<StateMachine>` |
| Activity packages | `xmlns` declarations on root `<Activity>` element | Which packages are used (for target app detection) | `xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail;..."` |
| Workflow steps | Activity elements in the body | What the workflow does at each step | `<ui:TypeInto>`, `<umam:GetNewestEmail>`, `<p:ReadRange>` |
| Arguments | `<x:Members>` block with `<x:Property>` elements | Input/output interface of the workflow | `Type="InArgument(x:String)"` = input, `OutArgument` = output, `InOutArgument` = both |
| Business rules | `<If>`, `<Switch>`, `<FlowDecision>` elements | Conditional logic and decision points | `Condition="[Amount > 10000]"` |
| Error handling | `<TryCatch>`, `<RetryScope>` elements | How failures are handled | `<Catch x:TypeArguments="s:TimeoutException">` |
| IS connections (package) | `ConnectionId` attribute on activity elements | Integration Service connection present | `ConnectionId="6265de1b-4264-ed11-ade6-e42aac668fcd"` |
| IS connections (connector) | `<isactr:ConnectorActivity>` elements | Integration Service connector activity | `xmlns:isactr="http://schemas.uipath.com/workflow/integration-service-activities/isactr"` |
| Variables | `<Variable>` elements in `.Variables` blocks | Data flow within the workflow | `<Variable x:TypeArguments="x:String" Name="filePath" />` |
| Call graph edges | `<InvokeWorkflowFile>` with `FileName` attribute | Which workflows call which other workflows | `FileName="ProcessInvoice.xaml"` |

### Critical: What to Skip in XAML

- **`<sap2010:WorkflowViewState.ViewStateManager>`** -- Skip this entire section. It contains designer layout metadata (positions, sizes, colors). It is not logic.
- **`xmlns` declarations as workflow steps** -- Use `xmlns` only to identify which packages are in use (for target app detection). They are namespace plumbing, not actions the workflow performs.

### Resolving Integration Service Connections

`ConnectionId` is a GUID that does not reveal the service name. To determine the actual target application:

1. Check the `xmlns` namespace of the activity element -- e.g., `umam:GetNewestEmail` with `xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail;..."` indicates Outlook/Office 365
2. Check the activity class name -- e.g., `GetNewestEmail` in the `MicrosoftOffice365` namespace indicates email
3. For `isactr:ConnectorActivity`, check `UiPathActivityTypeId` and the `xmlns` imports for the connector-specific namespace to identify the service

## Step 4 -- Coded Workflow Analysis (.cs Files)

For each `.cs` file in the inventory (excluding auto-generated files per Step 2 exclusion rules), extract these signals:

| Signal | Code Pattern | What It Tells You | Example |
|--------|-------------|-------------------|---------|
| Workflow entry | `[Workflow]` attribute on class or method | This file is a workflow entry point | `[Workflow] public void Execute()` |
| Test case | `[TestCase]` attribute | This is a test case, not a business workflow. Skip for genome extraction | `[TestCase] public void Execute()` |
| Target applications | Service property usage: `system.`, `excel.`, `office365.`, `testing.` | Which applications and services the workflow interacts with | `excel.ReadRange(...)`, `office365.Mail(conn).SendEmail(...)` |
| IS connections | `connections.*` property usage | Integration Service connections in use. Service name is visible in the property chain | `connections.O365Mail.My_Workspace` |
| Call graph edges | `workflows.*` method calls | Which workflows this file invokes | `workflows.ProcessInvoice(id: "INV-001")` |
| Error handling | `try/catch` blocks with exception types | How failures are handled | `catch (TimeoutException ex)` |
| Business rules | `if`, `switch`, `foreach`, `while` with business-relevant conditions | Decision logic and iteration patterns | `if (amount > threshold)` |
| Data flow | Method signatures, return types, parameter types | What data enters and leaves the workflow | `public (bool success, string message) Execute(string invoiceId)` |
| Orchestrator API | `BuildClient("Orchestrator")` | Direct Orchestrator API interaction | `var client = BuildClient("Orchestrator");` |

### .cs.json Metadata Files

For each `.cs.json` file, read the argument definitions:
- `arguments` array with `name`, `type`, `direction` for each argument
- `displayName` for the human-readable workflow name

These complement the `.cs` file analysis by providing the formal argument interface without parsing the C# method signatures.

## Step 5 -- Flow File Analysis (.flow JSON)

For each `.flow` file, extract these signals:

| Signal | Where in JSON | What It Tells You | Example |
|--------|--------------|-------------------|---------|
| Flow steps | `nodes` array | Each node is a step in the orchestration | `{ "type": "core.action.script", "display": { "label": "Roll Dice" } }` |
| Step type | `nodes[].type` | What kind of step this is | `core.action.script`, `core.action.invoke`, `core.action.http` |
| Step ordering | `edges` array | Source-to-target connections define execution flow | `{ "sourceNodeId": "start", "targetNodeId": "processData" }` |
| Embedded logic | `nodes[].inputs.script` in script nodes | Business logic embedded in the flow | `return { total: items.reduce((s,i) => s + i.amount, 0) };` |
| Variables | `variables` object | Data definitions and flow state | Named variables with types |
| Decision logic | `core.logic.decision` and `core.logic.switch` nodes | Branching and routing logic | Decision nodes with `expression` inputs |
| Connector bindings | `bindings` array or `bindings_v2.json` | Integration Service connections used by the flow | Connection resources with `metadata.Connector` identifying the service |
| Entry point | `core.trigger.manual` node with `model.entryPointId` | Where the flow starts | Start node linked to `entry-points.json` |

## Building the Call Graph

After analyzing all files, construct the workflow execution order:

1. **Start from the entry point.** Read the `main` field in `project.json` to identify the starting workflow file.
2. **Follow XAML invocations.** In XAML files, read `<InvokeWorkflowFile>` elements and extract the `FileName` attribute to find called workflows.
3. **Follow coded workflow invocations.** In `.cs` files, read `workflows.*` method calls to find called workflows.
4. **Order by call chain depth.** Use depth-first traversal from the entry point. The entry point is step 1, its first invocation is step 2, and so on.
5. **Handle parallel branches.** When a workflow invokes multiple sub-workflows at the same level, order them by their position in the calling workflow (top-to-bottom for Sequences, left-to-right for Flowcharts).
6. **Handle missing entry points** (check `outputType` and `entryPoints` in project.json):
   - `outputType: Library` -- Treat all public workflows as independent capabilities. List each in the Workflow section.
   - `outputType: Process` without a `main` field -- Look for `Main.xaml` or `Main.cs` by convention. If not found, order alphabetically and flag with `*[Inferred from project signals]*`.
   - `outputType: Tests` -- Skip test files (`[TestCase]` attribute). Extract only workflows marked with `[Workflow]`.

---

After completing all 5 steps, use [extraction-mapping-guide.md](extraction-mapping-guide.md) to map these signals to genome sections.

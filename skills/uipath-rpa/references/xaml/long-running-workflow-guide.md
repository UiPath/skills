# Long Running Workflow (ProcessDiagram) Guide

Package, node vocabulary, gateway patterns, and suspend/resume for Long Running Workflows. Related references: XAML anatomy → [xaml-basics-and-rules.md § Long Running Workflow](xaml-basics-and-rules.md); layout + ViewState → [canvas-layout-guide.md § 5](canvas-layout-guide.md); node registration → [common-pitfalls.md § x:Reference](common-pitfalls.md#xreference--__referenceid-naming).

## When to Use LRW

| Requirement | Workflow type |
|-------------|---------------|
| Linear steps, completes in one run | Sequence |
| Branching/looping logic, in-memory, completes in one run | Flowchart |
| Distinct states with transitions (e.g. REFramework) | State Machine |
| Human tasks, long waits (hours–weeks), suspend/resume, parallel branch coordination, BPMN-style modeling | **Long Running Workflow** (`upa:ProcessDiagram`) |

## Required Package

LRW node types ship in **`UiPath.FlowchartBuilder.Activities`** (runtime assembly `UiPath.Process.Activities` — the `upa`/`upas` xmlns target). Mandatory dependency for any workflow containing `upa:ProcessDiagram`; the runtime pair `UiPath.FlowchartBuilder.Activities.Runtime` resolves automatically. Not supported on `targetFramework: "Legacy"`. Studio creates LRW projects with this package plus `UiPath.System.Activities`.

Install per Common Rule 6 and SKILL.md § Resolving Packages before authoring:

```bash
uip rpa packages versions --package-id UiPath.FlowchartBuilder.Activities --include-prerelease --project-dir "<PROJECT_DIR>" --output json
uip rpa packages install --packages '[{"id":"UiPath.FlowchartBuilder.Activities","version":"<LATEST_VERSION>"}]' --project-dir "<PROJECT_DIR>" --output json
```

BPMN import (`.bpmn` → ProcessDiagram, Studio wizard) requires version 1.0.4 or later.

**Discovery commands do not see LRW nodes.** `upa:` node types are diagram nodes, not activities — `activities find` returns nothing for them and `activities get-default-xaml --activity-class-name "UiPath.Process.Activities.SplitNode"` fails with `TypeLoadException`. The package also ships no `.local/docs`. Author nodes structurally from this guide's vocabulary and patterns; do NOT burn calls on Rule 21 discovery for `upa:` types. Activities *inside* a TaskNode body (Sequence content) follow normal Rule 21 discovery.

## Node Vocabulary

Class names below live in namespace `UiPath.Process.Activities` (prefix `upa:`); `DesignerMetadata` in `UiPath.Process.Activities.Shared` (prefix `upas:`). Every node has `Behavior` (a `NodeBehavior` carrying `DesignerMetadata NodeType="<string>"` — controls the canvas shape/icon) and `DisplayName`.

| Canvas name | XAML element | Behavior class | NodeType | Notes |
|-------------|--------------|----------------|----------|-------|
| Manual Trigger (start) | `upa:EventNode` | `upa:StartBehavior` | `StartEvent.Interrupting.None` | One start node required; `ProcessDiagram.StartNode` points to it |
| On a Schedule (start) | `upa:EventNode` | `upa:StartBehavior` | `StartEvent.Interrupting.Timer` | |
| On App Trigger (start) | `upa:EventNode` | `upa:StartBehavior` | `StartEvent.Interrupting.Message` | |
| Sequence (task) | `upa:TaskNode` | `upa:NodeBehavior` | `Task.None` | Body = a `Sequence` activity (the node's `Action`); `Next` to following node |
| Human Approval | `upa:TaskNode` | `upa:NodeBehavior` | `Task.User` | Body holds persistence activities — see § Suspend/Resume |
| Process (agentic) | `upa:TaskNode` | `upa:NodeBehavior` | `Task.Agentic` | |
| Business Rule | `upa:TaskNode` | `upa:NodeBehavior` | `Task.BusinessRule` | |
| Wait for Trigger | `upa:TaskNode` | `upa:NodeBehavior` | `Task.Receive` | |
| Activity (send) | `upa:TaskNode` | `upa:NodeBehavior` | `Task.Send` | |
| Invoke Workflow | `upa:TaskNode` | `upa:NodeBehavior` | `Task.Service` | Body wraps `InvokeWorkflowFile` |
| Subprocess | `upa:SubProcessNode` | `upa:NodeBehavior` | `Task.Subprocess` | |
| Detached Error Handler | `upa:EventSubProcessNode` | `upa:NodeBehavior` on the node; `upa:StartOnParentErrorBehavior` (`ExceptionType`) on the inner diagram's start | `Task.EventSubprocess` | In `ProcessDiagram.EventSubProcesses`, not `Nodes`; `Action` = inner `ProcessDiagram` — see § Detached Error Handler |
| Decision (gateway) | `upa:DecisionNode` | — | — | `Condition` (`Activity<Boolean>`), `True`/`False` branch properties |
| Switch (gateway) | `upa:SwitchNode` (`x:TypeArguments`) | — | — | `Expression`, `Cases` (keyed children), `Default` — see § Gateway Patterns |
| Split (gateway) | `upa:SplitNode` | — | — | `Branches` collection of parallel next nodes |
| Merge (gateway) | `upa:MergeNode` | `upa:MergeAllBehavior` or `upa:MergeFirstBehavior` | — | All = wait for every incoming branch; First = continue on first, cancel others |
| Event Placeholder | `upa:EventNode` | `upa:IntermediateBehavior` | `IntermediateEvent.Throw.None` | Intermediate marker; convert to a catch event below |
| Resume after Delay | `upa:EventNode` | `upa:IntermediateBehavior` | `IntermediateEvent.Catch.Timer` | Body holds `Resume After Delay` persistence activity |
| Wait for Message | `upa:EventNode` | `upa:IntermediateBehavior` | `IntermediateEvent.Catch.Message` | |
| Error Handler (boundary) | `upa:BoundaryNode` | `upa:CatchMostSpecificErrorBehavior` (`ExceptionType`) | `BoundaryEvent.Interrupting.Error` | Attached via `upa:TaskNode.BoundaryNodes`; own `Next` chain |
| End | `upa:EndNode` | `upa:EndBehavior` | `EndEvent.None` | |
| Throw (end) | `upa:EndNode` | `upa:EndBehavior` | `EndEvent.Error` | Body (`Action`) holds a `Throw` |
| Terminate (end) | `upa:EndNode` | `upa:EndBehavior` | `EndEvent.Terminate` | Body holds `upa:TerminateProcessDiagram` |

`ProcessDiagram` root properties: `StartNode`, `Nodes` (content collection — registration target for `x:Reference`), `EventSubProcesses`, `Variables` (diagram-scoped variables), `ValidateUnconnectedNodes`.

## Choosing Nodes

NodeType drives the canvas icon and diagram readability — model intent, don't default everything to a plain sequence box.

### Task steps — assigning a NodeType per step is MANDATORY, before authoring

1. Before writing XAML, map every task step in the plan to a row of this table.
2. `Task.None` is permitted ONLY for steps matching no other row — generic scripted logic. Checks, validations, sends, invokes, waits, approvals all have a specific row.
3. After authoring, audit the file: for each `NodeType="Task.None"`, confirm no other row fits. A diagram where most tasks are `Task.None` is mis-modeled, not neutral — the canvas renders unreadable uniform boxes.

| Step semantics | NodeType |
|----------------|----------|
| Human decision/input (Action Center task) | `Task.User` |
| Body is `InvokeWorkflowFile` to another workflow | `Task.Service` |
| Check / rule evaluation / classification / data validation | `Task.BusinessRule` |
| Agent step | `Task.Agentic` |
| Waits on an inbound trigger/message | `Task.Receive` |
| Sends to an external system (notification, email, API call) | `Task.Send` |
| Generic scripted logic matching no row above | `Task.None` |

### Task body contents — regular activities or invokes

The `Sequence` inside a TaskNode is a **normal activity container** — author its contents with the standard activity rules (common-activity-card fast path, Rule 21 discovery for everything else, IS connector activities, persistence activities). Two patterns:

- **Inline** — few activities, specific to this step (log, assign, one connector call): put them directly in the body `Sequence`.
- **Invoke** — multi-step or reusable business logic: put it in a separate `.xaml` and call it via `InvokeWorkflowFile` (`Task.Service`). Keeps the diagram readable; the invoked workflow is a normal Sequence/Flowchart authored per the standard XAML rules.

### Gateways — exclusive vs parallel

| Need | Gateway |
|------|---------|
| Two paths, boolean condition | `DecisionNode` (`Condition`, `True`/`False`) |
| 3+ exclusive paths routed by one value | `SwitchNode<T>` (`Expression`, `Cases`, `Default`) |
| Paths that ALL run, concurrently | `SplitNode` → branches → `MergeNode` |
| Continue when every parallel branch finishes | `MergeNode` + `MergeAllBehavior` |
| Continue on first finisher, cancel the rest (race/timeout patterns) | `MergeNode` + `MergeFirstBehavior` |

Decision/Switch branches are exclusive — exactly one path executes. Split branches are parallel — all paths execute. Don't model an either/or with Split.

### Error handling — three scopes plus end semantics

| Scope | Mechanism | Use when |
|-------|-----------|----------|
| Inside one step | `TryCatch` in the task's body `Sequence` | Error is handled and the step continues/retries — flow unaffected |
| One node | `upa:BoundaryNode` on `TaskNode.BoundaryNodes` (`CatchMostSpecificErrorBehavior`, `ExceptionType`) | A specific task's failure diverts flow to a recovery path (own `Next` chain) |
| Whole diagram | `upa:EventSubProcessNode` (Detached Error Handler) in `ProcessDiagram.EventSubProcesses` — § Detached Error Handler | Any unhandled error anywhere triggers a shared handler (notify, compensate) |
| End with failure | `EndNode` `EndEvent.Error` + `Throw` in body | Path reached a business/system failure — fail the job |
| Hard stop | `EndNode` `EndEvent.Terminate` + `upa:TerminateProcessDiagram` in body | Abort everything immediately, including running parallel branches |

A plain `EndNode` (`EndEvent.None`) ends only its own path; parallel branches keep running.

### Events

| Need | Node |
|------|------|
| Start manually / on schedule / on app message | `EventNode` + `StartBehavior` (`StartEvent.Interrupting.{None,Timer,Message}`) |
| Pause mid-flow for a duration | `EventNode` + `IntermediateBehavior` `IntermediateEvent.Catch.Timer` (Resume after Delay) |
| Pause mid-flow until an external signal | `EventNode` + `IntermediateBehavior` `IntermediateEvent.Catch.Message` (Wait for Message) |
| Pause for a human task | `Task.User` TaskNode with persistence activities — § Suspend/Resume |
| Group a reusable sub-flow inside the diagram | `upa:SubProcessNode` (`Task.Subprocess`) |

## Gateway Patterns

Skeletons below omit per-node ViewState (`ShapeLocation`/`ShapeSize`/`ConnectorLocation`) — generate it per [canvas-layout-guide.md § 5](canvas-layout-guide.md) (Rule 20). `SwitchNode` branch connectors reuse the FlowSwitch ViewState key convention (`Default`, `{caseKey}Connector`). Standard root xmlns per [xaml-basics-and-rules.md](xaml-basics-and-rules.md) plus:

```xml
xmlns:upa="clr-namespace:UiPath.Process.Activities;assembly=UiPath.Process.Activities"
xmlns:upas="clr-namespace:UiPath.Process.Activities.Shared;assembly=UiPath.Process.Activities"
```

### Split / Merge (parallel branches)

`SplitNode.Branches` holds the first node of each parallel path. Each branch chain ends by pointing `Next` at the shared `MergeNode` — define the merge inline in one branch, `x:Reference` it from the others. Inline-defined nodes need trailing `<x:Reference>` registration as direct children of `<upa:ProcessDiagram>` (same rule as Flowchart).

**Branch nodes count as inline — register them.** A TaskNode defined inside `<upa:SplitNode.Branches>` MUST also appear as a trailing `<x:Reference>` direct child of the diagram. `validate` AND `build` pass without the registration; the Studio canvas then crashes opening the file (`Value cannot be null` in `FlowSplitBehavior.AddToDesigner`). Exempt collections that are a node's own home — `TaskNode.BoundaryNodes`, `ProcessDiagram.EventSubProcesses` — never get diagram-level registration.

```xml
<upa:SplitNode x:Name="__ReferenceID1" DisplayName="Split">
  <upa:SplitNode.Branches>
    <upa:TaskNode x:Name="__ReferenceID2" DisplayName="Branch A">
      <upa:TaskNode.Behavior>
        <upa:NodeBehavior>
          <upa:NodeBehavior.DesignerMetadata>
            <upas:DesignerMetadata NodeType="Task.None" />
          </upa:NodeBehavior.DesignerMetadata>
        </upa:NodeBehavior>
      </upa:TaskNode.Behavior>
      <Sequence DisplayName="Branch A Steps">
        <!-- activities -->
      </Sequence>
      <upa:TaskNode.Next>
        <upa:MergeNode x:Name="__ReferenceID4" DisplayName="Merge">
          <upa:MergeNode.Behavior>
            <upa:MergeAllBehavior />
          </upa:MergeNode.Behavior>
          <upa:MergeNode.Next>
            <!-- next node after merge -->
          </upa:MergeNode.Next>
        </upa:MergeNode>
      </upa:TaskNode.Next>
    </upa:TaskNode>
    <upa:TaskNode x:Name="__ReferenceID3" DisplayName="Branch B">
      <!-- Behavior + body as above -->
      <upa:TaskNode.Next>
        <x:Reference>__ReferenceID4</x:Reference>
      </upa:TaskNode.Next>
    </upa:TaskNode>
  </upa:SplitNode.Branches>
</upa:SplitNode>
<!-- trailing registration on ProcessDiagram: __ReferenceID2, __ReferenceID3, __ReferenceID4, ... -->
```

### Switch (multi-way routing)

`x:TypeArguments` on the node; `Cases` entries are keyed child nodes (`x:Key`); `Default` is a separate branch property.

```xml
<!-- standard xmlns omitted -->
<upa:SwitchNode x:TypeArguments="x:String" x:Name="__ReferenceID1" DisplayName="Route">
  <upa:SwitchNode.Expression>
    <mva:VisualBasicValue x:TypeArguments="x:String">[routeVar]</mva:VisualBasicValue>
  </upa:SwitchNode.Expression>
  <upa:SwitchNode.Cases>
    <upa:TaskNode x:Key="approve" x:Name="__ReferenceID2" DisplayName="Approve Path">
      <!-- Behavior + body + Next -->
    </upa:TaskNode>
  </upa:SwitchNode.Cases>
  <upa:SwitchNode.Default>
    <upa:TaskNode x:Name="__ReferenceID4" DisplayName="Default Path">
      <!-- Behavior + body + Next -->
    </upa:TaskNode>
  </upa:SwitchNode.Default>
</upa:SwitchNode>
```

`DecisionNode` is the boolean special case: `Condition` instead of `Expression`, `True`/`False` instead of `Cases`/`Default` — full snippet in [canvas-layout-guide.md § 5](canvas-layout-guide.md).

### Detached Error Handler (event subprocess)

A diagram-wide handler is an **event subprocess**: the node's `Action` is an inner `ProcessDiagram` whose start event carries the error trigger. Behavior placement is the trap — `StartOnParentErrorBehavior` derives `NodeBehavior<EventNode>`, so it goes on the **inner diagram's start EventNode**, never on the `EventSubProcessNode` itself (that cast-fails). The outer node takes plain `NodeBehavior`.

```xml
<!-- standard xmlns omitted; also: xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib" -->
<upa:ProcessDiagram.EventSubProcesses>
  <upa:EventSubProcessNode x:Name="__ReferenceID16" DisplayName="Unhandled Error Handler">
    <upa:EventSubProcessNode.Behavior>
      <upa:NodeBehavior>
        <upa:NodeBehavior.DesignerMetadata>
          <upas:DesignerMetadata NodeType="Task.EventSubprocess" />
        </upa:NodeBehavior.DesignerMetadata>
      </upa:NodeBehavior>
    </upa:EventSubProcessNode.Behavior>
    <upa:EventSubProcessNode.Action>
      <upa:ProcessDiagram DisplayName="Error Handler Sub">
        <upa:ProcessDiagram.StartNode>
          <x:Reference>__ReferenceID17</x:Reference>
        </upa:ProcessDiagram.StartNode>
        <upa:EventNode x:Name="__ReferenceID17" DisplayName="On Error">
          <upa:EventNode.Behavior>
            <upa:StartOnParentErrorBehavior ExceptionType="s:Exception">
              <upa:StartOnParentErrorBehavior.DesignerMetadata>
                <upas:DesignerMetadata NodeType="StartEvent.Interrupting.Error" />
              </upa:StartOnParentErrorBehavior.DesignerMetadata>
            </upa:StartOnParentErrorBehavior>
          </upa:EventNode.Behavior>
          <upa:EventNode.Next>
            <upa:TaskNode x:Name="__ReferenceID18" DisplayName="Log Incident">
              <!-- Behavior (Task.None) + body Sequence with handler activities -->
            </upa:TaskNode>
          </upa:EventNode.Next>
        </upa:EventNode>
        <x:Reference>__ReferenceID18</x:Reference>
      </upa:ProcessDiagram>
    </upa:EventSubProcessNode.Action>
  </upa:EventSubProcessNode>
</upa:ProcessDiagram.EventSubProcesses>
```

Validation errors that mean a placement mistake:

| Error | Cause → fix |
|-------|-------------|
| `EventSubProcessNode.Action must be of type ProcessDiagram` | `Action` holds a `Sequence` → wrap handler in an inner `ProcessDiagram` |
| `Unable to cast ... EventSubProcessNode to ... EventNode` | `StartOnParentErrorBehavior`/`StartSubProcessBehavior` set on the outer node → move to the inner start `EventNode`; outer takes plain `NodeBehavior` |
| `SubProcess.StartNode must have a StartSubProcessBehavior behavior` | Inner start has `StartBehavior` → use `StartOnParentErrorBehavior` (error trigger) or `StartSubProcessBehavior` |
| `Cannot set unknown member EventSubProcessNode.Next` | Event subprocesses are detached — no `Next`; flow never routes into them |

`ProcessDiagram` has no `EventHandlers`/`ErrorHandler` property — `EventSubProcesses` is the only diagram-level hook.

## Suspend/Resume (Persistence)

Wait steps suspend the job, serialize state, and **release the robot** — the process resumes (possibly on another robot) when the awaited task completes, a message arrives, or the delay elapses. Waits can span hours to weeks. Activities ship in **`UiPath.Persistence.Activities`** (separate package — install like FlowchartBuilder above):

| Activity | Purpose |
|----------|---------|
| `CreateFormTask` / `WaitForFormTaskAndResume` | Action Center form task (human approval/input) |
| `CreateExternalTask` / `WaitForExternalTaskAndResume` | External system completes the task |
| `ResumeAfterDelay` | Timer suspension |

Place create+wait inside the body of a Human Approval TaskNode (`Task.User`). xmlns:

```xml
xmlns:upae="clr-namespace:UiPath.Persistence.Activities.ExternalTask;assembly=UiPath.Persistence.Activities"
xmlns:upamt="clr-namespace:UiPath.Persistence.Activities.Model.Task;assembly=UiPath.Persistence.Activities"
```

```xml
<!-- inside a Task.User TaskNode's Sequence; taskObj: ProcessDiagram.Variables, type upae:ExternalTaskData -->
<upae:CreateExternalTask ExternalTag="{x:Null}" Labels="{x:Null}" TaskCatalog="{x:Null}" TimeoutMs="{x:Null}"
                         DisplayName="Create External Task" TaskTitle="Approve order"
                         TaskOutput="[taskObj]" TaskPriority="[TaskPriority.Medium]">
  <upae:CreateExternalTask.TaskData>
    <scg:Dictionary x:TypeArguments="x:String, Argument" />
  </upae:CreateExternalTask.TaskData>
</upae:CreateExternalTask>
<upae:WaitForExternalTaskAndResume StatusMessage="{x:Null}" TaskAction="{x:Null}" TimeoutMs="{x:Null}" WaitItemDataObject="{x:Null}"
                                   DisplayName="Wait For External Task and Resume"
                                   TaskInput="[taskObj]" TaskOutput="[taskObj]" />
```

Rules:

1. **VB variable bindings on persistence activities: bracket attribute form only** (`TaskOutput="[taskObj]"`). Element-form `<mva:VisualBasicReference>` inside `OutArgument` fails `validate` with `Failed to create a 'VisualBasicReference'`. Plain-enum attribute form is also valid where the starter emits it (`TaskPriority="Medium"`).
2. **Discover the installed version's property surface with `activities find` + `activities get-default-xaml`** (persistence activities are normal activities, unlike `upa:` nodes) and prefer the returned starter — newer package versions add properties the snippet above omits (`Group`, `UserNameOrEmail`, an `AssignmentCriteria` block requiring `xmlns:upat="clr-namespace:UiPath.Persistence.Activities.Tasks;assembly=UiPath.Persistence.Activities"`). The package generates no `.local/docs` and has no bundled fallback under `references/activity-docs/`.
3. Add `UiPath.Persistence.Activities` to `TextExpression.ReferencesForImplementation` and its namespaces to `NamespacesForImplementation` when expressions use its types (`ExternalTaskData`, `TaskPriority`).
4. Suspension at runtime requires `runtimeOptions.supportsPersistence: true` in `project.json` (Studio's "Supports Persistence" project setting). `build` passes either way — the flag gates Orchestrator suspension, not compilation.
5. **Register every file containing a Wait-and-Resume activity in `project.json` → `entryPoints`** — analyzer ST-DBP-024 (surfaces in `build` as `Unsupported usage of persistence activities`) allows suspension only in entry-point files. Same `entryPoints` array schema as [../../assets/json-template.md](../../assets/json-template.md); it applies to XAML files here, not only coded workflows.

## Diagram Validation Rules

The designer canvas enforces these; **CLI `validate` and `build` do NOT** — a dangling split branch compiles with only warnings. Author correctly by construction:

1. Exactly one start node, referenced by `ProcessDiagram.StartNode`.
2. Every node connected — no unreachable nodes (`ValidateUnconnectedNodes`).
3. `DecisionNode` requires `Condition`; `SwitchNode` requires `Expression`.
4. Every `SplitNode` pairs with exactly one `MergeNode`; every `MergeNode` has an upstream `SplitNode`; all split branches converge on the same merge.
5. A node cannot be shared across branches (except the merge target).
6. Boundary error handlers: no duplicate `ExceptionType` on one node; `ExceptionType` must be specified (attribute form: `ExceptionType="s:Exception"`).

**Expected warning — do not "fix":** `build` emits `unreachable code` warnings for every node downstream of a `SplitNode`, including correctly converged split/merge wiring — static analysis does not trace `Branches`. The warning is noise for LRW diagrams, not a wiring defect.

## BPMN Import

Studio imports `.bpmn` files as ProcessDiagrams (Import Workflow wizard); unsupported BPMN elements get warning markers and must be replaced with supported node types. For authoring `.bpmn` directly, this skill does not apply.

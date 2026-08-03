# Flowchart Guide

Node vocabulary, structure, and wiring for `<Flowchart>` workflows. Related references: XAML anatomy → [xaml-basics-and-rules.md](xaml-basics-and-rules.md); layout + ViewState → [canvas-layout-guide.md § 3](canvas-layout-guide.md#3-flowchart-layout); node registration full rules → [common-pitfalls.md § x:Reference](common-pitfalls.md#xreference--__referenceid-naming).

## When to Use a Flowchart

Branching logic with multiple decision points, loops, and back-edges. Best when the flow is a graph rather than a straight sequence. For straight-line steps use a `Sequence`; for state-driven processes use a State Machine; for BPMN-style event-driven long waits use a Long Running Workflow (ProcessDiagram).

## Node Vocabulary

| Node | Purpose | Successor wiring |
|------|---------|------------------|
| `FlowStep` | Wraps **exactly one** activity (which may be a container). The unit of work. | `FlowStep.Next` → one node |
| `FlowDecision` | Boolean branch. `Condition` plus `True`/`False` targets. | `FlowDecision.True` / `.False` → one node each |
| `FlowSwitch<T>` | Multi-way branch keyed by an expression. | `Default` plus one target per case |

A `FlowStep` wraps one activity. If that activity is a container (`Sequence`, `NApplicationCard`, `TryCatch`), its children stay nested and are NOT separate nodes. See [canvas-layout-guide.md § What Counts as a Node](canvas-layout-guide.md#3-flowchart-layout).

## Structure & Wiring

**Rule:** every `FlowStep`/`FlowDecision`/`FlowSwitch` is a **direct child of `<Flowchart>`** with an `x:Name`. Links between nodes are made with `<x:Reference>__ReferenceIDn</x:Reference>` inside property elements (`Flowchart.StartNode`, `FlowStep.Next`, `FlowDecision.True`/`.False`) — never by physically nesting one node inside another.

```xml
<Flowchart DisplayName="My Flowchart" sap2010:WorkflowViewState.IdRef="Flowchart_1">
  <Flowchart.StartNode>
    <x:Reference>__ReferenceID0</x:Reference>
  </Flowchart.StartNode>
  <FlowStep x:Name="__ReferenceID0">
    <ui:LogMessage DisplayName="Step 1" />
    <FlowStep.Next>
      <x:Reference>__ReferenceID1</x:Reference>
    </FlowStep.Next>
  </FlowStep>
  <FlowDecision x:Name="__ReferenceID1">
    <FlowDecision.Condition>
      <CSharpValue x:TypeArguments="x:Boolean">condition</CSharpValue>
    </FlowDecision.Condition>
    <FlowDecision.True>
      <x:Reference>__ReferenceID0</x:Reference>
    </FlowDecision.True>
    <!-- FlowDecision.False omitted = end of flow -->
  </FlowDecision>
</Flowchart>
```

`__ReferenceID` values must be unique across the whole file. When adding nodes, use a number higher than any existing one.

## Node Registration

Only nodes in the `Flowchart.Nodes` collection render — and that collection is built from the **direct children** of `<Flowchart>`. A node that is not a direct child is never registered, so the designer does not draw it, regardless of ViewState.

Two cases:

1. **Direct children** of `<Flowchart>` — already registered. Do NOT also add a trailing `<x:Reference>`.
2. **Inline definitions** inside a property element (e.g., a `FlowStep` written inside `<FlowDecision.True>`) — MUST add a trailing `<x:Reference>` entry as a direct child of `<Flowchart>` to register them.

Full correct/wrong examples for inline registration: [common-pitfalls.md § x:Reference](common-pitfalls.md#xreference--__referenceid-naming).

### Forbidden — nested FlowStep chains

Do NOT build the flow by physically nesting each `FlowStep` inside the previous one's `<FlowStep.Next>` (a deep chain with only the first node under `<Flowchart.StartNode>`). Nested-only steps never enter `Flowchart.Nodes`, so the designer renders almost nothing — invisible regardless of ViewState. Wire successors by reference and keep every step a direct child.

**Correct** — each step a direct child, linked by reference:
```xml
<Flowchart sap2010:WorkflowViewState.IdRef="Flowchart_1">
  <Flowchart.StartNode>
    <x:Reference>__ReferenceID0</x:Reference>
  </Flowchart.StartNode>
  <FlowStep x:Name="__ReferenceID0">
    <ui:LogMessage DisplayName="Step 1" />
    <FlowStep.Next>
      <x:Reference>__ReferenceID1</x:Reference>
    </FlowStep.Next>
  </FlowStep>
  <FlowStep x:Name="__ReferenceID1">          <!-- direct child — in Flowchart.Nodes -->
    <ui:LogMessage DisplayName="Step 2" />
  </FlowStep>
</Flowchart>
```

**Wrong** — Step 2 nested inside Step 1's `.Next`; `Flowchart.Nodes` holds only Step 1, so Step 2 never renders:
```xml
<Flowchart sap2010:WorkflowViewState.IdRef="Flowchart_1">
  <Flowchart.StartNode>
    <x:Reference>__ReferenceID0</x:Reference>
  </Flowchart.StartNode>
  <FlowStep x:Name="__ReferenceID0">
    <ui:LogMessage DisplayName="Step 1" />
    <FlowStep.Next>
      <FlowStep>                              <!-- WRONG — nested, not registered -->
        <ui:LogMessage DisplayName="Step 2" />
      </FlowStep>
    </FlowStep.Next>
  </FlowStep>
</Flowchart>
```

### No Orphan Nodes

Every node except the start must be reachable: referenced by `Flowchart.StartNode`, a `FlowStep.Next`, or a decision/switch branch. A `FlowStep` with no incoming reference and no `FlowStep.Next` is an orphan — it renders as a disconnected box and is almost always a leftover. Do not generate them.

## Condition Expressions

`FlowDecision.Condition` and `FlowSwitch` expressions follow the project's expression language:

- **C# projects:** `<CSharpValue x:TypeArguments="x:Boolean">condition</CSharpValue>`
- **VB projects:** `<mva:VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="condition" />`

## Layout & ViewState

ViewState is **mandatory** for Flowcharts — without per-node `ShapeLocation`+`ShapeSize`, Studio stacks every node at (0,0) and they overlap into what looks like a single node (Studio does NOT auto-arrange on open). ViewState positions a node **only after** it is registered in `Flowchart.Nodes` — structure first, then coordinates.

Coordinate system, node sizes, connector routing, and full ViewState recipes: [canvas-layout-guide.md § 3](canvas-layout-guide.md#3-flowchart-layout). See also SKILL.md Rule 20.

# Canvas Layout Guide

How to generate ViewState for Flowchart, State Machine, and Long Running Workflow (ProcessDiagram) canvases so nodes render with a usable layout in UiPath Studio.

**When to generate ViewState:**
- **Sequences**: ViewState is optional — Studio auto-stacks children vertically. Only `IsExpanded=True` matters.
- **Flowcharts, State Machines, ProcessDiagrams**: ViewState is **mandatory** for usable layout. Without it, Studio stacks all nodes at (0,0).

---

## 1. Required XAML Namespaces

Add these to the root `<Activity>` element when generating ViewState:

```xml
xmlns:av="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
xmlns:sap="http://schemas.microsoft.com/netfx/2009/xaml/activities/presentation"
xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
```

| Prefix | Purpose |
|--------|---------|
| `av` | WPF types: `Point`, `Size`, `PointCollection` for coordinates |
| `sap` | `VirtualizedContainerService.HintSize`, `WorkflowViewStateService.ViewState` |
| `sap2010` | `WorkflowViewState.IdRef`, `ExpressionActivityEditor`, annotations |
| `scg` | `Dictionary` for ViewState storage |

For Long Running Workflows, also add:
```xml
xmlns:upa="clr-namespace:UiPath.Process.Activities;assembly=UiPath.Process.Activities"
xmlns:upas="clr-namespace:UiPath.Process.Activities.Shared;assembly=UiPath.Process.Activities"
```

---

## 2. ViewState System

Every activity gets an inline ViewState dictionary and a unique IdRef:

```xml
<FlowStep x:Name="__ReferenceID0" sap2010:WorkflowViewState.IdRef="FlowStep_1">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <av:Point x:Key="ShapeLocation">170,110</av:Point>
      <av:Size x:Key="ShapeSize">262,60</av:Size>
      <av:PointCollection x:Key="ConnectorLocation">300,170 300,220</av:PointCollection>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  <!-- activity content -->
</FlowStep>
```

### IdRef Naming

Format: `{ActivityTypeName}_{Counter}`. Counters are per-type and sequential within the file.

Examples: `Flowchart_1`, `FlowStep_1`, `FlowDecision_1`, `Assign_1`, `StateMachine_1`, `State_1`, `Transition_1`, `ProcessDiagram_1`, `EventNode_1`, `TaskNode_1`.

### HintSize

Every activity should have `sap:VirtualizedContainerService.HintSize` as an attribute (not in the ViewState dict):
```xml
<Assign sap:VirtualizedContainerService.HintSize="110,70" sap2010:WorkflowViewState.IdRef="Assign_1">
```

---

## 3. Flowchart Layout

### Coordinate System

- **Origin**: Top-left corner (0, 0)
- **X increases rightward**, **Y increases downward**
- `ShapeLocation` = top-left corner of the node's bounding box
- Units: WPF device-independent pixels (1/96 inch)

### Node Types and Default Sizes

| Node Type | Typical Size (W x H) | Shape |
|-----------|----------------------|-------|
| Start Node (Flowchart's own ViewState) | 50x50 or 60x75 | Circle at top |
| FlowStep (wraps any activity) | 110x70 to 262x60 | Rectangle |
| FlowDecision | 60x60 to 61x61 | Diamond |
| FlowSwitch | 60x60 | Diamond |

### ViewState Per Node Type

#### Start Node (Flowchart container)

The Flowchart element itself has ViewState for the start circle and canvas dimensions:

```xml
<Flowchart sap:VirtualizedContainerService.HintSize="884,809"
           sap2010:WorkflowViewState.IdRef="Flowchart_1">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <x:Boolean x:Key="IsExpanded">True</x:Boolean>
      <av:Point x:Key="ShapeLocation">425,35</av:Point>
      <av:Size x:Key="ShapeSize">50,50</av:Size>
      <av:PointCollection x:Key="ConnectorLocation">450,85 450,130</av:PointCollection>
      <x:Double x:Key="Width">831</x:Double>
      <x:Double x:Key="Height">668</x:Double>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  <Flowchart.StartNode>
    <x:Reference>__ReferenceID0</x:Reference>
  </Flowchart.StartNode>
  ...
</Flowchart>
```

| Property | Description |
|----------|-------------|
| `IsExpanded` | Must be `True` for flowchart to show content |
| `ShapeLocation` | Position of the Start circle |
| `ShapeSize` | Size of the Start circle (typically `50,50` or `60,75`) |
| `ConnectorLocation` | Line from Start to the first node |
| `Width` / `Height` | Total canvas dimensions (optional — auto-calculated by auto-arrange) |

#### FlowStep

```xml
<FlowStep x:Name="__ReferenceID0" sap2010:WorkflowViewState.IdRef="FlowStep_1">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <av:Point x:Key="ShapeLocation">105,365</av:Point>
      <av:Size x:Key="ShapeSize">110,70</av:Size>
      <av:PointCollection x:Key="ConnectorLocation">160,435 160,485</av:PointCollection>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  <ui:LogMessage DisplayName="Log message"
                 sap:VirtualizedContainerService.HintSize="110,70"
                 sap2010:WorkflowViewState.IdRef="LogMessage_1" />
  <FlowStep.Next>
    <x:Reference>__ReferenceID1</x:Reference>
  </FlowStep.Next>
</FlowStep>
```

| Property | Description |
|----------|-------------|
| `ShapeLocation` | Top-left of the step rectangle |
| `ShapeSize` | Width/height of the step rectangle |
| `ConnectorLocation` | Waypoints from this node to `FlowStep.Next` target |

#### FlowDecision

```xml
<FlowDecision x:Name="__ReferenceID1" Condition="[retryCount &gt; maxRetries]"
              DisplayName="Max retries reached?"
              sap:VirtualizedContainerService.HintSize="61,61"
              sap2010:WorkflowViewState.IdRef="FlowDecision_1">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <x:Boolean x:Key="IsExpanded">True</x:Boolean>
      <av:Point x:Key="ShapeLocation">420,130</av:Point>
      <av:Size x:Key="ShapeSize">61,61</av:Size>
      <x:String x:Key="TrueLabel">Yes</x:String>
      <x:String x:Key="FalseLabel">No</x:String>
      <av:PointCollection x:Key="TrueConnector">420,160 290,160 290,250</av:PointCollection>
      <av:PointCollection x:Key="FalseConnector">481,160 590,160 590,245</av:PointCollection>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  <FlowDecision.True>
    <x:Reference>__ReferenceID2</x:Reference>
  </FlowDecision.True>
  <FlowDecision.False>
    <x:Reference>__ReferenceID3</x:Reference>
  </FlowDecision.False>
</FlowDecision>
```

| Property | Description |
|----------|-------------|
| `ShapeLocation` / `ShapeSize` | Diamond position and size |
| `TrueConnector` | Waypoints for the True branch connector |
| `FalseConnector` | Waypoints for the False branch connector |
| `TrueLabel` / `FalseLabel` | Custom labels (default: "True"/"False") |

#### FlowSwitch

```xml
<FlowSwitch x:TypeArguments="x:Int32" x:Name="__ReferenceID4"
            sap:VirtualizedContainerService.HintSize="60,60"
            sap2010:WorkflowViewState.IdRef="FlowSwitch`1_1">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <av:Point x:Key="ShapeLocation">580,160</av:Point>
      <av:Size x:Key="ShapeSize">60,60</av:Size>
      <av:PointCollection x:Key="Default">580,190 270,190 270,265</av:PointCollection>
      <av:PointCollection x:Key="1Connector">610,220 610,280</av:PointCollection>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
</FlowSwitch>
```

| Property | Description |
|----------|-------------|
| `Default` | Connector for the default branch |
| `{CaseValue}Connector` | Connector for each case (e.g., `"1Connector"`, `"2Connector"`) |

### Connector Routing Rules

Connectors are `av:PointCollection` — a sequence of (X,Y) waypoints forming an **orthogonal/rectilinear path** (axis-aligned segments with right-angle bends).

**Straight vertical drop** (most common — sequential flow):
```xml
<av:PointCollection x:Key="ConnectorLocation">160,435 160,485</av:PointCollection>
```
Start at center-bottom of source → end at center-top of target.

**L-shaped connector** (branching left/right from a decision):
```xml
<av:PointCollection x:Key="TrueConnector">420,160 290,160 290,250</av:PointCollection>
```
Exit left side of diamond → horizontal → down to target.

**Multi-segment connector** (loop back-edge):
```xml
<av:PointCollection x:Key="TrueConnector">261,602 141,602 141,364 200,364</av:PointCollection>
```
Left → up → right — routes around other nodes for loops.

**How to calculate connector points:**
1. **Source point**: Edge of source shape (center-bottom for downward, left/right center for branches)
2. **Target point**: Edge of target shape (center-top for entering from above)
3. **Intermediate points**: Add waypoints for right-angle bends. Keep segments axis-aligned.

### Layout Algorithm

Based on Studio's auto-arrange (Sugiyama layered layout):

- **Layer separation** (vertical gap between rows): **50px**
- **Node separation** (horizontal gap between siblings): **100px**
- **Default new node position**: **(30, 100)**
- **Adding below existing**: **Y + 100** from lowest node

**Recommended layout for generation:**

1. Start node: `ShapeLocation="270,2.5"` with `ShapeSize="50,50"` — centered horizontally
2. Nodes in rows, each row ~110-120px apart (node height + 50px gap)
3. Linear flows: keep X centered (all at X=170 for 262px-wide steps on a 600px canvas)
4. Decision branches: True ~150-200px left, False ~150-200px right of center
5. Use `__ReferenceID{N}` starting from 0

**Simple linear flowchart (3 steps):**
```text
Start:      (270, 2.5)    50x50
FlowStep 1: (170, 110)    262x60
FlowStep 2: (170, 220)    262x60
FlowStep 3: (170, 330)    262x60
```

**Flowchart with decision:**
```text
Start:          (270, 2.5)     50x50
FlowStep 1:    (170, 110)     262x60
FlowDecision:  (270, 220)     60x60
  True branch:  (100, 330)    200x60     (left)
  False branch: (400, 330)    200x60     (right)
```

### Node Registration

All FlowStep/FlowDecision/FlowSwitch nodes must be registered as children of `<Flowchart>`. Direct children are already registered. Nodes defined inline within property elements (e.g., inside `FlowDecision.True`) need a trailing `<x:Reference>` entry at the Flowchart level.

See [common-pitfalls.md § x:Reference](common-pitfalls.md#xreference--__referenceid-naming) for the full rules with correct/wrong examples.

---

## 4. State Machine Layout

### Container ViewState

```xml
<StateMachine InitialState="{x:Reference __ReferenceID0}"
              DisplayName="Process"
              sap:VirtualizedContainerService.HintSize="1562,744"
              sap2010:WorkflowViewState.IdRef="StateMachine_1">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <x:Boolean x:Key="IsExpanded">True</x:Boolean>
      <av:Point x:Key="ShapeLocation">45,135</av:Point>
      <x:Double x:Key="StateContainerWidth">974</x:Double>
      <x:Double x:Key="StateContainerHeight">722</x:Double>
      <av:PointCollection x:Key="ConnectorLocation">95,160 125,160 125,158 164,158</av:PointCollection>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  ...
</StateMachine>
```

| Property | Description |
|----------|-------------|
| `ShapeLocation` | Position of the initial state indicator (circle/arrow) |
| `StateContainerWidth` / `StateContainerHeight` | Canvas size (default ~600x600, REFramework uses ~974x722) |
| `ConnectorLocation` | Connector from initial indicator to the `InitialState` |
| `InitialState` | Attribute reference to the starting State |

### State Nodes

```xml
<State x:Name="__ReferenceID0" DisplayName="Get Transaction Data"
       sap:VirtualizedContainerService.HintSize="229,110"
       sap2010:WorkflowViewState.IdRef="State_1">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <av:Point x:Key="ShapeLocation">545,215</av:Point>
      <av:Size x:Key="ShapeSize">229,110</av:Size>
      <x:Boolean x:Key="IsPinned">False</x:Boolean>
      <x:Double x:Key="StateContainerWidth">217</x:Double>
      <x:Double x:Key="StateContainerHeight">34</x:Double>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  <State.Entry>
    <Sequence DisplayName="Retrieve Data">
      <!-- Activities -->
    </Sequence>
  </State.Entry>
  <State.Transitions>
    <!-- Transition elements -->
  </State.Transitions>
</State>
```

| Property | Description |
|----------|-------------|
| `ShapeLocation` | Top-left position on canvas |
| `ShapeSize` | State rectangle size (typical: 134x62 to 229x110) |
| `IsPinned` | Whether state details are pinned open |
| `StateContainerWidth` / `StateContainerHeight` | Internal container size for the state's activities |

**Final State:** Same as State but with `IsFinal="True"`.

### Transitions

Transitions connect states and have explicit **connection point indices**:

```xml
<Transition DisplayName="New Transaction" sap2010:WorkflowViewState.IdRef="Transition_1">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <av:PointCollection x:Key="ConnectorLocation">659,325 659,355 660,355 660,385</av:PointCollection>
      <x:Int32 x:Key="SrcConnectionPointIndex">39</x:Int32>
      <x:Int32 x:Key="DestConnectionPointIndex">38</x:Int32>
      <x:Boolean x:Key="IsExpanded">True</x:Boolean>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  <Transition.To>
    <x:Reference>__ReferenceID1</x:Reference>
  </Transition.To>
  <Transition.Condition>[condition]</Transition.Condition>
</Transition>
```

| Property | Description |
|----------|-------------|
| `SrcConnectionPointIndex` | Connection point on the source state where connector leaves |
| `DestConnectionPointIndex` | Connection point on the destination state where connector arrives |
| `ConnectorLocation` | Waypoints for the connector path |

**Connection Point System:** States have numbered connection points around their border, increasing clockwise from top-left. The exact numbering depends on state size.

**Practical guidance:**
- **Downward transitions**: bottom-edge source points, top-edge destination points
- **Self-transitions** (loop to same state): right-edge points with a small routing loop
- **Upward transitions**: top-edge source, bottom-edge destination, route around

### Recommended Layout

```text
Initial indicator:  (45, 135)
Init State:         (164, 100)      229x110
Get Data State:     (545, 215)      229x110
Process State:      (545, 385)      240x192
End State:          (164, 385)      229x110 (IsFinal=True)
```

**Rules of thumb:**
- `StateContainerWidth="974"`, `StateContainerHeight="722"` for complex state machines
- Space states ~120-170px apart vertically
- Place Final State at the bottom or left
- Place Initial State near the top, to the right of the start indicator

### Node Registration

States defined inline inside `Transition.To` need `<x:Reference>` registration as direct children of `<StateMachine>`, same as Flowchart pattern.

---

## 5. Long Running Workflow (ProcessDiagram) Layout

ProcessDiagrams use a **BPMN-style horizontal left-to-right** flow, distinct from Flowchart's vertical top-to-bottom.

### Key Differences from Flowchart

| Aspect | Flowchart | ProcessDiagram |
|--------|-----------|----------------|
| Root activity | `Flowchart` | `upa:ProcessDiagram` |
| Flow direction | Top-to-bottom (vertical) | **Left-to-right (horizontal)** |
| Node types | FlowStep, FlowDecision, FlowSwitch | EventNode, TaskNode, DecisionNode, EndNode, BoundaryNode |
| Start node | `Flowchart.StartNode` | `upa:ProcessDiagram.StartNode` |
| Decision node | `FlowDecision` | `upa:DecisionNode` (True/False branches) |
| File extension | `.xaml` | `.xaml` |

### Node Types and Sizes

| Node Type | Typical Size | Shape | Purpose |
|-----------|-------------|-------|---------|
| `upa:EventNode` | 40x40 | Circle | Start event (with `StartBehavior`) |
| `upa:TaskNode` | 120x80 | Rectangle | Activity container (wraps Sequence) |
| `upa:DecisionNode` | 60x60 | Diamond | True/False branching |
| `upa:EndNode` | 40x40 | Circle | End event (with `EndBehavior`) |
| `upa:BoundaryNode` | 40x40 | Circle | Error handler attached to TaskNode |

### Container ViewState

```xml
<upa:ProcessDiagram DisplayName="Long Running Workflow"
                    sap:VirtualizedContainerService.HintSize="1163,850"
                    sap2010:WorkflowViewState.IdRef="ProcessDiagram_1">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <x:Boolean x:Key="IsExpanded">True</x:Boolean>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  <upa:ProcessDiagram.StartNode>
    <x:Reference>__ReferenceID0</x:Reference>
  </upa:ProcessDiagram.StartNode>
  ...
</upa:ProcessDiagram>
```

### EventNode (Start)

```xml
<upa:EventNode x:Name="__ReferenceID0" DisplayName="Manual Trigger"
               sap:VirtualizedContainerService.HintSize="40,40"
               sap2010:WorkflowViewState.IdRef="EventNode_1">
  <upa:EventNode.Behavior>
    <upa:StartBehavior>
      <upa:StartBehavior.DesignerMetadata>
        <upas:DesignerMetadata NodeType="StartEvent.Interrupting.None" />
      </upa:StartBehavior.DesignerMetadata>
    </upa:StartBehavior>
  </upa:EventNode.Behavior>
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <av:Point x:Key="ShapeLocation">130,140</av:Point>
      <av:Size x:Key="ShapeSize">40,40</av:Size>
      <av:PointCollection x:Key="ConnectorLocation">170,160 260,160</av:PointCollection>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  <upa:EventNode.Next>
    <!-- Next node (inline or x:Reference) -->
  </upa:EventNode.Next>
</upa:EventNode>
```

### TaskNode

```xml
<upa:TaskNode x:Name="__ReferenceID1" DisplayName="Process Step">
  <upa:TaskNode.Behavior>
    <upa:NodeBehavior>
      <upa:NodeBehavior.DesignerMetadata>
        <upas:DesignerMetadata NodeType="Task.None" />
      </upa:NodeBehavior.DesignerMetadata>
    </upa:NodeBehavior>
  </upa:TaskNode.Behavior>
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <av:Point x:Key="ShapeLocation">260,120</av:Point>
      <av:Size x:Key="ShapeSize">120,80</av:Size>
      <av:PointCollection x:Key="ConnectorLocation">380,160 470,160</av:PointCollection>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  <Sequence DisplayName="Process Steps" sap:VirtualizedContainerService.HintSize="120,80"
            sap2010:WorkflowViewState.IdRef="Sequence_1">
    <sap:WorkflowViewStateService.ViewState>
      <scg:Dictionary x:TypeArguments="x:String, x:Object">
        <x:Boolean x:Key="IsExpanded">True</x:Boolean>
      </scg:Dictionary>
    </sap:WorkflowViewStateService.ViewState>
    <!-- Activities here -->
  </Sequence>
  <upa:TaskNode.Next>
    <!-- Next node -->
  </upa:TaskNode.Next>
</upa:TaskNode>
```

### DecisionNode

```xml
<upa:DecisionNode x:Name="__ReferenceID2" DisplayName="Decision"
                  sap:VirtualizedContainerService.HintSize="60,60"
                  sap2010:WorkflowViewState.IdRef="DecisionNode_1">
  <upa:DecisionNode.Condition>
    <Literal x:TypeArguments="x:Boolean" DisplayName="Literal" Value="True" />
  </upa:DecisionNode.Condition>
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <x:Boolean x:Key="IsExpanded">True</x:Boolean>
      <av:Point x:Key="ShapeLocation">470,130</av:Point>
      <av:Size x:Key="ShapeSize">60,60</av:Size>
      <av:PointCollection x:Key="TrueConnector">500,130 500,70 620,70</av:PointCollection>
      <av:PointCollection x:Key="FalseConnector">500,190 500,220 620,220</av:PointCollection>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  <upa:DecisionNode.True>
    <!-- True branch node -->
  </upa:DecisionNode.True>
  <upa:DecisionNode.False>
    <!-- False branch node -->
  </upa:DecisionNode.False>
</upa:DecisionNode>
```

### EndNode

```xml
<upa:EndNode x:Name="__ReferenceID3" DisplayName="End"
             sap:VirtualizedContainerService.HintSize="40,40"
             sap2010:WorkflowViewState.IdRef="EndNode_1">
  <upa:EndNode.Behavior>
    <upa:EndBehavior>
      <upa:EndBehavior.DesignerMetadata>
        <upas:DesignerMetadata NodeType="EndEvent.None" />
      </upa:EndBehavior.DesignerMetadata>
    </upa:EndBehavior>
  </upa:EndNode.Behavior>
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <av:Point x:Key="ShapeLocation">830,50</av:Point>
      <av:Size x:Key="ShapeSize">40,40</av:Size>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
</upa:EndNode>
```

### BoundaryNode (Error Handler)

Attaches to a TaskNode for error handling:

```xml
<upa:TaskNode x:Name="__ReferenceID4" DisplayName="Risky Step">
  <upa:TaskNode.BoundaryNodes>
    <upa:BoundaryNode x:Name="__ReferenceID5" DisplayName="Error Handler"
                      sap:VirtualizedContainerService.HintSize="40,40"
                      sap2010:WorkflowViewState.IdRef="BoundaryNode_1">
      <upa:BoundaryNode.Behavior>
        <upa:CatchMostSpecificErrorBehavior>
          <upa:CatchMostSpecificErrorBehavior.DesignerMetadata>
            <upas:DesignerMetadata NodeType="BoundaryEvent.Interrupting.Error" />
          </upa:CatchMostSpecificErrorBehavior.DesignerMetadata>
        </upa:CatchMostSpecificErrorBehavior>
      </upa:BoundaryNode.Behavior>
      <sap:WorkflowViewStateService.ViewState>
        <scg:Dictionary x:TypeArguments="x:String, x:Object">
          <av:Point x:Key="ShapeLocation">720,240</av:Point>
          <av:Size x:Key="ShapeSize">40,40</av:Size>
          <av:PointCollection x:Key="ConnectorLocation">760,260 900,260</av:PointCollection>
        </scg:Dictionary>
      </sap:WorkflowViewStateService.ViewState>
      <upa:BoundaryNode.Next>
        <!-- Error handling task node -->
      </upa:BoundaryNode.Next>
    </upa:BoundaryNode>
  </upa:TaskNode.BoundaryNodes>
  <!-- TaskNode content -->
</upa:TaskNode>
```

### Horizontal Layout

ProcessDiagram flows **left-to-right** (unlike Flowcharts' top-to-bottom):

```text
EventNode (start)  →  TaskNode 1  →  DecisionNode  →  TaskNode 2  →  EndNode
(130, 140)            (260, 120)      (470, 130)       (620, 30)      (830, 50)
 40x40                 120x80          60x60            120x80          40x40
```

**Horizontal connector routing:**
```xml
<!-- From EventNode to TaskNode — exit right, enter left -->
<av:PointCollection x:Key="ConnectorLocation">170,160 260,160</av:PointCollection>

<!-- DecisionNode True (upward branch) -->
<av:PointCollection x:Key="TrueConnector">500,130 500,70 620,70</av:PointCollection>

<!-- DecisionNode False (downward branch) -->
<av:PointCollection x:Key="FalseConnector">500,190 500,220 620,220</av:PointCollection>
```

**Spacing guidelines:**
- Horizontal gap between nodes: ~50-90px
- Vertical centering: align node centers on Y ~140-160
- Start event at left edge (~X=130)
- Tasks proceed rightward with gaps
- Decision branches split vertically (True up, False down)

### Node Registration

Same rules as Flowchart — nodes defined inline within property elements (e.g., `TaskNode` inside `EventNode.Next`) need trailing `<x:Reference>` entries as direct children of `<upa:ProcessDiagram>`. See [common-pitfalls.md § x:Reference](common-pitfalls.md#xreference--__referenceid-naming) for the full rules.

---

## 6. ViewState Properties Reference

| Property | Type | Used On | Description |
|----------|------|---------|-------------|
| `ShapeLocation` | `av:Point` | FlowStep, FlowDecision, FlowSwitch, State, Flowchart start, StateMachine start, EventNode, TaskNode, DecisionNode, EndNode, BoundaryNode | X,Y position of top-left corner |
| `ShapeSize` | `av:Size` | Same as above | Width,Height of the shape |
| `ConnectorLocation` | `av:PointCollection` | FlowStep, StateMachine start, Transition, EventNode, TaskNode, BoundaryNode | Waypoints for outgoing connector |
| `TrueConnector` | `av:PointCollection` | FlowDecision, DecisionNode | Waypoints for True branch |
| `FalseConnector` | `av:PointCollection` | FlowDecision, DecisionNode | Waypoints for False branch |
| `TrueLabel` | `x:String` | FlowDecision | Custom label for True branch |
| `FalseLabel` | `x:String` | FlowDecision | Custom label for False branch |
| `Default` | `av:PointCollection` | FlowSwitch | Connector for default case |
| `{Value}Connector` | `av:PointCollection` | FlowSwitch | Connector for case `{Value}` |
| `IsExpanded` | `x:Boolean` | Any container | Whether activity is expanded in designer |
| `IsPinned` | `x:Boolean` | State, FlowDecision | Whether details panel is pinned |
| `Width` | `x:Double` | Flowchart | Total canvas width |
| `Height` | `x:Double` | Flowchart | Total canvas height |
| `StateContainerWidth` | `x:Double` | StateMachine, State | Canvas/internal container width |
| `StateContainerHeight` | `x:Double` | StateMachine, State | Canvas/internal container height |
| `SrcConnectionPointIndex` | `x:Int32` | Transition | Source connection point index |
| `DestConnectionPointIndex` | `x:Int32` | Transition | Destination connection point index |
| `sap:VirtualizedContainerService.HintSize` | string `"W,H"` | Any activity | Rendering hint — set as attribute, not in ViewState dict |
| `sap2010:WorkflowViewState.IdRef` | string | Any activity | Unique ID for ViewState correlation |

---

## 7. When to Skip ViewState

If generating XAML for **execution only** (not for visual display), you can omit all ViewState properties. The workflow will execute correctly. Studio will auto-arrange nodes when the file is first opened.

**Trade-off:** The initial layout will be messy — all nodes may overlap at (0,0). For a professional-looking layout, always include ViewState.

**Recommended approach:** Generate ViewState for all Flowchart, State Machine, and ProcessDiagram workflows. It adds bulk but produces immediately usable designs.

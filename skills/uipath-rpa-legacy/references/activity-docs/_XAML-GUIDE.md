# UiPath Legacy XAML Workflow Guide

## Purpose
How XAML workflows work internally: structure, VB.NET vs C#, arguments, variables, Sequence vs Flowchart vs State Machine, visual layout, and templates for generating valid workflow files.

---

## 1. XAML File Structure

Every UiPath .xaml workflow file is a **WF4 (Windows Workflow Foundation 4) Activity** serialized as XAML. The root structure is:

```xml
<Activity
  mc:Ignorable="sap sap2010"
  x:Class="WorkflowName"
  xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
  xmlns:ui="http://schemas.uipath.com/workflow/activities"
  xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
  ...>

  <!-- 1. Arguments (x:Members) -->
  <!-- 2. Namespace imports -->
  <!-- 3. Assembly references -->
  <!-- 4. Root container (Sequence/Flowchart/StateMachine) -->

</Activity>
```

### Key Attributes on Root `<Activity>`
| Attribute | Purpose |
|-----------|---------|
| `x:Class="Main"` | Workflow class name (matches filename without .xaml) |
| `mva:VisualBasic.Settings="{x:Null}"` | **VB.NET project** marker |
| `sap2010:ExpressionActivityEditor.ExpressionActivityEditor="C#"` | **C# project** marker |
| `sap:VirtualizedContainerService.HintSize="1224.8,523.2"` | Designer canvas size |

---

## 2. VB.NET vs C# — Key Differences

### How to Tell
| | VB.NET | C# |
|---|--------|-----|
| **Root attribute** | `mva:VisualBasic.Settings="{x:Null}"` | `sap2010:ExpressionActivityEditor.ExpressionActivityEditor="C#"` |
| **Expression type** | `mva:VisualBasicValue<T>` / `mva:VisualBasicReference<T>` | `mca:CSharpValue<T>` / `mca:CSharpReference<T>` |
| **Namespace xmlns** | `xmlns:mva="clr-namespace:Microsoft.VisualBasic.Activities;assembly=System.Activities"` | `xmlns:mca="clr-namespace:Microsoft.CSharp.Activities;assembly=System.Activities"` |
| **project.json** | `"expressionLanguage": "VisualBasic"` | `"expressionLanguage": "CSharp"` |
| **Assembly ref** | `Microsoft.VisualBasic` | `Microsoft.CSharp` |

### Expression Syntax in XAML

**VB.NET expressions** (inline in attributes):
```xml
<!-- Simple value in brackets -->
<ui:LogMessage Message="[&quot;Hello &quot; + userName]" />

<!-- Typed expression -->
<Assign.Value>
  <InArgument x:TypeArguments="x:Int32">[variable1 + 1]</InArgument>
</Assign.Value>

<!-- Condition (FlowDecision) -->
<FlowDecision.Condition>
  <mva:VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="variable1 &lt; 5" />
</FlowDecision.Condition>
```

**C# expressions** (wrapped in CSharpValue/CSharpReference):
```xml
<!-- String value -->
<ui:LogMessage.Message>
  <InArgument x:TypeArguments="x:Object">
    <mca:CSharpValue x:TypeArguments="x:Object">"LegacyC#"</mca:CSharpValue>
  </InArgument>
</ui:LogMessage.Message>

<!-- Condition -->
<FlowDecision.Condition>
  <mca:CSharpValue x:TypeArguments="x:Boolean">variable1 &lt; 5</mca:CSharpValue>
</FlowDecision.Condition>
```

### Key Difference: VB uses `[expression]` bracket notation; C# uses `<mca:CSharpValue>` wrapper elements

---

## 3. Arguments (In/Out/InOut)

Arguments are the workflow's public interface — how data flows between workflows via `Invoke Workflow File`.

### XAML Declaration
```xml
<x:Members>
  <x:Property Name="inputName"    Type="InArgument(x:String)" />
  <x:Property Name="inputAge"     Type="InArgument(x:Int32)" />
  <x:Property Name="inputData"    Type="InArgument(sd:DataTable)" />
  <x:Property Name="outputResult" Type="OutArgument(x:String)" />
  <x:Property Name="ioCounter"    Type="InOutArgument(x:Int32)" />
</x:Members>
```

### Argument Directions
| Direction | XAML Type | Description | Caller Side |
|-----------|-----------|-------------|-------------|
| `In` | `InArgument(TypeName)` | Input only — caller provides value | Set before invoke |
| `Out` | `OutArgument(TypeName)` | Output only — workflow sets value | Read after invoke |
| `InOut` | `InOutArgument(TypeName)` | Both directions — caller provides, workflow may modify | Set before, read after |

### Common Type Mappings in XAML
| XAML Type | .NET Type |
|-----------|-----------|
| `x:String` | System.String |
| `x:Int32` | System.Int32 |
| `x:Int64` | System.Int64 |
| `x:Boolean` | System.Boolean |
| `x:Double` | System.Double |
| `x:Object` | System.Object |
| `x:Decimal` | System.Decimal |
| `sd:DataTable` | System.Data.DataTable (requires `xmlns:sd` namespace) |
| `scg:Dictionary(x:String, x:Object)` | Dictionary\<String, Object\> |
| `scg:List(x:String)` | List\<String\> |
| `s:DateTime` | System.DateTime |
| `s:SecureString` | System.Security.SecureString |

### Referencing Arguments in Expressions
```xml
<!-- VB.NET: use [argumentName] brackets -->
<InArgument x:TypeArguments="x:String">[inputName]</InArgument>

<!-- Setting output argument -->
<Assign.To>
  <OutArgument x:TypeArguments="x:String">[outputResult]</OutArgument>
</Assign.To>
<Assign.Value>
  <InArgument x:TypeArguments="x:String">[inputName + " processed"]</InArgument>
</Assign.Value>
```

---

## 4. Variables

Variables are local to a container (Sequence, Flowchart, StateMachine, etc.). They are declared inside the container element.

### XAML Declaration
```xml
<Sequence.Variables>
  <Variable x:TypeArguments="x:String" Name="myText" Default="Hello" />
  <Variable x:TypeArguments="x:Int32" Name="counter" Default="0" />
  <Variable x:TypeArguments="sd:DataTable" Name="dtResult" />
  <Variable x:TypeArguments="x:Boolean" Name="isValid" />
</Sequence.Variables>
```

### Scope Rules
- Variables are **scoped to their parent container** (Sequence, Flowchart, State, etc.)
- Variables declared in an outer Sequence are accessible in inner Sequences
- Variables are NOT accessible across invoked workflows (use Arguments for that)
- Variables in a Flowchart are accessible from all FlowSteps in that Flowchart

---

## 5. Sequence

**Purpose**: Executes activities in top-to-bottom order. The most common container.

**When to use**: Linear processes, step-by-step operations, most workflows.

### XAML Structure
```xml
<Sequence DisplayName="Main Sequence" sap2010:WorkflowViewState.IdRef="Sequence_1">
  <Sequence.Variables>
    <Variable x:TypeArguments="x:String" Name="result" />
  </Sequence.Variables>
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <x:Boolean x:Key="IsExpanded">True</x:Boolean>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>

  <!-- Activities execute top-to-bottom -->
  <Assign DisplayName="Set Result" sap2010:WorkflowViewState.IdRef="Assign_1">
    <Assign.To>
      <OutArgument x:TypeArguments="x:String">[result]</OutArgument>
    </Assign.To>
    <Assign.Value>
      <InArgument x:TypeArguments="x:String">["Hello World"]</InArgument>
    </Assign.Value>
  </Assign>

  <ui:LogMessage DisplayName="Log Result" sap2010:WorkflowViewState.IdRef="LogMessage_1"
    Message="[result]" />

</Sequence>
```

### Visual Layout
- Activities stack vertically in order
- `IsExpanded` controls whether the Sequence shows its children or is collapsed
- `HintSize` controls the visual width/height in the designer

---

## 6. Flowchart

**Purpose**: Visual flow with decisions, branches, and loops via connectors. Activities connect via arrows.

**When to use**: Decision-heavy logic, loops with conditions, when you need visual flow representation.

### XAML Structure
```xml
<Flowchart DisplayName="Main Flowchart" sap2010:WorkflowViewState.IdRef="Flowchart_1">
  <Flowchart.Variables>
    <Variable x:TypeArguments="x:Int32" Name="counter" />
  </Flowchart.Variables>
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <x:Boolean x:Key="IsExpanded">True</x:Boolean>
      <!-- Start node position -->
      <av:Point x:Key="ShapeLocation">270,2.5</av:Point>
      <av:Size x:Key="ShapeSize">60,74.66</av:Size>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>

  <!-- Start node points to first FlowStep -->
  <Flowchart.StartNode>
    <x:Reference>__ReferenceID0</x:Reference>
  </Flowchart.StartNode>

  <!-- FlowStep: wraps an activity + points to next -->
  <FlowStep x:Name="__ReferenceID0">
    <sap:WorkflowViewStateService.ViewState>
      <scg:Dictionary x:TypeArguments="x:String, x:Object">
        <av:Point x:Key="ShapeLocation">185,127</av:Point>
        <av:Size x:Key="ShapeSize">229,62</av:Size>
        <!-- Connector line coordinates -->
        <av:PointCollection x:Key="ConnectorLocation">300,189 300,239</av:PointCollection>
      </scg:Dictionary>
    </sap:WorkflowViewStateService.ViewState>
    <Assign DisplayName="Increment" .../>
    <FlowStep.Next>
      <x:Reference>__ReferenceID1</x:Reference>
    </FlowStep.Next>
  </FlowStep>

  <!-- FlowDecision: True/False branching -->
  <FlowDecision x:Name="__ReferenceID1" DisplayName="Check Condition">
    <FlowDecision.Condition>
      <mva:VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" />
    </FlowDecision.Condition>
    <FlowDecision.True>
      <x:Reference>__ReferenceID0</x:Reference>  <!-- Loop back -->
    </FlowDecision.True>
    <FlowDecision.False>
      <!-- null = end of flow -->
    </FlowDecision.False>
  </FlowDecision>

  <!-- Do NOT add trailing <x:Reference> for child nodes here — they are already direct children -->
</Flowchart>
```

### Key Elements
| Element | Purpose |
|---------|---------|
| `Flowchart.StartNode` | Points to the first FlowStep (entry point) |
| `FlowStep` | Wraps one activity + `FlowStep.Next` (pointer to next) |
| `FlowDecision` | Boolean branch: `True` path and `False` path |
| `FlowSwitch<T>` | Multi-branch switch (like Switch activity) |
| `x:Reference` | Cross-references between nodes (used inside `Flowchart.StartNode`, `FlowStep.Next`, `FlowDecision.True/False` — never as trailing children of `<Flowchart>`) |

### Flowchart ViewState Layout Guide

**MANDATORY for generated/edited Flowcharts.** Without ViewState, Studio stacks all nodes at (0,0) — unusable.

**Required xmlns** on root `<Activity>`:
```xml
xmlns:av="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
```

**Coordinate system:** Origin top-left (0,0), X increases right, Y increases down, units in pixels.

**Standard node sizes:**

| Node Type | ShapeSize (W×H) | Notes |
|-----------|----------------|-------|
| Start Node (Flowchart entry) | 60×75 | Positioned by Flowchart container ViewState |
| FlowStep (activity box) | 230×65 | Width varies with activity content |
| FlowDecision (diamond) | 60×75 | Same as start node |

**Layout algorithm (grid-based):**
1. Main path center X: **270**
2. Start node at **(270, 2.5)** — set in the Flowchart container's ViewState
3. First FlowStep at **(155, 120)** — centered below start (270 - 230/2 = 155)
4. Vertical step: **~110px** (node height + ~45px gap)
5. True branch: offset left — center X at **~120** (150px left of main center)
6. False branch: offset right — center X at **~420** (150px right of main center)
7. Merge node: back to center X **~155**

**ConnectorLocation formula:**
- `center_x = ShapeLocation.X + ShapeSize.Width / 2`
- `bottom_y = ShapeLocation.Y + ShapeSize.Height`
- `top_y = ShapeLocation.Y`
- **Straight down:** `center_x,bottom_y center_x,next_top_y`
- **Decision True (left):** `decision_left_x,decision_center_y target_center_x,decision_center_y target_center_x,target_top_y`
- **Decision False (right):** `decision_right_x,decision_center_y target_center_x,decision_center_y target_center_x,target_top_y`
  - Where `decision_left_x = ShapeLocation.X`, `decision_right_x = ShapeLocation.X + ShapeSize.Width`
  - Where `decision_center_y = ShapeLocation.Y + ShapeSize.Height / 2`

**ViewState placement per node:**
```xml
<FlowStep x:Name="__ReferenceID0">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <av:Point x:Key="ShapeLocation">155,120</av:Point>
      <av:Size x:Key="ShapeSize">230,65</av:Size>
      <av:PointCollection x:Key="ConnectorLocation">270,185 270,240</av:PointCollection>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  <!-- activity here -->
  <FlowStep.Next>...</FlowStep.Next>
</FlowStep>
```

**Flowchart container ViewState (start node position):**
```xml
<Flowchart DisplayName="Main Flowchart" sap2010:WorkflowViewState.IdRef="Flowchart_1">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <x:Boolean x:Key="IsExpanded">True</x:Boolean>
      <av:Point x:Key="ShapeLocation">270,2.5</av:Point>
      <av:Size x:Key="ShapeSize">60,75</av:Size>
      <av:PointCollection x:Key="ConnectorLocation">300,77.5 300,120</av:PointCollection>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  ...
</Flowchart>
```

**FlowDecision ViewState (True/False connectors):**
```xml
<FlowDecision x:Name="__ReferenceID1" DisplayName="Has Data?">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <av:Point x:Key="ShapeLocation">240,240</av:Point>
      <av:Size x:Key="ShapeSize">60,75</av:Size>
      <!-- True exits left -->
      <av:PointCollection x:Key="TrueConnector">240,277.5 120,277.5 120,340</av:PointCollection>
      <!-- False exits right -->
      <av:PointCollection x:Key="FalseConnector">300,277.5 450,277.5 450,340</av:PointCollection>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  ...
</FlowDecision>
```

**Complete example layout map:**
```
              [Start]             (270, 2.5)     60×75
                 │
          [Read Data]             (155, 120)    230×65
                 │
            <Has Data?>           (240, 240)     60×75
           /           \
    [Calculate]     [Log None]    (5, 340)      (335, 340)   230×65
         │
    <Direction?>                  (240, 460)     60×75
       /       \
 [Bullish]  [Bearish]            (5, 560)       (335, 560)   230×65
       \       /
    [Write Output]                (155, 680)    230×65
```

**When adding nodes to an existing Flowchart:** Read existing ShapeLocation values first. Place new nodes below or beside existing ones with ≥110px vertical / ≥200px horizontal clearance.

---

## 7. State Machine

**Purpose**: State-based workflow with explicit states, transitions, and conditions. Used for complex business processes like the REFramework.

**When to use**: Processes with distinct states (Init, Process, End), approval workflows, retry patterns.

### XAML Structure
```xml
<StateMachine InitialState="{x:Reference __ReferenceID_InitState}"
  DisplayName="Process State Machine" sap2010:WorkflowViewState.IdRef="StateMachine_1">

  <StateMachine.Variables>
    <Variable x:TypeArguments="x:Int32" Name="transactionCounter" />
  </StateMachine.Variables>

  <!-- State with Entry activities and Transitions -->
  <State x:Name="__ReferenceID_InitState" DisplayName="Init">
    <State.Entry>
      <Sequence DisplayName="Initialize">
        <!-- Activities that run when entering this state -->
        <Assign .../>
      </Sequence>
    </State.Entry>
    <State.Transitions>
      <Transition DisplayName="Success" sap2010:WorkflowViewState.IdRef="Transition_1">
        <Transition.Condition>[initSuccess]</Transition.Condition>
        <Transition.To>
          <x:Reference>__ReferenceID_ProcessState</x:Reference>
        </Transition.To>
      </Transition>
      <Transition DisplayName="SystemError">
        <Transition.Condition>[Not initSuccess]</Transition.Condition>
        <Transition.To>
          <x:Reference>__ReferenceID_EndState</x:Reference>
        </Transition.To>
      </Transition>
    </State.Transitions>
  </State>

  <!-- Processing State -->
  <State x:Name="__ReferenceID_ProcessState" DisplayName="Process Transaction">
    <State.Entry>
      <Sequence DisplayName="Process">...</Sequence>
    </State.Entry>
    <State.Transitions>
      <Transition DisplayName="More Items">
        <Transition.Condition>[hasMoreItems]</Transition.Condition>
        <Transition.To>
          <x:Reference>__ReferenceID_ProcessState</x:Reference> <!-- Loop to self -->
        </Transition.To>
      </Transition>
      <Transition DisplayName="Done">
        <Transition.To>
          <x:Reference>__ReferenceID_EndState</x:Reference>
        </Transition.To>
      </Transition>
    </State.Transitions>
  </State>

  <!-- Final State (IsFinal=True means workflow ends here) -->
  <State x:Name="__ReferenceID_EndState" DisplayName="End Process" IsFinal="True">
    <State.Entry>
      <Sequence DisplayName="Cleanup">...</Sequence>
    </State.Entry>
  </State>

</StateMachine>
```

### Key Elements
| Element | Purpose |
|---------|---------|
| `StateMachine.InitialState` | Reference to first state |
| `State` | A state with Entry activities, Exit activities, and Transitions |
| `State.Entry` | Activities executed when entering the state |
| `State.Exit` | Activities executed when leaving the state |
| `State.Transitions` | List of possible transitions to other states |
| `Transition.Condition` | Boolean expression that must be true to take this transition |
| `Transition.To` | Reference to destination state |
| `Transition.Action` | Activities to execute during the transition |
| `State IsFinal="True"` | Final state — workflow ends when this state is reached |

### StateMachine ViewState Layout Guide

**MANDATORY for generated/edited StateMachines.** Without ViewState, Studio stacks all states at (0,0) — unusable.

**Required xmlns** on root `<Activity>`:
```xml
xmlns:av="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
```

**Coordinate system:** Same as Flowchart — origin top-left (0,0), X right, Y down, pixels. StateMachine uses a 600×600 container.

**Standard sizes:**

| Node Type | ShapeSize (W×H) | Notes |
|-----------|----------------|-------|
| State | 134×61.6 | Universal — all states same size |
| Final State (IsFinal="True") | 134×61.6 | Same size as regular states |

**StateMachine container ViewState:**
```xml
<StateMachine DisplayName="Process" sap2010:WorkflowViewState.IdRef="StateMachine_1">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <x:Boolean x:Key="IsExpanded">True</x:Boolean>
      <x:Double x:Key="StateContainerWidth">600</x:Double>
      <x:Double x:Key="StateContainerHeight">600</x:Double>
      <av:Point x:Key="ShapeLocation">270,2.5</av:Point>
      <av:Size x:Key="ShapeSize">60,75</av:Size>
      <av:PointCollection x:Key="ConnectorLocation">270,77.5 270,107 110,107 110,109</av:PointCollection>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  ...
</StateMachine>
```

**Layout algorithm:**
1. Container: **600×600** pixels
2. Start connector at **(270, 2.5)** — centered top
3. Initial state: **(43, 109)** — top-left area
4. Horizontal spacing: **~200px** between state centers
5. Vertical spacing: **~130px** between state centers
6. Final state: below the last processing state

**State ViewState:**
```xml
<State x:Name="__ReferenceID_Init" DisplayName="Init">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <av:Point x:Key="ShapeLocation">43,109</av:Point>
      <av:Size x:Key="ShapeSize">134,61.6</av:Size>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  ...
</State>
```

**Transition connector ViewState:**
```xml
<Transition DisplayName="Success">
  <sap:WorkflowViewStateService.ViewState>
    <scg:Dictionary x:TypeArguments="x:String, x:Object">
      <av:PointCollection x:Key="ConnectorLocation">177,139 300,139 300,149</av:PointCollection>
      <x:Int32 x:Key="SrcConnectionPointIndex">8</x:Int32>
      <x:Int32 x:Key="DestConnectionPointIndex">12</x:Int32>
    </scg:Dictionary>
  </sap:WorkflowViewStateService.ViewState>
  ...
</Transition>
```

Connector formula: exit right edge of source state → route horizontally → enter top edge of target state. `SrcConnectionPointIndex` and `DestConnectionPointIndex` are internal Studio indices — use values from existing workflows or let Studio adjust them on first open.

**Complete REFramework-style layout map:**
```
         [Start]              (270, 2.5)     60×75
            │
       [Init]                 (43, 109)     134×61.6
       /         \
  [Process]    [End]          (233, 149)    (233, 279)    134×61.6
    ↺ (self-loop)             Final state
```

**Self-loop transition** (Process → Process for retry):
```xml
<av:PointCollection x:Key="ConnectorLocation">367,158 397,158 397,162 367,162</av:PointCollection>
```
Forms a small rectangle extending ~30px right of the state's right edge.

**When adding states to an existing StateMachine:** Read existing ShapeLocation values. Place new states with ≥130px vertical / ≥200px horizontal clearance. Update `StateContainerWidth`/`StateContainerHeight` if new states exceed the 600×600 canvas.

---

## 8. project.json Structure

Every UiPath project has a `project.json` at the root defining metadata and configuration.

### Key Fields
```json
{
  "name": "MyProject",
  "description": "Project description",
  "main": "Main.xaml",
  "dependencies": {
    "UiPath.System.Activities": "[22.10.4]",
    "UiPath.UIAutomation.Activities": "[22.10.4]",
    "UiPath.Excel.Activities": "[2.11.3]",
    "UiPath.Mail.Activities": "[1.12.1]",
    "UiPath.Testing.Activities": "[22.10.3]"
  },
  "schemaVersion": "4.0",
  "studioVersion": "23.4.0.0",
  "projectVersion": "1.0.0",
  "expressionLanguage": "VisualBasic",   // or "CSharp"
  "targetFramework": "Legacy",           // "Legacy", "Windows", "Portable"
  "runtimeOptions": {
    "autoDispose": false,
    "isPausable": true,
    "isAttended": false,
    "requiresUserInteraction": true,
    "supportsPersistence": false,
    "workflowSerialization": "DataContract",
    "excludedLoggedData": ["Private:*", "*password*"],
    "executionType": "Workflow"
  },
  "designOptions": {
    "projectProfile": "Developement",
    "outputType": "Process",             // "Process" or "Library"
    "modernBehavior": true
  },
  "entryPoints": [
    {
      "filePath": "Main.xaml",
      "uniqueId": "...",
      "input": [],
      "output": []
    }
  ]
}
```

### Target Framework Values
| Value | Description |
|-------|-------------|
| `"Legacy"` | .NET Framework 4.6.1 (Windows-Legacy compatibility) |
| `"Windows"` | .NET 6+ Windows (modern) |
| `"Portable"` | .NET 6+ cross-platform |

### Output Types
| Value | Description |
|-------|-------------|
| `"Process"` | Standalone process (has Main.xaml entry point) |
| `"Library"` | Reusable library (workflows invokable from other projects) |
| `"TestAutomation"` | Test automation project |

---

## 9. Namespace Imports

### Standard VB.NET Legacy Namespaces
```xml
<TextExpression.NamespacesForImplementation>
  <sco:Collection x:TypeArguments="x:String">
    <x:String>System.Activities</x:String>
    <x:String>System.Activities.Statements</x:String>
    <x:String>System.Activities.Expressions</x:String>
    <x:String>System.Activities.Validation</x:String>
    <x:String>System.Activities.XamlIntegration</x:String>
    <x:String>Microsoft.VisualBasic</x:String>
    <x:String>Microsoft.VisualBasic.Activities</x:String>
    <x:String>System</x:String>
    <x:String>System.Collections</x:String>
    <x:String>System.Collections.Generic</x:String>
    <x:String>System.Data</x:String>
    <x:String>System.Diagnostics</x:String>
    <x:String>System.Drawing</x:String>
    <x:String>System.IO</x:String>
    <x:String>System.Linq</x:String>
    <x:String>System.Net.Mail</x:String>
    <x:String>System.Xml</x:String>
    <x:String>System.Xml.Linq</x:String>
    <x:String>UiPath.Core</x:String>
    <x:String>UiPath.Core.Activities</x:String>
    <x:String>System.Windows.Markup</x:String>
  </sco:Collection>
</TextExpression.NamespacesForImplementation>
```

### Additional C# Namespaces
```xml
<x:String>System.Text</x:String>
<x:String>System.Linq.Expressions</x:String>
```

---

## 10. ViewState — Visual Layout System

The `sap:WorkflowViewStateService.ViewState` dictionary controls how activities appear in the designer.

### Common ViewState Keys
| Key | Type | Purpose |
|-----|------|---------|
| `IsExpanded` | Boolean | Whether container is expanded/collapsed |
| `ShapeLocation` | Point | Position of node in Flowchart/StateMachine (x,y) |
| `ShapeSize` | Size | Width/height of node |
| `ConnectorLocation` | PointCollection | Arrow path coordinates between nodes |
| `StateContainerWidth` | Double | Canvas width for StateMachine |
| `StateContainerHeight` | Double | Canvas height for StateMachine |
| `IsPinned` | Boolean | Whether state is pinned in StateMachine |

### HintSize
Every activity has `sap:VirtualizedContainerService.HintSize="width,height"` controlling its rendered size in the designer. The designer adjusts these automatically, but they must be present for proper rendering.

### IdRef
Every activity has `sap2010:WorkflowViewState.IdRef="UniqueId_N"` which is a unique identifier within the XAML file. Format is typically `ActivityType_N` (e.g., `Sequence_1`, `Assign_3`, `FlowDecision_1`).

---

## 11. Gotchas When Generating XAML

1. **Every `x:Name` must be unique** within the file — FlowSteps use `__ReferenceID0`, `__ReferenceID1`, etc.
2. **`x:Reference` must match an `x:Name`** — broken references crash the designer
3. **IdRef must be unique** — duplicate IdRef values cause designer rendering errors
4. **Bracket expressions `[expr]`** are VB.NET only — C# must use `<mca:CSharpValue>` elements
5. **XML escaping required**: `<` becomes `&lt;`, `>` becomes `&gt;`, `"` becomes `&quot;`, `&` becomes `&amp;`
6. **Assembly references must include all dependencies** — missing references cause design-time compilation errors
7. **HintSize must be present** on every activity for proper designer rendering
8. **`expressionLanguage` in project.json must match XAML expression style** — VB project with C# expressions crashes
9. **Never add trailing `<x:Reference>` for Flowchart child nodes** — nodes defined inline as direct children must NOT be re-listed at the end. Only use `<x:Reference>` inside property elements (`Flowchart.StartNode`, `FlowStep.Next`, `FlowDecision.True/False`, etc.) to create cross-references
10. **Variables declared inside a container** are only accessible within that container and its children
11. **Arguments declared at top level** (`x:Members`) are the public API of the workflow
12. **State Machine needs exactly one `IsFinal="True"` state** for proper termination

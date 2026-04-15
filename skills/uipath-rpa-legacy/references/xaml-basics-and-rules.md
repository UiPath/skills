# XAML Basics and Rules (Legacy)

Core concepts for legacy UiPath workflow XAML files and rules for generating and editing XAML content. Legacy projects use .NET Framework 4.6.1 (WF4) and primarily VB.NET expressions.

For the full XAML internals guide with detailed templates, see [activity-docs/_XAML-GUIDE.md](./activity-docs/_XAML-GUIDE.md).

---

## XAML File Anatomy

Every legacy UiPath XAML workflow is a WF4 Activity serialized as XAML:

```xml
<Activity
  mc:Ignorable="sap sap2010"
  x:Class="WorkflowName"
  mva:VisualBasic.Settings="{x:Null}"
  xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:mva="clr-namespace:Microsoft.VisualBasic.Activities;assembly=System.Activities"
  xmlns:sap="http://schemas.microsoft.com/netfx/2009/xaml/activities/presentation"
  xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
  xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"
  xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=mscorlib"
  xmlns:ui="http://schemas.uipath.com/workflow/activities"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">

  <!-- BASELINE NAMESPACE IMPORTS (21 — include ALL of these in every new VB.NET XAML) -->
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
      <!-- Add package-specific namespaces below when using additional packages -->
    </sco:Collection>
  </TextExpression.NamespacesForImplementation>

  <!-- BASELINE ASSEMBLY REFERENCES (16 — include ALL of these in every new VB.NET XAML) -->
  <TextExpression.ReferencesForImplementation>
    <sco:Collection x:TypeArguments="AssemblyReference">
      <AssemblyReference>System.Activities</AssemblyReference>
      <AssemblyReference>Microsoft.VisualBasic</AssemblyReference>
      <AssemblyReference>mscorlib</AssemblyReference>
      <AssemblyReference>System.Data</AssemblyReference>
      <AssemblyReference>System.Data.DataSetExtensions</AssemblyReference>
      <AssemblyReference>System</AssemblyReference>
      <AssemblyReference>System.Drawing</AssemblyReference>
      <AssemblyReference>System.Core</AssemblyReference>
      <AssemblyReference>System.Xml</AssemblyReference>
      <AssemblyReference>System.Xml.Linq</AssemblyReference>
      <AssemblyReference>PresentationFramework</AssemblyReference>
      <AssemblyReference>WindowsBase</AssemblyReference>
      <AssemblyReference>PresentationCore</AssemblyReference>
      <AssemblyReference>System.Xaml</AssemblyReference>
      <AssemblyReference>UiPath.System.Activities</AssemblyReference>
      <AssemblyReference>UiPath.UiAutomation.Activities</AssemblyReference>
      <!-- Add package-specific assembly references below when using additional packages -->
    </sco:Collection>
  </TextExpression.ReferencesForImplementation>

  <!-- x:Members (arguments) -->
  <x:Members>
    <x:Property Name="in_InputName" Type="InArgument(x:String)" />
    <x:Property Name="out_Result" Type="OutArgument(x:String)" />
  </x:Members>

  <!-- Main workflow body -->
  <Sequence DisplayName="Main Sequence" sap2010:WorkflowViewState.IdRef="Sequence_1">
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

### Key Differences from Modern XAML

| Aspect | Legacy | Modern |
|--------|--------|--------|
| Root marker | `mva:VisualBasic.Settings="{x:Null}"` | No `mva:` marker; may have expression editor attribute |
| Assembly xmlns | `assembly=mscorlib` | `assembly=System.Private.CoreLib` |
| Expression types | `mva:VisualBasicValue` / `mva:VisualBasicReference` | Brackets `[expr]` or `CSharpValue` |
| VB namespace | `xmlns:mva="clr-namespace:Microsoft.VisualBasic.Activities;assembly=System.Activities"` | Same or inferred |
| Framework | .NET Framework 4.6.1 | .NET 6+ |

---

## VB.NET vs C# Expression Detection

| Marker | VB.NET (Primary) | C# (Rare in Legacy) |
|--------|-------------------|---------------------|
| **Root attribute** | `mva:VisualBasic.Settings="{x:Null}"` | `sap2010:ExpressionActivityEditor.ExpressionActivityEditor="C#"` |
| **Expression type** | `mva:VisualBasicValue<T>` / `mva:VisualBasicReference<T>` | `mca:CSharpValue<T>` / `mca:CSharpReference<T>` |
| **Namespace xmlns** | `xmlns:mva="clr-namespace:Microsoft.VisualBasic.Activities;assembly=System.Activities"` | `xmlns:mca="clr-namespace:Microsoft.CSharp.Activities;assembly=System.Activities"` |
| **project.json** | `"expressionLanguage": "VisualBasic"` | `"expressionLanguage": "CSharp"` |

**Always check `project.json` `expressionLanguage` field before writing any expressions.**

---

## VB.NET Expression Syntax (Primary)

VB.NET expressions use bracket notation `[expression]` inline in attributes:

```xml
<!-- Simple variable reference -->
<ui:LogMessage Message="[myVariable]" />

<!-- String concatenation -->
<ui:LogMessage Message="[&quot;Hello &quot; + userName]" />

<!-- Typed expression in InArgument -->
<Assign.Value>
  <InArgument x:TypeArguments="x:Int32">[counter + 1]</InArgument>
</Assign.Value>

<!-- Boolean condition -->
<If Condition="[age >= 18]">

<!-- FlowDecision with explicit VisualBasicValue -->
<FlowDecision.Condition>
  <mva:VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" />
</FlowDecision.Condition>
```

**XML escaping required inside expressions:** `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`, `&` → `&amp;`

**Throw.Exception quote escaping gotcha:** Fully-qualified class names + complex string expressions with multiple `&quot;` in `Throw.Exception` can cause compiler errors. Use short-form class names (`BusinessRuleException` not `UiPath.Core.Activities.BusinessRuleException`) and for complex messages, assign to a variable first then throw with the variable. See [common-pitfalls.md](./common-pitfalls.md#vbnet-quote-escaping-in-throwexception-critical-for-xaml-generation) for the full pattern.

For comprehensive VB.NET expression patterns (strings, dates, collections, DataTables), see [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md).

---

## C# Expression Syntax (Secondary)

C# expressions use `<mca:CSharpValue>` / `<mca:CSharpReference>` wrappers:

```xml
<!-- String value -->
<ui:LogMessage.Message>
  <InArgument x:TypeArguments="x:Object">
    <mca:CSharpValue x:TypeArguments="x:Object">"Hello " + userName</mca:CSharpValue>
  </InArgument>
</ui:LogMessage.Message>

<!-- Assign with CSharpReference (lvalue) and CSharpValue (rvalue) -->
<Assign DisplayName="Set Name">
  <Assign.To>
    <OutArgument x:TypeArguments="x:String">
      <mca:CSharpReference x:TypeArguments="x:String">fullName</mca:CSharpReference>
    </OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:String">
      <mca:CSharpValue x:TypeArguments="x:String">firstName + " " + lastName</mca:CSharpValue>
    </InArgument>
  </Assign.Value>
</Assign>
```

**Do NOT use `[bracket]` notation in C# projects** — brackets create `VisualBasicValue` nodes, causing validation failures for C#-only syntax.

---

## Workflow Types

### Sequence
Linear, top-to-bottom execution. **Most common** for legacy workflows.
```xml
<Sequence DisplayName="My Sequence" sap2010:WorkflowViewState.IdRef="Sequence_1">
  <Sequence.Variables>
    <Variable x:TypeArguments="x:String" Name="result" />
  </Sequence.Variables>
  <!-- Activities execute top to bottom -->
</Sequence>
```

### Flowchart
Visual branching with FlowStep, FlowDecision, and FlowSwitch nodes.
```xml
<Flowchart DisplayName="My Flowchart" sap2010:WorkflowViewState.IdRef="Flowchart_1">
  <Flowchart.StartNode>
    <x:Reference>__ReferenceID0</x:Reference>
  </Flowchart.StartNode>
  <FlowStep x:Name="__ReferenceID0">
    <!-- Activity + FlowStep.Next -->
  </FlowStep>
  <FlowDecision x:Name="__ReferenceID1">
    <FlowDecision.Condition>
      <mva:VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="condition" />
    </FlowDecision.Condition>
    <FlowDecision.True>
      <x:Reference>__ReferenceID0</x:Reference>
    </FlowDecision.True>
  </FlowDecision>
</Flowchart>
```

### State Machine
State-based workflow with transitions. Used in REFramework pattern.
```xml
<StateMachine InitialState="{x:Reference __ReferenceID_Init}" DisplayName="Process">
  <State x:Name="__ReferenceID_Init" DisplayName="Init">
    <State.Entry>
      <Sequence><!-- Init activities --></Sequence>
    </State.Entry>
    <State.Transitions>
      <Transition DisplayName="Success">
        <Transition.Condition>[initSuccess]</Transition.Condition>
        <Transition.To>
          <x:Reference>__ReferenceID_Process</x:Reference>
        </Transition.To>
      </Transition>
    </State.Transitions>
  </State>
  <State x:Name="__ReferenceID_End" DisplayName="End" IsFinal="True" />
</StateMachine>
```

For complete workflow type templates with ViewState, see [activity-docs/_XAML-GUIDE.md](./activity-docs/_XAML-GUIDE.md).

---

## Arguments (In/Out/InOut)

Arguments are declared in `<x:Members>` and define the workflow's public interface:

```xml
<x:Members>
  <x:Property Name="in_CustomerName" Type="InArgument(x:String)" />
  <x:Property Name="out_ProcessedCount" Type="OutArgument(x:Int32)" />
  <x:Property Name="io_DataTable" Type="InOutArgument(sd:DataTable)" />
</x:Members>
```

### Common Type Mappings

| XAML Type | .NET Type | Notes |
|-----------|-----------|-------|
| `x:String` | System.String | |
| `x:Int32` | System.Int32 | |
| `x:Int64` | System.Int64 | |
| `x:Boolean` | System.Boolean | |
| `x:Double` | System.Double | |
| `x:Object` | System.Object | |
| `x:Decimal` | System.Decimal | |
| `sd:DataTable` | System.Data.DataTable | Requires `xmlns:sd="clr-namespace:System.Data;assembly=System.Data"` |
| `s:DateTime` | System.DateTime | **Cannot** use `x:DateTime` — it's not in the XAML schema |
| `ss:SecureString` | System.Security.SecureString | Requires `xmlns:ss="clr-namespace:System.Security;assembly=mscorlib"` (NOT `xmlns:s` — SecureString is in `System.Security`, not `System`) |
| `scg:Dictionary(x:String, x:Object)` | Dictionary\<String, Object\> | |
| `scg:List(x:String)` | List\<String\> | |

**IMPORTANT:** The `x:` schema only supports: String, Int32, Int64, Double, Boolean, Byte, Single, Decimal, Char, Object, TimeSpan. Any other CLR type must use the appropriate namespace prefix (e.g., `s:DateTime`, `sd:DataTable`).

---

## Variables

Variables are scoped to their containing activity:

```xml
<Sequence.Variables>
  <Variable x:TypeArguments="x:String" Name="filePath" />
  <Variable x:TypeArguments="x:Int32" Name="counter" Default="0" />
  <Variable x:TypeArguments="x:Boolean" Name="isValid" Default="True" />
  <Variable x:TypeArguments="sd:DataTable" Name="dtResults" />
</Sequence.Variables>
```

Variables declared in an outer container are accessible in nested containers but not across invoked workflows (use Arguments for that).

---

## XAML Safety Rules

### ViewState Rules (Editing vs Generating)

ViewState controls how activities appear in the designer. The rules differ for editing vs generating:

**Editing existing workflows:**
- Do NOT modify the global `<sap2010:WorkflowViewState.ViewStateManager>` section
- Do NOT modify existing ViewState on nodes you're not changing
- When **adding new nodes** to an existing Flowchart/StateMachine, **DO generate ViewState** (ShapeLocation, ShapeSize, ConnectorLocation) for the new nodes — read existing node positions first to avoid overlap

**Generating new workflows:**
- **Sequence workflows:** ViewState is optional — Studio auto-manages `IsExpanded`
- **Flowchart workflows:** ViewState is **MANDATORY** — generate ShapeLocation, ShapeSize, ConnectorLocation for every FlowStep and FlowDecision, plus the Flowchart container's start node position
- **StateMachine workflows:** ViewState is **MANDATORY** — generate ShapeLocation, ShapeSize for every State, plus StateContainerWidth/Height on the container

**Without ViewState on Flowchart/StateMachine nodes, Studio stacks everything at (0,0) — producing an unusable jumbled pile.**

See the Flowchart and StateMachine ViewState Layout Guides in [activity-docs/_XAML-GUIDE.md](./activity-docs/_XAML-GUIDE.md) for coordinate systems, standard sizes, layout algorithms, and complete examples.

### Preserve xmlns Declarations
Never remove existing `xmlns` attributes from the root `<Activity>` element. Only add new ones as needed.

### Respect Expression Language
Always check `project.json` `expressionLanguage` before writing expressions. Mixing VB.NET and C# expression syntax causes build failures.

### Preserve Existing Structure
When editing XAML:
- Do not reformat or re-indent the entire file
- Only modify the specific section you need to change
- Use the `Edit` tool for targeted replacements (match exact `old_string`, replace with `new_string`)

### Validate After Every Change
Run `uip rpa-legacy validate` after every XAML modification. Do not batch multiple edits without validation.

### Unique Identifiers
- Every `x:Name` must be unique within the file
- Every `sap2010:WorkflowViewState.IdRef` must be unique
- `x:Reference` must match an existing `x:Name`

---

## Property Binding: Attributes vs Child Elements

### Attribute Syntax (Inline)
```xml
<ui:LogMessage Message="[myVar]" Level="Info" />
```

### Child Element Syntax (Property Element)
```xml
<Assign DisplayName="Set Result">
  <Assign.To>
    <OutArgument x:TypeArguments="x:String">[resultVar]</OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:String">["processed"]</InArgument>
  </Assign.Value>
</Assign>
```

**Simple values** (strings, enums, booleans, VB expressions) work as attributes. **Output properties** and **complex objects** typically require child element syntax.

---

## Managing References When Adding Packages (CRITICAL)

**Every package you use in a XAML file MUST have its assembly references and namespace imports added to that file.** Missing a single assembly reference causes all expressions using types from that assembly to fail validation.

This replicates what Studio does automatically when you drag an activity onto the canvas or add an import via the Imports panel. When generating XAML programmatically, you must do this manually.

### UiPath Activity Packages

When you add a UiPath activity package to `dependencies` in project.json and use its activities in a XAML file:

1. Add `xmlns` declaration to root `<Activity>` — use `XmlnsDeclaration` from `find-activities` output
2. Add `<AssemblyReference>` — use `AssemblyName` from `find-activities` output
3. Add `<x:String>` namespace imports — use the activity's `Namespace` from `find-activities` output

```xml
<!-- Example: after adding UiPath.Excel.Activities to dependencies -->
<!-- 1. xmlns on root Activity: -->
xmlns:ueab="clr-namespace:UiPath.Excel.Activities.Business;assembly=UiPath.Excel.Activities"

<!-- 2. Assembly reference: -->
<AssemblyReference>UiPath.Excel.Activities</AssemblyReference>

<!-- 3. Namespace imports: -->
<x:String>UiPath.Excel</x:String>
<x:String>UiPath.Excel.Activities.Business</x:String>
```

### Arbitrary .NET Packages

When you add a NuGet package (e.g., `CsvHelper`, `HtmlAgilityPack`) and use its classes in expressions or InvokeCode:

1. Add `<AssemblyReference>` with the package's assembly name
2. Add `<x:String>` namespace import for the namespace you use
3. If using in xmlns attributes, add `xmlns` declaration too

```xml
<!-- Example: after adding HtmlAgilityPack to dependencies -->
<AssemblyReference>HtmlAgilityPack</AssemblyReference>
<x:String>HtmlAgilityPack</x:String>
```

### C# Projects — Additional Baseline References

C# legacy projects need these **in addition** to the 16 VB.NET baseline refs:

```xml
<AssemblyReference>Microsoft.CSharp</AssemblyReference>
<AssemblyReference>System.Runtime.Serialization</AssemblyReference>
<AssemblyReference>System.ServiceModel</AssemblyReference>
<AssemblyReference>System.ServiceModel.Activities</AssemblyReference>
```

And this additional namespace import:
```xml
<x:String>System.Text</x:String>
```

---

## xmlns Prefix Deconfliction

`find-activities` may suggest the **same xmlns prefix** for activities from different CLR namespaces (e.g., both `LogMessage` and `ReadCsvFile` return `uca`). Using the same prefix for two different namespace URIs breaks the XAML.

**Before writing XAML:**
1. Collect all `XmlnsDeclaration` values from all activities you plan to use
2. Check for prefix collisions (same prefix, different `clr-namespace` URI)
3. Rename conflicting prefixes with descriptive abbreviations

**Example conflict:**
```xml
<!-- Both returned "uca" but point to different namespaces — CONFLICT -->
xmlns:uca="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
xmlns:uca="clr-namespace:UiPath.CSV.Activities;assembly=UiPath.Excel.Activities"

<!-- Fix: rename one prefix -->
xmlns:uca="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
xmlns:ucsvact="clr-namespace:UiPath.CSV.Activities;assembly=UiPath.Excel.Activities"
```

**Tip:** The `ui` schema prefix (`xmlns:ui="http://schemas.uipath.com/workflow/activities"`) covers most `UiPath.Core.Activities` — prefer it over CLR-based prefixes for core activities like LogMessage, InvokeCode, etc.

---

## XAML Generation Gotchas

1. **Every `x:Name` must be unique** — FlowSteps use `__ReferenceID0`, `__ReferenceID1`, etc.
2. **`x:Reference` must match an `x:Name`** — broken references crash the designer
3. **Bracket expressions `[expr]` are VB.NET only** — C# must use `<mca:CSharpValue>` elements
4. **XML escaping required**: `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`, `&` → `&amp;`
5. **Assembly references must include all dependencies** — missing refs cause compilation errors
6. **`expressionLanguage` must match XAML expression style** — VB project with C# expressions crashes
7. **Never add trailing `<x:Reference>` for Flowchart child nodes** — FlowStep/FlowDecision/FlowSwitch nodes defined inline as direct children of `<Flowchart>` must NOT be re-listed with `<x:Reference>` at the end. Only use `<x:Reference>` inside property elements (`Flowchart.StartNode`, `FlowStep.Next`, `FlowDecision.True/False`, etc.) to create cross-references
8. **State Machine needs exactly one `IsFinal="True"` state** for proper termination
9. **Legacy uses `assembly=mscorlib`** — not `assembly=System.Private.CoreLib` (which is .NET 6+)
10. **Scope activities require `ActivityAction<T>` body** — `ExcelApplicationScope`, `ExcelProcessScopeX`, `ExcelApplicationCard`, `WordApplicationScope`, etc. do NOT accept direct children. They require a `.Body` property with `ActivityAction<T>` and `DelegateInArgument`. See [common-pitfalls.md](./common-pitfalls.md#scope-activities-require-activityaction-body-critical-for-xaml-generation) for the complete template.

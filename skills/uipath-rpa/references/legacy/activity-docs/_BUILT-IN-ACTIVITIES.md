# Built-in Activities — Complete XAML Reference

**No `find-activities` or `type-definition` needed for these activities.** Use the XAML snippets below directly.

All VB.NET examples. For C# projects, replace `[expression]` brackets with `<mca:CSharpValue>` wrappers.

---

## Group 1: WF4 Built-in Activities

Default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — no xmlns prefix needed.

### 1. If

```xml
<If Condition="[age >= 18]" DisplayName="Check Age" sap2010:WorkflowViewState.IdRef="If_1">
  <If.Then>
    <Sequence DisplayName="Then">
      <!-- activities when true -->
    </Sequence>
  </If.Then>
  <If.Else>
    <Sequence DisplayName="Else">
      <!-- activities when false -->
    </Sequence>
  </If.Else>
</If>
```

Properties: `Condition` (InArgument Boolean), `If.Then` (single activity), `If.Else` (optional, single activity). Wrap multiple activities in a Sequence.

### 2. Assign

```xml
<Assign DisplayName="Set Counter" sap2010:WorkflowViewState.IdRef="Assign_1">
  <Assign.To>
    <OutArgument x:TypeArguments="x:Int32">[counter]</OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:Int32">[counter + 1]</InArgument>
  </Assign.Value>
</Assign>
```

Properties: `Assign.To` (OutArgument — target variable), `Assign.Value` (InArgument — source expression). Both need matching `x:TypeArguments`.

### 3. Sequence

```xml
<Sequence DisplayName="Main Sequence" sap2010:WorkflowViewState.IdRef="Sequence_1">
  <Sequence.Variables>
    <Variable x:TypeArguments="x:String" Name="filePath" />
    <Variable x:TypeArguments="x:Int32" Name="counter" Default="0" />
    <Variable x:TypeArguments="sd:DataTable" Name="dtData" />
  </Sequence.Variables>
  <!-- child activities execute top to bottom -->
</Sequence>
```

Properties: `Sequence.Variables` (local variables scoped to this Sequence), child activities in order.

### 4. TryCatch

```xml
<TryCatch DisplayName="Try Catch" sap2010:WorkflowViewState.IdRef="TryCatch_1">
  <TryCatch.Try>
    <Sequence DisplayName="Try">
      <!-- activities that may throw -->
    </Sequence>
  </TryCatch.Try>
  <TryCatch.Catches>
    <Catch x:TypeArguments="uic:BusinessRuleException" sap2010:WorkflowViewState.IdRef="Catch`1_1">
      <ActivityAction x:TypeArguments="uic:BusinessRuleException">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="uic:BusinessRuleException" Name="exception" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Catch BusinessRuleException">
          <!-- use [exception.Message] to access the error -->
        </Sequence>
      </ActivityAction>
    </Catch>
    <Catch x:TypeArguments="s:Exception" sap2010:WorkflowViewState.IdRef="Catch`1_2">
      <ActivityAction x:TypeArguments="s:Exception">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="s:Exception" Name="exception" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Catch System.Exception">
          <!-- generic catch-all -->
        </Sequence>
      </ActivityAction>
    </Catch>
  </TryCatch.Catches>
  <TryCatch.Finally>
    <!-- cleanup activities (always runs) -->
  </TryCatch.Finally>
</TryCatch>
```

**Required xmlns for exception types:**
```xml
xmlns:s="clr-namespace:System;assembly=mscorlib"
xmlns:uic="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
```

Each `Catch` needs `ActivityAction<ExceptionType>` with `DelegateInArgument` named `exception`. Order matters — put specific catches first.

### 5. Flowchart

```xml
<Flowchart DisplayName="Main Flowchart" sap2010:WorkflowViewState.IdRef="Flowchart_1">
  <Flowchart.StartNode>
    <x:Reference>__ReferenceID0</x:Reference>
  </Flowchart.StartNode>

  <FlowStep x:Name="__ReferenceID0">
    <!-- activity here -->
    <FlowStep.Next>
      <x:Reference>__ReferenceID1</x:Reference>
    </FlowStep.Next>
  </FlowStep>

  <!-- Do NOT add trailing <x:Reference> for child nodes here — they are already direct children -->
</Flowchart>
```

See `_XAML-GUIDE.md` for ViewState layout guide (MANDATORY for Flowcharts).

### 6. ForEach

```xml
<ForEach x:TypeArguments="x:String" DisplayName="For Each" sap2010:WorkflowViewState.IdRef="ForEach`1_1">
  <ForEach.Values>
    <InArgument x:TypeArguments="scg:IEnumerable(x:String)">[myList]</InArgument>
  </ForEach.Values>
  <ActivityAction x:TypeArguments="x:String">
    <ActivityAction.Argument>
      <DelegateInArgument x:TypeArguments="x:String" Name="item" />
    </ActivityAction.Argument>
    <Sequence DisplayName="Body">
      <!-- use [item] to access current element -->
    </Sequence>
  </ActivityAction>
</ForEach>
```

**Required xmlns:** `xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"`

`x:TypeArguments` sets the element type. Body is `ActivityAction<T>` with DelegateInArgument named `item`.

### 7. While

```xml
<While DisplayName="While Loop" sap2010:WorkflowViewState.IdRef="While_1">
  <While.Condition>
    <mva:VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" />
  </While.Condition>
  <Sequence DisplayName="Body">
    <!-- loop body -->
  </Sequence>
</While>
```

**Required xmlns:** `xmlns:mva="clr-namespace:Microsoft.VisualBasic.Activities;assembly=System.Activities"`

Condition uses `VisualBasicValue<Boolean>` with `ExpressionText` (not bracket notation).

### 8. DoWhile

```xml
<DoWhile DisplayName="Do While" sap2010:WorkflowViewState.IdRef="DoWhile_1">
  <DoWhile.Condition>
    <mva:VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="hasMore" />
  </DoWhile.Condition>
  <Sequence DisplayName="Body">
    <!-- runs at least once -->
  </Sequence>
</DoWhile>
```

Same as While but body executes before condition check.

### 9. Switch

```xml
<Switch x:TypeArguments="x:String" Expression="[status]" DisplayName="Switch" sap2010:WorkflowViewState.IdRef="Switch`1_1">
  <ui:LogMessage x:Key="Active" Message="[&quot;Status is Active&quot;]" DisplayName="Log Active" />
  <ui:LogMessage x:Key="Closed" Message="[&quot;Status is Closed&quot;]" DisplayName="Log Closed" />
  <Switch.Default>
    <ui:LogMessage Message="[&quot;Unknown status: &quot; &amp; status]" DisplayName="Log Default" />
  </Switch.Default>
</Switch>
```

`x:TypeArguments` sets the switch type. Cases use `x:Key="value"`. `Switch.Default` for the default case.

### 10. Throw

```xml
<Throw Exception="[New BusinessRuleException(&quot;Invalid data&quot;)]" DisplayName="Throw" sap2010:WorkflowViewState.IdRef="Throw_1" />
```

Use short-form class names (namespace must be imported). For complex messages, assign to a variable first then `[New BusinessRuleException(errorMsg)]`.

### 11. Rethrow

```xml
<Rethrow DisplayName="Rethrow" sap2010:WorkflowViewState.IdRef="Rethrow_1" />
```

No properties. Use inside a Catch block to re-throw the caught exception.

### 12. Delay

```xml
<Delay Duration="[TimeSpan.FromSeconds(5)]" DisplayName="Delay" sap2010:WorkflowViewState.IdRef="Delay_1" />
```

`Duration` is `InArgument<TimeSpan>`. Common: `TimeSpan.FromSeconds(N)`, `TimeSpan.FromMinutes(N)`, `TimeSpan.FromMilliseconds(N)`.

### 13. Parallel

```xml
<Parallel DisplayName="Parallel" sap2010:WorkflowViewState.IdRef="Parallel_1">
  <Sequence DisplayName="Branch 1">
    <!-- first parallel branch -->
  </Sequence>
  <Sequence DisplayName="Branch 2">
    <!-- second parallel branch -->
  </Sequence>
</Parallel>
```

Direct child activities execute in parallel. No ActivityAction pattern — just list branches as children.

### 14. FlowDecision (inside Flowchart)

```xml
<FlowDecision x:Name="__ReferenceID1" DisplayName="Has Data?">
  <FlowDecision.Condition>
    <mva:VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="dtData.Rows.Count > 0" />
  </FlowDecision.Condition>
  <FlowDecision.True>
    <x:Reference>__ReferenceID2</x:Reference>
  </FlowDecision.True>
  <FlowDecision.False>
    <x:Reference>__ReferenceID3</x:Reference>
  </FlowDecision.False>
</FlowDecision>
```

### 15. FlowSwitch (inside Flowchart)

```xml
<FlowSwitch x:TypeArguments="x:String" x:Name="__ReferenceID4" DisplayName="Route by Type"
  Expression="[documentType]">
  <FlowStep x:Key="Invoice">
    <x:Reference>__ReferenceID5</x:Reference>
  </FlowStep>
  <FlowStep x:Key="Receipt">
    <x:Reference>__ReferenceID6</x:Reference>
  </FlowStep>
  <FlowSwitch.Default>
    <x:Reference>__ReferenceID7</x:Reference>
  </FlowSwitch.Default>
</FlowSwitch>
```

---

## Group 2: UiPath Core Activities

All use `xmlns:ui="http://schemas.uipath.com/workflow/activities"`.

### 16. LogMessage

```xml
<ui:LogMessage DisplayName="Log Message" sap2010:WorkflowViewState.IdRef="LogMessage_1"
  Message="[&quot;Processing item: &quot; &amp; itemName]"
  Level="Info" />
```

| Property | Type | Values |
|----------|------|--------|
| `Message` | InArgument(Object) | Any expression — converted via `.ToString()` |
| `Level` | LogLevel enum | `Trace`, `Info`, `Warn`, `Error`, `Fatal` |

### 17. InvokeCode

```xml
<ui:InvokeCode Code="result = input.Trim().ToUpper()" Language="VBNet"
  DisplayName="Invoke Code" sap2010:WorkflowViewState.IdRef="InvokeCode_1">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="input">[rawText]</InArgument>
      <OutArgument x:TypeArguments="x:String" x:Key="result">[cleanText]</OutArgument>
    </scg:Dictionary>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>
```

| Property | Type | Values |
|----------|------|--------|
| `Code` | String | VB.NET or C# method body (not class/module wrapper) |
| `Language` | NetLanguage enum | `VBNet`, `CSharp` |
| `Arguments` | Dictionary(String, Argument) | In/Out/InOut arguments keyed by name |
| `ContinueOnError` | InArgument(Boolean) | Suppresses runtime errors only (compilation errors always throw) |

**Required xmlns:** `xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"`

See `_INVOKE-CODE.md` for full reference (generated code structure, compilation details, gotchas).

### 18. InvokeWorkflowFile

```xml
<ui:InvokeWorkflowFile DisplayName="Invoke Process.xaml"
  WorkflowFileName="Workflows\Process.xaml" UnSafe="False"
  sap2010:WorkflowViewState.IdRef="InvokeWorkflowFile_1">
  <ui:InvokeWorkflowFile.Arguments>
    <InArgument x:TypeArguments="x:String" x:Key="in_FilePath">[inputPath]</InArgument>
    <OutArgument x:TypeArguments="x:Boolean" x:Key="out_Success">[wasSuccessful]</OutArgument>
  </ui:InvokeWorkflowFile.Arguments>
</ui:InvokeWorkflowFile>
```

| Property | Type | Notes |
|----------|------|-------|
| `WorkflowFileName` | InArgument(String) | Relative path from project root |
| `UnSafe` | Boolean | `True` = isolated execution |
| `Arguments` | Dictionary | Keys match target workflow's argument names |
| `Timeout` | InArgument(TimeSpan) | Optional execution timeout |
| `ContinueOnError` | InArgument(Boolean) | Continue on invocation failure |

### 19. ForEachRow

```xml
<ui:ForEachRow DisplayName="For Each Row" sap2010:WorkflowViewState.IdRef="ForEachRow_1"
  DataTable="[dtData]">
  <ui:ForEachRow.Body>
    <ActivityAction x:TypeArguments="sd:DataRow">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="sd:DataRow" Name="CurrentRow" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Body">
        <!-- use [CurrentRow("ColumnName").ToString()] to access cell values -->
      </Sequence>
    </ActivityAction>
  </ui:ForEachRow.Body>
</ui:ForEachRow>
```

**Required xmlns:** `xmlns:sd="clr-namespace:System.Data;assembly=System.Data"`

| Property | Type | Notes |
|----------|------|-------|
| `DataTable` | InArgument(DataTable) | Table to iterate |
| `Body` | ActivityAction(DataRow) | DelegateInArgument named `CurrentRow` |

### 20. AddDataRow

```xml
<!-- Add row from array -->
<ui:AddDataRow DisplayName="Add Data Row" sap2010:WorkflowViewState.IdRef="AddDataRow_1"
  DataTable="[dtTable]">
  <ui:AddDataRow.ArrayRow>
    <InArgument x:TypeArguments="x:Object[]">[New Object() {"Value1", 123, True}]</InArgument>
  </ui:AddDataRow.ArrayRow>
</ui:AddDataRow>
```

| Property | Type | Notes |
|----------|------|-------|
| `DataTable` | InOutArgument(DataTable) | Table to add row to |
| `ArrayRow` | InArgument(Object[]) | Array of column values |
| `DataRow` | InArgument(DataRow) | Alternative: existing DataRow (mutually exclusive with ArrayRow) |

### 21. BuildDataTable — Use InvokeCode Instead

`BuildDataTable` exists but its `TableInfo` property is a complex .NET DataTable XML schema generated by Studio's designer wizard. It is **not practical to construct manually** — the XML includes XSD schema declarations, namespace URIs, column type metadata, and assembly-qualified type names.

**Recommended: create DataTables with InvokeCode:**

```xml
<ui:InvokeCode Language="VBNet" DisplayName="Build DataTable"
  sap2010:WorkflowViewState.IdRef="InvokeCode_BDT"
  Code="Dim dt As New DataTable(&quot;Results&quot;)&#xA;dt.Columns.Add(&quot;Name&quot;, GetType(String))&#xA;dt.Columns.Add(&quot;Amount&quot;, GetType(Double))&#xA;dt.Columns.Add(&quot;IsActive&quot;, GetType(Boolean))&#xA;dt.Columns(&quot;Name&quot;).MaxLength = 100&#xA;result = dt">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <OutArgument x:TypeArguments="sd:DataTable" x:Key="result">[dtResults]</OutArgument>
    </scg:Dictionary>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>
```

**The VB.NET code inside** (readable form):
```vb
Dim dt As New DataTable("Results")
dt.Columns.Add("Name", GetType(String))
dt.Columns.Add("Amount", GetType(Double))
dt.Columns.Add("IsActive", GetType(Boolean))
dt.Columns("Name").MaxLength = 100
result = dt
```

**To also add initial rows**, append to the code:
```vb
dt.Rows.Add("Alice", 100.50, True)
dt.Rows.Add("Bob", 0, False)
dt.Rows.Add(DBNull.Value, DBNull.Value, DBNull.Value)  ' null row for edge case testing
```

**Why not BuildDataTable:** The `TableInfo` XML format is the output of `DataTable.WriteXml(writer, XmlWriteMode.WriteSchema)` — a verbose XSD schema that requires precise namespace declarations, column metadata, and assembly-qualified type names. Studio's GUI generates this automatically; manual construction is error-prone and not worth the effort.

---

## Required xmlns Summary

These xmlns are needed beyond the baseline when using activities above:

| xmlns | Needed For |
|-------|-----------|
| `xmlns:mva="clr-namespace:Microsoft.VisualBasic.Activities;assembly=System.Activities"` | While/DoWhile conditions (VisualBasicValue) |
| `xmlns:sd="clr-namespace:System.Data;assembly=System.Data"` | ForEachRow (DataRow), DataTable variables |
| `xmlns:s="clr-namespace:System;assembly=mscorlib"` | TryCatch (System.Exception), DateTime |
| `xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"` | ForEach (IEnumerable), InvokeCode Arguments |
| `xmlns:uic="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"` | TryCatch (BusinessRuleException) |

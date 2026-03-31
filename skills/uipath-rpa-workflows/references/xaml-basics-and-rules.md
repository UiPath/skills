# XAML basics and rules

Read this file when: you are creating or editing XAML workflow files. Covers file anatomy, safety rules, expressions, and examples.

## XAML file anatomy

Every UiPath XAML workflow has this structure:

```xml
<Activity mc:Ignorable="sap sap2010 sads" x:Class="ProjectName.FileName"
  xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:sap="http://schemas.microsoft.com/netfx/2009/xaml/activities/presentation"
  xmlns:sap2010="http://schemas.microsoft.com/netfx/2010/xaml/activities/presentation"
  xmlns:sads="http://schemas.microsoft.com/netfx/2010/xaml/activities/debugger"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">

  <TextExpression.NamespacesForImplementation>
    <sco:Collection x:TypeArguments="x:String"
      xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib">
      <x:String>System</x:String>
      <x:String>System.Collections.Generic</x:String>
      <x:String>System.Linq</x:String>
    </sco:Collection>
  </TextExpression.NamespacesForImplementation>

  <TextExpression.ReferencesForImplementation>
    <sco:Collection x:TypeArguments="AssemblyReference"
      xmlns:sco="clr-namespace:System.Collections.ObjectModel;assembly=System.Private.CoreLib">
      <AssemblyReference>System</AssemblyReference>
    </sco:Collection>
  </TextExpression.ReferencesForImplementation>

  <x:Members>
    <x:Property Name="in_Name" Type="InArgument(x:String)" />
    <x:Property Name="out_Result" Type="OutArgument(x:Int32)" />
  </x:Members>

  <Sequence DisplayName="Main Sequence">
    <Sequence.Variables>
      <Variable x:TypeArguments="x:String" Name="tempVar" Default="hello" />
    </Sequence.Variables>
    <!-- Activities go here -->
  </Sequence>

  <!-- ViewState section (DO NOT EDIT) -->
</Activity>
```

## Safety rules

1. **Never touch ViewState.** The `<sap2010:WorkflowViewState.ViewStateManager>` section is managed by Studio. Corrupting it breaks the designer.
2. **Never remove xmlns declarations.** Only add new ones. Removing a referenced namespace causes validation errors.
3. **Check expression language first.** Read `project.json` `expressionLanguage`. VB uses `[brackets]`, C# uses `<CSharpValue>`/`<CSharpReference>`.
4. **Use `get-default-activity-xaml` output.** Never construct activity XAML from memory.
5. **Edit surgically.** Do not reformat the entire file. Use `Edit` for targeted replacements only.
6. **Validate after every change.** Run `get-errors` immediately.

## Workflow types

**Sequence**: linear, top-to-bottom execution. Best for straightforward processes.
```xml
<Sequence DisplayName="My Sequence">
  <!-- Activities execute in order -->
</Sequence>
```

**Flowchart**: branching with decision nodes. Uses `FlowStep`, `FlowDecision`, `x:Name`/`x:Reference`.
```xml
<Flowchart DisplayName="My Flowchart">
  <Flowchart.StartNode>
    <FlowStep x:Name="__ReferenceID0">...</FlowStep>
  </Flowchart.StartNode>
</Flowchart>
```

**State Machine**: state-based with transitions. Best for long-running processes.

## Arguments

Add `x:Property` elements inside `<x:Members>`. Naming convention: `in_`, `out_`, `io_` prefixes.

```xml
<x:Members>
  <x:Property Name="in_CustomerName" Type="InArgument(x:String)" />
  <x:Property Name="out_Count" Type="OutArgument(x:Int32)" />
  <x:Property Name="io_Data" Type="InOutArgument(scg:List(x:String))" />
</x:Members>
```

## Variables

Add inside the container's `.Variables` block. Variables are scoped to their containing activity.

```xml
<Sequence.Variables>
  <Variable x:TypeArguments="x:String" Name="filePath" />
  <Variable x:TypeArguments="x:Int32" Name="counter" Default="0" />
</Sequence.Variables>
```

For `DateTime`, `Guid`, etc., use `s:` prefix (not `x:`). See common-pitfalls.md for details.

## Expressions

### C# projects

Use `<CSharpValue>` for reads and `<CSharpReference>` for writes. No namespace prefix on these elements.

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

Do NOT use `[bracket]` shorthand in C# projects. Brackets create VB expression nodes.

### VB projects

Use `[bracket]` shorthand:

```xml
<Assign sap2010:WorkflowViewState.IdRef="Assign_1">
  <Assign.To>
    <OutArgument x:TypeArguments="x:String">[fullName]</OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:String">[firstName & " " & lastName]</InArgument>
  </Assign.Value>
</Assign>
```

## Property binding

**Attribute syntax** (simple values, enums, VB expressions):
```xml
<ui:LogMessage Message="[myVar]" Level="Info" />
```

**Child element syntax** (output properties, complex objects):
```xml
<ui:SomeActivity>
  <ui:SomeActivity.Result>
    <OutArgument x:TypeArguments="x:String">[outputVar]</OutArgument>
  </ui:SomeActivity.Result>
</ui:SomeActivity>
```

If an attribute-form output binding causes a validation error, try child element syntax.

## Resource types (IResource / ILocalResource)

Some properties accept `IResource` instead of strings:

```xml
<InArgument x:TypeArguments="upr:ILocalResource">
  <CSharpValue x:TypeArguments="upr:ILocalResource">LocalResource.FromPath(filePath)</CSharpValue>
</InArgument>
```

Required namespace: `UiPath.Platform.ResourceHandling`.

## ConnectorActivity internals

For Integration Service connector activities (`isactr:ConnectorActivity`):

| Property | Editable? | Notes |
|----------|-----------|-------|
| `Configuration` | Never | Compressed blob from `get-default-activity-xaml`. Never parse or construct. |
| `ConnectionId` | Yes | GUID from `uip is connections list`. |
| `UiPathActivityTypeId` | Never | From `get-default-activity-xaml` or `find-activities`. |
| `DisplayName` | Yes | Human-readable name. |

`FieldObjects` hold input/output fields. You can change input values and bind to variables, but do not change field names, types, or add/remove fields.

JIT-generated assembly names are unpredictable (derived from SHA-512 hashes). Always get them from `get-default-activity-xaml`.

# Common Activity Card

**Package anchor:** `UiPath.System.Activities` 26.4 (verified against 26.4.1-preview).

Copy-safe snippets for the 14 activities: `Sequence` · `If` · `Switch<T>` · `TryCatch` · `While` · `DoWhile` · `ForEach<T>` · `Assign` · `MultipleAssign` · `LogMessage` · `WriteLine` · `Delay` · `Throw` · `Rethrow`.

**Supersedes the Rule 21 discovery procedure for these activities only:** when authoring one, skip `activities find`, `activities get-default-xaml`, and the per-activity `<Activity>.md` read; copy its snippet here. For every other activity, full Rule 21 applies. Self-extending this card by personal judgment ("this one feels simple, I'll skip the procedure") is the failure mode.

## How to read the snippets

Insert fragments in a complete `<Activity>` root declaring:

```xml
xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
xmlns:ui="http://schemas.uipath.com/workflow/activities"
```

Entries that need additional prefixes (`xmlns:s` for `System` types, `xmlns:sc` for `System.Collections`) call them out in the entry's **Class:** line.

Use `assembly=System.Private.CoreLib` for modern Windows-target projects and `assembly=mscorlib` for Legacy (.NET 4.6.1). Add `sap2010:WorkflowViewState.IdRef` to every inserted activity element per [xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md) Rule 25: `<TypeName>_<next free N>`; never change existing IdRefs. ViewState is optional for `Sequence` (Rule 20), but required when the parent is `Flowchart`, `StateMachine`, or `ProcessDiagram`.

Snippets use property-element `<VisualBasicValue>` / `<VisualBasicReference>`. For C# expression projects, apply [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md). Unless stated otherwise, use the standard activities namespace without `ui:` and wrap activity body/branch slots in `Sequence` per Rule 24, including single-child slots.

## Group A — Control flow

### Sequence
**Class:** `System.Activities.Statements.Sequence`; standard activities namespace; no `ui:` prefix.

```xml
<Sequence DisplayName="Sequence"><!-- child activities in execution order --></Sequence>
```

Use `Sequence` as the Rule 24 container in every body/branch slot of `If`, `Switch`, `TryCatch`, `While`, `DoWhile`, `ForEach`, `Pick`, etc., including a single child. Declare `<Sequence.Variables>` only for variables it owns.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/Sequence.md`](activity-docs/UiPath.System.Activities/26.4/activities/Sequence.md)

### If
**Class:** `System.Activities.Statements.If`; standard activities namespace; no `ui:` prefix.

```xml
<If DisplayName="If"><If.Condition><InArgument x:TypeArguments="x:Boolean"><VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" /></InArgument></If.Condition><If.Then><Sequence DisplayName="Then"><!-- then branch --></Sequence></If.Then><If.Else><Sequence DisplayName="Else"><!-- else branch --></Sequence></If.Else></If>
```

Wrap both slots in `Sequence`; omit unused `<If.Else>` and never emit an empty slot. For multiple `else if`, use `IfElseIfV2` (off this card; see `ElseIf.md`).

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/If.md`](activity-docs/UiPath.System.Activities/26.4/activities/If.md)

### Switch&lt;T&gt;
**Class:** `System.Activities.Statements.Switch`1`; standard activities namespace; no `ui:` prefix.

Typed `Int32` example; change `x:TypeArguments` as needed:

```xml
<Switch x:TypeArguments="x:Int32" DisplayName="Switch"><Switch.Expression><InArgument x:TypeArguments="x:Int32"><VisualBasicValue x:TypeArguments="x:Int32" ExpressionText="status" /></InArgument></Switch.Expression><Sequence x:Key="1" DisplayName="Case 1"><!-- case body for status == 1 --></Sequence><Sequence x:Key="2" DisplayName="Case 2"><!-- case body for status == 2 --></Sequence><Switch.Default><Sequence DisplayName="Default"><!-- fallback body --></Sequence></Switch.Default></Switch>
```

Wrap every case and default in `Sequence`. Put each literal key directly on its child with `x:Key`; do not declare a `Cases` dictionary. For strings use `x:TypeArguments="x:String"` and `x:Key="someString"`.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/Switch.md`](activity-docs/UiPath.System.Activities/26.4/activities/Switch.md)

### TryCatch
**Class:** `System.Activities.Statements.TryCatch`; standard namespace plus `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"` for exception types; Legacy uses `assembly=mscorlib`.

```xml
<TryCatch DisplayName="Try Catch"><TryCatch.Try><Sequence DisplayName="Try"><!-- guarded body --></Sequence></TryCatch.Try><TryCatch.Catches><Catch x:TypeArguments="s:Exception"><ActivityAction x:TypeArguments="s:Exception"><ActivityAction.Argument><DelegateInArgument x:TypeArguments="s:Exception" Name="exception" /></ActivityAction.Argument><Sequence DisplayName="Catch"><!-- handler body; reference "exception" --></Sequence></ActivityAction></Catch></TryCatch.Catches><TryCatch.Finally><Sequence DisplayName="Finally"><!-- finally body --></Sequence></TryCatch.Finally></TryCatch>
```

Wrap `Try`, every `Catch.Action`, and `Finally` in `Sequence`. Each `Catch` requires its own `<ActivityAction x:TypeArguments="...">` holding a `<DelegateInArgument x:TypeArguments="..." Name="exception" />`; `Name` is the handler variable. Put specific exception types before `s:Exception`; omit unused `Finally`. For exception taxonomy, Retry Scope, ContinueOnError, screenshot-on-error, and Global Exception Handler see [error-handling-guide.md](error-handling-guide.md).

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/TryCatch.md`](activity-docs/UiPath.System.Activities/26.4/activities/TryCatch.md)

### While
**Class:** `UiPath.Core.Activities.InterruptibleWhile` (Studio emits this, not `System.Activities.Statements.While`); `xmlns:ui="http://schemas.uipath.com/workflow/activities"`.

```xml
<ui:InterruptibleWhile DisplayName="While"><ui:InterruptibleWhile.Condition><VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" /></ui:InterruptibleWhile.Condition><ui:InterruptibleWhile.Body><Sequence DisplayName="Body"><!-- iteration body --></Sequence></ui:InterruptibleWhile.Body></ui:InterruptibleWhile>
```

`MaxIterations` is `InArgument<int>`; `0` means **unlimited** and is the default. Set to a positive value to guard against infinite loops. `CurrentIndex` is `OutArgument<int>`, zero-based, and may bind to a variable. Wrap the body in `Sequence`. The condition runs before each iteration; false on entry means no execution.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/While.md`](activity-docs/UiPath.System.Activities/26.4/activities/While.md)

### Do While
**Class:** `UiPath.Core.Activities.InterruptibleDoWhile` (Studio emits this, not `System.Activities.Statements.DoWhile`); `xmlns:ui="http://schemas.uipath.com/workflow/activities"`.

```xml
<ui:InterruptibleDoWhile DisplayName="Do While"><ui:InterruptibleDoWhile.Body><Sequence DisplayName="Body"><!-- iteration body --></Sequence></ui:InterruptibleDoWhile.Body><ui:InterruptibleDoWhile.Condition><VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" /></ui:InterruptibleDoWhile.Condition></ui:InterruptibleDoWhile>
```

`MaxIterations` is `InArgument<int>`; `0` means **unlimited** and is the default. `CurrentIndex` is `OutArgument<int>` and zero-based. Wrap the body in `Sequence`. The body executes at least once; the condition runs afterward.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/DoWhile.md`](activity-docs/UiPath.System.Activities/26.4/activities/DoWhile.md)

### For Each&lt;T&gt;
**Class:** `UiPath.Core.Activities.ForEach`1` (Studio emits this, not `System.Activities.Statements.ForEach<T>`); `xmlns:ui="http://schemas.uipath.com/workflow/activities"`; add `xmlns:sc="clr-namespace:System.Collections;assembly=System.Private.CoreLib"` for non-generic `IEnumerable` (Legacy uses `assembly=mscorlib`).

Typed `String` example; change the outer, `ActivityAction`, and `DelegateInArgument` `x:TypeArguments` together:

```xml
<ui:ForEach x:TypeArguments="x:String" DisplayName="For Each"><ui:ForEach.Values><InArgument x:TypeArguments="sc:IEnumerable"><VisualBasicValue x:TypeArguments="sc:IEnumerable" ExpressionText="myList" /></InArgument></ui:ForEach.Values><ui:ForEach.Body><ActivityAction x:TypeArguments="x:String"><ActivityAction.Argument><DelegateInArgument x:TypeArguments="x:String" Name="item" /></ActivityAction.Argument><Sequence DisplayName="Body"><!-- iteration body; reference "item" --></Sequence></ActivityAction></ui:ForEach.Body></ui:ForEach>
```

`Values` is `InArgument<System.Collections.IEnumerable>`, not `IEnumerable<T>` (verified against `ForEachBase<T>.Values`); `T` comes from the outer activity. `Body` is `ActivityAction<T>` and must use `<ui:ForEach.Body>` (it is NOT the ContentProperty); placing a bare `<ActivityAction>` directly inside `<ui:ForEach>` produces `Cannot set unknown member '...Implementation'`. `MaxIterations` is `InArgument<int>` (`0` = **unlimited**, default `0`); `CurrentIndex` is `OutArgument<int>` and zero-based. The iterator name is `DelegateInArgument.Name` (auto-suggested by Studio based on element type); wrap the body in `Sequence`.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/ForEach.md`](activity-docs/UiPath.System.Activities/26.4/activities/ForEach.md)

## Group B — Data + logging

### Assign
**Class:** `System.Activities.Statements.Assign` — no activity type argument; type its arguments. Standard namespace; no `ui:` prefix.

```xml
<Assign DisplayName="Assign"><Assign.To><OutArgument x:TypeArguments="x:Int32"><VisualBasicReference x:TypeArguments="x:Int32" ExpressionText="counter" /></OutArgument></Assign.To><Assign.Value><InArgument x:TypeArguments="x:Int32"><VisualBasicValue x:TypeArguments="x:Int32" ExpressionText="counter + 1" /></InArgument></Assign.Value></Assign>
```

Argument typing surfaces mismatches at `validate`. `To` must be writable (variable, argument, or indexer); use `VisualBasicReference`/`CSharpReference` for it and `VisualBasicValue`/`CSharpValue` for the readable side. Use one target per `Assign`. In a Windows project, put two or more consecutive assignments in one `Multiple Assign`.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/Assign.md`](activity-docs/UiPath.System.Activities/26.4/activities/Assign.md)

### Multiple Assign
**Class:** `UiPath.Core.Activities.MultipleAssign`; Windows only. Portable projects fail `validate` with `Cannot create unknown type '{http://schemas.uipath.com/workflow/activities}MultipleAssign'`; use one `Assign` per target there, even though installed docs include `MultipleAssign.md`. Prefix `xmlns:ui="http://schemas.uipath.com/workflow/activities"`; add `xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"` (Legacy uses `assembly=mscorlib`).

```xml
<ui:MultipleAssign DisplayName="Multiple Assign"><ui:MultipleAssign.AssignOperations><scg:List x:TypeArguments="ui:AssignOperation" Capacity="4"><ui:AssignOperation><ui:AssignOperation.To><OutArgument x:TypeArguments="x:String"><VisualBasicReference x:TypeArguments="x:String" ExpressionText="trimmedName" /></OutArgument></ui:AssignOperation.To><ui:AssignOperation.Value><InArgument x:TypeArguments="x:String"><VisualBasicValue x:TypeArguments="x:String" ExpressionText="fullName.Trim()" /></InArgument></ui:AssignOperation.Value></ui:AssignOperation><ui:AssignOperation><ui:AssignOperation.To><OutArgument x:TypeArguments="x:String"><VisualBasicReference x:TypeArguments="x:String" ExpressionText="upperName" /></OutArgument></ui:AssignOperation.To><ui:AssignOperation.Value><InArgument x:TypeArguments="x:String"><VisualBasicValue x:TypeArguments="x:String" ExpressionText="trimmedName.ToUpperInvariant()" /></InArgument></ui:AssignOperation.Value></ui:AssignOperation></scg:List></ui:MultipleAssign.AssignOperations></ui:MultipleAssign>
```

`AssignOperations` is hidden `List<AssignOperation>`; each operation has one typed `To` and `Value`, target types may mix, operations run in list order, and later values may read earlier targets. A failed operation reports its value and target expressions. C# uses `CSharpReference`/`CSharpValue` in this property-element form; the package attribute form (`To="[firstName]"`) is VB bracket syntax. Shape was verified against 26.8.2 on Windows.

**Long-form:** the installed package's `{PROJECT_DIR}/.local/docs/packages/UiPath.System.Activities/activities/MultipleAssign.md` (no bundled copy); snippet shape verified against 26.8.2 on a Windows project.

### Log Message
**Class:** `UiPath.Core.Activities.LogMessage`; prefix `xmlns:ui="http://schemas.uipath.com/workflow/activities"`; no extra prefix (`x:Object` uses `xmlns:x`).

```xml
<ui:LogMessage Level="Info" DisplayName="Log Message"><ui:LogMessage.Message><InArgument x:TypeArguments="x:Object"><VisualBasicValue x:TypeArguments="x:Object" ExpressionText="$&quot;Processed {count} items&quot;" /></InArgument></ui:LogMessage.Message></ui:LogMessage>
```

`Level` is `InArgument<LogLevel>`, required in practice, defaults to `Info`, and is hidden from `get-default-xaml`; values are `Trace` | `Info` | `Warn` | `Error` | `Fatal`. `Message` is `InArgument<object>`, not `string`; it accepts any expression and calls `.ToString()`. VB bracket shorthand supports composite expressions such as `[$"x = {x}"]`; C# uses `<CSharpValue x:TypeArguments="x:Object">...</CSharpValue>`. Prefer `LogMessage` for Orchestrator output; omit explicit `Level` only when `Info` is desired.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/LogMessage.md`](activity-docs/UiPath.System.Activities/26.4/activities/LogMessage.md)

### Write Line
**Class:** `System.Activities.Statements.WriteLine`; standard namespace; no `ui:` prefix.

```xml
<WriteLine DisplayName="Write Line"><WriteLine.Text><InArgument x:TypeArguments="x:String"><VisualBasicValue x:TypeArguments="x:String" ExpressionText="$&quot;processed {count} items&quot;" /></InArgument></WriteLine.Text></WriteLine>
```

Writes to stdout only and is invisible in Orchestrator; prefer `LogMessage` when Orchestrator visibility matters. Do not set `TextWriter`; its default (`Console.Out`) is correct for Studio and `uip rpa run`.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/WriteLine.md`](activity-docs/UiPath.System.Activities/26.4/activities/WriteLine.md)

### Delay
**Class:** `System.Activities.Statements.Delay`; standard namespace plus `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"` for `TimeSpan`; Legacy uses `assembly=mscorlib`.

```xml
<Delay DisplayName="Delay"><Delay.Duration><InArgument x:TypeArguments="s:TimeSpan"><VisualBasicValue x:TypeArguments="s:TimeSpan" ExpressionText="TimeSpan.FromSeconds(5)" /></InArgument></Delay.Duration></Delay>
```

`Duration` must produce `TimeSpan`. VB supports `[TimeSpan.FromSeconds(5)]`; C# uses `<CSharpValue x:TypeArguments="s:TimeSpan">TimeSpan.FromSeconds(5)</CSharpValue>` or `Duration="00:00:05"`. It blocks the workflow thread for the full duration; avoid it in `ForEach`/`While` bodies. Do not wait on external state with `Delay`; use `RetryScope`, `WaitForElement`, or a polling loop with a `Condition`.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/Delay.md`](activity-docs/UiPath.System.Activities/26.4/activities/Delay.md)

### Throw
**Class:** `System.Activities.Statements.Throw`; standard namespace plus `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"` for exception arguments; Legacy uses `assembly=mscorlib`.

```xml
<Throw DisplayName="Throw"><Throw.Exception><InArgument x:TypeArguments="s:Exception"><VisualBasicValue x:TypeArguments="s:Exception" ExpressionText="new InvalidOperationException(&quot;Invoice total is negative&quot;)" /></InArgument></Throw.Exception></Throw>
```

`Exception` is a constructor expression, not a string; `Throw.Exception = "message"` is invalid. Use a domain-specific type such as `BusinessRuleException` when `Catch` handlers must distinguish business from system errors. Use `Rethrow` inside a `Catch` body to preserve the original stack trace.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/Throw.md`](activity-docs/UiPath.System.Activities/26.4/activities/Throw.md)

### Rethrow
**Class:** `System.Activities.Statements.Rethrow`; standard namespace; no `ui:` prefix.

```xml
<Rethrow DisplayName="Rethrow" />
```

It has zero properties and is valid only inside a `Catch.Action` body; elsewhere it causes runtime `InvalidOperationException`. It preserves the original stack trace. Use `Throw new <Type>(...)` to translate the exception, and place `Rethrow` last in the `Catch` body because following content is unreachable.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/Rethrow.md`](activity-docs/UiPath.System.Activities/26.4/activities/Rethrow.md)
# Common Activity Card

**Package anchor:** `UiPath.System.Activities` 26.4 (verified against 26.4.1-preview).

Copy-safe snippets for the 14 activities listed below. **Supersedes the Rule 21 discovery procedure for these activities only** — when authoring one of these, skip `activities find`, skip `activities get-default-xaml`, skip the per-activity `<Activity>.md` read, and copy the snippet here.

For every other activity, full Rule 21 applies. Self-extending this card by personal judgment ("this one feels simple, I'll skip the procedure") is the failure mode.

## Card entries

`Sequence` · `If` · `Switch<T>` · `TryCatch` · `While` · `DoWhile` · `ForEach<T>` · `Assign` · `MultipleAssign` · `LogMessage` · `WriteLine` · `Delay` · `Throw` · `Rethrow`

## How to read the snippets

Snippets below are **fragments** intended to drop inside a complete `<Activity>` root. The root must declare:

```xml
xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
xmlns:ui="http://schemas.uipath.com/workflow/activities"
```

Entries that need additional prefixes (`xmlns:s` for `System` types, `xmlns:sc` for `System.Collections`) call them out in the "XAML prefix" line. For modern Windows-target projects use `assembly=System.Private.CoreLib`; for Legacy (.NET 4.6.1) projects use `assembly=mscorlib`.

Snippets use the property-element form with `<VisualBasicValue>` / `<VisualBasicReference>`. For C# expression projects, apply [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md).

---

## Group A — Control flow

### Sequence
**Class:** `System.Activities.Statements.Sequence`
**XAML prefix:** standard activities namespace (`xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"`); no `ui:` prefix.

**Snippet:**
```xml
<Sequence DisplayName="Sequence">
  <!-- child activities in execution order -->
</Sequence>
```

**Notes:** `Sequence` is the canonical container wrap required by Rule 24 in every body/branch slot of `If`, `Switch`, `TryCatch`, `While`, `DoWhile`, `ForEach`, `Pick`, etc. — even with a single child. Declare `<Sequence.Variables>` only when this sequence owns local variables. ViewState is **optional** for Sequences (Rule 20); required only when the parent is `Flowchart`, `StateMachine`, or `ProcessDiagram`.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/Sequence.md`](activity-docs/UiPath.System.Activities/26.4/activities/Sequence.md)

---

### If
**Class:** `System.Activities.Statements.If`
**XAML prefix:** standard activities namespace; no `ui:` prefix.

**Snippet:**
```xml
<If DisplayName="If">
  <If.Condition>
    <InArgument x:TypeArguments="x:Boolean">
      <VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" />
    </InArgument>
  </If.Condition>
  <If.Then>
    <Sequence DisplayName="Then">
      <!-- then branch -->
    </Sequence>
  </If.Then>
  <If.Else>
    <Sequence DisplayName="Else">
      <!-- else branch -->
    </Sequence>
  </If.Else>
</If>
```

**Notes:** Both `If.Then` and `If.Else` slots must wrap their body in `<Sequence>` per Rule 24. Omit `<If.Else>` entirely when no else branch is needed — do not emit an empty `<If.Else></If.Else>`. For multi-branch `else if … else if`, use `IfElseIfV2` (off this card; see `ElseIf.md`).

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/If.md`](activity-docs/UiPath.System.Activities/26.4/activities/If.md)

---

### Switch&lt;T&gt;
**Class:** `System.Activities.Statements.Switch`1`
**XAML prefix:** standard activities namespace; no `ui:` prefix.

**Snippet** (typed `Int32` example — change `x:TypeArguments` for other types):
```xml
<Switch x:TypeArguments="x:Int32" DisplayName="Switch">
  <Switch.Expression>
    <InArgument x:TypeArguments="x:Int32">
      <VisualBasicValue x:TypeArguments="x:Int32" ExpressionText="status" />
    </InArgument>
  </Switch.Expression>
  <Sequence x:Key="1" DisplayName="Case 1">
    <!-- case body for status == 1 -->
  </Sequence>
  <Sequence x:Key="2" DisplayName="Case 2">
    <!-- case body for status == 2 -->
  </Sequence>
  <Switch.Default>
    <Sequence DisplayName="Default">
      <!-- fallback body -->
    </Sequence>
  </Switch.Default>
</Switch>
```

**Notes:** Each case body and `Switch.Default` must wrap their content in `<Sequence>` per Rule 24. Case keys are declared via `x:Key="<literal>"` on each case-body child directly inside `<Switch>` — the `Cases` dictionary is not declared explicitly. For string keys: `x:TypeArguments="x:String"` and `x:Key="someString"`.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/Switch.md`](activity-docs/UiPath.System.Activities/26.4/activities/Switch.md)

---

### TryCatch
**Class:** `System.Activities.Statements.TryCatch`
**XAML prefix:** standard activities namespace; also declare `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"` for the exception type (Legacy/.NET 4.6.1 projects use `assembly=mscorlib`).

**Snippet:**
```xml
<TryCatch DisplayName="Try Catch">
  <TryCatch.Try>
    <Sequence DisplayName="Try">
      <!-- guarded body -->
    </Sequence>
  </TryCatch.Try>
  <TryCatch.Catches>
    <Catch x:TypeArguments="s:Exception">
      <ActivityAction x:TypeArguments="s:Exception">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="s:Exception" Name="exception" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Catch">
          <!-- handler body; reference iterator variable "exception" -->
        </Sequence>
      </ActivityAction>
    </Catch>
  </TryCatch.Catches>
  <TryCatch.Finally>
    <Sequence DisplayName="Finally">
      <!-- finally body -->
    </Sequence>
  </TryCatch.Finally>
</TryCatch>
```

**Notes:** `Try`, every `Catch.Action`, and `Finally` must wrap their body in `<Sequence>` per Rule 24. Each `Catch` requires its own `<ActivityAction x:TypeArguments="...">` holding a `<DelegateInArgument x:TypeArguments="..." Name="exception" />` — the `Name` is the variable name the handler body uses. Place specific exception types before `s:Exception`. Omit `<TryCatch.Finally>` entirely when not needed. For strategy — exception taxonomy, Retry Scope, ContinueOnError, screenshot-on-error, Global Exception Handler — see [error-handling-guide.md](error-handling-guide.md).

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/TryCatch.md`](activity-docs/UiPath.System.Activities/26.4/activities/TryCatch.md)

---

### While
**Class:** `UiPath.Core.Activities.InterruptibleWhile` (Studio emits **this**, not the framework `System.Activities.Statements.While`)
**XAML prefix:** `xmlns:ui="http://schemas.uipath.com/workflow/activities"`.

**Snippet:**
```xml
<ui:InterruptibleWhile DisplayName="While">
  <ui:InterruptibleWhile.Condition>
    <VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" />
  </ui:InterruptibleWhile.Condition>
  <ui:InterruptibleWhile.Body>
    <Sequence DisplayName="Body">
      <!-- iteration body -->
    </Sequence>
  </ui:InterruptibleWhile.Body>
</ui:InterruptibleWhile>
```

**Non-obvious properties:**
- `MaxIterations` — `InArgument<int>` — upper bound; `0` means **unlimited**. Default `0`. Set to a positive value to guard against infinite loops.
- `CurrentIndex` — `OutArgument<int>` — zero-based iteration counter; bind to a variable when the body needs the index.

**Notes:** Studio uses `InterruptibleWhile`, not the framework `While`. The body must be `<Sequence>`-wrapped per Rule 24. `Condition` is evaluated **before** each iteration; if false on entry, the body never runs.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/While.md`](activity-docs/UiPath.System.Activities/26.4/activities/While.md)

---

### Do While
**Class:** `UiPath.Core.Activities.InterruptibleDoWhile` (Studio emits **this**, not the framework `System.Activities.Statements.DoWhile`)
**XAML prefix:** `xmlns:ui="http://schemas.uipath.com/workflow/activities"`.

**Snippet:**
```xml
<ui:InterruptibleDoWhile DisplayName="Do While">
  <ui:InterruptibleDoWhile.Body>
    <Sequence DisplayName="Body">
      <!-- iteration body -->
    </Sequence>
  </ui:InterruptibleDoWhile.Body>
  <ui:InterruptibleDoWhile.Condition>
    <VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" />
  </ui:InterruptibleDoWhile.Condition>
</ui:InterruptibleDoWhile>
```

**Non-obvious properties:**
- `MaxIterations` — `InArgument<int>` — upper bound; `0` means **unlimited**. Default `0`.
- `CurrentIndex` — `OutArgument<int>` — zero-based iteration counter.

**Notes:** Studio uses `InterruptibleDoWhile`, not the framework `DoWhile`. The body must be `<Sequence>`-wrapped per Rule 24. Body executes **at least once**; `Condition` is evaluated **after** each iteration.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/DoWhile.md`](activity-docs/UiPath.System.Activities/26.4/activities/DoWhile.md)

---

### For Each&lt;T&gt;
**Class:** `UiPath.Core.Activities.ForEach`1` (Studio emits **this**, not the framework `System.Activities.Statements.ForEach<T>`)
**XAML prefix:** `xmlns:ui="http://schemas.uipath.com/workflow/activities"`; declare `xmlns:sc="clr-namespace:System.Collections;assembly=System.Private.CoreLib"` for the (non-generic) `IEnumerable` argument typing.

**Snippet** (typed `String` example — change `x:TypeArguments` on the outer activity and on the inner `ActivityAction`/`DelegateInArgument` to match the element type):
```xml
<ui:ForEach x:TypeArguments="x:String" DisplayName="For Each">
  <ui:ForEach.Values>
    <InArgument x:TypeArguments="sc:IEnumerable">
      <VisualBasicValue x:TypeArguments="sc:IEnumerable" ExpressionText="myList" />
    </InArgument>
  </ui:ForEach.Values>
  <ui:ForEach.Body>
    <ActivityAction x:TypeArguments="x:String">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="x:String" Name="item" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Body">
        <!-- iteration body; reference iterator variable "item" -->
      </Sequence>
    </ActivityAction>
  </ui:ForEach.Body>
</ui:ForEach>
```

**Non-obvious properties:**
- `Values` — `InArgument<System.Collections.IEnumerable>` — **non-generic** `IEnumerable`, not `IEnumerable<T>` (verified against `ForEachBase<T>.Values`). The element type `T` comes from the outer `x:TypeArguments` on `<ui:ForEach>`, not from `Values`.
- `Body` — `ActivityAction<T>` — must be set via the `<ui:ForEach.Body>` property element (it is NOT the ContentProperty; placing a bare `<ActivityAction>` directly inside `<ui:ForEach>` produces `Cannot set unknown member '...Implementation'`).
- `MaxIterations` — `InArgument<int>` — upper bound; `0` means **unlimited**. Default `0`.
- `CurrentIndex` — `OutArgument<int>` — zero-based iteration counter.

**Notes:** Studio uses `UiPath.Core.Activities.ForEach`, not the framework `ForEach<T>`. The iterator variable name (`item` in the snippet) is set via `DelegateInArgument.Name` on the inner `ActivityAction.Argument` — auto-suggested by Studio based on element type. Body must be `<Sequence>`-wrapped per Rule 24.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/ForEach.md`](activity-docs/UiPath.System.Activities/26.4/activities/ForEach.md)

---

## Group B — Data + logging

### Assign
**Class:** `System.Activities.Statements.Assign` — no type argument on the activity; the types go on its arguments.
**XAML prefix:** standard activities namespace; no `ui:` prefix.

**Snippet** (typed `Int32` example):
```xml
<Assign DisplayName="Assign">
  <Assign.To>
    <OutArgument x:TypeArguments="x:Int32">
      <VisualBasicReference x:TypeArguments="x:Int32" ExpressionText="counter" />
    </OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:Int32">
      <VisualBasicValue x:TypeArguments="x:Int32" ExpressionText="counter + 1" />
    </InArgument>
  </Assign.Value>
</Assign>
```

**Notes:** Type safety comes from the arguments — the typed `OutArgument`/`InArgument` above surface mismatch errors at `validate` time. `To` must be a writable expression (variable, argument, indexer) — Studio's emitter uses `VisualBasicReference` (or `CSharpReference` in C# projects) for the writable side and `VisualBasicValue` (or `CSharpValue`) for the readable side. One target per `Assign`; two or more consecutive assignments go into one Multiple Assign (next entry), which reads as one block instead of a stack of `Assign`s.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/Assign.md`](activity-docs/UiPath.System.Activities/26.4/activities/Assign.md)

---

### Multiple Assign
**Class:** `UiPath.Core.Activities.MultipleAssign`
**XAML prefix:** `xmlns:ui="http://schemas.uipath.com/workflow/activities"`; declare `xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"` for the operations list (Legacy/.NET 4.6.1 projects use `assembly=mscorlib`).

**Snippet** (two `String` targets — each operation is typed on its own arguments):
```xml
<ui:MultipleAssign DisplayName="Multiple Assign">
  <ui:MultipleAssign.AssignOperations>
    <scg:List x:TypeArguments="ui:AssignOperation" Capacity="4">
      <ui:AssignOperation>
        <ui:AssignOperation.To>
          <OutArgument x:TypeArguments="x:String">
            <VisualBasicReference x:TypeArguments="x:String" ExpressionText="trimmedName" />
          </OutArgument>
        </ui:AssignOperation.To>
        <ui:AssignOperation.Value>
          <InArgument x:TypeArguments="x:String">
            <VisualBasicValue x:TypeArguments="x:String" ExpressionText="fullName.Trim()" />
          </InArgument>
        </ui:AssignOperation.Value>
      </ui:AssignOperation>
      <ui:AssignOperation>
        <ui:AssignOperation.To>
          <OutArgument x:TypeArguments="x:String">
            <VisualBasicReference x:TypeArguments="x:String" ExpressionText="upperName" />
          </OutArgument>
        </ui:AssignOperation.To>
        <ui:AssignOperation.Value>
          <InArgument x:TypeArguments="x:String">
            <VisualBasicValue x:TypeArguments="x:String" ExpressionText="trimmedName.ToUpperInvariant()" />
          </InArgument>
        </ui:AssignOperation.Value>
      </ui:AssignOperation>
    </scg:List>
  </ui:MultipleAssign.AssignOperations>
</ui:MultipleAssign>
```

**Non-obvious properties:**
- `AssignOperations` — `List<AssignOperation>`, hidden in the property grid. Each `AssignOperation` has one `To` and one `Value`, typed and bound like `Assign.To` / `Assign.Value`; targets of different types mix freely in one list.

**Notes:** Operations run in list order, so a later `Value` reads a target an earlier operation set (`upperName` reads `trimmedName`). A failed operation raises with its value and target expressions in the message. C# projects bind `To` and `Value` in this property-element form with `CSharpReference` / `CSharpValue` per [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md); the package doc's attribute form (`To="[firstName]"`) is bracket syntax, which is VB only.

**Long-form:** the installed package's `{PROJECT_DIR}/.local/docs/packages/UiPath.System.Activities/activities/MultipleAssign.md` (no bundled copy); snippet shape verified against 26.8.2.

---

### Log Message
**Class:** `UiPath.Core.Activities.LogMessage`
**XAML prefix:** `xmlns:ui="http://schemas.uipath.com/workflow/activities"`; no extra prefix needed (`x:Object` uses the root `xmlns:x`).

**Snippet:**
```xml
<ui:LogMessage Level="Info" DisplayName="Log Message">
  <ui:LogMessage.Message>
    <InArgument x:TypeArguments="x:Object">
      <VisualBasicValue x:TypeArguments="x:Object" ExpressionText="$&quot;Processed {count} items&quot;" />
    </InArgument>
  </ui:LogMessage.Message>
</ui:LogMessage>
```

**Non-obvious properties:**
- `Level` — `InArgument<LogLevel>` — required-in-practice; **default `Info`** but the skip-tax hides it from `get-default-xaml`. Enum values: `Trace` | `Info` | `Warn` | `Error` | `Fatal`.
- `Message` — `InArgument<object>` — **not** `string`. Accepts any expression; the activity calls `.ToString()`. In VB projects, bracket shorthand can hold composite expressions such as `[$"x = {x}"]`; in C# projects, use `<CSharpValue x:TypeArguments="x:Object">...</CSharpValue>`.

**Notes:** Prefer `LogMessage` over `WriteLine` for any output that must appear in Orchestrator. `Level` defaults to `Info`; omit only when you want `Info` and the explicit attribute clutters the snippet.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/LogMessage.md`](activity-docs/UiPath.System.Activities/26.4/activities/LogMessage.md)

---

### Write Line
**Class:** `System.Activities.Statements.WriteLine`
**XAML prefix:** standard activities namespace; no `ui:` prefix.

**Snippet:**
```xml
<WriteLine DisplayName="Write Line">
  <WriteLine.Text>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="$&quot;processed {count} items&quot;" />
    </InArgument>
  </WriteLine.Text>
</WriteLine>
```

**Notes:** Writes to stdout only — invisible in Orchestrator. Prefer `LogMessage` whenever Orchestrator visibility matters. Do **not** set `TextWriter` — its default (`Console.Out`) is correct for every Studio and `uip rpa run` context.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/WriteLine.md`](activity-docs/UiPath.System.Activities/26.4/activities/WriteLine.md)

---

### Delay
**Class:** `System.Activities.Statements.Delay`
**XAML prefix:** standard activities namespace; declare `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"` for the `TimeSpan` argument type (Legacy/.NET 4.6.1 projects use `assembly=mscorlib`).

**Snippet:**
```xml
<Delay DisplayName="Delay">
  <Delay.Duration>
    <InArgument x:TypeArguments="s:TimeSpan">
      <VisualBasicValue x:TypeArguments="s:TimeSpan" ExpressionText="TimeSpan.FromSeconds(5)" />
    </InArgument>
  </Delay.Duration>
</Delay>
```

**Notes:** `Duration` must produce a `TimeSpan`. In VB projects, bracket shorthand such as `[TimeSpan.FromSeconds(5)]` is valid; in C# projects, use `<CSharpValue x:TypeArguments="s:TimeSpan">TimeSpan.FromSeconds(5)</CSharpValue>` or a literal attribute such as `Duration="00:00:05"`. Blocks the workflow thread for the full duration — avoid inside `ForEach`/`While` bodies where it multiplies. Do **not** use `Delay` to wait on external state; use `RetryScope`, `WaitForElement`, or a polling loop with a `Condition` instead.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/Delay.md`](activity-docs/UiPath.System.Activities/26.4/activities/Delay.md)

---

### Throw
**Class:** `System.Activities.Statements.Throw`
**XAML prefix:** standard activities namespace; also declare `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"` for the exception argument type (Legacy/.NET 4.6.1 projects use `assembly=mscorlib`).

**Snippet:**
```xml
<Throw DisplayName="Throw">
  <Throw.Exception>
    <InArgument x:TypeArguments="s:Exception">
      <VisualBasicValue x:TypeArguments="s:Exception" ExpressionText="new InvalidOperationException(&quot;Invoice total is negative&quot;)" />
    </InArgument>
  </Throw.Exception>
</Throw>
```

**Notes:** `Exception` is a **constructor expression**, not a string. `Throw.Exception = "message"` is invalid. Use a domain-specific exception type (e.g., `BusinessRuleException`) when downstream `Catch` handlers need to distinguish business errors from system errors. Use `Rethrow` (inside a `Catch` body) to preserve the original stack trace instead.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/Throw.md`](activity-docs/UiPath.System.Activities/26.4/activities/Throw.md)

---

### Rethrow
**Class:** `System.Activities.Statements.Rethrow`
**XAML prefix:** standard activities namespace; no `ui:` prefix.

**Snippet:**
```xml
<Rethrow DisplayName="Rethrow" />
```

**Notes:** Zero properties. **Only valid inside a `Catch.Action` body** — using it outside a `Catch` is a runtime `InvalidOperationException`. Preserves the original exception's stack trace; use `Throw new <Type>(...)` instead when you want to translate to a different exception type. Place `Rethrow` last in the `Catch` body — anything after it is unreachable.

**Long-form:** [`activity-docs/UiPath.System.Activities/26.4/activities/Rethrow.md`](activity-docs/UiPath.System.Activities/26.4/activities/Rethrow.md)

---

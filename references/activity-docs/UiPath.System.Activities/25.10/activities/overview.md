# UiPath.System.Activities — Overview

Core control flow activities, inline code, and coded workflow patterns for `UiPath.System.Activities` (always installed).

## Expression Syntax Notes (C# Projects)

- Inside `<InArgument>` / `<InOutArgument>` elements, use explicit `<CSharpValue>` (read/evaluate):
  ```xml
  <InArgument x:TypeArguments="x:String">
    <CSharpValue x:TypeArguments="x:String">myVariable.ToString()</CSharpValue>
  </InArgument>
  ```
- Inside `<OutArgument>` / `<InOutArgument>` elements for lvalue (write target), use `<CSharpReference>`:
  ```xml
  <OutArgument x:TypeArguments="x:String">
    <CSharpReference x:TypeArguments="x:String">myVariable</CSharpReference>
  </OutArgument>
  ```
- `CSharpValue` and `CSharpReference` are in the default activities namespace (no prefix needed)
- Do **NOT** use `[bracket]` shorthand — brackets create `VisualBasicValue` nodes at deserialization time, which fail validation for C#-only syntax (`null`, `?.`, `??`, `typeof()`, etc.)
- Simple non-argument properties (`Direction == "Property"`) like `DisplayName`, `Level`, etc. are plain attribute strings — no expression wrapper needed

## xmlns Prefixes

These should be present in all workflow files created:

```
xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"   (default — Assign, If, Sequence, etc.)
xmlns:ui="http://schemas.uipath.com/workflow/activities"          (UiPath — ForEach, LogMessage, etc.)
xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"
xmlns:sc="clr-namespace:System.Collections;assembly=System.Private.CoreLib"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
```

## Activities in This Package

### Control Flow
- [Assign](Assign.md)
- [If](If.md)
- [ForEach](ForEach.md)
- [While](While.md)
- [DoWhile](DoWhile.md)
- [Switch](Switch.md)
- [TryCatch](TryCatch.md)
- [Throw](Throw.md)
- [Delay](Delay.md)
- [LogMessage](LogMessage.md)
- [InvokeWorkflowFile](InvokeWorkflowFile.md)
- [VariablesAndScoping](VariablesAndScoping.md)

### Inline Code & Coded Workflows
- [InvokeCode](InvokeCode.md)
- [CodedWorkflows](CodedWorkflows.md)

## Decision Guide: InvokeCode vs Coded Workflow

| Factor | InvokeCode | Coded Workflow |
|--------|-----------|----------------|
| **Lines of code** | ~1-15 lines | 15+ lines |
| **Class dependencies** | None — only inline .NET BCL calls | NuGet packages, custom classes, services |
| **Testability needed** | No | Yes — unit tests, mocking |
| **Reusability** | One-off, single workflow | Shared across multiple workflows |
| **Debugging** | Limited (no breakpoints in inline code) | Full IDE debugging in Studio |
| **Code complexity** | Simple transforms, one-liners, quick fixes | Business logic, API integrations, data pipelines |
| **Error handling** | Basic (try-catch in inline code) | Structured (proper exception types, logging) |

**Rule of thumb:** If you're reaching for `&#xA;` more than ~10 times, or you need to import a NuGet package the inline code can't access, switch to a coded workflow.

## Common Variable Types

| Type in XAML | C# Type | xmlns prefix |
|---|---|---|
| `x:String` | `string` | `x:` (built-in) |
| `x:Int32` | `int` | `x:` |
| `x:Boolean` | `bool` | `x:` |
| `x:Double` | `double` | `x:` |
| `x:Object` | `object` | `x:` |
| `s:DateTime` | `DateTime` | `s:` |
| `s:String[]` | `string[]` | `s:` |
| `s:Exception` | `Exception` | `s:` |
| `scg:List(x:String)` | `List<string>` | `scg:` |
| `scg:Dictionary(x:String, x:Object)` | `Dictionary<string, object>` | `scg:` |

## Variable vs Argument Guidelines

- **Variables:** Scope-local, defined in `<Sequence.Variables>` or `<Flowchart.Variables>`
- **Arguments:** Cross-workflow, defined in `<x:Members>` at workflow root
- **Naming:** Use `in_`, `out_`, `io_` prefixes for arguments (avoid confusion)
- **Direction:** IN (read-only), OUT (write-only), IN/OUT (read-write)
- **Case Sensitive:** Argument names are case-sensitive

These activities are part of `UiPath.System.Activities` (always installed). You can write them directly **without** calling `uip rpa get-default-activity-xaml --use-studio`. Use the templates as-is — just replace the placeholder expressions with your actual logic.

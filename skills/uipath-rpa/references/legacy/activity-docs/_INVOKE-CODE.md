# UiPath Invoke Code Activity - Deep Reference

## Overview
`Invoke Code` executes inline VB.NET or C# code at runtime. It compiles user code using **Roslyn** into a temporary assembly, caches it, and invokes it via reflection. Located in `UiPath.System.Activities` package.

---

## 1. Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `Code` | String | YES | (empty) | The inline code to execute |
| `Language` | NetLanguage enum | NO | `VBNet` | `VBNet` or `CSharp` |
| `Arguments` | Dictionary\<String, Argument\> | NO | empty dict | Named arguments passed in/out of the code |
| `ContinueOnError` | InArgument\<Boolean\> | NO | false | Suppress runtime exceptions (NOT compilation errors) |

---

## 2. How It Works Internally (Source Code Verified)

### Compilation Pipeline
1. User code is wrapped in a generated class/module
2. Namespace imports inherited from the workflow's `TextExpression.NamespacesForImplementation`
3. Assemblies from `AppDomain.CurrentDomain.GetAssemblies()` provided as references
4. Code compiled by **Roslyn** (`Microsoft.CodeAnalysis`) into in-memory assembly
5. Compiled assembly **cached** by code+arguments hash (reuse in loops)
6. Executed via `Assembly.GetType().InvokeMember("Run", ...)`

### VB.NET Generated Code Structure
```vb
Option Explicit
Option Strict
Imports System
Imports System.Collections.Generic
' ... (all workflow namespace imports)

Module UiPathCodeRunner_<guid>
  Sub Run(ByVal inputArg As System.String, ByRef outputArg As System.Int32)
    ' === YOUR CODE HERE ===
  End Sub
End Module
```

### C# Generated Code Structure
```csharp
using System;
using System.Collections.Generic;
// ... (all workflow namespace imports)

namespace UiPathCodeRunnerNamespace {
  public class UiPathCodeRunner_<guid> {
    public static void Run(global::System.String inputArg, ref global::System.Int32 outputArg) {
      // === YOUR CODE HERE ===
    }
  }
}
```

### Key Implementation Details
- **VB.NET uses `Option Explicit` and `Option Strict`** — you must declare variables and types must match
- **C# uses `global::` prefix** for all type names to avoid namespace conflicts
- **In arguments** → `ByVal` (VB) / no modifier (C#) — passed by value
- **Out/InOut arguments** → `ByRef` (VB) / `ref` (C#) — passed by reference, changes reflected back
- **Compilation cached** in static `Dictionary<string, CompilerRunner>` (max 25 entries) — same code in a loop compiles only once
- **AssemblyLoadContext** used on .NET 6+ to allow unloading compiled assemblies

---

## 3. Arguments — How They Map

### Argument Directions
| Direction | VB.NET Generated | C# Generated | Behavior |
|-----------|-----------------|--------------|----------|
| `In` | `ByVal name As Type` | `Type name` | Read-only; changes NOT reflected back |
| `Out` | `ByRef name As Type` | `ref Type name` | Write-only; value set in code is returned to workflow |
| `InOut` | `ByRef name As Type` | `ref Type name` | Read+Write; initial value passed in, modified value returned |

### How Arguments Appear in Your Code
Arguments become **method parameters**. Use them directly by name:

**VB.NET:**
```vb
' Arguments: inputText (In, String), result (Out, String), counter (InOut, Int32)
result = inputText.ToUpper()
counter = counter + 1
```

**C#:**
```csharp
// Arguments: inputText (In, String), result (Out, String), counter (InOut, Int32)
result = inputText.ToUpper();
counter = counter + 1;
```

### Type Mapping for Arguments
| Workflow Type | VB.NET Parameter | C# Parameter |
|--------------|-----------------|--------------|
| String | `ByVal x As System.String` | `global::System.String x` |
| Int32 | `ByVal x As System.Int32` | `global::System.Int32 x` |
| Boolean | `ByVal x As System.Boolean` | `global::System.Boolean x` |
| DataTable | `ByVal x As System.Data.DataTable` | `global::System.Data.DataTable x` |
| List\<String\> | `ByVal x As System.Collections.Generic.List(Of System.String)` | `global::System.Collections.Generic.List<global::System.String> x` |
| Dictionary\<String,Object\> | `ByVal x As System.Collections.Generic.Dictionary(Of System.String, System.Object)` | `global::System.Collections.Generic.Dictionary<global::System.String, global::System.Object> x` |
| Object | `ByVal x As System.Object` | `global::System.Object x` |
| String[] | `ByVal x As System.String()` | `global::System.String[] x` |

### XAML Representation of Arguments
```xml
<ui:InvokeCode Code="result = input.ToUpper()" Language="VBNet"
  DisplayName="Invoke code" sap2010:WorkflowViewState.IdRef="InvokeCode_1">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="input">[myVariable]</InArgument>
      <OutArgument x:TypeArguments="x:String" x:Key="result">[outputVariable]</OutArgument>
      <InOutArgument x:TypeArguments="x:Int32" x:Key="counter">[counterVariable]</InOutArgument>
    </scg:Dictionary>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>
```

---

## 4. Available Namespaces & Assemblies

### Automatically Available (inherited from workflow)
All namespaces imported in the workflow's `TextExpression.NamespacesForImplementation` are available. Standard legacy VB.NET workflow includes:

```
System, System.Collections, System.Collections.Generic, System.Data,
System.Diagnostics, System.Drawing, System.IO, System.Linq,
System.Net.Mail, System.Xml, System.Xml.Linq,
UiPath.Core, UiPath.Core.Activities
```

### Also Available (from loaded assemblies)
All assemblies in the AppDomain are referenced for compilation. This means:
- **System.Data** (DataTable, DataSet, DataRow)
- **System.Drawing** (Color, Image, Bitmap)
- **System.IO** (File, Directory, Path, Stream)
- **System.Linq** (LINQ extension methods)
- **System.Text.RegularExpressions** (Regex)
- **System.Net.Http** (HttpClient — use fully qualified name to avoid conflicts)
- Any activity package assemblies loaded in the project

### Adding Custom Namespaces
To use additional namespaces, add them in Studio: Design tab → Imports panel. They will be passed to the compiler via `GetImports()`.

---

## 5. Code Examples

### VB.NET Examples

**Simple calculation:**
```vb
' Arguments: x (In, Int32), y (In, Int32), result (Out, Int32)
result = x + y
```

**String manipulation:**
```vb
' Arguments: input (In, String), output (Out, String)
output = input.Trim().ToUpper().Replace("OLD", "NEW")
```

**DataTable filtering:**
```vb
' Arguments: dt (InOut, DataTable)
Dim rows = dt.Select("[Status] = 'Active'")
Dim filtered = dt.Clone()
For Each row As System.Data.DataRow In rows
    filtered.ImportRow(row)
Next
dt = filtered
```

**File operations:**
```vb
' Arguments: filePath (In, String), content (Out, String)
content = System.IO.File.ReadAllText(filePath)
```

**Regex:**
```vb
' Arguments: input (In, String), matches (Out, String[])
Dim rx = New System.Text.RegularExpressions.Regex("\d+")
Dim mc = rx.Matches(input)
Dim result(mc.Count - 1) As String
For i As Integer = 0 To mc.Count - 1
    result(i) = mc(i).Value
Next
matches = result
```

**Multi-line with variables:**
```vb
' Arguments: items (In, List(Of String)), csv (Out, String)
Dim sb As New System.Text.StringBuilder()
For Each item As String In items
    sb.AppendLine(item)
Next
csv = sb.ToString()
```

### C# Examples

**Simple calculation:**
```csharp
// Arguments: x (In, Int32), y (In, Int32), result (Out, Int32)
result = x + y;
```

**String manipulation:**
```csharp
// Arguments: input (In, String), output (Out, String)
output = input.Trim().ToUpper().Replace("OLD", "NEW");
```

**LINQ on DataTable:**
```csharp
// Arguments: dt (In, DataTable), total (Out, Double)
total = dt.AsEnumerable()
    .Where(r => r["Status"].ToString() == "Active")
    .Sum(r => Convert.ToDouble(r["Amount"]));
```

**JSON parsing:**
```csharp
// Arguments: json (In, String), value (Out, String)
var obj = Newtonsoft.Json.Linq.JObject.Parse(json);
value = obj["data"]["name"].ToString();
```

**Dictionary building:**
```csharp
// Arguments: keys (In, String[]), values (In, String[]), dict (Out, Dictionary<String,String>)
dict = new Dictionary<string, string>();
for (int i = 0; i < keys.Length; i++) {
    dict[keys[i]] = values[i];
}
```

---

## 6. Error Handling

### Compilation Errors
- **Always thrown** as `ArgumentException` regardless of `ContinueOnError`
- Error message format: `"Compiled Code exception: <ErrorId> <Message> at line <Line>"`
- Line numbers offset-adjusted to match user code (not generated wrapper)
- **Shown at design time** if code is edited in the Code Editor dialog

### Runtime Errors
- Thrown as the original exception type (IOException, NullReferenceException, etc.)
- **Suppressed** if `ContinueOnError = true`
- `ArgumentException` from compilation is **NEVER suppressed** (explicit check in source code)

### Common Compilation Errors

**VB.NET:**
| Error | Cause | Fix |
|-------|-------|-----|
| `BC30451: 'x' is not declared` | Variable not declared or not in Arguments | Add as Argument or declare with `Dim` |
| `BC30311: Cannot convert 'String' to 'Int32'` | Type mismatch (Option Strict enforced!) | Use explicit conversion: `CInt(str)` |
| `BC30205: End of statement expected` | Missing line break or syntax error | Check VB.NET syntax |
| `BC30035: Syntax error` | Invalid VB.NET syntax | Review code structure |

**C#:**
| Error | Cause | Fix |
|-------|-------|-----|
| `CS0103: The name 'x' does not exist` | Variable not in Arguments | Add as Argument or declare locally |
| `CS0029: Cannot implicitly convert type` | Type mismatch | Use explicit cast |
| `CS1002: ; expected` | Missing semicolon | Add `;` at end of statements |
| `CS0246: The type or namespace could not be found` | Missing import/reference | Use fully qualified name: `global::System.Net.Http.HttpClient` |

---

## 7. Critical Gotchas

### Language & Syntax
1. **VB.NET uses `Option Strict`** — implicit conversions are NOT allowed. `Dim x As Integer = "5"` will fail. Use `CInt("5")`.
2. **C# requires semicolons** and follows standard C# syntax
3. **You are writing the METHOD BODY only** — do not write class/module/method declarations, just the code inside `Sub Run()` / `void Run()`
4. **Do NOT use `Return` statements** — the method is `Sub`/`void`. Set Out arguments instead.
5. **VB arrays use `()` not `[]`** — `Dim arr(5) As String` not `string[] arr`

### Arguments
6. **Argument names must be valid identifiers** — no spaces, no special chars, must start with letter
7. **In arguments are COPIES** (ByVal) — modifying them does NOT change the workflow variable
8. **Out/InOut arguments are REFERENCES** (ByRef) — changes ARE reflected back to the workflow
9. **Generic types work** but the generated code uses fully-qualified names like `System.Collections.Generic.List(Of System.Int32)`
10. **Argument type must match exactly** — passing a String to an Int32 argument fails at compile time

### Performance
11. **First execution is SLOW** — Roslyn compilation takes 100-500ms
12. **Subsequent executions are FAST** — compiled assembly cached by code+arguments hash
13. **Cache limit is 25 entries** — after that, oldest entries may be evicted
14. **Avoid modifying code dynamically** in loops — each unique code string triggers new compilation

### Namespace Conflicts
15. **C# `System` namespace conflict** — using `HttpClient` may fail because `System` is both a namespace and a member. Use `global::System.Net.Http.HttpClient` instead. (Bug fix: STUD-77435)
16. **Workflow imports filter** — only namespaces that exist in loaded assemblies are passed to compiler. If you need `System.Net.Http`, ensure the assembly is loaded.

### Assemblies
17. **All AppDomain assemblies available** — activity package DLLs, .NET framework, etc.
18. **Cannot add custom DLL references** at runtime — only assemblies already loaded in the workflow
19. **On .NET 6+** compiled assemblies use `AssemblyLoadContext` for proper unloading

### ContinueOnError
20. **Compilation errors ALWAYS throw** — `ContinueOnError` only suppresses RUNTIME exceptions
21. **This is by design** — invalid code that can't compile should never be silently ignored

---

## 8. XAML Template

### Minimal VB.NET Invoke Code
```xml
<ui:InvokeCode Code="result = &quot;Hello &quot; + name" Language="VBNet"
  DisplayName="Invoke code" sap2010:WorkflowViewState.IdRef="InvokeCode_1">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="name">[inputName]</InArgument>
      <OutArgument x:TypeArguments="x:String" x:Key="result">[outputResult]</OutArgument>
    </scg:Dictionary>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>
```

### Minimal C# Invoke Code
```xml
<ui:InvokeCode Code="result = &quot;Hello &quot; + name;" Language="CSharp"
  DisplayName="Invoke code" sap2010:WorkflowViewState.IdRef="InvokeCode_1">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="name">[inputName]</InArgument>
      <OutArgument x:TypeArguments="x:String" x:Key="result">[outputResult]</OutArgument>
    </scg:Dictionary>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>
```

### With No Arguments (side-effect code)
```xml
<ui:InvokeCode Code="System.IO.File.WriteAllText(&quot;C:\temp\log.txt&quot;, &quot;done&quot;)"
  Language="VBNet" DisplayName="Write File">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument" />
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>
```

---

## 9. When to Use Invoke Code vs. Alternatives

| Scenario | Best Choice | Why |
|----------|-------------|-----|
| Simple assignment | `Assign` activity | Simpler, no compilation overhead |
| DataTable LINQ query | `Invoke Code` | LINQ not available in Assign expressions |
| Complex string parsing | `Invoke Code` | Multi-line logic with variables |
| File I/O | Built-in activities (Read/Write Text File) | Error handling built-in |
| HTTP requests | `HTTP Request` activity | Retry, auth, proxy built-in |
| Regex matching | `Matches` activity or Invoke Code | Activity is simpler for basic patterns |
| JSON parsing | `Deserialize JSON` + Invoke Code | Activity for deserialization, code for complex traversal |
| Custom business logic | `Invoke Code` | When no activity exists for the operation |
| Reusable logic | `Invoke Workflow File` | Invoke Code can't be reused across workflows |

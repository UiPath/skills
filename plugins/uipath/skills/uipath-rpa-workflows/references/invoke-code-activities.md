# Inline Code & Coded Workflows

This reference covers two approaches for embedding custom .NET logic in UiPath workflows:

1. **InvokeCode** — inline VB.NET/C# snippets directly in XAML (simple, self-contained logic)
2. **Coded Workflows** — full `.cs` files invoked via `InvokeWorkflowFile` (complex logic, real class dependencies, testability)

Choose the right tool for the job. Using the wrong one creates maintenance pain or unnecessary complexity.

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

---

## InvokeCode Activity

`ui:InvokeCode` executes inline VB.NET or C# code within a workflow. Part of `UiPath.System.Activities` (`xmlns:ui="http://schemas.uipath.com/workflow/activities"`).

InvokeCode is best suited as a quick escape hatch for simple, self-contained code. When a dedicated activity has unresolvable type issues, missing output properties, or complex configuration that resists XAML-level fixes, a few lines in InvokeCode can solve it in one pass. But if the code grows beyond a handful of lines or needs real dependencies, use a coded workflow instead.

### Language Attribute

By default, InvokeCode infers the language from the project's `expressionLanguage` setting in `project.json`, so omitting the `Language` attribute is usually fine. However, if you do set it explicitly, use the correct enum values — they differ from `project.json`:

| project.json `expressionLanguage` | InvokeCode `Language` value |
|-----------------------------------|-----------------------------|
| `"VisualBasic"` | `"VBNet"` |
| `"CSharp"` | `"CSharp"` |

**IMPORTANT:** `"VisualBasic"` is NOT a valid `Language` value — it will pass Studio validation but fail at runtime with: *"VisualBasic is not a valid value for NetLanguage"*. This is a known mismatch between project.json naming and the runtime enum.

```xml
<!-- WRONG — passes Studio validation but fails at runtime -->
<ui:InvokeCode Language="VisualBasic" Code="..." />

<!-- CORRECT — explicit language -->
<ui:InvokeCode Language="VBNet" Code="..." />

<!-- ALSO CORRECT — language inferred from project -->
<ui:InvokeCode Code="..." />
```

### XAML Structure

```xml
<ui:InvokeCode ContinueOnError="{x:Null}"
  DisplayName="My Code Block"
  sap2010:WorkflowViewState.IdRef="InvokeCode_1"
  Code="Dim result As String = &quot;hello&quot;">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <!-- Arguments here -->
    </scg:Dictionary>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>
```

### Arguments Dictionary

Arguments pass data between the workflow and the inline code. Each argument maps a string key (used as a variable name in the code) to an `InArgument`, `OutArgument`, or `InOutArgument`.

```xml
<ui:InvokeCode.Arguments>
  <scg:Dictionary x:TypeArguments="x:String, Argument">
    <!-- Input: workflow variable -> code variable (read-only) -->
    <InArgument x:TypeArguments="x:String" x:Key="inputUrl">[myUrlVariable]</InArgument>

    <!-- Output: code variable -> workflow variable (write-only) -->
    <OutArgument x:TypeArguments="x:String" x:Key="httpResponse">[httpResponse]</OutArgument>

    <!-- InOut: both directions -->
    <InOutArgument x:TypeArguments="x:Int32" x:Key="counter">[counter]</InOutArgument>
  </scg:Dictionary>
</ui:InvokeCode.Arguments>
```

**Rules:**
- The `x:Key` is the variable name available inside the code block
- The `[bracketValue]` binds to a workflow variable (VB projects) or use `<CSharpValue>`/`<CSharpReference>` (C# projects)
- Types must match exactly between the argument declaration and the workflow variable
- Arguments with complex types (DataTable, JObject, etc.) work the same way — just change `x:TypeArguments`

### Code Attribute Escaping

The `Code` attribute contains the full source code as an XML attribute value. XML special characters must be escaped:

| Character | Escape | Example |
|-----------|--------|---------|
| Newline | `&#xA;` | Line breaks between statements |
| `"` | `&quot;` | String literals in code |
| `&` | `&amp;` | String concatenation (VB `&`), logical AND |
| `<` | `&lt;` | Comparisons (rare in attribute form) |
| `>` | `&gt;` | Comparisons (rare in attribute form) |

**Example — VB multi-line code:**
```xml
Code="Dim x As Integer = 5&#xA;Dim y As String = &quot;hello&quot;&#xA;Console.WriteLine(x.ToString() &amp; &quot; &quot; &amp; y)"
```

Equivalent VB code:
```vb
Dim x As Integer = 5
Dim y As String = "hello"
Console.WriteLine(x.ToString() & " " & y)
```

### Good Use Cases for InvokeCode

These are the sweet spot — simple, self-contained, no external dependencies:

**Quick string/data transforms:**
```xml
Code="System.IO.File.WriteAllText(filePath, content)"
```

**DataTable row manipulation:**
```xml
Code="For Each row As DataRow In dt.Rows&#xA;    row(&quot;Column1&quot;) = row(&quot;Column1&quot;).ToString().Trim()&#xA;Next"
```

**Simple HTTP fetch (when NetHttpRequest has type issues):**
```xml
<ui:InvokeCode ContinueOnError="{x:Null}"
  DisplayName="Fetch Data via HTTP"
  sap2010:WorkflowViewState.IdRef="InvokeCode_1"
  Code="Using wc As New System.Net.WebClient()&#xA;    wc.Headers.Add(&quot;User-Agent&quot;, &quot;Mozilla/5.0&quot;)&#xA;    responseBody = wc.DownloadString(url)&#xA;End Using">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="url">[requestUrl]</InArgument>
      <OutArgument x:TypeArguments="x:String" x:Key="responseBody">[httpResponse]</OutArgument>
    </scg:Dictionary>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>
```
**Required namespace import:** `System.Net`
**Required assembly reference:** `System.Net.WebClient`

### When NOT to Use InvokeCode

Stop and switch to a coded workflow when:
- The code exceeds ~15 lines — XML-escaped inline code becomes unreadable and unmaintainable
- You need NuGet packages or third-party libraries not available in the inline context
- The logic involves multiple classes, interfaces, or dependency injection
- You need unit testing or structured error handling
- The same logic is needed in multiple workflows (code reuse)
- You're doing complex API integrations with authentication, retries, pagination

### Namespace Requirements

Add to `TextExpression.NamespacesForImplementation` as needed by your code:

| Code Uses | Namespace Import |
|-----------|-----------------|
| `System.Net.WebClient` | `System.Net` |
| `System.IO.File` | `System.IO` |
| `DataTable`, `DataRow` | `System.Data` |
| `JObject`, `JArray`, `JToken` | `Newtonsoft.Json.Linq` |
| `Regex` | `System.Text.RegularExpressions` |

---

## Coded Workflows (via uipath-coded-workflows skill)

For anything beyond simple inline snippets, use **coded workflows** — full C# files (`.cs`) that inherit from `CodedWorkflow` and are managed by the `uipath-coded-workflows` skill.

**Invoke the `uipath-coded-workflows` skill** for creating, editing, or managing coded workflow files. That skill handles:
- Project initialization and configuration (`project.json`, dependencies)
- Creating `.cs` workflow files with proper `[Workflow]` attributes and `.cs.json` metadata
- Service injection (`excel`, `mail`, `uiAutomation`, etc.) via NuGet package dependencies
- Coded Source Files (helper classes, models, utilities — plain C# without `CodedWorkflow` base)
- Validation, building, and running coded workflows
- Test case creation with `[TestCase]` attributes

### Invoking a Coded Workflow from XAML

Once a coded workflow `.cs` file exists in the project, invoke it from an XAML workflow using `ui:InvokeWorkflowFile` — the same activity used to call other `.xaml` workflows. Point `WorkflowFileName` at the `.cs` file:

```xml
<ui:InvokeWorkflowFile WorkflowFileName="MyCodedWorkflow.cs" UnSafe="False">
  <ui:InvokeWorkflowFile.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="in_FilePath">
        <CSharpValue x:TypeArguments="x:String">inputPath</CSharpValue>
      </InArgument>
      <OutArgument x:TypeArguments="x:Boolean" x:Key="out_Success">
        <CSharpReference x:TypeArguments="x:Boolean">wasSuccessful</CSharpReference>
      </OutArgument>
    </scg:Dictionary>
  </ui:InvokeWorkflowFile.Arguments>
</ui:InvokeWorkflowFile>
```

For VB projects, use bracket syntax for argument bindings instead of `CSharpValue`/`CSharpReference`:
```xml
<InArgument x:TypeArguments="x:String" x:Key="in_FilePath">[inputPath]</InArgument>
<OutArgument x:TypeArguments="x:Boolean" x:Key="out_Success">[wasSuccessful]</OutArgument>
```

**Key points:**
- `WorkflowFileName` is relative to the project root — use the `.cs` file path (e.g., `"Workflows/ProcessData.cs"`)
- Arguments are passed via the same `Dictionary<string, Argument>` pattern as XAML-to-XAML invocation
- The `x:Key` must match the argument name defined in the coded workflow's `.cs.json` metadata
- The coded workflow's `Execute` method receives arguments and returns outputs through the standard `CodedWorkflow` mechanism

### When to Use Coded Workflows

- Complex business logic (validation rules, data transformations, calculations)
- API integrations requiring HttpClient, authentication, retry logic, pagination
- Code that needs NuGet packages (e.g., `Newtonsoft.Json`, `CsvHelper`, `Dapper`)
- Reusable logic shared across multiple XAML workflows
- Logic that benefits from unit testing
- Working with custom models, DTOs, or complex data structures
- Anything where XML-escaped inline code becomes a liability

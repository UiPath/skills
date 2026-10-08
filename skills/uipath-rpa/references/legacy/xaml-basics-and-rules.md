# XAML Basics and Rules (Legacy)

Core rules for legacy UiPath workflow XAML: .NET Framework 4.6.1 (WF4), primarily VB.NET. See [activity-docs/_XAML-GUIDE.md](./activity-docs/_XAML-GUIDE.md) for detailed templates and internals.

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
|---|---|---|
| Root marker | `mva:VisualBasic.Settings="{x:Null}"` | No `mva:` marker; may have expression editor attribute |
| Assembly xmlns | `assembly=mscorlib` | `assembly=System.Private.CoreLib` |
| Expression types | `mva:VisualBasicValue` / `mva:VisualBasicReference` | Brackets `[expr]` or `CSharpValue` |
| VB namespace | `xmlns:mva="clr-namespace:Microsoft.VisualBasic.Activities;assembly=System.Activities"` | Same or inferred |
| Framework | .NET Framework 4.6.1 | .NET 6+ |

---

## VB.NET vs C# Expression Detection

| Marker | VB.NET (Primary) | C# (Rare in Legacy) |
|---|---|---|
| Root attribute | `mva:VisualBasic.Settings="{x:Null}"` | `sap2010:ExpressionActivityEditor.ExpressionActivityEditor="C#"` |
| Expression type | `mva:VisualBasicValue<T>` / `mva:VisualBasicReference<T>` | `mca:CSharpValue<T>` / `mca:CSharpReference<T>` |
| Namespace xmlns | `xmlns:mva="clr-namespace:Microsoft.VisualBasic.Activities;assembly=System.Activities"` | `xmlns:mca="clr-namespace:Microsoft.CSharp.Activities;assembly=System.Activities"` |
| `project.json` | `"expressionLanguage": "VisualBasic"` | `"expressionLanguage": "CSharp"` |

Always check `project.json` `expressionLanguage` before writing expressions; never mix expression languages.

---

## VB.NET Expression Syntax (Primary)

VB.NET expressions use `[expression]` inline in attributes or typed arguments; explicit `mva:VisualBasicValue` is also valid (for example, a Boolean condition uses `ExpressionText`). XML-escape `<` as `&lt;`, `>` as `&gt;`, `"` as `&quot;`, and `&` as `&amp;`.

For `Throw.Exception`, use short-form class names and assign complex messages to a variable before throwing; see [§ VB.NET Quote Escaping in Throw.Exception](#vbnet-quote-escaping-in-throwexception-critical-for-xaml-generation).

For strings, dates, collections, DataTables, and other VB.NET patterns, see [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md).

---

## C# Expression Syntax (Secondary)

Use `<mca:CSharpValue>` / `<mca:CSharpReference>` wrappers for C# values and lvalues. Do NOT use `[bracket]` notation in C# projects: it creates `VisualBasicValue` nodes and causes validation failures for C#-only syntax.

---

## Workflow Types

### Sequence

Linear, top-to-bottom execution; most common for legacy workflows. Declare variables in `Sequence.Variables`.

### Flowchart

Visual branching with `FlowStep`, `FlowDecision`, and `FlowSwitch`. Set `Flowchart.StartNode` using an `x:Reference` to a defined node; use references in node properties for cross-links.

### State Machine

State-based workflow, used in REFramework. Set the initial state reference and transition destinations; a State Machine needs exactly one `IsFinal="True"` state for proper termination.

For complete templates including ViewState, see [activity-docs/_XAML-GUIDE.md](./activity-docs/_XAML-GUIDE.md).

---

## Arguments (In/Out/InOut)

Declare public-interface arguments in `<x:Members>` as `InArgument(...)`, `OutArgument(...)`, or `InOutArgument(...)` (for example, `x:String`, `x:Int32`, `sd:DataTable`).

| XAML Type | .NET Type | Notes |
|---|---|---|
| `x:String` | System.String | |
| `x:Int32` | System.Int32 | |
| `x:Int64` | System.Int64 | |
| `x:Boolean` | System.Boolean | |
| `x:Double` | System.Double | |
| `x:Object` | System.Object | |
| `x:Decimal` | System.Decimal | |
| `sd:DataTable` | System.Data.DataTable | Requires `xmlns:sd="clr-namespace:System.Data;assembly=System.Data"` |
| `s:DateTime` | System.DateTime | `x:DateTime` is not in the XAML schema |
| `ss:SecureString` | System.Security.SecureString | Requires `xmlns:ss="clr-namespace:System.Security;assembly=mscorlib"` (NOT `xmlns:s`; SecureString is in `System.Security`, not `System`) |
| `scg:Dictionary(x:String, x:Object)` | Dictionary<String, Object> | |
| `scg:List(x:String)` | List<String> | |

The `x:` schema supports only String, Int32, Int64, Double, Boolean, Byte, Single, Decimal, Char, Object, and TimeSpan. Other CLR types need the appropriate namespace prefix (for example, `s:DateTime`, `sd:DataTable`).

---

## Variables

Variables belong to their containing activity; outer-container variables are accessible in nested containers, but not across invoked workflows (use Arguments there). Declare them in the containing activity's `Variables` collection with appropriate `x:TypeArguments`.

---

## XAML Safety Rules

### ViewState Rules (Editing vs Generating)

ViewState controls designer layout.

- **Editing existing workflows:** Do NOT modify the global `<sap2010:WorkflowViewState.ViewStateManager>` or ViewState on unchanged nodes. For new Flowchart/StateMachine nodes, generate `ShapeLocation`, `ShapeSize`, and `ConnectorLocation`; first read existing positions to avoid overlap.
- **Generating new workflows:** Sequence ViewState is optional; Studio auto-manages `IsExpanded`. Flowchart ViewState is **MANDATORY**: generate `ShapeLocation`, `ShapeSize`, and `ConnectorLocation` for every `FlowStep` and `FlowDecision`, plus the Flowchart container's start-node position. StateMachine ViewState is **MANDATORY**: generate `ShapeLocation` and `ShapeSize` for every `State`, plus `StateContainerWidth/Height` on the container.

Without Flowchart/StateMachine node ViewState, Studio stacks nodes at (0,0), producing an unusable jumbled pile. See the Flowchart and StateMachine ViewState Layout Guides in [activity-docs/_XAML-GUIDE.md](./activity-docs/_XAML-GUIDE.md) for coordinate systems, standard sizes, layout algorithms, and examples.

### Preserve xmlns Declarations

Never remove existing root `<Activity>` `xmlns` attributes; only add declarations as needed.

### Respect Expression Language

Always check `project.json` `expressionLanguage` before writing expressions; mixing VB.NET and C# causes build failures.

### Preserve Existing Structure

When editing, do not reformat or re-indent the whole file; change only the needed section. Use the `Edit` tool for targeted replacements, matching exact `old_string` and replacing with `new_string`.

### Validate After Every Change

Run `uip rpa-legacy validate` after every XAML modification. Do not batch edits without validation.

### Unique Identifiers

Every `x:Name` and `sap2010:WorkflowViewState.IdRef` must be unique. Every `x:Reference` must match an existing `x:Name`.

---

## Property Binding: Attributes vs Child Elements

Simple strings, enums, booleans, and VB expressions may be attributes. Output properties and complex objects typically require child property-element syntax (for example, `Assign.To` with `OutArgument` and `Assign.Value` with `InArgument`).

---

## Managing References When Adding Packages (CRITICAL)

Every package used in XAML MUST have its assembly references and namespace imports added; missing references cause expressions using its types to fail validation. Studio normally adds these when activities are dragged onto the canvas or imports are added; programmatic XAML generation must add them manually.

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

In addition to the 16 VB.NET baseline references, C# legacy projects need assembly references `Microsoft.CSharp`, `System.Runtime.Serialization`, `System.ServiceModel`, and `System.ServiceModel.Activities`, plus the `System.Text` namespace import.

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

The `ui` schema prefix (`xmlns:ui="http://schemas.uipath.com/workflow/activities"`) covers most `UiPath.Core.Activities`; prefer it over CLR-based prefixes for core activities such as LogMessage and InvokeCode.

---

## XAML Generation Gotchas

1. Keep every `x:Name` unique; FlowSteps commonly use `__ReferenceID0`, `__ReferenceID1`, etc. Keep every `x:Reference` matched to an `x:Name`; broken references crash the designer. See [Unique Identifiers](#unique-identifiers).
2. `[expr]` is VB.NET only; C# uses `<mca:CSharpValue>`. Check `expressionLanguage` and never mix languages (see [VB.NET vs C# Expression Detection](#vbnet-vs-c-expression-detection)).
3. XML-escape `<` as `&lt;`, `>` as `&gt;`, `"` as `&quot;`, and `&` as `&amp;`.
4. Include all dependency assembly references; missing references cause compilation errors.
5. Never add trailing `<x:Reference>` entries for Flowchart child nodes. Nodes defined inline as direct `<Flowchart>` children must not be re-listed at the end; use `<x:Reference>` only inside property elements (`Flowchart.StartNode`, `FlowStep.Next`, `FlowDecision.True/False`, etc.) for cross-references.
6. A State Machine needs exactly one `IsFinal="True"` state.
7. Legacy uses `assembly=mscorlib`, not `assembly=System.Private.CoreLib` (.NET 6+).
8. Scope activities require an `ActivityAction<T>` body; `ExcelApplicationScope`, `ExcelProcessScopeX`, `ExcelApplicationCard`, `WordApplicationScope`, etc. do not accept direct children. Use `.Body` with `ActivityAction<T>` and `DelegateInArgument`. See [§ Scope Activities Require ActivityAction Body](#scope-activities-require-activityaction-body-critical-for-xaml-generation).

---

## Common Pitfalls & Quick Reference

Essential legacy UiPath gotchas, required scopes, and VB.NET patterns. Full gotchas: [activity-docs/_COMMON-PITFALLS.md](./activity-docs/_COMMON-PITFALLS.md). Full VB.NET cheat sheet: [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md).

### Flowcharts/StateMachines Without ViewState

**Severity: HIGH.** Missing ViewState stacks nodes at (0,0), making the designer unusable. Every Flowchart/StateMachine node needs `ShapeLocation` + `ShapeSize`. Required: `xmlns:av="http://schemas.microsoft.com/winfx/2006/xaml/presentation"`. See [activity-docs/_XAML-GUIDE.md](./activity-docs/_XAML-GUIDE.md) for coordinate systems, standard sizes, layout algorithms, connector formulas, and examples.

### Required Parent Scopes

These classic activities **must** be placed inside a specific parent scope:

| Activities | Required Parent Scope |
|---|---|
| Excel Interop (`ExcelReadRange`, `ExcelWriteCell`, etc.) | `Excel Application Scope` |
| Excel Modern (`ReadRangeX`, `WriteRangeX`, etc.) | `ExcelApplicationCard` inside `ExcelProcessScopeX` |
| PowerPoint Interop (`InsertSlide`, `InsertText`, etc.) | `PowerPoint Application Scope` |
| Word Interop (`AppendText`, `ReplaceText`, etc.) | `Word Application Scope` |
| FTP (`Download`, `Upload`, `Delete`, etc.) | `FTP Session` (`WithFtpSession`) |
| Java (`InvokeJavaMethod`, `LoadJar`, etc.) | `Java Scope` |
| Python (`RunScript`, `InvokeMethod`, etc.) | `Python Scope` |
| Terminal (`GetField`, `SetField`, `SendKeys`, etc.) | `Terminal Session` |
| Office 365 (`SendMail`, `CreateEvent`, etc.) | `Microsoft Office 365 Scope` |
| SAP BAPI (`InvokeSapBapi`) | `SAP Application Scope` |
| SharePoint (`GetListItems`, `UploadFile`, etc.) | `SharePoint Application Scope` |

### Scope Activities Require ActivityAction Body (CRITICAL for XAML Generation)

Scope activities (Excel Application Scope, ExcelProcessScopeX, ExcelApplicationCard, Word Application Scope, etc.) do NOT accept direct children: use an `ActivityAction<T>` body with a `DelegateInArgument`, or validation fails. `RetryScope` also wraps its body, but uses a bare `ActivityAction` (no `x:TypeArguments` or `DelegateInArgument`); see table.

**Wrong — direct children (fails validation):**
```xml
<ueab:ExcelApplicationCard WorkbookPath="file.xlsx">
  <ueab:ReadRangeX ... />  <!-- WRONG -->
</ueab:ExcelApplicationCard>
```

**Correct — ActivityAction body wrapper:**
```xml
<ueab:ExcelApplicationCard WorkbookPath="file.xlsx" DisplayName="Use Excel File">
  <ueab:ExcelApplicationCard.Body>
    <ActivityAction x:TypeArguments="ue:IWorkbookQuickHandle">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="ue:IWorkbookQuickHandle" Name="Excel" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- Child activities go here, using Excel handle -->
        <ueab:ReadRangeX Range="[Excel.Sheet(&quot;Sheet1&quot;).Range(&quot;A1:A20&quot;)]" />
      </Sequence>
    </ActivityAction>
  </ueab:ExcelApplicationCard.Body>
</ueab:ExcelApplicationCard>
```

| Activity | Body TypeArgument | DelegateInArgument Name | Notes |
|---|---|---|---|
| `ExcelProcessScopeX` | `ui:IExcelProcess` | `ExcelProcessScopeTag` | Outer Excel scope |
| `ExcelApplicationCard` | `ue:IWorkbookQuickHandle` | `Excel` | Inner Excel scope inside ExcelProcessScopeX |
| `ExcelApplicationScope` | `ue:WorkbookApplication` | `ExcelWorkbookScope` | Classic Interop scope |
| `ForEachRow` | `ActivityAction(sd:DataRow)` | `row` | Iterates DataTable rows |
| `WordApplicationScope` | (Word handle type) | `WordApplicationScope` | Word COM scope |
| `PowerPointApplicationScope` | (PowerPoint handle type) | `PowerPointApplication` | PowerPoint COM scope |
| `TryCatch` | (special — `Catches` collection) | — | Not ActivityAction; nested body structure |
| `Parallel` | (multiple `Branches`) | — | Each branch is a separate Sequence |
| `RetryScope` | _(none — bare `<ActivityAction>`)_ | — | Property is `.ActivityBody`, not `.Body`; no type argument or `DelegateInArgument` |

Check `find-activities` output for `Body` info when an activity requires `ActivityAction<T>`. Required key xmlns declarations:
- `xmlns:ue="clr-namespace:UiPath.Excel;assembly=UiPath.Excel.Activities"`
- `xmlns:ueab="clr-namespace:UiPath.Excel.Activities.Business;assembly=UiPath.Excel.Activities"`
- `xmlns:ui="http://schemas.uipath.com/workflow/activities"`
- `xmlns:sd="clr-namespace:System.Data;assembly=System.Data"` for `ForEachRow` DataRow.

Modern Excel requires two nested levels, `ExcelProcessScopeX` → `ExcelApplicationCard` → activities; each level has its own `ActivityAction` body. Always check `find-activities` output for scope body patterns.

### Dangerous Defaults (Source Code Verified)

- **`ContinueOnError` defaults to TRUE:** `NetHttpRequest` / `HttpClient` (HTTP Request, Web package) silently returns an empty response on HTTP 500/timeout; Data Scraping wizard output (UIAutomation) silently returns an empty DataTable on extraction failure. Always set `ContinueOnError=False` on HTTP Request activities.
- **Library workflows:** NEVER use `ContinueOnError=True`; consumers cannot know which errors were swallowed. Let exceptions propagate so the consuming process decides how to handle them.
- **Excel AutoSave:** `AutoSave=true` (default) on `ExcelApplicationScope` writes to disk on every Write Cell; 1000 loop operations cause 1000 saves. Set `AutoSave=false` and add one `Save Workbook` at the end.
- **OpenBrowser:** source default `BrowserType` is `IE`; always explicitly set it to Chrome, Firefox, or Edge.
- **HTTP timeout:** legacy `HttpClient` (also internally `NetHttpRequest`) has a 6,000-10,000ms timeout, often too low for production APIs. Set `TimeoutMS` to 30,000-60,000ms.

### VB.NET Quote Escaping in Throw.Exception (CRITICAL for XAML Generation)

`Throw.Exception` wraps bracket expressions in `VisualBasicValue<Exception>`. Fully-qualified class names combined with complex strings containing multiple `&quot;` can fail VB.NET compilation, even if the same escaping works in simpler attributes such as `LogMessage.Message`.

#### What fails

```xml
<!-- FAILS: Fully-qualified name + complex string concatenation -->
<Throw Exception="[New UiPath.Core.Activities.BusinessRuleException(&quot;Invalid amount: &quot; &amp; amount.ToString(&quot;F2&quot;) &amp; &quot; for &quot; &amp; txId)]" />

<!-- FAILS: String.Format with multiple &quot; inside brackets -->
<Throw Exception="[New UiPath.Core.Activities.BusinessRuleException(String.Format(&quot;Invalid amount: {0} for {1}&quot;, amount, txId))]" />
```

#### What works

**Approach 1: Short-form class name + simple expression (recommended for simple messages)**
```xml
<Throw Exception="[New BusinessRuleException(&quot;Invalid amount for &quot; &amp; txId)]" />
```

**Approach 2: Variable for message, then Throw (recommended for complex messages)**
```xml
<Assign DisplayName="Build Error Message">
  <Assign.To>
    <OutArgument x:TypeArguments="x:String">[errorMessage]</OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:String">["Invalid amount: " &amp; amount.ToString("F2") &amp; " for transaction " &amp; txId]</InArgument>
  </Assign.Value>
</Assign>
<Throw Exception="[New BusinessRuleException(errorMessage)]" />
```

#### Rules

1. Always use short-form class names in `Throw.Exception` (`BusinessRuleException`, not `UiPath.Core.Activities.BusinessRuleException`); ensure `UiPath.Core.Activities` is imported.
2. For complex messages, assign the message string to a variable first and throw using that variable.
3. Simple inline messages work: `[New BusinessRuleException(&quot;simple message&quot;)]`.
4. Apply the same rules to `Exception`, `BusinessRuleException`, `ArgumentException`, and other exception types.

A long fully-qualified type path plus embedded `&quot;` literals and concatenation can confuse the `VisualBasicValue<Exception>` expression compiler; shorter expressions or variable references avoid this.

### Top Gotchas by Package

- **Excel:** crashes can leave zombie `EXCEL.EXE` processes—use Kill Process in Finally; dates may read as serials—set `PreserveFormat=true` or convert using `DateTime.FromOADate()`; empty Read Range DataTable—verify sheet name and use `""` for entire used range; Write Range strips formatting—use Write Cell in loops for small updates.
- **UIAutomation:** TypeInto requires escaping `{`, `}`, `[`, `]`, `+`, `^`, `%`, `~` with forms such as `{{}`, `{+}`; `EmptyField` is ignored with SimulateType and works only with hardware events or SendWindowMessages; selectors that work in Studio may fail on Robot—use SimulateClick/SimulateType and avoid `idx`; dynamic selectors—use `*` wildcards and prefer `AutomationId`.
- **Mail:** Gmail/M365 SMTP auth—use App Passwords or OAuth2, not “Less Secure Apps”; port 587 = STARTTLS, 465 = implicit SSL, 25 = unencrypted; separate multiple recipients with semicolons `;`, not commas.
- **Web:** HTTP Request `ContinueOnError=TRUE` by default silently swallows errors; legacy HttpClient timeout is 6 seconds—raise to 30-60 seconds.
- **PDF:** empty `ReadPDFText` may mean scanned images—use Read PDF With OCR; text out of order—set `PreserveFormatting=true`.
- **GenericValue:** comparisons are string-based (`"10" > "9"` returns False)—use `CInt()`; any non-null, non-empty string converts to `True`; `GenericValue(null)` converts to int `0` and DateTime `DateTime.MinValue`. Avoid GenericValue; use strongly typed variables.

### VB.NET Quick Reference

For the complete cheat sheet (string/type/DateTime/collection/DataTable operations, file paths, Orchestrator patterns), see [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md).

### Common XAML Generation Mistakes

Check generated XAML for these errors:

#### Hallucination-Prone Activity Names

| Wrong (invented) | Correct | Package |
|---|---|---|
| `ReadExcel`, `WriteExcel` | `ExcelReadRange`, `ExcelWriteRange` | Excel |
| `SendEmail` | `SendSmtpMailMessage`, `SendOutlookMailMessage` | Mail |
| `OpenBrowserActivity` | `OpenBrowser` | UIAutomation |
| `ReadPdf` | `ReadPDFText`, `ReadPDFWithOCR` | PDF |
| `HttpRequest` | `HttpClient` (also known as `NetHttpRequest`) | Web |

NEVER guess activity names; run `find-activities` for the exact class name.

#### Nesting Errors

| Mistake | Fix |
|---|---|
| Multiple children directly inside `If.Then` or `If.Else` | Wrap them in one `Sequence` |
| Activities directly inside `ForEach` body | Use an `ActivityAction` wrapper (see Scope Activities section above) |
| Activities directly inside scope activities (Excel, Word, etc.) | Use the `ActivityAction<T>` body pattern |
| ViewState references nonexistent workflow nodes | Remove orphaned ViewState entries or add the missing nodes |

#### Expression Language Mismatches

| Mistake | Symptom | Fix |
|---|---|---|
| C# operators (`!=`, `&&`, `\|\|`) in VB.NET | Compilation error | Use `<>`, `AndAlso`, `OrElse` |
| C# interpolation `$"..."` in VB.NET | Compilation error | Use `String.Format` or `&` concatenation |
| VB.NET `[bracket]` expressions in C# | Compilation error | Use `<mca:CSharpValue>` or `<mca:CSharpReference>` |

#### Security Anti-Patterns

| Anti-Pattern | Risk | Fix |
|---|---|---|
| Password in `String` variable | Visible in logs and memory dumps | Use `SecureString` |
| Hardcoded API keys or JWT tokens in XAML | Credentials in source control | Use Orchestrator Credential assets |
| Hardcoded URLs in activity properties | Breaks across environments | Use Config.xlsx Settings or Orchestrator Text assets |
| Empty `Catch ex As Exception` body | Silent failures, impossible to debug | At minimum, log `ex.Message` with `Log Message` |
| Timeout magic numbers (for example, `30000`) | Unclear intent, hard to tune | Use Config.xlsx Constants with descriptive names |

### Deprecated Activity → Replacement

Full mapping: [activity-docs/_PATTERNS.md § Deprecated Activities](./activity-docs/_PATTERNS.md).
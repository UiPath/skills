# Common Pitfalls & Quick Reference

Essential gotchas, required scopes, and VB.NET patterns for legacy UiPath RPA workflows.

For the complete gotchas list, see [activity-docs/_COMMON-PITFALLS.md](./activity-docs/_COMMON-PITFALLS.md).
For the complete VB.NET cheat sheet, see [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md).

---

## Required Parent Scopes

These classic activities **must** be placed inside a specific parent scope:

| Activities | Required Parent Scope |
|-----------|----------------------|
| Excel Interop (ExcelReadRange, ExcelWriteCell, etc.) | `Excel Application Scope` |
| Excel Modern (ReadRangeX, WriteRangeX, etc.) | `ExcelApplicationCard` inside `ExcelProcessScopeX` |
| PowerPoint Interop (InsertSlide, InsertText, etc.) | `PowerPoint Application Scope` |
| Word Interop (AppendText, ReplaceText, etc.) | `Word Application Scope` |
| FTP activities (Download, Upload, Delete, etc.) | `FTP Session` (WithFtpSession) |
| Java activities (InvokeJavaMethod, LoadJar, etc.) | `Java Scope` |
| Python activities (RunScript, InvokeMethod, etc.) | `Python Scope` |
| Terminal activities (GetField, SetField, SendKeys, etc.) | `Terminal Session` |
| Office 365 activities (SendMail, CreateEvent, etc.) | `Microsoft Office 365 Scope` |
| SAP BAPI activities (InvokeSapBapi) | `SAP Application Scope` |
| SharePoint activities (GetListItems, UploadFile, etc.) | `SharePoint Application Scope` |

---

## Scope Activities Require ActivityAction Body (CRITICAL for XAML Generation)

Scope activities (Excel Application Scope, ExcelProcessScopeX, ExcelApplicationCard, Word Application Scope, etc.) do **NOT** accept direct children. They require an `ActivityAction<T>` body wrapper with a `DelegateInArgument`. Placing activities directly inside the scope element will fail validation.

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

### Common Scope Body Patterns

| Scope Activity | Body TypeArgument | DelegateInArgument Name |
|---------------|-------------------|------------------------|
| `ExcelProcessScopeX` | `ui:IExcelProcess` | `ExcelProcessScopeTag` |
| `ExcelApplicationCard` (Use Excel File) | `ue:IWorkbookQuickHandle` | `Excel` |
| `ExcelApplicationScope` (classic Interop) | `ue:WorkbookApplication` | `ExcelWorkbookScope` |
| `WordApplicationScope` | (Word handle type) | `WordApplicationScope` |
| `PowerPointApplicationScope` | (PowerPoint handle type) | `PowerPointApplication` |

**Key xmlns required:**
- `xmlns:ue="clr-namespace:UiPath.Excel;assembly=UiPath.Excel.Activities"`
- `xmlns:ueab="clr-namespace:UiPath.Excel.Activities.Business;assembly=UiPath.Excel.Activities"`
- `xmlns:ui="http://schemas.uipath.com/workflow/activities"`

**Nested scopes:** Modern Excel requires TWO levels: `ExcelProcessScopeX` → `ExcelApplicationCard` → activities. Each level has its own `ActivityAction` body.

**Always use `find-activities --include-type-definitions`** to discover the exact TypeArgument and body structure for any scope activity. Do not guess.

---

## Dangerous Defaults (Source Code Verified)

### ContinueOnError Defaults to TRUE
These activities **silently swallow all errors** by default:

| Activity | Package | Impact |
|----------|---------|--------|
| `NetHttpRequest` (HTTP Request) | Web | HTTP 500/timeout → empty response, no error |
| `Data Scraping` wizard output | UIAutomation | Extraction failure → empty DataTable |

**Always** set `ContinueOnError=False` on HTTP Request activities.

### Excel AutoSave Causes Performance Disasters
`AutoSave=true` (default) on `ExcelApplicationScope` means every Write Cell triggers a disk write. In loops with 1000 operations, that's 1000 saves.

**Fix:** Set `AutoSave=false`, add a single `Save Workbook` at the end.

### OpenBrowser Defaults to Internet Explorer
`BrowserType` defaults to `IE` in source code. **Always explicitly set** BrowserType to Chrome, Firefox, or Edge.

### HTTP Request Very Short Timeout
Legacy `HttpClient` timeout is only 6,000ms. `NetHttpRequest` default is 10,000ms. Both are often too low for production APIs.

**Fix:** Set `TimeoutMS` to 30,000-60,000ms.

---

## VB.NET Quote Escaping in Throw.Exception (CRITICAL for XAML Generation)

The `Throw.Exception` attribute wraps the bracket expression in `VisualBasicValue<Exception>`. When fully-qualified class names are combined with complex string expressions containing multiple `&quot;`, the VB.NET compiler can reject the expression — even though the same `&quot;` escaping works fine in simpler attributes like `LogMessage.Message`.

### What fails

```xml
<!-- FAILS: Fully-qualified name + complex string concatenation -->
<Throw Exception="[New UiPath.Core.Activities.BusinessRuleException(&quot;Invalid amount: &quot; &amp; amount.ToString(&quot;F2&quot;) &amp; &quot; for &quot; &amp; txId)]" />

<!-- FAILS: String.Format with multiple &quot; inside brackets -->
<Throw Exception="[New UiPath.Core.Activities.BusinessRuleException(String.Format(&quot;Invalid amount: {0} for {1}&quot;, amount, txId))]" />
```

### What works

**Approach 1: Short-form class name + simple expression (recommended for simple messages)**
```xml
<!-- Works: Short name (namespace already imported) + simple concatenation -->
<Throw Exception="[New BusinessRuleException(&quot;Invalid amount for &quot; &amp; txId)]" />
```

**Approach 2: Variable for message, then Throw (recommended for complex messages)**
```xml
<!-- Best practice from codebase: construct message in a variable, then throw -->
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

### Rules

1. **Always use short-form class names** in `Throw.Exception` — `BusinessRuleException` not `UiPath.Core.Activities.BusinessRuleException`. Ensure `UiPath.Core.Activities` is in the namespace imports.
2. **For complex messages, use the variable approach** — Assign the message string to a variable first, then pass the variable to the exception constructor.
3. **For simple messages, inline is fine** — `[New BusinessRuleException(&quot;simple message&quot;)]` works.
4. **Same rules apply to all exception types** — `Exception`, `BusinessRuleException`, `ArgumentException`, etc.

### Why this happens

`Throw.Exception` compiles the bracket expression via `VisualBasicValue<Exception>`. The combination of a long fully-qualified type path + embedded `&quot;` string literals with concatenation operators creates ambiguity for the VB.NET expression compiler. Shorter expressions or variable references avoid this.

---

## Top Gotchas by Package

### Excel
- **Zombie EXCEL.EXE processes** after workflow crashes — use Kill Process in Finally block
- **Dates read as serial numbers** — set `PreserveFormat=true` or convert with `DateTime.FromOADate()`
- **Empty DataTable from Read Range** — verify sheet name, use `""` for entire used range
- **Write Range strips formatting** — use Write Cell in loops for small updates

### UIAutomation
- **TypeInto missing/wrong characters** — escape `{`, `}`, `[`, `]`, `+`, `^`, `%`, `~` with `{{}`, `{+}` etc.
- **EmptyField ignored with SimulateType** — only works with hardware events or SendWindowMessages
- **Selectors work in Studio, fail on Robot** — use SimulateClick/SimulateType, avoid `idx` attribute
- **Dynamic selectors break** — use wildcards `*` for dynamic parts, prefer `AutomationId`

### Mail
- **SMTP auth fails with Gmail/M365** — use App Passwords or OAuth2, not "Less Secure Apps"
- **SSL/TLS port mismatch** — Port 587 = STARTTLS, Port 465 = implicit SSL, Port 25 = unencrypted
- **Multiple recipients** — use semicolons `;` not commas

### Web
- **HTTP Request ContinueOnError=TRUE by default** — errors silently swallowed
- **Legacy HttpClient 6-second timeout** — increase to 30-60 seconds

### PDF
- **ReadPDFText returns empty** — PDF is scanned images, use Read PDF With OCR instead
- **Text out of order** — set `PreserveFormatting=true`

### GenericValue
- **String comparison instead of numeric** — `"10" > "9"` returns False. Use `CInt()` explicitly.
- **Boolean conversion trap** — ANY non-null, non-empty string converts to `True`
- **Null converts to 0** — `GenericValue(null)` → int returns `0`, → DateTime returns `DateTime.MinValue`

**Recommendation:** Avoid GenericValue entirely. Use strongly-typed variables.

---

## VB.NET Quick Reference

### String Operations
```vb
"Hello " + variable + " World"              ' Concatenation
String.IsNullOrEmpty(myVar)                  ' Null/empty check
If(myVar Is Nothing, "default", myVar.ToString())  ' Null coalesce
myString.Contains("search")                  ' Contains
myString.Replace("old", "new")               ' Replace
myString.Split({";"c}, StringSplitOptions.RemoveEmptyEntries)  ' Split
```

### Type Conversions
```vb
CInt(stringVar)                ' String to Integer
CDbl(stringVar)                ' String to Double
CDate(stringVar)               ' String to Date
CType(objVar, String)          ' Object to specific type
DirectCast(objVar, DataTable)  ' Object to DataTable
```

### DateTime
```vb
DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
DateTime.Now.AddDays(7)
(endDate - startDate).TotalDays
```

### Collections
```vb
New String() {"item1", "item2"}              ' Array
New List(Of String) From {"a", "b"}          ' List
New Dictionary(Of String, Object) From {{"key", "value"}}  ' Dictionary
```

### DataTable Access
```vb
row("ColumnName").ToString()                 ' Cell by name
row(0).ToString()                            ' Cell by index
Convert.ToInt32(row("Amount"))               ' Typed value
dt.Select("[Status] = 'Active'")             ' Filter (returns DataRow[])
dt.AsEnumerable().Where(Function(r) r("Col").ToString() = "Val").CopyToDataTable()  ' LINQ
```

### Error Handling
```vb
' Use Try-Catch activity (not code)
' BusinessRuleException → skip item
' System.Exception → retry/escalate
' Always set ContinueOnError=False on HTTP Request
```

For the complete reference with DataTable operations, file paths, Orchestrator patterns, and deprecated activity mappings, see [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md).

---

## Deprecated Activity → Replacement

| Deprecated | Replacement |
|-----------|-------------|
| `OpenWorkbook` | `Excel Application Scope` |
| `CloseWorkbook` | (scope handles cleanup) |
| `ExcelForEachRow` (v1) | `For Each Row in Data Table` |
| `KeywordBasedClassifier` | `IntelligentKeywordClassifier` |
| `OutlookForEachMail` | `For Each Email` |

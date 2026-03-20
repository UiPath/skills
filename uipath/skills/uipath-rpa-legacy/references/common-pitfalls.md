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

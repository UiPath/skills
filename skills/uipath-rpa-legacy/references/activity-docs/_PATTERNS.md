# UiPath Legacy Workflows - Practical Patterns & Cheat Sheet

## Purpose
Quick-reference patterns for writing legacy XAML workflows: VB.NET expressions, DataTable operations, error handling, required scopes, and common recipes.

---

## Required Parent Scopes

See [common-pitfalls.md](../common-pitfalls.md) for the canonical Required Parent Scopes table and ActivityAction body patterns.

---

## VB.NET Expression Cheat Sheet

### String Operations
```vb
' Concatenation
"Hello " + variable + " World"
String.Format("Order {0} has {1} items", orderId, count)
$"Order {orderId} has {count} items"    ' String interpolation (2021.10+)

' Null/empty check
String.IsNullOrEmpty(myVar)
String.IsNullOrWhiteSpace(myVar)
If(myVar Is Nothing, "default", myVar.ToString())

' Common operations
myString.Trim()
myString.ToUpper() / myString.ToLower()
myString.Contains("search")
myString.Replace("old", "new")
myString.Split({";"c}, StringSplitOptions.RemoveEmptyEntries)
myString.Substring(startIndex, length)
System.Text.RegularExpressions.Regex.Match(input, pattern).Value
```

### Type Conversions
```vb
' String to number
CInt(stringVar)           ' To Integer (throws on failure)
CDbl(stringVar)           ' To Double
CDec(stringVar)           ' To Decimal
Convert.ToInt32(stringVar)
Integer.Parse(stringVar)
Int32.TryParse(stringVar, result)  ' Safe parse (returns bool)

' String to date
CDate(stringVar)
DateTime.Parse(stringVar)
DateTime.ParseExact(stringVar, "MM/dd/yyyy", CultureInfo.InvariantCulture)
DateTime.Now / DateTime.Today / DateTime.UtcNow

' Number to string
intVar.ToString()
doubleVar.ToString("F2")      ' 2 decimal places
doubleVar.ToString("#,##0.00") ' With thousands separator

' Object to specific type
CType(objVar, String)
DirectCast(objVar, DataTable)
CStr(objVar)
```

### DateTime Operations
```vb
DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
DateTime.Now.AddDays(7)
DateTime.Now.AddHours(-2)
(endDate - startDate).TotalDays
DateTime.Now.ToString("yyyyMMdd")  ' Compact date for filenames
```

### Array/Collection Creation
```vb
' Array
New String() {"item1", "item2", "item3"}
New Integer() {1, 2, 3}

' List
New List(Of String) From {"item1", "item2"}

' Dictionary
New Dictionary(Of String, Object) From {
  {"key1", "value1"},
  {"key2", 42}
}
```

---

## DataTable Operations Cheat Sheet

### Creating
```vb
' Use Build Data Table activity (wizard) for design-time creation
' Or in code:
New DataTable()
```

### Accessing Data
```vb
' Get cell value by column name
row("ColumnName").ToString()
row.Item("ColumnName").ToString()

' Get cell value by column index (0-based)
row(0).ToString()

' Get value with null safety
If(row("Column") Is Nothing OrElse row("Column") Is DBNull.Value,
   "default",
   row("Column").ToString())

' Get typed value
Convert.ToInt32(row("Amount"))
Convert.ToDateTime(row("Date"))
```

### Filtering & Querying
```vb
' DataTable.Select (returns DataRow array)
dt.Select("[Status] = 'Active'")
dt.Select("[Amount] > 100")
dt.Select("[Name] LIKE 'John%'")
dt.Select("[Date] >= #2024-01-01#")
dt.Select("[Column] = 'Value'", "Date DESC")  ' With sort

' LINQ (requires System.Linq import)
dt.AsEnumerable().Where(Function(r) r("Status").ToString() = "Active").CopyToDataTable()
dt.AsEnumerable().OrderBy(Function(r) r("Name")).CopyToDataTable()
dt.AsEnumerable().Select(Function(r) r("Name").ToString()).ToArray()

' Count rows matching condition
dt.Select("[Status] = 'Active'").Count()
dt.AsEnumerable().Count(Function(r) CInt(r("Amount")) > 100)
```

### Modifying
```vb
' Add row (in Assign)
dt.Rows.Add({"col1value", "col2value", "col3value"})

' Remove column
dt.Columns.Remove("ColumnName")

' Rename column
dt.Columns("OldName").ColumnName = "NewName"

' Clone structure without data
dt.Clone()

' Copy structure with data
dt.Copy()

' Trim column names (common fix for Read Range whitespace)
For Each col As DataColumn In dt.Columns
    col.ColumnName = col.ColumnName.Trim()
Next
```

### Common Gotchas
- `row("Column")` returns `Object` - always `.ToString()` or convert explicitly
- Empty cells may be `DBNull.Value` (not Nothing/null) - check with `row("Col") Is DBNull.Value`
- Column names are case-sensitive in `.Select()` expressions
- Column names with spaces need brackets: `[Column Name]`
- `CopyToDataTable()` throws if LINQ query returns empty - wrap in If check

---

## Error Handling Quick Reference

For the full error handling guide (exception classification, TryCatch best practices, Retry Scope configuration, ContinueOnError decision matrix, Finally patterns), see [error-handling-guide.md](../error-handling-guide.md).

### Throw Activity — Quote Escaping Gotcha (XAML Generation)

In `Throw.Exception` bracket expressions, fully-qualified class names + complex string concatenation with `&quot;` can cause compiler errors. The VB.NET expression compiler rejects the combination.

**Rules:**
1. **Use short-form class names** — `BusinessRuleException` not `UiPath.Core.Activities.BusinessRuleException`
2. **For complex messages, use a variable** — Assign the message string first, then `[New BusinessRuleException(errorMessage)]`
3. **Simple inline is fine** — `[New BusinessRuleException(&quot;simple message&quot;)]`

```xml
<!-- GOOD: Short name + simple expression -->
<Throw Exception="[New BusinessRuleException(&quot;Invalid data for &quot; &amp; txId)]" />

<!-- BEST: Variable approach for complex messages -->
<!-- Step 1: Assign errorMessage = "Invalid: " & amount.ToString("F2") & " for " & txId -->
<!-- Step 2: Throw with variable reference -->
<Throw Exception="[New BusinessRuleException(errorMessage)]" />
```

### REFramework Exception Types
| Exception | Meaning | Action |
|-----------|---------|--------|
| `BusinessRuleException` | Data/logic problem (invalid input, missing field) | Skip item, set Failed status |
| `System.Exception` | Technical problem (timeout, app crash, network) | Retry, then escalate |
| `SelectorNotFoundException` | UI element not found | Check app state, retry |
| `TimeoutException` | Activity exceeded timeout | Retry with longer timeout |

---

## Orchestrator Integration Patterns

### Queue Processing (Dispatcher + Performer)
```
DISPATCHER workflow:
1. Read input data (Excel, DB, email)
2. For Each row: Add Queue Item (QueueName, ItemInformation dictionary)

PERFORMER workflow (REFramework):
1. Get Transaction Item (QueueName)
2. If TransactionItem Is Nothing → no more items
3. Process item (access data via TransactionItem.SpecificContent("FieldName"))
4. Set Transaction Status (Success/Failed)
```

### Asset Access Patterns
```vb
' Get text asset
assetValue = Get Asset("MyAssetName")  ' Returns String

' Get credential asset
Get Credential("MyCredential") → username (String), password (SecureString)

' Convert SecureString to String (when needed)
New System.Net.NetworkCredential("", securePassword).Password
```

### Storage Bucket File Patterns
```
Upload: Upload Storage File (BucketName, LocalPath, RemoteBlobPath)
Download: Download Storage File (BucketName, RemoteBlobPath, LocalPath)
List: List Storage Files (BucketName) → IEnumerable of file info
```

---

## File Path Patterns
```vb
' Project-relative path
Path.Combine(Environment.CurrentDirectory, "Data", "input.xlsx")

' User folders
Environment.GetFolderPath(Environment.SpecialFolder.Desktop)
Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments)

' Temp file
Path.Combine(Path.GetTempPath(), "output_" + DateTime.Now.ToString("yyyyMMdd") + ".xlsx")

' Safe path joining (handles separators)
Path.Combine(folderPath, fileName)

' Extract parts
Path.GetFileName(fullPath)          ' "file.xlsx"
Path.GetFileNameWithoutExtension()  ' "file"
Path.GetExtension()                 ' ".xlsx"
Path.GetDirectoryName()             ' parent folder
```

---

## Deprecated Activity → Replacement Mapping

| Deprecated | Replacement | Package |
|-----------|-------------|---------|
| `OpenWorkbook` | `Excel Application Scope` | Excel |
| `CloseWorkbook` | (scope handles cleanup) | Excel |
| `WithWorkbook` | `Excel Application Scope` | Excel |
| `ExcelForEachRow` (v1) | `For Each Row in Data Table` | Excel |
| `CreatePivotTableX` (v1) | `CreatePivotTableXv2` | Excel |
| `KeywordBasedClassifier` | `IntelligentKeywordClassifier` | IntelligentOCR |
| `AddTestDataQueueItem` | `NewAddTestDataQueueItem` | Testing |
| `OutlookForEachMail` | `For Each Email` | Mail |
| `OverwriteExistingFile` (property) | `ConflictResolution` enum | GSuite Drive |
| `SingleFileToUpload` (property) | `MultipleFilesToUpload` | GSuite Drive |
| `UseISConnection` (property) | `ConnectionDetails` | Mail |

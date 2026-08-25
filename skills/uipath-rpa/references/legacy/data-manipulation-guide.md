# Data Manipulation Guide

Advanced data manipulation patterns for legacy UiPath workflows: RegEx, LINQ, JObject, StringBuilder, and type conversion edge cases.

For basic VB.NET expressions (strings, DataTable access, DateTime, collections), see [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md).

---

## 1. Regular Expressions (RegEx)

Use `System.Text.RegularExpressions.Regex` for pattern matching and extraction. Available by default in legacy projects.

### Common Patterns

| Pattern | RegEx | Match Examples |
|---|---|---|
| Email | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` | `user@example.com` |
| Phone (US) | `\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}` | `(555) 123-4567`, `555.123.4567` |
| Date (MM/DD/YYYY) | `\d{2}/\d{2}/\d{4}` | `01/15/2025` |
| Date (YYYY-MM-DD) | `\d{4}-\d{2}-\d{2}` | `2025-01-15` |
| Currency (USD) | `\$[\d,]+\.?\d{0,2}` | `$1,234.56`, `$50` |
| Invoice Number | `INV-\d{4,10}` | `INV-12345`, `INV-0001234567` |
| ZIP Code (US) | `\d{5}(-\d{4})?` | `90210`, `90210-1234` |
| SSN | `\d{3}-\d{2}-\d{4}` | `123-45-6789` |
| IP Address | `\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` | `192.168.1.1` |
| Decimal Number | `-?\d+\.?\d*` | `123.45`, `-67`, `0.5` |

### VB.NET Usage

```vb
' Check if string matches pattern
System.Text.RegularExpressions.Regex.IsMatch(inputText, "\d{3}-\d{2}-\d{4}")

' Extract first match
System.Text.RegularExpressions.Regex.Match(inputText, "INV-\d+").Value

' Extract all matches (returns MatchCollection — iterate in ForEach)
System.Text.RegularExpressions.Regex.Matches(inputText, "\$[\d,]+\.?\d{0,2}")

' Replace matched text
System.Text.RegularExpressions.Regex.Replace(inputText, "\s+", " ")

' Extract with named groups
System.Text.RegularExpressions.Regex.Match(inputText, "(?<amount>\$[\d,.]+)\s+(?<date>\d{2}/\d{2}/\d{4})")
' Access: match.Groups("amount").Value, match.Groups("date").Value
```

### Rules

1. **Use `Regex.IsMatch` before `Regex.Match`** when you only need a boolean check
2. **Use named groups `(?<name>...)` for multi-value extraction** — clearer than positional groups
3. **Escape special characters** — `.` matches any character; use `\.` for literal dot
4. **Test patterns on sample data first** — regex bugs silently return empty matches
5. **Set a timeout for complex patterns** — `New Regex(pattern, RegexOptions.None, TimeSpan.FromSeconds(5))` prevents catastrophic backtracking

---

## 2. StringBuilder

Use `System.Text.StringBuilder` when concatenating strings in a loop. Regular `+` concatenation creates a new string object each iteration, wasting memory for large loops.

### When to Use

| Scenario | Use |
|---|---|
| Concatenating < 10 strings | Regular `+` or `String.Format` |
| Building a string in a loop (10+ iterations) | `StringBuilder` |
| Building large HTML/XML content | `StringBuilder` |
| Simple single-line concatenation | Regular `+` |

### VB.NET Pattern (InvokeCode)

```vb
Dim sb As New System.Text.StringBuilder()
For Each row As DataRow In dt.Rows
    sb.AppendLine(row("Name").ToString() & "," & row("Amount").ToString())
Next
Dim result As String = sb.ToString()
```

### In Workflow (without InvokeCode)

1. Assign: `sb = New System.Text.StringBuilder()` (variable type: `System.Text.StringBuilder`)
2. Inside For Each: Assign: `sb.AppendLine(row("Name").ToString())`
3. After loop: Assign: `result = sb.ToString()`

---

## 3. Advanced LINQ for DataTables

All LINQ operations require `System.Linq` in namespace imports (included by default in legacy projects). DataTable LINQ requires `.AsEnumerable()` first.

### GroupBy

```vb
' Group rows by department, returns IEnumerable(Of IGrouping)
dt.AsEnumerable().GroupBy(Function(r) r("Department").ToString())

' Get grouped counts
dt.AsEnumerable() _
    .GroupBy(Function(r) r("Department").ToString()) _
    .Select(Function(g) New Object() {g.Key, g.Count()})
```

### OrderBy / ThenBy

```vb
' Single sort
dt.AsEnumerable() _
    .OrderBy(Function(r) r("Name").ToString()) _
    .CopyToDataTable()

' Descending
dt.AsEnumerable() _
    .OrderByDescending(Function(r) Convert.ToDouble(r("Amount"))) _
    .CopyToDataTable()

' Multi-column sort
dt.AsEnumerable() _
    .OrderBy(Function(r) r("Department").ToString()) _
    .ThenByDescending(Function(r) Convert.ToDouble(r("Amount"))) _
    .CopyToDataTable()
```

### Aggregations

```vb
' Sum
dt.AsEnumerable().Sum(Function(r) Convert.ToDouble(r("Amount")))

' Average
dt.AsEnumerable().Average(Function(r) Convert.ToDouble(r("Amount")))

' Count with condition
dt.AsEnumerable().Count(Function(r) r("Status").ToString() = "Active")

' Min / Max
dt.AsEnumerable().Min(Function(r) Convert.ToDateTime(r("Date")))
dt.AsEnumerable().Max(Function(r) Convert.ToDouble(r("Amount")))
```

### Any / All

```vb
' Check if any row matches
dt.AsEnumerable().Any(Function(r) Convert.ToDouble(r("Amount")) > 10000)

' Check if all rows match
dt.AsEnumerable().All(Function(r) Not String.IsNullOrEmpty(r("Email").ToString()))
```

### Distinct

```vb
' Distinct values from one column
dt.AsEnumerable().Select(Function(r) r("Department").ToString()).Distinct().ToArray()

' Distinct rows (by all columns) — use DataRowComparer
dt.AsEnumerable().Distinct(DataRowComparer.Default).CopyToDataTable()
```

### Take / Skip (Pagination)

```vb
' First 10 rows
dt.AsEnumerable().Take(10).CopyToDataTable()

' Skip first 10, take next 10
dt.AsEnumerable().Skip(10).Take(10).CopyToDataTable()
```

### CopyToDataTable Gotcha

`CopyToDataTable()` throws `InvalidOperationException` when the LINQ result is empty. ALWAYS check first:

```vb
Dim filtered = dt.AsEnumerable().Where(Function(r) r("Status").ToString() = "Active")
If filtered.Any() Then
    resultDt = filtered.CopyToDataTable()
Else
    resultDt = dt.Clone()  ' Empty DataTable with same structure
End If
```

---

## 4. Dictionary Operations

### Common Operations

```vb
' Check if key exists
myDict.ContainsKey("KeyName")

' Safe get (avoids KeyNotFoundException)
Dim value As String = Nothing
If myDict.TryGetValue("KeyName", value) Then
    ' Use value
End If

' Iterate key-value pairs (ForEach with TypeArgument KeyValuePair(Of String, Object))
For Each kvp As KeyValuePair(Of String, Object) In myDict
    ' kvp.Key, kvp.Value
Next

' Get all keys or values
myDict.Keys.ToList()
myDict.Values.ToList()

' Merge two dictionaries (second overwrites first on key conflicts)
For Each kvp In dict2
    dict1(kvp.Key) = kvp.Value
Next

' Count
myDict.Count
```

### Nested Dictionaries

For Config.xlsx-style hierarchical data:

```vb
' Dictionary(Of String, Dictionary(Of String, String))
Dim settings = DirectCast(configDict("DatabaseSettings"), Dictionary(Of String, String))
Dim connString = settings("ConnectionString")
```

---

## 5. JObject / JArray (Newtonsoft.Json)

`Newtonsoft.Json` is bundled with UiPath legacy projects. Use `Newtonsoft.Json.Linq` for JSON parsing and manipulation.

### Parsing

```vb
' Parse JSON string to JObject
Dim jObj = Newtonsoft.Json.Linq.JObject.Parse(jsonString)

' Parse JSON array
Dim jArr = Newtonsoft.Json.Linq.JArray.Parse(jsonArrayString)
```

### Accessing Values

```vb
' Top-level property
jObj("name").ToString()

' Nested property
jObj("address")("city").ToString()

' Array element
jArr(0)("name").ToString()

' Safe access (returns Nothing if path doesn't exist)
jObj("optional")?("nested")?.ToString()

' Typed value
jObj("count").Value(Of Integer)()
jObj("isActive").Value(Of Boolean)()
```

### Querying with LINQ to JSON

```vb
' Select all items matching condition
jArr.Where(Function(item) item("status").ToString() = "active")

' Select specific field from array
jArr.Select(Function(item) item("name").ToString()).ToList()
```

### Creating/Modifying

```vb
' Create JObject
Dim jObj = New Newtonsoft.Json.Linq.JObject()
jObj("name") = "John"
jObj("age") = 30

' Serialize back to string
Dim jsonString = jObj.ToString()
' Or compact: Newtonsoft.Json.JsonConvert.SerializeObject(jObj)
```

### API Response Pattern

```vb
' HTTP Request → responseBody (String)
' Parse response
Dim response = Newtonsoft.Json.Linq.JObject.Parse(responseBody)

' Check for errors
If response("error") IsNot Nothing Then
    Throw New BusinessRuleException("API error: " & response("error")("message").ToString())
End If

' Extract data
Dim items = DirectCast(response("data")("items"), Newtonsoft.Json.Linq.JArray)
For Each item In items
    ' Process item("id").ToString(), item("name").ToString()
Next
```

---

## 6. Null Safety Patterns

### String Null Checks

```vb
' Check for null or empty
String.IsNullOrEmpty(myVar)

' Check for null, empty, or whitespace-only
String.IsNullOrWhiteSpace(myVar)

' Null coalesce (return default if null)
If(myVar Is Nothing, "default", myVar.ToString())
If(String.IsNullOrEmpty(myVar), "default", myVar)
```

### DataRow Null Checks

```vb
' Cell may be DBNull (not Nothing)
If row("Column") Is DBNull.Value OrElse row("Column") Is Nothing Then
    ' Handle missing value
Else
    Dim value = row("Column").ToString()
End If

' Compact check
If(IsDBNull(row("Column")), "default", row("Column").ToString())
```

### Object/Generic Null Checks

```vb
' Check Nothing
If myObject Is Nothing Then ...

' Safe ToString
If(myObject Is Nothing, "", myObject.ToString())

' Type check before cast
If TypeOf myObject Is DataTable Then
    Dim dt = DirectCast(myObject, DataTable)
End If
```

---

## 7. Type Conversion Edge Cases

### Integer Parsing

| Method | Behavior on Failure | Use When |
|---|---|---|
| `CInt(value)` | Throws `InvalidCastException` | VB.NET shorthand, known-good data |
| `Convert.ToInt32(value)` | Throws `FormatException` | .NET standard, handles null (returns 0) |
| `Integer.Parse(value)` | Throws `FormatException` | Explicit intent, known-good data |
| `Int32.TryParse(value, result)` | Returns `False`, sets result to 0 | **SAFEST** — use for external/user input |

### Culture-Dependent Parsing

Number and date formats differ by culture. **ALWAYS specify culture for external data:**

```vb
' DANGEROUS: depends on system locale
CDbl("1,234.56")   ' Works on US locale, fails on German locale (1.234,56)

' SAFE: explicit culture
Double.Parse("1,234.56", System.Globalization.CultureInfo.InvariantCulture)

' SAFE: explicit date format
DateTime.ParseExact("01/15/2025", "MM/dd/yyyy", System.Globalization.CultureInfo.InvariantCulture)
```

### Common Conversion Traps

| Trap | Issue | Fix |
|---|---|---|
| `CInt("12.5")` | Rounds to 12 (not truncates) | Use `CInt(Math.Floor(CDbl("12.5")))` for truncation |
| `CDate("01/02/2025")` | Jan 2 or Feb 1? Depends on locale | Use `DateTime.ParseExact` with explicit format |
| `CBool("yes")` | Throws — only `"True"`/`"False"` work | Use `If(value.ToLower() = "yes", True, False)` |
| `GenericValue("10") > GenericValue("9")` | Returns `False` — string comparison | Cast to `Int32` first: `CInt(gv1) > CInt(gv2)` |
| `Convert.ToInt32(Nothing)` | Returns 0 (not exception) | Check for Nothing first if 0 is a valid value |

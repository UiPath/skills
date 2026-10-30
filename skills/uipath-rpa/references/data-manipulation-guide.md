# Data Manipulation Guide

Transform data outside activities: DataTable LINQ, strings, RegEx, DateTime, conversion, collections, and JSON.

**Owned elsewhere:** DataTable activity mechanics (BuildDataTable `TableInfo` trap + inline build, FilterDataTable type-compat, LookupDataTable, GetRowItem) → [xaml/common-pitfalls.md § DataTable Activity Gotchas](xaml/common-pitfalls.md); C# XAML expression binding (`CSharpValue`/`CSharpReference`) → [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md); REFramework configuration access → [reframework-guide.md](reframework-guide.md); activity properties (ForEachRow, AddDataRow, JoinDataTables, SortDataTable, …) → `{PROJECT_DIR}/.local/docs/packages/UiPath.System.Activities/` or `references/activity-docs/UiPath.System.Activities/`; coded-mode `using` directives → [coded/operations-guide.md § Using Statements Rules](coded/operations-guide.md#using-statements-rules).

## Where each snippet goes — read first

A DataTable LINQ chain is one value for one `Assign`. `For Each`, `Dim`, and mutation blocks are not expressions and cannot go in an `Assign`; statement-style VB pasted there is the most common paste error.

| Tag | Placement |
|---|---|
| `[expr]` | One `Assign.Value`, one expression. Examples are VB; translate for C#-expression projects and wrap in `CSharpValue`; VB is not valid C# as-is. |
| `[seq]` | XAML activity sequence: `For Each` / `Add Data Row` / multiple `Assign`s; never one expression. |
| `[coded]` | Coded `.cs` workflow or `Invoke Code` only: statements, `Dim`, mutation loops. |

After more than ~2 chained `[seq]` steps or a real helper, stop hand-assembling XAML and write a coded workflow; see § When to move to coded.

## Required imports & references

For a DataTable LINQ chain, set these in XAML `TextExpression`:

- `NamespacesForImplementation`: `System.Data`, `System.Linq`
- `ReferencesForImplementation`: `System.Data`, `System.Data.Common`, `System.Data.DataSetExtensions`

A scaffolded project (`uip rpa init`) already has all of these — untouched, the LINQ family just works. Add them only when hand-authoring a XAML file or after trimming imports. In coded `.cs`, add `using System.Data;` and `using System.Linq;` ([coded/operations-guide.md § Using Statements Rules](coded/operations-guide.md#using-statements-rules)).

`AsEnumerable` / `CopyToDataTable` / `DataRowComparer` resolve through `System.Data` in modern Windows/cross-platform projects; legacy .NET Framework 4.6.1 requires `System.Data.DataSetExtensions`. Including that reference in both is safe. Without `System.Linq`, `AsEnumerable` fails at **run** (runtime JIT), not at `uip rpa validate` or even `uip rpa build` packaging.

## VB ↔ C# translation key

Examples are VB, the default XAML expression language. Translate `Function(r) r("Col")` to `r => r["Col"]`, `()` to `[]`, and `If(c,a,b)` to `c ? a : b`; coded `.cs` and C#-expression XAML use C# forms.

Coded-only constructs that fail in VB XAML and inside `CSharpValue` because XAML binds expression trees: C# `out` parameters (`int.TryParse(s, out int n)`; not a workflow/XAML `OutArgument`), `?.`, `?[]`, `??`, collection initializers (`new Dictionary<…>{ … }`), and statement-body lambdas/IIFEs. Failures include CS8198 (`out`), CS8072 (`?.`), CS8074 (initializer), and CS0834 (statement-body lambdas/IIFEs). In C#-expression XAML only, optional-argument overloads also fail (`CS0854`).

XAML-safe alternatives:

- Parse: pre-declare `n` and use `If(Integer.TryParse(s, n), n, 0)`; C#-expression XAML has no `out`-free `TryParse`, so parse in a coded helper/workflow or accept the VB form—`out` cannot appear in `CSharpValue`.
- Null-safe: `If(x Is Nothing, "", x.ToString())` in VB, not `?.`/`??`.
- Build dictionaries across `Assign`s / `Invoke Method`, not with an inline initializer.

See [csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md).

## Choose the approach

| Task | Use | Notes |
|---|---|---|
| Simple single-condition filter | **Filter Data Table** activity | GUI, no expression. |
| Expression filter without new columns | `dt.Select("[Amount] > 1000")` | Returns `DataRow()`; string matching is case-INSENSITIVE by default and SQL-like. |
| Filter/sort/group/join/project | LINQ in one `Assign` | Most flexible; ~2× faster than Join Data Tables on large sets. |
| Heavy multi-step transforms, unit-tested logic, safe accessors | coded `.cs` | C# LINQ inline; see § When to move to coded. |
| Multi-step transform in C#-expression XAML | Coded Source File helper, `Invoke Code`, or coded workflow via `Invoke Workflow File` | Expression trees forbid statements, `out var`, and optional-argument overloads (`CS0854`). |
| Key-value config/counters | `Dictionary(Of K,V)` | |
| Tabular data | `DataTable` | Typed columns; LINQ via `.AsEnumerable()`. |

### When to move to coded

In VB projects, default to native `Assign` expressions for LINQ and JSON, not `Invoke Code`: `Invoke Code` introduces separately resolved assembly/import/version pitfalls, can drift from project references, and is not checked by `validate`; native expressions reuse project imports and round-trip in the designer. The `[expr]` snippets here are native.

When a transform exceeds expressions—more than 2 statement steps, a reusable safe accessor/helper, row mutation in a loop, real try/catch around parsing, or an unreadable one-liner—move to a coded `.cs` workflow ([coded/operations-guide.md](coded/operations-guide.md)), still not `Invoke Code`. Coded workflows provide `?.`, `out var`, multi-statement logic, and unit tests.

### Exception: C#-expression XAML workflows — the transform leaves the expression

C# XAML expressions are expression trees: no statements, `out var` (`TryParse`), or optional-argument overloads (`CS0854`) ([xaml/common-pitfalls.md § C# XAML Expressions Compile as Expression Trees](xaml/common-pitfalls.md)). Escalate to:

- **Coded Source File helper:** a `public static` method on a plain `.cs` class; call it from the expression (for example, `NameRules.LastWord(name)`). Import its namespace and reference the project's coded assembly ([xaml/common-pitfalls.md § Coded Source File Types in XAML Expressions Need a Namespace Import and Assembly Reference](xaml/common-pitfalls.md#coded-source-file-types-in-xaml-expressions-need-a-namespace-import-and-assembly-reference)).
- **`Invoke Code`:** keep logic inline, pass data through its Arguments collection, and author `Code` as an XML attribute ([xaml/common-pitfalls.md § InvokeCode Code Property](xaml/common-pitfalls.md)).
- **Coded Workflow via `Invoke Workflow File`:** move logic to a `.cs` file with `[Workflow]` + `Execute`; use when it needs coded services or activities.

**Code vs activity chains for row processing:** unless the user states a preference, complex bulk row processing (per-row parse + validate + branch + accumulate) goes to **code** — one of the escalations above — not an activity chain. Nested `If`/`Switch` levels inside a `ForEach` become unreadable, trip the analyzer nesting threshold, and every embedded expression re-fights the expression-tree limits. A simple `ForEach` row with ONE `If` or `Switch` is fine as plain XAML activities — more readable than code for that size.

A bare Coded Source File helper has no entry point and is called from expressions, XAML, or coded code. A Coded Workflow has `[Workflow]` + `Execute` and is invoked as a step via **Invoke Workflow File** (XAML) or `RunWorkflow` / typed `workflows` (coded); see [coded/operations-guide.md](coded/operations-guide.md).

For tabular Excel source/sink, use modern **Use Excel File**, not classic Excel Application Scope; route to Excel activity docs.

## Safe data access first

Excel, scraping, UI, and queue data may contain `DBNull`, blanks, localized numbers, and bad dates. `DBNull` `.ToString()` returns `""`, so bare reads silently propagate blanks and `CDbl`/`Convert.ToDateTime`/`ParseExact` then throw; genuine `Nothing` causes an object-reference error. Direct-cast only typed, known-non-null columns; safely read String/Excel/scraped columns.

**Inline safe reads `[expr]`:**

```vb
' string cell (never throws)
If(IsDBNull(r("Name")), "", r("Name").ToString().Trim())
' number cell -> Decimal, invariant, default 0 on bad/blank/null (n is a Decimal out-var)
If(Decimal.TryParse(If(IsDBNull(r("Amount")), "", r("Amount").ToString()), Globalization.NumberStyles.Any, Globalization.CultureInfo.InvariantCulture, n), n, 0D)
```

**Reusable `[coded]` accessor** (plain Coded Source File, no `CodedWorkflow` base):

```csharp
public static class Row
{
    public static string Str(DataRow r, string c) => r.IsNull(c) ? "" : r[c].ToString().Trim();
    public static decimal Dec(DataRow r, string c) => decimal.TryParse(Str(r, c), NumberStyles.Any, CultureInfo.InvariantCulture, out var d) ? d : 0m;
    public static DateTime? Date(DataRow r, string c, string fmt) => DateTime.TryParseExact(Str(r, c), fmt, CultureInfo.InvariantCulture, DateTimeStyles.None, out var dt) ? dt : (DateTime?)null;
}
```

When invalid business data must stop the item, throw `BusinessRuleException`, not a crash: `If String.IsNullOrWhiteSpace(Row.Str(r,"Id")) Then Throw New BusinessRuleException("Missing Id at row " & i)`.

## DataTable transforms (LINQ)

Call `.AsEnumerable()` first and `.CopyToDataTable()` to produce a DataTable. The casts below assume typed/clean columns; safely wrap String/Excel fields as above.

**MANDATORY: guard every possibly empty `CopyToDataTable()` result.** Otherwise it throws `InvalidOperationException: "The source contains no DataRows"`:

```vb
[If(q.Any(), q.CopyToDataTable(), dt.Clone())]
```

`dt.Clone()` is an empty same-schema table; `dt.Copy()` includes schema and all rows.

### Filter, sort, dedup, paginate — each `[expr]`

```vb
dt.AsEnumerable().Where(Function(r) r("Status").ToString().Trim().Equals("active", StringComparison.OrdinalIgnoreCase))
dt.AsEnumerable().OrderByDescending(Function(r) CDbl(r("Amount"))).CopyToDataTable()
dt.AsEnumerable().Distinct(DataRowComparer.Default).CopyToDataTable()
dt.AsEnumerable().GroupBy(Function(r) r("Id").ToString()).Select(Function(g) g.First()).CopyToDataTable()
dt.AsEnumerable().Skip(10).Take(10).CopyToDataTable()
```

Guard each `CopyToDataTable()` when no match is possible. `dt.Select`/Filter Data Table matching is case-INSENSITIVE by default; use `StringComparison.Ordinal` for case-sensitive matching. C# equivalents use `r => r["Status"]…` and `g => g.First()`.

### Aggregate — each `[expr]`

```vb
dt.AsEnumerable().Sum(Function(r) CDbl(r("Amount")))
dt.AsEnumerable().Count(Function(r) r("Status").ToString().Trim().Equals("active", StringComparison.OrdinalIgnoreCase))
dt.AsEnumerable().Any(Function(r) CDbl(r("Amount")) > 10000)
```

### Compare two DataTables (diff) — each `[expr]`

```vb
dtA.AsEnumerable().Except(dtB.AsEnumerable(), DataRowComparer.Default)
dtA.AsEnumerable().Where(Function(a) Not dtB.AsEnumerable().Any(Function(b) b("Id").ToString() = a("Id").ToString()))
```

The first returns rows in A not in B by whole row; guard and copy it when producing a DataTable. The second returns A rows whose key is absent from B.

### Join two DataTables (VLOOKUP equivalent) — `[expr]`

| Need | Use |
|---|---|
| One value from lookup | **Lookup Data Table** activity |
| Simple combination | **Join Data Tables** activity, slower at scale |
| Combine/filter/shape in one pass | LINQ join |

```vb
(From a In dtA.AsEnumerable()
 Join b In dtB.AsEnumerable() On a("Id").ToString() Equals b("Id").ToString()
 Select New Object(){ a("Id"), a("Name"), b("Region") }).ToList()
```

`Select New Object(){…}` produces `List(Of Object())`; type the receiving variable accordingly, or project to an anonymous type for named fields.

### Remove blank rows — `[expr]`

Remove trailing all-empty Excel/scraping rows because they pollute counts/output and break numeric/date casts:

```vb
dt.AsEnumerable().Where(Function(r) Not r.ItemArray.All(Function(f) f Is DBNull.Value OrElse String.IsNullOrWhiteSpace(f.ToString())))
```

Guard and `CopyToDataTable()` the result.

### Group-by-sum into a NEW DataTable — `[seq]` (or `[coded]`)

This is not an `Assign`: use `For Each` over groups and `Add Data Row`. `grouped` must already contain `Category(String)` and `Total(Decimal)` columns.

```vb
For Each g In dt.AsEnumerable().GroupBy(Function(r) r("Category").ToString())
    grouped.Rows.Add(g.Key, g.Sum(Function(r) CDec(r("Amount"))))
Next
```

In XAML, use `ui:ForEach` with `<ui:ForEach.Body>` over `…GroupBy(...).Select(Function(g) New Object(){g.Key, g.Sum(...)}).ToList()`, with `Add Data Row` into `grouped`.

### Convert DataTable ↔ collections / JSON — `[expr]`

```vb
dt.Columns.Cast(Of DataColumn)().ToDictionary(Function(c) c.ColumnName, Function(c) dt.Rows(0)(c.ColumnName).ToString())
Newtonsoft.Json.JsonConvert.SerializeObject(dt)
Newtonsoft.Json.JsonConvert.DeserializeObject(Of System.Data.DataTable)(jsonString)
```

`CollectionToDataTable` builds a DataTable from `List(Of T)`.

## Iterating rows & common errors

- Use **For Each Row in Data Table** for row work; `CurrentRow` is a `DataRow`. It does not support persistence; inside a Long Running Workflow use coded code ([xaml/long-running-workflow-guide.md](xaml/long-running-workflow-guide.md)).
- **MANDATORY modify-during-iteration rule:** never add/remove rows from the table being iterated; it throws `Collection was modified; enumeration operation may not execute`. Iterate a fresh array (`dt.Select()`), then call `AcceptChanges()` after `[seq]`/`[coded]`:

```vb
For Each r In dt.Select()
    If r("Status").ToString() = "drop" Then r.Delete()
Next
dt.AcceptChanges()
```

- A null cell is `DBNull.Value`, not `Nothing`; use § Safe data access first.
- Add Data Row error `Input array is longer than the number of columns in this table`: a wider source `ItemArray` was passed to a narrower target. Add missing target columns or build an `Object()` matching target count/order.

## Strings & RegEx

**Always** `Trim()` text from UI/web/Excel; check `String.IsNullOrWhiteSpace(s)` before use. In loops use `System.Text.StringBuilder` (`sb.AppendLine(...)`, then `sb.ToString()`), not `&`. Split multiple delimiters with `s.Split(New Char(){";"c, ","c})`; format numbers with `value.ToString("N2", Globalization.CultureInfo.InvariantCulture)` because bare `ToString("N2")` follows machine locale.

Use `System.Text.RegularExpressions.Regex` without a package; each is `[expr]`:

```vb
System.Text.RegularExpressions.Regex.IsMatch(input, "\d{3}-\d{2}-\d{4}")
System.Text.RegularExpressions.Regex.Match(input, "INV-\d+").Value
System.Text.RegularExpressions.Regex.Matches(input, "\$[\d,]+\.?\d{0,2}")
System.Text.RegularExpressions.Regex.Replace(input, "\s+", " ")
```

| Pattern | RegEx |
|---|---|
| Email | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` |
| Phone (US) | `\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}` |
| Date `MM/DD/YYYY` | `\d{2}/\d{2}/\d{4}` |
| Currency (USD) | `\$[\d,]+\.?\d{0,2}` |
| Invoice | `INV-\d{4,10}` |
| ZIP (US) | `\d{5}(-\d{4})?` |
| Decimal | `-?\d+\.?\d*` |

Patterns are unanchored and extract anywhere. For full-string validation, anchor with `^…$`, such as `^\d{5}(-\d{4})?$` for ZIP.

Pattern-string escaping:

- VB (XAML `Assign` or coded VB): `"\d+"`.
- C# coded: `@"\d+"` or `"\\d+"`; bare `"\d+"` is a compile error.
- Any XAML attribute: raw `<` and `>` are illegal XML; use `&lt;`/`&gt;`. Thus named-group XAML uses `(?&lt;amt&gt;…)`; raw `(?<amt>…)` is only for coded `.cs`.

Named-group examples:

```vb
System.Text.RegularExpressions.Regex.Match(input, "(?&lt;amt&gt;\$[\d,.]+)").Groups("amt").Value
```

```csharp
Regex.Match(input, @"(?<amt>\$[\d,.]+)").Groups["amt"].Value
```

Prefer named groups; escape literal dots. For untrusted/long input, set a timeout to prevent catastrophic backtracking: `New Regex(pattern, RegexOptions.None, TimeSpan.FromSeconds(5))`. `Matches` does not support persistence; use code in a Long Running Workflow.

## DateTime & type conversion

Use an explicit format and invariant culture. `MM` is month and `mm` is minutes; `"mm/dd/yyyy"` silently misparses June as January, so only a test catches it.

```vb
DateTime.ParseExact(dateText, "MM/dd/yyyy", System.Globalization.CultureInfo.InvariantCulture)
DateTime.ParseExact(s, New String(){"dd/MM/yyyy", "dd.MM.yyyy"}, System.Globalization.CultureInfo.InvariantCulture, System.Globalization.DateTimeStyles.None)
```

For external dates use `TryParseExact`, as in § Safe data access first.

| Method | Bad input | Use |
|---|---|---|
| `CInt(v)` / `Integer.Parse(v)` | throws | Known-good data |
| `Convert.ToInt32(v)` | throws; `Nothing` → 0 | Known-good; literal `Nothing` needs `CObj(Nothing)` in VB XAML because of overload ambiguity |
| `Integer.TryParse(v, n)` / `Decimal.TryParse` / `DateTime.TryParseExact` | returns `False`, out = default | External/user/Excel input; default choice |

Read a `TryParse` result in the same composite expression: `If(Integer.TryParse(v, n), n, 0)`, with `n` pre-declared. A standalone `Integer.TryParse(v, n)` does not reliably write `n` for a later step because WF may bind `ByRef` to a copy. The same applies to `Dictionary.TryGetValue`.

Specify culture for external numbers/dates: `Double.Parse("1,234.56", System.Globalization.CultureInfo.InvariantCulture)`; bare `CDbl` follows machine locale. `CInt("12.5")` rounds banker's-style to even, not truncates; use `CInt(Math.Floor(...))` to truncate. `CBool("yes")` throws; only `"True"`/`"False"` are accepted. `GenericValue` string comparison is lexical, not numeric; cast first.

## Collections

`[expr]` initialization and reads:

```vb
New List(Of String) From {"a", "b"}
New Dictionary(Of String, Integer) From {{"a", 1}, {"b", 2}}
myDict.ContainsKey("k")
If(myDict.TryGetValue("k", value), value, 0)
```

`value` is a pre-declared out variable. Iterate/mutate under `[seq]`/`[coded]`:

```vb
For Each kvp As KeyValuePair(Of String, Object) In myDict
    ' kvp.Key, kvp.Value
Next
For Each kvp In dict2 : dict1(kvp.Key) = kvp.Value : Next
```

The merge gives precedence to `dict2`. Nested config `[expr]`: `DirectCast(configDict("DatabaseSettings"), Dictionary(Of String, String))("ConnectionString")`.

C# coded permits collection initializers (`{ ["a"]=1 }`), null-conditional (`dict.GetValueOrDefault("k")?.Trim()`), and null-coalescing (`?? ""`).

## JSON (JObject / JArray)

`Newtonsoft.Json` ships with UiPath projects; use `Newtonsoft.Json.Linq`. `Deserialize JSON` / `Deserialize JSON Array` wrap it. `System.Text.Json` is the modern BCL alternative in coded code.

`[expr]` parse/read:

```vb
Newtonsoft.Json.Linq.JObject.Parse(jsonString)
Newtonsoft.Json.Linq.JArray.Parse(jsonArrayString)
jObj("name").ToString()
jObj("address")("city").ToString()
jArr(0)("name").ToString()
jObj("count").Value(Of Integer)()
If(jObj("optional") IsNot Nothing AndAlso jObj("optional")("nested") IsNot Nothing, jObj("optional")("nested").ToString(), Nothing)
jArr.Where(Function(i) i("status").ToString() = "active")
jArr.Select(Function(i) i("name").ToString()).ToList()
```

VB `?.` does not compile in a XAML `Assign` (BC37240); use the guard shown. Build/modify under `[coded]`/`[seq]`, not one `Assign`:

```vb
Dim o = New Newtonsoft.Json.Linq.JObject()
o("name") = "John" : o("age") = 30
o.ToString()
```

For an API response, parse `responseBody`; if `response("error") IsNot Nothing`, throw `BusinessRuleException(...)`; then read `DirectCast(response("data")("items"), Newtonsoft.Json.Linq.JArray)`.

## Coded (`.cs`) note

Coded workflows use C# directly: `r => r["Col"]`, ternary, `out`, `?.`, `??`, collection initializers, verbatim `@"\d+"` regex, and query or method LINQ. Add `using`s `System.Data`, `System.Linq`, `System.Text.RegularExpressions`, and `System.Globalization` per [coded/operations-guide.md § Using Statements Rules](coded/operations-guide.md#using-statements-rules). The XAML C# binding wrapper is separate: [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md).

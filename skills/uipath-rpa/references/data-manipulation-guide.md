# Data Manipulation Guide

Expression/code patterns for transforming data in modern projects: DataTable LINQ, strings, RegEx, DateTime, type conversion, collections, JSON — the layer **not wrapped in activities**.

**Boundary — these own their topics, link don't reinvent:**
- DataTable *activity* mechanics (BuildDataTable `TableInfo` trap + inline build, FilterDataTable type-compat, LookupDataTable, GetRowItem) → [xaml/common-pitfalls.md § DataTable Activity Gotchas](xaml/common-pitfalls.md).
- C# XAML expression *binding* form (`CSharpValue`/`CSharpReference`) → [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md).
- Config.xlsx row/field access in REFramework → [reframework-guide.md](reframework-guide.md).
- Per-activity property surfaces (ForEachRow, AddDataRow, JoinDataTables, SortDataTable, …) → `{PROJECT_DIR}/.local/docs/packages/UiPath.System.Activities/` or `references/activity-docs/UiPath.System.Activities/`.
- Coded-mode `using` directives → [coded/coding-guidelines.md](coded/coding-guidelines.md).

## Where each snippet goes — read first

Each code block below is tagged. **A DataTable LINQ chain is a single value — it belongs in one `Assign`. A `For Each`/`Dim`/object-mutation block is NOT an expression — it cannot go in an `Assign`.** Putting statement-style VB into an `Assign` is the most common paste error.

| Tag | Where it goes |
|-----|---------------|
| `[expr]` | One `Assign.Value` — a single expression. Examples are **VB**; in a C#-expression project translate per the VB↔C# key AND wrap in `CSharpValue` — the VB text is not valid C# as-is. |
| `[seq]` | An XAML **activity sequence** — `For Each` / `Add Data Row` / multiple `Assign`s. Not one expression. |
| `[coded]` | Coded `.cs` workflow (or `Invoke Code`) only — statement blocks, `Dim`, mutation loops. |

When a transform needs more than ~2 chained `[seq]` steps or a real helper, **stop hand-assembling XAML and write a coded workflow** — see § When to move to coded.

## Required imports & references

A DataTable LINQ chain needs ALL of the following in `TextExpression` (XAML). Don't infer — set them:

- **Namespace imports** (`NamespacesForImplementation`): `System.Data`, `System.Linq`
- **Assembly references** (`ReferencesForImplementation`): `System.Data`, `System.Data.Common`, `System.Data.DataSetExtensions`

A scaffolded project (`uip rpa init`) already has all of these — untouched, the LINQ family just works. Add them only when hand-authoring a XAML file or after trimming imports. Coded (`.cs`): `using System.Data;` + `using System.Linq;` ([coded/coding-guidelines.md](coded/coding-guidelines.md)).

Notes:
- `AsEnumerable` / `CopyToDataTable` / `DataRowComparer`: in modern (Windows / cross-platform) they resolve via `System.Data` (the `System.Data.DataSetExtensions` reference is harmless and present by default); **legacy (.NET Framework 4.6.1) requires `System.Data.DataSetExtensions`** — there they live in that assembly, not `System.Data`. Including it in both is the safe default.
- Drop the `System.Linq` import and `AsEnumerable` won't resolve — the break surfaces at **run** (runtime JIT), not at `uip rpa validate` or even `uip rpa build` packaging.

## VB ↔ C# translation key

Examples are **VB** (default expression language; bracket `[expr]` in XAML attributes). VB→C# is mechanical (`Function(r) r("Col")` → `r => r["Col"]`, `()`→`[]` indexing, `If(c,a,b)` → `c ? a : b`); coded (`.cs`) uses the C# form directly and C#-expression XAML uses it too — **except** the coded-only constructs below.

**Coded-only — these do NOT compile in any XAML expression:** the C# `out` **parameter** keyword (e.g. `int.TryParse(s, out int n)` — this is the C# `out` keyword, *not* a workflow/XAML `OutArgument`), null-propagation `?.` / `?[]`, the null-coalescing `??`, and collection initializers (`new Dictionary<…>{ … }`). They work only in coded (`.cs`) workflows. They fail in a VB XAML `Assign`, and — despite being "C#" — also fail **inside `CSharpValue`** in a C#-expression XAML project, because XAML binds expressions as expression trees that forbid them (CS8198 `out`, CS8072 `?.`, CS8074 initializer; statement-body lambdas/IIFEs fail CS0834).

**XAML-safe forms instead** (both VB and C# expression projects):
- Parse: pre-declare `n`, use the composite VB `If(Integer.TryParse(s, n), n, 0)` (C#-expression XAML: there is no `out`-free `TryParse`, so do the parse in a coded workflow or accept the VB form — `out` cannot appear in `CSharpValue`).
- Null-safe: `If(x Is Nothing, "", x.ToString())` (VB) — not `?.`/`??`.
- Build a dictionary across `Assign`s / `Invoke Method`, not an inline initializer.

See [csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md).

## Choose the approach

| Task | Use | Notes |
|------|-----|-------|
| Simple single-condition filter | **Filter Data Table** activity | GUI, no expression |
| Expression filter, no new columns | `dt.Select("[Amount] > 1000")` | returns `DataRow()`; string match is **case-INSENSITIVE** by default; SQL-ish syntax |
| Filter/sort/group/join/project | **LINQ** in one `Assign` | most flexible; ~2× faster than Join Data Tables on large sets |
| Heavy multi-step transforms, unit-tested logic, safe accessors | **coded** (`.cs`) | C# LINQ inline; see § When to move to coded |
| Key-value config / counters | `Dictionary(Of K,V)` | |
| Tabular data | `DataTable` | typed columns; LINQ via `.AsEnumerable()` |

### When to move to coded

**Default in VB projects: native expressions (`Assign`) for LINQ and JSON — not `Invoke Code`.** Inline `Invoke Code` adds assembly/import/version pitfalls (it compiles against a separately-resolved set, drifts from the project's references, and isn't checked by `validate`); native expressions reuse the project's imports and round-trip in the designer. The `[expr]` snippets here are all native.

When a transform genuinely outgrows expressions — >2 statement steps, a reusable safe accessor/helper, mutating rows in a loop, real try/catch around a parse, or an unreadable one-liner — move to a **coded (`.cs`) workflow** ([coded/operations-guide.md](coded/operations-guide.md)), still not `Invoke Code`. Coded gives `?.`, `out var`, multi-statement logic, and unit tests.

**Source file vs workflow — and how to call it:** a bare **Coded Source File** (helper class, no entry point) is callable only from other code. To invoke the logic from a XAML process, make it a **Coded Workflow** (`[Workflow]` + `Execute`) and call it via **Invoke Workflow File** (from XAML) or `RunWorkflow` / the typed `workflows` property (from coded) — see [coded/operations-guide.md](coded/operations-guide.md).

Tabular *source/sink*: modern projects use the **Use Excel File** scope (not classic Excel Application Scope) — route to the Excel activity docs.

## Safe data access first

Production data (Excel, scraping, UI, queues) is full of `DBNull`, blanks, localized numbers, and bad dates. A `DBNull` cell's `.ToString()` returns `""` (no error) — so **bare reads silently propagate blanks**, and `CDbl`/`Convert.ToDateTime`/`ParseExact` then **throw on the resulting blank/garbage**; a genuinely `Nothing` value throws `Object reference not set`. Use direct casts only on **typed, known-non-null** columns (e.g. a Decimal column you built). For String/Excel/scraped columns, read safely.

**Inline safe reads** `[expr]`:
```vb
' string cell (never throws)
If(IsDBNull(r("Name")), "", r("Name").ToString().Trim())
' number cell -> Decimal, invariant, default 0 on bad/blank/null (n is a Decimal out-var)
If(Decimal.TryParse(If(IsDBNull(r("Amount")), "", r("Amount").ToString()), Globalization.NumberStyles.Any, Globalization.CultureInfo.InvariantCulture, n), n, 0D)
```

**Reusable safe accessor** `[coded]` — the maintainable form once more than a couple of fields are involved (Coded Source File, plain `.cs`, no `CodedWorkflow` base):
```csharp
public static class Row
{
    public static string Str(DataRow r, string c) => r.IsNull(c) ? "" : r[c].ToString().Trim();
    public static decimal Dec(DataRow r, string c) =>
        decimal.TryParse(Str(r, c), NumberStyles.Any, CultureInfo.InvariantCulture, out var d) ? d : 0m;
    public static DateTime? Date(DataRow r, string c, string fmt) =>
        DateTime.TryParseExact(Str(r, c), fmt, CultureInfo.InvariantCulture, DateTimeStyles.None, out var dt) ? dt : (DateTime?)null;
}
```
Throw a `BusinessRuleException` (not a crash) when invalid business data must stop the item — e.g. `If String.IsNullOrWhiteSpace(Row.Str(r,"Id")) Then Throw New BusinessRuleException("Missing Id at row " & i)`.

## DataTable transforms (LINQ)

`.AsEnumerable()` first; `.CopyToDataTable()` to produce a DataTable. Casts below assume a **typed/clean** column — for String/Excel data wrap fields per § Safe data access first.

**Rule — guard `CopyToDataTable()` against empty results (MANDATORY).** It throws `InvalidOperationException: "The source contains no DataRows"` on an empty sequence:
```vb
[If(q.Any(), q.CopyToDataTable(), dt.Clone())]
```
`dt.Clone()` = empty table, same schema (`dt.Copy()` = schema + all rows).

### Filter, sort, dedup, paginate — each `[expr]`
```vb
' filter — explicit case-insensitive + trimmed. dt.Select / Filter Data Table string
' match is case-INSENSITIVE by default; use StringComparison.Ordinal for case-sensitive.
dt.AsEnumerable().Where(Function(r) r("Status").ToString().Trim().Equals("active", StringComparison.OrdinalIgnoreCase))

' sort descending
dt.AsEnumerable().OrderByDescending(Function(r) CDbl(r("Amount"))).CopyToDataTable()

' distinct whole rows
dt.AsEnumerable().Distinct(DataRowComparer.Default).CopyToDataTable()

' dedup by a SUBSET of columns — GroupBy + first row per key
dt.AsEnumerable().GroupBy(Function(r) r("Id").ToString()).Select(Function(g) g.First()).CopyToDataTable()

' pagination
dt.AsEnumerable().Skip(10).Take(10).CopyToDataTable()
```
Wrap each `…CopyToDataTable()` in the empty-guard when the filter may match nothing. C#: `r => r["Status"]…`, `g => g.First()`.

### Aggregate — each `[expr]`
```vb
dt.AsEnumerable().Sum(Function(r) CDbl(r("Amount")))
dt.AsEnumerable().Count(Function(r) r("Status").ToString().Trim().Equals("active", StringComparison.OrdinalIgnoreCase))
dt.AsEnumerable().Any(Function(r) CDbl(r("Amount")) > 10000)
```

### Compare two DataTables (diff) — each `[expr]`
```vb
' rows in A not in B — whole-row (guard + CopyToDataTable)
dtA.AsEnumerable().Except(dtB.AsEnumerable(), DataRowComparer.Default)
' rows in A whose key is absent from B
dtA.AsEnumerable().Where(Function(a) Not dtB.AsEnumerable().Any(Function(b) b("Id").ToString() = a("Id").ToString()))
```

### Join two DataTables (VLOOKUP equivalent) — `[expr]`

| Need | Use |
|------|-----|
| Pull one value from a lookup table | **Lookup Data Table** activity |
| Combine columns from both, simple | **Join Data Tables** activity (slower at scale) |
| Combine/filter/shape in one pass | **LINQ join** |

```vb
(From a In dtA.AsEnumerable()
 Join b In dtB.AsEnumerable() On a("Id").ToString() Equals b("Id").ToString()
 Select New Object(){ a("Id"), a("Name"), b("Region") }).ToList()
```
`Select New Object(){…}` makes each element an `Object()`, so the result is **`List(Of Object())`** — type the receiving variable accordingly (or project to an anonymous type for named fields).

### Remove blank rows — `[expr]`
Excel/scraping leave trailing all-empty rows; left in, they pollute counts/output and break downstream numeric/date casts (blank → failed parse). Drop them:
```vb
dt.AsEnumerable().Where(Function(r) Not r.ItemArray.All(Function(f) f Is DBNull.Value OrElse String.IsNullOrWhiteSpace(f.ToString())))
```
(guard + `CopyToDataTable()`).

### Group-by-sum into a NEW DataTable — `[seq]` (or `[coded]`)
Not an `Assign` — a `For Each` over the groups feeding `Add Data Row`:
```vb
' grouped: pre-built DataTable with columns Category(String), Total(Decimal)
For Each g In dt.AsEnumerable().GroupBy(Function(r) r("Category").ToString())
    grouped.Rows.Add(g.Key, g.Sum(Function(r) CDec(r("Amount"))))
Next
```
In XAML: `ui:ForEach` (with `<ui:ForEach.Body>`) over `…GroupBy(...).Select(Function(g) New Object(){g.Key, g.Sum(...)}).ToList()`, body = `Add Data Row` into `grouped`.

### Convert DataTable ↔ collections / JSON — `[expr]`
```vb
' first row -> Dictionary(Of String,String)
dt.Columns.Cast(Of DataColumn)().ToDictionary(Function(c) c.ColumnName, Function(c) dt.Rows(0)(c.ColumnName).ToString())
' DataTable -> JSON
Newtonsoft.Json.JsonConvert.SerializeObject(dt)
' JSON array of objects -> DataTable
Newtonsoft.Json.JsonConvert.DeserializeObject(Of System.Data.DataTable)(jsonString)
```
`CollectionToDataTable` activity builds a DataTable from a `List(Of T)`.

## Iterating rows & common errors

- **For Each Row in Data Table** for row-by-row work; the row var (`CurrentRow`) is a `DataRow`. Does **not** support persistence — inside a Long Running Workflow use a coded path ([xaml/long-running-workflow-guide.md](xaml/long-running-workflow-guide.md)).
- **Modify-during-iteration trap (MANDATORY).** Never add/remove rows on the table you are iterating — throws `Collection was modified; enumeration operation may not execute`. Iterate a fresh array (`dt.Select()` returns one) and `AcceptChanges()` after `[seq]`/`[coded]`:
  ```vb
  For Each r In dt.Select()            ' fresh DataRow array — safe to Delete during the loop
      If r("Status").ToString() = "drop" Then r.Delete()
  Next
  dt.AcceptChanges()
  ```
- **Null cells.** A cell may be `DBNull.Value` (not `Nothing`) — see § Safe data access first.
- **`Input array is longer than the number of columns in this table`** (Add Data Row). Cause: passing a wider source row's `ItemArray` into a narrower table. Fix: add the missing columns first, or build the `Object()` array to match the target's column count/order.

## Strings & RegEx

- Always `Trim()` text from UI/web/Excel; check `String.IsNullOrWhiteSpace(s)` before use.
- Build strings in loops with `System.Text.StringBuilder` (`sb.AppendLine(...)` then `sb.ToString()`) `[seq]`/`[coded]`, not `&`.
- Split on multiple delimiters: `s.Split(New Char(){";"c, ","c})`; format numbers: `value.ToString("N2", Globalization.CultureInfo.InvariantCulture)` (bare `ToString("N2")` follows the machine locale).

RegEx via `System.Text.RegularExpressions.Regex` (no package needed) — each `[expr]`:
```vb
System.Text.RegularExpressions.Regex.IsMatch(input, "\d{3}-\d{2}-\d{4}")
System.Text.RegularExpressions.Regex.Match(input, "INV-\d+").Value
System.Text.RegularExpressions.Regex.Matches(input, "\$[\d,]+\.?\d{0,2}")   ' MatchCollection — iterate
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

Patterns are **unanchored** (extraction — `IsMatch`/`Match` find them anywhere in the string). For full-string *validation*, anchor: `^…$` (e.g. ZIP `^\d{5}(-\d{4})?$`).

**Escaping the pattern string differs by mode:**
- **VB** (XAML `Assign` or coded VB): single-escaped, `"\d+"`.
- **C# coded**: verbatim `@"\d+"` or doubled `"\\d+"` (bare `"\d+"` is a compile error).
- **Any XAML attribute** (VB or C# expression): `<` and `>` are illegal raw XML — escape as `&lt;`/`&gt;`. So a named group is `(?&lt;amt&gt;…)` in XAML; raw `(?<amt>…)` only in coded `.cs`.

Named-group extraction:
```vb
' XAML Assign (note &lt; &gt;):  Groups("amt").Value
System.Text.RegularExpressions.Regex.Match(input, "(?&lt;amt&gt;\$[\d,.]+)").Groups("amt").Value
```
```csharp
// coded C#: raw <, >, verbatim string
Regex.Match(input, @"(?<amt>\$[\d,.]+)").Groups["amt"].Value
```
Prefer named over positional groups; escape literal dots (`\.`); for untrusted/long input set a timeout — `New Regex(pattern, RegexOptions.None, TimeSpan.FromSeconds(5))` — against catastrophic backtracking. The `Matches` activity doesn't support persistence; use the code form in a Long Running Workflow.

## DateTime & type conversion

Parse with an EXPLICIT format + invariant culture (uppercase `MM` = month, lowercase `mm` = minutes) — each `[expr]`:
```vb
DateTime.ParseExact("01/15/2025", "MM/dd/yyyy", System.Globalization.CultureInfo.InvariantCulture)
' wrong case SILENTLY misparses (does not throw): "mm/dd/yyyy" on "06/15/2025" -> January, "06" read as minutes. Only a test catches it.
' multiple accepted formats:
DateTime.ParseExact(s, New String(){"dd/MM/yyyy", "dd.MM.yyyy"}, System.Globalization.CultureInfo.InvariantCulture, System.Globalization.DateTimeStyles.None)
' SAFE (no throw) for external dates — uses TryParseExact, see § Safe data access first
```

**Parse safely** — pick by data trust:

| Method | On bad input | Use when |
|---|---|---|
| `CInt(v)` / `Integer.Parse(v)` | throws | known-good data |
| `Convert.ToInt32(v)` | throws (`Nothing`→0) | known-good; a literal `Nothing` needs `CObj(Nothing)` in VB XAML (overload ambiguity) |
| `Integer.TryParse(v, n)` / `Decimal.TryParse` / `DateTime.TryParseExact` | returns `False`, out=default | **external/user/Excel input (default choice)** |

**TryParse out-var:** read it in the SAME composite expression — `If(Integer.TryParse(v, n), n, 0)`, `n` pre-declared. A standalone `Integer.TryParse(v, n)` in one `Assign` does NOT reliably write `n` back for a later step (WF expression evaluation binds the ByRef arg to a copy). Same for `Dictionary.TryGetValue`.

Specify culture for external numbers/dates: `Double.Parse("1,234.56", System.Globalization.CultureInfo.InvariantCulture)` — bare `CDbl` follows machine locale (US vs German flips `.`/`,`).

Traps: `CInt("12.5")` rounds (banker's, to even) not truncates → `CInt(Math.Floor(...))`; `CBool("yes")` throws (only `"True"`/`"False"`); comparing `GenericValue` strings is lexical, not numeric → cast first.

## Collections

`[expr]` — init & reads:
```vb
New List(Of String) From {"a", "b"}
New Dictionary(Of String, Integer) From {{"a", 1}, {"b", 2}}
myDict.ContainsKey("k")
If(myDict.TryGetValue("k", value), value, 0)        ' value is a pre-declared out-var
```
`[seq]`/`[coded]` — iterate & mutate:
```vb
For Each kvp As KeyValuePair(Of String, Object) In myDict
    ' kvp.Key, kvp.Value
Next
For Each kvp In dict2 : dict1(kvp.Key) = kvp.Value : Next     ' merge (dict2 wins)
```
Nested config `[expr]`: `DirectCast(configDict("DatabaseSettings"), Dictionary(Of String, String))("ConnectionString")`.

C# coded adds collection initializers (`{ ["a"]=1 }`), null-conditional (`dict.GetValueOrDefault("k")?.Trim()`), null-coalescing (`?? ""`).

## JSON (JObject / JArray)

`Newtonsoft.Json` ships with UiPath projects; use `Newtonsoft.Json.Linq`. (The `Deserialize JSON` / `Deserialize JSON Array` activities wrap these; `System.Text.Json` is the modern BCL alternative for coded.)

`[expr]` — parse & read:
```vb
Newtonsoft.Json.Linq.JObject.Parse(jsonString)
Newtonsoft.Json.Linq.JArray.Parse(jsonArrayString)
jObj("name").ToString()                              ' top-level
jObj("address")("city").ToString()                  ' nested
jArr(0)("name").ToString()                           ' array element
jObj("count").Value(Of Integer)()                    ' typed
' safe nested access — VB ?. does NOT compile in a XAML Assign (BC37240); use an If guard:
If(jObj("optional") IsNot Nothing AndAlso jObj("optional")("nested") IsNot Nothing, jObj("optional")("nested").ToString(), Nothing)
jArr.Where(Function(i) i("status").ToString() = "active")           ' LINQ-to-JSON
jArr.Select(Function(i) i("name").ToString()).ToList()
```
`[coded]`/`[seq]` — build/modify (statement block, not one `Assign`):
```vb
Dim o = New Newtonsoft.Json.Linq.JObject()
o("name") = "John" : o("age") = 30
o.ToString()                                          ' or Newtonsoft.Json.JsonConvert.SerializeObject(o)
```
API-response pattern: parse `responseBody`, `If response("error") IsNot Nothing` → `Throw New BusinessRuleException(...)`, then read `DirectCast(response("data")("items"), Newtonsoft.Json.Linq.JArray)`.

## Coded (`.cs`) note

Coded workflows use the C# forms directly (`r => r["Col"]`, ternary, `out`, `?.`, `??`, collection initializers, verbatim `@"\d+"` regex, query or method LINQ). Add the `using`s (`System.Data`, `System.Linq`, `System.Text.RegularExpressions`, `System.Globalization`) per [coded/coding-guidelines.md](coded/coding-guidelines.md). The XAML C# *binding* wrapper is separate — [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md).

# ExtractionResultHandler

**Namespace:** `UiPath.DocumentProcessing.Contracts.Extensions.Navigator.V1`
**Source:** `UiPath.DocumentProcessing.Contracts/Extensions/Navigator/V1/ExtractionResultHandler.cs`
**Kind:** class. Fluent navigator + editor over `ExtractionResult`. Wraps the underlying mutable data points; all changes flow back into the original `ExtractionResult`.

Prefer this over hand-walking `ResultsDocument.Fields`. It adds **type-checked facades per field type** (basic / table / field group), id-or-name lookup, safe inserts / removes, and taxonomy-aware initialization of tables and field groups.

**This is the only supported way to read or mutate tables.** `ResultsTable` / `ResultsTableValue` / `ResultsTableCell` / `ResultsDocument.Tables` are deprecated — do not use them. Tables are `ResultsDataPoint` entries with `FieldType == Table` in `ResultsDocument.Fields`, and the handler navigates them correctly.

**Prefer `FieldName` over `FieldId`** when calling lookup methods. `FieldName` is the taxonomy display name; it throws clearly on ambiguity (a taxonomy bug to fix) or miss. `FieldId` lookups are there for code that needs to survive taxonomy renames.

```
ExtractionResultHandler                (entry point; exposes fields of ResultsDocument)
 └─ extends ComponentCollectionFacade  (GetField / GetFields / GetSimpleField(s) /
                                        GetTable(s) / GetFieldGroup(s) / GetTableValue /
                                        GetFieldGroupValue)

Per-field facades:
  WildcardDataPoint      — unknown type; convert via ToBasicField / ToTable / ToFieldGroup
  BasicDataPoint         — Text / Number / Date / Name / Address / Keyword / Set / Boolean / MonetaryQuantity
  TableDataPoint         — Table; exposes TableValue with rows and cells
  FieldGroupDataPoint    — FieldGroup; collection of FieldGroupValue instances

Per-value facades (ResultsValue wrappers):
  BasicValue             — single extracted value (Text / Number / …)
  TableValue             — whole table body with rows
  TableRow               — one table row
  FieldGroupValue        — one field group instance; itself a ComponentCollectionFacade
```

All facades expose `GetRawDataPoint()` / `GetRawResultsValue()` to drop back to the underlying `ResultsDataPoint` / `ResultsValue` if you need something the facade doesn't surface.

## The shape — recursive model, with a fixed set of supported depths

The underlying tree is a repeating `DataPoint → Value → Components → DataPoint → …` cycle: tables and field groups are the complex `FieldType`s that put child data points into `ResultsValue.Components`. The contract itself does not cap the depth, but **today's taxonomies only produce five shapes**. Treat anything outside this list as unsupported and code defensively only for these:

| Shape (from `ResultsDocument.Fields[i]`) | Meaning |
| --- | --- |
| basic field | `FieldType` ∈ { Text, Number, Date, Name, Address, Keyword, Set, Boolean, MonetaryQuantity }. `Values[k]` is an extracted value; no components. |
| table field → simple columns | `FieldType == Table`. Every column (cell) is a basic field. |
| field-group field → simple sub-fields | `FieldType == FieldGroup`. Every sub-field inside each instance is basic. |
| field-group field → table sub-field → simple columns | One `FieldGroup` containing a `Table`; the table's columns are basic. |
| field-group field → field-group sub-field → simple sub-fields | One `FieldGroup` containing another `FieldGroup`; the inner group's sub-fields are basic. |

**Not supported today** (don't produce, don't expect): table cells that are tables or field groups; three-level field-group nesting; field groups or tables inside nested field groups other than the two shapes listed above.

Practical consequence: you'll see at most **two complex levels** from the root, and the leaves are always basic fields. So `TableRow[col]` always yields a `BasicDataPoint`, and traversal tops out after one nested `GetTable` or `GetFieldGroup` call from a `FieldGroupValue`.

```
ResultsDataPoint                         ← root field, `ResultsDocument.Fields[i]`
 └─ Values : ResultsValue[]              ← one entry per FieldGroup instance or the single Table instance;
                                           for basic fields, each entry is one extracted alternative
      └─ Components : ResultsDataPoint[] ← present only on Table / FieldGroup values
           └─ Values : ResultsValue[]
                └─ Components : ResultsDataPoint[]   ← leaves here are basic (no further Components)
```

`FieldType.Internal` appears only as the `[Header, Body]` scaffolding of `Table` values — skip it when you enumerate user-facing fields. `recursive: true` on `ComponentCollectionFacade.GetFields` walks the whole tree for you with that skip already applied.

## When to use it

- You are writing **validation / review / post-processing** logic that reads and mutates fields by id or name.
- You are writing a **classifier / extractor** that needs to populate table rows or field-group instances from a taxonomy definition.
- You want **safer lookups** than hand-rolled LINQ over `ResultsDocument.Fields` — the navigator throws clearly on missing / ambiguous / wrong-type lookups.

## Entry points

```csharp
using UiPath.DocumentProcessing.Contracts.Extensions.Navigator.V1;

// From an ExtractionResult
ExtractionResultHandler nav = new ExtractionResultHandler(result);
// or
ExtractionResultHandler nav = ExtractionResultHandler.FromExtractionResult(result);

// From an existing ResultsDataPoint / ResultsValue (useful when writing extractors)
TableDataPoint      table      = ExtractionResultHandler.FromTable(dataPoint);
FieldGroupDataPoint fieldGroup = ExtractionResultHandler.FromFieldGroup(dataPoint);
BasicDataPoint      basic      = ExtractionResultHandler.FromBasicDataPoint(dataPoint);
WildcardDataPoint   any        = ExtractionResultHandler.FromDataPoint(dataPoint);

FieldGroupValue fgValue     = ExtractionResultHandler.FromFieldGroupValue(resultsValue);
TableValue      tableValue  = ExtractionResultHandler.FromTableValue(resultsValue);
TableRow        row         = ExtractionResultHandler.FromTableRow(resultsValue);
BasicValue      basicValue  = ExtractionResultHandler.FromBasicValue(resultsValue);
```

The navigator does **not** copy. Every facade holds a reference to the underlying data point / value and mutates the `ExtractionResult` you passed in.

## `ComponentCollectionFacade` — lookup and filtering

Both `ExtractionResultHandler` and `FieldGroupValue` extend `ComponentCollectionFacade`.

```csharp
// Filter / enumerate
WildcardDataPointCollection GetFields(
    Func<ResultsDataPoint, bool> condition = null,
    bool recursive = false);

// Typed bulk accessors
BasicDataPoint[]      GetSimpleFields();
TableDataPoint[]      GetTables();
FieldGroupDataPoint[] GetFieldGroups();

// Single lookup — accepts full/partial FieldId or FieldName, case-insensitive, throws on miss/ambiguous
BasicDataPoint      GetSimpleField(string fieldLookup);
TableDataPoint      GetTable(string tableLookup);
TableValue          GetTableValue(string tableLookup);
FieldGroupDataPoint GetFieldGroup(string fieldLookup);
FieldGroupValue     GetFieldGroupValue(string fieldLookup, int index);
```

`WildcardDataPointCollection` is a `ReadOnlyCollection<WildcardDataPoint>` with sliced views `BasicFields`, `Tables`, `FieldGroups`.

**Lookup semantics** (`FieldLookupBase.GetField`) — pass either a FieldName (recommended) or a FieldId. Two passes:

1. **FieldId pass** — match on the full `FieldId` **OR** on the last dotted segment of `FieldId` (partial id — e.g. `"Total"` matches `"Invoice.Total"`), case-insensitive. Both forms are matched together; ambiguity inside this pass throws `ArgumentException`.
2. **FieldName pass** — only reached if pass 1 found nothing. Matches `FieldName` case-insensitively; ambiguity throws `ArgumentException`.
3. No matches in either pass → `ArgumentException`.

Because pass 1 inspects FieldId first, if your taxonomy has a FieldId ending in the same last segment as some other field's FieldName, the id-segment match wins. In practice, pass the `FieldName` you see in Studio — if it collides, fix the taxonomy.

`recursive: true` walks into `Table` / `FieldGroup` children but **skips `FieldType.Internal`** nodes and header subtrees (so you get user-facing fields only).

## `BasicDataPoint` — basic fields

Wraps `ResultsDataPoint` with `FieldType` ∈ { `Text`, `Number`, `Date`, `Name`, `Address`, `Keyword`, `Set`, `Boolean`, `MonetaryQuantity` }. Constructor **throws** if handed a `Table` or `FieldGroup`.

Exposed (on top of `DataPointFacadeBase`: `FieldId`, `FieldName`, `FieldType`, `IsMissing`, `DataVersion`, `DataSource`, `OperatorConfirmed`, `ValidatorNotes`, `ValidatorNotesInfo`, `GetRawDataPoint()`):

```csharp
BasicValue   Value                 // first value or null
BasicValue[] Values                // all values
BasicValue   GetValue(int index = 0);

// Mutators (all return the wrapped BasicValue or `this`)
BasicValue    AddValue(ResultsValue value);
BasicValue    AddValue(string value, float confidence, float ocrConfidence = 0,
                       ResultsContentReference reference = null,
                       bool operatorConfirmed = false,
                       ResultsDerivedField[] derivedFields = null);
BasicValue    InsertValue(int index, ResultsValue value);
BasicValue    InsertValue(int index, string value, float confidence, …);
BasicValue    UpdateValue(ResultsValue value);                     // index 0
BasicValue    UpdateValue(int index, ResultsValue value);
BasicValue    UpdateValue(int index = 0, string value = null,
                          float? confidence = null, float? ocrConfidence = null,
                          ResultsContentReference reference = null,
                          bool? operatorConfirmed = null,
                          ResultsDerivedField[] derivedFields = null); // only non-null args applied
BasicDataPoint Clear();
BasicDataPoint Remove(int index);
```

`UpdateValue` on a missing data point degrades to `AddValue`, so it's safe to call on either missing or populated fields.

## `TableDataPoint` / `TableValue` / `TableRow`

Constructor of `TableDataPoint` throws on non-`Table` fields.

```csharp
// TableDataPoint
TableValue Value { get; }                 // throws InvalidOperationException if missing
TableValue GetValue();
TableDataPoint Clear();
TableDataPoint InitializeIfMissing(Field taxonomyField);  // builds header+body from taxonomy

// TableValue (wraps the single ResultsValue that holds [Header, Body] components)
TableRow[]     Rows;
TableRow       GetRow(int rowIndex);
TableRow       this[int rowIndex];
BasicDataPoint GetCell(int rowIndex, int columnIndex);
BasicDataPoint GetCell(int rowIndex, string columnLookup);
BasicValue     GetCellValue(int rowIndex, int columnIndex);
BasicValue     GetCellValue(int rowIndex, string columnLookup);
TableValue     RemoveRow(int rowIndex);
TableRow       AddEmptyRow(Field taxonomyField);
TableRow       InsertEmptyRow(int index, Field taxonomyField);

// TableRow
BasicDataPoint[] Cells;
BasicDataPoint   GetCell(int columnIndex);
BasicDataPoint   GetCell(string columnLookup);
BasicDataPoint   this[int columnIndex];
BasicDataPoint   this[string columnLookup];
```

`Field` is `UiPath.DocumentProcessing.Contracts.Taxonomy.Field` — the taxonomy definition. `InitializeIfMissing` / `AddEmptyRow` / `InsertEmptyRow` throw if the `Field.Type` isn't `Table`.

`TableValue` is the **only supported table accessor** — it walks the `ResultsDataPoint` (`FieldType == Table`) → `Values[0].Components[1]` (Body) → `Values[row].Components[col]` (cell) shape that lives in `ResultsDocument.Fields`. Do not reach for `ResultsTable` / `ResultsDocument.Tables`.

## `FieldGroupDataPoint` / `FieldGroupValue`

Constructor throws on non-`FieldGroup` fields.

```csharp
// FieldGroupDataPoint (= list of FieldGroupValue instances)
FieldGroupValue[] Values;
FieldGroupValue   GetValue(int index);
FieldGroupValue   this[int index];
FieldGroupValue   AddEmptyValue(Field taxonomyField);
FieldGroupValue   InsertEmptyValue(int index, Field taxonomyField);
FieldGroupDataPoint Clear();
FieldGroupDataPoint Remove(int index);

// FieldGroupValue (one instance; behaves like a mini "extraction result")
//   extends ComponentCollectionFacade — GetSimpleField / GetTable / GetFieldGroup / …
float  Confidence { get; set; }
float  OcrConfidence { get; set; }
bool   OperatorConfirmed { get; set; }
string ValidatorNotes { get; set; }
string ValidatorNotesInfo { get; set; }
ResultsContentReference Reference { get; }
ResultsDerivedField[]   DerivedFields { get; }
ResultsValue GetRawResultsValue();
```

A `FieldGroupValue` inherits the full `ComponentCollectionFacade` API, so within a single instance you can call `GetSimpleField`, `GetTable`, `GetTableValue`, `GetFieldGroup` on its own components — just like you do on the top-level handler. This is where the recursion described above actually shows up in code.

## Typical code

All examples below pass the **FieldName** (what you see in Studio / the taxonomy) to lookup methods. That is the recommended style.

### Read a simple field value

```csharp
using UiPath.DocumentProcessing.Contracts.Extensions.Navigator.V1;

var nav = new ExtractionResultHandler(result);

BasicValue vendor = nav.GetSimpleField("Vendor").Value;
if (vendor != null)
    Console.WriteLine($"{vendor.Value}  (conf={vendor.Confidence:P0})");
```

### Overwrite or add a value on a basic field

```csharp
var amount = nav.GetSimpleField("Total Amount");
amount.UpdateValue(
    value: "100.00",
    confidence: 1.0f,
    ocrConfidence: 0.99f,
    operatorConfirmed: true);                 // missing → AddValue; present → update in place
```

### Walk a table and fix low-confidence cells

```csharp
TableValue table = nav.GetTableValue("Line Items");

for (int r = 0; r < table.Rows.Length; r++)
{
    BasicDataPoint qtyCell = table.GetCell(r, "Quantity");
    BasicValue qty = qtyCell.Value;
    if (qty != null && qty.Confidence < 0.6f)
    {
        qtyCell.UpdateValue(value: qty.Value, confidence: 0.6f, operatorConfirmed: true);
    }
}
```

### Append a new row to a table, driven by the taxonomy

```csharp
using UiPath.DocumentProcessing.Contracts.Taxonomy;

Field taxonomyTable = /* resolved from DocumentType.Fields by FieldName */;
TableDataPoint lineItems = nav.GetTable("Line Items")
                              .InitializeIfMissing(taxonomyTable);
TableRow newRow = lineItems.Value.AddEmptyRow(taxonomyTable);

newRow["Description"].UpdateValue(value: "Widget",  confidence: 0.95f);
newRow["Quantity"]   .UpdateValue(value: "3",       confidence: 0.95f);
newRow["Unit Price"] .UpdateValue(value: "10.00",   confidence: 0.95f);
```

### Add a field-group instance (e.g. Payees)

```csharp
Field payeesTaxonomy = /* FieldGroup field from taxonomy */;
FieldGroupDataPoint payees = nav.GetFieldGroup("Payees");
FieldGroupValue entry = payees.AddEmptyValue(payeesTaxonomy);

entry.GetSimpleField("Name").UpdateValue(value: "ACME Inc.", confidence: 0.99f);
entry.GetSimpleField("IBAN").UpdateValue(value: "DE…",       confidence: 0.88f);
```

### Navigate a nested field group that itself contains a table

Structure (from the taxonomy): `Payees` is a FieldGroup; each payee has a basic `Name` **and** a nested `Addresses` table with columns `Street`, `City`. Reading it end-to-end:

```csharp
foreach (FieldGroupValue payee in nav.GetFieldGroup("Payees").Values ?? Array.Empty<FieldGroupValue>())
{
    string name = payee.GetSimpleField("Name").Value?.Value;

    // `Addresses` lives inside this payee — call GetTableValue on the payee itself, not on `nav`.
    foreach (TableRow addr in payee.GetTableValue("Addresses").Rows)
    {
        string street = addr["Street"].Value?.Value;
        string city   = addr["City"].Value?.Value;
        Console.WriteLine($"{name}: {street}, {city}");
    }
}
```

The same pattern works for a **field group nested inside a field group** (the fifth supported shape) — e.g. `payee.GetFieldGroup("Contacts").Values[i].GetSimpleField("Email")`. Every `FieldGroupValue` is a fresh scope in which `GetSimpleField` / `GetTable` / `GetFieldGroup` resolve against *that* instance's components. That is as deep as the supported shapes go — the inner field group's sub-fields are always basic.

### Populate a nested table inside a new field-group instance

```csharp
Field payeesTaxonomy    = /* FieldGroup field */;
Field addressesTaxonomy = /* the nested Addresses table field, from payeesTaxonomy.Components */;

FieldGroupValue payee = nav.GetFieldGroup("Payees").AddEmptyValue(payeesTaxonomy);
payee.GetSimpleField("Name").UpdateValue(value: "ACME Inc.", confidence: 0.99f);

TableDataPoint addresses = payee.GetTable("Addresses")
                                .InitializeIfMissing(addressesTaxonomy);
TableRow row = addresses.Value.AddEmptyRow(addressesTaxonomy);
row["Street"].UpdateValue(value: "1 Infinite Loop", confidence: 0.95f);
row["City"]  .UpdateValue(value: "Cupertino",       confidence: 0.95f);
```

### Recursive scan across the whole tree (low-confidence basic values)

```csharp
// Walks all supported shapes and returns every basic value in the result — including those inside
// tables, inside field groups, and inside the one-level-deep nested table or field group.
var suspicious = nav
    .GetFields(f => !f.IsMissing, recursive: true)     // WildcardDataPointCollection
    .BasicFields
    .SelectMany(b => b.Values ?? Array.Empty<BasicValue>())
    .Where(v => v.Confidence < 0.7f)
    .ToList();
```

### Escape hatch — drop to raw when the facade is too narrow

```csharp
ResultsDataPoint raw = nav.GetSimpleField("Vendor").GetRawDataPoint();
raw.DataSource = ResultsDataSource.External;
```

## Don't

- **Don't** touch `ResultsTable`, `ResultsTableValue`, `ResultsTableCell`, `ResultsTableColumnInfo`, or `ResultsDocument.Tables`. They are deprecated. All table work goes through `TableDataPoint` / `TableValue` / `TableRow` on this handler.
- **Don't** construct `BasicDataPoint(dataPoint)` for a `Table` / `FieldGroup` — it throws. Use the specific facade, or start from `WildcardDataPoint` and call `ToBasicField` / `ToTable` / `ToFieldGroup` based on `FieldType`.
- **Don't** call `TableValue.Value` on a table that is `IsMissing` — it throws `InvalidOperationException`. Call `InitializeIfMissing(taxonomyField)` first, or check `IsMissing` on the `TableDataPoint`.
- **Don't** pass ambiguous `FieldName` values. The lookup will throw `ArgumentException` — that's a taxonomy uniqueness violation, fix the taxonomy rather than working around it.
- **Don't** cache facades across `ExtractionResult` mutations that replace `Values` arrays wholesale (e.g. full re-extraction). They wrap the array slot, not the array — after replacement the old facade points at stale data.

## See also

- [ExtractionResult](ExtractionResult.md) — the underlying data the handler navigates.
- [Document](Document.md) — DOM that `ResultsContentReference` values point into.
- `UiPath.DocumentProcessing.Contracts.Taxonomy.Field` — the taxonomy definition passed to `InitializeIfMissing`, `AddEmptyRow`, `AddEmptyValue`.

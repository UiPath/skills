# ExtractionResult

**Namespace:** `UiPath.DocumentProcessing.Contracts.Results`
**Source:** `UiPath.DocumentProcessing.Contracts/Results/ExtractionResult.cs`
**Kind:** `sealed` data class. Mutable. JSON-serializable. Not thread-safe.

`ExtractionResult` is the **typed output of data extraction**. It carries:

- the document type that was classified/confirmed (`ResultsDocument.DocumentTypeId`),
- every extracted field **and table** as `ResultsDataPoint` entries in `ResultsDocument.Fields` (tables have `FieldType == Table`; field groups have `FieldType == FieldGroup`),
- optional business-rule results.

Treat it as the **single source of truth** passed between extract → validate → business-rules → review → export. It is mutated in place at each stage.

> **Prefer `FieldName` over `FieldId` in code you write.** `FieldName` is the stable display name from taxonomy; it is required, non-empty, and unique within a taxonomy in practice. All lookup helpers (`…ByFieldName` on `ExtractionResult`, id-or-name lookup on `ExtractionResultHandler`) will **throw if the name is ambiguous** — that's a taxonomy bug to fix, not an edge case to code around. Use `FieldId` only when your code must survive a taxonomy rename.

> **Ignore `ResultsTable` / `ResultsDocument.Tables` / `ResultsTableValue` / `ResultsTableCell` / `ResultsTableColumnInfo`.** These types are being deprecated. Tables live as `ResultsDataPoint` entries with `FieldType == Table` inside `ResultsDocument.Fields`. For reading, writing, adding, or deleting table rows / cells, use [ExtractionResultHandler](ExtractionResultHandler.md).

## Shape

```
ExtractionResult
 ├─ DocumentId : string
 ├─ ResultsVersion : int                    // bumped on each publish
 ├─ ResultsDocument : ResultsDocument
 │   ├─ Bounds : ResultsDocumentBounds      // PageRange ("1-5"), PageCount
 │   ├─ Language : string
 │   ├─ DocumentGroup / DocumentCategory : string
 │   ├─ DocumentTypeId : string             // taxonomy id
 │   ├─ DocumentTypeName : string
 │   ├─ DocumentTypeDataVersion : int
 │   ├─ DataVersion : int
 │   ├─ DocumentTypeSource : ResultsDataSource
 │   ├─ DocumentTypeField : ResultsValue    // classification reference/value
 │   └─ Fields : ResultsDataPoint[]         // every extracted field: basic, Table, FieldGroup
 ├─ ExtractorPayloads : ExtractorPayload[]  // optional, extractor-specific side-channel data
 └─ BusinessRulesResults : RuleSetResult[]  // populated by Apply Business Rules

// (ResultsDocument also has a deprecated `Tables : ResultsTable[]` — ignore it.)
```

### `ResultsDataPoint` (basic field or complex container)

```
ResultsDataPoint
 ├─ FieldId : string                        // taxonomy id, required
 ├─ FieldName : string                      // display name, required
 ├─ FieldType : FieldType                   // Text | Number | Date | Name | Address | Keyword | Set
 │                                          //   | Boolean | Table | FieldGroup | Internal | MonetaryQuantity
 ├─ IsMissing : bool                        // true when Values is null/empty
 ├─ DataSource : ResultsDataSource          // Automatic | Manual | ManuallyChanged | Defaulted | External
 ├─ Values : ResultsValue[]                 // 0..n values (multi-value fields, nested components)
 ├─ DataVersion : int
 ├─ OperatorConfirmed : bool
 ├─ ValidatorNotes / ValidatorNotesInfo : string
 └─ GetValue() / GetValue(index) / SetValue(ResultsValue)
```

### `ResultsValue` (one extracted value; may be composed)

```
ResultsValue
 ├─ Value : string                          // formatted value (populated for basic values)
 ├─ UnformattedValue : string               // raw text as extracted
 ├─ Reference : ResultsContentReference     // where in Document this came from
 ├─ DerivedFields : ResultsDerivedField[]   // normalized parts (Day/Month/Year, Currency/Value, …)
 ├─ Components : ResultsDataPoint[]         // children: table header+body / field-group sub-fields
 ├─ Confidence : float
 ├─ OcrConfidence : float
 ├─ TextType : TextType
 ├─ OperatorConfirmed : bool
 └─ ValidatorNotes / ValidatorNotesInfo : string
```

### Recursion model and the supported shapes

The underlying tree is a `DataPoint → Value → Components → DataPoint → …` cycle — tables and field groups are the complex `FieldType`s that put child data points into `ResultsValue.Components`. The contract doesn't cap the depth, but **today's taxonomies only produce five shapes** at the top level (`ResultsDocument.Fields[i]`):

1. basic field
2. table field → basic columns
3. field-group field → basic sub-fields
4. field-group field → table sub-field → basic columns
5. field-group field → field-group sub-field → basic sub-fields

Everything else (table cells that are themselves tables or field groups, three-level field-group chains, etc.) is **not supported today**. Two complex levels max, basic fields at the leaves.

`FieldType.Internal` shows up only as the `[Header, Body]` scaffolding of a `Table` value — skip it when enumerating user-facing fields. `FieldTypeExtensions.IsComplexType()` returns `true` only for `Table` / `FieldGroup`.

Don't walk this tree by hand — use [ExtractionResultHandler](ExtractionResultHandler.md). `FieldGroupValue` exposes `GetSimpleField` / `GetTable` / `GetFieldGroup` on its own scope; `TableRow` returns `BasicDataPoint[]` (safe, since cells are always basic); `GetFields(condition, recursive: true)` walks every supported shape while skipping the Internal nodes.

### Tables — how they are represented (ignore `ResultsTable`)

A table is a **`ResultsDataPoint` with `FieldType == Table`** living in `ResultsDocument.Fields`, exactly like any other field. The nested shape is:

```
ResultsDataPoint (FieldType = Table)              ← the table itself
  └─ Values : ResultsValue[]                      ← typically length 1 (the table instance)
       └─ [0].Components : ResultsDataPoint[2]
            ├─ [0] Header  (FieldType = Internal) ← skip; columns-as-values
            └─ [1] Body    (FieldType = Internal)
                 └─ Values : ResultsValue[]       ← one entry per row
                      └─ [row].Components : ResultsDataPoint[]   ← one entry per column (basic field)
                           └─ Values[0].Value                     ← the cell's text
```

Columns are always basic fields (no nested tables / field groups in cells).

You don't walk this structure by hand. Use [ExtractionResultHandler](ExtractionResultHandler.md):

```csharp
var nav = new ExtractionResultHandler(result);
TableValue table = nav.GetTableValue("Line Items");

foreach (TableRow row in table.Rows)
{
    string qty  = row["Quantity"].Value?.Value;
    string desc = row["Description"].Value?.Value;
}
```

The older `ResultsTable` / `ResultsTableValue` / `ResultsTableCell` / `ResultsTableColumnInfo` flat-grid types and the parallel `ResultsDocument.Tables` array are **deprecated — do not reference them in new code**. Existing payloads that still use them are bridged by `ResultsTable.ConvertToDataPointTableFormat()` on the producer side.

## Serialization

```csharp
string Serialize();
string Serialize(SerializationSettings serializationSettings);
static ExtractionResult Deserialize(string jsonString);   // forces DateParseHandling.None
```

Use these rather than calling `JsonConvert` directly — the package registers converters (`ResultsDataPointJsonConverter`, `PrettyBoxConverter`, `FieldValueDetailsJsonConverter`) that the built-in `Serialize` / `Deserialize` wire up for you.

## Read API (built-in, no navigator needed)

> **Prefer the `…ByFieldName` / `…ByTableName` variants in the code you write.** They're easier to read and they throw on ambiguous names, which surfaces taxonomy issues immediately. The `FieldId` variants are there for taxonomy-rename-resilient code.

```csharp
string GetDocumentType();                                  // == ResultsDocument.DocumentTypeId

// Lookup by display name (preferred; throws on ambiguity / missing)
ResultsDataPoint    GetFieldByFieldName(string fieldName);
int                 GetValueCountByFieldName(string fieldName);
SimpleFieldValue[]  GetSimpleFieldValuesByFieldName(string fieldName);
TableFieldValue[][] GetTableFieldValueByTableName(string tableName, int valueIndex = 0);
TableFieldValue     GetTableFieldCellValue(string tableName, string columnName, int rowIndex, int valueIndex = 0);

// Lookup by FieldId (rename-resilient)
ResultsDataPoint    GetField(string fieldId);
int                 GetValueCount(string fieldId);
SimpleFieldValue[]  GetSimpleFieldValues(string fieldId);
TableFieldValue[][] GetTableFieldValue(string fieldId, int valueIndex = 0);
FieldGroupField     GetFieldGroupField(string fieldId);

// Flattened / filtered views over ResultsDocument.Fields
ResultsDataPoint[]        GetFields(Func<ResultsDataPoint,bool> condition = null);
ResultsDataPoint[]        FlattenFields(Func<ResultsDataPoint,bool> condition = null);
IEnumerable<ResultsValue> EnumerateValues(Func<ResultsValue,bool> condition = null);

// Projection to ClassificationResult (uses DocumentTypeField)
ClassificationResult AsClassificationResult();

// DataTable / DataSet export (one DataTable per table field)
DataSet AsDataSet(bool includeConfidence = false);
DataSet AsDataSet(bool includeConfidence = false, bool includeOcrConfidence = false);

// Missing-values check across fields and table cells
bool IsAnyFieldOrTableCellMissing();
```

For **tables**, prefer [ExtractionResultHandler](ExtractionResultHandler.md) over `GetTableFieldValue*`; the handler exposes typed row / cell access and safe mutators, and does not depend on the deprecated `ResultsTable` path. The `GetTableFieldValue*` helpers remain useful when you want a cheap flat projection (no mutation).

## Business rule API

```csharp
bool HasExceptions();
bool HasExceptionsOfType(FieldType fieldType);
bool HasExceptionsOfCriticality(Criticality criticality);
bool HasExceptionsOnField(string fieldId);
```

All four return `false` when `BusinessRulesResults` is null.

## Validator-notes API (mutates)

```csharp
string GetFieldValidatorNotes(string fieldId);
string GetFieldValidatorNotesByFieldName(string fieldName);
void   SetFieldValidatorNotes(string fieldId, string validatorNotes);        // throws if field not found
void   SetFieldValidatorNotesByFieldName(string fieldName, string validatorNotes);

string GetFieldValidatorNotesInfo(string fieldId);
string GetFieldValidatorNotesInfoByFieldName(string fieldName);
void   SetFieldValidatorNotesInfo(string fieldId, string validatorNotesInfo);
void   SetFieldValidatorNotesInfoByFieldName(string fieldName, string validatorNotesInfo);
```

These mutate `ResultsDataPoint.ValidatorNotes` / `ValidatorNotesInfo`. Values on individual `ResultsValue` instances have their own `ValidatorNotes` and must be set directly.

## Typical code

### Read a simple field value (by FieldName)

```csharp
using UiPath.DocumentProcessing.Contracts.Results;

var vendor = result.GetSimpleFieldValuesByFieldName("Vendor").FirstOrDefault();
if (vendor != null)
{
    Console.WriteLine($"{vendor.Value}  conf={vendor.Confidence:P0}");
}
```

### Iterate a table (prefer the handler)

```csharp
using UiPath.DocumentProcessing.Contracts.Extensions.Navigator.V1;

var nav = new ExtractionResultHandler(result);

foreach (TableRow row in nav.GetTableValue("Line Items").Rows)
{
    string qty   = row["Quantity"].Value?.Value;
    string total = row["Line Total"].Value?.Value;
    Console.WriteLine($"{qty} × … = {total}");
}
```

### Flag low-confidence fields before review

```csharp
var lowConfidence = result
    .FlattenFields(f => !f.IsMissing)
    .SelectMany(f => f.Values)
    .Where(v => v.Confidence < 0.7f)
    .ToList();
```

### Confirm all fields programmatically

```csharp
foreach (var dp in result.ResultsDocument.Fields)
{
    dp.OperatorConfirmed = true;
    foreach (var v in dp.Values ?? Array.Empty<ResultsValue>())
        v.OperatorConfirmed = true;
}
```

### Export all tables to a `DataSet` for a reporting sink

```csharp
System.Data.DataSet tables = result.AsDataSet(includeConfidence: true);
```

### Round-trip through JSON (e.g. queue boundary)

```csharp
string json = result.Serialize();
// …send over the wire…
ExtractionResult copy = ExtractionResult.Deserialize(json);
```

## Don't

- **Don't** use `ResultsTable`, `ResultsTableValue`, `ResultsTableCell`, `ResultsTableColumnInfo`, or `ResultsDocument.Tables` in new code. They are deprecated. Treat tables as `ResultsDataPoint` entries with `FieldType == Table` in `ResultsDocument.Fields`, and mutate them through [ExtractionResultHandler](ExtractionResultHandler.md).
- **Don't** index `Values[0]` without checking `IsMissing` — missing data points have an **empty** `Values` array, not `null`, but complex / defaulted fields may still throw on `[0]` when empty.
- **Don't** compare `Confidence` values across different extractors — scales are not unified. Use extractor-specific thresholds or calibrate.
- **Don't** mutate `FieldId` / `FieldName` at runtime to rename a field; downstream lookups (including Action Center) rely on the original taxonomy id.

## See also

- [ExtractionResultHandler](ExtractionResultHandler.md) — fluent, safer navigator over `ExtractionResult` with type-checked facades per field type.
- [ClassificationResult](ClassificationResult.md) — the classification stage's output. `ClassificationResult.AsExtractionResult(taxonomy)` is the inverse of `ExtractionResult.AsClassificationResult()`.
- [Document](Document.md) — the DOM that `ResultsValue.Reference` points into.
- [DocumentTaxonomy](Taxonomy.md) — schema source for the `Field` arguments passed to handler initializers.

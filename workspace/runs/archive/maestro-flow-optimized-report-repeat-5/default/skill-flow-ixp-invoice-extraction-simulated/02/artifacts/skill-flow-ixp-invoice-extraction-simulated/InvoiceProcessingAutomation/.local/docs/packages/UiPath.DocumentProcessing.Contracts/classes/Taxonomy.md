# DocumentTaxonomy

**Namespace:** `UiPath.DocumentProcessing.Contracts.Taxonomy`
**Source:** `UiPath.DocumentProcessing.Contracts/Taxonomy/DocumentTaxonomy.cs`
**Kind:** plain data class. Mutable. JSON-serializable.

`DocumentTaxonomy` is the **schema your extraction results are shaped by**. It lists the document types your automation knows about, each with the fields (basic, table, field-group) to extract, their names / ids / types, optional defaults, business-rule sets, and UI-facing metadata (colors, keys, confidence thresholds, …). Every `FieldId` / `FieldName` you see on a `ResultsDataPoint` in an `ExtractionResult` traces back to a `Field` in this object.

In practice you'll touch `DocumentTaxonomy` in four places:

1. **Load it** — read the taxonomy JSON your project ships (Studio stores it at `Documents/taxonomy.json`; a coded workflow that wants to use it calls `DocumentTaxonomy.Deserialize(json)`).
2. **Resolve a `Field`** — fetch the taxonomy `Field` for a given `DocumentType` / `FieldName` and pass it to the handler when you need to initialize complex fields: `TableDataPoint.InitializeIfMissing(Field)`, `TableValue.AddEmptyRow(Field)`, `FieldGroupDataPoint.AddEmptyValue(Field)`.
3. **Set or read field metadata** — UI / runtime configuration for a field (color, key, per-field confidence thresholds, etc.) is stored as `MetadataEntry { Key, Value }` pairs on `Field.Metadata` (and `DocumentType.Metadata`). Read them to drive UI decisions; set them when you build or adjust a taxonomy at runtime.
4. **Clone / mutate for a downstream phase** — it's legitimate to take the loaded taxonomy, drop fields that aren't needed later, add extras for human review, or restrict `DocumentTypes` based on business rules / classification / extraction output. See the constraint note below before doing this alongside an existing `ExtractionResult`.

## Shape

```
DocumentTaxonomy
 ├─ DataContractVersion : string                  // "1.0" | "1.1" | "1.2" (CurrentSchemaVersion)
 ├─ DocumentTypes       : DocumentType[]          // one entry per document type
 ├─ Groups              : DocumentGroup[]         // hierarchical grouping for UI / filtering
 ├─ SupportedLanguages  : LanguageInfo[]
 └─ ReportAsExceptionSettings : ReportAsExceptionSettings

DocumentType
 ├─ DocumentTypeId            : string            // stable id; appears as ResultsDocument.DocumentTypeId
 ├─ Name                      : string            // display name (ResultsDocument.DocumentTypeName)
 ├─ Group                     : string            // free-form hierarchy level 1 (ResultsDocument.DocumentGroup)
 ├─ Category                  : string            // free-form hierarchy level 2 (ResultsDocument.DocumentCategory)
 ├─ OptionalUniqueIdentifier  : string            // alternative id for downstream systems
 ├─ TypeField                 : TypeField         // { FieldId, FieldName } — placeholder for document-type evidencing
 ├─ Fields                    : Field[]           // the fields to extract
 └─ Metadata                  : MetadataEntry[]

Field  ← used for both root fields and sub-components (table columns, field-group sub-fields)
 ├─ FieldId            : string                   // stable, dotted, often "Parent.Child"
 ├─ FieldName          : string                   // display name; what you want to pass to handler lookups
 ├─ Type               : FieldType                // Text | Number | Date | Name | Address | Keyword | Set
 │                                                //   | Boolean | Table | FieldGroup | Internal | MonetaryQuantity
 ├─ IsMultiValue       : bool                     // basic-field flag; multiple values per field (e.g. "all cities")
 ├─ Components         : Field[]                  // present when Type is Table or FieldGroup
 ├─ SetValues          : string[]                 // options when Type == Set
 ├─ DeriveFieldsFormat : string                   // normalization format for dates / numbers / addresses
 ├─ DefaultValue       : string                   // used when nothing was extracted
 ├─ RuleSet            : RuleSet                  // business rules for this field; Criticality: Must | Should
 ├─ DataSource         : DataSource               // optional; binds the field to an external Connection resource
 └─ Metadata           : MetadataEntry[]           // UI / runtime config: color, key, confidence thresholds, …

DocumentGroup      { Name : string, Categories : string[] }
LanguageInfo       { Name : string, Code   : string }
TypeField          { FieldId : string, FieldName : string }
MetadataEntry      { Key : string, Value : string }
DataSource         { ResourceId : string, ElementFieldId : string }   // ResourceId targets a Connection;
                                                                       // ElementFieldId names the searchable field
RuleSet            { Criticality : Criticality, Rules : Rule[] }
Criticality        enum { Must = 1, Should = 2 }
```

`DataContractVersion` is a string with a small set of legal values exposed as constants on `DocumentTaxonomyVersion`:

```csharp
DocumentTaxonomyVersion.Version10            // "1.0"
DocumentTaxonomyVersion.Version11            // "1.1"
DocumentTaxonomyVersion.Version12            // "1.2"
DocumentTaxonomyVersion.CurrentSchemaVersion // = Version12 today
```

The default constructor sets `DataContractVersion = CurrentSchemaVersion`. Use these constants (instead of inline string literals) when you author or check schema versions.

## The taxonomy mirrors the five supported result shapes

A `Field.Components` collection is only meaningful when `Type` is `Table` or `FieldGroup`. In line with the supported extraction shapes, you will find these `Field` layouts in taxonomies in use today — and no others:

1. basic `Field` (Type ≠ Table, ≠ FieldGroup) — `Components` is null / empty.
2. `Table` — `Components[i]` are basic fields (one per column).
3. `FieldGroup` — `Components[i]` are basic fields (sub-fields of the group).
4. `FieldGroup` → `Table` — one `Components[i]` has `Type == Table`; that table's own `Components` are basic.
5. `FieldGroup` → `FieldGroup` — one `Components[i]` has `Type == FieldGroup`; that inner group's `Components` are basic.

Anything beyond that (tables inside tables, three-level field-group chains, field groups as table cells) is **not supported today** — if you see it, treat it as a taxonomy authoring bug.

See [ExtractionResult](ExtractionResult.md) and [ExtractionResultHandler](ExtractionResultHandler.md) for how these shapes surface in results.

## API

```csharp
// Build / load
public DocumentTaxonomy();                                  // DataContractVersion = CurrentSchemaVersion
static DocumentTaxonomy Deserialize(string jsonString);

// Lookup — returns the document type's root Fields array, or an empty array
// if the document type id is not found. Throws ArgumentException on null/empty input.
Field[] GetFields(string documentTypeId);

// Serialize
string Serialize();
string Serialize(SerializationSettings serializationSettings);
```

For anything beyond the single `GetFields` helper, walk `DocumentTypes` / `Fields` / `Components` with plain LINQ — there are no built-in "find a field by name" helpers on the taxonomy itself.

## Typical code

### Load the taxonomy that ships with your project

```csharp
using UiPath.DocumentProcessing.Contracts.Taxonomy;

string json = File.ReadAllText(Path.Combine(projectRoot, "Documents", "taxonomy.json"));
DocumentTaxonomy taxonomy = DocumentTaxonomy.Deserialize(json);
```

### Resolve a taxonomy field by name (for handler calls)

```csharp
static Field FindField(DocumentTaxonomy taxonomy, string documentTypeId, string fieldName)
{
    var fields = taxonomy.GetFields(documentTypeId);
    return fields.FirstOrDefault(f => f.FieldName.Equals(fieldName, StringComparison.OrdinalIgnoreCase))
        ?? throw new InvalidOperationException(
               $"Field '{fieldName}' not found on document type '{documentTypeId}'.");
}
```

### Add a row to a table using the matching taxonomy field

```csharp
using UiPath.DocumentProcessing.Contracts.Extensions.Navigator.V1;

var nav = new ExtractionResultHandler(result);
Field lineItemsFieldDef = FindField(taxonomy, result.ResultsDocument.DocumentTypeId, "Line Items");

TableDataPoint lineItems = nav.GetTable("Line Items")
                              .InitializeIfMissing(lineItemsFieldDef);
TableRow row = lineItems.Value.AddEmptyRow(lineItemsFieldDef);

row["Description"].UpdateValue(value: "Widget",  confidence: 0.95f);
row["Quantity"]   .UpdateValue(value: "3",       confidence: 0.95f);
row["Unit Price"] .UpdateValue(value: "10.00",   confidence: 0.95f);
```

### Populate a nested table inside a new field-group instance

```csharp
Field payeesFieldDef    = FindField(taxonomy, documentTypeId, "Payees");
Field addressesFieldDef = payeesFieldDef.Components
    .First(c => c.FieldName.Equals("Addresses", StringComparison.OrdinalIgnoreCase));

FieldGroupValue payee = nav.GetFieldGroup("Payees").AddEmptyValue(payeesFieldDef);
payee.GetSimpleField("Name").UpdateValue(value: "ACME Inc.", confidence: 0.99f);

TableDataPoint addresses = payee.GetTable("Addresses")
                                .InitializeIfMissing(addressesFieldDef);
TableRow addr = addresses.Value.AddEmptyRow(addressesFieldDef);
addr["Street"].UpdateValue(value: "1 Infinite Loop", confidence: 0.95f);
addr["City"]  .UpdateValue(value: "Cupertino",       confidence: 0.95f);
```

### List every field defined for a document type (including components)

```csharp
static IEnumerable<Field> AllFields(Field field)
{
    yield return field;
    foreach (var child in field.Components ?? Array.Empty<Field>())
        foreach (var descendant in AllFields(child))
            yield return descendant;
}

IEnumerable<Field> everything = taxonomy
    .GetFields(documentTypeId)
    .SelectMany(AllFields);
```

### Enforce "every `Must` field is confirmed" before export

```csharp
using UiPath.DocumentProcessing.Contracts.Taxonomy;

Field[] rootFields = taxonomy.GetFields(result.ResultsDocument.DocumentTypeId);

var unconfirmedMust = rootFields
    .Where(f => f.RuleSet?.Criticality == Criticality.Must)
    .Select(f => nav.GetFields(dp => dp.FieldName == f.FieldName).BasicFields.FirstOrDefault())
    .Where(bf => bf != null && !bf.OperatorConfirmed)
    .ToList();

if (unconfirmedMust.Any())
    throw new InvalidOperationException("Export blocked: mandatory fields not confirmed.");
```

## Constraints when you mutate a taxonomy at runtime

Runtime cloning / filtering of a taxonomy is fine — it's a common pattern (e.g. trim fields before a lightweight downstream phase, add review-only fields, restrict `DocumentTypes` based on classification / business rules). Two constraints:

- **If an `ExtractionResult` is still going to be validated or mutated against the taxonomy, keep the two in sync.** Human validation UIs, the handler's `InitializeIfMissing` / `AddEmptyRow` / `AddEmptyValue`, and per-field rule evaluation all resolve through the taxonomy — removing a `Field` from the taxonomy while that field still has values in the result (or vice versa) will produce `ArgumentException`s on handler lookups and confused validation UI. When in doubt, clone both the taxonomy and the result in the same step.
- **Restrict `DocumentTypes` consciously.** Dropping a `DocumentType` from the taxonomy before a stage will cause that stage to ignore documents classified as that type. This is often what you want; make it an explicit decision rather than a side effect.

## Don't

- **Don't** rely on `GetFields(docTypeId)` to search by name or traverse components — it only returns the root-level `Fields` array for the matching document type. Walk `Components` yourself (see the `AllFields` helper above) when you need anything nested.
- **Don't** hand-author `FieldId` in C#. Ids are generated by Taxonomy Manager in Studio; if you need a new field, add it there and re-export. Matching by `FieldName` is usually what you want anyway.
- **Don't** assume every `Field` has a `RuleSet`, `DefaultValue`, or `Metadata` — all of these are optional and may be null.
- **Don't** expect `DocumentTypeId` to travel with the document through OCR or digitization — it's populated on `ResultsDocument` after classification. Use it as the key into `GetFields` after you have classified.

## See also

- [ExtractionResult](ExtractionResult.md) — the extraction output whose `FieldId` / `FieldName` / `FieldType` / `Components` map one-to-one onto the taxonomy `Field` tree.
- [ExtractionResultHandler](ExtractionResultHandler.md) — the navigator whose `InitializeIfMissing`, `AddEmptyRow`, `AddEmptyValue` take a taxonomy `Field` as the source of truth for structure.

# UiPath Document Processing Contracts

`UiPath.DocumentProcessing.Contracts` — data contracts for UiPath Document Understanding. Target framework: `net6.0`.

Data contracts plus abstract activity base classes for authoring custom Document Understanding activities — no concrete runtime activities, no designer UI. Coding agents typically only consume the data contracts listed below; the activity base classes (under `Classification/`, `DataExtraction/`, `Training/`, `Apps/` namespaces) are for activity authors building new packages.

## What's inside

| Namespace | Purpose |
| --- | --- |
| `UiPath.DocumentProcessing.Contracts.Dom` | `Document` object model produced by digitization (pages, sections, word groups, words, metadata, markups, boxes). |
| `UiPath.DocumentProcessing.Contracts.Results` | `ExtractionResult` and the results model: `ResultsDocument`, `ResultsDataPoint`, `ResultsValue`, `ResultsContentReference`, `ResultsDerivedField`, `SimpleFieldValue`, `TableFieldValue`, `ClassificationResult`, `DocumentSplittingResult`. |
| `UiPath.DocumentProcessing.Contracts.Extensions.Navigator.V1` | Fluent navigator API over `ExtractionResult`. Entry point: `ExtractionResultHandler`. |
| `UiPath.DocumentProcessing.Contracts.Taxonomy` | `DocumentTaxonomy`, `DocumentType`, `Field`, `FieldType`, `Criticality`, `RuleSet`. |
| `UiPath.DocumentProcessing.Contracts.BusinessRules` | `RuleSetResult`, `RuleResult`, `FieldValue`, `FieldValueResult`. |
| `UiPath.DocumentProcessing.Contracts.Actions` | Classification / Validation Action payloads used with Action Center. |

## Class reference (for coding agents)

Start here. These five entry points cover the code you will realistically write against this package.

- [Document](classes/Document.md) — the Document Object Model (DOM). Output of digitization. Input of classification and extraction.
- [ClassificationResult](classes/ClassificationResult.md) — typed output of classification. Use `AsExtractionResult(taxonomy)` to seed the `ExtractionResult` for the downstream extractor.
- [ExtractionResult](classes/ExtractionResult.md) — structured extraction output. Input of validation, business rules, export.
- [ExtractionResultHandler](classes/ExtractionResultHandler.md) — fluent navigator and editor over `ExtractionResult`. Prefer this over hand-walking `ResultsDocument.Fields`.
- [DocumentTaxonomy](classes/Taxonomy.md) — the schema that defines document types and fields. Load it to resolve the `Field` you pass to `InitializeIfMissing` / `AddEmptyRow` / `AddEmptyValue` on the handler.

## End-to-end pipeline (where each contract shows up)

```
 Raw file (PDF/image/email/text)
        │
        ▼
 Digitize  ──────────────►  Document          (Dom/Document.cs)
        │
        ▼
 Classify ──────────────►  ClassificationResult
        │
        ▼
 Extract  ──────────────►  ExtractionResult   (Results/ExtractionResult.cs)
        │                     │
        │                     ├─► ResultsDocument ─► ResultsDataPoint (basic + Table + FieldGroup)
        │                     └─► BusinessRulesResults
        ▼
 Validate / Review  ────►  ExtractionResult (mutated via ExtractionResultHandler)
        │
        ▼
 Export / Persist
```

Every stage after digitization carries the original `Document` alongside its stage output. Many APIs expect both (`Document document, ExtractionResult result`).

## Serialization

- `Document` and `ExtractionResult` both have `Serialize()` / `Deserialize(string json)` — round-trippable JSON. Use these instead of hand-rolling `JsonConvert`; there is a custom `ResultsDataPointJsonConverter` and `PrettyBoxConverter` on the wire format.
- Both classes support a `SerializationSettings` overload for customization.
- `ExtractionResult.Deserialize` forces `DateParseHandling.None` — do the same if you deserialize manually, otherwise dates in `ResultsValue.Value` (strings) get silently coerced to `DateTime`.

## Common pitfalls

- **Prefer `FieldName` over `FieldId` for readability.** `FieldName` is the stable display name from taxonomy; `FieldId` is the dotted internal id. Both are guaranteed present on every `ResultsDataPoint`. The lookup helpers on `ExtractionResult` (`…ByFieldName`) and on `ExtractionResultHandler` (id-or-name lookup) will **throw if a `FieldName` is ambiguous** — that's a taxonomy bug, not something to code around. Reach for `FieldId` only when you're writing code that must be robust to taxonomy-rename operations.
- **Ignore `ResultsTable` and the `ResultsDocument.Tables` array.** They are being deprecated. Treat tables as `ResultsDataPoint` entries in `ResultsDocument.Fields` with `FieldType == Table`; their rows live under `Values[*].Components[1].Values` (the table "Body"). Always go through `ExtractionResultHandler` for table reads and mutations — see [ExtractionResultHandler](classes/ExtractionResultHandler.md). Do not write new code against `ResultsTable` / `ResultsTableValue` / `ResultsTableCell` / `ResultsTableColumnInfo`.
- **`IsMissing` before `GetValue()`.** `ResultsDataPoint` exposes `IsMissing` and returns `null` from `GetValue()` when missing. Check first.
- **Confidence scales are not unified.** `Confidence` values are extractor-specific. Don't compare confidences across extractors without calibration. Missing / unknown values use `ResultConstants.UnknownConfidence`.
- **Complex vs basic fields.** `FieldType.Table` and `FieldType.FieldGroup` are complex (have nested components). Everything else is basic. `FieldTypeExtensions.IsComplexType()` is the canonical check. `FieldType.Internal` is a structural placeholder (e.g. table headers) — skip it when enumerating user-facing fields.
- **Validator notes live on two levels.** `ResultsDataPoint.ValidatorNotes` and `ResultsValue.ValidatorNotes` are distinct. `ExtractionResult.GetFieldValidatorNotes` reads the data-point level.

## Related packages

This package contains **contracts only**. Concrete activities live in:

- `UiPath.IntelligentOCR.Activities` — classification, extraction, validation, training, digitization activities.
- `UiPath.DocumentUnderstanding.ML.Activities` — ML classifier / extractor implementations.
- `UiPath.OCR.*.Activities` — OCR engines.
- `UiPath.PDF.Activities` — PDF read/split/convert.

When you reference those packages you also reference this one transitively. Use the types here from your coded workflows / code activities; do not duplicate them.

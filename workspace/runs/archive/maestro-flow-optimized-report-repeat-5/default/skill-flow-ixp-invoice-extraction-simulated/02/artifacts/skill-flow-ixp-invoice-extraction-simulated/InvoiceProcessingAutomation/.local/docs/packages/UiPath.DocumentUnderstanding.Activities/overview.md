# UiPath Document Understanding Activities

`UiPath.DocumentUnderstanding.Activities`

Activities for document classification, data extraction, and human-in-the-loop validation using the UiPath Document Understanding framework. Supports pretrained models for standard document types and custom DU project models.

> **Package selection.** Depend on `UiPath.DocumentUnderstanding.Activities` **only**. Do **not** add `UiPath.IntelligentOCR.Activities` (the classic pre-StudioWeb DU package) — it has no agent-facing documentation, and mixing the two packages in a single workflow is unsupported and can cause runtime failures. Agent-generated DU workflows must reference `UiPath.DocumentUnderstanding.Activities` exclusively.

## Common Mistakes — DO NOT write this XAML

The package name and the assembly name are **not** the same. Every observed agent failure on this package has stemmed from one of the rows below. Read this table before writing any DU XAML.

| ❌ Wrong | ✅ Correct |
|---|---|
| Project references the classic `UiPath.IntelligentOCR.Activities` package (alone or alongside `UiPath.DocumentUnderstanding.Activities`) | Depend on `UiPath.DocumentUnderstanding.Activities` only. The classic `UiPath.IntelligentOCR.Activities` package has no agent-facing docs; mixing the two packages in one workflow is unsupported and can cause runtime failures. |
| `assembly=UiPath.DocumentUnderstanding.Activities` | `assembly=UiPath.IntelligentOCR.StudioWeb.Activities` |
| `xmlns:du="clr-namespace:UiPath.DocumentUnderstanding.Activities;..."` | `xmlns:du="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"` |
| `<du:DigitizeDocument />` (no such activity) | Digitization is internal to `ExtractDocumentDataWithDocumentData` and `ClassifyDocument` — there is **no separate Digitize step in this package**. |
| `<du:ExtractDocumentData />` (legacy upgrade stub — `[Browsable(false)]`, hidden from the Studio toolbox; always throws at runtime with the message *"The activity cannot be automatically upgraded: please remove and re-add it to the workflow."* and emits the same text as a validation error at design time. Exists **only** so workflows authored against the old IntelligentOCR package can be opened for migration — **never use it in new workflows**.) | `<du:ExtractDocumentDataWithDocumentData x:TypeArguments="dux:DictionaryData" ProjectId="…" DocType="…" FileInput="[…]" ExtractionResults="[extractionResults]" … />` |
| `<du:CreateDocumentValidationAction />` (invented name) | `<duVal:CreateValidationAction x:TypeArguments="dux:DictionaryData" AutomaticExtractionResults="[…]" ActionTitle="[…]" CreatedValidationAction="[…]" />` |
| `<du:WaitForDocumentValidationActionAndResume />` (invented name) | `<duVal:WaitForValidationAction x:TypeArguments="dux:DictionaryData" CreatedValidationAction="[…]" ValidatedExtractionResults="[…]" />` |
| Activity element with no property bindings | Every DU activity must bind its required inputs **and** its output `OutArgument` to a variable. The required-input set differs by activity (each item below corresponds to a runtime `?? throw new ArgumentException(...)` guard in the activity's `BeginExecute` — omitting any of these produces XAML that validates and packages cleanly but throws *"X not specified"* at runtime): `ProjectId` + `ClassifierId` + `FileInput` + `Endpoint` for `ClassifyDocument` (note `Endpoint` is `[Browsable(false)]` — Studio sets it via dropdown wiring, but agents authoring raw XAML must supply it or the activity throws *"Endpoint not specified"*); `ProjectId` + `FileInput` + **one of** `{DocType, ExtractorName, ModernDocumentTypeId, ModernDocumentTypeName}` for `ExtractDocumentDataWithDocumentData` (if all four document-type selectors are null, throws *"Document Type not specified"*); `AutomaticExtractionResults` for `CreateValidationAction`, `ValidateDocumentDataWithDocumentData`, and `CreateDocumentValidationArtifacts` (the first throws *"Extracted data not specified"* on null; the other two propagate the null downstream). `ActionTitle` is also required by `CreateValidationAction` and `ValidateDocumentDataWithDocumentData` (no explicit guard, but the property table marks it `Required: Yes` and null fails downstream); `CreateDocumentValidationArtifacts` does **not** take `ActionTitle` (writes to a bucket, not Action Center). `CreatedValidationAction` for `WaitForValidationAction` (no explicit guard; null fails downstream). `ContentValidationData` for `RetrieveDocumentValidationArtifacts` (throws *"Content Validation Data not specified"*). **Storage-bucket binding:** `CreateValidationAction`, `ValidateDocumentDataWithDocumentData`, and `CreateDocumentValidationArtifacts` read `OrchestratorFolderName` and `OrchestratorBucketName` at runtime via `BindableStorageBucketActivityExtensions.GetOrchestratorFolderNameValue` / `GetOrchestratorBucketNameValue` (`Bindings/BindableStorageBucketActivityExtensions.cs`). The two properties behave asymmetrically: **`OrchestratorBucketName` is safe to omit** — each activity's constructor assigns `OrchestratorBucketName ?? SWConstants.DefaultBucketName` (`"du_storage_bucket"`), so the runtime always sees a value. **`OrchestratorFolderName` has no such default** — if neither the property nor a bindings override is set, the runtime receives `null`. For the document activities above this null propagates into the action-center / validation-start calls and fails there at runtime; for the classification activities (`CreateClassificationValidationAction`, `CreateClassificationValidationActionAndWait`) the failure is immediate and explicit: `ArgumentException` with message *"Orchestrator folder not specified"*. Either way the XAML validates and packages cleanly. Bind `OrchestratorFolderName` to a known folder path unless the runtime is guaranteed to supply one. See the per-activity docs for the full input set. An empty `<du:X />` element is never valid. |

The friendly UI titles ("Create Validation Task and Wait") do **not** transform mechanically into XAML class names ("CreateValidationActionAndWait"). The next section is the authoritative mapping — use it instead of guessing.

## Activity XAML Cheat Sheet

One row per shipped activity. Look up the XAML element tag here before writing it.

| UI / Doc Title | XAML element tag | xmlns prefix | Generic? |
|---|---|---|---|
| Classify Document | `<du:ClassifyDocument>` | `du` | no |
| Extract Document Data | `<du:ExtractDocumentDataWithDocumentData x:TypeArguments="dux:DictionaryData">` | `du` (activity) + `dux` (type arg) | **yes** — `x:TypeArguments` required |
| Create Classification Validation Task | `<duVal:CreateClassificationValidationAction>` | `duVal` | no |
| Create Classification Validation Task and Wait | `<duVal:CreateClassificationValidationActionAndWait>` | `duVal` | no |
| Wait for Classification Validation Task & Resume | `<duVal:WaitForClassificationValidationAction>` | `duVal` | no |
| Create Validation Task | `<duVal:CreateValidationAction x:TypeArguments="dux:DictionaryData">` | `duVal` (activity) + `dux` (type arg) | **yes** |
| Create Validation Task and Wait | `<duVal:ValidateDocumentDataWithDocumentData x:TypeArguments="dux:DictionaryData">` | `duVal` (activity) + `dux` (type arg) | **yes** |
| Wait for Validation Task and Resume | `<duVal:WaitForValidationAction x:TypeArguments="dux:DictionaryData">` | `duVal` (activity) + `dux` (type arg) | **yes** |
| Create Document Validation Artifacts | `<duArt:CreateDocumentValidationArtifacts x:TypeArguments="dux:DictionaryData">` | `duArt` (activity) + `dux` (type arg) | **yes** |
| Retrieve Document Validation Artifacts | `<duArt:RetrieveDocumentValidationArtifacts>` | `duArt` | no |

**Notes on this table:**
- "Create Validation Task and Wait" maps to `ValidateDocumentDataWithDocumentData`, not `CreateValidationActionAndWait`. This is the most common naming-guess failure on this package.
- "Wait for Validation Task and Resume" maps to `WaitForValidationAction`, not `WaitForValidationActionAndResume`. There is no `AndResume` suffix on the class.
- For all activities marked **yes** under "Generic?", `x:TypeArguments` is mandatory — Studio will not load the XAML without it. `dux:DictionaryData` is the recommended type for agent-generated workflows (no Studio JIT required) and **must be the same across the whole pipeline** — every generic extraction-validation activity downstream of `ExtractDocumentDataWithDocumentData` must use the same `T`.

## Required XAML Namespace Declarations

All Document Understanding activities require these namespace declarations on the workflow root.

**XAML xmlns prefixes:**

```xml
xmlns:du="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:duc="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:dux="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:duVal="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:duArt="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.Artifacts;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:uicore="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"
```

**TextExpression.NamespacesForImplementation** (required for VB expressions referencing DU types):

```xml
<TextExpression.NamespacesForImplementation>
  <scg:List x:TypeArguments="x:String">
    <x:String>UiPath.IntelligentOCR.StudioWeb.Activities</x:String>
    <x:String>UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification</x:String>
    <x:String>UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction</x:String>
    <x:String>UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation</x:String>
  </scg:List>
</TextExpression.NamespacesForImplementation>
```

**TextExpression.ReferencesForImplementation:**

```xml
<TextExpression.ReferencesForImplementation>
  <scg:List x:TypeArguments="AssemblyReference">
    <AssemblyReference>UiPath.IntelligentOCR.StudioWeb.Activities</AssemblyReference>
  </scg:List>
</TextExpression.ReferencesForImplementation>
```

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows
- [Coded Workflow API Reference](coded/) — `du.*` service surface for coded (C#) workflows

## Activities

### Document Understanding

| Activity | Description |
|----------|-------------|
| [Classify Document](activities/ClassifyDocument.md) | Classifies a document according to the configured classifier. |
| [Extract Document Data](activities/ExtractDocumentData.md) | Extracts data from a document using pretrained or custom project extractors. |

### Document Validation — Extraction

| Activity | Description |
|----------|-------------|
| [Create Validation Task and Wait](activities/CreateValidationTaskAndWait.md) | Creates a Document Validation Task in Action Center and waits for completion. |
| [Create Validation Task](activities/CreateValidationTask.md) | Creates a Document Validation Task in Action Center without waiting. |
| [Wait for Validation Task and Resume](activities/WaitForValidationTaskAndResume.md) | Waits for a Document Validation Task to be completed and resumes the workflow. |

### Document Validation — Classification

| Activity | Description |
|----------|-------------|
| [Create Classification Validation Task](activities/CreateClassificationValidationTask.md) | Creates a Classification Validation Task in Action Center without waiting. |
| [Create Classification Validation Task and Wait](activities/CreateClassificationValidationTaskAndWait.md) | Creates a Classification Validation Task in Action Center and waits for completion. |
| [Wait for Classification Validation Task & Resume](activities/WaitForClassificationValidationTaskAndResume.md) | Waits for a Classification Validation Task to be completed and resumes the workflow. |

### Document Validation — Artifacts

| Activity | Description |
|----------|-------------|
| [Create Document Validation Artifacts](activities/CreateDocumentValidationArtifacts.md) | Uploads extraction results to an Orchestrator storage bucket for external validation via UiPath Apps. |
| [Retrieve Document Validation Artifacts](activities/RetrieveDocumentValidationArtifacts.md) | Retrieves validated extraction results from an Orchestrator storage bucket. |

## Type Reference

Key types used across Document Understanding activities. All types are in assembly `UiPath.IntelligentOCR.StudioWeb.Activities`.

### DocumentData (Classification)

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification.DocumentData`
**XAML xmlns:** `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`

Output of ClassifyDocument. Implements `IDocumentData`, which extends `IResource` (but deliberately not `ILocalResource`, so document-data inputs don't render Studio's local-file picker).

| Property | Type | Description |
|----------|------|-------------|
| `DocumentType` | `DocumentType` | The classified document type (see below). |
| `SubDocuments` | `IDocumentData[]` | Array of subdocuments when splitting is enabled. |
| `FileDetails` | `FileDetails` | File path, name, extension, and page range. |
| `DocumentMetadata` | `DocumentMetadata` | OCR text, DOM, language, and results as DataTables. |

### DocumentType

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification.DocumentType`

| Property | Type | Description |
|----------|------|-------------|
| `DisplayName` | `string` | Human-readable label (e.g., `"Invoices"`). |
| `Id` | `string` | Machine identifier (e.g., `"invoices"`). Use this for programmatic comparisons. |
| `Confidence` | `float` | Classification confidence score (0.0 to 1.0). |
| `Name` | `string` | **Obsolete.** Use `Id` instead. |
| `Url` | `string` | Reference URL for the document type definition. |

### IDocumentData\<T\> (Extraction)

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction.IDocumentData<T>`
**XAML xmlns:** `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`

Output of ExtractDocumentData. Extends the classification `IDocumentData` with strongly-typed extraction results.

| Property | Type | Description |
|----------|------|-------------|
| `Data` | `T` | Strongly-typed extraction results (available when `GenerateData=True`). |
| `DocumentType` | `DocumentType` | The document type used for extraction. |
| `SubDocuments` | `IDocumentData[]` | Subdocuments (if splitting occurred upstream). |
| `DocumentMetadata` | `DocumentMetadata` | OCR text, DOM, and `ResultsAsDataTables` for tabular export. |

### ExtendedExtractionResultsForDocumentData

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction.ExtendedExtractionResultsForDocumentData`

Base type argument for `ExtractDocumentDataWithDocumentData<T>`. When `GenerateData=True`, Studio generates a subclass with strongly-typed properties for each extracted field.

| Method | Return Type | Description |
|--------|-------------|-------------|
| `GetProperties()` | `IDocumentDataProperties` | Returns the activity-side metadata bag: the underlying contracts `ExtractionResult`, the loaded `DocumentTaxonomy`, classification results, project / extractor / classifier ids, cross-org runtime settings, and `ActivityMajorVersion`. **This is the runtime path from the activity output to the contracts API** — call it instead of trying to reach into the result through `Data`. Inherited by `DictionaryData` and any Studio-generated `GenerateData=True` subclass. |

#### `IDocumentDataProperties` members

| Member | Type | Description |
|--------|------|-------------|
| `ExtractionResult` | `ExtractionResult` | The contracts `ExtractionResult` that `Data` wraps. Pass this into [`ExtractionResult` helpers](../UiPath.DocumentProcessing.Contracts/classes/ExtractionResult.md) or construct an [`ExtractionResultHandler`](../UiPath.DocumentProcessing.Contracts/classes/ExtractionResultHandler.md) from it. |
| `Taxonomy` | `DocumentTaxonomy` | Loaded taxonomy used for the run. Source of `Field` arguments for `Handler.GetTable(...).InitializeIfMissing(field)`, `TableValue.AddEmptyRow(field)`, and `FieldGroupDataPoint.AddEmptyValue(field)`. |
| `ClassificationResults` | `ClassificationResult[]` | Classification output(s) that produced the document type used for extraction. |
| `ProjectId` | `string` | DU project GUID. |
| `ExtractorId` | `string` | Extractor identifier used for the run. |
| `ClassifierId` | `string` | Classifier identifier used for the run (when classification ran upstream). |
| `ProjectTag` | `string` | Project version tag (e.g. `"Production"`). |
| `ExtractorModelType` | `ResourceType` | Whether the extractor was a built-in / DU project / IXP project model. |
| `ClassifierModelType` | `ResourceType` | Same for the classifier. |
| `OriginalDocumentHash` | `string` | Hash of the source document; useful for deduplication / audit. |
| `IsCrossOrgClassification` / `IsCrossOrgExtraction` | `bool` | True when the activity authenticated against an external DU tenant. |
| `CrossOrgClassificationRuntimeAssetPath` / `…RuntimeTenantUrl` | `string` | Orchestrator credential asset path and tenant URL used at runtime for cross-org classification. |
| `CrossOrgExtractionRuntimeAssetPath` / `…RuntimeTenantUrl` | `string` | Same for extraction. |
| `ActivityMajorVersion` | `int` | Major version of the activity that produced this output. |

Reach the contracts API from a coded workflow:

```csharp
// extractedData is IDocumentData<DictionaryData> from ExtractDocumentDataWithDocumentData
var props = extractedData.Data.GetProperties();
ExtractionResult result = props.ExtractionResult;

// Then use the direct API for basic-field reads...
SimpleFieldValue vendor = result
    .GetSimpleFieldValuesByFieldName("Vendor Name")
    .FirstOrDefault();

// ...or the handler when you need tables / field groups / mutation
var handler = extractedData.Data.Handler;     // shortcut on DictionaryData; equivalent to `new ExtractionResultHandler(props.ExtractionResult)`
foreach (TableRow row in handler.GetTableValue("Line Items").Rows) { /* ... */ }
```

### DictionaryData

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction.DictionaryData`
**XAML xmlns:** `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities` (prefix `dux`)

Extends `ExtendedExtractionResultsForDocumentData`. Provides methods to access extracted fields and tables by name or ID. **Recommended type argument for agent-generated workflows** since it does not require Studio's design-time JIT code generation.

| Method | Return Type | Description |
|--------|-------------|-------------|
| `GetField(string fieldIdOrName)` | `ResultsDataPoint` | Returns a field by ID or name. |
| `GetFieldValue(string fieldIdOrName)` | `ResultsValue` | Returns the first value of a field. |
| `GetFieldValues(string fieldIdOrName)` | `ResultsValue[]` | Returns all values of a field. |
| `GetFields()` | `ResultsDataPoint[]` | Returns all non-table fields. |
| `GetTable(string tableIdOrName)` | `ResultsTable` | Returns a table by ID or name. |
| `GetTables()` | `ResultsTable[]` | Returns all tables. |

See [Data Type Patterns](activities/ExtractDocumentData/data-type-patterns.md) for the full API reference, including setter methods, lookup behavior, and **table access patterns** — the modern `Handler.GetTableValue(...)` path is recommended; the legacy `GetTable(...)` / `ResultsTable` chain is kept for backwards compatibility only.

> **`Handler` is a runtime navigator, not part of the wire format.** It holds references to data points in the underlying `ExtractionResult`. If you JSON-serialize a `DictionaryData` (or its `IDocumentData<T>` wrapper) — e.g. via `WriteTextFile` for persistence — the serialized `Handler` is empty (`{}`); the field references aren't part of the JSON. After deserializing, reconstruct the handler from the underlying extraction result instead: `new ExtractionResultHandler(deserializedDictionaryData.GetProperties().ExtractionResult)`.

### Underlying contracts types

The StudioWeb wrapper types above expose the underlying `UiPath.DocumentProcessing.Contracts.*` data model on specific properties. The contracts types are split across sub-namespaces — `.Results` for `ExtractionResult` / `SimpleFieldValue` / `ResultsDataPoint` / `ResultsValue`, `.Extensions.Navigator.V1` for `ExtractionResultHandler` / `TableRow` / `TableValue`, `.Taxonomy` for `DocumentTaxonomy`, `.Actions` for `ContentValidationData`. A bare `using UiPath.DocumentProcessing.Contracts;` will not resolve any of them — see [coded/coded-api.md § Per-type → namespace lookup](coded/coded-api.md#per-type--namespace-lookup) for the exact `using` line per type. When you need to read or mutate fields, tables, taxonomies, or DOM in code, drop down to the contracts types and read their docs. After Studio extracts package docs into `.local/`, the contracts docs land at:

```
.local/docs/packages/UiPath.DocumentProcessing.Contracts/classes/
```

| Wrapper / property | Contracts type | Contracts doc |
|--------------------|----------------|---------------|
| `DictionaryData.Handler` | `ExtractionResultHandler` | [`classes/ExtractionResultHandler.md`](../UiPath.DocumentProcessing.Contracts/classes/ExtractionResultHandler.md) |
| `DictionaryData.GetField(...)` / `GetFieldValue(...)` returns | `ResultsDataPoint`, `ResultsValue` | [`classes/ExtractionResult.md`](../UiPath.DocumentProcessing.Contracts/classes/ExtractionResult.md) |
| `DocumentData` (output of ClassifyDocument) | conceptually wraps `ClassificationResult` plus the digitized `Document` | [`classes/ClassificationResult.md`](../UiPath.DocumentProcessing.Contracts/classes/ClassificationResult.md), [`classes/Document.md`](../UiPath.DocumentProcessing.Contracts/classes/Document.md) |
| `DocumentMetadata.DocumentObjectModel` | `Document` (the DOM) | [`classes/Document.md`](../UiPath.DocumentProcessing.Contracts/classes/Document.md) |
| `Field` argument to `Handler.GetTable(...).InitializeIfMissing(...)`, `TableValue.AddEmptyRow(...)`, `FieldGroupDataPoint.AddEmptyValue(...)` | `Taxonomy.Field` (loaded via `DocumentTaxonomy`) | [`classes/Taxonomy.md`](../UiPath.DocumentProcessing.Contracts/classes/Taxonomy.md) |

Cross-package relative links above resolve at agent runtime (after `PackageDocsSync` extracts both packages side-by-side under `.local/docs/packages/`). They will not resolve in source-tree review — the contracts docs live in a separate repository.

## Reading Extraction Results

`ExtractDocumentDataWithDocumentData<DictionaryData>` produces an `IDocumentData<DictionaryData>` in its `ExtractionResults` OutArgument. **The extracted fields are not magically projected onto the variable** — you have to read them via the `.Data.GetFieldValue(...)` / `.Data.Handler.GetTableValue(...)` API. An `If` condition that depends on an extracted confidence without first assigning it will gate on the variable's default (typically `0`), not on real extraction output. This is the most common silent-failure pattern in agent-generated DU workflows.

### Field reads in VB expressions (XAML `Assign` / `If`)

```vb
' Read a basic field's first value
Dim total As String = extractionResults.Data.GetFieldValue("total").Value

' Read its confidence (0.0 to 1.0)
Dim conf As Single = extractionResults.Data.GetFieldValue("total").Confidence
```

`GetFieldValue` has two distinct failure modes — handle them separately:

1. **Field id/name not in the taxonomy** → throws `ArgumentException` ("Field {x} not found"). This is what happens if you hardcode a wrong literal. There is **no** `HasField` / `TryGetField` helper — either wrap the call in `Try/Catch ArgumentException`, or (preferred) discover the real ids up-front with `GetFields()` (next snippet) and stop guessing.
2. **Field is in the taxonomy but had no extracted value** (`IsMissing` on the underlying `ResultsDataPoint`) → returns `Nothing`. A null-guard on the return value covers only this case.

```vb
' Defensive read — assumes the field IS in the taxonomy; guards only against IsMissing
Dim fv = extractionResults.Data.GetFieldValue("total")
Dim total As String = If(fv IsNot Nothing, fv.Value, "")
Dim conf As Single  = If(fv IsNot Nothing, fv.Confidence, 0F)

' Full guard — also catches the "field id not in taxonomy" case
Dim total2 As String = ""
Dim conf2  As Single  = 0F
Try
    Dim fv2 = extractionResults.Data.GetFieldValue("total")
    If fv2 IsNot Nothing Then
        total2 = fv2.Value
        conf2  = fv2.Confidence
    End If
Catch ex As ArgumentException
    ' field id/name is not in this project's taxonomy — log and move on
End Try
```

The argument to `GetFieldValue` is **either the field's id (`"total"`) or its name (`"Total Amount"`)** — `DictionaryData` tries id first, then name. Distinguishing the two failure modes when debugging:

- **`ArgumentException` "Field {x} not found"** = the literal you passed matches no id and no name in the project's taxonomy. The field is most likely under a different id (`"total"` vs `"invoice-total"`) or a different name (`"Total Amount"` vs `"Invoice Total"`). Stop hardcoding and discover the real ids (next snippet).
- **Return value is `Nothing`** = the id/name *does* resolve in the taxonomy, but the document had no extracted value for that field (`IsMissing` on the underlying `ResultsDataPoint`). The literal is correct; the document just doesn't contain a value to extract.

### Discovering the field id / name programmatically

When the user describes the field in natural language (e.g. "the total"), don't hardcode a guess — enumerate the extraction's fields and pick the one whose id or display name matches:

```vb
' Returns ResultsDataPoint[] — each has FieldId and FieldName
For Each f In extractionResults.Data.GetFields()
    ' Inspect f.FieldId, f.FieldName, then write a log line so you can verify
    ' which literal to hardcode in the final workflow.
Next
```

### Reading a table

```vb
' Modern Handler API (recommended)
Dim items As TableValue = extractionResults.Data.Handler.GetTableValue("items")
For Each row As TableRow In items.Rows
    Dim desc As String = row.GetCell("description").Value.Value   ' GetCell -> BasicDataPoint -> .Value (BasicValue) -> .Value (string)
    Dim amt  As String = row.GetCell("line-amount").Value.Value
Next
```

`Handler` is a runtime navigator that lives on `DictionaryData.Handler`. The legacy `DictionaryData.GetTable(...)` chain still works but is kept only for backwards compatibility — prefer `Handler.GetTableValue(...)`.

See [Data Type Patterns](activities/ExtractDocumentData/data-type-patterns.md) for the full API: setter methods, confidence aggregation across cells, field-group access, taxonomy-driven `InitializeIfMissing(field)`, `AddEmptyRow(field)`, and `AddEmptyValue(field)` mutation patterns.

## Activity Data Flow

Document Understanding workflows follow a pipeline pattern. The output of each activity feeds into the next. The type argument `<T>` chosen for extraction must be consistent across all downstream extraction validation activities.

```
ClassifyDocument
  Output: DocumentData ──────────────────────────────────┐
                                                          │
  ┌───────────────────────────────────────────────────────┘
  │
  ├──> [Optional] Classification Validation
  │    CreateClassificationValidationAction
  │      Input:  DocumentData
  │      Output: CreatedClassificationValidationAction (token)
  │                │
  │    WaitForClassificationValidationAction
  │      Input:  CreatedClassificationValidationAction
  │      Output: DocumentData (validated)
  │
  ├──> ExtractDocumentDataWithDocumentData<T>
  │      Input:  DocumentData (as FileInput — implements IResource)
  │      Output: IDocumentData<T>
  │                │
  │    ┌───────────┘
  │    │
  │    ├──> [Optional] Extraction Validation (Action Center)
  │    │    CreateValidationAction<T>
  │    │      Input:  IDocumentData<T>
  │    │      Output: CreatedValidationAction<T> (token)
  │    │                │
  │    │    WaitForValidationAction<T>
  │    │      Input:  CreatedValidationAction<T>
  │    │      Output: IDocumentData<T> (validated)
  │    │
  │    └──> [Alternative] Extraction Validation (UiPath Apps)
  │         CreateDocumentValidationArtifacts<T>
  │           Input:  IDocumentData<T>
  │           Output: ContentValidationData
  │                     │
  │         RetrieveDocumentValidationArtifacts
  │           Input:  ContentValidationData
  │           Output: IDocumentData<DictionaryData> (validated)
```

**Key points:**
- `DocumentData` from ClassifyDocument implements `IResource`, so it can be passed directly as `FileInput` to ExtractDocumentData.
- `<T>` is either `DictionaryData` (recommended for agents) or a Studio-generated type. All generic activities in the extraction validation path must use the same `T`.
- Classification validation activities are **not** generic.
- The "and Wait" variants (`CreateClassificationValidationActionAndWait`, `ValidateDocumentDataWithDocumentData`) combine the create + wait steps into a single persistent activity.

## Persistence Requirement for Validation Workflows

Workflows that use any `Wait` or `...AndWait` validation activity suspend execution until a human completes a task in Action Center. For this to work, the UiPath project must have persistence enabled in `project.json`.

**When to enable:** Any workflow containing `WaitForValidationAction`, `WaitForClassificationValidationAction`, `ValidateDocumentDataWithDocumentData`, or `CreateClassificationValidationActionAndWait`.

**How to enable:** Set `"supportsPersistence": true` inside the `"runtimeOptions"` object in `project.json`:

```json
{
  "runtimeOptions": {
    "supportsPersistence": true
  }
}
```

If this setting is missing or `false`, the workflow will fail at runtime when it reaches a persistent activity. **Agents must always set this when generating workflows that include validation activities.**

## Common Patterns

### Classify then Extract

A typical workflow classifies a document first, then extracts data based on the classification result. The `classificationResults.DocumentType.Id` value from ClassifyDocument provides the lowercase identifier needed for ExtractDocumentData's `DocType`.

```xml
<Sequence DisplayName="Classify then Extract">
  <Sequence.Variables>
    <Variable x:TypeArguments="duc:DocumentData" Name="classificationResults" />
    <Variable x:TypeArguments="dux:IDocumentData(dux:ExtendedExtractionResultsForDocumentData)" Name="extractionResults" />
  </Sequence.Variables>

  <!-- Step 1: Classify the document -->
  <du:ClassifyDocument
      DisplayName="Classify Document"
      ProjectId="00000000-0000-0000-0000-000000000000"
      ProjectName="Predefined"
      ProjectTag="Production"
      ProjectVersionName="Production"
      ProjectVersionNumber="0"
      ClassifierId="ml-classification"
      ClassifierName="ML Classification"
      FileInput="[inputFile]"
      TimeoutInSeconds="[3600]"
      ClassificationResults="[classificationResults]">
    <du:ClassifyDocument.GptPromptWithVariables>
      <scg:Dictionary x:TypeArguments="x:String, InArgument(x:String)" />
    </du:ClassifyDocument.GptPromptWithVariables>
  </du:ClassifyDocument>

  <!-- Step 2: Extract using the classification result -->
  <du:ExtractDocumentDataWithDocumentData
      x:TypeArguments="dux:ExtendedExtractionResultsForDocumentData"
      DisplayName="Extract Document Data"
      ActivityMajorVersion="2"
      ProjectId="00000000-0000-0000-0000-000000000000"
      ProjectName="Predefined"
      ProjectTag="Production"
      ProjectVersionName="Production"
      ProjectVersionNumber="0"
      DocType="[classificationResults.DocumentType.Id]"
      FileInput="[classificationResults]"
      TimeoutInSeconds="[3600]"
      ExtractionResults="[extractionResults]">
    <du:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
      <scg:Dictionary x:TypeArguments="x:String, InArgument(x:String)" />
    </du:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
  </du:ExtractDocumentDataWithDocumentData>
</Sequence>
```

**Key points:**
- The `FileInput` for ExtractDocumentData accepts the `classificationResults` directly — `DocumentData` implements `IResource`, passing along the digitized document.
- `classificationResults.DocumentType.Id` provides the lowercase identifier (e.g., `"invoices"`) needed for `DocType`.
- Both activities use the Predefined project GUID `00000000-0000-0000-0000-000000000000`.
- Studio UI display properties (`ProjectName`, `ProjectVersionName`, `ClassifierName`) must be set alongside functional properties for dropdowns to render correctly.
- For the Predefined project, always set `ProjectTag="Production"`, `ProjectVersionNumber="0"`, `ProjectVersionName="Production"`.
- This pattern uses `ExtendedExtractionResultsForDocumentData` as the base type. For agent-generated workflows, prefer the `DictionaryData` variant shown below which provides field access methods.

### Full Pipeline with Human-in-the-Loop Validation (DictionaryData)

A complete Document Understanding pipeline that classifies a document, validates the classification via Action Center, extracts data, and validates the extraction. Uses `DictionaryData` throughout for agent-compatible field access.

This example processes all files from a folder. Adapt by replacing the `ForEach` with your own document source.

```xml
<Sequence DisplayName="Document Understanding Pipeline">
  <Sequence.Variables>
    <Variable x:TypeArguments="x:String" Default="InputDocs\" Name="documentsFolderPath" />
  </Sequence.Variables>

  <uicore:ForEach x:TypeArguments="x:String" DisplayName="Process each document" Values="[directory.GetFiles(documentsFolderPath)]">
    <uicore:ForEach.Body>
      <ActivityAction x:TypeArguments="x:String">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="x:String" Name="currentFile" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Process document">
          <Sequence.Variables>
            <Variable x:TypeArguments="x:String" Name="fileName" />
            <!-- Classification -->
            <Variable x:TypeArguments="duc:DocumentData" Name="classificationResults" />
            <Variable x:TypeArguments="duVal:CreatedClassificationValidationAction" Name="classificationTask" />
            <Variable x:TypeArguments="duc:DocumentData" Name="validatedClassificationResults" />
            <!-- Extraction (DictionaryData) -->
            <Variable x:TypeArguments="dux:IDocumentData(dux:DictionaryData)" Name="extractionResults" />
            <Variable x:TypeArguments="duVal:CreatedValidationAction(dux:DictionaryData)" Name="extractionValidationTask" />
            <Variable x:TypeArguments="dux:IDocumentData(dux:DictionaryData)" Name="validatedExtractionResults" />
          </Sequence.Variables>

          <Assign DisplayName="Get file name">
            <Assign.To>
              <OutArgument x:TypeArguments="x:String">[fileName]</OutArgument>
            </Assign.To>
            <Assign.Value>
              <InArgument x:TypeArguments="x:String">[System.IO.Path.GetFileNameWithoutExtension(currentFile)]</InArgument>
            </Assign.Value>
          </Assign>

          <!-- Step 1: Classify the document -->
          <du:ClassifyDocument
              DisplayName="Classify Document"
              ProjectId="00000000-0000-0000-0000-000000000000"
              ProjectName="Predefined"
              ProjectTag="Production"
              ProjectVersionName="Production"
              ProjectVersionNumber="0"
              ClassifierId="ml-classification"
              ClassifierName="ML Classification"
              FileInput="[LocalResource.FromPath(currentFile)]"
              TimeoutInSeconds="[3600]"
              ClassificationResults="[classificationResults]">
            <du:ClassifyDocument.GptPromptWithVariables>
              <scg:Dictionary x:TypeArguments="x:String, InArgument(x:String)" />
            </du:ClassifyDocument.GptPromptWithVariables>
          </du:ClassifyDocument>

          <!-- Step 2: Create classification validation task -->
          <duVal:CreateClassificationValidationAction
              DisplayName="Create Classification Validation Task"
              AutomaticClassificationResults="[classificationResults]"
              ActionTitle="[fileName + &quot;_classification&quot;]"
              CreatedClassificationValidationAction="[classificationTask]" />

          <!-- Step 3: Wait for human to validate classification -->
          <duVal:WaitForClassificationValidationAction
              DisplayName="Wait for Classification Validation Task &amp; Resume"
              CreatedClassificationValidationAction="[classificationTask]"
              ValidatedClassificationResults="[validatedClassificationResults]" />

          <!-- Step 4: Extract data using validated classification result -->
          <du:ExtractDocumentDataWithDocumentData
              x:TypeArguments="dux:DictionaryData"
              DisplayName="Extract Document Data"
              ActivityMajorVersion="2"
              DocType="{x:Null}"
              GenerateData="False"
              ProjectId="00000000-0000-0000-0000-000000000000"
              ProjectName="Predefined"
              ProjectTag="Production"
              ProjectVersionName="Production"
              ProjectVersionNumber="0"
              ModernDocumentTypeId="use_classification_result"
              FileInput="[validatedClassificationResults]"
              TimeoutInSeconds="[3600]"
              ExtractionResults="[extractionResults]">
            <du:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
              <scg:Dictionary x:TypeArguments="x:String, InArgument(x:String)" />
            </du:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
          </du:ExtractDocumentDataWithDocumentData>

          <!-- Step 5: Create extraction validation task -->
          <duVal:CreateValidationAction
              x:TypeArguments="dux:DictionaryData"
              DisplayName="Create Validation Task"
              AutomaticExtractionResults="[extractionResults]"
              ActionTitle="[fileName + &quot;_extraction&quot;]"
              CreatedValidationAction="[extractionValidationTask]" />

          <!-- Step 6: Wait for human to validate extraction -->
          <duVal:WaitForValidationAction
              x:TypeArguments="dux:DictionaryData"
              DisplayName="Wait for Validation Task and Resume"
              CreatedValidationAction="[extractionValidationTask]"
              ValidatedExtractionResults="[validatedExtractionResults]" />

        </Sequence>
      </ActivityAction>
    </uicore:ForEach.Body>
  </uicore:ForEach>
</Sequence>
```

**Key points:**
- All extraction-related activities use `x:TypeArguments="dux:DictionaryData"` consistently.
- `ModernDocumentTypeId="use_classification_result"` dynamically resolves the extractor from the classification result at runtime. When using this, set `DocType="{x:Null}"`. This is incompatible with `GenerateData=True`.
- `GenerateData="False"` is required for agent-generated workflows. Agents should always set this explicitly. `GenerateData=True` requires Studio's design-time JIT compilation and is incompatible with `use_classification_result`.
- `FileInput="[validatedClassificationResults]"` passes the validated `DocumentData` directly — it implements `IResource`.
- `LocalResource.FromPath(currentFile)` creates an `IResource` from a file path for the initial classification.
- Classification validation and extraction validation tasks are created in Action Center. The workflow suspends at each `Wait` activity until a human completes the task.
- **Persistence requirement:** Any workflow that uses `Wait` or `...AndWait` activities (e.g., `WaitForValidationAction`, `WaitForClassificationValidationAction`, `ValidateDocumentDataWithDocumentData`, `CreateClassificationValidationActionAndWait`) requires `"supportsPersistence": true` in `project.json` under `"runtimeOptions"`. Without this, the workflow will fail at runtime. When generating a workflow that includes any of these activities, always ensure this setting is present in `project.json`.
- For workflows without validation, omit steps 2-3 (classification validation) and/or steps 5-6 (extraction validation). Pass `classificationResults` directly to `FileInput` if skipping classification validation.
- Use UiPath control flow activities (`uicore:ForEach`, `uicore:InterruptibleWhile`) from `UiPath.Core.Activities` (assembly `UiPath.System.Activities`), **not** the .NET equivalents from the default XAML namespace. The UiPath versions require explicit `.Body` wrappers (e.g., `<uicore:ForEach.Body>`) around their content.

### Custom DU Project Pipeline

To use a custom Document Understanding project instead of Predefined, substitute these values in the pipeline above. Studio resolves all names to internal GUIDs at design time — the agent only needs names from the user, not GUIDs.

```xml
<!-- ClassifyDocument: replace Predefined project and classifier -->
<du:ClassifyDocument
    ProjectId="placeholder"
    ProjectName="{Your Project Name}"
    ProjectTag="{your-version-tag}"
    ProjectVersionName="{your-version-tag}"
    ProjectVersionNumber="0"
    ClassifierId="{your-classifier-name}"
    ClassifierName="{your-classifier-name}"
    ... />

<!-- ExtractDocumentDataWithDocumentData: replace Predefined project and extractor -->
<du:ExtractDocumentDataWithDocumentData
    x:TypeArguments="dux:DictionaryData"
    ActivityMajorVersion="2"
    ProjectId="placeholder"
    ProjectName="{Your Project Name}"
    ProjectTag="{your-version-tag}"
    ProjectVersionName="{your-version-tag}"
    ProjectVersionNumber="0"
    DocType="{document-type-name}"
    ExtractorName="{document-type-name}"
    ModernDocumentTypeId="{document-type-name}"
    ModernDocumentTypeName="{document-type-name}"
    ... />
```

**Project name resolution:** `ProjectName` is the driving property. When the user opens the workflow in Studio, it performs the following resolutions at design time:
- `ProjectId` is resolved from `ProjectName` to the actual project GUID
- `ProjectVersionNumber` is resolved from `ProjectTag` to the correct version number
- Classifier and extractor names are resolved to internal identifiers

This works for both DU and IXP projects. The agent can set `ProjectId="placeholder"` and `ProjectVersionNumber="0"` — Studio overwrites both with the correct values.

**Key differences from Predefined:**
- `ProjectName` is the project's display name. Studio uses it to resolve `ProjectId` to the correct GUID at design time.
- `ProjectId` can be a placeholder — Studio resolves it from `ProjectName`. If the user provides the GUID, use it; otherwise `"placeholder"` works.
- `ClassifierId` is the **classifier name** from the custom project. Studio resolves the name to the internal GUID at design time. Set `ClassifierName` to the same value.
- `DocType` is the **document type name** from the project (e.g., `"invoices"`). Studio resolves the name to the correct extractor at design time. When using `ModernDocumentTypeId="use_classification_result"`, set `DocType="{x:Null}"`.
- `ModernDocumentTypeId` is the **document type name** from the project (same value as `DocType`). Studio resolves it to the internal GUID at design time. Alternatively, set to `"use_classification_result"` to dynamically resolve from the classification output (set `DocType="{x:Null}"` when using this).
- `ProjectTag` and `ProjectVersionNumber` reflect the custom project's version. When `ProjectTag` is set, `ProjectVersionNumber` is auto-resolved by Studio — agents can set `ProjectVersionNumber="0"` as a safe placeholder.
- Classification and extraction can use **different projects**. For example, `ClassifyDocument` can use a DU classification project while `ExtractDocumentDataWithDocumentData` uses a separate IXP extraction project. When `ModernDocumentTypeId="use_classification_result"` is set, the extraction project resolves the document type from the classification output at runtime, even across projects.

### Agent Guidance: Custom DU Projects

When a user says "use my DU project called X", the agent already has the project name. Collect the remaining values below. **No GUIDs are needed** — Studio resolves all names to GUIDs at design time.

#### Required Information Checklist

| # | What to ask the user | Maps to XAML property |
|---|----------------------|-----------------------|
| 1 | **Project name** — typically already given in the user's request (e.g., "use my project called X") | `ProjectName` on both `ClassifyDocument` and `ExtractDocumentDataWithDocumentData`. **This is the driving property** — Studio uses it to resolve `ProjectId` to the correct GUID at design time. |
| 2 | **Version tag or number** — e.g., `"Production"`, `"live"` | `ProjectTag` and `ProjectVersionName` (use the tag string), **or** `ProjectVersionNumber` (use the number). When `ProjectTag` is set, Studio auto-resolves `ProjectVersionNumber`. |
| 3 | **Classifier name** — the name of the classifier in the project. Ask the user. | `ClassifierId` and `ClassifierName` on `ClassifyDocument` (set both to the same name). Studio resolves the name to the internal GUID at design time. |
| 4 | **Document type name(s)** — the name of each document type to extract (e.g., `"invoices"`, `"purchase_orders"`). Ask the user. **Skip this for IXP projects** — IXP has no document-type concept; use `"Default"` instead (see below). | `DocType`, `ModernDocumentTypeId`, `ExtractorName`, `ModernDocumentTypeName` on `ExtractDocumentDataWithDocumentData` (set all four to the same name). Studio resolves names to GUIDs at design time. |
| 4a | **IXP projects only:** the user says their project is IXP (or the project has no document types defined). Don't ask for a document-type name. | Set `DocType="Default"`, `ExtractorName="Default"`, `ModernDocumentTypeId="Default"`, `ModernDocumentTypeName="Default"` on `ExtractDocumentDataWithDocumentData`. This is what Studio's designer auto-fills for IXP. Do not leave these properties unset. |

#### What the agent can set without asking

- `ProjectId="placeholder"` — Studio resolves the correct GUID from `ProjectName` at design time. If the user provides a GUID, use it; otherwise a placeholder works.
- `ProjectVersionNumber="0"` — when `ProjectTag` is set, Studio auto-resolves the correct version number. Use `0` as a safe placeholder.
- `GenerateData="False"` — always use this for agent-generated workflows.
- `ActivityMajorVersion="2"` — always set this on `ExtractDocumentDataWithDocumentData`.
- `x:TypeArguments="dux:DictionaryData"` — always use this type argument.
- `TimeoutInSeconds="[3600]"` — standard default.
- `ProjectTag` / `ProjectVersionName` — if the user says "production", use `"Production"`.
- If the user confirms that classification validation is in the pipeline, the agent can use `ModernDocumentTypeId="use_classification_result"` with `DocType="{x:Null}"` instead of asking for document type names (item 4). This dynamically resolves the extractor from the classification result.

#### UI-to-XAML Property Mapping

The table below shows how values from the Document Understanding UI map to XAML attributes on each activity.

**ClassifyDocument:**

| User-provided value | XAML property | Format | Example |
|---------------------|---------------|--------|---------|
| Project name | `ProjectName` | Display string — **Studio resolves `ProjectId` from this** | `"My Invoice Project"` |
| (auto-resolved) | `ProjectId` | GUID or placeholder — Studio resolves from `ProjectName` | `"placeholder"` |
| Version tag | `ProjectTag` | String | `"Production"` |
| Version tag | `ProjectVersionName` | Same as `ProjectTag` | `"Production"` |
| (auto-resolved) | `ProjectVersionNumber` | Integer — Studio resolves from `ProjectTag`. Use `"0"` as placeholder. | `"0"` |
| Classifier name | `ClassifierId` | Classifier name — Studio resolves to GUID | `"My Classifier"` |
| Classifier name | `ClassifierName` | Same name | `"My Classifier"` |

**ExtractDocumentDataWithDocumentData:**

| User-provided value | XAML property | Format | Example |
|---------------------|---------------|--------|---------|
| Project name | `ProjectName` | Display string — **Studio resolves `ProjectId` from this** | `"My Invoice Project"` |
| (auto-resolved) | `ProjectId` | GUID or placeholder — Studio resolves from `ProjectName` | `"placeholder"` |
| Version tag | `ProjectTag` | String | `"Production"` |
| Version tag | `ProjectVersionName` | Same as `ProjectTag` | `"Production"` |
| (auto-resolved) | `ProjectVersionNumber` | Integer — Studio resolves from `ProjectTag`. Use `"0"` as placeholder. | `"0"` |
| Document type name | `DocType` | Lowercase document type name — Studio resolves to extractor. **IXP: always use `"Default"`** (the project has no document types). | `"invoices"` (DU.Apps) · `"Default"` (IXP) |
| Document type name | `ExtractorName` | Same name as `DocType` (also `"Default"` for IXP) | `"invoices"` · `"Default"` |
| Document type name | `ModernDocumentTypeId` | Same name — Studio resolves to GUID (also `"Default"` for IXP) | `"invoices"` · `"Default"` |
| Document type name | `ModernDocumentTypeName` | Same name (also `"Default"` for IXP) | `"invoices"` · `"Default"` |

> **Note:** Studio resolves all names to internal GUIDs at design time when the user opens the workflow. The agent does not need any GUIDs from the user — `ProjectName` drives the resolution of `ProjectId`, and all other names (classifier, document type, extractor) are resolved similarly.

#### Example agent interaction

> **User:** "Create a DU workflow using my project called Invoice Processing"
>
> **Agent should ask:** "I have the project name ('Invoice Processing'). To complete the workflow, I also need:
> 1. The **classifier name** from your project (e.g., 'My Classifier')
> 2. The **document type name(s)** you want to extract (e.g., 'invoices')
> 3. The **version tag** (e.g., 'Production') or version number to use
>
> If classification validation is part of the workflow, I can skip the document type names and use the classification result directly. **If the project is IXP** (no document types defined), I'll skip the document-type question and use `"Default"`. No GUIDs are needed — Studio resolves everything from the names when you open the workflow."

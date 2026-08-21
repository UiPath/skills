# UiPath Document Understanding Activities — Coded Workflow API

`UiPath.DocumentUnderstanding.Activities`

Provides Document Understanding operations to coded workflows: classify a document against a DU.Apps project, extract structured field data, and run the Apps-based validation handoff (upload artifacts to Orchestrator storage, retrieve validated results). The coded surface wraps the same activity engines used by the XAML activities — see the per-activity references under [`../activities/`](../activities/) for the design-time properties they expose.

**Service accessor:** `du` (type `IDocumentUnderstandingService`)

## Required packages

Add both of these as **direct** dependencies in `project.json` — not only the first:

- `"UiPath.DocumentUnderstanding.Activities": "[{Version}]"` — the primary package providing the `du` service.
- `"UiPath.DocumentProcessing.Contracts": "[{Version}]"` — required by every coded workflow that touches `ExtractionResult`, `ExtractionResultHandler`, `SimpleFieldValue`, `ResultsDataPoint`, `ResultsValue`, `DocumentTaxonomy`, `TableRow`, or `TableValue` (i.e. nearly every non-trivial pattern in this doc). The DU package restores the contracts assembly transitively into the NuGet cache, but the transitive restore does **not** put the assembly on the project's compile reference list — only a direct dependency does. Without it, `uip rpa build` fails with `CS0246` on any contracts-side type even though `uip rpa get-errors` passes clean. Install with:
   ```
   uip rpa install-or-update-packages --packages '[{"id":"UiPath.DocumentProcessing.Contracts","version":"<x.y.z>"}]'
   ```

> **Read the contracts package docs too.** `UiPath.DocumentProcessing.Contracts` ships its own per-class documentation — the *authoritative* reference for the types this doc points you at. Whenever you reach `Data.GetProperties().ExtractionResult`, `Data.Handler`, or any other contracts-side type, the per-class doc has the full property/method surface, lookup-semantics rules, mutation contracts, and edge cases that this doc only summarizes:
>
> | Type | Contracts doc (source-tree relative · runtime path) |
> |---|---|
> | `ExtractionResult`, `ResultsDocument`, `ResultsDataPoint`, `ResultsValue`, `SimpleFieldValue` | [`../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResult.md`](../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResult.md) · `.local/docs/packages/UiPath.DocumentProcessing.Contracts/classes/ExtractionResult.md` |
> | `ExtractionResultHandler`, `TableValue`, `TableRow`, `BasicDataPoint`, `FieldGroupValue` | [`../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResultHandler.md`](../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResultHandler.md) · `.local/.../ExtractionResultHandler.md` |
> | `ClassificationResult` (underlying `DocumentData`) | [`../../UiPath.DocumentProcessing.Contracts/classes/ClassificationResult.md`](../../UiPath.DocumentProcessing.Contracts/classes/ClassificationResult.md) |
> | `DocumentTaxonomy`, `Taxonomy`, `Field` | [`../../UiPath.DocumentProcessing.Contracts/classes/Taxonomy.md`](../../UiPath.DocumentProcessing.Contracts/classes/Taxonomy.md) |
> | `Document` (DOM, exposed via `DocumentMetadata.DocumentObjectModel`) | [`../../UiPath.DocumentProcessing.Contracts/classes/Document.md`](../../UiPath.DocumentProcessing.Contracts/classes/Document.md) |
>
> Source-tree relative links resolve only after `PackageDocsSync` extracts both packages side-by-side under `.local/docs/packages/` (the runtime path is the right form for production agents).

> **Platform:** the `du` service is currently available only for Windows projects.

## Namespaces and `using` directives

**Standalone coded workflows (`.cs` files compiled by `uip rpa build` or Studio's project compile) do NOT receive any implicit `using` imports beyond the C# language defaults.** Every type used in your code needs an explicit `using` directive — the Patterns section below shows the right header for each recipe.

The list of namespaces that follow is what XAML expression compilation and InvokeCode activity bodies receive implicitly. In a coded `.cs` file you must still add these as explicit `using` directives:

```
UiPath.DocumentUnderstanding.Activities.Api
UiPath.Platform.ResourceHandling
UiPath.DocumentProcessing.Contracts.Actions
UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction
UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification
```

The `du` accessor is auto-injected by the coded-workflow runtime — just call `du.<Method>(…)` — but the namespace `using` for the types it returns is your responsibility.

### Per-type → namespace lookup

When a type below appears in your code, add the corresponding `using` line. Each row is verified against `UiPath.DocumentProcessing.Contracts` 2.1.0 and the DU/IntelligentOCR.StudioWeb packages.

| Type | Namespace |
|---|---|
| `IDocumentUnderstandingService` | `UiPath.DocumentUnderstanding.Activities.Api` |
| `DocumentData`, `DocumentType` | `UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification` |
| `IDocumentData<T>`, `DictionaryData`, `ExtendedExtractionResultsForDocumentData` | `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction` |
| `IResource`, `ILocalResource`, `LocalResource` | `UiPath.Platform.ResourceHandling` |
| `ContentValidationData` | `UiPath.DocumentProcessing.Contracts.Actions` |
| `ExtractionResult`, `SimpleFieldValue`, `ResultsDocument`, `ResultsDataPoint`, `ResultsValue` | `UiPath.DocumentProcessing.Contracts.Results` |
| `ExtractionResultHandler`, `TableRow`, `TableValue`, `BasicDataPoint` | `UiPath.DocumentProcessing.Contracts.Extensions.Navigator.V1` |
| `DocumentTaxonomy`, `Taxonomy`, `Field` | `UiPath.DocumentProcessing.Contracts.Taxonomy` |

> **Common pitfall.** `ExtractionResult` and `SimpleFieldValue` are **not** in the root `UiPath.DocumentProcessing.Contracts` namespace — they're in the `.Results` sub-namespace. `ExtractionResultHandler` and the `Table*` types live one level deeper still, at `.Extensions.Navigator.V1`. A `using UiPath.DocumentProcessing.Contracts;` alone will not resolve any of them.

## Service Overview

The `du` service exposes four operations covering the standard DU pipeline:

| Operation | Methods | Use when |
|---|---|---|
| **Classify** | `ClassifyDocument(…)` | You need to determine the document type before extraction, or you want to drive a downstream extractor from the classification result. |
| **Extract** | `ExtractDocumentData(…)` | You want the structured field data for a document. Three overloads: start from a path, an `IResource`, or a previously-classified `DocumentData`. |
| **Stage validation artifacts** | `CreateDocumentValidationArtifacts(…)` | You want a human to review the automatic extraction inside a UiPath App — uploads the extraction payload to an Orchestrator storage bucket and returns a handle (`ContentValidationData`) for the app to load. |
| **Retrieve validated results** | `RetrieveDocumentValidationArtifacts(…)` | The App has signaled that validation is complete — pulls the validated `IDocumentData<DictionaryData>` back from storage. |

> **What's not in the `du` service.** The Action Center–based validation activities (`CreateValidationAction`, `WaitForValidationAction`, `CreateClassificationValidationAction`, `WaitForClassificationValidationAction`) are **not** exposed in the coded API. Those activities are persistent — they suspend the workflow until a human action completes — and persistence is not modeled by the coded-workflow request/response shape. For human-in-the-loop validation in a coded workflow, use the Apps-based **artifacts** path (`CreateDocumentValidationArtifacts` + `RetrieveDocumentValidationArtifacts`) shown in this doc.

### Authentication

The `du` methods do **not** take an `apiKey` parameter. At runtime the activities authenticate against your DU.Apps tenant using the robot's standard UiPath cloud session (Orchestrator credentials / `RuntimeAssetPath` / `RuntimeTenantUrl` resolved by the DU framework). The coded API fills `ProjectId` / `ClassifierId` / `Endpoint` with sentinel values; the runtime then resolves the real ids by name via the DU discovery helpers. You only supply names from the user — project name, classifier (when relevant), document type — and the framework does the GUID lookup.

### `projectVersionOrTag` — Studio's unified "Version" parameter

`ClassifyDocument` and `ExtractDocumentData` both take a single string `projectVersionOrTag` argument. This mirrors Studio's "Version" dropdown — pass **either** a version name (e.g. `"v3"`) **or** a tag (e.g. `"Production"`, `"Staging"`, `"live"`). The runtime resolves whichever the project uses: it tries a tag-based lookup first when the project supports tags, then falls back to matching the version name. **For the Predefined project, pass `"Production"`.**

### `projectName` values

- Predefined project → `"Predefined"`
- Custom DU.Apps project → the project's display name as it appears in Document Understanding (e.g. `"Invoice Processing"`). No GUID required.

---

## Classify

### `DocumentData ClassifyDocument(string documentPath, string projectName, string projectVersionOrTag, int timeoutMs = 3_600_000)`
### `DocumentData ClassifyDocument(IResource file, string projectName, string projectVersionOrTag, int timeoutMs = 3_600_000)`

Classifies a document against a DU.Apps project. Two overloads: by file path string, or by `IResource` (e.g. returned from a `PathExists` activity).

**Parameters:**
- `documentPath` (`string`) — Path to the document file on the local file system. Internally wrapped as `LocalResource.FromPath(documentPath)`.
- `file` (`IResource`) — The document resource. Accepts any `IResource`.
- `projectName` (`string`) — DU.Apps project name. Use `"Predefined"` for the predefined project.
- `projectVersionOrTag` (`string`) — Version name (e.g. `"v3"`) or tag (e.g. `"Production"`). Required. See the Service Overview for resolution semantics.
- `timeoutMs` (`int`) — Timeout in milliseconds (default: `3_600_000` = 1 hour). Sub-second values round up to the next whole second.

**Returns:** `DocumentData` — The classification result. Inspect `.DocumentType.Id` for the resolved document-type identifier, `.DocumentType.Confidence` for the classifier's score, and `.SubDocuments` if document splitting produced multiple sections. `DocumentData` implements `IResource`, so you can pass it straight into `ExtractDocumentData(DocumentData, …)` to chain into extraction without re-digitizing the file.

> The wrapped activity is the same `ClassifyDocument` engine used by the XAML activity. The runtime picks the first classifier defined on the project (mirrors Studio's design-time default).

---

## Extract

The `ExtractDocumentData` family has three overloads. The first two take a fresh document (path or `IResource`); the third takes a `DocumentData` produced by a prior `ClassifyDocument` call and avoids re-digitizing the file.

### `IDocumentData<DictionaryData> ExtractDocumentData(string documentPath, string projectName, string projectVersionOrTag, string docType, int timeoutMs = 3_600_000)`
### `IDocumentData<DictionaryData> ExtractDocumentData(IResource file, string projectName, string projectVersionOrTag, string docType, int timeoutMs = 3_600_000)`

Extracts structured data from a document.

**Parameters:**
- `documentPath` / `file` — Source document (path string or `IResource`).
- `projectName` (`string`) — DU.Apps project name.
- `projectVersionOrTag` (`string`) — Version name or tag. Required.
- `docType` (`string`) — Document type id. Semantics depend on the project shape:
  - **DU.Apps multi-doc projects** — required. Pass the doc-type name (e.g. `"invoices"`).
  - **IXP projects** (a single extractor per version, no document-type concept) — pass `null` or empty string. The coded API substitutes its own internal placeholder so the runtime resolves the project's single extractor. This is the coded-workflow equivalent of the XAML `DocType="Default"` value Studio's designer auto-fills for IXP — *do not* pass the literal string `"Default"` here. The XAML doc treats `"Default"` as a special sentinel; in the coded API, omission is the contract.
  - **Predefined project** — pass the pretrained extractor name (e.g. `"invoices"`, `"receipts"`).
- `timeoutMs` (`int`) — Timeout in milliseconds (default: 1 hour).

**Returns:** `IDocumentData<DictionaryData>` — Extracted fields. See [Return Types](#return-types) and the [reaching the contracts API](#4-reach-the-contracts-api-from-an-extracted-document) pattern below for read access.

---

### `IDocumentData<DictionaryData> ExtractDocumentData(DocumentData classifiedDocument, string projectName, string projectVersionOrTag, string docType = null, int timeoutMs = 3_600_000)`

Extracts data from a previously classified document. Avoids re-digitizing the file because `DocumentData` already carries the digitized DOM.

**Parameters:**
- `classifiedDocument` (`DocumentData`) — Output of a previous `ClassifyDocument` call.
- `projectName` (`string`) — DU.Apps project name.
- `projectVersionOrTag` (`string`) — Version name or tag. Required.
- `docType` (`string`) — Optional. When `null` (the default), the runtime resolves the extractor via the **"Use Classification Result"** path: the document-type id from `classifiedDocument.DocumentType.Id` is looked up in the extract project's catalog. This works **only when classify and extract live in the same DU.Apps project**. For cross-project chains, pass `docType` explicitly with the extract project's document-type name.
- `timeoutMs` (`int`) — Timeout in milliseconds (default: 1 hour).

**Returns:** `IDocumentData<DictionaryData>`.

> **Why no `GenerateData=True` / strongly-typed `<T>`?** XAML offers a "Generate strongly-typed data class" option that emits a project-specific subclass of `ExtendedExtractionResultsForDocumentData` at design time. That subclass needs Studio's JIT compilation step — it doesn't exist at coded-workflow build time. The coded API standardizes on `DictionaryData`, which exposes the same fields by name/id (`GetField`, `GetFieldValue`, `GetTable`) without any code generation. For the full `DictionaryData` API see the [data type patterns reference](../activities/ExtractDocumentData/data-type-patterns.md).

---

## Stage Validation Artifacts

### `ContentValidationData CreateDocumentValidationArtifacts(IDocumentData<DictionaryData> automaticExtractionResults, string orchestratorFolderName, string orchestratorBucketName = null)`

Uploads the extraction payload (results + DOM + taxonomy) to an Orchestrator storage bucket and returns the handle for a UiPath App to load.

**Parameters:**
- `automaticExtractionResults` (`IDocumentData<DictionaryData>`) — Output of `ExtractDocumentData(…)`.
- `orchestratorFolderName` (`string`) — Orchestrator folder under which the bucket lives. **Required** — no default.
- `orchestratorBucketName` (`string`) — Bucket name. When `null` (the default), the underlying activity falls back to `SWConstants.DefaultBucketName` (`"du_storage_bucket"`). Pass a value only when the user specifies a custom bucket.

**Returns:** `ContentValidationData` — Opaque handle. Persist or pass it to the validating UiPath App; later round-trip it back to `RetrieveDocumentValidationArtifacts`.

---

### `IDocumentData<DictionaryData> RetrieveDocumentValidationArtifacts(ContentValidationData contentValidationData, object completedAppAction = null, bool removeDataFromStorage = false, bool returnAutomaticExtractionResults = false)`

Retrieves the validated extraction results from storage after the App has completed validation.

**Parameters:**
- `contentValidationData` (`ContentValidationData`) — The handle returned from `CreateDocumentValidationArtifacts(…)`.
- `completedAppAction` (`object`) — Optional. The completed app-action object handed back by the UiPath App (matches the XAML activity's `CompletedAppAction` input, typed as `object`).
- `removeDataFromStorage` (`bool`) — When `true`, deletes the underlying storage artifacts after a successful retrieval (default: `false`).
- `returnAutomaticExtractionResults` (`bool`) — When `true`, returns the **original automatic** extraction results instead of the validated ones — useful for diffing automatic vs. validated outputs (default: `false`).

**Returns:** `IDocumentData<DictionaryData>` — The validated (or original, if `returnAutomaticExtractionResults` is `true`) extraction results.

---

## Return Types

### `DocumentData` (namespace `UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification`)

Output of `ClassifyDocument`. Implements `IResource` so it can be passed straight into `ExtractDocumentData(DocumentData, …)` without re-loading the file.

| Property | Type | Description |
|---|---|---|
| `DocumentType` | `DocumentType` | The classified document type (see below). |
| `SubDocuments` | `IDocumentData[]` | Sub-documents when document splitting produced multiple sections. |
| `FileDetails` | `FileDetails` | File path, name, extension, and page range. |
| `DocumentMetadata` | `DocumentMetadata` | OCR text, DOM, language, and extraction results as DataTables. |

### `DocumentType`

| Property | Type | Description |
|---|---|---|
| `DisplayName` | `string` | Human-readable label (e.g. `"Invoices"`). |
| `Id` | `string` | Machine identifier (e.g. `"invoices"`). Use for programmatic comparisons. |
| `Confidence` | `float` | Classification confidence (0.0–1.0). |
| `Url` | `string` | Reference URL for the document type definition. |

### `IDocumentData<DictionaryData>` (namespace `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction`)

Output of `ExtractDocumentData`. Wraps the contracts `ExtractionResult` and exposes the fields through `DictionaryData`.

| Member | Type | Description |
|---|---|---|
| `Data` | `DictionaryData` | The strongly-typed-by-name field bag (see below). |
| `DocumentType` | `DocumentType` | The document type used for extraction. |
| `DocumentMetadata` | `DocumentMetadata` | OCR text, DOM, and `ResultsAsDataTables` for tabular export. |
| `SubDocuments` | `IDocumentData[]` | Subdocuments (if splitting occurred upstream). |

#### `DictionaryData`

| Method | Returns | Description |
|---|---|---|
| `GetField(string idOrName)` | `ResultsDataPoint` | A non-table field by id or name. |
| `GetFieldValue(string idOrName)` | `ResultsValue` | First value of a field. |
| `GetFieldValues(string idOrName)` | `ResultsValue[]` | All values of a field. |
| `GetFields()` | `ResultsDataPoint[]` | All non-table fields. |
| `GetTable(string idOrName)` | `ResultsTable` | A table by id or name (legacy — for the modern path use `Handler.GetTableValue(…)`). |
| `GetTables()` | `ResultsTable[]` | All tables. |
| `GetProperties()` | `IDocumentDataProperties` | Activity-side metadata bag; the runtime path to the contracts `ExtractionResult`. See the pattern below. |
| `Handler` | `ExtractionResultHandler` | Shortcut equivalent to `new ExtractionResultHandler(GetProperties().ExtractionResult)` — use for tables, field groups, and mutation. |

> `Handler` is a **runtime navigator**, not part of the wire format. If you JSON-serialize a `DictionaryData` (or its `IDocumentData<DictionaryData>` wrapper), the `Handler` is empty (`{}`) after a round-trip; reconstruct it via `new ExtractionResultHandler(deserialized.GetProperties().ExtractionResult)`.

### `ContentValidationData` (namespace `UiPath.DocumentProcessing.Contracts.Actions`)

Opaque handle returned by `CreateDocumentValidationArtifacts` and consumed by `RetrieveDocumentValidationArtifacts`. Treat as opaque — persist by serializing and pass round-trip; do not depend on its internal shape.

---

## Reading extracted fields

> **READ THIS FIRST — discover before hardcoding.** When a user says "extract the total" (or any field), **the user's phrasing rarely matches the project's schema literally.** The schema's **FieldId** is a machine identifier — often a short, dashed slug like `total-amount`, `invoice-total`, or `inv_total` — and the **FieldName** is the display label like `"Total Amount"`. Neither of them is usually `"total"`. **Never hardcode the user's term as the FieldId on your first attempt.** Always either run [Recipe 1 (dump every extracted field)](#recipe-1--dump-every-extracted-field) once to inspect what the project actually exposes, **or** use the substring-discovery entry point shown in [Recipe 2](#recipe-2--fuzzy-match-a-user-phrasing-to-a-real-field) and [Common Patterns § 5](#5-extract-a-basic-field-with-a-confidence-check). The hardcoded-FieldId form `result.GetSimpleFieldValues("total")` is a known foot-gun — `"total"` is not the FieldId for the Predefined `invoices` extractor (the agent's most common first guess) and the call returns an empty array. Treat hardcoded ids as an **optimization** for code you've already verified, not as the entry point for new code.

Once you have an `IDocumentData<DictionaryData>` from `ExtractDocumentData(...)`, fields are accessed by **FieldId** or **FieldName**, both case-insensitive. The remainder of this section covers (1) the defensive discovery pattern you should reach for first, (2) the three lookup methods and their match rules, and (3) symptoms-and-fixes for the common failure modes.

> **Authoritative reference for the types used in this section:** the contracts package per-class docs — [`ExtractionResult.md`](../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResult.md) (covers `ResultsDocument`, `ResultsDataPoint`, `ResultsValue`, `SimpleFieldValue`, all the `Get*FieldValues*` overloads, lookup semantics, and the five supported field shapes) and [`ExtractionResultHandler.md`](../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResultHandler.md) (covers `Data.Handler`, `TableValue`/`TableRow` navigation, mutation, and FieldId/FieldName ambiguity rules). The summaries here are intentionally narrow — read those docs when you need a property or method this section doesn't mention.

### Discovering field names (the defensive entry point)

Discovery is the **first** thing your code should do when given a user-supplied field term — not the recovery action after a miss. The two recipes below tolerate FieldId/FieldName drift, user-phrasing/schema mismatches, and case differences.

#### Recipe 1 — dump every extracted field

Logs FieldId, FieldName, first value, and confidence. Run this on one representative document to see what the project exposes before you write any field-name-dependent code:

```csharp
// Required usings for this recipe:
using System.Linq;                                                       // .FirstOrDefault
using UiPath.DocumentProcessing.Contracts.Results;                       // ExtractionResult, ResultsDocument

ExtractionResult result = extracted.Data.GetProperties().ExtractionResult;
foreach (var f in result.ResultsDocument.Fields)
{
    var v = f.Values?.FirstOrDefault();
    Log($"FieldId='{f.FieldId}', FieldName='{f.FieldName}', value='{v?.Value}', conf={v?.Confidence:P2}");
}
```

#### Recipe 2 — fuzzy-match a user phrasing to a real field

This is the **canonical reading pattern** when you start from a user term (e.g. `"total"`, `"vendor"`, `"date"`) and need to find the matching schema entry. Substring-match against both `FieldId` and `FieldName` case-insensitively. On a unique hit, log the resolved FieldId AND FieldName so future runs and code reviewers see the mapping; on miss or ambiguity, dump the full inventory automatically:

```csharp
// Required usings for this recipe:
using System;                                                            // StringComparison
using System.Linq;                                                       // .Where, .Select, .FirstOrDefault, .ToList
using UiPath.DocumentProcessing.Contracts.Results;                       // ExtractionResult, ResultsDataPoint, ResultsValue

ExtractionResult result = extracted.Data.GetProperties().ExtractionResult;
string userTerm = "total";   // ← whatever the user said; do NOT assume this matches the FieldId or FieldName literally

var matches = result.ResultsDocument.Fields.Where(f =>
    f.FieldId.IndexOf(userTerm, StringComparison.OrdinalIgnoreCase) >= 0 ||
    f.FieldName.IndexOf(userTerm, StringComparison.OrdinalIgnoreCase) >= 0
).ToList();

if (matches.Count != 1)
{
    Log(matches.Count == 0
        ? $"No field matched '{userTerm}'."
        : $"'{userTerm}' is ambiguous — matched {matches.Count} fields: " +
          string.Join(", ", matches.Select(f => $"{f.FieldName} ({f.FieldId})")) +
          ". Pick a more specific term or hard-code the resolved FieldId after inspecting the dump below.");
    Log("Available fields:");
    foreach (var f in result.ResultsDocument.Fields)
    {
        var v = f.Values?.FirstOrDefault();
        Log($"  - FieldId='{f.FieldId}', FieldName='{f.FieldName}', value='{v?.Value}', conf={v?.Confidence:P2}");
    }
}
else
{
    ResultsDataPoint match = matches[0];
    ResultsValue value = match.Values?.FirstOrDefault();
    Log($"Matched '{match.FieldName}' (FieldId='{match.FieldId}', conf={value?.Confidence:P2}): '{value?.Value}'");
}
```

> **Why substring on both sides?** FieldId and FieldName don't paraphrase the same way. A schema can expose `FieldId="total-amount"` with `FieldName="Total Amount"`, or `FieldId="inv_total"` with `FieldName="Invoice Total"`. A user term `"total"` is a substring of all of these on at least one side, but matches none of them exactly. Both exact `GetSimpleFieldValues("total")` and `GetSimpleFieldValuesByFieldName("Total")` return empty arrays; only the substring scan finds the field. **This is the failure mode the agent hit on Recipe 5 before it was rewritten** — see [Symptoms and fixes](#symptoms-and-fixes) below.

> **If you need this in multiple workflows, hoist into an extension method.** Same logic, reusable:
>
> ```csharp
> using System;
> using System.Linq;
> using UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;
> using UiPath.DocumentProcessing.Contracts.Results;
>
> public static class DuExtensions
> {
>     public static (ResultsValue value, string fieldId, string fieldName)? ResolveBasicField(
>         this IDocumentData<DictionaryData> doc, string userTerm, Action<string> log)
>     {
>         var result = doc.Data.GetProperties().ExtractionResult;
>         var matches = result.ResultsDocument.Fields.Where(f =>
>             f.FieldId.IndexOf(userTerm, StringComparison.OrdinalIgnoreCase) >= 0 ||
>             f.FieldName.IndexOf(userTerm, StringComparison.OrdinalIgnoreCase) >= 0
>         ).ToList();
>         if (matches.Count != 1)
>         {
>             log($"'{userTerm}' matched {matches.Count} field(s). Available fields:");
>             foreach (var f in result.ResultsDocument.Fields)
>             {
>                 var fv = f.Values?.FirstOrDefault();
>                 log($"  - FieldId='{f.FieldId}', FieldName='{f.FieldName}', value='{fv?.Value}', conf={fv?.Confidence:P2}");
>             }
>             return null;
>         }
>         var m = matches[0];
>         return (m.Values?.FirstOrDefault(), m.FieldId, m.FieldName);
>     }
> }
> ```

### Which lookup method to call (reference)

Once you have **verified** the actual FieldId or FieldName by running discovery, you can swap the substring scan for a direct lookup. `DictionaryData` and the underlying `ExtractionResult` expose three lookups with **different match rules**:

| Call | Matches against | Falls back? | Use when |
|---|---|---|---|
| `extracted.Data.GetFieldValue(idOrName)` | FieldId (or last dotted segment), then FieldName — case-insensitive two-pass | yes | You know the **exact** FieldId or FieldName — but note: neither side falls back to substring, so a user term like `"total"` against a `total-amount` FieldId still returns `null` here. Use the discovery scan for user-phrasing inputs. |
| `result.GetSimpleFieldValues(fieldId)` | FieldId only, case-insensitive **exact** | no | You have the FieldId hardcoded from a verified taxonomy and don't need name resolution. |
| `result.GetSimpleFieldValuesByFieldName(name)` | FieldName only, case-insensitive **exact** | no | You have the FieldName hardcoded from a verified taxonomy. |

(where `result = extracted.Data.GetProperties().ExtractionResult`)

**None of these three is a safe entry point for user-phrasing inputs.** All three require an exact match (case-aside) on a side they search. For agent-generated code starting from user terms, the substring discovery in Recipe 2 is the correct entry point.

### Symptoms and fixes

Common symptoms seen when reading basic fields, with their actual cause and fix:

| Symptom | Most likely cause | Fix |
|---|---|---|
| `result.GetSimpleFieldValues("total").FirstOrDefault()` returns `null` on every document. | FieldId is **not** literally `"total"` in this extractor (Predefined `invoices` uses something like `total-amount` or similar; schemas drift between versions). The exact FieldId match never fires. | Switch to the substring scan in [Recipe 2](#recipe-2--fuzzy-match-a-user-phrasing-to-a-real-field) / [Pattern 5](#5-extract-a-basic-field-with-a-confidence-check). Run [Recipe 1](#recipe-1--dump-every-extracted-field) once to see the real FieldId, then optionally hardcode it after verification. |
| `result.GetSimpleFieldValuesByFieldName("Total").FirstOrDefault()` returns `null`. | FieldName is `"Total Amount"` (or similar), not exactly `"Total"`. Exact FieldName match fails. | Same fix — substring discovery. |
| `extracted.Data.GetFieldValue("total")` returns `null`. | Neither side of the two-pass matches the user term exactly. `Data.GetFieldValue` does **not** fall back to substring. | Same fix — substring discovery. |
| `null` on **some** documents but a value on others (same FieldId). | The extractor genuinely produced no value for those documents — the field was not visible / not extractable. Not a code bug. | Treat null as "not extracted on this document" and route to your null-handling branch (log + skip / send to validation / etc.). |
| `value.Confidence < 1.0f` is firing on every document. | The minimum-confidence threshold is too strict for this extractor. Most extractors rarely return exactly `1.0`. | Use `0.8f`–`0.9f` as a typical gate, or whatever the user's SLA dictates. |
| `extracted.Data.GetFieldValue("items")` throws or returns unexpected shape. | `items` is a **table** field, not a basic field. The basic-field lookups skip table fields. | Use `extracted.Data.Handler.GetTableValue("items")` — see [§ Common Patterns 4](#4-reach-the-contracts-api-from-an-extracted-document). |

---

## Common Patterns

### 1. Classify and extract a Predefined-project document

```csharp
// Required usings for this recipe:
using UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification; // DocumentData
using UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;          // IDocumentData<T>, DictionaryData

public class ClassifyAndExtractInvoice : CodedWorkflow
{
    [Workflow]
    public void Execute()
    {
        DocumentData classified = du.ClassifyDocument(
            documentPath: @"C:\inbox\unknown.pdf",
            projectName: "Predefined",
            projectVersionOrTag: "Production");

        Log($"Classified as {classified.DocumentType.Id} " +
            $"(confidence {classified.DocumentType.Confidence:P0})");

        IDocumentData<DictionaryData> extracted = du.ExtractDocumentData(
            classifiedDocument: classified,
            projectName: "Predefined",
            projectVersionOrTag: "Production");
        //  docType omitted → "use classification result" mode (same project)

        // Extract the field value into a variable first — nesting an unescaped string literal
        // inside an interpolated string (e.g. $"... {x.GetFieldValue("Vendor Name")} ...") is a
        // compile error on C# 10 and earlier (the default for net6.0 projects).
        string vendorName = extracted.Data.GetFieldValue("Vendor Name")?.Value;
        Log($"Vendor: {vendorName}");
    }
}
```

> The string `"Vendor Name"` here is the FieldName from the Predefined `invoices` taxonomy. Field names are project-specific — if your `GetFieldValue(...)` call returns `null`, use the [§ Discovering field names](#discovering-field-names-the-defensive-entry-point) recipes to find the real ones in the extraction result.

### 2. Extract from a custom DU.Apps project (friendly-name `docType`)

```csharp
// Required usings for this recipe:
using UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction; // IDocumentData<T>, DictionaryData

public class ExtractInvoices : CodedWorkflow
{
    [Workflow]
    public void Execute()
    {
        IDocumentData<DictionaryData> extracted = du.ExtractDocumentData(
            documentPath: @"C:\inbox\acme-invoice.pdf",
            projectName: "Invoice Processing",
            projectVersionOrTag: "Production",
            docType: "invoices");

        foreach (var field in extracted.Data.GetFields())
        {
            Log($"{field.FieldName}: {field.Values.FirstOrDefault()?.Value}");
        }
    }
}
```

### 3. Extract from an IXP-style project (single extractor per version)

IXP projects don't have a doc-type concept — pass `null` or empty string for `docType`. The runtime resolves the single extractor for the version. (In a XAML workflow the equivalent is `DocType="Default"` — the coded API uses omission instead; **do not** pass the literal string `"Default"`.)

```csharp
// Required usings for this recipe:
using UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction; // IDocumentData<T>, DictionaryData

public class ExtractWithIxpProject : CodedWorkflow
{
    [Workflow]
    public void Execute()
    {
        IDocumentData<DictionaryData> extracted = du.ExtractDocumentData(
            documentPath: @"C:\inbox\receipt.pdf",
            projectName: "Receipts IXP",
            projectVersionOrTag: "v2",
            docType: null);   // IXP: null/empty → coded API resolves the single extractor

        Log(extracted.Data.GetFieldValue("Total")?.Value);
    }
}
```

> `"Total"` is shown here as a placeholder for whatever field the IXP project exposes — substitute the FieldId or FieldName from that project's taxonomy. If you don't know the exact spelling, [§ Discovering field names](#discovering-field-names) gives you a runtime recipe.

### 4. Reach the contracts API from an extracted document

The wrapper types are thin — when you need tables, field groups, or any mutation, drop down to `ExtractionResult` / `ExtractionResultHandler`. `GetProperties().ExtractionResult` is the supported runtime path; `Data.Handler` is the shortcut for the same instance.

```csharp
// Required usings for this recipe:
using System.Linq;                                                        // .FirstOrDefault
using UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;          // IDocumentData<T>, DictionaryData
using UiPath.DocumentProcessing.Contracts.Results;                        // ExtractionResult, SimpleFieldValue
using UiPath.DocumentProcessing.Contracts.Extensions.Navigator.V1;        // ExtractionResultHandler, TableRow

public class ReadInvoiceFields : CodedWorkflow
{
    [Workflow]
    public void Execute()
    {
        IDocumentData<DictionaryData> extracted = du.ExtractDocumentData(
            documentPath: @"C:\inbox\invoice.pdf",
            projectName: "Invoice Processing",
            projectVersionOrTag: "Production",
            docType: "invoices");

        // Basic-field read: use the direct ExtractionResult API
        ExtractionResult result = extracted.Data.GetProperties().ExtractionResult;
        SimpleFieldValue vendor = result
            .GetSimpleFieldValuesByFieldName("Vendor Name")   // FieldName-only, no FieldId fallback
            .FirstOrDefault();
        Log($"Vendor: {vendor?.Value}");

        // Tables / field groups: use the Handler.
        // TableRow exposes GetCell(string)/this[string] returning BasicDataPoint; .Value gives BasicValue; .Value on that gives the string.
        // There is no GetCellValue(string) on TableRow — that overload lives on TableValue (and takes a row index).
        // Hoist each cell read into a local before interpolating: nesting an unescaped string literal
        // inside $"..." (e.g. $"... {row["Description"]} ...") is a parse error on C# 10 and earlier.
        ExtractionResultHandler handler = extracted.Data.Handler;
        foreach (TableRow row in handler.GetTableValue("Line Items").Rows)
        {
            string description = row["Description"].Value?.Value;
            string quantity = row["Quantity"].Value?.Value;
            Log($"  • {description} × {quantity}");
        }
    }
}
```

> The strings `"Vendor Name"`, `"Line Items"`, `"Description"`, `"Quantity"` are FieldNames from the Predefined `invoices` taxonomy at the time of writing. They can change between project versions. If `vendor` comes back `null` or the table loop yields nothing, run the [§ Discovering field names](#discovering-field-names) recipes to confirm the actual taxonomy.

### 5. Extract a basic field with a confidence check

Extracting one named field and gating downstream logic on its confidence is the single most common DU coded task — and the most common failure mode for agent-generated code. **Use this recipe as the entry point, not the optimised form below it.** It is intentionally verbose: it starts from the user's phrasing (which rarely matches the schema literally), uses substring discovery to resolve to the real FieldId/FieldName, auto-dumps the field inventory on miss so the next iteration of agent code can self-correct, and logs the resolved FieldId AND FieldName on hit so future runs see the mapping.

```csharp
// Required usings for this recipe:
using System;                                                             // StringComparison
using System.Linq;                                                        // .Where, .Select, .FirstOrDefault, .ToList
using UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;          // IDocumentData<T>, DictionaryData
using UiPath.DocumentProcessing.Contracts.Results;                        // ExtractionResult, ResultsDataPoint, ResultsValue

public class ReadInvoiceFieldWithConfidence : CodedWorkflow
{
    [Workflow]
    public void Execute()
    {
        IDocumentData<DictionaryData> extracted = du.ExtractDocumentData(
            documentPath: @"C:\inbox\invoice.pdf",
            projectName: "Predefined",
            projectVersionOrTag: "Production",
            docType: "invoices");

        ExtractionResult result = extracted.Data.GetProperties().ExtractionResult;

        // ── Step 1: Discovery scan ────────────────────────────────────────────────
        // Substring-match the user's term against BOTH FieldId and FieldName.
        // This is the defensive entry point — do not skip it with a hardcoded FieldId.
        // User term -> schema mapping is rarely literal (e.g. user says "total",
        // schema has FieldId="total-amount", FieldName="Total Amount").
        const string userTerm = "total";                  // ← substitute with whatever the user said
        const float minConfidence = 1.0f;                 // ← raise/lower per SLA; 1.0 means "any uncertainty flags"

        var matches = result.ResultsDocument.Fields.Where(f =>
            f.FieldId.IndexOf(userTerm, StringComparison.OrdinalIgnoreCase) >= 0 ||
            f.FieldName.IndexOf(userTerm, StringComparison.OrdinalIgnoreCase) >= 0
        ).ToList();

        // ── Step 2: On miss or ambiguity, dump the full inventory and bail ────────
        // Inlining the dump (instead of telling the developer "go run a diagnostic")
        // means the next iteration of agent code has everything it needs to self-correct.
        if (matches.Count != 1)
        {
            Log(matches.Count == 0
                ? $"No field matched '{userTerm}' on this document."
                : $"'{userTerm}' is ambiguous — matched {matches.Count} fields: " +
                  string.Join(", ", matches.Select(f => $"{f.FieldName} ({f.FieldId})")) +
                  ". Pick a more specific term or hard-code the resolved FieldId.");
            Log("Available fields on this document:");
            foreach (var f in result.ResultsDocument.Fields)
            {
                var fv = f.Values?.FirstOrDefault();
                Log($"  - FieldId='{f.FieldId}', FieldName='{f.FieldName}', value='{fv?.Value}', conf={fv?.Confidence:P2}");
            }
            return;
        }

        // ── Step 3: Hit — log the resolved mapping and read the value ─────────────
        ResultsDataPoint match = matches[0];
        ResultsValue value = match.Values?.FirstOrDefault();
        if (value == null)
        {
            Log($"'{match.FieldName}' (FieldId='{match.FieldId}') is present in the schema but the extractor returned no value on this document.");
            return;
        }

        // Log BOTH the resolved FieldId and FieldName so reviewers / future runs see what userTerm mapped to.
        Log($"Matched '{match.FieldName}' (FieldId='{match.FieldId}', conf={value.Confidence:P2}): '{value.Value}'");

        // ── Step 4: Apply confidence gate ─────────────────────────────────────────
        if (value.Confidence < minConfidence)
        {
            Log($"Low confidence ({value.Confidence:P2}) for {match.FieldName} = '{value.Value}' — flag for review.");
        }
        else
        {
            // … use value.Value, e.g. write to Excel, push to next workflow step.
        }
    }
}
```

> **Why is this recipe so much longer than `result.GetSimpleFieldValues("total").FirstOrDefault()`?**
> Because the one-line form **silently returns an empty array** when the FieldId doesn't literally match — and `"total"` is **not** the Predefined `invoices` FieldId (a real failure mode hit by an agent following an earlier version of this recipe). The defensive form above costs ~30 lines and tolerates user-phrasing mismatch, FieldId/FieldName drift between project versions, and provides automatic self-correction telemetry on miss. **For agent-generated code, this is the right shape.** Treat the one-liner as an optimisation you can apply *after* discovery has confirmed the literal id.

> **Optimised variant — only after you've verified the FieldId.** Once a discovery run has logged the resolved mapping (e.g. `Matched 'Total Amount' (FieldId='total-amount', conf=98.40%)`), you can swap to the direct contracts-side read. Treat this as code-for-stable-pipelines, not for agent-generated first drafts. Re-verify after any project-version bump:
>
> ```csharp
> SimpleFieldValue v = result.GetSimpleFieldValues("<resolved-field-id-from-discovery>").FirstOrDefault();
> if (v == null) { /* fall back to discovery — the FieldId may have drifted */ }
> ```

### 6. PDF → Classify → Extract (cross-package: requires `UiPath.PDF.Activities`)

`DocumentData` and `IResource`-returning PDF methods compose cleanly. The PDF service can hand a page-range PDF directly to `ClassifyDocument` as an `IResource`.

Add to `project.json`:
```json
"UiPath.DocumentUnderstanding.Activities": "*",
"UiPath.PDF.Activities":                   "*"
```

```csharp
// Required usings for this recipe:
using UiPath.Platform.ResourceHandling;                                  // ILocalResource
using UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification; // DocumentData
using UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;         // IDocumentData<T>, DictionaryData

public class FirstThreePagesOnly : CodedWorkflow
{
    [Workflow]
    public void Execute()
    {
        ILocalResource trimmed = pdf.ExtractPdfPageRange(
            fileName: @"C:\inbox\big.pdf",
            range: "1-3");

        DocumentData classified = du.ClassifyDocument(
            file: trimmed,
            projectName: "Predefined",
            projectVersionOrTag: "Production");

        IDocumentData<DictionaryData> extracted = du.ExtractDocumentData(
            classifiedDocument: classified,
            projectName: "Predefined",
            projectVersionOrTag: "Production");

        Log(extracted.Data.GetFieldValue("Total")?.Value);
    }
}
```

### 7. Apps-based validation handoff

Stage the automatic extraction for a UiPath App, then retrieve the validated result later. In a real workflow the App run typically lives in a separate process — the two halves shown here would not normally execute in the same `Execute()` method.

```csharp
// Required usings for this recipe:
using UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;         // IDocumentData<T>, DictionaryData
using UiPath.DocumentProcessing.Contracts.Actions;                       // ContentValidationData

public class ValidateViaApp : CodedWorkflow
{
    [Workflow]
    public void Execute()
    {
        IDocumentData<DictionaryData> automatic = du.ExtractDocumentData(
            documentPath: @"C:\inbox\invoice.pdf",
            projectName: "Invoice Processing",
            projectVersionOrTag: "Production",
            docType: "invoices");

        ContentValidationData handle = du.CreateDocumentValidationArtifacts(
            automaticExtractionResults: automatic,
            orchestratorFolderName: "Shared");
        //  orchestratorBucketName omitted → activity default "du_storage_bucket"

        // ... persist 'handle' and hand it to the UiPath App.
        // Later, after the App reports completion:

        IDocumentData<DictionaryData> validated = du.RetrieveDocumentValidationArtifacts(
            contentValidationData: handle,
            removeDataFromStorage: true);

        string validatedVendor = validated.Data.GetFieldValue("Vendor Name")?.Value;
        Log($"Validated vendor: {validatedVendor}");
    }
}
```

---

## Notes for Coding Agents

- **Windows only.** The `du` service is currently available only for Windows projects.
- **Always add explicit `using` directives in coded `.cs` files.** The list of namespaces in [§ Namespaces and `using` directives](#namespaces-and-using-directives) is a *lookup table*, not an implicit-imports list — it applies to XAML expression compile and InvokeCode bodies, **not** to standalone `.cs` files compiled by `uip rpa build`. Every code example in this doc starts with a `// Required usings for this recipe:` block — preserve those when copying. `uip rpa get-errors` passes clean on missing `using`s; only `uip rpa build` (or Studio's project compile) surfaces the `CS0246` failures.
- **Direct dependency on `UiPath.DocumentProcessing.Contracts` is mandatory** for any recipe that reaches the contracts API (Recipes 1–2, Patterns 4 and 5). The DU package restores the contracts assembly transitively into the NuGet cache, but the compile reference list only sees direct dependencies — install via `uip rpa install-or-update-packages` (see [§ Required packages](#required-packages)).
- **No `apiKey` parameter.** The `du` methods authenticate via the robot's standard UiPath cloud session — same path the XAML activities use. You only supply names from the user (project, classifier, document type); the framework resolves GUIDs and endpoints at runtime. Never invent an `apiKey` parameter when generating coded DU workflows.
- **`projectVersionOrTag` accepts either form.** A version name (e.g. `"v3"`) or a tag (e.g. `"Production"`, `"live"`) both work — the runtime resolves whichever the project uses. For Predefined, always pass `"Production"`.
- **`docType` semantics differ by project shape.** Friendly name for DU.Apps multi-doc projects (e.g. `"invoices"`); `null` or `""` for IXP single-extractor projects (the coded-workflow equivalent of XAML's `DocType="Default"` — pass omission, **not** the literal string `"Default"`); omitted (on the `DocumentData` overload only) to mean "use the classification result" — which requires classify and extract to live in the **same** project. Do not ask the user for a document-type name when the project is IXP.
- **`DictionaryData` is the only extraction type.** XAML's "Generate strongly-typed data class" path is unavailable in coded workflows because it relies on Studio's design-time JIT. Reach fields by name via `Data.GetField(…)` / `Data.GetFieldValue(…)`, or drop to the contracts API via `Data.GetProperties().ExtractionResult` / `Data.Handler`.
- **Discover field names before reading them — never hardcode the user's phrasing as a FieldId.** This is the single most common agent failure mode for DU coded workflows. The user's term (`"total"`, `"vendor"`, `"date"`) is almost never the literal FieldId or FieldName in the schema — Predefined extractors and DU.Apps projects use slugs like `total-amount`, `inv_total`, `vendor-name`. All three exact lookups (`Data.GetFieldValue`, `GetSimpleFieldValues`, `GetSimpleFieldValuesByFieldName`) return empty when the user term doesn't match exactly. The defensive entry point is the substring-scan pattern shown in [§ Reading extracted fields — Discovering field names](#discovering-field-names-the-defensive-entry-point), inlined end-to-end in [Common Patterns § 5](#5-extract-a-basic-field-with-a-confidence-check). Use the direct lookups only **after** discovery has logged the resolved FieldId — and re-verify after a project-version bump. See also [§ Symptoms and fixes](#symptoms-and-fixes) for the specific failure modes and their fixes.
- **No `using` blocks needed on the service return values.** Neither `DocumentData`, `IDocumentData<DictionaryData>`, nor `ContentValidationData` is `IDisposable`. Just call and use.
- **No Action Center / `Wait*` activities in the coded surface.** The `du` service exposes only the **Apps-based** validation path (`CreateDocumentValidationArtifacts` + `RetrieveDocumentValidationArtifacts`). For Action Center–based persistent validation tasks, author a XAML workflow with the corresponding activities — see the per-activity docs under [`../activities/`](../activities/).
- **`DocumentData` is itself an `IResource`.** Chain `ClassifyDocument` into `ExtractDocumentData(DocumentData, …)` to avoid re-digitizing the file. The classified document carries the digitized DOM into the extract call.
- **Default timeout is 1 hour.** Match the underlying XAML activities' `TimeoutInSeconds = 3600`. Override via `timeoutMs` when you have a shorter SLA budget.
- **Per-activity references.** For the full property surface of each underlying activity — including `MinimumConfidence`, `RuntimeAssetPath`, `RuntimeTenantUrl`, sub-document handling, and the XAML examples — read the matching doc under [`../activities/`](../activities/): [`ClassifyDocument.md`](../activities/ClassifyDocument.md), [`ExtractDocumentData.md`](../activities/ExtractDocumentData.md), [`CreateDocumentValidationArtifacts.md`](../activities/CreateDocumentValidationArtifacts.md), [`RetrieveDocumentValidationArtifacts.md`](../activities/RetrieveDocumentValidationArtifacts.md).
- **Contracts API for advanced reads — read the contracts docs.** When you need anything beyond basic field reads — tables, field groups, mutation, taxonomy-driven row construction — drop to the `UiPath.DocumentProcessing.Contracts.*` types (`ExtractionResult`, `ExtractionResultHandler`, `DocumentTaxonomy`, …). The per-class reference for those types lives in the contracts package's own docs, not in this file; this doc only points you at them. Read [`ExtractionResult.md`](../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResult.md), [`ExtractionResultHandler.md`](../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResultHandler.md), [`Taxonomy.md`](../../UiPath.DocumentProcessing.Contracts/classes/Taxonomy.md), [`ClassificationResult.md`](../../UiPath.DocumentProcessing.Contracts/classes/ClassificationResult.md), and [`Document.md`](../../UiPath.DocumentProcessing.Contracts/classes/Document.md) — also indexed in the [§ Required packages](#required-packages) callout — before authoring contracts-side code. They are the authoritative source for property/method surface, lookup rules, mutation contracts, and edge cases. See also [`overview.md` § Underlying contracts types](../overview.md#underlying-contracts-types) for the wrapper-to-contracts type mapping.

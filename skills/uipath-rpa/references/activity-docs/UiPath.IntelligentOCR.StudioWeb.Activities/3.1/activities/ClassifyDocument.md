# Classify Document

`UiPath.IntelligentOCR.StudioWeb.Activities.ClassifyDocument`

Classifies a document according to the configured classifier in the Document Understanding framework. Supports pretrained classifiers for standard document types (invoices, receipts, id_cards, passports, purchase_orders, utility_bills, remittance_advices, bills_of_lading, checks).

**Package:** `UiPath.DocumentUnderstanding.Activities`
**Category:** Document Understanding

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ProjectId` | Document Understanding project | InArgument | `string` | Yes | | The Document Understanding project ID. Should be a GUID-formatted string (e.g., `"00000000-0000-0000-0000-000000000000"` for the Predefined project). Internally parsed via `Guid.Parse()` at runtime. For custom projects, if the GUID is unknown, set `ProjectName` to the project's display name and use a non-GUID placeholder string for ProjectId (e.g., ProjectId="placeholder"). Do not use "00000000-0000-0000-0000-000000000000" — that is the Predefined project's real GUID and will be accepted as-is without triggering name-based resolution — **Studio resolves `ProjectId` from `ProjectName` at design time**. Set as a **literal attribute value** (not a VB expression). |
| `ProjectVersionNumber` | Version | InArgument | `int` | No | | The version number referencing a snapshot of the Document Understanding project. Use this **or** `ProjectTag` (not both). For the Predefined project, use `0`. |
| `ProjectTag` | Tag | InArgument | `string` | No | | An alternative to version number. A tag referencing a snapshot of the Document Understanding project (e.g., `"Production"`). For the Predefined project, use `"Production"`. |
| `ClassifierId` | Classifier | InArgument | `string` | Yes | | The classifier to use. For the Predefined project, use `ml-classification` (recommended) or a document-type-specific identifier (see Enum Reference). For custom DU projects, use the **classifier name** from the project. Ask the user for this name. Studio resolves names to internal GUIDs at design time. Set `ClassifierName` to the same value. |
| `FileInput` | Input | InArgument | `IResource` | Yes | | Document Data referencing the digitized input file, or the input file itself if Document Data has not been created yet. |
| `TimeoutInSeconds` | Timeout (seconds) | InArgument | `int` | Yes | `3600` | Maximum execution time in seconds. If exceeded, the operation is terminated. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `MinimumConfidence` | Minimum confidence | `float` | `0` | Minimum confidence threshold for classification. If the classification confidence is below this value, the document type is set to Unknown. |
| `RuntimeAssetPath` | Runtime Credentials Asset | `string` | | Orchestrator credentials asset path for cross-org authentication. Format: `<orchestratorFolder>/<assetName>`. |
| `RuntimeTenantUrl` | Runtime Tenant Url | `string` | | URL to an external tenant for cross-org authentication. Format: `https://<base_url>/<organization>/<tenant>`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ClassificationResults` | Document data | OutArgument | `DocumentData` | Classification results. The `DocumentType` property contains the classified type, confidence, and identifiers. May contain multiple subdocuments if document splitting is enabled. See Type Reference below. |

### Studio UI Display Properties

These properties control how Studio's designer renders dropdown selections and drive name-based resolution. When generating XAML programmatically, always set them alongside their corresponding functional properties. They are marked `Browsable(false)` in the source code but are serialized in XAML by Studio.

| Property | Type | Role | Example Value |
|----------|------|------|---------------|
| `ProjectName` | `string` | **Drives resolution of `ProjectId`** — Studio looks up the project by this name and populates `ProjectId` with the GUID at design time. | `"Predefined"` |
| `ProjectVersionName` | `string` | Mirrors `ProjectTag` | `"Production"` |
| `ClassifierName` | `string` | Mirrors `ClassifierId` | `"ML Classification"` |

## Type Reference

### DocumentData

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification.DocumentData`
**Assembly:** `UiPath.IntelligentOCR.StudioWeb.Activities`
**XAML xmlns:** `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`

| Property | Type | Description |
|----------|------|-------------|
| `DocumentType` | `DocumentType` | The classified document type (see below). |
| `SubDocuments` | `IDocumentData[]` | Array of subdocuments when splitting is enabled. |
| `FileDetails` | `FileDetails` | File path, name, extension, and page range of the source document. |
| `DocumentMetadata` | `DocumentMetadata` | OCR text (`Text`), document object model (`DocumentObjectModel`), language, and extraction results as DataTables (`ResultsAsDataTables`). |

### DocumentType

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification.DocumentType`

| Property | Type | Description |
|----------|------|-------------|
| `DisplayName` | `string` | Human-readable label (e.g., `"Invoices"`). |
| `Id` | `string` | Machine identifier (e.g., `"invoices"`). Use this for programmatic comparisons and for passing to ExtractDocumentData's `DocType`. |
| `Confidence` | `float` | Classification confidence score (0.0 to 1.0). |
| `Name` | `string` | **Obsolete.** Use `Id` instead. |
| `Url` | `string` | Reference URL for the document type definition. |

**VB expression examples:**
- `classificationResults.DocumentType.Id` — returns `"invoices"`
- `classificationResults.DocumentType.DisplayName` — returns `"Invoices"`
- `classificationResults.DocumentType.Confidence` — returns confidence score

## Enum Reference

### Classifier Identifiers

| Identifier | Display Name | Description |
|------------|-------------|-------------|
| `ml-classification` | ML Classification | General-purpose multi-class classifier that distinguishes between all supported pretrained document types. **Recommended for most use cases.** |

### Pretrained Document Type Identifiers

These lowercase identifiers can be used as `ClassifierId` for single-type classification:

| Identifier | Display Name |
|------------|-------------|
| `invoices` | Invoices |
| `receipts` | Receipts |
| `id_cards` | ID Cards |
| `passports` | Passports |
| `purchase_orders` | Purchase Orders |
| `utility_bills` | Utility Bills |
| `remittance_advices` | Remittance Advices |
| `bills_of_lading` | Bills of Lading |
| `checks` | Checks |

## XAML Example

Classifies a document using the Predefined project with the ML Classification classifier. Replace `[inputFile]` with an `IResource` variable pointing to the document.

```xml
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
```

**Required variable declaration:**

```xml
<Variable x:TypeArguments="duc:DocumentData" Name="classificationResults" />
```

**Required XAML namespace prefixes:**

```xml
xmlns:du="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:duc="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"
```

**Required expression namespace imports:**

```xml
<TextExpression.NamespacesForImplementation>
  <scg:List x:TypeArguments="x:String">
    <x:String>UiPath.IntelligentOCR.StudioWeb.Activities</x:String>
    <x:String>UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification</x:String>
  </scg:List>
</TextExpression.NamespacesForImplementation>
<TextExpression.ReferencesForImplementation>
  <scg:List x:TypeArguments="AssemblyReference">
    <AssemblyReference>UiPath.IntelligentOCR.StudioWeb.Activities</AssemblyReference>
  </scg:List>
</TextExpression.ReferencesForImplementation>
```

## Notes

- `ProjectId` should be a GUID-formatted string at runtime (`Guid.Parse()` is used). The Predefined project GUID is `00000000-0000-0000-0000-000000000000`. For custom projects, Studio resolves `ProjectId` from `ProjectName` at design time — so if `ProjectName` is set to a valid project name, the GUID does not need to be known at authoring time.
- Properties backed by Studio dropdown widgets (`ProjectId`, `ProjectTag`, `ProjectVersionNumber`, `ClassifierId`) should be set as **literal attribute values** rather than VB/C# expressions (e.g., `ProjectId="00000000-..."` not `ProjectId="[&quot;00000000-...&quot;]"`) to ensure the dropdown displays correctly in the designer.
- For the Predefined project, the standard version configuration is: `ProjectTag="Production"`, `ProjectVersionNumber="0"`, `ProjectVersionName="Production"`.
- `ProjectVersionNumber` and `ProjectTag` are two ways to reference a project snapshot. Use one or the other. If neither is specified, the Staging version is used by default; if not available, the latest version is used.
- For custom DU projects, set `ClassifierId` to the **classifier name** from the project. Studio resolves the name to the internal GUID at design time. Set `ClassifierName` to the same value. Ask the user for the classifier name if not provided.
- The `ClassificationResults` output is of type `DocumentData` (namespace `UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification`). Access the classified type via `classificationResults.DocumentType.Id` (lowercase identifier like `"invoices"`) or `classificationResults.DocumentType.DisplayName` (human-readable like `"Invoices"`). Do **not** use `.ToString()` on `DocumentType` — it returns the CLR type name, not the classification label.
- `DocumentType.Name` is obsolete — use `DocumentType.Id` instead.
- `RuntimeAssetPath` and `RuntimeTenantUrl` enable cross-organization access. Both must be set together.
- In a typical pipeline, this is the first activity. Its `ClassificationResults` output (`DocumentData`) feeds into classification validation activities and/or directly into `ExtractDocumentDataWithDocumentData` as `FileInput` (`DocumentData` implements `IResource`).

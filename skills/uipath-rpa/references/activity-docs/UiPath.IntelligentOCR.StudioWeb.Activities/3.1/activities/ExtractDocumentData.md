# Extract Document Data

`UiPath.IntelligentOCR.StudioWeb.Activities.ExtractDocumentDataWithDocumentData`

Extracts data from a document and stores the results into automatically generated variables. Supports pretrained extractors for standard document types (invoices, receipts, id_cards, passports, purchase_orders, utility_bills, remittance_advices, bills_of_lading, checks) and custom DU project extractors.

**Package:** `UiPath.DocumentUnderstanding.Activities`
**Category:** Document Understanding

## References

- [Data Type Patterns](ExtractDocumentData/data-type-patterns.md) — DictionaryData API, type propagation rules, and pipeline variable declarations

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ProjectId` | Document Understanding project | InArgument | `string` | Yes | | The Document Understanding project ID. Should be a GUID-formatted string (parsed via `Guid.Parse()` at runtime). The Predefined project GUID is `"00000000-0000-0000-0000-000000000000"`. For custom projects, if the GUID is unknown, set `ProjectName` to the project's display name and use a non-GUID placeholder string for ProjectId (e.g., ProjectId="placeholder"). Do not use "00000000-0000-0000-0000-000000000000" — that is the Predefined project's real GUID and will be accepted as-is without triggering name-based resolution — **Studio resolves `ProjectId` from `ProjectName` at design time**. Set as a **literal attribute value** (not a VB expression). |
| `ProjectVersionNumber` | Version | InArgument | `int` | No | | The version number referencing a snapshot of the Document Understanding project. Use this **or** `ProjectTag` (not both). For the Predefined project, use `0`. |
| `ProjectTag` | Tag | InArgument | `string` | No | | An alternative to version number. A tag referencing a snapshot of the Document Understanding project. For the Predefined project, use `"Production"`. |
| `DocType` | Extractor | InArgument | `string` | Conditional | | The extractor identifier (**lowercase**). Required unless `ModernDocumentTypeId="use_classification_result"` is used (in which case set `DocType="{x:Null}"`). Pretrained values (Predefined project only): `invoices`, `receipts`, `id_cards`, `passports`, `purchase_orders`, `utility_bills`, `remittance_advices`, `bills_of_lading`, `checks`. For custom DU projects: use the **document type name** as it appears in the project (e.g., `"invoices"`) — ask the user for this name if not provided (they can find it in the project's Document Types tab). Studio resolves it to the correct extractor at design time. Alternatively, use the extractor GUID if known. See Enum Reference. |
| `ModernDocumentTypeId` | Document type | InArgument | `string` | Conditional | | The document type ID defining the fields to extract. Required unless `DocType` is set (both can be set together). **For pretrained extractors, use the same lowercase identifier as `DocType`** (e.g., `"invoices"`, `"receipts"`). For custom DU projects, use the **document type name** from the project's Document Types tab (e.g., `"invoices"`) — ask the user for this name if not provided. Studio resolves the name to the internal GUID at design time. The GUID can also be used directly if known. Set to `"use_classification_result"` to dynamically resolve the document type from the upstream ClassifyDocument result (requires `FileInput` to be a `DocumentData`; set `DocType="{x:Null}"` when using this). Together with `DocType`, these two properties fully specify the extraction target. |
| `FileInput` | Input | InArgument | `IResource` | Yes | | Document Data referencing the digitized input file, or the input file itself if Document Data has not been created yet. Accepts a `DocumentData` object from ClassifyDocument directly. |
| `TimeoutInSeconds` | Timeout (seconds) | InArgument | `int` | Yes | `3600` | Maximum execution time in seconds. If exceeded, the operation is terminated. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ApplyAutoValidation` | Auto-validation | `bool` | `false` | Whether to apply automatic validation based on configurations provided as input or at the Document Understanding project level. |
| `AutoValidationConfidenceThreshold` | Confidence threshold | `int?` | `0` | Extraction results below this confidence threshold are auto-validated when `ApplyAutoValidation` is enabled. |
| `GenerateData` | Generate data type | `bool` | `false` | When `true`, generates a strongly-typed output with fields available under the `Data` property. When `false`, fields are retrieved via method calls by ID (using `DictionaryData`). **Agents should always set this to `False`** — `True` requires Studio's design-time JIT compilation which agents cannot trigger. Also, `GenerateData=True` is incompatible with `ModernDocumentTypeId="use_classification_result"`. See Type Reference for details. |
| `ActivityMajorVersion` | Activity major version | `int` | | Internal version flag. **Always set `ActivityMajorVersion="2"`** in generated XAML. If omitted or set to a value less than `2`, Studio displays a migration warning banner ("The activity has been updated to a new major version…") that requires manual acknowledgement. Setting this to `2` suppresses the warning. |
| `RuntimeAssetPath` | Runtime Credentials Asset | `string` | | Orchestrator credentials asset path for cross-org authentication. Format: `<orchestratorFolder>/<assetName>`. |
| `RuntimeTenantUrl` | Runtime Tenant Url | `string` | | URL to an external tenant for cross-org authentication. Format: `https://<base_url>/<organization>/<tenant>`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `ExtractionResults` | Document data | OutArgument | `IDocumentData<ExtendedExtractionResultsForDocumentData>` | Extracted data in a (field-name, field-value) format. For example: ('invoice-date', '01/04/2022'). See Type Reference below. |

### Studio UI Display Properties

These properties control how Studio's designer renders dropdown selections and drive name-based resolution. When generating XAML programmatically, always set them alongside their corresponding functional properties. They are marked `Browsable(false)` in the source code but are serialized in XAML by Studio.

| Property | Type | Role | Example Value (for `invoices` extractor) |
|----------|------|------|------------------------------------------|
| `ProjectName` | `string` | **Drives resolution of `ProjectId`** — Studio looks up the project by this name and populates `ProjectId` with the GUID at design time. | `"Predefined"` |
| `ProjectVersionName` | `string` | Mirrors `ProjectTag` | `"Production"` |
| `ExtractorName` | `string` | Mirrors `DocType` | `"Invoices"` (capitalized display name) |
| `ModernDocumentTypeName` | `string` | Mirrors `ModernDocumentTypeId` | `"Invoices"` (capitalized display name) |

## Type Reference

### IDocumentData\<T\>

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction.IDocumentData<T>`
**Assembly:** `UiPath.IntelligentOCR.StudioWeb.Activities`
**XAML xmlns:** `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`

The output `ExtractionResults` implements `IDocumentData<T>` where `T` is `ExtendedExtractionResultsForDocumentData` (or a Studio-generated subclass when `GenerateData=True`).

| Property | Type | Description |
|----------|------|-------------|
| `Data` | `T` | Strongly-typed extraction results (available when `GenerateData=True`). |
| `DocumentType` | `DocumentType` | The document type used for extraction. |
| `SubDocuments` | `IDocumentData[]` | Subdocuments (if splitting occurred upstream). |
| `FileDetails` | `FileDetails` | File path, name, extension, and page range. |
| `DocumentMetadata` | `DocumentMetadata` | OCR text (`Text`), DOM (`DocumentObjectModel`), and `ResultsAsDataTables` for tabular export. |

### ExtendedExtractionResultsForDocumentData

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction.ExtendedExtractionResultsForDocumentData`
**XAML xmlns:** `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`

Base type argument for the generic activity. When `GenerateData=True`, Studio generates a type-specific subclass at design time with strongly-typed properties for each extracted field, accessible via `ExtractionResults.Data`. The generated subclass has a dynamic assembly name and namespace — this is normal and handled automatically by Studio.

### DictionaryData

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction.DictionaryData`
**XAML xmlns:** `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities` (prefix `dux`)

Extends `ExtendedExtractionResultsForDocumentData`. Provides methods to access extracted fields and tables by name or ID without requiring Studio's design-time code generation. **Recommended type argument for agent-generated workflows** when `GenerateData=False`.

Key methods: `GetField(string)`, `GetFieldValue(string)`, `GetTable(string)`, `GetFields()`, `GetTables()`. See [Data Type Patterns](ExtractDocumentData/data-type-patterns.md) for the full API reference.

## Enum Reference

### Pretrained Extractor Identifiers (DocType and ModernDocumentTypeId values)

Use these **lowercase** identifiers for both `DocType` and `ModernDocumentTypeId`. Do not use the capitalized display names for these properties (use capitalized names only for the display properties `ExtractorName` and `ModernDocumentTypeName`).

| Identifier (DocType & ModernDocumentTypeId) | Display Name (ExtractorName & ModernDocumentTypeName) |
|---------------------------------------------|------------------------------------------------------|
| `invoices` | `Invoices` |
| `receipts` | `Receipts` |
| `id_cards` | `ID Cards` |
| `passports` | `Passports` |
| `purchase_orders` | `Purchase Orders` |
| `utility_bills` | `Utility Bills` |
| `remittance_advices` | `Remittance Advices` |
| `bills_of_lading` | `Bills of Lading` |
| `checks` | `Checks` |

**Special ModernDocumentTypeId values:**
- `use_classification_result` — Dynamically resolves the document type from the upstream ClassifyDocument result. When using this value, set `DocType="{x:Null}"` and pass a `DocumentData` from ClassifyDocument as `FileInput`. The activity determines the extractor and document type from the classification output at runtime. Works with both Predefined and custom DU projects. **Cannot be used with `GenerateData=True`.**

**Custom DU project values:**
When targeting a custom DU project (not Predefined), set `DocType` to the document type name from the project's Document Types tab (e.g., `"invoices"`). Ask the user for this name if not provided. Studio resolves the name to the correct extractor at design time. The predefined identifiers listed above only work with the Predefined project (`ProjectId="00000000-0000-0000-0000-000000000000"`). For custom projects, the document type names are project-specific.

## XAML Example

Extracts invoice data using the Predefined project with a pretrained extractor. Replace `[inputFile]` with an `IResource` variable pointing to the document (or a `DocumentData` from ClassifyDocument).

```xml
<du:ExtractDocumentDataWithDocumentData
    x:TypeArguments="dux:ExtendedExtractionResultsForDocumentData"
    DisplayName="Extract Document Data"
    ActivityMajorVersion="2"
    ProjectId="00000000-0000-0000-0000-000000000000"
    ProjectName="Predefined"
    ProjectTag="Production"
    ProjectVersionName="Production"
    ProjectVersionNumber="0"
    DocType="[&quot;invoices&quot;]"
    ExtractorName="Invoices"
    ModernDocumentTypeId="invoices"
    ModernDocumentTypeName="Invoices"
    FileInput="[inputFile]"
    TimeoutInSeconds="[3600]"
    ExtractionResults="[extractionResults]">
  <du:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
    <scg:Dictionary x:TypeArguments="x:String, InArgument(x:String)" />
  </du:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
</du:ExtractDocumentDataWithDocumentData>
```

**Required variable declaration:**

```xml
<Variable x:TypeArguments="dux:IDocumentData(dux:ExtendedExtractionResultsForDocumentData)" Name="extractionResults" />
```

### DictionaryData Variant

When generating workflows programmatically, use `DictionaryData` as the type argument. This provides field access methods without requiring Studio's JIT code generation:

```xml
<du:ExtractDocumentDataWithDocumentData
    x:TypeArguments="dux:DictionaryData"
    DisplayName="Extract Document Data"
    ActivityMajorVersion="2"
    ProjectId="00000000-0000-0000-0000-000000000000"
    ProjectName="Predefined"
    ProjectTag="Production"
    ProjectVersionName="Production"
    ProjectVersionNumber="0"
    DocType="[&quot;invoices&quot;]"
    ExtractorName="Invoices"
    ModernDocumentTypeId="invoices"
    ModernDocumentTypeName="Invoices"
    FileInput="[inputFile]"
    TimeoutInSeconds="[3600]"
    ExtractionResults="[extractionResults]">
  <du:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
    <scg:Dictionary x:TypeArguments="x:String, InArgument(x:String)" />
  </du:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
</du:ExtractDocumentDataWithDocumentData>
```

**Required variable declaration:**

```xml
<Variable x:TypeArguments="dux:IDocumentData(dux:DictionaryData)" Name="extractionResults" />
```

### Custom DU Project Variant

When targeting a custom DU project, use the document type name from the project for both `DocType` and `ModernDocumentTypeId`. Studio resolves these to the correct internal identifiers at design time. `ProjectId` must still be a GUID.

```xml
<du:ExtractDocumentDataWithDocumentData
    x:TypeArguments="dux:DictionaryData"
    DisplayName="Extract Document Data"
    ActivityMajorVersion="2"
    ProjectId="{your-project-guid}"
    ProjectName="{Your Project Name}"
    ProjectTag="{your-version-tag}"
    ProjectVersionName="{your-version-tag}"
    ProjectVersionNumber="{version-number}"
    DocType="invoices"
    ExtractorName="invoices"
    ModernDocumentTypeId="invoices"
    ModernDocumentTypeName="invoices"
    FileInput="[inputFile]"
    TimeoutInSeconds="[3600]"
    GenerateData="False"
    ExtractionResults="[extractionResults]">
  <du:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
    <scg:Dictionary x:TypeArguments="x:String, InArgument(x:String)" />
  </du:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
</du:ExtractDocumentDataWithDocumentData>
```

After opening the workflow in Studio, the designer resolves `ModernDocumentTypeId` from the name to the project-specific GUID. The `DocType` name is also validated against the project's registered extractors.

**Required XAML namespace prefixes:**

```xml
xmlns:du="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:dux="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"
```

**Required expression namespace imports:**

```xml
<TextExpression.NamespacesForImplementation>
  <scg:List x:TypeArguments="x:String">
    <x:String>UiPath.IntelligentOCR.StudioWeb.Activities</x:String>
    <x:String>UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction</x:String>
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

- This is a generic activity. In XAML, use `x:TypeArguments="dux:ExtendedExtractionResultsForDocumentData"` (from namespace `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction`, prefix `dux`).
- `ProjectId` should be a GUID-formatted string at runtime (`Guid.Parse()` is used). The Predefined project GUID is `00000000-0000-0000-0000-000000000000`. For custom projects, Studio resolves `ProjectId` from `ProjectName` at design time — so if `ProjectName` is set to a valid project name, the GUID does not need to be known at authoring time. When `ProjectTag` is set, `ProjectVersionNumber` is also auto-resolved by Studio — agents can set `ProjectVersionNumber="0"` as a placeholder.
- Properties backed by Studio dropdown widgets (`ProjectId`, `ProjectTag`, `ProjectVersionNumber`) should be set as **literal attribute values** rather than VB/C# expressions to ensure the dropdown displays correctly in the designer.
- For the Predefined project, the standard version configuration is: `ProjectTag="Production"`, `ProjectVersionNumber="0"`, `ProjectVersionName="Production"`.
- `ProjectVersionNumber` and `ProjectTag` are alternatives. Use one or the other.
- `DocType` values are **lowercase identifiers**. For the Predefined project, use predefined names (e.g., `invoices`). For custom DU projects, use the document type name as it appears in the project (e.g., `"invoices"` if the project defines a document type named "invoices") — ask the user for this name if not provided (found in the project's Document Types tab). Studio resolves names to the correct extractor at design time.
- `ModernDocumentTypeId` uses the **same lowercase identifier** as `DocType` for pretrained extractors (e.g., both are `"invoices"`). For custom DU projects, use the document type name — Studio resolves it to the internal GUID at design time. The GUID can also be used directly if known.
- The legacy `ExtractorDocumentType` property does **not** exist on this activity. Use `DocType` (extractor identifier) and `ModernDocumentTypeId` (document type definition) instead.
- **Always set `ActivityMajorVersion="2"`** in generated XAML. Without this, Studio shows a migration warning banner ("The activity has been updated to a new major version…") that requires manual acknowledgement before the activity can be used.
- **Agents should always set `GenerateData="False"`.** `GenerateData=True` requires Studio's design-time JIT compilation which agents cannot trigger, and is incompatible with `ModernDocumentTypeId="use_classification_result"`.
- When `GenerateData=True`, Studio generates a type-specific assembly at design time, producing a subclass of `ExtendedExtractionResultsForDocumentData` with typed field properties accessible via `ExtractionResults.Data`. The generated type has a dynamic assembly name — this is expected behavior.
- `RuntimeAssetPath` and `RuntimeTenantUrl` enable cross-organization access. Both must be set together.
- The type argument chosen for this activity (`ExtendedExtractionResultsForDocumentData`, `DictionaryData`, or a generated type) **must be used consistently** across all downstream validation activities (`CreateValidationAction<T>`, `WaitForValidationAction<T>`, `ValidateDocumentDataWithDocumentData<T>`, `CreateDocumentValidationArtifacts<T>`). Mismatched type arguments cause runtime errors. See [Data Type Patterns](ExtractDocumentData/data-type-patterns.md) for details.

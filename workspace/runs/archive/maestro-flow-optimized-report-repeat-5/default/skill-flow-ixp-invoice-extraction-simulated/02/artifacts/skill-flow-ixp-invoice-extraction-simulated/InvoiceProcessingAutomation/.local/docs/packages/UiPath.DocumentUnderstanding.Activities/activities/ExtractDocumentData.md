# Extract Document Data

`UiPath.IntelligentOCR.StudioWeb.Activities.ExtractDocumentDataWithDocumentData`

**XAML element:** `<du:ExtractDocumentDataWithDocumentData x:TypeArguments="dux:DictionaryData" …>` *(generic — `x:TypeArguments` is required; `dux:DictionaryData` for agent-generated workflows)*
**xmlns prefixes:** `du` → `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities;assembly=UiPath.IntelligentOCR.StudioWeb.Activities` (the activity itself), `dux` → `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities` (the type argument)
**Pairs with:** `FileInput` accepts a `DocumentData` from `ClassifyDocument` (or its validated form) directly. Output `ExtractionResults` (`IDocumentData<T>`) feeds `CreateValidationAction<T>` / `ValidateDocumentDataWithDocumentData<T>` / `CreateDocumentValidationArtifacts<T>` for validation, **or** is read in-place via `extractionResults.Data.GetFieldValue("…")` / `…Data.Handler.GetTableValue("…")` — see [Reading Extraction Results](../overview.md#reading-extraction-results).

Extracts data from a document and stores the results into automatically generated variables. Supports pretrained extractors for standard document types (invoices, receipts, id_cards, passports, purchase_orders, utility_bills, remittance_advices, bills_of_lading, checks) and custom DU project extractors.

**Package:** `UiPath.DocumentUnderstanding.Activities`
**Category:** Document Understanding

## References

- [Data Type Patterns](ExtractDocumentData/data-type-patterns.md) — DictionaryData API, type propagation rules, and pipeline variable declarations
- [`ExtractionResult`](../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResult.md) — underlying contract behind `IDocumentData<DictionaryData>`. Read this for the `ResultsDocument` / `ResultsDataPoint` / `ResultsValue` shape, the five supported field shapes (basic / table / field-group / one-level nested), and built-in helpers (`AsClassificationResult`, `AsDataSet`, `IsAnyFieldOrTableCellMissing`).
- [`ExtractionResultHandler`](../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResultHandler.md) — the recommended fluent navigator. Reach it via `extractionResults.Data.Handler`.
- [`Document`](../../UiPath.DocumentProcessing.Contracts/classes/Document.md) — DOM that `ResultsValue.Reference` points into; available as `ExtractionResults.DocumentMetadata.DocumentObjectModel`.
- [`DocumentTaxonomy`](../../UiPath.DocumentProcessing.Contracts/classes/Taxonomy.md) — required when calling `Handler.GetTable(...).InitializeIfMissing(field)`, `TableValue.AddEmptyRow(field)`, or `FieldGroupDataPoint.AddEmptyValue(field)` to populate complex fields from a taxonomy definition.

Cross-package links resolve at agent runtime once `PackageDocsSync` extracts the contracts package alongside this one under `.local/docs/packages/`.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ProjectId` | Document Understanding project | InArgument | `string` | Yes | | The Document Understanding project ID. Should be a GUID-formatted string (parsed via `Guid.Parse()` at runtime). The Predefined project GUID is `"00000000-0000-0000-0000-000000000000"`. For custom projects, if the GUID is unknown, set `ProjectName` to the project's display name and use a non-GUID placeholder string for ProjectId (e.g., ProjectId="placeholder"). Do not use "00000000-0000-0000-0000-000000000000" — that is the Predefined project's real GUID and will be accepted as-is without triggering name-based resolution — **Studio resolves `ProjectId` from `ProjectName` at design time**. Set as a **literal attribute value** (not a VB expression). |
| `ProjectVersionNumber` | Version | InArgument | `int` | No | | The version number referencing a snapshot of the Document Understanding project. Use this **or** `ProjectTag` (not both). For the Predefined project, use `0`. |
| `ProjectTag` | Tag | InArgument | `string` | No | | An alternative to version number. A tag referencing a snapshot of the Document Understanding project. For the Predefined project, use `"Production"`. |
| `DocType` | Extractor | InArgument | `string` | Conditional | | The extractor identifier. **Casing depends on project shape: lowercase for Predefined / DU.Apps, title-cased `"Default"` for IXP.** Required unless `ModernDocumentTypeId="use_classification_result"` is used (in which case set `DocType="{x:Null}"`). Pretrained values (Predefined project only): `invoices`, `receipts`, `id_cards`, `passports`, `purchase_orders`, `utility_bills`, `remittance_advices`, `bills_of_lading`, `checks`. For custom DU.Apps projects: use the **document type name** as it appears in the project (e.g., `"invoices"`) — ask the user for this name if not provided (they can find it in the project's Document Types tab). Studio resolves it to the correct extractor at design time. **For IXP projects, which do not have a document-type concept (a single extractor per version), always use `DocType="Default"`** — this is the value Studio's designer auto-fills for the IXP "Document Type" dropdown. Do not ask the user for a document-type name when the project is IXP, and do not leave `DocType` empty. Alternatively, use the extractor GUID if known. See Enum Reference. |
| `ModernDocumentTypeId` | Document type | InArgument | `string` | Conditional | | The document type ID defining the fields to extract. **Use the same identifier as `DocType`** — lowercase for Predefined / DU.Apps, title-cased `"Default"` for IXP. Required unless `DocType` is set (both can be set together). For pretrained extractors, use the same lowercase identifier as `DocType` (e.g., `"invoices"`, `"receipts"`). For custom DU.Apps projects, use the **document type name** from the project's Document Types tab (e.g., `"invoices"`) — ask the user for this name if not provided. Studio resolves the name to the internal GUID at design time. The GUID can also be used directly if known. **For IXP projects, use `"Default"` (matching `DocType`)** — IXP projects have no document-type concept, so the designer auto-fills `"Default"` as a sentinel that the runtime resolves to the project's single extractor. Set to `"use_classification_result"` to dynamically resolve the document type from the upstream ClassifyDocument result (requires `FileInput` to be a `DocumentData`; set `DocType="{x:Null}"` when using this). Together with `DocType`, these two properties fully specify the extraction target. |
| `FileInput` | Input | InArgument | `IResource` | Yes | | Document Data referencing the digitized input file, or the input file itself if Document Data has not been created yet. Accepts a `DocumentData` object from ClassifyDocument directly. |
| `TimeoutInSeconds` | Timeout (seconds) | InArgument | `int` | Yes | `3600` | Maximum execution time in seconds. If exceeded, the operation is terminated. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ApplyAutoValidation` | Auto-validation | `bool` | `false` | Whether to apply automatic validation based on configurations provided as input or at the Document Understanding project level. |
| `AutoValidationConfidenceThreshold` | Confidence threshold | `int?` | `0` | Extraction results below this confidence threshold are auto-validated when `ApplyAutoValidation` is enabled. |
| `GenerateData` | Generate data type | `bool` | `false` | When `true`, generates a strongly-typed output with fields available under the `Data` property. When `false`, fields are retrieved via method calls by ID (using `DictionaryData`). **Agents should always set this to `False`** — `True` requires Studio's design-time JIT compilation which agents cannot trigger. Also, `GenerateData=True` is incompatible with `ModernDocumentTypeId="use_classification_result"`. See Type Reference for details. |
| `ActivityMajorVersion` | Activity major version | `int` | | Internal version flag. **Always set `ActivityMajorVersion="2"`** in generated XAML. If omitted or set to a value less than `2`, Studio displays a migration warning banner ("The activity has been updated to a new major version…") that requires manual acknowledgement. Setting this to `2` suppresses the warning. |
| `RuntimeAssetPath` | Credentials Asset | `string` | | Orchestrator credentials asset path used to authenticate against the Document Understanding tenant. Format: `<orchestratorFolder>/<assetName>`. |
| `RuntimeTenantUrl` | Tenant URL | `string` | | URL of the tenant used to authenticate against the Document Understanding service. Format: `https://<base_url>/<organization>/<tenant>`. |

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

**Special DocType / ModernDocumentTypeId values:**
- `use_classification_result` — Dynamically resolves the document type from the upstream ClassifyDocument result. When using this value, set `DocType="{x:Null}"` and pass a `DocumentData` from ClassifyDocument as `FileInput`. The activity determines the extractor and document type from the classification output at runtime. Works with both Predefined and custom DU projects. **Cannot be used with `GenerateData=True`.**
- `Default` — Use **for IXP projects only**. IXP projects have a single extractor per version and do not expose document types, so the designer's "Document Type" dropdown auto-fills `"Default"` as a sentinel. The runtime resolves it to the project's single extractor for the selected version. Set `DocType`, `ExtractorName`, `ModernDocumentTypeId`, and `ModernDocumentTypeName` all to `"Default"`. Do **not** use `"Default"` for Predefined or DU.Apps projects — those have real document-type names and the sentinel would not resolve.

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

### IXP Project Variant

IXP projects have a **single extractor per version** and no document-type concept. The designer auto-fills the "Document Type" dropdown with `"Default"`; the runtime resolves it to that single extractor. **Always use `"Default"` for `DocType`, `ExtractorName`, `ModernDocumentTypeId`, and `ModernDocumentTypeName`** when the user's project is IXP — do not ask them for a document-type name, and do not leave these properties unset.

```xml
<du:ExtractDocumentDataWithDocumentData
    x:TypeArguments="dux:DictionaryData"
    DisplayName="Extract Document Data"
    ActivityMajorVersion="2"
    ProjectId="placeholder"
    ProjectName="{Your IXP Project Name}"
    ProjectTag="{your-version-tag}"
    ProjectVersionName="{your-version-tag}"
    ProjectVersionNumber="0"
    DocType="Default"
    ExtractorName="Default"
    ModernDocumentTypeId="Default"
    ModernDocumentTypeName="Default"
    FileInput="[inputFile]"
    TimeoutInSeconds="[3600]"
    GenerateData="False"
    ExtractionResults="[extractionResults]">
  <du:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
    <scg:Dictionary x:TypeArguments="x:String, InArgument(x:String)" />
  </du:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
</du:ExtractDocumentDataWithDocumentData>
```

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

## Cross-org authentication

This activity can authenticate against an external Document Understanding tenant via an Orchestrator credential asset. The same `Credentials Asset` value is used at both design time (to populate the Project / Version / Document Type dropdowns from the external tenant) and runtime (to acquire the access token when the activity executes).

### Design-time UX

To author an `ExtractDocumentDataWithDocumentData` activity that authenticates against an external Document Understanding tenant:

1. Set **Credentials Asset** (`RuntimeAssetPath`) to the Orchestrator credential asset path. Format: `<orchestratorFolder>/<assetName>`.
2. Set **Tenant URL** (`RuntimeTenantUrl`) to the external tenant URL. Format: `https://<base_url>/<organization>/<tenant>`.
3. Click **Connect**. StudioWeb resolves the asset's username/password via Orchestrator and authenticates against the external tenant. The Project / Version / Document Type dropdowns then populate from the external tenant.

### Variable expressions block Connect

If **Credentials Asset** or **Tenant URL** contains a variable expression (for example `In_AssetPath`), clicking **Connect** surfaces this error and the connection is not attempted:

```text
The Connect button needs the actual asset path and tenant URL — variable expressions only resolve when running the workflow.
```

This design-time check is intentional: variables are only resolved at runtime, so the editor cannot use them to authenticate. To work with cross-org authentication where the asset path or tenant URL is dynamic, set literal values during authoring and rely on the runtime path to honor the variable substitution at execution time.

### Disconnect

Clicking **Connect** a second time disconnects from the external tenant. The Project dropdown stays visible but is cleared; clicking **Connect** again with valid literals reconnects.

### Note on previous versions

Earlier StudioWeb releases required separate `DesigntimeAppId`, `DesigntimeAppSecret`, and `DesigntimeTenantUrl` fields at design time. Those fields have been removed; the same **Credentials Asset** now feeds both design time and runtime. Existing customer workflows (`.xaml`) continue to load unchanged because the underlying property names (`RuntimeAssetPath`, `RuntimeTenantUrl`) are preserved.

## Notes

- This is a generic activity. In XAML, use `x:TypeArguments="dux:ExtendedExtractionResultsForDocumentData"` (from namespace `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction`, prefix `dux`).
- `ProjectId` should be a GUID-formatted string at runtime (`Guid.Parse()` is used). The Predefined project GUID is `00000000-0000-0000-0000-000000000000`. For custom projects, Studio resolves `ProjectId` from `ProjectName` at design time — so if `ProjectName` is set to a valid project name, the GUID does not need to be known at authoring time. When `ProjectTag` is set, `ProjectVersionNumber` is also auto-resolved by Studio — agents can set `ProjectVersionNumber="0"` as a placeholder.
- Properties backed by Studio dropdown widgets (`ProjectId`, `ProjectTag`, `ProjectVersionNumber`) should be set as **literal attribute values** rather than VB/C# expressions to ensure the dropdown displays correctly in the designer.
- For the Predefined project, the standard version configuration is: `ProjectTag="Production"`, `ProjectVersionNumber="0"`, `ProjectVersionName="Production"`.
- `ProjectVersionNumber` and `ProjectTag` are alternatives. Use one or the other.
- `DocType` values are **lowercase identifiers for Predefined and DU.Apps projects** (e.g., `"invoices"`, `"receipts"`). For the Predefined project, use the pretrained extractor name. For custom DU.Apps projects, use the document type name as it appears in the project — ask the user for this name if not provided (found in the project's Document Types tab); Studio resolves names to the correct extractor at design time. **IXP projects are the one exception** — they have no document-type concept and require the title-cased sentinel `"Default"` instead (see the dedicated IXP bullet below).
- `ModernDocumentTypeId` uses the **same identifier as `DocType`** — lowercase for Predefined and DU.Apps projects (e.g., both are `"invoices"`); the title-cased `"Default"` sentinel for IXP projects. For DU.Apps projects, Studio resolves the document type name to the internal GUID at design time. The GUID can also be used directly if known.
- **IXP projects: always use `"Default"` for `DocType` / `ExtractorName` / `ModernDocumentTypeId` / `ModernDocumentTypeName`.** IXP projects have a single extractor per version and no document-type concept, so the designer auto-fills `"Default"` as the dropdown value; the runtime resolves it to the project's single extractor. Do not ask the user for a document-type name when the project is IXP, do not leave these properties unset, and do not invent a name based on the file content. The `"Default"` sentinel is exclusive to IXP projects — using it on a Predefined or DU.Apps project will fail to resolve. See the [IXP Project Variant](#ixp-project-variant) XAML example.
- The legacy `ExtractorDocumentType` property does **not** exist on this activity. Use `DocType` (extractor identifier) and `ModernDocumentTypeId` (document type definition) instead.
- **Always set `ActivityMajorVersion="2"`** in generated XAML. Without this, Studio shows a migration warning banner ("The activity has been updated to a new major version…") that requires manual acknowledgement before the activity can be used.
- **Agents should always set `GenerateData="False"`.** `GenerateData=True` requires Studio's design-time JIT compilation which agents cannot trigger, and is incompatible with `ModernDocumentTypeId="use_classification_result"`.
- When `GenerateData=True`, Studio generates a type-specific assembly at design time, producing a subclass of `ExtendedExtractionResultsForDocumentData` with typed field properties accessible via `ExtractionResults.Data`. The generated type has a dynamic assembly name — this is expected behavior.
- `RuntimeAssetPath` and `RuntimeTenantUrl` enable cross-organization access. Both must be set together. See [Cross-org authentication](#cross-org-authentication) for the design-time flow and the variable-expression hard-error.
- The type argument chosen for this activity (`ExtendedExtractionResultsForDocumentData`, `DictionaryData`, or a generated type) **must be used consistently** across all downstream validation activities (`CreateValidationAction<T>`, `WaitForValidationAction<T>`, `ValidateDocumentDataWithDocumentData<T>`, `CreateDocumentValidationArtifacts<T>`). Mismatched type arguments cause runtime errors. See [Data Type Patterns](ExtractDocumentData/data-type-patterns.md) for details.

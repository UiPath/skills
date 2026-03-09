# XAML Document Understanding Activities (Non-PDF)

Document Understanding (DU) classify/extract/validate pipeline activities for `UiPath.DocumentUnderstanding.Activities`. Use for image and scanned-document inputs (not PDF utilities — see `pdf-document-understanding.md` for PDF utility activities). Always get full XAML from `uipcli rpa get-default-activity-xaml` — this file covers confirmed patterns from real workflows only.

## Package

`UiPath.DocumentUnderstanding.Activities`

## Variable Types

| Type | Namespace prefix | When used |
|------|-----------------|-----------|
| `uisad1:DocumentData` | `uisad1:` | Output of `ClassifyDocument`; contains `DocumentType.DisplayName` and `DocumentType.Confidence` |
| `uisad2:IDocumentData(T)` | `uisad2:` | Output of `ExtractDocumentDataWithDocumentData`; generic extraction result typed to bundle |
| `uisad:CreatedValidationAction(T)` | `uisad:` | Output of `CreateValidationAction` (async create-only variant) |

## File Input Pattern

All DU pipeline activities accept a document file via `IResource`:

```xml
FileInput="[LocalResource.FromPath(filePath)]"
```

Where `filePath` is a `String` variable containing the local file path. You can also pass the `Resource` output of a `PathExists` activity directly.

## DU Pipeline Activities

The standard pipeline: **Classify → Extract → Validate**

### ClassifyDocument — ML Classifier

Classifies a document using a trained ML classification model.

```xml
<p:ClassifyDocument
    ApiKey="{x:Null}"
    ClassifierResult="{x:Null}"
    ClassifierId="ml-classification"
    ClassificationResults="[DocumentData]"
    DisplayName="Classify Document"
    Endpoint="[&quot;https://cloud.uipath.com/orgname/tenantname/du_/api/framework/projects/00000000-0000-0000-0000-000000000000/classifiers/ml-classification/classification/&quot;]"
    FileInput="[LocalResource.FromPath(filePath)]"
    MinimumConfidence="50"
    ProjectId="[&quot;00000000-0000-0000-0000-000000000000&quot;]"
    TimeoutInSeconds="3600">
  <p:ClassifyDocument.GptPromptWithVariables>
    <scg:Dictionary x:TypeArguments="x:String, InArgument(x:String)" />
  </p:ClassifyDocument.GptPromptWithVariables>
</p:ClassifyDocument>
```

Key notes:
- `ClassificationResults` — output variable of type `uisad1:DocumentData`
- `MinimumConfidence` — integer 0–100 (not a float)
- `ProjectId` — use placeholder `"00000000-0000-0000-0000-000000000000"`; user must replace
- `Endpoint` — full DU API URL; user must replace with actual tenant/project URL
- `GptPromptWithVariables` child — empty `scg:Dictionary` for ML classifier
- Many null attributes are required: `ApiKey="{x:Null}"`, `ClassifierResult="{x:Null}"`

### ClassifyDocument — Generative Classifier

Classifies using an LLM with per-type prompts.

```xml
<p:ClassifyDocument
    ApiKey="{x:Null}"
    ClassifierResult="{x:Null}"
    ClassifierId="generative_classifier"
    ClassificationResults="[DocumentData]"
    DisplayName="Classify Document (Generative)"
    Endpoint="{x:Null}"
    FileInput="[LocalResource.FromPath(filePath)]"
    MinimumConfidence="50"
    ProjectId="{x:Null}"
    TimeoutInSeconds="3600">
  <p:ClassifyDocument.GptPromptWithVariables>
    <InArgument x:TypeArguments="x:String" x:Key="Receipt">Is this a Receipt?</InArgument>
    <InArgument x:TypeArguments="x:String" x:Key="Invoice">Is this an Invoice?</InArgument>
  </p:ClassifyDocument.GptPromptWithVariables>
</p:ClassifyDocument>
```

Key notes:
- `ClassifierId="generative_classifier"` — fixed value for generative
- `Endpoint="{x:Null}"` and `ProjectId="{x:Null}"` — not needed for generative
- `GptPromptWithVariables` — one `InArgument` per document type; `x:Key` is the type name, value is the classification prompt

### ExtractDocumentDataWithDocumentData — ML Extractor

Extracts structured data using a trained ML extraction model for a predefined DocType.

```xml
<p:ExtractDocumentDataWithDocumentData
    x:TypeArguments="uisaseib:Invoices"
    ApiKey="{x:Null}"
    DisplayName="Extract Document Data"
    DocType="invoices"
    ExtractionResults="[DocumentExtractedData]"
    FileInput="[LocalResource.FromPath(filePath)]"
    GenerateData="False"
    ProjectId="[&quot;00000000-0000-0000-0000-000000000000&quot;]"
    TimeoutInSeconds="3600">
  <p:ExtractDocumentDataWithDocumentData.AutoValidationConfidenceThreshold>
    <InArgument x:TypeArguments="s:Nullable(x:Int32)">
      <Literal x:TypeArguments="s:Nullable(x:Int32)" Value="0" />
    </InArgument>
  </p:ExtractDocumentDataWithDocumentData.AutoValidationConfidenceThreshold>
  <p:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
    <scg:Dictionary x:TypeArguments="x:String, InArgument(x:String)" />
  </p:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
</p:ExtractDocumentDataWithDocumentData>
```

Key notes:
- `x:TypeArguments` — the specific bundle type for the DocType (e.g., `uisaseib:Invoices` for invoices). Use `x:Object` when the exact bundle type is not known at design time.
- `ExtractionResults` — output variable typed `uisad2:IDocumentData(Of uisaseib:Invoices)` (or `x:Object` if type unknown)
- `AutoValidationConfidenceThreshold` — set via child element as `Nullable(Int32)`, not as an attribute
- `GptPromptWithVariables` child — empty `scg:Dictionary` for ML extractor
- `ProjectId` — placeholder; user must replace

### ExtractDocumentDataWithDocumentData — Generative Extractor

Extracts fields using an LLM with per-field prompts.

```xml
<p:ExtractDocumentDataWithDocumentData
    x:TypeArguments="x:Object"
    ApiKey="{x:Null}"
    DisplayName="Extract Document Data (Generative)"
    DocType="generative_extractor"
    ExtractionResults="[DocumentExtractedData]"
    FileInput="[LocalResource.FromPath(filePath)]"
    GenerateData="True"
    ProjectId="[&quot;00000000-0000-0000-0000-000000000000&quot;]"
    TimeoutInSeconds="3600">
  <p:ExtractDocumentDataWithDocumentData.AutoValidationConfidenceThreshold>
    <InArgument x:TypeArguments="s:Nullable(x:Int32)">
      <Literal x:TypeArguments="s:Nullable(x:Int32)" Value="0" />
    </InArgument>
  </p:ExtractDocumentDataWithDocumentData.AutoValidationConfidenceThreshold>
  <p:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
    <InArgument x:TypeArguments="x:String" x:Key="Total">Extract the total amount</InArgument>
    <InArgument x:TypeArguments="x:String" x:Key="Date">Extract the document date</InArgument>
  </p:ExtractDocumentDataWithDocumentData.GptPromptWithVariables>
</p:ExtractDocumentDataWithDocumentData>
```

Key notes:
- `DocType="generative_extractor"` — fixed value for generative
- `GenerateData="True"` — required for generative extractor
- `ProjectId` — use placeholder `"00000000-0000-0000-0000-000000000000"`; user must replace
- `GptPromptWithVariables` — one `InArgument` per field; `x:Key` is the field name, value is the extraction prompt
- Output type is `IDocumentData(Of CustomGptDocumentTypeXXX)` — JIT-generated; use `x:Object` as type arg at design time

### ValidateDocumentDataWithDocumentData (Combined Create+Wait)

Single activity that creates a validation task and waits synchronously for human review.

```xml
<uisad:ValidateDocumentDataWithDocumentData
    x:TypeArguments="uisaseib:Invoices"
    ActionCatalogue="default_du_actions"
    ActionPriority="Medium"
    ActionTitle="[&quot;Validate Invoice - &quot; + invoiceId]"
    AutomaticExtractionResults="[DocumentExtractedData]"
    DisplayName="Validate Document Data"
    OrchestratorBucketName="du_storage_bucket"
    OrchestratorFolderName="[&quot;Shared&quot;]"
    RemoveDataAfterProcessing="True"
    ValidatedExtractionResults="[DocumentExtractedData]" />
```

Key notes:
- `AutomaticExtractionResults` — input `uisad2:IDocumentData(Of T)` from the extraction step
- `ValidatedExtractionResults` — output `uisad2:IDocumentData(Of T)`; can be the same variable as input (overwrites)
- `ActionCatalogue` — Orchestrator action catalogue name (e.g., `"default_du_actions"`)
- `OrchestratorBucketName` — storage bucket for document data (e.g., `"du_storage_bucket"`)
- `RemoveDataAfterProcessing="True"` — cleans up document data after validation

### CreateValidationAction (Async — Create Only)

Creates a validation task in Orchestrator and returns immediately without waiting.

```xml
<uisad:CreateValidationAction
    x:TypeArguments="uisaseib:Invoices"
    ActionCatalogue="default_du_actions"
    ActionPriority="Medium"
    ActionTitle="[&quot;Validate Invoice&quot;]"
    AutomaticExtractionResults="[DocumentExtractedData]"
    CreatedValidationAction="[createdValidationAction]"
    DisplayName="Create Validation Action"
    OrchestratorBucketName="du_storage_bucket"
    OrchestratorFolderName="[&quot;Shared&quot;]" />
```

Key notes:
- `CreatedValidationAction` — output variable of type `uisad:CreatedValidationAction(Of T)` (e.g., `uisad:CreatedValidationAction(Of uisaseib:Invoices)`)
- Use this activity when the workflow needs to suspend between creating and waiting for the validation

### WaitForValidationAction (Async — Wait Only)

Waits for a previously created validation task to be completed by a human reviewer.

```xml
<uisad:WaitForValidationAction
    x:TypeArguments="uisaseib:Invoices"
    CreatedValidationAction="[createdValidationAction]"
    DisplayName="Wait For Validation Action"
    ValidatedExtractionResults="[DocumentExtractedData]" />
```

Key notes:
- `CreatedValidationAction` — input from `CreateValidationAction` output
- `ValidatedExtractionResults` — output `uisad2:IDocumentData(Of T)` after human validation

### CreateClassificationValidationActionAndWait

Sends a low-confidence classification result to a human for correction.

```xml
<uisad1:CreateClassificationValidationActionAndWait
    ActionCatalogue="default_du_actions"
    ActionPriority="Medium"
    ActionTitle="[&quot;Validate Classification&quot;]"
    AutomaticClassificationResults="[DocumentData]"
    DisplayName="Create Classification Validation Task And Wait"
    OrchestratorBucketName="du_storage_bucket"
    OrchestratorFolderName="[&quot;Shared&quot;]"
    ValidatedClassificationResults="[DocumentData]" />
```

Key notes:
- `AutomaticClassificationResults` — input `uisad1:DocumentData` from `ClassifyDocument`
- `ValidatedClassificationResults` — output `uisad1:DocumentData`; can be the same variable as input
- Typically used inside an `If` checking `DocumentData.DocumentType.Confidence < 0.7`

## DocType Values

| Value | Use for |
|-------|---------|
| `invoices` | Invoice documents |
| `receipts` | Receipt documents |
| `id_cards` | Identity cards |
| `passports` | Passport documents |
| `purchase_orders` | Purchase order documents |
| `utility_bills` | Utility bill documents |
| `remittance_advices` | Remittance advice documents |
| `bills_of_lading` | Bill of lading documents |
| `checks` | Check documents |
| `generative_extractor` | Custom/unknown document types — use with `GptPromptWithVariables` and `GenerateData="True"` |

## Accessing Extracted Data

```vb
' Access a specific field value
DocumentExtractedData.Data.InvoiceNumber.ToString
DocumentExtractedData.Data.TotalAmount.ToString

' Check document type from classification
DocumentData.DocumentType.DisplayName.Equals("Invoices")

' Check classification confidence (float 0-1)
DocumentData.DocumentType.Confidence

' Gate on low confidence before sending to human validation
If DocumentData.DocumentType.Confidence < 0.7 Then
    ' CreateClassificationValidationActionAndWait
End If
```

## Key Patterns

| Pattern | Notes |
|---------|-------|
| File input | `[LocalResource.FromPath(filePath)]` — always use for `IResource` parameters |
| Pipeline order | ClassifyDocument → ExtractDocumentDataWithDocumentData → Validate |
| ML classifier | `ClassifierId="ml-classification"`, empty `scg:Dictionary` for `GptPromptWithVariables`, integer `MinimumConfidence` |
| Generative classifier | `ClassifierId="generative_classifier"`, per-type `InArgument` entries, `Endpoint/ProjectId="{x:Null}"` |
| ML extractor | Named `DocType` (e.g., `"invoices"`), `GenerateData="False"`, empty `scg:Dictionary` for `GptPromptWithVariables` |
| Generative extractor | `DocType="generative_extractor"`, `GenerateData="True"`, per-field `InArgument` entries |
| AutoValidationConfidenceThreshold | Always set via child element as `Nullable(Int32)`, not as an XML attribute |
| Synchronous validation | Use `ValidateDocumentDataWithDocumentData` (combined create+wait) |
| Async validation | Use `CreateValidationAction` + `WaitForValidationAction` pair when workflow must suspend between create and wait |
| Classification validation | Use `CreateClassificationValidationActionAndWait` when `DocumentData.DocumentType.Confidence < 0.7` |
| ClassificationResults type | `uisad1:DocumentData` |
| ExtractionResults type | `uisad2:IDocumentData(Of T)` — use bundle type (e.g., `uisaseib:Invoices`) when known; `x:Object` otherwise |
| Full XAML | Always use `uipcli rpa get-default-activity-xaml` for complete activity XAML |

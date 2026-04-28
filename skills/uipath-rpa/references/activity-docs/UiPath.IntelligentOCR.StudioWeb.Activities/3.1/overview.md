# UiPath Document Understanding Activities

`UiPath.DocumentUnderstanding.Activities`

Activities for document classification, data extraction, and human-in-the-loop validation using the UiPath Document Understanding framework. Supports pretrained models for standard document types and custom DU project models.

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows

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

## Required XAML Namespace Declarations

All Document Understanding activities require these namespace declarations.

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

## Type Reference

Key types used across Document Understanding activities. All types are in assembly `UiPath.IntelligentOCR.StudioWeb.Activities`.

### DocumentData (Classification)

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification.DocumentData`
**XAML xmlns:** `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`

Output of ClassifyDocument. Implements `IDocumentData` and `ILocalResource`.

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

See [Data Type Patterns](activities/ExtractDocumentData/data-type-patterns.md) for the full API reference, including setter methods, lookup behavior, and **table access patterns** (`ResultsTable` → `ResultsTableValue` → `ResultsTableCell` type hierarchy with code examples).

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
| 4 | **Document type name(s)** — the name of each document type to extract (e.g., `"invoices"`, `"purchase_orders"`). Ask the user. | `DocType`, `ModernDocumentTypeId`, `ExtractorName`, `ModernDocumentTypeName` on `ExtractDocumentDataWithDocumentData` (set all four to the same name). Studio resolves names to GUIDs at design time. |

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
| Document type name | `DocType` | Lowercase document type name — Studio resolves to extractor | `"invoices"` |
| Document type name | `ExtractorName` | Same name | `"invoices"` |
| Document type name | `ModernDocumentTypeId` | Same name — Studio resolves to GUID | `"invoices"` |
| Document type name | `ModernDocumentTypeName` | Same name | `"invoices"` |

> **Note:** Studio resolves all names to internal GUIDs at design time when the user opens the workflow. The agent does not need any GUIDs from the user — `ProjectName` drives the resolution of `ProjectId`, and all other names (classifier, document type, extractor) are resolved similarly.

#### Example agent interaction

> **User:** "Create a DU workflow using my project called Invoice Processing"
>
> **Agent should ask:** "I have the project name ('Invoice Processing'). To complete the workflow, I also need:
> 1. The **classifier name** from your project (e.g., 'My Classifier')
> 2. The **document type name(s)** you want to extract (e.g., 'invoices')
> 3. The **version tag** (e.g., 'Production') or version number to use
>
> If classification validation is part of the workflow, I can skip the document type names and use the classification result directly. No GUIDs are needed — Studio resolves everything from the names when you open the workflow."

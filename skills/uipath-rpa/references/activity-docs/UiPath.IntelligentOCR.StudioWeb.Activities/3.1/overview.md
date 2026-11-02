# UiPath Document Understanding Activities

`UiPath.DocumentUnderstanding.Activities` provides document classification, extraction, and human validation with UiPath Document Understanding, including pretrained standard-document models and custom DU project models.

## Documentation

- [XAML Activities Reference](activities/) — Per-activity XAML documentation.

## Activities

### Document Understanding

| Activity | Description |
|---|---|
| [Classify Document](activities/ClassifyDocument.md) | Classifies a document with the configured classifier. |
| [Extract Document Data](activities/ExtractDocumentData.md) | Extracts data with pretrained or custom project extractors. |

### Document Validation — Extraction

| Activity | Description |
|---|---|
| [Create Validation Task and Wait](activities/CreateValidationTaskAndWait.md) | Creates an Action Center Document Validation Task and waits. |
| [Create Validation Task](activities/CreateValidationTask.md) | Creates an Action Center Document Validation Task without waiting. |
| [Wait for Validation Task and Resume](activities/WaitForValidationTaskAndResume.md) | Waits for a Document Validation Task, then resumes. |

### Document Validation — Classification

| Activity | Description |
|---|---|
| [Create Classification Validation Task](activities/CreateClassificationValidationTask.md) | Creates an Action Center Classification Validation Task without waiting. |
| [Create Classification Validation Task and Wait](activities/CreateClassificationValidationTaskAndWait.md) | Creates an Action Center Classification Validation Task and waits. |
| [Wait for Classification Validation Task & Resume](activities/WaitForClassificationValidationTaskAndResume.md) | Waits for a Classification Validation Task, then resumes. |

### Document Validation — Artifacts

| Activity | Description |
|---|---|
| [Create Document Validation Artifacts](activities/CreateDocumentValidationArtifacts.md) | Uploads extraction results to an Orchestrator storage bucket for external validation through UiPath Apps. |
| [Retrieve Document Validation Artifacts](activities/RetrieveDocumentValidationArtifacts.md) | Retrieves validated extraction results from an Orchestrator storage bucket. |

## Required XAML Namespace Declarations

All Document Understanding activities require:

```xml
xmlns:du="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:duc="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:dux="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:duVal="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:duArt="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation.Artifacts;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:uicore="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"
```

VB expressions referencing DU types require:

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

```xml
<TextExpression.ReferencesForImplementation>
  <scg:List x:TypeArguments="AssemblyReference">
    <AssemblyReference>UiPath.IntelligentOCR.StudioWeb.Activities</AssemblyReference>
  </scg:List>
</TextExpression.ReferencesForImplementation>
```

## Type Reference

All following types are in assembly `UiPath.IntelligentOCR.StudioWeb.Activities`.

### DocumentData (Classification)

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification.DocumentData`  
**XAML xmlns:** `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`

`ClassifyDocument` output; implements `IDocumentData` and `ILocalResource`.

| Property | Type | Meaning |
|---|---|---|
| `DocumentType` | `DocumentType` | Classified document type. |
| `SubDocuments` | `IDocumentData[]` | Subdocuments when splitting is enabled. |
| `FileDetails` | `FileDetails` | File path, name, extension, and page range. |
| `DocumentMetadata` | `DocumentMetadata` | OCR text, DOM, language, and results as DataTables. |

### DocumentType

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification.DocumentType`

| Property | Type | Meaning |
|---|---|---|
| `DisplayName` | `string` | Human-readable label, such as `"Invoices"`. |
| `Id` | `string` | Machine identifier, such as `"invoices"`; use for programmatic comparisons. |
| `Confidence` | `float` | Classification confidence from 0.0 to 1.0. |
| `Name` | `string` | **Obsolete;** use `Id`. |
| `Url` | `string` | Reference URL for the document type definition. |

### IDocumentData\<T\> (Extraction)

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction.IDocumentData<T>`  
**XAML xmlns:** `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities`

`ExtractDocumentData` output; extends classification `IDocumentData`.

| Property | Type | Meaning |
|---|---|---|
| `Data` | `T` | Strongly typed results when `GenerateData=True`. |
| `DocumentType` | `DocumentType` | Type used for extraction. |
| `SubDocuments` | `IDocumentData[]` | Subdocuments created upstream. |
| `DocumentMetadata` | `DocumentMetadata` | OCR text, DOM, and `ResultsAsDataTables` for tabular export. |

### ExtendedExtractionResultsForDocumentData

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction.ExtendedExtractionResultsForDocumentData`

Base type argument for `ExtractDocumentDataWithDocumentData<T>`. With `GenerateData=True`, Studio generates a subclass with strongly typed properties for extracted fields.

### DictionaryData

**CLR type:** `UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction.DictionaryData`  
**XAML xmlns:** `clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities` (prefix `dux`)

Extends `ExtendedExtractionResultsForDocumentData`; recommended for agent-generated workflows because it avoids Studio design-time JIT code generation.

| Method | Return type | Meaning |
|---|---|---|
| `GetField(string fieldIdOrName)` | `ResultsDataPoint` | Field by ID or name. |
| `GetFieldValue(string fieldIdOrName)` | `ResultsValue` | First field value. |
| `GetFieldValues(string fieldIdOrName)` | `ResultsValue[]` | All field values. |
| `GetFields()` | `ResultsDataPoint[]` | All non-table fields. |
| `GetTable(string tableIdOrName)` | `ResultsTable` | Table by ID or name. |
| `GetTables()` | `ResultsTable[]` | All tables. |

See [Data Type Patterns](activities/ExtractDocumentData/data-type-patterns.md) for setters, lookup behavior, and table access patterns: `ResultsTable` → `ResultsTableValue` → `ResultsTableCell`, with code examples.

## Activity Data Flow

Use this pipeline, keeping one extraction type argument `<T>` throughout extraction and validation:

```text
ClassifyDocument
  DocumentData
    ├─ optional CreateClassificationValidationAction
    │    CreatedClassificationValidationAction (token)
    │    └─ WaitForClassificationValidationAction → validated DocumentData
    └─ ExtractDocumentDataWithDocumentData<T>
         input: DocumentData as FileInput (implements IResource)
         output: IDocumentData<T>
           ├─ optional CreateValidationAction<T>
           │    CreatedValidationAction<T> (token)
           │    └─ WaitForValidationAction<T> → validated IDocumentData<T>
           └─ alternative CreateDocumentValidationArtifacts<T>
                ContentValidationData
                └─ RetrieveDocumentValidationArtifacts
                     → validated IDocumentData<DictionaryData>
```

`T` is `DictionaryData` (recommended for agents) or a Studio-generated type. Classification validation is not generic. The “and Wait” variants (`CreateClassificationValidationActionAndWait`, `ValidateDocumentDataWithDocumentData`) combine creation and waiting in one persistent activity. `DocumentData` implements `IResource` and can be passed directly as `FileInput`.

## Persistence Requirement for Validation Workflows

Any workflow containing `WaitForValidationAction`, `WaitForClassificationValidationAction`, `ValidateDocumentDataWithDocumentData`, or `CreateClassificationValidationActionAndWait` suspends until a human completes an Action Center task. Enable persistence by setting `"supportsPersistence": true` inside `"runtimeOptions"` in `project.json`:

```json
{
  "runtimeOptions": {
    "supportsPersistence": true
  }
}
```

Agents must always set this for workflows containing validation activities. If missing or `false`, runtime execution fails at the persistent activity. This applies to every `Wait` or `...AndWait` activity, including `WaitForValidationAction`, `WaitForClassificationValidationAction`, `ValidateDocumentDataWithDocumentData`, and `CreateClassificationValidationActionAndWait`.

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

Replace Predefined values as follows:

```xml
<du:ClassifyDocument
  ProjectId="placeholder" ProjectName="{Your Project Name}"
  ProjectTag="{your-version-tag}" ProjectVersionName="{your-version-tag}"
  ProjectVersionNumber="0" ClassifierId="{your-classifier-name}"
  ClassifierName="{your-classifier-name}" ... />

<du:ExtractDocumentDataWithDocumentData
  x:TypeArguments="dux:DictionaryData" ActivityMajorVersion="2"
  ProjectId="placeholder" ProjectName="{Your Project Name}"
  ProjectTag="{your-version-tag}" ProjectVersionName="{your-version-tag}"
  ProjectVersionNumber="0" DocType="{document-type-name}"
  ExtractorName="{document-type-name}" ModernDocumentTypeId="{document-type-name}"
  ModernDocumentTypeName="{document-type-name}" ... />
```

`ProjectName` drives design-time resolution. Studio resolves `ProjectId` to the project GUID, `ProjectVersionNumber` from `ProjectTag`, and classifier/extractor names to internal identifiers when the workflow is opened. This applies to DU and IXP projects; `ProjectId="placeholder"` and `ProjectVersionNumber="0"` are safe when the user supplies no GUID or number. Use a supplied GUID when available.

Custom-project rules:

- `ProjectName` is the display name and drives `ProjectId` resolution.
- `ClassifierId` and `ClassifierName` are both the custom classifier name.
- `DocType`, `ExtractorName`, `ModernDocumentTypeId`, and `ModernDocumentTypeName` are the document type name, such as `"invoices"`, unless using `ModernDocumentTypeId="use_classification_result"`; then set `DocType="{x:Null}"`.
- `ProjectTag` and `ProjectVersionName` identify the version; Studio resolves `ProjectVersionNumber`, so agents may use `"0"`.
- Classification and extraction may use different projects, including DU and IXP projects. `ModernDocumentTypeId="use_classification_result"` resolves the extraction document type from classification output at runtime across projects.

### Agent Guidance: Custom DU Projects

When the user names a DU project, collect the remaining values; no GUIDs are needed because Studio resolves names at design time.

#### Required Information Checklist

| # | Ask for | XAML mapping |
|---|---|---|
| 1 | Project name, usually already supplied | `ProjectName` on both activities; drives `ProjectId`. |
| 2 | Version tag or number, such as `"Production"` or `"live"` | Tag → `ProjectTag` and `ProjectVersionName`; or number → `ProjectVersionNumber`. |
| 3 | Classifier name | Set `ClassifierId` and `ClassifierName` to the same name. |
| 4 | Document type name(s), such as `"invoices"` or `"purchase_orders"` | Set `DocType`, `ModernDocumentTypeId`, `ExtractorName`, and `ModernDocumentTypeName` to the same name. |

If classification validation is included, use `ModernDocumentTypeId="use_classification_result"` and `DocType="{x:Null}"` instead of asking for item 4.

#### What the agent can set without asking

- `ProjectId="placeholder"` unless the user supplies a GUID.
- `ProjectVersionNumber="0"` when `ProjectTag` is set.
- `GenerateData="False"` — always use this for agent-generated workflows.
- `ActivityMajorVersion="2"` — always set this on `ExtractDocumentDataWithDocumentData`.
- `x:TypeArguments="dux:DictionaryData"` — always use this type argument.
- `TimeoutInSeconds="[3600]"`.
- `ProjectTag` and `ProjectVersionName` to `"Production"` when the user says “production”.
- `ModernDocumentTypeId="use_classification_result"` with `DocType="{x:Null}"` when classification validation is confirmed.

#### UI-to-XAML Property Mapping

**ClassifyDocument:**

| User value | Property | Format | Example |
|---|---|---|---|
| Project name | `ProjectName` | Display string; Studio resolves `ProjectId`. | `"My Invoice Project"` |
| Auto-resolved | `ProjectId` | GUID or placeholder. | `"placeholder"` |
| Version tag | `ProjectTag`, `ProjectVersionName` | Same string. | `"Production"` |
| Auto-resolved | `ProjectVersionNumber` | Integer; use `"0"` placeholder. | `"0"` |
| Classifier name | `ClassifierId`, `ClassifierName` | Same name; Studio resolves `ClassifierId`. | `"My Classifier"` |

**ExtractDocumentDataWithDocumentData:**

| User value | Property | Format | Example |
|---|---|---|---|
| Project name | `ProjectName` | Display string; Studio resolves `ProjectId`. | `"My Invoice Project"` |
| Auto-resolved | `ProjectId` | GUID or placeholder. | `"placeholder"` |
| Version tag | `ProjectTag`, `ProjectVersionName` | Same string. | `"Production"` |
| Auto-resolved | `ProjectVersionNumber` | Integer; use `"0"` placeholder. | `"0"` |
| Document type name | `DocType`, `ExtractorName`, `ModernDocumentTypeId`, `ModernDocumentTypeName` | Same lowercase/name value; Studio resolves identifiers. | `"invoices"` |

Studio resolves all names to internal GUIDs when the user opens the workflow; the agent does not need GUIDs.

#### Example agent interaction

For “Create a DU workflow using my project called Invoice Processing,” retain the project name and ask for:

1. Classifier name (e.g., `"My Classifier"`).
2. Document type name(s) (e.g., `"invoices"`), unless classification validation allows `ModernDocumentTypeId="use_classification_result"` with `DocType="{x:Null}"`.
3. Version tag, such as `"Production"`, or version number.

Tell the user that no GUIDs are needed because Studio resolves names when the workflow opens.

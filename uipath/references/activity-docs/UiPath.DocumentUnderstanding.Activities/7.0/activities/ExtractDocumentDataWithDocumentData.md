# ExtractDocumentDataWithDocumentData

Extracts structured data from a document using either a trained ML extraction model or a generative (LLM) extractor.

## ML Extractor

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

## Generative Extractor

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

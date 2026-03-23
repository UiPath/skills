# ClassifyDocument

Classifies a document using either a trained ML classification model or a generative (LLM) classifier.

## ML Classifier

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

## Generative Classifier

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

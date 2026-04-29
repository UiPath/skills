# Read XPS With OCR

`UiPath.XPS.Activities.ReadXPSWithOCR`

Reads all characters from a specified XPS (XML Paper Specification) file and stores the result in a string variable by using OCR technology. Use this activity for scanned XPS documents where native text extraction returns empty results.

**Package:** `UiPath.PDF.Activities`
**Category:** App Integration > XPS
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FileName` | File (local path) | `InArgument` | `string` | Yes | | The full path of the XPS file to be read. |
| `Password` | Password | `InArgument` | `string` | | `null` | The password of the XPS file, if necessary. Leave empty if the file is not encrypted. |
| `Range` | Range | `InArgument` | `string` | | `"All"` | The page range to read (e.g. `"2-4"`, `"1,3,5"`, or `"All"`). If the range isn't specified, the whole file is read. |
| `DegreeOfParallelism` | DegreeOfParallelism | `InArgument` | `int` | Yes | `1` | Number of pages to be OCRed in parallel. A value of `-1` indicates the operation will be executed on available LogicalProcessorCount - 1. A positive value n will execute the operation on n logical processors, no greater than LogicalProcessorCount - 1. |

### OCR Engine

| Name | Display Name | Type | Required | Description |
|------|-------------|------|----------|-------------|
| `OCREngine` | OCR Engine | `ActivityFunc<Image, IEnumerable<KeyValuePair<Rectangle, String>>>` | Yes | The OCR engine activity used to extract text from XPS page images. Drop an OCR engine activity into this scope. **Use UiPath Document OCR** (`ocr:UiPathDocumentOCR`) — see OCR Engine Selection below. |

#### OCR Engine Selection

**Use UiPath Document OCR** (`ocr:UiPathDocumentOCR`) as the default OCR engine for XPS OCR activities. It provides the best accuracy for document-oriented content (tables, paragraphs, mixed layouts, skewed scans).

**Do NOT use UiPath Screen OCR** (`ocr:UiPathScreenOCR`) with XPS activities. Screen OCR is designed for live screen captures and UI automation scenarios, not for document processing. It will produce inferior results on scanned documents.

| Engine | Use With XPS? | Designed For |
|--------|---------------|--------------|
| UiPath Document OCR | **Yes (recommended)** | Document processing, PDFs/XPS — requires `Endpoint` and `ApiKey` |
| OmniPage OCR | Acceptable | Document processing |
| Google Cloud Vision OCR | Acceptable | General-purpose OCR |
| Microsoft OCR | Acceptable | General-purpose OCR |
| UiPath Screen OCR | **No** | Live screen captures, UI automation |

> **Required credentials for UiPath Document OCR:** `Endpoint` and `ApiKey` are user/organization-specific values that cannot be auto-discovered. The agent **must ask the user** for these values before generating the workflow. Do not leave them as `{x:Null}` or use placeholder strings — the workflow will fail at runtime without valid credentials.
>
> - **Endpoint**: The Document OCR service URL (e.g., `https://du.uipath.com/ocr` or a staging/on-prem URL).
> - **ApiKey**: The authentication key for the OCR service.

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `Text` | Text | `string` | The extracted string containing all recognized text from the specified page range. |

## XAML Examples

### With UiPath Document OCR

```xml
<!-- Required namespace declarations:
     xmlns:ui="http://schemas.uipath.com/workflow/activities"
     xmlns:ocr="http://schemas.uipath.com/workflow/activities/ocr"
     xmlns:sd="clr-namespace:System.Drawing;assembly=System.Drawing"
     xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"

     Required package: UiPath.OCR.Activities (provides UiPath Document OCR, Google Cloud Vision OCR, Microsoft OCR, etc.)
-->

<ui:ReadXPSWithOCR
    DisplayName="Read XPS With OCR"
    FileName="[xpsFilePath]"
    Range="[pageRange]"
    Password="[password]"
    DegreeOfParallelism="1"
    Text="[outputText]">
  <ui:ReadXPSWithOCR.OCREngine>
    <ActivityFunc x:TypeArguments="sd:Image, scg:IEnumerable(scg:KeyValuePair(sd:Rectangle, x:String))">
      <ActivityFunc.Argument>
        <DelegateInArgument x:TypeArguments="sd:Image" Name="Image" />
      </ActivityFunc.Argument>
      <ocr:UiPathDocumentOCR
          DisplayName="UiPath Document OCR"
          Image="[Image]"
          Endpoint="[ocrEndpoint]"
          ApiKey="[ocrApiKey]"
          Language="auto"
          Scale="1"
          Timeout="100000" />
    </ActivityFunc>
  </ui:ReadXPSWithOCR.OCREngine>
</ui:ReadXPSWithOCR>
```

### Minimal (OCR engine placeholder)

```xml
<!-- xmlns:ui="http://schemas.uipath.com/workflow/activities" -->
<!-- xmlns:sd="clr-namespace:System.Drawing;assembly=System.Drawing" -->
<!-- xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib" -->

<ui:ReadXPSWithOCR
    DisplayName="Read XPS With OCR"
    FileName="[xpsFilePath]"
    Range="All"
    DegreeOfParallelism="1"
    Text="[outputText]">
  <ui:ReadXPSWithOCR.OCREngine>
    <ActivityFunc x:TypeArguments="sd:Image, scg:IEnumerable(scg:KeyValuePair(sd:Rectangle, x:String))">
      <ActivityFunc.Argument>
        <DelegateInArgument x:TypeArguments="sd:Image" Name="Image" />
      </ActivityFunc.Argument>
      <!-- Insert an OCR engine activity here. The engine MUST bind Image="[Image]" to the delegate argument.
           RECOMMENDED: ocr:UiPathDocumentOCR (best for document/XPS content)
             - Requires Endpoint and ApiKey (ask user for these values)
             - xmlns:ocr="http://schemas.uipath.com/workflow/activities/ocr"
           ACCEPTABLE alternatives:
             - uoa:OmniPageOCR (from UiPath.OmniPage.Activities)
             - ui:GoogleCloudOCR (requires API key)
             - ui:MicrosoftOCR
             Note: GoogleCloudOCR and MicrosoftOCR use the ui: prefix (xmlns:ui="http://schemas.uipath.com/workflow/activities"), NOT ocr:.
           NOT RECOMMENDED for document processing:
             - ocr:UiPathScreenOCR (designed for screen captures, not documents)
      -->
    </ActivityFunc>
  </ui:ReadXPSWithOCR.OCREngine>
</ui:ReadXPSWithOCR>
```

## Notes

- This activity requires an OCR engine to be placed inside the `OCREngine` scope. Without an OCR engine, a validation error is raised: the activity will not work without one.
- The `OCREngine` child element is an `ActivityFunc` delegate — it must contain exactly one OCR engine activity. **The OCR engine must set `Image="[Image]"` to bind to the delegate argument** — without this binding the engine receives no input.
- **OCR engine packages must be installed separately.** The most common package is `UiPath.OCR.Activities` (namespace `xmlns:ocr="http://schemas.uipath.com/workflow/activities/ocr"`), which provides UiPath Document OCR, Google Cloud Vision OCR, and Microsoft OCR. Use `uip rpa find-activities --query "OCR engine"` to discover available engines and `uip rpa install-or-update-packages` to install the required package.
- Unlike `ReadPDFWithOCR`, there is no `ImageDpi` configuration property — the XPS reader uses a fixed internal rendering DPI.
- The `Range` property accepts formats such as `"All"`, `"1"`, `"2-5"`, or comma-separated page numbers. An invalid format raises an exception at runtime.
- This activity is only available on Windows (`#if !NETPORTABLE_UIPATH`). It uses the Windows-native XPS reader and cannot be used in cross-platform workflows.
- For XPS files with embedded (native) text, prefer **Read XPS Text** instead — it is faster and does not require an OCR engine.

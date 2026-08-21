# UiPath Document OCR

`UiPath.OCR.Activities.UiPathDocumentOCR`

Extracts a string containing all the text from the input image, along with all word positions. This OCR engine is optimized for processing document images (PDFs, scanned forms, structured layouts) and is the recommended engine for document-oriented OCR. Backed by the UiPath Document OCR cloud service.

**Package:** `UiPath.OCR.Activities`
**Category:** OCR Engines
**Platform:** Windows only

## Typical Usage

This activity is an **OCR engine** — a leaf activity placed inside an OCR-consuming scope. It can be used in two ways:

1. **As an OCR engine inside a parent activity's `OCREngine` slot.** This is the most common pattern: the parent (e.g. `ReadPDFWithOCR`, `ReadXPSWithOCR`, `DigitizeDocument`, UI Automation OCR-based selectors) supplies the image via an `ActivityFunc<Image, …>` delegate, and this engine binds `Image="[Image]"` to the delegate argument.
2. **Standalone**, with the caller providing a `System.Drawing.Image` to the `Image` input and consuming the `Text` (and optionally `OCRResult`) output directly. Less common, but supported.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Image` | Image | `InArgument` | `System.Drawing.Image` | Yes | | The image that you want to process. Do not change if the OCR activity is used inside a parent activity — bind `Image="[Image]"` to the parent's `ActivityFunc` delegate argument. |

### OCR Service

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Endpoint` | Endpoint | `InArgument` | `string` | **No — default applies** | `"https://du.uipath.com/ocr"` | UiPath Document OCR endpoint URL. The activity has a hardcoded fallback (`UiPathDocumentOCR.DefaultEndpoint` → `https://du.uipath.com/ocr`); leaving the attribute and project setting empty resolves to that URL at runtime. Only override for on-prem (AI Center / Document Understanding self-hosted), staging, or region-specific deployments. Agents should **not** ask the user about this field unless the user explicitly signals a non-default deployment. Supports only `String` variables. |
| `ApiKey` | ApiKey | `InArgument` | `string` | **Yes (or via project setting)** | `""` | UiPath Document OCR API key. User- and tenant-specific; cannot be auto-discovered. No default — empty value results in a runtime authentication error. Supports only `String` variables. |

> ### Credentials — ALWAYS ASK BEFORE GENERATING
>
> `ApiKey` and `Endpoint` are **not symmetric**. Handle them differently.
>
> | Field | User input required? | Default behavior |
> |-------|---------------------|------------------|
> | `ApiKey` | **YES — ALWAYS ask the user before generating the workflow.** No sensible default. Without a real key the workflow compiles green and fails on the first OCR call with `OCRException: Invalid API key specified` / `UiPathOCRInvalidApiKey` (see Troubleshooting). | None. Empty/missing key → runtime exception from the cloud service. |
> | `Endpoint` | **NO — default to `https://du.uipath.com/ocr`.** Only ask the user if they signal a non-default deployment (on-prem, AI Center / Document Understanding self-hosted, staging, region-specific). | `https://du.uipath.com/ocr` (UiPath Automation Cloud, public). |
>
> The minimum interaction for a workflow on Automation Cloud is **one question** ("What is your UiPath Document OCR API key?"). Do **not** skip that question even when the user picks the Project-Settings wiring path below — they still need to know which key to provide and where to put it.
>
> **Where to obtain the API key.** UiPath Automation Cloud → **Admin → Licenses → Consumables** (Document Understanding / AI Units pane). The same key serves every `UiPath.OCR.Activities` activity in the tenant. Treat it as a secret — read it from an Orchestrator asset / credential / secrets manager at runtime; never hardcode it in source-controlled XAML.
>
> ### Wiring decision: where the ApiKey lives
>
> Once the agent has the key (or has confirmed the user will fill it in via Project Settings), pick ONE of the two strategies. Both are valid; the difference is only where the value lives.
>
> **A. Per-activity attribute (embed in XAML)** — set `ApiKey="[apiKey]"` (variable) or a literal on every `<ocr:UiPathDocumentOCR>` element. Simplest when the workflow is not source-controlled or the user prefers value-in-XAML.
>
> **B. Project Settings (recommended for source-controlled projects)** — OMIT the `ApiKey` attribute on the activity element (do **not** set it to `""` or `"{x:Null}"`) and store the value under **Project Settings → UiPath.OCR.Activities → UiPathDocumentOCR → ApiKey**. With the attribute omitted, the runtime resolution order (per-activity → project setting → empty) lets the project setting take effect.
>
> **If you pick path B, the completion summary MUST include a top-level "Before running" line.** Recommended phrasing:
>
> > **Before running:** open **Project Settings → UiPath.OCR.Activities → UiPathDocumentOCR** in Studio and set **ApiKey** to the key from Automation Cloud → Admin → Licenses → Consumables. Without this the workflow will fail at the first OCR call with `Invalid API key specified` (`UiPathOCRInvalidApiKey`).
>
> Omitting this instruction is the single most common cause of "looked complete, failed on first run".
>
> `Endpoint` follows the same A/B logic — embed only if the user provided a non-default value; otherwise omit it and let the built-in default apply.
>
> ### Agent question template (suggested wording)
>
> Before generating, the agent SHOULD ask the user something like:
>
> > To wire up UiPath Document OCR I need your API key. You can find it in UiPath Automation Cloud → **Admin → Licenses → Consumables** (Document Understanding / AI Units pane). I'll default the endpoint to `https://du.uipath.com/ocr` unless you're on on-prem, AI Center, or a staging URL — tell me if that's the case. Do you want the key embedded directly in the XAML, or held in Studio's Project Settings (recommended for source-controlled projects)?

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `UseLocalServer` | UseLocalServer | `InArgument<bool>` | `False` | Determines if a local Document Understanding server (DU.LocalServer) should be used instead of the cloud endpoint. Requires DU.LocalServer to be installed on the robot; a design-time validation error is raised if `True` but the local server is missing. |
| `UseSeparateOcrProcess` | UseSeparateOcrProcess | `InArgument<bool>` | `True` | Determines whether OCR runs in a separate OS process (more robust against native-library crashes) or in-process (lower overhead). Leave at `True` unless you have a specific reason. |

### Common

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Timeout` | Timeout (milliseconds) | `InArgument` | `int` | Yes | `100000` | Amount of time (in milliseconds) to wait for a response from the OCR server before an error is thrown. Must be greater than 0. Default is `100000` (100 seconds). |
| `DisplayName` | DisplayName | `string` | `"UiPath Document OCR"` | | The activity's display name in Studio. |
| `ContinueOnError` | ContinueOnError | `InArgument<bool>` | `False` | | If `True`, the workflow continues when the activity throws. Inherited from `AsyncCodeActivity` / activity base. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Text` | Text | `OutArgument` | `string` | The extracted string containing all recognized text from the input image. |
| `Result` | Result | `OutArgument` | `OCRResult` | (Inherited) Full OCR result including words, confidence, skew angle, model info, and capabilities. Inspect this when you need positional or per-word information instead of just text. |

### Hidden / Advanced Properties

These are public but `[Browsable(false)]` — they do not appear in Studio's property grid. Most workflows never set them. Document them only because some XAML samples (including the canonical PDF reference) include them explicitly:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `Language` | `InArgument<string>` | `"auto"` | Language hint for the OCR engine. `"auto"` is correct for almost every scenario; the service auto-detects script. |
| `Scale` | `InArgument<double>` | `1.0` | Scale factor applied to the input image before OCR. Values >1 upscale (can help on tiny captures); values <1 downscale. |
| `Profile` | `OCRProfile` | `None` | Internal profile selector — leave at default. |
| `ExtractWords` | `bool` | `True` | Whether to populate the per-word breakdown in the `OCRResult`. |
| `ComputeSkewAngle` | `bool` | `False` | Whether to compute the page skew angle (only meaningful when `UseLocalServer = True`). |
| `UseAccents` | `InArgument<bool>` | `False` | Accent handling toggle. Not used by Document OCR; retained for base-class compatibility. |

## Valid Configurations

### Endpoint resolution order

1. The activity-level `Endpoint`/`ApiKey` arguments, if set on this activity.
2. Otherwise, the project setting under section `UiPathDocumentOCR` (`Endpoint`, `ApiKey`).
3. Otherwise, the built-in default endpoint `https://du.uipath.com/ocr` and an empty API key — execution will fail authentication.

### Local server mode

- `UseLocalServer = False` (default) — calls the cloud endpoint at `Endpoint`. Requires `ApiKey`.
- `UseLocalServer = True` — calls the locally installed Document Understanding server. `Endpoint`/`ApiKey` are ignored for the call but DU.LocalServer must be installed; otherwise a design-time validation error and a runtime `NotSupportedException` are raised.

## Project Settings

`Endpoint` and `ApiKey` are project-settable arguments. Studio surfaces them under **Project Settings → UiPath.OCR.Activities → UiPathDocumentOCR**, and they persist as keys in `project.json` under `settings`.

| Property | Setting Section | Setting Key | Default | Description |
|----------|-----------------|-------------|---------|-------------|
| `Endpoint` | `UiPathDocumentOCR` | `Endpoint` | `"https://du.uipath.com/ocr"` | Default endpoint applied to all instances of this activity in the project. |
| `ApiKey` | `UiPathDocumentOCR` | `ApiKey` | `""` | Default API key applied to all instances of this activity in the project. |

Per-activity values override project settings. If both are empty, the activity raises a required-setting error at runtime.

## Troubleshooting

### "In order to use this activity in this Studio version, please install the UiPath.CoreIpc package, version 2.0.1 or higher."

This message can be misleading. It is emitted from `OCRBase.CacheMetadata` via the activity-pack validator (`CoreIPCMissingError` resource), and the package itself does **not** depend on `UiPath.CoreIPC` directly — it depends on `UiPath.Platform` (which transitively pulls a compatible `UiPath.CoreIpc`). When this message appears under `uip rpa get-errors` / `uip rpa validate` / `uip rpa build`, the actual cause is usually one of:

1. **Wrong assembly in the XAML namespace declaration for `sd:Image` / `sd:Rectangle`.** On modern Windows / Portable projects (`targetFramework: "Windows"` or `"Portable"`, .NET 6), `System.Drawing.Image` lives in `System.Drawing.Common.dll` — not `System.Drawing.dll`. An `xmlns:sd="clr-namespace:System.Drawing;assembly=System.Drawing"` declaration leaves `sd:Image` unresolvable at XAML load time; the OCR activity's design-time validator then surfaces the catch-all CoreIpc message. Fix: use the correct assembly per project target (see "XAML Examples" below).
2. **Stale `xmlns:ocr=…` URI from an older package version.** The current URI is `http://schemas.uipath.com/workflow/activities/ocr`.
3. **Stale `.local/` state in a headless `uip rpa` session for a project that has never been opened in Studio Desktop.** Open the project in Studio Desktop once — it normalizes the XAML and seeds `.local/` correctly — then re-run `uip rpa get-errors`.

**Do not** add `UiPath.CoreIpc` to `project.json` in response to this message. It is not a direct dependency of this package, and adding it does not address the underlying failure.

### `"Invalid API key specified"` / `UiPathOCRInvalidApiKey` at runtime

Exact wording the user will see (`OCRException` from `ImageAnnotatorService`, `OCRResultCode = UiPathOCRInvalidApiKey`):

```
Error performing OCR: Server response: Invalid API key specified
Error: UiPathOCRInvalidApiKey
CF-RAY: cid-v1:...
   at UiPathDocumentOCR "UiPath Document OCR"
   in Main.xaml
```

The activity attribute resolved to an **empty string** (because both the per-activity `ApiKey` attribute and the Project Settings entry were left blank) **OR** the value supplied is not a valid key for this tenant / endpoint. The XAML compiles green, the runtime ships an empty `ApiKey` to the cloud service, and the service rejects it with HTTP 401 → `UiPathOCRInvalidApiKey`.

**Recovery:** populate **Project Settings → UiPath.OCR.Activities → UiPathDocumentOCR → ApiKey** (path B in the Credentials callout above) **OR** set the `ApiKey` attribute on the activity element (path A). The key itself comes from Automation Cloud → Admin → Licenses → Consumables.

**Prevention (for agents):** never generate this workflow without first asking the user for the API key. See the Credentials callout under Properties — the "ALWAYS ASK" rule applies regardless of which wiring path you pick.

## XAML Examples

### Required Namespace Declarations

Add these `xmlns:` entries to the workflow root `<Activity>` element. The correct assembly names depend on the project's `targetFramework`.

**Modern projects (`targetFramework: "Windows"` or `"Portable"`, .NET 6):**

```xml
xmlns:ui="http://schemas.uipath.com/workflow/activities"
xmlns:ocr="http://schemas.uipath.com/workflow/activities/ocr"
xmlns:sd="clr-namespace:System.Drawing;assembly=System.Drawing.Common"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
```

Add `<AssemblyReference>System.Drawing.Common</AssemblyReference>` and `<AssemblyReference>UiPath.OCR.Activities</AssemblyReference>` to `<TextExpression.ReferencesForImplementation>` on the workflow root.

**Legacy projects (`targetFramework: "Legacy"`, .NET Framework 4.6.1):**

```xml
xmlns:ui="http://schemas.uipath.com/workflow/activities"
xmlns:ocr="http://schemas.uipath.com/workflow/activities/ocr"
xmlns:sd="clr-namespace:System.Drawing;assembly=System.Drawing"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"
```

`mscorlib` and `System.Drawing` are the historically correct assembly names on .NET Framework. Using them on a modern project causes XAML type resolution to fail and triggers the misleading "install UiPath.CoreIpc" validator message (see Troubleshooting above).

> **`Endpoint` is omitted from these examples on purpose** — the runtime fallback (`https://du.uipath.com/ocr`) applies automatically. Only emit `Endpoint="..."` when the user has signaled a non-default deployment (on-prem / AI Center / DU self-hosted / staging / region-specific). See the "Custom endpoint" variant at the bottom.

### Inside `ReadPDFWithOCR.OCREngine` (recommended pattern)

```xml
<ui:ReadPDFWithOCR
    DisplayName="Read PDF With OCR"
    FileName="[pdfFilePath]"
    Range="All"
    Text="[outputText]">
  <ui:ReadPDFWithOCR.OCREngine>
    <ActivityFunc x:TypeArguments="sd:Image, scg:IEnumerable(scg:KeyValuePair(sd:Rectangle, x:String))">
      <ActivityFunc.Argument>
        <DelegateInArgument x:TypeArguments="sd:Image" Name="Image" />
      </ActivityFunc.Argument>
      <ocr:UiPathDocumentOCR
          DisplayName="UiPath Document OCR"
          Image="[Image]"
          ApiKey="[ocrApiKey]"
          Timeout="100000" />
    </ActivityFunc>
  </ui:ReadPDFWithOCR.OCREngine>
</ui:ReadPDFWithOCR>
```

### Standalone (caller-supplied image)

```xml
<ocr:UiPathDocumentOCR
    DisplayName="UiPath Document OCR"
    Image="[pageImage]"
    ApiKey="[ocrApiKey]"
    Timeout="100000"
    Text="[extractedText]" />
```

### Standalone, credentials from Project Settings (omit attributes)

When the project supplies `ApiKey` via **Project Settings → UiPath.OCR.Activities → UiPathDocumentOCR**, omit the attribute from the activity element entirely — do **not** set it to an empty string or `{x:Null}`.

```xml
<ocr:UiPathDocumentOCR
    DisplayName="UiPath Document OCR"
    Image="[pageImage]"
    Timeout="100000"
    Text="[extractedText]" />
```

### Standalone, custom endpoint (on-prem / staging / region-specific)

**Only when** the user has signaled a non-default deployment. Embed the literal URL the user supplied — do not invent one.

```xml
<ocr:UiPathDocumentOCR
    DisplayName="UiPath Document OCR"
    Image="[pageImage]"
    Endpoint="https://ocr.internal.contoso.com/ocr"
    ApiKey="[ocrApiKey]"
    Timeout="100000"
    Text="[extractedText]" />
```

## Notes

- **Class-level `[Browsable(false)]`.** This activity is hidden from Studio's modern toolbox and is intended to be authored either by dropping it into an OCR-engine slot of a parent activity (Studio offers it from the parent's OCR-engine picker — backed by `UiPathDocumentOCRFactory`) or directly in XAML by type name. Both are fully supported; it is **not** deprecated. **Consequence for tooling:** `uip rpa activities find --query "UiPathDocumentOCR"` (or any keyword that would match the class) returns zero hits whether the assembly is loaded or not — `[Browsable(false)]` excludes the class from the discovery surface. Do **not** treat absence-from-`find-activities` as a signal that the package failed to load. Use `uip rpa packages inspect` against the installed `.nupkg`, or run `uip rpa get-errors` / `uip rpa validate` against an XAML file that references the activity by type name, to confirm the assembly is wired correctly.
- **Windows only.** The OCR host (`UiPath.OCR.Host64.exe`) is shipped only for `net6.0-windows7.0`. Cross-platform workflows that need OCR must select a different engine.
- **`Image` binding inside a parent scope.** When used inside an `ActivityFunc<Image, …>` slot (as in `ReadPDFWithOCR.OCREngine`), set `Image="[Image]"` so the engine receives the image the parent passes through the delegate. Omitting this binding leaves the engine with no input and the run fails with a null-image error.
- **Default endpoint.** `https://du.uipath.com/ocr` is the hardcoded runtime fallback (`UiPathDocumentOCR.DefaultEndpoint`). Use it without asking the user; only override on an explicit signal from the user (on-prem / AI Center / DU self-hosted / staging / region-specific). **Never invent an endpoint URL** — the only acceptable values are the documented default and a user-supplied override.
- **Required API key.** No default — if neither the activity attribute nor the Project Settings entry supplies a non-empty `ApiKey`, the cloud service rejects the request at runtime (see Troubleshooting → "Invalid API key specified"). The agent **must** ask the user for the key — do not substitute placeholders.
- **`OCRResult` shape.** When you need more than `Text`, read `Result.Words` (per-word boxes and confidence), `Result.Confidence`, `Result.SkewAngle`, `Result.OCRCapabilities`, `Result.OcrModelInfo` (model commit SHA + release version), `Result.ImageHash`. See the coded-API doc for the full property list.
- **Related activities.** Prefer `ExtendedLanguagesOCR` (`UiPath Extended Languages OCR`) for handwriting-heavy or extended-language (CJK) workloads; prefer `UiPathScreenOCR` for live screen captures. Do **not** use `UiPathScreenOCR` for document content — it is tuned for UI captures and produces inferior results on scans.

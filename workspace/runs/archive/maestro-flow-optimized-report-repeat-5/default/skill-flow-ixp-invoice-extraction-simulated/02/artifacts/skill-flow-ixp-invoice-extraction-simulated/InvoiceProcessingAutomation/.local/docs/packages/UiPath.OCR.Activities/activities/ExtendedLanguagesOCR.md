# UiPath Extended Languages OCR

`UiPath.OCR.Activities.ExtendedLanguagesOCR`

Extracts a string containing all the text from the input image, along with all word positions from an indicated document or UI element using the UiPath Extended Languages OCR. This engine is backed by **Microsoft Azure Computer Vision (Read API)** with handwriting recognition enabled and the **document-understanding detection mode** — well-suited to CJK (Chinese, Japanese, Korean) scripts and handwriting-heavy content that the default UiPath Document OCR engine handles less reliably.

**Package:** `UiPath.OCR.Activities`
**Category:** OCR Engines
**Platform:** Windows only

## Typical Usage

This activity is an **OCR engine** — a leaf activity placed inside an OCR-consuming scope. It can be used in two ways:

1. **As an OCR engine inside a parent activity's `OCREngine` slot.** This is the most common pattern: the parent (e.g. `ReadPDFWithOCR`, `ReadXPSWithOCR`, `DigitizeDocument`, UI Automation OCR-based selectors) supplies the image via an `ActivityFunc<Image, …>` delegate, and this engine binds `Image="[Image]"` to the delegate argument.
2. **Standalone**, with the caller providing a `System.Drawing.Image` to the `Image` input and consuming the `Text` (and optionally `OCRResult`) output directly.

Pick this engine when the source contains CJK script or significant handwriting; otherwise `UiPathDocumentOCR` is the default for Latin-script document content.

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Image` | Image | `InArgument` | `System.Drawing.Image` | Yes | | The image that you want to process. Do not change if the OCR activity is used inside a parent activity — bind `Image="[Image]"` to the parent's `ActivityFunc` delegate argument. |

### OCR Service

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Endpoint` | Endpoint | `InArgument` | `string` | **No — default applies** | `"https://du.uipath.com/extended-ocr"` | Endpoint URL for the UiPath-hosted Azure Computer Vision proxy. The activity has a hardcoded fallback (`ExtendedLanguagesOCR.DefaultEndpoint` → `https://du.uipath.com/extended-ocr`); the same value is also pre-populated as the project setting's default via `[ArgumentSetting(..., DefaultExtendedLanguagesOCREndPoint, true)]`. Leaving the attribute and project setting empty resolves to that URL at runtime. Only override for on-prem, staging, or region-specific deployments. Agents should **not** ask the user about this field unless the user explicitly signals a non-default deployment. Supports only `String` variables. |
| `ApiKey` | ApiKey | `InArgument` | `string` | **Yes (or via project setting)** | `""` | Document Understanding API key for the Extended Languages OCR service. User- and tenant-specific; no default. Empty value results in an Azure CV 401 at runtime. Supports only `String` variables. |

> ### Credentials — ALWAYS ASK BEFORE GENERATING
>
> `ApiKey` and `Endpoint` are **not symmetric**. Handle them differently.
>
> | Field | User input required? | Default behavior |
> |-------|---------------------|------------------|
> | `ApiKey` | **YES — ALWAYS ask the user before generating the workflow.** No sensible default. Without a real key the workflow compiles green and fails on the first OCR call with a 401 from the Azure Computer Vision Read API (see Troubleshooting). | None. Empty/missing key → runtime exception from the Azure-backed service. |
> | `Endpoint` | **NO — default to `https://du.uipath.com/extended-ocr`.** Only ask the user if they signal a non-default deployment (on-prem, AI Center, staging, region-specific). | `https://du.uipath.com/extended-ocr` (UiPath-hosted Azure Computer Vision proxy, public). |
>
> The minimum interaction for a workflow on Automation Cloud is **one question** ("What is your UiPath Extended Languages OCR API key?"). Do **not** skip that question even when the user picks the Project-Settings wiring path below — they still need to know which key to provide and where to put it.
>
> **Where to obtain the API key.** UiPath Automation Cloud → **Admin → Licenses → Consumables** (Document Understanding / AI Units pane). The same Document Understanding key serves every `UiPath.OCR.Activities` activity in the tenant (Document OCR, Extended Languages OCR, etc.) — you do **not** need a separate Azure subscription key from the user. Treat the key as a secret — read it from an Orchestrator asset / credential / secrets manager at runtime; never hardcode it in source-controlled XAML.
>
> ### Wiring decision: where the ApiKey lives
>
> Once the agent has the key (or has confirmed the user will fill it in via Project Settings), pick ONE of the two strategies. Both are valid; the difference is only where the value lives.
>
> **A. Per-activity attribute (embed in XAML)** — set `ApiKey="[apiKey]"` (variable) or a literal on every `<ocr:ExtendedLanguagesOCR>` element. Simplest when the workflow is not source-controlled or the user prefers value-in-XAML.
>
> **B. Project Settings (recommended for source-controlled projects)** — OMIT the `ApiKey` attribute on the activity element (do **not** set it to `""` or `"{x:Null}"`) and store the value under **Project Settings → UiPath.OCR.Activities → ExtendedLanguagesOCR → ApiKey**. With the attribute omitted, the runtime resolution order (per-activity → project setting → empty) lets the project setting take effect.
>
> **If you pick path B, the completion summary MUST include a top-level "Before running" line.** Recommended phrasing:
>
> > **Before running:** open **Project Settings → UiPath.OCR.Activities → ExtendedLanguagesOCR** in Studio and set **ApiKey** to the key from Automation Cloud → Admin → Licenses → Consumables. Without this the workflow will fail at the first OCR call with an "Access denied due to invalid subscription key" / HTTP 401 error from the Azure Computer Vision backend.
>
> Omitting this instruction is the single most common cause of "looked complete, failed on first run".
>
> `Endpoint` follows the same A/B logic — embed only if the user provided a non-default value; otherwise omit it and let the built-in default apply.
>
> ### Agent question template (suggested wording)
>
> Before generating, the agent SHOULD ask the user something like:
>
> > To wire up UiPath Extended Languages OCR I need your API key. You can find it in UiPath Automation Cloud → **Admin → Licenses → Consumables** (Document Understanding / AI Units pane). I'll default the endpoint to `https://du.uipath.com/extended-ocr` unless you're on on-prem, AI Center, or a staging URL — tell me if that's the case. Do you want the key embedded directly in the XAML, or held in Studio's Project Settings (recommended for source-controlled projects)?

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `UseSeparateOcrProcess` | UseSeparateOcrProcess | `InArgument<bool>` | `True` | Determines whether OCR runs in a separate OS process (more robust against native-library crashes) or in-process (lower overhead). Leave at `True` unless you have a specific reason. |

### Common

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Timeout` | Timeout (milliseconds) | `InArgument` | `int` | Yes | `100000` | Amount of time (in milliseconds) to wait for a response from the OCR server before an error is thrown. Must be greater than 0. Default is `100000` (100 seconds). The Azure Read API is asynchronous and polled internally; allow generous timeouts for multi-page or low-confidence inputs. |
| `DisplayName` | DisplayName | `string` | `"UiPath Extended Languages OCR"` | | The activity's display name in Studio. |
| `ContinueOnError` | ContinueOnError | `InArgument<bool>` | `False` | | If `True`, the workflow continues when the activity throws. Inherited from `AsyncCodeActivity` / activity base. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Text` | Text | `OutArgument` | `string` | The extracted string containing all recognized text from the input image. |
| `Result` | Result | `OutArgument` | `OCRResult` | (Inherited) Full OCR result including words, confidence, skew angle, model info, and capabilities. Inspect this when you need positional or per-word information. |

### Hidden / Advanced Properties

These are public but `[Browsable(false)]` — they do not appear in Studio's property grid. Most workflows never set them:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `Language` | `InArgument<string>` | `"auto"` | Language hint. `"auto"` is correct for almost every scenario; the Azure Read API auto-detects script. |
| `Scale` | `InArgument<double>` | `1.0` | Scale factor applied to the input image before OCR. Values >1 upscale (can help on tiny captures); values <1 downscale. |
| `Profile` | `OCRProfile` | `None` | Internal profile selector — leave at default. |
| `ExtractWords` | `bool` | `True` | Whether to populate the per-word breakdown in the `OCRResult`. |
| `ComputeSkewAngle` | `bool` | `False` | Whether to compute the page skew angle. Hard-coded to `False` for this engine regardless of the property value. |

## Valid Configurations

### Endpoint resolution order

1. The activity-level `Endpoint`/`ApiKey` arguments, if set on this activity.
2. Otherwise, the project setting under section `ExtendedLanguagesOCR` (`Endpoint`, `ApiKey`).
3. Otherwise, the built-in default endpoint `https://du.uipath.com/extended-ocr` and an empty API key — execution will fail authentication.

### Internal request shape

Each call sends the image to the configured endpoint using the Microsoft Azure Computer Vision Read API v3.2 with `handwritingRecognition=true` and `detectionMode=DocumentUnderstanding`. Read operations are asynchronous; the engine polls until the operation completes or `Timeout` is reached.

## Project Settings

`Endpoint` and `ApiKey` are project-settable arguments. Studio surfaces them under **Project Settings → UiPath.OCR.Activities → ExtendedLanguagesOCR**, and they persist as keys in `project.json` under `settings`.

| Property | Setting Section | Setting Key | Default | Description |
|----------|-----------------|-------------|---------|-------------|
| `Endpoint` | `ExtendedLanguagesOCR` | `Endpoint` | `"https://du.uipath.com/extended-ocr"` | Default endpoint applied to all instances. Marked as `isRequired = true` in `[ArgumentSetting]` — Studio's design-time validator (`Shared.Contracts.PropertySettings.CacheMetadata`) checks the setting is non-empty, but the same attribute also supplies the URL as the default value, so this check passes out of the box. No agent action required. |
| `ApiKey` | `ExtendedLanguagesOCR` | `ApiKey` | `""` | Default API key applied to all instances. Marked as `isRequired = true`, with no default value (empty string). If both the activity attribute and this project setting are empty, Studio emits a `RequiredSettingArgumentErrorMessage` at design time AND the runtime call fails authentication. |

Per-activity values override project settings. The `Endpoint` is satisfied by its built-in default; the `ApiKey` is not — see the Credentials callout under Properties for the "ALWAYS ASK" rule.

## Troubleshooting

### "In order to use this activity in this Studio version, please install the UiPath.CoreIpc package, version 2.0.1 or higher."

This message can be misleading. It is emitted from `OCRBase.CacheMetadata` via the activity-pack validator (`CoreIPCMissingError` resource), and the package itself does **not** depend on `UiPath.CoreIPC` directly — it depends on `UiPath.Platform` (which transitively pulls a compatible `UiPath.CoreIpc`). When this message appears under `uip rpa get-errors` / `uip rpa validate` / `uip rpa build`, the actual cause is usually one of:

1. **Wrong assembly in the XAML namespace declaration for `sd:Image` / `sd:Rectangle`.** On modern Windows / Portable projects (`targetFramework: "Windows"` or `"Portable"`, .NET 6), `System.Drawing.Image` lives in `System.Drawing.Common.dll` — not `System.Drawing.dll`. An `xmlns:sd="clr-namespace:System.Drawing;assembly=System.Drawing"` declaration leaves `sd:Image` unresolvable at XAML load time; the OCR activity's design-time validator then surfaces the catch-all CoreIpc message. Fix: use the correct assembly per project target (see "XAML Examples" below).
2. **Stale `xmlns:ocr=…` URI from an older package version.** The current URI is `http://schemas.uipath.com/workflow/activities/ocr`.
3. **Stale `.local/` state in a headless `uip rpa` session for a project that has never been opened in Studio Desktop.** Open the project in Studio Desktop once — it normalizes the XAML and seeds `.local/` correctly — then re-run `uip rpa get-errors`.

**Do not** add `UiPath.CoreIpc` to `project.json` in response to this message. It is not a direct dependency of this package, and adding it does not address the underlying failure.

### Empty / invalid ApiKey at runtime (Azure CV 401)

Because this engine routes through the Microsoft Azure Computer Vision Read API (via `CjkScrapeEngine` → `MicrosoftAzureComputerVisionEngine`), an empty or invalid `ApiKey` produces an Azure-side authentication failure rather than the UiPath `UiPathOCRInvalidApiKey` code. Typical wording the user will see:

```
Error performing OCR: ... Access denied due to invalid subscription key
or wrong API endpoint. ...
   at ExtendedLanguagesOCR "UiPath Extended Languages OCR"
   in Main.xaml
```

(The exact string is the Azure CV server response — it may also surface as a wrapped `ComputerVisionErrorResponseException` or HTTP 401.)

The activity attribute resolved to an **empty string** (because both the per-activity `ApiKey` attribute and the Project Settings entry were left blank) **OR** the value supplied is not a valid Document Understanding API key for this tenant / endpoint. The XAML compiles green, the runtime ships an empty `ApiKey` to the Azure-backed service, and the service rejects it with HTTP 401.

**Recovery:** populate **Project Settings → UiPath.OCR.Activities → ExtendedLanguagesOCR → ApiKey** (path B in the Credentials callout above) **OR** set the `ApiKey` attribute on the activity element (path A). The key itself comes from Automation Cloud → Admin → Licenses → Consumables.

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

`mscorlib` and `System.Drawing` are the historically correct assembly names on .NET Framework. Using them on a modern project causes XAML type resolution to fail and triggers the misleading "install UiPath.CoreIPC" validator message (see Troubleshooting above).

> **`Endpoint` is omitted from these examples on purpose** — the runtime fallback (`https://du.uipath.com/extended-ocr`) applies automatically. Only emit `Endpoint="..."` when the user has signaled a non-default deployment (on-prem / staging / region-specific). See the "Custom endpoint" variant at the bottom.

### Inside `ReadPDFWithOCR.OCREngine` (recommended pattern for CJK / handwriting PDFs)

```xml
<ui:ReadPDFWithOCR
    DisplayName="Read PDF With OCR (Extended)"
    FileName="[pdfFilePath]"
    Range="All"
    Text="[outputText]">
  <ui:ReadPDFWithOCR.OCREngine>
    <ActivityFunc x:TypeArguments="sd:Image, scg:IEnumerable(scg:KeyValuePair(sd:Rectangle, x:String))">
      <ActivityFunc.Argument>
        <DelegateInArgument x:TypeArguments="sd:Image" Name="Image" />
      </ActivityFunc.Argument>
      <ocr:ExtendedLanguagesOCR
          DisplayName="UiPath Extended Languages OCR"
          Image="[Image]"
          ApiKey="[ocrApiKey]"
          Timeout="100000" />
    </ActivityFunc>
  </ui:ReadPDFWithOCR.OCREngine>
</ui:ReadPDFWithOCR>
```

### Standalone (caller-supplied image)

```xml
<ocr:ExtendedLanguagesOCR
    DisplayName="UiPath Extended Languages OCR"
    Image="[pageImage]"
    ApiKey="[ocrApiKey]"
    Timeout="100000"
    Text="[extractedText]" />
```

### Standalone, credentials from Project Settings (omit attributes)

When the project supplies `ApiKey` via **Project Settings → UiPath.OCR.Activities → ExtendedLanguagesOCR**, omit the attribute from the activity element entirely — do **not** set it to an empty string or `{x:Null}`.

```xml
<ocr:ExtendedLanguagesOCR
    DisplayName="UiPath Extended Languages OCR"
    Image="[pageImage]"
    Timeout="100000"
    Text="[extractedText]" />
```

### Standalone, custom endpoint (on-prem / staging / region-specific)

**Only when** the user has signaled a non-default deployment. Embed the literal URL the user supplied — do not invent one.

```xml
<ocr:ExtendedLanguagesOCR
    DisplayName="UiPath Extended Languages OCR"
    Image="[pageImage]"
    Endpoint="https://extended-ocr.internal.contoso.com/extended-ocr"
    ApiKey="[ocrApiKey]"
    Timeout="100000"
    Text="[extractedText]" />
```

## Notes

- **Class-level `[Browsable(false)]`.** This activity is hidden from Studio's modern toolbox and is not present in the package's `ActivitiesMetadataWindows.json`. It is intended to be authored either by dropping it into an OCR-engine slot of a parent activity (Studio offers it from the parent's OCR-engine picker — backed by `ExtendedLanguagesOCRFactory`) or directly in XAML by type name. It is **not** deprecated. **Consequence for tooling:** `uip rpa activities find --query "ExtendedLanguagesOCR"` (or any keyword that would match the class) returns zero hits whether the assembly is loaded or not — `[Browsable(false)]` and the metadata-file omission both exclude the class from the discovery surface. Do **not** treat absence-from-`find-activities` as a signal that the package failed to load. Use `uip rpa packages inspect` against the installed `.nupkg`, or run `uip rpa get-errors` / `uip rpa validate` against an XAML file that references the activity by type name, to confirm the assembly is wired correctly.
- **Windows only.** The OCR host (`UiPath.OCR.Host64.exe`) is shipped only for `net6.0-windows7.0`.
- **`Image` binding inside a parent scope.** When used inside an `ActivityFunc<Image, …>` slot (as in `ReadPDFWithOCR.OCREngine`), set `Image="[Image]"` so the engine receives the image the parent passes through the delegate. Omitting this binding leaves the engine with no input and the run fails with a null-image error.
- **Default endpoint.** `https://du.uipath.com/extended-ocr` is the hardcoded runtime fallback (`ExtendedLanguagesOCR.DefaultEndpoint`) and is pre-populated as the project setting's default. Use it without asking the user; only override on an explicit signal from the user (on-prem / staging / region-specific). **Never invent an endpoint URL** — the only acceptable values are the documented default and a user-supplied override.
- **Required API key.** No default — if neither the activity attribute nor the Project Settings entry supplies a non-empty `ApiKey`, the Azure-backed service rejects the request with HTTP 401 at runtime (see Troubleshooting). The agent **must** ask the user for the key — do not substitute placeholders.
- **Not the default.** Prefer `UiPathDocumentOCR` for Latin-script document content (faster, generally higher accuracy on those layouts). Pick `ExtendedLanguagesOCR` specifically when the input is CJK or contains heavy handwriting.
- **Class name vs. display name.** The class is `ExtendedLanguagesOCR`; the user-facing display name is "UiPath Extended Languages OCR". XAML must use the class name as the element name.
- **Legacy heritage.** The base class is `CjkOCRBase` — the engine originated as a CJK-only variant and was extended to broader language coverage; the base name is retained for code-compatibility and surfaces in some internal options classes.

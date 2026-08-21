# UiPath OCR Activities

`UiPath.OCR.Activities`

The UiPath OCR Activities package provides UiPath's OCR engines as drop-in activities. These engines are leaf activities placed inside an OCR-consuming scope (for example `ReadPDFWithOCR.OCREngine` in the PDF package, or UI Automation OCR-based selectors) and produce a `Text` output plus an `OCRResult` with per-word positions, confidence, and model info. Backed by the UiPath Document OCR service and Microsoft Azure Computer Vision (for extended languages).

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows
- [Coded Workflow API Reference](coded/) — `ocr.*` service surface for coded (C#) workflows

## Activities

### OCR Engines

| Activity                                                      | Description                                                                                                                              |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| [UiPath Document OCR](activities/UiPathDocumentOCR.md)        | Cloud-based OCR optimized for document images (PDFs, scanned forms, structured layouts). Default engine for document content. Windows only. Requires `ApiKey`. |
| [UiPath Extended Languages OCR](activities/ExtendedLanguagesOCR.md) | Cloud-based OCR built on Microsoft Azure Computer Vision (Read API) with handwriting recognition and document-understanding detection mode. Use for CJK scripts or handwriting-heavy content. Windows only. Requires `ApiKey`. |

## Engine Selection at a Glance

| Source content | Recommended engine |
|----------------|---------------------|
| Latin-script documents (PDF scans, forms) | UiPath Document OCR |
| CJK (Chinese / Japanese / Korean) | UiPath Extended Languages OCR |
| Handwriting-heavy content | UiPath Extended Languages OCR |
| Live screen captures / UI automation | `UiPathScreenOCR` (separate; designed for UI captures, not documents) |

### Name aliases (for agents resolving user requests)

Users routinely refer to these engines by shortened or colloquial names that are not exact matches for any class name or display name in the package. An agent should resolve a user-supplied phrase by checking for a distinguishing keyword and **skip** any "which engine?" confirmation question when the match is unique.

| User phrase contains…                                  | Engine                                  |
|--------------------------------------------------------|-----------------------------------------|
| "Extended" (any case, any suffix — "Extended OCR", "UiPath Extended OCR", "the Extended engine") | `ExtendedLanguagesOCR`                  |
| "Document" / "Doc OCR" / "the doc OCR"                 | `UiPathDocumentOCR`                     |
| "Screen" / "Screen OCR"                                | `UiPathScreenOCR` (not in this doc)     |
| "CJK" / "Chinese" / "Japanese" / "Korean"              | `ExtendedLanguagesOCR`                  |

Only ask the user to confirm engine choice when:
- (a) the phrase contains no distinguishing keyword from this table, OR
- (b) the phrase matches multiple engines (none in the current catalog do).

Both documented engines need an **`ApiKey`** — there is no sensible default for this field. **Always ask the user for the API key before generating a workflow.** Obtain it from Automation Cloud → **Admin → Licenses → Consumables** (Document Understanding / AI Units pane); the same key serves every `UiPath.OCR.Activities` activity in the tenant.

The **`Endpoint`** is different — it defaults to the public UiPath-hosted URL for each engine (`https://du.uipath.com/ocr` for Document OCR, `https://du.uipath.com/extended-ocr` for Extended Languages OCR). Only ask the user about the endpoint if they signal a non-default deployment (on-prem, AI Center, staging, region-specific).

Per-activity docs spell out the full wiring decision (embed in XAML vs. store in Project Settings) and the mandatory completion-summary line when the Project-Settings path is used — see [UiPathDocumentOCR § Credentials](activities/UiPathDocumentOCR.md#credentials--always-ask-before-generating) and [ExtendedLanguagesOCR § Credentials](activities/ExtendedLanguagesOCR.md#credentials--always-ask-before-generating).

## Compatibility

- **Windows only.** The OCR host (`UiPath.OCR.Host64.exe`) is shipped only for `net6.0-windows7.0`. Cross-platform / Portable workflows that need OCR must select a different engine.
- **Authoring surface.** All shipped activities (`UiPathDocumentOCR`, `ExtendedLanguagesOCR`, `UiPathScreenOCR`) are marked `[Browsable(false)]` and surfaced in Studio's toolbox via their matching `*Factory` classes (`UiPathDocumentOCRFactory`, …). This is by design — see the per-activity Notes for the consequence on `uip rpa activities find` (zero hits regardless of load state).
- **Headless `uip rpa` callers and dev-channel package builds.** When using a `-dev.*` or `-preview.*` package build through headless `uip rpa` (without Studio Desktop), the activity's design-time validator may emit a misleading `CoreIPCMissingError` ("In order to use this activity in this Studio version, please install the UiPath.CoreIPC package…"). The package does **not** depend on `UiPath.CoreIPC` directly — it depends on `UiPath.Platform`. See the Troubleshooting section in each activity's doc for the actual root causes (most commonly the wrong `xmlns:sd` assembly in the workflow XAML for modern .NET projects). A pragmatic recovery when stuck: open the project in Studio Desktop once, then re-run `uip rpa get-errors`. A published minimum-`UiPath.Studio.Helm` version contract for this package channel would let agents fail fast and clearly — until then, treat the CoreIPC message as "validator could not initialize", not as a literal dependency request.

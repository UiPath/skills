# OCR Activities

Low-level OCR engine activities from `UiPath.OCR.Activities`. Provides **UiPath Screen OCR** and **UiPath Document OCR** (cloud endpoint or local server), plus **CJK** and **Extended Languages** OCR via Document Understanding. These are the foundational text-recognition engines consumed by higher-level surfaces — Document Understanding `Digitize Document`, and Computer Vision screen scopes.

## Key Activity Types

- **UiPath Screen OCR** — cloud/local screen text recognition
- **UiPath Document OCR** — cloud/local document text recognition
- **CJK OCR / Extended Languages OCR** — Chinese/Japanese/Korean and extended-language recognition via DU

Engines: `ScreenOcr`, `DocumentOcr`, `Cjk`. Local-server modes: `UiPath.ComputerVision.LocalServer` (screen), `UiPath.DocumentUnderstanding.OCR.LocalServer` (document).

## Common Failure Patterns

- Missing local-server / `UiPath.CoreIPC` package, incompatible companion package versions, unsupported engine, or a missing required `ApiKey` / `Endpoint`
- Invalid API key, null/empty endpoint, invalid CJK server config, non-2xx service response, invalid/missing response, or service-call timeout
- Invalid or missing image input, unsupported rotation angle, runtime timeout, wrong scrape usage, or an empty/silent result

## Cross-References

- For the Document Understanding pipeline (`Digitize`, classification, extraction, validation) — the OCR invalid-key surfaces there wrapped as `System.AggregateException` → `UiPathOCRInvalidApiKey`; see the Document Understanding (Intelligent OCR) playbooks.
- For Computer Vision screen-targeting scopes, see the CV Activities package.

## Package

NuGet: `UiPath.OCR.Activities`. Exceptions: `OCRException` carrying an `OCRResultCode` (e.g. `UiPathOCRInvalidApiKey` 99902, `UiPathOCRErrorInvalidResponse` 99904, running-engine/timeout 99901, Azure/CJK 751).

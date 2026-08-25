# OCR Activities Investigation Guide

## Data Correlation

Before concluding, verify the fetched data matches the reported problem:

- **Activity** — which OCR activity faulted (UiPath Screen OCR vs UiPath Document OCR vs CJK/Extended Languages)
- **Mode** — cloud endpoint vs local server, and which local-server package the mode requires
- **Endpoint** — the OCR endpoint resolved at run time (cloud `.uipath.com` vs on-prem/local)
- **Input** — the image/text the activity processed corresponds to the input the user reported

## Routing

1. **Exception type first:**
   - `NotSupportedException` (missing local-server) / package-compatibility or required-argument validation errors → **config & dependencies**
   - `OCRException` (carries an `OCRResultCode`) or `ArgumentException` on the endpoint → **endpoint & authentication**
   - `ArgumentException` (`No image input` / `Usage must be ...`), `TimeoutException` (`OCR timeout exceeded`), `NotSupportedException` (`Rotation angle ...`) → **input & runtime**
2. **`OCRResultCode` routes the auth/endpoint branch:** `99902` `UiPathOCRInvalidApiKey` (auth), `99904` invalid response, `99901` running-engine / timeout, `751` Azure/CJK engine.
3. **Cloud vs local:** a cloud endpoint (`.uipath.com`) has an ApiKey → access-token fallback — a rotated/revoked key can silently fall back and only fail when that path also lacks entitlement. A local-server or on-prem endpoint has no fallback.

## Prerequisites

- `UiPath.OCR.Activities` version, and the versions of `IntelligentOCR` / `PDF` / `DocumentUnderstanding.ML` / `OmniPage` (compatibility gate)
- Whether local server mode is on and the corresponding LocalServer package is installed
- The `ApiKey` / `Endpoint` resolved at run time (project settings or bindings), and `Timeout` value

## Cross-Domain

For the Document Understanding pipeline (`Digitize` / classify / extract), the OCR invalid-key surfaces as `System.AggregateException` wrapping `UiPathOCRInvalidApiKey` — see the Document Understanding (Intelligent OCR) playbooks. For CV screen scopes, see the CV Activities package.

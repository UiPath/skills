---
confidence: medium
---

# OCR Endpoint & Authentication Errors

## Context

A UiPath OCR call reached the transport layer and failed on authentication, endpoint configuration, or the service response. Surfaces as an `OCRException` carrying an `OCRResultCode`, or an `ArgumentException` on the endpoint. Route on the message and the code.

What this looks like:
- `Invalid API key specified` (`OCRException`, `OCRResultCode` `UiPathOCRInvalidApiKey` / 99902; HTTP 401) — the API key was rejected. In the Document Understanding `Digitize` pipeline this surfaces wrapped as `System.AggregateException` → `Server response: Invalid API key specified Error:UiPathOCRInvalidApiKey`.
- `endpoint is null or empty` (`ArgumentException`) — no endpoint was configured at run time.
- `Invalid CJK server configuration. Neither async nor sync endpoints are enabled.` (`OCRException` 751) — the CJK endpoint returned no usable API path.
- `Response indicates an error: <status>, Error: <body>` (`OCRException` 751) — a non-2xx response from the CJK/Azure endpoint.
- Invalid / missing response (`OCRException` `UiPathOCRErrorInvalidResponse` / 99904) — passes through the service error message or the raw body; logs show `Invalid/missing response from UiPath Screen OCR API`.
- `The OCR service call timed out` / `The Model Info call timed out` (`OCRException` 99901) — the endpoint did not respond within the timeout.

What can cause it:
- The API key is wrong, expired, or was rotated/revoked; or the tenant lacks OCR entitlement.
- No endpoint (or a wrong endpoint) is configured; the CJK server has neither async nor sync path enabled.
- Proxy / firewall / TLS on the robot host blocks the endpoint, or the endpoint is slow/overloaded.

What to look for:
- The message plus the `OCRResultCode`; whether the endpoint is cloud (`.uipath.com`) or on-prem/local.
- For an invalid key: whether the key was recently rotated, and whether the tenant has OCR entitlement.
- For endpoint/response/timeout: reachability of the endpoint from the robot host, and the passed-through service status/body.

> **Cloud fallback:** a cloud endpoint falls back from the `ApiKey` to the signed-in access token. A rotated/revoked key can silently fall back and only fail when that path also lacks entitlement — treat a sudden 401 after a key change as the rotated key. On-prem / local endpoints have no fallback.

## Investigation

1. Capture the message and `OCRResultCode`; identify cloud vs on-prem/local endpoint.
2. For an invalid key (99902): verify the `ApiKey` is current, confirm tenant OCR entitlement, and check whether the key was recently rotated.
3. For endpoint / response / timeout: test endpoint reachability from the robot host (proxy / TLS / firewall) and read the passed-through service status/body.

## Resolution

### Invalid API key (`UiPathOCRInvalidApiKey` / 99902)
Set a current `ApiKey` (Project Settings for the OCR engine, or the activity binding), or ensure the robot is signed in to the licensed tenant so the token fallback authenticates. Confirm the tenant has OCR entitlement.

### `endpoint is null or empty`
Configure the OCR `Endpoint` (project settings or binding).

### Invalid CJK server configuration
Enable an async or sync endpoint for the CJK server, or use a supported OCR engine.

### `Response indicates an error` / invalid or missing response
Read the passed-through status/body and fix the endpoint-side error (auth, payload, availability); verify the endpoint URL is correct and reachable from the robot host.

### Service-call / model-info timeout
Confirm endpoint reachability and latency from the robot host. Raise the timeout only if the endpoint is legitimately slow — not to mask an auth or endpoint error, which surface as their own messages.

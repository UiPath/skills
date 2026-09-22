# Resolution — InvoiceApiClient

## Root Cause

Job `9d4f2a18-3c5b-4e70-8a2f-1b6c3e5d7a90` (process `InvoiceApiClient`, entry
point `Wf_PostInvoice.xaml`, folder Shared) faulted in **HTTP Request
(HttpClient)** with:

```
System.Net.WebException: The remote server returned an error: (401) Unauthorized.
```

The request reached the API and was rejected on **authentication**, not
transport, path, proxy, or payload. `Wf_PostInvoice.xaml` builds the
`Authorization` header from the **bare token** — `Authorization = [apiToken]`
(the raw value read from the `VENDOR_API_TOKEN` environment variable) — with
**no `Bearer ` scheme prefix**. The API expects `Authorization: Bearer <token>`,
so the un-prefixed value is treated as unauthenticated and returns `401`.

Matches `activity-packages/web-activities/playbooks/http-request-auth-401-403.md`.

## Fix

Format the `Authorization` header with its scheme:

- Set the header value to **`"Bearer " + apiToken`** instead of the bare
  `apiToken`, matching the scheme the API documents.
- Confirm the token itself is valid and unexpired (retrieve it from an
  Orchestrator credential asset / Get Credential rather than a stale source),
  minted for the correct environment/audience.
- Mirror the exact headers of a known-good request (e.g. a working Postman /
  curl call) to confirm parity, then re-run and confirm a `2xx`.

## Must NOT attribute

Do not attribute this to: a DNS/connection/TLS transport failure (the server
answered with an HTTP status); a corporate proxy `407`; a wrong `EndPoint` path
(`404` — the resource was found and the request was authenticated-checked); a
payload/`Content-Type` problem (`400/415`); or a timeout. It is also not a `403`
(the identity is not merely under-permitted — it was not authenticated at all).
The specific defect is the malformed `Authorization` header (bare token, missing
the `Bearer ` prefix); supplying a new token without fixing the header format,
or changing the URL/network, will not resolve the `401`.

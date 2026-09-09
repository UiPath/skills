# Resolution — CrmContactUpload

## Root Cause

Job `3f8d5a91-2b7c-4e60-9a1f-6c8e4d2b0a75` (process `CrmContactUpload`, entry
point `Wf_CreateContact.xaml`, folder Shared) faulted in **HTTP Request
(HttpClient)** with:

```
System.Net.WebException: The remote server returned an error: (415) Unsupported Media Type.
```

The request reached the CRM API and was rejected on **media type**, not auth,
path, or transport. `Wf_CreateContact.xaml` posts a **JSON** body
(`{"name":"Acme Corp","email":"ops@acme.example","tier":"gold"}`) while
`BodyFormat` is set to **`application/xml`** — so the request advertises
`Content-Type: application/xml` but carries JSON. The API rejects the
mismatched media type with `415 Unsupported Media Type`.

Matches `activity-packages/web-activities/playbooks/http-request-content-type-rejected.md`.

## Fix

Make the advertised media type match the body:

- Set the HttpClient `BodyFormat` to **`application/json`** (or set a
  `Content-Type: application/json` header) so it matches the JSON `Body`.
  `HttpClient`'s `BodyFormat` defaults to `application/xml`, so a JSON body
  must set it explicitly.
- Confirm the endpoint expects `application/json` (per the CRM API docs); if
  it truly wants XML, send an XML body instead — either way, the `Content-Type`
  and the body must agree.
- Re-run and confirm a `2xx`.

## Must NOT attribute

Do not attribute this to: an authentication/permission problem (401/403) — the
server returned `415`, not an auth status; a wrong endpoint path (404) — the
resource was found and the request was understood enough to be rejected on
media type; a DNS/connection/TLS transport failure — the call reached the
server and got an HTTP response; or a timeout. This is a payload/`Content-Type`
formatting mismatch (JSON body sent as `application/xml`), fixed by aligning
`BodyFormat`/`Content-Type` with the body — supplying credentials or changing
the URL will not fix it.

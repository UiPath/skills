---
confidence: medium
---

# HTTP Request — Payload Rejected (400 Bad Request / 415 Unsupported Media Type)

## Context

What this looks like:
- A **`POST` / `PUT`** HTTP request that sends a body or a file is answered by the server with **`(400) Bad Request`** or **`(415) Unsupported Media Type`**.
- On the legacy `HttpClient` this surfaces as `System.Net.WebException: The remote server returned an error: (415) Unsupported Media Type.` (a faulted job); on `NetHttpRequest` (default `ContinueOnError = True`) it is returned as a **response** with `StatusCode 415`/`400` (no fault) — read the response, not a fault.
- The request reached the server and was **understood enough to be rejected** — this is a payload/formatting problem, NOT auth (`401/403`), NOT a wrong path (`404`), NOT transport.

What causes it:
- **`Content-Type` does not match the body.** `HttpClient`'s `BodyFormat` defaults to **`application/xml`**; sending a JSON body without setting `BodyFormat`/the `Content-Type` header to `application/json` → the server rejects the media type (`415`) or fails to parse (`400`).
- **Attachments sent with the wrong shape.** The **Add Attachment** option is enabled **only when the Method is `POST` or `PUT`**. Posting a file the API expects as **`multipart/form-data`** while the request advertises `application/json` (or vice versa) → `415`/`400`. Mixing an explicit body with attachments can also produce a malformed request.
- **Header vs body mismatch** — a hand-set `Content-Type` header that contradicts the actual body encoding.

What to look for:
- **The status code in the message/response** — `415` = server refused the media type; `400` = server could not parse/validate the payload as sent.
- **`Method`** — `400/415` on a body/file almost always accompanies `POST`/`PUT`.
- **`BodyFormat` and the `Headers`** in the workflow source — is `Content-Type` set, and does it match the actual `Body`?
- **Attachments** — is a file attached, and does the API expect `multipart/form-data`?
- **The API's documented `Content-Type` requirement** for this endpoint.

## Investigation

1. **Confirm the status is `400` or `415`** (not `401/403/404`). `uip or jobs get <job-key> --output json` / `uip or jobs logs <job-key> --level Error --output json` (legacy fault) or the activity's response output (`NetHttpRequest`).
2. **Read the request configuration from source** — `Method`, `BodyFormat`, the `Content-Type` header, the `Body` value, and whether Add Attachment is used.
3. **Compare the advertised `Content-Type` to the actual body / attachment shape** and to what the API documents it accepts. The mismatch is the root cause.

## Resolution

- **Set the `Content-Type` to match the body.** For a JSON body, set `BodyFormat` / the `Content-Type` header to `application/json` (do not rely on the `application/xml` default). Align header and body encoding.
- **Use the media type the API expects for files.** For a file upload the API wants as `multipart/form-data`, send it via the attachment mechanism with `multipart/form-data` — do not stuff the file into a JSON body; conversely do not attach a file when the API expects a raw JSON/binary body.
- **Keep attachments on `POST`/`PUT`** (the only methods that allow them) and avoid combining a conflicting explicit `Body` with attachments.
- Re-run and confirm a `2xx`. Do not treat `400/415` as an auth or endpoint-path problem — supplying credentials or changing the URL will not fix a media-type mismatch.

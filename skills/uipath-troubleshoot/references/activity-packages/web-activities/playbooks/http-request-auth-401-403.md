---
confidence: medium
---

# HTTP Request — 401 Unauthorized / 403 Forbidden (auth)

## Context

What this looks like:
- An `HttpClient` / `NetHttpRequest` call is answered by the server with **`(401) Unauthorized`** or **`(403) Forbidden`**.
- Legacy `HttpClient` surfaces it as `System.Net.WebException: The remote server returned an error: (401) Unauthorized.` (a faulted job). `NetHttpRequest` (default `ContinueOnError = True`) returns it as a **response** with `StatusCode 401`/`403` — read the response, not a fault.
- The request **reached the server and was authenticated-checked** — this is a credential/authorization problem, NOT transport (DNS/connection/TLS), NOT a payload/media-type problem (`400/415`), NOT a proxy `407`.

What causes it (branch on the code):
- **`401` Unauthorized — the caller was not authenticated.** Common causes:
  - **Missing / malformed `Authorization` header** — the classic one is sending the **bare token** instead of the scheme-prefixed value: the header must be `"Bearer " + tokenVariable`, not just `tokenVariable`. A missing `Bearer ` prefix (or wrong scheme, e.g. `Basic` vs `Bearer`) → `401`.
  - **Expired / revoked token**, or a token minted for a different environment/audience.
  - **Token in the wrong place** — query string vs header, or a custom header name (`X-API-Key`) the API doesn't read.
- **`403` Forbidden — authenticated but not permitted.** The token is valid but the identity lacks the scope/role/permission for that resource, or the API key is out of quota / IP-restricted.

What to look for:
- **The exact status in the message/response** — `401` (authN) vs `403` (authZ) selects the branch.
- **The `Headers` in the workflow source** — is there an `Authorization` header, and is its value `"Bearer " + token` (scheme prefix present) or a bare token? Is the token literal, a variable, or an unset value?
- **Token source & freshness** — Get Credential / Orchestrator asset vs hard-coded; whether it is refreshed per run or reused past expiry.
- **What a known-good client sends** — the same request in Postman / curl that succeeds. Header/scheme parity with the working client is the fastest confirmation.

## Investigation

1. **Confirm the status is `401` or `403`** (not `400/415`, `407`, or a transport `WebException`). `uip or jobs get <job-key> --output json` / `uip or jobs logs <job-key> --level Error --output json` (legacy fault) or the activity's response output (`NetHttpRequest`).
2. **Read the auth configuration from source** — the `Authorization` header value expression, `AuthenticationType`/auth properties, and where the token comes from. Note whether the scheme prefix (`Bearer `) is present.
3. **Branch:**
   - `401` → authentication: check the header format/scheme prefix, token presence, and token freshness/audience.
   - `403` → authorization: the token is accepted but lacks scope/role/permission (or key quota / IP restriction).
4. **Compare to a known-good request** (Postman/curl) — replicate its headers exactly; a difference in the `Authorization` value or a missing header is the cause.

## Resolution

- **401 — fix the credential presentation:**
  - Format the header with its scheme: `Authorization = "Bearer " + tokenVariable` (do not send the bare token; match the scheme the API documents).
  - Supply a **fresh, valid** token (refresh per run; retrieve via Get Credential / an Orchestrator credential asset rather than a stale literal), minted for the **correct environment/audience**.
  - Put the credential where the API expects it (header vs query; correct header name).
- **403 — fix authorization:** grant the identity the required scope/role/permission on the target API, or use a principal/key that has it; check API-key quota and any IP allowlist.
- **Confirm against a known-good client** — mirror the exact headers of a succeeding Postman/curl call, then re-run and confirm a `2xx`.
- Do not treat `401/403` as a transport, proxy, or endpoint-path problem — the server answered; correcting DNS/proxy/URL will not change an auth rejection. For the raw-transport / DNS / TLS branch see [http-request-connection-failure.md](./http-request-connection-failure.md); for secure handling of the token itself (Workflow Analyzer ST-SEC-009) see [securestring-misuse-analyzer.md](./securestring-misuse-analyzer.md).

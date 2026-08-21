---
name: uipath-automationhub
description: "Publish and read business processes in UiPath Automation Hub via the Open API, using the user's cloud login — no admin OpenAPI token needed. PUBLISH an approved process and its PDD/SDD documents (schema-driven payload, link-based docs) to AH as the system of record — e.g. a process captured/approved by Process Scribe. GET a process back by id or search and retrieve its attached documents (e.g. for dedup / related-idea lookups). Authenticates with the user's cloud bearer token and NEVER sends the admin `x-ah-openapi-auth` header. Routes by intent to `references/publish-process.md` (publish/create/upload) or `references/get-process.md` (get/read/fetch/list), over the shared auth + endpoint catalog in `references/api-endpoints.md`. Structured to extend to more Automation Hub Open API operations."
allowed-tools: Bash, Read, AskUserQuestion
user-invocable: true
---

# UiPath Automation Hub — Open API Assistant

Work with business processes in UiPath Automation Hub (AH) through the AH Open API, authenticating with the **user's cloud access token** — the user does **not** need an admin-generated OpenAPI token. This one skill covers both writing a process to AH and reading one back; pick the flow below.

## Step 0: Read the API reference

Always read [`references/api-endpoints.md`](references/api-endpoints.md) first. It is the shared source of truth for the cloud-token auth model, the base/gateway URL, the exact headers (**and which header to never send**), and every endpoint the flows use.

## Authentication (shared — both flows)

Resolve the cloud token + base URL + org + tenant in this **priority order**:

1. **Runtime env-auth (preferred — how UiPath Delegate provides it).** If `UIPATH_CLI_AUTH_TOKEN` is set (with `UIPATH_CLI_ENABLE_ENV_AUTH=true`), use it as the bearer and take org/tenant from `UIPATH_CLI_ORGANIZATION_NAME` / `UIPATH_CLI_TENANT_NAME` (and the `..._ID` variants). Base URL defaults to `https://cloud.uipath.com`. *(If a parent `uip` process instead exported `UIPATH_ACCESS_TOKEN` + `UIPATH_URL` — the `{base}/{org}/{tenant}` shape — use those.)*
2. **Logged-in `uip` session.** Otherwise, if the user has run `uip login`, read `~/.uipath/.auth` (JSON: `accessToken`, `baseUrl`, `organizationName`, `tenantName`).
3. **User-provided (last resort).** Ask the user to paste a cloud bearer token plus their **org** and **tenant** slugs (the two path segments after the host in their AH URL).

Use whatever you resolved as `$ACCESS_TOKEN`, `$BASE_URL`, `$ORG`, `$TENANT` in the flows.

**Gateway URL** (every request):

```
{baseUrl}/{org}/{tenant}/automationhub_/api/v1/openapi
```

The platform injects tenant-routing headers from the `{org}/{tenant}` segments — always use this gateway URL.

**Header rules (do not regress these):**

- Send `Authorization: Bearer <cloud access token>` on every request (and `Content-Type: application/json` on POSTs).
- **NEVER** send `x-ah-openapi-auth` or `x-ah-openapi-app-key`. Those route to the admin-token path and reject a cloud token with **401** — never add them to "fix" a 401.
- Never fall back to an admin OpenAPI token. If no token resolves, stop and explain the skill needs the user's cloud session (`uip login`) or a host-provided token.
- Cloud tokens are short-lived. On a **401**, if the token came from `~/.uipath/.auth`, tell the user to run `uip login` again, re-resolve, and retry.

## Routing — pick the flow by intent

Classify what the user wants, then follow the matching reference. All flows share the Authentication section above and the endpoint catalog in `references/api-endpoints.md`.

| The user wants to... | Follow |
|---|---|
| **Publish / create / upload** a process (+ its PDD/SDD documents) to AH | [`references/publish-process.md`](references/publish-process.md) |
| **Get / read / fetch / list** a process (+ its documents) from AH | [`references/get-process.md`](references/get-process.md) |
| Shared **auth + endpoint catalog** (base URL, headers, every endpoint, error codes) | [`references/api-endpoints.md`](references/api-endpoints.md) |
| _(future AH Open API operation — add a row here)_ <!-- uip-check-skip --> | _add `references/<operation>.md` and route to it_ |

To add a new capability (e.g. a future AH `uip` CLI surface or another Open API operation), keep this skill's product shape: add one `references/<operation>.md`, add a row above, and reuse this shared Authentication section — do not create a new per-operation skill.

## Notes

- **Cloud token only** — authorization is the user's real AH permissions; you see and can do exactly what their AH role allows.
- The publish flow fetches the idea-flow schema live, so it adapts automatically if fields change on the tenant.
- **Open dependency:** in a hosted runtime (e.g. Process Scribe/Delegate) the cloud token is expected via the environment (Authentication, option 1). Confirm the runtime provides `UIPATH_CLI_AUTH_TOKEN` (or an equivalent) before relying on it in production.

# Automation Hub Open API — Reference (cloud-token auth, read path)

> Authenticate with the **user's UiPath cloud access token** — **not** an admin OpenAPI token. Send the bearer token and **do not** send `x-ah-openapi-auth`.

## Authentication

Identical to the publish skill. Resolve the cloud token + base + org + tenant in priority order:
1. **Runtime env-auth (preferred — how UiPath Delegate provides it):** `UIPATH_CLI_AUTH_TOKEN` (bearer) + `UIPATH_CLI_ORGANIZATION_NAME` / `UIPATH_CLI_TENANT_NAME`, set when the runtime runs `uip` with `UIPATH_CLI_ENABLE_ENV_AUTH=true`. Base URL defaults to `https://cloud.uipath.com`. *(Or `UIPATH_ACCESS_TOKEN` + `UIPATH_URL` if a parent `uip` process exported them.)*
2. `~/.uipath/.auth` (JSON: `accessToken`, `baseUrl`, `organizationName`, `tenantName`) after `uip login`.
3. User-provided token + org + tenant.

Base URL: `{baseUrl}/{org}/{tenant}/automationhub_/api/v1/openapi`. Headers: `Authorization: Bearer <token>` only (no `x-ah-openapi-auth`, no `x-ah-openapi-app-key`). Cloud tokens are short-lived — on 401, re-run `uip login` (or re-provide) and retry.

## Endpoints

### GET `/automations?search=<text>&limit=<n>&offset=<n>`
Search/list processes. Returns a paged list (results under a resource key, e.g. `processes`, or a bare array). Use to resolve a name → `process_id`.

### GET `/automations/{id}`
Fetch one process by numeric id (or slug). Returns the full process record (can be ~300 fields; project to the ones you need for display).

### GET `/automations/{id}/documents`
List the process's documents (key `documents`); each entry includes the document name, type, and a `FileId` / download reference.

### GET `/automations/{id}/components`  *(optional)*
Linked components for the process.

## Errors

| Status | Meaning |
|--------|---------|
| 401 | Token missing/expired, or `x-ah-openapi-auth` wrongly sent |
| 403 | User lacks AH permission for this process |
| 404 | No such process, wrong URL, or AH not enabled |

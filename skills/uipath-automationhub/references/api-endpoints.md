# Automation Hub Open API — Reference (cloud-token auth)

> This skill authenticates with the **user's UiPath cloud access token** — **not** an admin-generated OpenAPI token. This is the AH Open API's `automation-cloud` mode: send the bearer token and **do not** send `x-ah-openapi-auth`.

This is the shared auth + endpoint catalog for both flows — [`publish-process.md`](publish-process.md) (write) and [`get-process.md`](get-process.md) (read).

## Authentication

### Getting the cloud token + org/tenant (in priority order)

1. **Runtime env-auth (preferred — this is how UiPath Delegate provides it).** The runtime runs `uip` in a virtual shell with `UIPATH_CLI_ENABLE_ENV_AUTH=true` and sets `UIPATH_CLI_AUTH_TOKEN` (the user's cloud bearer token) plus `UIPATH_CLI_ORGANIZATION_NAME` / `UIPATH_CLI_TENANT_NAME` (and `..._ID` variants). If `UIPATH_CLI_AUTH_TOKEN` is set, use it as the bearer and take org/tenant from those vars. Base URL defaults to `https://cloud.uipath.com` unless the environment specifies another. *(If a parent `uip` process instead exported `UIPATH_ACCESS_TOKEN` + `UIPATH_URL` — the `{base}/{org}/{tenant}` shape — use those.)*
2. **Logged-in `uip` session.** Otherwise, if the user has run `uip login`, read `~/.uipath/.auth` (JSON). Use its `accessToken`, `baseUrl`, `organizationName`, `tenantName`. If the file is missing or has no `accessToken`, tell the user to run `uip login` (and `uip login tenant set <name>` to pick the tenant).
3. **User-provided (last resort).** Ask the user to paste a cloud bearer token plus their **org** and **tenant** slugs (the two path segments after the host in their AH URL).

Never fall back to an admin OpenAPI token. If none of the above yields a token, stop and explain that the skill needs the user's cloud session (`uip login`) or a host-provided token.

### Base URL

```
{baseUrl}/{org}/{tenant}/automationhub_/api/v1/openapi
```

e.g. `https://cloud.uipath.com/acme/prod/automationhub_/api/v1/openapi`. Always use this **gateway** URL — the platform injects the tenant-routing headers from the `{org}/{tenant}` segments. (Local dev: base `http://localhost:3002`, path `/api/v1/openapi`, and you must confirm how org/tenant are supplied locally.)

### Headers (every request)

| Header | Value | When |
|--------|-------|------|
| `Authorization` | `Bearer <cloud access token>` | always |
| `Content-Type` | `application/json` | POST only |

**Do NOT send** `x-ah-openapi-auth` or `x-ah-openapi-app-key`. Sending `x-ah-openapi-auth: openapi-token` routes to the admin-token path and rejects a cloud token with **401**.

### Token expiry

Cloud access tokens are short-lived. If any call returns **401** and the token came from `~/.uipath/.auth`, tell the user to run `uip login` again (or re-provide a token) and retry.

## Endpoints used by this skill

### GET `/idea-flows`
All idea flows (workflow types) on the tenant. Each element has `Idea flow name` (e.g. "Business Process") and `Idea flow ID` (number). Response wrapped as `{ message, statusCode, data: [...] }`. *(Used by the publish flow.)*

### GET `/idea-schema?idea_flow_id={id}`
Full JSON schema for an idea flow + a ready-made `user_inputs` template. Response wrapped as `{ status: "success", data: {...} }`:
- `data.properties.schema.properties` — field definitions, 3-level nested (Assessment Type > Section > Question); enums carry `answer_option` codes + labels in `custom_properties`.
- `data.user_inputs` — the exact POST body template ("fill in the blanks"). Most fields wrap as `{ "value": <v> }`; owner/submitter questions take a direct string (no wrapper); questions with no example are omitted.

*(Used by the publish flow.)*

### POST `/idea-from-schema`
Create a process from the schema. **Use this, not `POST /automations`** (the `/automations` alias 404s in some deployments).

Body:
```json
{ "idea_flow_id": <id>, "user_inputs": { "<AssessmentType>": { "<section-ahid>": { "<question-key>": { "value": "<v>" } } } } }
```
**Do not POST `data.user_inputs` verbatim** — its example values are placeholders that the API rejects. Replace each with a real value; in particular resolve a **valid** `OVERVIEW_CATEGORY` id (the template's `1` → `Invalid Category Id`) and real `answer_option` codes (a placeholder code → backend `co_question_answer_option_value` crash).

**Required fields (Business Process, `idea_flow_id`=7), verified live** — note the backend enforces owner + submitter even though the schema's `required` flags omit them:

| Key | Section | Shape |
|---|---|---|
| `OVR-OVERVIEW_NAME` | `ah-section-ovr-0-0` | `{"value":"…"}` |
| `OVR-OVERVIEW_DESCRIPTION` | `ah-section-ovr-0-0` | `{"value":"…"}` |
| `OVR-OVERVIEW_CATEGORY` | `ah-section-ovr-0-0` | `{"value":<valid id>}` |
| `OVR-PROCESS_DOCUMENTS` | `ah-section-ovr-0-0` | `{"value":["<answer_option code>"]}` |
| `OVR-PROCESS_OWNER` | `ah-section-ovr-0-0` | `"<email>"` (direct string) |
| `OVR-OVERVIEW_PROCESS_SUBMITTER` | `ah-section-ovr-0-1` | `"<email>"` (direct string) |

When a required field is missing the API may return `errorDetails: {}` (no field named) with `"Please fill in all the required information"` — that is almost always the un-flagged owner/submitter.

**Response 201** — the created process object **at the top level** (not nested): `process_id`, `process_uuid`, `process_name`, … Record `process_id`. *(Used by the publish flow.)*

### POST `/automations/{process_id}/documents`
Attach a document to a process. **Link-based** (a link/embed URL + metadata), not a raw file upload — byte upload is a separate `media` endpoint that is not usable yet. Governed by `open-api-service` `ProcessDocumentValidator` (`src/models/schema/processDocumentRequest.schema.ts`). **Required fields, verified live:**

```json
{ "document_title": "…", "document_description": "…", "document_type_id": 1, "embed_link": "https://…" }
```

- `document_title` (**not** `document_name`), `document_description`, `document_type_id` are all required by the schema.
- Plus **exactly one** of `embed_link` or `file` — enforced in the handler (not the schema), so omitting both 400s with `"One and only one of embed_link or file need to be specified."` Use `embed_link`.

Returns the created `document_id`. *(Used by the publish flow.)*

### GET `/automations?search=<text>&limit=<n>&offset=<n>`
Search/list processes. Returns a paged list (results under a resource key, e.g. `processes`, or a bare array). Use to resolve a name → `process_id`. *(Used by the get flow.)*

### GET `/automations/{id}`
Fetch one process by numeric id (or slug). Returns the full process record (can be ~300 fields; project to the ones you need for display). *(Used by the get flow.)*

### GET `/automations/{process_id}/documents`
List a process's documents (key `documents`); each entry includes the document name, type, and a `FileId` / download reference. *(Used by both flows.)*

### GET `/automations/{id}/components`  *(optional)*
Linked components for the process.

## Errors

| Status | Meaning |
|--------|---------|
| 400 | Validation — missing required field, invalid enum, empty `user_inputs`, missing `OVERVIEW_NAME` |
| 401 | Unauthorized — token missing/expired, or `x-ah-openapi-auth` was wrongly sent |
| 403 | Forbidden — the user lacks the AH permission (authorization = the user's real AH role) |
| 404 | Wrong URL, or AH not enabled on the tenant |
| 409 | Duplicate process name |
